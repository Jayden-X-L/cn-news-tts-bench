# Release v0.1 Audit

Audit date: 2026-06-23.

This document records the reproducibility status of the first public CN-NewsTTS Bench release.

## Scope

v0.1 evaluates Raw Model Track TTS systems on Chinese news-style pronunciation targets. The benchmark input is raw text only: no external frontend, no LLM rewrite, no SSML, and no manual text fix.

Public test size:

| split | records | targets | auto-evaluable targets | optional targets |
|---|---:|---:|---:|---:|
| dev | 200 | 252 | 248 | 4 |
| test_public | 800 | 1008 | 992 | 16 |

Dataset validation passed for:

```bash
python3 scripts/validate_dataset.py data/dev.jsonl
python3 scripts/validate_dataset.py data/test_public.jsonl
```

## Baseline TTS Systems

The first public baseline run includes seven product TTS systems:

| model_id | public rows |
|---|---:|
| aliyun_tts | 800 |
| aws_polly | 800 |
| azure_speech_tts | 800 |
| google_cloud_tts | 800 |
| mimo | 800 |
| minimax_tts | 800 |
| volcengine_tts | 800 |

The generated TTS audio was used locally for ASR and scoring. Audio files are not included in the core GitHub release because provider redistribution terms need separate review. The local audio directory is ignored by git:

```text
results/tts_generation/
```

## ASR Ensemble

The official v0.1 public score uses three ASR routes:

| asr_id | rows | status |
|---|---:|---|
| mimo_v2_5_asr | 5600 | ok |
| sensevoice_small | 5600 | ok |
| paraformer_zh | 5600 | ok |

MiMo API ASR was run in five non-overlapping public shards. The raw shard logs contain six historical `bad_text` refusal traces from MiMo API. All affected samples were retried, and the canonical transcript file contains 5600 final ok rows with no refusal-like ok text.

Canonical transcript:

```text
results/asr_transcripts/public_test/mimo_v2_5_asr.jsonl
```

The local ASR transcripts are:

```text
results/asr_transcripts/public_test/sensevoice_small.jsonl
results/asr_transcripts/public_test/paraformer_zh.jsonl
```

Final process audit:

```text
run_mimo_asr.py: none
watch_mimo_api_asr_shards.py: none
```

## Merge Audit

Public ASR merge command:

```bash
python3 scripts/merge_asr_transcripts.py \
  --dataset data/test_public.jsonl \
  --transcripts \
    results/asr_transcripts/public_test/sensevoice_small.jsonl \
    results/asr_transcripts/public_test/paraformer_zh.jsonl \
    results/asr_transcripts/public_test/mimo_v2_5_asr.jsonl \
  --output-dir results/asr_results/public_test \
  --min-asr 3
```

Merge summary:

| provider | rows | missing | insufficient_asr |
|---|---:|---:|---:|
| aliyun_tts | 800 | 0 | 0 |
| aws_polly | 800 | 0 | 0 |
| azure_speech_tts | 800 | 0 | 0 |
| google_cloud_tts | 800 | 0 | 0 |
| mimo | 800 | 0 | 0 |
| minimax_tts | 800 | 0 | 0 |
| volcengine_tts | 800 | 0 | 0 |

Total merged ASR rows: 16800 ok.

## Public Leaderboard

| Rank | TTS model | Strict Acc | Coverage | Resolved Acc | Correct | Wrong | Unknown |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | volcengine_tts | 0.879 | 0.913 | 0.962 | 872 | 34 | 86 |
| 2 | azure_speech_tts | 0.756 | 0.756 | 1.000 | 750 | 0 | 242 |
| 3 | google_cloud_tts | 0.604 | 0.861 | 0.701 | 599 | 255 | 138 |
| 4 | minimax_tts | 0.548 | 0.850 | 0.645 | 544 | 299 | 149 |
| 5 | aliyun_tts | 0.472 | 0.533 | 0.885 | 468 | 61 | 463 |
| 6 | mimo | 0.275 | 0.628 | 0.438 | 273 | 350 | 369 |
| 7 | aws_polly | 0.244 | 0.570 | 0.428 | 242 | 323 | 427 |

Leaderboard files:

```text
results/leaderboard.csv
results/leaderboard.json
results/per_model_public_test/leaderboard_public_test.csv
results/per_model_public_test/leaderboard_public_test.md
site/leaderboard.json
```

## Reproduction Commands

Score a model:

```bash
python3 scripts/score_submission.py \
  --dataset data/test_public.jsonl \
  --asr-results results/asr_results/public_test/{model_id}.asr.jsonl \
  --model-id {model_id} \
  --output-dir results/per_model_public_test
```

Aggregate leaderboard:

```bash
python3 scripts/aggregate_leaderboard.py \
  --per-model-dir results/per_model_public_test \
  --results-dir results \
  --site-dir site
```

Verify core checksums:

```bash
shasum -a 256 -c release/v0.1_core_checksums.sha256
```

## Release Hygiene

Do not commit:

- `tts_api_config.local.json`
- API keys or service account files
- `logs/`
- runtime shard manifests
- generated TTS audio under `results/tts_generation/`
- raw shard retry files under `results/asr_transcripts/**/*shard*.jsonl`

Tracked release artifacts should be enough to reproduce the public leaderboard from fixed ASR transcripts.
