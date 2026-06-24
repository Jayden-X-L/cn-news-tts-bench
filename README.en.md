# CN-NewsTTS Bench

<div align="center">

**A target-level automatic benchmark for raw-input Chinese news TTS pronunciation accuracy**

[![arXiv](https://img.shields.io/badge/arXiv-2606.24714-b31b1b?style=for-the-badge)](https://arxiv.org/abs/2606.24714)
[![Zenodo DOI](https://img.shields.io/badge/Zenodo-10.5281%2Fzenodo.20822327-1682D4?style=for-the-badge)](https://doi.org/10.5281/zenodo.20822327)
[![Leaderboard](https://img.shields.io/badge/Leaderboard-GitHub%20Pages-00A3FF?style=for-the-badge)](https://jayden-x-l.github.io/cn-news-tts-bench/)
[![Release](https://img.shields.io/badge/Release-v0.1-16A34A?style=for-the-badge)](https://github.com/Jayden-X-L/cn-news-tts-bench/releases/tag/v0.1)

[中文说明](README.md) | [Leaderboard](https://jayden-x-l.github.io/cn-news-tts-bench/) | [Paper](https://arxiv.org/abs/2606.24714) | [Data Archive](https://doi.org/10.5281/zenodo.20822327)

</div>

---

## 30-Second Overview

CN-NewsTTS Bench v0.1 asks one narrow question:

> Given the same raw Chinese news text, without external rule frontends, LLM rewriting, SSML, or manual text fixes, can a TTS product pronounce the target news expressions correctly?

It is not MOS and not sentence-level WER/CER. It is a **target-level** benchmark for compact written expressions in Chinese news, such as `96-91`, `苏-27`, `2028-2030年`, `620N·m`, `3.5%`, `80后`, and `AI`. A typical failure is reading `苏-27` as `苏负二十七`, turning an aircraft model into a mathematical expression.

| Signal | v0.1 |
|---|---:|
| Dev set | 200 records / 248 auto-evaluable targets |
| Public test | 800 records / 992 auto-evaluable targets |
| Initial systems | 7 commercial/product TTS systems |
| Evaluation routes | MiMo API ASR + SenseVoiceSmall + Paraformer-zh |
| Scoring unit | target-level positive/negative reading match |
| Main metric | Strict Auto Accuracy |
| Data archive | [10.5281/zenodo.20822327](https://doi.org/10.5281/zenodo.20822327) |
| Paper | [arXiv:2606.24714](https://arxiv.org/abs/2606.24714) |

## Why This Benchmark Exists

Chinese news text contains many surface forms that are uncommon in ordinary prose but frequent in spoken news: scores, hyphens, ranges, model names, unit symbols, percentages, English abbreviations, and mixed Chinese-Latin-digit names. These forms are usually clear to human editors, but raw-input TTS systems often normalize them incorrectly.

Such errors are not just naturalness problems. They can change the meaning of the news item: a score may be read as a range, an aircraft model may be read as a negative number, `80后` may be read as "eighty-hou", and unit symbols may be spelled out letter by letter. CN-NewsTTS Bench measures this product-facing capability with an open, reproducible, automatic protocol.

## High-Risk Misreading Examples

These are not rare corner cases. They are meaning-changing pronunciation errors that show up in Chinese news reading. CN-NewsTTS Bench decomposes them into target-level positive and negative reading patterns, so the leaderboard can identify which target was misread instead of only reporting a sentence-level average.

| Written target | Expected news reading | Typical wrong reading | Meaning drift |
|---|---|---|---|
| `117-116` | `一百一十七比一百一十六` | `一百一十七到一百一十六`, `一百一十七负一百一十六` | score becomes range or subtraction |
| `苏-27` | `苏二十七`, `苏二七` | `苏负二十七`, `苏杠二十七` | aircraft model becomes math expression |
| `2028-2030年` | `二零二八到二零三零年` | `二零二八负二零三零年` | year range becomes negative expression |
| `3.5%` | `百分之三点五` | `三点五百分号`, `三点五个百分点` | percent, percentage-point, and symbol readings are confused |
| `80后` | `八零后` | `八十后` | generation label becomes an ordinary two-digit number |
| `620N·m` | `六百二十牛米` | `六百二十恩点米`, `六百二十N点m` | physical unit becomes a letter string |
| `AI` / `CEO` | `A I`, `C E O` | `人工智能`, `首席执行官` | original abbreviation is expanded into Chinese |

## Released Resources

| Resource | Location | Purpose |
|---|---|---|
| Dataset / schema | [data/](data/) | dev/public test text, target annotations, and schema |
| Scorer / validators | [scripts/](scripts/) | dataset validation, target-level scoring, leaderboard aggregation |
| Public ASR transcripts | [results/asr_transcripts/public_test/](results/asr_transcripts/public_test/) | fixed three-route public ASR transcripts |
| Public ASR results | [results/asr_results/public_test/](results/asr_results/public_test/) | merged ASR results for the seven TTS systems |
| Leaderboard data | [results/leaderboard.csv](results/leaderboard.csv), [results/leaderboard.json](results/leaderboard.json) | machine-readable leaderboard results |
| Web leaderboard | [GitHub Pages](https://jayden-x-l.github.io/cn-news-tts-bench/) | public leaderboard page |
| Full archive | [Zenodo DOI](https://doi.org/10.5281/zenodo.20822327) | audio packages, full ASR transcripts, core reproducibility package |
| Paper | [arXiv:2606.24714](https://arxiv.org/abs/2606.24714) | method, experiments, and limitations |

The Zenodo v0.1 archive includes:

| File | Contents |
|---|---|
| `cn-news-tts-bench-v0.1-core.zip` | GitHub core reproducibility package |
| `cn-news-tts-bench-v0.1-asr-transcripts-full.zip` | full dev/public-test ASR transcripts and scoring artifacts |
| `cn-news-tts-bench-v0.1-audio-dev-wav24k-mono.zip` | 7 TTS systems x 200 dev records = 1,400 wav files |
| `cn-news-tts-bench-v0.1-audio-public-test-wav24k-mono.zip` | 7 TTS systems x 800 public-test records = 5,600 wav files |
| `SHA256SUMS` | checksums for uploaded Zenodo files |

Canonical audio is normalized to 24 kHz mono wav. Provider-returned raw audio duplicates are not included.

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

`Strict Acc = correct / all_auto_evaluable_targets`. Unknown targets remain in the main denominator.

## Task Definition

Each sample is a short Chinese news-style sentence containing one or more pronunciation-risk targets. Each target includes acceptable readings and known-bad readings; the scorer evaluates these key readings at target level:

| Target | Positive reading examples | Negative reading examples |
|---|---|---|
| `117-116` | `一百一十七比一百一十六`, `一一七比一一六` | `一百一十七到一百一十六`, `一百一十七负一百一十六` |
| `苏-27` | `苏二十七`, `苏二七` | `苏负二十七`, `苏杠二十七`, `苏减二十七` |
| `80后` | `八零后` | `八十后` |
| `3.5%` | `百分之三点五` | `三点五百分号`, `三点五个百分点` |
| `620N·m` | `六百二十牛米` | `六百二十恩点米`, `六百二十N点m` |
| `AI` | `AI`, `A I` | `人工智能` |

The Raw Input Product Track allows only the TTS provider's default processing. It does not allow external rule frontends, LLM rewrites, SSML pronunciation hints, or manual edits to benchmark text. Provider-internal normalization is part of the evaluated product behavior.

## Dataset

| split | records | targets | auto-evaluable targets | optional targets |
|---|---:|---:|---:|---:|
| dev | 200 | 252 | 248 | 4 |
| test_public | 800 | 1008 | 992 | 16 |
| total | 1000 | 1260 | 1240 | 20 |

Core files:

```text
data/dev.jsonl
data/test_public.jsonl
data/dataset_summary.json
data/schema.json
```

Dataset details are in [docs/dataset_v0.1.md](docs/dataset_v0.1.md).

## Scoring Protocol

The official v0.1 score uses three fixed ASR routes:

| ASR route | Public transcript file |
|---|---|
| MiMo API ASR | [results/asr_transcripts/public_test/mimo_v2_5_asr.jsonl](results/asr_transcripts/public_test/mimo_v2_5_asr.jsonl) |
| SenseVoiceSmall | [results/asr_transcripts/public_test/sensevoice_small.jsonl](results/asr_transcripts/public_test/sensevoice_small.jsonl) |
| Paraformer-zh | [results/asr_transcripts/public_test/paraformer_zh.jsonl](results/asr_transcripts/public_test/paraformer_zh.jsonl) |

For each target and each ASR transcript, the scorer matches target-level positive and negative readings, then applies three-route voting:

| Route decisions | Final decision |
|---|---|
| at least two `correct` decisions | `correct` |
| at least two `wrong` decisions | `wrong` |
| otherwise | `unknown` |

Metrics:

```text
Strict Auto Accuracy = correct / all_auto_evaluable_targets
Resolved Accuracy    = correct / (correct + wrong)
Coverage             = (correct + wrong) / all_auto_evaluable_targets
Unknown Rate         = unknown / all_auto_evaluable_targets
```

See [docs/scoring.md](docs/scoring.md).

## Quick Reproduction

```bash
git clone https://github.com/Jayden-X-L/cn-news-tts-bench.git
cd cn-news-tts-bench

python3 scripts/validate_dataset.py data/dev.jsonl
python3 scripts/validate_dataset.py data/test_public.jsonl

python3 scripts/score_submission.py \
  --dataset data/test_public.jsonl \
  --asr-results results/asr_results/public_test/volcengine_tts.asr.jsonl \
  --model-id volcengine_tts \
  --output-dir /tmp/cn-news-tts-repro

python3 scripts/aggregate_leaderboard.py \
  --per-model-dir results/per_model_public_test \
  --results-dir /tmp/cn-news-tts-leaderboard/results \
  --site-dir /tmp/cn-news-tts-leaderboard/site

shasum -a 256 -c release/v0.1_core_checksums.sha256
```

For public leaderboard reproduction, replace `{model_id}` with:

```text
volcengine_tts
azure_speech_tts
google_cloud_tts
minimax_tts
aliyun_tts
mimo
aws_polly
```

## Evaluate a New TTS System

1. Read raw text from `data/dev.jsonl` or `data/test_public.jsonl`.
2. Generate one audio file per sample without external text normalization, LLM rewriting, SSML, or manual text fixes.
3. Prepare `system_card.json`, `manifest.json`, and an audio directory following [docs/submission.md](docs/submission.md).
4. Generate three-route ASR transcripts or provide equivalent ASR results following [docs/asr_results_format.md](docs/asr_results_format.md).
5. Run [scripts/score_submission.py](scripts/score_submission.py) to obtain target-level scores.

A minimal example is available at [examples/asr_results/example_model.asr.jsonl](examples/asr_results/example_model.asr.jsonl).

## Repository Layout

```text
cn-news-tts-bench/
  data/                         # dev/public test data and schema
  docs/                         # task, scoring, submission, release audit
  examples/                     # minimal ASR result example
  paper/                        # benchmark preprint note
  results/
    leaderboard.csv
    leaderboard.json
    asr_transcripts/public_test/
    asr_results/public_test/
    per_model_public_test/
  scripts/                      # validation, scoring, aggregation
  site/                         # GitHub Pages leaderboard
  tools/api_config_builder.html # local TTS API config builder
```

## Citation

Paper:

```bibtex
@misc{luo2026cnnewsttsbench,
  title = {CN-NewsTTS Bench: A Target-Level Automatic Benchmark for Raw-Input Chinese News Text-to-Speech Pronunciation Accuracy},
  author = {Luo, Shijun},
  year = {2026},
  eprint = {2606.24714},
  archivePrefix = {arXiv},
  primaryClass = {cs.CL}
}
```

Dataset:

```text
CN-NewsTTS Bench v0.1. Zenodo. https://doi.org/10.5281/zenodo.20822327
```

## License

- Code: [MIT](LICENSE)
- Dataset, fixed ASR transcripts, benchmark results, documentation, and metadata: [CC BY 4.0](LICENSE-DATA.md)
- Generated TTS audio is released on Zenodo as evaluation artifacts. Reuse may be subject to provider/API terms and should not be treated as an unrestricted speech-training corpus without separate rights review.
