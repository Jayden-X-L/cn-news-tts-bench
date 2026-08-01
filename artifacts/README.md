# Artifacts

本目录保存模型推理与评分产物，不包含任何训练 checkpoint。

```text
artifacts/
  tts_raw/                 # TTS provider 原始返回音频与生成 manifest（本地忽略）
    dev/
    public_test/
    smoke/
  tts_canonical/           # 统一为 24 kHz mono WAV 的标准音频（本地忽略）
    dev/
    public_test/
  asr_transcripts/         # 三路 ASR 的逐条推理输出
    dev/
    public_test/
  asr_merged/              # 按 TTS 系统合并后的 scorer 输入
    dev/
    public_test/
  scores/                  # 单模型评分、榜单及投稿元数据
    dev/
    public_test/
    submissions/
    leaderboard.csv
    leaderboard.json
```

v0.1 public test 的复现命令：

```bash
python3 scripts/score_submission.py \
  --dataset data/canonical/test_public.jsonl \
  --asr-results artifacts/asr_merged/public_test/{model_id}.asr.jsonl \
  --model-id {model_id} \
  --output-dir artifacts/scores/public_test

python3 scripts/aggregate_leaderboard.py \
  --per-model-dir artifacts/scores/public_test \
  --results-dir artifacts/scores \
  --site-dir site \
  --site-metadata configs/public/site_metadata.json
```

`tts_raw/`、`tts_canonical/`、dev 中间结果和运行分片默认由 `.gitignore` 排除；固定 public ASR、public merged results、public scores 与榜单可以进入版本控制。

生成 dev TTS 音频时，原始与标准化输出必须显式分开：

```bash
python3 scripts/run_tts_generation.py \
  --dataset data/canonical/dev.jsonl \
  --config configs/local/tts_api_config.local.json \
  --raw-output-dir artifacts/tts_raw/dev \
  --canonical-output-dir artifacts/tts_canonical/dev
```
