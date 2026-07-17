# DIaT

> 结构化需求提取与翻译工具 — 从 PDF 文档中提取层级化需求，按结构拆分并翻译，
> 输出 Excel 报表。

语言：**中文**（本文件） · **English** → [`README.md`](README.md)

---

## 1. DIaT 是什么？—— 项目背景

### 它解决什么问题

国际工程、能源、基础设施项目每天都会产生**多语言、结构化的 PDF 文档**
—— 招投标文件、技术规格书、合同、法规、标准。 这些文档有一个共同特征：

- **层级编号**：章 → 节 → 条 → 款 → 项，常混用 `Art. 1º`、`CAPÍTULO`、
  `1.2.1`、`（1）`、`(a)`、罗马数字、带圈数字等多种编号样式。
- **多语言**：葡萄牙语规格书服务于中资项目、阿拉伯语标书由德国承包商评审、
  俄语运维计划给巴西团队阅读。
- **版式复杂**：多栏文本、内嵌表格、重复页眉页脚，严重时甚至是扫描件。

对项目工程师、采购员、技术审核员来说，真正的工作是：*"把每条需求提取出来，
标注它属于哪个章节，并翻译成我能读懂的语言。"* 手工做这件事慢、容易出错，
更无法批量处理整个文件夹的文档。

### DIaT 做了什么

**DIaT**（项目代号）把这样一份 PDF 变成一份带翻译的结构化 Excel，一条命令搞定：

1. **提取** — 用 4 策略融合（layout → words → tables → chars）还原 PDF 正文，
   自动剥离页眉页脚，并对扫描件做 OCR 回退。
2. **分解** — 按文档的章节结构层级化拆解为独立需求，保留每条需求的章节路径。
3. **断句** — 按源语言（pt / en / zh / ja / ko / es / fr / de / …）的最佳实践切分句子。
4. **翻译** — 把每条需求翻译成两种语言——英文固定为一列，你再选一种。
5. **校验** — 强制检查正文没有被丢弃（覆盖率 < 80% 直接终止，绝不输出残缺结果）。
6. **输出** — Excel 报表：`ID / 章 / 节 / 需求原文 / English / <你选的语言>`。

### 适合谁用

- 需要处理多语言规格书、标书的项目工程师与采购人员。
- 需要基于文档结构做第一轮机翻的技术翻译人员。
- 需要把每条需求追溯到原文章节的合规 / 质检审核人员。
- 需要确定性、可自检的文档处理工具的 AI agent 编排流程。

---

## 2. 怎么用 —— 推荐方式

### ▶ 推荐方式：交互模式（直接跑）

最简单、最推荐的用法是**交互运行**，让脚本引导你。你只需要回答三个问题，
其余全自动：

```bash
# 进入项目根目录
cd "<项目根目录>"

# 直接运行 —— 脚本会依次问你 3 个问题，然后输出 Excel
PYTHONIOENCODING=utf-8 python 005_main/main.py "你的文件.pdf"
```

依次会问你：

| # | 问题 | 默认值 |
|---|------|--------|
| (a) | **选一种非英语目标语言** —— 英文 `en` 始终是一个目标，你只需选第二种 | `zh-cn`（简体中文）|
| (b) | **选翻译引擎** — `google`（Google 翻译API）或 `agent`（Claude 自行翻译）| `google` |
| (c) | **补充专有名词**（按类别：人名、项目代号、公司名……）— 或直接回车跳过 | 无（使用内置 ~30 条通用种子词）|

回答完毕后，流水线自动运行，Excel 输出到 `output/<你的文件>_requirements.xlsx`。

> **提示：** 如果自动检测到的源语言与某个目标语言相同，该列会自动保留原文，
> 不会重复调用翻译 API。

### ▶ 非交互模式（批量 / CI / 显式传参）

如果已经确定所有选择、不想看提示，直接传 flag：

```bash
# 英文 + 日文，Google，非交互
PYTHONIOENCODING=utf-8 python 005_main/main.py "你的文件.pdf" \
    -l ja -e google --no-input

# 英文 + 中文，Agent 模式，非交互
PYTHONIOENCODING=utf-8 python 005_main/main.py "你的文件.pdf" \
    -l zh-cn -e agent --no-input

# 仅提取 + 拆分 + 输出 Excel，不翻译
PYTHONIOENCODING=utf-8 python 005_main/main.py "你的文件.pdf" \
    --no-translate --json --no-input

# 批量处理整个目录（非交互）
PYTHONIOENCODING=utf-8 python 005_main/main.py ./pdfs --no-input
```

