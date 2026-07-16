# DIaT — Agent Guide

> Agent-facing documentation for the generic PDF-requirement extraction
> and translation skill.  The human-facing counterpart is `README.md`.

---

## 1. Purpose (One-Liner)

This skill converts a **structured, multi-language PDF** into a
hierarchical Excel workbook of requirements, each translated into
**two user-selected target languages** — while **guaranteeing no body
text is silently dropped** and **protecting proper nouns** from
translation.

---

## 2. Before You Run — Mandatory Checklist

You **MUST** ask the user (in this order) before executing a run.
Even if the CLI flags supply defaults, the interactive flow must
always prompt the user explicitly:

| # | Question | Default |
|---|----------|---------|
| (a) | **Pick ONE non-English target language** — English (`en`) is always a target by default; you only choose the *second* language. Excel will have two translation columns: English + your pick | `zh-cn` (Simplified Chinese) |
| (b) | **Pick translation engine** — `google` (Translate API) or `agent` (Claude self-translates via JSON queue) | `google` |
| (c) | **Review / add proper-noun terms** by **category** — the prompt shows each category's existing seeds and lets you fill: person name, place name, product/project code, company (this document), regulatory body, legal/doc reference, industry-specific term, role/title, plus a "new category" entry for anything else | none (use the built-in ~30-term generic seed list) |

**Source-language match rule (automatic):** If the auto-detected
source language equals one of the chosen targets, that column keeps
the original text — no translation API call needed.  You do **not**
need to ask the user about this; the pipeline handles it internally.

### 2b. Default Interactive Behavior

**Default = interactive. Always.**

- `006_main/main.py` only enters non-interactive mode when the `--no-input`
  CLI flag is **explicitly passed**.
- **As the orchestrating agent, you MUST NOT pass `--no-input` on behalf
  of the user.**  Only pass it when the user explicitly tells you they want
  a non-interactive run (e.g. "don't ask me anything", "batch mode",
  "fully automated").  If the user is silent on this, run interactively.
- This matches the invariant in §3.2: prompts (a) / (b) / (c) must fire
  every time unless `--no-input` is explicitly set.

> **Critical:** Skipping any of (a) / (b) / (c) in interactive mode is
> **forbidden**.  The `--no-input` flag is the only legitimate way to
> bypass prompts, and it implies the defaults above.

### 2c. Dependency Bootstrap (Auto-Install)

The pipeline depends on the packages listed in
`006_main/main.py::REQUIRED_PACKAGES` (mirrored in the project
`requirements.txt`).  **Before any run, ensure they are importable.**

**Agent path (automatic, no human in the loop):**

```bash
# 1. Self-install missing packages from requirements.txt, then exit.
PYTHONIOENCODING=utf-8 python -m 006_main.main --install-deps

# 2. (Optional) also install optional extras (pysbd, ocrmypdf).
PYTHONIOENCODING=utf-8 python -m 006_main.main --install-deps --with-optional

# 3. Run the actual pipeline.
PYTHONIOENCODING=utf-8 python -m 006_main.main "<file.pdf>" --no-input
```

`--install-deps` detects a non-TTY (agent / pipe) and installs without
prompting.  It exits after install, so it is always followed by a real run.

**Human path (manual, one command):**

```bash
# Install everything the project ships (pinned versions).
pip install -r requirements.txt

# Optional extras (better segmentation + scanned-PDF OCR).
pip install -r requirements-optional.txt

# Run (interactive by default).
PYTHONIOENCODING=utf-8 python 006_main/main.py "<file.pdf>"
```

If a human runs the script without installing first and a package is
missing, the script prints the exact `pip install` command and, in a TTY,
asks whether to install now (opt-in).

**Dependency contract**

| Package | Required? | Why |
|---------|-----------|-----|
| `openpyxl` | required | Excel workbook read/write |
| `pdfplumber` | required | PDF text extraction (4-strategy merge) |
| `PyPDF2` | required | PDF page probing / metadata |
| `pypdfium2` | required | PDF rendering / page images |
| `googletrans` | required | Google Translate engine (only when `-e google`) |
| `pysbd` | optional | language-aware sentence segmentation (regex fallback if absent) |
| `ocrmypdf` | optional | OCR fallback for scanned PDFs (needs system tesseract + ghostscript) |

