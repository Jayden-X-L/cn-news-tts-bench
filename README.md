# CN-NewsTTS Bench

[English README](README.en.md) | [DOI:10.5281/zenodo.20822327](https://doi.org/10.5281/zenodo.20822327) | [arXiv:2606.24714](https://arxiv.org/abs/2606.24714) | [预印本 PDF](https://arxiv.org/pdf/2606.24714) | [公开榜单](https://jayden-x-l.github.io/cn-news-tts-bench/) | [v0.1 Release](https://github.com/Jayden-X-L/cn-news-tts-bench/releases/tag/v0.1)

CN-NewsTTS Bench 是一个面向中文新闻裸 TTS 模型的开源、自动化、target-level 读法准确率 benchmark。

本 benchmark 只评估一个问题：

> 给定同一段原始中文新闻文本，不使用外部规则前端、LLM 改写、SSML 或人工修正，TTS 模型自身能否把关键新闻读法读对？

## 为什么做这个 benchmark

中文新闻文本里有大量普通文本很少连续出现、但新闻播报中非常高频的表面形式：比分、连字符、区间、型号、单位符号、百分比、英文缩写和中英数混排名称。例如 `96-91`、`苏-27`、`2028-2030年`、`620N·m`、`3.5%`、`80后`。这些写法对人类新闻编辑通常很清楚，但裸 TTS 很容易按通用文本归一化读错。

这类错读不是单纯的“声音不好听”，而是会改变信息含义：比分可能被读成范围，机型可能被读成负数，`80后` 可能被读成“八十后”，单位符号可能被逐字母读出。我们做这个 benchmark，是为了用公开、可复现、自动化的方式衡量各家 TTS 模型在真实中文新闻读法上的裸模型能力。

## v0.1 状态

v0.1 已包含并跑通：

- dev set：200 条
- public test set：800 条
- public test：992 个 auto-evaluable targets
- 三路固定 public ASR transcript
- target-level 三 ASR 投票评分脚本
- 七家 TTS public baseline 结果
- reproducibility checksum
- GitHub Pages 静态榜单
- arXiv 预印本论文：[`arXiv:2606.24714`](https://arxiv.org/abs/2606.24714)
- Zenodo 数据归档：[`10.5281/zenodo.20822327`](https://doi.org/10.5281/zenodo.20822327)

公开榜单：

- Zenodo dataset: [https://doi.org/10.5281/zenodo.20822327](https://doi.org/10.5281/zenodo.20822327)
- arXiv: [https://arxiv.org/abs/2606.24714](https://arxiv.org/abs/2606.24714)
- Preprint PDF: [https://arxiv.org/pdf/2606.24714](https://arxiv.org/pdf/2606.24714)
- Repository PDF copy: [paper/cn_newstts_bench_preprint.pdf](paper/cn_newstts_bench_preprint.pdf)
- Preprint markdown: [paper/cn_newstts_bench_preprint.md](paper/cn_newstts_bench_preprint.md)
- Web: [https://jayden-x-l.github.io/cn-news-tts-bench/](https://jayden-x-l.github.io/cn-news-tts-bench/)
- CSV: [results/leaderboard.csv](results/leaderboard.csv)
- JSON: [results/leaderboard.json](results/leaderboard.json)
- Release audit: [docs/release_v0.1_audit.md](docs/release_v0.1_audit.md)

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

`Strict Acc = correct / all auto-evaluable targets`。`unknown` 不从主榜分母里删除。

## 任务定义

每条样本是一段中文新闻风格短句，包含一个或多个读法风险目标，例如：

- `117-116`
- `苏-27`
- `80后`
- `3.5%`
- `N·m`
- `AI`

参评系统需要对每条输入文本生成一段音频。Raw Model Track 只允许 TTS provider 自身默认处理，不允许外部规则前端、LLM 改写、SSML pronunciation hint 或人工修改 benchmark 文本。

## 数据规模

| split | records | targets | auto-evaluable targets | optional targets |
|---|---:|---:|---:|---:|
| dev | 200 | 252 | 248 | 4 |
| test_public | 800 | 1008 | 992 | 16 |
| total | 1000 | 1260 | 1240 | 20 |

详见 [docs/dataset_v0.1.md](docs/dataset_v0.1.md)。

## 评分协议

v0.1 使用三路 ASR：

| ASR route | Public transcript file |
|---|---|
| MiMo API ASR | [results/asr_transcripts/public_test/mimo_v2_5_asr.jsonl](results/asr_transcripts/public_test/mimo_v2_5_asr.jsonl) |
| SenseVoiceSmall | [results/asr_transcripts/public_test/sensevoice_small.jsonl](results/asr_transcripts/public_test/sensevoice_small.jsonl) |
| Paraformer-zh | [results/asr_transcripts/public_test/paraformer_zh.jsonl](results/asr_transcripts/public_test/paraformer_zh.jsonl) |

对每个 target、每条 ASR transcript，评分器匹配 positive readings 和 negative readings，并做三 ASR 投票：

- 至少两路 `correct` -> `correct`
- 至少两路 `wrong` -> `wrong`
- 其他情况 -> `unknown`

主指标：

```text
Strict Auto Accuracy = correct / all_auto_evaluable_targets
```

辅助指标：

- Resolved Accuracy = correct / (correct + wrong)
- Coverage = (correct + wrong) / all_auto_evaluable_targets
- Unknown Rate = unknown / all_auto_evaluable_targets

## 复现

```bash
python3 scripts/validate_dataset.py data/dev.jsonl
python3 scripts/validate_dataset.py data/test_public.jsonl

python3 scripts/score_submission.py \
  --dataset data/test_public.jsonl \
  --asr-results results/asr_results/public_test/{model_id}.asr.jsonl \
  --model-id {model_id} \
  --output-dir results/per_model_public_test

python3 scripts/aggregate_leaderboard.py \
  --per-model-dir results/per_model_public_test \
  --results-dir results \
  --site-dir site

shasum -a 256 -c release/v0.1_core_checksums.sha256
```

## License

- Code: [MIT](LICENSE)
- Dataset、固定 ASR transcript、benchmark results 和文档：[CC BY 4.0](LICENSE-DATA.md)
- 本仓库不包含生成音频；生成音频可能受各 TTS provider 的单独条款约束。
