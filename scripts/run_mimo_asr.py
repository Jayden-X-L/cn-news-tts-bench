#!/usr/bin/env python3
"""Run MiMo ASR API over generated TTS audio.

The output schema matches scripts/run_local_asr.py so local and API ASR routes
can be merged by scripts/merge_asr_transcripts.py.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "tts_api_config.local.json"
DEFAULT_PROMPT = (
    "请逐字转写这段音频内容，只输出转写文本，不要解释。"
    "请尽量保留你实际听到的中文数字、英文缩写、单位和符号读法，"
    "不要把口语读法改写成原始书面文本。"
)
RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}
REFUSAL_PATTERNS = [
    "无法转写",
    "抱歉",
    "无法接收",
    "无法直接接收",
    "无法直接处理音频文件",
    "没有收到音频",
    "没有看到或听到任何音频",
    "没有看到您上传",
    "请提供音频",
    "提供音频中的文字内容",
    "上传音频文件",
    "上传的音频文件",
    "不是音频文件",
    "处理音频文件",
    "not able to listen",
    "process audio content",
]


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def json_path(obj: Any, path: str) -> Any:
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def load_mimo_provider(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    for provider in config.get("providers", []):
        if provider.get("provider") == "mimo":
            return provider
    raise RuntimeError(f"mimo provider not found in {config_path}")


def require_key(provider: dict[str, Any]) -> str:
    auth = provider.get("auth", {})
    inline = str(auth.get("api_key") or "").strip()
    if inline:
        return inline
    env_name = str(auth.get("api_key_env") or "").strip()
    if env_name and os.environ.get(env_name):
        return os.environ[env_name]
    raise RuntimeError("missing MiMo API key")


def looks_bad(text: str) -> bool:
    s = str(text or "").strip()
    return (not s) or any(pat in s for pat in REFUSAL_PATTERNS)


def request_with_retries(
    url: str,
    *,
    headers: dict[str, str],
    json_body: Any,
    timeout: float,
    max_attempts: int,
    backoff_seconds: float,
) -> requests.Response:
    proxies = None if os.environ.get("CN_NEWTTS_ALLOW_PROXY") == "1" else {"http": None, "https": None}
    last: requests.Response | None = None
    for attempt in range(1, max_attempts + 1):
        resp = requests.post(url, headers=headers, json=json_body, timeout=timeout, proxies=proxies)
        last = resp
        if resp.status_code not in RETRY_STATUS or attempt == max_attempts:
            return resp
        retry_after = resp.headers.get("retry-after")
        wait = float(retry_after) if retry_after else backoff_seconds * (2 ** (attempt - 1))
        time.sleep(wait)
    assert last is not None
    return last


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


def call_mimo_asr(
    provider: dict[str, Any],
    audio_path: Path,
    *,
    api_key: str,
    asr_model: str,
    prompt: str,
    timeout: float,
    max_attempts: int,
    backoff_seconds: float,
) -> tuple[str, dict[str, Any]]:
    endpoint = provider.get("request", {}).get("endpoint") or "https://token-plan-cn.xiaomimimo.com/v1/chat/completions"
    audio_b64 = base64.b64encode(audio_path.read_bytes()).decode("utf-8")
    body = {
        "model": asr_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": f"data:audio/wav;base64,{audio_b64}",
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "max_completion_tokens": 2048,
    }
    resp = request_with_retries(
        endpoint,
        headers={"api-key": api_key, "Content-Type": "application/json"},
        json_body=body,
        timeout=timeout,
        max_attempts=max_attempts,
        backoff_seconds=backoff_seconds,
    )
    resp.raise_for_status()
    data = resp.json()
    return str(json_path(data, "choices.0.message.content") or "").strip(), data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--audio-root", type=Path, default=ROOT / "results" / "tts_generation" / "dev" / "audio_wav_24k_mono")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--asr-id", default="mimo_v2_5_asr")
    parser.add_argument("--asr-model", default="mimo-v2.5")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--providers", nargs="*")
    parser.add_argument("--sample-ids", nargs="*")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--bad-text-max-attempts", type=int, default=2)
    parser.add_argument("--backoff-seconds", type=float, default=4)
    parser.add_argument("--row-sleep-seconds", type=float, default=0)
    parser.add_argument("--retry-errors", action="store_true")
    args = parser.parse_args()

    provider = load_mimo_provider(args.config)
    api_key = require_key(provider)
    providers = set(args.providers) if args.providers else None
    sample_ids = set(args.sample_ids) if args.sample_ids else None
    jobs = load_jobs(args.manifest, providers, sample_ids, args.audio_root)
    if args.limit:
        jobs = jobs[: args.limit]

    done = load_done(args.output, args.retry_errors)
    pending = [job for job in jobs if (job["tts_provider"], job["id"]) not in done]
    print(json.dumps({
        "asr_id": args.asr_id,
        "asr_model": args.asr_model,
        "manifest": str(args.manifest),
        "output": str(args.output),
        "jobs": len(jobs),
        "already_done": len(jobs) - len(pending),
        "pending": len(pending),
    }, ensure_ascii=False), flush=True)

    for idx, job in enumerate(pending, 1):
        audio_path = Path(job["audio_path"])
        started = time.time()
        text = ""
        error = ""
        attempts = 0
        response_id = ""
        if not audio_path.exists():
            error = f"FileNotFoundError: {audio_path}"
        else:
            for attempt in range(1, args.bad_text_max_attempts + 1):
                attempts = attempt
                try:
                    text, raw = call_mimo_asr(
                        provider,
                        audio_path,
                        api_key=api_key,
                        asr_model=args.asr_model,
                        prompt=args.prompt,
                        timeout=args.timeout,
                        max_attempts=args.max_attempts,
                        backoff_seconds=args.backoff_seconds,
                    )
                    response_id = str(raw.get("id") or "")
                    error = ""
                except Exception as exc:
                    text = ""
                    error = f"{type(exc).__name__}: {exc}"
                if error or not looks_bad(text):
                    break
                if attempt < args.bad_text_max_attempts:
                    time.sleep(args.backoff_seconds)

        status = "ok" if text and not error and not looks_bad(text) else ("error" if error else "bad_text")
        row = {
            "created_at": now_iso(),
            "id": job["id"],
            "tts_provider": job["tts_provider"],
            "asr_id": args.asr_id,
            "asr_model": args.asr_model,
            "audio_path": job["audio_path_rel"],
            "duration_sec": job.get("duration_sec"),
            "source_text": job.get("source_text", ""),
            "text": text,
            "status": status,
            "error": error,
            "attempts": attempts,
            "response_id": response_id,
            "elapsed_sec": round(time.time() - started, 3),
        }
        append_jsonl(args.output, row)
        print(json.dumps({
            "idx": idx,
            "pending": len(pending),
            "id": row["id"],
            "tts_provider": row["tts_provider"],
            "status": row["status"],
            "attempts": row["attempts"],
            "elapsed_sec": row["elapsed_sec"],
            "text": row["text"][:80],
            "error": row["error"][:160],
        }, ensure_ascii=False), flush=True)
        if args.row_sleep_seconds:
            time.sleep(args.row_sleep_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
