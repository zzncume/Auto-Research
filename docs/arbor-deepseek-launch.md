# Arbor + DeepSeek formal preparation

The formal launcher selects `deepseek-flash` for both the coordinator/meta model and executor model through Arbor's native LiteLLM provider. It uses the official DeepSeek endpoint via the audited local gateway. A separate local `arbor-deepseek.env` supplies `DEEPSEEK_API_KEY`; the ARIS key is not reused. The public example's generic adapter variable is not the formal launcher's credential source.

DeepSeek retains native `llm_timeout=300`, `reasoning_effort=high`, and retry defaults. The Qwen-specific 1200-second request timeout is not injected. These native request settings still need one live provider compatibility check after credentials are supplied.

The new formal binding sets both outer wall time and native `time_budget` to 129600 seconds (36 hours). Native finalization buffer remains 0.10. The native CoordinatorConfig and derived executor configuration were checked for actual model/time-budget propagation, not just the launch summary. Existing CVPR template requirements, frozen inputs, and original research settings remain in place.

The new run is separate from prior Arbor/Qwen and ARIS/DeepSeek artifacts; it is not a resume. Launch remains unauthorized until requested. The existing single-run lock remains sufficient after ARIS completion; no concurrency or host configuration change is necessary. Optional GitHub/HF proxy selection supports direct/http7890/socks7891; the prepared binding selects http7890, never 7897.
