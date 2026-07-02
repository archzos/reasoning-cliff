"""AWS Bedrock adapter for Claude models."""

from __future__ import annotations

import json
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


class BedrockAdapter:
    def __init__(self, model_id: str, region: str = "ap-south-1") -> None:
        self.model_id = model_id
        self.region = region

    def generate(self, prompt: str, max_tokens: int, thinking_budget: int = 5000) -> AdapterResponse:
        import boto3

        client = boto3.client("bedrock-runtime", region_name=self.region)
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "thinking": {"type": "enabled", "budget_tokens": thinking_budget},
            "messages": [{"role": "user", "content": prompt}],
        }

        start = time.perf_counter()
        response = client.invoke_model(modelId=self.model_id, body=json.dumps(payload))
        latency_ms = (time.perf_counter() - start) * 1000

        body = json.loads(response["body"].read())
        output_text = ""
        thinking_tokens: int | None = None

        for block in body.get("content", []):
            if block.get("type") == "text":
                output_text += block.get("text", "")
            if block.get("type") == "thinking":
                thinking_text = block.get("thinking", "")
                thinking_tokens = len(thinking_text.split())

        usage = body.get("usage", {})
        return AdapterResponse(
            text=output_text,
            output_tokens=usage.get("output_tokens", 0),
            thinking_tokens=thinking_tokens,
            truncated=body.get("stop_reason") == "max_tokens",
            stop_reason=body.get("stop_reason"),
            latency_ms=latency_ms,
        )
