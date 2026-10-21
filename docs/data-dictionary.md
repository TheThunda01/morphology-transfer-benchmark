# Data dictionary

The source and snapshot are public experimental aggregate features, not patient records. Each input row is one physical plate/well, containing medians of single-cell measurements. Values are retained from the upstream numeric CSV; the compact input panel is selected in [config.json](../config.json).

| Input fields | Meaning |
| --- | --- |
| `Metadata_Plate`, `Metadata_Well` | Unique source well key |
| `Metadata_Plate_Map_Name` | Repeated compound layout, distinct from physical plate |
| `Metadata_Batch_Number`, `Metadata_Batch_Date` | Source batch annotations |
| `Metadata_cell_id` | A549 in this selection |
| `Metadata_broad_sample`, `Metadata_broad_id`, `Metadata_pert_iname` | Sample identifier, broad compound identifier, and supplied name |
| `Metadata_InChIKey14` | Supplied structure-connectivity key used for related-identity grouping |
| `Metadata_moa`, `Metadata_target` | Source annotations; neither is an independently measured outcome here |
| `Metadata_broad_sample_type`, `Metadata_pert_type` | Control or treatment role |
| `Metadata_mmoles_per_liter` | Original concentration-field value; its name conflicts with publication units |
| `Metadata_dose_recode` | Upstream ordinal dose category; treatment category 6 retained |
| `Cells_*`, `Cytoplasm_*`, `Nuclei_*` | Features measured within corresponding segmentation masks |

The source treatment value is exactly `10.0` for this selection. The publication describes the usual top dose as 10 μM, whereas the field name says millimoles/liter. We do not convert the field or infer potency from it. Controls can carry a nonzero recoded category despite raw concentration zero; control inclusion uses the sample label DMSO rather than the dose recode.

Shape features: Area, Perimeter, Compactness, Eccentricity, Solidity, FormFactor, Extent, MajorAxisLength, MinorAxisLength. Intensity features: MeanIntensity, MedianIntensity and StdIntensity for DNA, ER, RNA, AGP and Mito channels. Image intensity is not a calibrated protein concentration. AGP includes actin/Golgi/plasma-membrane staining contributions; channel labels are not target measurements. Empty/NA/NaN entries are missing, not zero.

| Output | Unit of analysis |
| --- | --- |
| `annotation_audit.csv` | Candidate identity in the source annotation table, including absent or excluded groups |
| `compound_audit.csv` | Observed related-compound group with replicate counts and gate status |
| `control_audit.csv` | Plate, number of DMSO controls, unusable scale counts, descriptive control shift |
| `class_support.csv` | Requested class, included/excluded status and independent group counts |
| `split_manifest.csv` | One split assignment per retained related-compound group |
| `metadata_distribution.csv` | Plate-map counts within each split |
| `retrieval_queries.csv` | Test query, reference counts, eligibility, top match and average precision |
| `validation_candidates.csv` | Validation score for each prespecified model setting |
| `model_comparison.csv`, `class_predictions.csv` | Test metrics, conditional intervals and class denominators |
| `test_predictions.csv` | Public compound-group label and prediction, not patient predictions |
| `features.csv` | Whether each fixed input feature survives training-only checks |
| `metrics.json` | Hashes, scope, denominators, settings and aggregate results |
