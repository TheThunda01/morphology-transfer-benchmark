# Morphology transfer benchmark

76 related-compound groups; 3674 retained raw wells; 72/72 training-usable features.

The fixed split contains 48 training, 14 validation, and 14 test groups. All related identities and replicate wells stay together.

Requested 8 mechanism classes; 7 pass the prespecified minimum of 6 independent groups. Inspect class_support.csv and annotation_audit.csv for all exclusions.

Retrieval: 14/14 test queries have a same-MOA training reference after both identity and plate-map exclusions. Mean AP is 0.463; random-order expected AP is 0.224. These are within-panel results.

| Model | Selected setting | Test accuracy | Test macro F1 |
| --- | --- | ---: | ---: |
| prior | prior | 0.214 | 0.050 |
| logistic | C=10 | 0.500 | 0.496 |
| random_forest | depth=2 | 0.571 | 0.490 |

![Support, retrieval, and model comparison](benchmark.svg)

Models use one fixed compound split and settings selected on validation macro F1. No neural model was fitted because class support is small. The test set is small; these estimates do not establish model superiority or broad mechanism recognition.

One changed test-group prediction moves overall accuracy by 7.14 percentage points. model_comparison.csv contains descriptive bootstrap intervals for accuracy; retrieval mean-AP intervals are in metrics.json. These resample fixed held-out compound results, assume exchangeability, and do not include uncertainty from data collection, model fitting, split choice, annotation error, or related chemistry. class_predictions.csv gives every class denominator.

Each query has an explicit eligibility record. The reference gallery contains training groups only; same identity and any shared plate map are excluded. Classifier inputs retain plate/position confounding risk despite compound separation. DMSO normalization uses negative controls on the same plates, an explicitly assumed available-at-analysis resource.

Morphology is an indirect, context-dependent phenotype. Annotated MOA can be incomplete or wrong; matches do not identify direct targets, mechanisms, drug efficacy, or clinical safety. The source dose field name and publication units disagree; the analysis uses the fixed upstream dose category and preserves original values.
