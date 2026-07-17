# -*- coding: utf-8 -*-
"""
Text splitting module — REWRITTEN
==================================
New components
--------------
1. `ChapterSectionParser` — priority-ordered named regex + stack builder.
   Handles: Art. 1º / CAPÍTULO / Seção / § / I. / 1. / 1.2 / 1.2.1 /
            （1）/ (a) / • / (1) / ①

2. `SentenceSegmenter` — per-source-language sentence boundary detection.
   pt / en / es / fr / de  → pysbd (optional) + regex fallback
   zh / ja / ko              → CJK terminator rule
   others                     → generic regex
   ALL abbreviation tables hardcoded in 006_config/config.py::ABBR.

Top-level API:
  parse_text(raw_text) -> ParseResult(roots, items, meta)
  save_json_output(json_data, output_file) -> str
"""
from __future__ import annotations

import re
import sys
import os
import json
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --------------------------------------------------------------------------- #
#  Config (lazy)
# --------------------------------------------------------------------------- #

def _cfg():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "config",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "006_config", "config.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _abbr(lang: str) -> list[str]:
    try:
        return _cfg().ABBR.get(lang, [])
    except Exception:
        return []


# --------------------------------------------------------------------------- #
#  0. Heading RE macros  (priority ORDERED — first match wins)
# --------------------------------------------------------------------------- #

_RE_ART  = re.compile(r'^\s*Art\.?\s*(\d+)º?\b', re.I)
_RE_CAP  = re.compile(r'^\s*(CAP[ÍI]TULO|T[ÍI]TULO)\s+([IVXLCDM]+|\d+)\b', re.I)
_RE_SEC  = re.compile(r'^\s*(SE[ÇC][AÃO])\s+([IVXLCDM]+|\d+)\b', re.I)
_RE_PARA = re.compile(r'^\s*§\s*(\d+)º?\b')
_RE_ROM  = re.compile(r'^\s*(IX|IV|V?I{0,3})\.\s+')
_RE_D3   = re.compile(r'^\s*(\d+\.\d+\.\d+)\.?\s+(?=[A-ZÀ-Ú])')   # 1.2.3 <title> or 1.2.3. <title>
_RE_D2   = re.compile(r'^\s*(\d+\.\d+)\.?\s+(?=[A-ZÀ-Ú])')        # 1.2 <title> or 1.2. <title>
_RE_D1   = re.compile(r'^\s*(\d+)\s+(?=[A-ZÀ-Ú])')               # 1 <title> (NO dot — excludes "128. Os algarismos")
_RE_DBRA = re.compile(r'^（(\d+)）')
_RE_BRA  = re.compile(r'^\s*(\([a-z]\)|[a-z]\))\s+')
_RE_NUM  = re.compile(r'^\s*\(\d+\)\s+')
_RE_BUL  = re.compile(r'^\s*[•·●]\s*')   # no capture group — handled in matcher

_TAG_DEPTH = {
    'ART': 0, 'CAP': 0, 'SEC': 1, 'PARA': 2, 'ROM': 1,
    'D3': 2, 'D2': 1, 'D1': 0, 'DBRA': 2, 'BRA': 3,
    'NUM': 3, 'BUL': 4,
}
# Reject matches whose "title" exceeds this length — table rows in the PDF
# frequently look like  "06  DIGITOS; CODIGOS MOSTRADOR: 4; ..." after the
# leading number+space pattern fires.
_TITLE_MAX_LEN = {
    'D3': 80,
    'D2': 120,
    'D1': 80,
    'DBRA': 80,
    'NUM': 90,
    'PARA': 80,
}
_H_PATTERNS = [
    (_RE_ART, 'ART'), (_RE_CAP, 'CAP'), (_RE_SEC, 'SEC'),
    (_RE_PARA, 'PARA'), (_RE_ROM, 'ROM'),
    (_RE_D3, 'D3'), (_RE_D2, 'D2'), (_RE_D1, 'D1'),
    (_RE_DBRA, 'DBRA'), (_RE_BRA, 'BRA'), (_RE_NUM, 'NUM'),
    (_RE_BUL, 'BUL'),
]
_CHAPTER_SIGNAL_MAX = 80
_REQ_KEYWORDS = (
    'deve ', 'deverá ', 'devem ', 'deverão ',
    'requisito', 'requisitos', 'exige ', 'exigido', 'exigida',
    'é vedado', 'vedada', 'é obrigatória', 'é obrigatório',
    'obrigatoriamente', 'mandatório', 'compulsório',
)


