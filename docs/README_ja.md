# DIaT

> 構造化要件抽出・翻訳ツール — PDF ドキュメントから階層的な要件を抽出し、
> 構造ごとに分解し、翻訳し、Excel レポートをエクスポートします。

言語: **日本語** (このファイル) · **English** → [`README.md`](../README.md) · **中文** → [`README_zh.md`](README_zh.md) · **Português (Brasil)** → [`README_pt.md`](README_pt.md) · **Español** → [`README_es.md`](README_es.md) · **Français** → [`README_fr.md`](README_fr.md) · **Deutsch** → [`README_de.md`](README_de.md)

---

## 1. DIaT とは？ — プロジェクトの背景

### 解決する問題

国際的なエンジニアリング、エネルギー、インフラプロジェクトでは、構造化された
**多言語 PDF ドキュメント** — 入札書、技術仕様書、契約書、法規、規格 — が
日常的に作成されます。これらのドキュメントには共通の特徴があります：

- **階層的な章番号付け**: パーサーが内部的に 章 → 節 → 条 → 款 → 項
  （5 階層構造）としてモデル化し、`Art. 1º`、`CAPÍTULO`、`1.2.1`、`（1）`、
  `(a)`、ローマ数字、丸囲み数字など、複数の番号体系が混在する場合があります。
  すべての要件は内部的に完全な `hierarchy_path` を持ちますが、エクスポートされる
  Excel には上位 2 レベル（章 / 節）のみ専用の構造列として公開され、それより
  深い階層は要件本文に折りたたまれて行の可読性を保ちます。
- **多言語**: 中国資本プロジェクト向けのポルトガル語仕様書、ドイツの請負業者
  がレビューするアラビア語入札書、ブラジルのチームが読むロシア語 O&M 計画。
- **レイアウトが複雑**: 複数段組みのテキスト、埋め込みテーブルのほか、繰り返し
  ヘッダー・フッター、そして最悪の場合 — スキャンされた画像ページ。

プロジェクトエンジニア、調達担当者、または技術レビュアーの本来の作業は：
*「すべての要件を抽出し、それが属する章を把握し、自分の言語で読めるようにする」*
ことです。手作業では遅く、エラーが発生しやすく、ドキュメントのフォルダ全体には
対応できません。

### DIaT である理由

ドキュメントごとの翻訳は�くもろい。DIaT は、コピー＆ペースト → 翻訳 → 再構築という
手作業のループを、決定的で自己検証型の 1 つのパイプラインに置き換えます：

| 能力 | 手動 / Google 翻訳のみ | DIaT |
|------|----------------------|------|
| ドキュメントレイアウト | ページごとにコピー＆ペースト。複数段組みやテーブルは日常的に崩れる | 4 戦略マージ抽出（レイアウト → 単語 → テーブル → 文字）＋ ヘッダー・フッター自動除去 |
| 要件分割 | 番号を目視で確認。項目を漏らしたりネストを平らにしやすい | 12 種の番号体系を自動検出（Art. / CAPÍTULO / § / 1.2.1 / （1）/ (a) / ローマ数字 / 丸囲み数字 …）。スタックベースのツリーで各項目の**完全な**章パスを保持 |
| 文分割 | 段落全体を翻訳。長文は品質低下、改行が失われる | ソース言語ごとのベストプラクティス（ラテン文字は pysbd、CJK は zh/ja/ko の終端子ルール、その他は regex フォールバック） |
| 固有名詞 | 翻訳エンジンにより破損（`MDC` → 小文字化、`AMI` が歪む） | ～30 の組み込み汎用用語＋カテゴリ別インタラクティブ追加によるプレースホルダー保護。翻訳後にそのまま復元 |
| 翻訳エンジン | 1 つに固定 | Google 翻訳 **および** Agent（Claude）のデュアルエンジン — 同一パイプライン内で同じ出力レイアウトで切替可能 |
| 本文安全性 | 翻訳ロストは事後に気づくしかない（気づかない場合もある） | 必須の単語マルチセットカバレッジチェック。**80% 未満パイプラインを強制停止し、Excel は出力しません** — 部分的な出力は許容されません |
| 出力言語 | 単一言語、混在ヘッダー | シートタイトル、固定ヘッダー、列見出しがターゲット言語に完全にローカライズ — 混在なし |
| バッチ | ファイルごとの反復処理 | ディレクトリ全体の一括処理、CI フラグ（`--no-input`）、Agent 自律実行 |

### DIaT の機能

**DIaT**（名前は仮の頭字語）は、そのような PDF 1 つを 1 つのコマンドで
構造化された翻訳済み Excel ブックに変換します：

