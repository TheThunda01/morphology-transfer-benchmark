# Methods

The scientific question is deliberately narrow: within a prespecified panel, do morphological profiles place unseen related-compound groups near training compounds with the same annotation? The checked-in [configuration](../config.json) fixes the selection and model choices. No test score was used to choose classes or features.

## Selection and support gate

We start from raw annotated Level-3 well medians in LINCS Pilot1, A549 cells, 48-hour exposure, upstream dose category 6. The fixed panel contains eight mechanism labels with at least six distinct InChIKey14 groups in the annotation table. Multiple-label and unannotated treatments are excluded explicitly; the snapshot retains all DMSO controls from the inspected plates.

The 72 features are a fixed panel of nine shape measurements and three intensity summaries for each of five channels in each of three object compartments. This reduces download and inspection burden; it is not a claim to reproduce results obtained from all 1,781 source features. Neither variance nor labels were used to select this input panel.

The extracted snapshot has 410 treatment wells and 3,264 controls. One annotated group is absent at the chosen dose; another lacks three distinct replicate plates. After these gates, proteasome inhibitors have only five groups and fail the prespecified minimum of six. Their source rows stay in the input and audit but do not enter scoring. The remaining seven classes contain 76 groups. [Annotation](../results/annotation_audit.csv), [compound](../results/compound_audit.csv), and [class support](../results/class_support.csv) tables show each decision.

InChIKey14 groups collapse the supplied connectivity identifier, keeping matching identities across names, doses and replicates together. This is not a complete chemical-family or salt-normalization solution. Related but distinct structures can remain on opposite sides of a split.

## Normalization and compound profiles

For each plate and feature, subtract the DMSO median and divide by 1.4826 times its median absolute deviation. At least twelve controls are required. A missing or effectively zero scale leaves that plate-feature missing; treated wells never supply its replacement scale. This assumes negative controls on the measurement plate are available at analysis time. It is not a simulation of acquiring data without controls.

Each compound-group profile is the featurewise median across its selected replicate wells. A group needs at least three distinct plates and at most 5% missing normalized entries. The [control audit](../results/control_audit.csv) also describes plate shifts relative to pooled controls, strictly as a diagnostic; pooled-control statistics are not used to transform predictive inputs. DMSO normalization is not a guarantee that positional or batch effects disappear. The source study identified fixed-position artifacts and used additional corrections [1].

## Split and model fitting

Within each retained class, sort group identifiers, permute with seed 27182, allocate the floored 20% to test, another floored 20% to validation, and the remainder to training; each held-out portion has at least one group. At least three training identities per class are required. The resulting counts are 48/14/14. All input rows for a group inherit its one assignment.

Missingness/variance feature checks, median imputation, and StandardScaler are fitted only on training compound profiles. Validation chooses logistic C from 0.01, 0.1, 1, 10 and forest maximum depth from 2, 4; ties select the first, more regularized candidate. The forest has 150 trees and a fixed seed. Models remain fitted on training data; no refit uses validation or test labels. A prior-only classifier supplies a baseline. No neural network is fitted because independent class support is small.

## Retrieval and denominators

Each test group queries the training gallery. Remove its own InChIKey14 and every reference sharing any of its plate maps. If no reference or no same-label reference remains, the query is visibly ineligible; exclusions are never relaxed. Cosine similarity ranks remaining profiles. Average precision uses binary same-annotation relevance; deterministic identity ordering resolves top-1 score ties.

For a gallery of size n with m positives, random top-1 expectation is m/n. Expected average precision for a uniformly random complete ranking is H_n/n + (m−1)(n−H_n)/(n(n−1)), with the n=1 case handled separately. These are chance references, not biological null tests. Macro F1 weights retained classes equally; accuracy weights test groups equally.

Descriptive 95% percentile intervals resample fixed test-group outcomes 2,000 times. They omit uncertainty from training, choosing this split, measurement, annotations and chemical dependence. One test group represents 1/14 of overall accuracy. Per-class denominators are reported because some classes have only one test group.

## Interpretation

The source publication treats MOA labels as incomplete, context-sensitive annotations [1]. A class match is not proof of a direct molecular interaction. The fixed feature panel and one dose intentionally limit scope. [Metadata distribution](../results/metadata_distribution.csv) exposes shared plate maps in model evaluation; this is compound-held-out analysis, not an independent-laboratory test. See [references](references.md) for the evidence and [practical use](practical-use.md) for operational boundaries.
