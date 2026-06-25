# CN-NewsTTS Bench

<div align="center">

**面向中文新闻 raw-input TTS 的 target-level 自动读法准确率基准**

[![arXiv](https://img.shields.io/badge/arXiv-2606.24714-b31b1b?style=for-the-badge)](https://arxiv.org/abs/2606.24714)
[![Zenodo DOI](https://img.shields.io/badge/Zenodo-10.5281%2Fzenodo.20822327-1682D4?style=for-the-badge)](https://doi.org/10.5281/zenodo.20822327)
[![Leaderboard](https://img.shields.io/badge/Leaderboard-GitHub%20Pages-00A3FF?style=for-the-badge)](https://jayden-x-l.github.io/cn-news-tts-bench/)
[![Release](https://img.shields.io/badge/Release-v0.1-16A34A?style=for-the-badge)](https://github.com/Jayden-X-L/cn-news-tts-bench/releases/tag/v0.1)

[English README](README.en.md) | [公开榜单](https://jayden-x-l.github.io/cn-news-tts-bench/) | [提交新系统](SUBMIT.md) | [论文](https://arxiv.org/abs/2606.24714) | [数据归档](https://doi.org/10.5281/zenodo.20822327)

</div>

---

## 为什么做这个 benchmark

CN-NewsTTS Bench 起源于作者在网易云音乐负责 AI 资讯播客期间遇到的真实线上播报问题反馈。我们观察到，中文新闻播报中频繁出现的比分、型号、单位、连字符、百分号、英文缩写和中英数混排名称，在直接输入 TTS 时，容易被通用文本归一化为另一种语义：`苏-27` 可能被读成“苏负二十七”，`96-91` 可能被读成范围，`620N·m` 可能被逐字母或按符号读出。

这类错读不是单纯的“声音不好听”，而是信息含义被改变。因此，CN-NewsTTS Bench 只评估一个明确问题：在不使用外部规则前端、LLM 改写、SSML 或人工修正的条件下，TTS 产品能否把中文新闻中的关键读法目标读对。它不是 MOS，也不是整句 WER/CER，而是一个面向 raw-input 中文新闻 TTS 的 **target-level** 自动读法准确率 benchmark。

本 benchmark 发布的是公开、可复现的新闻式测试集和自动评估协议，不包含用户数据、内部业务数据、线上日志或未公开内容。

## 高风险错读示例

这些不是罕见边角 case，而是中文新闻播报里会直接改变信息含义的读法错误。CN-NewsTTS Bench 把这类错误显式拆成 target-level positive readings 和 negative readings，让榜单能定位“哪个目标被读错”，而不只给整句平均分。

| Written target | 新闻中应保留的读法 | 常见错读形态 | 含义漂移 |
|---|---|---|---|
| `117-116` | `一百一十七比一百一十六` | `一百一十七到一百一十六`、`一百一十七负一百一十六` | 比分变成范围或减法 |
| `苏-27` | `苏二十七`、`苏二七` | `苏负二十七`、`苏杠二十七` | 军机型号变成数学表达 |
| `2028-2030年` | `二零二八到二零三零年` | `二零二八负二零三零年` | 年份区间变成负号表达 |
| `3.5%` | `百分之三点五` | `三点五百分号`、`三点五个百分点` | 百分比、百分点和符号读法混淆 |
| `80后` | `八零后` | `八十后` | 代际标签变成普通两位数 |
| `620N·m` | `六百二十牛米` | `六百二十恩点米`、`六百二十N点m` | 物理单位变成字母串 |
| `AI` / `CEO` | `A I`、`C E O` | `人工智能`、`首席执行官` | 原文缩写被擅自展开 |

## 发布内容

| Resource | Location | 用途 |
|---|---|---|
| Dataset / schema | [data/](data/) | dev/public test 文本、target 标注和数据 schema |
| Scorer / validators | [scripts/](scripts/) | 数据校验、target-level 评分、榜单聚合 |
| Public ASR transcripts | [results/asr_transcripts/public_test/](results/asr_transcripts/public_test/) | 三路固定 public ASR transcript |
| Public ASR results | [results/asr_results/public_test/](results/asr_results/public_test/) | 七家 TTS 的合并 ASR 结果 |
| Leaderboard data | [results/leaderboard.csv](results/leaderboard.csv), [results/leaderboard.json](results/leaderboard.json) | 可机器读取的榜单结果 |
| Web leaderboard | [GitHub Pages](https://jayden-x-l.github.io/cn-news-tts-bench/) | 在线公开榜单 |
| Full archive | [Zenodo DOI](https://doi.org/10.5281/zenodo.20822327) | 音频包、完整 ASR 转写、核心复现包 |
| Paper | [arXiv:2606.24714](https://arxiv.org/abs/2606.24714) | 方法、实验和局限性说明 |

Zenodo v0.1 归档包含：

| File | 内容 |
|---|---|
| `cn-news-tts-bench-v0.1-core.zip` | GitHub 核心复现包 |
| `cn-news-tts-bench-v0.1-asr-transcripts-full.zip` | dev/public test 完整 ASR 转写与评分产物 |
| `cn-news-tts-bench-v0.1-audio-dev-wav24k-mono.zip` | 7 家 TTS x 200 dev records = 1,400 wav files |
| `cn-news-tts-bench-v0.1-audio-public-test-wav24k-mono.zip` | 7 家 TTS x 800 public-test records = 5,600 wav files |
| `SHA256SUMS` | Zenodo 上传文件校验和 |

音频均为 canonical 24 kHz mono wav；provider 返回的原始重复音频不包含在归档中。

## v0.1 Public Test Leaderboard

ASR ensemble：MiMo API ASR + SenseVoiceSmall + Paraformer-zh。

| Rank | TTS system | Strict Acc | Coverage | Resolved Acc | Correct | Wrong | Unknown |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | 火山 / 豆包 TTS | 0.879 | 0.913 | 0.962 | 872 | 34 | 86 |
| 2 | Azure Speech TTS | 0.756 | 0.756 | 1.000 | 750 | 0 | 242 |
| 3 | Google Cloud TTS | 0.604 | 0.861 | 0.701 | 599 | 255 | 138 |
| 4 | MiniMax TTS | 0.548 | 0.850 | 0.645 | 544 | 299 | 149 |
| 5 | 阿里云 CosyVoice | 0.472 | 0.533 | 0.885 | 468 | 61 | 463 |
| 6 | MiMo TTS | 0.275 | 0.628 | 0.438 | 273 | 350 | 369 |
| 7 | AWS Polly | 0.244 | 0.570 | 0.428 | 242 | 323 | 427 |

`Strict Acc = correct / all_auto_evaluable_targets`。`unknown` 不从主榜分母里删除。

## 任务定义

每条样本是一段中文新闻风格短句，包含一个或多个读法风险目标。每个 target 都带有可接受读法和已知错误读法，评分器只在 target level 上判断这些关键读法：

| Target | Positive reading examples | Negative reading examples |
|---|---|---|
| `117-116` | `一百一十七比一百一十六`、`一一七比一一六` | `一百一十七到一百一十六`、`一百一十七负一百一十六` |
| `苏-27` | `苏二十七`、`苏二七` | `苏负二十七`、`苏杠二十七`、`苏减二十七` |
| `80后` | `八零后` | `八十后` |
| `3.5%` | `百分之三点五` | `三点五百分号`、`三点五个百分点` |
| `620N·m` | `六百二十牛米` | `六百二十恩点米`、`六百二十N点m` |
| `AI` | `AI`、`A I` | `人工智能` |

Raw Input Product Track 只允许 TTS provider 自身默认处理，不允许外部规则前端、LLM 改写、SSML pronunciation hint 或人工修改 benchmark 文本。Provider 内部 normalization 视为被测产品行为的一部分。

## 数据规模

| split | records | targets | auto-evaluable targets | optional targets |
|---|---:|---:|---:|---:|
| dev | 200 | 252 | 248 | 4 |
| test_public | 800 | 1008 | 992 | 16 |
| total | 1000 | 1260 | 1240 | 20 |

核心文件：

```text
data/dev.jsonl
data/test_public.jsonl
data/dataset_summary.json
data/schema.json
```

数据说明见 [docs/dataset_v0.1.md](docs/dataset_v0.1.md)。

## 评分协议

v0.1 使用三路固定 ASR：

| ASR route | Public transcript file |
|---|---|
| MiMo API ASR | [results/asr_transcripts/public_test/mimo_v2_5_asr.jsonl](results/asr_transcripts/public_test/mimo_v2_5_asr.jsonl) |
| SenseVoiceSmall | [results/asr_transcripts/public_test/sensevoice_small.jsonl](results/asr_transcripts/public_test/sensevoice_small.jsonl) |
| Paraformer-zh | [results/asr_transcripts/public_test/paraformer_zh.jsonl](results/asr_transcripts/public_test/paraformer_zh.jsonl) |

对每个 target、每条 ASR transcript，评分器匹配 positive readings 和 negative readings，并做三路投票：

| Route decisions | Final decision |
|---|---|
| 至少两路 `correct` | `correct` |
| 至少两路 `wrong` | `wrong` |
| 其他情况 | `unknown` |

主指标：

```text
Strict Auto Accuracy = correct / all_auto_evaluable_targets
Resolved Accuracy    = correct / (correct + wrong)
Coverage             = (correct + wrong) / all_auto_evaluable_targets
Unknown Rate         = unknown / all_auto_evaluable_targets
```

完整协议见 [docs/scoring.md](docs/scoring.md)。

## 快速复现

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

复现 public leaderboard 时可以把 `{model_id}` 替换为：

```text
volcengine_tts
azure_speech_tts
google_cloud_tts
minimax_tts
aliyun_tts
mimo
aws_polly
```

## 评测新的 TTS 系统

一页式提交流程见 [SUBMIT.md](SUBMIT.md)。问题和协作可联系
xiaobiluo@gmail.com。

1. 从 `data/dev.jsonl` 或 `data/test_public.jsonl` 读取原始文本。
2. 每条样本生成一个音频文件，不做外部 text normalization、LLM rewrite、SSML 或手工修正。
3. 按 [docs/submission.md](docs/submission.md) 准备 `system_card.json`、`manifest.json` 和音频目录。
4. 用三路 ASR 生成 transcript，或按 [docs/asr_results_format.md](docs/asr_results_format.md) 提供等价 ASR result。
5. 运行 [scripts/score_submission.py](scripts/score_submission.py) 得到 target-level 分数。

提交样例见 [examples/asr_results/example_model.asr.jsonl](examples/asr_results/example_model.asr.jsonl)。

## 仓库结构

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

## 引用

论文：

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

数据：

```text
CN-NewsTTS Bench v0.1. Zenodo. https://doi.org/10.5281/zenodo.20822327
```

## License

- Code: [MIT](LICENSE)
- Dataset、固定 ASR transcripts、benchmark results、文档和 metadata：[CC BY 4.0](LICENSE-DATA.md)
- 生成 TTS 音频作为 evaluation artifacts 发布在 Zenodo；复用可能受各 provider/API 条款约束，不应在未做额外权利审查时视为无限制语音训练语料。

## Contact

Leaderboard submission questions: xiaobiluo@gmail.com.
