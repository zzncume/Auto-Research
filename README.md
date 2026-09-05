# Auto-Research

Reproducible benchmark harness for comparing AI-Scientist v1, AI-Scientist v2,
Arbor, and ARIS-Code on the same research task with DeepSeek, Qwen, and GPT
executors.

This repository contains only orchestration code, public prompts, configuration
templates, provenance records, and evaluation tooling. It intentionally does not
contain API credentials, model checkpoints, Conda environments, datasets, gated
assets, or unfiltered run logs.

## Current status

- Four official systems are installed outside this repository on the experiment host.
- Official SAM 3D Objects and its checkpoints have passed the upstream demo.
- The 4 x 3 provider matrix is represented under `configs/`.
- Provider compatibility has been audited against the deployed official source.
- AI-Scientist v1/v2 require minimal, documented transport adapters for some routes;
  these adapters must not change research logic or prompts.
- API credentials are intentionally absent.

## Repository versus runtime assets

```text
/home/user/projects/autoresearch/
├── Auto-Research/       # this public Git repository
├── systems/             # upstream source snapshots; not tracked here
├── envs/                # isolated environments; not tracked here
├── common/              # checkpoints, caches, canonical local assets
├── secrets/             # local credentials; ignored and never committed
└── runs/                # immutable raw runs; ignored until curated
```

## Before a formal run

1. Replace `FILL_MODEL_ID` in the selected config with the exact served model ID.
2. Export the API key named by `api_key_env` from a protected local secret file.
3. Resolve every `requires_adapter` entry and record the patch commit.
4. Freeze the protocol and tag the repository (for example, `protocol-v1.0`).
5. Run `python scripts/validate_repository.py`.
6. Create an immutable run directory with `python scripts/new_run.py --config ...`.

See `docs/api-compatibility.md`, `docs/experiment-protocol.md`, and
`docs/reproducibility.md` before starting paid API experiments.

## License

The license for this benchmark repository has not yet been selected. Upstream
projects retain their own licenses; see `THIRD_PARTY.md`. Do not assume that this
repository's future license will relicense any upstream code, weights, or data.
