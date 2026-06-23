# Local API Configs

本目录用于放本地 API 配置文件，例如：

```text
tts_api_config.local.json
```

不要把真实 API key、service account JSON 或 credential 文件提交到 GitHub。

推荐做法：

1. 打开 `tools/api_config_builder.html`
2. 在本地浏览器里填写 API 信息
3. 导出 `tts_api_config.local.json`
4. 放到 `configs/` 目录或其他本地安全目录

`configs/.gitignore` 默认忽略所有本地配置文件。

v0.1 首轮默认启用：

- MiMo
- Google Cloud TTS
- Azure Speech TTS
- MiniMax
- Aliyun CosyVoice
- Volcano / Doubao
- AWS Polly

OpenAI、ElevenLabs 保留为可选 provider；OpenAI 因当前 API 付款不可用，默认不进入首轮导出配置。