# --------------------------------------------------------------------------- #
#  1. Heading node
# --------------------------------------------------------------------------- #

class Node:
    __slots__ = ('tag', 'prefix', 'number', 'title', 'depth', 'page',
                 'children', 'body_lines', 'is_chapter_signal', '_parent')

    def __init__(self, tag, prefix, number, title, depth,
                 page=0, is_chapter_signal=False):
        self.tag = tag
        self.prefix = prefix
        self.number = number
        self.title = title
        self.depth = depth
        self.page = page
        self.children = []
        self.body_lines = []
        self.is_chapter_signal = is_chapter_signal
        self._parent = None

    @property
    def label(self):
        p = self.prefix.strip()
        t = self.title.strip()
        return f"{p} {t}".strip() if (p and t) else (p or t)


# --------------------------------------------------------------------------- #
#  2. Helpers
# --------------------------------------------------------------------------- #

_TOC_DOT_RE = re.compile(r'[.。…]{4,}\s*\d*\s*$')   # "Title .........." or "Title ....... 12"


def _is_noise(line: str) -> bool:
    """Page headers / footers / doc codes / TOC lines to skip."""
    s = line.strip()
    if not s:
        return True
    # Table-of-contents dotted entries (Title ........... <page>)
    if _TOC_DOT_RE.search(s) and len(s) < 160:
        return True
    pat = re.compile
    NOISE_PATS = [
        pat(r'^\s*T[íi]tulo do Documento[:：]?\s*$', re.I),
        pat(r'^\s*N[.:\s]*Documento\s*$', re.I),
        pat(r'^\s*P[áa]gina\s+\d+\s+de\s+\d+\s*$', re.I),
        pat(r'^\s*Controle de Revis[ãa]o\s*$', re.I),
        pat(r'^\s*Classifica[çc][ãa]o[:：]?\s*\S*\s*$', re.I),
        pat(r'^\s*Elaborado por[:：]?\s*\S*\s*$', re.I),
        pat(r'^\s*Verificado por[:：]?\s*\S*\s*$', re.I),
        pat(r'^\s*Aprovado por[:：]?\s*\S*\s*$', re.I),
        pat(r'^\s*Revis[ãa]o\s+Data\s+Item\s+Descri[çc][ãa]o.*$', re.I),
        pat(r'^\s*\d+\.\s*\d{2}/\d{2}/\d{4}[\s|].*$'),
        pat(r'^\s*\d+\.\d+[\s|]+\d{2}/\d{2}/\d{4}.*$'),   # revision-row "1.0 13/05/2026 …"
        pat(r'^\s*\d{2}/\d{2}/\d{4}.*$'),                  # bare date
        pat(r'^\s*Revis[ãa]o\s*[|\s]\s*Data\b.*$', re.I),  # rev-table header "Revisão | Data | Item"
        pat(r'^\s*Especifica[çc][ãa]o T[ée]cnica.*$', re.I),
        pat(r'^\s*Sum[áa]rio\s*$', re.I),
    ]
    for p in NOISE_PATS:
        if p.match(s):
            return True
    if re.fullmatch(r'\s*\d+\s*', s):
        return True
    return False


def _in_quote(buf: str) -> bool:
    """True if `buf` has unbalanced CJK/Latin quotation marks."""
    for oc, cc in [('“', '”'), ('「', '」'),
                   ('『', '』'), ('"', '"'), ('、', '。')]:
        if oc == cc:
            if buf.count(oc) % 2 == 1:
                return True
        else:
            if buf.count(oc) != buf.count(cc):
                return True
    return False


