# Morphology transfer benchmark

**Do compounds with the same annotated mechanism produce similar cellular profiles when the query compound is absent from training?**

## Why this project

Cell Painting is an imaging assay that summarizes cellular appearance after a perturbation, such as a chemical treatment. That gives chemistry a biological readout, but similarity in appearance is only indirect evidence about mechanism. This project examines that distinction using public profiles from A549, a human lung cancer-derived cell line, in the Library of Integrated Network-based Cellular Signatures (LINCS) experiment. Both retrieval and classification hold out compound identities; retrieval also excludes references that share a plate map with the query.

[Project background](docs/project-context.md) · [Biology and concepts](docs/biology-and-concepts.md)

## What it does

The repository packages a compact, raw-data-derived panel: 3,674 wells, including 3,264 dimethyl sulfoxide (DMSO) solvent controls, and 72 fixed shape/intensity measurements. Eight mechanism classes were selected before model scores were calculated. Seven passed the prespecified distinct-identity support rule; the excluded proteasome class remains visible in the audits.

It uses control-only plate normalization, keeps related compound identities together, and assigns 76 eligible groups to fixed training, validation, and test sets. It ranks reference profiles using cosine similarity (similarity of feature-vector directions) and compares the ranks with a random-order expectation. It also compares a class-frequency baseline, logistic regression and a small random forest, two standard classification models. The classifier splits can share plate maps, so their scores do not measure transfer to unseen plate layouts. It does not process images or discover new drug targets.

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

| Readout | Checked-in result |
| --- | ---: |
| Mean of per-query average precision (AP; a score for the ranked relevant references) of cosine retrieval | 0.463 |
| Random-order expected mean average precision | 0.224 |
| Retrieval top-1 matches | 8 / 14 |
| Prior-only classifier macro F1 (equal-weight mean of per-class F1 scores, each the harmonic mean of precision and recall) | 0.050 |
| Logistic classifier macro F1 | 0.496 |
| Random forest macro F1 | 0.490 |

![Panel support, retrieval and model comparisons](results/benchmark.svg)

These are small-sample, within-panel results. One changed test prediction moves accuracy by **7.14 percentage points**. The [report](results/report.md) and [metrics](results/metrics.json) give denominators and descriptive uncertainty; the difference between learned models does not establish superiority.

## Practical use and limitations

The useful output is a traceable comparison between a morphological neighborhood and existing annotations. It can show where a proposed relationship is worth checking, where no valid reference remains, or where a simple model fails. Similarity does not demonstrate a direct target, a causal mechanism, efficacy, or safety.

The source has fixed well positions, one cell line and one exposure duration. Compound-disjoint evaluation does not remove every plate, positional, annotation, or chemistry bias. The source concentration column name conflicts with units in the publication; this analysis preserves the numerical source value and selects its documented dose category. No neural model is forced onto the small number of distinct groups.

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
