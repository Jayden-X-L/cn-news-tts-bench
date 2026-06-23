# CN-NewsTTS Bench: A Target-Level Automatic Benchmark for Raw Chinese News TTS Pronunciation

Draft: 2026-06-23
Status: preprint draft, not yet submitted

## Abstract

Chinese news text contains dense, high-impact surface forms whose intended readings depend on news conventions rather than ordinary character-level pronunciation. Examples include sports scores such as `117-116`, military model names such as `苏-27`, generation labels such as `80后`, percentages, unit symbols, English abbreviations, and mixed alphanumeric product names. A text-to-speech (TTS) system that reads these forms incorrectly may preserve the written text while changing the spoken meaning. However, existing public TTS evaluations rarely provide a reproducible, target-level benchmark for this specific news-pronunciation problem.

We introduce CN-NewsTTS Bench v0.1, an open benchmark for evaluating the pronunciation accuracy of raw Chinese news TTS systems. The benchmark defines a Raw Model Track in which each system receives the same original text without external rule frontends, LLM rewriting, SSML hints, or manual corrections. It contains a 200-record development set and an 800-record public test set with 992 public auto-evaluable targets. We evaluate TTS outputs using a three-ASR ensemble consisting of MiMo API ASR, SenseVoiceSmall, and Paraformer-zh. For each target, the scorer matches positive and negative reading patterns in ASR transcripts and applies target-level voting to produce `correct`, `wrong`, or `unknown` decisions.

We release the data schema, dev/public splits, fixed public ASR transcripts, scoring scripts, leaderboard site, release audit, and initial results for seven product TTS systems: MiMo TTS, Google Cloud TTS, Azure Speech TTS, MiniMax TTS, Aliyun CosyVoice, Volcano/Doubao TTS, and AWS Polly. The best v0.1 public score is 0.879 Strict Auto Accuracy, while several widely used systems remain below 0.60, indicating that news-specific reading accuracy remains a practical gap even for production TTS services. CN-NewsTTS Bench is intended as a reproducible public benchmark for tracking raw-model pronunciation capability on Chinese news text.

## 1. Introduction

Chinese news writing frequently compresses meaning into short symbolic forms. In a single news paragraph, a TTS system may encounter sports scores, date ranges, stock and product names, military aircraft models, percentages, units, English abbreviations, and mixed-script names. These forms are common in production news feeds, but many are ambiguous under generic text normalization. A hyphen can mark a score, a date range, or a negative number. A digit sequence can be a model identifier, a cardinal number, or part of a brand. A Latin abbreviation can be spelled, translated, or silently normalized.

This benchmark focuses on the spoken reading of such forms. The input string itself is usually unambiguous to a human news editor, but a raw TTS system may choose a reading that changes the intended meaning. For example, reading `117-116` as a range rather than a basketball score changes the relation between the numbers; reading `苏-27` as "Su negative twenty-seven" changes a military model name into a nonsensical expression; reading `80后` as "eighty-hou" loses the Chinese generation-label convention.

Despite the practical importance of these errors, public evaluation resources for Chinese TTS often focus on naturalness, intelligibility, MOS-style listening quality, or general pronunciation quality rather than target-level correctness for news text. Manual listening evaluation is expensive and hard to reproduce at leaderboard scale. ASR round-trip evaluation is cheaper, but direct transcript comparison is too coarse: the benchmark needs to know whether a specific target was read as the intended expression.

CN-NewsTTS Bench v0.1 addresses this gap with a reproducible target-level protocol. The benchmark is deliberately narrow: it does not claim to measure all dimensions of TTS quality. Instead, it asks whether a TTS system, used in a raw product-like configuration, can read high-risk Chinese news targets correctly.

## 2. Contributions

This preprint contributes:

1. A public benchmark for raw Chinese news TTS reading accuracy, with a 200-record dev set and an 800-record public test set.
2. A target-level annotation schema with positive and negative readings for news-specific surface forms.
3. A Raw Model Track that excludes external rule frontends, LLM rewriting, SSML hints, and manual text fixes.
4. A three-ASR automatic evaluation protocol using MiMo API ASR, SenseVoiceSmall, and Paraformer-zh.
5. A strict target-level scoring method that counts `unknown` targets against the main score.
6. Initial public results for seven product TTS systems.
7. An open-source reproducibility toolkit, including fixed ASR transcripts, scoring scripts, leaderboard data, release audit, and GitHub Pages dashboard.

The contribution is a benchmark and reproducible evaluation protocol. Mechanism-discovery claims about why TTS and ASR systems share blind spots are outside the scope of this paper and are handled separately.

## 3. Benchmark Design

### 3.1 Raw Model Track

The v0.1 main leaderboard defines a Raw Model Track. Each TTS system receives the same benchmark text. The following are allowed:

- the TTS provider's own built-in text normalization and frontend
- default or provider-recommended inference configuration
- a fixed voice chosen before evaluation

The following are not allowed:

- external rule frontend
- LLM rewrite or paraphrase
- SSML or pronunciation hints
- manual correction of benchmark text
- target-specific rules written after seeing the test set

