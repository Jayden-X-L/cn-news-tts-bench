# ASR Results Format

评分脚本接受一个 JSONL 文件，每行对应一个样本：

```json
{
  "id": "dev_000001",
  "asr": {
    "mimo_strict": "苏二十七和歼十C战机参加了此次联合演训。",
    "whisper_small": "苏二七和歼十C战机参加了此次联合演训。",
    "sensevoice": "苏负二十七和歼十C战机参加了此次联合演训。"
  }
}
```

要求：

- 每个样本至少有 3 个 ASR transcript
- ASR 名称可以变化，但同一个提交内应保持一致
- transcript 应尽量保留实际听到的读法，不要做数字归一化
- 评分器只读取 `id` 和 `asr` 字段

