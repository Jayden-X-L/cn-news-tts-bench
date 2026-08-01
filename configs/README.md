# Configs

配置按是否可以公开分成两个目录：

```text
configs/
  public/                         # 可提交和发布
    site_metadata.json
    tts_api_config.schema.json
    tts_api_config.example.json
    api_config_builder.html
    examples/
  local/                          # 本地凭证，Git 忽略
    .gitignore
    tts_api_config.local.json
```

不要把真实 API key、service account JSON 或 credential 文件提交到 GitHub。

推荐做法：

1. 打开 `configs/public/api_config_builder.html`。
2. 在本地浏览器里填写 API 信息。
3. 导出 `tts_api_config.local.json`。
4. 保存为 `configs/local/tts_api_config.local.json`。

`configs/local/.gitignore` 会忽略该目录中的本地配置。

v0.1 首轮默认启用：

- MiMo
- Google Cloud TTS
- Azure Speech TTS
- MiniMax
- Aliyun CosyVoice
- Volcano / Doubao
- AWS Polly

OpenAI、ElevenLabs 保留为可选 provider；OpenAI 因当前 API 付款不可用，默认不进入首轮导出配置。