This track is designed to measure the product-facing raw capability of TTS systems rather than the performance of a complete text normalization pipeline.

### 3.2 Target Categories

v0.1 contains targets from categories that are common in Chinese news and can be evaluated from ordinary ASR text:

| Category | Example | Intended distinction |
|---|---|---|
| sports score | `96-91`, `4-3` | score reading vs range/subtraction |
| range hyphen | `6-8分钟` | range reading |
| year range | `2028-2030年` | year-range reading |
| military model | `苏-27`, `F-35` | model designator vs negative number |
| vehicle model | `小米SU7`, `ET5` | model/brand reading |
| abbreviation | `AI`, `ETF`, `IPO` | abbreviation spelling vs translation |
| brand mixed | mixed Chinese/Latin/digit names | brand-specific mixed reading |
| unit symbol | `N·m`, `GW` | unit reading |
| percentage | `3.5%` | percentage reading |
| generation label | `80后`, `90后` | Chinese generation-label reading |

Pure same-character polyphones, such as words whose tonal reading differs but whose ASR transcript remains the same Chinese characters, are included only as optional audit targets in v0.1. They are excluded from the main automatic score because ordinary ASR text cannot reliably expose the relevant tonal contrast.

### 3.3 Dataset Splits

| Split | Records | Targets | Auto-evaluable targets | Optional targets |
|---|---:|---:|---:|---:|
| dev | 200 | 252 | 248 | 4 |
| test_public | 800 | 1008 | 992 | 16 |
| total | 1000 | 1260 | 1240 | 20 |

The public test set is released to make the benchmark fully reproducible and easy to extend. A future private test set can be added if the benchmark becomes competitive enough to require anti-overfitting protection.

### 3.4 Target Annotation

Each target includes:

- the written span
- category and group labels
- `positive_readings`
- `negative_readings`
- whether it is `auto_evaluable`

The scorer normalizes ASR text with Unicode normalization, whitespace removal, punctuation removal, and case folding. Negative readings are matched before positive readings to reduce false positives in transcripts that contain repeated or explanatory text.

## 4. Automatic Evaluation Protocol

### 4.1 TTS Generation

For the initial v0.1 baseline run, each of seven systems generated one audio file per public test record. Each system used one fixed voice and provider-level default normalization. Generated audio was converted to 24 kHz mono WAV for ASR where needed.

Generated audio is not included in the GitHub repository because redistribution terms differ across commercial providers. The benchmark release includes fixed ASR transcripts and scoring outputs so that the leaderboard can be reproduced without rerunning commercial TTS.

### 4.2 Three-ASR Ensemble

The official v0.1 public score uses:

| ASR route | Source | Public rows |
|---|---|---:|
| MiMo API ASR | API | 5600 |
| SenseVoiceSmall | open-source local inference | 5600 |
| Paraformer-zh | open-source local inference | 5600 |

MiMo API ASR was run in five non-overlapping shards. The raw retry logs contain a small number of refusal-like responses; all affected samples were retried. The canonical public MiMo ASR transcript contains 5600 final `ok` rows and no refusal-like final transcript.

### 4.3 Target-Level Voting

For each target and each ASR transcript:

1. Match negative readings. If matched, the single-ASR decision is `wrong`.
2. Otherwise match positive readings. If matched, the single-ASR decision is `correct`.
3. Otherwise the single-ASR decision is `unknown`.

The three single-ASR decisions are combined:

| ASR decisions | Final decision |
|---|---|
| at least 2 correct | correct |
| at least 2 wrong | wrong |
| otherwise | unknown |

The main metric is:

```text
Strict Auto Accuracy = correct / all_auto_evaluable_targets
```

Auxiliary metrics are:

```text
Resolved Accuracy = correct / (correct + wrong)
Coverage = (correct + wrong) / all_auto_evaluable_targets
Unknown Rate = unknown / all_auto_evaluable_targets
ASR Disagreement Rate = non-unanimous target decisions / all_auto_evaluable_targets
```

Unlike resolved accuracy, strict accuracy does not remove `unknown` targets from the denominator. This makes the main metric conservative and discourages systems from producing audio that the evaluation ensemble cannot confidently resolve.

## 5. Initial Baselines

The v0.1 initial public leaderboard evaluates seven TTS systems:

| model_id | Provider/API | Model | Voice |
|---|---|---|---|
| volcengine_tts | Volcengine Speech Synthesis API | seed-tts-2.0-standard | configured Chinese voice |
| azure_speech_tts | Azure AI Speech TTS | azure-neural-tts | zh-CN-XiaoxiaoNeural |
| google_cloud_tts | Google Cloud Text-to-Speech | Chirp 3 HD | cmn-CN-Chirp3-HD-Kore |
| minimax_tts | MiniMax Speech API | speech-2.8-hd | configured Mandarin news voice |
| aliyun_tts | DashScope / Model Studio Speech API | cosyvoice-v3-plus | configured Chinese voice |
| mimo | MiMo TTS API | mimo-v2.5-tts | 白桦 |
| aws_polly | Amazon Polly | polly-neural | Zhiyu |

