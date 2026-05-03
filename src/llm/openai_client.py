import json
from typing import AsyncGenerator
from openai import AsyncOpenAI
from src.config import settings
from .base import BaseLLMClient

class OpenAILLMClient(BaseLLMClient):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def generate(self, prompt: str, response_format: str = "text") -> str:
        kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 700
        }
        if response_format == "json_object":
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            temperature=0.0,
            max_tokens=700
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content
