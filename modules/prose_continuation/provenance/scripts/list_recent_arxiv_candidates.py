"""List recent arXiv candidate papers for the text-prediction benchmark."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
import textwrap
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass


API_URL = "https://export.arxiv.org/api/query"
LIST_URL = "https://arxiv.org/list/{category}/pastweek?skip=0&show={show}"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class Paper:
    arxiv_id: str
    title: str
    published: str
    updated: str
    primary_category: str
    categories: list[str]
    comments: str
    pages: int | None
    score: int
    summary: str


def normalize_text(value: str) -> str:
    return " ".join(html.unescape(value or "").split())


def parse_pages(comments: str) -> int | None:
    text = comments or ""
    patterns = [
        r"(\d+)\s*\+\s*pages",
        r"(\d+)\s*(?:pages|pp\.?|p\.)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def arxiv_id_from_entry_id(entry_id: str) -> str:
    return entry_id.rstrip("/").rsplit("/", 1)[-1].split("v")[0]


def vibe_score(title: str, summary: str, categories: list[str], comments: str) -> int:
    haystack = f"{title} {summary} {comments}".lower()
    score = 0

    positive_terms = [
        "theorem",
        "proof",
        "bound",
        "optimal",
        "algorithm",
        "complexity",
        "tomography",
        "error correction",
        "quantum code",
        "stabilizer",
        "pauli",
        "channel",
        "entropy",
        "entanglement",
        "holograph",
        "conformal",
        "cft",
        "bcft",
        "yang-mills",
        "gauge",
        "gravity",
        "string",
        "syk",
        "hydrodynamics",
        "operator growth",
        "krylov",
        "many-body",
        "bosonic",
        "fermionic",
        "resurgence",
        "wall-crossing",
        "duality",
        "amplitudes",
        "anomaly",
        "defect",
        "lattice",
    ]
    for term in positive_terms:
        if term in haystack:
            score += 2

    especially_close_categories = {
        "quant-ph",
        "hep-th",
        "math-ph",
        "cond-mat.stat-mech",
        "cond-mat.str-el",
        "gr-qc",
    }
    score += sum(1 for category in categories if category in especially_close_categories)

    negative_terms = [
        "perspective",
        "review",
        "tutorial",
        "survey",
        "comment on",
        "reply to",
        "conference",
        "proceedings",
        "popular",
    ]
    for term in negative_terms:
        if term in haystack:
            score -= 4

    return score


def query_arxiv(categories: list[str], start: dt.date, end: dt.date, max_results: int) -> list[Paper]:
    category_query = "+OR+".join(f"cat:{urllib.parse.quote(category)}" for category in categories)
    start_stamp = start.strftime("%Y%m%d") + "0000"
    end_stamp = end.strftime("%Y%m%d") + "2359"
    search_query = f"({category_query})+AND+submittedDate:[{start_stamp}+TO+{end_stamp}]"

    papers: dict[str, Paper] = {}
    start_index = 0
    batch_size = min(100, max_results)
    while start_index < max_results:
        params = {
            "search_query": search_query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "start": str(start_index),
            "max_results": str(batch_size),
        }
        url = API_URL + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "RLVR-text-prediction-candidate-search/0.1 "
                "(local research utility)"
            },
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()

        root = ET.fromstring(data)
        entries = root.findall(f"{ATOM}entry")
        if not entries:
            break

        for entry in entries:
            entry_id = normalize_text(entry.findtext(f"{ATOM}id"))
            arxiv_id = arxiv_id_from_entry_id(entry_id)
            title = normalize_text(entry.findtext(f"{ATOM}title"))
            summary = normalize_text(entry.findtext(f"{ATOM}summary"))
            published = normalize_text(entry.findtext(f"{ATOM}published"))
            updated = normalize_text(entry.findtext(f"{ATOM}updated"))
            primary_el = entry.find(f"{ARXIV}primary_category")
            primary_category = primary_el.attrib.get("term", "") if primary_el is not None else ""
            category_values = [
                category.attrib.get("term", "")
                for category in entry.findall(f"{ATOM}category")
                if category.attrib.get("term")
            ]
            comment = normalize_text(entry.findtext(f"{ARXIV}comment"))
            pages = parse_pages(comment)
            score = vibe_score(title, summary, category_values, comment)
            papers[arxiv_id] = Paper(
                arxiv_id=arxiv_id,
                title=title,
                published=published,
                updated=updated,
                primary_category=primary_category,
                categories=category_values,
                comments=comment,
                pages=pages,
                score=score,
                summary=summary,
            )

        start_index += len(entries)
        if len(entries) < batch_size:
            break
        time.sleep(3.1)

    return list(papers.values())


def field_from_block(block: str, field_class: str) -> str:
    match = re.search(
        rf"<div class=['\"]{re.escape(field_class)}[^'\"]*['\"]>(.*?)</div>",
        block,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    value = re.sub(r"<span class=['\"]descriptor['\"]>.*?</span>", "", match.group(1), flags=re.DOTALL)
    value = re.sub(r"<[^>]+>", " ", value)
    return normalize_text(value)


def categories_from_subjects(subjects: str) -> list[str]:
    found = re.findall(r"\(([a-z-]+(?:\.[A-Z]{2})?)\)", subjects)
    seen = []
    for category in found:
        if category not in seen:
            seen.append(category)
    return seen


def query_arxiv_list_pages(categories: list[str], show: int) -> list[Paper]:
    papers: dict[str, Paper] = {}
    for category in categories:
        url = LIST_URL.format(category=urllib.parse.quote(category), show=show)
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "RLVR-text-prediction-candidate-search/0.1 "
                "(local research utility)"
            },
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            html_text = response.read().decode("utf-8", errors="replace")

        # Pair each <dt> arXiv id block with the following <dd> metadata block.
        pattern = re.compile(
            r"<dt>.*?<a\s+href\s*=\s*['\"]\s*/abs/(?P<id>[^'\"#\s]+)\s*['\"][^>]*>.*?</dt>\s*"
            r"<dd>(?P<meta>.*?)</dd>",
            flags=re.IGNORECASE | re.DOTALL,
        )
        for match in pattern.finditer(html_text):
            arxiv_id = match.group("id").split("v")[0]
            meta = match.group("meta")
            title = field_from_block(meta, "list-title")
            comments = field_from_block(meta, "list-comments")
            subjects = field_from_block(meta, "list-subjects")
            category_values = categories_from_subjects(subjects)
            if not category_values:
                category_values = [category]
            pages = parse_pages(comments)
            score = vibe_score(title, subjects, category_values, comments)
            previous = papers.get(arxiv_id)
            if previous is not None:
                merged_categories = list(dict.fromkeys(previous.categories + category_values))
                previous.categories = merged_categories
                previous.score = max(previous.score, score)
                continue
            papers[arxiv_id] = Paper(
                arxiv_id=arxiv_id,
                title=title,
                published="pastweek-list",
                updated="pastweek-list",
                primary_category=category_values[0] if category_values else category,
                categories=category_values,
                comments=comments,
                pages=pages,
                score=score,
                summary=subjects,
            )
        time.sleep(1.0)
    return list(papers.values())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2026-04-20")
    parser.add_argument("--end", default="2026-04-27")
    parser.add_argument("--min-pages", type=int, default=25)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--max-results", type=int, default=500)
    parser.add_argument("--source", choices=["api", "list"], default="list")
    parser.add_argument(
        "--categories",
        nargs="+",
        default=["quant-ph", "hep-th", "math-ph"],
    )
    args = parser.parse_args()

    start = dt.date.fromisoformat(args.start)
    end = dt.date.fromisoformat(args.end)
    if args.source == "api":
        papers = query_arxiv(args.categories, start, end, args.max_results)
        source_note = f"{start} to {end}"
    else:
        papers = query_arxiv_list_pages(args.categories, args.max_results)
        source_note = "arXiv pastweek category pages"

    filtered = [
        paper
        for paper in papers
        if paper.pages is not None and paper.pages >= args.min_pages
    ]
    filtered.sort(
        key=lambda paper: (
            paper.score,
            paper.pages or 0,
            paper.published,
        ),
        reverse=True,
    )

    print(
        f"Found {len(papers)} unique arXiv entries in {args.categories} "
        f"from {source_note}; {len(filtered)} have >= {args.min_pages} pages."
    )
    print()

    for index, paper in enumerate(filtered[: args.limit], start=1):
        cats = ", ".join(paper.categories[:5])
        print(f"{index}. {paper.arxiv_id} | {paper.title}")
        print(f"   primary={paper.primary_category}; categories={cats}")
        print(f"   pages={paper.pages}; comments={paper.comments or '[none]'}")
        print(f"   link=https://arxiv.org/abs/{paper.arxiv_id}")
        wrapped = textwrap.fill(paper.summary, width=96, subsequent_indent="   ")
        print(f"   abstract: {wrapped[:500]}{'...' if len(wrapped) > 500 else ''}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
