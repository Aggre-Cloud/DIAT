# DIaT

> Structured-requirement extraction and translation tool — pull hierarchical
> requirements out of PDF documents, decompose by structure, translate, and
> export an Excel report.

Language: **English** (this file) · **中文** → [`README_zh.md`](README_zh.md)

---

## 1. What is DIaT? — Project Background

### The problem it solves

International engineering, energy, and infrastructure projects routinely produce
**structured, multi-language PDF documents** — procurement bids, technical
specifications, contracts, regulations, and standards.  These documents share
a common shape:

- **Hierarchically numbered**: chapters → sections → articles → clauses → items
  (章 → 节 → 条 → 款 → 项), often mixing numbering schemes like `Art. 1º`,
  `CAPÍTULO`, `1.2.1`, `（1）`, `(a)`, roman numerals.
- **Multi-language**: a Portuguese specification for a Chinese-backed project,
  an Arabic tender reviewed by a German contractor, a Russian O&M plan read by a
  Brazilian team.
- **Layout-heavy**: multi-column text, embedded tables, repeating headers and
  footers, and — in the worst case — scanned image pages.

For a project engineer, procurement officer, or technical reviewer, the real
work is: *"extract every requirement, know which chapter it belongs to, and make
it readable in my language."*  Doing this by hand is slow, error-prone, and
does not scale across a folder of documents.

### What DIaT does

**DIaT** (the name is a placeholder acronym) turns one such PDF into a
structured, translated Excel workbook in a single command:

1. **Extract** body text from the PDF — 4-strategy merge (layout → words →
   tables → chars) with automatic header/footer stripping and scanned-PDF OCR
   fallback.
2. **Decompose** the document into hierarchical requirements, preserving the
   chapter/section path of each item.
3. **Segment** sentences per source language (pt / en / zh / ja / ko / es /
   fr / de / …).
4. **Translate** each requirement into two target languages — English is always
   one column; you pick the other.
5. **Validate** that no body text was silently dropped (aborts if coverage <
   80% — partial output is intolerable).
6. **Export** an Excel workbook: `ID / 章 / 节 / 需求原文 / English / <your
   language>`.

### Who it is for

- Project engineers and procurement staff working with multi-language specs and
  bids.
- Technical translators who need a first-pass machine translation anchored to
  the document's structure.
- Compliance / QA reviewers who need to trace every requirement back to its
  source chapter.
- AI agents (Claude, etc.) that orchestrate document-processing pipelines and
  need a deterministic, self-validating tool.

### Non-goals

DIaT does **not** replace a human translator, does not produce legally-certified
output, does not read text embedded in images or flowcharts, and does not
perform semantic analysis of contractual obligation ("shall / must").  It is a
**structure-preserving extraction + machine-translation aid** — the human
remains in the loop for review.

---

## 2. How to Use — Recommended Ways

### ▶ Recommended: interactive mode (just run it)

The simplest, recommended way to use DIaT is to run it **interactively** and let
the script guide you.  You only need to answer three questions; everything else
is automatic:

```bash
# Make sure you're in the project root
cd "<project-root>"

# Run — that's it.  The script asks you 3 questions, then produces the Excel.
PYTHONIOENCODING=utf-8 python 006_main/main.py "your-file.pdf"
```

You will be prompted, in order:

| # | Question | Default |
|---|----------|---------|
| (a) | **Pick ONE non-English target language** — English (`en`) is always a target; you only choose the second | `zh-cn` (Simplified Chinese) |
| (b) | **Pick translation engine** — `google` (Translate API) or `agent` (Claude self-translates via JSON queue) | `google` |
| (c) | **Add proper-noun terms** by category (person name, project code, company, …) — or press Enter to skip | none (built-in ~30 generic seed terms) |

After the prompts, the pipeline runs to completion and writes the Excel to
`output/<your-file>_requirements.xlsx`.

> **Tip:** if the auto-detected source language equals one of your targets,
> that column keeps the original text automatically — no extra API call.

### ▶ Non-interactive mode (batch / CI / explicit flags)

If you already know all the choices and want to skip the prompts, pass the
flags explicitly:

```bash
# English + Japanese, Google, non-interactive
PYTHONIOENCODING=utf-8 python 006_main/main.py "your-file.pdf" \
    -l ja -e google --no-input

# English + Chinese, Agent mode, non-interactive
PYTHONIOENCODING=utf-8 python 006_main/main.py "your-file.pdf" \
    -l zh-cn -e agent --no-input

# Extract + split + export Excel only, no translation
PYTHONIOENCODING=utf-8 python 006_main/main.py "your-file.pdf" \
    --no-translate --json --no-input

# Batch a whole directory (non-interactive)
PYTHONIOENCODING=utf-8 python 006_main/main.py ./pdfs --no-input
```

