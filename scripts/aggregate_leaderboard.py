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


def load_site_metadata(path: Path) -> dict:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def default_model_metadata(model_id: str) -> dict:
    return {
        "name_en": model_id,
        "name_zh": model_id,
        "provider_en": "Unknown",
        "provider_zh": "Unknown",
        "api_source_en": "Unknown",
        "api_source_zh": "Unknown",
        "model": model_id,
        "voice": "unknown",
        "sample_rate": 24000,
        "audio_format": "wav",
    }


def build_site_payload(rows: list[dict], metadata: dict) -> dict:
    model_metadata = metadata.get("models", {})
    if isinstance(model_metadata, list):
        model_metadata = {item["model_id"]: item for item in model_metadata}

    first = rows[0] if rows else {}
    auto_targets = int(first.get("total_auto_evaluable_targets", 0))
    optional_targets = int(first.get("optional_targets_excluded", 0))
    benchmark = {
        "name": "CN-NewsTTS Bench",
        "split": "unknown",
        "records": 0,
        "targets": auto_targets + optional_targets,
        "auto_evaluable_targets": auto_targets,
        "optional_targets_excluded": optional_targets,
        "audio_per_model": 0,
        "raw_track": True,
    }
    benchmark.update(metadata.get("benchmark", {}))

    site_rows = []
    for row in rows:
        site_row = default_model_metadata(row["model_id"])
        site_row.update(model_metadata.get(row["model_id"], {}))
        site_row.update(row)
        site_rows.append(site_row)

    return {
        "generated_by": "scripts/aggregate_leaderboard.py",
        "version": metadata.get("version", ""),
        "benchmark": benchmark,
        "asr_ensemble": metadata.get("asr_ensemble", []),
        "models": site_rows,
        "examples": metadata.get("examples", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-model-dir", type=Path, default=Path("results/per_model"))
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    parser.add_argument("--site-metadata", type=Path, default=Path("configs/site_metadata.json"))
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
    site_payload = build_site_payload(rows, load_site_metadata(args.site_metadata))
    site_json_path.write_text(json.dumps(site_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"models": len(rows), "csv": str(csv_path), "json": str(json_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
