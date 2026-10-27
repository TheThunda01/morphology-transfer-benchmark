"""Display every saved retrieval query with its own chance reference and denominator."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {'eligible', 'no_references_after_exclusions', 'no_positive_references_after_exclusions', 'zero_query_vector'}


def load_results(directory: Path) -> tuple[list[dict], dict]:
    loaded = {}
    fingerprints = {}
    for name in ('retrieval_queries.csv', 'split_manifest.csv'):
        path = directory / name
        fingerprints[name] = hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        with path.open(encoding='utf-8-sig', newline='') as handle:
            loaded[name] = list(csv.DictReader(handle))
    assignments = {}
    for row in loaded['split_manifest.csv']:
        if row['group'] in assignments or row['split'] not in {'train', 'validation', 'test'}:
            raise ValueError('Duplicate identity or unsupported split')
        assignments[row['group']] = row
    tests = {key for key, row in assignments.items() if row['split'] == 'test'}
    training = Counter(row['moa'] for row in assignments.values() if row['split'] == 'train')
    seen = set()
    queries = []
    for raw in loaded['retrieval_queries.csv']:
        group = raw['group']
        if group in seen or group not in tests or raw['moa'] != assignments[group]['moa']:
            raise ValueError('Query identity or annotation does not match the test split')
        seen.add(group)
        n, m = int(raw['reference_count']), int(raw['positive_reference_count'])
        status = raw['status']
        if status not in STATUSES or not (0 <= m <= n <= sum(training.values())) or m > training[raw['moa']]:
            raise ValueError('Invalid reference counts or query status')
        row = dict(raw, reference_count=n, positive_reference_count=m)
        if status == 'eligible':
            if not 0 < m <= n or raw['top1_correct'] not in {'True', 'False'} or not raw['nearest_compound']:
                raise ValueError('Eligible query lacks support or top-1 outcome')
            for field in ('average_precision', 'random_ap_expectation', 'random_top1_expectation'):
                row[field] = float(raw[field])
                if not math.isfinite(row[field]) or not 0 <= row[field] <= 1:
                    raise ValueError('Retrieval probabilities must be finite and within [0, 1]')
            harmonic = sum(1 / i for i in range(1, n + 1))
            expected = 1.0 if n == 1 else harmonic / n + (m - 1) * (n - harmonic) / (n * (n - 1))
            if not math.isclose(row['random_ap_expectation'], expected, abs_tol=1e-12) or not math.isclose(row['random_top1_expectation'], m / n, abs_tol=1e-12):
                raise ValueError('Chance reference disagrees with its query denominator')
        else:
            if any(raw[field] for field in ('average_precision', 'random_ap_expectation', 'random_top1_expectation', 'top1_correct', 'nearest_compound')):
                raise ValueError('Ineligible queries must retain missing outcomes, not invented scores')
            if status == 'no_references_after_exclusions' and n != 0:
                raise ValueError('No-reference status contradicts its denominator')
            if status == 'no_positive_references_after_exclusions' and not (n > 0 and m == 0):
                raise ValueError('No-positive status contradicts its denominator')
            if status == 'zero_query_vector' and not (n >= m > 0):
                raise ValueError('Zero-vector status contradicts its denominator')
        queries.append(row)
    if not tests or seen != tests:
        raise ValueError('Every test identity must be represented exactly once')
    return queries, fingerprints


def render(queries: list[dict], fingerprints: dict, output: Path) -> None:
    import plotly
    import plotly.graph_objects as go

    eligible = [r for r in queries if r['status'] == 'eligible']
    figure = go.Figure()
    for row in eligible:
        label = html.escape(row['compound'])
        figure.add_trace(go.Scatter(x=[row['random_ap_expectation'], row['average_precision']], y=[label, label],
            mode='lines', line=dict(color='#b9c5ce', width=3), showlegend=False, hoverinfo='skip'))
    for field, label, color, symbol in (
        ('random_ap_expectation', 'Random-order expectation', '#64748b', 'circle-open'),
        ('average_precision', 'Observed cosine retrieval', '#176b87', 'diamond'),
    ):
        custom = [[html.escape(r['moa']), r['positive_reference_count'], r['reference_count'], html.escape(r['nearest_compound']), r['top1_correct'], html.escape(r['group'])] for r in eligible]
        figure.add_trace(go.Scatter(x=[r[field] for r in eligible], y=[html.escape(r['compound']) for r in eligible], mode='markers', name=label,
            marker=dict(color=color, symbol=symbol, size=12, line=dict(width=2)), customdata=custom,
            hovertemplate='%{y}<br>AP %{x:.4f}<br>Annotation: %{customdata[0]}<br>Positive / total references: %{customdata[1]} / %{customdata[2]}<br>Nearest: %{customdata[3]}<br>Top-1 annotation match: %{customdata[4]}<br>Identity: %{customdata[5]}<extra>' + label + '</extra>'))
    figure.update_layout(template='plotly_white', width=1180, height=max(725, len(eligible) * 36 + 305),
        title=f'Retrieval depends on the query: {len(eligible)} / {len(queries)} eligible',
        font=dict(family='Arial', size=14), margin=dict(l=180, r=50, t=85, b=180),
        legend=dict(orientation='h', y=-0.12, yanchor='top'), xaxis=dict(title='Average precision (AP)', range=[0, 1.02]),
        yaxis=dict(title='', categoryorder='array', categoryarray=[html.escape(r['compound']) for r in reversed(eligible)]))
    figure.add_annotation(x=0, y=-0.24, xref='paper', yref='paper', xanchor='left', yanchor='top', showarrow=False, align='left', font=dict(size=12),
        text='Query-specific chance expectations are not confidence intervals. Annotation similarity does not establish mechanism.<br>Identity and shared-plate-map exclusions remain; unscored queries stay in the HTML table.')
    if not eligible:
        figure.add_annotation(text='No eligible queries; inspect the status table below.', xref='paper', yref='paper', x=0.5, y=0.5, showarrow=False)
    caption = ('Each connector compares observed average precision with the complete-random-ranking expectation for that query’s retained gallery. '
        'Own-identity and shared-plate-map exclusions remain in force. The random expectation is not a confidence interval or a biological null test. '
        'An annotation match does not demonstrate a molecular target or mechanism. Ineligible queries remain in the table and are not plotted as zero. '
        'The chart preserves saved query order and shows no classifier results; no model was refit.')
    columns = ['compound', 'moa', 'reference_count', 'positive_reference_count', 'status', 'average_precision', 'random_ap_expectation', 'nearest_compound', 'top1_correct']
    headers = ['Query compound', 'Annotation', 'References', 'Positive references', 'Status', 'AP', 'Random expected AP', 'Nearest compound', 'Top-1 match']
    table = '<table><thead><tr>' + ''.join('<th>' + text + '</th>' for text in headers) + '</tr></thead><tbody>'
    for row in queries:
        table += '<tr>' + ''.join('<td>' + html.escape(f'{row[c]:.5f}' if isinstance(row[c], float) else ('Not scored' if row[c] == '' else str(row[c]))) + '</td>' for c in columns) + '</tr>'
    table += '</tbody></table>'
    output.mkdir(parents=True, exist_ok=True)
    fragment = figure.to_html(full_html=False, include_plotlyjs=True, div_id='retrieval-query-explorer', config={'displaylogo': False, 'responsive': True})
    content = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Morphology retrieval queries</title><style>body{font:16px/1.55 Arial,sans-serif;margin:24px auto;max-width:1250px;padding:0 20px;color:#20303c}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:8px;text-align:left;border-bottom:1px solid #ccd6df}pre{white-space:pre-wrap;font-size:12px}</style><h1>Inspect every retrieval query</h1><p>' + caption + '</p>' + fragment + '<h2>All query outcomes</h2>' + table + '<h2>Source fingerprints (LF-normalized SHA-256)</h2><pre>' + html.escape(json.dumps(fingerprints, indent=2)) + '</pre></html>'
    (output / 'query-explorer.html').write_text(content, encoding='utf-8')
    figure.write_image(str(output / 'query-explorer.png'), scale=1.5)
    (output / 'source-manifest.json').write_text(json.dumps({'schema_version': 1, 'plotly_version': plotly.__version__, 'source_sha256_lf_normalized': fingerprints, 'queries': len(queries), 'eligible': len(eligible), 'scope': caption}, indent=2) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results-dir', type=Path, default=ROOT / 'results')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'docs/figures/query-explorer')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    queries, fingerprints = load_results(args.results_dir)
    if not args.check_only:
        render(queries, fingerprints, args.output_dir)
    print(json.dumps({'queries': len(queries), 'eligible': sum(r['status'] == 'eligible' for r in queries), 'validated': True}))


if __name__ == '__main__':
    main()
