# Arbor + DeepSeek formal preparation

The formal launcher selects `deepseek-flash` for both the coordinator/meta model and executor model through Arbor's native LiteLLM provider. It uses the official DeepSeek endpoint via the audited local gateway. A separate local `arbor-deepseek.env` supplies `DEEPSEEK_API_KEY`; the ARIS key is not reused. The public example's generic adapter variable is not the formal launcher's credential source.

DeepSeek retains native `llm_timeout=300`, `reasoning_effort=high`, and retry defaults. The Qwen-specific 1200-second request timeout is not injected. These native request settings still need one live provider compatibility check after credentials are supplied.

The new formal binding sets both outer wall time and native `time_budget` to 129600 seconds (36 hours). Native finalization buffer remains 0.10. The native CoordinatorConfig and derived executor configuration were checked for actual model/time-budget propagation, not just the launch summary. Existing CVPR template requirements, frozen inputs, and original research settings remain in place.

The new run is separate from prior Arbor/Qwen and ARIS/DeepSeek artifacts; it is not a resume. Launch remains unauthorized until requested. The existing single-run lock remains sufficient after ARIS completion; no concurrency or host configuration change is necessary. Optional GitHub/HF proxy selection supports direct/http7890/socks7891; the prepared binding selects http7890, never 7897.

## Compaction compatibility

For DeepSeek only, the runtime enables `AUTORESEARCH_ARBOR_DEEPSEEK_COMPACTION_COMPAT=1` through sitecustomize. The outbound converter omits the exact synthetic assistant acknowledgement immediately following an internal context summary. It does not remove model-generated reasoning, tool calls/results, summaries, or modify native stored history. Native two-message compaction bookkeeping remains unchanged.

A minimal live test reproduced DeepSeek's missing-reasoning HTTP 400 when continuing the same tool turn after native compaction. With the compatibility layer enabled, the next tool call and tool-result response passed. A newly inserted user turn did not reproduce that failure, so the regression specifically tests same-turn continuation. The native summarization function used a fixed summary fixture; no research experiment or large-context workload was run. Request timeout and reasoning defaults are unchanged. Old failed artifacts and approvals remain immutable; use a fresh bound launch for a future experiment.