1. **抽出** — PDF から本文テキストを 4 戦略マージ（レイアウト → 単語 →
   テーブル → 文字）で抽出。ヘッダー・フッター自動除去とスキャン PDF の OCR
   フォールバック付き。
2. **分解** — ドキュメントを階層的な要件に分解し、各項目の章/节パスを保持。
3. **分割** — ソース言語ごとに文を分割（pt / en / zh / ja / ko / es / fr / de / …）。
4. **翻訳** — 各要件を 2 つのターゲット言語に翻訳。英語は常に 1 列で、もう 1
   つを選択。
5. **検証** — 本文テキストが失われていないことを確認（カバレッジ < 80% の場合に
   中止 — 部分的な出力は許容されません）。
6. **エクスポート** — Excel ブック：`ID / 章 / 節 / 原文 / English / <選択した
   言語>`。

### 対象ユーザー

- 多言語の仕様書や入札書を扱うプロジェクトエンジニアおよび調達担当者。
- ドキュメント構造に基づいた初稿機械翻訳が必要な技術翻訳者。
- 各要件をソース章に追跡できる品質保証 / コンプライアンスレビュアー。
- ドキュメント処理パイプラインをオーケストレーションし、決定的で自己検証型のツール
  を必要とする AI Agent（Claude など）。

---

## 2. 使い方 — 推奨方法

### ▶ 推奨：インタラクティブモード（ただ実行するだけ）

DIaT を使う最も簡単で推奨される方法は、**インタラクティブ** に実行し、スクリプトに
ガイドさせることです。回答は 3 つの質問だけで、あとはすべて自動です：

```bash
# プロジェクトルートにいることを確認
cd "<project-root>"

# 実行 — これだけ。3 つの質問のあと、Excel が生成される。
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf"
```

プロンプトは順序次のとおりです：

| # | 質問 | デフォルト |
|---|------|-----------|
| (a) | **英語以外のターゲット言語を 1 つ選択** — 英語 (`en`) は常にターゲット。2 つ目を選択 | `zh-cn`（中国語簡体字） |
| (b) | **翻訳エンジンを選択** — `google`（Translate API）または `agent`（Claude が JSON キューで自己翻訳） | `google` |
| (c) | **カテゴリ別に固有名詞を追加**（人名、プロジェクトコード、会社名 …）— スキップは Enter なし | なし（組み込み ～30 の汎用シード） |

プロンプト後、パイプラインが完了まで実行され、Excel が
`output/<your-file>_requirements.xlsx` に書き出されます。

> **ヒント:** 自動検出されたソース言語がターゲットのいずれかと一致する場合、
> その列は自動的に原文を保持します — 余分な API 呼び出しはありません。

### ▶ 非インタラクティブモード（バッチ / CI / 明示的フラグ）

すべての選択がすでに決まっていてプロンプトをスキップしたい場合は、フラグを明示的に
渡します：

```bash
# 英語 + 日本語、Google、非インタラクティブ
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    -l ja -e google --no-input

# 英語 + 中国語、Agent モード、非インタラクティブ
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    -l zh-cn -e agent --no-input

# 抽出 + 分割 + Excel エクスポートのみ、翻訳なし
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    --no-translate --json --no-input

# ディレクトリ全体を一括処理（非インタラクティブ）
PYTHONIOENCODING=utf-8 python 005_main/main.py ./pdfs --no-input
```

> **注意:** 英語 (`en`) は常に自動追加されます — `-l` は *英語以外の* 言語のみを
> 受け取ります。`-l en` は明確なエラーメッセージで拒否されます。

### ▶ Agent / 自動実行（最初に依存関係を自動インストール）

AI Agent が DIaT を実行する場合、依存関係が存在しない可能性があります。スクリプトは
プロジェクト独自の `requirements.txt` から人手なしでインストールできます：

```bash
# 1. (オプション) 不足している依存関係を自己インストール — 非 TTY では非インタラクティブ。
#    すでに `pip install -r requirements.txt` を実行済みならスキップ。
python -m 005_main.main --install-deps

# 2. オプション拡張も取得（より良いセグメンテーション + スキャン PDF OCR）
python -m 005_main.main --install-deps --with-optional

# 3. 実際のパイプラインを実行
python -m 005_main.main "your-file.pdf" -l ja -e google --no-input
```

### ▶ 手動インストール（1 コマンド）

```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt   # オプション: pysbd + ocrmypdf
```

---

## 3. AI Agent 経由で DIaT を使う

DIaT は **agent skill** です。**1 つの prompt** を送るだけで、Agent が残りをすべて
行います — プロジェクトの取得、依存関係のインストール、そして抽出 → 翻訳 → Excel
までの全パイプラインの実行。あなたが自分で clone したり `pip install` したりする
必要はありません。インストールは Agent が実行の一環として自分で行います。

