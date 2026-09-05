# Reproducibility guide

Each formal run must preserve:

- harness Git commit and protocol tag;
- upstream repository revisions and source archive hashes;
- configuration and prompt SHA-256 values;
- system, executor, reviewer, and auxiliary model identifiers;
- operating system, GPU, driver, CUDA, Python, and dependency lockfiles;
- dataset manifest and split hashes;
- start/end time, random seeds, command line, exit status, and intervention log;
- input/output tokens, request count, retries, failures, and cost method;
- hashes of final papers, code patches, metrics, and representative artifacts.

Raw logs may contain sensitive values or copyrighted material. Store raw results on
the experiment host, then generate a deterministic redacted public summary. Large
public artifacts should be released through an appropriate artifact store with
checksums rather than committed directly to Git.
