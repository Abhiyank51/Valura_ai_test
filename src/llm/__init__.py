from src.config import settings
from .base import BaseLLMClient
from .fake_client import FakeLLMClient
from .openai_client import OpenAILLMClient

def get_llm_client() -> BaseLLMClient:
    if settings.APP_ENV == "test" or not settings.OPENAI_API_KEY:
        return FakeLLMClient()
    return OpenAILLMClient()
