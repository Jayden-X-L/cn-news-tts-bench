#!/usr/bin/env python3
"""Generate raw-text TTS audio for a CN-NewsTTS split.

This runner reads local credentials from tts_api_config.local.json, calls each
enabled provider with the original dataset text, and writes provider audio plus
a resumable manifest. Secrets are never written to output files.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "tts_api_config.local.json"
DEFAULT_DATASET = ROOT / "data" / "dev.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "results" / "tts_generation" / "dev"

RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
            if limit and len(rows) >= limit:
                break
    return rows


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def safe_name(value: str) -> str:
    out = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return out.strip("._") or "item"


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def json_path(obj: Any, path: str) -> Any:
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def request_with_retries(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: Any = None,
    data: bytes | str | None = None,
    timeout: float = 120,
    max_attempts: int = 3,
    backoff_seconds: float = 2,
) -> requests.Response:
    last: requests.Response | None = None
    proxies = None if os.environ.get("CN_NEWTTS_ALLOW_PROXY") == "1" else {"http": None, "https": None}
    for attempt in range(1, max_attempts + 1):
        resp = requests.request(
            method,
            url,
            headers=headers,
            json=json_body,
            data=data,
            timeout=timeout,
            proxies=proxies,
        )
        last = resp
        if resp.status_code not in RETRY_STATUS or attempt == max_attempts:
            return resp
        retry_after = resp.headers.get("retry-after")
        wait = float(retry_after) if retry_after else backoff_seconds * (2 ** (attempt - 1))
        time.sleep(wait)
    assert last is not None
    return last


def require_key(provider: dict[str, Any]) -> str:
    auth = provider.get("auth", {})
    inline = str(auth.get("api_key") or "").strip()
    if inline:
        return inline
    env_name = str(auth.get("api_key_env") or "").strip()
    if env_name and os.environ.get(env_name):
        return os.environ[env_name]
    raise RuntimeError(f"missing API key for {provider['provider']}")


def provider_defaults(provider: dict[str, Any]) -> dict[str, Any]:
    """Resolve benchmark defaults for fields that the form left blank."""
    p = deepcopy(provider)
    pid = p["provider"]
    request = p.setdefault("request", {})
    auth = p.setdefault("auth", {})

    if pid == "mimo":
        request.setdefault("endpoint", "https://token-plan-cn.xiaomimimo.com/v1/chat/completions")
        if not request.get("endpoint"):
            request["endpoint"] = "https://token-plan-cn.xiaomimimo.com/v1/chat/completions"
        p["voice"] = p.get("voice") or "白桦"
        p["audio_format"] = p.get("audio_format") or "wav"
    elif pid == "google_cloud_tts":
        p["audio_format"] = p.get("audio_format") or "wav"
        request["language_code"] = request.get("language_code") or "cmn-CN"
    elif pid == "azure_speech_tts":
        region = auth.get("region") or os.environ.get(request.get("region_env", "")) or "eastasia"
        auth["region"] = region
        p["voice"] = p.get("voice") or "zh-CN-XiaoxiaoNeural"
        p["audio_format"] = p.get("audio_format") or "wav"
    elif pid == "minimax_tts":
        request["endpoint"] = request.get("endpoint") or "https://api.minimaxi.com/v1/t2a_v2"
        request["sleep_seconds"] = request.get("sleep_seconds", 2.0)
        request["rate_limit_wait_seconds"] = request.get("rate_limit_wait_seconds", 65.0)
        p["voice"] = p.get("voice") or "Chinese (Mandarin)_News_Anchor"
        p["audio_format"] = p.get("audio_format") or "mp3"
    elif pid == "aws_polly":
        auth["region"] = auth.get("region") or "us-east-1"
        p["voice"] = p.get("voice") or "Zhiyu"
        p["audio_format"] = p.get("audio_format") or "mp3"
    elif pid == "volcengine_tts":
        request["endpoint"] = request.get("endpoint") or "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
        request["resource_id"] = request.get("resource_id") or "seed-tts-2.0"
        p["voice"] = p.get("voice") or "zh_female_vv_uranus_bigtts"
        p["audio_format"] = p.get("audio_format") or "wav"
    elif pid == "aliyun_tts":
        model = p.get("model") or "cosyvoice-v3-plus"
        p["model"] = model
        if not p.get("voice"):
            p["voice"] = "longshuo_v3" if model == "cosyvoice-v3-flash" else "longanyang"
        p["audio_format"] = p.get("audio_format") or "wav"
    return p


def validate_policy(provider: dict[str, Any]) -> None:
    policy = provider.get("policy") or {}
    required = {
        "raw_text_only": True,
        "external_frontend": False,
        "llm_rewrite": False,
        "manual_text_fix": False,
    }
    for key, expected in required.items():
        if policy.get(key) is not expected:
            raise RuntimeError(f"{provider['provider']} policy {key}={policy.get(key)!r}, expected {expected!r}")


def call_mimo(provider: dict[str, Any], text: str, timeout: float, max_attempts: int) -> tuple[bytes, str, dict[str, Any]]:
    api_key = require_key(provider)
    body = {
        "model": provider.get("model") or "mimo-v2.5-tts",
        "messages": [
            {
                "role": "user",
                "content": "新闻快讯播报风格：清晰、稳健、自然，语速适中，避免夸张情绪。",
            },
            {"role": "assistant", "content": text},
        ],
        "audio": {
            "format": provider.get("audio_format") or "wav",
            "voice": provider.get("voice") or "白桦",
        },
    }
    resp = request_with_retries(
        "POST",
        provider["request"]["endpoint"],
        headers={"api-key": api_key, "Content-Type": "application/json"},
        json_body=body,
        timeout=timeout,
        max_attempts=max_attempts,
    )
    resp.raise_for_status()
    data = resp.json()
    audio_b64 = json_path(data, "choices.0.message.audio.data")
    return base64.b64decode(audio_b64), "wav", {"response_id": data.get("id")}


def call_google(provider: dict[str, Any], text: str, timeout: float, max_attempts: int) -> tuple[bytes, str, dict[str, Any]]:
    api_key = require_key(provider)
    audio_format = (provider.get("audio_format") or "wav").lower()
    encoding = "MP3" if audio_format == "mp3" else "LINEAR16"
    url = provider["request"].get("endpoint") or "https://texttospeech.googleapis.com/v1/text:synthesize"
    if "?" in url:
        url = f"{url}&key={api_key}"
    else:
        url = f"{url}?key={api_key}"
    body = {
        "input": {"text": text},
        "voice": {
            "languageCode": provider["request"].get("language_code") or "cmn-CN",
            "name": provider.get("voice") or "cmn-CN-Chirp3-HD-Kore",
        },
        "audioConfig": {
            "audioEncoding": encoding,
            "sampleRateHertz": int(provider.get("sample_rate") or 24000),
        },
    }
    resp = request_with_retries(
        "POST",
        url,
        headers={"Content-Type": "application/json"},
        json_body=body,
        timeout=timeout,
        max_attempts=max_attempts,
    )
    resp.raise_for_status()
    data = resp.json()
    return base64.b64decode(data["audioContent"]), audio_format, {}


def call_azure(provider: dict[str, Any], text: str, timeout: float, max_attempts: int) -> tuple[bytes, str, dict[str, Any]]:
    api_key = require_key(provider)
    region = provider["auth"].get("region") or "eastasia"
    endpoint = provider["request"].get("endpoint") or ""
    if ".tts.speech." in endpoint and endpoint.rstrip("/").endswith("/cognitiveservices/v1"):
        url = endpoint.rstrip("/")
    else:
        url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    voice = provider.get("voice") or "zh-CN-XiaoxiaoNeural"
    lang = "-".join(voice.split("-")[:2]) if "-" in voice else "zh-CN"
    sample_rate = int(provider.get("sample_rate") or 24000)
    output_format = "riff-24khz-16bit-mono-pcm" if sample_rate == 24000 else "riff-16khz-16bit-mono-pcm"
    ssml = (
        f"<speak version='1.0' xml:lang='{html.escape(lang)}'>"
        f"<voice name='{html.escape(voice)}'>{html.escape(text)}</voice>"
        "</speak>"
    )
    resp = request_with_retries(
        "POST",
        url,
        headers={
            "Ocp-Apim-Subscription-Key": api_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": output_format,
            "User-Agent": "cn-newstts-bench",
        },
        data=ssml.encode("utf-8"),
        timeout=timeout,
        max_attempts=max_attempts,
    )
    resp.raise_for_status()
    return resp.content, "wav", {"api_required_wrapper": "ssml"}


def call_minimax(provider: dict[str, Any], text: str, timeout: float, max_attempts: int) -> tuple[bytes, str, dict[str, Any]]:
    api_key = require_key(provider)
    audio_format = provider.get("audio_format") or "mp3"
    body = {
        "model": provider.get("model") or "speech-2.8-hd",
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": provider.get("voice") or "Chinese (Mandarin)_News_Anchor",
            "speed": 1,
            "vol": 1,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": int(provider.get("sample_rate") or 24000),
            "bitrate": 128000,
            "format": audio_format,
            "channel": 1,
        },
        "language_boost": "Chinese",
        "subtitle_enable": False,
        "output_format": "hex",
    }
    rate_limit_wait = float(provider.get("request", {}).get("rate_limit_wait_seconds") or 65.0)
    data: dict[str, Any] = {}
    base_resp: dict[str, Any] = {}
    for attempt in range(1, max_attempts + 1):
        resp = request_with_retries(
            "POST",
            provider["request"]["endpoint"],
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json_body=body,
            timeout=timeout,
            max_attempts=max_attempts,
        )
        resp.raise_for_status()
        data = resp.json()
        base_resp = data.get("base_resp") or {}
        status_code = base_resp.get("status_code")
        if status_code == 1002 and attempt < max_attempts:
            time.sleep(rate_limit_wait)
            continue
        break
    if base_resp.get("status_code") not in (0, None):
        raise RuntimeError(f"MiniMax error {base_resp.get('status_code')}: {base_resp.get('status_msg')}")
    audio_hex = ((data.get("data") or {}).get("audio") or "").strip()
    if not audio_hex:
        raise RuntimeError("MiniMax returned empty audio")
    return bytes.fromhex(audio_hex), audio_format, {"extra_info": data.get("extra_info")}


def find_aws_access_key_id(provider: dict[str, Any]) -> tuple[str, str]:
    auth = provider.get("auth", {})
    request = provider.get("request", {})
    api_key = str(auth.get("api_key") or "").strip()
    env_name = str(auth.get("api_key_env") or "").strip()
    env_value = os.environ.get(env_name, "")

    looks_like_access_id = re.match(r"^A(KIA|SIA)[A-Z0-9]{16}$", api_key)
    if looks_like_access_id:
        access_key_id = api_key
        secret = os.environ.get(str(request.get("secret_key_env") or ""), "")
        if not secret:
            secret = str(request.get("secret_access_key") or "").strip()
        return access_key_id, secret

    notes = str(provider.get("notes") or "")
    match = re.search(r"(A(?:KIA|SIA)[A-Z0-9]{16})", notes)
    access_key_id = match.group(1) if match else env_value
    secret = api_key or os.environ.get(str(request.get("secret_key_env") or ""), "")
    return access_key_id, secret


def aws_signing_key(secret: str, date_stamp: str, region: str, service: str) -> bytes:
    def sign(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    key = ("AWS4" + secret).encode("utf-8")
    return sign(sign(sign(sign(key, date_stamp), region), service), "aws4_request")


def call_aws_polly(provider: dict[str, Any], text: str, timeout: float, max_attempts: int) -> tuple[bytes, str, dict[str, Any]]:
    access_key_id, secret = find_aws_access_key_id(provider)
    if not access_key_id or not secret:
        raise RuntimeError("missing AWS access key id or secret access key")
    region = provider["auth"].get("region") or "us-east-1"
    service = "polly"
    host = f"polly.{region}.amazonaws.com"
    endpoint = f"https://{host}/v1/speech"
    audio_format = provider.get("audio_format") or "mp3"
    body = json.dumps(
        {
            "Text": text,
            "OutputFormat": audio_format,
            "VoiceId": provider.get("voice") or "Zhiyu",
            "Engine": "neural" if "neural" in str(provider.get("model") or "").lower() else "standard",
            "SampleRate": str(provider.get("sample_rate") or 24000),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    now = datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    payload_hash = hashlib.sha256(body).hexdigest()
    headers = {
        "content-type": "application/json",
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"
    canonical_headers = "".join(f"{k}:{headers[k]}\n" for k in sorted(headers))
    canonical_request = "\n".join(["POST", "/v1/speech", "", canonical_headers, signed_headers, payload_hash])
    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(
        [algorithm, amz_date, credential_scope, hashlib.sha256(canonical_request.encode()).hexdigest()]
    )
    signing_key = aws_signing_key(secret, date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    headers["Authorization"] = (
        f"{algorithm} Credential={access_key_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    resp = request_with_retries(
        "POST",
        endpoint,
        headers=headers,
        data=body,
        timeout=timeout,
        max_attempts=max_attempts,
    )
    resp.raise_for_status()
    return resp.content, audio_format, {"region": region}


def extract_volc_audio(data: Any) -> bytes:
    chunks: list[bytes] = []

    def visit(obj: Any) -> None:
        if not isinstance(obj, dict):
            return
        code = obj.get("code")
        if code not in (None, 0, "0", 200, "200", 20000000, "20000000"):
            raise RuntimeError(f"Volcengine error {code}: {obj.get('message') or obj.get('msg')}")
        value = obj.get("data") or obj.get("audio") or obj.get("audio_data")
        if isinstance(value, str) and value:
            chunks.append(base64.b64decode(value))
        for key in ("result", "payload", "response"):
            if isinstance(obj.get(key), dict):
                visit(obj[key])

    if isinstance(data, list):
        for item in data:
            visit(item)
    else:
        visit(data)
    if not chunks:
        raise RuntimeError("Volcengine returned empty audio")
    return b"".join(chunks)


def parse_json_or_lines(content: bytes) -> Any:
    text = content.decode("utf-8", errors="replace").strip()
    if not text:
        raise RuntimeError("empty response")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        items = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("data:"):
                line = line[5:].strip()
            if line in {"[DONE]", "DONE"}:
                continue
            items.append(json.loads(line))
        return items


def call_volcengine(provider: dict[str, Any], text: str, timeout: float, max_attempts: int) -> tuple[bytes, str, dict[str, Any]]:
    api_key = require_key(provider)
    request = provider["request"]
    resource_id = request.get("resource_id") or "seed-tts-2.0"
    audio_format = provider.get("audio_format") or "wav"
    body = {
        "user": {"uid": "cn_news_tts_bench"},
        "req_params": {
            "text": text,
            "speaker": provider.get("voice") or "zh_female_vv_uranus_bigtts",
            "audio_params": {
                "format": audio_format,
                "sample_rate": int(provider.get("sample_rate") or 24000),
            },
            "resource_id": resource_id,
        },
    }
    resp = request_with_retries(
        "POST",
        request["endpoint"],
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": api_key,
            "X-Api-Resource-Id": resource_id,
        },
        json_body=body,
        timeout=timeout,
        max_attempts=max_attempts,
    )
    resp.raise_for_status()
    data = parse_json_or_lines(resp.content)
    return extract_volc_audio(data), audio_format, {"resource_id": resource_id}


def call_aliyun(provider: dict[str, Any], text: str, timeout: float, max_attempts: int) -> tuple[bytes, str, dict[str, Any]]:
    api_key = require_key(provider)
    try:
        from dashscope.audio.http_tts import HttpSpeechSynthesizer
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("dashscope package is required for aliyun_tts") from exc

    audio_format = provider.get("audio_format") or "wav"
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        seed_kwargs = {} if attempt == 1 else {"seed": attempt - 1}
        result = HttpSpeechSynthesizer.call(
            model=provider.get("model") or "cosyvoice-v3-plus",
            text=text,
            voice=provider.get("voice") or "longanyang",
            audio_format=audio_format,
            sample_rate=int(provider.get("sample_rate") or 24000),
            stream=False,
            api_key=api_key,
            **seed_kwargs,
        )
        try:
            response = result.response
            if response is not None:
                status_code = getattr(response, "status_code", None)
                if status_code not in (None, 200):
                    message = getattr(response, "message", "") or getattr(response, "code", "")
                    raise RuntimeError(f"Aliyun error {status_code}: {message}")
            audio = result.audio_data
            if not audio and result.audio_url:
                resp = request_with_retries("GET", result.audio_url, timeout=timeout, max_attempts=1)
                resp.raise_for_status()
                audio = resp.content
            if not audio:
                raise RuntimeError("Aliyun returned empty audio")
            return audio, audio_format, {
                "audio_id": result.audio_id,
                "expires_at": result.expires_at,
                "retry_seed": seed_kwargs.get("seed"),
            }
        except Exception as exc:  # noqa: BLE001 - retry provider-side transient bad URLs
            last_exc = exc
            if attempt == max_attempts:
                break
            time.sleep(min(2 * attempt, 10))
    assert last_exc is not None
    raise last_exc


CALLERS = {
    "mimo": call_mimo,
    "google_cloud_tts": call_google,
    "azure_speech_tts": call_azure,
    "minimax_tts": call_minimax,
    "aws_polly": call_aws_polly,
    "volcengine_tts": call_volcengine,
    "aliyun_tts": call_aliyun,
}


def ffprobe_duration(path: Path) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    try:
        return round(float(proc.stdout.strip()), 6)
    except ValueError:
        return None


def normalize_audio(raw_path: Path, wav_path: Path, sample_rate: int) -> None:
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("ffmpeg"):
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(raw_path),
                "-ar",
                str(sample_rate),
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(wav_path),
            ],
            check=True,
        )
    elif raw_path.suffix.lower() == ".wav":
        shutil.copy2(raw_path, wav_path)
    else:
        raise RuntimeError("ffmpeg is required to normalize non-wav audio")


def completed_ok(audio_path: Path) -> bool:
    return audio_path.exists() and audio_path.stat().st_size > 44


def provider_public_config(provider: dict[str, Any]) -> dict[str, Any]:
    request = deepcopy(provider.get("request") or {})
    auth = deepcopy(provider.get("auth") or {})
    for key in list(auth):
        if "key" in key.lower() or "secret" in key.lower() or "credential" in key.lower():
            if auth.get(key):
                auth[key] = "<redacted>"
    for key in list(request):
        if "key" in key.lower() or "secret" in key.lower() or "credential" in key.lower():
            if request.get(key):
                request[key] = "<redacted>"
    return {
        "provider": provider["provider"],
        "display_name": provider.get("display_name"),
        "model": provider.get("model"),
        "voice": provider.get("voice"),
        "sample_rate": provider.get("sample_rate"),
        "audio_format": provider.get("audio_format"),
        "auth": auth,
        "request": request,
        "policy": provider.get("policy"),
    }


def run(args: argparse.Namespace) -> int:
    config = read_json(args.config)
    rows = load_jsonl(args.dataset, args.limit)
    requested = set(args.providers.split(",")) if args.providers else None
    providers = [provider_defaults(p) for p in config["providers"] if p.get("enabled")]
    if requested:
        providers = [p for p in providers if p["provider"] in requested]
    if not providers:
        raise SystemExit("No providers selected.")

    output_dir: Path = args.output_dir
    raw_dir = output_dir / "raw_audio"
    audio_dir = output_dir / "audio_wav_24k_mono"
    manifest_path = output_dir / "manifest.jsonl"
    errors_path = output_dir / "errors.jsonl"
    status_path = output_dir / "status.json"
    resolved_config_path = output_dir / "resolved_provider_config.redacted.json"
    output_dir.mkdir(parents=True, exist_ok=True)

    for provider in providers:
        validate_policy(provider)
        if provider["provider"] not in CALLERS:
            raise RuntimeError(f"unsupported provider: {provider['provider']}")

    write_json(
        resolved_config_path,
        {
            "created_at": now_iso(),
            "dataset": str(args.dataset),
            "output_dir": str(output_dir),
            "providers": [provider_public_config(p) for p in providers],
            "normalization": {"format": "wav", "sample_rate": 24000, "channels": 1},
        },
    )

    total = len(rows) * len(providers)
    done = 0
    skipped = 0
    failed = 0
    start_time = time.time()
    print(f"dataset={args.dataset} records={len(rows)} providers={len(providers)} total={total}")
    print(f"output_dir={output_dir}")

    for provider in providers:
        pid = provider["provider"]
        caller = CALLERS[pid]
        for row_index, row in enumerate(rows, 1):
            case_id = row["id"]
            audio_path = audio_dir / pid / f"{case_id}.wav"
            raw_ext = (provider.get("audio_format") or "wav").lower().lstrip(".")
            raw_path = raw_dir / pid / f"{case_id}.{raw_ext}"
            if not args.force and completed_ok(audio_path):
                record = {
                    "created_at": now_iso(),
                    "split": row.get("split"),
                    "case_id": case_id,
                    "provider": pid,
                    "display_name": provider.get("display_name"),
                    "model": provider.get("model"),
                    "voice": provider.get("voice"),
                    "text_sha256_16": text_hash(row["text"]),
                    "source_text": row["text"],
                    "raw_audio_path": str(raw_path),
                    "audio_path": str(audio_path),
                    "raw_audio_bytes": raw_path.stat().st_size if raw_path.exists() else None,
                    "audio_bytes": audio_path.stat().st_size,
                    "duration_sec": ffprobe_duration(audio_path),
                    "status": "skipped_existing",
                    "error": "",
                }
                append_jsonl(manifest_path, record)
                skipped += 1
                done += 1
                print(f"[{done}/{total}] {pid} {case_id} skip")
                continue

            started = time.time()
            record = {
                "created_at": now_iso(),
                "split": row.get("split"),
                "case_id": case_id,
                "provider": pid,
                "display_name": provider.get("display_name"),
                "model": provider.get("model"),
                "voice": provider.get("voice"),
                "text_sha256_16": text_hash(row["text"]),
                "source_text": row["text"],
                "raw_audio_path": str(raw_path),
                "audio_path": str(audio_path),
                "status": "ok",
                "error": "",
            }
            try:
                raw_audio, returned_ext, meta = caller(provider, row["text"], args.timeout, args.max_attempts)
                raw_ext = returned_ext.lower().lstrip(".")
                if raw_path.suffix.lower() != f".{raw_ext}":
                    raw_path = raw_path.with_suffix(f".{raw_ext}")
                    record["raw_audio_path"] = str(raw_path)
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_bytes(raw_audio)
                normalize_audio(raw_path, audio_path, 24000)
                raw_duration = ffprobe_duration(raw_path)
                wav_duration = ffprobe_duration(audio_path)
                record.update(
                    {
                        "raw_audio_bytes": raw_path.stat().st_size,
                        "audio_bytes": audio_path.stat().st_size,
                        "raw_duration_sec": raw_duration,
                        "duration_sec": wav_duration,
                        "latency_sec": round(time.time() - started, 3),
                        "provider_meta": meta,
                    }
                )
                append_jsonl(manifest_path, record)
                done += 1
                print(
                    f"[{done}/{total}] {pid} {case_id} ok "
                    f"dur={record.get('duration_sec')}s latency={record['latency_sec']}s"
                )
            except Exception as exc:  # noqa: BLE001 - manifest should preserve provider errors
                failed += 1
                done += 1
                record.update({"status": "error", "error": repr(exc), "latency_sec": round(time.time() - started, 3)})
                append_jsonl(manifest_path, record)
                append_jsonl(errors_path, record)
                print(f"[{done}/{total}] {pid} {case_id} ERROR {record['error']}", file=sys.stderr)
                if args.stop_on_error:
                    write_json(status_path, make_status(args, providers, rows, done, skipped, failed, start_time))
                    return 1
            row_sleep = max(args.sleep_seconds, float(provider.get("request", {}).get("sleep_seconds") or 0))
            if row_sleep:
                time.sleep(row_sleep)

    write_json(status_path, make_status(args, providers, rows, done, skipped, failed, start_time))
    print(f"manifest={manifest_path}")
    print(f"status={status_path}")
    if failed:
        print(f"errors={errors_path}", file=sys.stderr)
    return 1 if failed else 0


def make_status(
    args: argparse.Namespace,
    providers: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    done: int,
    skipped: int,
    failed: int,
    start_time: float,
) -> dict[str, Any]:
    return {
        "updated_at": now_iso(),
        "dataset": str(args.dataset),
        "output_dir": str(args.output_dir),
        "records": len(rows),
        "providers": [p["provider"] for p in providers],
        "total_expected": len(rows) * len(providers),
        "processed": done,
        "skipped_existing": skipped,
        "failed": failed,
        "ok": done - failed,
        "elapsed_sec": round(time.time() - start_time, 3),
        "complete": done == len(rows) * len(providers) and failed == 0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--providers", help="Comma-separated provider ids. Default: all enabled providers.")
    parser.add_argument("--limit", type=int, help="Only run the first N dataset records.")
    parser.add_argument("--force", action="store_true", help="Regenerate audio even if normalized wav already exists.")
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    return parser.parse_args()


def main() -> int:
    return run(parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
