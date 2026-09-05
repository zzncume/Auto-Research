# Provider matrix

`status: prepared` currently applies only to the four Qwen cells. DeepSeek and GPT
cells are intentionally `deferred`; their unresolved placeholders must not be used
to start a run.

Each `config.example.json` is public and contains no credential. Copy it to a
protected runtime location as `config.local.json`, replace `FILL_` values, and export
the environment variable named by `api_key_env`.

These files describe the benchmark contract. System-specific launch code translates
them into the native CLI/environment format. A template marked `requires_adapter`
must not be used for a formal run until the referenced adapter exists, is tested, and
its Git commit is recorded.
