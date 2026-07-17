# DIaT

> Herramienta de extracción y traducción de requisitos estructurados — extrae
> requisitos jerárquicos de documentos PDF, los descompone por estructura, los
> traduce y exporta un informe en Excel.

Idioma: **Español** (este archivo) · **English** → [`README.md`](../README.md) · **中文** → [`README_zh.md`](README_zh.md) · **Português (Brasil)** → [`README_pt.md`](README_pt.md) · **Français** → [`README_fr.md`](README_fr.md) · **Deutsch** → [`README_de.md`](README_de.md) · **日本語** → [`README_ja.md`](README_ja.md)

---

## 1. ¿Qué es DIaT? — Antecedentes del proyecto

### El problema que resuelve

Los proyectos internacionales de ingeniería, energía e infraestructura producen
rutinariamente **documentos PDF estructurados y multilingües** — licitaciones,
especificaciones técnicas, contratos, normativas y estándares.  Estos documentos
comparten una forma común:

- **Numeración jerárquica**: una estructura de 5 niveles que el analizador modela
  internamente como capítulo → sección → artículo → cláusula → ítem
  (capítulo → sección → artículo → cláusula → item), que a menudo combina esquemas de numeración como
  `Art. 1º`, `CAPÍTULO`, `1.2.1`, `（1）`, `(a)`, números romanos, números
  circulares.  Cada requisito lleva internamente su `hierarchy_path` completo,
  pero el Excel exportado expone solo los dos niveles superiores (Capítulo / Sección) como
  columnas estructurales dedicadas — los niveles más profundos permanecen
  integrados en el cuerpo del requisito para que la fila siga siendo legible.
- **Multilingüe**: una especificación en portugués para un proyecto respaldado
  por China, una licitación en árabe revisada por un contratista alemán, un plan
  de O&M en ruso leído por un equipo brasileño.
- **Diseño complejo**: texto en múltiples columnas, tablas incrustadas,
  encabezados y pies de página repetidos y, en el peor de los casos, páginas
  escaneadas como imágenes.

Para un ingeniero de proyecto, responsable de compras o revisor técnico, el
trabajo real es: *"extraer cada requisito, saber a qué capítulo pertenece y
hacerlo legible en mi idioma."*  Hacer esto a mano es lento, propenso a errores
y no es escalable en una carpeta de documentos.

### Por qué DIaT

La traducción documento por documento es lenta y frágil.  DIaT reemplaza el
bucle manual de copiar-pegar → traducir → reensamblar con un único pipeline
determinista y autovalidante:

| Capacidad | Manual / solo Google Translate | DIaT |
|-----------|-------------------------------|------|
| Diseño del documento | Copiar-pegar por página; el texto en columnas múltiples y tablas se desordena habitualmente | Extracción por fusión de 4 estrategias (layout → words → tables → chars) con eliminación automática de encabezados/pies de página |
| División de requisitos | Identificar la numeración a ojo — es fácil omitir ítems o aplanar la anidación | 12 esquemas de numeración detectados automáticamente (Art. / CAPÍTULO / § / 1.2.1 / （1）/ (a) / romano / circular …) y un árbol basado en pila que mantiene la **ruta completa** del capítulo de cada ítem |
| Segmentación de oraciones | Traducir el párrafo completo — las oraciones largas se degradan, se pierden las pausas | Mejor práctica por idioma de origen (pysbd para escrituras latinas, reglas de terminación CJK para zh/ja/ko, regex para el resto) |
| Nombres propios | Corrompidos por el motor de traducción (`MDC` → minúsculas, `AMI` deformado) | Protección con marcadores de posición con ~30 términos genéricos integrados más adición interactiva guiada por categorías, restaurados textualmente tras la traducción |
| Motor de traducción | Comprometerse con uno solo | Motores duales Google Translate **y** Agent (Claude) — conmutables en el mismo pipeline con idéntica disposición de salida |
| Seguridad del cuerpo | La pérdida de traducción solo se detecta a posteriori, si es que se detecta | Verificación obligatoria de cobertura de multiconjunto de palabras; **< 80% detiene el pipeline y no emite Excel** — la salida parcial es intolerable |
| Idioma de salida | Idioma único, encabezados en varios idiomas | Título de la hoja, encabezados estáticos y encabezados de columna completamente localizados al idioma de destino — sin mezcla |
| Procesamiento por lotes | Repetición por archivo | Procesamiento por lotes de todo el directorio, flags de CI (`--no-input`) y ejecución autónoma del Agent |

