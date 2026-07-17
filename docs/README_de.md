# DIaT

> Werkzeug zur Extraktion und Übersetzung strukturierter Anforderungen —
> hierarchische Anforderungen aus PDF-Dokumenten extrahieren, strukturiert
> zerlegen, übersetzen und als Excel-Bericht exportieren.

Sprache: **Deutsch** (diese Datei) · **English** → [`README.md`](../README.md) · **中文** → [`README_zh.md`](README_zh.md) · **Português (Brasil)** → [`README_pt.md`](README_pt.md) · **Español** → [`README_es.md`](README_es.md) · **Français** → [`README_fr.md`](README_fr.md) · **日本語** → [`README_ja.md`](README_ja.md)

---

## 1. Was ist DIaT? — Projekthintergrund

### Das gelöste Problem

Internationale Ingenieur-, Energie- und Infrastrukturprojekte produzieren
routinemäßig **strukturierte, mehrsprachige PDF-Dokumente** —
Ausschreibungen, technische Spezifikationen, Verträge, Vorschriften und
Normen. Diese Dokumente teilen eine gemeinsame Struktur:

- **Hierarchisch nummeriert**: eine 5-stufige Struktur, die der Parser intern
  als Kapitel → Abschnitt → Artikel → Klausel → Punkt modelliert
  (Kapitel → Abschnitt → Artikel → Klausel → Punkt), häufig mit gemischten Nummerierungsschemata wie
  `Art. 1º`, `CAPÍTULO`, `1.2.1`, `（1）`, `(a)`, römischen Ziffern,
  kreisförmigen Zahlen. Jede Anforderung trägt intern ihren vollständigen
  `hierarchy_path`, aber die exportierte Excel-Datei legt nur die obersten
  zwei Ebenen (Kapitel / Abschnitt) als eigene Strukturspalten offen — tiefere Ebenen
  bleiben im Anforderungstext verborgen, damit die Zeile lesbar bleibt.
- **Mehrsprachig**: eine portugiesische Spezifikation für ein
  chinesisch-gesponsertes Projekt, eine arabische Ausschreibung geprüft von
  einem deutschen Auftragnehmer, ein russischer Wartungsplan gelesen von
  einem brasilianischen Team.
- **Layout-intensiv**: mehrspaltiger Text, eingebettete Tabellen,
  wiederholte Kopf- und Fußzeilen und — im schlimmsten Fall — gescannte
  Bildseiten.

Für einen Projektingenieur, Beschaffungsbeauftragten oder technischen
Prüfer besteht die eigentliche Arbeit darin: *„jede Anforderung
extrahieren, wissen, zu welchem Kapitel sie gehört, und sie in meiner
Sprache lesbar machen."* Dies von Hand zu tun ist langsam, fehleranfällig
und skaliert nicht über einen Ordner voller Dokumente.

### Warum DIaT

Die übersetzung Dokument für Dokument ist langsam und fragil. DIaT ersetzt
die manuelle Kopieren → Einfügen → Übersetzen → Neu-Zusammenfügen-Schleife
durch eine deterministische, selbstvalidierende Pipeline:

| Fähigkeit | Manuell / nur Google Translate | DIaT |
|-----------|-------------------------------|------|
| Dokumentlayout | Kopieren und Einfügen pro Seite; Mehrspalten- und Tabellentext regelmäßig verfälscht | 4-Strategien-Merge-Extraktion (Layout → Wörter → Tabellen → Zeichen) mit automatischer Kopf-/Fußzeilen-Entfernung |
| Aufteilung der Anforderungen | Nummerierung abschätzen — leicht, Elemente zu verlieren oder die Verschachtelung zu verflachen | 12 Nummerierungsschemata automatisch erkannt (Art. / CAPÍTULO / § / 1.2.1 / （1）/ (a) / römisch / kreisförmig …) und ein stack-basierter Baum, der den **vollständigen** Kapitelpfad jedes Elements beibehält |
| Satzsegmentierung | Den ganzen Absatz übersetzen — lange Sätze verschlechtern sich, Zeilenumbrüche gehen verloren | Pro Quellsprache Best Practice (pysbd für lateinische Schriften, CJK-Terminatorregeln für zh/ja/ko, Regex-Fallback für alles andere) |
| Eigennamen | Von der Übersetzungs-Engine verfälscht (`MDC` → Kleinbuchstaben, `AMI` entstellt) | Platzhalterschutz mit ~30 eingebauten generischen Begriffen plus kategoriengesteuerter interaktiver Ergänzung, nach der Übersetzung wortwiederhergestellt |
| Übersetzungs-Engine | An eine einzige gebunden | Google Translate **und** Agent (Claude) duale Engines — umschaltbar in derselben Pipeline mit identischem Ausgabelayout |
| Textkörper-Sicherheit | Übersetzungsverlust wird erst im Nachhinein bemerkt, wenn überhaupt | Obligatorische Wort-Multimengen-Abdeckungsprüfung; **< 80% stoppt die Pipeline zwingend und gibt keine Excel-Datei aus** — Teilausgabe ist inakzeptabel |
| Ausgabesprache | Einzelsprache, gemischte Kopfzeilen | Blattüberschrift, statische Kopfzeilen und Spaltenüberschriften vollständig in die Zielsprache lokalisiert — keine Vermischung |
| Stapelverarbeitung | Wiederholung pro Datei | Verzeichnisweite Stapelverarbeitung, CI-Flags (`--no-input`) und autonomer Agenten-Lauf |

### Was DIaT macht

