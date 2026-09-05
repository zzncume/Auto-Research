#!/usr/bin/env python3
"""One minimal live request to verify the configured Qwen endpoint."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path

from openai import OpenAI


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path)
    args = parser.parse_args()

    key = os.environ.get("DASHSCOPE_API_KEY")
    model = os.environ.get("AI_SCIENTIST_MODEL")
    base_url = os.environ.get("AI_SCIENTIST_BASE_URL")
    if not key or not model or not base_url:
        raise SystemExit("Source the protected qwen.env file first.")

    content = [{"type": "text", "text": "Reply with exactly: QWEN_SMOKE_OK"}]
    if args.image:
        mime = mimetypes.guess_type(args.image.name)[0] or "image/jpeg"
        encoded = base64.b64encode(args.image.read_bytes()).decode("ascii")
        content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}})

    response = OpenAI(api_key=key, base_url=base_url).chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": content}],
        max_tokens=16,
        temperature=0,
    )
    message = response.choices[0].message.content
    if not message or not message.strip():
        raise RuntimeError("Live endpoint returned empty content.")
    usage = response.usage
    print(json.dumps({
        "status": "ok",
        "requested_model": model,
        "response_model": response.model,
        "content": message.strip(),
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
