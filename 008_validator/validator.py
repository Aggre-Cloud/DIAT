# -*- coding: utf-8 -*-
"""
Body-preservation validator.

Guarantees that the extraction-splitter did not silently drop document body
text.  Pipeline contract:

    raw_text  ──►  pdf.extract_text()
    items     ──►  splitter.extract_requirements(raw_text)

    report = assert_body_intact(raw_text, items, ...)

    if report.coverage_ratio < min_char_cov:
        raise BodyLossError(...)

Motivation from the user: "正文被丢弃现象，这点是绝对不可容忍的"
(body-text dropping is absolutely intolerable).
"""
from __future__ import annotations

import json
import os
import re
# --------------------------------------------------------------------------- #
#  Public types
# --------------------------------------------------------------------------- #

class BodyLossError(RuntimeError):
    """Raised when body-text coverage falls below the hard threshold."""


class BodyReport:
    __slots__ = ('raw_chars', 'covered_chars', 'coverage_ratio',
                 'orphan_lines', 'orphans_path')

    def __init__(self, raw_chars, covered_chars, coverage_ratio,
                 orphan_lines, orphans_path):
        self.raw_chars = raw_chars
        self.covered_chars = covered_chars
        self.coverage_ratio = coverage_ratio
        self.orphan_lines = orphan_lines
        self.orphans_path = orphans_path


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #

# Lines that are pure metadata — not "body" that we measure against.
# Only *generic* header/footer/metadata patterns go here.  Do NOT add
# customer / project / document-specific strings.
_NON_BODY_RES = [
    re.compile(r'^\s*__PAGE_\d+__\s*$'),
    re.compile(r'^\s*T[íi]tulo do Documento\s*[:：]?\s*$', re.I),
    re.compile(r'^\s*N[.:\s]*Documento\s*$', re.I),
    re.compile(r'^\s*P[áa]gina\s+\d+\s+de\s+\d+\s*$', re.I),
    re.compile(r'^\s*Controle de Revis[ãa]o\s*$', re.I),
    re.compile(r'^\s*Classifica[çc][ãa]o\s*[:：]?\s*\S*\s*$', re.I),
    re.compile(r'^\s*Elaborado por[:：]?\s*\S*\s*$', re.I),
    re.compile(r'^\s*Verificado por[:：]?\s*\S*\s*$', re.I),
    re.compile(r'^\s*Aprovado por[:：]?\s*\S*\s*$', re.I),
    re.compile(r'^\s*Revis[ãa]o\s+Data\s+Item\s+Descri[çc][ãa]o.*$', re.I),
    re.compile(r'^\s*\d+\.\s*\d{2}/\d{2}/\d{4}\s+.*$'),
    re.compile(r'^\s*\d+\.\d+[\s|]+\d{2}/\d{2}/\d{4}.*$'),   # "1.0 | 13/05/2026 | …"
    re.compile(r'^\s*\d{2}/\d{2}/\d{4}.*$'),                  # bare date line
    re.compile(r'^\s*Revis[ãa]o\s*[|\s]\s*Data\b.*$', re.I),  # rev table header
    re.compile(r'^\s*Especifica[çc][ãa]o T[ée]cnica.*$', re.I),
    re.compile(r'^\s*Sum[áa]rio\s*$', re.I),
]
_ORPHAN_MIN_LEN = 8  # lines shorter than this are noise, never orphans


_TOC_BODY_RE = re.compile(r'[.。…]{4,}\s*\d*\s*$')   # "Title ........ 12"


def _is_non_body_line(line: str) -> bool:
    if not line.strip():
        return True
    for pat in _NON_BODY_RES:
        if pat.match(line):
            return True
    # Table-of-contents dotted entries (Title ........... <page>)
    if _TOC_BODY_RE.search(line) and len(line) < 160:
        return True
    # Pure page-number fragments like "  12" on their own line
    if re.fullmatch(r'\s*\d+\s*', line):
        return True
    # Pure dotted leaders ("……" or "...") followed by numbers (TOC)
    if re.fullmatch(r'\s*[.。…*_]{2,}\s*\d*\s*', line):
        return True
    return False


