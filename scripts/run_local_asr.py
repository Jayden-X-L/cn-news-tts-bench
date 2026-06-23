#!/usr/bin/env python3
"""Run a local FunASR recognizer over generated TTS audio.

The script writes one JSONL row per (sample, TTS provider, ASR model). It is
resumable: existing successful rows are skipped.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

ASR_MODELS = {
    "sensevoice_small": {
        "model": "iic/SenseVoiceSmall",
        "trust_remote_code": True,
        "generate_kwargs": {
            "language": "zh",
            "use_itn": False,
            "batch_size_s": 60,
        },
    },
    "paraformer_zh": {
        "model": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        "generate_kwargs": {
            "use_itn": False,
            "batch_size_s": 60,
        },
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_done(path: Path, retry_errors: bool) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    done: set[tuple[str, str]] = set()
    for row in load_jsonl(path):
        if retry_errors and row.get("status") != "ok":
            continue
        done.add((str(row["tts_provider"]), str(row["id"])))
    return done


def extract_text(result: Any) -> str:
    if isinstance(result, list) and result:
        first = result[0]
        if isinstance(first, dict):
            return clean_transcript(str(first.get("text") or first.get("sentence") or ""))
        return clean_transcript(str(first))
    if isinstance(result, dict):
        return clean_transcript(str(result.get("text") or result.get("sentence") or ""))
    return clean_transcript(str(result or ""))


def clean_transcript(text: str) -> str:
    # SenseVoice returns control tags such as <|zh|><|NEUTRAL|><|Speech|>.
    return re.sub(r"<\|[^|]*\|>", "", text).strip()


def load_jobs(
    manifest_path: Path,
    providers: set[str] | None,
    sample_ids: set[str] | None,
    audio_root: Path,
) -> list[dict[str, Any]]:
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in load_jsonl(manifest_path):
        if row.get("error"):
            continue
        provider = str(row.get("provider") or "")
        case_id = str(row.get("case_id") or "")
        if not provider or not case_id:
            continue
        if providers and provider not in providers:
            continue
        if sample_ids and case_id not in sample_ids:
            continue
        if not row.get("audio_path"):
            continue
        latest[(provider, case_id)] = row

    jobs: list[dict[str, Any]] = []
    for (provider, case_id), row in sorted(latest.items()):
        rel_audio = Path(str(row["audio_path"]))
        audio_path = ROOT / rel_audio
        if not audio_path.exists():
            audio_path = audio_root / provider / f"{case_id}.wav"
        jobs.append({
            "id": case_id,
            "tts_provider": provider,
            "audio_path": audio_path,
            "audio_path_rel": str(rel_audio),
            "duration_sec": row.get("duration_sec"),
            "source_text": row.get("source_text", ""),
        })
    return jobs


def build_model(asr_id: str, device: str):
    try:
        from funasr import AutoModel
    except Exception as exc:  # pragma: no cover
        raise SystemExit("funasr is not installed in this Python environment") from exc

    cfg = ASR_MODELS[asr_id]
    kwargs = {
        "model": cfg["model"],
        "device": device,
        "disable_update": True,
    }
    if cfg.get("trust_remote_code"):
        kwargs["trust_remote_code"] = True
    return AutoModel(**kwargs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asr-id", choices=sorted(ASR_MODELS), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--audio-root", type=Path, default=ROOT / "results" / "tts_generation" / "dev" / "audio_wav_24k_mono")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--providers", nargs="*", help="Optional TTS provider ids to include.")
    parser.add_argument("--sample-ids", nargs="*", help="Optional sample ids to include.")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--retry-errors", action="store_true")
    args = parser.parse_args()

    providers = set(args.providers) if args.providers else None
    sample_ids = set(args.sample_ids) if args.sample_ids else None
    jobs = load_jobs(args.manifest, providers, sample_ids, args.audio_root)
    if args.limit:
        jobs = jobs[: args.limit]

    done = load_done(args.output, args.retry_errors)
    pending = [job for job in jobs if (job["tts_provider"], job["id"]) not in done]
    print(json.dumps({
        "asr_id": args.asr_id,
        "manifest": str(args.manifest),
        "output": str(args.output),
        "jobs": len(jobs),
        "already_done": len(jobs) - len(pending),
        "pending": len(pending),
        "device": args.device,
    }, ensure_ascii=False))
    if not pending:
        return 0

    model = build_model(args.asr_id, args.device)
    generate_kwargs = dict(ASR_MODELS[args.asr_id]["generate_kwargs"])

    for idx, job in enumerate(pending, 1):
        audio_path = Path(job["audio_path"])
        started = time.time()
        row = {
            "created_at": now_iso(),
            "id": job["id"],
            "tts_provider": job["tts_provider"],
            "asr_id": args.asr_id,
            "audio_path": job["audio_path_rel"],
            "duration_sec": job.get("duration_sec"),
            "source_text": job.get("source_text", ""),
            "text": "",
            "status": "ok",
            "error": "",
            "elapsed_sec": None,
        }
        try:
            if not audio_path.exists():
                raise FileNotFoundError(str(audio_path))
            result = model.generate(input=str(audio_path), **generate_kwargs)
            row["text"] = extract_text(result)
            if not row["text"]:
                row["status"] = "empty"
                row["error"] = "empty transcript"
        except Exception as exc:
            row["status"] = "error"
            row["error"] = f"{type(exc).__name__}: {exc}"
        row["elapsed_sec"] = round(time.time() - started, 3)
        append_jsonl(args.output, row)
        print(json.dumps({
            "idx": idx,
            "pending": len(pending),
            "id": row["id"],
            "tts_provider": row["tts_provider"],
            "status": row["status"],
            "elapsed_sec": row["elapsed_sec"],
            "text": row["text"][:80],
            "error": row["error"][:160],
        }, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
