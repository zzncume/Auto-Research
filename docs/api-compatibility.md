# API compatibility audit

Audited against the official source snapshots recorded in
`upstream/versions.lock.json`. "Native" means the official code exposes the route;
it does not guarantee that every future model accepts legacy request parameters.

| System | GPT | DeepSeek | Qwen cloud API |
|---|---|---|---|
| AI-Scientist v1 | Conditional native OpenAI Chat Completions route for model names containing `gpt`. | Native only for the hard-coded legacy names `deepseek-chat`, `deepseek-coder`, and `deepseek-reasoner`, with a fixed DeepSeek endpoint. New model IDs require an adapter. | Not present in official source; adapter required. |
| AI-Scientist v2 | Conditional native OpenAI route for GPT/o-series names. | Official route is limited to `deepseek-coder-v2-0724` mapped to `deepseek-coder`; target cloud models require an adapter. | Official source includes local Ollama Qwen names, not DashScope cloud routing; adapter required. |
| Arbor | Native `openai-responses` route. | Native `openai-chat` route with custom base URL. | Native OpenAI-compatible route; official example uses DashScope. |
| ARIS-Code v0.4.24 | Native OpenAI executor. | Native guided setup / compatible provider route. | Native guided setup / custom OpenAI-compatible provider route. |

## Important multi-stage behavior

AI-Scientist v1 selects a main model but contains GPT-specific review calls in the
official launcher. AI-Scientist v2 exposes separate models for plot aggregation,
write-up, citation gathering, small-model drafting, and review; their defaults are
OpenAI models. A claimed "DeepSeek run" or "Qwen run" is therefore not valid until
every model-calling stage is either routed to the declared provider or explicitly
reported as a fixed auxiliary model.

AI-Scientist v2 also performs a visual paper review. If the selected executor model
cannot accept images, the protocol must either choose a separately reported, fixed
VLM for every v2 cell or disable that stage consistently. Treating a text-only model
as a drop-in VLM is not an API adapter and would invalidate the comparison.

ARIS-Code intentionally separates Executor and Reviewer. For an executor comparison,
the Reviewer provider/model must be frozen across all three ARIS runs and recorded.
Changing both simultaneously confounds the result.

## Adapter policy

Adapters may only translate provider selection, base URL, authentication variable,
model ID, request/response fields, streaming, and token-usage extraction. They must
not alter the research prompt, tool permissions, iteration policy, search access,
experimental objective, or scientific decision logic. Every adapter change must be
stored as a reviewable patch and identified in run metadata.