**DIaT** (der Name ist ein Platzhalter-Akronym) wandelt ein solches PDF in
einem einzigen Befehl in eine strukturierte, übersetzte Excel-Arbeitsmappe
um:

1. **Extrahieren** des Textkörpers aus dem PDF — 4-Strategien-Merge
   (Layout → Wörter → Tabellen → Zeichen) mit automatischer Kopf-/
   Fußzeilen-Entfernung und OCR-Fallback für gescannte PDFs.
2. **Zerlegen** des Dokuments in hierarchische Anforderungen unter
   Beibehaltung des Kapitel-/Abschnittspfades jedes Elements.
3. **Segmentieren** der Sätze pro Quellsprache (pt / en / zh / ja / ko /
   es / fr / de / …).
4. **Übersetzen** jeder Anforderung in zwei Zielsprachen — Englisch ist
   immer eine Spalte; Sie wählen die andere.
5. **Validieren**, dass kein Textkörper stillschweigend verloren ging
   (bricht ab, wenn Abdeckung < 80 % — Teilausgabe ist inakzeptabel).
6. **Exportieren** einer Excel-Arbeitsmappe: `ID / Kapitel / Abschnitt / Quelle /
   English / <Ihre Sprache>`.

### Für wen es ist

- Projektingenieure und Beschaffungspersonal, die mit mehrsprachigen
  Spezifikationen und Ausschreibungen arbeiten.
- Technische Übersetzer, die eine erste maschinelle Übersetzung benötigen,
  die an der Struktur des Dokuments verankert ist.
- Compliance-/QS-Prüfer, die jede Anforderung zu ihrem Quellkapitel
  zurückverfolgen müssen.
- KI-Agenten (Claude usw.), die Dokumentverarbeitungs-Pipelines
  orchestrieren und ein deterministisches, selbstvalidierendes Werkzeug
  benötigen.

---

## 2. Verwendung — Empfohlene Methoden

### ▶ Empfohlen: interaktiver Modus (einfach ausführen)

Die einfachste, empfohlene Art, DIaT zu verwenden, ist der **interaktive**
Ausführungsmodus, bei dem das Skript Sie durch den Prozess führt. Sie
müssen nur drei Fragen beantworten; alles andere geschieht automatisch:

```bash
# Stellen Sie sicher, dass Sie sich im Stammverzeichnis des Projekts befinden
cd "<project-root>"

# Ausführen — das ist alles. Das Skript stellt 3 Fragen und erstellt dann die Excel-Datei.
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf"
```

Sie werden in dieser Reihenfolge gefragt:

| # | Frage | Standardwert |
|---|-------|--------------|
| (a) | **Eine einzige nicht-englische Zielsprache wählen** — Englisch (`en`) ist immer eine Zielsprache; Sie wählen nur die zweite | `zh-cn` (Vereinfachtes Chinesisch) |
| (b) | **Übersetzungs-Engine wählen** — `google` (Translate-API) oder `agent` (Claude übersetzt selbst über JSON-Warteschlange) | `google` |
| (c) | **Eigennamen-Begriffe** nach Kategorie hinzufügen (Personenname, Projektcodes, Unternehmen, …) — oder Enter drücken zum Überspringen | keine (eingebaut ~30 generische Seed-Begriffe) |

Nach den Eingabeaufforderungen läuft die Pipeline bis zum Abschluss durch
und schreibt die Excel-Datei nach `output/<your-file>_requirements.xlsx`.

> **Tipp:** Wenn die automatisch erkannte Quellsprache mit einer Ihrer
> Zielsprachen übereinstimmt, behält diese Spalte automatisch den
> Originaltext bei — kein zusätzlicher API-Aufruf.

### ▶ Nicht-interaktiver Modus (Stapelverarbeitung / CI / explizite Flags)

Wenn Sie alle Entscheidungen bereits kennen und die Eingabeaufforderungen
überspringen möchten, übergeben Sie die Flags explizit:

```bash
# Englisch + Japanisch, Google, nicht-interaktiv
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    -l ja -e google --no-input

# Englisch + Chinesisch, Agenten-Modus, nicht-interaktiv
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    -l zh-cn -e agent --no-input

# Nur Extrahieren + Aufteilen + Excel exportieren, keine Übersetzung
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    --no-translate --json --no-input

# Einen ganzen Stapelverarbeitungs-Ordner (nicht-interaktiv)
PYTHONIOENCODING=utf-8 python 005_main/main.py ./pdfs --no-input
```

> **Hinweis:** Englisch (`en`) wird immer automatisch hinzugefügt — `-l>
> akzeptiert nur die *nicht-englische* Sprache. `-l en` wird mit einer
> klaren Meldung abgelehnt.

### ▶ Agenten- / automatisierte Ausführung (zuerst Abhängigkeiten installieren)

Wenn ein KI-Agent DIaT ausführt, sind Abhängigkeiten möglicherweise nicht
vorhanden. Das Skript kann sie aus der eigenen `requirements.txt` des
Projekts ohne Benutzereingabe installieren:

```bash
# 1. (Optional) Fehlende Abhängigkeiten selbst installieren — nicht-interaktiv in einem nicht-TTY.
#    Überspringen, wenn Sie bereits `pip install -r requirements.txt` ausgeführt haben.
python -m 005_main.main --install-deps

# 2. Auch optionale Extras abrufen (bessere Segmentierung + OCR für gescannte PDFs)
python -m 005_main.main --install-deps --with-optional