リポジトリの `AGENT_GUIDE.md` は Agent の取扱説明書です。対応する Agent はプロジェクトが
ディスク上にあるとすぐにそれを読むため、あなたの prompt に必要なのは
**ドキュメント**と**選択**だけです。

### 3a. 1 つの prompt で十分 — テンプレート

最も短い prompt から始め、質問をスキップしたいときだけ詳細を追加します。事前に
どれだけ決めておきたいかに合った行を選んでください。

| あなたの prompt | Agent の動作 |
|---|---|
| `用 DIaT 处理 my-spec.pdf` | プロジェクトを取得し、依存関係をインストールした後、§3b の 3 つの質問を聞いてから Excel を生成します。**最も安全 — 迷ったらこれを選んでください。** |
| `Process my-spec.pdf with DIaT` | 同上（英語版）。 |
| `DIaT my-spec.pdf → English + Japanese, Google engine` | プロジェクトを取得し、依存関係をインストールし、そのまま実行：`-l ja -e google --no-input`。 |
| `用 DIaT 把 spec.pdf 条目化成 Excel，不翻译` | 抽出 + 分割 + Excel のみ：`--no-translate --json --no-input`。 |
| `DIaT ./pdfs 全部 → zh-cn, agent engine, batch` | Agent 翻訳モード（`-e agent`）でディレクトリを一括処理。Agent が出力された JSON キューを翻訳します。 |

prompt は Agent が理解できる任意の言語で機能します。上の中国語例は、DIaT の
デフォルトが中英エンジニアリング文書に調整されているため用いられます。

#### タスクの説明の仕方

良い prompt は Agent に 4 つを伝えます——**作業内容**、**対象ドキュメント**、
**出力言語**、**ドメインの詳細**。毎回 4 つすべてが必要なわけではありません。
省略するほど Agent が尋ねます（§3b 参照）。以下はどの言語でも機能する自然な
説明です——Agent はそれぞれを正しい CLI 呼び出しに変換します：

| あなたの説明 | Agent の解釈 |
|---|---|
| `この入札ポルトガル語なんで、英語と中国語にして、電力業界の略語が多い` | ソース `pt`、ターゲット `en + zh-cn`；用語（`SCADA` / `AMI` / `MDM`…）を挙げると Agent は「製品/プロジェクトコード」で保護 |
| `日本の入札書を Excel に変換して、翻訳なしで構造だけ欲しい` | `--no-translate --json --no-input`；日本語見出し（ID / 章 / 節 / 原文）で階層的項目を出力 |
| `この PDF はスキャンされたアラビア語契約（約 300 ページ）、英語と中国語、品質のため Agent エンジンで` | OCR フォールバックを想定（`ocrmypdf`/`tesseract` 不足なら最初に警告）；`-l zh-cn -e agent --no-input` |
| `このフォルダの pdf 全部一括、中国語、Google でまず速く回す` | ディレクトリ一括（`./pdfs`）、`-l zh-cn -e google --no-input` |
| `02.pdf 処理、原文中国語、英語翻訳の列だけ欲しい` | ソース `zh`、単一非英語ターゲット；Agent は中国語列を保持し `English` 列のみ出力 |

**Agent がより良く働くための詳細：**

- **業種 / ドメイン** — 電力、医薬、法律、建設…指名すると固有名詞保護が適切に読み込まれ、分野別略語の警告が出ます。
- **既知の固有名詞** — プロジェクトコード（`MDC`、`SCADA`、`HPLC`）、企業名、人名。カンマ区切りで渡すと Agent は `DO_NOT_TRANSLATE` リストに追加し、翻訳後に原形のまま復元します。
- **ソース言語**（分かっていれば）— 自動検出は頼りになりますが、事前に伝えると短い・混在言語のドキュメントで往復を省けます。
- **スキャン vs デジタル** — スキャン PDF は OCR フォールバックをトリガ（1〜5 秒/ページ）；明示しておくと Agent が長実行の前に `ocrmypdf` を確認できます。
- **範囲** — 単一ファイルは 1 回、ディレクトリは一括実行。「最初の 10 ページだけ」「付録をスキップ」といった限定を加えると Agent は作業を絞り込みます。

これらを 1 文に自由に混ぜても構いません——例：
`このスキャンされた電力入札書（ポルトガル語）を処理、英中国語に翻訳、MDC/SCADA/AMI というプロジェクトコードを保護して`
で完全な prompt です。

### 3b. Agent が尋ねる 3 つの質問

prompt で言語 / エンジン / 固有名詞が固定されない場合、Agent は翻訳前にこれら
3 つを尋ねます — これは `AGENT_GUIDE.md` の必須チェックリストであり、義理では
ありません：

