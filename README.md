# DIaT

> Structured-requirement extraction and translation tool — pull hierarchical
> requirements out of PDF documents, decompose by structure, translate, and
> export an Excel report.

Language docs: **English** (this file) · **中文** → [`README_zh.md`](README_zh.md)

---

## 1. Purpose

This tool processes **structured, multi-language PDF documents** end-to-end:

- **Extract**: restore body text from multi-column, table-heavy PDFs with repeating headers/footers (4-strategy merge + scanned-PDF OCR fallback).
- **Split**: decompose the document into hierarchical requirements (章 → 节 → 条 → 款 → 项).
- **Segment**: per-source-language sentence boundary detection — hard-coded best practices for pt / en / zh / ja / ko / es / fr / de / …
- **Translate**: multi-language rendering via Google Translate or Agent (Claude) mode.
- **Validate**: mandatory body-preservation assertion (raises `BodyLossError` if < 80% coverage — silent dropping is intolerable).
- **Export**: Excel workbook (ID / 章 / 节 / 需求原文 / per-language translation columns).

---

## 2. Capability Boundaries

### ✅ Supported

| Dimension | Scope |
|-----------|-------|
| Input | Single PDF file, or a directory of PDFs (batch) |
| Structure type | Hierarchically-numbered documents (contracts, specs, regulations, bids, standards…) |
| Headers / footers | Auto-detect repeating blocks (≥ 75% of pages) and strip them |
| Scanned PDFs | Probe, then call `ocrmypdf --language <config>` for OCR fallback (lazy import, not a hard dependency) |
| Hierarchy markers | `Art. 1º` / `CAPÍTULO` / `SEÇÃO` / `§ 1º` / `I.` / `1.` / `1.2` / `1.2.1` / `（1）` / `(a)` / `•` / `(1)` / roman numerals / circled numbers |
| Source language | pysbd (optional) + built-in regex fallback; pt / en / es / fr / de / zh / ja / ko each have dedicated segmentation rules |
| Target language | Any googletrans / Claude language code (2 columns per run) |
| Translation engine | Google Translate (direct) or Agent (Claude translates on its own) |
| Proper-noun protection | Placeholder substitution (built-in ~30 generic terms + user-supplied additions), restored after translation |
| Output format | Excel workbook (ID / 章 / 节 / 需求原文 / per-language translation columns) |
| Body validation | Mandatory coverage check; < 80% halts the pipeline with no output |
| Title preservation | Heading lines are always emitted as part of each requirement's body (for coverage audit + context tracing); empty-body headings are auto-synthesized |
| Default interaction | Interactive by default — prompts for target language / translation engine / proper-noun additions; only skips when the user explicitly asks or passes `--no-input` |
| Table-row filtering | When matching a `D1/D2/D3` heading, rejects rows containing `;` (cell separator), `(` (unit annotation), a trailing " - short word" (label/value pair), or digits — avoids misreading PDF table rows as section headings |

### ❌ NOT supported (out of scope)

- ❌ Recognizing text embedded in images, flowcharts, or scanned drawings (body text only)
- ❌ Handwritten documents / very low quality scans / heavily skewed OCR
- ❌ Cross-document diffing, aggregation, or delta extraction
- ❌ Auto-filling scorecards, compliance matrices, or bid responses
- ❌ Non-text PDFs (pure image albums, rasterized CAD PDFs)
- ❌ Real-time collaboration / concurrent multi-user editing
- ❌ Structured semantic understanding (does not classify deontic modality like "shall / must")
- ❌ Legally-certified translation (machine output is reference-only, no legal warranty)

### ⚠️ Prerequisites

- PDF must be **text-selectable** digital, or scanned at ≥ 200 dpi
- Access to the Google Translate API (direct or via overseas proxy) is required unless you use Agent mode
- Runtime: Python 3.9+; dependencies `pdfplumber`, `openpyxl`,
  `googletrans==4.0.0-rc1` (the first two are required; googletrans is only needed for the Google engine)
- Large files (> 100 pages) grow significantly in processing time; OCR fallback runs ~1-5 s per page

---

## 3. Architecture / Pipeline

