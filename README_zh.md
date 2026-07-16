# DIaT

> 需求拆分与翻译工具 — 从 PDF 文档中提取层级化需求，按结构拆分并翻译，输出 Excel 报表。

语言文档：**中文**（本文件） · **English** → [`README.md`](README.md)

---

## 1. 作用

本工具面向 **多语言、结构化的 PDF 文档** 的典型工作流：

- **提取** — 从多栏、多表格、含重复页眉/页脚的 PDF 中还原正文文本（4 策略融合 + 扫描件 OCR 回退）
- **拆分** — 按文档章节结构（章 → 节 → 条 → 款 → 项）层级化分解为独立需求
- **断句** — 按源语言（pt / en / zh / ja / ko / es / fr / de / …）硬编码的最佳实践进行句级切分
- **翻译** — 调用 Google Translate 或 Agent 模式完成多语言翻译
- **校验** — 强制正文覆盖率校验（< 80% 即报错，绝不丢弃正文）
- **输出** — Excel 报表（ID / 章 / 节 / 需求原文 / 各语言翻译列）

---

## 2. 能力边界

### ✅ 支持

| 维度 | 范围 |
|------|------|
| 输入 | 单 PDF 文件，或 PDF 所在目录（批量） |
| 结构类型 | 带层级编号的文档（合同、规格书、法规、标书、标准等）|
| 页眉/页脚 | 自动探测重复块（≥ 75% 页出现）并剥离 |
| 扫描件 | 探测后调用 `ocrmypdf --language <config>` 做 OCR 回退（lazy import，非硬依赖）|
| 层级标记 | `Art. 1º` / `CAPÍTULO` / `SEÇÃO` / `§ 1º` / `I.` / `1.` / `1.2` / `1.2.1` / `（1）` / `(a)` / `•` / `(1)` / 罗马数字 / 带圈数字 |
| 源语言 | pysbd (可选) + 内置正则 fallback；pt / en / es / fr / de / zh / ja / ko 均有专属断句规则 |
| 目标语言 | 任意 googletrans / Claude 支持的语言码（每次输出 2 列）|
| 翻译引擎 | Google Translate（直连）或 Agent（Claude 自行翻译）|
| 专有名词保护 | 占位符替换（内置通用 ~30 条 + 用户交互补充），翻译后还原 |
| 输出格式 | Excel 工作簿（ID / 章 / 节 / 原文 / 各语言翻译列）|
| 正文校验 | 强制覆盖率检查，< 80% 终止流程不输出 |
| 标题保留 | 标题行始终作为每条需求正文的一部分输出（供覆盖率校验 + 上下文追溯）；空正文标题行自动合成 |
| 默认交互 | 默认进入交互模式，依次询问用户目标语言 / 翻译引擎 / 专有名词补充；仅当用户明确要求或传入 `--no-input` 才跳过 |
| 表格行过滤 | D1/D2/D3 标题匹配时拒绝含 `;`（单元格分隔符）、`(`（单位注释）、尾部" - 短词"（标签/值对）、或含数字的行，避免把 PDF 表格行误识别为章节标题 |

### ❌ 不支持（不在范围）

- ❌ 图像、流程图、扫描版图纸内嵌文字的识别（仅正文文本）
- ❌ 手写件 / 极低质量扫描件 / 严重歪斜的 OCR
- ❌ 跨文档比对、汇总、差异提取
- ❌ 自动填回评分表、合规矩阵、投标响应
- ❌ 非文本类 PDF（纯图片册、CAD 导出的位图 PDF）
- ❌ 实时协作 / 多人并发编辑
- ❌ 结构化语义理解（不识别 "shall / must" 等模态词的合同义务强度）
- ❌ 法律效力的翻译认证（机器翻译仅供参考，不作法律背书）

### ⚠️ 使用前提

- PDF 须为 **可选取文本** 的数字版，或扫描分辨率 ≥ 200 dpi
- 须能访问 Google Translate API（直连或境外代理），除非使用 Agent 模式
- 运行环境：Python 3.9+；所需依赖 `pdfplumber`、`openpyxl`、
  `googletrans==4.0.0-rc1`（前两者必装，googletrans 仅 Google 引擎需要）
