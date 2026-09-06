# Experiment protocol (draft)

This document is a draft until tagged as `protocol-v1.0`.

## Controlled task

All systems receive the same research goal and the same permissible starting
materials. Each system receives those materials through its native input mechanism;
one system's template or harness requirements are not imposed on the others.

## Comparison unit

The planned matrix contains twelve cells: four systems by three executor providers.
Each cell starts from a fresh workspace. Raw outputs are immutable, and retries create
new run IDs rather than overwriting earlier attempts.

## Provider controls

- Run one provider round at a time. Qwen is first; DeepSeek and GPT remain deferred.
- Within a run, route every auxiliary role to the same model as the main model.
- Record exact provider, endpoint class, served model ID, and response model ID.
- Record all executor and auxiliary/reviewer models.
- Do not impose a hard monetary cap; record successful, failed, and retried calls.
- Freeze temperature, reasoning effort, token settings, and retry policy where the
  system exposes them; otherwise record the native defaults.

## Evaluation controls

- Freeze the core datasets, splits, object-input protocol, baseline, and evaluator.
- Keep evaluator-only ground truth inaccessible to research agents.
- Preserve both aggregate results and category-level trade-offs.
- Additional datasets may provide supplementary evidence but cannot replace the core
  benchmark result.

## Paper format control

All systems must use the same frozen official CVPR LaTeX template. The exact CVPR
edition, anonymous review versus final mode, page limit, and supplementary-material
policy must be selected before `protocol-v1.0` is tagged. Record the template source,
version, and file hashes, and compile a no-API test PDF for every system. A system's
default ICLR, NeurIPS, or other template must not be used as its primary paper format.

## Failure accounting

Empty responses, incompatible response structures, truncation, rate limits, crashes,
manual intervention, and abandoned runs are first-class outcomes. Record the failure
stage, attempts, consumed tokens, elapsed time, and cost. Do not silently restart a
failed cell and report only the successful attempt.
