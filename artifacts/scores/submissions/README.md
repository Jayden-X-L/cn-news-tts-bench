# Leaderboard Submissions

完整流程见 [../../../SUBMIT.md](../../../SUBMIT.md)。问题和协作可联系
xiaobiluo@gmail.com。

每个参评模型使用一个子目录：

```text
artifacts/scores/submissions/{model_id}/
  system_card.json
  manifest.json
  audio/
```

`example_model/` 提供可复制的 metadata 与 manifest。正式音频建议放到 Git LFS、GitHub Release、Hugging Face Dataset、Zenodo 或对象存储；仓库内保留 manifest 和评分结果即可。