### Lo que hace DIaT

**DIaT** (el nombre es un acrónimo provisional) convierte uno de esos PDF en un
libro de Excel estructurado y traducido con un solo comando:

1. **Extraer** el texto del cuerpo del PDF — fusión de 4 estrategias
   (layout → words → tables → chars) con eliminación automática de
   encabezados/pies de página y OCR de respaldo para PDF escaneados.
2. **Descomponer** el documento en requisitos jerárquicos, preservando la ruta
   de capítulo/sección de cada ítem.
3. **Segmentar** las oraciones según el idioma de origen (pt / en / zh / ja /
   ko / es / fr / de / …).
4. **Traducir** cada requisito a dos idiomas de destino — el inglés es siempre
   una columna; usted elige la otra.
5. **Validar** que no se haya perdido texto del cuerpo silenciosamente (anula si
   la cobertura < 80% — la salida parcial es intolerable).
6. **Exportar** un libro de Excel: `ID / Capítulo / Sección / Original / English / <su
   idioma>`.

### Para quién es

- Ingenieros de proyecto y personal de compras que trabajan con especificaciones
  y licitaciones multilingües.
- Traductores técnicos que necesitan una traducción automática preliminar
  anclada a la estructura del documento.
- Revisores de conformidad / QA que necesitan rastrear cada requisito hasta su
  capítulo de origen.
- Agentes de IA (Claude, etc.) que orquestan pipelines de procesamiento de
  documentos y necesitan una herramienta determinista y autovalidante.

---

## 2. Cómo usarlo — Formas recomendadas

### ▶ Recomendado: modo interactivo (simplemente ejecútelo)

La forma más sencilla y recomendada de usar DIaT es ejecutarlo de forma
**interactiva** y dejar que el script le guíe.  Solo necesita responder tres
preguntas; todo lo demás es automático:

```bash
# Asegúrese de estar en la raíz del proyecto
cd "<project-root>"

# Ejecutar — eso es todo.  El script le hace 3 preguntas y luego produce el Excel.
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf"
```

Se le preguntará, en orden:

| # | Pregunta | Valor predeterminado |
|---|----------|----------------------|
| (a) | **Elija UN idioma de destino que no sea inglés** — el inglés (`en`) siempre es un destino; usted solo elige el segundo | `zh-cn` (chino simplificado) |
| (b) | **Elija el motor de traducción** — `google` (API de Translate) o `agent` (Claude traduce mediante cola JSON) | `google` |
| (c) | **Añada términos de nombres propios** por categoría (nombre de persona, código de proyecto, empresa, …) — o pulse Enter para omitir | ninguno (semilla genérica integrada de ~30 términos) |

Tras las preguntas, el pipeline se ejecuta hasta completarse y escribe el Excel
en `output/<your-file>_requirements.xlsx`.

> **Consejo:** si el idioma de origen detectado automáticamente coincide con uno
> de sus destinos, esa columna conserva el texto original automáticamente — sin
> llamada API adicional.

### ▶ Modo no interactivo (por lotes / CI / flags explícitos)

Si ya conoce todas las opciones y desea omitir las preguntas, pase los flags
explícitamente:

```bash
# Inglés + japonés, Google, no interactivo
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    -l ja -e google --no-input

# Inglés + chino, modo Agent, no interactivo
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    -l zh-cn -e agent --no-input

# Extraer + dividir + exportar solo Excel, sin traducción
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    --no-translate --json --no-input

# Procesar por lotes un directorio completo (no interactivo)
PYTHONIOENCODING=utf-8 python 005_main/main.py ./pdfs --no-input
```

