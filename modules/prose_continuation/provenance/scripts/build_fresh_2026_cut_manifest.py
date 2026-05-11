"""Build a dry-run X/Y cut manifest for the fresh 2026 paper slate."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRAINING = ROOT / "training documents"
DEFAULT_OUT = ROOT / "experiments" / "2026-04-27_fresh20_cut_manifest_tex_suffix_v2"
DEFAULT_IDS = [
    "2604.17369",
    "2604.21800",
    "2604.19625",
    "2604.21866",
    "2604.20619",
    "2604.18675",
    "2604.19082",
    "2604.18405",
    "2604.17649",
    "2604.19881",
    "2604.19731",
    "2604.18672",
    "2604.21408",
    "2604.21447",
    "2604.20418",
    "2604.19155",
    "2604.19885",
    "2604.20674",
    "2604.18692",
    "2604.22745",
]
DEFAULT_VIEWS = [
    "same_x_j4000_y1800:4000:4000:1800",
    "decoupled_x_j4000_p12000_y1800:4000:12000:1800",
    "decoupled_x_j4500_p12000_y1800:4500:12000:1800",
]

SECTION_RE = re.compile(
    r"\\(?P<kind>section|subsection|subsubsection)\*?\{(?P<title>[^{}\n]*(?:\{[^{}\n]*\}[^{}\n]*)*)\}",
    flags=re.IGNORECASE,
)
EXCLUDE_SECTION_RE = re.compile(
    r"acknowledg|appendix|bibliography|references|conclusion|outlook|"
    r"introduction|related work|overview",
    flags=re.IGNORECASE,
)
EXCLUDE_BLOCK_MARKERS = (
    "\\maketitle",
    "\\tableofcontents",
    "\\bibliographystyle",
    "\\bibliography",
    "\\begin{thebibliography",
    "\\includegraphics",
    "\\begin{figure",
    "\\end{figure",
    "\\begin{table",
    "\\end{table",
    "\\begin{tikzpicture",
)
TECH_MARKERS = (
    "\\begin{equation",
    "\\begin{align",
    "\\begin{gather",
    "\\begin{multline",
    "\\begin{theorem",
    "\\begin{lemma",
    "\\begin{proposition",
    "\\begin{corollary",
    "\\begin{definition",
    "\\begin{proof",
    "\\begin{algorithm",
    "\\[",
    "$$",
)
ENV_START_RE = re.compile(r"\\begin\{([^}]+)\}")
ENV_END_RE = re.compile(r"\\end\{([^}]+)\}")


@dataclass(frozen=True)
class Block:
    paper_id: str
    section: str
    block_index: int
    start: int
    end: int
    text: str
    word_count: int
    tech_score: int


@dataclass(frozen=True)
class CutAnchor:
    paper_id: str
    cut_index: int
    section: str
    block_index: int
    split_mode: str
    pre_cut_text: str
    post_cut_text: str
    current_block_prefix: str
    current_block_suffix: str
    block_word_count: int
    block_tech_score: int
    balanced_prefix: bool
    balanced_suffix: bool
    would_balance_reject: bool
    split_inside_environment: bool
    split_environment_stack: list[str]
    cut_source_char: int
    pre_source_available_chars: int
    post_source_available_chars: int
    has_equation_available: bool
    has_theorem_like_available: bool
    has_proof_available: bool


@dataclass(frozen=True)
class Cut:
    paper_id: str
    cut_index: int
    view_name: str
    context_regime: str
    section: str
    block_index: int
    split_mode: str
    judge_x_text: str
    predictor_x_text: str
    y_text: str
    x_tail: str
    current_block_prefix: str
    current_block_suffix: str
    judge_x_chars: int
    predictor_x_chars: int
    y_chars: int
    y_words: int
    block_word_count: int
    block_tech_score: int
    balanced_prefix: bool
    balanced_suffix: bool
    would_balance_reject: bool
    split_inside_environment: bool
    split_environment_stack: list[str]
    cut_source_char: int
    y_source_available_chars: int
    has_equation: bool
    has_theorem_like: bool
    has_proof: bool


def strip_latex_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        cut = len(line)
        for index, char in enumerate(line):
            if char != "%":
                continue
            backslashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                cut = index
                break
        lines.append(line[:cut].rstrip())
    return "\n".join(lines)


def strip_latex_false_conditionals(text: str) -> str:
    pattern = re.compile(r"\\iffalse\b.*?\\fi\b", flags=re.DOTALL)
    previous = None
    while previous != text:
        previous = text
        text = pattern.sub("\n", text)
    return text


def clean_latex_source(text: str) -> str:
    return strip_latex_false_conditionals(strip_latex_comments(text))


def document_body(tex: str) -> str:
    begin = tex.find(r"\begin{document}")
    if begin >= 0:
        tex = tex[begin + len(r"\begin{document}") :]
    end = tex.find(r"\end{document}")
    if end >= 0:
        tex = tex[:end]

    # Drop common front matter before the first section.
    first_section = re.search(r"\\section\*?\{", tex)
    if first_section:
        tex = tex[first_section.start() :]

    cut_markers = [
        r"\appendix",
        r"\bibliography",
        r"\begin{thebibliography}",
    ]
    cut_positions = [tex.find(marker) for marker in cut_markers if tex.find(marker) >= 0]
    if cut_positions:
        tex = tex[: min(cut_positions)]
    return tex


def normalize_block(text: str) -> str:
    lines = [line.rstrip() for line in text.strip().splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines).strip()


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z-]{2,}", text)


def technical_score(text: str) -> int:
    lowered = text.lower()
    score = 0
    for marker in TECH_MARKERS:
        if marker.lower() in lowered:
            score += 2
    score += min(text.count("$"), 8) // 2
    score += min(len(re.findall(r"\\[A-Za-z]+", text)), 20) // 5
    return score


def environment_stack(text: str) -> list[str] | None:
    stack = []
    for match in re.finditer(r"\\(?:begin|end)\{([^}]+)\}", text):
        token = match.group(0)
        env = match.group(1)
        if token.startswith(r"\begin"):
            stack.append(env)
        elif stack and stack[-1] == env:
            stack.pop()
        else:
            return None
    return stack


def environment_balance(text: str) -> bool:
    starts = ENV_START_RE.findall(text)
    ends = ENV_END_RE.findall(text)
    stack = environment_stack(text)
    if stack is None:
        return False
    return not stack and len(starts) == len(ends)


def split_environment_stack(text: str, index: int) -> list[str]:
    stack = environment_stack(text[:index])
    return [] if stack is None else stack


def split_sections(body: str) -> list[tuple[str, int, int]]:
    matches = list(SECTION_RE.finditer(body))
    if not matches:
        return [("unknown", 0, len(body))]
    sections = []
    for index, match in enumerate(matches):
        title = " ".join(re.sub(r"\\[A-Za-z]+\*?", "", match.group("title")).split())
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections.append((title or "untitled", start, end))
    return sections


def extract_blocks(paper_id: str, tex: str) -> list[Block]:
    body = document_body(clean_latex_source(tex))
    blocks: list[Block] = []
    for section, section_start, section_end in split_sections(body):
        if EXCLUDE_SECTION_RE.search(section):
            continue
        section_text = body[section_start:section_end]
        local_chunks = list(re.finditer(r"(?:^|\n\s*\n+)(?P<chunk>.*?)(?=\n\s*\n+|$)", section_text, flags=re.DOTALL))
        for match in local_chunks:
            raw = match.group("chunk")
            text = normalize_block(raw)
            if not is_candidate_block(text):
                continue
            start = section_start + match.start("chunk")
            end = section_start + match.end("chunk")
            blocks.append(
                Block(
                    paper_id=paper_id,
                    section=section,
                    block_index=len(blocks),
                    start=start,
                    end=end,
                    text=text,
                    word_count=len(words(text)),
                    tech_score=technical_score(text),
                )
            )
    return blocks


def is_candidate_block(text: str) -> bool:
    if len(text) < 500 or len(text) > 6000:
        return False
    lowered = text.lower()
    if any(marker in lowered for marker in EXCLUDE_BLOCK_MARKERS):
        return False
    if text.lstrip().startswith(r"\end{"):
        return False
    word_count = len(words(text))
    tech = technical_score(text)
    if word_count >= 55:
        return True
    if word_count >= 25 and tech >= 2:
        return True
    return False


def safe_split_index(text: str, fraction: float, split_safety: str = "balanced") -> tuple[int, dict[str, object]] | None:
    target = int(len(text) * fraction)
    radius = min(350, max(120, len(text) // 5))
    left = max(100, target - radius)
    right = min(len(text) - 100, target + radius)
    candidates: list[tuple[int, dict[str, object]]] = []
    for index in range(left, right):
        if not text[index].isspace():
            continue
        if text[index - 1] in "\\{[(" or text[index + 1 : index + 2] in "}]":
            continue
        prefix = text[:index].rstrip()
        suffix = text[index:].lstrip()
        if len(prefix) < 300 or len(suffix) < 200:
            continue
        balanced_prefix = environment_balance(prefix)
        balanced_suffix = environment_balance(suffix)
        would_balance_reject = not balanced_prefix or not balanced_suffix
        if split_safety == "balanced" and would_balance_reject:
            continue
        env_stack = split_environment_stack(text, index)
        candidates.append(
            (
                index,
                {
                    "balanced_prefix": balanced_prefix,
                    "balanced_suffix": balanced_suffix,
                    "would_balance_reject": would_balance_reject,
                    "split_inside_environment": bool(env_stack),
                    "split_environment_stack": env_stack,
                },
            )
        )
    if not candidates:
        return None
    return min(candidates, key=lambda candidate: abs(candidate[0] - target))


def tail_chars(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def build_y_source(suffix: str, following_blocks: list[Block]) -> str:
    parts = [suffix]
    for block in following_blocks:
        parts.append(block.text)
    return "\n\n".join(part for part in parts if part.strip()).strip()


def render_y(y_source: str, target_chars: int, max_chars: int) -> str:
    if len(y_source) <= target_chars:
        return y_source.strip()
    limit = min(target_chars, max_chars)
    y = y_source[:limit].strip()
    cutoff = y.rfind("\n\n")
    if cutoff >= max(900, int(limit * 0.65)):
        return y[:cutoff].rstrip()
    whitespace = y.rfind(" ")
    if whitespace >= max(900, int(limit * 0.8)):
        return y[:whitespace].rstrip()
    return y.rstrip()


def make_candidate_anchors(
    paper_id: str,
    blocks: list[Block],
    min_y_chars: int,
    min_pre_cut_chars: int,
    split_fraction: float,
    split_safety: str,
) -> list[CutAnchor]:
    anchors = []
    split_mode = "tex_suffix_v2" if split_safety == "balanced" else "tex_suffix_v3_relaxed_env"
    for index, block in enumerate(blocks):
        split_result = safe_split_index(block.text, split_fraction, split_safety)
        if split_result is None:
            continue
        split_index, split_metadata = split_result
        prefix = block.text[:split_index].rstrip()
        suffix = block.text[split_index:].lstrip()
        pre_cut_text = "\n\n".join([candidate.text for candidate in blocks[:index]] + [prefix]).strip()
        if len(pre_cut_text) < min_pre_cut_chars:
            continue
        following = blocks[index + 1 :]
        post_cut_text = build_y_source(suffix, following)
        if len(post_cut_text) < min_y_chars:
            continue
        cut_source_char = block.start + split_index
        anchors.append(
            CutAnchor(
                paper_id=paper_id,
                cut_index=-1,
                section=block.section,
                block_index=block.block_index,
                split_mode=split_mode,
                pre_cut_text=pre_cut_text,
                post_cut_text=post_cut_text,
                current_block_prefix=prefix,
                current_block_suffix=suffix,
                block_word_count=block.word_count,
                block_tech_score=block.tech_score,
                balanced_prefix=bool(split_metadata["balanced_prefix"]),
                balanced_suffix=bool(split_metadata["balanced_suffix"]),
                would_balance_reject=bool(split_metadata["would_balance_reject"]),
                split_inside_environment=bool(split_metadata["split_inside_environment"]),
                split_environment_stack=list(split_metadata["split_environment_stack"]),
                cut_source_char=cut_source_char,
                pre_source_available_chars=len(pre_cut_text),
                post_source_available_chars=len(post_cut_text),
                has_equation_available=any(marker in post_cut_text for marker in (r"\begin{equation", r"\begin{align", r"\[", "$$")),
                has_theorem_like_available=any(
                    marker in y
                    for marker in (
                        r"\begin{theorem",
                        r"\begin{lemma",
                        r"\begin{proposition",
                        r"\begin{corollary",
                        r"\begin{definition",
                    )
                    for y in [post_cut_text]
                ),
                has_proof_available=r"\begin{proof" in post_cut_text,
            )
        )
    return anchors


def select_spaced(
    anchors: list[CutAnchor],
    max_cuts: int,
    min_gap_chars: int,
    selection_y_chars: int,
) -> list[CutAnchor]:
    anchors = sorted(anchors, key=lambda anchor: anchor.cut_source_char)
    if len(anchors) <= max_cuts:
        selected = anchors
    else:
        selected = []
        bins = max_cuts
        for bin_index in range(bins):
            start = math.floor(bin_index * len(anchors) / bins)
            end = math.floor((bin_index + 1) * len(anchors) / bins)
            segment = anchors[start:end] or anchors[start : start + 1]
            selected.append(segment[len(segment) // 2])
    selected = sorted(selected, key=lambda anchor: anchor.cut_source_char)

    spaced = []
    last_y_end = -10**9
    for anchor in selected:
        if anchor.cut_source_char < last_y_end + min_gap_chars:
            continue
        spaced.append(anchor)
        last_y_end = anchor.cut_source_char + selection_y_chars
    return [
        CutAnchor(**{**asdict(anchor), "cut_index": index})
        for index, anchor in enumerate(spaced)
    ]


def render_cut(
    anchor: CutAnchor,
    view_name: str,
    judge_x_chars: int,
    predictor_x_chars: int,
    target_y_chars: int,
    max_y_chars: int,
) -> Cut:
    y = render_y(anchor.post_cut_text, target_y_chars, max_y_chars)
    judge_x = tail_chars(anchor.pre_cut_text, judge_x_chars)
    predictor_x = tail_chars(anchor.pre_cut_text, predictor_x_chars)
    context_regime = "same_x" if judge_x_chars == predictor_x_chars else "decoupled_x"
    return Cut(
        paper_id=anchor.paper_id,
        cut_index=anchor.cut_index,
        view_name=view_name,
        context_regime=context_regime,
        section=anchor.section,
        block_index=anchor.block_index,
        split_mode=anchor.split_mode,
        judge_x_text=judge_x,
        predictor_x_text=predictor_x,
        y_text="\n\n" + y,
        x_tail=judge_x[-800:],
        current_block_prefix=anchor.current_block_prefix,
        current_block_suffix=anchor.current_block_suffix,
        judge_x_chars=len(judge_x),
        predictor_x_chars=len(predictor_x),
        y_chars=len(y),
        y_words=len(words(y)),
        block_word_count=anchor.block_word_count,
        block_tech_score=anchor.block_tech_score,
        balanced_prefix=anchor.balanced_prefix,
        balanced_suffix=anchor.balanced_suffix,
        would_balance_reject=anchor.would_balance_reject,
        split_inside_environment=anchor.split_inside_environment,
        split_environment_stack=anchor.split_environment_stack,
        cut_source_char=anchor.cut_source_char,
        y_source_available_chars=anchor.post_source_available_chars,
        has_equation=any(marker in y for marker in (r"\begin{equation", r"\begin{align", r"\[", "$$")),
        has_theorem_like=any(
            marker in y
            for marker in (
                r"\begin{theorem",
                r"\begin{lemma",
                r"\begin{proposition",
                r"\begin{corollary",
                r"\begin{definition",
            )
        ),
        has_proof=r"\begin{proof" in y,
    )


def preview_row(cut: Cut) -> dict[str, object]:
    return {
        "paper_id": cut.paper_id,
        "cut_index": cut.cut_index,
        "view_name": cut.view_name,
        "context_regime": cut.context_regime,
        "section": cut.section,
        "block_index": cut.block_index,
        "judge_x_chars": cut.judge_x_chars,
        "predictor_x_chars": cut.predictor_x_chars,
        "y_chars": cut.y_chars,
        "y_words": cut.y_words,
        "block_word_count": cut.block_word_count,
        "block_tech_score": cut.block_tech_score,
        "would_balance_reject": cut.would_balance_reject,
        "split_inside_environment": cut.split_inside_environment,
        "split_environment_stack": cut.split_environment_stack,
        "has_equation": cut.has_equation,
        "has_theorem_like": cut.has_theorem_like,
        "has_proof": cut.has_proof,
        "cut_source_char": cut.cut_source_char,
        "x_tail_preview": cut.x_tail[-220:].replace("\n", " "),
        "y_preview": cut.y_text[:320].replace("\n", " "),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def parse_view_specs(specs: list[str]) -> list[dict[str, int | str]]:
    views = []
    for spec in specs:
        try:
            name, judge, predictor, y_chars = spec.split(":")
        except ValueError as exc:
            raise ValueError(
                "View specs must have form name:judge_x_chars:predictor_x_chars:y_chars"
            ) from exc
        views.append(
            {
                "name": name,
                "judge_x_chars": int(judge),
                "predictor_x_chars": int(predictor),
                "target_y_chars": int(y_chars),
            }
        )
    return views


def write_jsonl(path: Path, rows: list[object]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")


def paper_summary_row(
    paper_id: str,
    blocks: list[Block],
    candidates: list[CutAnchor],
    selected: list[CutAnchor],
    default_view_cuts: list[Cut],
) -> dict[str, object]:
    return {
        "paper_id": paper_id,
        "status": "ok",
        "blocks": len(blocks),
        "eligible_anchors": len(candidates),
        "selected_anchors": len(selected),
        "balance_reject_eligible": sum(1 for anchor in candidates if anchor.would_balance_reject),
        "balance_reject_selected": sum(1 for anchor in selected if anchor.would_balance_reject),
        "inside_environment_eligible": sum(1 for anchor in candidates if anchor.split_inside_environment),
        "inside_environment_selected": sum(1 for anchor in selected if anchor.split_inside_environment),
        "default_view_avg_y_chars": round(
            sum(cut.y_chars for cut in default_view_cuts) / max(len(default_view_cuts), 1),
            1,
        ),
        "equation_y_selected": sum(1 for cut in default_view_cuts if cut.has_equation),
        "theorem_like_y_selected": sum(1 for cut in default_view_cuts if cut.has_theorem_like),
        "proof_y_selected": sum(1 for cut in default_view_cuts if cut.has_proof),
    }


def overlap_audit_rows(rendered_by_view: dict[str, list[Cut]]) -> list[dict[str, object]]:
    rows = []
    for view_name, cuts in rendered_by_view.items():
        by_paper: dict[str, list[Cut]] = {}
        for cut in cuts:
            by_paper.setdefault(cut.paper_id, []).append(cut)
        for paper_id, paper_cuts in sorted(by_paper.items()):
            paper_cuts = sorted(paper_cuts, key=lambda cut: cut.cut_source_char)
            overlaps = 0
            min_gap = None
            for left, right in zip(paper_cuts, paper_cuts[1:]):
                gap = right.cut_source_char - (left.cut_source_char + left.y_chars)
                min_gap = gap if min_gap is None else min(min_gap, gap)
                if gap < 0:
                    overlaps += 1
            rows.append(
                {
                    "view_name": view_name,
                    "paper_id": paper_id,
                    "cuts": len(paper_cuts),
                    "adjacent_y_overlaps": overlaps,
                    "min_gap_after_rendered_y_chars": "" if min_gap is None else min_gap,
                }
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", nargs="+", default=DEFAULT_IDS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--cuts-per-paper", type=int, default=10)
    parser.add_argument("--views", nargs="+", default=DEFAULT_VIEWS)
    parser.add_argument("--max-y-chars", type=int, default=2600)
    parser.add_argument("--min-y-chars", type=int, default=1200)
    parser.add_argument(
        "--min-pre-cut-chars",
        type=int,
        default=0,
        help="Minimum available retained pre-cut text required before an anchor can be selected.",
    )
    parser.add_argument("--split-fraction", type=float, default=0.58)
    parser.add_argument(
        "--split-safety",
        choices=("balanced", "relaxed_env"),
        default="balanced",
        help="balanced preserves old TeX environment balance rules; relaxed_env allows cuts inside environments and records old-rule rejection metadata.",
    )
    parser.add_argument("--min-gap-chars", type=int, default=1800)
    parser.add_argument(
        "--selection-y-chars",
        type=int,
        help="Y span length used when enforcing min-gap between selected anchors. Defaults to max view Y length.",
    )
    args = parser.parse_args()

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    views = parse_view_specs(args.views)
    selection_y_chars = args.selection_y_chars or max(int(view["target_y_chars"]) for view in views)

    all_anchors: list[CutAnchor] = []
    rendered_by_view: dict[str, list[Cut]] = {str(view["name"]): [] for view in views}
    paper_rows = []
    for paper_id in args.ids:
        path = TRAINING / f"arxiv-{paper_id.replace('.', '-')}.tex"
        if not path.exists():
            paper_rows.append({"paper_id": paper_id, "status": "missing", "blocks": 0, "eligible_anchors": 0, "selected_anchors": 0})
            continue
        tex = path.read_text(encoding="utf-8", errors="ignore")
        blocks = extract_blocks(paper_id, tex)
        candidates = make_candidate_anchors(
            paper_id,
            blocks,
            args.min_y_chars,
            args.min_pre_cut_chars,
            args.split_fraction,
            args.split_safety,
        )
        selected = select_spaced(candidates, args.cuts_per_paper, args.min_gap_chars, selection_y_chars)
        all_anchors.extend(selected)
        default_view_cuts: list[Cut] = []
        for view in views:
            view_name = str(view["name"])
            rendered = [
                render_cut(
                    anchor,
                    view_name=view_name,
                    judge_x_chars=int(view["judge_x_chars"]),
                    predictor_x_chars=int(view["predictor_x_chars"]),
                    target_y_chars=int(view["target_y_chars"]),
                    max_y_chars=args.max_y_chars,
                )
                for anchor in selected
            ]
            rendered_by_view[view_name].extend(rendered)
            if view is views[0]:
                default_view_cuts = rendered
        paper_rows.append(paper_summary_row(paper_id, blocks, candidates, selected, default_view_cuts))

    write_jsonl(out / "cut_anchors.jsonl", all_anchors)
    all_rendered = [cut for cuts in rendered_by_view.values() for cut in cuts]
    write_jsonl(out / "cuts_all_views.jsonl", all_rendered)
    write_csv(out / "cuts_preview_all_views.csv", [preview_row(cut) for cut in all_rendered])
    for view in views:
        view_name = str(view["name"])
        view_dir = out / "views" / view_name
        view_dir.mkdir(parents=True, exist_ok=True)
        write_jsonl(view_dir / "cuts.jsonl", rendered_by_view[view_name])
        write_csv(view_dir / "cuts_preview.csv", [preview_row(cut) for cut in rendered_by_view[view_name]])
    write_csv(out / "paper_summary.csv", paper_rows)
    overlap_rows = overlap_audit_rows(rendered_by_view)
    write_csv(out / "overlap_audit.csv", overlap_rows)

    readme = [
        "# Fresh 2026 Cut Manifest",
        "",
        f"Created: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Dry-run cut manifest only. No predictor or judge API calls were made.",
        "",
        "Parameters:",
        "",
        f"- cuts_per_paper: {args.cuts_per_paper}",
        f"- min_y_chars: {args.min_y_chars}",
        f"- min_pre_cut_chars: {args.min_pre_cut_chars}",
        f"- max_y_chars: {args.max_y_chars}",
        f"- split_fraction: {args.split_fraction}",
        f"- split_safety: {args.split_safety}",
        f"- min_gap_chars: {args.min_gap_chars}",
        f"- selection_y_chars: {selection_y_chars}",
        "",
        "Rendered views:",
        "",
    ]
    for view in views:
        readme.append(
            f"- `{view['name']}`: judge_x_chars={view['judge_x_chars']}, "
            f"predictor_x_chars={view['predictor_x_chars']}, target_y_chars={view['target_y_chars']}"
        )
    readme.extend(
        [
            "",
            f"Total selected anchors: {len(all_anchors)}",
            f"Total rendered cut rows across views: {len(all_rendered)}",
            f"Selected anchors old balance rule would reject: {sum(1 for anchor in all_anchors if anchor.would_balance_reject)}",
            f"Selected anchors inside an explicit TeX environment: {sum(1 for anchor in all_anchors if anchor.split_inside_environment)}",
            "",
            "Files:",
            "",
            "- `cut_anchors.jsonl`: frozen cutpoints and full pre/post source text",
            "- `cuts_all_views.jsonl`: all rendered X/Y views",
            "- `cuts_preview_all_views.csv`: compact previews for all rendered views",
            "- `views/<view_name>/cuts.jsonl`: one rendered view from the same anchors",
            "- `views/<view_name>/cuts_preview.csv`: compact previews for one view",
            "- `paper_summary.csv`: per-paper block/eligibility/selection counts",
            "- `overlap_audit.csv`: adjacent rendered-Y overlap counts by view and paper",
        ]
    )
    readme.extend(
        [
            "",
            "Anchor/view design:",
            "",
            "The selected cutpoints are frozen in `cut_anchors.jsonl`. X and Y",
            "lengths are rendered afterward into named views, so future runs can",
            "compare same-X and decoupled-X regimes without changing which paper",
            "locations were selected.",
        ]
    )
    (out / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    print((out / "README.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
