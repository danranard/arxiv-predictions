# Equation Forecast Example Appendix

This folder contains a paper-appendix style rendering of 10 equation-suffix
forecasting examples:

- `appendix_equation_forecast_examples.pdf`
- `appendix_equation_forecast_examples.tex`
- `sample_metadata.md`

These examples were randomly sampled from the frozen combined equation-suffix
benchmark. They were not chosen after inspection for impressiveness,
readability, score, or model success. The only subsequent edits were rendering
edits: a few equations were hand-aligned or line-broken so that the paper
continuation and forecast continuation could be read side by side in a compact
appendix layout. These edits do not correct or alter the mathematical/LaTeX
content of the sampled paper continuations or GPT-5.5 high forecasts; the
forecast strings were already valid LaTeX snippets.

The PDF intentionally omits internal benchmark metadata and control-condition
jargon. It reports one outward-facing score for each example: the clipped
scorer-likelihood gain over a same-budget recent-context control.
The accompanying `sample_metadata.md` records where each displayed example
came from in the frozen benchmark.