# --------------------------------------------------------------------------- #
#  3. ChapterSectionParser
# --------------------------------------------------------------------------- #

class ChapterSectionParser:
    def __init__(self, *, drop_noise: bool = True):
        self.drop_noise = drop_noise

    def parse(self, raw_text: str) -> tuple[list[Node], list[dict]]:
        roots: list[Node] = []
        stack: list[Node] = []
        current_page = 0

        # Pre-pass: identify TOC pages — a TOC entry has a trailing page
        # number after the dotted leader (e.g. "Title ........ 12").
        _toc_line_re = re.compile(
            r'^\s*\d+(?:\.\d+)*\s+.+?[.。…]{4,}\s+\d{1,3}\s*$')
        _page_re = re.compile(r'^\s*__PAGE_(\d+)__\s*$')
        _toc_counts: dict[int, int] = {}
        _pg = 0
        for _ln in raw_text.splitlines():
            _m = _page_re.match(_ln)
            if _m:
                _pg = int(_m.group(1))
                continue
            if _toc_line_re.match(_ln):
                _toc_counts[_pg] = _toc_counts.get(_pg, 0) + 1
        toc_pages = {pg for pg, cnt in _toc_counts.items() if cnt >= 3}

        parent_map: dict[int, Optional[Node]] = {}
        node_seq: list[Node] = []

        for raw_line in raw_text.splitlines():
            line = raw_line.rstrip()

            m = re.match(r'^\s*__PAGE_(\d+)__\s*$', line)
            if m:
                current_page = int(m.group(1))
                continue

            # On TOC pages skip dotted-heading lines.
            if current_page in toc_pages and _TOC_DOT_RE.search(line):
                continue

            if self.drop_noise and _is_noise(line):
                continue

            heading = self._match_heading(line)
            if not heading:
                if stack:
                    stack[-1].body_lines.append(line)
                continue

            tag, number, title = heading
            depth = _TAG_DEPTH.get(tag, 2)
            is_signal = (tag == 'D1'
                         and 0 < len(title.strip()) <= _CHAPTER_SIGNAL_MAX)

            n = Node(tag=tag, prefix=number, number=number,
                     title=title, depth=depth, page=current_page,
                     is_chapter_signal=is_signal)
            node_seq.append(n)

            while stack and stack[-1].depth >= depth:
                stack.pop()
            if stack:
                stack[-1].children.append(n)
                parent_map[id(n)] = stack[-1]
            else:
                roots.append(n)
                parent_map[id(n)] = None
            stack.append(n)

        # attach parents for ancestry lookup
        for n in node_seq:
            n._parent = parent_map.get(id(n))

        # link for flatten's ancestry
        for r in roots:
            self._link(r, None)

        items = self._flatten(roots)
        return roots, items

    def _link(self, n: Node, p: Optional[Node]):
        n._parent = p
        for c in n.children:
            self._link(c, n)

    # -- helpers --------------------------------------------------------- #

    def _match_heading(self, line: str):
        s = line.rstrip()
        for pat, tag in _H_PATTERNS:
            m = pat.match(s)
            if not m:
                continue
            # Not every pattern has capture groups — derive a number.
            if m.lastindex:
                number = m.group(1)
                for g in range(2, m.lastindex + 1):
                    if m.group(g):
                        number = m.group(g)
            else:
                number = m.group(0).strip(' .')
            title = s[m.end():].strip()
            max_len = _TITLE_MAX_LEN.get(tag, 200)
            if len(title) > max_len:
                continue  # title too long — likely a table row, not a heading
            # Table-row guard: real D1/D2/D3 headings never contain these
            # markers, but table rows frequently do.
            if tag in ('D1', 'D2', 'D3'):
                if ';' in title or '(' in title:              # cell sep / unit annotation
                    continue
                if re.search(r'\s{2,}-\s{2,}', title):          # "Label  -  Value" multi-pad
                    continue
                # Trailing " - <word>" (hyphen, not en-dash – which real headings use)
                if re.search(r' - [A-Za-zÀ-Úà-ú]{1,15}\s*$', title):
                    continue
                if re.search(r'\d', title):                     # any digit (titles are words only)
                    continue
            return tag, number, title
        return None

    def _flatten(self, roots: list[Node]) -> list[dict]:
        """One row per node.

        Every heading becomes a row so that its heading words appear in the
        pipeline body pool (validator coverage).  Heading-only nodes synthesize
        content from the numbered heading; body-bearing nodes carry their
        body_lines with the heading prepended.
        """
        out: list[dict] = []

        def _walk(node: Node, chapter: Optional[Node],
                  section: Optional[Node]):
            # Update chapter/section context.  A D1 heading (depth 0) becomes
            # the new chapter; a D2 heading (depth 1) becomes the new section.
            if node.depth == 0:
                ch = node
                sec = None
            elif node.depth == 1:
                ch = chapter
                sec = node
            else:
                ch = chapter
                sec = section

            out.append(self._mk_row(node, ch, sec))

            for c in node.children:
                _walk(c, ch, sec)

        for r in roots:
            _walk(r, None, None)
        return out

    @staticmethod
    def _title_is_demand(title: str) -> bool:
        """True when the heading title carries a complete demand sentence
        (not just a structural label like 'Condições Gerais')."""
        t = title.strip()
        if not t:
            return False
        # A demand title typically:
        #   - contains a verb/requirement keyword, OR
        #   - is a full clause (≥ 30 chars and ends with no trailing dot-leader)
        _DEMAND_KW = (
            'deve ', 'deverá ', 'devem ', 'deverão ',
            'é obrigatório', 'é vedado', 'obrigatoriamente',
            'exige ', 'requisito', 'requisitos',
            'deverá ser', 'deverão ser', 'deverá permitir',
            'deverá permitir', 'deverá possuir', 'deverá fornecer',
            'deverá garantir', 'deverá manter', 'deverá entregar',
            'deverá possuir',
        )
        tl = t.lower()
        if any(k in tl for k in _DEMAND_KW):
            return True
        # Full-clause heading: ≥ 40 chars, contains verb-like punctuation
        if len(t) >= 40 and (' ' in t) and not t.endswith((':', '.', ',')):
            return True
        if len(t) >= 50:
            return True
        return False

    def _mk_row(self, node: Node, ch: Optional[Node],
                 sec: Optional[Node]) -> dict:
        path = self._ancestry(node)
        body: list[str] = []
        # Always start with the numeric + title heading line so that heading
        # tokens show up in the item body pool (validator will no longer see
        # them as "orphan" body lines).
        heading_line = f"{node.number} {node.title}".strip()
        # Guard against trailing-colon labels that were deliberately left
        # heading-only (structural labels like "6.1.3 Características Mecânicas"
        # without body under them).  They are still preserved here.
        body.append(heading_line)
        for bl in node.body_lines:
            if bl.strip() and bl.strip() != heading_line:
                body.append(bl.rstrip())
        content_raw = '\n'.join(body)
        return {
            'tag': node.tag,
            'number': node.number,
            'title': node.title,
            'prefix': node.prefix,
            'page': node.page,
            'depth': node.depth,
            'chapter_number': ch.number if ch else '',
            'chapter_title': ch.title if ch else '',
            'chapter_label': ch.label if ch else '',
            'section_number': sec.number if sec else '',
            'section_title': sec.title if sec else '',
            'section_label': sec.label if sec else '',
            'content_raw': content_raw,
            'hierarchy_path': ' > '.join(path),
        }

    def _ancestry(self, node: Node) -> list[str]:
        out, cur = [], node
        while cur is not None:
            out.append(cur.label)
            cur = getattr(cur, '_parent', None)
        return list(reversed(out))