> **Note:** English (`en`) is always added automatically — `-l` only takes the
> *non-English* language.  `-l en` is rejected with a clear message.

### ▶ Agent / automated execution (auto-install deps first)

When an AI agent runs DIaT, dependencies may not be present.  The script can
install them from the project's own `requirements.txt` without human input:

```bash
# 1. (Optional) self-install missing deps — non-interactive in a non-TTY.
#    Skip if you already ran `pip install -r requirements.txt`.
python -m 006_main.main --install-deps

# 2. Also pull optional extras (better segmentation + scanned-PDF OCR)
python -m 006_main.main --install-deps --with-optional

# 3. Run the actual pipeline
python -m 006_main.main "your-file.pdf" -l ja -e google --no-input
```

### ▶ Human manual install (one command)

```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt   # optional: pysbd + ocrmypdf
```

---

## 3. Agent Execution Protocol — What the Agent Should Recommend

When an AI agent orchestrates DIaT on behalf of a user, **the recommended
behavior is**:

1. **Default to interactive.**  Do NOT pass `--no-input` on behalf of the
   user — only pass it when the user explicitly asks for a non-interactive /
   batch / fully-automated run.
2. **Ask the user the three questions (a) / (b) / (c) above** before
   executing, even if CLI flags could supply defaults.  This is the
   project's mandatory pre-run checklist (see `AGENT_GUIDE.md §2`).
3. **Recommend the interactive path** (`python 006_main/main.py "file.pdf"`)
   as the primary way to use the skill — it is the least error-prone and
   teaches the user what the tool can do.
4. **Verify dependencies** before the first run: invoke `--install-deps` if a
   required import is missing, then re-run.

The tool is ultimately **for people to use** — the agent's job is to put the
user in front of the three prompts, not to silently decide on their behalf.

---

## 4. Installed Dependencies

| Package | Required? | Purpose |
|---------|-----------|---------|
| `openpyxl` | required | Excel workbook read/write |
| `pdfplumber` | required | PDF text extraction (4-strategy merge) |
| `PyPDF2` | required | PDF page probing / metadata |
| `pypdfium2` | required | PDF rendering / page images |
| `googletrans` | required | Google Translate engine (only when `-e google`) |
| `pysbd` | optional | language-aware sentence segmentation (regex fallback if absent) |
| `ocrmypdf` | optional | OCR fallback for scanned PDFs (needs system tesseract + ghostscript) |

---

## 5. Capability Boundaries

### ✅ Supported

| Dimension | Scope |
|-----------|-------|
| Input | Single PDF file, or a directory of PDFs (batch) |
| Structure type | Hierarchically-numbered documents (contracts, specs, regulations, bids, standards…) |
| Headers / footers | Auto-detect repeating blocks (≥ 75% of pages) and strip them |
| Scanned PDFs | Probe, then call `ocrmypdf --language <config>` for OCR fallback (lazy import, not a hard dependency) |
| Hierarchy markers | `Art. 1º` / `CAPÍTULO` / `SEÇÃO` / `§ 1º` / `I.` / `1.` / `1.2` / `1.2.1` / `（1）` / `(a)` / `•` / `(1)` / roman numerals / circled numbers |
| Source language | pysbd (optional) + built-in regex fallback; pt / en / es / fr / de / zh / ja / ko each have dedicated segmentation rules |
| Target language | English (fixed) + one user-picked language (any googletrans / Claude code) |
| Translation engine | Google Translate (direct) or Agent (Claude translates on its own) |
| Proper-noun protection | Placeholder substitution (built-in ~30 generic terms + user-supplied additions), restored after translation |
| Output format | Excel workbook (ID / 章 / 节 / 需求原文 / English / <your language>) |
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
- Runtime: Python 3.9+; dependencies listed in §4
- Large files (> 100 pages) grow significantly in processing time; OCR fallback runs ~1-5 s per page

---

## 6. Architecture / Pipeline

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
        ID | 章 | 节 | 需求原文 | English | <your language>
```

### Key invariants

1. Body coverage from `raw_text` into `items['content']` **must never fall below 80%** (hard threshold).
2. Every page is marked with a `__PAGE_N__` sentinel so page attribution survives header stripping.
3. Every requirement row carries a full `hierarchy_path` (e.g. `1 Sistemas > 1.2 MDC > 1.2.1 Condições Gerais`).

---

## 7. Project Structure

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
│   └── excel_generator.py      # Excel output (localized headers; English + one user language)
├── 008_validator/
│   └── validator.py            # assert_body_intact — body-survival check
├── 002_translator/
│   └── translator.py           # TranslationService (Google + Agent)
├── 006_main/
│   └── main.py                 # CLI entry point + pipeline orchestration
├── 006_postprocess/
│   └── split_items_postprocess.py
├── sample doc/                 # example PDFs (multi-language) for testing
├── README.md                   # this file — user-facing docs (English)
├── README_zh.md                # user-facing docs (Chinese)
└── AGENT_GUIDE.md              # orchestrator / sub-agent usage principles
```

