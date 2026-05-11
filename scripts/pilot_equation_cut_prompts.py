"""Pilot equation-cut prompt construction for the RLVR text-prediction project.

This script is intentionally small and read-only. It extracts display equations
from one TeX file, picks candidate internal cuts, and prints the predictor and
judge prompts we would use before any API calls.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRAINING = ROOT / "training documents"

DISPLAY_ENV_RE = re.compile(
    r"\\begin\{(?P<env>equation\*?|align\*?|gather\*?|multline\*?|eqnarray\*?)\}"
    r"(?P<body>.*?)"
    r"\\end\{(?P=env)\}",
    flags=re.DOTALL,
)
BRACKET_DISPLAY_RE = re.compile(r"\\\[(?P<body>.*?)\\\]", flags=re.DOTALL)
LABEL_RE = re.compile(r"\\label\{[^{}]*\}")
TAG_RE = re.compile(r"\\tag\{[^{}]*\}")
OPERATOR_RE = re.compile(
    r"\\Longrightarrow|\\longrightarrow|\\Rightarrow|\\rightarrow|\\mapsto|"
    r"\\leq|\\geq|\\le|\\ge|\\approx|\\simeq|\\sim|\\cong|\\equiv|"
    r"\\propto|\\in\b|:=|=>|<=|>=|[=<>]"
)
UNSUPPORTED_DISPLAY_MARKUP = (
    r"\begin{tikzpicture}",
    r"\begin{tikzcd}",
    r"\begin{picture}",
    r"\begin{fmfgraph}",
    r"\includegraphics",
    r"\feynmandiagram",
)


@dataclass(frozen=True)
class DisplayEquation:
    env: str
    start: int
    end: int
    body_start: int
    body_end: int
    body: str


@dataclass(frozen=True)
class EquationCut:
    paper_id: str
    cut_id: int
    env: str
    equation_index: int
    equation_start: int
    equation_start_line: int
    equation_body_start_line: int
    cut_source_char: int
    cut_source_line: int
    predictor_context_available_chars: int
    equation_body_len: int
    cut_pos: int
    cut_frac: float
    operator: str
    operator_start: int
    operator_left_char: str
    operator_right_char: str
    operator_has_adjacent_whitespace: bool
    operator_surrounded_by_whitespace: bool
    operator_class: str
    env_class: str
    env_is_starred: bool
    equation_body_lines: int
    x_eq_len: int
    x_eq_lines: int
    y_lines: int
    cut_line_in_equation: int
    cut_near_tex_linebreak: bool
    x_eq: str
    y: str
    y_len: int
    target_chars: int
    budget_chars: int
    predictor_context: str
    bare_b_context: str
    raw_precontext_budget: str
    predictor_prompt: str
    bare_b_judge_prompt_prefix: str
    bare_b_judge_prompt_full: str
    judge_prompt_template: str
    judge_prompt_empty: str
    judge_prompt_raw_precontext: str
    judge_prompt_oracle: str


def strip_latex_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        cut = None
        escaped = False
        for idx, char in enumerate(line):
            if char == "\\":
                escaped = not escaped
                continue
            if char == "%" and not escaped:
                cut = idx
                break
            escaped = False
        if cut is None:
            lines.append(line.rstrip())
        else:
            lines.append(line[:cut].rstrip())
    return "\n".join(lines)


def strip_latex_false_conditionals(text: str) -> str:
    pattern = re.compile(r"\\iffalse\b.*?\\fi\b", flags=re.DOTALL)
    previous = None
    while previous != text:
        previous = text
        text = pattern.sub("\n", text)
    return text


def document_body(tex: str) -> str:
    begin = tex.find(r"\begin{document}")
    if begin >= 0:
        tex = tex[begin + len(r"\begin{document}") :]
    end = tex.find(r"\end{document}")
    if end >= 0:
        tex = tex[:end]
    return tex


def clean_tex(tex: str) -> str:
    return document_body(strip_latex_false_conditionals(strip_latex_comments(tex)))


def clean_equation_body(body: str) -> str:
    body = LABEL_RE.sub("", body)
    body = TAG_RE.sub("", body)
    lines = [line.rstrip() for line in body.strip().splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def extract_display_equations(tex: str) -> list[DisplayEquation]:
    displays: list[DisplayEquation] = []
    spans: list[tuple[int, int]] = []

    for match in DISPLAY_ENV_RE.finditer(tex):
        env = match.group("env")
        body_start = match.start("body")
        body_end = match.end("body")
        displays.append(
            DisplayEquation(
                env=env,
                start=match.start(),
                end=match.end(),
                body_start=body_start,
                body_end=body_end,
                body=match.group("body"),
            )
        )
        spans.append((match.start(), match.end()))

    def overlaps_existing(start: int, end: int) -> bool:
        return any(not (end <= old_start or start >= old_end) for old_start, old_end in spans)

    for match in BRACKET_DISPLAY_RE.finditer(tex):
        if overlaps_existing(match.start(), match.end()):
            continue
        displays.append(
            DisplayEquation(
                env="bracket-display",
                start=match.start(),
                end=match.end(),
                body_start=match.start("body"),
                body_end=match.end("body"),
                body=match.group("body"),
            )
        )

    return sorted(displays, key=lambda d: d.start)


def skip_following_space(text: str, pos: int) -> int:
    while pos < len(text) and text[pos].isspace():
        pos += 1
    return pos


def brace_depths(text: str) -> list[int]:
    depths: list[int] = []
    depth = 0
    escaped = False
    for char in text:
        depths.append(depth)
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth = max(0, depth - 1)
    return depths


def candidate_operator_cuts(body: str) -> list[tuple[int, str, int]]:
    """Return cut positions as (cut_pos, operator_text, operator_start)."""
    candidates: list[tuple[int, str, int]] = []
    for match in OPERATOR_RE.finditer(body):
        candidates.append((skip_following_space(body, match.end()), match.group(0), match.start()))

    depths = brace_depths(body)
    for idx, char in enumerate(body):
        if char not in "+-":
            continue
        if idx == 0 or idx >= len(depths):
            continue
        # This is deliberately rough: allow low-depth additive splits, but skip
        # obvious command names and exponents/subscripts.
        prev = body[idx - 1]
        if prev in "_^\\{([":
            continue
        if depths[idx] <= 1:
            candidates.append((skip_following_space(body, idx + 1), char, idx))

    dedup: dict[int, tuple[int, str, int]] = {}
    for item in candidates:
        dedup.setdefault(item[0], item)
    return sorted(dedup.values(), key=lambda item: item[0])


def classify_operator(op: str) -> str:
    if op in {"=", ":=", "=>"}:
        return "equality_or_definition"
    if op in {"\\leq", "\\le", "\\geq", "\\ge", "<=", ">=", "<", ">"}:
        return "inequality_or_order"
    if op in {"\\in"}:
        return "membership"
    if op in {"\\approx", "\\simeq", "\\sim", "\\cong", "\\equiv", "\\propto"}:
        return "approx_or_equivalence"
    if op in {"\\Longrightarrow", "\\longrightarrow", "\\Rightarrow", "\\rightarrow", "\\mapsto"}:
        return "arrow_or_implication"
    if op in {"+", "-"}:
        return "additive"
    return "other_relation"


def classify_env(env: str) -> str:
    if env == "bracket-display":
        return "bracket_display"
    base = env.rstrip("*")
    if base in {"align", "eqnarray"}:
        return "alignment"
    if base in {"equation"}:
        return "single_equation"
    if base in {"gather", "multline"}:
        return "multi_line_display"
    return "other_display"


def has_tex_linebreak_near(text: str, pos: int, radius: int = 12) -> bool:
    window = text[max(0, pos - radius) : min(len(text), pos + radius)]
    return r"\\" in window


def has_unsupported_display_markup(body: str) -> bool:
    return any(marker in body for marker in UNSUPPORTED_DISPLAY_MARKUP)


def char_at(text: str, pos: int) -> str:
    if 0 <= pos < len(text):
        return text[pos]
    return ""


def env_open(env: str) -> str:
    if env == "bracket-display":
        return r"\["
    return f"\\begin{{{env}}}"


def env_close(env: str) -> str:
    if env == "bracket-display":
        return r"\]"
    return f"\\end{{{env}}}"


def make_predictor_prompt(predictor_context: str, x_eq: str, target_chars: int, env: str) -> str:
    return (
        "You are given recent context from a technical paper and the beginning of a "
        "LaTeX display equation.\n"
        "Continue the equation from exactly where it stops, in about "
        f"{target_chars} characters or fewer.\n"
        "Write only the continuation. Do not write explanatory prose. Do not write "
        f"{env_close(env)}.\n\n"
        f"Recent paper context:\n{predictor_context}\n\n"
        f"Equation prefix:\n{env_open(env)}\n{x_eq}"
    )


def make_bare_judge_prefix(bare_judge_context: str, x_eq: str, env: str) -> str:
    return f"{bare_judge_context}\n{env_open(env)}\n{x_eq}"


def make_bare_judge_full(bare_judge_context: str, x_eq: str, y: str, env: str) -> str:
    return f"{make_bare_judge_prefix(bare_judge_context, x_eq, env)}{y}\n{env_close(env)}"


def make_judge_prompt(x_eq: str, y: str, z: str, env: str) -> str:
    return (
        "% First equation:\n"
        f"{env_open(env)}\n"
        f"{x_eq}{z}\n"
        f"{env_close(env)}\n\n"
        "% Same equation:\n"
        f"{env_open(env)}\n"
        f"{x_eq}{y}"
    )


def make_judge_template(x_eq: str, y: str, env: str) -> str:
    return make_judge_prompt(x_eq, y, "{Z}", env)


def build_cuts(
    tex: str,
    paper_id: str,
    y_min: int,
    y_max: int,
    slack: int,
    predictor_context_chars: int,
    bare_tail_multiplier: float,
    min_predictor_context_chars: int,
) -> tuple[list[EquationCut], dict[str, int]]:
    displays = extract_display_equations(tex)
    line_starts = [0]
    for match in re.finditer(r"\n", tex):
        line_starts.append(match.end())

    def line_number(pos: int) -> int:
        # 1-based source line in the cleaned TeX text used for extraction.
        lo = 0
        hi = len(line_starts)
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            if line_starts[mid] <= pos:
                lo = mid
            else:
                hi = mid
        return lo + 1

    cuts: list[EquationCut] = []
    stats = {
        "display_equations": len(displays),
        "nonempty_equations": 0,
        "operator_candidates_mid_third": 0,
        "accepted_cuts": 0,
        "reject_y_too_short": 0,
        "reject_y_too_long": 0,
        "reject_no_mid_operator": 0,
        "reject_insufficient_predictor_context": 0,
        "reject_unsupported_display_markup": 0,
    }

    cut_id = 0
    for equation_index, display in enumerate(displays):
        body = clean_equation_body(display.body)
        if not body:
            continue
        stats["nonempty_equations"] += 1
        if has_unsupported_display_markup(body):
            stats["reject_unsupported_display_markup"] += 1
            continue
        if display.start < min_predictor_context_chars:
            stats["reject_insufficient_predictor_context"] += 1
            continue
        length = len(body)
        left = math.floor(length / 3)
        right = math.ceil(2 * length / 3)
        candidates = [
            item for item in candidate_operator_cuts(body)
            if left <= item[0] <= right
        ]
        stats["operator_candidates_mid_third"] += len(candidates)
        if not candidates:
            stats["reject_no_mid_operator"] += 1
            continue

        accepted_for_eq = False
        # Keep at most one cut per display equation. Nearby equations may
        # overlap in context, but same-equation cuts are not independent enough
        # for the first pilot. Prefer the cut nearest the middle whose suffix is
        # in range.
        candidates = sorted(candidates, key=lambda item: abs(item[0] - length / 2))
        for cut_pos, op, op_start in candidates:
            y = body[cut_pos:]
            y_len = len(y)
            if y_len < y_min:
                stats["reject_y_too_short"] += 1
                continue
            if y_len > y_max:
                stats["reject_y_too_long"] += 1
                continue
            x_eq = body[:cut_pos]
            x_eq_lines = x_eq.count("\n") + 1 if x_eq else 1
            operator_left_char = char_at(body, op_start - 1)
            operator_right_char = char_at(body, op_start + len(op))
            operator_left_ws = bool(operator_left_char and operator_left_char.isspace())
            operator_right_ws = bool(operator_right_char and operator_right_char.isspace())
            target_chars = int(math.ceil(y_len / 10) * 10)
            budget_chars = y_len + slack
            source_cut = display.body_start + cut_pos
            source_eq_start = display.start
            predictor_context = tex[
                max(0, source_eq_start - predictor_context_chars) : source_eq_start
            ].rstrip()
            bare_tail_chars = max(0, int(math.ceil(budget_chars * bare_tail_multiplier)))
            bare_b_context = tex[max(0, source_eq_start - bare_tail_chars) : source_eq_start].rstrip()
            raw_precontext = tex[max(0, source_cut - budget_chars) : source_cut]
            predictor_prompt = make_predictor_prompt(
                predictor_context, x_eq, target_chars, display.env
            )
            judge_template = make_judge_template(x_eq, y, display.env)
            cut = EquationCut(
                paper_id=paper_id,
                cut_id=cut_id,
                env=display.env,
                equation_index=equation_index,
                equation_start=display.start,
                equation_start_line=line_number(display.start),
                equation_body_start_line=line_number(display.body_start),
                cut_source_char=source_cut,
                cut_source_line=line_number(source_cut),
                predictor_context_available_chars=display.start,
                equation_body_len=length,
                cut_pos=cut_pos,
                cut_frac=round(cut_pos / length, 4),
                operator=op,
                operator_start=op_start,
                operator_left_char=operator_left_char,
                operator_right_char=operator_right_char,
                operator_has_adjacent_whitespace=operator_left_ws or operator_right_ws,
                operator_surrounded_by_whitespace=operator_left_ws and operator_right_ws,
                operator_class=classify_operator(op),
                env_class=classify_env(display.env),
                env_is_starred=display.env.endswith("*"),
                equation_body_lines=body.count("\n") + 1,
                x_eq_len=len(x_eq),
                x_eq_lines=x_eq_lines,
                y_lines=y.count("\n") + 1 if y else 1,
                cut_line_in_equation=x_eq_lines,
                cut_near_tex_linebreak=has_tex_linebreak_near(body, cut_pos),
                x_eq=x_eq,
                y=y,
                y_len=y_len,
                target_chars=target_chars,
                budget_chars=budget_chars,
                predictor_context=predictor_context,
                bare_b_context=bare_b_context,
                raw_precontext_budget=raw_precontext,
                predictor_prompt=predictor_prompt,
                bare_b_judge_prompt_prefix=make_bare_judge_prefix(
                    bare_b_context, x_eq, display.env
                ),
                bare_b_judge_prompt_full=make_bare_judge_full(
                    bare_b_context, x_eq, y, display.env
                ),
                judge_prompt_template=judge_template,
                judge_prompt_empty=make_judge_prompt(x_eq, y, "", display.env),
                judge_prompt_raw_precontext=make_judge_prompt(x_eq, y, raw_precontext, display.env),
                judge_prompt_oracle=make_judge_prompt(x_eq, y, y, display.env),
            )
            cuts.append(cut)
            cut_id += 1
            accepted_for_eq = True
            break
        if accepted_for_eq:
            stats["accepted_cuts"] += 1

    return cuts, stats


def clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[clipped]..."


def print_sample(cut: EquationCut, max_chars: int) -> None:
    print("=" * 88)
    print(
        f"cut_id={cut.cut_id} env={cut.env} equation_index={cut.equation_index} "
        f"len_eq={cut.equation_body_len} cut={cut.cut_pos} frac={cut.cut_frac} "
        f"op={cut.operator!r}/{cut.operator_class} len_y={cut.y_len} "
        f"target={cut.target_chars} budget={cut.budget_chars}"
    )
    print("\n--- X_eq ---")
    print(clip(cut.x_eq, max_chars))
    print("\n--- Y ---")
    print(clip(cut.y, max_chars))
    print("\n--- raw_precontext_budget control text ---")
    print(clip(cut.raw_precontext_budget, max_chars))
    print("\n--- predictor prompt ---")
    print(clip(cut.predictor_prompt, max_chars * 2))
    print("\n--- bare_B contiguous judge prompt prefix (score Y after this) ---")
    print(clip(cut.bare_b_judge_prompt_prefix, max_chars * 2))
    print("\n--- bare_B contiguous judge prompt full preview ---")
    print(clip(cut.bare_b_judge_prompt_full, max_chars * 2))
    print("\n--- judge prompt template ---")
    print(clip(cut.judge_prompt_template, max_chars * 2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tex_file", type=Path)
    parser.add_argument("--y-min", type=int, default=50)
    parser.add_argument("--y-max", type=int, default=400)
    parser.add_argument("--slack", type=int, default=40)
    parser.add_argument("--predictor-context-chars", type=int, default=10000)
    parser.add_argument("--min-predictor-context-chars", type=int, default=10000)
    parser.add_argument("--bare-tail-multiplier", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--sample-offset", type=int, default=0)
    parser.add_argument("--max-chars", type=int, default=900)
    parser.add_argument("--jsonl-out", type=Path)
    args = parser.parse_args()

    tex_path = args.tex_file
    if not tex_path.is_absolute():
        tex_path = ROOT / tex_path
    paper_id = tex_path.stem.replace("arxiv-", "").replace("arXiv-", "").replace("-", ".")
    tex = clean_tex(tex_path.read_text(encoding="utf-8", errors="replace"))
    cuts, stats = build_cuts(
        tex,
        paper_id,
        args.y_min,
        args.y_max,
        args.slack,
        args.predictor_context_chars,
        args.bare_tail_multiplier,
        args.min_predictor_context_chars,
    )

    print(f"paper_id: {paper_id}")
    print(f"tex_file: {tex_path}")
    print("criteria:")
    print(f"  cut: operator/relation in middle third")
    print(f"  y_len: {args.y_min}..{args.y_max} chars, using full equation suffix")
    print(f"  predictor target: ceil(len(Y)/10)*10 chars or fewer")
    print(f"  z/control budget: len(Y)+{args.slack} chars")
    print(f"  predictor context tail: {args.predictor_context_chars} chars before equation")
    print(f"  minimum available predictor context before equation: {args.min_predictor_context_chars} chars")
    print(
        f"  bare control tail: {args.bare_tail_multiplier:g} * B chars before equation, "
        "where B=len(Y)+slack"
    )
    print("stats:")
    print(json.dumps(stats, indent=2, sort_keys=True))

    if args.jsonl_out:
        out_path = args.jsonl_out
        if not out_path.is_absolute():
            out_path = ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as handle:
            for cut in cuts:
                handle.write(json.dumps(asdict(cut), ensure_ascii=False) + "\n")
        print(f"wrote: {out_path}")

    for cut in cuts[args.sample_offset : args.sample_offset + args.samples]:
        print_sample(cut, args.max_chars)


if __name__ == "__main__":
    main()
