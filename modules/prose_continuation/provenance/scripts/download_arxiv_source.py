"""Download and inspect arXiv TeX source bundles.

arXiv source downloads are not always zip files. Depending on the paper, the
`/e-print/<id>` endpoint can return a tar archive, a gzipped tar archive, a
gzipped single TeX file, or occasionally plain TeX. This script handles those
cases, extracts the source tree, guesses the main TeX file, and optionally
copies that main file into the project's `training documents` folder.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import re
import shutil
import tarfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_ROOT = PROJECT_ROOT / "training documents" / "arxiv sources"
DEFAULT_PROMOTE_ROOT = PROJECT_ROOT / "training documents"


@dataclass
class TexCandidate:
    path: str
    chars: int
    score: float
    has_documentclass: bool
    has_begin_document: bool
    input_like_count: int
    body_chars: int
    own_body_chars: int
    resolved_input_like_count: int
    resolved_input_like_chars: int
    unresolved_input_like_count: int
    container_like: bool
    container_reason: str


INPUT_LIKE_PATTERN = re.compile(r"\\(?:input|include|subfile)\s*\{([^}]+)\}")


def normalize_arxiv_id(raw: str) -> str:
    value = raw.strip()
    value = value.removeprefix("arXiv:")
    value = value.removeprefix("arxiv:")
    value = value.split("v")[0] if re.fullmatch(r"\d{4}\.\d{4,5}v\d+", value) else value
    if not re.fullmatch(r"(\d{4}\.\d{4,5}|[a-z-]+/\d{7})", value):
        raise ValueError(f"Unrecognized arXiv id format: {raw!r}")
    return value


def safe_name(arxiv_id: str) -> str:
    return arxiv_id.replace("/", "_").replace(".", "-")


def download_bytes(arxiv_id: str, timeout: int = 90) -> bytes:
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "RLVR-text-prediction-source-fetch/0.1 "
            "(local research utility; contact: local-user)"
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def ensure_inside(parent: Path, child: Path) -> None:
    parent_abs = os.path.abspath(os.fspath(parent))
    child_abs = os.path.abspath(os.fspath(child))
    if os.path.commonpath([parent_abs, child_abs]) != parent_abs:
        raise RuntimeError(f"Unsafe archive path escapes extraction root: {child}")


def extract_tar_bytes(data: bytes, extract_root: Path) -> bool:
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
            members = archive.getmembers()
            for member in members:
                target = extract_root / member.name
                ensure_inside(extract_root, target)
            archive.extractall(extract_root)
        return True
    except tarfile.TarError:
        return False


def extract_zip_file(raw_path: Path, extract_root: Path) -> bool:
    if not zipfile.is_zipfile(raw_path):
        return False
    with zipfile.ZipFile(raw_path) as archive:
        for member in archive.infolist():
            target = extract_root / member.filename
            ensure_inside(extract_root, target)
        archive.extractall(extract_root)
    return True


def decode_likely_text(data: bytes) -> str | None:
    for encoding in ("utf-8", "latin-1"):
        try:
            text = data.decode(encoding)
        except UnicodeDecodeError:
            continue
        printable = sum(ch.isprintable() or ch in "\r\n\t" for ch in text)
        if text and printable / max(len(text), 1) > 0.92:
            return text
    return None


def extract_source(raw_path: Path, extract_root: Path) -> str:
    data = raw_path.read_bytes()

    if extract_zip_file(raw_path, extract_root):
        return "zip"

    if extract_tar_bytes(data, extract_root):
        return "tar"

    if data.startswith(b"\x1f\x8b"):
        decompressed = gzip.decompress(data)
        if extract_tar_bytes(decompressed, extract_root):
            return "gzip-tar"
        text = decode_likely_text(decompressed)
        if text is not None:
            suffix = ".tex" if "\\documentclass" in text or "\\begin{document}" in text else ".txt"
            (extract_root / f"source{suffix}").write_text(text, encoding="utf-8")
            return "gzip-single-text"

    text = decode_likely_text(data)
    if text is not None:
        suffix = ".tex" if "\\documentclass" in text or "\\begin{document}" in text else ".txt"
        (extract_root / f"source{suffix}").write_text(text, encoding="utf-8")
        return "single-text"

    (extract_root / "source.bin").write_bytes(data)
    return "unknown-binary"


def detect_source_kind(raw_path: Path) -> str:
    data = raw_path.read_bytes()

    if zipfile.is_zipfile(raw_path):
        return "zip"

    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*"):
            return "tar"
    except tarfile.TarError:
        pass

    if data.startswith(b"\x1f\x8b"):
        try:
            decompressed = gzip.decompress(data)
        except OSError:
            return "gzip-unknown"
        try:
            with tarfile.open(fileobj=io.BytesIO(decompressed), mode="r:*"):
                return "gzip-tar"
        except tarfile.TarError:
            pass
        if decode_likely_text(decompressed) is not None:
            return "gzip-single-text"
        return "gzip-unknown"

    if decode_likely_text(data) is not None:
        return "single-text"
    return "unknown-binary"


def strip_tex_comments(text: str) -> str:
    stripped_lines = []
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
        stripped_lines.append(line[:cut])
    return "\n".join(stripped_lines)


def document_body(text: str) -> str:
    begin = text.find(r"\begin{document}")
    if begin >= 0:
        text = text[begin + len(r"\begin{document}") :]
    end = text.find(r"\end{document}")
    if end >= 0:
        text = text[:end]
    return text


def non_ws_chars(text: str) -> int:
    return sum(1 for char in text if not char.isspace())


def resolve_tex_reference(root: Path, current_dir: Path, target: str) -> Path | None:
    target = target.strip()
    if not target:
        return None

    raw = Path(target)
    candidate_bases = [current_dir / raw, root / raw]
    candidates = []
    for base in candidate_bases:
        candidates.append(base)
        if base.suffix == "":
            candidates.append(base.with_suffix(".tex"))
            candidates.append(base.with_suffix(".ltx"))

    for candidate in candidates:
        try:
            ensure_inside(root, candidate)
        except RuntimeError:
            continue
        if candidate.is_file():
            return candidate
    return None


def classify_container_like(
    input_like_count: int,
    body_chars: int,
    own_body_chars: int,
    resolved_input_like_count: int,
    resolved_input_like_chars: int,
) -> tuple[bool, str]:
    if input_like_count == 0:
        return False, "no input/include/subfile commands"

    if own_body_chars < 4000 and resolved_input_like_count >= 1:
        return True, "very little direct body text and at least one resolved included TeX file"

    if resolved_input_like_chars > 0:
        direct_share = own_body_chars / max(own_body_chars + resolved_input_like_chars, 1)
        if resolved_input_like_count >= 3 and direct_share < 0.35:
            return True, "included TeX files contain most of the apparent paper text"

    if input_like_count >= 8 and own_body_chars < 30000:
        return True, "many include-like commands and modest direct body text"

    if body_chars > 0:
        direct_body_share = own_body_chars / max(body_chars, 1)
        if input_like_count >= 5 and direct_body_share < 0.45:
            return True, "body is dominated by include-like commands"

    return False, "direct body text appears substantial"


def score_tex_file(path: Path, root: Path) -> TexCandidate:
    text = path.read_text(encoding="utf-8", errors="ignore")
    uncommented = strip_tex_comments(text)
    body = document_body(uncommented)
    lower_name = path.name.lower()
    rel = path.relative_to(root).as_posix()

    has_documentclass = "\\documentclass" in text
    has_begin_document = "\\begin{document}" in text
    input_targets = INPUT_LIKE_PATTERN.findall(uncommented)
    input_like_count = len(input_targets)

    resolved_inputs = []
    unresolved_inputs = []
    for target in input_targets:
        resolved = resolve_tex_reference(root, path.parent, target)
        if resolved is None:
            unresolved_inputs.append(target)
        else:
            resolved_inputs.append(resolved)

    resolved_input_like_chars = 0
    for resolved in sorted(set(resolved_inputs)):
        try:
            resolved_input_like_chars += len(resolved.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass

    own_body = INPUT_LIKE_PATTERN.sub("", body)
    body_chars = non_ws_chars(body)
    own_body_chars = non_ws_chars(own_body)
    container_like, container_reason = classify_container_like(
        input_like_count,
        body_chars,
        own_body_chars,
        len(resolved_inputs),
        resolved_input_like_chars,
    )

    score = len(text) / 100.0
    if has_documentclass:
        score += 5000
    if has_begin_document:
        score += 5000
    if lower_name in {"main.tex", "paper.tex", "ms.tex", "article.tex", "manuscript.tex"}:
        score += 1200
    if any(token in lower_name for token in ("main", "paper", "article", "manuscript")):
        score += 400
    if any(token in lower_name for token in ("supp", "appendix", "response", "cover", "referee")):
        score -= 800
    if input_like_count:
        score += min(input_like_count, 20) * 30

    return TexCandidate(
        path=rel,
        chars=len(text),
        score=score,
        has_documentclass=has_documentclass,
        has_begin_document=has_begin_document,
        input_like_count=input_like_count,
        body_chars=body_chars,
        own_body_chars=own_body_chars,
        resolved_input_like_count=len(resolved_inputs),
        resolved_input_like_chars=resolved_input_like_chars,
        unresolved_input_like_count=len(unresolved_inputs),
        container_like=container_like,
        container_reason=container_reason,
    )


def find_tex_candidates(extract_root: Path) -> list[TexCandidate]:
    candidates = []
    for path in extract_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".tex", ".ltx"}:
            candidates.append(score_tex_file(path, extract_root))
    return sorted(candidates, key=lambda item: item.score, reverse=True)


def write_manifest(
    paper_root: Path,
    arxiv_id: str,
    archive_kind: str,
    candidates: list[TexCandidate],
    promoted_to: Path | None,
) -> None:
    manifest = {
        "arxiv_id": arxiv_id,
        "source_url": f"https://arxiv.org/e-print/{arxiv_id}",
        "archive_kind": archive_kind,
        "main_candidate": asdict(candidates[0]) if candidates else None,
        "candidate_count": len(candidates),
        "promoted_to": str(promoted_to) if promoted_to else None,
        "top_candidates": [asdict(candidate) for candidate in candidates[:10]],
    }
    (paper_root / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    lines = [
        f"# arXiv {arxiv_id} Source Ingest",
        "",
        f"- Source URL: https://arxiv.org/e-print/{arxiv_id}",
        f"- Archive kind: {archive_kind}",
        f"- TeX candidates: {len(candidates)}",
    ]
    if candidates:
        main = candidates[0]
        lines.extend(
            [
                f"- Guessed main file: `{main.path}`",
                f"- Main chars: {main.chars}",
                f"- Has documentclass: {main.has_documentclass}",
                f"- Has begin document: {main.has_begin_document}",
                f"- Input/include count: {main.input_like_count}",
                f"- Resolved input/include count: {main.resolved_input_like_count}",
                f"- Direct body chars after removing include commands: {main.own_body_chars}",
                f"- Included TeX chars: {main.resolved_input_like_chars}",
                f"- Container-like main: {main.container_like} ({main.container_reason})",
            ]
        )
    if promoted_to:
        lines.append(f"- Copied main file to: `{promoted_to}`")
    lines.extend(["", "## Top Candidates", ""])
    for candidate in candidates[:10]:
        lines.append(
            f"- `{candidate.path}`: score={candidate.score:.1f}, chars={candidate.chars}, "
            f"docclass={candidate.has_documentclass}, begin={candidate.has_begin_document}, "
            f"inputs={candidate.input_like_count}, own_body={candidate.own_body_chars}, "
            f"included_chars={candidate.resolved_input_like_chars}, "
            f"container_like={candidate.container_like}"
        )
    (paper_root / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def ingest_one(
    arxiv_id: str,
    out_root: Path,
    promote_main: bool,
    promote_root: Path,
    overwrite: bool,
) -> dict[str, object]:
    paper_root = out_root / f"arxiv-{safe_name(arxiv_id)}"
    raw_path = paper_root / "source_download"
    extract_root = paper_root / "source_tree"

    if paper_root.exists() and overwrite:
        shutil.rmtree(paper_root)
    paper_root.mkdir(parents=True, exist_ok=True)
    if extract_root.exists() and overwrite:
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True, exist_ok=True)

    if not raw_path.exists() or overwrite:
        data = download_bytes(arxiv_id)
        raw_path.write_bytes(data)

    if any(extract_root.iterdir()) and not overwrite:
        archive_kind = detect_source_kind(raw_path)
    else:
        archive_kind = extract_source(raw_path, extract_root)
    candidates = find_tex_candidates(extract_root)

    promoted_to = None
    if promote_main and candidates:
        main_src = extract_root / candidates[0].path
        promoted_to = promote_root / f"arxiv-{safe_name(arxiv_id)}.tex"
        if promoted_to.exists() and not overwrite:
            pass
        else:
            shutil.copyfile(main_src, promoted_to)
    elif candidates:
        existing_promoted = promote_root / f"arxiv-{safe_name(arxiv_id)}.tex"
        if existing_promoted.exists():
            promoted_to = existing_promoted

    write_manifest(paper_root, arxiv_id, archive_kind, candidates, promoted_to)

    main = candidates[0] if candidates else None
    if main is None:
        print(f"{arxiv_id}: downloaded/extracted as {archive_kind}; no .tex candidates found")
    else:
        promoted_note = f"; promoted to {promoted_to.name}" if promoted_to else ""
        print(
            f"{arxiv_id}: {archive_kind}; main={main.path}; chars={main.chars}; "
            f"docclass={main.has_documentclass}; begin={main.has_begin_document}; "
            f"container_like={main.container_like}; own_body_chars={main.own_body_chars}; "
            f"included_chars={main.resolved_input_like_chars}{promoted_note}"
        )
    return {
        "arxiv_id": arxiv_id,
        "status": "ok",
        "archive_kind": archive_kind,
        "main_path": main.path if main else "",
        "main_chars": main.chars if main else "",
        "has_documentclass": main.has_documentclass if main else "",
        "has_begin_document": main.has_begin_document if main else "",
        "input_like_count": main.input_like_count if main else "",
        "resolved_input_like_count": main.resolved_input_like_count if main else "",
        "unresolved_input_like_count": main.unresolved_input_like_count if main else "",
        "own_body_chars": main.own_body_chars if main else "",
        "included_tex_chars": main.resolved_input_like_chars if main else "",
        "container_like": main.container_like if main else "",
        "container_reason": main.container_reason if main else "",
        "promoted_to": str(promoted_to) if promoted_to else "",
        "error": "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arxiv_ids", nargs="+", help="arXiv ids such as 2604.17369")
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--promote-main", action="store_true")
    parser.add_argument("--promote-root", type=Path, default=DEFAULT_PROMOTE_ROOT)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--summary-csv", type=Path)
    args = parser.parse_args()

    out_root = args.out_root.resolve()
    promote_root = args.promote_root.resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    promote_root.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    exit_code = 0
    for raw_id in args.arxiv_ids:
        arxiv_id = normalize_arxiv_id(raw_id)
        try:
            row = ingest_one(arxiv_id, out_root, args.promote_main, promote_root, args.overwrite)
            summary_rows.append(row)
        except Exception as exc:
            print(f"{arxiv_id}: download failed: {exc}")
            summary_rows.append(
                {
                    "arxiv_id": arxiv_id,
                    "status": "failed",
                    "archive_kind": "",
                    "main_path": "",
                    "main_chars": "",
                    "has_documentclass": "",
                    "has_begin_document": "",
                    "input_like_count": "",
                    "resolved_input_like_count": "",
                    "unresolved_input_like_count": "",
                    "own_body_chars": "",
                    "included_tex_chars": "",
                    "container_like": "",
                    "container_reason": "",
                    "promoted_to": "",
                    "error": repr(exc),
                }
            )
            exit_code = 2
            if not args.continue_on_error:
                break

    if args.summary_csv and summary_rows:
        args.summary_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.summary_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0]))
            writer.writeheader()
            writer.writerows(summary_rows)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
