# Directory Layout

项目按“输入、配置、推理产物、论文、发布和工作输出”分层：

```text
cn_news_tts_bench/
  data/
    canonical/
    runtime/
  configs/
    public/
    local/
  artifacts/
    tts_raw/
    tts_canonical/
    asr_transcripts/
    asr_merged/
    scores/
  papers/
    arxiv/
    iscslp2026/
    icassp2027/
  releases/
    v0.1/
  output/
    submission/
    outreach/
    qa/
  scripts/
  docs/
  site/
```

## Ownership rules

| Directory | Source of truth | Git policy |
|---|---|---|
| `data/canonical/` | Benchmark 输入、schema、summary | 跟踪 |
| `data/runtime/` | 临时分片和重试输入 | 忽略 |
| `configs/public/` | 无密钥 schema、样例与站点元数据 | 跟踪 |
| `configs/local/` | API key 和本地 provider 配置 | 忽略，`.gitignore` 除外 |
| `artifacts/tts_raw/` | 厂商原始音频和 TTS manifest | 忽略，本地/外部归档 |
| `artifacts/tts_canonical/` | 24 kHz mono WAV | 忽略，本地/外部归档 |
| `artifacts/asr_transcripts/` | 单路 ASR 推理输出 | public 固定结果跟踪，dev/shard 忽略 |
| `artifacts/asr_merged/` | 三路 ASR 合并结果 | public 跟踪，dev 忽略 |
| `artifacts/scores/` | 评分明细与排行榜 | public 跟踪，dev 忽略 |
| `papers/` | 各投稿版本源文件 | 按版本管理 |
| `releases/` | checksum 与发布审计 | 跟踪 |
| `output/submission/` | 最终上传文件 | 人工确认后决定是否跟踪 |
| `output/outreach/` | 厂商沟通草稿 | 人工确认后决定是否跟踪 |
| `output/qa/` | 日志、渲染图和构建中间文件 | 忽略 |

不要在顶层重新创建 `results/`、`paper/`、`release/`、`logs/` 或 `tmp/`；相关程序默认路径已经迁移到以上目录。
