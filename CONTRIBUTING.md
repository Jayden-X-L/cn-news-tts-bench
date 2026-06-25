# Contributing

CN-NewsTTS Bench welcomes reproducible submissions, bug reports, and scoring
protocol improvements.

For the one-page leaderboard submission flow, start with [SUBMIT.md](SUBMIT.md).
Submission questions can be sent to xiaobiluo@gmail.com.

## Submission Rules

The v0.1 main leaderboard is Raw Model Track only:

- use the original benchmark text as input
- do not add an external rules frontend
- do not use LLM rewrite
- do not use SSML or pronunciation hints
- do not manually edit test text

See [SUBMIT.md](SUBMIT.md) for the end-to-end flow and
[docs/submission.md](docs/submission.md) for the submission format.

## Local Checks

Before opening a pull request, run:

```bash
python3 scripts/validate_dataset.py data/dev.jsonl
python3 scripts/validate_dataset.py data/test_public.jsonl
python3 -m py_compile scripts/*.py
```

If you update public results, also regenerate:

```bash
python3 scripts/aggregate_leaderboard.py \
  --per-model-dir results/per_model_public_test \
  --results-dir results \
  --site-dir site
```

## Secrets

Never commit API keys, service account files, local config files, logs, or
generated TTS audio. The repository `.gitignore` excludes the standard local
paths.