```
PDF file
   │
   ▼
[003_pdf_extractor]  extract_with_meta()
   │  4-strategy merge: layout → words → tables → chars   (fallback cascading)
   │  repeat-block stripper  +  __PAGE_N__  sentinels
   │  scanned-PDF probe → ocrmypdf → re-open
   ▼
raw_text  +  ExtractionMeta
   │
   ▼
[001_text_splitter]  parse_text(raw_text, lang)
   │  ChapterSectionParser  — priority-ordered regex + stack builder
   │  SentenceSegmenter     — per-language best-practice rules
   ▼
ParseResult  { roots, items, meta, raw_rows }
   │
   ├──▶ [008_validator]  assert_body_intact(raw_text, items)
   │       word-multiset coverage ratio  →  BodyLossError if < 80%
   │
   ▼
[002_translator]  (optional)  Google / Agent translation
   │
   ▼
[005_excel_generator]  Excel workbook
        ID | 章 | 节 | 需求原文 | English | 中文 | …
```

### Key invariants

1. Body coverage from `raw_text` into `items['content']` **must never fall below 80%** (hard threshold).
2. Every page is marked with a `__PAGE_N__` sentinel so page attribution survives header stripping.
3. Every requirement row carries a full `hierarchy_path` (e.g. `1 Sistemas > 1.2 MDC > 1.2.1 Condições Gerais`).

---

## 4. Project Structure

```
DIaT/
├── 007_config/
│   └── config.py               # global config + language-abbreviation table + VALIDATION thresholds
├── 003_pdf_extractor/
│   └── pdf_extractor.py        # 4-strategy merge extraction + repeating-block stripper + OCR fallback
├── 001_text_splitter/
│   └── text_splitter.py        # ChapterSectionParser + SentenceSegmenter
├── 004_classifier/             # (inactive — no longer called from main.py)
│   └── classifier.py
├── 005_excel_generator/
│   └── excel_generator.py      # Excel output (requirement-category / product columns removed)
├── 008_validator/
│   └── validator.py            # assert_body_intact — body-survival check
├── 002_translator/
│   └── translator.py           # TranslationService (Google + Agent)
├── 006_main/
│   └── main.py                 # CLI entry point + pipeline orchestration
├── 006_postprocess/
│   └── split_items_postprocess.py
├── README.md                   # user-facing documentation (this file, English)
├── README_zh.md                # user-facing documentation (Chinese)
└── AGENT_GUIDE.md              # orchestrator / sub-agent usage principles
```

---

## 5. Quick Start

### Install

```bash
pip install pdfplumber openpyxl googletrans==4.0.0-rc1
# optional (better segmentation):
pip install pysbd
# optional (OCR for scanned PDFs):
pip install ocrmypdf     # also requires system tesseract + ghostscript installed
```

### Run

> **Default = interactive.** When `--no-input` is omitted, the script prompts for target language / translation engine / proper-noun additions. Pass `--no-input` only when the user explicitly wants non-interactive mode.

```bash
cd "D:/Tool Development/Skills Development/DIaT"

# single file — default interactive mode (prompts for language / engine / proper nouns)
PYTHONIOENCODING=utf-8 python 006_main/main.py "<your-file.pdf>"

# non-interactive — explicitly skip all prompts, use en + zh-cn + Google
PYTHONIOENCODING=utf-8 python 006_main/main.py \
    "<your-file.pdf>" --no-input

# single file — extract + split + export Excel only, no translation (non-interactive)
PYTHONIOENCODING=utf-8 python 006_main/main.py \
    "<your-file.pdf>" \
    --no-translate --json --no-input

# single file — auto-translate (Google Translate, non-interactive)
PYTHONIOENCODING=utf-8 python 006_main/main.py \
    "<your-file.pdf>" \
    -e google --no-input -l en,zh-cn

# Agent mode (Claude reads the JSON, translates, writes back to Excel)
PYTHONIOENCODING=utf-8 python 006_main/main.py \
    "<your-file.pdf>" \
    -e agent --no-input -l en,zh-cn

# batch a directory (non-interactive)
PYTHONIOENCODING=utf-8 python 006_main/main.py ./pdfs --no-input
```

### CLI arguments

