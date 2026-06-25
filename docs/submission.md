# Submission Format

一页式提交流程见 [../SUBMIT.md](../SUBMIT.md)。问题和协作可联系
xiaobiluo@gmail.com。

每个参评模型提交一个目录：

```text
submissions/{model_id}/
  system_card.json
  manifest.json
  audio/
    dev_000001.wav
    dev_000002.wav
```

## system_card.json

可复制示例见
[../examples/submissions/example_model/system_card.json](../examples/submissions/example_model/system_card.json)。

```json
{
  "model_id": "example_model",
  "model_name": "Example TTS",
  "organization": "Example Lab",
  "open_source": true,
  "model_url": "https://example.com/model",
  "raw_model_track": true,
  "external_frontend": false,
  "llm_rewrite": false,
  "ssml": false,
  "manual_text_fix": false,
  "voice": "default",
  "sample_rate": 24000,
  "submission_date": "2026-06-20"
}
```

## manifest.json

可复制示例见
[../examples/submissions/example_model/manifest.json](../examples/submissions/example_model/manifest.json)。

```json
{
  "model_id": "example_model",
  "dataset": "dev.sample",
  "items": [
    {
      "id": "dev_000001",
      "audio_path": "audio/dev_000001.wav"
    }
  ]
}
```

`audio_path` 是相对提交目录的路径。未来正式榜单也可允许 `audio_url`，用于 GitHub Release、Hugging Face Dataset 或对象存储。

## Hard Rules

Raw Model Track 不允许：

- 外部规则前端
- LLM 改写
- SSML
- 人工修正测试集文本
- 针对测试集 target 编写特殊替换规则

违反规则的提交应移出主榜，可另列 system track。
