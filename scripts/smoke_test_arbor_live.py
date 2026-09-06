#!/usr/bin/env python3
"""One minimal live request through Arbor's native LiteLLM provider."""

from __future__ import annotations

import asyncio
import os

from arbor.core import AgentConfig, create_provider


async def run() -> None:
    model = os.environ.get("AI_SCIENTIST_MODEL")
    base_url = os.environ.get("AI_SCIENTIST_BASE_URL")
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not model or not base_url or not api_key:
        raise SystemExit("Source the protected qwen.env file first.")

    config = AgentConfig(
        provider="litellm",
        model=model,
        api_key=api_key,
        base_url=base_url,
        reasoning_effort=None,
    )
    response = await create_provider(config).create(
        system="Follow the user's instruction exactly.",
        messages=[{"role": "user", "content": "Reply with exactly: ARBOR_QWEN_OK"}],
        max_tokens=16,
    )
    content = response.get_text().strip()
    if content != "ARBOR_QWEN_OK":
        raise RuntimeError(f"Unexpected response: {content!r}")
    print(
        "Arbor native Qwen smoke test passed "
        f"(model={response.model}, input_tokens={response.usage.input_tokens}, "
        f"output_tokens={response.usage.output_tokens})"
    )


if __name__ == "__main__":
    asyncio.run(run())
