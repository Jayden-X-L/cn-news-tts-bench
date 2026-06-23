#!/usr/bin/env python3
"""Score a model from fixed ASR transcripts using target-level voting."""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


FINAL_LABELS = ("correct", "wrong", "unknown")


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", "" if value is None else str(value))
    text = text.upper()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，。！？、：；,.!?;:“”\"'‘’（）()\[\]{}《》<>〈〉·•/\\|_+=~`]", "", text)
    return text


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_dataset(path: Path) -> dict[str, dict]:
    records = {}
    for row in load_jsonl(path):
        records[str(row["id"])] = row
    return records


def load_asr_results(path: Path) -> dict[str, dict[str, str]]:
    results: dict[str, dict[str, str]] = {}
    for row in load_jsonl(path):
        sid = str(row["id"])
        asr = row.get("asr")
        if not isinstance(asr, dict):
            raise ValueError(f"ASR row {sid!r} must contain object field 'asr'")
        results[sid] = {str(k): str(v or "") for k, v in asr.items()}
    return results


def match_one(transcript: str, positives: list[str], negatives: list[str]) -> tuple[str, str]:
    text = normalize_text(transcript)
    negs = sorted({normalize_text(x) for x in negatives if str(x).strip()}, key=len, reverse=True)
    poss = sorted({normalize_text(x) for x in positives if str(x).strip()}, key=len, reverse=True)
    for pattern in negs:
        if pattern and pattern in text:
            return "wrong", pattern
    for pattern in poss:
        if pattern and pattern in text:
            return "correct", pattern
    return "unknown", ""


def vote(decisions: list[str]) -> str:
    counts = Counter(decisions)
    if counts["correct"] >= 2:
        return "correct"
    if counts["wrong"] >= 2:
        return "wrong"
    return "unknown"


def safe_div(num: int | float, den: int | float) -> float:
    return float(num) / float(den) if den else 0.0


def summarize(rows: list[dict], model_id: str, asr_names: list[str]) -> dict:
    auto_rows = [r for r in rows if r["auto_evaluable"]]
    total = len(auto_rows)
    counts = Counter(r["final_decision"] for r in auto_rows)
    correct = counts["correct"]
    wrong = counts["wrong"]
    unknown = counts["unknown"]
    resolved = correct + wrong
    disagreement = sum(1 for r in auto_rows if r["asr_disagreement"])

    category_stats: dict[str, dict] = {}
    for key_name in ["category", "group", "domain"]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in auto_rows:
            grouped[str(row[key_name])].append(row)
        category_stats[key_name] = {}
        for key, subset in sorted(grouped.items()):
            c = Counter(r["final_decision"] for r in subset)
            category_stats[key_name][key] = {
                "targets": len(subset),
                "correct": c["correct"],
                "wrong": c["wrong"],
                "unknown": c["unknown"],
                "strict_auto_accuracy": round(safe_div(c["correct"], len(subset)), 6),
                "unknown_rate": round(safe_div(c["unknown"], len(subset)), 6),
            }

    return {
        "model_id": model_id,
        "asr_names": asr_names,
        "total_auto_evaluable_targets": total,
        "correct": correct,
        "wrong": wrong,
        "unknown": unknown,
        "strict_auto_accuracy": round(safe_div(correct, total), 6),
        "resolved_accuracy": round(safe_div(correct, resolved), 6),
        "coverage": round(safe_div(resolved, total), 6),
        "unknown_rate": round(safe_div(unknown, total), 6),
        "asr_disagreement_rate": round(safe_div(disagreement, total), 6),
        "optional_targets_excluded": sum(1 for r in rows if not r["auto_evaluable"]),
        "breakdowns": category_stats,
    }


def score(dataset: dict[str, dict], asr_results: dict[str, dict[str, str]], model_id: str) -> tuple[list[dict], dict]:
    asr_names = sorted({name for per_sample in asr_results.values() for name in per_sample.keys()})
    if len(asr_names) < 3:
        raise ValueError(f"expected at least 3 ASR systems, got {asr_names}")

    out_rows: list[dict] = []
    for sample_id, sample in sorted(dataset.items()):
        transcripts = asr_results.get(sample_id, {})
        for i, target in enumerate(sample.get("targets", []), 1):
            target_id = str(target.get("target_id") or f"{sample_id}_t{i}")
            auto_evaluable = bool(target.get("auto_evaluable", True))
            decisions = []
            matches = {}
            for asr_name in asr_names:
                decision, matched = match_one(
                    transcripts.get(asr_name, ""),
                    list(target.get("positive_readings", [])),
                    list(target.get("negative_readings", [])),
                )
                decisions.append(decision)
                matches[asr_name] = {
                    "decision": decision,
                    "matched": matched,
                }
            final_decision = vote(decisions) if auto_evaluable else "excluded"
            distinct = {d for d in decisions}
            out_rows.append({
                "model_id": model_id,
                "sample_id": sample_id,
                "target_id": target_id,
                "domain": sample.get("domain", ""),
                "span": target.get("span", ""),
                "category": target.get("category", ""),
                "group": target.get("group", "other"),
                "auto_evaluable": auto_evaluable,
                "final_decision": final_decision,
                "asr_disagreement": auto_evaluable and len(distinct) > 1,
                "asr_decisions_json": json.dumps(matches, ensure_ascii=False, sort_keys=True),
            })
    summary = summarize(out_rows, model_id, asr_names)
    return out_rows, summary


def write_target_scores(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "model_id",
        "sample_id",
        "target_id",
        "domain",
        "span",
        "category",
        "group",
        "auto_evaluable",
        "final_decision",
        "asr_disagreement",
        "asr_decisions_json",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_breakdown_csv(path: Path, summary: dict, breakdown_name: str) -> None:
    rows = summary["breakdowns"].get(breakdown_name, {})
    with path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["name", "targets", "correct", "wrong", "unknown", "strict_auto_accuracy", "unknown_rate"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for name, stats in rows.items():
            writer.writerow({"name": name, **stats})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--asr-results", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("results/per_model"))
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)
    asr_results = load_asr_results(args.asr_results)
    missing = sorted(set(dataset) - set(asr_results))
    if missing:
        raise SystemExit(f"missing ASR results for {len(missing)} samples; first few: {missing[:5]}")

    target_rows, summary = score(dataset, asr_results, args.model_id)
    model_dir = args.output_dir / args.model_id
    model_dir.mkdir(parents=True, exist_ok=True)
    write_target_scores(model_dir / "target_scores.csv", target_rows)
    write_breakdown_csv(model_dir / "category_scores.csv", summary, "category")
    write_breakdown_csv(model_dir / "group_scores.csv", summary, "group")
    write_breakdown_csv(model_dir / "domain_scores.csv", summary, "domain")
    (model_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