> **Nota:** el inglés (`en`) siempre se añade automáticamente — `-l` solo toma
> el idioma *que no es inglés*.  `-l en` se rechaza con un mensaje claro.

### ▶ Ejecución con Agent / automatizada (instalar dependencias primero)

Cuando un agente de IA ejecuta DIaT, las dependencias pueden no estar
presentes.  El script puede instalarlas desde el propio `requirements.txt` del
proyecto sin intervención humana:

```bash
# 1. (Opcional) auto-instalar dependencias faltantes — no interactivo en un no-TTY.
#    Omita si ya ejecutó `pip install -r requirements.txt`.
python -m 005_main.main --install-deps

# 2. También instalar los extras opcionales (mejor segmentación + OCR para PDF escaneados)
python -m 005_main.main --install-deps --with-optional

# 3. Ejecutar el pipeline real
python -m 005_main.main "your-file.pdf" -l ja -e google --no-input
```

### ▶ Instalación manual humana (un solo comando)

```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt   # opcional: pysbd + ocrmypdf
```

---

## 3. Instalación del Skill e invocación del Agent

### Instalación del skill en su agente

DIaT es un proyecto Python normal — "instalar el skill" significa hacer la
carpeta del proyecto disponible para el agente para que pueda ejecutar
`005_main/main.py`.

1. **Clonar** el repositorio en una ubicación permanente en el host del agente
   (o en su propia máquina):
   ```bash
   git clone https://github.com/Aggre-Cloud/DIAT.git
   cd DIaT
   ```
2. **Instalar las dependencias una vez** (el agente también puede auto-instalar
   mediante `--install-deps`, pero una instalación manual es más rápida):
   ```bash
   pip install -r requirements.txt
   ```
3. **Indicar al agente la raíz del proyecto.**  No se necesita registro ni
   archivo de configuración — cuando quiera procesar un PDF, indique al agente
   la ruta absoluta a la raíz del proyecto y al archivo de entrada:

   ```
   Procesar este PDF con DIaT:
     project → D:/Tool Development/Skills Development/DIaT
     input   → D:/.../my-spec.pdf
   ```

Eso es toda la "instalación" — una clonación más un `pip install`.

### Cómo ordenar al agente que comience a trabajar

Una vez que el proyecto está en el disco del agente y las dependencias están
instaladas, invóquelo con una instrucción breve.  El agente ya conoce el skill
desde `AGENT_GUIDE.md`; su mensaje solo necesita nombrar el documento y
cualquier opción no predeterminada.  Ejemplos:

| Su mensaje al agente | Lo que hace el agente |
|---|---|
| `用 DIaT 处理 02.pdf` | Ejecuta interactivamente — pregunta por idioma / motor / nombres propios, luego produce el Excel |
| `用 DIaT 处理 02.pdf，目标语言 ja，Google，不要问` | No interactivo: `-l ja -e google --no-input` |
| `把 spec.pdf 条目化成 Excel，不翻译` | Extraer + dividir + solo Excel: `--no-translate --json --no-input` |
| `批量处理 ./pdfs 全部，zh-cn，agent 翻译` | Procesar el directorio por lotes en modo Agent (`-e agent`) |

**Recomendado:** sea conciso y deje que el agente ejecute las tres preguntas
(idioma / motor / nombres propios) — ese flujo interactivo es la vía más
segura y le enseña lo que la herramienta puede hacer.  Solo especifique flags
(`-l`, `-e`, `--no-input`) cuando deliberadamente quiera omitir las preguntas.

---

## 4. Protocolo de ejecución del Agent — Lo que el Agent debe recomendar

Cuando un agente de IA orquesta DIaT en nombre de un usuario, **el
comportamiento recomendado** es:

1. **Usar interactivo como predeterminado.**  NO pasar `--no-input` en nombre
   del usuario — solo pasarlo cuando el usuario solicite explícitamente una
   ejecución no interactiva / por lotes / totalmente automatizada.
