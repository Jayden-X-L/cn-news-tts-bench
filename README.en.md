# CN-NewsTTS Bench

[中文说明](README.md) | [Preprint PDF](paper/cn_newstts_bench_preprint.pdf) | [Leaderboard](https://jayden-x-l.github.io/cn-news-tts-bench/) | [v0.1 Release](https://github.com/Jayden-X-L/cn-news-tts-bench/releases/tag/v0.1)

CN-NewsTTS Bench is an open, target-level benchmark for evaluating whether **raw Chinese news TTS systems** pronounce high-risk news expressions correctly.

The benchmark asks one narrow question:

> Given the same raw Chinese news text, without external rule frontends, LLM rewriting, SSML, or manual text fixes, can a TTS system pronounce the target expressions correctly?

## Why This Benchmark Exists

Chinese news text contains many surface forms that are uncommon in ordinary prose but frequent in spoken news: scores, hyphens, ranges, model names, unit symbols, percentages, English abbreviations, and mixed Chinese-Latin-digit names. Examples include `96-91`, `苏-27`, `2028-2030年`, `620N·m`, `3.5%`, and `80后`. These forms are usually clear to human news editors, but raw TTS systems often normalize them incorrectly.

Such errors are not just naturalness issues. They can change the meaning of the news item: a score may be read as a range, an aircraft model may be read as a negative number, `80后` may be read as "eighty-hou", and unit symbols may be spelled or normalized inconsistently. CN-NewsTTS Bench measures this raw-model capability with an open, reproducible, automatic target-level protocol.

## v0.1 Status

The v0.1 public release includes:

- `dev`: 200 records
- `test_public`: 800 records
- 992 auto-evaluable targets in the public test set
- fixed public ASR transcripts from three ASR systems
- target-level voting scorer
- seven initial commercial/product TTS baselines
- reproducibility checksums
- a GitHub Pages leaderboard
- an ICASSP-style preprint PDF

Public leaderboard:

- Preprint PDF: [paper/cn_newstts_bench_preprint.pdf](paper/cn_newstts_bench_preprint.pdf)
- Preprint markdown: [paper/cn_newstts_bench_preprint.md](paper/cn_newstts_bench_preprint.md)
- Web: [https://jayden-x-l.github.io/cn-news-tts-bench/](https://jayden-x-l.github.io/cn-news-tts-bench/)
- CSV: [results/leaderboard.csv](results/leaderboard.csv)
- JSON: [results/leaderboard.json](results/leaderboard.json)
- Release audit: [docs/release_v0.1_audit.md](docs/release_v0.1_audit.md)

## Public Test Leaderboard

ASR ensemble: MiMo API ASR + SenseVoiceSmall + Paraformer-zh.

| Rank | TTS system | Strict Acc | Coverage | Resolved Acc | Correct | Wrong | Unknown |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | Volcano / Doubao TTS | 0.879 | 0.913 | 0.962 | 872 | 34 | 86 |
| 2 | Azure Speech TTS | 0.756 | 0.756 | 1.000 | 750 | 0 | 242 |
| 3 | Google Cloud TTS | 0.604 | 0.861 | 0.701 | 599 | 255 | 138 |
| 4 | MiniMax TTS | 0.548 | 0.850 | 0.645 | 544 | 299 | 149 |
| 5 | Aliyun CosyVoice | 0.472 | 0.533 | 0.885 | 468 | 61 | 463 |
| 6 | MiMo TTS | 0.275 | 0.628 | 0.438 | 273 | 350 | 369 |
| 7 | AWS Polly | 0.244 | 0.570 | 0.428 | 242 | 323 | 427 |

`Strict Acc = correct / all auto-evaluable targets`. Unknown targets remain in the denominator.

## Task

Each sample is a short Chinese news-style sentence containing one or more pronunciation-risk targets, such as:

- `117-116`
- `苏-27`
- `80后`
- `3.5%`
- `N·m`
- `AI`

The evaluated system produces one audio file per input text. The Raw Model Track allows only the TTS provider's own default processing. It does not allow external rule frontends, LLM rewrites, SSML pronunciation hints, or manual edits to benchmark text.

## Dataset

| split | records | targets | auto-evaluable targets | optional targets |
|---|---:|---:|---:|---:|
| dev | 200 | 252 | 248 | 4 |
| test_public | 800 | 1008 | 992 | 16 |
| total | 1000 | 1260 | 1240 | 20 |

Files:

```text
data/dev.jsonl
data/test_public.jsonl
data/dataset_summary.json
data/schema.json
```

Dataset details are in [docs/dataset_v0.1.md](docs/dataset_v0.1.md).

## Scoring Protocol

The official v0.1 score uses three ASR routes:

| ASR route | Public transcript file |
|---|---|
| MiMo API ASR | [results/asr_transcripts/public_test/mimo_v2_5_asr.jsonl](results/asr_transcripts/public_test/mimo_v2_5_asr.jsonl) |
| SenseVoiceSmall | [results/asr_transcripts/public_test/sensevoice_small.jsonl](results/asr_transcripts/public_test/sensevoice_small.jsonl) |
| Paraformer-zh | [results/asr_transcripts/public_test/paraformer_zh.jsonl](results/asr_transcripts/public_test/paraformer_zh.jsonl) |

For each target and each ASR transcript, the scorer matches target-level positive and negative readings, then applies three-ASR voting:

- at least two `correct` decisions -> `correct`
- at least two `wrong` decisions -> `wrong`
- otherwise -> `unknown`

Metrics:

```text
Strict Auto Accuracy = correct / all_auto_evaluable_targets
Resolved Accuracy    = correct / (correct + wrong)
Coverage             = (correct + wrong) / all_auto_evaluable_targets
Unknown Rate         = unknown / all_auto_evaluable_targets
```

See [docs/scoring.md](docs/scoring.md).

## Reproduce the Public Leaderboard

Validate datasets:

```bash
python3 scripts/validate_dataset.py data/dev.jsonl
python3 scripts/validate_dataset.py data/test_public.jsonl
```

Score one model from fixed ASR transcripts:

```bash
python3 scripts/score_submission.py \
  --dataset data/test_public.jsonl \
  --asr-results results/asr_results/public_test/{model_id}.asr.jsonl \
  --model-id {model_id} \
  --output-dir results/per_model_public_test
```

Aggregate the leaderboard:

```bash
python3 scripts/aggregate_leaderboard.py \
  --per-model-dir results/per_model_public_test \
  --results-dir results \
  --site-dir site
```

Verify release checksums:

```bash
shasum -a 256 -c release/v0.1_core_checksums.sha256
```

## Repository Layout

```text
cn_news_tts_bench/
  data/                         # dev/public test data and schema
  docs/                         # task, scoring, submission, release audit
  examples/                     # minimal ASR result example
  paper/                        # benchmark preprint draft
  results/
    leaderboard.csv
    leaderboard.json
    asr_transcripts/public_test/
    asr_results/public_test/
    per_model_public_test/
  scripts/                      # validation, merge, scoring, aggregation
  site/                         # GitHub Pages leaderboard
  tools/api_config_builder.html # local TTS API config builder
```

Generated TTS audio is not committed. Local audio and API artifacts are ignored by git.

## Initial Baselines

v0.1 includes seven initial product TTS baselines:

- MiMo TTS
- Google Cloud TTS
- Azure Speech TTS
- MiniMax TTS
- Aliyun CosyVoice
- Volcano / Doubao TTS
- AWS Polly

OpenAI TTS is not included in the v0.1 official baseline run because the API payment path was unavailable during this run.

## License

- Code: [MIT](LICENSE)
- Dataset, fixed ASR transcripts, benchmark results, and documentation: [CC BY 4.0](LICENSE-DATA.md)
- Generated TTS audio is not included in this repository and may be subject to separate provider terms.
