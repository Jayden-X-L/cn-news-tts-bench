#!/usr/bin/env python3
"""Validate CN-NewsTTS Bench JSONL data without external dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


VALID_SPLITS = {"dev", "test_public", "test_hidden"}
VALID_SOURCES = {"synthetic", "rewritten_news", "licensed_news"}
VALID_DOMAINS = {
    "general",
    "sports",
    "military",
    "finance",
    "tech",
    "auto",
    "international",
    "society",
}
VALID_CATEGORIES = {
    "sports_score",
    "range_hyphen",
    "year_range",
    "military_model",
    "vehicle_model",
    "abbreviation",
    "brand_mixed",
    "unit_symbol",
    "percentage",
    "decimal_number",
    "generation_label",
    "other_auto_evaluable",
    "optional_homograph_polyphone",
}
VALID_GROUPS = {"number", "entity", "abbreviation", "unit", "polyphone", "other"}


def normalize_pattern(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.upper()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，。！？、：；,.!?;:“”\"'‘’（）()\[\]{}《》<>〈〉·•/\\|_+=~`]", "", text)
    return text


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def check_row(row: dict) -> list[str]:
    errors: list[str] = []
    prefix = f"line {row.get('_line_no', '?')} id={row.get('id', '<missing>')}: "
    for key in ["id", "split", "source", "domain", "text", "targets"]:
        if key not in row:
            errors.append(prefix + f"missing required field {key!r}")
    if row.get("split") not in VALID_SPLITS:
        errors.append(prefix + f"invalid split {row.get('split')!r}")
    if row.get("source") not in VALID_SOURCES:
        errors.append(prefix + f"invalid source {row.get('source')!r}")
    if row.get("domain") not in VALID_DOMAINS:
        errors.append(prefix + f"invalid domain {row.get('domain')!r}")
    text = row.get("text")
    if not isinstance(text, str) or not text.strip():
        errors.append(prefix + "text must be a non-empty string")
    targets = row.get("targets")
    if not isinstance(targets, list) or not targets:
        errors.append(prefix + "targets must be a non-empty list")
        return errors

    seen_target_ids: set[str] = set()
    for i, target in enumerate(targets, 1):
        tprefix = prefix + f"target[{i}]: "
        if not isinstance(target, dict):
            errors.append(tprefix + "target must be an object")
            continue
        for key in ["target_id", "span", "category", "positive_readings", "negative_readings"]:
            if key not in target:
                errors.append(tprefix + f"missing required field {key!r}")
        target_id = target.get("target_id")
        if target_id in seen_target_ids:
            errors.append(tprefix + f"duplicate target_id {target_id!r} within record")
        seen_target_ids.add(str(target_id))
        span = target.get("span")
        if isinstance(text, str) and isinstance(span, str) and span not in text:
            errors.append(tprefix + f"span {span!r} is not found in text")
        if target.get("category") not in VALID_CATEGORIES:
            errors.append(tprefix + f"invalid category {target.get('category')!r}")
        if "group" in target and target.get("group") not in VALID_GROUPS:
            errors.append(tprefix + f"invalid group {target.get('group')!r}")
        positives = target.get("positive_readings")
        negatives = target.get("negative_readings")
        if not isinstance(positives, list) or not all(isinstance(x, str) and x.strip() for x in positives):
            errors.append(tprefix + "positive_readings must be a non-empty string list")
        if not isinstance(negatives, list) or not all(isinstance(x, str) and x.strip() for x in negatives):
            errors.append(tprefix + "negative_readings must be a string list")
        if isinstance(positives, list) and isinstance(negatives, list):
            pos_norms = {normalize_pattern(x) for x in positives}
            neg_norms = {normalize_pattern(x) for x in negatives}
            for neg in sorted(neg_norms):
                if not neg:
                    continue
                for pos in sorted(pos_norms):
                    if neg == pos or (len(neg) >= 2 and neg in pos):
                        errors.append(tprefix + f"negative reading {neg!r} overlaps positive reading {pos!r}")
        if target.get("category") == "optional_homograph_polyphone" and target.get("auto_evaluable", True):
            errors.append(tprefix + "optional_homograph_polyphone must set auto_evaluable=false")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    args = parser.parse_args()

    rows = load_jsonl(args.jsonl)
    errors: list[str] = []
    seen_ids: set[str] = set()
    target_ids: set[str] = set()
    category_counts: Counter[str] = Counter()
    group_counts: Counter[str] = Counter()
    auto_targets = 0
    optional_targets = 0

    for row in rows:
        rid = row.get("id")
        if rid in seen_ids:
            errors.append(f"line {row.get('_line_no')}: duplicate id {rid!r}")
        seen_ids.add(str(rid))
        errors.extend(check_row(row))
        for target in row.get("targets", []) if isinstance(row.get("targets"), list) else []:
            tid = str(target.get("target_id"))
            if tid in target_ids:
                errors.append(f"line {row.get('_line_no')}: duplicate global target_id {tid!r}")
            target_ids.add(tid)
            category_counts[str(target.get("category"))] += 1
            group_counts[str(target.get("group", "other"))] += 1
            if target.get("auto_evaluable", True):
                auto_targets += 1
            else:
                optional_targets += 1

    if errors:
        for err in errors:
            print("ERROR:", err, file=sys.stderr)
        return 1

    print(json.dumps({
        "path": str(args.jsonl),
        "records": len(rows),
        "targets": len(target_ids),
        "auto_evaluable_targets": auto_targets,
        "optional_targets": optional_targets,
        "categories": dict(sorted(category_counts.items())),
        "groups": dict(sorted(group_counts.items())),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