| # | 質問 | 未回答時のデフォルト |
|---|------|------|
| (a) | **英語以外の対象言語を 1 つ選択** — 英語 (`en`) は常に対象。あなたが選ぶのは 2 つ目のみ | `zh-cn`（簡体字中国語） |
| (b) | **翻訳エンジンを選択** — `google`（Translate API）または `agent`（Claude が JSON キューで自動翻訳） | `google` |
| (c) | **固有名詞をカテゴリ別に追加**（人名、プロジェクトコード、企業…） | スキップ — 組み込みの汎用シード約 30 件を使用 |

**推奨:** 少なくとも初回は 3 つのプロンプトに答えてください。このインタラクティブ
フローでツールの機能を学べ、言語 / エンジンの選択ミスを防げます。意図的に質問を
スキップしたいときだけ、prompt に選択を明記してください（§3a の非インタラクティブ行を参照）。

### 3c. エンドツーエンド例（1 つの prompt → 完成した Excel）

以下が全会話の形です — あなたが 1 つの prompt を送り、Agent が足りないものを
インストールし、3 つの質問をするかそのまま実行します。§10 と同じフローを対話形式で
示します。開始前に何が起きるかがわかるように。

```
You:  Process my-spec.pdf with DIaT

Agent: [github.com/Aggre-Cloud/DIaT がなければ clone]
       [実行: python -m 005_main.main --install-deps  ]
       検出されたソース言語: pt
       英語以外の対象言語は？（デフォルト zh-cn）
You:   ja

Agent: 翻訳エンジン — Google または Agent？
You:   google

Agent: 固有名詞を追加しますか？Enter でスキップ
       （カテゴリ別リストを表示）
You:   [Enter]

Agent: [抽出 → 分割 → 検証 → 翻訳 → Excel 書き込み]
       書き込み完了: output/my-spec_requirements.xlsx
       要件数 393、本文カバレッジ 100.7 %
```

### 3d. インストールの実際の流れ（Agent 側）

これらはあなたが手で実行することはありません — Agent が内部で何をしているか
理解できるように掲載します：

| 状況 | Agent が実行 |
|---|---|
| プロジェクトがディスクにない | `git clone https://github.com/Aggre-Cloud/DIAT.git` → `AGENT_GUIDE.md` を読む |
| 依存関係が欠落 | `PYTHONIOENCODING=utf-8 python -m 005_main.main --install-deps`（`requirements.txt` を自動インストール、非 TTY はプロンプトなし） |
| オプション拡張が必要 | `--with-optional` を追加し `pysbd` + `ocrmypdf` もインストール |
| パイプライン実行 | `PYTHONIOENCODING=utf-8 python -m 005_main.main "<file.pdf>" -l ja -e google --no-input` |
| Agent エンジン選択時 | パイプラインが翻訳列空の `*_agent_queue.json` を書き出し → Agent が各行を翻訳し `write_translations_to_excel()` で保存 |

### 3e. Agent がしてよいこと・してはいけないこと

完全な契約は `AGENT_GUIDE.md §3` にあります。要約版：

- **1 つの prompt がユーザーの全仕事** — Agent がインストール + 実行。ユーザーに
  手動での clone や `pip install` を求めてはなりません。
- **デフォルトはインタラクティブ** — ユーザーの代わりに `--no-input` を渡しては
  なりません。ユーザーが非インタラクティブ / バッチ実行を明示的に要求した場合のみ。
- **インタラクティブモードで 3 つの質問をスキップしてはなりません**（§3b）。
- **インタラクティブパス**（`python 005_main/main.py "file.pdf"`、flags なし）を
  スキル使用の主要な方法として推奨 — 最もエラーが少なく、ユーザーにツールの機能を
  教えられます。
- **本文消失を黙って無視してはなりません** — カバレッジ < 80% ならパイプラインが
  停止し Excel は出力されません。Agent はエラーを表示し、ユーザーが頼まない限り
  閾値を下げて再試行してはなりません。
- **実行中に DIaT のソースファイルを変更してはなりません**。ユーザーが提供した
  固有名詞は実行時キャッシュ / JSON キューに格納され、`config.py` は書き換えられ
  ません（実行間汚染を防止）。

---

## 5. インストールされる依存関係

| パッケージ | 必須 / オプション | 用途 |
|-----------|-----------------|------|
| `openpyxl` | 必須 | Excel ブックの読み書き |
| `pdfplumber` | 必須 | PDF テキスト抽出（4 戦略マージ） |
| `PyPDF2` | 必須 | PDF ページのプローブ / メタデータ |
| `pypdfium2` | 必須 | PDF レンダリング / ページ画像 |
| `googletrans` | 必須 | Google 翻訳エンジン（`-e google` 時のみ） |
| `pysbd` | オプション | 言語対応文セグメンテーション（未インストール時は regex フォールバック） |
| `ocrmypdf` | オプション | スキャン PDF の OCR フォールバック（システム tesseract + ghostscript が必要） |

