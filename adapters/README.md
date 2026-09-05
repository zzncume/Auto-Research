# Provider adapters

This directory will contain minimal, reviewable patches for API transport
compatibility. No adapter may change research behavior, prompts, search policy,
iteration counts, scientific objectives, or evaluator access.

Planned adapters:

- `ai_scientist_v1_openai_compatible.patch`: configurable OpenAI-compatible endpoint,
  model allow-list removal, response validation, and usage/error logging.
- `ai_scientist_v2_openai_compatible.patch`: the same transport layer applied to all
  independently configured v2 stages, including explicit VLM capability checks.

Adapters are intentionally not fabricated before the exact served model IDs and API
contracts are selected and smoke-tested.