- 大文件（> 100 页）处理时间会显著增长；OCR 回退每页约 1-5 秒

---

## 3. 架构 / 流水线

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
   ├──▶ [008_validator]  assert_body_intact(raw_text, items)
   │       词多重集合覆盖率  →  < 80% 抛 BodyLossError
   │
   ▼
[002_translator]  (可选)  Google / Agent 翻译
   │
   ▼
[005_excel_generator]  Excel 工作簿
        ID | 章 | 节 | 需求原文 | 英文翻译 | 中文翻译 | …
```

### 关键不变式

1. `raw_text` 到 `items['content']` 的正文覆盖率 **不得低于 80%**（硬阈值）。
2. 每页以 `__PAGE_N__` 哨兵标记，确保页码归属性在剥离页眉后仍可恢复。
3. 每个需求行包含完整 `hierarchy_path`（如 `1 Sistemas > 1.2 MDC > 1.2.1 Condições Gerais`）。

---

## 4. 项目结构

```
DIaT/
├── 007_config/
│   └── config.py               # 全局配置 + 语言缩写表 + VALIDATION 阈值
├── 003_pdf_extractor/
│   └── pdf_extractor.py        # 4 策略融合提取 + 重复块剥离 + OCR 回退
├── 001_text_splitter/
│   └── text_splitter.py        # ChapterSectionParser + SentenceSegmenter
├── 004_classifier/             # (已停用 — 不再从 main.py 调用)
│   └── classifier.py
├── 005_excel_generator/
│   └── excel_generator.py      # Excel 输出（已删除需求分类/产品相关列）
├── 008_validator/
│   └── validator.py            # assert_body_intact — 正文存活校验
├── 002_translator/
│   └── translator.py           # TranslationService (Google + Agent)
├── 006_main/
│   └── main.py                 # CLI 入口 + 流程编排
├── 006_postprocess/
│   └── split_items_postprocess.py
├── README.md                   # 面向用户的说明（English）
├── README_zh.md                # 面向用户的说明（中文, 本文件）
└── AGENT_GUIDE.md              # 面向 orchestrator / sub-agent 的使用原则
```

---

## 5. 快速开始

### 安装依赖

两种方式 — 按你的运行方式选择。

**人工运行（手动）** — 一次性安装固定版本，随后直接运行：

```bash
# 核心依赖（必需）
pip install -r requirements.txt

# 可选增强：更好的断句 + 扫描件 OCR（需系统安装 tesseract + ghostscript）
pip install -r requirements-optional.txt
```

**Agent / 自动运行** — 脚本会从同一个 `requirements.txt` 自动安装缺
失的包，无需单独的 install 步骤。在非 TTY（agent / 管道）下或使用
`--install-deps` 时，缺包自动安装、不弹窗：

```bash
# 仅安装步骤（自动检测缺包，安装后退出）
python -m 006_main.main --install-deps

# 同时安装可选增强包
python -m 006_main.main --install-deps --with-optional
```

| 包 | 是否必需 | 用途 |
|----|----------|------|
| `openpyxl` | 必需 | Excel 工作簿读写 |
| `pdfplumber` | 必需 | PDF 文本提取（4 策略融合）|
| `PyPDF2` | 必需 | PDF 页面探测 / 元数据 |
| `pypdfium2` | 必需 | PDF 渲染 / 页面图像 |
| `googletrans` | 必需 | Google 翻译引擎（仅 `-e google` 时）|
| `pysbd` | 可选 | 按源语言断句（缺失则用内置正则 fallback）|
| `ocrmypdf` | 可选 | 扫描件 OCR 回退（需系统 tesseract + ghostscript）|

### 运行

> **默认交互模式** — 不传 `--no-input` 时，脚本会依次询问用户目标语言 / 翻译引擎 / 专有名词补充。仅在用户明确要求非交互时使用 `--no-input`。

**人工运行（已 `pip install`）：**

```bash
cd "D:/Tool Development/Skills Development/DIaT"