# 3. Die eigentliche Pipeline ausführen
python -m 005_main.main "your-file.pdf" -l ja -e google --no-input
```

### ▶ Manuelle Installation durch einen Menschen (ein Befehl)

```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt   # optional: pysbd + ocrmypdf
```

---

## 3. DIaT über einen KI-Agenten nutzen

DIaT ist ein **Agent-Skill**: Sie senden **einen Prompt** und der Agent
erledigt den Rest — Projekt abrufen, Abhängigkeiten installieren und die
komplette Extraktion → Übersetzung → Excel-Pipeline ausführen.  Sie müssen
nicht selbst klonen oder `pip install` ausführen; der Agent übernimmt die
Installation als Teil der Ausführung.

Das `AGENT_GUIDE.md` des Repos ist das Handbuch des Agenten — ein fähiger
Agent liest es, sobald das Projekt auf der Platte ist, daher muss Ihr Prompt
nur das **Dokument** und Ihre **Wahlen** benennen.

### 3a. Ein Prompt genügt — Templates

Beginnen Sie mit dem kürzesten Prompt und ergänzen Sie Details nur, wenn Sie
eine Frage überspringen wollen.  Wählen Sie die Zeile, die zu dem passt, was
Sie vorab entscheiden möchten.

| Ihr Prompt | Was der Agent tut |
|---|---|
| `用 DIaT 处理 my-spec.pdf` | Ruft das Projekt ab, installiert Abhängigkeiten, stellt dann die drei Fragen aus §3b, bevor er das Excel erzeugt. **Sicherster Start — wählen Sie diesen, wenn Sie unsicher sind.** |
| `Process my-spec.pdf with DIaT` | Dasselbe, auf Englisch. |
| `DIaT my-spec.pdf → English + Japanese, Google engine` | Ruft das Projekt ab, installiert Abhängigkeiten, führt direkt aus: `-l ja -e google --no-input`. |
| `用 DIaT 把 spec.pdf 条目化成 Excel，不翻译` | Nur Extrahieren + Aufteilen + Excel: `--no-translate --json --no-input`. |
| `DIaT ./pdfs 全部 → zh-cn, agent engine, batch` | Stapelverarbeitung des Ordners im Agent-Modus (`-e agent`); der Agent übersetzt die ausgegebene JSON-Warteschlange. |

Prompts funktionieren in jeder Sprache, die der Agent versteht.  Die
Beispiele auf Chinesisch gewählt, weil DIaTs Standardwerte auf
Chinesisch↔Englisch-Ingenieurdokumente abgestimmt sind.

### 3b. Die drei Fragen, die der Agent stellt

Wenn der Prompt Sprache / Engine / Eigennamen nicht festlegt, stellt der
Agent diese drei Fragen vor der Übersetzung — das ist die verpflichtende
Checkliste aus `AGENT_GUIDE.md`, keine Höflichkeit:

| # | Frage | Wenn Sie nichts antworten (Standard) |
|---|-------|------|
| (a) | **Wählen Sie EINE nicht-englische Zielsprache** — Englisch (`en`) ist immer ein Ziel; Sie wählen nur die zweite | `zh-cn` (Vereinfachtes Chinesisch) |
| (b) | **Wählen Sie die Übersetzungs-Engine** — `google` (Translate-API) oder `agent` (Claude übersetzt via JSON-Warteschlange) | `google` |
| (c) | **Fügen Sie Eigennamen-Termini** nach Kategorie hinzu (Personenname, Projektcode, Firma, …) | überspringen — verwendet die ~30 eingebetteten generischen Startwerte |

**Empfohlen:** Beantworten Sie die drei Eingabeaufforderungen zumindest beim
ersten Mal.  Dieser interaktive Ablauf zeigt, was das Werkzeug kann, und
vermeidet Ausführungen mit falscher Sprache / Engine.  Legen Sie Ihre Wahlen
im Prompt fest (wie die nicht-interaktiven Zeilen in §3a) nur, wenn Sie die
Fragen bewusst überspringen möchten.

### 3c. End-to-End-Beispiel (ein Prompt → fertiges Excel)

Dies ist der vollständige Gesprächsverlauf — ein Prompt von Ihnen, der Agent
installiert, was fehlt, stellt dann entweder die drei Fragen oder führt aus.
Gleicher Ablauf wie §10, als Dialog dargestellt, damit Sie wissen, was Sie
erwartet.

```
You:  Process my-spec.pdf with DIaT

Agent: [klont github.com/Aggre-Cloud/DIaT falls fehlend]
       [führt aus: python -m 005_main.main --install-deps  ]
       Erkannte Quellsprache: pt
       Welche nicht-englische Zielsprache? (Standard zh-cn)
You:   ja

Agent: Übersetzungs-Engine — Google oder Agent?
You:   google

Agent: Eigennamen-Termini hinzufügen? Enter zum Überspringen?
       (zeigt die kategorisierte Liste)
You:   [Enter]

Agent: [extrahieren → aufteilen → validieren → übersetzen → Excel schreiben]
       Geschrieben: output/my-spec_requirements.xlsx
       393 Anforderungen, Textkörper-Abdeckung 100.7 %
```

### 3d. Wie die Installation tatsächlich abläuft (Agent-Seite)

Sie führen diese Befehle nie von Hand aus — hier nur aufgeführt, damit Sie
verstehen, was der Agent unter der Haube tut:

| Situation | Agent führt aus |
|---|---|
| Projekt nicht auf der Platte | `git clone https://github.com/Aggre-Cloud/DIAT.git` → liest `AGENT_GUIDE.md` |
| Abhängigkeiten fehlen | `PYTHONIOENCODING=utf-8 python -m 005_main.main --install-deps` (installiert `requirements.txt` automatisch; ohne Abfrage bei nicht-TTY) |
| Optionale Extras gewünscht | `--with-optional` hinzufügen, um auch `pysbd` + `ocrmypdf` zu installieren |
| Pipeline | `PYTHONIOENCODING=utf-8 python -m 005_main.main "<file.pdf>" -l ja -e google --no-input` |
| Agent-Engine gewählt | Pipeline schreibt `*_agent_queue.json` mit leeren Übersetzungsspalten → Agent übersetzt jede Zeile und ruft `write_translations_to_excel()` zum Persistieren auf |

