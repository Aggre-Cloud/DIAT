# DIaT

> Structured-requirement extraction and translation tool — pull hierarchical
> requirements out of PDF documents, decompose by structure, translate, and
> export an Excel report.

Language: **English** (this file) · **中文** → [`README_zh.md`](docs/README_zh.md) · **Português (Brasil)** → [`README_pt.md`](docs/README_pt.md) · **Español** → [`README_es.md`](docs/README_es.md) · **Français** → [`README_fr.md`](docs/README_fr.md) · **Deutsch** → [`README_de.md`](docs/README_de.md) · **日本語** → [`README_ja.md`](docs/README_ja.md)

---

## 1. What is DIaT? — Project Background

### The problem it solves

International engineering, energy, and infrastructure projects routinely produce
**structured, multi-language PDF documents** — procurement bids, technical
specifications, contracts, regulations, and standards.  These documents share
a common shape:

- **Hierarchically numbered**: a 5-depth structure the parser models internally
  as chapter → section → article → clause → item,
  often mixing numbering schemes like `Art. 1º`, `CAPÍTULO`, `1.2.1`, `（1）`,
  `(a)`, roman numerals, circled numbers.  Every requirement carries its full
  `hierarchy_path` internally, but the exported Excel exposes only the top two
  levels (Chapter / Section) as dedicated structural columns — deeper levels stay folded
  into the requirement body so the row stays readable.
- **Multi-language**: a Portuguese specification for a Chinese-backed project,
  an Arabic tender reviewed by a German contractor, a Russian O&M plan read by a
  Brazilian team.
- **Layout-heavy**: multi-column text, embedded tables, repeating headers and
  footers, and — in the worst case — scanned image pages.

For a project engineer, procurement officer, or technical reviewer, the real
work is: *"extract every requirement, know which chapter it belongs to, and make
it readable in my language."*  Doing this by hand is slow, error-prone, and
does not scale across a folder of documents.

### Why DIaT

Document-by-document translation is slow and fragile.  DIaT replaces the
manual copy-paste → translate → reassemble loop with one deterministic,
self-validating pipeline:

| Capability | Manual / Google-translate-only | DIaT |
|------------|-------------------------------|------|
| Document layout | Copy-paste per page; multi-column and table text routinely scrambled | 4-strategy merge extraction (layout → words → tables → chars) with automatic header/footer stripping |
| Requirement splitting | Eyeball the numbering — easy to drop items or flatten the nesting | 12 numbering schemes auto-detected (Art. / CAPÍTULO / § / 1.2.1 / （1）/ (a) / roman / circled …) and a stack-based tree that keeps the **full** chapter path of every item |
| Sentence segmentation | Translate the whole paragraph — long sentences degrade, breaks get lost | Per-source-language best practice (pysbd for Latin scripts, CJK terminator rules for zh/ja/ko, regex fallback for everything else) |
| Proper nouns | Corrupted by the translation engine (`MDC` → lower-case, `AMI` mangled) | Placeholder protection with ~30 built-in generic terms plus category-guided interactive addition, restored verbatim after translation |
| Translation engine | Commit to one | Google Translate **and** Agent (Claude) dual engines — switchable in the same pipeline with identical output layout |
| Body safety | Translation loss is only spotted after the fact, if at all | Mandatory word-multiset coverage check; **< 80% hard-halts the pipeline and emits no Excel** — partial output is intolerable |
| Output language | Single language, mixed-language headers | Sheet title, static headers, and column headers fully localized to the target language — zero mixing |
| Batch | Per-file repetition | Whole-directory batch, CI flags (`--no-input`), and Agent autonomous run |

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
6. **Export** an Excel workbook: `ID / Chapter / Section / Source / English / <your
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
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf"
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
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    -l ja -e google --no-input

# English + Chinese, Agent mode, non-interactive
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    -l zh-cn -e agent --no-input

# Extract + split + export Excel only, no translation
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    --no-translate --json --no-input

# Batch a whole directory (non-interactive)
PYTHONIOENCODING=utf-8 python 005_main/main.py ./pdfs --no-input
```

