#!/usr/bin/env python3
"""Aggregate per-model summaries into leaderboard files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


LEADERBOARD_FIELDS = [
    "rank",
    "model_id",
    "strict_auto_accuracy",
    "resolved_accuracy",
    "coverage",
    "unknown_rate",
    "asr_disagreement_rate",
    "correct",
    "wrong",
    "unknown",
    "total_auto_evaluable_targets",
    "optional_targets_excluded",
]


def load_summaries(per_model_dir: Path) -> list[dict]:
    summaries = []
    for path in sorted(per_model_dir.glob("*/summary.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        summaries.append(data)
    return summaries


def flatten(summary: dict) -> dict:
    return {
        "model_id": summary["model_id"],
        "strict_auto_accuracy": summary["strict_auto_accuracy"],
        "resolved_accuracy": summary["resolved_accuracy"],
        "coverage": summary["coverage"],
        "unknown_rate": summary["unknown_rate"],
        "asr_disagreement_rate": summary["asr_disagreement_rate"],
        "correct": summary["correct"],
        "wrong": summary["wrong"],
        "unknown": summary["unknown"],
        "total_auto_evaluable_targets": summary["total_auto_evaluable_targets"],
        "optional_targets_excluded": summary["optional_targets_excluded"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-model-dir", type=Path, default=Path("results/per_model"))
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    args = parser.parse_args()

    summaries = load_summaries(args.per_model_dir)
    rows = [flatten(s) for s in summaries]
    rows.sort(key=lambda r: (-r["strict_auto_accuracy"], -r["coverage"], r["unknown_rate"], r["model_id"]))
    for i, row in enumerate(rows, 1):
        row["rank"] = i

    args.results_dir.mkdir(parents=True, exist_ok=True)
    args.site_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.results_dir / "leaderboard.csv"
    json_path = args.results_dir / "leaderboard.json"
    site_json_path = args.site_dir / "leaderboard.json"

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LEADERBOARD_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "generated_by": "scripts/aggregate_leaderboard.py",
        "models": rows,
    }
    json_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    json_path.write_text(json_text, encoding="utf-8")
    site_json_path.write_text(json_text, encoding="utf-8")
    print(json.dumps({"models": len(rows), "csv": str(csv_path), "json": str(json_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