2. **Hacer al usuario las tres preguntas (a) / (b) / (c) anteriores** antes de
   ejecutar, incluso si los flags de CLI podrían proporcionar valores
   predeterminados.  Esta es la lista de verificación obligatoria previa a la
   ejecución del proyecto (ver `AGENT_GUIDE.md §2`).
3. **Recomendar la vía interactiva** (`python 005_main/main.py "file.pdf"`)
   como la forma principal de usar el skill — es la menos propensa a errores y
   enseña al usuario lo que la herramienta puede hacer.
4. **Verificar las dependencias** antes de la primera ejecución: invocar
   `--install-deps` si falta un import requerido, luego volver a ejecutar.

La herramienta es, en última instancia, **para que la usen las personas** — el
trabajo del agente es poner al usuario frente a las tres preguntas, no decidir
silenciosamente en su nombre.

---

## 5. Dependencias instaladas

| Paquete | ¿Requerido? | Propósito |
|---------|-------------|-----------|
| `openpyxl` | requerido | Lectura/escritura de libros de Excel |
| `pdfplumber` | requerido | Extracción de texto de PDF (fusión de 4 estrategias) |
| `PyPDF2` | requerido | Sondeo de páginas / metadatos de PDF |
| `pypdfium2` | requerido | Renderizado de PDF / imágenes de página |
| `googletrans` | requerido | Motor Google Translate (solo cuando `-e google`) |
| `pysbd` | opcional | Segmentación de oraciones con conciencia de idioma (respaldo regex si ausente) |
| `ocrmypdf` | opcional | Respaldo OCR para PDF escaneados (necesita tesseract + ghostscript del sistema) |

---

## 6. Límites de capacidad

### ✅ Compatible

| Dimensión | Alcance |
|-----------|---------|
| Entrada | Archivo PDF individual, o directorio de PDF (por lotes) |
| Tipo de estructura | Documentos con numeración jerárquica (contratos, especificaciones, normativas, licitaciones, estándares…) |
| Encabezados / pies de página | Detección automática de bloques repetidos (≥ 75% de las páginas) y eliminación |
| PDF escaneados | Sondear, luego llamar a `ocrmypdf --language <config>` para respaldo OCR (importación diferida, no dependencia dura) |
| Marcadores de jerarquía | `Art. 1º` / `CAPÍTULO` / `SEÇÃO` / `§ 1º` / `I.` / `1.` / `1.2` / `1.2.1` / `（1）` / `(a)` / `•` / `(1)` / números romanos / números circulares |
| Idioma de origen | `pysbd` (opcional) + respaldo regex integrado; pt / en / es / fr / de / zh / ja / ko tienen cada uno reglas de segmentación dedicadas |
| Idioma de destino | Inglés (fijo) + un idioma elegido por el usuario (cualquiera de googletrans / Claude code) |
| Motor de traducción | Google Translate (directo) o Agent (Claude traduce por sí mismo) |
| Protección de nombres propios | Sustitución con marcadores de posición (semilla genérica integrada de ~30 términos + adiciones proporcionadas por el usuario), restaurados tras la traducción |
| Formato de salida | Libro de Excel (ID / Capítulo / Sección / Original / English / <su idioma>) |
| Validación del cuerpo | Verificación de cobertura obligatoria; < 80% detiene el pipeline sin salida |
| Preservación del título | Las líneas de encabezado siempre se emiten como parte del cuerpo de cada requisito (para auditoría de cobertura + rastreo de contexto); los encabezados con cuerpo vacío se sintetizan automáticamente |
| Interacción predeterminada | Interactivo por defecto — pregunta por idioma de destino / motor de traducción / adiciones de nombres propios; solo omite cuando el usuario lo solicita explícitamente o pasa `--no-input` |
| Filtrado de filas de tabla | Al hacer coincidir un encabezado `D1/D2/D3`, rechaza filas que contengan `;` (separador de celdas), `(` (anotación de unidad), un " - palabra corta" final (par etiqueta/valor) o dígitos — evita leer erróneamente filas de tablas PDF como encabezados de sección |

