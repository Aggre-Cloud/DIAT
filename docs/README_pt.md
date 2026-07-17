# DIaT

> Ferramenta de extração e tradução de requisitos estruturados — extrai
> requisitos hierárquicos de documentos PDF, decompõe por estrutura, traduz e
> exporta um relatório em Excel.

Language: **Português (Brasil)** (este arquivo) · **English** → [`README.md`](../README.md) · **中文** → [`README_zh.md`](README_zh.md) · **Español** → [`README_es.md`](README_es.md) · **Français** → [`README_fr.md`](README_fr.md) · **Deutsch** → [`README_de.md`](README_de.md) · **日本語** → [`README_ja.md`](README_ja.md)

---

## 1. O que é o DIaT? — Contexto do Projeto

### O problema que ele resolve

Projetos internacionais de engenharia, energia e infraestrutura produzem
rotineiramente **documentos PDF estruturados e multilíngues** — licitações,
especificações técnicas, contratos, regulamentos e normas. Esses documentos
compartilham uma forma comum:

- **Numerados hierarquicamente**: uma estrutura de 5 níveis que o parser modela
  internamente como capítulo → seção → artigo → cláusula → item
  (capítulo → seção → artigo → cláusula → item), frequentemente misturando esquemas de numeração
  como `Art. 1º`, `CAPÍTULO`, `1.2.1`, `（1）`, `(a)`, algarismos romanos,
  números circulados. Cada requisito carrega seu `hierarchy_path` completo
  internamente, mas o Excel exportado expõe apenas os dois níveis superiores
  (Capítulo / Seção) como colunas estruturais dedicadas — os níveis mais profundos
  permanecem incorporados no corpo do requisito para que a linha fique legível.
- **Multilíngue**: uma especificação em português para um projeto com
  investimento chinês, um edital em árabe revisado por um contratado alemão,
  um plano de O&M em russo lido por uma equipe brasileira.
- **Com layout pesado**: texto em múltiplas colunas, tabelas incorporadas,
  cabeçalhos e rodapés repetidos e — no pior caso — páginas digitalizadas
  como imagem.

Para um engenheiro de projeto, agente de compras ou revisor técnico, o
trabalho real é: *"extrair cada requisito, saber a qual capítulo ele pertence
e torná-lo legível no meu idioma."* Fazer isso manualmente é lento, sujeito a
erros e não escala para uma pasta de documentos.

### Por que o DIaT

A tradução documento a documento é lenta e frágil. O DIaT substitui o ciclo
manual de copiar-colar → traduzir → remontar por um pipeline determinístico e
auto-validável:

| Capacidade | Manual / Apenas Google Translate | DIaT |
|------------|----------------------------------|------|
| Layout do documento | Copiar-colar por página; texto em múltiplas colunas e tabelas rotineiramente embaralhado | Extração por mesclagem de 4 estratégias (layout → palavras → tabelas → caracteres) com remoção automática de cabeçalho/rodapé |
| Divisão de requisitos | Olhar a numeração — fácil perder itens ou achatar o aninhamento | 12 esquemas de numeração detectados automaticamente (Art. / CAPÍTULO / § / 1.2.1 / （1）/ (a) / romano / circulado …) e uma árvore baseada em pilha que mantém o caminho de capítulo **completo** de cada item |
| Segmentação de frases | Traduzir o parágrafo inteiro — frases longas degradam, quebras se perdem | Melhor prática por idioma de origem (pysbd para escritas latinas, regras de terminador CJK para zh/ja/ko, fallback de regex para os demais) |
| Nomes próprios | Corrompidos pelo mecanismo de tradução (`MDC` → minúsculas, `AMI` deturpado) | Proteção por placeholder com ~30 termos genéricos embutidos mais adição interativa guiada por categoria, restaurados literalmente após a tradução |
| Mecanismo de tradução | Comprometido com um único | Google Translate **e** Agent (Claude) — dois motores alternáveis no mesmo pipeline com layout de saída idêntico |
| Segurança do corpo | A perda de tradução só é percebida depois, se for | Verificação obrigatória de cobertura de multiconjunto de palavras; **< 80% interrompe o pipeline e não emite Excel** — saída parcial é intolerável |
| Idioma de saída | Idioma único, cabeçalhos em vários idiomas | Título da planilha, cabeçalhos estáticos e cabeçalhos de coluna totalmente localizados no idioma de destino — zero mistura |
| Lote | Repetição por arquivo | Lote de diretório completo, flags de CI (`--no-input`) e execução autônoma via Agent |