> **注意：** 英文 (`en`) 会自动加入——`-l` 只接受**非英语**语言码。传 `-l en`
> 会收到明确提示并被拒绝。

### ▶ Agent / 自动运行（先装依赖）

AI agent 运行 DIaT 时，环境里可能还没有依赖。脚本会从项目自带的
`requirements.txt` 自动安装，无需人工介入：

```bash
# 1. （可选）自动安装缺包 —— 非 TTY 下不弹窗。
#    如果已执行过 `pip install -r requirements.txt` 可跳过。
python -m 005_main.main --install-deps

# 2. 同时安装可选增强包
python -m 005_main.main --install-deps --with-optional

# 3. 运行实际流水线
python -m 005_main.main "你的文件.pdf" -l ja -e google --no-input
```

### ▶ 人工手动安装（一条命令）

```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt   # 可选：更好的断句 + 扫描件 OCR
```

---

## 3. 安装 Skill 到 Agent & 指挥 Agent 启动任务

### 安装 skill 到 agent 中

DIaT 是一个纯 Python 项目——所谓「安装 skill」，就是把项目文件夹放到 agent
能访问到的地方，让它可以运行 `005_main/main.py`。

1. **克隆仓库**到 agent 所在机器（或你自己的机器）上的一个固定位置：
   ```bash
   git clone https://github.com/Aggre-Cloud/DIAT.git
   cd DIaT
   ```
2. **一次性安装依赖**（agent 也能通过 `--install-deps` 自动安装，但手动装更快）：
   ```bash
   pip install -r requirements.txt
   ```
3. **告诉 agent 项目根目录路径**。无需注册或配置文件——需要处理 PDF 时，
   把项目根目录的绝对路径和输入文件一起告诉 agent：

   ```
   用 DIaT 处理这份 PDF：
     项目路径 → D:/Tool Development/Skills Development/DIaT
     输入文件 → D:/.../my-spec.pdf
   ```

整个「安装」过程就是克隆仓库 + 一条 `pip install`。

### 指挥 agent 开始工作

项目已在 agent 磁盘上并装好依赖后，用一句简短的指令即可调用。Agent 已从
`AGENT_GUIDE.md` 了解该 skill；你只需要说明文档路径和（如果有）非默认选择。
常用示例：

| 你给 agent 的指令 | agent 的行为 |
|---|---|
| `用 DIaT 处理 02.pdf` | 交互运行 —— 询问语言 / 引擎 / 专有名词，再生成 Excel |
| `用 DIaT 处理 02.pdf，目标语言 ja，Google，不要问` | 非交互：`-l ja -e google --no-input` |
| `把 spec.pdf 条目化成 Excel，不翻译` | 仅提取 + 拆分 + 输出 Excel：`--no-translate --json --no-input` |
| `批量处理 ./pdfs 全部，zh-cn，agent 翻译` | 对目录做 Agent 模式批量处理（`-e agent`） |

**推荐做法：** 指令尽量简洁，让 agent 走三步提示（语言 / 引擎 / 专有名词）——
这是最稳妥的路径，也能让你了解工具的能力。只有在你明确想跳过提示时，才指定
`-l` / `-e` / `--no-input` 等 flag。

---

## 4. Agent 执行规范 —— Agent 应如何推荐

当 AI agent 代替用户运行 DIaT 时，**推荐行为**是：

1. **默认交互模式。** 不要擅自替用户传 `--no-input` —— 只在用户明确要求
   非交互 / 批量 / 全自动时才传。
2. **执行前先问用户 (a) / (b) / (c) 三个问题**，即使 CLI flag 能提供默认值。
   这是项目强制的前置检查清单（详见 `AGENT_GUIDE.md §2`）。
3. **把交互路径**（`python 005_main/main.py "文件.pdf"`）**作为首要推荐**
   —— 这是最不容易出错的方式，也能让用户了解工具的能力。
4. **首次运行前检查依赖**：如发现缺包，先调用 `--install-deps` 再重跑。

这个工具归根结底是**给人用的** —— agent 的职责是让用户面前出现那三个提示，
而不是默默替用户做决定。

---

## 5. 依赖清单

