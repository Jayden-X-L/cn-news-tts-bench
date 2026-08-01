# Data

```text
data/
  canonical/              # 固定、可发布、可校验的 Benchmark 数据
    dev.jsonl
    test_public.jsonl
    dev.sample.jsonl
    schema.json
    dataset_summary.json
  runtime/                # 分片、缺失项重试清单等本地运行文件，Git 忽略
```

`canonical/` 中的文本是由 `scripts/build_v01_datasets.py` 使用固定 seed 合成并标注的正式输入，不是抓取的真实新闻语料。运行数据验证：

```bash
python3 scripts/validate_dataset.py data/canonical/dev.jsonl
python3 scripts/validate_dataset.py data/canonical/test_public.jsonl
```
