# DIaT

> 结构化需求提取与翻译工具 — 从 PDF 文档中提取层级化需求，按结构拆分并翻译，
> 输出 Excel 报表。

语言：**中文**（本文件） · **English** → [`README.md`](../README.md) · **Português (Brasil)** → [`README_pt.md`](README_pt.md) · **Español** → [`README_es.md`](README_es.md) · **Français** → [`README_fr.md`](README_fr.md) · **Deutsch** → [`README_de.md`](README_de.md) · **日本語** → [`README_ja.md`](README_ja.md)

---

## 1. DIaT 是什么？—— 项目背景

### 它解决什么问题

国际工程、能源、基础设施项目每天都会产生**多语言、结构化的 PDF 文档**
—— 招投标文件、技术规格书、合同、法规、标准。 这些文档有一个共同特征：

- **层级编号**：解析器在内部建模为 5 层深度结构——章 → 节 → 条 → 款 → 项，
  常混用 `Art. 1º`、`CAPÍTULO`、`1.2.1`、`（1）`、`(a)`、罗马数字、带圈数字
  等多种编号样式。每条需求在内部都保留完整的 `hierarchy_path`，但导出的
  Excel **仅把前两层（章 / 节）作为独立的结构化列**，更深层级折叠进需求正文，
  以保证每行可读。
- **多语言**：葡萄牙语规格书服务于中资项目、阿拉伯语标书由德国承包商评审、
  俄语运维计划给巴西团队阅读。
- **版式复杂**：多栏文本、内嵌表格、重复页眉页脚，严重时甚至是扫描件。

对项目工程师、采购员、技术审核员来说，真正的工作是：*"把每条需求提取出来，
标注它属于哪个章节，并翻译成我能读懂的语言。"* 手工做这件事慢、容易出错，
更无法批量处理整个文件夹的文档。

### 为什么选择 DIaT —— 整体优势

一份一份地手工复制粘贴 → 翻译 → 拼装，慢且容易出错。DIaT 用一条确定性、
可自检的流水线替代整个循环：

| 能力 | 手工 / 单纯机翻 | DIaT |
|------|----------------|------|
| 文档版式 | 逐页复制粘贴，多栏、表格文本经常串位 | 4 策略融合提取（layout → words → tables → chars），自动剥离页眉页脚 |
| 需求拆分 | 人眼识别编号，容易漏项、压平层级 | 12 种编号格式自动识别（Art. / CAPÍTULO / § / 1.2.1 / （1）/ (a) / 罗马 / 带圈…）+ 栈式构造，保留每条需求的**完整章节路径** |
| 句子切分 | 整段翻译，长句质量差、断句丢失 | 按源语言最佳实践切分（拉丁语 pysbd；中/日/韩 CJK 句末规则；其它正则兜底） |
| 专有名词 | 被翻译引擎破坏（`MDC`→小写、`AMI` 被改写）| 占位符保护 + ~30 条通用内置词 + 按类别交互补充，翻译后原样还原 |
| 翻译引擎 | 只能选一个 | Google 翻译 **与** Agent（Claude）双引擎——同一流程随意切换，输出布局一致 |
| 正文安全 | 翻译丢失只能事后对比才能发现 | 强制词多重集合覆盖率校验，**< 80% 直接终止、绝不输出残缺 Excel** |
| 输出语言 | 单一语言、表头混用 | 工作表名 + 固定表头 + 列表头按目标语言本地化，零混用 |
| 批量 | 逐文件重复操作 | 目录批量 + CI flag（`--no-input`）+ Agent 自主运行 |

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

## 3. 通过 AI Agent 使用 DIaT

DIaT 是一个 **agent skill**：你只需发送**一条 prompt**，agent 会完成剩下的
所有事——拉取项目、安装依赖、运行完整的「提取 → 翻译 → Excel」流水线。
你不需要自己 clone 或 `pip install`；agent 会在运行过程中自行处理安装。

仓库中的 `AGENT_GUIDE.md` 是 agent 的操作手册——只要项目在磁盘上，有能力的
agent 就会自动阅读它，所以你的 prompt 只需要说明**文档**和你的**选择**。

### 3a. 一条 prompt 就够了——模板

从最短的 prompt 开始，只在你想跳过某个问题时再补充细节。选一行匹配你想
预先决定多少。

