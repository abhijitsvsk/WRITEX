"""Provider adapters for chat-completion APIs used by Writex."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, Optional

import requests
from groq import Groq


GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"
GROQ_INTERPRETER_MODEL = "llama-3.3-70b-versatile"
DEEPSEEK_DEFAULT_MODEL = "deepseek-chat"


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    model_name: str
    base_url: Optional[str] = None


class GroqChatClient:
    """Small wrapper that lets the rest of the app read a default model."""

    def __init__(self, api_key: str, model_name: str = GROQ_DEFAULT_MODEL):
        self.provider = "groq"
        self.default_model = model_name or GROQ_DEFAULT_MODEL
        self._client = Groq(api_key=api_key)
        self.chat = self._client.chat
        self.models = self._client.models


class _DeepSeekCompletions:
    def __init__(self, owner: "DeepSeekChatClient"):
        self._owner = owner

    def create(self, **kwargs):
        payload: Dict[str, Any] = {
            key: value for key, value in kwargs.items() if value is not None
        }
        payload["model"] = payload.get("model") or self._owner.default_model

        response = requests.post(
            f"{self._owner.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._owner.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self._owner.timeout,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"DeepSeek API Error {response.status_code}: {response.text[:500]}"
            )

        data = response.json()
        choices = []
        for choice in data.get("choices", []):
            message = choice.get("message", {}) or {}
            choices.append(
                SimpleNamespace(
                    message=SimpleNamespace(content=message.get("content", "")),
                    finish_reason=choice.get("finish_reason"),
                    index=choice.get("index"),
                )
            )
        return SimpleNamespace(
            choices=choices,
            usage=data.get("usage", {}),
            model=data.get("model"),
            id=data.get("id"),
        )


class _DeepSeekChat:
    def __init__(self, owner: "DeepSeekChatClient"):
        self.completions = _DeepSeekCompletions(owner)


class _DeepSeekModels:
    def list(self):
        # DeepSeek's OpenAI-compatible API does not need model discovery for this app.
        return SimpleNamespace(data=[])


class DeepSeekChatClient:
    """OpenAI-compatible DeepSeek client without adding a new SDK dependency."""

    def __init__(
        self,
        api_key: str,
        model_name: str = DEEPSEEK_DEFAULT_MODEL,
        base_url: str = "https://api.deepseek.com",
        timeout: int = 120,
    ):
        self.provider = "deepseek"
        self.api_key = api_key
        self.default_model = model_name or DEEPSEEK_DEFAULT_MODEL
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.chat = _DeepSeekChat(self)
        self.models = _DeepSeekModels()


def normalise_provider(provider: str) -> str:
    value = (provider or "groq").strip().lower()
    if value not in {"groq", "deepseek"}:
        raise ValueError(f"Unsupported AI provider: {provider}")
    return value


def create_ai_client(
    api_key: str,
    provider: str = "groq",
    model_name: Optional[str] = None,
):
    provider = normalise_provider(provider)
    if not api_key:
        raise ValueError("API key is required.")

    if provider == "deepseek":
        return DeepSeekChatClient(
            api_key=api_key,
            model_name=model_name or DEEPSEEK_DEFAULT_MODEL,
        )

    return GroqChatClient(api_key=api_key, model_name=model_name or GROQ_DEFAULT_MODEL)


def provider_display_name(provider: str) -> str:
    return "DeepSeek" if normalise_provider(provider) == "deepseek" else "Groq"