> **Note:** English (`en`) is always added automatically — `-l` only takes the
> *non-English* language.  `-l en` is rejected with a clear message.

### ▶ Agent / automated execution (auto-install deps first)

When an AI agent runs DIaT, dependencies may not be present.  The script can
install them from the project's own `requirements.txt` without human input:

```bash
# 1. (Optional) self-install missing deps — non-interactive in a non-TTY.
#    Skip if you already ran `pip install -r requirements.txt`.
python -m 005_main.main --install-deps

# 2. Also pull optional extras (better segmentation + scanned-PDF OCR)
python -m 005_main.main --install-deps --with-optional

# 3. Run the actual pipeline
python -m 005_main.main "your-file.pdf" -l ja -e google --no-input
```

### ▶ Human manual install (one command)

```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt   # optional: pysbd + ocrmypdf
```

---

## 3. Use DIaT Through an AI Agent

DIaT is an **agent skill**: you send **one prompt**, and the agent does the
rest — fetching the project, installing dependencies, and running the full
extract → translate → Excel pipeline.  You do not clone or `pip install`
yourself; the agent handles install as part of its run.

The repo's `AGENT_GUIDE.md` is the agent's instruction manual — a capable
agent reads it the moment the project is on disk, so your prompt only needs
to name the **document** and your **choices**.

### 3a. One prompt is enough — templates

Start with the shortest prompt and add detail only when you want to skip a
question.  Pick the row that matches how much you want to decide up front.

| Your prompt | What the agent does |
|---|---|
| `用 DIaT 处理 my-spec.pdf` | Fetches the project, installs deps, then asks you the three questions in §3b before producing the Excel. **Safest start — pick this if unsure.** |
| `Process my-spec.pdf with DIaT` | Same as above, in English. |
| `DIaT my-spec.pdf → English + Japanese, Google engine` | Fetches project, installs deps, runs straight through: `-l ja -e google --no-input`. |
| `用 DIaT 把 spec.pdf 条目化成 Excel，不翻译` | Extract + split + Excel only: `--no-translate --json --no-input`. |
| `DIaT ./pdfsall → zh-cn, agent engine, batch` | Whole-directory batch in Agent-translation mode (`-e agent`); the agent translates the emitted JSON queue. |

The prompts work in any language the agent understands.  The Chinese
examples are used because DIaT's defaults are tuned for Chinese↔English
engineering documents.

### 3b. The three questions the agent will ask

If your prompt does not pin down language / engine / proper nouns, the
agent asks you these before translating — this is `AGENT_GUIDE.md`'s
mandatory checklist, not a courtesy:

| # | Question | If you say nothing (default) |
|---|----------|------|
| (a) | **Pick ONE non-English target language** — English (`en`) is always a target; you only choose the second | `zh-cn` (Simplified Chinese) |
| (b) | **Pick translation engine** — `google` (Translate API) or `agent` (Claude self-translates via JSON queue) | `google` |
| (c) | **Add proper-noun terms** by category (person name, project code, company, …) | skip — uses built-in ~30 generic seed terms |

**Recommended:** answer the three prompts at least the first time.  That
interactive flow teaches you what the tool can do and avoids a
wrong-language / wrong-engine run.  Spell out your choices in the prompt
(like the non-interactive rows in §3a) only when you deliberately want to
skip the questions.

### 3c. End-to-end example (one prompt → finished Excel)

This is the full conversation shape — one prompt from you, the agent
installs whatever is missing, then either asks the three questions or runs.
Same flow as §10, shown as a dialogue so you know what to expect.

```
You:  Process my-spec.pdf with DIaT

Agent: [clones github.com/Aggre-Cloud/DIaT absent]
       [runs: python -m 005_main.main --install-deps  ]
       Detected source language: pt
       Which NON-English target language? (default zh-cn)
You:   ja

Agent: Translation engine — Google or Agent?
You:   google

Agent: Add any proper-noun terms, or press Enter to skip?
       (shows the categorized term list)
You:   [Enter]

Agent: [extract → split → validate → translate → write Excel]
       Written: output/my-spec_requirements.xlsx
       393 requirements, body coverage 100.7 %
```