### O que o DIaT faz

**DIaT** (o nome é um acrônimo provisório) transforma um desses PDFs em uma
pasta de trabalho do Excel estruturada e traduzida com um único comando:

1. **Extrai** o texto do corpo do PDF — mesclagem de 4 estratégias
   (layout → palavras → tabelas → caracteres) com remoção automática de
   cabeçalho/rodapé e fallback de OCR para PDFs digitalizados.
2. **Decompõe** o documento em requisitos hierárquicos, preservando o caminho
   de capítulo/seção de cada item.
3. **Segmenta** as frases por idioma de origem (pt / en / zh / ja / ko / es /
   fr / de / …).
4. **Traduz** cada requisito para dois idiomas de destino — o inglês é sempre
   uma coluna; você escolhe a outra.
5. **Valida** se nenhum texto do corpo foi silenciosamente descartado (aborta
   se a cobertura for < 80% — saída parcial é intolerável).
6. **Exporta** uma pasta de trabalho do Excel: `ID / Capítulo / Seção / Original /
   English / <seu idioma>`.

### Para quem é

- Engenheiros de projeto e agentes de compras que trabalham com especificações
  e editais multilíngues.
- Tradutores técnicos que precisam de uma tradução automática de primeira
  passagem ancorada na estrutura do documento.
- Revisores de conformidade / QA que precisam rastrear cada requisito de volta
  ao seu capítulo de origem.
- Agentes de IA (Claude, etc.) que orquestram pipelines de processamento de
  documentos e precisam de uma ferramenta determinística e auto-validável.

---

## 2. Como Usar — Formas Recomendadas

### ▶ Recomendado: modo interativo (basta executar)

A forma mais simples e recomendada de usar o DIaT é executá-lo
**interativamente** e deixar o script guiá-lo. Você só precisa responder a
três perguntas; todo o resto é automático:

```bash
# Certifique-se de estar na raiz do projeto
cd "<project-root>"

# Execute — é só isso. O script faz 3 perguntas e depois produz o Excel.
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf"
```

Você será solicitado, em ordem:

| # | Pergunta | Padrão |
|---|----------|--------|
| (a) | **Escolha UM idioma de destino que não seja inglês** — o inglês (`en`) é sempre um destino; você escolhe apenas o segundo | `zh-cn` (Chinês Simplificado) |
| (b) | **Escolha o mecanismo de tradução** — `google` (API do Translate) ou `agent` (Claude traduz via fila JSON) | `google` |
| (c) | **Adicione termos de nomes próprios** por categoria (nome de pessoa, código de projeto, empresa, …) — ou pressione Enter para pular | nenhum (sementes genéricas embutidas ~30) |

Após os prompts, o pipeline é executado até o fim e grava o Excel em
`output/<your-file>_requirements.xlsx`.

> **Dica:** se o idioma de origem detectado for igual a um dos seus destinos,
> essa coluna mantém o texto original automaticamente — sem chamada extra de API.

### ▶ Modo não interativo (lote / CI / flags explícitas)

Se você já sabe todas as escolhas e quer pular os prompts, passe as flags
explicitamente:

```bash
# Inglês + Japonês, Google, não interativo
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    -l ja -e google --no-input

# Inglês + Chinês, modo Agent, não interativo
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    -l zh-cn -e agent --no-input

# Extrair + dividir + exportar Excel apenas, sem tradução
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    --no-translate --json --no-input

# Lote de um diretório inteiro (não interativo)
PYTHONIOENCODING=utf-8 python 005_main/main.py ./pdfs --no-input
```

> **Nota:** o inglês (`en`) é sempre adicionado automaticamente — `-l` recebe
> apenas o idioma *que não é inglês*. `-l en` é rejeitado com uma mensagem
> clara.

### ▶ Execução via Agent / automatizada (instalar deps primeiro)

Quando um agente de IA executa o DIaT, as dependências podem não estar
presentes. O script pode instalá-las a partir do `requirements.txt` do próprio
projeto sem intervenção humana:

```bash
# 1. (Opcional) auto-instalar dependências ausentes — não interativo em não-TTY.
#    Pule se você já executou `pip install -r requirements.txt`.
python -m 005_main.main --install-deps

# 2. Também puxar os extras opcionais (melhor segmentação + OCR de PDF digitalizado)
python -m 005_main.main --install-deps --with-optional

# 3. Executar o pipeline real
python -m 005_main.main "your-file.pdf" -l ja -e google --no-input
```