### 3e. Was der Agent tun und nicht tun muss

Der vollständige Vertrag steht in `AGENT_GUIDE.md §3`.  Die Kurzfassung:

- **Ein Prompt ist die ganze Arbeit des Benutzers** — Agent macht Installation
  + Ausführung.  Bitten Sie den Benutzer niemals, manuell zu klonen oder
  `pip install` auszuführen.
- **Standardmäßig interaktiv** — übergeben Sie NIEMALS `--no-input` im Namen
  des Benutzers; nur wenn der Benutzer ausdrücklich eine nicht-interaktive /
  Stapel-Ausführung verlangt.
- **Fragen Sie niemals die drei Fragen** (§3b) im interaktiven Modus.
- **Empfehlen Sie den interaktiven Weg** (`python 005_main/main.py "file.pdf"`,
  ohne Flags) als primäre Nutzungsart des Skills — er ist am wenigsten
  fehleranfällig und bringt dem Benutzer bei, was das Werkzeug kann.
- **Schlucken Sie niemals Textkörper-Verlust** — bei < 80 % Abdeckung stoppt
  die Pipeline und kein Excel wird geschrieben; der Agent muss den Fehler
  anzeigen, nicht mit einem niedrigeren Schwellenwert wiederholen, es sei
  denn, der Benutzer bittet darum.
- **Verändern Sie niemals DIaT-Quelldateien** während einer Ausführung.  Vom
  Benutzer gelieferte Eigennamen-Termini gehen in den Live-Cache / die
  JSON-Warteschlange, niemals in `config.py` (vermeidet Verschmutzung zwischen
  Ausführungen).

---

## 5. Installierte Abhängigkeiten

| Paket | Erforderlich? | Zweck |
|-------|---------------|-------|
| `openpyxl` | erforderlich | Excel-Arbeitsmappe lesen/schreiben |
| `pdfplumber` | erforderlich | PDF-Textextraktion (4-Strategien-Merge) |
| `PyPDF2` | erforderlich | PDF-Seitenabfrage / Metadaten |
| `pypdfium2` | erforderlich | PDF-Rendering / Seitenbilder |
| `googletrans` | erforderlich | Google Translate-Engine (nur bei `-e google`) |
| `pysbd` | optional | sprachbewusste Satzsegmentierung (Regex-Fallback falls nicht vorhanden) |
| `ocrmypdf` | optional | OCR-Fallback für gescannte PDFs (benötigt System-tesseract + ghostscript) |

---

## 6. Fähigkeitsgrenzen

### ✅ Unterstützt

| Dimension | Umfang |
|-----------|--------|
| Eingabe | Einzelne PDF-Datei oder ein Verzeichnis mit PDFs (Stapelverarbeitung) |
| Strukturtyp | Hierarchisch nummerierte Dokumente (Verträge, Spezifikationen, Vorschriften, Ausschreibungen, Normen …) |
| Kopf-/Fußzeilen | Wiederholte Blöcke automatisch erkennen (≥ 75 % der Seiten) und entfernen |
| Gescannte PDFs | Prüfen, dann `ocrmypdf --language <config>` für OCR-Fallback aufrufen (lazy Import, keine harte Abhängigkeit) |
| Hierarchie-Marker | `Art. 1º` / `CAPÍTULO` / `SEÇÃO` / `§ 1º` / `I.` / `1.` / `1.2` / `1.2.1` / `（1）` / `(a)` / `•` / `(1)` / römische Ziffern / kreisförmige Zahlen |
| Quellsprache | `pysbd` (optional) + eingebauter Regex-Fallback; pt / en / es / fr / de / zh / ja / ko haben jeweils eigene Segmentierungsregeln |
| Zielsprache | Englisch (fest) + eine vom Benutzer gewählte Sprache (jede googletrans / Claude code) |
| Übersetzungs-Engine | Google Translate (direkt) oder Agent (Claude übersetzt selbst) |
| Eigennamen-Schutz | Platzhalter-Substitution (eingebaut ~30 generische Begriffe + benutzerseitige Ergänzungen), nach der Übersetzung wiederhergestellt |
| Ausgabeformat | Excel-Arbeitsmappe (ID / Kapitel / Abschnitt / Quelle / English / <Ihre Sprache>) |
| Textkörper-Validierung | Obligatorische Abdeckungsprüfung; < 80 % stoppt die Pipeline ohne Ausgabe |
| Titel-Erhalt | Überschriftenzeilen werden immer als Teil des Textkörpers jeder Anforderung ausgegeben (für Abdeckungsaudit + Kontextverfolgung); Überschriften ohne Inhalt werden automatisch synthetisiert |
| Standardinteraktion | Standardmäßig interaktiv — fragt nach Zielsprache / Übersetzungs-Engine / Eigennamen-Ergänzungen; überspringt nur, wenn der Benutzer ausdrücklich fragt oder `--no-input` übergibt |
| Tabellenzeilen-Filterung | Bei Übereinstimmung einer `D1/D2/D3`-Überschrift werden Zeilen abgelehnt, die `;` (Zellentrenner), `(` (Einheitsangabe), ein nachgestelltes " - kurzes Wort" (Label/Wert-Paar) oder Ziffern enthalten — verhindert das Fehlinterpretieren von PDF-Tabellenzeilen als Abschnittsüberschriften |