### 3d. How install actually happens (agent-side)

You never run these by hand — shown here only so you understand what the
agent is doing under the hood:

| Situation | Agent runs |
|---|---|
| Project not on disk | `git clone https://github.com/Aggre-Cloud/DIAT.git` → reads `AGENT_GUIDE.md` |
| Dependencies missing | `PYTHONIOENCODING=utf-8 python -m 005_main.main --install-deps` (auto-installs `requirements.txt`; no prompt in a non-TTY) |
| Optional extras wanted | add `--with-optional` to also pull `pysbd` + `ocrmypdf` |
| Pipeline | `PYTHONIOENCODING=utf-8 python -m 005_main.main "<file.pdf>" -l ja -e google --no-input` |
| Agent engine chosen | pipeline writes `*_agent_queue.json` with blank translation columns → agent translates each row and calls `write_translations_to_excel()` to persist |

### 3e. What the agent must and must not do

The full contract is `AGENT_GUIDE.md §3`.  The short version:

- **One prompt is the user's whole job** — the agent does install + run.
  It must never ask the user to manually clone or `pip install`.
- **Default to interactive** — never pass `--no-input` on the user's behalf;
  only when the user *explicitly* asks for a non-interactive / batch run.
- **Never skip the three questions** (§3b) in interactive mode.
- **Recommend the interactive path** as the primary way to use the skill
  (`python 005_main/main.py "file.pdf"`, no flags) — it is the least
  error-prone and teaches the user what the tool can do.
- **Never silence body loss** — if coverage < 80 %, the pipeline halts and
  no Excel is written; the agent must surface the error, not retry with a
  lower threshold unless the user asks.
- **Never modify DIaT's source files** during a run.  User-supplied
  proper-noun terms go into the live cache / JSON queue, never into
  `config.py` (avoids cross-run leakage).

---

## 5. Installed Dependencies

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

## 6. Capability Boundaries

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
| Output format | Excel workbook (ID / Chapter / Section / Source / English / <your language>) |
| Body validation | Mandatory coverage check; < 80% halts the pipeline with no output |
| Title preservation | Heading lines are always emitted as part of each requirement's body (for coverage audit + context tracing); empty-body headings are auto-synthesized |
| Default interaction | Interactive by default — prompts for target language / translation engine / proper-noun additions; only skips when the user explicitly asks or passes `--no-input` |
| Table-row filtering | When matching a `D1/D2/D3` heading, rejects rows containing `;` (cell separator), `(` (unit annotation), a trailing " - short word" (label/value pair), or digits — avoids misreading PDF table rows as section headings |

### ⚠️ Prerequisites

- PDF must be **text-selectable** digital, or scanned at ≥ 200 dpi
- Access to the Google Translate API (direct or via overseas proxy) is required unless you use Agent mode
- Runtime: Python 3.9+; dependencies listed in §4
- Large files (> 100 pages) grow significantly in processing time; OCR fallback runs ~1-5 s per page

---

## 7. Architecture / Pipeline

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
   ├──▶ [007_validator]  assert_body_intact(raw_text, items)
   │       word-multiset coverage ratio  →  BodyLossError if < 80%
   │
   ▼
[002_translator]  (optional)  Google / Agent translation
   │
   ▼
[004_excel_generator]  Excel workbook
        ID | Chapter | Section | Source | English | <your language>
