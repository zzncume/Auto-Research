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
- Qwen is the active first provider (`qwen3.8-max`); DeepSeek and GPT are deferred.
- Minimal, reviewable Qwen transport patches are included for AI-Scientist v1/v2.
  They route every model-calling stage to the same configured model and do not
  change the research goal or scientific search logic.
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

1. Copy `secrets.example/qwen.env.example` outside the repository and fill the key.
2. Export the protected environment file for the selected run.
3. Apply and verify the matching adapter patch in an isolated runtime copy.
4. Freeze the protocol and tag the repository (for example, `protocol-v1.0`).
5. Run `python scripts/validate_repository.py`.
6. Create an immutable run directory with `python scripts/new_run.py --config ...`.

See `docs/api-compatibility.md`, `docs/experiment-protocol.md`, and
`docs/reproducibility.md` before starting paid API experiments. Exact key-loading and
smoke-test steps are in `docs/qwen-setup.md`.

## License

Original harness code and documentation in this repository are licensed under
Apache-2.0. Upstream projects retain their own licenses; see `THIRD_PARTY.md`.
This license does not relicense upstream code, weights, datasets, or checkpoints.