---

## 6. 対応範囲

### ✅ サポート対象

| 次元 | 範囲 |
|------|------|
| 入力 | 単一 PDF ファイル、または PDF ディレクトリ（バッチ） |
| 構造タイプ | 階層的に番号付けされたドキュメント（契約書、仕様書、法規、入札書、規格…） |
| ヘッダー / フッター | 繰り返しブロックを自動検出（ページの ≥ 75%）して除去 |
| スキャン PDF | プローブ後、`ocrmypdf --language <config>` で OCR フォールバック（遅延インポート、必須依存ではない） |
| 階層マーカー | `Art. 1º` / `CAPÍTULO` / `SEÇÃO` / `§ 1º` / `I.` / `1.` / `1.2` / `1.2.1` / `（1）` / `(a)` / `•` / `(1)` / ローマ数字 / 丸囲み数字 |
| ソース言語 | pysbd（オプション）＋ 組み込み regex フォールバック。pt / en / es / fr / de / zh / ja / ko それぞれに専用セグメンテーションルール |
| ターゲット言語 | 英語（固定）＋ ユーザー選択言語 1 つ（googletrans / Claude code のいずれか） |
| 翻訳エンジン | Google 翻訳（直接）または Agent（Claude が自己翻訳） |
| 固有名詞保護 | プレースホルダー置換（組み込み ～30 の汎用用語 ＋ ユーザー追加）。翻訳後に復元 |
| 出力形式 | Excel ブック（ID / 章 / 節 / 原文 / English / <選択した言語>） |
| 本文検証 | 必須カバレッジチェック。< 80% でパイプラインを停止し、出力なし |
| タイトル保持 | 見出し行は常に各要件の本文の一部として出力（カバレッジ監査 ＋ コンテキスト追跡用）。空本文の見出しは自動合成 |
| デフォルトの対話 | デフォルトはインタラクティブ — ターゲット言語 / 翻訳エンジン / 固有名詞追加をプロンプト。ユーザーが明示的に要求した場合、または `--no-input` を渡した場合のみスキップ |
| テーブル行フィルタリング | `D1/D2/D3` 見出しに一致する場合、`;`（セル区切り）、`(`（単位注釈）、末尾の " - short word"（ラベル/値ペア）、数字を含む行を拒否 — PDF テーブル行のセクション見出しとしての誤読を防止 |

### ⚠️ 前提条件

- PDF は **テキスト選択可能な** デジタルであるか、≥ 200 dpi でスキャンされていること
- Agent モード以外では、Google Translate API へのアクセス（直接または海外プロキシ経由）が必要
- ランタイム：Python 3.9+。依存関係は §4 に記載
- 大容量ファイル（> 100 ページ）は処理時間が大幅に増加。OCR フォールバックはページあたり約 1-5 秒

---

## 7. アーキテクチャ / パイプライン

```
PDF ファイル
   │
   ▼
[003_pdf_extractor]  extract_with_meta()
   │  4 戦略マージ: layout → words → tables → chars   (フォールバック・カスケード)
   │  繰り返しブロック除去  +  __PAGE_N__  センチネル
   │  スキャン PDF プローブ → ocrmypdf → 再オープン
   ▼
raw_text  +  ExtractionMeta
   │
   ▼
[001_text_splitter]  parse_text(raw_text, lang)
   │  ChapterSectionParser  — 優先順位付き regex ＋ スタック構築
   │  SentenceSegmenter     — 言語ごとのベストプラクティス・ルール
   ▼
ParseResult  { roots, items, meta, raw_rows }
   │
   ├──▶ [007_validator]  assert_body_intact(raw_text, items)
   │       単語マルチセットカバレッジ率  →  < 80% なら BodyLossError
   │
   ▼
[002_translator]  (オプション)  Google / Agent 翻訳
   │
   ▼
[004_excel_generator]  Excel ブック
        ID | 章 | 節 | 原文 | English | <選択した言語>
```

### 重要な不変条件

1. `raw_text` から `items['content']` への本文カバレッジは **80% を下回ってはならない**
   （ハードしきい値）。
2. すべてのページに `__PAGE_N__` センチネルが付与され、ページ帰属がヘッダー除去後も
   維持される。
3. すべての要件行は完全な `hierarchy_path` を持つ（例：
   `1 Sistemas > 1.2 MDC > 1.2.1 Condições Gerais`）。

