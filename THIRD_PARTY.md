# Third-party provenance and redistribution policy

This repository does not vendor the four research systems, SAM 3D checkpoints,
datasets, or gated model assets. Installation scripts must retrieve upstream
materials from their official locations at the revisions recorded in
`upstream/versions.lock.json`.

| Component | Upstream | Observed license | Redistribution policy here |
|---|---|---|---|
| AI-Scientist v1 | SakanaAI/AI-Scientist | AI Scientist Source Code License 1.0 | Do not vendor; preserve license and restrictions for patches/derivatives. |
| AI-Scientist v2 | SakanaAI/AI-Scientist-v2 | AI Scientist Source Code License 1.0 | Do not vendor; preserve license and restrictions for patches/derivatives. |
| Arbor | RUC-NLPIR/Arbor | Apache-2.0 | Reference pinned upstream; retain notices for copied code. |
| ARIS / ARIS-Code | wanshuiyin/Auto-claude-code-research-in-sleep | MIT | Reference pinned upstream; retain copyright/license for copied code. |
| SAM 3D Objects | facebookresearch/sam-3d-objects | SAM License (custom) | Do not upload checkpoints; follow redistribution, attribution, and use conditions. |

Dataset licenses and redistribution terms must be recorded before publishing any
sample, derived annotation, or evaluation artifact. Link to papers instead of
committing publisher PDFs unless redistribution is explicitly permitted.