| Argument | Description |
|----------|-------------|
| `input` | PDF file or directory path |
| `-o, --output` | Output directory (default `output_fixed/`) |
| `--no-translate` | Skip translation |
| `--json` | Also emit the JSON intermediate |
| `-l, --lang` | Target languages, comma-separated (e.g. `en,zh-cn`). Default is 2 columns (English + Chinese) |
| `-e, --engine` | Translation engine `google` (default) or `agent` |
| `--no-input` | **Explicit** non-interactive mode (en + zh-cn + Google). Default behavior is interactive; only pass this when explicitly asked |

### Translation language-selection rules

1. **Default 2-column translation** — Excel emits `需求原文` followed by two translation columns (e.g. `英文翻译` + `中文翻译`)
2. **Interactive selection** — in non-`--no-input` mode the script asks the user to pick any two target languages (default `en,zh-cn`)
3. **Same-source skip** — if the source language equals a target language, that column keeps the original text and the translation API is not called
   - e.g. source is English and you pick `en,zh-cn` → the `英文翻译` column shows the original, `中文翻译` calls Google Translate

### Interactive flow

In non-`--no-input` mode the script asks the user three questions in sequence:

1. **Target language** (default en + zh-cn)
2. **Translation engine** (default Google Translate)
3. **Proper-noun additions** (category-guided; defaults to none)

Example session:

```
$ PYTHONIOENCODING=utf-8 python 006_main/main.py example.pdf

  =======================================================
    Target Translation Language Selection
  =======================================================
  Detected source: pt (Português)

    en       — English
    zh-cn    — 中文（简体）
    pt       — Português ← source
    ...

  Enter 2 language codes (comma-separated)
  or press Enter for default [en,zh-cn]:

  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Translation Engine Selection
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    1. Google Translate API   (default — fast, external)
    2. Agent  — Claude reads JSON, translates, writes back

  Enter 1 or 2 (or press Enter for default Google):

  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Proper-Noun Protection
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  The following term categories are kept verbatim during translation:
    [technical abbreviations]  API, HTTP, HTTPS, JSON, XML, CSV, TCP, UDP, IP, VPN, … (17)
    [standards bodies]         IEC, IEEE, ISO, ITU, ANSI, IETF, W3C                (7)
    [network / infrastructure] RF, PLC, LAN, WAN, HAN                              (5)
    [measurement units]        GWh, MWh, kWh, Hz, kV, kW, kVA, MVA, ms, s        (10)
    [company / product names]  Google, Microsoft, Amazon, Apple                     (4)

  The following categories start empty and are filled per-document:
     1. Person names             6. Regulatory bodies
     2. Place names              7. Legal / document references
     3. Product / project codes  8. Industry-specific terms
     4. Company (this document)  9. Roles / responsibilities
    10. ＋ Create a new category…
     0. Done — continue to translation

  Select a category number (1-10 to add, 0=done): 3
  → [Product / project codes] currently empty
    Add comma-separated terms (Enter to skip): SCADA,AMI,MDM,MDC
    + added 4 term(s).

  Select a category number (1-10 to add, 0=done): 4
  → [Company (this document)] currently empty
    Add comma-separated terms (Enter to skip): CPFL,Enel
    + added 2 term(s).

  Select a category number (1-10 to add, 0=done): 0
  ✓ Proper-noun protection configured. 2 categories, 6 terms total.

  [3/4] Translating (engine=google, languages=['en', 'zh-cn'])...
  ...
```

---

## 6. Roadmap

- [ ] Allow specifying the source language on the CLI (skip auto-detection)
- [ ] Add docx / odt output formats
- [ ] Improve the multi-paragraph merge strategy (currently sentence-based)
- [ ] Broader adaptation to official documents in other languages (Spanish / Portuguese / Angolan / …)
- [ ] Incremental processing: extract deltas between two revisions of the same PDF

---

## 7. Body-Preservation Guarantee

Silent body loss is **intolerable** — `008_validator` runs unconditionally before the Excel is generated:

1. Walk `raw_text` line by line, skipping header/footer/toc rows → produce `body_lines`.
2. Normalize each `item['content']` into a word multiset.
3. Greedy match: `coverage = Σ covered_words / Σ body_words`.
4. Coverage `< 80%` → raise `BodyLossError`, **halt the pipeline, no Excel is emitted**.
5. Uncovered lines are written to `{prefix}_orphans.json` for triage.

