import asyncio
import json
import logging
import time
from pathlib import Path
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from src.core.schemas import ChatRequest
from src.safety.guard import check as safety_check
from src.classifier.intent import classify
from src.router.orchestrator import route_request
from src.memory.store import get_history, add_to_history

logger = logging.getLogger(__name__)
router = APIRouter()

# Project root — two levels above src/api/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

PIPELINE_TIMEOUT_SECONDS = 8


def load_user_fixture(user_id: str) -> dict:
    """
    Load user fixture from several candidate locations.
    Never crashes — returns {} if nothing is found.
    """
    candidates_dirs = [
        _PROJECT_ROOT / "fixtures" / "user_profiles",
        _PROJECT_ROOT / "fixtures" / "users",
        _PROJECT_ROOT / "fixtures",
    ]
    # 1. exact matches
    for dir_path in candidates_dirs:
        exact_path = dir_path / f"{user_id}.json"
        if exact_path.exists():
            try:
                return json.loads(exact_path.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("Could not parse fixture at %s", exact_path)
    # 2. prefix matches
    for dir_path in candidates_dirs:
        if dir_path.exists():
            matches = sorted(dir_path.glob(f"{user_id}*.json"))
            for match in matches:
                try:
                    return json.loads(match.read_text(encoding="utf-8"))
                except Exception:
                    logger.warning("Could not parse fixture at %s", match)
    return {}


@router.post(
    "/v1/chat/stream",
    responses={
        200: {
            "description": "Server-Sent Events (SSE) stream",
            "content": {"text/event-stream": {}},
        }
    },
)
async def chat_stream(request: Request, body: ChatRequest):
    user_id = body.user_id or "default_user"
    query = body.message
    # Use session_id for memory scoping — falls back to user_id
    session_key = body.session_id or user_id

    async def event_generator():
        start_time = time.perf_counter()
        
        # ── 1. Safety Guard (synchronous, always first) ───────────────────
        safety_verdict = safety_check(query)
        if safety_verdict.blocked:
            yield {
                "data": json.dumps({
                    "type": "safety",
                    "blocked": True,
                    "category": safety_verdict.category,
                    "message": safety_verdict.message,
                })
            }
            elapsed_ms = round((time.perf_counter() - start_time) * 1000)
            yield {
                "data": json.dumps({
                    "type": "metrics",
                    "total_elapsed_ms": elapsed_ms,
                    "timeout_seconds": PIPELINE_TIMEOUT_SECONDS
                })
            }
            yield {"data": "[DONE]"}
            return
            
        yield {
            "data": json.dumps({
                "type": "metadata",
                "status": "pipeline_started",
                "message": "Request accepted. Classifying intent..."
            })
        }

        # ── 2. Classify + Route (with pipeline timeout) ───────────────────
        async def _pipeline():
            history = get_history(session_key)
            classifier_result = await classify(query, history=history)
            add_to_history(session_key, query)
            user_data = body.user_context or load_user_fixture(user_id)
            agent_response = await route_request(classifier_result, user_data)
            return classifier_result, agent_response

        try:
            classifier_result, agent_response = await asyncio.wait_for(
                _pipeline(), timeout=PIPELINE_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            yield {
                "data": json.dumps({
                    "type": "error",
                    "category": "timeout",
                    "message": "The request timed out. Please try again with a shorter query.",
                })
            }
            elapsed_ms = round((time.perf_counter() - start_time) * 1000)
            yield {
                "data": json.dumps({
                    "type": "metrics",
                    "total_elapsed_ms": elapsed_ms,
                    "timeout_seconds": PIPELINE_TIMEOUT_SECONDS
                })
            }
            yield {"data": "[DONE]"}
            return
        except Exception:
            logger.exception("Pipeline error for query=%r", query)
            yield {
                "data": json.dumps({
                    "type": "error",
                    "message": "The request could not be processed safely. Please try again.",
                })
            }
            elapsed_ms = round((time.perf_counter() - start_time) * 1000)
            yield {
                "data": json.dumps({
                    "type": "metrics",
                    "total_elapsed_ms": elapsed_ms,
                    "timeout_seconds": PIPELINE_TIMEOUT_SECONDS
                })
            }
            yield {"data": "[DONE]"}
            return

        # ── 3. Stream classifier event ────────────────────────────────────
        yield {
            "data": json.dumps({
                "type": "classifier",
                "intent": classifier_result.intent,
                "agent": classifier_result.target_agent,
            })
        }

        # ── 4. Stream agent response ──────────────────────────────────────
        yield {
            "data": json.dumps({
                "type": "agent_response",
                "payload": agent_response,
            })
        }

        elapsed_ms = round((time.perf_counter() - start_time) * 1000)
        yield {
            "data": json.dumps({
                "type": "metrics",
                "total_elapsed_ms": elapsed_ms,
                "timeout_seconds": PIPELINE_TIMEOUT_SECONDS
            })
        }

        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())