# 单文件 — 默认交互模式（询问语言 / 引擎 / 专有名词）
PYTHONIOENCODING=utf-8 python 006_main/main.py "<your-file.pdf>"

# 非交互模式 — 显式跳过所有提示，使用 en + zh-cn + Google
PYTHONIOENCODING=utf-8 python 006_main/main.py \
    "<your-file.pdf>" --no-input

# 单文件 — 不翻译，仅提取+拆分+输出 Excel（非交互）
PYTHONIOENCODING=utf-8 python 006_main/main.py \
    "<your-file.pdf>" \
    --no-translate --json --no-input

# 单文件 — 自动翻译（Google Translate，非交互）
PYTHONIOENCODING=utf-8 python 006_main/main.py \
    "<your-file.pdf>" \
    -e google --no-input -l en,zh-cn

# Agent 模式（Claude 自行读取 JSON、翻译、回写 Excel）
PYTHONIOENCODING=utf-8 python 006_main/main.py \
    "<your-file.pdf>" \
    -e agent --no-input -l en,zh-cn

# 批量目录（非交互）
PYTHONIOENCODING=utf-8 python 006_main/main.py ./pdfs --no-input
```

**自动 / Agent 运行（先自动安装依赖）：**

```bash
# 1. （可选）自动安装缺包 — 非 TTY 下不弹窗。
#    若已执行过 `pip install -r requirements.txt` 可跳过。
python -m 006_main.main --install-deps

# 2. 运行（加 `--no-input` 进入非交互模式）。
python -m 006_main.main "<your-file.pdf>" -e google --no-input -l en,zh-cn
```

### CLI 参数

| 参数 | 说明 |
|------|------|
| `input` | PDF 文件或目录路径 |
| `-o, --output` | 输出目录（默认 `output_fixed/`）|
| `--no-translate` | 跳过翻译 |
| `--json` | 额外输出 JSON 中间产物 |
| `-l, --lang` | 目标语言，逗号分隔（如 `en,zh-cn`）。默认 2 列（英文+中文）|
| `-e, --engine` | 翻译引擎 `google`（默认）或 `agent` |
| `--no-input` | **显式** 非交互模式（en + zh-cn + Google）。默认行为是交互模式，仅当用户明确要求时才传此参数 |
| `--install-deps` | 从 `requirements.txt` 安装缺包随后退出。非 TTY（agent / 管道）下不弹窗；TTY 下询问确认 |
| `--with-optional` | 配合 `--install-deps`，同时安装可选增强包（`pysbd`、`ocrmypdf`）|

### 翻译语言选择规则

1. **默认 2 列翻译** — Excel 输出 `需求原文` 后紧跟两列翻译列（`英文翻译` + `中文翻译`）
2. **交互式选择** — 非 `--no-input` 模式下，脚本会询问用户选择任意两种目标语言（默认 `en,zh-cn`）
3. **同源语言不翻译** — 若源语言与某个目标语言相同，该列保留原文，不调用翻译 API
   - 例：原文为英文，选择 `en,zh-cn` → `英文翻译` 列显示原文，`中文翻译` 列调用 Google Translate

### 交互模式流程

非 `--no-input` 模式下，脚本会依次询问用户三项选择：

1. **目标语言**（默认 en + zh-cn）
2. **翻译引擎**（默认 Google Translate）
3. **专有名词补充**（按类别引导，默认无补充）

示例交互：

```
$ PYTHONIOENCODING=utf-8 python 006_main/main.py example.pdf

  =======================================================
    目标翻译语言选择 / Target Language Selection
  =======================================================
  Detected source: pt (Português)

    en       — English
    zh-cn    — 中文（简体）
    pt       — Português ← source
    ...

  Enter 2 language codes (comma-separated)
  or press Enter for default [en,zh-cn]:

  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    翻译引擎选择 / Translation Engine
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    1. Google Translate API   (default — fast, external)
    2. Agent  — Claude reads JSON, translates, writes back

  Enter 1 or 2 (or press Enter for default Google):

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

  请选择类别编号 (1-10 补充, 0=完成): 4
  → [公司名（本文档）] 当前为空
    输入逗号分隔词追加 (Enter 跳过): CPFL,Enel
    + added 2 term(s)。

  请选择类别编号 (1-10 补充, 0=完成): 0
  ✓ 专有名词保护配置完成。共 2 个类别，6 个术语。

  [3/4] Translating (engine=google, languages=['en', 'zh-cn'])...
  ...