---

## 8. プロジェクト構成

```
DIaT/
├── 001_text_splitter/
│   └── text_splitter.py        # ChapterSectionParser（12 種の番号体系、スタックベース 5 階層ツリー）＋ SentenceSegmenter
├── 002_translator/
│   └── translator.py           # TranslationService（Google ＋ Agent）＋ ローカライズ済みヘッダー/タイトル補助
├── 003_pdf_extractor/
│   └── pdf_extractor.py        # 4 戦略マージ抽出 ＋ 繰り返しブロック除去 ＋ OCR フォールバック
├── 004_excel_generator/
│   └── excel_generator.py      # 単一シート Excel 出力（ローカライズ済みヘッダー；英語 ＋ ユーザー言語 1 つ）
├── 005_main/
│   └── main.py                 # CLI エントリポイント ＋ パイプラインオーケストレーション ＋ Agent キュー書き込み
├── 006_config/
│   └── config.py               # グローバル設定 ＋ ABBR テーブル ＋ DO_NOT_TRANSLATE カテゴリ ＋ VALIDATION しきい値
├── 007_validator/
│   └── validator.py            # assert_body_intact — 本文存続チェック
├── sample doc/                 # テスト用サンプル PDF（多言語）
├── output/                     # 生成された Excel ＋ JSON 中間ファイル（git 管理外）
├── requirements.txt            # 固定版ランタイム依存関係
├── requirements-optional.txt   # pysbd ＋ ocrmypdf（より良いセグメンテーション、スキャン PDF OCR）
├── README.md                   # ユーザー向けドキュメント（英語）
├── docs/
│   ├── README_zh.md            # ユーザー向けドキュメント（中国語）
│   ├── README_pt.md            # ユーザー向けドキュメント（ポルトガル語）
│   ├── README_es.md            # ユーザー向けドキュメント（スペイン語）
│   ├── README_fr.md            # ユーザー向けドキュメント（フランス語）
│   ├── README_de.md            # ユーザー向けドキュメント（ドイツ語）
│   └── README_ja.md            # このファイル — ユーザー向けドキュメント（日本語）
├── AGENT_GUIDE.md              # オーケストレータ / サブ Agent 利用原則
└── LICENSE                     # プロジェクトライセンス
```

---

## 9. CLI 引数

| 引数 | 説明 |
|------|------|
| `input` | PDF ファイルまたはディレクトリパス |
| `-o, --output` | 出力ディレクトリ（デフォルト `output/`） |
| `--no-translate` | 翻訳をスキップ |
| `--json` | JSON 中間ファイルも出力 |
| `-l, --lang` | 英語以外のターゲット言語（例：`pt`、`ja`）。英語は常に自動追加 |
| `-e, --engine` | 翻訳エンジン `google`（デフォルト）または `agent` |
| `--no-input` | **明示的** 非インタラクティブモード（en ＋ zh-cn ＋ Google）。デフォルトはインタラクティブ。明示的に要求された場合のみ渡す |
| `--display-lang` | Excel ヘッダー / シート言語を上書き（デフォルト：英語以外のターゲット言語） |
| `--install-deps` | `requirements.txt` から不足しているサードパッケージをインストールして終了。stdin が TTY でない場合（Agent / パイプライン）は非インタラクティブ。TTY では確認を求める |
| `--with-optional` | `--install-deps` と組み合わせ、オプション拡張（`pysbd`、`ocrmypdf`）もインストール |

### 翻訳言語選択ルール

1. **英語は常にターゲット** — 2 つ目の言語のみを選択。
2. **同一ソーススキップ** — ソース言語がターゲットと一致する場合、その列は原文を保持（API 呼び出しなし）。
3. **ローカライズ済みヘッダー** — Excel の固定ヘッダー、列見出し、シートタイトルが英語以外のターゲット言語で描画（例：`en + ja` → `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`）。混在ヘッダーなし。

---

## 10. インタラクティブフロー — セッション例

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

## 11. 本文保持の保証

本文の黙然的な喪失は **許容されません** — Excel が生成される前に `007_validator` が
無条件に実行されます：

1. `raw_text` を行ごとに走査し、ヘッダー/フッター/目次行をスキップ → `body_lines`
   を生成。
2. 各 `item['content']` を単語マルチセットに正規化。
3. 貪欲マッチング：`coverage = Σ covered_words / Σ body_words`。
4. カバレッジ `< 80%` → `BodyLossError` を発生させ、**パイプラインを停止、Excel は
   出力されません**。
5. カバーされなかった行はトリアージ用に `{prefix}_orphans.json` に書き出されます。

語彙的正规化は、すべての空白を 1 つのスペースに畳んでからトークンに分割するため、
pdfplumber 駆動の改行インデントの差異が本文喪失として誤カウントされることはありません。

