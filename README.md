# Morphology transfer benchmark

Can you recognize a compound’s annotated mechanism from the appearance of cells exposed to it? This benchmark uses Cell Painting measurements from A549 cells, a human lung cancer cell line, to compare compounds the model has never seen with compounds in its training set.

## Why this project

A close match can reflect the response of the cells or the arrangement of an experiment. The retrieval analysis asks whether similar profiles share an annotation after removing training examples from the same plate map. A companion classification experiment measures how much the plate map and well position can predict on their own. [Project background](docs/project-context.md) · [Biology and concepts](docs/biology-and-concepts.md) · [Portfolio guide](https://github.com/TheThunda01/TheThunda01/blob/main/PROJECT_GUIDE.md)

## What it does

The repository includes a compact panel derived from raw data: 3,674 wells, including 3,264 dimethyl sulfoxide (DMSO) solvent controls, and 72 fixed shape and intensity measurements. The panel specifies eight mechanism classes chosen before calculating model scores. Seven passed the prespecified rule for the number of distinct identities; the excluded proteasome class remains visible in the audits.

The analysis normalizes each plate using controls only, keeps related compound identities together, and assigns 76 eligible groups to fixed training, validation, and test sets. For retrieval, it ranks reference profiles using cosine similarity, which compares feature-vector directions, and compares the ranks with a random-order expectation.

For classification, it compares a class-frequency baseline with logistic regression and a small random forest. The classifier splits can share plate maps, so their scores do not measure transfer to unseen plate layouts. The analysis does not process images or discover new drug targets.

## Quick start

Use Python 3.12. The bundled analysis runs offline after installing dependencies.

```sh
python -m pip install -r requirements.txt
python -m morphology --output reproduced-results
python scripts/check_reproduction.py reproduced-results
python -m unittest discover -s tests -v
```

The optional `python scripts/fetch_snapshot.py --output /tmp/new-profiles.csv.gz` rebuilds the compact input from content-addressed public profiles. It downloads about 136 raw plate files; normal analysis does not require that download. It refuses to overwrite an existing output.

## Example results

The fixed split has **48 training, 14 validation, and 14 test groups**. All 14 test queries retain a positive training reference after excluding the same compound identity and every shared plate map.

Average precision (AP) scores the ranking of relevant references for each query; the table reports its mean across queries. Macro F1 weights each class equally when averaging class-specific F1 scores, each the harmonic mean of precision and recall.

| Readout | Checked-in result |
| --- | ---: |
| Cosine retrieval mean AP | 0.463 |
| Random-order expected mean average precision | 0.224 |
| Retrieval top-1 matches | 8 / 14 |
| Prior-only classifier macro F1 | 0.050 |
| Logistic classifier macro F1 | 0.496 |
| Random forest macro F1 | 0.490 |

![Panel support, retrieval and model comparisons](results/benchmark.svg)

These are small-sample, within-panel results. One changed test prediction moves accuracy by **7.14 percentage points**. The [report](results/report.md) and [metrics](results/metrics.json) give denominators and descriptive uncertainty; the difference between learned models does not establish superiority.

### How much can plate layout predict on its own?

Thirteen of the 14 test groups share a plate map with a training group. To measure the signal available from layout, a separate logistic regression uses only plate map and well position. It learns the category vocabulary on the 48 training groups, ignores unseen categories, and uses a fixed regularization setting (C = 1). The comparison scores the same 14 groups for all four models.

![Macro F1 on 14 groups, prior 0.050, layout only 0.095, morphology logistic 0.496 and morphology forest 0.490](examples/layout-baseline/comparison.png)

The layout model correctly classified **1 of 14 groups**, compared with 3 for the prior and 7 for morphology logistic regression. Macro F1 weights each of the seven classes equally. This diagnostic measures one type of layout signal on a small panel. Batch effects can also enter through the measured cell features.

Run `python -m morphology.layout_baseline --output reproduced-results/layout` to reproduce the chart from the frozen assignments and group audit. The [score table](examples/layout-baseline/scores.json) includes class denominators.

### Inspect the queries behind the mean

![Observed and random-expected AP for each query](docs/figures/query-explorer/query-explorer.png)

For binimetinib, six of 46 eligible reference groups shared its annotation. Its nearest reference was one of those six, and average precision reached 0.727, compared with 0.196 expected from random ordering. Taselisib had five same-annotation references among 47, yet its nearest reference carried a different annotation. These cases show why the identity and size of each query’s reference set matter. [Query rows](results/retrieval_queries.csv) · [Interactive query explorer](docs/query-explorer.md)

## Practical use and limitations

The output compares compounds with similar profiles against existing annotations. It helps identify relationships to investigate, queries that lack a valid reference, and cases where simple models fail. Similarity does not demonstrate a direct target, a causal mechanism, efficacy, or safety.

The source has fixed well positions, one cell line and one exposure duration. Holding out compound identities does not remove every plate, positional, annotation, or chemistry bias. The source concentration column name conflicts with units in the publication; this analysis preserves the numerical source value and selects its documented dose category. The small number of distinct groups also limits modeling: no neural model is fitted.

## Documentation

[Glossary](docs/glossary.md) · [Assumptions and justifications](docs/assumptions.md) · [Reference audit](docs/reference-audit.json) · [Review record, 20 October 2026](docs/review-2026-10-20.md)

[Maintenance review, 21 October 2026](docs/review-2026-10-21.md) records the Windows checkout fix, source recheck, and interpretation of legacy output labels.

| Guide | What it covers |
| --- | --- |
| [Project context](docs/project-context.md) | Biological question and rationale |
| [Biology and concepts](docs/biology-and-concepts.md) | What profiles, mechanisms and similarities mean |
| [Methods](docs/methods.md) | Selection, normalization, splits, retrieval and models |
| [Data provenance](docs/data-provenance.md) | Sources, exact version, hashes and CC0 reuse |
| [Data dictionary](docs/data-dictionary.md) | Input and output fields |
| [Practical use](docs/practical-use.md) | Contracts, failure behavior and next steps |
| [Literature review](docs/literature-review.md) | Source-to-implementation appraisal |
| [References](docs/references.md) | Primary papers and official resources |
| [Search log](docs/search-log.json) | Exact searches and access limits |

## Development and reuse

The original code is [MIT licensed](LICENSE). Public data are covered separately by the upstream [CC0 license](data/LICENSE_CC0.md). Retain the dataset and article citations when reusing this analysis. Contributions should preserve input hashes, identity grouping, reference exclusions, and honest denominators; see [CONTRIBUTING.md](CONTRIBUTING.md).
