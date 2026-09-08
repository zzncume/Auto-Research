# Verified preparation tools — not a production launcher

Canonical root: `/home/zf/projects/autoresearch`.
These tools prepare independent copies and perform CPU-only offline checks. They
are not permission to execute research, use a provider API or allocate a GPU.
The production isolation/resource and native-launch/archive integration gates
remain unverified. Candidate parameters are not frozen.

Input preparation is sequential: `prepare_inputs.py --dest <new-view>`,
`prepare_assets.py --dest <same-view>`, then `finalize_inputs.py --dest <same-view>`.
Only `common/` and the selected system's subdirectory may become visible to a
system. `operator-manifest.json`, management directories and other systems are
never mounted. The frozen brief/PDF are checked by digest. Checkpoints are a
separate read-only mount. Original inputs and source trees are not changed.

Complete v1/v2 source diffs and the minimal SAM3D environment-path patch are in
`artifacts/`. Apply them to new source copies, never to historical/frozen evidence.
`native_config.py` renders lossless mappings and model-role routing without
executing a process. `run_frames.py --validate-inputs --out_dir <unused-path>` only
checks input existence; omitting `--validate-inputs` would perform real inference
and is NOT authorized in this preparation task.

The new environments are under `envs-rebuilt/preexperiment-20260907/`.
Reinstall v1/v2 from their hash locks with `uv pip sync --require-hashes --python
<new-env>/bin/python <lock>`. Arbor uses its corrected separate `arbor.uv.lock`
with `uv sync --locked --no-dev --no-editable` in a new prepared source tree.
Do not execute or overwrite copied `envs/`.

SAM3D runtime reconstruction uses Python3.11.13 and three preserved locks:

1. `sam3d-compatible-runtime-resolved.txt` (runtime setuptools80.9.0 for existing Lightning).
2. `sam3d-final-extras-resolved.txt` (fixed official inference dependencies).
3. `sam3d-native-wheels-resolved.txt` (preserved kaolin/flash-attn and built PyTorch3D/gsplat wheels).

Use `uv pip install --require-hashes --python <new-env>/bin/python -r <lock>` for
all three in the same new environment. All local wheel URI targets and hashes
must exist; they are not included as Git blobs. Missing artifacts are errors,
not permission to fetch a different scientific version.
Then run `repair_wheel_tags.py --environment <new-env> --backup <new-operator-backup>`
once. This corrects verified upstream internal WHEEL tags for bpy/decord to their
actual official published filenames; no binary or package version is changed.
Original metadata is retained and replacement is atomic to avoid changing uv's
hardlinked package cache. CPU import/mesh/decode checks and official PyPI source
metadata are stored in the operator evidence directory.

CUDA extensions were compiled with setuptools84.0.0, GCC11 and an independent
CUDA12.1.105 toolchain before switching to runtime setuptools80.9.0. The official
NVIDIA package digests are in `artifacts/cuda-build-toolchain.json`. Builds used
2 CPU workers and explicit `-gencode=arch=compute_80,code=sm_80` for the already
specified A100. This avoids Torch's automatic-flag suppression when an include
path contains the substring `arch`. No GPU device was mounted or kernel run.
Preserved build-helper source is `artifacts/build_cuda_extensions.py`; it expects
the safely unpacked fixed source archives and CUDA toolchain under `/work` in the
offline namespace. Build outputs and toolchain receipts are server artifacts.
Runtime reinstall from the recorded wheels does not require rebuilding them.

`offline_wrapper.py` clears inherited environment, creates isolated namespaces,
mounts explicit prepared sources/new environments, and captures logs/termination.
Its CPU/RSS numbers cover bwrap only and are explicitly incomplete. They must not
be reused as production resource accounting. `local_relay.py` is only one tested
component of the future controlled transport boundary, not a network policy.

`check_readiness.py` reads actual evidence and leaves status BLOCKED when a gate
is missing. Unit tests and CLI/help checks are not native research runs.

## Parameter review versus execution (2026-09-08)

`check_parameter_review.py --dossier <operator-json> --expected-sha256 <external-hash>`
checks the offline parameter-review dossier. Its READY status is scoped to review;
it always includes the unchanged strict production readiness and missing gates.
This separates approval preparation from live verification that requires later
API/GPU/execution authorization. It does not waive production integration work.
Candidate values remain unapproved. Host cgroup/systemd deployment is optional,
not authorized, and never invoked by these tools. Project isolation retains
explicitly incomplete resource accounting; a measurement policy needs review.

`offline_lifecycle.py` adds bounded process cleanup and streamed operator logs to
the existing CPU-only wrapper. Its tests cover failure retention, separated
evidence, namespace boundaries and timeout of a detached descendant. The trusted
server-only integration captures fixed native --help invocations and verifies
their archives. This proves lifecycle plumbing, not native research-stage,
compiler, model, GPU or complete resource observation. It has no live CLI mode.