```

---

## 6. 后续方向 / Roadmap

- [ ] 支持命令行指定源语言（跳过自动检测）
- [ ] 引入 docx / odt 输出格式
- [ ] 多段落合并策略优化（当前按句切分）
- [ ] 对其他语种官方文档的泛化适配（西班牙/葡萄牙/安哥拉/…）
- [ ] 增量处理：同一 PDF 修订版差异提取

---

## 7. 正文不丢弃规范

> **正文被丢弃现象，这点是绝对不可容忍的。**

`008_validator` 在 Excel 生成前强制执行：

1. 把 `raw_text` 按行遍历，跳过页眉/页脚/目录行，得到 `body_lines`。
2. 把每个 `item['content']` 归一化为词的多重集合（multiset）。
3. 贪心比对：`coverage = Σ covered_words / Σ body_words`。
4. 覆盖率 `< 80%` → 抛 `BodyLossError`，**终止流程，不输出 Excel**。
5. 未覆盖行写入 `{prefix}_orphans.json` 供排查。

词法归一化规则：将所有空白字符折叠为一个空格，再 split 为词元。这保证了 pdfplumber 的断行缩进差异不会误计为正文丢失。

阈值可在 `007_config/config.py::VALIDATION` 中调整：

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

## 8. License & Attribution

© **Aggre-Cloud 聚云科技** — <https://www.acdatech.com>

本工具由 Aggre-Cloud 聚云科技 开发并内部使用。

---

## 9. 专有名词保护

翻译前，以下词类会被占位符 `__PROPER_<uuid>__` 替换，使 Google
Translate 保持其原样，翻译完成后再还原：

`007_config/config.py::DO_NOT_TRANSLATE` 是**分类词典**（`category → {label, items}`），
内置种子只放**跨行业通用术语**（~30 条），按类别组织：

- 技术缩略语（API、HTTP、HTTPS、JSON、XML、CSV、TCP、UDP、IP、SSH、…）
- 国际标准组织（IEC、IEEE、ISO、ITU、ANSI、IETF、W3C）
- 网络 / 基础设施（RF、PLC、LAN、WAN、HAN）
- 计量单位（GWh、MWh、kWh、Hz、kV、kW、kVA、MVA、ms、s）
- 通用公司 / 产品名（Google、Microsoft、Amazon、Apple）

以下为**空类别**，在交互步骤 3 中按本文档实际情况逐一补充：
人名、地名、产品/项目代号、公司名（本文档）、监管机构、法规/文档编号、
行业专有术语、岗位/职责，并可在运行时**新建任意类别**。

> 类别集合是**开放**的：行业特定术语（如电力的 `SCADA/AMI/MDM/MDC`、医疗的
> 药品名、法律的法院名）不属于版本化种子，而是用户在处理具体文档时按对应
> 类别补充——这是工具跨行业泛化的核心机制。

交互模式下，步骤 3 会**按类别引导**用户补充，并即时显示已填数量，而不是让用户
凭空罗列。

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

## 10. Agent 模式

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

## 11. 输出格式

Excel 工作表 `Requirements` 列定义：

| 列 | 字段 | 说明 |
|----|------|------|
| A | ID | REQ-0001 起递增 |
| B | 章 | 顶层章节号 + 标题 |
| C | 节 | 子章节号 + 标题 |
| D | 需求原文 | 源语言完整句 |
| E | {lang1}翻译 | 第一目标语言（如 `英文翻译`） |
| F | {lang2}翻译 | 第二目标语言（如 `中文翻译`） |

- 列 E / F 的标题由目标语言动态决定
- 若源语言匹配某目标语言，该列保留原文（不调用 API）
- 列宽：`[10, 35, 35, 65, 65, 65]`
```