### ⚠️ Voraussetzungen

- PDF muss **textselektierbar** digital sein oder mit ≥ 200 dpi gescannt sein
- Zugriff auf die Google Translate-API (direkt oder über einen ausländischen Proxy) ist erforderlich, es sei denn, Sie verwenden den Agenten-Modus
- Laufzeit: Python 3.9+; Abhängigkeiten aufgelistet in §4
- Große Dateien (> 100 Seiten) verlängern die Verarbeitungszeit erheblich; OCR-Fallback läuft ~1-5 s pro Seite

---

## 7. Architektur / Pipeline

```
PDF-Datei
   │
   ▼
[003_pdf_extractor]  extract_with_meta()
   │  4-Strategien-Merge: Layout → Wörter → Tabellen → Zeichen   (Fallback-Kaskadierung)
   │  Wiederholungsblock-Entferner  +  __PAGE_N__-Sentinels
   │  Gescannte-PDF-Prüfung → ocrmypdf → erneut öffnen
   ▼
roher_Text  +  ExtractionMeta
   │
   ▼
[001_text_splitter]  parse_text(raw_text, lang)
   │  ChapterSectionParser  — priorisierter Regex + Stack-Builder
   │  SentenceSegmenter     — Best-Practice-Regeln pro Sprache
   ▼
ParseResult  { roots, items, meta, raw_rows }
   │
   ├──▶ [007_validator]  assert_body_intact(raw_text, items)
   │       Wort-Multimengen-Abdeckungsverhältnis  →  BodyLossError wenn < 80 %
   │
   ▼
[002_translator]  (optional)  Google / Agent-Übersetzung
   │
   ▼
[004_excel_generator]  Excel-Arbeitsmappe
        ID | Kapitel | Abschnitt | Quelle | English | <Ihre Sprache>
```

### Schlüsselinvarianten

1. Die Textkörper-Abdeckung von `raw_text` in `items['content']` **darf nie unter 80 % fallen** (harter Schwellenwert).
2. Jede Seite wird mit einem `__PAGE_N__`-Sentinel markiert, damit die Seitenzuordnung nach dem Entfernen der Kopfzeilen erhalten bleibt.
3. Jede Anforderungszeile trägt einen vollständigen `hierarchy_path` (z. B. `1 Sistemas > 1.2 MDC > 1.2.1 Condições Gerais`).

---

## 8. Projektstruktur

```
DIaT/
├── 001_text_splitter/
│   └── text_splitter.py        # ChapterSectionParser (12 Nummerierungsschemata, stack-basierter 5-Stufen-Baum) + SentenceSegmenter
├── 002_translator/
│   └── translator.py           # TranslationService (Google + Agent) + lokalisierte Kopf-/Titel-Hilfsfunktionen
├── 003_pdf_extractor/
│   └── pdf_extractor.py        # 4-Strategien-Merge-Extraktion + Wiederholungsblock-Entferner + OCR-Fallback
├── 004_excel_generator/
│   └── excel_generator.py      # Ein-Blatt-Excel-Ausgabe (lokalisierte Kopfzeilen; Englisch + eine Benutzersprache)
├── 005_main/
│   └── main.py                 # CLI-Einstiegspunkt + Pipeline-Orchestrierung + Agenten-Warteschlangen-Schreiber
├── 006_config/
│   └── config.py               # globale Konfiguration + ABBR-Tabellen + DO_NOT_TRANSLATE-Kategorien + VALIDATION-Schwellenwerte
├── 007_validator/
│   └── validator.py            # assert_body_intact — Textkörper-Überlebensprüfung
├── sample doc/                 # Beispiel-PDFs (mehrsprachig) zum Testen
├── output/                     # generierte Excel + JSON-Zwischendateien (git-ignoriert)
├── requirements.txt            # festversionierte Laufzeitabhängigkeiten
├── requirements-optional.txt   # pysbd + ocrmypdf (bessere Segmentierung, OCR für gescannte PDFs)
├── README.md                   # benutzerseitige Dokumentation (Englisch)
├── docs/
│   ├── README_zh.md            # benutzerseitige Dokumentation (Chinesisch)
│   ├── README_pt.md            # benutzerseitige Dokumentation (Portugiesisch)
│   ├── README_es.md            # benutzerseitige Dokumentation (Spanisch)
│   ├── README_fr.md            # benutzerseitige Dokumentation (Französisch)
│   ├── README_de.md            # diese Datei — benutzerseitige Dokumentation (Deutsch)
│   └── README_ja.md            # benutzerseitige Dokumentation (Japanisch)
├── AGENT_GUIDE.md              # Orchestrierer / Sub-Agent-Nutzungsprinzipien
└── LICENSE                     # Projektlizenz
```

---

## 9. CLI-Argumente

