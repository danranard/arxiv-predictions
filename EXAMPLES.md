# Examples

This file shows two concrete frozen rows from the equation-suffix benchmark.
They were mildly selected from a random sample for readability: they are meant
to illustrate the mechanics, not to define a new evaluation subset. Many rows
are less visually tidy, and some are more obviously copied or more obviously
wrong.

For a presentation-oriented appendix page with 10 randomly sampled examples
and no score/control annotations, see
`examples/random_equation_forecast_appendix/`. Those examples were not selected
after inspection; the accompanying metadata file records their exact frozen-row
provenance.

All context omissions below are marked explicitly as `[omitted for brevity]`.
The frozen artifacts contain the full prompts, generations, and token-level
scores.

Scores below use the frozen Qwen3-8B scorer and `clip2`, reported per target
token. Higher is better. The scorer assigns likelihood to the true held-out
suffix `Y` plus the closing display delimiter, not to the forecast string `Z`
itself.

## How Scoring Works

The predictor receives a large paper context `X`, the visible equation prefix,
and a coarse target-length hint. It returns a forecast string `Z`.

For the scaffolded scorer condition, `Z` is inserted into a first copy of the
equation. The scorer is then given a second copy of the same equation prefix,
and the logprobs of the true suffix `Y` are recorded.

```text
% First equation:
\begin{ENV}
X_eq + Z
\end{ENV}

% Same equation:
\begin{ENV}
X_eq
[score Y + closing delimiter here]
```

Thus `Z` is conditioning context. It is not scored by edit distance or exact
string match. A forecast can help even when it has TeX formatting differences,
omits details, or gets part of the continuation wrong.

The main controls in the frozen full731 artifact are:

- `scaffold_empty`: same scaffold, but `Z` is empty.
- `bare_B`: a same-budget recent-context control using the previous `B = len(Y) + 40` raw
  source characters before the equation, followed by the equation prefix.

`bare_B` is a strong same-budget raw-context baseline, but it is not the only
notion of whether `Z` is useful to the scaffolded scorer. Comparing to
`scaffold_empty` asks whether the inserted `Z` helps in the scaffold at all.
Comparing to `bare_B` asks the harder question of whether forecast-like `Z`
beats a same-budget recent-context baseline.

## Example 1: Clean Useful Forecast

Frozen row:

```text
row_id_731: 255
dataset_row_index: 258
paper_id: 2604.19885
paper title: On non-relativistic integrable models and 4d SCFTs
environment: align
```

### Generator Prompt

The real prompt contains roughly 10k characters of preceding paper context.
Here the middle is omitted and only the task instruction plus the final visible
paper-context lines are shown.

```text
You are given recent context from a technical paper and the beginning of a LaTeX display equation.
Continue the equation from exactly where it stops, in about 130 characters or fewer.
Write only the continuation. Do not write explanatory prose. Do not write \end{align}.

Recent paper context:
[omitted for brevity]

Let us first take the following ansatz for the eigenfunctions,
\begin{equation}
		\psi_\lambda(z;q,\alpha)=\frac{\mathcal{F}_\lambda(q)}{(q\,z^{\pm2}q;q)^{\alpha}}\sum_{\lambda'=0}^\infty c_{\lambda\lambda'}(\alpha)J^{(\alpha)}_{\lambda'}(z) q^{\frac{|\lambda-\lambda'|}{2}}\,.
\end{equation}
Here $J_\lambda(z)$ denotes the $A_1$ Jack polynomials which are the well-known eigenfunctions of the Lam\'{e} equation in the limit $q\rightarrow 0$.
The first few Jack polynomials take the following form.

Equation prefix:
\begin{align}
J^{(\alpha)}_0(z)&=1~,\nonumber\\
		J^{(\alpha)}_1(z)&=z+\frac{1}{z}~,\\
		J^{(\alpha)}_2(z)&=z^2+\frac{1}{z^2}+\frac{2 \alpha }{\alpha +
```

### True Suffix

```tex
1}~,\nonumber\\
		J^{(\alpha)}_3(z)&=z^3+\frac{1}{z^3}+\frac{3 \alpha }{\alpha +2}\left(z+\frac{1}{z}\right)\,, \cdots ~.\nonumber
```

The actual scored target is this suffix followed by:

```tex
\end{align}
```

### Returned Forecasts

GPT-5.5 medium:

```tex
1}~,\nonumber\\
		J^{(\alpha)}_3(z)&=z^3+\frac{1}{z^3}+\frac{3 \alpha }{\alpha +2}\left(z+\frac{1}{z}\right)~,\nonumber\\
```

Nano-low:

```tex
1}~,\qquad J^{(\alpha)}_2(z)=z^2+\frac{1}{z^2}+\frac{2\alpha}{\alpha+1}\,,\nonumber\\
```

