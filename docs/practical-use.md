# Practical use

Terminology: [glossary](glossary.md). Scientific and operational choices: [assumptions](assumptions.md).

## Where this fits

Use this repository to examine a precise question: within a small annotated compound panel, does an unseen compound's measured morphology resemble training compounds with the same label? It is useful for learning phenotype profiling, auditing label support, and checking what a simple model can infer under an explicit split. It is not a target-identification service or a decision tool for treatment, safety or compound design.

## Input and output contract

By default, the analysis uses the checked-in gzip snapshot, its JSON manifest, two exact upstream metadata tables, and `config.json`. `--data-dir` accepts another directory with that complete structure, but a compatible schema and matching manifest do not prove that experiments are comparable. The fixed source selection must agree with the configuration.

The run stops with exit code 2 for hash mismatches, malformed CSV rows, duplicate plate/well keys, unexpected cell lines or dose categories, missing identities, or insufficient control or class support.

Successful runs create `metrics.json`, a readable `report.md`, an SVG, and twelve CSV audit/result tables. `annotation_audit.csv` includes absent candidates; `compound_audit.csv` includes quality exclusions; `class_support.csv` distinguishes requested and scored classes. `retrieval_queries.csv` preserves each query's eligible reference and positive-reference counts. No references, no positives after exclusions, or a zero query vector yields an explicit ineligible status, not a zero score. The [dictionary](data-dictionary.md) defines all tables.

## Worked use case

From the repository root, install requirements and run:

```sh
python -m morphology --output reproduced-results
python scripts/check_reproduction.py reproduced-results
```

The compact snapshot yields 76 eligible compound groups in seven scored classes, split 48/14/14. Read `class_support.csv` first: the requested proteasome class has five otherwise eligible groups and does not meet the fixed six-group rule. Then inspect `retrieval_queries.csv`: all 14 test queries have positive training references even after same-identity and shared-plate-map exclusion. Mean AP is 0.463, compared with random-order expectation 0.224 for these query-specific reference sets. These values describe this panel, not an unseen class or a new laboratory.

Next compare the prior-only, logistic and random-forest rows. Their macro F1 values are 0.050, 0.496 and 0.490. The learned models' close scores and small denominators do not establish a winner. One altered test prediction changes accuracy by 7.14 percentage points. Read each class count alongside any aggregate score.

## Checks before relying on a result

Check hashes and source version, then review the initial class choice, annotation exclusions, replicate counts and feature missingness. Confirm that the intended analysis would have same-plate negative controls available. Inspect the control and metadata-distribution audits; compound separation does not eliminate fixed-position effects or all batch structure. For retrieval, verify positive reference support after both exclusions rather than relying on the overall sample count. For models, inspect the validation candidates and fixed split manifest before reading test scores.

If replacing data, reconcile feature definitions, units, concentration and exposure metadata with the new experiment. A file accepted by the parser is not evidence that its measurements are equivalent. The preserved dose-unit ambiguity must be resolved before absolute-dose comparisons.

## Known limits

The panel covers one A549 setting and a selected dose category. Its annotations can be incomplete, context-dependent or wrong, and related chemicals with distinct connectivity identities can fall in different splits. Models can share plate maps across split groups, although primary retrieval excludes them pairwise. Negative-control normalization can reduce certain shifts but cannot establish their absence.

The bootstrap intervals describe fixed held-out outcomes conditional on this analysis. They omit uncertainty from training, split choice, measurement and labels. No independent experiment validates these particular predictions.

## Next improvements

A justified next study would predeclare a second experiment or laboratory, reconcile dose units, check class support before training, and test external transfer. Richer features or learned representations would require enough independent compounds and independent validation to assess their value. Additional class selection or tuning after seeing these test results should use a new holdout and a versioned configuration, not reuse the current test set as fresh evidence.
