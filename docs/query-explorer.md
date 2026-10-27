# Inspect every retrieval query

The [interactive query explorer](figures/query-explorer/query-explorer.html) shows which compounds are above or below their own random-order expectation, with each query's reference counts available on hover. Download the HTML using GitHub's **Download raw file** control and open it locally. It includes its plotting library and works without a server or network connection.

![Per-query average precision and query-specific random expectation](figures/query-explorer/query-explorer.png)

The open circle is the expected average precision of a completely random ordering of that query's retained gallery; the diamond is its observed cosine-retrieval AP. Connectors are comparisons, not uncertainty intervals. Hover identifies the annotation, positive/total reference denominator, nearest compound, top-1 outcome and identity. The HTML table retains **every** test query, including explicit unscored states.

The query order comes from the saved table; no new split or model is chosen. An annotation match does not prove a target or mechanism. Exclusion of related identities and shared plate maps remains as implemented in [Methods](methods.md). The complete-ranking random expectation is not a tie-adjusted null test.

## Input and output contract

The [builder](../scripts/build_query_explorer.py) reads `results/retrieval_queries.csv` and `results/split_manifest.csv`. Each test identity must appear exactly once with matching annotation. Reference counts must be compatible with the training set. For eligible queries, finite AP values must fall within `[0, 1]`, and the saved chance expectations must agree with the query's denominator. Unsupported statuses and inconsistent data fail explicitly.

For an ineligible query, scores, top-1 outcome and nearest compound must remain missing. Zero reference counts remain zero; absent scores are never converted to zero or silently dropped from the HTML table. Ineligible queries are omitted from the scored chart and remain in its eligibility denominator.

The builder writes `query-explorer.html`, `query-explorer.png`, and [source-manifest.json](figures/query-explorer/source-manifest.json) to `docs/figures/query-explorer/`. Source SHA-256 fingerprints normalize CRLF to LF only to handle Git text checkouts. Existing results and analysis settings are unchanged. The visualization does not process images; Fiji image-analysis validation would require actual source images and a separate protocol.

## Regenerate and verify

The input checks require only the Python standard library:

```sh
python scripts/build_query_explorer.py --check-only
python -m unittest discover -s tests -v
```

To render in a separate optional environment:

```sh
python -m venv .venv-visualization
# macOS/Linux: source .venv-visualization/bin/activate
# Windows PowerShell: .venv-visualization\Scripts\Activate.ps1
python -m pip install -r requirements-visualization.txt
python scripts/build_query_explorer.py
```

Optional rendering pins Plotly 7.1.0 and Kaleido 1.5.0. The generated HTML retains the embedded Plotly.js MIT license header. PNG output requires an existing Chrome installation; see [Plotly's official export guide](https://plotly.com/python/static-image-export/). The builder does not install Chrome. `--results-dir` accepts the same table contract from a separate run; `--output-dir` preserves the included exports by writing elsewhere. The three named outputs are overwritten in the selected directory; check the command's exit status before treating a bundle as complete.

Tests cover missing/duplicate identities, changed chance denominators, nonfinite AP, explicit empty galleries, and invalid scoring of ineligible queries. A passing check establishes the table/plot contract, not biological mechanism or transportability.
