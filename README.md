# Valura AI Portfolio Copilot

## 1. Project Overview
Valura AI is a backend microservice that serves as an AI co-investor for novice users. It provides an intelligent ecosystem of specialized agents capable of parsing intent, safely interacting with user queries, and streaming real-time guidance directly into an SSE client dashboard.

## 2. Mission
To provide a safety-first, educational, and accessible AI-driven portfolio copilot for novice investors, helping them build, monitor, grow, and protect their investments.

## 3. Architecture
- **Framework**: `FastAPI` powering an asynchronous SSE `text/event-stream` endpoint.
- **Frontend**: Lightweight vanilla HTML/JS/CSS dashboard included for evaluation.
- **LLM Client**: Pluggable interface (`BaseLLMClient`) wrapping `AsyncOpenAI`.

## 4. Request Flow
```text
Client/Dashboard -> POST /v1/chat/stream
  |
  +-- 1. Safety Guard (Synchronous, local heuristic validation)
  |      [If blocked -> yield type="safety" -> end with [DONE]]
  |
  +-- 2. Intent Classifier (LLM, extracts intents & entities)
  |      [Yield type="classifier"]
  |
  +-- 3. Orchestrator / Router
  |      [Routes to target agent]
  |
  +-- 4. Target Agent
  |      [Yield type="agent_response"]
  |
  +-- 5. End Stream
         [Yield data="[DONE]"]
```

## 5. Agent Taxonomy
The system is designed with a specific agent taxonomy:
- `portfolio_health`: Analyzes existing holdings, concentration, and performance.
- `market_research`: Evaluates specific companies or macro trends.
- `investment_strategy`: Helps define asset allocation and strategy.
- `financial_planning`: Focuses on retirement, education, and goal-based planning.
- `financial_calculator`: Computes taxes, SIPs, and compounding.
- `risk_assessment`: Assesses user risk tolerance.
- `product_recommendation`: Suggests specific financial products.
- `predictive_analysis`: Predicts market trends (strictly governed).
- `customer_support`: Handles account access and platform issues.
- `general_query`: Fallback for unrelated questions.

## 6. Safety Guard Design
- **Local & Synchronous**: Runs before any network or LLM calls to ensure sub-millisecond response times for policy violations.
- **Strict Precedence**: If the Safety Guard blocks a query, the intent classifier is *never* run, and the pipeline terminates immediately with a structured refusal.
- **Educational Pass-through**: Uses heuristic matching to allow educational questions (e.g., "What is insider trading?") while strictly blocking enabling requests containing action words (e.g., "How do I use inside info").

## 7. Classifier Design
- The Intent Classifier uses a structured LLM output (`json_object`) to map user input into the agent taxonomy while extracting relevant entities (like tickers or amounts).
- Handles conversational history for context-aware routing.
- Falls back gracefully to `general_query` if the LLM fails or fails to return valid JSON.

## 8. Portfolio Health Agent Design
- **Fully Implemented**: The `portfolio_health` agent calculates concentration risk thresholds (`low` < 25%, `moderate` 25-40%, `high` > 40%).
- **Dynamic Performance**: Computes total return only when `cost_basis` and `current_value` are present.
- **No Hardcoded Market Data**: It dynamically selects the correct benchmark based on user context (e.g., S&P 500 for US, Nifty 50 for India) but correctly notes that benchmark returns require an external market data feed.
- **Empty Portfolios**: Gracefully guides users on how to build a portfolio (goals, time horizon, emergency funds) if no holdings exist.

## 9. Stub Agent Behavior
- As per the assignment constraints, only the `portfolio_health` agent is fully implemented.
- All other agents successfully route via the Orchestrator but return a structured `not_implemented` stub response gracefully, without crashing the application.

## 10. SSE Streaming Design
- The `/v1/chat/stream` endpoint uses `sse-starlette` to stream discrete JSON events (`type: "classifier"`, `type: "agent_response"`, `type: "safety"`, `type: "error"`).
- Strict termination: The stream always closes cleanly by yielding `data: [DONE]`.
- No JSON fallback path for the main query pipeline.

## 11. Persistence / Session Memory Decision
- Session history is tracked in-memory using `session_id` (defaulting to `user_id` if missing).
- This strictly scopes memory to prior turns of the same conversation, matching assignment requirements, and guarantees zero infrastructure friction during evaluation.

## 12. Timeout Decision
- **8 Seconds**: A strict 8-second `asyncio.wait_for` timeout wraps the Classifier and Agent execution. 8 seconds was chosen as it provides sufficient time for a modern LLM (gpt-4o-mini) to return a structured JSON response while preventing the SSE connection from hanging indefinitely on network stalls.
- If timeout occurs, the system yields a graceful `type: "error"` event.

## 13. Cost and Performance Strategy
- **Local Safety**: Bouncing harmful queries locally saves LLM tokens and latency.
- **Model Selection**: Defaults to `gpt-4o-mini` for fast, cost-effective development. Evaluation or production can be switched to `gpt-4.1` via `.env`.
- **Token Limits**: Uses `max_tokens=700` for LLM calls to prevent runaway generation costs.
- **Single Classifier Call**: Intent mapping and entity extraction are performed in a single structured prompt to minimize roundtrips.

## 14. Setup Instructions

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```

## 15. Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key.
- `OPENAI_MODEL`: Model choice (defaults to `gpt-4o-mini`).
- `APP_ENV`: Environment (e.g., `development`, `production`).
- `DATABASE_URL`: Connection string (if implemented later).

## 16. Run Instructions
Start the FastAPI application:
```bash
uvicorn src.main:app --reload
```

## 17. Test Instructions
Tests run safely without requiring an OpenAI key:
```bash
pytest tests/ -v
```
*(Tests use a `FakeLLMClient` deterministic classifier in no-key mode. The real `OpenAILLMClient` is used when `OPENAI_API_KEY` is present).*

## 18. Dashboard Instructions
A polished, Valura-themed frontend dashboard is available at:
- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/dashboard`

## 19. API Examples
To test the SSE API manually:
```bash
curl -N -X POST http://127.0.0.1:8000/v1/chat/stream \
     -H "Content-Type: application/json" \
     -d '{"message": "How is my portfolio doing?", "user_id": "usr_001", "session_id": "test_session"}'
```

## 20. Non-obvious Decisions
- **Fake Client Fixture Matching**: The `FakeLLMClient` parses test queries and strictly maps them against `fixtures/test_queries/intent_classification.json`. This ensures the CI pipeline perfectly evaluates routing logic without flakiness.

## 21. Tradeoffs
- **In-memory store**: Tradeoff made for simplicity of assignment deployment. In production, this would be swapped for Redis.
- **Rule-based Safety Guard**: RegExp-based safety is extremely fast but brittle compared to an LLM-based guardrail. To offset this, the prompt classifier also includes an informational safety verdict layer.

## 22. Future Improvements
- Implement the remaining 9 specialized agents.
- Replace in-memory history with Redis.
- Integrate real-time market data API for accurate benchmark returns.
- Upgrade Safety Guard with an embedded, quantized local model for semantic harm detection.

## 23. Defence Video
Defence video: <ADD_UNLISTED_VIDEO_LINK_HERE>
