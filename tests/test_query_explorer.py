"""Preserve query identities, denominators and explicit unscored states."""
import csv
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('query_explorer', ROOT / 'scripts/build_query_explorer.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class QueryExplorerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        for name in ('retrieval_queries.csv', 'split_manifest.csv'):
            shutil.copyfile(ROOT / 'results' / name, self.path / name)

    def edit(self, change):
        path = self.path / 'retrieval_queries.csv'
        with path.open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        fields = list(rows[0])
        change(rows)
        with path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_reference_has_every_test_query(self):
        queries, hashes = MODULE.load_results(self.path)
        self.assertEqual(len(queries), 14)
        self.assertTrue(all(r['status'] == 'eligible' for r in queries))

    def test_missing_query_is_rejected(self):
        self.edit(lambda rows: rows.pop())
        with self.assertRaisesRegex(ValueError, 'Every test'):
            MODULE.load_results(self.path)

    def test_duplicate_query_is_rejected(self):
        self.edit(lambda rows: rows.append(rows[0]))
        with self.assertRaisesRegex(ValueError, 'identity'):
            MODULE.load_results(self.path)

    def test_wrong_chance_denominator_is_rejected(self):
        self.edit(lambda rows: rows[0].update(reference_count='45'))
        with self.assertRaisesRegex(ValueError, 'Chance reference'):
            MODULE.load_results(self.path)

    def test_ineligible_score_is_not_coerced_to_zero(self):
        self.edit(lambda rows: rows[0].update(status='zero_query_vector', average_precision='0'))
        with self.assertRaisesRegex(ValueError, 'missing outcomes'):
            MODULE.load_results(self.path)

    def test_explicit_empty_gallery_preserves_zero_counts_and_missing_score(self):
        def change(rows):
            rows[0].update(status='no_references_after_exclusions', reference_count='0', positive_reference_count='0',
                           average_precision='', random_ap_expectation='', random_top1_expectation='', top1_correct='', nearest_compound='')
        self.edit(change)
        queries, _ = MODULE.load_results(self.path)
        self.assertEqual(queries[0]['reference_count'], 0)
        self.assertEqual(queries[0]['average_precision'], '')

    def test_nonfinite_ap_is_rejected(self):
        self.edit(lambda rows: rows[0].update(average_precision='nan'))
        with self.assertRaisesRegex(ValueError, 'finite'):
            MODULE.load_results(self.path)
