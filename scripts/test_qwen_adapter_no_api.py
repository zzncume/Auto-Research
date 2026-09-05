#!/usr/bin/env python3
"""Exercise an adapted AI-Scientist client without sending an external request."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


MODEL = "qwen3.8-max"


class FakeCompletions:
    def __init__(self, content="mock response"):
        self.content = content
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        usage = SimpleNamespace(
            prompt_tokens=7,
            completion_tokens=3,
            completion_tokens_details=None,
            prompt_tokens_details=None,
        )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))],
            usage=usage,
            model=MODEL,
            created=0,
        )


class FakeClient:
    def __init__(self, content="mock response"):
        self.chat = SimpleNamespace(completions=FakeCompletions(content))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system-root", required=True)
    parser.add_argument("--version", choices=("v1", "v2"), required=True)
    args = parser.parse_args()

    os.environ.update(
        AI_SCIENTIST_OPENAI_COMPATIBLE="1",
        AI_SCIENTIST_MODEL=MODEL,
        AI_SCIENTIST_BASE_URL="http://127.0.0.1:9/v1",
        AI_SCIENTIST_API_KEY="mock-not-a-secret",
    )
    sys.path.insert(0, args.system_root)
    from ai_scientist import llm

    real_client, served_model = llm.create_client(MODEL)
    assert served_model == MODEL
    assert str(real_client.base_url).rstrip("/") == "http://127.0.0.1:9/v1"

    fake = FakeClient()
    text, history = llm.get_response_from_llm(
        "hello", fake, MODEL, "system", temperature=0.2
    )
    assert text == "mock response"
    assert history[-1]["content"] == "mock response"
    request = fake.chat.completions.calls[-1]
    assert request["model"] == MODEL
    assert "seed" not in request and "n" not in request

    try:
        llm.get_response_from_llm("blank", FakeClient("  "), MODEL, "system")
    except ValueError as exc:
        assert "empty" in str(exc).lower()
    else:
        raise AssertionError("empty response was not rejected")

    if args.version == "v2":
        from PIL import Image
        from ai_scientist import vlm

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "pixel.jpg"
            Image.new("RGB", (1, 1), color="white").save(image_path)
            vision_fake = FakeClient()
            output, _ = vlm.get_response_from_vlm(
                "inspect", str(image_path), vision_fake, MODEL, "system"
            )
            assert output == "mock response"
            content = vision_fake.chat.completions.calls[-1]["messages"][-1]["content"]
            assert any(block.get("type") == "image_url" for block in content)

    print(f"{args.version} Qwen adapter no-API smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
