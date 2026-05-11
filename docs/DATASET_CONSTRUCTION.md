# Dataset Construction

The default offline headline path starts from the merged frozen equation rows:

```text
data/frozen/equation_splits/data/cuts_all1363.jsonl
```

This file combines two same-recipe construction waves:

```text
first wave (old731): 731 cuts from 74 papers
extension wave (new632): 632 cuts from 64 papers
combined benchmark: 1363 cuts from 138 papers
```

The wave labels are retained as provenance, not as separate benchmark families.
Rows carry `component_bundle` and `super_key`; the stable merged key is:

```text
component_bundle:paper_id:cut_id
```

The first construction wave is still stored under
`data/frozen/data/cuts_731.jsonl` because the context-only SFT control and
examples are tied to that component.

## Reproducibility Promise

Exact numerical reproduction should use the frozen rows and token-level
logprob files. The construction scripts are included so the automatic dataset
recipe is inspectable and comparable slices can be regenerated from arXiv TeX
sources.

This is intentionally weaker than the frozen-score promise. arXiv source
downloads can change, source archives can contain several candidate TeX files,
and reproducing model generations or hosted logprobs would require paid API
calls. The project write-up claims should be checked from frozen rows and
frozen scores.

## Scripts

Top-level scripts:

- `scripts/download_arxiv_source.py`: downloads `/e-print/<id>` source bundles,
  extracts them safely, guesses the main TeX file, and optionally promotes that
  file into `training documents/arxiv-<id>.tex`.
- `scripts/pilot_equation_cut_prompts.py`: original TeX cleaning, display
  equation extraction, operator-site cut selection, and prompt construction.
- `scripts/build_equation_cut_dataset.py`: deterministic multi-paper cut
  selection from promoted TeX files.

The merged equation module also includes the exact scripts copied from the
source superbundle under:

```text
data/frozen/equation_splits/scripts/
```

Those include the newer combined-bundle builder, OpenAI generation batch
helpers, scoring helpers, and strip/join scripts.

## Recipe for Comparable Slices

To recreate a small slice using the first construction wave's paper IDs:

```bash
python scripts/download_arxiv_source.py \
  --ids-file data/frozen/data/paper_provenance.csv \
  --promote-main \
  --continue-on-error \
  --summary-csv outputs/source_download_summary.csv

python scripts/build_equation_cut_dataset.py \
  --tex-root "training documents" \
  --include-paper-ids-file data/frozen/data/paper_provenance.csv \
  --target-cuts 20 \
  --cuts-per-paper 2 \
  --min-paper-cuts 2 \
  --out-dir outputs/generated_cuts_slice20
```

To inspect the merged source slate directly, use:

```text
data/frozen/equation_splits/data/paper_list.csv
```

## Cut Rule Summary

The cut builder:

- strips comments and false conditionals, then keeps the document body;
- extracts display equations from common LaTeX display environments and
  `\[...\]`;
- skips display equations with obvious graphics/diagram markup;
- requires at least 10k characters of paper context before the equation;
- considers relation/operator sites and low-depth additive sites in the middle
  third of the cleaned equation body;
- keeps at most one cut per display equation;
- requires the held-out suffix `Y` to be 50 to 400 characters;
- gives the predictor a coarse target-length hint of
  `ceil(len(Y) / 10) * 10` characters;
- stores predictor context, equation prefix `x_eq`, true suffix `y`, same-budget
  recent-context control text, and scoring prompt templates.

The public-facing method name for this is equation-suffix forecasting.

## Within-Equation Cut Choice

Cuts are chosen inside the cleaned body of a displayed equation. The displayed
environment wrapper itself is not part of the cut body: for example, in an
`align` environment the builder cuts within the equation text between
`\begin{align}` and `\end{align}`.

The builder first finds candidate relation/operator sites in the middle third
of the equation body. These include equality/definition signs, inequalities,
membership, approximate equivalences, arrows/implications, and low-depth `+` or
`-` additive sites. Additive sites are filtered to avoid obvious command names,
subscripts, and superscripts. The cut position is placed immediately after the
matched operator, skipping any following whitespace. Candidate sites are sorted
by distance to the equation midpoint, and the first candidate whose remaining
suffix `Y` has length 50 to 400 characters is accepted.

At most one cut is kept per displayed equation. When more qualifying cuts are
available than the per-manuscript quota, cuts are ordered by source position,
divided into source-order buckets, and sampled with a fixed seed. This spreads
selected tasks through the manuscript rather than clustering many cuts in the
same local passage.

## Exclusions and Repairs

The first construction wave began with 740 source rows, then dropped 9 rows
whose exact target suffix appeared in predictor context, leaving 731. The
extension wave was built with the same spirit of exact-target audit. The merged
module records the first-wave exclusion audit and extension-wave exact-Y
prompt-match audit under:

```text
data/frozen/equation_splits/data/
```

The original nano-high lane had 10 missing rows in the first component. The
merged module includes a repair generation lane and Qwen/Kimi repair scores, so
combined nano-high comparisons cover all 1363 cuts.

## Command-Prefix Split Caveat

One artifact of the simple automatic rule in the first construction wave is that
some TeX commands are split as if they began with an operator. In the frozen
731-row first component, 89 cuts match `\le` as a prefix of a longer command:
85 are `\left...` split as `\le` plus `ft...`, and 4 are `\lesssim...` split as
`\le` plus `sssim...`.

These command-prefix splits were not a deliberate design choice; they are a
consequence of the simple automatic matcher. They are kept in the frozen
benchmark rather than filtered after observing results. Under the frozen task
definition they are still well-defined continuation tasks: the predictor is
given an exact TeX prefix and is scored on forecasting the exact following TeX
suffix. Future task designs may choose whether to include this class.
