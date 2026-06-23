# Dataset v0.1

CN-NewsTTS Bench v0.1 包含两份公开数据：

| split | records | targets | auto-evaluable targets | optional targets |
|---|---:|---:|---:|---:|
| dev | 200 | 252 | 248 | 4 |
| test_public | 800 | 1008 | 992 | 16 |
| total | 1000 | 1260 | 1240 | 20 |

## Files

```text
data/dev.jsonl
data/test_public.jsonl
data/dataset_summary.json
```

`dev.sample.jsonl` 仅作为最小文档示例保留，不用于正式 leaderboard。

## Construction

v0.1 使用确定性生成脚本构建：

```bash
python3 scripts/build_v01_datasets.py
```

生成脚本使用固定 seed：

```text
20260620
```

文本为 synthetic news-style sentences，用于开源 benchmark 开发，避免直接复刻受版权保护的新闻原文。

## Category Distribution

### Record Categories

| category | dev | test_public | total |
|---|---:|---:|---:|
| sports_score | 28 | 112 | 140 |
| range_hyphen | 20 | 80 | 100 |
| year_range | 20 | 80 | 100 |
| military_model | 24 | 96 | 120 |
| vehicle_model | 16 | 64 | 80 |
| abbreviation | 26 | 104 | 130 |
| brand_mixed | 16 | 64 | 80 |
| unit_symbol | 24 | 96 | 120 |
| percentage | 14 | 56 | 70 |
| generation_label | 8 | 32 | 40 |
| optional_homograph_polyphone | 4 | 16 | 20 |

### Target Groups

| group | total targets |
|---|---:|
| number | 590 |
| entity | 400 |
| abbreviation | 130 |
| unit | 120 |
| polyphone optional | 20 |

## Main-Score Scope

The main score uses only `auto_evaluable=true` targets.

`optional_homograph_polyphone` targets are included in the dataset for future audit and phoneme-level evaluation, but excluded from v0.1 Strict Auto Accuracy because ordinary ASR text cannot reliably expose tone errors for same-character polyphones.