| 你的 prompt | agent 的行为 |
|---|---|
| `用 DIaT 处理 my-spec.pdf` | 拉取项目、安装依赖，然后问完 §3b 的三个问题再生成 Excel。**最稳妥的起点——拿不准就选这条。** |
| `Process my-spec.pdf with DIaT` | 同上，英文版。 |
| `DIaT my-spec.pdf → English + Japanese, Google engine` | 拉取项目、安装依赖，直接跑完：`-l ja -e google --no-input`。 |
| `用 DIaT 把 spec.pdf 条目化成 Excel，不翻译` | 仅提取 + 拆分 + 输出 Excel：`--no-translate --json --no-input`。 |
| `DIaT ./pdfs 全部 → zh-cn, agent engine, batch` | Agent 翻译模式（`-e agent`）下对整个目录做批量处理；agent 翻译输出的 JSON 队列。 |

prompt 可以用 agent 支持的任何语言。上面用中文示例是因为 DIaT 的默认值
针对中英工程文档调优。

#### 如何描述你要处理的任务

一个好的 prompt 告诉 agent 四件事——**做什么**、**处理什么**、**输出什么语言**、
以及**领域细节**。每次 prompt 不必包含全部四项；省略得越多，agent 问得越多
（见 §3b）。下面是各种自然语言描述——agent 会把每一条转成正确的 CLI 调用：

| 你的描述 | agent 的解读 |
|---|---|
| `我这个标书是葡语的，要翻成英文和中文，里面有很多电力行业缩写` | 源语言 `pt`，目标 `en + zh-cn`；如果你列出行业术语（`SCADA` / `AMI` / `MDM`…），agent 会将其纳入「产品/项目代号」保护 |
| `把这份日文标书条目化成 Excel，不要翻译，我只要结构` | `--no-translate --json --no-input`；输出带日文表头（ID / 章 / 節 / 原文）的层级条目 |
| `这份 PDF 是扫描版阿拉伯合同（约 300 页），要英文 + 中文，用 Agent 引擎保证质量` | 需要 OCR 回退（若 `ocrmypdf`/`tesseract` 缺失会先提醒）；`-l zh-cn -e agent --no-input` |
| `批处理这个文件夹里全部 pdf，目标中文，Google 快翻先过一遍` | 整目录批量（`./pdfs`），`-l zh-cn -e google --no-input` |
| `处理 02.pdf，原文中文，只要英文翻译这一列` | 源语言 `zh`，单一非英语目标；agent 保留中文列，只产出 `English` 列 |

**让 agent 做得更好的细节：**

- **行业 / 领域**——电力、医药、法律、建筑……点明领域能让 agent 加载对应的专有名词保护，并对领域缩写给出提示。
- **已知的专有名词**——项目代号（`MDC`、`SCADA`、`HPLC`）、公司名、人名。用逗号分隔交给 agent，agent 会将其加入 `DO_NOT_TRANSLATE` 列表，确保翻译后原样保留。
- **源语言**（如果你知道）——自动检测已很可靠，但提前告知可在短篇或混合语言文档上省一轮交互。
- **扫描版 vs 数字版**——扫描件会触发 OCR 回退（约每页 1–5 秒）；提前说明让 agent 先检查 `ocrmypdf`，以便在长耗时运行前安装或提醒。
- **范围**——单文件运行一次；目录则批量处理。可以加「只要前 10 页」或「跳过附录」等限定，agent 会据此收窄工作范围。

你也可以把这些自由组合成一句话——比如
`处理这份扫描的电力招标书（葡语），翻成中英双语，保护 MDC/SCADA/AMI 这些项目代号`
就是一条完整的 prompt。

### 3b. agent 会问的三个问题

如果 prompt 没有固定语言 / 引擎 / 专有名词，agent 会在翻译前先问这三个
问题——这是 `AGENT_GUIDE.md` 的强制检查清单，不是客套：

| # | 问题 | 不回答时的默认值 |
|---|------|------|
| (a) | **选一个非英语目标语言** —— 英语 (`en`) 始终是目标语言；你只选第二个 | `zh-cn`（简体中文） |
| (b) | **选翻译引擎** —— `google`（Translate API）或 `agent`（Claude 通过 JSON 队列自行翻译） | `google` |
| (c) | **按类别补充专有名词**（人名、项目代号、公司……） | 跳过——使用内置的 ~30 条通用种子词 |

**推荐做法：** 至少第一次回答这三个提示。这个交互流程能帮你了解工具的能力，
避免语言 / 引擎选错。只在明确想跳过提示时，才在 prompt 里写死选项
（如 §3a 非交互那几行）。

