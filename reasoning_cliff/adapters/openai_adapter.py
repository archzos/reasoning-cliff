"""OpenAI adapter for GPT/o-series models."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(slots=True)
class AdapterResponse:
    text: str
    output_tokens: int
    thinking_tokens: int | None
    truncated: bool
    stop_reason: str | None
    latency_ms: float


class OpenAIAdapter:
    def __init__(self, model: str) -> None:
        self.model = model

    def generate(self, prompt: str, max_tokens: int) -> AdapterResponse:
        from openai import OpenAI

        client = OpenAI()
        start = time.perf_counter()

        if self.model.startswith("o"):
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=max_tokens,
            )
        else:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )

        latency_ms = (time.perf_counter() - start) * 1000
        choice = response.choices[0]
        details = getattr(response.usage, "completion_tokens_details", None)
        thinking_tokens = getattr(details, "reasoning_tokens", None) if details is not None else None

        return AdapterResponse(
            text=choice.message.content or "",
            output_tokens=response.usage.completion_tokens,
            thinking_tokens=thinking_tokens,
            truncated=choice.finish_reason == "length",
            stop_reason=choice.finish_reason,
            latency_ms=latency_ms,
        )
