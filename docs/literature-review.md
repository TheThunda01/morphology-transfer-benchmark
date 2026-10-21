# Literature and practice review

## Question and scope

The question is whether morphological similarity recovers a prespecified annotation for a compound group that was absent from training, within a small, explicitly selected panel. This is a rapid review to guide an inspectable implementation. It is not a systematic review of Cell Painting, a comparison of every profiling method, or evidence that morphology identifies a compound's molecular target.

We considered public numeric profiles with enough metadata to distinguish compounds, controls, doses and experimental structure. The selected source is Broad's LINCS Pilot1 Cell Painting data: A549 cells, a 48-hour exposure, raw annotated well medians, and one recorded dose category. The source and selection are pinned separately from the literature. See [methods](methods.md), [data dictionary](data-dictionary.md), and [the source manifest](../data/profiles.csv.manifest.json).

## Search record

Searches were performed on **2026-10-20**. The [machine-readable log](search-log.json) records the exact PubMed queries, pagination, returned identifiers and access limits, plus supplementary web queries and official source inspections.

The recorded PubMed searches returned **31 unique candidate identifiers**. Three papers were retained for the implementation synthesis below. The other 28 were not carried into detailed synthesis; we do not present this as a complete abstract-by-abstract quality assessment. The broader query was paginated through all 26 reported results. Retrieval identifiers are recorded as returned, including identifiers whose publication chronology was not independently checked. No scientific claim here relies on those unretained records.

Full-text access was partial: the first 35,000 of 75,826 characters for Way et al., the first 26,000 characters for Arevalo et al., and the first 8,000 characters for Gustafsdottir et al. This is excerpt inspection, not complete article or supplement coverage. Supplementary web result totals and full rankings were not retained. The log therefore leaves their counts unknown rather than inventing a screening denominator.

## What the sources support

| Source | What it contributes here | What it does not establish |
| --- | --- | --- |
| [Gustafsdottir et al., 2013](https://pubmed.ncbi.nlm.nih.gov/24312513/), [doi:10.1371/journal.pone.0080999](https://doi.org/10.1371/journal.pone.0080999) | Primary evidence for multiplex cytological profiling as a way to measure diverse cellular responses. It supports explaining morphology as a multivariate phenotype. | A morphological feature is not a direct assay of every annotated target. This benchmark is not a replication of that paper. |
| [Way et al., 2022](https://pubmed.ncbi.nlm.nih.gov/36395727/), [doi:10.1016/j.cels.2022.10.001](https://doi.org/10.1016/j.cels.2022.10.001) | The source study compares morphology and gene-expression profiling and discusses complementary information, imperfect mechanism annotations, and fixed-position effects. It motivates a restricted question and explicit experimental-structure checks. | Its reported results cannot be transferred to this 72-feature subset, one dose category, or this compound split. Shared annotations do not prove a shared causal target. |
| [Arevalo et al., 2024](https://pubmed.ncbi.nlm.nih.gov/39095341/), [doi:10.1038/s41467-024-50613-5](https://doi.org/10.1038/s41467-024-50613-5) | A primary evaluation of batch-correction methods for image-based profiling. It supports checking technical effects while asking whether useful biological variation survives correction. | Per-plate control normalization alone is not established as sufficient for this panel, and this repository does not reproduce that comparison. |

The official [LINCS repository at the pinned commit](https://github.com/broadinstitute/lincs-cell-painting/tree/061870127481dcd73c29df85ebcfddeac2ed0828) supplies the data organization, profiling workflow and explicit reuse terms. The official [Cell Painting Gallery at the inspected commit](https://github.com/broadinstitute/cellpainting-gallery/tree/4e878a31d0c730cbe8366a2522c4aab7c599a3ff) helps place the source in its public data collection. These are data and software documentation, not peer-reviewed validation of this implementation. Original repository code and upstream data have separate licenses.

## Changes made

The review informed concrete safeguards. We retain controls and metadata alongside the compact profile matrix; normalize with same-plate DMSO controls; show control shifts, exclusions and class support; and keep the supplied related-identity groups together. Imputation, scaling and feature checks are fitted on training compounds. Retrieval excludes both matching identity groups and shared plate maps, and reports queries with no eligible positive reference instead of relaxing exclusions.

Eight mechanism labels were requested before evaluating scores. Proteasome inhibitors fail the configured minimum after filtering, leaving seven scored classes; the input rows and exclusion audit remain available. Small independent-compound support also led us to compare transparent retrieval, regularized logistic regression, a restricted random forest and a prior baseline, without adding a neural network. The papers motivate caution; they do not validate our numerical thresholds, split, feature panel or models. Those are declared implementation choices in [config.json](../config.json).

## Remaining work

Useful follow-up would inspect the complete source articles and supplements, extend the search beyond PubMed, and evaluate more than one fixed split without selecting a favorable result. An independent laboratory or held-out experimental batch would be more informative about transfer than another random compound split. Chemical-family overlap, concentration dependence, uncertain annotations and the effects of stronger batch correction also need dedicated analysis. Any expansion should set eligibility and validation rules before examining its final test results.

## Limits of this review

This is a narrow, single-pass implementation review, without duplicate screening, a formal risk-of-bias instrument, registered protocol, citation chasing or exhaustive method coverage. It combines a limited literature search with targeted official-source inspection. We report neither a pooled effect nor a general claim that this workflow is validated. The executable result answers a within-panel benchmark question under its stated assumptions; it does not establish target identity, therapeutic efficacy or transfer to unseen cell types, doses or laboratories.
