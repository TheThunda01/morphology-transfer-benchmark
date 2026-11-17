import unittest

from morphology.layout_baseline import ROOT, evaluate, layout_features


class LayoutBaselineTests(unittest.TestCase):
    def test_features_exclude_identity_and_annotation(self):
        row = {"plate_maps": "p1|p2", "well_positions": "B04", "group": "secret", "moa": "label"}
        self.assertEqual(layout_features(row),
                         {"plate_maps/p1": 1, "plate_maps/p2": 1, "well_positions/B04": 1})

    def test_pinned_comparison_uses_the_same_denominators(self):
        report = evaluate(ROOT / "results")
        self.assertEqual(report["train_groups"], 48)
        self.assertEqual(report["test_groups"], 14)
        self.assertEqual(sum(report["class_support_test"].values()), 14)
        self.assertEqual(report["test_groups_with_a_training_map"], 13)
        self.assertEqual(report["scores"]["logistic"]["correct"], 7)