---

## 3. Forbidden Actions — NEVER

The following are **explicitly prohibited** during any run:

1. **NEVER modify source files** during an active run.

   This includes but is not limited to:
   `007_config/config.py`, `002_translator/translator.py`,
   `006_main/main.py`, `001_text_splitter/text_splitter.py`,
   `003_pdf_extractor/pdf_extractor.py`,
   `005_excel_generator/excel_generator.py`,
   `008_validator/validator.py`.

2. **NEVER bypass interactive prompts.**

   Even if CLI flags (`-l`, `-e`, `--no-translate`) already supply all
   needed values, the interactive flow must still ask the user to
   confirm (a), (b), (c).  The only legitimate skip is `--no-input`.

3. **NEVER add or drop Excel columns outside the generator module.**

   Column definitions belong exclusively to
   `005_excel_generator/excel_generator.py` (`static_headers +
   dynamic language columns`).  Do not alter the layout from any other
   module.

4. **NEVER silence `BodyLossError`.**

   If coverage is below the 80 % threshold, the pipeline **must abort
   without writing Excel**.  Swallowing the exception and producing a
   partial output is intolerable.

5. **NEVER feed `DO_NOT_TRANSLATE` terms directly to Google Translate.**

   They **must** be replaced with `__PROPER_<uuid>__` placeholders
   before the API call and restored afterwards
   (`_protect_proper_nouns()` → translate → `_restore_proper_nouns()`).

6. **NEVER call the Google Translate API in Agent mode.**

   Agent mode delegates translation entirely to the orchestrating agent
   (Claude) via the JSON queue.  Making real Google Translate calls in
   that path breaks the contract.

7. **NEVER pass `--no-input` unless the user explicitly asks for it.**

   The skill defaults to interactive mode — target languages, engine, and
   proper-noun prompts must all fire for the user to answer.  Only add
   `--no-input` to the CLI invocation when the user *explicitly* requests
   non-interactive / batch / unattended operation.  Never add it merely
   because you already happen to know sensible defaults; that is exactly
   the bypass that §2b forbids.

8. **NEVER add runtime terms to `config.DO_NOT_TRANSLATE`.**

   User-supplied extras from step (c) are injected into the live
   `TranslationService.do_not_translate` instance cache (Google path)
   or written into the `*_agent_queue.json` file (Agent path).  Do not
   mutate the module-level config list — that causes cross-run leakage.

---

## 4. Pipeline Responsibility Map

Each file has one owner and one job.  Cross-module calls go only
downward through `main.py`.

| Module | Responsibility | Called by |
|--------|----------------|-----------|
| `003_pdf_extractor/pdf_extractor.py` | PDF → `raw_text` + `ExtractionMeta` (4-strategy merge + header/footer strip + OCR fallback) | `main.py` |
| `001_text_splitter/text_splitter.py` | `raw_text` → hierarchical `items` (章→节→条→款→项) + per-language sentence segmentation | `main.py` |
| `008_validator/validator.py` | Word-multiset body-coverage check → `BodyReport` / `BodyLossError` | `main.py` |
| `002_translator/translator.py` | Translation + proper-noun placeholder protection + language detection | `main.py` |
| `005_excel_generator/excel_generator.py` | `items` → Excel workbook (fixed 4 columns + N language columns) | `main.py` |
| `006_main/main.py` | CLI + orchestration + interactive prompts + JSON queue emit | **user / agent** |

**Key invariants (must never be violated):**

- `raw_text` → `items['content']` coverage **≥ 80 %** (hard threshold).
- Each page is bookended by a `__PAGE_N__` sentinel so page attribution
  survives header stripping.
- Every row carries a full `hierarchy_path` (e.g. `1 Sistemas > 1.2 MDC
  > 1.2.1 Condições Gerais`).

