"""Keep the presentation-only legacy correction narrow during comparison."""
import unittest

from scripts.check_reproduction import comparable_metadata, equivalent


class LegacyWordingTests(unittest.TestCase):
    def test_only_documented_legacy_wording_is_equivalent(self):
        legacy = {'neural_model': 'Not fitted: only a small number of independent compounds per class', 'score': 0.5}
        current = {'neural_model': 'Not fitted: only a small number of distinct compound groups per class', 'score': 0.5}
        self.assertTrue(equivalent(comparable_metadata(legacy), comparable_metadata(current)))
        self.assertIn('independent', legacy['neural_model'])
        current['neural_model'] = 'A different model was fitted'
        self.assertFalse(equivalent(comparable_metadata(legacy), comparable_metadata(current)))

    def test_numerical_changes_still_fail(self):
        legacy = {'neural_model': 'Not fitted: only a small number of independent compounds per class', 'score': 0.5}
        changed = {'neural_model': 'Not fitted: only a small number of distinct compound groups per class', 'score': 0.7}
        self.assertFalse(equivalent(comparable_metadata(legacy), comparable_metadata(changed)))
