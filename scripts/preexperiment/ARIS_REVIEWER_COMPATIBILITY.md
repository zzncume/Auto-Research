# ARIS reviewer timeout compatibility

ARIS v0.4.24's native LlmReview HTTP client uses a fixed 180-second
request timeout. In the authorized CPU diagnostic, a non-streaming Qwen review
returned after 710 seconds, after its native caller had timed out. Native
retries produced additional in-flight calls. This is not a successful review.

`aris-reviewer-timeout.patch` adds ARIS_REVIEWER_TIMEOUT_SECONDS, accepting
1–3600 seconds and retaining 180 when unset or invalid. It changes no request
body, model, prompt, review loop or research code. The diagnostic uses 1200s;
the enclosing native wall limit remains 3600s and request ceiling remains 120.
The override does not guarantee provider completion within that window.

Apply the patch to a separate copy of the pinned v0.4.24 source, preserving the
original source and binary. Build with Rust 1.98.1:

```
cargo build --locked --release -p aris-cli -j 4
cargo test --offline --locked --release -p tools reviewer_timeout_preserves_default_and_bounds_override -j 4
```

Install the resulting binary as
`tools/aris-code-v0.4.24/reviewer-timeout-compat/aris`. The diagnostic launch
approval must contain `reviewer_timeout_compatibility` with `timeout_seconds`
1200 and the exact `binary_sha256`. Staging verifies that digest before execution.
The existing formal launch still uses its original binary and settings.

Focused validation: Rust timeout default/bounds test and Python diagnostic
binary hash/task binding tests. A live full-workflow pass is still required.
Failed diagnostic evidence is preserved; operator stop reasons are recorded
outside sealed historical receipts. Client timeout does not cancel already
submitted provider work; the trusted parent drains audit records before archive
and before allowing another run. Monetary cost remains unknown without prices.

Diagnostic approvals may additionally bind `native_resume` with the prior
`source_run_id`, ARIS `native_run_id`, and exact `state_sha256`. After prior
archival completes, staging copies the original project artifacts into a fresh
workspace, verifies the unchanged task/state, and appends native
`— resume <run_id>`. It never marks a stage accepted. The native pipeline chooses
the first unaccepted phase and may revalidate it; no exact conversation resume
is claimed. The environment is freshly prepared, while prior project artifacts
and their state are retained verbatim. This path avoids discarding existing work
without treating incomplete stages as passed.