| 包 | 是否必需 | 用途 |
|----|----------|------|
| `openpyxl` | 必需 | Excel 工作簿读写 |
| `pdfplumber` | 必需 | PDF 文本提取（4 策略融合）|
| `PyPDF2` | 必需 | PDF 页面探测 / 元数据 |
| `pypdfium2` | 必需 | PDF 渲染 / 页面图像 |
| `googletrans` | 必需 | Google 翻译引擎（仅 `-e google` 时）|
| `pysbd` | 可选 | 按源语言断句（缺失则用内置正则 fallback）|
| `ocrmypdf` | 可选 | 扫描件 OCR 回退（需系统 tesseract + ghostscript）|

---

## 6. 能力边界

### ✅ 支持

| 维度 | 范围 |
|------|------|
| 输入 | 单 PDF 文件，或 PDF 所在目录（批量）|
| 结构类型 | 带层级编号的文档（合同、规格书、法规、标书、标准等）|
| 页眉/页脚 | 自动探测重复块（≥ 75% 页出现）并剥离 |
| 扫描件 | 探测后调用 `ocrmypdf --language <config>` 做 OCR 回退（lazy import，非硬依赖）|
| 层级标记 | `Art. 1º` / `CAPÍTULO` / `SEÇÃO` / `§ 1º` / `I.` / `1.` / `1.2` / `1.2.1` / `（1）` / `(a)` / `•` / `(1)` / 罗马数字 / 带圈数字 |
| 源语言 | pysbd (可选) + 内置正则 fallback；pt / en / es / fr / de / zh / ja / ko 均有专属断句规则 |
| 目标语言 | 英文（固定）+ 用户选的一种（任意 googletrans / Claude 语言码）|
| 翻译引擎 | Google Translate（直连）或 Agent（Claude 自行翻译）|
| 专有名词保护 | 占位符替换（内置通用 ~30 条 + 用户交互补充），翻译后还原 |
| 输出格式 | Excel 工作簿（ID / 章 / 节 / 原文 / English / <你选的语言>）|
| 正文校验 | 强制覆盖率检查，< 80% 终止流程不输出 |
| 标题保留 | 标题行始终作为每条需求正文的一部分输出（供覆盖率校验 + 上下文追溯）；空正文标题行自动合成 |
| 默认交互 | 默认进入交互模式，依次询问用户目标语言 / 翻译引擎 / 专有名词补充；仅当用户明确要求或传入 `--no-input` 才跳过 |
| 表格行过滤 | D1/D2/D3 标题匹配时拒绝含 `;`（单元格分隔符）、`(`（单位注释）、尾部" - 短词"（标签/值对）、或含数字的行，避免把 PDF 表格行误识别为章节标题 |

### ⚠️ 使用前提

- PDF 须为 **可选取文本** 的数字版，或扫描分辨率 ≥ 200 dpi
- 须能访问 Google Translate API（直连或境外代理），除非使用 Agent 模式
- 运行环境：Python 3.9+；依赖见 §4
- 大文件（> 100 页）处理时间会显著增长；OCR 回退每页约 1-5 秒

---

## 7. 架构 / 流水线

```
PDF 文件
   │
   ▼
[003_pdf_extractor]  extract_with_meta()
   │  4 策略融合：layout → words → tables → chars   (fallback cascading)
   │  重复块剥离 + __PAGE_N__ 哨兵
   │  扫描件探测 → ocrmypdf → 重新打开
   ▼
raw_text  +  ExtractionMeta
   │
   ▼
[001_text_splitter]  parse_text(raw_text, lang)
   │  ChapterSectionParser  — 优先顺序正则 + 栈式构造
   │  SentenceSegmenter     — 按源语言最佳实践
   ▼
ParseResult  { roots, items, meta, raw_rows }
   │
   ├──▶ [007_validator]  assert_body_intact(raw_text, items)
   │       词多重集合覆盖率  →  < 80% 抛 BodyLossError
   │
   ▼
[002_translator]  (可选)  Google / Agent 翻译
   │
   ▼
[005_excel_generator]  Excel 工作簿
        ID | 章 | 节 | 需求原文 | English | <你选的语言>
```

### 关键不变式

1. `raw_text` 到 `items['content']` 的正文覆盖率 **不得低于 80%**（硬阈值）。
2. 每页以 `__PAGE_N__` 哨兵标记，确保页码归属性在剥离页眉后仍可恢复。
3. 每个需求行包含完整 `hierarchy_path`（如 `1 Sistemas > 1.2 MDC > 1.2.1 Condições Gerais`）。

---