### ⚠️ Prerrequisitos

- El PDF debe ser digital **seleccionable por texto**, o escaneado a ≥ 200 dpi
- Se requiere acceso a la API de Google Translate (directa o mediante proxy en el extranjero) a menos que use el modo Agent
- Entorno de ejecución: Python 3.9+; dependencias listadas en §4
- Los archivos grandes (> 100 páginas) aumentan significativamente el tiempo de procesamiento; el respaldo OCR se ejecuta ~1-5 s por página

---

## 7. Arquitectura / Pipeline

```
PDF file
   │
   ▼
[003_pdf_extractor]  extract_with_meta()
   │  Fusión de 4 estrategias: layout → words → tables → chars   (cascada de respaldo)
   │  eliminador de bloques repetidos  +  centinelas __PAGE_N__
   │  sondeo de PDF escaneado → ocrmypdf → re-apertura
   ▼
raw_text  +  ExtractionMeta
   │
   ▼
[001_text_splitter]  parse_text(raw_text, lang)
   │  ChapterSectionParser  — regex por orden de prioridad + constructor de pila
   │  SentenceSegmenter     — reglas de mejor práctica por idioma
   ▼
ParseResult  { roots, items, meta, raw_rows }
   │
   ├──▶ [007_validator]  assert_body_intact(raw_text, items)
   │       ratio de cobertura de multiconjunto de palabras  →  BodyLossError si < 80%
   │
   ▼
[002_translator]  (opcional)  traducción Google / Agent
   │
   ▼
[004_excel_generator]  libro de Excel
        ID | Capítulo | Sección | Original | English | <su idioma>
```

### Invariantes clave

1. La cobertura del cuerpo de `raw_text` en `items['content']` **nunca debe caer por debajo del 80%** (umbral duro).
2. Cada página se marca con un centinela `__PAGE_N__` para que la atribución de página sobreviva a la eliminación de encabezados.
3. Cada fila de requisito lleva un `hierarchy_path` completo (p. ej. `1 Sistemas > 1.2 MDC > 1.2.1 Condições Gerais`).

---

## 8. Estructura del proyecto

```
DIaT/
├── 001_text_splitter/
│   └── text_splitter.py        # ChapterSectionParser (12 esquemas de numeración, árbol de 5 niveles basado en pila) + SentenceSegmenter
├── 002_translator/
│   └── translator.py           # TranslationService (Google + Agent) + asistentes de encabezado/título localizados
├── 003_pdf_extractor/
│   └── pdf_extractor.py        # Extracción por fusión de 4 estrategias + eliminador de bloques repetidos + respaldo OCR
├── 004_excel_generator/
│   └── excel_generator.py      # Salida de Excel en una sola hoja (encabezados localizados; inglés + un idioma del usuario)
├── 005_main/
│   └── main.py                 # Punto de entrada CLI + orquestación del pipeline + escritor de cola del agente
├── 006_config/
│   └── config.py               # Configuración global + tablas ABBR + categorías DO_NOT_TRANSLATE + umbrales VALIDATION
├── 007_validator/
│   └── validator.py            # assert_body_intact — verificación de supervivencia del cuerpo
├── sample doc/                 # PDF de ejemplo (multilingües) para pruebas
├── output/                     # Excel generado + JSON intermedios (ignorado por git)
├── requirements.txt            # dependencias de tiempo de ejecución fijadas
├── requirements-optional.txt   # pysbd + ocrmypdf (mejor segmentación, OCR para PDF escaneados)
├── docs/
│   ├── README_es.md            # este archivo — documentación para el usuario (español)
│   ├── README_pt.md            # documentación para el usuario (portugués)
│   ├── README_fr.md            # documentación para el usuario (francés)
│   ├── README_de.md            # documentación para el usuario (alemán)
│   └── README_ja.md            # documentación para el usuario (japonés)
├── AGENT_GUIDE.md              # principios de uso del orquestador / sub-agente
└── LICENSE                     # licencia del proyecto
```

