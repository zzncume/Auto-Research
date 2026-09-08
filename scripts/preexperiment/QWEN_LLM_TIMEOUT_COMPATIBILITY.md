# Qwen API waiting-time compatibility

The user explicitly authorizes LLM API timeout adaptation for all four systems
because Qwen was slow in prior experiments. Report these interventions honestly;
they are transport compatibility settings, not native defaults or science changes.
The observed ARIS non-streaming replies took 646–904 seconds (including errors).

| System/path | Original | Current preparation |
| --- | --- | --- |
| ARIS LlmReview | fixed180s total HTTP timeout | diagnostic build1200s; default180 retained |
| AI-Scientist v1 SDK |600s read,5s connect |1200s read; connect/write/pool unchanged |
| AI-Scientist v1 Aider |600s request timeout |1200s request timeout |
| AI-Scientist v2 SDK, including tree backend |600s read,5s connect |1200s read; connect/write/pool unchanged |
| Arbor coordinator/executor |native llm_timeout300s |native config llm.llm_timeout1200s |

Python adaptation is opt-in via AUTORESEARCH_NATIVE_SYSTEM and
AUTORESEARCH_LLM_TIMEOUT_SECONDS in the isolated runtime binding. A small
sitecustomize adapter covers native Python child processes as well as the entry
process. It modifies only implicit OpenAI/AsyncOpenAI constructor read timeouts
and v1's Aider request_timeout; explicit native timeout overrides remain explicit.
Arbor uses its own configuration field and unmodified native provider factory.
ARIS uses the separately documented source patch and exact binary hash binding.
Original prepared scientific inputs and source snapshots remain unchanged.

Focused offline evidence uses the actual installed SDKs: synchronous/asynchronous
clients receive1200s read while preserving5s connect, explicit37s override and
retry count; Aider receives1200s. Arbor's native config/provider factory forwards
1200s and preserves retries, with a mocked provider (zero model calls).
Evidence is stored under admin_review/qwen-timeout-compatibility-20260908.
No v1/v2/Arbor live run is authorized by this preparation change.

Native retry counts, model/request bodies, sampling and scientific loops are
unchanged. The trusted gateway remains3600s; the native run deadline remains the
separately approved ceiling (1h diagnostic;36h formal setting). A longer wait
cannot prevent provider503s or guarantee workflow completion. Already-submitted
requests can outlive native cancellation; record them and archive after drainage.
