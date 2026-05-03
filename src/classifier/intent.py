import json
import logging
from typing import List, Optional, Any
from src.core.schemas import ClassifierResult
from src.llm import get_llm_client

logger = logging.getLogger(__name__)

_SAFE_FALLBACK = ClassifierResult(
    intent="general_query",
    target_agent="general_query",
    entities={},
    safety_verdict={"blocked": False, "category": "safe"},
)

async def classify(query: str, history: Optional[List[str]] = None, llm: Any = None) -> ClassifierResult:
    if llm is None:
        llm = get_llm_client()

    system_prompt = """You are an intent classification and entity extraction system for a wealth management platform.
Classify the user's intent into one of the following agents:
- portfolio_health
- market_research
- investment_strategy
- financial_planning
- financial_calculator
- risk_assessment
- product_recommendation
- predictive_analysis
- customer_support
- general_query

Extract entities such as tickers, amount, currency, topics, etc.
Also provide an informational safety verdict.

Respond ONLY with a JSON object in this exact format:
{
  "intent": "string description",
  "target_agent": "exact agent name from the list above",
  "entities": {
    "tickers": ["AAPL"],
    "amount": 1000
  },
  "safety_verdict": {
    "blocked": false,
    "category": "safe"
  }
}"""

    history_str = ""
    if history:
        history_str = "Conversation History:\n" + "\n".join([f"- {h}" for h in history]) + "\n\n"

    prompt = f"{system_prompt}\n{history_str}Current Query: {query}"

    try:
        response_text = await llm.generate(prompt, response_format="json_object")
        data = json.loads(response_text)
        return ClassifierResult(**data)
    except json.JSONDecodeError:
        logger.warning("Classifier: JSON decode failed for query=%r", query)
        return _SAFE_FALLBACK
    except Exception:
        logger.warning("Classifier: LLM call failed for query=%r", query, exc_info=True)
        return _SAFE_FALLBACK
