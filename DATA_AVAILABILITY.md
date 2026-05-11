# Data Availability

The offline headline path reads frozen files under:

```text
data/frozen/equation_splits/
```

The historical first-component payload remains under `data/frozen/` for SFT
controls, examples, and old smoke scripts. The prose-continuation follow-up is
under:

```text
modules/prose_continuation/
```

For public packaging, the artifact can be distributed as:

- a repository with large files in Git LFS;
- a release zip;
- a small repository plus frozen-data mirror.

The intended reproducibility promise is independent of that choice:

1. equation headline tables reproduce from frozen data without API calls;
2. the context-only SFT control reproduces from frozen score files without GPU
   work;
3. the prose-continuation module includes its own provenance, audits, and score
   files;
4. optional live smoke tests check current provider interfaces but are not
   required for any numerical claim.

The repository should not require users to rerun paid OpenAI or Fireworks jobs
to verify the main numerical results.

The arXiv source TeX bundles are not required for offline headline
reproduction. For construction audits, `scripts/download_arxiv_source.py` can
redownload source bundles listed in the provenance CSVs, and the build scripts
can regenerate comparable cut slices. Exact write-up table reproduction should
still use the frozen rows.

The context-only SFT adapter weights are not required for frozen-score headline
reproduction. The final adapter is large enough that public packaging can put it
in Git LFS or a release asset if adapter-rescore reproduction is desired. Full
retraining also requires Qwen3-8B weights and GPU hardware, and should be
treated as a deeper audit rather than the default reproducibility path.

The MIT license in this artifact applies to the original code and
documentation. Paper excerpts, model outputs, and referenced model weights may
be subject to their source licenses or provider terms.
