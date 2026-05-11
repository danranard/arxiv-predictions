# Single-Paper Equation Demo

This folder is a small, self-contained demo path. It is not part of the
headline benchmark.

The bundled TeX source is arXiv:2307.05326, used here only as an inspectable
paper for a pipeline demo. It is not part of the 2026 no-leakage benchmark
sample.

Default offline run:

```bash
python demo/run_single_paper_equation_demo.py
```

That reads frozen demo cuts, forecast generations, and Qwen scores from
`demo/frozen/`, then prints a small `clip2` table comparing nano low versus
nano medium forecast generations.

This 10-cut single-paper demo is meant to make the pipeline inspectable. It is
not evidence for the benchmark/model-ordering claim by itself; the reported
equation-suffix results use much more data across many papers.

To inspect the selected cuts without API calls:

```bash
python demo/run_single_paper_equation_demo.py --show-cuts
```

To regenerate from the bundled TeX source:

```bash
python demo/run_single_paper_equation_demo.py --rebuild-cuts
```

To refresh paid live calls:

```bash
python demo/run_single_paper_equation_demo.py --call-openai --call-fireworks
```

Live regeneration requires `OPENAI_API_KEY` for forecast generation and
`FIREWORKS_API_KEY` for Qwen logprob scoring. The script writes refreshed files
under `demo/frozen/`.