---

## 9. Argumentos CLI

| Argumento | Descripción |
|-----------|-------------|
| `input` | Ruta de archivo PDF o directorio |
| `-o, --output` | Directorio de salida (predeterminado `output/`) |
| `--no-translate` | Omitir traducción |
| `--json` | También emitir el JSON intermedio |
| `-l, --lang` | El idioma de destino QUE NO ES inglés (p. ej. `pt`, `ja`). El inglés siempre se añade automáticamente |
| `-e, --engine` | Motor de traducción `google` (predeterminado) o `agent` |
| `--no-input` | Modo no interactivo **explícito** (en + zh-cn + Google). El predeterminado es interactivo; solo pasar cuando se solicite explícitamente |
| `--display-lang` | Sobrescribir el idioma de encabezado / hoja de Excel (predeterminado: el destino que no es inglés) |
| `--install-deps` | Instalar paquetes de terceros faltantes desde `requirements.txt`, luego salir. No interactivo cuando stdin no es un TTY (agente / tubería); pide confirmación en un TTY |
| `--with-optional` | Combinado con `--install-deps`, también instalar los extras opcionales (`pysbd`, `ocrmypdf`) |

### Reglas de selección de idioma de traducción

1. **El inglés siempre es un destino** — usted solo elige el segundo idioma.
2. **Omisión por coincidencia de origen** — si el idioma de origen coincide con un destino, esa columna conserva el texto original (sin llamada API).
3. **Encabezados localizados** — los encabezados estáticos de Excel, encabezados de columna y título de hoja se muestran en el idioma de destino que no es inglés (p. ej. `en + ja` → hoja `要求事項`, encabezados `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`).  Sin encabezados en varios idiomas.

---

## 10. Flujo interactivo — Sesión de ejemplo

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

## 11. Garantía de preservación del cuerpo

La pérdida silenciosa del cuerpo es **intolerable** — `007_validator` se ejecuta incondicionalmente antes de generar el Excel:

1. Recorrer `raw_text` línea por línea, omitiendo filas de encabezado/pie/índice → producir `body_lines`.
2. Normalizar cada `item['content']` a un multiconjunto de palabras.
3. Coincidencia voraz: `coverage = Σ covered_words / Σ body_words`.
4. Cobertura `< 80%` → lanzar `BodyLossError`, **detener el pipeline, no se emite Excel**.
5. Las líneas no cubiertas se escriben en `{prefix}_orphans.json` para triaje.

La normalización léxica pliega todo los espacios en blanco a un único espacio antes de dividir en tokens, de modo que las diferencias de sangría de salto de línea introducidas por pdfplumber no se cuenten erróneamente como pérdida del cuerpo.

Los umbrales residen en `006_config/config.py::VALIDATION`:

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

## 12. Protección de nombres propios

Antes de la traducción, las siguientes clases de términos son reemplazadas por marcadores de posición `__PROPER_<uuid>__` para que Google Translate no las toque, y se restauran después:

`006_config/config.py::DO_NOT_TRANSLATE` es un **diccionario categorizado**
(`category → {label, items}`); la semilla integrada contiene solo
**términos genéricos multi-industria** (~30), organizados por categoría:

- Abreviaturas técnicas (API, HTTP, HTTPS, JSON, XML, CSV, TCP, UDP, IP, SSH, …)
- Organismos de estándares (IEC, IEEE, ISO, ITU, ANSI, IETF, W3C)
- Red / infraestructura (RF, PLC, LAN, WAN, HAN)
- Unidades de medida (GWh, MWh, kWh, Hz, kV, kW, kVA, MVA, ms, s)
- Nombres genéricos de empresa / producto (Google, Microsoft, Amazon, Apple)

Las siguientes son **categorías vacías** que se llenan durante el paso interactivo (c) para cada documento: nombres de persona, nombres de lugar, códigos de producto / proyecto, empresa (este documento), organismos reguladores, referencias legales / documentales, términos específicos de la industria, roles / responsabilidades — y el usuario puede **crear nuevas categorías arbitrarias** en tiempo de ejecución.

