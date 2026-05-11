# Generation And Scoring Sample Audit

Created: 2026-05-03.

Purpose: quick human-readable audit of the actual forecast `Z` strings and scaffolded prompts sent to the SFT forecast-scaffold scorer. This is not a statistical sample; it is a deterministic spread across predictor models to catch obvious prompt/generation pathologies.

The scorer sees:

```text
X_base

% Notes about what's next:
% Z

% Returning to the paper text:
X_tail
Y
```

The score is on `Y`; `X_base + notes + X_tail` is the prompt.

## Automated Wrapper Scan

Searched the first 500 chars of extracted `Z` for obvious wrapper/preamble language such as `here is my prediction`, `to continue`, `best guess`, and similar.

```text
gpt55_none         flagged_matches=0 details={}
gpt55_low          flagged_matches=0 details={}
gpt55_medium       flagged_matches=0 details={}
gpt55_high         flagged_matches=0 details={}
gpt54_nano_low     flagged_matches=0 details={}
gpt54_nano_medium  flagged_matches=0 details={}
gpt54_nano_high    flagged_matches=0 details={}
```

No obvious wrapper/preamble patterns were flagged by this crude scan.

## Generation Quality Summary

```text
gpt55_none         rows=326 z_chars min/p10/med/p90/max=996/999/1000/1000/1000 empty=0 under200=0 target40_in_z=15 target120_in_z=2
gpt55_low          rows=326 z_chars min/p10/med/p90/max=992/999/1000/1000/1000 empty=0 under200=0 target40_in_z=15 target120_in_z=2
gpt55_medium       rows=326 z_chars min/p10/med/p90/max=995/999/1000/1000/1000 empty=0 under200=0 target40_in_z=12 target120_in_z=0
gpt55_high         rows=324 z_chars min/p10/med/p90/max=991/999/1000/1000/1000 empty=0 under200=0 target40_in_z=12 target120_in_z=0
gpt54_nano_low     rows=325 z_chars min/p10/med/p90/max=996/999/1000/1000/1000 empty=0 under200=0 target40_in_z=7 target120_in_z=0
gpt54_nano_medium  rows=325 z_chars min/p10/med/p90/max=997/999/1000/1000/1000 empty=0 under200=0 target40_in_z=8 target120_in_z=0
gpt54_nano_high    rows=325 z_chars min/p10/med/p90/max=996/999/1000/1000/1000 empty=0 under200=0 target40_in_z=8 target120_in_z=0
```

`target40_in_z` and `target120_in_z` are crude leakage/near-copy scans for the first 40 or 120 chars of the scored target appearing inside extracted `Z`. Hits are not automatically invalid, because technical text can repeat local phrases, but nonzero counts should be hand-read.

## Samples

### gpt55_none | paper 2604.19861 | cut 0

- prompt chars: `5088`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
is obtained by decomposing the problem into its center and its central fibers.  More explicitly, let \(\tau_1\) and \(\tau_2\) be centrally pure quasifree states, and write the corresponding central decompositions as
\begin{equation}
	\H_{\tau_i}\simeq \int_{\Spec \Z_{\tau_i}}^\oplus d\mu_i(\zeta)\,\H_{\zeta,i},
	\qquad
	\A_{\tau_i}\simeq \int_{\Spec \Z_{\tau_i}}^\oplus d\mu_i(\zeta)\,\A_{\zeta,i},
\end{equation}
where, for \(\mu_i\)-almost every \(\zeta\), the fiber state is pure on the factor \(\A_{\zeta,i}\).
The central part of the inclusion is precisely the abelian problem studied above.  Thus theorem \ref{thm:abelian} tells us that the center of \(\tau_2\) can be represented in the Hilbert space of the center of \(\tau_1\) if and only if the corresponding covariance operators obey
\begin{equation}
	\mu_2\prec \mu_1,\qquad \ker Q_{\rm cen}=0,\qquad Q_{\rm cen}-1\in \mathcal L^2 .
\end{equation}
On the complement of the center, the fibers are pure quasifree representations.  The on
```

**Prompt Tail Before Returning Marker**

```text
 --- to prove the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this

% Notes about what's next:
% is obtained by decomposing the problem into its center and its central fibers.  More explicitly, let \(\tau_1\) and \(\tau_2\) be centrally pure quasifree states, and write the corresponding central decompositions as
% \begin{equation}
% 	\H_{\tau_i}\simeq \int_{\Spec \Z_{\tau_i}}^\oplus d\mu_i(\zeta)\,\H_{\zeta,i},
% 	\qquad
% 	\A_{\tau_i}\simeq \int_{\Spec \Z_{\tau_i}}^\oplus d\mu_i(\zeta)\,\A_{\zeta,i},
% \end{equation}
% where, for \(\mu_i\)-almost every \(\zeta\), the fiber state is pure on the factor \(\A_{\zeta,i}\).
% The central part of the inclusion is precisely the abelian problem studied above.  Thus theorem \ref{thm:abelian} tells us that the center of \(\tau_2\) can be represented in the Hilbert space of the center of \(\tau_1\) if and only if the corresponding covariance operators obey
% \begin{equation}
% 	\mu_2\prec \mu_1,\qquad \ker Q_{\rm cen}=0,\qquad Q_{\rm cen}-1\in \mathcal L^2 .
% \end{equation}
% On the complement of the center, the fibers are pure quasifree representations.  The on
```

**X Tail Given To Judge**

```text
2^{\natural}\rangle.$

All that remains is to show that this vector, which we have constructed as the endpoint of a particular sequence, is actually a good representative for $\tau_2$ in $\H_{\tau_1}.$
By construction, each of the $|(\tau_2^{\natural})_{(m)}\rangle$ vectors produces the correct correlation functions of $\tau_2$ on the algebra $\A_{\tau_1, (m)}$ that is generated by the operators $\phi[e_1]$ through $\phi[e_m].$
So $|\tau_2^{\natural}\rangle$ produces the correct correlation functions on the algebra
\begin{equation}
	(\cup_m \A_{\tau_1, (m)})''.
\end{equation}
This algebra is in fact equal to all of $\A_{\tau_1}.$
To see this, note that $\A_{\tau_1}$ is generated by the Weyl operators $e^{i \phi[\psi]}$ for generic real $|\psi\rangle_{\mu_1} \in \K_{\mu_1}.$
But writing $|\psi\rangle_{\mu_1} = \sum_{j=1}^{\infty} c_j |e_j\rangle_{\mu_1},$ we have
\begin{equation}
e^{\,i \phi[\sum_{j=1}^{N} c_j e_j]} \;\xrightarrow{\;\text{strongly}\;}\; e^{\,i \phi[\psi]}
\end{equation}
and this limit is obviously in the von Neumann algebra generated by $\cup_m \A_{\tau_1, (m)}.$

Now we put together theorems \ref{thm:mixed-from-pure} and \ref{thm:abelian} --- which deal with the mixed-from-pure case and the abelian case, respectively --- to prove the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this
```

**Target Y Head**

```text
result (together with the simple logic of section \ref{sec:factorial-consequences}) automatically implies the general excitability theorem,  theorem \ref{thm:general-theorem}, which is the main result of the paper.

To prove theorem \ref{thm:c-pure-from-c-pure}, we make use of the decomposition from section \ref{sec:excitability-breakdown}, which tells us that for centrally pure states, we have $\omega_2 \prec \omega_1$ if and only if the following ``restriction maps'' are ultraweakly continuous: the map $\alpha_{\pm i}:\A_{\omega_1, \pm i}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{\pm i}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{1,\pm i}{\cal K}_{\mu_1} \text{  real}
    \label{eq:pure-piece-alpha}
\end{equation}
and the map
$\alpha_{0}:\A_{\omega_1, 0}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{0}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{0}{\cal K}_{\mu_1}
```

### gpt55_none | paper 2604.22194 | cut 311

- prompt chars: `5098`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
counts after transpilation. These logs are also used to compute aggregate hardware metrics, including
backend utilization, override rate, simulator fallback rate, and the distribution of selected arms over
time. Because the LR algorithm may call the knapsack oracle many times, audit logs provide a fine-grained
view of how hardware constraints influence optimization progress rather than only final solution quality.

\subsection{Metrics and evaluation protocol}
\label{sec:metrics}

We evaluate the proposed hybrid system along three axes: optimization quality, quantum-resource cost,
and orchestration reliability. For optimization quality, we report the best feasible primal objective
found, the final Lagrangian bound, and the corresponding optimality gap when the classical optimum is
available:
\[
\mathrm{gap}=\frac{z_{\mathrm{best}}-z^\star}{\max\{1,|z^\star|\}},
\]
for minimization instances, with the sign adjusted analogously for profit-maximization formulations.
We also report feasibil
```

**Prompt Tail Before Returning Marker**

```text
ride occurred due to
gate-budget screening, runtime and failure codes, and (when available) compilation statistics such
as depth and gate

% Notes about what's next:
% counts after transpilation. These logs are also used to compute aggregate hardware metrics, including
% backend utilization, override rate, simulator fallback rate, and the distribution of selected arms over
% time. Because the LR algorithm may call the knapsack oracle many times, audit logs provide a fine-grained
% view of how hardware constraints influence optimization progress rather than only final solution quality.
% 
% \subsection{Metrics and evaluation protocol}
% \label{sec:metrics}
% 
% We evaluate the proposed hybrid system along three axes: optimization quality, quantum-resource cost,
% and orchestration reliability. For optimization quality, we report the best feasible primal objective
% found, the final Lagrangian bound, and the corresponding optimality gap when the classical optimum is
% available:
% \[
% \mathrm{gap}=\frac{z_{\mathrm{best}}-z^\star}{\max\{1,|z^\star|\}},
% \]
% for minimization instances, with the sign adjusted analogously for profit-maximization formulations.
% We also report feasibil
```

**X Tail Given To Judge**

```text
 selection and bandit configuration performed
independently per subproblem. This parallelization is essential in the hybrid setting because
quantum evaluations are expensive; parallel dispatch increases throughput and reduces wall-clock
time per LR iteration when multiple devices are available.

\paragraph{Failure handling and deterministic fallbacks.}
Physical execution can fail due to queue delays, transient backend errors, or unexpected compilation
issues. The orchestration layer therefore implements deterministic failover: if a submission times
out or a device returns an error, the system retries on an alternate backend when available; after a
bounded number of failures, it falls back to a local noisy simulator to
ensure progress and preserve reproducibility. Importantly, the bandit decision remains \emph{screened} by the feasibility filter, so failures
are treated as operational events rather than as training signals; bandit updates are performed in the trace-driven
training regime (Section~\ref{sec:bandit_training}).

\paragraph{Audit logging.}
To support circuit-level reporting (Section~\ref{sec:metrics}) and reproducibility, we log for each
knapsack call:
backend chosen, configuration arm (placement/entanglement/depth), whether an override occurred due to
gate-budget screening, runtime and failure codes, and (when available) compilation statistics such
as depth and gate
```

**Target Y Head**

```text
counts.
These compilation statistics are obtained from the transpiled circuit, where routing algorithms
insert SWAPs to map two-qubit interactions to the coupling graph. This produces a complete audit trail
linking hardware decisions to realized optimization utility.

\paragraph{Feasibility/override statistics (gate-budget screening).}
We report the rate at which the top-ranked arm is rejected by the gate-budget feasibility filter and
replaced by a safe alternative (``override rate''), as well as the overall gate-budget violation rate
under the final deployed policy. These quantities are logged explicitly by the online consult routine
and by the training simulator (actions exceeding the gate budget receive
zero reward). In addition, we include a size-scaling diagnostic
showing when configurations become unsafe as logical width increases, which helps interpret when
hardware constraints dominate and why shallow/linear configurations are selected more often at larger
widths.

\paragraph{C
```

### gpt55_none | paper 2604.19625 | cut 660