## 8. 项目结构

```
DIaT/
├── 006_config/
│   └── config.py               # 全局配置 + 语言缩写表 + VALIDATION 阈值
├── 003_pdf_extractor/
│   └── pdf_extractor.py        # 4 策略融合提取 + 重复块剥离 + OCR 回退
├── 001_text_splitter/
│   └── text_splitter.py        # ChapterSectionParser + SentenceSegmenter
├── 005_excel_generator/
│   └── excel_generator.py      # Excel 输出（表头本地化；英文 + 一种用户语言）
├── 007_validator/
│   └── validator.py            # assert_body_intact — 正文存活校验
├── 002_translator/
│   └── translator.py           # TranslationService (Google + Agent)
├── 005_main/
│   └── main.py                 # CLI 入口 + 流程编排
├── sample doc/                 # 多语言示例 PDF（供测试）
├── README.md                   # 面向用户的说明（English）
├── README_zh.md                # 面向用户的说明（中文，本文件）
└── AGENT_GUIDE.md              # 面向 orchestrator / sub-agent 的使用原则
```

---

## 9. CLI 参数

| 参数 | 说明 |
|------|------|
| `input` | PDF 文件或目录路径 |
| `-o, --output` | 输出目录（默认 `output/`）|
| `--no-translate` | 跳过翻译 |
| `--json` | 额外输出 JSON 中间产物 |
| `-l, --lang` | 非英语目标语言（如 `pt`、`ja`），英文自动加入 |
| `-e, --engine` | 翻译引擎 `google`（默认）或 `agent` |
| `--no-input` | **显式** 非交互模式（en + zh-cn + Google）。默认行为是交互模式，仅当用户明确要求时才传此参数 |
| `--display-lang` | 覆盖 Excel 表表头 / 工作表名语言（默认：非英语目标语言）|
| `--install-deps` | 从 `requirements.txt` 安装缺包随后退出。非 TTY（agent / 管道）下不弹窗；TTY 下询问确认 |
| `--with-optional` | 配合 `--install-deps`，同时安装可选增强包（`pysbd`、`ocrmypdf`）|

### 翻译语言选择规则

1. **英文始终是目标** —— 你只需选第二种语言。
2. **同源语言不翻译** —— 若源语言与某目标语言相同，该列保留原文（不调用 API）。
3. **表头本地化** —— Excel 静态表头、列表头、工作表名按非英语目标语言渲染
   （如 `en + ja` → 工作表 `要求事項`，表头 `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`），
   不混用语言。

---

## 10. 交互流程 —— 示例

```
$ PYTHONIOENCODING=utf-8 python 005_main/main.py example.pdf

  =======================================================
    目标翻译语言选择 / Target Language Selection
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
    翻译引擎选择 / Translation Engine
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    1. Google Translate API   (default — fast, external)
    2. Agent  — Claude reads JSON, translates, writes back

  Enter 1 or 2 (or press Enter for default Google): 1

  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    专有名词保护 / Proper-Noun Protection
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
  → [产品/项目代号] 当前为空
    输入逗号分隔词追加 (Enter 跳过): SCADA,AMI,MDM,MDC
    + added 4 term(s)。

  请选择类别编号 (1-10 补充, 0=完成): 0
  ✓ 专有名词保护配置完成。共 1 个类别，4 个术语。

  [3/4] Translating (engine=google, languages=['en', 'pt'])...
  ...

  [OK] Completed!
  [OK] Output file: output/example_requirements.xlsx
  [OK] Total requirements: 393
  [OK] Valid requirements: 393 (100.0%)
  [OK] Body coverage: 100.7%
```

---

## 11. 正文不丢弃规范

> **正文被丢弃现象，这点是绝对不可容忍的。**

`007_validator` 在 Excel 生成前强制执行：

1. 把 `raw_text` 按行遍历，跳过页眉/页脚/目录行，得到 `body_lines`。
2. 把每个 `item['content']` 归一化为词的多重集合（multiset）。
3. 贪心比对：`coverage = Σ covered_words / Σ body_words`。
4. 覆盖率 `< 80%` → 抛 `BodyLossError`，**终止流程，不输出 Excel**。
5. 未覆盖行写入 `{prefix}_orphans.json` 供排查。

词法归一化规则：将所有空白字符折叠为一个空格，再 split 为词元。这保证了 pdfplumber 的断行缩进差异不会误计为正文丢失。

