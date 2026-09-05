#!/usr/bin/env bash
set -euo pipefail

runtime_root="${1:-/home/user/projects/autoresearch}"
repo_root="${runtime_root}/Auto-Research"

deploy_one() {
  local system_name="$1"
  local upstream_name="$2"
  local patch_name="$3"
  local target="${runtime_root}/experiments/${system_name}/qwen/workspace/system"

  if [[ -e "${target}" ]]; then
    if (cd "${target}" && git apply --reverse --check "${repo_root}/adapters/${patch_name}"); then
      echo "Verified existing isolated ${system_name}/qwen adapter workspace"
      return 0
    fi
    echo "Existing runtime copy is not the expected patched state: ${target}" >&2
    return 1
  fi
  mkdir -p "$(dirname "${target}")"
  cp -a --reflink=auto "${runtime_root}/systems/${upstream_name}" "${target}"
  (
    cd "${target}"
    git apply --check "${repo_root}/adapters/${patch_name}"
    git apply "${repo_root}/adapters/${patch_name}"
  )
  echo "Deployed isolated ${system_name}/qwen adapter workspace"
}

deploy_one \
  ai-scientist-v1 \
  ai-scientist-v1 \
  0001-adapter-add-Qwen-OpenAI-compatible-route-to-AI-Scientist-v1.patch
deploy_one \
  ai-scientist-v2 \
  ai-scientist-v2 \
  0001-adapter-add-Qwen-OpenAI-compatible-route-to-AI-Scientist-v2.patch

cp "${repo_root}/configs/ai-scientist-v2/qwen/bfts_config.qwen.yaml" \
  "${runtime_root}/experiments/ai-scientist-v2/qwen/workspace/bfts_config.qwen.yaml"

for system_name in ai-scientist-v1 ai-scientist-v2 arbor aris-code; do
  chmod u+w "${runtime_root}/experiments/${system_name}/qwen/local-config/config.example.json"
  cp "${repo_root}/configs/${system_name}/qwen/config.example.json" \
    "${runtime_root}/experiments/${system_name}/qwen/local-config/config.example.json"
  chmod 444 "${runtime_root}/experiments/${system_name}/qwen/local-config/config.example.json"
done
cp "${repo_root}/configs/arbor/qwen/research_config.qwen.yaml" \
  "${runtime_root}/experiments/arbor/qwen/workspace/research_config.qwen.yaml"