---

## 5. Interactive Flow (Canonical)

The exact prompt sequence when `--no-input` is **not** set:

```
1. user inputs PDF path                          ← CLI
2. extract + split                               ← automatic
3. validate coverage                             ← automatic; abort if < 80 %
4. _ask_target_languages()                       ← prompt (a)
5. _ask_translation_engine()                     ← prompt (b)
6. _ask_do_not_translate_additions()             ← prompt (c) — category-guided
7. translate (Google API or Agent JSON queue)    ← automatic
8. write Excel (.xlsx)                           ← automatic
```

Terminal example:

```
$ PYTHONIOENCODING=utf-8 python 006_main/main.py example.pdf

  === 目标翻译语言选择 / Target Language Selection ===
  Detected source: pt (Português)
  Enter 2 language codes (comma-separated) or Enter for default [en,zh-cn]:

  ~~~ 翻译引擎选择 / Translation Engine ~~~
  Enter 1 or 2 (or press Enter for default Google):

  ~~~~~~ 专有名词保护 / Proper-Noun Protection ~~~~~~
  翻译时下列类别的术语将保持原文不译：
    [技术缩略语]   API, HTTP, HTTPS, JSON, XML, CSV, TCP, UDP, IP, VPN, … (17)
    [国际标准组织] IEC, IEEE, ISO, ITU, ANSI, IETF, W3C                (7)
    [网络/基础设施] RF, PLC, LAN, WAN, HAN                              (5)
    [计量单位]     GWh, MWh, kWh, Hz, kV, kW, kVA, MVA, ms, s        (10)
    [公司/产品名]  Google, Microsoft, Amazon, Apple                     (4)

  以下类别暂无术语或需按本文档补充：
     1. 人名                    6. 监管机构
     2. 地名                    7. 法规/文档编号
     3. 产品/项目代号            8. 行业专有术语
     4. 公司名（本文档）         9. 岗位/职责
    10. ＋ 新建类别…
     0. 完成并继续

  请选择类别编号 (1-10 补充, 0=完成): 3
  → [产品/项目代号 / Product / Project Codes]  当前为空
    输入逗号分隔词追加 (Enter 跳过): SCADA,AMI,MDM,MDC
    + added 4 term(s)。

  请选择类别编号 (1-10 补充, 0=完成): 4
  → [公司名（本文档） / Company (this document)]  当前为空
    输入逗号分隔词追加 (Enter 跳过): CPFL,Enel
    + added 2 term(s)。

  请选择类别编号 (1-10 补充, 0=完成): 0
  ✓ 专有名词保护配置完成。共 2 个类别，6 个术语。

  [3/4] Translating (engine=google, languages=['en', 'zh-cn'])...
  ...

  [4/4] Generating Excel ...

  [OK] Completed!
  [OK] Output file: .../example_requirements.xlsx
  [OK] Total requirements: 42
  [OK] Body coverage: 91.4 %
```

---

## 6. Body-Preservation Guarantee

> **正文被丢弃现象，这点是绝对不可容忍的。**
> (Silently dropping body text is absolutely intolerable.)

`008_validator.assert_body_intact()` runs **before** Excel generation:

1. Walk `raw_text` lines; skip recognised header/footer/TOC lines.
2. Normalise each surviving line to a word-multiset.
3. For every item, consume (decrement) matched words from a shared pool →
   `coverage = Σ covered_chars / Σ body_chars`.
4. If `coverage < 0.80` → raise `BodyLossError` → **abort**.
5. Uncovered lines → written to `{prefix}_orphans.json` for debugging.

Thresholds are configurable in `007_config/config.py::VALIDATION` but
should not be loosened without explicit user request.

---

## 7. Proper-Noun Protection Mechanism

The translator shields two layers of text from Google Translate:

