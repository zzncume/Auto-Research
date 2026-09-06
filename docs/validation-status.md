# Validation status

Validated on the isolated experiment host on 2026-09-05/06.

| Route | Result | Observed model | Usage |
|---|---|---|---|
| OpenAI-compatible text endpoint | Passed | `qwen3.8-max` | 72 input, 19 output tokens |
| OpenAI-compatible image endpoint | Passed | `qwen3.8-max` | 1070 input, 29 output tokens |
| AI-Scientist v1 adapted text route | Passed | `qwen3.8-max` | Transport-level smoke |
| AI-Scientist v2 adapted text and VLM routes | Passed | `qwen3.8-max` | Transport-level smoke |
| Arbor native LiteLLM route | Passed | `qwen3.8-max` | 70 input, 36 output tokens |
| ARIS-Code v0.4.24 native executor route | Passed | `qwen3.8-max` | 8381 input, 16 output tokens |

The tests above prove connectivity and request/response compatibility only. They do
not establish that a full autonomous research run will complete successfully.

Arbor initially failed before making an API request because an unconstrained editable
install had resolved LiteLLM 1.99.0 under Python 3.10. The deployed Arbor revision's
official `uv.lock` pins LiteLLM 1.89.0. Restoring that locked version fixed the import
failure and the native live request passed.

ARIS-Code's project-local skill pack is installed inside its Qwen workspace. The
executor and HTTP reviewer are both mapped to Qwen by benchmark policy. Same-family
review remains an explicitly reported deviation from ARIS's cross-family invariant.
