# CN-NewsTTS Bench

面向中文新闻裸 TTS 模型的开源自动化读法准确率 benchmark。

本 benchmark 只评估一个问题：

> 给定同一段原始中文新闻文本，不使用外部规则前端、LLM 改写、SSML 或人工修正，TTS 模型自身能否把关键新闻读法读对？

## 当前状态

这是 v0.1 初版，已经包含并跑通：

- 数据 schema
- dev set：200 条
- public test set：800 条
- 提交格式说明
- target-level 三 ASR 投票评分脚本
- 三路 ASR public transcript
- 七家 TTS public baseline 结果
- leaderboard 聚合脚本和 GitHub Pages 静态榜单

当前 public test 主榜见 [results/leaderboard.csv](results/leaderboard.csv) 和 [site/leaderboard.json](site/leaderboard.json)。

## v0.1 首轮 TTS Baselines

当前首轮已跑 7 个可实际获取的商业/产品 TTS：

- MiMo TTS
- Google Cloud TTS
- Azure Speech TTS
- MiniMax TTS
- Aliyun CosyVoice
- Volcano / Doubao TTS
- AWS Polly

OpenAI TTS 暂不纳入 v0.1 首轮官方结果，因为当前 API 付款路径不可用；后续可作为社区补充或第二批可选 baseline。

## 目录结构

```text
cn_news_tts_bench/
  data/
    dev.jsonl
    test_public.jsonl
    dataset_summary.json
    dev.sample.jsonl
    schema.json
  docs/
    task.md
    dataset_v0.1.md
    submission.md
    scoring.md
    license_policy.md
  examples/
    asr_results/
      example_model.asr.jsonl
  scripts/
    validate_dataset.py
    validate_submission.py
    score_submission.py
    aggregate_leaderboard.py
    run_tts_generation.py
  results/
    leaderboard.csv
    leaderboard.json
    per_model_public_test/
    asr_results/public_test/
    asr_transcripts/public_test/
    tts_generation/            # local only, ignored by git
  site/
    index.html
    leaderboard.js
    leaderboard.json
```

## v0.1 Public Test Leaderboard

ASR ensemble：MiMo API ASR + SenseVoiceSmall + Paraformer-zh。每个模型 public test 有 800 条音频、992 个 auto-evaluable targets。

| Rank | TTS model | Strict Acc | Coverage | Resolved Acc | Correct | Wrong | Unknown |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | volcengine_tts | 0.879 | 0.913 | 0.962 | 872 | 34 | 86 |
| 2 | azure_speech_tts | 0.756 | 0.756 | 1.000 | 750 | 0 | 242 |
| 3 | google_cloud_tts | 0.604 | 0.861 | 0.701 | 599 | 255 | 138 |
| 4 | minimax_tts | 0.548 | 0.850 | 0.645 | 544 | 299 | 149 |
| 5 | aliyun_tts | 0.472 | 0.533 | 0.885 | 468 | 61 | 463 |
| 6 | mimo | 0.275 | 0.628 | 0.438 | 273 | 350 | 369 |
| 7 | aws_polly | 0.244 | 0.570 | 0.428 | 242 | 323 | 427 |

完整 per-model breakdown 在 [results/per_model_public_test](results/per_model_public_test)。v0.1 发布审计见 [docs/release_v0.1_audit.md](docs/release_v0.1_audit.md)。

## 快速验证

```bash
cd /Users/shijunluo/Downloads/cn_news_tts_bench
python3 scripts/validate_dataset.py data/dev.jsonl
python3 scripts/validate_dataset.py data/test_public.jsonl
python3 scripts/validate_dataset.py data/dev.sample.jsonl
python3 scripts/score_submission.py \
  --dataset data/dev.sample.jsonl \
  --asr-results examples/asr_results/example_model.asr.jsonl \
  --model-id example_model \
  --output-dir results/per_model
python3 scripts/aggregate_leaderboard.py \
  --per-model-dir results/per_model_public_test \
  --results-dir results \
  --site-dir site
```

## 本地生成 dev TTS 音频

真实 API key 放在本地 `tts_api_config.local.json`，不要提交。生成 dev set 音频：

```bash
cd /Users/shijunluo/Downloads/cn_news_tts_bench
python3 scripts/run_tts_generation.py \
  --dataset data/dev.jsonl \
  --config tts_api_config.local.json \
  --output-dir results/tts_generation/dev
```

脚本会断点续跑，跳过已经存在的 `24kHz mono wav`。provider 原始返回音频保存在 `raw_audio/`，统一转码后的 ASR 输入音频保存在 `audio_wav_24k_mono/`。

v0.1 public baseline 音频已在本地生成并用于评分，但 `results/tts_generation/` 默认不提交到 GitHub。正式公开音频包建议放 Zenodo、Hugging Face Dataset 或 GitHub Release，并先确认各商业 TTS provider 的再分发条款。

然后打开：

```text
/Users/shijunluo/Downloads/cn_news_tts_bench/site/index.html
```

## 本地 API 配置工具

填写商业 TTS API 信息时，可以直接打开：

```text
/Users/shijunluo/Downloads/cn_news_tts_bench/tools/api_config_builder.html
```

页面会导出 `tts_api_config.local.json`。真实 key 不要提交到 GitHub；`configs/.gitignore` 已默认忽略本地配置文件。

## v0.1 数据规模

| split | records | targets | auto-evaluable targets | optional targets |
|---|---:|---:|---:|---:|
| dev | 200 | 252 | 248 | 4 |
| test_public | 800 | 1008 | 992 | 16 |
| total | 1000 | 1260 | 1240 | 20 |

详见 [docs/dataset_v0.1.md](docs/dataset_v0.1.md)。

## v0.1 可复现文件

核心文件 checksum：

```bash
shasum -a 256 -c release/v0.1_core_checksums.sha256
```

注意：checksum 覆盖数据、评分脚本、三路 public ASR transcript、merge summary 和 leaderboard，不覆盖本地 API key、日志或生成音频。

## License

- Code: [MIT](LICENSE)
- Dataset, fixed ASR transcripts, benchmark results, and documentation: [CC BY 4.0](LICENSE-DATA.md)
- Generated TTS audio is not included in this repository and may be subject to separate provider terms.

## 主指标

```text
Strict Auto Accuracy = correct / all_targets
```

辅助指标：

- Resolved Accuracy = correct / (correct + wrong)
- Coverage = (correct + wrong) / all_targets
- Unknown Rate = unknown / all_targets
- ASR Disagreement Rate = non-unanimous ASR decisions / all_targets

`unknown` 不从主榜分母里删除。

## 重要边界

v0.1 主榜只纳入 ASR 文本可区分的读法目标，例如：

- `117-116` 读作“比”还是“到/负”
- `苏-27` 读作“苏二七/苏二十七”还是“苏负二十七”
- `80后` 读作“八零后”还是“八十后”
- `3.5%` 读作“百分之三点五”还是“三点五百分号”
- `AI` 逐字母读还是被翻译成“人工智能”

纯同形多音字如“重庆”“行长”“增长”，普通 ASR 文本转写往往仍输出同一汉字，无法稳定自动判断真实声调。此类样本先放入 optional audit，不进入 v0.1 主榜。
