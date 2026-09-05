# Simplified Unified Research Brief

## Research Objective

Temporally Consistent Object-Level 3D Reconstruction from Monocular Video

## Goal

Develop and evaluate a novel method that extends SAM 3D from single-image reconstruction to temporally consistent object-level 3D reconstruction from monocular RGB video. Investigate how information across frames can help maintain a coherent 3D representation of the same object over time and improve upon independent per-frame reconstruction.

## Research Task

Use the supplied CO3D and Aria Digital Twin video subsets as the main experimental data. RGB frames, per-frame object masks, and persistent instance IDs are available. Use the official SAM 3D model applied independently to each frame as the starting baseline.

Search the relevant literature and explore multiple feasible ideas before selecting a promising direction. The solution is intentionally open: you may modify or extend the supplied system and investigate simple, efficient, or unconventional approaches. Base decisions on experiments and revise the method when the evidence suggests a better direction.

Implement the proposed approach, compare it with the starting baseline, and analyze reconstruction quality, temporal behavior, practical limitations, and representative successes and failures. Include useful ablations and visualizations where appropriate. Preserve the essential code, configurations, outputs, results, and logs needed to understand and reproduce the work. Complete the research process with a clear English paper and compiled PDF that accurately report the method, experiments, findings, and limitations.