OpenAI TTS is not included in v0.1 because the API payment path was unavailable for this run. It can be added as a community or later official baseline.

## 6. Results

### 6.1 Public Leaderboard

| Rank | TTS system | Strict Acc | Coverage | Resolved Acc | Correct | Wrong | Unknown |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | Volcano / Doubao TTS | 0.879 | 0.913 | 0.962 | 872 | 34 | 86 |
| 2 | Azure Speech TTS | 0.756 | 0.756 | 1.000 | 750 | 0 | 242 |
| 3 | Google Cloud TTS | 0.604 | 0.861 | 0.701 | 599 | 255 | 138 |
| 4 | MiniMax TTS | 0.548 | 0.850 | 0.645 | 544 | 299 | 149 |
| 5 | Aliyun CosyVoice | 0.472 | 0.533 | 0.885 | 468 | 61 | 463 |
| 6 | MiMo TTS | 0.275 | 0.628 | 0.438 | 273 | 350 | 369 |
| 7 | AWS Polly | 0.244 | 0.570 | 0.428 | 242 | 323 | 427 |

The best system reaches 0.879 strict accuracy, but several product systems remain below 0.60. This indicates that Chinese news-specific reading accuracy remains uneven across deployed TTS products.

### 6.2 Interpreting Coverage and Resolved Accuracy

Azure Speech TTS has zero `wrong` targets under the three-ASR vote, giving it a resolved accuracy of 1.0, but it also has 242 `unknown` targets and a strict accuracy of 0.756. In contrast, Google Cloud TTS and MiniMax have higher coverage but many more wrong targets. This illustrates why the benchmark reports strict accuracy, coverage, and resolved accuracy together: strict accuracy is the main conservative score, while the other metrics separate unrecognized cases from clearly wrong readings.

### 6.3 Example Target Types

Representative public benchmark cases include:

| Target type | Example input | Expected reading behavior | Common risk |
|---|---|---|---|
| sports score | `96-91`, `4-3` | read as score separators | range/subtraction |
| military model | `F-35`, `苏-27` | read as model names | negative-number reading |
| generation label | `80后` | read as `八零后` | `八十后` |
| unit symbol | `620N·m` | read as torque unit | letter-by-letter or unstable normalization |

## 7. Reproducibility

The release repository contains:

- dev and public test data
- schema and validation scripts
- fixed public ASR transcripts
- merged per-model ASR results
- target-level scoring scripts
- per-model scores and breakdowns
- leaderboard CSV/JSON
- GitHub Pages dashboard
- release audit
- checksum manifest

Core checksum verification:

```bash
shasum -a 256 -c release/v0.1_core_checksums.sha256
```

Repository:

```text
https://github.com/Jayden-X-L/cn-news-tts-bench
```

Leaderboard:

```text
https://jayden-x-l.github.io/cn-news-tts-bench/
```

## 8. Limitations

First, the benchmark is automatic and should not be treated as a replacement for human listening tests. It is designed for scalable public comparison, not final perceptual validation.

Second, ASR text may still hide some pronunciation errors. The three-ASR ensemble reduces single-ASR brittleness but cannot fully solve ASR language-model correction or same-character tonal ambiguity.

Third, v0.1 uses a public test set. This favors reproducibility and transparency but may eventually require a hidden test split if leaderboard overfitting becomes a concern.

Fourth, generated commercial TTS audio is not redistributed in the repository due to provider-specific terms. The release therefore fixes ASR transcripts as the reproducible scoring artifact.

Fifth, the current target inventory emphasizes surface forms that can be evaluated from ASR text. Future versions should add phoneme- or pinyin-level evaluation for same-character polyphones and tonal errors.

## 9. Future Work

Future benchmark versions can extend CN-NewsTTS Bench in several directions:

- add a hidden test set for competitive submissions
- add more open-source TTS systems
- add OpenAI TTS and other international APIs when accessible
- add phoneme/pinyin-level evaluation for same-character polyphones
- release provider-permitted audio packages via Zenodo or Hugging Face Dataset
- add human audit subsets for estimating automatic-evaluation precision
- expand the target taxonomy using real-world news production logs

## 10. Conclusion

CN-NewsTTS Bench v0.1 provides a reproducible public benchmark for target-level pronunciation accuracy in raw Chinese news TTS. By combining a news-specific target schema, fixed public splits, three-ASR voting, strict scoring, and open tooling, the benchmark makes it possible to compare production TTS systems on a practical class of errors that are often missed by broader naturalness-oriented evaluations. The initial seven-system leaderboard shows substantial variation across providers, suggesting that Chinese news reading remains a meaningful and measurable challenge for modern TTS systems.

## References

References are intentionally left as a TODO for the next preprint pass. The camera-ready version should cite prior work on TTS evaluation, Chinese text normalization, ASR-assisted speech evaluation, open speech benchmarks, and the specific ASR systems used in the v0.1 ensemble.