阈值可在 `006_config/config.py::VALIDATION` 中调整：

```python
VALIDATION = {
    'min_char_coverage': 0.80,   # 最低正文覆盖率
    'min_word_coverage': 0.85,
    'write_orphans': True,
    'sentence_target_min': 50,    # 单句最短字符数
    'sentence_target_max': 500,   # 单句最长字符数
}
```

---

## 12. 专有名词保护

翻译前，以下词类会被占位符 `__PROPER_<uuid>__` 替换，使 Google
Translate 保持其原样，翻译完成后再还原：

`006_config/config.py::DO_NOT_TRANSLATE` 是**分类词典**（`category → {label, items}`），
内置种子只放**跨行业通用术语**（~30 条），按类别组织：

- 技术缩略语（API、HTTP、HTTPS、JSON、XML、CSV、TCP、UDP、IP、SSH、…）
- 国际标准组织（IEC、IEEE、ISO、ITU、ANSI、IETF、W3C）
- 网络 / 基础设施（RF、PLC、LAN、WAN、HAN）
- 计量单位（GWh、MWh、kWh、Hz、kV、kW、kVA、MVA、ms、s）
- 通用公司 / 产品名（Google、Microsoft、Amazon、Apple）

以下为**空类别**，在交互步骤 (c) 中按本文档实际情况逐一补充：
人名、地名、产品/项目代号、公司名（本文档）、监管机构、法规/文档编号、
行业专有术语、岗位/职责，并可在运行时**新建任意类别**。

> 类别集合是**开放**的：行业特定术语（如电力的 `SCADA/AMI/MDM/MDC`、医疗的
> 药品名、法律的法院名）不属于版本化种子，而是用户在处理具体文档时按对应
> 类别补充——这是工具跨行业泛化的核心机制。

**实现机制**（`002_translator/translator.py`）：

```text
原文
  │
  ▼
_protect_proper_nouns()        ← 用占位符替换 DO_NOT_TRANSLATE 词
  │
  ▼
Google Translate API
  │
  ▼
_restore_proper_nouns()        ← 把占位符还原为原词
  │
  ▼
译文
```

词表按长度降序排列，确保 `Advanced Metering` 优先于 `AMI` 被匹配。

---

## 13. Agent 模式

Agent 模式下，脚本**不调用 Google Translate**，而是：

1. 写 `*_agent_queue.json`（含 `source_language`、`target_languages`、
   `requirements`、`extra_do_not_translate`）
2. Agent（Claude）读取 JSON，逐条翻译
3. Agent 调用 `write_translations_to_excel()` 回写 Excel

**适用场景**：

- Google Translate 不可用（网络限制）
- 需要更高质量的翻译（Claude 理解上下文）
- 需要保持术语一致性（Claude 可参考全文）

**注意**：Agent 模式下，`extra_do_not_translate` 列表同样生效，
agent 在翻译前必须用占位符替换这些词（与 Google 路径相同的
`_protect_proper_nouns` / `_restore_proper_nouns` 模式）。

---

## 14. 输出格式

Excel 工作表列定义（工作表名与表头按非英语目标语言本地化）：

| 列 | 字段 | 说明 |
|----|------|------|
| A | ID | REQ-0001 起递增 |
| B | 章 (Chapter) | 顶层章节号 + 标题 |
| C | 节 (Section) | 子章节号 + 标题 |
| D | 需求原文 (Source) | 源语言完整句 |
| E | English 翻译 | 始终存在 |
| F | <你选的语言> 翻译 | 用户选的语言 |

- 目标语言为 `en` + 另一种语言时，静态表头 + 工作表名以该语言渲染
  ——如 `en + ja` → 工作表 `要求事項`，表头 `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`，
  不混用语言。
- 若源语言匹配某目标语言，该列保留原文（不调用 API）。
- 列宽：`[10, 32, 32, 65, 65]`。
- 可用 `--display-lang <code>` 覆盖表头语言。

---

## 15. 后续方向 / Roadmap

- [ ] 支持命令行指定源语言（跳过自动检测）
- [ ] 引入 docx / odt 输出格式
- [ ] 多段落合并策略优化（当前按句切分）
- [ ] 对其他语种官方文档的泛化适配
- [ ] 增量处理：同一 PDF 修订版差异提取

---

## 16. License & Attribution

© **Aggre-Cloud 聚云科技** — <https://www.acdatech.com>

本工具由 Aggre-Cloud 聚云科技 开发并维护。