### 3c. 端到端示例（一条 prompt → 完成的 Excel）

下面是完整的对话形态——你发一条 prompt，agent 补装缺的依赖，然后要么问
三个问题要么直接运行。流程与 §10 相同，这里以对话形式展示，方便你在
开始前就知道会发生什么。

```
You:  Process my-spec.pdf with DIaT

Agent: [如缺失则 clone github.com/Aggre-Cloud/DIAT]
       [运行: python -m 005_main.main --install-deps  ]
       检测到的源语言: pt
       选哪个非英语目标语言？（默认 zh-cn）
You:   ja

Agent: 翻译引擎 —— Google 还是 Agent？
You:   google

Agent: 要补充专有名词吗？不补请直接回车
       （显示分类词表）
You:   [回车]

Agent: [提取 → 拆分 → 校验 → 翻译 → 写 Excel]
       已写入: output/my-spec_requirements.xlsx
       393 条需求，正文覆盖率 100.7 %
```

### 3d. 安装实际是怎样发生的（agent 侧）

你永远不需要手动执行这些——列在这里只是让你知道 agent 在底层做什么：

| 情形 | agent 运行 |
|---|---|
| 项目不在磁盘上 | `git clone https://github.com/Aggre-Cloud/DIAT.git` → 读 `AGENT_GUIDE.md` |
| 缺少依赖 | `PYTHONIOENCODING=utf-8 python -m 005_main.main --install-deps`（自动安装 `requirements.txt`；非 TTY 下不弹确认） |
| 需要可选扩展 | 加 `--with-optional`，同时安装 `pysbd` + `ocrmypdf` |
| 跑流水线 | `PYTHONIOENCODING=utf-8 python -m 005_main.main "<file.pdf>" -l ja -e google --no-input` |
| 选了 Agent 引擎 | 流水线写出 `*_agent_queue.json`，翻译列为空 → agent 逐行翻译并调用 `write_translations_to_excel()` 写回 |

### 3e. agent 必须做和不能做的事

完整契约见 `AGENT_GUIDE.md §3`。精简版：

- **一条 prompt 就是用户的全部工作** —— agent 负责安装 + 运行，绝不能要求用户手动 clone 或 `pip install`。
- **默认交互模式** —— 绝不能擅自替用户传 `--no-input`；只在用户明确要求非交互 / 批量时才传。
- **交互模式下绝不跳过三个问题**（§3b）。
- **把交互路径**（`python 005_main/main.py "file.pdf"`，不带 flag）**作为首要推荐**——最不容易出错，也能让用户了解工具的能力。
- **绝不静默丢弃正文** —— 覆盖率 < 80% 时流水线中止且不输出 Excel；agent 必须报出错误，不能擅自降低阈值重试（除非用户要求）。
- **运行期间绝不修改 DIaT 的源文件**。用户补充的专有名词写入运行时缓存 / JSON 队列，绝不写入 `config.py`（避免跨次运行污染）。

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
[004_excel_generator]  Excel 工作簿
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
├── 001_text_splitter/
│   └── text_splitter.py        # ChapterSectionParser（12 种编号格式，栈式 5 层树）+ SentenceSegmenter
├── 002_translator/
│   └── translator.py           # TranslationService (Google + Agent) + 本地化表头/标题辅助函数
├── 003_pdf_extractor/
│   └── pdf_extractor.py        # 4 策略融合提取 + 重复块剥离 + OCR 回退
├── 004_excel_generator/
│   └── excel_generator.py      # 单工作表 Excel 输出（表头本地化；英文 + 一种用户语言）
├── 005_main/
│   └── main.py                 # CLI 入口 + 流程编排 + agent 队列写入
├── 006_config/
│   └── config.py               # 全局配置 + ABBR 缩写表 + DO_NOT_TRANSLATE 分类 + VALIDATION 阈值
├── 007_validator/
│   └── validator.py            # assert_body_intact — 正文存活校验
├── sample doc/                 # 多语言示例 PDF（供测试）
├── output/                     # 生成的 Excel + JSON 中间产物（已 gitignore）
├── requirements.txt            # 固定版本运行依赖
├── requirements-optional.txt   # pysbd + ocrmypdf（更优断句、扫描件 OCR）
├── README.md                   # 面向用户的说明（English）
├── README_zh.md                # 面向用户的说明（中文，本文件）
├── README_pt.md                # 面向用户的说明（Português）
├── README_es.md                # 面向用户的说明（Español）
├── README_fr.md                # 面向用户的说明（Français）
├── README_de.md                # 面向用户的说明（Deutsch）
├── README_ja.md                # 面向用户的说明（日本語）
├── AGENT_GUIDE.md              # 面向 orchestrator / sub-agent 的使用原则
└── LICENSE                     # 项目许可证
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