### ▶ Instalação manual humana (um comando)

```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt   # opcional: pysbd + ocrmypdf
```

---

## 3. Instalar o Skill e Invocar o Agent

### Instalando o skill no seu agente

O DIaT é um projeto Python comum — "instalar o skill" significa tornar a
pasta do projeto disponível para o agente para que ele possa executar
`005_main/main.py`.

1. **Clone** o repositório para um local permanente no host do agente
   (ou na sua própria máquina):
   ```bash
   git clone https://github.com/Aggre-Cloud/DIAT.git
   cd DIaT
   ```
2. **Instale as dependências uma vez** (o agente também pode auto-instalar via
   `--install-deps`, mas uma instalação manual é mais rápida):
   ```bash
   pip install -r requirements.txt
   ```
3. **Aponte o agente para a raiz do projeto.** Nenhum registro ou arquivo de
   configuração é necessário — quando quiser processar um PDF, informe ao
   agente o caminho absoluto para a raiz do projeto e o arquivo de entrada:

   ```
   Processe este PDF com o DIaT:
     projeto → D:/Tool Development/Skills Development/DIaT
     entrada  → D:/.../my-spec.pdf
   ```

Essa é toda a "instalação" — um clone mais um `pip install`.

### Comandando o agente para iniciar o trabalho

Uma vez que o projeto esteja no disco do agente e as dependências instaladas,
invoque-o com uma instrução curta. O agente já conhece o skill pelo
`AGENT_GUIDE.md`; sua mensagem só precisa nomear o documento e quaisquer
escolhas fora do padrão. Exemplos:

| Sua mensagem para o agente | O que o agente faz |
|---|---|
| `用 DIaT 处理 02.pdf` | Executa interativamente — pergunta idioma / mecanismo / nomes próprios, depois produz o Excel |
| `用 DIaT 处理 02.pdf，目标语言 ja，Google，不要问` | Não interativo: `-l ja -e google --no-input` |
| `把 spec.pdf 条目化成 Excel，不翻译` | Extrair + dividir + Excel apenas: `--no-translate --json --no-input` |
| `批量处理 ./pdfs 全部，zh-cn，agent 翻译` | Lote do diretório no modo Agent (`-e agent`) |

**Recomendado:** seja conciso e deixe o agente executar os três prompts
(idioma / mecanismo / nomes próprios) — esse fluxo interativo é o caminho
mais seguro e ensina o que a ferramenta pode fazer. Especifique flags (`-l`,
`-e`, `--no-input`) apenas quando quiser deliberadamente pular os prompts.

---

## 4. Protocolo de Execução do Agent — O Que o Agent Deve Recomendar

Quando um agente de IA orquestra o DIaT em nome de um usuário, o
**comportamento recomendado** é:

1. **Usar o interativo como padrão.** NÃO passe `--no-input` em nome do
   usuário — apenas passe quando o usuário pedir explicitamente uma execução
   não interativa / em lote / totalmente automatizada.
2. **Perguntar ao usuário as três perguntas (a) / (b) / (c) acima** antes de
   executar, mesmo que flags de CLI possam fornecer padrões. Esta é a
   checklist obrigatória de pré-execução do projeto (ver `AGENT_GUIDE.md §2`).
3. **Recomendar o caminho interativo** (`python 005_main/main.py "file.pdf"`)
   como a forma principal de usar o skill — é o menos propenso a erros e
   ensina ao usuário o que a ferramenta pode fazer.
4. **Verificar as dependências** antes da primeira execução: invoque
   `--install-deps` se um import necessário estiver ausente e depois execute
   novamente.

A ferramenta é, em última instância, **para pessoas usarem** — o trabalho do
agente é colocar o usuário diante dos três prompts, não decidir
silenciosamente em seu lugar.

---

## 5. Dependências Instaladas

