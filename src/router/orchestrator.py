from typing import Any
from src.core.schemas import ClassifierResult

async def route_request(classifier_result: ClassifierResult, user_data: dict, llm: Any = None) -> dict:
    target_agent = classifier_result.target_agent
    
    if target_agent == "portfolio_health":
        from src.agents.portfolio_health import run as run_portfolio_health
        return await run_portfolio_health(user_data, llm=llm)
    
    # Stub response for all other agents as required by ASSIGNMENT.md
    return {
        "status": "not_implemented",
        "intent": classifier_result.intent,
        "extracted_entities": classifier_result.entities,
        "target_agent": target_agent,
        "message": f"Agent '{target_agent}' is not implemented in this assignment build. Stub response."
    }
