from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any

class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, response_format: str = "text") -> str:
        """Generate a complete text response."""
        pass

    @abstractmethod
    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream the text response."""
        pass