しきい値は `006_config/config.py::VALIDATION` にあります：

```python
VALIDATION = {
    'min_char_coverage': 0.80,   # 最小本文存続率
    'min_word_coverage': 0.85,
    'write_orphans': True,
    'sentence_target_min': 50,    # 文あたりの最小文字数
    'sentence_target_max': 500,   # 文あたりの最大文字数
}
```

---

## 12. 固有名詞保護

翻訳前に、次の用語クラスはプレースホルダー `__PROPER_<uuid>__` に置換され、
Google 翻訳がそのままにし、翻訳後に復元されます：

`006_config/config.py::DO_NOT_TRANSLATE` は **カテゴリ別辞書**
（`category → {label, items}`）です。組み込みシードには **業界横断的な汎用用語**
（～30）のみが含まれ、カテゴリ別に整理されています：

- 技術略語（API, HTTP, HTTPS, JSON, XML, CSV, TCP, UDP, IP, SSH, …）
- 規格団体（IEC, IEEE, ISO, ITU, ANSI, IETF, W3C）
- ネットワーク / インフラ（RF, PLC, LAN, WAN, HAN）
- 計測単位（GWh, MWh, kWh, Hz, kV, kW, kVA, MVA, ms, s）
- 汎用会社 / 製品名（Google, Microsoft, Amazon, Apple）

以下は **空のカテゴリ** で、インタラクティブステップ (c) でドキュメントごとに
入力されます：人名、地名、製品 / プロジェクトコード、会社（該当ドキュメント）、
法規機関、法的 / ドキュメント参照、業界固有用語、役割 / 責任 — およびユーザーは
実行時に **任意の新カテゴリを作成** できます。

> カテゴリセットは **オープン** です：業界固有用語（電力事業者の `SCADA/AMI/MDM/MDC`、
> 医療の薬品名、法務の裁判所名など）はバージョン管理されたシードには **含まれず**、
> ユーザーが具体的なドキュメントを処理する際に一致するカテゴリに入力します。
> これがツールの業界横断的汎用化の中核メカニズムです。

**メカニズム**（`002_translator/translator.py`）：

```
原文
  │
  ▼
_protect_proper_nouns()        ← DO_NOT_TRANSLATE 用語をプレースホルダーに置換
  │
  ▼
Google Translate API
  │
  ▼
_restore_proper_nouns()        ← プレースホルダーを受期用語に戻す
  │
  ▼
翻訳
```

用語リストは降順の長さでソートされ、`AMI` より先に `Advanced Metering` が
一致します。

---

## 13. 翻訳エンジン — Google vs. Agent

DIaT は `-e google`（デフォルト）または `-e agent` で選択可能な 2 つの交換可能な
翻訳エンジンを提供します。どちらも同じ Excel レイアウトに出力し、同じ固有名詞保護を
尊重し、同じ本文存続チェックで検証されます。*誰が* 翻訳し、*どのように* 翻訳するか
が異なります。

### 動作の仕組み

| | Google 翻訳（`-e google`） | Agent / Claude（`-e agent`） |
|---|---|---|
| **実行者** | `TranslationService._translate_with_google` からチャンクごとに呼び出される Google Translate API | AI Agent（Claude）が JSON キューを読み取り、翻訳を書き戻す |
| **ハンドシェイク** | 直接、プロセス内 | `main.py` が `*_agent_queue.json`（ソース言語、ターゲット言語、要件、`extra_do_not_translate`）を書き込み → Agent が翻訳 → Agent が `write_translations_to_excel()` を呼び出し |
| **コンテキストウィンドウ**  | 1 チャンクずつ（≤ 4 500 文字）。要件間でメモリなし | キュー全体が利用可能。Agent は要件間で用語の一貫性を強制し、前の項目からコンテキストを引き継げる |
| **ネットワーク** | Google Translate エンドポイントへのアクセスが必要（直接または海外プロキシ） | Claude API のみ必要 — Google エンドポイントは一切触れない |
| **速度（要件 100 件あたり）** | 秒単位 — 高速、I/O バウンド | 分単位 — 各項目が独立した推論パス |
| **コスト** | 無料（レート制限あり） | Claude API トークンを消費 |

### 長所と短所

#### Google 翻訳（`-e google`）

**長所**
- **高速** — 高スループット。「十分な品質」でよい場合のクイックファーストパスや
  大量ドキュメントのバッチに最適。
- **トークンコストなし** — Translate API は無料（レート制限内）。
- **予測可能な品質** — 一般的な言語ペア（pt/en、en/es、en/zh）の一般的な文章は
  流暢。