| Pacote | Obrigatório? | Finalidade |
|--------|--------------|------------|
| `openpyxl` | obrigatório | Leitura/escrita de pasta de trabalho do Excel |
| `pdfplumber` | obrigatório | Extração de texto de PDF (mesclagem de 4 estratégias) |
| `PyPDF2` | obrigatório | Sondagem de páginas / metadados de PDF |
| `pypdfium2` | obrigatório | Renderização de PDF / imagens de página |
| `googletrans` | obrigatório | Mecanismo Google Translate (apenas quando `-e google`) |
| `pysbd` | opcional | Segmentação de frases com reconhecimento de idioma (fallback de regex se ausente) |
| `ocrmypdf` | opcional | Fallback de OCR para PDFs digitalizados (precisa de tesseract + ghostscript no sistema) |

---

## 6. Limites de Capability

### ✅ Suportado

| Dimensão | Escopo |
|----------|--------|
| Entrada | Arquivo PDF único ou diretório de PDFs (lote) |
| Tipo de estrutura | Documentos numerados hierarquicamente (contratos, especificações, regulamentos, editais, normas…) |
| Cabeçalhos / rodapés | Detectar blocos repetidos automaticamente (≥ 75% das páginas) e removê-los |
| PDFs digitalizados | Sondar e depois chamar `ocrmypdf --language <config>` para fallback de OCR (import preguiçoso, não dependência rígida) |
| Marcadores de hierarquia | `Art. 1º` / `CAPÍTULO` / `SEÇÃO` / `§ 1º` / `I.` / `1.` / `1.2` / `1.2.1` / `（1）` / `(a)` / `•` / `(1)` / algarismos romanos / números circulados |
| Idioma de origem | pysbd (opcional) + fallback de regex embutido; pt / en / es / fr / de / zh / ja / ko cada um com regras de segmentação dedicadas |
| Idioma de destino | Inglês (fixo) + um idioma escolhido pelo usuário (qualquer googletrans / Claude code) |
| Mecanismo de tradução | Google Translate (direto) ou Agent (Claude traduz por conta própria) |
| Proteção de nomes próprios | Substituição por placeholder (termos genéricos embutidos ~30 + adições fornecidas pelo usuário), restaurados após a tradução |
| Formato de saída | Pasta de trabalho do Excel (ID / Capítulo / Seção / Original / English / <seu idioma>) |
| Validação do corpo | Verificação obrigatória de cobertura; < 80% interrompe o pipeline sem saída |
| Preservação de título | Linhas de cabeçalho são sempre emitidas como parte do corpo de cada requisito (para auditoria de cobertura + rastreamento de contexto); cabeçalhos de corpo vazio são auto-sintetizados |
| Interação padrão | Interativo por padrão — solicita idioma de destino / mecanismo de tradução / adições de nomes próprios; só pula quando o usuário pede explicitamente ou passa `--no-input` |
| Filtragem de linhas de tabela | Ao corresponder um cabeçalho `D1/D2/D3`, rejeita linhas contendo `;` (separador de célula), `(` (anotação de unidade), um " - palavra curta" à direita (par rótulo/valor) ou dígitos — evita interpretar linhas de tabela de PDF como cabeçalhos de seção |

### ⚠️ Pré-requisitos

- O PDF deve ser digital **com texto selecionável**, ou digitalizado com ≥ 200 dpi
- É necessário acesso à API do Google Translate (direta ou via proxy no exterior), a menos que você use o modo Agent
- Runtime: Python 3.9+; dependências listadas no §4
- Arquivos grandes (> 100 páginas) crescem significativamente em tempo de processamento; o fallback de OCR executa ~1-5 s por página

---

## 7. Arquitetura / Pipeline

```
PDF file
   │
   ▼
[003_pdf_extractor]  extract_with_meta()
   │  mesclagem de 4 estratégias: layout → words → tables → chars   (cascateamento de fallback)
   │  removedor de blocos repetidos  +  sentinelas __PAGE_N__
   │  sondagem de PDF digitalizado → ocrmypdf → reabertura
   ▼
raw_text  +  ExtractionMeta
   │
   ▼
[001_text_splitter]  parse_text(raw_text, lang)
   │  ChapterSectionParser  — regex por ordem de prioridade + construtor de pilha
   │  SentenceSegmenter     — regras de melhor prática por idioma
   ▼
ParseResult  { roots, items, meta, raw_rows }
   │
   ├──▶ [007_validator]  assert_body_intact(raw_text, items)
   │       razão de cobertura de multiconjunto de palavras  →  BodyLossError se < 80%
   │
   ▼
[002_translator]  (opcional)  tradução Google / Agent
   │
   ▼
[004_excel_generator]  pasta de trabalho do Excel
        ID | Capítulo | Seção | Original | English | <seu idioma>
```