> El conjunto de categorías es **abierto**: los términos específicos de la industria
> (p. ej. `SCADA/AMI/MDM/MDC` para empresas eléctricas, nombres de fármacos para
> sanidad, nombres de tribunales para derecho) **no** es semilla versionada — el
> usuario los llena bajo la categoría correspondiente mientras procesa un
> documento concreto. Este es el mecanismo central de la herramienta para la
> generalización multi-industria.

**Mecanismo** (`002_translator/translator.py`):

```
original
  │
  ▼
_protect_proper_nouns()        ← reemplazar términos DO_NOT_TRANSLATE con marcadores de posición
  │
  ▼
Google Translate API
  │
  ▼
_restore_proper_nouns()        ← reemplazar marcadores de posición de vuelta por los términos originales
  │
  ▼
translation
```

La lista de términos se ordena por longitud descendente para que `Advanced Metering` se coincida antes que `AMI`.

---

## 13. Motores de traducción — Google vs. Agent

DIaT ofrece dos motores de traducción intercambiables seleccionables con
`-e google` (predeterminado) o `-e agent`.  Ambos alimentan la misma disposición
de Excel, ambos respetan la misma protección de nombres propios y ambos son
validados por la misma verificación de supervivencia del cuerpo.  Diferen en
*quién* traduce y *cómo*.

### Cómo funcionan

| | Google Translate (`-e google`) | Agent / Claude (`-e agent`) |
|---|---|---|
| **Ejecutor** | API de Google Translate, llamada fragmento a fragmento desde `TranslationService._translate_with_google` | El agente de IA (Claude) lee una cola JSON y escribe las traducciones de vuelta |
| **Enlace** | Directo, en proceso | `main.py` escribe `*_agent_queue.json` (idioma de origen, idiomas de destino, requisitos, `extra_do_not_translate`) → el agente traduce → el agente llama a `write_translations_to_excel()` |
| **Ventana de contexto** | Un fragmento a la vez (≤ 4 500 caracteres); sin memoria entre requisitos | Toda la cola está disponible; el agente puede imponer consistencia terminológica entre requisitos y llevar contexto de ítems anteriores |
| **Red** | Necesita acceso al punto de conexión de Google Translate (directo o proxy en el extranjero) | Solo necesita la API de Claude — los puntos de conexión de Google nunca se tocan |
| **Velocidad (por 100 requisitos)** | Segundos — rápido, limitado por E/S | Minutos — cada ítem es un paso de razonamiento separado |
| **Costo** | Gratis (con límite de tasa) | Consume tokens de la API de Claude |

### Pros y contras

#### Google Translate (`-e google`)

**Pros**
- **Rápido** — alto rendimiento; ideal para una primera pasada rápida o un lote
  grande de documentos donde "suficientemente bueno" es aceptable.
- **Sin costo de tokens** — la API de Translate es gratis (dentro de los límites de tasa).
- **Calidad predecible** — para pares de idiomas comunes (pt/en, en/es, en/zh)
  la prosa general es fluida.

**Contras**
- **Fragmentado, sin contexto** — cada fragmento de ≤ 4 500 caracteres se
  traduce aisladamente, por lo que un requisito dividido en un límite de
  fragmento pierde la referencia entre oraciones.
- **Más débil en prosa técnica densa** — especificaciones largas con cláusulas
  anidadas, referencias cruzadas y enunciados tabulares breves pueden volver
  confusas o subtraducidas (la verificación de cobertura puede entonces negarse
  a emitir).
- **Fragilidad con nombres propios** — sin el paso de marcadores de posición,
  siglas como `MDC`, `AMI`, `HPLC` habitualmente se convierten a minúsculas o
  se transliteran; la protección con marcadores mitiga esto pero no es
  infalible para siglas no vistas.
- **Necesita red saliente** — inutilizable desde un host CI restringido que
  solo alcanza la API de Claude.

