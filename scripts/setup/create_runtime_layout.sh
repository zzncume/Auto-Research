#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ASSETS_ROOT="${AUTO_RESEARCH_ASSETS_ROOT:-/home/user/projects/autoresearch}"
MATRIX_ROOT="$ASSETS_ROOT/experiments"
PROMPT="$REPO_ROOT/prompts/unified_research_brief_en_260904_simplified.md"

test -f "$PROMPT"
mkdir -p "$MATRIX_ROOT"

for system in ai-scientist-v1 ai-scientist-v2 arbor aris-code; do
  for provider in deepseek qwen gpt; do
    cell="$MATRIX_ROOT/$system/$provider"
    mkdir -p "$cell/workspace/inputs" "$cell/runs" "$cell/logs" "$cell/local-config"
    if [[ ! -e "$cell/workspace/inputs/RESEARCH_BRIEF.md" ]]; then
      install -m 0444 "$PROMPT" "$cell/workspace/inputs/RESEARCH_BRIEF.md"
    fi
    if [[ ! -e "$cell/local-config/config.example.json" ]]; then
      install -m 0444 "$REPO_ROOT/configs/$system/$provider/config.example.json" \
        "$cell/local-config/config.example.json"
    fi
  done
done

printf 'runtime_matrix=%s\n' "$MATRIX_ROOT"
find "$MATRIX_ROOT" -mindepth 2 -maxdepth 2 -type d | sort