- prompt chars: `5142`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
For a fixed output state of the form
\begin{equation}
\label{eq:readout-superposition-gaussians}
\ket{\psi}
=
\sum_{k=1}^{N} c_k \ket{\phi_k},
\end{equation}
where each $\ket{\phi_k}$ is a pure Gaussian state, the probability density of a quadrature outcome
$x\in\mathbb{R}^m$ can be written as
\begin{equation}
\label{eq:readout-density-general}
p(x)
=
\left|
\sum_{k=1}^{N} c_k\,\phi_k(x)
\right|^2
=
\sum_{k,k'=1}^{N} c_k c_{k'}^*
\,\phi_k(x)\phi_{k'}(x)^* .
\end{equation}
After the final Gaussian basis change, each wavefunction $\phi_k(x)$ is a multivariate Gaussian amplitude with a complex quadratic phase,
\begin{equation}
\label{eq:gaussian-wavefunction-form}
\phi_k(x)
=
\gamma_k
\exp\!\left[
-\frac{1}{2}x^{T}A_k x
+b_k^{T}x
+d_k
\right],
\end{equation}
with $\operatorname{Re}(A_k)>0$. Consequently every interference term in
\eqref{eq:readout-density-general} is again an unnormalized complex Gaussian,
\begin{equation}
\label{eq:readout-interference-term}
\phi_k(x)\phi_{k'}(x)^*
=
\ga
```

**Prompt Tail Before Returning Marker**

```text
y measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.

% Notes about what's next:
% For a fixed output state of the form
% \begin{equation}
% \label{eq:readout-superposition-gaussians}
% \ket{\psi}
% =
% \sum_{k=1}^{N} c_k \ket{\phi_k},
% \end{equation}
% where each $\ket{\phi_k}$ is a pure Gaussian state, the probability density of a quadrature outcome
% $x\in\mathbb{R}^m$ can be written as
% \begin{equation}
% \label{eq:readout-density-general}
% p(x)
% =
% \left|
% \sum_{k=1}^{N} c_k\,\phi_k(x)
% \right|^2
% =
% \sum_{k,k'=1}^{N} c_k c_{k'}^*
% \,\phi_k(x)\phi_{k'}(x)^* .
% \end{equation}
% After the final Gaussian basis change, each wavefunction $\phi_k(x)$ is a multivariate Gaussian amplitude with a complex quadratic phase,
% \begin{equation}
% \label{eq:gaussian-wavefunction-form}
% \phi_k(x)
% =
% \gamma_k
% \exp\!\left[
% -\frac{1}{2}x^{T}A_k x
% +b_k^{T}x
% +d_k
% \right],
% \end{equation}
% with $\operatorname{Re}(A_k)>0$. Consequently every interference term in
% \eqref{eq:readout-density-general} is again an unnormalized complex Gaussian,
% \begin{equation}
% \label{eq:readout-interference-term}
% \phi_k(x)\phi_{k'}(x)^*
% =
% \ga
```

**X Tail Given To Judge**

```text
11\lambda^2+1
\le
16(1+\lambda^2)^2.
\end{equation}
Therefore
\begin{equation}
\sqrt{\lambda^4+6\lambda^3+7\lambda^2+\lambda}
\le
4(1+\lambda^2),
\end{equation}
and hence
\begin{equation}
E_0
\le
8\,\kappa L(1+\lambda^2)
\le
8c\,\delta
=
\mathcal{O}(\delta).
\end{equation}
This proves that the first contribution to the total error is
$\mathcal{O}(\delta)$.

Finally, since
\begin{equation}
s\le \left\lceil \log_4(1/\varepsilon)\right\rceil
=
\mathcal{O}(\log(1/\varepsilon)),
\end{equation}
the bounds in \eqref{eq:cor-proof-starting-runtime} give
\begin{equation}
N
=
\mathcal{O}(L^s)
=
L^{\,\mathcal{O}(\log(1/\varepsilon))}
\end{equation}
and
\begin{equation}
t
=
\mathcal{O}(Lm^3+m^2L^{s+1})
=
\mathcal{O}\!\left(
Lm^3+m^2L^{\,1+\mathcal{O}(\log(1/\varepsilon))}
\right),
\end{equation}
which prove \eqref{eq:simple-small-kappa-term-count} and
\eqref{eq:simple-small-kappa-runtime}.
\end{proof}

Let us now consider the readout stage for the proposed circuit design in Fig.~\ref{fig:circuit_scheme} yielding the superposition of Gaussian states as an output. Since quadrature detection is the basic measurement primitive in continuous-variable platforms \cite{RevModPhys.77.513}, a final Gaussian basis change allows one to express many relevant readout schemes in this language. For instance, one may measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.
```

**Target Y Head**

```text
This is natural in our setting, because the final Gaussian layer is able to change the measurement basis \cite{RevModPhys.84.621}. Bell-type measurements also fit into this framework, since they can be implemented by adding auxiliary modes, applying Gaussian interference, and then performing quadrature measurements \cite{PhysRevLett.80.869}.

Besides sampling from output quadrature distributions, one is often interested in expectation values of observables. Typical examples include moments and correlations such as $\langle \hat{X}_j\rangle$, $\langle \hat{X}_j^2\rangle$, $\langle \hat{X}_j\hat{X}_k\rangle$, $\langle \hat{P}_j\hat{P}_k\rangle$, and more general polynomial observables $O(\hat{\bm X},\hat{\bm P})$. These quantities are central in theoretical analysis, since they directly characterize the output state and provide the main objects compared across simulation methods. Accordingly, in this section we consider two readout tasks for the final coherent-state superposition: sampli
```

### gpt55_low | paper 2604.19861 | cut 0

- prompt chars: `5082`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
amounts to applying the two results separately to the central and non-central parts of the one-particle data.  We spell this out briefly.

Let $\omega_1$ and $\omega_2$ be centrally pure quasifree states, and let
\begin{equation}
	\mathcal K_{\omega_i}=\mathcal K_{\mu_i}\oplus \mathcal K_{\tau_i}
\end{equation}
denote the decomposition into the central (abelian) part and the pure factor part, in the notation introduced above.  The central purity assumption implies that the factor part is pure, while the center is described by the corresponding classical Gaussian measure $\mu_i$.  Hence the question of whether $\omega_2$ is normal in the representation of $\omega_1$ separates into the question of whether the classical Gaussian measure associated with the center of $\omega_2$ is normal with respect to that of $\omega_1$, and the question of whether the pure quasifree state on the factor part is normal with respect to the corresponding pure quasifree state for $\omega_1$.

More explicitly
```

**Prompt Tail Before Returning Marker**

```text
tively --- to prove the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this

% Notes about what's next:
% amounts to applying the two results separately to the central and non-central parts of the one-particle data.  We spell this out briefly.
% 
% Let $\omega_1$ and $\omega_2$ be centrally pure quasifree states, and let
% \begin{equation}
% 	\mathcal K_{\omega_i}=\mathcal K_{\mu_i}\oplus \mathcal K_{\tau_i}
% \end{equation}
% denote the decomposition into the central (abelian) part and the pure factor part, in the notation introduced above.  The central purity assumption implies that the factor part is pure, while the center is described by the corresponding classical Gaussian measure $\mu_i$.  Hence the question of whether $\omega_2$ is normal in the representation of $\omega_1$ separates into the question of whether the classical Gaussian measure associated with the center of $\omega_2$ is normal with respect to that of $\omega_1$, and the question of whether the pure quasifree state on the factor part is normal with respect to the corresponding pure quasifree state for $\omega_1$.
% 
% More explicitly
```

**X Tail Given To Judge**

```text
2^{\natural}\rangle.$

All that remains is to show that this vector, which we have constructed as the endpoint of a particular sequence, is actually a good representative for $\tau_2$ in $\H_{\tau_1}.$
By construction, each of the $|(\tau_2^{\natural})_{(m)}\rangle$ vectors produces the correct correlation functions of $\tau_2$ on the algebra $\A_{\tau_1, (m)}$ that is generated by the operators $\phi[e_1]$ through $\phi[e_m].$
So $|\tau_2^{\natural}\rangle$ produces the correct correlation functions on the algebra
\begin{equation}
	(\cup_m \A_{\tau_1, (m)})''.
\end{equation}
This algebra is in fact equal to all of $\A_{\tau_1}.$
To see this, note that $\A_{\tau_1}$ is generated by the Weyl operators $e^{i \phi[\psi]}$ for generic real $|\psi\rangle_{\mu_1} \in \K_{\mu_1}.$
But writing $|\psi\rangle_{\mu_1} = \sum_{j=1}^{\infty} c_j |e_j\rangle_{\mu_1},$ we have
\begin{equation}
e^{\,i \phi[\sum_{j=1}^{N} c_j e_j]} \;\xrightarrow{\;\text{strongly}\;}\; e^{\,i \phi[\psi]}
\end{equation}
and this limit is obviously in the von Neumann algebra generated by $\cup_m \A_{\tau_1, (m)}.$

Now we put together theorems \ref{thm:mixed-from-pure} and \ref{thm:abelian} --- which deal with the mixed-from-pure case and the abelian case, respectively --- to prove the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this
```

**Target Y Head**

```text
result (together with the simple logic of section \ref{sec:factorial-consequences}) automatically implies the general excitability theorem,  theorem \ref{thm:general-theorem}, which is the main result of the paper.

To prove theorem \ref{thm:c-pure-from-c-pure}, we make use of the decomposition from section \ref{sec:excitability-breakdown}, which tells us that for centrally pure states, we have $\omega_2 \prec \omega_1$ if and only if the following ``restriction maps'' are ultraweakly continuous: the map $\alpha_{\pm i}:\A_{\omega_1, \pm i}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{\pm i}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{1,\pm i}{\cal K}_{\mu_1} \text{  real}
    \label{eq:pure-piece-alpha}
\end{equation}
and the map
$\alpha_{0}:\A_{\omega_1, 0}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{0}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{0}{\cal K}_{\mu_1}
```

### gpt55_low | paper 2604.22194 | cut 311

- prompt chars: `5096`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
counts after transpilation. These logs are used to compute per-episode resource metrics and to
diagnose whether performance changes are due to optimization behavior, backend selection, or
compilation overhead. They also provide an offline dataset for future policy refinement, although in
the experiments reported here the deployed bandit parameters are fixed after trace-driven training.

\subsection{Circuit construction and quantum subproblem solver}
\label{sec:quantum_subsolver}

For a given vehicle $k$ and multiplier vector $\lambda$, the Lagrangian subproblem is a binary
knapsack instance with item weights, effective profits, and capacity inherited from the routing
relaxation. We map this subproblem to a QUBO/Ising objective and solve it with a variational
circuit. Let $x_i\in\{0,1\}$ denote whether customer/item $i$ is assigned to the vehicle. The
subproblem objective has the form
\begin{equation}
    \max_{x\in\{0,1\}^n}\;\sum_i p_i(\lambda)x_i
    \quad \text{s.t.}\quad \sum_i w_i
```

**Prompt Tail Before Returning Marker**

```text
erride occurred due to
gate-budget screening, runtime and failure codes, and (when available) compilation statistics such
as depth and gate

% Notes about what's next:
% counts after transpilation. These logs are used to compute per-episode resource metrics and to
% diagnose whether performance changes are due to optimization behavior, backend selection, or
% compilation overhead. They also provide an offline dataset for future policy refinement, although in
% the experiments reported here the deployed bandit parameters are fixed after trace-driven training.
% 
% \subsection{Circuit construction and quantum subproblem solver}
% \label{sec:quantum_subsolver}
% 
% For a given vehicle $k$ and multiplier vector $\lambda$, the Lagrangian subproblem is a binary
% knapsack instance with item weights, effective profits, and capacity inherited from the routing
% relaxation. We map this subproblem to a QUBO/Ising objective and solve it with a variational
% circuit. Let $x_i\in\{0,1\}$ denote whether customer/item $i$ is assigned to the vehicle. The
% subproblem objective has the form
% \begin{equation}
%     \max_{x\in\{0,1\}^n}\;\sum_i p_i(\lambda)x_i
%     \quad \text{s.t.}\quad \sum_i w_i
```

**X Tail Given To Judge**

```text
 selection and bandit configuration performed
independently per subproblem. This parallelization is essential in the hybrid setting because
quantum evaluations are expensive; parallel dispatch increases throughput and reduces wall-clock
time per LR iteration when multiple devices are available.

\paragraph{Failure handling and deterministic fallbacks.}
Physical execution can fail due to queue delays, transient backend errors, or unexpected compilation
issues. The orchestration layer therefore implements deterministic failover: if a submission times
out or a device returns an error, the system retries on an alternate backend when available; after a
bounded number of failures, it falls back to a local noisy simulator to
ensure progress and preserve reproducibility. Importantly, the bandit decision remains \emph{screened} by the feasibility filter, so failures
are treated as operational events rather than as training signals; bandit updates are performed in the trace-driven
training regime (Section~\ref{sec:bandit_training}).

\paragraph{Audit logging.}
To support circuit-level reporting (Section~\ref{sec:metrics}) and reproducibility, we log for each
knapsack call:
backend chosen, configuration arm (placement/entanglement/depth), whether an override occurred due to
gate-budget screening, runtime and failure codes, and (when available) compilation statistics such
as depth and gate
```

**Target Y Head**

```text
counts.
These compilation statistics are obtained from the transpiled circuit, where routing algorithms
insert SWAPs to map two-qubit interactions to the coupling graph. This produces a complete audit trail
linking hardware decisions to realized optimization utility.

\paragraph{Feasibility/override statistics (gate-budget screening).}
We report the rate at which the top-ranked arm is rejected by the gate-budget feasibility filter and
replaced by a safe alternative (``override rate''), as well as the overall gate-budget violation rate
under the final deployed policy. These quantities are logged explicitly by the online consult routine
and by the training simulator (actions exceeding the gate budget receive
zero reward). In addition, we include a size-scaling diagnostic
showing when configurations become unsafe as logical width increases, which helps interpret when
hardware constraints dominate and why shallow/linear configurations are selected more often at larger
widths.

\paragraph{C
```

### gpt55_low | paper 2604.19625 | cut 660

- prompt chars: `5128`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
More generally, any homodyne pattern obtained after a passive or active Gaussian transformation can be absorbed into the final DPLO/Gaussian layer and represented as a measurement of the canonical position quadratures on the resulting state. Thus, in the following we restrict attention to the simultaneous measurement of
\[
\hat{\boldsymbol X}=(\hat X_1,\ldots,\hat X_m)
\]
on a state of the form
\begin{equation}
\label{eq:readout-sgs-state}
\ket{\psi}
=
\sum_{j=1}^{N} c_j \ket{\boldsymbol\alpha_j},
\qquad
\boldsymbol\alpha_j\in\mathbb{C}^m,
\end{equation}
where the amplitudes and coefficients are those produced by the online-pruned propagation. The corresponding probability density is
\begin{equation}
\label{eq:readout-density-def}
p(\boldsymbol x)
=
\left|
\sum_{j=1}^{N} c_j
\braket{\boldsymbol x}{\boldsymbol\alpha_j}
\right|^2,
\qquad
\boldsymbol x\in\mathbb{R}^m .
\end{equation}
With the convention
\begin{equation}
\braket{x}{\alpha}
=
\pi^{-1/4}
\exp\!\left[
-\frac{1}{2}\bigl(x-\sqr
```

**Prompt Tail Before Returning Marker**

```text
stance, one may measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.

% Notes about what's next:
% More generally, any homodyne pattern obtained after a passive or active Gaussian transformation can be absorbed into the final DPLO/Gaussian layer and represented as a measurement of the canonical position quadratures on the resulting state. Thus, in the following we restrict attention to the simultaneous measurement of
% \[
% \hat{\boldsymbol X}=(\hat X_1,\ldots,\hat X_m)
% \]
% on a state of the form
% \begin{equation}
% \label{eq:readout-sgs-state}
% \ket{\psi}
% =
% \sum_{j=1}^{N} c_j \ket{\boldsymbol\alpha_j},
% \qquad
% \boldsymbol\alpha_j\in\mathbb{C}^m,
% \end{equation}
% where the amplitudes and coefficients are those produced by the online-pruned propagation. The corresponding probability density is
% \begin{equation}
% \label{eq:readout-density-def}
% p(\boldsymbol x)
% =
% \left|
% \sum_{j=1}^{N} c_j
% \braket{\boldsymbol x}{\boldsymbol\alpha_j}
% \right|^2,
% \qquad
% \boldsymbol x\in\mathbb{R}^m .
% \end{equation}
% With the convention
% \begin{equation}
% \braket{x}{\alpha}
% =
% \pi^{-1/4}
% \exp\!\left[
% -\frac{1}{2}\bigl(x-\sqr
```

**X Tail Given To Judge**

```text
11\lambda^2+1
\le
16(1+\lambda^2)^2.
\end{equation}
Therefore
\begin{equation}
\sqrt{\lambda^4+6\lambda^3+7\lambda^2+\lambda}
\le
4(1+\lambda^2),
\end{equation}
and hence
\begin{equation}
E_0
\le
8\,\kappa L(1+\lambda^2)
\le
8c\,\delta
=
\mathcal{O}(\delta).
\end{equation}
This proves that the first contribution to the total error is
$\mathcal{O}(\delta)$.

Finally, since
\begin{equation}
s\le \left\lceil \log_4(1/\varepsilon)\right\rceil
=
\mathcal{O}(\log(1/\varepsilon)),
\end{equation}
the bounds in \eqref{eq:cor-proof-starting-runtime} give
\begin{equation}
N
=
\mathcal{O}(L^s)
=
L^{\,\mathcal{O}(\log(1/\varepsilon))}
\end{equation}
and
\begin{equation}
t
=
\mathcal{O}(Lm^3+m^2L^{s+1})
=
\mathcal{O}\!\left(
Lm^3+m^2L^{\,1+\mathcal{O}(\log(1/\varepsilon))}
\right),
\end{equation}
which prove \eqref{eq:simple-small-kappa-term-count} and
\eqref{eq:simple-small-kappa-runtime}.
\end{proof}

Let us now consider the readout stage for the proposed circuit design in Fig.~\ref{fig:circuit_scheme} yielding the superposition of Gaussian states as an output. Since quadrature detection is the basic measurement primitive in continuous-variable platforms \cite{RevModPhys.77.513}, a final Gaussian basis change allows one to express many relevant readout schemes in this language. For instance, one may measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.
```

**Target Y Head**

```text
This is natural in our setting, because the final Gaussian layer is able to change the measurement basis \cite{RevModPhys.84.621}. Bell-type measurements also fit into this framework, since they can be implemented by adding auxiliary modes, applying Gaussian interference, and then performing quadrature measurements \cite{PhysRevLett.80.869}.

Besides sampling from output quadrature distributions, one is often interested in expectation values of observables. Typical examples include moments and correlations such as $\langle \hat{X}_j\rangle$, $\langle \hat{X}_j^2\rangle$, $\langle \hat{X}_j\hat{X}_k\rangle$, $\langle \hat{P}_j\hat{P}_k\rangle$, and more general polynomial observables $O(\hat{\bm X},\hat{\bm P})$. These quantities are central in theoretical analysis, since they directly characterize the output state and provide the main objects compared across simulation methods. Accordingly, in this section we consider two readout tasks for the final coherent-state superposition: sampli
```

### gpt55_medium | paper 2604.19861 | cut 0

- prompt chars: `5102`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
is just the statement that the problem factorizes into a purely non-central part and a purely central part.

Indeed, let
\begin{equation}
	\K_{\mu_i}=\K_{\mu_i}^{\rm nc}\oplus \K_{\mu_i}^{\rm c}
\end{equation}
be the orthogonal decomposition into the non-central and central directions of the state $\tau_i$.  Central purity means precisely that the restriction of $\tau_i$ to the algebra generated by $\K_{\mu_i}^{\rm nc}$ is pure, while the algebra generated by $\K_{\mu_i}^{\rm c}$ is abelian.  Moreover the two algebras commute, and the GNS representation decomposes as
\begin{equation}
	\H_{\tau_i}=\H_{\tau_i}^{\rm nc}\otimes \H_{\tau_i}^{\rm c},\qquad
	|\tau_i\rangle=|\tau_i^{\rm nc}\rangle\otimes |\tau_i^{\rm c}\rangle ,
\end{equation}
with
\begin{equation}
	\A_{\tau_i}
		= \A_{\tau_i}^{\rm nc}\,\bar\otimes\, \A_{\tau_i}^{\rm c}.
\end{equation}
For $|\psi\rangle=|\psi_{\rm nc}\rangle\oplus |\psi_{\rm c}\rangle$ the corresponding Weyl operator factorizes as
\begin{equation}
	W_{\tau_i}[
```

**Prompt Tail Before Returning Marker**

```text
the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this

% Notes about what's next:
% is just the statement that the problem factorizes into a purely non-central part and a purely central part.
% 
% Indeed, let
% \begin{equation}
% 	\K_{\mu_i}=\K_{\mu_i}^{\rm nc}\oplus \K_{\mu_i}^{\rm c}
% \end{equation}
% be the orthogonal decomposition into the non-central and central directions of the state $\tau_i$.  Central purity means precisely that the restriction of $\tau_i$ to the algebra generated by $\K_{\mu_i}^{\rm nc}$ is pure, while the algebra generated by $\K_{\mu_i}^{\rm c}$ is abelian.  Moreover the two algebras commute, and the GNS representation decomposes as
% \begin{equation}
% 	\H_{\tau_i}=\H_{\tau_i}^{\rm nc}\otimes \H_{\tau_i}^{\rm c},\qquad
% 	|\tau_i\rangle=|\tau_i^{\rm nc}\rangle\otimes |\tau_i^{\rm c}\rangle ,
% \end{equation}
% with
% \begin{equation}
% 	\A_{\tau_i}
% 		= \A_{\tau_i}^{\rm nc}\,\bar\otimes\, \A_{\tau_i}^{\rm c}.
% \end{equation}
% For $|\psi\rangle=|\psi_{\rm nc}\rangle\oplus |\psi_{\rm c}\rangle$ the corresponding Weyl operator factorizes as
% \begin{equation}
% 	W_{\tau_i}[
```

**X Tail Given To Judge**

```text
2^{\natural}\rangle.$

All that remains is to show that this vector, which we have constructed as the endpoint of a particular sequence, is actually a good representative for $\tau_2$ in $\H_{\tau_1}.$
By construction, each of the $|(\tau_2^{\natural})_{(m)}\rangle$ vectors produces the correct correlation functions of $\tau_2$ on the algebra $\A_{\tau_1, (m)}$ that is generated by the operators $\phi[e_1]$ through $\phi[e_m].$
So $|\tau_2^{\natural}\rangle$ produces the correct correlation functions on the algebra
\begin{equation}
	(\cup_m \A_{\tau_1, (m)})''.
\end{equation}
This algebra is in fact equal to all of $\A_{\tau_1}.$
To see this, note that $\A_{\tau_1}$ is generated by the Weyl operators $e^{i \phi[\psi]}$ for generic real $|\psi\rangle_{\mu_1} \in \K_{\mu_1}.$
But writing $|\psi\rangle_{\mu_1} = \sum_{j=1}^{\infty} c_j |e_j\rangle_{\mu_1},$ we have
\begin{equation}
e^{\,i \phi[\sum_{j=1}^{N} c_j e_j]} \;\xrightarrow{\;\text{strongly}\;}\; e^{\,i \phi[\psi]}
\end{equation}
and this limit is obviously in the von Neumann algebra generated by $\cup_m \A_{\tau_1, (m)}.$

Now we put together theorems \ref{thm:mixed-from-pure} and \ref{thm:abelian} --- which deal with the mixed-from-pure case and the abelian case, respectively --- to prove the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this
```

**Target Y Head**

```text
result (together with the simple logic of section \ref{sec:factorial-consequences}) automatically implies the general excitability theorem,  theorem \ref{thm:general-theorem}, which is the main result of the paper.

To prove theorem \ref{thm:c-pure-from-c-pure}, we make use of the decomposition from section \ref{sec:excitability-breakdown}, which tells us that for centrally pure states, we have $\omega_2 \prec \omega_1$ if and only if the following ``restriction maps'' are ultraweakly continuous: the map $\alpha_{\pm i}:\A_{\omega_1, \pm i}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{\pm i}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{1,\pm i}{\cal K}_{\mu_1} \text{  real}
    \label{eq:pure-piece-alpha}
\end{equation}
and the map
$\alpha_{0}:\A_{\omega_1, 0}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{0}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{0}{\cal K}_{\mu_1}
```

### gpt55_medium | paper 2604.22194 | cut 311

- prompt chars: `5090`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
counts. The log record also stores the \texttt{GlobalState} features used by the bandit and the ordered arm list before screening. This makes it possible to distinguish three effects in post hoc analysis: (i) the policy preference induced by the learned LinUCB parameters, (ii) deterministic changes due to feasibility constraints, and (iii) operational changes due to backend unavailability or failover. We use these records to compute the override rate, simulator fallback rate, and per-backend success rate reported in Section~\ref{sec:bandit_results}.

\subsection{Quantum knapsack subroutine}
\label{sec:qknapsack}

Each vehicle subproblem in the Lagrangian relaxation has the form
\[
    \max_{x\in\{0,1\}^{m}} \;\sum_{i=1}^{m} p_i x_i
    \quad\text{s.t.}\quad
    \sum_{i=1}^{m} w_i x_i \le C ,
\]
where the profits $p_i$ include the current multiplier-adjusted contribution of assigning customer
$i$ to the vehicle, $w_i$ is the demand or resource consumption, and $C$ is the vehicle capacit
```

**Prompt Tail Before Returning Marker**

```text
 an override occurred due to
gate-budget screening, runtime and failure codes, and (when available) compilation statistics such
as depth and gate

% Notes about what's next:
% counts. The log record also stores the \texttt{GlobalState} features used by the bandit and the ordered arm list before screening. This makes it possible to distinguish three effects in post hoc analysis: (i) the policy preference induced by the learned LinUCB parameters, (ii) deterministic changes due to feasibility constraints, and (iii) operational changes due to backend unavailability or failover. We use these records to compute the override rate, simulator fallback rate, and per-backend success rate reported in Section~\ref{sec:bandit_results}.
% 
% \subsection{Quantum knapsack subroutine}
% \label{sec:qknapsack}
% 
% Each vehicle subproblem in the Lagrangian relaxation has the form
% \[
%     \max_{x\in\{0,1\}^{m}} \;\sum_{i=1}^{m} p_i x_i
%     \quad\text{s.t.}\quad
%     \sum_{i=1}^{m} w_i x_i \le C ,
% \]
% where the profits $p_i$ include the current multiplier-adjusted contribution of assigning customer
% $i$ to the vehicle, $w_i$ is the demand or resource consumption, and $C$ is the vehicle capacit
```

**X Tail Given To Judge**

```text
 selection and bandit configuration performed
independently per subproblem. This parallelization is essential in the hybrid setting because
quantum evaluations are expensive; parallel dispatch increases throughput and reduces wall-clock
time per LR iteration when multiple devices are available.

\paragraph{Failure handling and deterministic fallbacks.}
Physical execution can fail due to queue delays, transient backend errors, or unexpected compilation
issues. The orchestration layer therefore implements deterministic failover: if a submission times
out or a device returns an error, the system retries on an alternate backend when available; after a
bounded number of failures, it falls back to a local noisy simulator to
ensure progress and preserve reproducibility. Importantly, the bandit decision remains \emph{screened} by the feasibility filter, so failures
are treated as operational events rather than as training signals; bandit updates are performed in the trace-driven
training regime (Section~\ref{sec:bandit_training}).

\paragraph{Audit logging.}
To support circuit-level reporting (Section~\ref{sec:metrics}) and reproducibility, we log for each
knapsack call:
backend chosen, configuration arm (placement/entanglement/depth), whether an override occurred due to
gate-budget screening, runtime and failure codes, and (when available) compilation statistics such
as depth and gate
```

**Target Y Head**

```text
counts.
These compilation statistics are obtained from the transpiled circuit, where routing algorithms
insert SWAPs to map two-qubit interactions to the coupling graph. This produces a complete audit trail
linking hardware decisions to realized optimization utility.

\paragraph{Feasibility/override statistics (gate-budget screening).}
We report the rate at which the top-ranked arm is rejected by the gate-budget feasibility filter and
replaced by a safe alternative (``override rate''), as well as the overall gate-budget violation rate
under the final deployed policy. These quantities are logged explicitly by the online consult routine
and by the training simulator (actions exceeding the gate budget receive
zero reward). In addition, we include a size-scaling diagnostic
showing when configurations become unsafe as logical width increases, which helps interpret when
hardware constraints dominate and why shallow/linear configurations are selected more often at larger
widths.

\paragraph{C
```

### gpt55_medium | paper 2604.19625 | cut 660

- prompt chars: `5126`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
Equivalently, the local phase rotation can be absorbed into the final DPLO layer, after which the measurement is an ordinary homodyne measurement of the $\hat X$ quadrature.

Suppose that after the online pruning step the normalized output is represented as
\begin{equation}
\label{eq:readout-superposition}
\ket{\psi_{\rm out}}
=
\sum_{k=1}^{N} c_k \ket{\vec\alpha_k},
\qquad
\vec\alpha_k\in\mathbb{C}^{m},
\end{equation}
with $N$ retained branches. For a simultaneous homodyne measurement on all modes, the probability density at
$\vec x\in\mathbb{R}^{m}$ is
\begin{equation}
\label{eq:homodyne-density-full}
p(\vec x)
=
\left|
\sum_{k=1}^{N} c_k\,\braket{\vec x}{\vec\alpha_k}
\right|^2 .
\end{equation}
With the convention
$\hat X=(\hat a+\hat a^\dagger)/\sqrt{2}$, the coherent-state wavefunction factorizes as
\begin{equation}
\label{eq:coherent-x-wavefunction}
\braket{\vec x}{\vec\alpha}
=
\pi^{-m/4}
\exp\!\left[
-\frac12\|\vec x-\sqrt{2}\operatorname{Re}\vec\alpha\|_2^2
+i\sqrt{2}\,(\opera
```

**Prompt Tail Before Returning Marker**

```text
instance, one may measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.

% Notes about what's next:
% Equivalently, the local phase rotation can be absorbed into the final DPLO layer, after which the measurement is an ordinary homodyne measurement of the $\hat X$ quadrature.
% 
% Suppose that after the online pruning step the normalized output is represented as
% \begin{equation}
% \label{eq:readout-superposition}
% \ket{\psi_{\rm out}}
% =
% \sum_{k=1}^{N} c_k \ket{\vec\alpha_k},
% \qquad
% \vec\alpha_k\in\mathbb{C}^{m},
% \end{equation}
% with $N$ retained branches. For a simultaneous homodyne measurement on all modes, the probability density at
% $\vec x\in\mathbb{R}^{m}$ is
% \begin{equation}
% \label{eq:homodyne-density-full}
% p(\vec x)
% =
% \left|
% \sum_{k=1}^{N} c_k\,\braket{\vec x}{\vec\alpha_k}
% \right|^2 .
% \end{equation}
% With the convention
% $\hat X=(\hat a+\hat a^\dagger)/\sqrt{2}$, the coherent-state wavefunction factorizes as
% \begin{equation}
% \label{eq:coherent-x-wavefunction}
% \braket{\vec x}{\vec\alpha}
% =
% \pi^{-m/4}
% \exp\!\left[
% -\frac12\|\vec x-\sqrt{2}\operatorname{Re}\vec\alpha\|_2^2
% +i\sqrt{2}\,(\opera
```

**X Tail Given To Judge**

```text
11\lambda^2+1
\le
16(1+\lambda^2)^2.
\end{equation}
Therefore
\begin{equation}
\sqrt{\lambda^4+6\lambda^3+7\lambda^2+\lambda}
\le
4(1+\lambda^2),
\end{equation}
and hence
\begin{equation}
E_0
\le
8\,\kappa L(1+\lambda^2)
\le
8c\,\delta
=
\mathcal{O}(\delta).
\end{equation}
This proves that the first contribution to the total error is
$\mathcal{O}(\delta)$.

Finally, since
\begin{equation}
s\le \left\lceil \log_4(1/\varepsilon)\right\rceil
=
\mathcal{O}(\log(1/\varepsilon)),
\end{equation}
the bounds in \eqref{eq:cor-proof-starting-runtime} give
\begin{equation}
N
=
\mathcal{O}(L^s)
=
L^{\,\mathcal{O}(\log(1/\varepsilon))}
\end{equation}
and
\begin{equation}
t
=
\mathcal{O}(Lm^3+m^2L^{s+1})
=
\mathcal{O}\!\left(
Lm^3+m^2L^{\,1+\mathcal{O}(\log(1/\varepsilon))}
\right),
\end{equation}
which prove \eqref{eq:simple-small-kappa-term-count} and
\eqref{eq:simple-small-kappa-runtime}.
\end{proof}

Let us now consider the readout stage for the proposed circuit design in Fig.~\ref{fig:circuit_scheme} yielding the superposition of Gaussian states as an output. Since quadrature detection is the basic measurement primitive in continuous-variable platforms \cite{RevModPhys.77.513}, a final Gaussian basis change allows one to express many relevant readout schemes in this language. For instance, one may measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.
```

**Target Y Head**

```text
This is natural in our setting, because the final Gaussian layer is able to change the measurement basis \cite{RevModPhys.84.621}. Bell-type measurements also fit into this framework, since they can be implemented by adding auxiliary modes, applying Gaussian interference, and then performing quadrature measurements \cite{PhysRevLett.80.869}.

Besides sampling from output quadrature distributions, one is often interested in expectation values of observables. Typical examples include moments and correlations such as $\langle \hat{X}_j\rangle$, $\langle \hat{X}_j^2\rangle$, $\langle \hat{X}_j\hat{X}_k\rangle$, $\langle \hat{P}_j\hat{P}_k\rangle$, and more general polynomial observables $O(\hat{\bm X},\hat{\bm P})$. These quantities are central in theoretical analysis, since they directly characterize the output state and provide the main objects compared across simulation methods. Accordingly, in this section we consider two readout tasks for the final coherent-state superposition: sampli
```

### gpt55_high | paper 2604.19861 | cut 0

- prompt chars: `5090`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
is possible because any centrally pure quasifree state admits a canonical decomposition into a pure quasifree state on the non-central degrees of freedom and an abelian quasifree state on the center. More explicitly, after choosing the decomposition discussed there, we may write
\begin{equation}
	\A_{\tau_1}=\A_{\tau_1}^{\rm p}\,\bar\otimes\,\A_{\tau_1}^{\rm ab},
	\qquad
	\H_{\tau_1}=\H_{\tau_1}^{\rm p}\otimes \H_{\tau_1}^{\rm ab},
\end{equation}
and
\begin{equation}
	\tau_i=\tau_i^{\rm p}\otimes \tau_i^{\rm ab}.
\end{equation}
Here $\tau_1^{\rm p}$ is pure, while $\tau_i^{\rm ab}$ are abelian quasifree states. The state $\tau_2^{\rm p}$ need not be pure when regarded as a state on the factor determined by $\tau_1^{\rm p}$, which is precisely why theorem \ref{thm:mixed-from-pure} was needed.

Suppose first that the conditions stated in theorem \ref{thm:c-pure-from-c-pure} hold. Their restriction to the non-central factor is exactly the set of conditions appearing in theorem \ref{thm:mi
```

**Prompt Tail Before Returning Marker**

```text
-- to prove the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this

% Notes about what's next:
% is possible because any centrally pure quasifree state admits a canonical decomposition into a pure quasifree state on the non-central degrees of freedom and an abelian quasifree state on the center. More explicitly, after choosing the decomposition discussed there, we may write
% \begin{equation}
% 	\A_{\tau_1}=\A_{\tau_1}^{\rm p}\,\bar\otimes\,\A_{\tau_1}^{\rm ab},
% 	\qquad
% 	\H_{\tau_1}=\H_{\tau_1}^{\rm p}\otimes \H_{\tau_1}^{\rm ab},
% \end{equation}
% and
% \begin{equation}
% 	\tau_i=\tau_i^{\rm p}\otimes \tau_i^{\rm ab}.
% \end{equation}
% Here $\tau_1^{\rm p}$ is pure, while $\tau_i^{\rm ab}$ are abelian quasifree states. The state $\tau_2^{\rm p}$ need not be pure when regarded as a state on the factor determined by $\tau_1^{\rm p}$, which is precisely why theorem \ref{thm:mixed-from-pure} was needed.
% 
% Suppose first that the conditions stated in theorem \ref{thm:c-pure-from-c-pure} hold. Their restriction to the non-central factor is exactly the set of conditions appearing in theorem \ref{thm:mi
```

**X Tail Given To Judge**

```text
2^{\natural}\rangle.$

All that remains is to show that this vector, which we have constructed as the endpoint of a particular sequence, is actually a good representative for $\tau_2$ in $\H_{\tau_1}.$
By construction, each of the $|(\tau_2^{\natural})_{(m)}\rangle$ vectors produces the correct correlation functions of $\tau_2$ on the algebra $\A_{\tau_1, (m)}$ that is generated by the operators $\phi[e_1]$ through $\phi[e_m].$
So $|\tau_2^{\natural}\rangle$ produces the correct correlation functions on the algebra
\begin{equation}
	(\cup_m \A_{\tau_1, (m)})''.
\end{equation}
This algebra is in fact equal to all of $\A_{\tau_1}.$
To see this, note that $\A_{\tau_1}$ is generated by the Weyl operators $e^{i \phi[\psi]}$ for generic real $|\psi\rangle_{\mu_1} \in \K_{\mu_1}.$
But writing $|\psi\rangle_{\mu_1} = \sum_{j=1}^{\infty} c_j |e_j\rangle_{\mu_1},$ we have
\begin{equation}
e^{\,i \phi[\sum_{j=1}^{N} c_j e_j]} \;\xrightarrow{\;\text{strongly}\;}\; e^{\,i \phi[\psi]}
\end{equation}
and this limit is obviously in the von Neumann algebra generated by $\cup_m \A_{\tau_1, (m)}.$

Now we put together theorems \ref{thm:mixed-from-pure} and \ref{thm:abelian} --- which deal with the mixed-from-pure case and the abelian case, respectively --- to prove the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this
```

**Target Y Head**

```text
result (together with the simple logic of section \ref{sec:factorial-consequences}) automatically implies the general excitability theorem,  theorem \ref{thm:general-theorem}, which is the main result of the paper.

To prove theorem \ref{thm:c-pure-from-c-pure}, we make use of the decomposition from section \ref{sec:excitability-breakdown}, which tells us that for centrally pure states, we have $\omega_2 \prec \omega_1$ if and only if the following ``restriction maps'' are ultraweakly continuous: the map $\alpha_{\pm i}:\A_{\omega_1, \pm i}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{\pm i}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{1,\pm i}{\cal K}_{\mu_1} \text{  real}
    \label{eq:pure-piece-alpha}
\end{equation}
and the map
$\alpha_{0}:\A_{\omega_1, 0}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{0}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{0}{\cal K}_{\mu_1}
```

### gpt55_high | paper 2604.20099 | cut 312

- prompt chars: `5092`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
applying the covariant recursion twice. Namely,
\begin{equation}
    \widetilde{\mathcal K}_{x_1\cdots x_nx_{n+1}x_{n+2}}
    =\widetilde{\nabla}_{x_{n+2}}\widetilde{\nabla}_{x_{n+1}}
    \widetilde{\mathcal K}_{x_1\cdots x_n},
\end{equation}
and therefore crossing symmetry of the last two legs implies
\begin{equation}
    [\widetilde{\nabla}_{x_{n+1}},\widetilde{\nabla}_{x_{n+2}}]\,
    \widetilde{\mathcal K}_{x_1\cdots x_n}=0 .
\end{equation}
Since $\widetilde{\mathcal K}_{x_1\cdots x_n}=\widetilde{\mathcal M}_{x_1\cdots x_n}$ for $n\geq 4$, this is precisely the on-shell integrability condition found in Eq.~\eqref{eq: zero curvature}. Thus, the vanishing of the curvature should not be interpreted as the absence of interactions, but rather as a consequence of using the physical amplitudes as covariantly defined tensors on the on-shell submanifold.

Let us stress that this conclusion is intrinsically on-shell. Away from the on-shell locus, the terms collected in $U$ and $V$ do not van
```

**Prompt Tail Before Returning Marker**

```text
2}x_{n+1}}\Rightarrow[\nabla_{x_{n+1}},\nabla_{x_{n+2}}] \mathcal{M}_{x_1\cdots x_n}=0.
\end{equation}
We then arrive at the same conclusion by

% Notes about what's next:
% applying the covariant recursion twice. Namely,
% \begin{equation}
%     \widetilde{\mathcal K}_{x_1\cdots x_nx_{n+1}x_{n+2}}
%     =\widetilde{\nabla}_{x_{n+2}}\widetilde{\nabla}_{x_{n+1}}
%     \widetilde{\mathcal K}_{x_1\cdots x_n},
% \end{equation}
% and therefore crossing symmetry of the last two legs implies
% \begin{equation}
%     [\widetilde{\nabla}_{x_{n+1}},\widetilde{\nabla}_{x_{n+2}}]\,
%     \widetilde{\mathcal K}_{x_1\cdots x_n}=0 .
% \end{equation}
% Since $\widetilde{\mathcal K}_{x_1\cdots x_n}=\widetilde{\mathcal M}_{x_1\cdots x_n}$ for $n\geq 4$, this is precisely the on-shell integrability condition found in Eq.~\eqref{eq: zero curvature}. Thus, the vanishing of the curvature should not be interpreted as the absence of interactions, but rather as a consequence of using the physical amplitudes as covariantly defined tensors on the on-shell submanifold.
% 
% Let us stress that this conclusion is intrinsically on-shell. Away from the on-shell locus, the terms collected in $U$ and $V$ do not van
```

**X Tail Given To Judge**

```text
{equation}
    R_{abcd}=\frac{1}{2}(-\mathcal{N}_{bd,ca}+\mathcal{N}_{bc,da}-\mathcal{N}_{ac,db}+\mathcal{N}_{ad,cb})+\mathcal{N}_{ef}(\Gamma^e_{da}\Gamma^f_{cb}-\Gamma^e_{ca}\Gamma^f_{db}).
\end{equation}
Since our goal is to relate the curvature tensor to scattering amplitudes, let us impose on-shell conditions on both sides
\begin{equation}
\begin{split}
    \widetilde{R}_{abcd}&=\frac{1}{2}(G^e_{bd}\widetilde{\mathcal{M}}_{eca}-G^e_{bc}\widetilde{\mathcal{M}}_{eda}+G^e_{ac}\widetilde{\mathcal{M}}_{edb}-G^e_{ad}\widetilde{\mathcal{M}}_{ecb})\\&\ \ \ +\widetilde{\mathcal{M}}_{ef}(G^e_{da}G^f_{cb}-G^e_{ca}G^f_{db})\\
    &=0
    \end{split}
\end{equation}
where we note that
\begin{equation}
   \widetilde{\mathcal{N}}_{bd,ca}=\widetilde{\mathcal{M}}_{bdca}-G^e_{bd}\widetilde{\mathcal{M}}_{eca},
\end{equation}
and Eq. \eqref{eq:Gdefn} is used.

Consequently, we conclude that the (on-shell) curvature induced by $\mathcal{K}$ is zero. In fact, in \cite{Cohen:2023ekv} the authors show that the on-shell curvature induced by $\mathcal M$ is zero, using the crossing symmetry between the last two legs $x_{n+1}$ and $x_{n+2}$:
\begin{equation}\label{eq: zero curvature}
    \mathcal{M}_{x_1\cdots x_nx_{n+1}x_{n+2}}= \mathcal{M}_{x_1\cdots x_nx_{n+2}x_{n+1}}\Rightarrow[\nabla_{x_{n+1}},\nabla_{x_{n+2}}] \mathcal{M}_{x_1\cdots x_n}=0.
\end{equation}
We then arrive at the same conclusion by
```

**Target Y Head**

```text
noting that $\widetilde {\mathcal K}=\widetilde{\mathcal M}$. It is worth noting that the functional geometry may exhibit nonzero curvature away from the physical point. However, when expressing scattering amplitudes geometrically, only the geometry at the physical point is relevant. That being said, in the rest of this section, we refer to this local flatness when we use the word ``flat''.

At first glance, this seems to be a contradiction, but it can be resolved based on the observation that an m-sphere $S^m$ which is embedded in a flat Euclidean space $R^{n>m}$\footnote{Note that there is a subtle difference here: the functional manifold is infinite dimensional while the dimension of $R^{n}$ is still finite. In addition, it is not clear how to define a reasonable curvature on an infinite-dimensional manifold. Nevertheless, we shall simply use this example as an analogy and ignore the technical details.}, is equipped with a nonzero curvature. The embedding is realized by freezing cer
```

### gpt55_high | paper 2604.19625 | cut 660

- prompt chars: `5114`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
Equivalently, the Gaussian unitary implementing this change of basis can be commuted into the classical description of each branch. Thus, for the purpose of readout, it suffices to describe homodyne detection of the canonical quadratures on a state of the form
\begin{equation}
\label{eq:readout-branch-state}
\ket{\psi_{\rm out}}
=
\sum_{k=1}^{N} c_k \ket{\vec \alpha_k},
\qquad
\vec \alpha_k\in\mathbb{C}^m ,
\end{equation}
where the coefficients and amplitudes are those produced by the online propagation, possibly after the final Gaussian basis change.

Let
\begin{equation}
\vec x=(x_1,\ldots,x_m)\in\mathbb{R}^m
\end{equation}
denote the homodyne outcome. For a vector of rotation angles
$\vec\theta=(\theta_1,\ldots,\theta_m)$, define
\begin{equation}
\beta_{k,j}:=e^{-i\theta_j}\alpha_{k,j}.
\end{equation}
With the convention
$\hat X=(\hat a+\hat a^\dagger)/\sqrt2$, the quadrature wavefunction of a coherent state is
\begin{equation}
\label{eq:coherent-homodyne-wavefunction}
\varphi_{\vec
```

**Prompt Tail Before Returning Marker**

```text
nguage. For instance, one may measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.

% Notes about what's next:
% Equivalently, the Gaussian unitary implementing this change of basis can be commuted into the classical description of each branch. Thus, for the purpose of readout, it suffices to describe homodyne detection of the canonical quadratures on a state of the form
% \begin{equation}
% \label{eq:readout-branch-state}
% \ket{\psi_{\rm out}}
% =
% \sum_{k=1}^{N} c_k \ket{\vec \alpha_k},
% \qquad
% \vec \alpha_k\in\mathbb{C}^m ,
% \end{equation}
% where the coefficients and amplitudes are those produced by the online propagation, possibly after the final Gaussian basis change.
% 
% Let
% \begin{equation}
% \vec x=(x_1,\ldots,x_m)\in\mathbb{R}^m
% \end{equation}
% denote the homodyne outcome. For a vector of rotation angles
% $\vec\theta=(\theta_1,\ldots,\theta_m)$, define
% \begin{equation}
% \beta_{k,j}:=e^{-i\theta_j}\alpha_{k,j}.
% \end{equation}
% With the convention
% $\hat X=(\hat a+\hat a^\dagger)/\sqrt2$, the quadrature wavefunction of a coherent state is
% \begin{equation}
% \label{eq:coherent-homodyne-wavefunction}
% \varphi_{\vec
```

**X Tail Given To Judge**

```text
11\lambda^2+1
\le
16(1+\lambda^2)^2.
\end{equation}
Therefore
\begin{equation}
\sqrt{\lambda^4+6\lambda^3+7\lambda^2+\lambda}
\le
4(1+\lambda^2),
\end{equation}
and hence
\begin{equation}
E_0
\le
8\,\kappa L(1+\lambda^2)
\le
8c\,\delta
=
\mathcal{O}(\delta).
\end{equation}
This proves that the first contribution to the total error is
$\mathcal{O}(\delta)$.

Finally, since
\begin{equation}
s\le \left\lceil \log_4(1/\varepsilon)\right\rceil
=
\mathcal{O}(\log(1/\varepsilon)),
\end{equation}
the bounds in \eqref{eq:cor-proof-starting-runtime} give
\begin{equation}
N
=
\mathcal{O}(L^s)
=
L^{\,\mathcal{O}(\log(1/\varepsilon))}
\end{equation}
and
\begin{equation}
t
=
\mathcal{O}(Lm^3+m^2L^{s+1})
=
\mathcal{O}\!\left(
Lm^3+m^2L^{\,1+\mathcal{O}(\log(1/\varepsilon))}
\right),
\end{equation}
which prove \eqref{eq:simple-small-kappa-term-count} and
\eqref{eq:simple-small-kappa-runtime}.
\end{proof}

Let us now consider the readout stage for the proposed circuit design in Fig.~\ref{fig:circuit_scheme} yielding the superposition of Gaussian states as an output. Since quadrature detection is the basic measurement primitive in continuous-variable platforms \cite{RevModPhys.77.513}, a final Gaussian basis change allows one to express many relevant readout schemes in this language. For instance, one may measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.
```

**Target Y Head**

```text
This is natural in our setting, because the final Gaussian layer is able to change the measurement basis \cite{RevModPhys.84.621}. Bell-type measurements also fit into this framework, since they can be implemented by adding auxiliary modes, applying Gaussian interference, and then performing quadrature measurements \cite{PhysRevLett.80.869}.

Besides sampling from output quadrature distributions, one is often interested in expectation values of observables. Typical examples include moments and correlations such as $\langle \hat{X}_j\rangle$, $\langle \hat{X}_j^2\rangle$, $\langle \hat{X}_j\hat{X}_k\rangle$, $\langle \hat{P}_j\hat{P}_k\rangle$, and more general polynomial observables $O(\hat{\bm X},\hat{\bm P})$. These quantities are central in theoretical analysis, since they directly characterize the output state and provide the main objects compared across simulation methods. Accordingly, in this section we consider two readout tasks for the final coherent-state superposition: sampli
```

### gpt54_nano_low | paper 2604.19861 | cut 0

- prompt chars: `5088`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
As explained at the beginning of the section, this yields the desired centrally pure excitability result once we have checked that the representative we constructed for $|\tau_2^{\natural}\rangle$ descends correctly to the mixed state $\tau_2$.
Indeed, by definition of the natural cone representatives and by the assumed ordering $\tau_2\prec \tau_1$, the operators implementing the inclusion
\[
\A_{\tau_1,(m)}\subset \A_{\tau_1}
\]
are compatible with the approximating sequence. Since $|\tau_2^{\natural}\rangle$ produces the correct correlations on each algebra $\A_{\tau_1,(m)}$, it follows that for any Weyl operator $e^{i\phi[\psi]}$ with real $|\psi\rangle_{\mu_1}\in\K_{\mu_1}$ we have
\[
\langle \tau_2^{\natural}|\,e^{i\phi[\psi]}\,|\tau_2^{\natural}\rangle
=\lim_{N\to\infty}\langle (\tau_2^{\natural})_{(N)}|\,e^{i\phi[\sum_{j=1}^{N}c_j e_j]}\,|(\tau_2^{\natural})_{(N)}\rangle
=\langle \tau_2|\,e^{i\phi[\psi]}\,|\tau_2\rangle,
\]
where in the first equality we used strong convergence
```

**Prompt Tail Before Returning Marker**

```text
 --- to prove the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this

% Notes about what's next:
% As explained at the beginning of the section, this yields the desired centrally pure excitability result once we have checked that the representative we constructed for $|\tau_2^{\natural}\rangle$ descends correctly to the mixed state $\tau_2$.
% Indeed, by definition of the natural cone representatives and by the assumed ordering $\tau_2\prec \tau_1$, the operators implementing the inclusion
% \[
% \A_{\tau_1,(m)}\subset \A_{\tau_1}
% \]
% are compatible with the approximating sequence. Since $|\tau_2^{\natural}\rangle$ produces the correct correlations on each algebra $\A_{\tau_1,(m)}$, it follows that for any Weyl operator $e^{i\phi[\psi]}$ with real $|\psi\rangle_{\mu_1}\in\K_{\mu_1}$ we have
% \[
% \langle \tau_2^{\natural}|\,e^{i\phi[\psi]}\,|\tau_2^{\natural}\rangle
% =\lim_{N\to\infty}\langle (\tau_2^{\natural})_{(N)}|\,e^{i\phi[\sum_{j=1}^{N}c_j e_j]}\,|(\tau_2^{\natural})_{(N)}\rangle
% =\langle \tau_2|\,e^{i\phi[\psi]}\,|\tau_2\rangle,
% \]
% where in the first equality we used strong convergence
```

**X Tail Given To Judge**

```text
2^{\natural}\rangle.$

All that remains is to show that this vector, which we have constructed as the endpoint of a particular sequence, is actually a good representative for $\tau_2$ in $\H_{\tau_1}.$
By construction, each of the $|(\tau_2^{\natural})_{(m)}\rangle$ vectors produces the correct correlation functions of $\tau_2$ on the algebra $\A_{\tau_1, (m)}$ that is generated by the operators $\phi[e_1]$ through $\phi[e_m].$
So $|\tau_2^{\natural}\rangle$ produces the correct correlation functions on the algebra
\begin{equation}
	(\cup_m \A_{\tau_1, (m)})''.
\end{equation}
This algebra is in fact equal to all of $\A_{\tau_1}.$
To see this, note that $\A_{\tau_1}$ is generated by the Weyl operators $e^{i \phi[\psi]}$ for generic real $|\psi\rangle_{\mu_1} \in \K_{\mu_1}.$
But writing $|\psi\rangle_{\mu_1} = \sum_{j=1}^{\infty} c_j |e_j\rangle_{\mu_1},$ we have
\begin{equation}
e^{\,i \phi[\sum_{j=1}^{N} c_j e_j]} \;\xrightarrow{\;\text{strongly}\;}\; e^{\,i \phi[\psi]}
\end{equation}
and this limit is obviously in the von Neumann algebra generated by $\cup_m \A_{\tau_1, (m)}.$

Now we put together theorems \ref{thm:mixed-from-pure} and \ref{thm:abelian} --- which deal with the mixed-from-pure case and the abelian case, respectively --- to prove the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this
```

**Target Y Head**

```text
result (together with the simple logic of section \ref{sec:factorial-consequences}) automatically implies the general excitability theorem,  theorem \ref{thm:general-theorem}, which is the main result of the paper.

To prove theorem \ref{thm:c-pure-from-c-pure}, we make use of the decomposition from section \ref{sec:excitability-breakdown}, which tells us that for centrally pure states, we have $\omega_2 \prec \omega_1$ if and only if the following ``restriction maps'' are ultraweakly continuous: the map $\alpha_{\pm i}:\A_{\omega_1, \pm i}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{\pm i}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{1,\pm i}{\cal K}_{\mu_1} \text{  real}
    \label{eq:pure-piece-alpha}
\end{equation}
and the map
$\alpha_{0}:\A_{\omega_1, 0}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{0}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{0}{\cal K}_{\mu_1}
```

### gpt54_nano_low | paper 2604.21800 | cut 307

- prompt chars: `5108`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
\begin{equation}
\boldsymbol{\gamma}(P)
:=
\bigl(\gamma_1(P),\dots,\gamma_m(P)\bigr),
\qquad
\gamma_\alpha(P)
:=1-\lambda_\alpha(P)^2,
\label{eq:variance-profile}
\end{equation}
which can be viewed as the simultaneous Pauli-variance analogue of the higher-rank compression point \((\lambda_1(P),\dots,\lambda_m(P))\in\Lambda_K(A)\). Indeed, for \(\rho_P=P/K\) and using \(E_\alpha^2=\mathbbm{1}\) we have
\[
\mathrm{Var}_{\rho_P}(E_\alpha)
=
\Tr(\rho_P E_\alpha^2)-\Tr(\rho_P E_\alpha)^2
=
1-\lambda_\alpha(P)^2
=
\gamma_\alpha(P),
\]
so \(\gamma_\alpha(P)\) is precisely the Pauli variance of \(E_\alpha\) on the maximally mixed logical state.

Error-detection constraints translate into simple geometric requirements on \(\boldsymbol{\gamma}(P)\). If \(P\) is \(\mathcal E\)-detecting, then for each \(E_\alpha\in\mathcal E\) either \(PE_\alpha P=\lambda_\alpha(P)P\) with \(\lambda_\alpha(P)\in\{\pm1\}\) (undetected logical symmetry) or \(PE_\alpha P=0\) (detected error). In either case \(\gamma
```

**Prompt Tail Before Returning Marker**

```text

\Tr(\rho_P E_\alpha)
=
\langle E_\alpha\rangle_{\rho_P}.
\end{equation}
We therefore associate with \(P\) the variance profile

% Notes about what's next:
% \begin{equation}
% \boldsymbol{\gamma}(P)
% :=
% \bigl(\gamma_1(P),\dots,\gamma_m(P)\bigr),
% \qquad
% \gamma_\alpha(P)
% :=1-\lambda_\alpha(P)^2,
% \label{eq:variance-profile}
% \end{equation}
% which can be viewed as the simultaneous Pauli-variance analogue of the higher-rank compression point \((\lambda_1(P),\dots,\lambda_m(P))\in\Lambda_K(A)\). Indeed, for \(\rho_P=P/K\) and using \(E_\alpha^2=\mathbbm{1}\) we have
% \[
% \mathrm{Var}_{\rho_P}(E_\alpha)
% =
% \Tr(\rho_P E_\alpha^2)-\Tr(\rho_P E_\alpha)^2
% =
% 1-\lambda_\alpha(P)^2
% =
% \gamma_\alpha(P),
% \]
% so \(\gamma_\alpha(P)\) is precisely the Pauli variance of \(E_\alpha\) on the maximally mixed logical state.
% 
% Error-detection constraints translate into simple geometric requirements on \(\boldsymbol{\gamma}(P)\). If \(P\) is \(\mathcal E\)-detecting, then for each \(E_\alpha\in\mathcal E\) either \(PE_\alpha P=\lambda_\alpha(P)P\) with \(\lambda_\alpha(P)\in\{\pm1\}\) (undetected logical symmetry) or \(PE_\alpha P=0\) (detected error). In either case \(\gamma
```

**X Tail Given To Judge**

```text
{equation}
V(E)
:=
\left\{
\langle E\rangle_\rho^2
:\;
\rho\in\mathcal D(\mathcal H)
\right\},
\end{equation}
\begin{equation}
\mathcal D(\mathcal H)
=
\{\rho\in\mathcal B(\mathcal H):\rho\ge0,\ \Tr\rho=1\},
\end{equation}
and refer to this set as the variance range of \(E\). Since a Pauli observable has eigenvalues \(\pm1\), every value in \([0,1]\) is attainable, and therefore \(V(E)=[0,1]\). The nontrivial structure only appears after imposing higher-rank compression and error-detection constraints.

Motivated by recent work on Pauli expectation and variance geometry
\cite{xu2025simultaneous, Cabello2014Graph, XuSchwonnekWinter2024, BorelandTodorovWinter2022ConvexCorners, BorelandTodorovWinter2021, DuanSeveriniWinter2013},
we now fix a finite Pauli error set \(\mathcal E\subset\mathcal P_n\) and an ordered tuple \(\boldsymbol{E}=(E_1,\dots,E_m)\) selected from \(\mathcal E\). If \(P\in\mathcal P_K\) detects all operators in \(\mathcal E\), then in particular each \(E_\alpha\) compresses to a scalar on the code space:
\begin{equation}
P E_\alpha P=\lambda_\alpha(P)\,P,
\qquad \alpha=1,\dots,m .
\end{equation}
Since \(\rho_P=P/K\), these compression coefficients are exactly the corresponding code-state expectations,
\begin{equation}
\lambda_\alpha(P)
=
\Tr(\rho_P E_\alpha)
=
\langle E_\alpha\rangle_{\rho_P}.
\end{equation}
We therefore associate with \(P\) the variance profile
```

**Target Y Head**

```text
\begin{equation}
q(P)
:=
\bigl(
q_1(P),\dots,q_m(P)
\bigr),
\end{equation}
\begin{equation}
q_\alpha(P)
:=
\lambda_\alpha(P)^2
=
\langle E_\alpha\rangle_{\rho_P}^2,
\label{eq:variance-profile}
\end{equation}
and define the joint rank-$K$ variance range by
\begin{equation}
Q_K(\boldsymbol{E})
:=
\left\{
q(P)\in[0,1]^m
:\;
P\in\mathcal P_K \text{ is }\mathcal E\text{-detecting}
\right\},
\label{eq:QK-def}
\end{equation}
with the ambient detectable set \(\mathcal E\) understood from context. Equivalently, \(Q_K(\boldsymbol{E})\) is the set of all squared compression-coordinate vectors arising from rank-$K$ projectors that detect the prescribed Pauli set.

From this perspective, \(Q_K(\boldsymbol{E})\) is a higher-rank, code-constrained analogue of the joint variance body. Unlike the rank-$1$ setting, however, the admissible points are filtered by the requirement that one and the same rank-$K$ projector satisfy all of the Knill--Laflamme detection constraints. As a result, \(Q_K(\boldsymbo
```

### gpt54_nano_low | paper 2604.19625 | cut 660

- prompt chars: `5090`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
\begin{equation}
\label{eq:readout-stage-gaussian-overlap}
\braket{\vec{x}}{\psi_{\mathrm{online}}^{(L)}}=
\frac{1}{(\pi\sigma^2)^{m/4}}
\exp\!\left(
-\frac{1}{2\sigma^2}\sum_{j=1}^{m}(x_j-\mu_j)^2
\right)\!,
\end{equation}
for some displacement vector $\mu\in\mathbb{R}^m$ and width $\sigma^2>0$ determined by the circuit parameters (for the superposition of Gaussians, the right-hand side becomes a weighted sum over such terms). In this situation, standard homodyne detection of the quadrature vector
$\hat{\vec{X}}=(\hat{X}_1,\dots,\hat{X}_m)^{\mathsf{T}}$
directly accesses the position-space wave function up to a known Gaussian kernel, implying that the output probability density can be written as a Gaussian mixture with weights given by the corresponding coherent amplitudes.

To express more general readout procedures in the same language, note that a Gaussian unitary corresponds to a symplectic transformation $\mathbf{S}$ on quadratures, implemented by a change of mode basis. In parti
```

**Prompt Tail Before Returning Marker**

```text
adout schemes in this language. For instance, one may measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.

% Notes about what's next:
% \begin{equation}
% \label{eq:readout-stage-gaussian-overlap}
% \braket{\vec{x}}{\psi_{\mathrm{online}}^{(L)}}=
% \frac{1}{(\pi\sigma^2)^{m/4}}
% \exp\!\left(
% -\frac{1}{2\sigma^2}\sum_{j=1}^{m}(x_j-\mu_j)^2
% \right)\!,
% \end{equation}
% for some displacement vector $\mu\in\mathbb{R}^m$ and width $\sigma^2>0$ determined by the circuit parameters (for the superposition of Gaussians, the right-hand side becomes a weighted sum over such terms). In this situation, standard homodyne detection of the quadrature vector
% $\hat{\vec{X}}=(\hat{X}_1,\dots,\hat{X}_m)^{\mathsf{T}}$
% directly accesses the position-space wave function up to a known Gaussian kernel, implying that the output probability density can be written as a Gaussian mixture with weights given by the corresponding coherent amplitudes.
% 
% To express more general readout procedures in the same language, note that a Gaussian unitary corresponds to a symplectic transformation $\mathbf{S}$ on quadratures, implemented by a change of mode basis. In parti
```

**X Tail Given To Judge**

```text
11\lambda^2+1
\le
16(1+\lambda^2)^2.
\end{equation}
Therefore
\begin{equation}
\sqrt{\lambda^4+6\lambda^3+7\lambda^2+\lambda}
\le
4(1+\lambda^2),
\end{equation}
and hence
\begin{equation}
E_0
\le
8\,\kappa L(1+\lambda^2)
\le
8c\,\delta
=
\mathcal{O}(\delta).
\end{equation}
This proves that the first contribution to the total error is
$\mathcal{O}(\delta)$.

Finally, since
\begin{equation}
s\le \left\lceil \log_4(1/\varepsilon)\right\rceil
=
\mathcal{O}(\log(1/\varepsilon)),
\end{equation}
the bounds in \eqref{eq:cor-proof-starting-runtime} give
\begin{equation}
N
=
\mathcal{O}(L^s)
=
L^{\,\mathcal{O}(\log(1/\varepsilon))}
\end{equation}
and
\begin{equation}
t
=
\mathcal{O}(Lm^3+m^2L^{s+1})
=
\mathcal{O}\!\left(
Lm^3+m^2L^{\,1+\mathcal{O}(\log(1/\varepsilon))}
\right),
\end{equation}
which prove \eqref{eq:simple-small-kappa-term-count} and
\eqref{eq:simple-small-kappa-runtime}.
\end{proof}

Let us now consider the readout stage for the proposed circuit design in Fig.~\ref{fig:circuit_scheme} yielding the superposition of Gaussian states as an output. Since quadrature detection is the basic measurement primitive in continuous-variable platforms \cite{RevModPhys.77.513}, a final Gaussian basis change allows one to express many relevant readout schemes in this language. For instance, one may measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.
```

**Target Y Head**

```text
This is natural in our setting, because the final Gaussian layer is able to change the measurement basis \cite{RevModPhys.84.621}. Bell-type measurements also fit into this framework, since they can be implemented by adding auxiliary modes, applying Gaussian interference, and then performing quadrature measurements \cite{PhysRevLett.80.869}.

Besides sampling from output quadrature distributions, one is often interested in expectation values of observables. Typical examples include moments and correlations such as $\langle \hat{X}_j\rangle$, $\langle \hat{X}_j^2\rangle$, $\langle \hat{X}_j\hat{X}_k\rangle$, $\langle \hat{P}_j\hat{P}_k\rangle$, and more general polynomial observables $O(\hat{\bm X},\hat{\bm P})$. These quantities are central in theoretical analysis, since they directly characterize the output state and provide the main objects compared across simulation methods. Accordingly, in this section we consider two readout tasks for the final coherent-state superposition: sampli
```

### gpt54_nano_medium | paper 2604.19861 | cut 0

- prompt chars: `5066`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
As explained at the beginning of the section, this means that once $Q-1$ is shown to be Hilbert-Schmidt (in the abelian case) and once the appropriate analog for the mixed-from-pure case has been established, the centrally pure excitation criterion reduces to checking the same operator-theoretic conditions on each central component. Concretely, using the central decomposition of the Hilbert spaces with respect to the joint commutant action in the GNS representation of $\tau_1$, the general centrally pure statement can be verified componentwise: on each abelian fiber one applies theorem \ref{thm:abelian}, while on each mixed fiber one applies theorem \ref{thm:mixed-from-pure}. The requirement $\mu_2\prec \mu_1$ follows from the monotonicity of the one-particle structures under the embedding, and $\ker Q=0$ and the Hilbert-Schmidt property are inherited from the corresponding fiberwise statements. Since these properties are stable under forming the direct integral (and because Hilbert-Sc
```

**Prompt Tail Before Returning Marker**

```text
ian case, respectively --- to prove the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this

% Notes about what's next:
% As explained at the beginning of the section, this means that once $Q-1$ is shown to be Hilbert-Schmidt (in the abelian case) and once the appropriate analog for the mixed-from-pure case has been established, the centrally pure excitation criterion reduces to checking the same operator-theoretic conditions on each central component. Concretely, using the central decomposition of the Hilbert spaces with respect to the joint commutant action in the GNS representation of $\tau_1$, the general centrally pure statement can be verified componentwise: on each abelian fiber one applies theorem \ref{thm:abelian}, while on each mixed fiber one applies theorem \ref{thm:mixed-from-pure}. The requirement $\mu_2\prec \mu_1$ follows from the monotonicity of the one-particle structures under the embedding, and $\ker Q=0$ and the Hilbert-Schmidt property are inherited from the corresponding fiberwise statements. Since these properties are stable under forming the direct integral (and because Hilbert-Sc
```

**X Tail Given To Judge**

```text
2^{\natural}\rangle.$

All that remains is to show that this vector, which we have constructed as the endpoint of a particular sequence, is actually a good representative for $\tau_2$ in $\H_{\tau_1}.$
By construction, each of the $|(\tau_2^{\natural})_{(m)}\rangle$ vectors produces the correct correlation functions of $\tau_2$ on the algebra $\A_{\tau_1, (m)}$ that is generated by the operators $\phi[e_1]$ through $\phi[e_m].$
So $|\tau_2^{\natural}\rangle$ produces the correct correlation functions on the algebra
\begin{equation}
	(\cup_m \A_{\tau_1, (m)})''.
\end{equation}
This algebra is in fact equal to all of $\A_{\tau_1}.$
To see this, note that $\A_{\tau_1}$ is generated by the Weyl operators $e^{i \phi[\psi]}$ for generic real $|\psi\rangle_{\mu_1} \in \K_{\mu_1}.$
But writing $|\psi\rangle_{\mu_1} = \sum_{j=1}^{\infty} c_j |e_j\rangle_{\mu_1},$ we have
\begin{equation}
e^{\,i \phi[\sum_{j=1}^{N} c_j e_j]} \;\xrightarrow{\;\text{strongly}\;}\; e^{\,i \phi[\psi]}
\end{equation}
and this limit is obviously in the von Neumann algebra generated by $\cup_m \A_{\tau_1, (m)}.$

Now we put together theorems \ref{thm:mixed-from-pure} and \ref{thm:abelian} --- which deal with the mixed-from-pure case and the abelian case, respectively --- to prove the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this
```

**Target Y Head**

```text
result (together with the simple logic of section \ref{sec:factorial-consequences}) automatically implies the general excitability theorem,  theorem \ref{thm:general-theorem}, which is the main result of the paper.

To prove theorem \ref{thm:c-pure-from-c-pure}, we make use of the decomposition from section \ref{sec:excitability-breakdown}, which tells us that for centrally pure states, we have $\omega_2 \prec \omega_1$ if and only if the following ``restriction maps'' are ultraweakly continuous: the map $\alpha_{\pm i}:\A_{\omega_1, \pm i}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{\pm i}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{1,\pm i}{\cal K}_{\mu_1} \text{  real}
    \label{eq:pure-piece-alpha}
\end{equation}
and the map
$\alpha_{0}:\A_{\omega_1, 0}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{0}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{0}{\cal K}_{\mu_1}
```

### gpt54_nano_medium | paper 2604.21800 | cut 307

- prompt chars: `5126`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
variance profile of \(P\) with respect to \(\boldsymbol E\) by the vector of squared compression coefficients
\begin{equation}
\boldsymbol\lambda(P)
:=
(\lambda_1(P),\dots,\lambda_m(P))\in[-1,1]^m,
\qquad
\boldsymbol\lambda(P)^2
:=
(\lambda_1(P)^2,\dots,\lambda_m(P)^2)\in[0,1]^m .
\end{equation}
Since each \(E_\alpha\) is a Pauli observable with eigenvalues \(\pm1\), we have
\begin{equation}
1-\lambda_\alpha(P)^2
=
\mathrm{Var}_{\rho_P}(E_\alpha),
\end{equation}
so \(\boldsymbol\lambda(P)^2\) is equivalently the profile of expectation squares (and hence variances) attained by the maximally mixed logical state \(\rho_P\).

Accordingly, we define the set of feasible variance profiles for rank \(K\) projectors by
\begin{equation}
\mathcal V_K(\boldsymbol E)
:=
\left\{
(\lambda_1(P)^2,\dots,\lambda_m(P)^2)\in[0,1]^m
:\;
P\in\mathcal P_K,\;
P E_\alpha P=\lambda_\alpha(P)\,P,\ \alpha=1,\dots,m
\right\}.
\label{eq:variance-profile-set}
\end{equation}
In numerical-range terms, since the \(E_\a
```

**Prompt Tail Before Returning Marker**

```text
ha)
=
\langle E_\alpha\rangle_{\rho_P}.
\end{equation}
We therefore associate with \(P\) the variance profile

% Notes about what's next:
% variance profile of \(P\) with respect to \(\boldsymbol E\) by the vector of squared compression coefficients
% \begin{equation}
% \boldsymbol\lambda(P)
% :=
% (\lambda_1(P),\dots,\lambda_m(P))\in[-1,1]^m,
% \qquad
% \boldsymbol\lambda(P)^2
% :=
% (\lambda_1(P)^2,\dots,\lambda_m(P)^2)\in[0,1]^m .
% \end{equation}
% Since each \(E_\alpha\) is a Pauli observable with eigenvalues \(\pm1\), we have
% \begin{equation}
% 1-\lambda_\alpha(P)^2
% =
% \mathrm{Var}_{\rho_P}(E_\alpha),
% \end{equation}
% so \(\boldsymbol\lambda(P)^2\) is equivalently the profile of expectation squares (and hence variances) attained by the maximally mixed logical state \(\rho_P\).
% 
% Accordingly, we define the set of feasible variance profiles for rank \(K\) projectors by
% \begin{equation}
% \mathcal V_K(\boldsymbol E)
% :=
% \left\{
% (\lambda_1(P)^2,\dots,\lambda_m(P)^2)\in[0,1]^m
% :\;
% P\in\mathcal P_K,\;
% P E_\alpha P=\lambda_\alpha(P)\,P,\ \alpha=1,\dots,m
% \right\}.
% \label{eq:variance-profile-set}
% \end{equation}
% In numerical-range terms, since the \(E_\a
```

**X Tail Given To Judge**

```text
{equation}
V(E)
:=
\left\{
\langle E\rangle_\rho^2
:\;
\rho\in\mathcal D(\mathcal H)
\right\},
\end{equation}
\begin{equation}
\mathcal D(\mathcal H)
=
\{\rho\in\mathcal B(\mathcal H):\rho\ge0,\ \Tr\rho=1\},
\end{equation}
and refer to this set as the variance range of \(E\). Since a Pauli observable has eigenvalues \(\pm1\), every value in \([0,1]\) is attainable, and therefore \(V(E)=[0,1]\). The nontrivial structure only appears after imposing higher-rank compression and error-detection constraints.

Motivated by recent work on Pauli expectation and variance geometry
\cite{xu2025simultaneous, Cabello2014Graph, XuSchwonnekWinter2024, BorelandTodorovWinter2022ConvexCorners, BorelandTodorovWinter2021, DuanSeveriniWinter2013},
we now fix a finite Pauli error set \(\mathcal E\subset\mathcal P_n\) and an ordered tuple \(\boldsymbol{E}=(E_1,\dots,E_m)\) selected from \(\mathcal E\). If \(P\in\mathcal P_K\) detects all operators in \(\mathcal E\), then in particular each \(E_\alpha\) compresses to a scalar on the code space:
\begin{equation}
P E_\alpha P=\lambda_\alpha(P)\,P,
\qquad \alpha=1,\dots,m .
\end{equation}
Since \(\rho_P=P/K\), these compression coefficients are exactly the corresponding code-state expectations,
\begin{equation}
\lambda_\alpha(P)
=
\Tr(\rho_P E_\alpha)
=
\langle E_\alpha\rangle_{\rho_P}.
\end{equation}
We therefore associate with \(P\) the variance profile
```

**Target Y Head**

```text
\begin{equation}
q(P)
:=
\bigl(
q_1(P),\dots,q_m(P)
\bigr),
\end{equation}
\begin{equation}
q_\alpha(P)
:=
\lambda_\alpha(P)^2
=
\langle E_\alpha\rangle_{\rho_P}^2,
\label{eq:variance-profile}
\end{equation}
and define the joint rank-$K$ variance range by
\begin{equation}
Q_K(\boldsymbol{E})
:=
\left\{
q(P)\in[0,1]^m
:\;
P\in\mathcal P_K \text{ is }\mathcal E\text{-detecting}
\right\},
\label{eq:QK-def}
\end{equation}
with the ambient detectable set \(\mathcal E\) understood from context. Equivalently, \(Q_K(\boldsymbol{E})\) is the set of all squared compression-coordinate vectors arising from rank-$K$ projectors that detect the prescribed Pauli set.

From this perspective, \(Q_K(\boldsymbol{E})\) is a higher-rank, code-constrained analogue of the joint variance body. Unlike the rank-$1$ setting, however, the admissible points are filtered by the requirement that one and the same rank-$K$ projector satisfy all of the Knill--Laflamme detection constraints. As a result, \(Q_K(\boldsymbo
```

### gpt54_nano_medium | paper 2604.19625 | cut 660

- prompt chars: `5082`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
It is convenient to implement this measurement by applying a phase-space rotation before standard homodyne detection. Concretely, let $R(\theta)=\exp(-i\theta \hat{a}^\dagger \hat{a})$; then
\[
R^\dagger(\theta)\,\hat{X}\,R(\theta)=\hat{X}_{\theta},
\]
so measuring $\hat{X}_{\theta}$ on $\rho$ is equivalent to measuring $\hat{X}$ on the rotated state $R(\theta)\rho R^\dagger(\theta)$. For a (single-mode) Gaussian state with Wigner covariance matrix $\gamma$ and displacement $d$, the probability density for the outcome $x$ of homodyne detection of $\hat{X}_{\theta}$ is Gaussian,
\[
p_\theta(x)=\frac{1}{\sqrt{2\pi\,V_\theta}}\exp\!\left[-\frac{(x-\mu_\theta)^2}{2V_\theta}\right],
\]
with mean and variance given by the appropriate projections of $(\gamma,d)$ along the $\theta$-quadrature direction. In particular, writing $\mu_\theta=\cos\theta\,\langle \hat{X}\rangle+\sin\theta\,\langle \hat{P}\rangle$ and $V_\theta=\cos^2\theta\,\mathrm{Var}(\hat{X})+\sin^2\theta\,\mathrm{Var}(\hat{P})+\
```

**Prompt Tail Before Returning Marker**

```text
evant readout schemes in this language. For instance, one may measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.

% Notes about what's next:
% It is convenient to implement this measurement by applying a phase-space rotation before standard homodyne detection. Concretely, let $R(\theta)=\exp(-i\theta \hat{a}^\dagger \hat{a})$; then
% \[
% R^\dagger(\theta)\,\hat{X}\,R(\theta)=\hat{X}_{\theta},
% \]
% so measuring $\hat{X}_{\theta}$ on $\rho$ is equivalent to measuring $\hat{X}$ on the rotated state $R(\theta)\rho R^\dagger(\theta)$. For a (single-mode) Gaussian state with Wigner covariance matrix $\gamma$ and displacement $d$, the probability density for the outcome $x$ of homodyne detection of $\hat{X}_{\theta}$ is Gaussian,
% \[
% p_\theta(x)=\frac{1}{\sqrt{2\pi\,V_\theta}}\exp\!\left[-\frac{(x-\mu_\theta)^2}{2V_\theta}\right],
% \]
% with mean and variance given by the appropriate projections of $(\gamma,d)$ along the $\theta$-quadrature direction. In particular, writing $\mu_\theta=\cos\theta\,\langle \hat{X}\rangle+\sin\theta\,\langle \hat{P}\rangle$ and $V_\theta=\cos^2\theta\,\mathrm{Var}(\hat{X})+\sin^2\theta\,\mathrm{Var}(\hat{P})+\
```

**X Tail Given To Judge**

```text
11\lambda^2+1
\le
16(1+\lambda^2)^2.
\end{equation}
Therefore
\begin{equation}
\sqrt{\lambda^4+6\lambda^3+7\lambda^2+\lambda}
\le
4(1+\lambda^2),
\end{equation}
and hence
\begin{equation}
E_0
\le
8\,\kappa L(1+\lambda^2)
\le
8c\,\delta
=
\mathcal{O}(\delta).
\end{equation}
This proves that the first contribution to the total error is
$\mathcal{O}(\delta)$.

Finally, since
\begin{equation}
s\le \left\lceil \log_4(1/\varepsilon)\right\rceil
=
\mathcal{O}(\log(1/\varepsilon)),
\end{equation}
the bounds in \eqref{eq:cor-proof-starting-runtime} give
\begin{equation}
N
=
\mathcal{O}(L^s)
=
L^{\,\mathcal{O}(\log(1/\varepsilon))}
\end{equation}
and
\begin{equation}
t
=
\mathcal{O}(Lm^3+m^2L^{s+1})
=
\mathcal{O}\!\left(
Lm^3+m^2L^{\,1+\mathcal{O}(\log(1/\varepsilon))}
\right),
\end{equation}
which prove \eqref{eq:simple-small-kappa-term-count} and
\eqref{eq:simple-small-kappa-runtime}.
\end{proof}

Let us now consider the readout stage for the proposed circuit design in Fig.~\ref{fig:circuit_scheme} yielding the superposition of Gaussian states as an output. Since quadrature detection is the basic measurement primitive in continuous-variable platforms \cite{RevModPhys.77.513}, a final Gaussian basis change allows one to express many relevant readout schemes in this language. For instance, one may measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.
```

**Target Y Head**

```text
This is natural in our setting, because the final Gaussian layer is able to change the measurement basis \cite{RevModPhys.84.621}. Bell-type measurements also fit into this framework, since they can be implemented by adding auxiliary modes, applying Gaussian interference, and then performing quadrature measurements \cite{PhysRevLett.80.869}.

Besides sampling from output quadrature distributions, one is often interested in expectation values of observables. Typical examples include moments and correlations such as $\langle \hat{X}_j\rangle$, $\langle \hat{X}_j^2\rangle$, $\langle \hat{X}_j\hat{X}_k\rangle$, $\langle \hat{P}_j\hat{P}_k\rangle$, and more general polynomial observables $O(\hat{\bm X},\hat{\bm P})$. These quantities are central in theoretical analysis, since they directly characterize the output state and provide the main objects compared across simulation methods. Accordingly, in this section we consider two readout tasks for the final coherent-state superposition: sampli
```

### gpt54_nano_high | paper 2604.19861 | cut 0

- prompt chars: `5074`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
now implies the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
Indeed, central purity implies that the inclusion problem may be reduced to fibres in which either the restriction becomes abelian or one is in the mixed-from-pure situation (see section \ref{sec:central-pure-reduction} for the precise reduction argument).
On each such fibre, the operator $Q$ controlling the intertwiner of the quasifree dynamics is exactly the same operator constructed above from the covariance data; in particular, the spectral condition $\ker Q=0$ and the Hilbert-Schmidt condition $Q-1\in\mathcal L^2(\mathcal K_{\mu_1})$ are inherited fibrewise.
Thus, combining theorem \ref{thm:mixed-from-pure} with theorem \ref{thm:abelian}, we conclude that for centrally pure $\tau_1$ the relation $\tau_2\prec \tau_1$ holds if and only if (i) $\mu_2\prec \mu_1$, (ii) $Q$ is injective, and (iii) $Q-1$ is Hilbert-Schmidt.
Moreover, whenever these conditions hold, the construction in the abel
```

**Prompt Tail Before Returning Marker**

```text
, respectively --- to prove the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this

% Notes about what's next:
% now implies the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
% Indeed, central purity implies that the inclusion problem may be reduced to fibres in which either the restriction becomes abelian or one is in the mixed-from-pure situation (see section \ref{sec:central-pure-reduction} for the precise reduction argument).
% On each such fibre, the operator $Q$ controlling the intertwiner of the quasifree dynamics is exactly the same operator constructed above from the covariance data; in particular, the spectral condition $\ker Q=0$ and the Hilbert-Schmidt condition $Q-1\in\mathcal L^2(\mathcal K_{\mu_1})$ are inherited fibrewise.
% Thus, combining theorem \ref{thm:mixed-from-pure} with theorem \ref{thm:abelian}, we conclude that for centrally pure $\tau_1$ the relation $\tau_2\prec \tau_1$ holds if and only if (i) $\mu_2\prec \mu_1$, (ii) $Q$ is injective, and (iii) $Q-1$ is Hilbert-Schmidt.
% Moreover, whenever these conditions hold, the construction in the abel
```

**X Tail Given To Judge**

```text
2^{\natural}\rangle.$

All that remains is to show that this vector, which we have constructed as the endpoint of a particular sequence, is actually a good representative for $\tau_2$ in $\H_{\tau_1}.$
By construction, each of the $|(\tau_2^{\natural})_{(m)}\rangle$ vectors produces the correct correlation functions of $\tau_2$ on the algebra $\A_{\tau_1, (m)}$ that is generated by the operators $\phi[e_1]$ through $\phi[e_m].$
So $|\tau_2^{\natural}\rangle$ produces the correct correlation functions on the algebra
\begin{equation}
	(\cup_m \A_{\tau_1, (m)})''.
\end{equation}
This algebra is in fact equal to all of $\A_{\tau_1}.$
To see this, note that $\A_{\tau_1}$ is generated by the Weyl operators $e^{i \phi[\psi]}$ for generic real $|\psi\rangle_{\mu_1} \in \K_{\mu_1}.$
But writing $|\psi\rangle_{\mu_1} = \sum_{j=1}^{\infty} c_j |e_j\rangle_{\mu_1},$ we have
\begin{equation}
e^{\,i \phi[\sum_{j=1}^{N} c_j e_j]} \;\xrightarrow{\;\text{strongly}\;}\; e^{\,i \phi[\psi]}
\end{equation}
and this limit is obviously in the von Neumann algebra generated by $\cup_m \A_{\tau_1, (m)}.$

Now we put together theorems \ref{thm:mixed-from-pure} and \ref{thm:abelian} --- which deal with the mixed-from-pure case and the abelian case, respectively --- to prove the centrally pure excitability result, i.e. theorem \ref{thm:c-pure-from-c-pure}.
As explained at the beginning of the section, this
```

**Target Y Head**

```text
result (together with the simple logic of section \ref{sec:factorial-consequences}) automatically implies the general excitability theorem,  theorem \ref{thm:general-theorem}, which is the main result of the paper.

To prove theorem \ref{thm:c-pure-from-c-pure}, we make use of the decomposition from section \ref{sec:excitability-breakdown}, which tells us that for centrally pure states, we have $\omega_2 \prec \omega_1$ if and only if the following ``restriction maps'' are ultraweakly continuous: the map $\alpha_{\pm i}:\A_{\omega_1, \pm i}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{\pm i}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{1,\pm i}{\cal K}_{\mu_1} \text{  real}
    \label{eq:pure-piece-alpha}
\end{equation}
and the map
$\alpha_{0}:\A_{\omega_1, 0}\to {\cal A}_{\omega_2}$ with
\begin{equation}
	\alpha_{0}(e^{i \phi[\psi]}) = e^{i \phi[L \psi]} \quad \text{with} \quad  |\psi\rangle_{\mu_1} \in \Pi_{0}{\cal K}_{\mu_1}
```

### gpt54_nano_high | paper 2604.21800 | cut 307

- prompt chars: `5135`
- Z chars: `999`
- target chars: `1000`

**Z Head**

```text
\[
\boldsymbol\lambda(P)
:=
\bigl(\lambda_\alpha(P)\bigr)_{\alpha=1}^m,
\qquad
\lambda_\alpha(P)
=
\langle E_\alpha\rangle_{\rho_P},
\]
and with it the variance profile
\begin{equation}
\boldsymbol v(P)
:=
\bigl(v_\alpha(P)\bigr)_{\alpha=1}^m
\in[0,1]^m,
\qquad
v_\alpha(P)
:=
\langle E_\alpha\rangle_{\rho_P}^2
=\lambda_\alpha(P)^2 .
\label{eq:variance-profile}
\end{equation}
By construction, each component satisfies \(v_\alpha(P)\in V(E_\alpha)\), where for Pauli observables \(V(E_\alpha)=[0,1]\). The joint constraints imposed by the higher-rank compression therefore appear precisely as correlations between the entries of \(\boldsymbol v(P)\).

Fixing the ordered tuple \(\boldsymbol E=(E_1,\dots,E_m)\), we define the corresponding higher-rank variance set as
\begin{equation}
\mathcal V_K(\boldsymbol E)
:=
\left\{
\boldsymbol v(P)\in[0,1]^m:
P\in\mathcal P_K,\
P E_\alpha P=\lambda_\alpha(P)P,\ \alpha=1,\dots,m
\right\}.
\label{eq:VK-variance-set}
\end{equation}
Equivalently, \(\boldsym
```

**Prompt Tail Before Returning Marker**

```text
ngle E_\alpha\rangle_{\rho_P}.
\end{equation}
We therefore associate with \(P\) the variance profile

% Notes about what's next:
% \[
% \boldsymbol\lambda(P)
% :=
% \bigl(\lambda_\alpha(P)\bigr)_{\alpha=1}^m,
% \qquad
% \lambda_\alpha(P)
% =
% \langle E_\alpha\rangle_{\rho_P},
% \]
% and with it the variance profile
% \begin{equation}
% \boldsymbol v(P)
% :=
% \bigl(v_\alpha(P)\bigr)_{\alpha=1}^m
% \in[0,1]^m,
% \qquad
% v_\alpha(P)
% :=
% \langle E_\alpha\rangle_{\rho_P}^2
% =\lambda_\alpha(P)^2 .
% \label{eq:variance-profile}
% \end{equation}
% By construction, each component satisfies \(v_\alpha(P)\in V(E_\alpha)\), where for Pauli observables \(V(E_\alpha)=[0,1]\). The joint constraints imposed by the higher-rank compression therefore appear precisely as correlations between the entries of \(\boldsymbol v(P)\).
% 
% Fixing the ordered tuple \(\boldsymbol E=(E_1,\dots,E_m)\), we define the corresponding higher-rank variance set as
% \begin{equation}
% \mathcal V_K(\boldsymbol E)
% :=
% \left\{
% \boldsymbol v(P)\in[0,1]^m:
% P\in\mathcal P_K,\
% P E_\alpha P=\lambda_\alpha(P)P,\ \alpha=1,\dots,m
% \right\}.
% \label{eq:VK-variance-set}
% \end{equation}
% Equivalently, \(\boldsym
```

**X Tail Given To Judge**

```text
{equation}
V(E)
:=
\left\{
\langle E\rangle_\rho^2
:\;
\rho\in\mathcal D(\mathcal H)
\right\},
\end{equation}
\begin{equation}
\mathcal D(\mathcal H)
=
\{\rho\in\mathcal B(\mathcal H):\rho\ge0,\ \Tr\rho=1\},
\end{equation}
and refer to this set as the variance range of \(E\). Since a Pauli observable has eigenvalues \(\pm1\), every value in \([0,1]\) is attainable, and therefore \(V(E)=[0,1]\). The nontrivial structure only appears after imposing higher-rank compression and error-detection constraints.

Motivated by recent work on Pauli expectation and variance geometry
\cite{xu2025simultaneous, Cabello2014Graph, XuSchwonnekWinter2024, BorelandTodorovWinter2022ConvexCorners, BorelandTodorovWinter2021, DuanSeveriniWinter2013},
we now fix a finite Pauli error set \(\mathcal E\subset\mathcal P_n\) and an ordered tuple \(\boldsymbol{E}=(E_1,\dots,E_m)\) selected from \(\mathcal E\). If \(P\in\mathcal P_K\) detects all operators in \(\mathcal E\), then in particular each \(E_\alpha\) compresses to a scalar on the code space:
\begin{equation}
P E_\alpha P=\lambda_\alpha(P)\,P,
\qquad \alpha=1,\dots,m .
\end{equation}
Since \(\rho_P=P/K\), these compression coefficients are exactly the corresponding code-state expectations,
\begin{equation}
\lambda_\alpha(P)
=
\Tr(\rho_P E_\alpha)
=
\langle E_\alpha\rangle_{\rho_P}.
\end{equation}
We therefore associate with \(P\) the variance profile
```

**Target Y Head**

```text
\begin{equation}
q(P)
:=
\bigl(
q_1(P),\dots,q_m(P)
\bigr),
\end{equation}
\begin{equation}
q_\alpha(P)
:=
\lambda_\alpha(P)^2
=
\langle E_\alpha\rangle_{\rho_P}^2,
\label{eq:variance-profile}
\end{equation}
and define the joint rank-$K$ variance range by
\begin{equation}
Q_K(\boldsymbol{E})
:=
\left\{
q(P)\in[0,1]^m
:\;
P\in\mathcal P_K \text{ is }\mathcal E\text{-detecting}
\right\},
\label{eq:QK-def}
\end{equation}
with the ambient detectable set \(\mathcal E\) understood from context. Equivalently, \(Q_K(\boldsymbol{E})\) is the set of all squared compression-coordinate vectors arising from rank-$K$ projectors that detect the prescribed Pauli set.

From this perspective, \(Q_K(\boldsymbol{E})\) is a higher-rank, code-constrained analogue of the joint variance body. Unlike the rank-$1$ setting, however, the admissible points are filtered by the requirement that one and the same rank-$K$ projector satisfy all of the Knill--Laflamme detection constraints. As a result, \(Q_K(\boldsymbo
```

### gpt54_nano_high | paper 2604.19625 | cut 660

- prompt chars: `5100`
- Z chars: `1000`
- target chars: `1000`

**Z Head**

```text
To make contact with the circuit output, it is convenient to express the measurement in a vector form. Writing $\hat{\mathbf{X}}_\theta:=\hat{\mathbf{X}}\cos\theta+\hat{\mathbf{P}}\sin\theta\in\mathbb{R}^m$ and denoting by $\ket{\mathbf{x}_\theta}$ the (generalized) eigenstate with eigenvalue $\mathbf{x}\in\mathbb{R}^m$, the probability density for an $m$-mode homodyne readout is
\begin{equation}
p_\theta(\mathbf{x})
=
\bigl|\braket{\mathbf{x}_\theta}{\psi_{\mathrm{out}}}\bigr|^2 .
\end{equation}
In our setting the final state can be written as a coherent superposition of Gaussian branches,
$\ket{\psi_{\mathrm{out}}}=\sum_{k=1}^{N_{\mathrm{out}}} c_k \ket{G_k}$, where each $\ket{G_k}$ is a (generally displaced) Gaussian state. Consequently,
\begin{equation}
\label{eq:readout-prob-quad-sum}
p_\theta(\mathbf{x})
=
\left|
\sum_{k=1}^{N_{\mathrm{out}}} c_k\,\braket{\mathbf{x}_\theta}{G_k}
\right|^2
=
\sum_{k,k'} c_k c_{k'}^*\,
\braket{G_{k'}}{\mathbf{x}_\theta}\braket{\mathbf{x}_\theta}{G_
```

**Prompt Tail Before Returning Marker**

```text
mes in this language. For instance, one may measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.

% Notes about what's next:
% To make contact with the circuit output, it is convenient to express the measurement in a vector form. Writing $\hat{\mathbf{X}}_\theta:=\hat{\mathbf{X}}\cos\theta+\hat{\mathbf{P}}\sin\theta\in\mathbb{R}^m$ and denoting by $\ket{\mathbf{x}_\theta}$ the (generalized) eigenstate with eigenvalue $\mathbf{x}\in\mathbb{R}^m$, the probability density for an $m$-mode homodyne readout is
% \begin{equation}
% p_\theta(\mathbf{x})
% =
% \bigl|\braket{\mathbf{x}_\theta}{\psi_{\mathrm{out}}}\bigr|^2 .
% \end{equation}
% In our setting the final state can be written as a coherent superposition of Gaussian branches,
% $\ket{\psi_{\mathrm{out}}}=\sum_{k=1}^{N_{\mathrm{out}}} c_k \ket{G_k}$, where each $\ket{G_k}$ is a (generally displaced) Gaussian state. Consequently,
% \begin{equation}
% \label{eq:readout-prob-quad-sum}
% p_\theta(\mathbf{x})
% =
% \left|
% \sum_{k=1}^{N_{\mathrm{out}}} c_k\,\braket{\mathbf{x}_\theta}{G_k}
% \right|^2
% =
% \sum_{k,k'} c_k c_{k'}^*\,
% \braket{G_{k'}}{\mathbf{x}_\theta}\braket{\mathbf{x}_\theta}{G_
```

**X Tail Given To Judge**

```text
11\lambda^2+1
\le
16(1+\lambda^2)^2.
\end{equation}
Therefore
\begin{equation}
\sqrt{\lambda^4+6\lambda^3+7\lambda^2+\lambda}
\le
4(1+\lambda^2),
\end{equation}
and hence
\begin{equation}
E_0
\le
8\,\kappa L(1+\lambda^2)
\le
8c\,\delta
=
\mathcal{O}(\delta).
\end{equation}
This proves that the first contribution to the total error is
$\mathcal{O}(\delta)$.

Finally, since
\begin{equation}
s\le \left\lceil \log_4(1/\varepsilon)\right\rceil
=
\mathcal{O}(\log(1/\varepsilon)),
\end{equation}
the bounds in \eqref{eq:cor-proof-starting-runtime} give
\begin{equation}
N
=
\mathcal{O}(L^s)
=
L^{\,\mathcal{O}(\log(1/\varepsilon))}
\end{equation}
and
\begin{equation}
t
=
\mathcal{O}(Lm^3+m^2L^{s+1})
=
\mathcal{O}\!\left(
Lm^3+m^2L^{\,1+\mathcal{O}(\log(1/\varepsilon))}
\right),
\end{equation}
which prove \eqref{eq:simple-small-kappa-term-count} and
\eqref{eq:simple-small-kappa-runtime}.
\end{proof}

Let us now consider the readout stage for the proposed circuit design in Fig.~\ref{fig:circuit_scheme} yielding the superposition of Gaussian states as an output. Since quadrature detection is the basic measurement primitive in continuous-variable platforms \cite{RevModPhys.77.513}, a final Gaussian basis change allows one to express many relevant readout schemes in this language. For instance, one may measure rotated quadratures such as $\hat{X}_{\theta}=\hat{X}\cos\theta+\hat{P}\sin\theta$.
```

**Target Y Head**

```text
This is natural in our setting, because the final Gaussian layer is able to change the measurement basis \cite{RevModPhys.84.621}. Bell-type measurements also fit into this framework, since they can be implemented by adding auxiliary modes, applying Gaussian interference, and then performing quadrature measurements \cite{PhysRevLett.80.869}.

Besides sampling from output quadrature distributions, one is often interested in expectation values of observables. Typical examples include moments and correlations such as $\langle \hat{X}_j\rangle$, $\langle \hat{X}_j^2\rangle$, $\langle \hat{X}_j\hat{X}_k\rangle$, $\langle \hat{P}_j\hat{P}_k\rangle$, and more general polynomial observables $O(\hat{\bm X},\hat{\bm P})$. These quantities are central in theoretical analysis, since they directly characterize the output state and provide the main objects compared across simulation methods. Accordingly, in this section we consider two readout tasks for the final coherent-state superposition: sampli
```
