"""Measure how much classification signal comes from the recorded plate layout."""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parents[1]


def layout_features(row):
    features = {}
    for field in ("plate_maps", "well_positions"):
        for value in row[field].split("|"):
            if not value:
                raise ValueError(f"Empty category in {field}")
            features[f"{field}/{value}"] = 1
    return features


def read_rows(directory, filename):
    with (directory / filename).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def evaluate(directory):
    audit = read_rows(directory, "compound_audit.csv")
    by_group = {r["group"]: r for r in audit}
    assignments = read_rows(directory, "split_manifest.csv")
    if len(by_group) != len(audit) or len({r["group"] for r in assignments}) != len(assignments):
        raise ValueError("Group identity must be unique in each table")
    splits = {"train": [], "validation": [], "test": []}
    for row in assignments:
        item = by_group[row["group"]]
        if item["status"] != "eligible" or item["moa"] != row["moa"]:
            raise ValueError("Split and audit disagree about group eligibility or annotation")
        splits[row["split"]].append(item)

    train, test = splits["train"], splits["test"]
    labels = [row["moa"] for row in train]
    truth = [row["moa"] for row in test]
    classes = sorted(set(labels))
    if set(truth) != set(classes):
        raise ValueError("Each recorded class must appear in both partitions")
    model = make_pipeline(DictVectorizer(), LogisticRegression(C=1.0, max_iter=2000))
    model.fit([layout_features(row) for row in train], labels)
    predicted = model.predict([layout_features(row) for row in test])
    predictions = {"layout_only": list(predicted)}
    references = read_rows(directory, "test_predictions.csv")
    for name in ("prior", "logistic", "random_forest"):
        rows = [r for r in references if r["model"] == name]
        ref = {r["group"]: r for r in rows}
        if len(rows) != len(test) or set(ref) != {r["group"] for r in test}:
            raise ValueError(f"Held-out groups differ for {name}")
        if any(ref[r["group"]]["actual"] != r["moa"] for r in test):
            raise ValueError(f"Held-out annotations differ for {name}")
        predictions[name] = [ref[r["group"]]["predicted"] for r in test]
    train_maps = {m for row in train for m in row["plate_maps"].split("|")}
    return {
        "train_groups": len(train), "test_groups": len(test),
        "test_groups_with_a_training_map": sum(
            bool(train_maps.intersection(row["plate_maps"].split("|"))) for row in test),
        "class_support_test": dict(sorted(Counter(truth).items())),
        "scores": {name: {"correct": sum(a == b for a, b in zip(truth, pred)),
                          "accuracy": float(accuracy_score(truth, pred)),
                          "macro_f1": float(f1_score(truth, pred, average="macro", labels=classes, zero_division=0))}
                   for name, pred in predictions.items()},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory for scores and a comparison chart")
    out = parser.parse_args().output
    if out.exists():
        parser.error("choose a new output directory")
    result = evaluate(ROOT / "results")
    out.mkdir(parents=True)
    (out / "scores.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    names = ["prior", "layout_only", "logistic", "random_forest"]
    values = [result["scores"][name]["macro_f1"] for name in names]
    fig, ax = plt.subplots(figsize=(7.2, 3.6), layout="constrained")
    bars = ax.barh(["Prior", "Layout only", "Morphology · logistic", "Morphology · forest"],
                   values, color=["#777777", "#b15a1b", "#29697e", "#29697e"])
    ax.bar_label(bars, fmt="%.3f", padding=4)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.08)
    ax.set_xlabel("Macro F1 (equal weight per class)")
    ax.set_title(f"Same {result['test_groups']} held-out groups across classifiers", loc="left")
    fig.savefig(out / "comparison.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
