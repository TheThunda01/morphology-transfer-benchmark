# Reading a cell's response through morphology

Terminology: [glossary](glossary.md). Scientific and operational choices: [assumptions](assumptions.md).

## What a Cell Painting profile represents

Cell Painting is a multiplex imaging assay (several readouts collected in one experiment) that captures several aspects of cellular organization in a common experiment. Fluorescent labels provide views of cellular compartments, and image analysis converts those views into numerical features such as size, shape, intensity, and texture. The resulting profile is a description of an observed cell state, rather than a direct measurement of every protein, pathway, or molecular interaction. [Gustafsdottir et al., 2013](https://pubmed.ncbi.nlm.nih.gov/24312513/)

This repository starts from published well-level numerical profiles. The upstream LINCS processing summarizes single-cell measurements within each well using medians. We therefore do not inspect individual cells or rerun segmentation here. A population summary is convenient for comparing wells, but can hide heterogeneous responses: two wells can have similar medians while containing different mixtures of cell states. The [official processing description](https://github.com/broadinstitute/lincs-cell-painting/blob/061870127481dcd73c29df85ebcfddeac2ed0828/profiles/README.md) documents that aggregation step.

The selected data come from A549, a human lung cancer-derived cell line, after a 48-hour Cell Painting exposure. This context matters. An observation in one cultured cell line at one time point is not a general account of what the compound does in every tissue. The original study also used a different exposure duration for its gene-expression assay; those measurements should not be treated as interchangeable views of an identical time point. [Way et al., 2022](https://pubmed.ncbi.nlm.nih.gov/36395727/)

## Why compare annotated mechanisms?

The requested panel spans annotations involving tubulin polymerization, topoisomerases, proteasomes, histone deacetylases, and several kinase families. The proteasome class does not meet the minimum of six distinct compound-identity groups after filtering, leaving seven classes for analysis. These labels provide a biologically motivated reference for asking whether different compounds produce related phenotypic responses. They are not direct measurements made by the microscope. A feature associated with nuclear shape, for example, is not itself a readout of topoisomerase activity.

The central hypothesis is modest: **some compounds sharing a mechanism annotation may produce sufficiently similar profiles to be retrieved together in this experimental context**. The alternative is informative too. A failed match may reflect weak measurement signal, an unsuitable exposure, technical variation, incomplete annotations, or real differences between compounds assigned the same broad label. The original LINCS analysis explicitly treats mechanism annotations as imperfect and discusses polypharmacology (effects on multiple targets) and assay-specific signals. [Way et al., 2022](https://pubmed.ncbi.nlm.nih.gov/36395727/)

A positive match therefore suggests a relationship worth investigating, not proof of a shared direct target. Different perturbations can converge on similar downstream states. Conversely, related compounds can have different observed effects because the assay samples only part of their biology. A follow-up study would need independent evidence suited to the proposed mechanism; a retrieval score alone cannot supply it.

## Dose, controls, and experimental structure

The project selects one prespecified dose-recoding bin. A dose label describes recorded treatment conditions; it does not establish equal intracellular exposure or equal biological effect across compounds. The data dictionary and methods retain the upstream fields so that the choice remains auditable. The original study found that profiling signal depended on dose, which is a reason to state this selection clearly rather than blend all treatments into one undifferentiated dataset. [Way et al., 2022](https://pubmed.ncbi.nlm.nih.gov/36395727/)

Dimethyl sulfoxide (DMSO) solvent-control wells provide a reference distribution for plate-level normalization. Centering a feature on the control median and scaling by its dispersion describes a response relative to that plate's controls. It does not turn fluorescence measurements into calibrated molecular concentrations. A feature with almost no control variation also needs careful handling: dividing by a tiny number can exaggerate a small difference.

Technical structure remains important after normalization. A physical plate, its layout, acquisition conditions, and processing history can contribute shared variation. The LINCS study documents fixed well positions across replicate layouts. Broader benchmarking likewise shows that batch correction must balance removing technical variation against preserving biological information; an apparently well-mixed representation is not sufficient evidence of success. [Way et al., 2022](https://pubmed.ncbi.nlm.nih.gov/36395727/); [Arevalo et al., 2024](https://pubmed.ncbi.nlm.nih.gov/39095341/)

## Similarity, retrieval, and transfer

Cosine similarity compares the directions of two feature vectors. After an appropriate transformation, two profiles can have high cosine similarity even when one response is larger in magnitude. That makes the transformation and feature panel part of the scientific question. A zero-length vector has no defined direction and must not quietly become an ordinary similarity score.

Retrieval asks where reference profiles with the same annotation appear in a ranked list. Its denominator includes only eligible references. Excluding the query compound prevents a trivial match to another dose or replicate of itself. Excluding shared plate maps further reduces one source of experimental overlap, though it cannot remove all confounding. A query with no eligible same-class reference cannot answer this retrieval question and should be reported as ineligible, rather than counted as a meaningful biological failure.

For learned models, the splitting and evaluation unit is the compound-identity group. This rule prevents the same supplied connectivity identity appearing in multiple splits; it does not establish that distinct groups are statistically independent. Related identifiers stay together, while transformations and tuning use development data only. Repeated measurements increase precision about the sampled compounds; they do not justify treating those wells as independent evidence of generalization. The result is a within-panel transfer benchmark, with explicit limits on what “unseen” means. Read [the methods](methods.md) for the implemented split, eligibility, and scoring rules.
