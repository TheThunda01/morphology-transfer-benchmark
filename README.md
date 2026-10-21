# Morphology transfer benchmark

**Do compounds with the same annotated mechanism produce similar cell shapes when the query compound has never been seen?**

## Why this project

Cell Painting describes cellular appearance after a perturbation. That gives chemistry a biological readout, but similarity in appearance is only indirect evidence about mechanism. This project examines that distinction using public A549 cell profiles from the LINCS experiment, with explicit compound and plate-map exclusions.

[Project background](docs/project-context.md) · [Biology and concepts](docs/biology-and-concepts.md)

## What it does

The repository packages a compact, raw-data-derived panel: 3,674 wells, including 3,264 DMSO controls, and 72 fixed shape/intensity measurements. Eight mechanism classes were selected before model scores were calculated. Seven passed the prespecified independent-compound support rule; the excluded proteasome class remains visible in the audits.

It uses control-only plate normalization, keeps related compound identities together, and assigns 76 eligible groups to fixed training, validation, and test sets. It compares cosine retrieval with a random-ranking expectation and compares prior-only, logistic, and small random-forest classifiers. It does not process images or discover new drug targets.

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
| Mean average precision of cosine retrieval | 0.463 |
| Random-order expected mean average precision | 0.224 |
| Retrieval top-1 matches | 8 / 14 |
| Prior-only classifier macro F1 | 0.050 |
| Logistic classifier macro F1 | 0.496 |
| Random forest macro F1 | 0.490 |

![Panel support, retrieval and model comparisons](results/benchmark.svg)

These are small-sample, within-panel results. One changed test prediction moves accuracy by **7.14 percentage points**. The [report](results/report.md) and [metrics](results/metrics.json) give denominators and descriptive uncertainty; the difference between learned models does not establish superiority.

## Practical use and limitations

The useful output is a traceable comparison between a morphological neighborhood and existing annotations. It can show where a proposed relationship is worth checking, where no valid reference remains, or where a simple model fails. Similarity does not demonstrate a direct target, a causal mechanism, efficacy, or safety.

The source has fixed well positions, one cell line and one exposure duration. Compound-disjoint evaluation does not remove every plate, positional, annotation, or chemistry bias. The source concentration column name conflicts with units in the publication; this analysis preserves the numerical source value and selects its documented dose category. No neural model is forced onto the small number of independent groups.

## Documentation

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

The original code is [MIT licensed](LICENSE). Public data are covered separately by the upstream [CC0 license](data/LICENSE_CC0.md). Retain the dataset and article citations when reusing this analysis. Contributions should preserve input hashes, independent identity grouping, reference exclusions, and honest denominators; see [CONTRIBUTING.md](CONTRIBUTING.md).