**短所**
- **チャンク分割、コンテキストなし** — 各 ≤ 4 500 文字チャンクが独立して翻訳される
  ため、チャンク境界をまたぐ要件は文間参照を失う。
- **密な技術文章に弱い** — ネストされた条項、相互参照、簡潔な表形式の記述が長い
  仕様書は、めちゃくちゃになったり過小翻訳されたりすることがある（カバレッジ
  チェックが出力を拒否する場合がある）。
- **固有名詞のもろさ** — プレースホルダー処理なしでは、`MDC`、`AMI`、`HPLC` の
  ような頭字語は日常的に小文字化または翻字される。プレースホルダー保護はこれを
  緩和するが、未知の頭字語には完全ではない。
- **外向きネットワークが必要** — Claude API のみに到達可能なロックダウン CI
  ホストからは使用不可。

#### Agent / Claude（`-e agent`）

**長所**
- **コンテキスト対応** — Claude は要件全体、必要に応じて周囲のキューを見て、
  用語の一貫性を保つ（`MDC` は `MDC` のまま、`last-gasp` は計測の意味で解釈）
  し、ネストされた条項をクリーンに処理。
- **密で短い技術文章に最適** — まさに仕様書から抽出された要件の形状。ヒューマン
  グレードの出力を生成。
- **Google 依存なし** — Claude API のみ到達可能な場所で動作。
- **自己一貫性** — Agent はドキュメント全体で繰り返しフレーズの同じ翻訳を
  再利用でき、チャンク分割された Google 翻訳が毎回異なる翻訳を生成する可能性
  がある。

**短所**
- **低速** — 各要件が 1 つの推論パス。400 項目のドキュメントは数分かかる。
  スクリプトはキューをバッチ化し、可能な箇所で Agent ターンを並列化して
  緩和。
- **トークンコスト** — 1 000 トークンごとに課金。大容量ドキュメントは無料の
  Google パスより顕著に高価。
- **長い流暢な文章で変動** — 連続的な叙述段落（要件リストでは稀）の場合、
  流暢なエンジンが忠実に翻訳する代わりに言葉を「改善」することがある。
  本文存続チェックはコンテンツロストを検出するが、スタイルのドリフトは検出
  しない。

### 選択方法

| 状況 | 推奨エンジン |
|---|---|
| クイックプレビュー、大量バッチ、流暢な文章 | `-e google` |
| 密な技術仕様、用語の一貫性が重要 | `-e agent` |
| ロックダウンネットワーク（Claude API のみ到達可能） | `-e agent` |
| Google ドラフトのクリーンアップの 2 パス目 | 最初に Google を実行し、次にキューに対して Agent を実行 |

> **注意:** Agent モードでも `extra_do_not_translate` リストは同様に適用されます。
> Agent は翻訳前に同じ `__PROPER_<uuid>__` プレースホルダーを置換（Google パスが
> 使用するのと同じ `_protect_proper_nouns` / `_restore_proper_nouns` 契約）するため、
> 保護動作はエンジン間で同一です。

---

## 14. 出力形式

Excel ワークシートの列定義（シートタイトルとヘッダーは英語以外のターゲット言語に
ローカライズ）：

| 列 | フィールド | 説明 |
|--------|-------|-------------|
| A | ID | REQ-0001、インクリメント |
| B | 章 | 最上位の章番号 ＋ タイトル |
| C | 節 | サブ章番号 ＋ タイトル |
| D | 原文 | ソース言語の完全な文 |
| E | English translation | 常に存在 |
| F | <選択した言語> translation | ユーザーが選択した言語 |

- ターゲットが `en` ＋ その他の言語 1 つの場合、固定ヘッダー ＋ シートタイトルが
  その言語で描画 — 例：`en + ja` → シート `要求事項`、ヘッダー
  `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`。混在ヘッダーなし。
- ソース言語がターゲットと一致する場合、その列は原文を保持（API 呼び出しなし）。
- 列幅：`[10, 32, 32, 65, 65]`。
- `--display-lang <code>` でヘッダー言語を上書き。

---

## 15. ロードマップ

- [ ] CLI でソース言語を指定可能にする（自動検出をスキップ）
- [ ] docx / odt 出力形式を追加
- [ ] 複数段落マージ戦略を改善（現在は文ベース）
- [ ] 他の言語の公文書への適応を拡大
- [ ] 増分処理：同じ PDF の 2 つのリビジョン間の差分を抽出

---

## 16. ライセンスと帰属

© **Aggre-Cloud 聚云科技** — <https://www.acdatech.com>

Aggre-Cloud（聚云テクノロジー）によって開発およびメンテナンスされています。

Aggre-Cloud（聚云テクノロジー）によって開発およびメンテナンスされています。