| Argument | Beschreibung |
|----------|--------------|
| `input` | PDF-Datei oder Verzeichnispfad |
| `-o, --output` | Ausgabeverzeichnis (Standard `output/`) |
| `--no-translate` | Übersetzung überspringen |
| `--json` | Auch das JSON-Zwischenformat ausgeben |
| `-l, --lang` | Die nicht-englische Zielsprache (z. B. `pt`, `ja`). Englisch wird immer automatisch hinzugefügt |
| `-e, --engine` | Übersetzungs-Engine `google` (Standard) oder `agent` |
| `--no-input | **Expliziter** nicht-interaktiver Modus (en + zh-cn + Google). Standard ist interaktiv; nur übergeben, wenn ausdrücklich gefordert |
| `--display-lang` | Die Excel-Kopf-/Blatt-Sprache überschreiben (Standard: die nicht-englische Zielsprache) |
| `--install-deps` | Fehlende Drittanbieter-Pakete aus `requirements.txt` installieren, dann beenden. Nicht-interaktiv, wenn stdin kein TTY ist (Agent / Pipe); fragt in einem TTY um Bestätigung |
| `--with-optional` | Kombiniert mit `--install-deps`, installiert auch die optionalen Extras (`pysbd`, `ocrmypdf`) |

### Regeln zur Übersetzungssprachenauswahl

1. **Englisch ist immer eine Zielsprache** — Sie wählen nur die zweite Sprache.
2. **Gleiche Quell-Überspringen** — Wenn die Quellsprache mit einer Zielsprache übereinstimmt, behält diese Spalte den Originaltext bei (kein API-Aufruf).
3. **Lokalisierte Kopfzeilen** — Statische Excel-Kopfzeilen, Spaltenüberschriften und Blattüberschrift werden in der nicht-englischen Zielsprache gerendert (z. B. `en + ja` → `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`). Keine gemischten Kopfzeilen.

---

## 10. Interaktiver Ablauf — Beispielsitzung

```
$ PYTHONIOENCODING=utf-8 python 005_main/main.py example.pdf

  =======================================================
    Zielübersetzungs-Sprachauswahl
  =======================================================
  Erkannte Quellsprache: pt (Português)

    Englisch (en) ist immer eine Zielsprache.
    Wählen Sie EINE zusätzliche Sprache für die zweite Spalte.
    Standard: zh-cn
    zh-cn    — 中文（简体）
    pt       — Português ← Quellsprache
    es       — Español
    ...

  1 Sprachcode eingeben (oder Enter für Standard zh-cn): pt
  → Ziele: en + pt
  ⚠ Quellsprache ist pt (Português) → die Português-Spalte zeigt den Originaltext.

  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Übersetzungs-Engine-Auswahl
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    1. Google Translate-API   (Standard — schnell, extern)
    2. Agent  — Claude liest JSON, übersetzt, schreibt zurück

  1 oder 2 eingeben (oder Enter für Standard Google): 1

  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Eigennamen-Schutz
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  Die folgenden Begriffsklassen werden während der Übersetzung unverändert belassen:
    [technische Abkürzungen]  API, HTTP, HTTPS, JSON, XML, CSV, TCP, UDP, IP, VPN, … (17)
    [Normungsstellen]         IEC, IEEE, ISO, ITU, ANSI, IETF, W3C                (7)
    [Netzwerk / Infrastruktur] RF, PLC, LAN, WAN, HAN                              (5)
    [Maßeinheiten]            GWh, MWh, kWh, Hz, kV, kW, kVA, MVA, ms, s        (10)
    [Firmen- / Produktnamen]  Google, Microsoft, Amazon, Apple                     (4)

  Die folgenden Kategorien beginnen leer und werden dokumentweise ausgefüllt:
     1. Personenname             6. Regulierungsstellen
     2. Ortsname                7. Rechtliche / Dokumentenverweise
     3. Produkt-/Projektcodes   8. Branchenspezifische Begriffe
     4. Unternehmen (Dieses Dokument)  9. Rollen / Zuständigkeiten
    10. ＋ Neue Kategorie erstellen…
     0. Fertig — mit Übersetzung fortfahren

  Kategorienummer wählen (1-10 zum Hinzufügen, 0=fertig): 3
  → [Produkt-/Projektcodes] derzeit leer
    Kommagetrennte Begriffe hinzufügen (Enter zum Überspringen): SCADA,AMI,MDM,MDC
    + 4 Begriff(e) hinzugefügt.

  Kategorienummer wählen (1-10 zum Hinzufügen, 0=fertig): 0
  ✓ Eigennamen-Schutz konfiguriert. 1 Kategorie, 4 Begriffe insgesamt.

  [3/4] Übersetze (Engine=google, Sprachen=['en', 'pt'])...
  ...

  [OK] Abgeschlossen!
  [OK] Ausgabedatei: output/example_requirements.xlsx
  [OK] Anforderungen insgesamt: 393
  [OK] Gültige Anforderungen: 393 (100.0%)
  [OK] Textkörper-Abdeckung: 100.7%