Lexical normalization folds all whitespace to a single space before splitting into tokens, so pdfplumber-driven line-break indentation differences are not miscounted as body loss.

The thresholds live in `007_config/config.py::VALIDATION`:

```python
VALIDATION = {
    'min_char_coverage': 0.80,   # minimum body survival rate
    'min_word_coverage': 0.85,
    'write_orphans': True,
    'sentence_target_min': 50,    # min chars per sentence
    'sentence_target_max': 500,   # max chars per sentence
}
```

---

## 8. License & Attribution

© **Aggre-Cloud 聚云科技** — <https://www.acdatech.com>

Developed and maintained by Aggre-Cloud (聚云科技).

---

## 9. Proper-Noun Protection

Before translation, the following term classes are replaced by placeholders
`__PROPER_<uuid>__` so that Google Translate leaves them untouched, and are
restored afterwards:

`007_config/config.py::DO_NOT_TRANSLATE` is a **categorized dictionary**
(`category → {label, items}`); the built-in seed contains only **cross-industry
generic terms** (~30), organized by category:

- Technical abbreviations (API, HTTP, HTTPS, JSON, XML, CSV, TCP, UDP, IP, SSH, …)
- Standards bodies (IEC, IEEE, ISO, ITU, ANSI, IETF, W3C)
- Network / infrastructure (RF, PLC, LAN, WAN, HAN)
- Measurement units (GWh, MWh, kWh, Hz, kV, kW, kVA, MVA, ms, s)
- Generic company / product names (Google, Microsoft, Amazon, Apple)

The following are **empty categories** filled during interactive step 3 on a
per-document basis: person names, place names, product / project codes, company
(this document), regulatory bodies, legal / document references, industry-specific
terms, roles / responsibilities — and the user may **create arbitrary new
categories** at runtime.

> The category set is **open**: industry-specific terms (e.g. `SCADA/AMI/MDM/MDC`
> for power utilities, drug names for healthcare, court names for law) are
> **not** versioned seed — the user fills them under the matching category while
> processing a concrete document. This is the tool's core mechanism for
> cross-industry generalization.

In interactive mode, step 3 **guides the user category by category**,
immediately showing the running count, instead of asking them to list terms
from scratch.

**Mechanism** (`002_translator/translator.py`):

```
original
  │
  ▼
_protect_proper_nouns()        ← replace DO_NOT_TRANSLATE terms with placeholders
  │
  ▼
Google Translate API
  │
  ▼
_restore_proper_nouns()        ← replace placeholders back with original terms
  │
  ▼
translation
```

The term list is sorted by descending length so that `Advanced Metering`
is matched before `AMI`.

---

## 10. Agent Translation Mode

In Agent mode the script **does not call Google Translate**; instead it:

1. Writes `*_agent_queue.json` (containing `source_language`, `target_languages`,
   `requirements`, `extra_do_not_translate`)
2. The Agent (Claude) reads the JSON and translates each requirement
3. The Agent calls `write_translations_to_excel()` to write the results back

**When to use it**:

- Google Translate is not reachable (network restriction)
- Higher translation quality is needed (Claude understands context)
- Terminology consistency matters (Claude can reference the full document)

**Note**: in Agent mode the `extra_do_not_translate` list is likewise applied;
the agent must substitute the same placeholders before translation (the same
`_protect_proper_nouns` / `_restore_proper_nouns` pattern used by the Google path).

---

## 11. Output Format

Excel worksheet `Requirements` column definition:

| Column | Field | Description |
|--------|-------|-------------|
| A | ID | REQ-0001, incrementing |
| B | 章 | Top-level chapter number + title |
| C | 节 | Sub-chapter number + title |
| D | 需求原文 | Full sentence in the source language |
| E | {lang1} translation | First target language (e.g. `英文翻译`) |
| F | {lang2} translation | Second target language (e.g. `中文翻译`) |

- Columns E / F headers are chosen dynamically from the target languages
- When the source language matches a target language, that column keeps the original text (no API call)
- Column widths: `[10, 35, 35, 65, 65, 65]`
```

