# -*- coding: utf-8 -*-
"""
PDF extraction module — REWRITTEN
=================================
Pipeline (per page, in this order):
  1. clean-text     pdfplumber extract_text(layout=True)
  2. sorted-words   extract_words() sorted top→left
  3. tables         extract_tables() flattened to rows
  4. chars          pdfplumber chars reconstructed (fallback only)

Pre-processing:
  * Repeated top-K / bottom-K line blocks (page-header / footer / doc-code)
    appearing on ≥ 75 % of pages are stripped BEFORE concatenation.
  * Page-boundary sentinel  \\fPAGE{i+1}\\f  inserted so the text_splitter
    can later recover page numbers for 章/节 attribution.

Scanned PDF fallback:
  * is_scanned_pdf() probes up to 5 sample pages.
  * When ≥ 3 return empty text → OCRmyPDF (language from config,
    default `eng``, clean, deskew) is
    invoked to a temp file; extraction then re-runs on that temp file.
  * All imports inside the function — ocrmumber / ocrmypdf are OPTIONAL.

Public result
  extractor.extract_text(pdf_path) -> (final_text, ExtractionMeta)
"""
from __future__ import annotations

import collections
import os
import re
import shutil
import subprocess
import tempfile

# --------------------------------------------------------------------------- #
#  Config
# --------------------------------------------------------------------------- #

_SAMPLE_PAGES = 5          # pages probed for scan detection
_SCAN_EMPTY_THRESHOLD = 3  # ≥ this many empty pages → invoke OCR
_TOP_K = 10                # how many leading lines treated as header
_BOT_K = 4                 # how many trailing lines treated as footer
_REPEAT_FRAC = 0.70        # must appear on ≥ this fraction of pages

# --------------------------------------------------------------------------- #
#  Public types
# --------------------------------------------------------------------------- #

class ExtractionMeta:
    def __init__(self, scanned_fallback_used, page_blocks_stripped,
                 strategy_counts, pages):
        self.scanned_fallback_used = scanned_fallback_used
        self.page_blocks_stripped = page_blocks_stripped
        self.strategy_counts = strategy_counts
        self.pages = pages

    def as_dict(self):
        return {
            'scanned_fallback_used': self.scanned_fallback_used,
            'page_blocks_stripped': self.page_blocks_stripped,
            'strategy_counts': self.strategy_counts,
            'pages': self.pages,
        }


# --------------------------------------------------------------------------- #
#  Class
# --------------------------------------------------------------------------- #

