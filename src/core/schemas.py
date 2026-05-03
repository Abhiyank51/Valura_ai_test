from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# --- HTTP Request / Response ---

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user's input query.")
    user_id: Optional[str] = Field("default_user", description="The ID of the user.")
    session_id: Optional[str] = None
    user_context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    agent_used: str
    safety_notice: str

class SSEMessage(BaseModel):
    data: str
    event: Optional[str] = None
    id: Optional[str] = None
    retry: Optional[int] = None

# --- Internal Pipeline Structures ---

class SafetyVerdict(BaseModel):
    blocked: bool
    category: Optional[str] = None
    message: Optional[str] = None

class ClassifierResult(BaseModel):
    intent: str
    target_agent: str
    entities: Dict[str, Any] = Field(default_factory=dict)
    safety_verdict: Optional[SafetyVerdict] = None

class AgentResponse(BaseModel):
    agent_name: str
    response_content: Any