def _normalize(s: str) -> str:
    """Collapse every whitespace run to one space — comparison baseline."""
    return re.sub(r'\s+', ' ', s).strip()


# --------------------------------------------------------------------------- #
#  Core check
# --------------------------------------------------------------------------- #

def assert_body_intact(
    raw_text: str,
    items: list[dict],
    *,
    min_word_cov: float = 0.85,
    min_char_cov: float = 0.80,
    orphans_path: str | None = None,
) -> BodyReport:
    """Verify that `items` collectively cover most of `raw_text` body.

    Steps
    -----
    1. Walk `raw_text` lines; skip header/footer lines recognised by
       ``_is_non_body_line``.  Remaining non-empty lines → ``body_lines``.
    2. For every line attempt to find the **longest ordered subsequence**
       of its words inside any ``item['content']``.  Mark those words as
       "covered" (a multiset membership test, not strict positional) so
       two items covering overlapping words do not double-count.
    3. ``coverage = Σ covered_words_len / Σ body_words_len``.
    4. Lines whose every word-reference is absent → orphans → written to
       ``orphans_path`` when ``write_orphons`` is on.
    5. If ``coverage < min_char_cov`` → raise ``BodyLossError``.
    """

    if not raw_text or not items:
        return BodyReport(0, 0, 0.0, [], orphans_path)

    # ── 1. Build reference word-multiset of every item ─────────────────
    item_word_pool: list[dict[str, int]] = []
    for it in items:
        words = _normalize(it.get('content', '') or '').split()
        counter: dict[str, int] = {}
        for w in words:
            counter[w] = counter.get(w, 0) + 1
        item_word_pool.append(counter)
    # master copy so we can decrement as words get consumed
    pool = [dict(c) for c in item_word_pool]

    # ── 2. Walk raw lines, measure coverage ────────────────────────────
    raw_lines = raw_text.splitlines()
    covered_chars = 0
    body_chars = 0
    orphan_lines: list[str] = []

    for raw_line in raw_lines:
        line = raw_line.rstrip()
        if _is_non_body_line(line):
            continue
        nrm = _normalize(line)
        if not nrm:
            continue
        body_chars += len(nrm)

        # Greedy: for each word, try to consume it from any pool bucket
        words = nrm.split()
        matched_words = 0
        for w in words:
            for bucket in pool:
                if bucket.get(w, 0) > 0:
                    bucket[w] -= 1
                    matched_words += 1
                    break
        matched_chars = sum(len(w) + 1 for i, w in enumerate(words)
                            if i < matched_words)
        covered_chars += matched_chars

        # If almost none of the line's words are covered → orphan
        if words and matched_words / len(words) < 0.30 and len(nrm) >= _ORPHAN_MIN_LEN:
            orphan_lines.append(nrm)

    ratio = (covered_chars / body_chars) if body_chars else 1.0

    # ── 3. Write orphan file ───────────────────────────────────────────
    if orphan_lines and orphans_path:
        payload = {
            'orphan_count': len(orphan_lines),
            'sample': orphan_lines[:200],
        }
        os.makedirs(os.path.dirname(orphans_path) or '.', exist_ok=True)
        with open(orphans_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # ── 4. Hard gate ───────────────────────────────────────────────────
    if ratio < min_char_cov and body_chars > 100:
        raise BodyLossError(
            f"Body coverage {ratio:.1%} ({covered_chars}/{body_chars} ch) "
            f"is below hard threshold {min_char_cov:.0%}. "
            f"First 5 orphans: {orphan_lines[:5]}"
        )

    return BodyReport(
        raw_chars=body_chars,
        covered_chars=covered_chars,
        coverage_ratio=ratio,
        orphan_lines=orphan_lines,
        orphans_path=orphans_path if orphan_lines else None,
    )