### Invariantes principais

1. A cobertura do corpo de `raw_text` em `items['content']` **nunca deve cair abaixo de 80%** (limite rígido).
2. Cada página é marcada com um sentinela `__PAGE_N__` para que a atribuição de página sobreviva à remoção de cabeçalho.
3. Cada linha de requisito carrega um `hierarchy_path` completo (ex. `1 Sistemas > 1.2 MDC > 1.2.1 Condições Gerais`).

---

## 8. Estrutura do Projeto

```
DIaT/
├── 001_text_splitter/
│   └── text_splitter.py        # ChapterSectionParser (12 esquemas de numeração, árvore de 5 níveis baseada em pilha) + SentenceSegmenter
├── 002_translator/
│   └── translator.py           # TranslationService (Google + Agent) + auxiliares de cabeçalho/título localizados
├── 003_pdf_extractor/
│   └── pdf_extractor.py        # Extração por mesclagem de 4 estratégias + removedor de blocos repetidos + fallback de OCR
├── 004_excel_generator/
│   └── excel_generator.py      # Saída de planilha Excel única (cabeçalhos localizados; inglês + um idioma do usuário)
├── 005_main/
│   └── main.py                 # Ponto de entrada CLI + orquestração de pipeline + gravador de fila do Agent
├── 006_config/
│   └── config.py               # Configuração global + tabelas ABBR + categorias DO_NOT_TRANSLATE + limites VALIDATION
├── 007_validator/
│   └── validator.py            # assert_body_intact — verificação de sobrevivência do corpo
├── sample doc/                 # PDFs de exemplo (multilíngues) para testes
├── output/                     # Excel gerado + intermediários JSON (ignorados no git)
├── requirements.txt            # dependências de runtime fixadas
├── requirements-optional.txt   # pysbd + ocrmypdf (melhor segmentação, OCR de PDF digitalizado)
├── README.md                   # documentação voltada ao usuário (inglês)
├── docs/
│   ├── README_zh.md            # documentação voltada ao usuário (chinês)
│   ├── README_pt.md            # este arquivo — documentação voltada ao usuário (português)
│   ├── README_es.md            # documentação voltada ao usuário (espanhol)
│   ├── README_fr.md            # documentação voltada ao usuário (francês)
│   ├── README_de.md            # documentação voltada ao usuário (alemão)
│   └── README_ja.md            # documentação voltada ao usuário (japonês)
├── AGENT_GUIDE.md              # princípios de uso para orquestrador / sub-agent
└── LICENSE                     # licença do projeto
```

---

## 9. Argumentos de CLI

| Argumento | Descrição |
|-----------|-----------|
| `input` | Caminho de arquivo PDF ou diretório |
| `-o, --output` | Diretório de saída (padrão `output/`) |
| `--no-translate` | Pular tradução |
| `--json` | Também emitir o intermediário JSON |
| `-l, --lang` | O idioma de destino QUE NÃO É inglês (ex. `pt`, `ja`). O inglês é sempre adicionado automaticamente |
| `-e, --engine` | Mecanismo de tradução `google` (padrão) ou `agent` |
| `--no-input` | Modo não interativo **explícito** (en + zh-cn + Google). O padrão é interativo; passe apenas quando explicitamente solicitado |
| `--display-lang` | Substituir o idioma dos cabeçalho / planilha do Excel (padrão: o destino que não é inglês) |
| `--install-deps` | Instalar pacotes de terceiros ausentes a partir de `requirements.txt` e depois sair. Não interativo quando stdin não é um TTY (agent / pipe); pede confirmação em um TTY |
| `--with-optional` | Combinado com `--install-deps`, também instalar os extras opcionais (`pysbd`, `ocrmypdf`) |

### Regras de seleção de idioma de tradução

1. **O inglês é sempre um destino** — você escolhe apenas o segundo idioma.
2. **Pular se igual à origem** — se o idioma de origem for igual a um destino, essa coluna mantém o texto original (sem chamada de API).
3. **Cabeçalhos localizados** — Cabeçalhos estáticos do Excel, cabeçalhos de coluna e título da planilha são renderizados no idioma de destino que não é inglês (ex. `en + ja` → planilha `要求事項`, cabeçalhos `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`). Sem cabeçalhos em idioma misto.

---

## 10. Fluxo Interativo — Sessão de Exemplo

