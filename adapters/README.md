# Provider adapters

This directory will contain minimal, reviewable patches for API transport
compatibility. No adapter may change research behavior, prompts, search policy,
iteration counts, scientific objectives, or evaluator access.

Implemented adapters:

- `0001-adapter-add-Qwen-OpenAI-compatible-route-to-AI-Scientist-v1.patch`:
  configurable endpoint/client, Qwen model registration, Aider provider mapping,
  empty-response rejection, and removal of the fixed GPT review client.
- `0001-adapter-add-Qwen-OpenAI-compatible-route-to-AI-Scientist-v2.patch`:
  the same route for text, tree-search, write-up, citation, review, and visual-review
  stages; all stage defaults read the single configured run model.

The patches target only the pinned upstream revisions in `upstream/versions.lock.json`.
Run the no-API smoke test after applying them, then perform a one-request live smoke
test only after the user supplies a credential.