```

---

## 11. Garantie für den Textkörper-Erhalt

Stillschweigender Textkörperverlust ist **inakzeptabel** — `007_validator` läuft bedingungslos, bevor die Excel-Datei generiert wird:

1. `raw_text` zeilenweise durchgehen, wobei Kopf-/Fuß-/Inhaltsverzeichnis-Zeilen übersprungen werden → ergibt `body_lines`.
2. Jedes `item['content']` in eine Wort-Multimenge normalisieren.
3. Greedy-Übereinstimmung: `Abdeckung = Σ abgedeckte_Wörter / Σ Textkörper_Wörter`.
4. Abdeckung `< 80 %` → `BodyLossError` auslösen, **Pipeline anhalten, keine Excel-Datei wird ausgegeben**.
5. Nicht abgedeckte Zeilen werden zur Nachbearbeitung in `{prefix}_orphans.json` geschrieben.

Lexische Normalisierung faltet gesamten Whitespace vor dem Tokenisieren zu einem einzigen Leerzeichen zusammen, sodass pdfplumber-bedingte Zeilenumbrücheinrückungen-Veränderungen nicht fälschlich als Textkörperverlust gezählt werden.

Die Schwellenwerte liegen in `006_config/config.py::VALIDATION`:

```python
VALIDATION = {
    'min_char_coverage': 0.80,   # minimale Textkörper-Überlebensrate
    'min_word_coverage': 0.85,
    'write_orphans': True,
    'sentence_target_min': 50,    # min Zeichen pro Satz
    'sentence_target_max': 500,   # max Zeichen pro Satz
}
```

---

## 12. Eigennamen-Schutz

Vor der Übersetzung werden die folgenden Begriffsklassen durch Platzhalter
`__PROPER_<uuid>__` ersetzt, sodass Google Translate sie unangetastet lässt,
und anschließend wiederhergestellt:

`006_config/config.py::DO_NOT_TRANSLATE` ist ein **kategorisiertes
Wörterbuch** (`Kategorie → {label, items}`); der eingebautte Seed enthält
nur **branchenübergreifende generische Begriffe** (~30), kategorisiert:

- Technische Abkürzungen (API, HTTP, HTTPS, JSON, XML, CSV, TCP, UDP, IP, SSH, …)
- Normungsstellen (IEC, IEEE, ISO, ITU, ANSI, IETF, W3C)
- Netzwerk / Infrastruktur (RF, PLC, LAN, WAN, HAN)
- Maßeinheiten (GWh, MWh, kWh, Hz, kV, kW, kVA, MVA, ms, s)
- Generische Firmen- / Produktnamen (Google, Microsoft, Amazon, Apple)

Die folgenden sind **leere Kategorien**, die während des interaktiven
Schritts (c) dokumentweise ausgefüllt werden: Personenname, Ortsname,
Produkt-/Projektcodes, Unternehmen (Dieses Dokument), Regulierungsstellen,
Rechtliche / Dokumentenverweise, branchenspezifische Begriffe, Rollen /
Zuständigkeiten — und der Benutzer kann **beliebige neue Kategorien**
zur Laufzeit erstellen.

> Die Kategoriemenge ist **offen**: branchenspezifische Begriffe (z. B.
> `SCADA/AMI/MDM/MDC` für Energieversorger, Medikamentennamen im
> Gesundheitswesen, Gerichtsnamen im Recht) sind **nicht** versionierter
> Seed — der Benutzer füllt sie unter der passenden Kategorie, während er
> ein konkretes Dokument verarbeitet. Dies ist der Kernmechanismus des
> Werkzeugs für die branchenübergreifende Verallgemeinerung.

**Mechanismus** (`002_translator/translator.py`):

```
Original
  │
  ▼
_protect_proper_nouns()        ← DO_NOT_TRANSLATE-Begriffe durch Platzhalter ersetzen
  │
  ▼
Google Translate API
  │
  ▼
_restore_proper_nouns()        ← Platzhalter durch Originalbegriffe zurückersetzen
  │
  ▼
