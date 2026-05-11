# Metadata For Random Equation Forecast Examples

This file records the provenance of the 10 examples shown in
`appendix_equation_forecast_examples.pdf`.

The examples are a fixed random sample from the frozen combined equation-suffix
benchmark. They were sampled before visual inspection and were not filtered or
selected for score, model success, or visual neatness. After sampling, the only
changes made for the appendix were presentation edits to the TeX rendering:
equations were aligned or line-broken so that the paper continuation and
forecast continuation could be compared cleanly. The sampled paper suffixes and
GPT-5.5 high forecast strings were not mathematically corrected or rewritten;
the model forecasts were already valid LaTeX snippets, and the appendix only
changes the display layout.

The underlying rows remain identifiable through `super_key` and `custom_id`.
The `component` column records whether the row came from the older 731-cut
component or the newer 632-cut component of the merged benchmark.

The `score gain` column is the clipped scorer likelihood gain from conditioning on
the GPT-5.5 high forecast instead of a same-budget excerpt of immediately
preceding paper context. Positive values mean the forecast made the true hidden
suffix more likely under the scorer.

| Example | arXiv | Score gain | Component | super_key | Source file | Source line | Env | Equation index | Selection seed | Global shuffle rank | Analysis tier | custom_id |
|---:|---|---:|---|---|---|---:|---|---:|---:|---:|---|---|
| 1 | [2604.24491](https://arxiv.org/abs/2604.24491) | +0.171 | old731 | `old731:2604.24491:60` | `training documents/arxiv-2604-24491.tex` | 1664 | `align` | 112 | 20302808 | 445 | `light_holdout` | `eq_suffix|row-0445|2604.24491|eq-0112|cut-0060` |
| 2 | [2604.18952](https://arxiv.org/abs/2604.18952) | +0.338 | old731 | `old731:2604.18952:98` | `training documents/arxiv-2604-18952.tex` | 1362 | `equation` | 176 | 20320970 | 440 | `light_holdout` | `eq_suffix|row-0440|2604.18952|eq-0176|cut-0098` |
| 3 | [2604.19881](https://arxiv.org/abs/2604.19881) | +0.136 | old731 | `old731:2604.19881:26` | `training documents/arxiv-2604-19881.tex` | 775 | `eqnarray` | 33 | 20295745 | 488 | `light_holdout` | `eq_suffix|row-0488|2604.19881|eq-0033|cut-0026` |
| 4 | [2604.20635](https://arxiv.org/abs/2604.20635) | +0.345 | old731 | `old731:2604.20635:23` | `training documents/arxiv-2604-20635.tex` | 916 | `bracket-display` | 67 | 20267493 | 486 | `light_holdout` | `eq_suffix|row-0486|2604.20635|eq-0067|cut-0023` |
| 5 | [2604.19506](https://arxiv.org/abs/2604.19506) | +0.090 | old731 | `old731:2604.19506:88` | `training documents/arxiv-2604-19506.tex` | 2169 | `equation` | 159 | 20309871 | 712 | `light_holdout` | `eq_suffix|row-0712|2604.19506|eq-0159|cut-0088` |
| 6 | [2604.26927](https://arxiv.org/abs/2604.26927) | +0.684 | new632 | `new632:2604.26927:30` | `training documents/arxiv-2604-26927.tex` | 772 | `align` | 64 | 20295818 | 457 | `light_holdout` | `eq_suffix|row-0457|2604.26927|eq-0064|cut-0030` |
| 7 | [2604.27074](https://arxiv.org/abs/2604.27074) | -0.076 | new632 | `new632:2604.27074:1` | `training documents/arxiv-2604-27074.tex` | 304 | `equation` | 7 | 20269584 | 615 | `light_holdout` | `eq_suffix|row-0615|2604.27074|eq-0007|cut-0001` |
| 8 | [2604.27015](https://arxiv.org/abs/2604.27015) | -0.026 | new632 | `new632:2604.27015:1` | `training documents/arxiv-2604-27015.tex` | 132 | `bracket-display` | 2 | 20304899 | 14 | `pilot20` | `eq_suffix|row-0014|2604.27015|eq-0002|cut-0001` |
| 9 | [2604.24755](https://arxiv.org/abs/2604.24755) | -0.136 | new632 | `new632:2604.24755:19` | `training documents/arxiv-2604-24755.tex` | 544 | `equation` | 56 | 20285728 | 4 | `pilot20` | `eq_suffix|row-0004|2604.24755|eq-0056|cut-0019` |
| 10 | [2604.24314](https://arxiv.org/abs/2604.24314) | +0.051 | old731 | `old731:2604.24314:94` | `training documents/arxiv-2604-24314.tex` | 1548 | `equation` | 188 | 20272538 | 216 | `dev250_extra` | `eq_suffix|row-0216|2604.24314|eq-0188|cut-0094` |

## Sampling Note

The appendix sample was drawn from the already-frozen joined equation-suffix
rows containing GPT-5.5 high forecasts. The sample intentionally mixes rows
from both frozen components of the combined benchmark. The component labels are
preserved here only for traceability; the examples should be read as examples
from the same merged benchmark distribution, not as separate evaluation sets.
