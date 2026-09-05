#!/usr/bin/env python3
"""Create an immutable run directory without copying credentials."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument(
        "--prompt",
        type=Path,
        default=ROOT / "prompts" / "unified_research_brief_en_260904_simplified.md",
    )
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs" / "raw")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    if "FILL_" in json.dumps(config):
        raise SystemExit("config still contains FILL_ placeholders")

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]
    run_id = f"{config['system']}-{config['provider']}-s{args.seed}-{timestamp}-{suffix}"
    run_dir = args.runs_root.resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    config_copy = run_dir / "config.json"
    prompt_copy = run_dir / "prompt.md"
    config_copy.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    prompt_copy.write_bytes(args.prompt.read_bytes())

    metadata = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at_utc": timestamp,
        "status": "prepared",
        "seed": args.seed,
        "system": config["system"],
        "provider": config["provider"],
        "model": config["model"],
        "api_key_env": config["api_key_env"],
        "harness_git_commit": git_commit(),
        "config_sha256": sha256(config_copy),
        "prompt_sha256": sha256(prompt_copy),
        "credentials_copied": False,
    }
    (run_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
