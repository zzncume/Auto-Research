# ARIS + DeepSeek preparation

Executor and reviewer use `deepseek-flash` at the official `https://api.deepseek.com` endpoint. The trusted launcher reads one local `DEEPSEEK_API_KEY` assignment; it never exposes the provider key to the research sandbox. The public matrix example uses the generic adapter variable; it is not the credential file consumed by the formal launcher.

Use the original ARIS v0.4.24 binary for this profile. The Qwen reviewer-timeout compatibility binary and its 1200-second override are not applied to DeepSeek. Original reviewer timeout: 180 seconds, with original retry policy. ARIS's native OpenAI-compatible executor and custom reviewer transports are used through the existing audited gateway. ARIS's interactive DeepSeek setup instead advertises its Anthropic endpoint; this formal transport choice is explicit and does not use that setup preset.

Preserve approved pipeline options: AUTO_WRITE=true, CODE_REVIEW=true, BASE_REPO=false, VENUE=CVPR. AUTO_WRITE and VENUE are approved task choices, not upstream defaults. Review loops retain original limits of 4 research-review rounds and 2 paper-improvement rounds. Frozen brief/data/seed/baseline/template inputs remain read-only and are mounted into each new run.

The outer formal limit is 36 hours. This ARIS version exposes no corresponding whole-pipeline time-budget setting in its CLI or research-pipeline constants. Do not claim that ARIS automatically wraps up at 36 hours; expiry is an external stop, not native completion. Arbor's separate native time-budget binding must continue matching its outer budget.

## Optional GitHub / Hugging Face proxy

A new launch binding can select `download_proxy`:

- `direct` (code default): server network.
- `http7890`: local HTTP CONNECT proxy on 127.0.0.1:7890.
- `socks7891`: local SOCKS5 proxy on 127.0.0.1:7891.

Selection affects only GitHub/Hugging Face and their configured asset domains. Other allowed research sites use direct egress. No automatic retry/fallback is added to the research workflow. Port 7897 and inherited proxy variables are not used. The native sandbox still uses its existing local 18082 egress gateway; the trusted parent selects the external route. Live runs with this gateway disable inherited offline-only Hugging Face flags; offline verification stays offline. Existing frozen caches and materials remain read-only.

Preparation and its nonexecuting launch binding do not authorize an experiment. Choose one system and authorize its fresh launch separately. An updated binding must be hashed again before launch.
