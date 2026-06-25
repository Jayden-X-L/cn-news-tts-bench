# Pull Request

## Summary

- 

## Type

- [ ] New leaderboard submission
- [ ] Scoring or validation change
- [ ] Dataset or annotation change
- [ ] Documentation or website change
- [ ] Other:

## Leaderboard Submission Checklist

For new or updated TTS results:

- [ ] I used the original benchmark text without external rewriting.
- [ ] `raw_model_track` is `true`.
- [ ] `external_frontend`, `llm_rewrite`, `ssml`, and `manual_text_fix` are all `false`.
- [ ] A fixed model, voice, and configuration were used for all samples.
- [ ] `submissions/{model_id}/system_card.json` is included.
- [ ] `submissions/{model_id}/manifest.json` is included, or audio access is explained below.
- [ ] ASR result JSONL is included or clearly referenced.
- [ ] Per-model score outputs were regenerated.
- [ ] `results/leaderboard.csv`, `results/leaderboard.json`, and `site/leaderboard.json` were regenerated when relevant.

Audio access note:

```text

```

## Local Checks

- [ ] `python3 scripts/validate_dataset.py data/dev.jsonl`
- [ ] `python3 scripts/validate_dataset.py data/test_public.jsonl`
- [ ] `python3 -m py_compile scripts/*.py`
- [ ] `python3 scripts/validate_submission.py submissions/{model_id} --dataset data/test_public.jsonl` if this is a model submission

## Contact

For submission questions, contact xiaobiluo@gmail.com.

