# Data provenance and reuse

This is real public experimental data, not a simulation. The bundled file is a deliberately small extract of the Broad Institute LINCS Cell Painting **Pilot1** A549 profiles. We use raw annotated Level 3 well medians and preserve their selected values. We do not use the pre-normalized, feature-selected or spherized levels, whose fitted transformations could cross this benchmark's held-out compounds.

## Exact source

The source repository is [broadinstitute/lincs-cell-painting](https://github.com/broadinstitute/lincs-cell-painting/tree/061870127481dcd73c29df85ebcfddeac2ed0828), pinned at `061870127481dcd73c29df85ebcfddeac2ed0828`. Public objects are stored under the Cell Painting Gallery's `cpg0004-lincs/broad/workspace/software/lincs-cell-painting_DVC/` S3 prefix. The checked-in [manifest](../data/profiles.csv.manifest.json) lists every downloaded object's original path, full URL, byte count, MD5 and SHA-256. The upstream directory identifier is `856a0e07b38c2cdeae7822b80d8f8ee9`.

The [official profile documentation](https://github.com/broadinstitute/lincs-cell-painting/blob/061870127481dcd73c29df85ebcfddeac2ed0828/profiles/README.md) explains the aggregation levels; the [pipeline source](https://github.com/broadinstitute/lincs-cell-painting/blob/061870127481dcd73c29df85ebcfddeac2ed0828/profiles/profile_cells.py) identifies dose recoding and the fields carried into profiles. These source definitions, rather than inferred biological units, govern this extract.

| Bundled object | SHA-256 |
| --- | --- |
| `data/profiles.csv.gz` | `d2532b2484275a5c961caad3cbc77dc3072d77c02b9fbca6325b8bb91b3e9dbf` |
| `data/upstream/moa.tsv` | `fa06cb8310a5cf801f5f1ba39bf8176a1b4eefdb4a23d1739ba92be31632b6be` |
| `data/upstream/barcode_platemap.csv` | `dffd7395d0b0d92e5a12c04501b6688fc0dd7820261cd818ba12d7cd130cede2` |
| `data/upstream/dvc_manifest.json` | `eb83bc23bdb47bebe55239bc6957bd533ec4d7191bd986522f045fcf8c1ce27c` |

The normal run checks the first three hashes before analysis. It also checks the manifest's row count, the fixed feature selection, cell line and treatment dose category. The DVC directory manifest is retained for upstream object traceability, rather than required for the offline analysis.

## What was selected

The extractor examines 136 raw annotated plate objects, containing 52,223 rows. It retains 3,264 DMSO controls and 410 treatment wells from eight prespecified single-MOA classes at upstream `dose_recode=6`: **3,674 rows and 72 numeric measurements** in an 871,144-byte gzip file. The filter counters remain in the manifest; exclusions include other doses, outside-panel labels, missing labels and multiple labels. The [initial selection](../data/upstream/selection.json) records the candidate identities and 28 plate-map names before profiling scores. The full source inventory is much larger than the analyzed panel.

The 72 measurements are fixed shape and intensity summaries across Cells, Cytoplasm and Nuclei, with five staining channels. They are a tractable panel, not an optimized feature set. A row is a well-level median of source image-derived cell measurements; it is not an individual cell or a patient record. See the [data dictionary](data-dictionary.md).

The source's `Metadata_mmoles_per_liter` field is **10.0** for the selected treatment rows, whereas the paper describes the usual concentration range in micromolar units. This unresolved discrepancy is preserved explicitly. We select the upstream ordinal dose category; we do not silently convert the value or assert that its field-name unit is correct. Any absolute-dose interpretation needs reconciliation with the original experiment metadata.

## Rebuilding and licensing

After installing the pinned Python dependencies, run `python scripts/fetch_snapshot.py --output /tmp/new-profiles.csv.gz`. The optional rebuild downloads about 136 compressed raw objects, roughly 280 MB in decimal units, and caches them locally. Each object is checked against its content-addressed MD5 and recorded with SHA-256. The selected gzip output is deterministic; the provenance capture timestamp naturally changes. Normal analysis is offline and does not download these files. The full raw download cache is not part of this repository.

The official LINCS repository explicitly places **data, results and figures under CC0**, with source code separately under BSD 3-Clause. The data license is retained as [data/LICENSE_CC0.md](../data/LICENSE_CC0.md). This repository's original code is [MIT](../LICENSE); it does not relicense upstream material. Cite Way et al. and the source repository when using the data, even though CC0 does not require attribution. See [references](references.md) for the primary study and catalogue.