```

### Key invariants

1. Body coverage from `raw_text` into `items['content']` **must never fall below 80%** (hard threshold).
2. Every page is marked with a `__PAGE_N__` sentinel so page attribution survives header stripping.
3. Every requirement row carries a full `hierarchy_path` (e.g. `1 Sistemas > 1.2 MDC > 1.2.1 Condições Gerais`).

---

## 8. Project Structure

```
DIaT/
├── 001_text_splitter/
│   └── text_splitter.py        # ChapterSectionParser (12 numbering schemes, stack-based 5-depth tree) + SentenceSegmenter
├── 002_translator/
│   └── translator.py           # TranslationService (Google + Agent) + localized header/title helpers
├── 003_pdf_extractor/
│   └── pdf_extractor.py        # 4-strategy merge extraction + repeating-block stripper + OCR fallback
├── 004_excel_generator/
│   └── excel_generator.py      # single-sheet Excel output (localized headers; English + one user language)
├── 005_main/
│   └── main.py                 # CLI entry point + pipeline orchestration + agent queue writer
├── 006_config/
│   └── config.py               # global config + ABBR tables + DO_NOT_TRANSLATE categories + VALIDATION thresholds
├── 007_validator/
│   └── validator.py            # assert_body_intact — body-survival check
├── sample doc/                 # example PDFs (multi-language) for testing
├── output/                     # generated Excel + JSON intermediates (git-ignored)
├── requirements.txt            # pinned runtime dependencies
├── requirements-optional.txt   # pysbd + ocrmypdf (better segmentation, scanned-PDF OCR)
├── docs/
│   ├── README_zh.md            # user-facing docs (Chinese)
│   ├── README_pt.md            # user-facing docs (Português)
│   ├── README_es.md            # user-facing docs (Español)
│   ├── README_fr.md            # user-facing docs (Français)
│   ├── README_de.md            # user-facing docs (Deutsch)
│   └── README_ja.md            # user-facing docs (日本語)
├── README.md                   # this file — user-facing docs (English)
├── AGENT_GUIDE.md              # orchestrator / sub-agent usage principles
└── LICENSE                     # project license
```

---

## 9. CLI Arguments

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

## 10. Interactive Flow — Example Session

```
$ PYTHONIOENCODING=utf-8 python 005_main/main.py example.pdf

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

## 11. Body-Preservation Guarantee

Silent body loss is **intolerable** — `007_validator` runs unconditionally before the Excel is generated:

1. Walk `raw_text` line by line, skipping header/footer/toc rows → produce `body_lines`.
2. Normalize each `item['content']` into a word multiset.
3. Greedy match: `coverage = Σ covered_words / Σ body_words`.
4. Coverage `< 80%` → raise `BodyLossError`, **halt the pipeline, no Excel is emitted**.
5. Uncovered lines are written to `{prefix}_orphans.json` for triage.

Lexical normalization folds all whitespace to a single space before splitting into tokens, so pdfplumber-driven line-break indentation differences are not miscounted as body loss.

The thresholds live in `006_config/config.py::VALIDATION`:

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

## 12. Proper-Noun Protection

Before translation, the following term classes are replaced by placeholders
`__PROPER_<uuid>__` so that Google Translate leaves them untouched, and are
restored afterwards:

`006_config/config.py::DO_NOT_TRANSLATE` is a **categorized dictionary**
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

## 13. Translation Engines — Google vs. Agent

DIaT offers two interchangeable translation engines selectable with
`-e google` (default) or `-e agent`.  Both feed the same Excel layout, both
respect the same proper-noun protection, and both are validated by the same
body-survival check.  They differ in *who* translates and *how*.

### How they work

| | Google Translate (`-e google`) | Agent / Claude (`-e agent`) |
|---|---|---|
| **Executor** | Google Translate API, called chunk-by-chunk from `TranslationService._translate_with_google` | The AI agent (Claude) reads a JSON queue and writes translations back |
| **Handshake** | Direct, in-process | `main.py` writes `*_agent_queue.json` (source language, target languages, requirements, `extra_do_not_translate`) → agent translates → agent calls `write_translations_to_excel()` |
| **Context window** | One chunk at a time (≤ 4 500 chars); no memory across requirements | The whole queue is available; the agent can enforce terminology consistency across requirements and carry context from earlier items |
| **Network** | Needs access to the Google Translate endpoint (direct or overseas proxy) | Only needs the Claude API — Google endpoints are never touched |
| **Speed (per 100 requirements)** | Seconds — fast, I/O-bound | Minutes — each item is a separate reasoning pass |
| **Cost** | Free (rate-limited) | Consumes Claude API tokens |

