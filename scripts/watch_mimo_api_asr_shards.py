#!/usr/bin/env python3
"""Watch and restart sharded MiMo API ASR jobs.

This helper is intentionally small and local-runner oriented. It never reads or
prints API keys; it only restarts shard commands that use the existing config
file and rely on run_mimo_asr.py's resumable --retry-errors behavior.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def pid_command(pid: int | None) -> str:
    if not pid:
        return ""
    try:
        return subprocess.check_output(["ps", "-p", str(pid), "-o", "command="], text=True).strip()
    except subprocess.CalledProcessError:
        return ""


def read_pid(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def shard_alive(log_dir: Path, shard_idx: int) -> tuple[bool, int | None]:
    pid = read_pid(log_dir / f"public_mimo_api_asr_shard_{shard_idx}.pid")
    cmd = pid_command(pid)
    marker = f"shard_{shard_idx}.manifest.jsonl"
    return bool(cmd and "run_mimo_asr.py" in cmd and marker in cmd), pid


def output_age_seconds(path: Path) -> float | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    return time.time() - path.stat().st_mtime


def start_shard(args: argparse.Namespace, shard_idx: int, reason: str) -> None:
    manifest = args.shard_dir / f"shard_{shard_idx}.manifest.jsonl"
    output = args.output_dir / f"{args.output_prefix}.shard_{shard_idx}.jsonl"
    log_path = args.log_dir / f"public_mimo_api_asr_shard_{shard_idx}.log"
    cmd = [
        sys.executable,
        "scripts/run_mimo_asr.py",
        "--config",
        str(args.config.relative_to(args.root)),
        "--manifest",
        str(manifest.relative_to(args.root)),
        "--output",
        str(output.relative_to(args.root)),
        "--retry-errors",
        "--max-attempts",
        str(args.max_attempts),
        "--bad-text-max-attempts",
        str(args.bad_text_max_attempts),
        "--backoff-seconds",
        str(args.backoff_seconds),
        "--row-sleep-seconds",
        str(args.row_sleep_seconds),
    ]
    log_f = log_path.open("a", encoding="utf-8")
    proc = subprocess.Popen(cmd, cwd=args.root, stdout=log_f, stderr=subprocess.STDOUT, start_new_session=True)
    (args.log_dir / f"public_mimo_api_asr_shard_{shard_idx}.pid").write_text(
        f"{proc.pid}\n", encoding="utf-8"
    )
    print(f"[restart] shard_{shard_idx} pid={proc.pid} reason={reason}", flush=True)


def summarize(args: argparse.Namespace) -> tuple[int, Counter[str], Counter[str], list[str]]:
    seen: set[tuple[str, str]] = set()
    status_counts: Counter[str] = Counter()
    provider_ok: Counter[str] = Counter()
    lines: list[str] = []
    for shard_idx in range(args.shards):
        path = args.output_dir / f"{args.output_prefix}.shard_{shard_idx}.jsonl"
        rows = load_jsonl(path)
        status_counts.update(str(row.get("status")) for row in rows)
        unique_ok = {
            (str(row.get("tts_provider")), str(row.get("id")))
            for row in rows
            if row.get("status") == "ok"
        }
        seen |= unique_ok
        for provider, _sample_id in unique_ok:
            provider_ok[provider] += 1
        alive, pid = shard_alive(args.log_dir, shard_idx)
        age = output_age_seconds(path)
        last = rows[-1] if rows else {}
        age_text = "NA" if age is None else f"{age:.0f}s"
        lines.append(
            f"shard_{shard_idx}: ok={len(unique_ok)}/{args.per_shard} "
            f"bad={sum(1 for row in rows if row.get('status') == 'bad_text')} "
            f"err={sum(1 for row in rows if row.get('status') == 'error')} "
            f"alive={alive} pid={pid} age={age_text} "
            f"last={last.get('tts_provider')}/{last.get('id')} {last.get('status')}"
        )
        if len(unique_ok) < args.per_shard and not alive:
            start_shard(args, shard_idx, "dead")
        elif len(unique_ok) < args.per_shard and age is not None and age > args.stale_report_seconds:
            lines.append(f"shard_{shard_idx}: stale_report age={age:.0f}s")
    return len(seen), status_counts, provider_ok, lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, default=ROOT / "tts_api_config.local.json")
    parser.add_argument("--shard-dir", type=Path, default=ROOT / "data/_runtime_shards/public_mimo_api_asr")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/asr_transcripts/public_test")
    parser.add_argument("--log-dir", type=Path, default=ROOT / "logs")
    parser.add_argument("--output-prefix", default="mimo_v2_5_asr")
    parser.add_argument("--shards", type=int, default=5)
    parser.add_argument("--per-shard", type=int, default=1120)
    parser.add_argument("--total", type=int, default=5600)
    parser.add_argument("--check-seconds", type=float, default=60)
    parser.add_argument("--report-every-checks", type=int, default=5)
    parser.add_argument("--stale-report-seconds", type=float, default=45 * 60)
    parser.add_argument("--max-attempts", type=int, default=8)
    parser.add_argument("--bad-text-max-attempts", type=int, default=4)
    parser.add_argument("--backoff-seconds", type=float, default=15)
    parser.add_argument("--row-sleep-seconds", type=float, default=0.2)
    args = parser.parse_args()

    args.root = args.root.resolve()
    args.config = args.config.resolve()
    args.shard_dir = args.shard_dir.resolve()
    args.output_dir = args.output_dir.resolve()
    args.log_dir = args.log_dir.resolve()
    args.log_dir.mkdir(parents=True, exist_ok=True)

    check_idx = 0
    while True:
        check_idx += 1
        unique_ok, status_counts, provider_ok, shard_lines = summarize(args)
        should_report = check_idx == 1 or check_idx % args.report_every_checks == 0 or unique_ok >= args.total
        if should_report:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"[{ts}] unique_ok={unique_ok}/{args.total} ({unique_ok / args.total:.1%}) "
                f"status={dict(status_counts)}",
                flush=True,
            )
            print(
                "provider_ok " + " ".join(f"{k}={v}/800" for k, v in sorted(provider_ok.items())),
                flush=True,
            )
            for line in shard_lines:
                print("  " + line, flush=True)
        if unique_ok >= args.total:
            print("[done] all unique ok rows are present.", flush=True)
            return 0
        time.sleep(args.check_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
