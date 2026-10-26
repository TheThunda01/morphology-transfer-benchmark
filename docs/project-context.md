# Why this project exists

Terminology: [glossary](glossary.md). Scientific and operational choices: [assumptions](assumptions.md).

Similar cellular profiles can reflect a biological relationship or a shared experimental artifact. A compound can change cellular shape, internal organization, staining patterns, and the distribution of those measurements across a population. Morphology captures these broad responses, but their cause needs further investigation.

This project explores that question using public LINCS Cell Painting profiles from A549 cells. The original study compared morphology with gene-expression profiling and found that the assays captured partly overlapping, partly distinct information. It also described the difficulty of recovering compound mechanisms from either assay alone. Those findings motivate this benchmark; they are not results reproduced or claimed here. [Way et al., 2022](https://pubmed.ncbi.nlm.nih.gov/36395727/)

The scope is deliberately narrow: a prespecified panel of annotated mechanisms, one cell line and exposure period, and one recorded dose bin. The analysis asks whether a compound's profile retrieves other compounds with the same annotation when related identities and shared plate layouts are excluded. A learned baseline, where the retained class support permits it, asks a related question under a fixed compound-held-out split.

Interpreting a match requires attention to experimental structure. Controls help put measurements from different plates on a comparable scale, but they do not erase every batch or position effect. Repeated wells help characterize a compound; they do not create additional independent compounds. A successful match within this selected panel does not identify a new drug target or establish efficacy in a patient. [Arevalo et al., 2024](https://pubmed.ncbi.nlm.nih.gov/39095341/)

Use the repository to trace the public source data, check which compounds and queries are eligible, compare simple baselines, and examine failures alongside successes. It reports no new laboratory experiment. Start with [the biology and concepts](biology-and-concepts.md), then use [the methods](methods.md) to follow the analysis choices.