```
$ PYTHONIOENCODING=utf-8 python 005_main/main.py example.pdf

  =======================================================
    Seleção do Idioma de Tradução de Destino
  =======================================================
  Origem detectada: pt (Português)

    O inglês (en) é sempre um destino.
    Escolha UM idioma adicional para a segunda coluna.
    Padrão: zh-cn
    zh-cn    — 中文（简体）
    pt       — Português ← origem
    es       — Español
    ...

  Enter 1 language code (ou pressione Enter para o padrão zh-cn): pt
  → Destinos: en + pt
  ⚠ Origem é pt (Português) → a coluna em Português exibirá o texto original.

  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Seleção do Mecanismo de Tradução
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    1. Google Translate API   (padrão — rápido, externo)
    2. Agent  — Claude lê JSON, traduz, grava de volta

  Enter 1 ou 2 (ou pressione Enter para o padrão Google): 1

  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Proteção de Nomes Próprios
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  As seguintes categorias de termos são mantidas literalmente durante a tradução:
    [abreviações técnicas]  API, HTTP, HTTPS, JSON, XML, CSV, TCP, UDP, IP, VPN, … (17)
    [organismos de norma]   IEC, IEEE, ISO, ITU, ANSI, IETF, W3C                (7)
    [rede / infraestrutura] RF, PLC, LAN, WAN, HAN                              (5)
    [unidades de medida]    GWh, MWh, kWh, Hz, kV, kW, kVA, MVA, ms, s        (10)
    [empresas / produtos]   Google, Microsoft, Amazon, Apple                     (4)

  As seguintes categorias iniciam vazias e são preenchidas por documento:
     1. Nomes de pessoas        6. Órgãos reguladores
     2. Nomes de lugares        7. Referências legais / documentais
     3. Códigos de produto / projeto  8. Termos específicos do setor
     4. Empresa (este documento) 9. Papéis / responsabilidades
    10. ＋ Criar uma nova categoria…
     0. Concluir — seguir para a tradução

  Selecione um número de categoria (1-10 para adicionar, 0=concluir): 3
  → [Códigos de produto / projeto] atualmente vazio
    Adicione termos separados por vírgula (Enter para pular): SCADA,AMI,MDM,MDC
    + 4 termo(s) adicionado(s).

  Selecione um número de categoria (1-10 para adicionar, 0=concluir): 0
  ✓ Proteção de nomes próprios configurada. 1 categoria, 4 termos no total.

  [3/4] Traduzindo (engine=google, languages=['en', 'pt'])...
  ...

  [OK] Concluído!
  [OK] Arquivo de saída: output/example_requirements.xlsx
  [OK] Total de requisitos: 393
  [OK] Requisitos válidos: 393 (100.0%)
  [OK] Cobertura do corpo: 100.7%
```

---

## 11. Garantia de Preservação do Corpo

A perda silenciosa do corpo é **intolerável** — o `007_validator` é executado incondicionalmente antes de o Excel ser gerado:

1. Percorre `raw_text` linha a linha, pulando linhas de cabeçalho/rodapé/sumário → produz `body_lines`.
2. Normaliza cada `item['content']` em um multiconjunto de palavras.
3. Correspondência gulosa: `coverage = Σ palavras_cobertas / Σ palavras_do_corpo`.
4. Cobertura `< 80%` → levanta `BodyLossError`, **interrompe o pipeline, nenhum Excel é emitido**.
5. Linhas descobertas são gravadas em `{prefix}_orphans.json` para triagem.

A normalização léxica dobra todo espaço em branco em um único espaço antes de dividir em tokens, para que diferenças de indentação de quebra de linha geradas pelo pdfplumber não sejam contabilizadas indevidamente como perda de corpo.

Os limites ficam em `006_config/config.py::VALIDATION`:

```python
VALIDATION = {
    'min_char_coverage': 0.80,   # taxa mínima de sobrevivência do corpo
    'min_word_coverage': 0.85,
    'write_orphans': True,
    'sentence_target_min': 50,    # mín de caracteres por frase
    'sentence_target_max': 500,   # máx de caracteres por frase
}
```

---

## 12. Proteção de Nomes Próprios

Antes da tradução, as seguintes classes de termos são substituídas por placeholders
`__PROPER_<uuid>__` para que o Google Translate as deixe intocadas, e são
restauradas depois:

