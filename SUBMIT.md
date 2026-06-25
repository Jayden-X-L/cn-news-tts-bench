# Submit a TTS System

This is the one-page flow for adding a new CN-NewsTTS Bench leaderboard result.

Questions or coordination: xiaobiluo@gmail.com.

## 1. Check the Track

The v0.1 public leaderboard is the Raw Input Product Track. Your system must use
the original benchmark text as input.

Allowed:

- provider-internal text normalization or frontend behavior
- one fixed voice or configuration chosen before evaluation
- normal provider defaults

Not allowed:

- external rule frontend
- LLM rewrite or paraphrase
- SSML pronunciation hints
- manual edits to benchmark text
- target-specific rules written after seeing the public test set

## 2. Generate Audio

Generate one audio file per input record from:

```text
data/test_public.jsonl
```

Use the raw `text` field exactly as provided. Keep the same model, voice, and
configuration for all records.

## 3. Prepare Submission Metadata

Create:

```text
submissions/{model_id}/
  system_card.json
  manifest.json
```

Start from the example:

```text
examples/submissions/example_model/system_card.json
examples/submissions/example_model/manifest.json
```

If audio files are large, keep them outside git and use `audio_url` entries in
`manifest.json`, or coordinate a GitHub Release, Hugging Face Dataset, Zenodo,
or object-storage upload.

## 4. Validate the Submission

Run:

```bash
python3 scripts/validate_submission.py \
  submissions/{model_id} \
  --dataset data/test_public.jsonl
```

If you provide URLs instead of local audio files, validation checks the manifest
shape but does not download the audio.

## 5. Produce ASR Results

Either run the official three-ASR protocol or provide an equivalent ASR result
JSONL file in the documented format:

```text
docs/asr_results_format.md
```

The scorer expects one row per sample and at least three ASR transcripts per
row.

## 6. Score and Aggregate

Score your model:

```bash
python3 scripts/score_submission.py \
  --dataset data/test_public.jsonl \
  --asr-results results/asr_results/public_test/{model_id}.asr.jsonl \
  --model-id {model_id} \
  --output-dir results/per_model_public_test
```

Update leaderboard files:

```bash
python3 scripts/aggregate_leaderboard.py \
  --per-model-dir results/per_model_public_test \
  --results-dir results \
  --site-dir site
```

## 7. Open a Pull Request

Include:

- `submissions/{model_id}/system_card.json`
- `submissions/{model_id}/manifest.json` or a clear audio access note
- `results/asr_results/public_test/{model_id}.asr.jsonl`
- `results/per_model_public_test/{model_id}/`
- updated `results/leaderboard.csv`
- updated `results/leaderboard.json`
- updated `site/leaderboard.json`

Before opening the PR:

```bash
python3 scripts/validate_dataset.py data/dev.jsonl
python3 scripts/validate_dataset.py data/test_public.jsonl
python3 -m py_compile scripts/*.py
```

Use the pull request template and describe the model, provider, voice,
generation date, ASR routes, and whether any audio files are hosted outside the
repository.

