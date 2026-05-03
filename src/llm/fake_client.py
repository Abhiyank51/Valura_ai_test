import json
import os
import re
from typing import AsyncGenerator

from .base import BaseLLMClient


class FakeLLMClient(BaseLLMClient):
    def __init__(self):
        self.fixture_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "../../fixtures/test_queries/intent_classification.json",
            )
        )
        self.queries = []
        if os.path.exists(self.fixture_path):
            with open(self.fixture_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.queries = data.get("queries", [])

    def _extract_user_query(self, prompt: str) -> str:
        patterns = [
            r"Current Query:\s*(.+)",
            r"User Query:\s*(.+)",
            r"Query:\s*(.+)",
            r'"message"\s*:\s*"([^"]+)"',
            r"'message'\s*:\s*'([^']+)'",
        ]

        for pattern in patterns:
            match = re.search(pattern, prompt, flags=re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                # Keep only the first line if the capture includes prompt instructions after the query.
                return value.splitlines()[0].strip()

        return prompt.strip()

    def _extract_tickers(self, text: str) -> list[str]:
        alias_map = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "tesla": "TSLA",
            "nvidia": "NVDA",
            "amazon": "AMZN",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "meta": "META",
            "facebook": "META",
            "netflix": "NFLX",
        }

        found = set()
        lower = text.lower()

        for name, ticker in alias_map.items():
            if name in lower:
                found.add(ticker)

        for token in re.findall(r"\b[A-Z]{2,5}\b", text):
            # Avoid common non-ticker words from prompts.
            if token.upper() not in {"JSON", "LLM", "SSE", "USD", "INR"}:
                found.add(token.upper())

        return sorted(found)

    def _result(self, intent: str, target_agent: str, entities: dict | None = None) -> str:
        return json.dumps(
            {
                "intent": intent,
                "target_agent": target_agent,
                "entities": entities or {},
                "safety_verdict": {
                    "blocked": False,
                    "category": "safe",
                },
            }
        )

    async def generate(self, prompt: str, response_format: str = "text") -> str:
        if response_format != "json_object":
            return "This is a deterministic fake response."

        query = self._extract_user_query(prompt)
        q = query.lower()

        # 1. Portfolio Health / Monitor / Protect queries.
        portfolio_health_keywords = [
            "how is my portfolio doing",
            "portfolio doing",
            "portfolio health",
            "health check",
            "check my portfolio",
            "analyze my portfolio",
            "analyze my holdings",
            "my holdings",
            "am i diversified",
            "diversified",
            "diversification",
            "concentration risk",
            "is my portfolio risky",
            "portfolio risk",
            "am i beating the market",
            "portfolio summary",
            "drawdown",
        ]

        if any(keyword in q for keyword in portfolio_health_keywords):
            return self._result(
                intent="portfolio_health",
                target_agent="portfolio_health",
                entities={"topics": ["portfolio_health"]},
            )

        # 2. Support queries.
        if any(
            keyword in q
            for keyword in [
                "login",
                "password",
                "account locked",
                "can't access",
                "cannot access",
                "kyc issue",
                "support",
            ]
        ):
            return self._result(
                intent="support",
                target_agent="customer_support",
                entities={"topics": ["login"]},
            )

        # 3. Financial calculator queries.
        if any(
            keyword in q
            for keyword in [
                "calculate",
                "capital gains",
                "tax",
                "compound",
                "sip",
                "return calculation",
                "annualized return",
            ]
        ):
            return self._result(
                intent="financial_calculation",
                target_agent="financial_calculator",
                entities={"tickers": self._extract_tickers(query)},
            )

        # 4. Market research queries.
        if any(
            keyword in q
            for keyword in [
                "tell me about",
                "research",
                "news",
                "earnings",
                "stock analysis",
                "what about",
                "price target",
            ]
        ):
            return self._result(
                intent="market_research",
                target_agent="market_research",
                entities={"tickers": self._extract_tickers(query)},
            )

        # 5. Investment strategy / recommendation queries.
        if any(
            keyword in q
            for keyword in [
                "should i buy",
                "recommend",
                "allocation",
                "strategy",
                "invest in",
                "rebalance",
                "where should i invest",
            ]
        ):
            return self._result(
                intent="investment_strategy",
                target_agent="investment_strategy",
                entities={"tickers": self._extract_tickers(query)},
            )

        # 6. Fixture matching. This preserves the gold-file behavior.
        for case in self.queries:
            fixture_query = case.get("query", "").lower().strip()
            if fixture_query and fixture_query in q:
                expected_agent = case["expected_agent"]
                expected_entities = case.get("expected_entities", {})
                expected_intent = case.get("expected_intent", expected_agent)

                return self._result(
                    intent=expected_intent,
                    target_agent=expected_agent,
                    entities=expected_entities,
                )

        # 7. Unknown queries should go to a stub, not portfolio_health.
        return self._result(
            intent="general_query",
            target_agent="general_query",
            entities={},
        )

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        chunks = ["This ", "is ", "a ", "fake ", "streamed ", "response."]
        for chunk in chunks:
            yield chunk
