# Provenance And Cut Construction

This directory records the paper slate and cut text behind the prose/TeX
continuation SFT bundle.

## Paper Slate

`paper_list.csv` lists the 40 arXiv papers used by the fresh40 prose
continuation cut manifest. It includes:

- `paper_id`
- arXiv abstract/source URLs
- title extracted from the local TeX when available
- selected-cut counts and train/eval split counts
- coarse content counts from the cut builder

`paper_summary.csv` is the original compact summary emitted by the cut builder.

## Cut Text

`selected_cut_texts_decoupled_x_j4000_p10000_y1800.jsonl` contains the actual
selected cut text rows for the canonical prose continuation view:

```text
view_name = decoupled_x_j4000_p10000_y1800
judge_x_chars = 4000
predictor_x_chars = 10000
target y_chars ~= 1800
```

Each JSONL row includes the cut metadata plus text fields such as
`judge_x_text`, `predictor_x_text`, `x_tail`, and `y_text`. These are the
source X/Y cut texts from which the scorer-input prompts and targets were
derived.

`split_manifest_seed20260427_p10000.jsonl` is the fixed shuffled order used
for smoke/pilot/dev/holdout conventions. `split_manifest_with_cut_metadata.csv`
is the same manifest in a spreadsheet-friendly form.

## Scripts

The `scripts/` subdirectory contains local copies of the scripts most relevant
to reconstructing this data lineage:

- `download_arxiv_source.py`
- `list_recent_arxiv_candidates.py`
- `select_arxiv_expansion_slate.py`
- `finalize_arxiv_expansion_slate.py`
- `build_fresh_2026_cut_manifest.py`
- `make_split_manifest.py`
- `build_fresh40_scaffold_judge_eval_prompts.py`
- `build_fresh40_scaffold_judge_multi_model_sft_dataset.py`
- `build_fresh40_bareB_prose_clip2_sft_dataset.py`

The original source experiment README is copied here as `README.md` from the
source cut-manifest experiment.

## Integrity

`SHA256SUMS.txt` contains checksums for all files in this provenance directory.