class PDFExtractor:
    """Multi-strategy PDF text extractor with body-preservation focus."""

    def __init__(self):
        try:
            import pdfplumber
            self.use_pdfplumber = True
            print("[OK] Using pdfplumber for PDF text extraction")
        except ImportError:
            self.use_pdfplumber = False
            print("[WARN] pdfplumber not installed, using PyPDF2 fallback")
            print("        pip install pdfplumber")

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def extract_text(self, pdf_path: str) -> tuple[str, ExtractionMeta]:
        """Return (full_text, meta)."""
        if self.use_pdfplumber:
            return self._extract_with_pdfplumber(pdf_path)
        return self._extract_with_pypdf2(pdf_path)

    # ------------------------------------------------------------------ #
    #  pdfplumber path
    # ------------------------------------------------------------------ #

    def _extract_with_pdfplumber(self, pdf_path: str) -> tuple[str, ExtractionMeta]:
        import pdfplumber

        scanned_used = False

        # ── 1. Scan probe ──────────────────────────────────────────────
        if self._is_scanned_pdf(pdf_path):
            ocr_path = self._ocr_fallback(pdf_path)
            if ocr_path and os.path.exists(ocr_path):
                pdf_path = ocr_path
                scanned_used = True
                print("  [PDF] scanned-PDF detected → OCR fallback used")
            else:
                print("  [PDF] WARNING: scanned-PDF detected but OCR unavailable;"
                      " extraction may be empty.  Install ocrmypdf + tesseract.")

        # ── 2. Per-page multi-strategy ─────────────────────────────────
        #     Order matters: we only fall back to a lighter strategy when
        #     the heavier one returned nothing.  This avoids duplicating
        #     already-extracted words (which blows up file size ~3x).
        strategy_counts = {'direct': 0, 'words': 0, 'tables': 0, 'chars': 0}
        page_blocks: list[str] = []

        with pdfplumber.open(pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages):
                parts: list[str] = []

                # Strategy 1 — direct (layout-aware)
                t = (page.extract_text(layout=True) or '').strip()
                if t and len(t) > 20:
                    parts.append(t)
                    strategy_counts['direct'] += 1

                # Strategy 2 — extract_words (ONLY when layout was empty)
                if not parts:
                    try:
                        words = page.extract_words()
                        if words:
                            rows: dict[float, list] = {}
                            for w in words:
                                top = round(float(w['top']) / 8) * 8
                                rows.setdefault(top, []).append(w)
                            word_buf: list[str] = []
                            for top in sorted(rows):
                                row_words = sorted(
                                    rows[top], key=lambda x: float(x['x0']))
                                line_text = ' '.join(w['text'] for w in row_words)
                                if line_text.strip():
                                    word_buf.append(line_text)
                            if word_buf:
                                parts.append('\n'.join(word_buf))
                                strategy_counts['words'] += 1
                    except Exception:
                        pass

                # Strategy 3 — tables
                try:
                    tables = page.extract_tables() or []
                    if tables:
                        for tbl in tables:
                            for row in tbl:
                                line = ' | '.join(
                                    (c or '').strip() for c in row if (c or '').strip()
                                )
                                if line:
                                    parts.append(line)
                        strategy_counts['tables'] += 1
                except Exception:
                    pass

                # Strategy 4 — char-level fallback (only if everything above empty)
                if not parts:
                    try:
                        chars = page.chars
                        if chars:
                            char_rows: dict[float, list] = {}
                            for ch in chars:
                                top = round(float(ch['top']) / 4) * 4
                                char_rows.setdefault(top, []).append(ch)
                            char_buf: list[str] = []
                            for top in sorted(char_rows):
                                row_chars = sorted(char_rows[top],
                                                    key=lambda x: float(x['x0']))
                                line_text = ''.join(c['text'] for c in row_chars)
                                if line_text.strip():
                                    char_buf.append(line_text)
                            if char_buf:
                                parts.append('\n'.join(char_buf))
                                strategy_counts['chars'] += 1
                    except Exception:
                        pass

                # Page marker — plain-text sentinel (no form-feed) so the
                # splitter can recover page numbers via a simple regex.
                page_blocks.append(f"__PAGE_{idx + 1}__" + '\n' + '\n'.join(parts))

        # ── 3. Strip repeated header/footer blocks ─────────────────────
        stripped_count, page_blocks = self._strip_repeated_blocks(page_blocks)

        # ── 4. Join ────────────────────────────────────────────────────
        full = '\n'.join(page_blocks).strip()

        # Collapse any raw form-feeds left by pdfplumber into one blank line
        full = re.sub(r'\f', '\n', full)

        meta = ExtractionMeta(
            scanned_fallback_used=scanned_used,
            page_blocks_stripped=stripped_count,
            strategy_counts=strategy_counts,
            pages=len(page_blocks),
        )
        return full, meta

    # ------------------------------------------------------------------ #
    #  Repeat-block stripper
    # ------------------------------------------------------------------ #

    @staticmethod
    def _signature(lines: list[str], k: int, top: bool) -> tuple:
        """Normalised header/footer signature: collapse internal whitespace."""
        chosen = lines[:k] if top else lines[-k:]
        return tuple(re.sub(r'\s+', ' ', ln).strip() for ln in chosen)

    @classmethod
    def _strip_repeated_blocks(cls, page_blocks: list[str]) -> tuple[int, list[str]]:
        """Remove leading/trailing repeated lines that appear on ≥75% pages.

        Repetition is checked on *normalised* (collapsed-whitespace) lines
        because some PDFs pad headers with spaces.
        """
        if len(page_blocks) < 3:
            return 0, page_blocks

        n = len(page_blocks)
        threshold = max(2, int(n * _REPEAT_FRAC))

        # Collect header candidates at several prefix lengths (1..TOP_K) so
        # that a short common header repeated across all pages is still
        # found even when the longer prefixes diverge (e.g. page 1 vs body).
        header_at_k: dict[int, dict[tuple, int]] = {
            k: collections.Counter() for k in range(2, _TOP_K + 1)}
        footer_at_k: dict[int, dict[tuple, int]] = {
            k: collections.Counter() for k in range(1, _BOT_K + 1)}

        for blk in page_blocks:
            lines = [ln for ln in blk.split('\n')
                     if ln.strip() and not re.match(
                         r'^__PAGE_\d+__$', ln.strip())]
            if not lines:
                continue
            for k, counter in header_at_k.items():
                if len(lines) >= k:
                    counter[cls._signature(lines, k, top=True)] += 1
            for k, counter in footer_at_k.items():
                if len(lines) >= k:
                    counter[cls._signature(lines, k, top=False)] += 1

        best_head: tuple = ()
        best_head_k = 0
        for k in range(_TOP_K, 1, -1):              # prefer LONGEST match
            if not header_at_k[k]:
                continue
            sig, cnt = header_at_k[k].most_common(1)[0]
            if cnt >= threshold:
                best_head, best_head_k = sig, k
                break
        best_foot: tuple = ()
        best_foot_k = 0
        for k in range(_BOT_K, 0, -1):
            if not footer_at_k[k]:
                continue
            sig, cnt = footer_at_k[k].most_common(1)[0]
            if cnt >= threshold:
                best_foot, best_foot_k = sig, k
                break

        if not best_head and not best_foot:
            return 0, page_blocks

        stripped = 0
        new_blocks: list[str] = []
        page_marker_re = re.compile(r'^__PAGE_\d+__$')
        for blk in page_blocks:
            marker = ''
            if page_marker_re.match((blk.split('\n') + [''])[0].strip()):
                marker = blk.split('\n')[0].strip()
            data_lines = [ln for ln in blk.split('\n')
                          if ln.strip() and not page_marker_re.match(ln.strip())]
            if not data_lines:
                new_blocks.append(blk)
                continue

            drop_hd = 0
            if best_head_k and len(data_lines) >= best_head_k:
                if cls._signature(data_lines, best_head_k, top=True) == best_head:
                    drop_hd = best_head_k

            drop_ft = 0
            if best_foot_k and len(data_lines) - drop_hd >= best_foot_k:
                if cls._signature(data_lines, best_foot_k, top=False) == best_foot:
                    drop_ft = best_foot_k

            kept = data_lines[drop_hd:len(data_lines) - drop_ft] \
                if drop_ft else data_lines[drop_hd:]
            # Re-insert the page marker so the splitter can attribute page numbers
            out = ('\n'.join(kept))
            if marker:
                out = marker + '\n' + out
            new_blocks.append(out)
            if drop_hd + drop_ft > 0:
                stripped += 1

        return stripped, new_blocks

    # ------------------------------------------------------------------ #
    #  Scan probe + OCR fallback
    # ------------------------------------------------------------------ #

    @staticmethod
    def _is_scanned_pdf(pdf_path: str) -> bool:
        """Return True if most sample pages yield no text."""
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                sample = list(pdf.pages[:_SAMPLE_PAGES])
                if not sample:
                    return False
                empty = sum(1 for p in sample
                            if not (p.extract_text() or '').strip())
                return empty >= _SCAN_EMPTY_THRESHOLD
        except Exception:
            return False

    @staticmethod
    def _ocr_fallback(pdf_path: str) -> str | None:
        """Run ocrmypdf → temp file. Return temp path or None."""
        ocrmypdf_bin = shutil.which('ocrmypdf')
        if not ocrmypdf_bin:
            return None
        # Lazy import so the dependency stays optional
        import importlib.util as _ilu
        _cfg_path = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), '006_config', 'config.py')
        _spec = _ilu.spec_from_file_location('config_cfg', _cfg_path)
        _cfg = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_cfg)
        _ocr_lang = getattr(_cfg, 'OCR_LANGUAGE', 'eng')

        tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        tmp.close()
        try:
            subprocess.run(
                [ocrmypdf_bin,
                 '--language', _ocr_lang,
                 '--clean', '--deskew', '--force-ocr',
                 '--output-type', 'pdf',
                 pdf_path, tmp.name],
                check=True, capture_output=True, timeout=600,
            )
            return tmp.name
        except Exception as e:
            print(f"  [PDF] OCR failed: {e}")
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
            return None

    # ------------------------------------------------------------------ #
    #  PyPDF2 fallback (unchanged behaviour)
    # ------------------------------------------------------------------ #

    def _extract_with_pypdf2(self, pdf_path: str) -> tuple[str, ExtractionMeta]:
        import PyPDF2
        text = ''
        pages = 0
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                pages += 1
                t = page.extract_text()
                if t:
                    text += t + '\n'
        meta = ExtractionMeta(False, 0, {'pypdf2': pages}, pages)
        return text.strip(), meta

    # ------------------------------------------------------------------ #
    #  Utilities
    # ------------------------------------------------------------------ #

    def get_page_count(self, pdf_path: str) -> int:
        try:
            if self.use_pdfplumber:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    return len(pdf.pages)
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                return len(PyPDF2.PdfReader(f).pages)
        except Exception as e:
            print(f"  Error reading {pdf_path}: {e}")
            return 0


# --------------------------------------------------------------------------- #
#  Module-level convenience
# --------------------------------------------------------------------------- #

pdf_extractor = PDFExtractor()


def extract_text(pdf_path: str) -> str:
    """Return only the text (old call signature)."""
    text, _ = pdf_extractor.extract_text(pdf_path)
    return text


def extract_with_meta(pdf_path: str) -> tuple[str, ExtractionMeta]:
    """New preferred API — returns text AND metadata."""
    return pdf_extractor.extract_text(pdf_path)


def get_page_count(pdf_path: str) -> int:
    return pdf_extractor.get_page_count(pdf_path)