1. **Built-in categorized seeds** (`DO_NOT_TRANSLATE` in
   `007_config/config.py`) — a **category dictionary**, not a flat list.
   Each entry is `{category_key: {label: {en, zh}, items: […]}}`.  Built-in
   seeds carry only **cross-industry generic** terms (technical
   abbreviations like `API/HTTP/JSON`, standards bodies like
   `IEC/IEEE/ISO`, measurement units, generic company names, …).

   The category set is **OPEN**: new categories can be added at run time
   via prompt (c) without touching the config file.  This is how the
   tool stays industry-agnostic — power-sector terms (`SCADA/AMI/MDM/MDC`),
   medical terms, legal citations, etc. belong in per-session
   user-filled categories, not in the versioned seed list.

2. **User-supplied extras** from prompt (c) — collected
   category-by-category as `{category: [term, …]}` and merged into the
   live `TranslationService.do_not_translate` cache via
   `merge_do_not_translate_terms()` (Google path) or written into the
   `extra_do_not_translate` key of the agent JSON queue (Agent path).

**Call sequence (Google path):**

```text
original text
   │
   ▼
_protect_proper_nouns(text)          ← replace terms with __PROPER_<uuid>__
   │
   ▼
Google Translate API
   │
   ▼
_restore_proper_nouns(translated)    ← swap placeholders back
   │
   ▼
translated text
```

Terms are sorted longest-first so `Advanced Metering` matches before `AMI`.

**Agent path:** the placeholder logic is the agent's own
responsibility — the JSON queue lists `extra_do_not_translate`; the
agent must apply the same `__PROPER_<uuid>__` substitute-restore pattern
before/after its own translation pass.

---

## 8. Output Contract

Excel workbook `{pdf_stem}_requirements.xlsx`, sheet name localized to the
**display language** (`Requirements` for English, `需求` for Chinese,
`Requisitos` for Portuguese, … — defaults to the first target language).

| Column | Header (en display) | Header (zh display) | Width |
|--------|---------------------|---------------------|-------|
| A      | ID                  | ID                  | 10    |
| B      | Chapter             | 章                  | 35    |
| C      | Section             | 节                  | 35    |
| D      | Source              | 需求原文            | 65    |
| E      | {lang1} Translation | {lang1}翻译         | 65    |
| F      | {lang2} Translation | {lang2}翻译         | 65    |

- The four static headers (A–D) **and** the per-language headers (E / F)
  are all rendered in the **display language** (default = first target
  language).  An English-targeted sheet reads
  `ID / Chapter / Section / Source / English Translation / Chinese Translation`;
  a Chinese-targeted sheet reads
  `ID / 章 / 节 / 需求原文 / 中文翻译 / 英文翻译`.  No mixed-language headers.
- Columns E / F headers are **dynamic** — determined by the user's two
  target languages (e.g. `英文翻译` + `中文翻译`).
- If source == target for one column, that column keeps the **original
  text** (not an API-translated copy).
- Column count is always `4 + len(target_languages)`.

---

## 9. Error Handling

| Condition | Behaviour | Agent Action |
|-----------|-----------|--------------|
| `coverage < 80 %` | raise `BodyLossError`; **no Excel written** | Show the error + first 5 orphans; do **not** retry with a lower threshold unless the user asks |
| Google Translate failure | returns `''` (empty string), **not** source text | Leave cell blank — do not fill with source text silently |
| Source language == target language | column keeps original text, API **not** called | This is expected — do not warn the user |
| Scanned PDF detected | invoke `ocrmypdf --language por --clean --deskew` (lazy import) | Requires `tesseract` + `ghostscript` on the system; if missing, warn and continue with partial text |
| Agent mode selected | script writes JSON queue, leaves translations blank | Agent **must** read the JSON queue, translate each row, and call `write_translations_to_excel()` (or equivalent) to persist translations |

---

## 10. License & Attribution

© **Aggre-Cloud 聚云科技** — <https://www.acdatech.com>

本工具由 Aggre-Cloud 聚云科技 开发并内部使用。
Developed and maintained by Aggre-Cloud (聚云科技).

---

## 11. Run Protocols — Exact Command Sequences