## 13. 翻译引擎 —— Google vs. Agent

DIaT 提供两套可互换的翻译引擎，通过 `-e google`（默认）或 `-e agent`
选择。两者输出相同的 Excel 布局、遵守相同的专有名词保护、经过相同的正文
存活校验。区别在于**"谁来翻译"以及"怎么翻译"**。

### 工作机制对比

| | Google 翻译（`-e google`） | Agent / Claude（`-e agent`） |
|---|---|---|
| **执行者** | Google Translate API，由 `TranslationService._translate_with_google` 逐块调用 | AI agent（Claude）读取 JSON 队列并写回译文 |
| **握手方式** | 直接、进程内完成 | `main.py` 写 `*_agent_queue.json`（源语言、目标语言、需求列表、`extra_do_not_translate`）→ agent 翻译 → agent 调 `write_translations_to_excel()` 回写 |
| **上下文窗口** | 每次只翻译一个块（≤ 4 500 字符），跨需求无记忆 | 整个队列可见，agent 可跨需求保持术语一致，并利用前文的上下文 |
| **网络依赖** | 需要访问 Google Translate 端点（直连或境外代理） | 只需 Claude API，全程不触及 Google 端点 |
| **速度（每 100 条需求）** | 秒级——快，受 I/O 限制 | 分钟级——每条需求一次推理过程 |
| **费用** | 免费（有速率限制） | 消耗 Claude API token |

### 优势与劣势

#### Google 翻译（`-e google`）

**优势**
- **快**——吞吐高，适合快速预览或"足够即可"的大批量文档。
- **无 token 费用**——Translate API 在速率限制内免费。
- **通用语言对质量稳定**——常见语对（pt/en、en/es、en/zh）的一般行文流畅。

**劣势**
- **分块、无上下文**——每个 ≤ 4 500 字符的块独立翻译，跨块边界的长需求会丢失句间关联。
- **弱于密集技术文本**——长规格书中的嵌套条款、交叉引用、简洁表格式陈述，机翻容易失真或欠译（覆盖率校验届时可能拒绝输出）。
- **专有名词脆弱**——不经占位符保护，`MDC`、`AMI`、`HPLC` 等缩略语常被小写化或转写；占位符保护能缓解，但对未收录缩略语仍不彻底。
- **需要出网**——在只能访问 Claude API 的锁定 CI 主机上不可用。

#### Agent / Claude（`-e agent`）

**优势**
- **上下文感知**——Claude 能看到整条需求，必要时还可参照整个队列，
  因此术语保持一致（`MDC` 仍为 `MDC`，`last-gasp` 取"断电最后一搏"的
  计量语义），嵌套条款处理干净。
- **最适合密集、简短的技术文本**——正是规格书提炼出的需求的典型形态，
  输出接近人工翻译。
- **不依赖 Google**——在仅可访问 Claude API 的环境同样可用。
- **自一致性**——agent 对文档中重复出现的短语给出统一翻译，而分块的
  Google 可能每次略有不同。

**劣势**
- **较慢**——每条需求一次推理；400 条需求的文件需数分钟。脚本通过分批
  与多 agent turn 并行来缓解。
- **token 费用**——按千 token 计费，大文档成本明显高于免费的 Google 路径。
- **对流畅长文偶有"润色"**——对于叙事性长段落（需求列表里罕见），
  流畅的引擎可能"改进"措辞而非忠实翻译；覆盖率校验能发现内容丢失，
  但无法捕捉风格偏移。

### 如何选择

| 场景 | 推荐引擎 |
|---|---|
| 快速预览、大批量、流畅行文 | `-e google` |
| 密集技术规格、术语一致性要求高 | `-e agent` |
| 网络受限（仅可访问 Claude API） | `-e agent` |
| 对 Google 初稿做二轮润色 | 先跑 Google，再对队列跑 Agent |

> **注意**：Agent 模式下，`extra_do_not_translate` 列表同样生效；agent 在
> 翻译前须用相同的 `__PROPER_<uuid>__` 占位符替换这些词（与 Google 路径
> 共用同一套 `_protect_proper_nouns` / `_restore_proper_nouns` 契约），
> 因此两个引擎的保护行为完全一致。

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
