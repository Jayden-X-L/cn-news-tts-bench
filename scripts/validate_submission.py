#!/usr/bin/env python3
"""Validate a model submission directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_CARD_FIELDS = [
    "model_id",
    "model_name",
    "organization",
    "raw_model_track",
    "external_frontend",
    "llm_rewrite",
    "ssml",
    "manual_text_fix",
]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_dataset_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                ids.add(str(json.loads(line)["id"]))
    return ids


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("submission_dir", type=Path)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--allow-subset", action="store_true")
    parser.add_argument("--skip-audio-exists", action="store_true")
    args = parser.parse_args()

    submission_dir = args.submission_dir
    errors: list[str] = []
    card_path = submission_dir / "system_card.json"
    manifest_path = submission_dir / "manifest.json"

    if not card_path.exists():
        errors.append(f"missing {card_path}")
    if not manifest_path.exists():
        errors.append(f"missing {manifest_path}")
    if errors:
        for err in errors:
            print("ERROR:", err, file=sys.stderr)
        return 1

    card = load_json(card_path)
    manifest = load_json(manifest_path)
    for field in REQUIRED_CARD_FIELDS:
        if field not in card:
            errors.append(f"system_card.json missing {field!r}")
    for flag in ["external_frontend", "llm_rewrite", "ssml", "manual_text_fix"]:
        if card.get(flag) is not False:
            errors.append(f"Raw Model Track requires {flag}=false")
    if card.get("raw_model_track") is not True:
        errors.append("Raw Model Track requires raw_model_track=true")
    if manifest.get("model_id") != card.get("model_id"):
        errors.append("manifest model_id does not match system_card model_id")

    dataset_ids = load_dataset_ids(args.dataset)
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        errors.append("manifest.items must be a non-empty list")
        items = []

    seen: set[str] = set()
    for i, item in enumerate(items, 1):
        sid = str(item.get("id", ""))
        if not sid:
            errors.append(f"manifest item {i}: missing id")
            continue
        if sid in seen:
            errors.append(f"manifest item {i}: duplicate id {sid!r}")
        seen.add(sid)
        if sid not in dataset_ids:
            errors.append(f"manifest item {i}: unknown dataset id {sid!r}")
        has_path = bool(item.get("audio_path"))
        has_url = bool(item.get("audio_url"))
        if has_path == has_url:
            errors.append(f"manifest item {i}: provide exactly one of audio_path or audio_url")
        if has_path and not args.skip_audio_exists:
            audio_path = submission_dir / str(item["audio_path"])
            if not audio_path.exists():
                errors.append(f"manifest item {i}: missing audio file {audio_path}")

    missing = sorted(dataset_ids - seen)
    extra = sorted(seen - dataset_ids)
    if extra:
        errors.append(f"manifest has {len(extra)} ids not in dataset")
    if missing and not args.allow_subset:
        errors.append(f"manifest is missing {len(missing)} dataset ids; first few: {missing[:5]}")

    if errors:
        for err in errors:
            print("ERROR:", err, file=sys.stderr)
        return 1

    print(json.dumps({
        "submission_dir": str(submission_dir),
        "model_id": card.get("model_id"),
        "dataset_items": len(dataset_ids),
        "manifest_items": len(items),
        "status": "ok",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

