#!/usr/bin/env python3
"""Merge per-ASR transcript JSONL files into scorer input files."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--transcripts", nargs="+", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--min-asr", type=int, default=3)
    args = parser.parse_args()

    sample_ids = [str(row["id"]) for row in load_jsonl(args.dataset)]
    grouped: dict[str, dict[str, dict[str, str]]] = defaultdict(lambda: defaultdict(dict))
    status_counts: dict[str, int] = defaultdict(int)

    for path in args.transcripts:
        for row in load_jsonl(path):
            status = str(row.get("status") or "ok")
            status_counts[status] += 1
            if status != "ok":
                continue
            tts_provider = str(row["tts_provider"])
            sample_id = str(row["id"])
            asr_id = str(row["asr_id"])
            grouped[tts_provider][sample_id][asr_id] = str(row.get("text") or "")

    summary: dict[str, Any] = {"providers": {}, "status_counts": dict(status_counts)}
    for tts_provider, by_sample in sorted(grouped.items()):
        rows: list[dict[str, Any]] = []
        missing: list[str] = []
        insufficient: list[str] = []
        for sample_id in sample_ids:
            asr = by_sample.get(sample_id, {})
            if not asr:
                missing.append(sample_id)
                continue
            if len(asr) < args.min_asr:
                insufficient.append(sample_id)
            rows.append({"id": sample_id, "asr": dict(sorted(asr.items()))})
        out_path = args.output_dir / f"{tts_provider}.asr.jsonl"
        write_jsonl(out_path, rows)
        summary["providers"][tts_provider] = {
            "output": str(out_path),
            "rows": len(rows),
            "missing": len(missing),
            "insufficient_asr": len(insufficient),
            "first_missing": missing[:5],
            "first_insufficient": insufficient[:5],
        }

    summary_path = args.output_dir / "merge_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