Übersetzung
```

Die Begriffsliste wird nach absteigender Länge sortiert, sodass
`Advanced Metering` vor `AMI` abgeglichen wird.

---

## 13. Übersetzungs-Engines — Google vs. Agent

DIaT bietet zwei austauschbare Übersetzungs-Engines, wählbar mit
`-e google` (Standard) oder `-e agent`. Beide speisen dasselbe
Excel-Layout, beide respektieren denselben Eigennamen-Schutz und beide
werben durch denselben Textkörper-Überlebenscheck validiert. Sie
unterscheiden sich darin, *wer* übersetzt und *wie*.

### Wie sie funktionieren

| | Google Translate (`-e google`) | Agent / Claude (`-e agent`) |
|---|---|---|
| **Ausführende Instanz** | Google Translate-API, blockweise aufgerufen aus `TranslationService._translate_with_google` | Der KI-Agent (Claude) liest eine JSON-Warteschlange und schreibt Übersetzungen zurück |
| **Handshake** | Direkt, prozessintern | `main.py` schreibt `*_agent_queue.json` (Quellsprache, Zielsprachen, Anforderungen, `extra_do_not_translate`) → Agent übersetzt → Agent ruft `write_translations_to_excel()` auf |
| **Kontextfenster** | Ein Block gleichzeitig (≤ 4 500 Zeichen); kein Speicher über Anforderungen hinweg | Die gesamte Warteschlange ist verfügbar; der Agent kann terminologische Konsistenz über Anforderungen hinweg sicherstellen und Kontext aus früheren Elementen übernehmen |
| **Netzwerk** | Benötigt Zugriff auf den Google Translate-Endpunkt (direkt oder über ausländischen Proxy) | Benötigt nur die Claude-API — Google-Endpunkte werden nie erreicht |
| **Geschwindigkeit (pro 100 Anforderungen)** | Sekunden — schnell, I/O-bedingt | Minuten — jedes Element ist ein eigener Denkdurchgang |
| **Kosten** | Kostenlos (ratenbegrenzt) | Verbraucht Claude-API-Token |

### Vor- und Nachteile

#### Google Translate (`-e google`)

**Vorteile**
- **Schnell** — hoher Durchsatz; ideal für einen schnellen erste Durchlauf
  oder ein großes Dokumentenpaket, bei dem „gut genug" akzeptabel ist.
- **Keine Token-Kosten** — die Translate-API ist kostenlos (innerhalb
  der Ratenlimits).
- **Vorhersagbare Qualität** — für häufige Sprachpaare (pt/en, en/es,
  en/zh) ist prosa flüssig.

**Nachteile**
- **Blockweise, kontextfrei** — Jeder ≤ 4 500-Zeichen-Block wird isoliert
  übersetzt, sodart eine Anforderung, die über eine Blockgrenze
  hinausgeht, den satzübergreifenden Verlust verliert.
- **Schwächer bei dichter technischer Prosa** — lange Spezifikationen
  mit verschachtelten Klauseln, Querverweisen und knappen tabellarischen
  Aussagen können unleserlich oder unterübersetzt zurückkommen
  (der Abdeckungsprüfung kann dann verweigern, die Datei auszugeben).
- **Eigennamen-Fragilität** — Ohne Platzhalter-Pass werden Akronyme wie
  `MDC`, `AMI`, `HPLC` routinemäßig kleingeschrieben oder transkribiert;
  der Platzhalterschutz mildert dies, ist aber bei unbekannten Akronymen
  nicht narrensicher.
- **Benötigt ausgehendes Netzwerk** — unbrauchbar von einem gesperrten
  CI-Host, der nur die Claude-API erreicht.

#### Agent / Claude (`-e agent`)

**Vorteile**
- **Kontextbewusst** — Claude sieht die gesamte Anforderung und bei Bedarf
  die umgebende Warteschlange, sodass er Terminologie konsistent hält
  (`MDC` bleibt `MDC`, `last-gast` wird im Zählersinn interpretiert)
  und verschachtelte Klauseln sauber verarbeitet.
- **Am besten für dichte, kurze technische Prosa** — genau die Form der
  aus Spezifikationen extrahierten Anforderungen; erzeugt menschenähnliche
  Ausgabe.
- **Keine Google-Abhängigkeit** — funktioniert dort, wo nur die
  Claude-API erreichbar ist.
 **Selbstkonsistent** — Der Agent kann dieselbe Übersetzung einer
  wiederholten Phrase im gesamten Dokument wiederverwenden, was
  blockweises Google Translate jedes Mal anders rendern kann.

**Nachteile**
- **Langsamer** — jede Anforderung ist ein Denkdurchgang; ein Dokument
  mit 400 Elementen dauert mehrere Minuten. Das Skript mildert dies, indem
  es die Warteschlange stapelt und Agenten-Durchgänge wo möglich
  parallelisiert.
- **Token-Kosten** — abgerechnet pro 1 000 Token; große Dokumente sind
  merklicher teurer als der kostenlose Google-Pfad.
- **Variabel bei längerer, fließender Prosa** — Für fortlaufende
  erzählerische Absätze (selten in Anforderungslisten) kann eine flüssige
  Engine gelegentlich den Wortlaut „verbessern", statt treu zu übersetzen;
  der Textkörper-Überlebenscheck erfasst Inhaltsverlust, aber keinen
  stilistischen Drift.

### Wie wählt man

| Situation | Empfohlene Engine |
|---|---|
| Schnelle Vorschau, großes Paket, fließende Prosa | `-e google` |
| Dichte technische Spezifikationen, Terminologie-Konsistenz ist wichtig | `-e agent` |
| Gesperrtes Netzwerk (nur Claude-API erreichbar) | `-e agent` |
| Zweiter Durchlauf, um einen Google-Entwurf zu bereinigen | Zuerst Google ausführen, dann Agent auf die Warteschlange |

> **Hinweis:** Im Agenten-Modus wird die `extra_do_not_translate`-Liste
> ebenfalls angewendet; der Agent ersetzt die selben
> `__PROPER_<uuid>__`-Platzhalter vor der Übersetzung (derselbe
> `_protect_proper_nouns` / `_restore_proper_nouns`-Vertrag, den der
> Google-Pfad nutzt), sodass der Schutzverhalten über Engines hinweg
> identisch ist.

---

## 14. Ausgabeformat

Spaltendefinition des Excel-Arbeitsblatts (Blattüberschrift und Kopfzeilen
lokalisiert in die nicht-englische Zielsprache):

| Spalte | Feld | Beschreibung |
|--------|------|--------------|
| A | ID | REQ-0001, fortlaufend |
| B | Kapitel | Nummer + Titel des obersten Kapitels |
| C | Abschnitt | Nummer + Titel des Unterkapitels |
| D | Quelle | Vollständiger Satz in der Quellsprache |
| E | Englische Übersetzung | Immer vorhanden |
| F | <Ihre Sprache> Übersetzung | Die vom Benutzer gewählte Sprache |

- Wenn die Ziele `en` + eine weitere Sprache sind, werden die statischen
  Kopfzeilen und die Blattüberschrift in dieser Sprache gerendert —
  z. B. `en + ja` → Blatt `要求事項`, Kopfzeilen
  `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`. Keine gemischten
  Kopfzeilen.
- Wenn die Quellsprache mit einer Zielsprache übereinstimmt, behält
  diese Spalte den Originaltext bei (kein API-Aufruf).
- Spaltenbreiten: `[10, 32, 32, 65, 65]`.
- Kopfzeilensprache mit `--display-lang <code>` überschreiben.

---

## 15. Roadmap

- [ ] Quellsprache in der CLI angeben erlassen (Auto-Erkennung überspringen)
- [ ] docx- / odt-Ausgabeformate hinzufügen
- [ ] Die mehrabsatzbasierte Merge-Strategie verbessern (derzeit satzbasiert)
- [ ] Breitere Anpassung an offizielle Dokumente in anderen Sprachen
- [ ] Inkrementelle Verarbeitung: Deltas zwischen zwei Revisionen desselben PDF extrahieren

---

## 16. Lizenz & Urheberschaft

© **Aggre-Cloud 聚云科技** — <https://www.acdatech.com>

Entwickelt und gewartet von Aggre-Cloud (聚云科技).