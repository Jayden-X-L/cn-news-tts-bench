# Results

本目录由评分脚本生成。v0.1 public test 的主要文件：

```text
results/
  leaderboard.csv
  leaderboard.json
  per_model_public_test/
    {model_id}/
      summary.json
      target_scores.csv
      category_scores.csv
      group_scores.csv
      domain_scores.csv
  asr_results/public_test/
    {model_id}.asr.jsonl
    merge_summary.json
  asr_transcripts/public_test/
    mimo_v2_5_asr.jsonl
    sensevoice_small.jsonl
    paraformer_zh.jsonl
```

`leaderboard.csv` 和 `leaderboard.json` 当前指向 public test 榜单。生成命令：

```bash
python3 scripts/score_submission.py \
  --dataset data/test_public.jsonl \
  --asr-results results/asr_results/public_test/{model_id}.asr.jsonl \
  --model-id {model_id} \
  --output-dir results/per_model_public_test

python3 scripts/aggregate_leaderboard.py \
  --per-model-dir results/per_model_public_test \
  --results-dir results \
  --site-dir site
```

本地 TTS 音频位于 `results/tts_generation/`，默认被 `.gitignore` 排除。
