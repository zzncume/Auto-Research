# Qwen first-round setup

The active served model is `qwen3.8-max`. DeepSeek and GPT are deliberately deferred.
Do not put the API key in this Git repository or in a command-line argument.

## Fill the one protected key file

The deployment creates `/home/user/projects/autoresearch/secrets/qwen.env` with mode
`600`. Open it on the server and fill only this line:

```bash
export DASHSCOPE_API_KEY='paste-your-key-here'
```

Load it into the current shell:

```bash
source /home/user/projects/autoresearch/secrets/qwen.env
test -n "$DASHSCOPE_API_KEY" && echo "Qwen key loaded"
```

The remaining variables map the same key, endpoint, and model into AI-Scientist,
Aider, ARIS-Code executor, and ARIS-Code HTTP reviewer. The key itself remains local.

## Minimal paid smoke test

After filling the key, run one small text request:

```bash
/home/user/projects/autoresearch/envs/ai-scientist-v2/bin/python \
  /home/user/projects/autoresearch/Auto-Research/scripts/smoke_test_qwen_live.py
```

To verify image input, add `--image /absolute/path/to/a/small/image.jpg`. This test
prints the requested model, returned model, response text, and token counts, but never
prints the credential.

## Native mappings

- AI-Scientist v1/v2 use their isolated patched Qwen workspaces under `experiments/`.
- Arbor uses `provider: litellm` with the per-run `research_config.qwen.yaml`; its
  `meta_model` is also `qwen3.8-max`.
- ARIS-Code uses `EXECUTOR_PROVIDER=openai` and the `ARIS_REVIEWER_*` custom HTTP
  reviewer variables. Both roles use `qwen3.8-max` for this round.

ARIS officially recommends a different-family reviewer. The one-model policy is an
intentional benchmark deviation and must be stated when interpreting its results.

## Arbor environment constraint

Use the LiteLLM version locked by the pinned Arbor source revision:

```bash
/home/user/projects/autoresearch/envs/arbor/bin/pip install \
  -c /home/user/projects/autoresearch/Auto-Research/runtime/constraints/arbor.txt \
  litellm
```

An unconstrained install may select LiteLLM 1.99.0, which imports
`typing.NotRequired` and fails under the current Python 3.10 Arbor environment.