# --------------------------------------------------------------------------- #
#  4. SentenceSegmenter  (best-practice per language, no mandatory dep)
# --------------------------------------------------------------------------- #

class SentenceSegmenter:
    # Fixed-width lookbehind (1 char) — only split after sentence-ending
    # punctuation.  List-item markers are handled by _split_list_items()
    # which inserts \n before each marker; _split() then splits on \n first.
    HYBRID_FALLBACK = re.compile(r'(?<=[.!?])\s+(?=[A-ZÀ-Ú§\d（\(])')

    def __init__(self, lang: str):
        self.lang = (lang or 'pt').lower().split('-')[0]

    def segment(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        # Pre-process (string→string): insert newlines before list-item
        # markers so the period/newline-based splitter treats each as a
        # separate sentence. Handles (a), ①, III., i., (1), etc.
        text = self._split_list_items(text)
        if not text.strip():
            return []
        if self.lang == 'pt':
            sents = self._try_pysbd('pt', text) or self._split(text, 'pt')
        elif self.lang == 'en':
            sents = self._try_pysbd('en', text) or self._split(text, 'en')
        elif self.lang in ('es', 'fr', 'de', 'it', 'nl', 'ru', 'sk'):
            sents = self._try_pysbd(self.lang, text) or self._split(text, self.lang)
        elif self.lang in ('zh', 'ja', 'ko'):
            sents = self._segment_cjk(text)
        else:
            sents = self._split(text, self.lang)
        return self._post(sents)

    def _try_pysbd(self, lang: str, text: str):
        try:
            from pysbd import TextSegmenter
            seg = TextSegmenter(language=lang, clean=False)
            out = seg.segment(text)
            return out or None
        except ImportError:
            return None

    def _split(self, text: str, lang: str) -> list[str]:
        abbr = _abbr(lang)
        protected = text
        token_map: dict[str, str] = {}
        for i, a in enumerate(abbr):
            ph = f'__ABBR{i:04d}__'
            pat = re.compile(r'(?<![A-Za-z])' + re.escape(a) + r'\.(?=\s)', re.I)
            if pat.search(protected):
                token_map[ph] = f'{a}.'
                protected = pat.sub(ph, protected)
        # First: split on physical newlines (inserted by _split_list_items
        # for list-item markers).  Then apply HYBRID_FALLBACK within each chunk.
        chunks = protected.split('\n')
        sents: list[str] = []
        for chunk in chunks:
            parts = self.HYBRID_FALLBACK.split(chunk)
            sents.extend(p for p in parts if p.strip())
        out = []
        for s in sents:
            for ph, orig in token_map.items():
                s = s.replace(ph, orig)
            s = s.strip()
            if s:
                out.append(s)
        return out

    def _segment_cjk(self, text: str) -> list[str]:
        sents, buf, i = [], [], 0
        while i < len(text):
            ch = text[i]
            buf.append(ch)
            if ch in '。！？':
                sents.append(''.join(buf).strip())
                buf = []
            elif ch in '；;' and not _in_quote(''.join(buf)):
                sents.append(''.join(buf).strip())
                buf = []
            i += 1
        if buf:
            tail = ''.join(buf).strip()
            if tail:
                sents.append(tail)
        merged = []
        for s in sents:
            if merged and len(s) < 10:
                merged[-1] += s
            else:
                merged.append(s)
        return [s for s in merged if s]

    # List-item marker — permissive: matches the marker token at start-of-
    # string or after any whitespace.  The regex does NOT restrict which
    # delimiter precedes the marker via a lookbehind character class —
    # that filtering happens in _split_list_items via `valid_pre`, because a
    # restrictive lookbehind would cause finditer to skip markers preceded
    # by "; ", ") ", ")) " etc. that we actually want to split on.
    # List-item marker \u2014 permissive: matches the marker at start-of-
    # string or after any whitespace.  The regex does NOT restrict which
    # delimiter precedes the marker via a lookbehind character class \u2014
    # that filtering happens in _split_list_items via `valid_pre`.
    _LIST_MARKER_RE = re.compile(
        r'(?:(?:^|(?<=\s))'                     # start of string or after whitespace
        r'(?:[\uff08(]\s*)?'            # optional fullwidth/halfwidth paren
        r'(?:'
            r'[IVXLCDM]{1,5}(?=[.\)]\s)'    # roman upper
            r'|[ivxlcdm]{1,5}(?=[.\)]\s)'  # roman lower
            r'|[a-z](?=[.\)]\s)'           # single letter
            r'|\d+(?=[.\)]\s)'               # number
            r'|[\u2460-\u2473]'             # circled 1-20
            r'|[\u2474-\u2487]'             # paren-circled
            r'|[\u3220-\u3229]'             # ideographic circled
            r'|[\u3280-\u3289]'             # ideographic circled
        r')'
        r'[.\)]?'                               # optional closing dot/paren
        r'(?:\uff09)?'                          # optional closing fullwidth paren
        r')'
    )

    @classmethod
    def _split_list_items(cls, s: str) -> str:
        """Pre-process (string->string): insert a newline before each list-item marker
        ((a), circled, III., i., (1), etc.) when the marker follows a sentence-
        terminating delimiter (newline, ".", ":", ";", ")", "?").
        Returns the modified string."""
        if not s or len(s) < 5:
            return s

        matches = list(cls._LIST_MARKER_RE.finditer(s))
        if not matches:
            return s

        out_parts: list[str] = []
        cursor = 0
        # Ordered longest-first so that e.g. ") " wins over ")".
        valid_pre = (
            '\n', '. ', ': ', '; ', '! ', '? ', ') ', ')', '\uff09 ', '\uff09', '\uff08', '(',
        )
        for m in matches:
            if m.start() == 0:
                continue
            preceded = False
            if s[m.start() - 1] == '\n':
                preceded = True
            else:
                for prefix in valid_pre:
                    if prefix == '\n':
                        continue
                    pl = len(prefix)
                    if m.start() >= pl and s[m.start() - pl:m.start()] == prefix:
                        preceded = True
                        break
            if preceded:
                out_parts.append(s[cursor:m.start()])
                out_parts.append('\n')
                cursor = m.start()
        out_parts.append(s[cursor:])
        return ''.join(out_parts)
    def _post(self, sents: list[str]) -> list[str]:
        try:
            cfg = _cfg().VALIDATION
        except Exception:
            cfg = {}
        target_min = cfg.get('sentence_target_min', 50)
        target_max = cfg.get('sentence_target_max', 500)

        # 1. merge very-short / lowercase-start fragments into predecessor
        # BUT never merge a list-item marker ((a), ①, III., i., (1), etc.)
        # into its predecessor — that would erase the sentence boundary that
        # _split_list_items just opened.
        _LIST_START_RE = re.compile(
            r'^(?:[（(]\s*)?'
            r'(?:'
            r'[IVXLCDM]{1,5}(?=[.\)])'
            r'|[ivxlcdm]{1,5}(?=[.\)])'
            r'|[a-z](?=[.\)])'
            r'|\d+(?=[.\)])'
            r'|[①-⑳⑴-⒇㈠-㈩㊀-㊉]'
            r')'
        )

        merged = []
        for s in sents:
            s = s.strip()
            if not s:
                continue
            if merged and (
                len(s) <= 2
                or (s[0:1].islower()
                    and not s.startswith(('e ', 'ou ', 'ou,', 'a ', 'a,',
                                           'o ', 'i ', 'u ', 'em ', 'na ',
                                           'no ', 'para ', 'de ', ' ')))
            ):
                # Don't absorb a list-item marker into predecessor
                if _LIST_START_RE.match(s):
                    merged.append(s)
                    continue
                merged[-1] = merged[-1].rstrip() + ' ' + s
                continue
            merged.append(s)

        # 1b. split at list-item markers ((a), ①, III. i. etc.)
        # _split_list_items is now a string→string transform already applied
        # in segment() upstream, so this pass is a no-op / kept for safety.
        list_split = merged

        # 2. enforce upper bound
        bounded = []
        for s in list_split:
            if len(s) <= target_max:
                bounded.append(s)
            else:
                bounded.extend(self._hard_split(s, target_max))

        # 3. minimum-merge pass — but never merge a list-item marker into
        # its predecessor (would erase the boundary _split_list_items opened).
        out = []
        for s in bounded:
            s = s.strip()
            if not s:
                continue
            if (out and len(out[-1]) < target_min
                    and not _LIST_START_RE.match(s)):
                out[-1] = out[-1].rstrip() + ' ' + s
            else:
                out.append(s)
        if (len(out) > 1 and len(out[-1]) < target_min
                and not _LIST_START_RE.match(out[-1])):
            last = out.pop()
            out[-1] = out[-1].rstrip() + ' ' + last
        return out

    @staticmethod
    def _hard_split(s: str, max_len: int) -> list[str]:
        out = []
        while len(s) > max_len:
            cut = s.rfind(', ', 0, max_len)
            if cut == -1:
                cut = s.rfind('; ', 0, max_len)
            if cut == -1:
                cut = s.rfind(' ', int(max_len * 0.7), max_len)
            if cut == -1:
                cut = max_len
            out.append(s[:cut].rstrip())
            s = s[cut:].lstrip(',; ')
        if s.strip():
            out.append(s.strip())
        return out


# --------------------------------------------------------------------------- #
#  5. New unified entry point
# --------------------------------------------------------------------------- #

class ParseResult:
    __slots__ = ('roots', 'items', 'meta', 'raw_rows')

    def __init__(self, roots, items, meta, raw_rows):
        self.roots = roots            # list[Node]
        self.items = items            # list[dict] (per-sentence rows)
        self.meta = meta
        self.raw_rows = raw_rows      # list[dict] (pre-segmentation, one per node)


def parse_text(raw_text: str, *, lang: str = 'pt',
               drop_noise: bool = True) -> ParseResult:
    """Parse `raw_text` into requirement rows, with sentence segmentation."""
    parser = ChapterSectionParser(drop_noise=drop_noise)
    roots, rows = parser.parse(raw_text)
    meta = {
        'top_level_sections': len(roots),
        'nodes_with_body': len(rows),
    }

    if not rows:
        return ParseResult(roots, [], meta, rows)

    seg = SentenceSegmenter(lang)
    items: list[dict] = []
    seen_ids: set[str] = set()
    idx = 0
    for row in rows:
        body = row.get('content_raw', '').strip()
        if not body:
            continue
        # Collapse pdfplumber's per-line indentation + internal newlines
        # into a single-space-joined paragraph before segmentation.
        body = re.sub(r'[ \t]+', ' ', body)
        body = re.sub(r'\n ', '\n', body)
        body = re.sub(r'\n+', ' ', body)
        body = body.strip()
        if not body:
            continue
        sents = seg.segment(body)
        for s in sents:
            s = s.strip()
            if not s:
                continue
            idx += 1
            uid = f'REQ-{idx:04d}'
            while uid in seen_ids:
                idx += 1
                uid = f'REQ-{idx:04d}'
            seen_ids.add(uid)
            items.append({
                'id': uid,
                'chapter_number': row['chapter_number'],
                'chapter_title': row['chapter_title'],
                'section_number': row['section_number'],
                'section_title': row['section_title'],
                'content': s,
                'hierarchy_path': row['hierarchy_path'],
                'page': row['page'],
                'tag': row.get('tag', ''),
                'is_valid': True,
                'validation': {},
                'confidence': 0.0,
            })
    meta['requirement_count'] = len(items)
    return ParseResult(roots, items, meta, rows)


# --------------------------------------------------------------------------- #
#  JSON output helper
# --------------------------------------------------------------------------- #

def save_json_output(json_data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    return output_file