Two supported ways to run DIaT.  Pick the one that matches your caller.

### 11a. Agent Run (automated, no human interaction)

Use this when the orchestrating agent drives the tool end-to-end.

```bash
# Step 0 — enter the project directory.
cd "<path-to>/DIaT"

# Step 1 — ensure dependencies (auto-installs from requirements.txt,
#          no prompt because stdin is not a TTY).
PYTHONIOENCODING=utf-8 python -m 006_main.main --install-deps

# Step 2 — (optional) install extras for better segmentation / OCR.
PYTHONIOENCODING=utf-8 python -m 006_main.main --install-deps --with-optional

# Step 3 — run the pipeline non-interactively.
#   Google Translate engine:
PYTHONIOENCODING=utf-8 python -m 006_main.main \
    "<file.pdf>" -e google --no-input -l en,zh-cn

#   Agent translation engine (writes JSON queue, agent translates, writes back):
PYTHONIOENCODING=utf-8 python -m 006_main.main \
    "<file.pdf>" -e agent --no-input -l en,zh-cn

# Step 4 — (Agent engine only) read the emitted *_agent_queue.json,
#   translate each row, and call write_translations_to_excel() to persist.
```

**Agent-mode decision table**

| Condition | Action |
|-----------|--------|
| `--install-deps` exits non-zero | Read stderr — it prints the exact `pip` command to retry manually. Do NOT proceed to Step 3. |
| Google engine chosen | Pipeline calls Google Translate directly; no agent translation work needed. |
| Agent engine chosen | Pipeline writes `*_agent_queue.json` and an Excel with blank translation columns. Agent **must** fill them via `write_translations_to_excel()`. |
| `BodyLossError` raised | Abort. Show the error + first 5 orphans. Do NOT retry with a lower threshold unless the user asks. |

### 11b. Human Run (manual, interactive by default)

Use this when a person runs the tool from a terminal.

```bash
# Step 0 — enter the project directory.
cd "<path-to>/DIaT"

# Step 1 — install dependencies ONCE (pinned versions).
pip install -r requirements.txt
# Optional:
pip install -r requirements-optional.txt

# Step 2 — run interactively (prompts for language / engine / proper nouns).
PYTHONIOENCODING=utf-8 python 006_main/main.py "<file.pdf>"

# Step 2-alt — non-interactive (skips prompts, uses en + zh-cn + Google).
PYTHONIOENCODING=utf-8 python 006_main/main.py "<file.pdf>" --no-input

# Step 2-alt — Google engine, explicit languages, non-interactive.
PYTHONIOENCODING=utf-8 python 006_main/main.py \
    "<file.pdf>" -e google --no-input -l en,zh-cn
```

**Human-mode decision table**

| Condition | Action |
|-----------|--------|
| Script prints "missing required packages" | Run `pip install -r requirements.txt` (or answer `Y` to the in-TTY prompt) and re-run. |
| Forgot to install first | Same as above — the script tells you exactly what to run. |
| Want to change target languages | Re-run with `-l <codes>` or run interactively and pick at the prompt. |
| Want Agent mode | Add `-e agent --no-input`; then translate the JSON queue yourself or hand it to an agent. |

### 11c. Quick-Reference Card

```
┌──────────────────────────────────────────────────────────────────┐
│  DIaT — how to run                                              │
│                                                                  │
│  Human (one-time setup):                                         │
│      pip install -r requirements.txt                             │
│                                                                  │
│  Human (interactive):                                            │
│      python 006_main/main.py <file.pdf>                          │
│                                                                  │
│  Human (non-interactive):                                        │
│      python 006_main/main.py <file.pdf> --no-input               │
│                                                                  │
│  Agent (auto-install + run):                                     │
│      python -m 006_main.main --install-deps                      │
│      python -m 006_main.main <file.pdf> --no-input -e google     │
│                                                                  │
│  Optional extras (better segmentation + OCR):                    │
│      pip install -r requirements-optional.txt                    │
└──────────────────────────────────────────────────────────────────┘
```