---

## 8. CLI Arguments

| Argument | Description |
|----------|-------------|
| `input` | PDF file or directory path |
| `-o, --output` | Output directory (default `output/`) |
| `--no-translate` | Skip translation |
| `--json` | Also emit the JSON intermediate |
| `-l, --lang` | The NON-English target language (e.g. `pt`, `ja`). English is always added automatically |
| `-e, --engine` | Translation engine `google` (default) or `agent` |
| `--no-input` | **Explicit** non-interactive mode (en + zh-cn + Google). Default is interactive; only pass when explicitly asked |
| `--display-lang` | Override the Excel header / sheet language (default: the non-English target) |
| `--install-deps` | Install missing third-party packages from `requirements.txt`, then exit. Non-interactive when stdin is not a TTY (agent / pipe); asks for confirmation in a TTY |
| `--with-optional` | Combined with `--install-deps`, also install the optional extras (`pysbd`, `ocrmypdf`) |

### Translation language-selection rules

1. **English is always a target** — you only pick the second language.
2. **Same-source skip** — if the source language equals a target, that column keeps the original text (no API call).
3. **Localized headers** — Excel static headers, column headers, and sheet title render in the non-English target language (e.g. `en + ja` → `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`).  No mixed-language headers.

---

## 9. Interactive Flow — Example Session

```
$ PYTHONIOENCODING=utf-8 python 006_main/main.py example.pdf

  =======================================================
    Target Translation Language Selection
  =======================================================
  Detected source: pt (Português)

    English (en) is always a target.
    Choose ONE additional language for the second column.
    Default: zh-cn
    zh-cn    — 中文（简体）
    pt       — Português ← source
    es       — Español
    ...

  Enter 1 language code (or press Enter for default zh-cn): pt
  → Targets: en + pt
  ⚠ Source is pt (Português) → the Português column will show the original text.

  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Translation Engine Selection
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    1. Google Translate API   (default — fast, external)
    2. Agent  — Claude reads JSON, translates, writes back

  Enter 1 or 2 (or press Enter for default Google): 1

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

  Select a category number (1-10 to add, 0=done): 0
  ✓ Proper-noun protection configured. 1 categories, 4 terms total.

  [3/4] Translating (engine=google, languages=['en', 'pt'])...
  ...

  [OK] Completed!
  [OK] Output file: output/example_requirements.xlsx
  [OK] Total requirements: 393
  [OK] Valid requirements: 393 (100.0%)
  [OK] Body coverage: 100.7%
```

---

## 10. Body-Preservation Guarantee

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

## 11. Proper-Noun Protection

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

The following are **empty categories** filled during interactive step (c) on a
per-document basis: person names, place names, product / project codes, company
(this document), regulatory bodies, legal / document references, industry-specific
terms, roles / responsibilities — and the user may **create arbitrary new
categories** at runtime.

> The category set is **open**: industry-specific terms (e.g. `SCADA/AMI/MDM/MDC`
> for power utilities, drug names for healthcare, court names for law) are
> **not** versioned seed — the user fills them under the matching category while
> processing a concrete document. This is the tool's core mechanism for
> cross-industry generalization.

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

## 12. Agent Translation Mode

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

## 13. Output Format

Excel worksheet column definition (sheet title and headers localized to the
non-English target language):

| Column | Field | Description |
|--------|-------|-------------|
| A | ID | REQ-0001, incrementing |
| B | 章 (Chapter) | Top-level chapter number + title |
| C | 节 (Section) | Sub-chapter number + title |
| D | 需求原文 (Source) | Full sentence in the source language |
| E | English translation | Always present |
| F | <your language> translation | The user-picked language |

- When targets are `en` + one other language, the static headers + sheet title
  render in that language — e.g. `en + ja` → sheet `要求事項`, headers
  `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`.  No mixed-language headers.
- When the source language matches a target, that column keeps the original
  text (no API call).
- Column widths: `[10, 32, 32, 65, 65]`.
- Override the header language with `--display-lang <code>`.

---

## 14. Roadmap

- [ ] Allow specifying the source language on the CLI (skip auto-detection)
- [ ] Add docx / odt output formats
- [ ] Improve the multi-paragraph merge strategy (currently sentence-based)
- [ ] Broader adaptation to official documents in other languages
- [ ] Incremental processing: extract deltas between two revisions of the same PDF

---

## 15. License & Attribution

© **Aggre-Cloud 聚云科技** — <https://www.acdatech.com>

Developed and maintained by Aggre-Cloud (聚云科技).