### Scoring Prompt For GPT-5.5 Medium

The scoring prompt below ends at the second equation prefix. The target appended
and scored after this prompt is the true suffix plus `\end{align}`.

```text
% First equation:
\begin{align}
J^{(\alpha)}_0(z)&=1~,\nonumber\\
		J^{(\alpha)}_1(z)&=z+\frac{1}{z}~,\\
		J^{(\alpha)}_2(z)&=z^2+\frac{1}{z^2}+\frac{2 \alpha }{\alpha +1}~,\nonumber\\
		J^{(\alpha)}_3(z)&=z^3+\frac{1}{z^3}+\frac{3 \alpha }{\alpha +2}\left(z+\frac{1}{z}\right)~,\nonumber\\
\end{align}

% Same equation:
\begin{align}
J^{(\alpha)}_0(z)&=1~,\nonumber\\
		J^{(\alpha)}_1(z)&=z+\frac{1}{z}~,\\
		J^{(\alpha)}_2(z)&=z^2+\frac{1}{z^2}+\frac{2 \alpha }{\alpha +
```

### Scores

```text
condition                 clip2 score    vs scaffold_empty    vs bare_B
scaffold_empty             -0.4022              --              -0.0861
bare_B                     -0.3161           +0.0861              --
GPT-5.5 medium Z           -0.2308           +0.1714           +0.0854
nano-low Z                 -0.3740           +0.0282           -0.0578
```

This example is visually clean: GPT-5.5 medium predicts the next Jack
polynomial structure, with small formatting differences near the end. Nano-low
starts by closing the immediate denominator correctly but then repeats the
`J_2` pattern instead of moving to `J_3`.

## Example 2: Useful But Not Above Bare-B

This second example illustrates why `bare_B` and `scaffold_empty` answer
different questions. GPT-5.5 medium is worse than `bare_B` here, but it still
helps the scaffolded scorer substantially relative to empty and is clearly
preferred to nano-low.

Frozen row:

```text
row_id_731: 580
dataset_row_index: 587
paper_id: 2604.24042
environment: align
```

### Generator Prompt

Again, the full context is much longer; the omission marker below is not part
of the source text.

```text
You are given recent context from a technical paper and the beginning of a LaTeX display equation.
Continue the equation from exactly where it stops, in about 130 characters or fewer.
Write only the continuation. Do not write explanatory prose. Do not write \end{align}.

Recent paper context:
[omitted for brevity]

Substituting the full nonlinear vector field with $\Delta=0$ and using
$y=a_3(t)x^3+O(x^5)$, the left-hand side becomes
\begin{align}
\dot{y}
&=
-\left(p(t)+\frac{\kappa}{2}\right)y-Kx(x^2+y^2) \notag\\
&=
-\left(p(t)+\frac{\kappa}{2}\right)a_3(t)x^3-Kx^3+O(x^5).
\end{align}
The right-hand side is

Equation prefix:
\begin{align}
\frac{\partial h}{\partial t}+\frac{\partial h}{\partial x}\dot{x}
&=
\dot{a}_3(t)x^3
+
3a_3(t)x^2
\left[
\left(p(t)-
```

### True Suffix

```tex
\frac{\kappa}{2}\right)x+Ky(x^2+y^2)
\right] \notag\\
&=
\dot{a}_3(t)x^3
+
3\left(p(t)-\frac{\kappa}{2}\right)a_3(t)x^3
+
O(x^5).
```

The actual scored target is this suffix followed by:

```tex
\end{align}
```

### Returned Forecasts

GPT-5.5 medium:

```tex
\frac{\kappa}{2}\right)x+K y(x^2+y^2)
\right]+O(x^5) \notag\\
&=
\left[\dot{a}_3(t)+3a_3(t)\left(p(t)-\frac{\kappa}{2}\right)\right]x^3+O(x^5).
```

Nano-low:

```tex
\frac{\kappa}{2}\right)x-Kx(x^2+y^2)\right]
=3a_3(t)\left(p(t)-\frac{\kappa}{2}\right)x^3+O(x^5).
```

### Scores

```text
condition                 clip2 score    vs scaffold_empty    vs bare_B
scaffold_empty             -0.5662              --              -0.3207
bare_B                     -0.2455           +0.3207              --
GPT-5.5 medium Z           -0.2786           +0.2876           -0.0331
nano-low Z                 -0.3934           +0.1728           -0.1479
```

Here the GPT-5.5 medium forecast is not a full win against the same-budget
raw-context baseline, but it is still useful in the scaffold. It preserves the
main local continuation shape better than nano-low, which changes the sign and
variable structure of the nonlinear term. This is typical of why different
contrasts are useful: `scaffold_empty` measures whether `Z` carries any usable
side information in the prompt, while `bare_B` is a harder same-budget
raw-context control.