`006_config/config.py::DO_NOT_TRANSLATE` é um **dicionário categorizado**
(`category → {label, items}`); a semente embutida contém apenas **termos
genéricos interindustriais** (~30), organizados por categoria:

- Abreviações técnicas (API, HTTP, HTTPS, JSON, XML, CSV, TCP, UDP, IP, SSH, …)
- Organismos de norma (IEC, IEEE, ISO, ITU, ANSI, IETF, W3C)
- Rede / infraestrutura (RF, PLC, LAN, WAN, HAN)
- Unidades de medida (GWh, MWh, kWh, Hz, kV, kW, kVA, MVA, ms, s)
- Nomes genéricos de empresas / produtos (Google, Microsoft, Amazon, Apple)

As seguintes são **categorias vazias** preenchidas durante o passo interativo (c)
em base por documento: nomes de pessoas, nomes de lugares, códigos de produto /
projeto, empresa (este documento), órgãos reguladores, referências legais /
documentais, termos específicos do setor, papéis / responsabilidades — e o
usuário pode **criar categorias novas arbitrárias** em runtime.

> O conjunto de categorias é **aberto**: termos específicos do setor (ex.
> `SCADA/AMI/MDM/MDC` para concessionárias de energia, nomes de medicamentos
> para saúde, nomes de tribunais para direito) **não** são semente versionada —
> o usuário os preenche na categoria correspondente ao processar um documento
> concreto. Este é o mecanismo central da ferramenta para generalização
> interindustrial.

**Mecanismo** (`002_translator/translator.py`):

```
original
  │
  ▼
_protect_proper_nouns()        ← substitui termos DO_NOT_TRANSLATE por placeholders
  │
  ▼
Google Translate API
  │
  ▼
_restore_proper_nouns()        ← substitui placeholders de volta pelos termos originais
  │
  ▼
tradução
```

A lista de termos é ordenada por comprimento decrescente para que `Advanced Metering`
seja correspondido antes de `AMI`.

---

## 13. Mecanismos de Tradução — Google vs. Agent

O DIaT oferece dois mecanismos de tradução intercambiáveis selecionáveis com
`-e google` (padrão) ou `-e agent`. Ambos alimentam o mesmo layout de Excel,
ambos respeitam a mesma proteção de nomes próprios e ambos são validados pela
mesma verificação de sobrevivência do corpo. Eles diferem em *quem* traduz e
*como*.

### Como funcionam

| | Google Translate (`-e google`) | Agent / Claude (`-e agent`) |
|---|---|---|
| **Executor** | API do Google Translate, chamada pedaço a pedaço a partir de `TranslationService._translate_with_google` | O agente de IA (Claude) lê uma fila JSON e grava as traduções de volta |
| **Handshake** | Direto, em processo | `main.py` grava `*_agent_queue.json` (idioma de origem, idiomas de destino, requisitos, `extra_do_not_translate`) → agente traduz → agente chama `write_translations_to_excel()` |
| **Janela de contexto** | Um pedaço por vez (≤ 4 500 caracteres); sem memória entre requisitos | A fila inteira está disponível; o agente pode impor consistência terminológica entre requisitos e carregar contexto de itens anteriores |
| **Rede** | Precisa de acesso ao endpoint do Google Translate (direto ou via proxy no exterior) | Só precisa da API do Claude — os endpoints do Google nunca são tocados |
| **Velocidade (por 100 requisitos)** | Segundos — rápido, limitado por E/S | Minutos — cada item é um passo de raciocínio separado |
| **Custo** | Gratuito (com limite de taxa) | Consome tokens da API do Claude |

### Prós e contras

#### Google Translate (`-e google`)

**Prós**
- **Rápido** — alto throughput; ideal para uma primeira passagem rápida ou um
  grande lote de documentos onde "bom o suficiente" é aceitável.
- **Sem custo de token** — a API do Translate é gratuita (dentro dos limites de taxa).
- **Qualidade previsível** — para pares de idiomas comuns (pt/en, en/es, en/zh)
  a prosa geral é fluente.

**Contras**
- **Fragmentado, sem contexto** — cada pedaço de ≤ 4 500 caracteres é traduzido
  isoladamente, então um requisito dividido com a fronteira de um pedaço perde
  referência entre frases.
- **Mais fraco em prosa técnica densa** — especificações longas com cláusulas
  aninhadas, referências cruzadas e declarações tabulares concisas podem voltar
  truncadas ou subtraduzidas (a verificação de cobertura pode então se recusar
  a emitir).