#### Agent / Claude (`-e agent`)

**Pros**
- **Consciente del contexto** — Claude ve el requisito completo y, cuando es
  necesario, la cola circundante, por lo que mantiene la consistencia
  terminológica (`MDC` sigue siendo `MDC`, `last-gasp` se interpreta en el
  sentido de medición) y maneja las cláusulas anidadas limpiamente.
- **Mejor para prosa técnica densa y corta** — exactamente la forma de los
  requisitos extraídos de especificaciones; produce salida de nivel humano.
- **Sin dependencia de Google** — funciona donde solo se puede alcanzar la API
  de Claude.
- **Autoconsistente** — el agente puede reutilizar la misma traducción de una
  frase repetida en todo el documento, que el Google Translate fragmentado
  puede renderizar de manera diferente cada vez.

**Contras**
- **Más lento** — cada requisito es un paso de razonamiento; un documento de
  400 ítems tarda varios minutos.  El script mitiga esto agrupando la cola y
  paralelizando los turnos del agente donde es posible.
- **Costo de tokens** — facturado por 1 000 tokens; los documentos grandes son
  notablemente más caros que la vía gratuita de Google.
- **Variable en prosa larga y fluida** — para párrafos narrativos continuos
  (raros en listas de requisitos), un motor fluido puede ocasionalmente
  "mejorar" la redacción en lugar de traducir fielmente; la verificación de
  supervivencia del cuerpo detecta la pérdida de contenido pero no el cambio
  de estilo.

### Cómo elegir

| Situación | Motor recomendado |
|---|---|
| Vista previa rápida, lote grande, prosa fluida | `-e google` |
| Especificaciones técnicas densas, importa la consistencia terminológica | `-e agent` |
| Red restringida (solo se puede alcanzar la API de Claude) | `-e agent` |
| Segunda pasada para limpiar un borrador de Google | ejecutar Google primero, luego Agent en la cola |

> **Nota:** en modo Agent la lista `extra_do_not_translate` también se aplica;
> el agente sustituye los mismos marcadores de posición `__PROPER_<uuid>__`
> antes de la traducción (el mismo contrato `_protect_proper_nouns` /
> `_restore_proper_nouns` que usa la vía de Google), por lo que el
> comportamiento de protección es idéntico entre motores.

---

## 14. Formato de salida

Definición de columnas de la hoja de cálculo de Excel (título de la hoja y
encabezados localizados al idioma de destino que no es inglés):

| Columna | Campo | Descripción |
|---------|-------|-------------|
| A | ID | REQ-0001, incremental |
| B | Capítulo | Número y título del capítulo de nivel superior |
| C | Sección | Número y título del subcapítulo |
| D | Original | Oración completa en el idioma de origem |
| E | English translation | Siempre presente |
| F | <su idioma> translation | El idioma elegido por el usuario |

- Cuando los destinos son `en` + otro idioma, los encabezados estáticos + título
  de hoja se muestran en ese idioma — p. ej. `en + ja` → hoja `要求事項`,
  encabezados `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`.  Sin encabezados
  en varios idiomas.
- Cuando el idioma de origen coincide con un destino, esa columna conserva el
  texto original (sin llamada API).
- Anchos de columna: `[10, 32, 32, 65, 65]`.
- Sobrescribir el idioma de los encabezados con `--display-lang <code>`.

---

## 15. Hoja de ruta

- [ ] Permitir especificar el idioma de origen en la CLI (omitir detección automática)
- [ ] Añadir formatos de salida docx / odt
- [ ] Mejorar la estrategia de fusión de múltiples párrafos (actualmente basada en oraciones)
- [ ] Adaptación más amplia a documentos oficiales en otros idiomas
- [ ] Procesamiento incremental: extraer deltas entre dos revisiones del mismo PDF

---

## 16. Licencia y atribución

© **Aggre-Cloud 聚云科技** — <https://www.acdatech.com>

Desarrollado y mantenido por Aggre-Cloud (聚云科技).
