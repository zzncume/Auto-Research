#!/usr/bin/env python3
"""Minimal live call through an adapted AI-Scientist transport."""

from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--system-root", required=True)
    parser.add_argument("--version", choices=("v1", "v2"), required=True)
    parser.add_argument("--image")
    args = parser.parse_args()

    model = os.environ.get("AI_SCIENTIST_MODEL")
    if not os.environ.get("DASHSCOPE_API_KEY") or not model:
        raise SystemExit("Source the protected qwen.env file first.")

    sys.path.insert(0, args.system_root)
    from ai_scientist import llm

    client, served_model = llm.create_client(model)
    content, _ = llm.get_response_from_llm(
        "Reply with exactly: AI_SCIENTIST_QWEN_OK",
        client,
        served_model,
        "Follow the user's instruction exactly.",
        temperature=0,
    )
    if content.strip() != "AI_SCIENTIST_QWEN_OK":
        raise RuntimeError(f"Unexpected response: {content!r}")

    if args.version == "v1":
        assert llm.aider_model_name(model) == f"openai/{model}"

    if args.version == "v2" and args.image:
        from ai_scientist import vlm

        vlm_client, vlm_model = vlm.create_client(model)
        visual_content, _ = vlm.get_response_from_vlm(
            "Reply with exactly: AI_SCIENTIST_VLM_OK",
            args.image,
            vlm_client,
            vlm_model,
            "Follow the user's instruction exactly.",
            temperature=0,
            max_images=1,
        )
        if visual_content.strip() != "AI_SCIENTIST_VLM_OK":
            raise RuntimeError(f"Unexpected VLM response: {visual_content!r}")

    print(f"{args.version} adapted live Qwen smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
