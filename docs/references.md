# References and how they are used

Targeted checks from 21 October 2026 are recorded in the [maintenance review](review-2026-10-21.md). Earlier access dates and search records remain unchanged.

Checked on **20 October 2026**. The [reference audit](reference-audit.json) records access and metadata status for every source below. An abstract check is not a full-text appraisal. These sources support background or method choices; none independently validates this repository’s results. See the [glossary](glossary.md) and [assumptions](assumptions.md) for interpretation.

## Research and methods

- Way, G. P., et al. (2022). Morphology and gene expression profiling provide complementary information for mapping cell state. *Cell Systems, 13*(11), 911–923.e9. [doi:10.1016/j.cels.2022.10.001](https://doi.org/10.1016/j.cels.2022.10.001). [PMID: 36395727](https://pubmed.ncbi.nlm.nih.gov/36395727/). Source study’s Cell Painting/gene-expression comparison, 48-hour A549 context, usual micromolar doses, imperfect mechanism annotations and well-position effects. Complete main text was retrieved in two chunks; sections bearing on claims were inspected. Supplementary material was not comprehensively reviewed. The repository does not reproduce its full assay comparison or full feature analysis.

- Arevalo, J., et al. (2024). Evaluating batch correction methods for image-based cell profiling. *Nature Communications, 15*(1), 6516. [doi:10.1038/s41467-024-50613-5](https://doi.org/10.1038/s41467-024-50613-5). [PMID: 39095341](https://pubmed.ncbi.nlm.nih.gov/39095341/). Batch correction must consider technical mixing and preservation of biological signal across experimental contexts. Complete main text was retrieved in two chunks; sections bearing on claims were inspected. Supplementary material was not comprehensively reviewed. The JUMP benchmark does not validate this small LINCS panel or its particular normalization.

- Gustafsdottir, S. M., et al. (2013). Multiplex cytological profiling assay to measure diverse cellular states. *PLOS ONE, 8*(12), e80999. [doi:10.1371/journal.pone.0080999](https://doi.org/10.1371/journal.pone.0080999). [PMID: 24312513](https://pubmed.ncbi.nlm.nih.gov/24312513/). Multiplex cytological profiling measures diverse cell states. No direct target or activity inference is established by morphology alone.

## Data, software, standards, and reuse

- Broad Institute. (n.d.). *LINCS Cell Painting source, profiling workflow and licensing* [Dataset], 061870127481dcd73c29df85ebcfddeac2ed0828. [Source](https://github.com/broadinstitute/lincs-cell-painting/tree/061870127481dcd73c29df85ebcfddeac2ed0828). Level 3 stores annotated well aggregates; pipeline defines dose recoding; data/figures CC0 and code BSD 3-Clause. Readme and pipeline were inspected through the GitHub connector after web fetch failed. Dose field says millimoles/liter while the paper describes micromolar doses; unresolved. Full 136-object upstream raw download was not repeated.

- Broad Institute. (n.d.). *Cell Painting Gallery dataset catalog and reuse guidance* [Dataset], 4e878a31d0c730cbe8366a2522c4aab7c599a3ff. [Source](https://github.com/broadinstitute/cellpainting-gallery/tree/4e878a31d0c730cbe8366a2522c4aab7c599a3ff). Catalog identifies cpg0004-lincs and states CC0 data reuse with requested scientific attribution. Catalog is context; its whole-collection count is not the count in the specific paper or this extract.

- CellProfiler contributors. (n.d.). *CellProfiler measurement definitions* [Official documentation], 4.2.8. [Source](https://cellprofiler-manual.s3.amazonaws.com/CellProfiler-4.2.8/modules/measurement.html). Terminology for shape and intensity measurements. Reference terminology only. Historical upstream measurement settings/version are not reconstructed by this later manual; no images reprocessed.

- scikit-learn developers. (n.d.). *average_precision_score* [Official documentation], 1.8. [Source](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.average_precision_score.html). AP is a recall-weighted summary of precision, distinct from trapezoidal area.

- scikit-learn developers. (n.d.). *RandomForestClassifier* [Official documentation], 1.8. [Source](https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.RandomForestClassifier.html). Random forest estimator and tree-depth settings.