### Pros and cons

#### Google Translate (`-e google`)

**Pros**
- **Fast** — high throughput; ideal for a quick first pass or a large batch of
  documents where "good enough" is acceptable.
- **No token cost** — the Translate API is free (within rate limits).
- **Predictable quality** — for common language pairs (pt/en, en/es, en/zh)
  general prose is fluent.

**Cons**
- **Chunked, context-free** — each ≤ 4 500-char chunk is translated in
  isolation, so a requirement split across a chunk boundary loses
  cross-sentence reference.
- **Weaker on dense technical prose** — long specifications with nested
  clauses, cross-references, and terse tabular statements can come back
  garbled or under-translated (the coverage check may then refuse to emit).
- **Proper-noun brittleness** — without the placeholder pass, acronyms like
  `MDC`, `AMI`, `HPLC` are routinely lower-cased or transliterated; the
  placeholder protection mitigates this but is not foolproof for unseen
  acronyms.
- **Needs outbound network** — unusable from a locked-down CI host that only
  reaches the Claude API.

#### Agent / Claude (`-e agent`)

**Pros**
- **Context-aware** — Claude sees the whole requirement and, where needed,
  the surrounding queue, so it keeps terminology consistent (`MDC` stays
  `MDC`, `last-gasp` is interpreted in the metering sense) and handles
  nested clauses cleanly.
- **Best for dense, short, technical prose** — exactly the shape of
  requirements extracted from specifications; produces human-grade output.
- **No Google dependency** — works where only the Claude API is reachable.
- **Self-consistent** — the agent can reuse the same translation of a
  repeated phrase across the whole document, which chunked Google Translate
  may render differently each time.

**Cons**
- **Slower** — each requirement is one reasoning pass; a 400-item document
  takes several minutes.  The script mitigates this by batching the queue
  and parallelizing agent turns where possible.
- **Token cost** — billed per 1 000 tokens; large documents are noticeably
  more expensive than the free Google path.
- **Variable on long, fluent prose** — for running narrative paragraphs
  (rare in requirement lists), a fluent engine can occasionally "improve"
  the wording instead of translating faithfully; the body-survival check
  catches content loss but not stylistic drift.

### How to choose

| Situation | Recommended engine |
|---|---|
| Quick preview, large batch, fluent prose | `-e google` |
| Dense technical specs, terminology consistency matters | `-e agent` |
| Locked-down network (only Claude API reachable) | `-e agent` |
| Second pass to clean up a Google draft | run Google first, then Agent on the queue |

> **Note**: in Agent mode the `extra_do_not_translate` list is likewise applied;
> the agent substitutes the same `__PROPER_<uuid>__` placeholders before
> translation (the same `_protect_proper_nouns` / `_restore_proper_nouns`
> contract the Google path uses), so protection behaviour is identical across
> engines.

---

## 14. Output Format

Excel worksheet column definition (sheet title and headers localized to the
non-English target language):

| Column | Field | Description |
|--------|-------|-------------|
| A | ID | REQ-0001, incrementing |
| B | Chapter | Top-level chapter number + title |
| C | Section | Sub-chapter number + title |
| D | Source | Full sentence in the source language |
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

## 15. Roadmap

- [ ] Allow specifying the source language on the CLI (skip auto-detection)
- [ ] Add docx / odt output formats
- [ ] Improve the multi-paragraph merge strategy (currently sentence-based)
- [ ] Broader adaptation to official documents in other languages
- [ ] Incremental processing: extract deltas between two revisions of the same PDF

---

## 16. License & Attribution

© **Aggre-Cloud 聚云科技** — <https://www.acdatech.com>

Developed and maintained by Aggre-Cloud (聚云科技).
