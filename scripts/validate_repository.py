#!/usr/bin/env python3
"""Validate the public harness without importing third-party packages."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ("ai-scientist-v1", "ai-scientist-v2", "arbor", "aris-code")
PROVIDERS = ("deepseek", "qwen", "gpt")
EXPECTED_KEY_ENV = {
    "deepseek": "DEEPSEEK_API_KEY",
    "qwen": "DASHSCOPE_API_KEY",
    "gpt": "OPENAI_API_KEY",
}
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    re.compile(r'"(?:api_key|token|password)"\s*:\s*"(?!FILL_|\$\{)[^"\s]{8,}"', re.I),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    configs: list[Path] = []
    for system in SYSTEMS:
        for provider in PROVIDERS:
            path = ROOT / "configs" / system / provider / "config.example.json"
            configs.append(path)
            if not path.is_file():
                fail(f"missing matrix cell: {path.relative_to(ROOT)}", errors)
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                fail(f"invalid JSON {path.relative_to(ROOT)}: {exc}", errors)
                continue
            if data.get("system") != system or data.get("provider") != provider:
                fail(f"identity mismatch: {path.relative_to(ROOT)}", errors)
            if data.get("api_key_env") != EXPECTED_KEY_ENV[provider]:
                fail(f"wrong key env: {path.relative_to(ROOT)}", errors)
            execution = data.get("execution", {})
            if execution.get("budget_policy") != "no_hard_cap":
                fail(f"budget policy drift: {path.relative_to(ROOT)}", errors)
            if execution.get("record_usage") is not True or execution.get("record_failed_requests") is not True:
                fail(f"usage accounting disabled: {path.relative_to(ROOT)}", errors)
            if "api_key" in data:
                fail(f"literal api_key field forbidden: {path.relative_to(ROOT)}", errors)

    lock_path = ROOT / "upstream" / "versions.lock.json"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        for component in lock.get("components", []):
            if not re.fullmatch(r"[0-9a-f]{40}", component.get("revision", "")):
                fail(f"invalid upstream revision: {component.get('id')}", errors)
            if not re.fullmatch(r"[0-9a-f]{64}", component.get("source_archive_sha256", "")):
                fail(f"invalid source hash: {component.get('id')}", errors)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid upstream lock: {exc}", errors)

    prompt = ROOT / "prompts" / "unified_research_brief_en_260904_simplified.md"
    if not prompt.is_file():
        fail("canonical public prompt missing", errors)

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.stat().st_size > 10 * 1024 * 1024:
            fail(f"file exceeds 10 MiB public-repo limit: {path.relative_to(ROOT)}", errors)
        if path.suffix.lower() in {".md", ".json", ".py", ".sh", ".yaml", ".yml", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    fail(f"possible secret in {path.relative_to(ROOT)}", errors)

    if errors:
        print("repository validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"repository validation passed: {len(configs)} matrix cells")
    if prompt.is_file():
        print(f"prompt_sha256={sha256(prompt)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