- **Fragilidade com nomes próprios** — sem a passada de placeholder, acrônimos
  como `MDC`, `AMI`, `HPLC` são rotineiramente convertidos para minúsculas ou
  transliterados; a proteção por placeholder mitiga isso, mas não é infalível
  para acrônimos nunca vistos.
- **Precisa de rede de saída** — inutilizável a partir de um host CI bloqueado
  que só alcança a API do Claude.

#### Agent / Claude (`-e agent`)

**Prós**
- **Consciente de contexto** — Claude vê o requisito inteiro e, quando
  necessário, a fila ao redor, então mantém a terminologia consistente (`MDC`
  permanece `MDC`, `last-gasp` é interpretado no sentido de medição) e trata
  cláusulas aninhadas com clareza.
- **Melhor para prosa técnica densa e curta** — exatamente a forma dos
  requisitos extraídos de especificações; produz saída de nível humano.
- **Sem dependência do Google** — funciona onde apenas a API do Claude é alcançável.
- **Autoconsistente** — o agente pode reutilizar a mesma tradução de uma frase
  repetida em todo o documento, o que o Google Translate fragmentado pode
  renderizar diferentemente a cada vez.

**Contras**
- **Mais lento** — cada requisito é um passo de raciocínio; um documento de
  400 itens leva vários minutos. O script mitiga isso agrupando a fila e
  paralelizando as voltas do agente onde possível.
- **Custo de token** — cobrado por 1 000 tokens; documentos grandes são
  visivelmente mais caros que o caminho gratuito do Google.
- **Variável em prosa longa e fluente** — para parágrafos narrativos contínuos
  (raros em listas de requisitos), um mecanismo fluente pode ocasionalmente
  "melhorar" a redação em vez de traduzir fielmente; a verificação de
  sobrevivência do corpo captura a perda de conteúdo, mas não o desvio estilístico.

### Como escolher

| Situação | Mecanismo recomendado |
|---|---|
| Visualização rápida, lote grande, prosa fluente | `-e google` |
| Especificações técnicas densas, consistência terminológica importa | `-e agent` |
| Rede bloqueada (só API do Claude alcançável) | `-e agent` |
| Segunda passagem para limpar um rascunho do Google | executar o Google primeiro, depois o Agent na fila |

> **Nota:** no modo Agent, a lista `extra_do_not_translate` é igualmente aplicada;
> o agente substitui os mesmos placeholders `__PROPER_<uuid>__` antes da
> tradução (o mesmo contrato `_protect_proper_nouns` / `_restore_proper_nouns`
> que o caminho do Google usa), então o comportamento de proteção é idêntico
> entre os mecanismos.

---

## 14. Formato de Saída

Definição de colunas da planilha do Excel (título da planilha e cabeçalhos
localizados no idioma de destino que não é inglês):

| Coluna | Campo | Descrição |
|--------|-------|-----------|
| A | ID | REQ-0001, incrementando |
| B | Capítulo | Número + título do capítulo de nível superior |
| C | Seção | Número + título do subcapítulo |
| D | Original | Frase completa no idioma de origem |
| E | English translation | Sempre presente |
| F | <seu idioma> translation | O idioma escolhido pelo usuário |

- Quando os destinos são `en` + um outro idioma, os cabeçalhos estáticos + título
  da planilha são renderizados nesse idioma — ex. `en + ja` → planilha
  `要求事項`, cabeçalhos `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`.
  Sem cabeçalhos em idioma misto.
- Quando o idioma de origem corresponde a um destino, essa coluna mantém o
  texto original (sem chamada de API).
- Larguras de coluna: `[10, 32, 32, 65, 65]`.
- Substitua o idioma dos cabeçalhos com `--display-lang <code>`.

---

## 15. Roadmap

- [ ] Permitir especificar o idioma de origem na CLI (pular detecção automática)
- [ ] Adicionar formatos de saída docx / odt
- [ ] Melhorar a estratégia de mesclagem de múltiplos parágrafos (atualmente baseada em frases)
- [ ] Adaptação mais ampla a documentos oficiais em outros idiomas
- [ ] Processamento incremental: extrair deltas entre duas revisões do mesmo PDF

---

## 16. Licença e Atribuição

© **Aggre-Cloud 聚云科技** — <https://www.acdatech.com>

Desenvolvido e mantido pela Aggre-Cloud (聚云科技).
 