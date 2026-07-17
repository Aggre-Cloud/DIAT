# DIaT

> Outil d'extraction et de traduction d'exigences structurées — extrait les
> exigences hiérarchiques des documents PDF, les décompose par structure, les
> traduit et exporte un rapport Excel.

Langue : **Français** (ce fichier) · **English** → [`README.md`](../README.md) · **中文** → [`README_zh.md`](README_zh.md) · **Português (Brasil)** → [`README_pt.md`](README_pt.md) · **Español** → [`README_es.md`](README_es.md) · **Deutsch** → [`README_de.md`](README_de.md) · **日本語** → [`README_ja.md`](README_ja.md)

---

## 1. Qu'est-ce que DIaT ? — Contexte du projet

### Le problème qu'il résout

Les projets internationaux d'ingénierie, d'énergie et d'infrastructure produisent
régulièrement des **documents PDF structurés et multilingues** — appels
d'offres, spécifications techniques, contrats, réglementations et normes. Ces
documents partagent une forme commune :

- **Numérotation hiérarchique** : une structure à 5 niveaux que le parseur modélise
  en interne comme chapitre → section → article → clause → item
  (chapitre → section → article → clause → item), mélangeant souvent des schémas de numérotation comme
  `Art. 1º`, `CAPÍTULO`, `1.2.1`, `（1）`, `(a)`, des chiffres romains, des
  nombres cerclés. Chaque exigence porte son `hierarchy_path` complet en interne,
  mais le Excel exporté n'expose que les deux niveaux supérieurs (Chapitre / Section) en
  tant que colonnes structurelles dédiées — les niveaux plus profonds restent
  repliés dans le corps de l'exigence afin que la ligne reste lisible.
- **Multilingue** : une spécification en portugais pour un projet soutenu par la
  Chine, un appel d'offres en arabe examiné par un entrepreneur allemand, un plan
  de maintenance en russe lu par une équipe brésilienne.
- **Mise en page lourde** : texte multicolonne, tableaux intégrés, en-têtes et
  pieds de page répétitifs et — dans le pire des cas — des pages numérisées.

Pour un ingénieur projet, un responsable achats ou un réviseur technique, le
vrai travail est : *« extraire chaque exigence, savoir à quel chapitre elle
appartient et la rendre lisible dans ma langue. »* Faire cela à la main est
lent, source d'erreurs et ne passe pas à l'échelle sur un dossier de documents.

### Pourquoi DIaT

La traduction document par document est lente et fragile. DIaT remplace la boucle
copier-coller manuel → traduire → réassembler par un pipeline déterministe et
auto-validant :

| Capacité | Manuel / Google Translate seul | DIaT |
|----------|-------------------------------|------|
| Mise en page du document | Copier-coller par page ; le texte multicolonne et les tableaux sont régulièrement brouillés | Extraction par fusion à 4 stratégies (mise en page → mots → tableaux → caractères) avec suppression automatique des en-têtes/pieds de page |
| Séparation des exigences | Évaluer la numérotation à l'œil — facile d'omettre des items ou d'aplatir l'imbrication | 12 schémas de numérotation détectés automatiquement (Art. / CAPÍTULO / § / 1.2.1 / （1）/ (a) / romains / cerclés …) et un arbre basé sur une pile qui conserve le chemin de chapitre **complet** de chaque item |
| Segmentation des phrases | Traduire le paragraphe entier — les longues phrases se dégradent, les coupures sont perdues | Bonnes pratiques par langue source (pysbd pour les scripts latins, règles de terminateur CJK pour zh/ja/ko, repli par regex pour le reste) |
| Noms propres | Corrompus par le moteur de traduction (`MDC` → minuscules, `AMI` déformé) | Protection par placeholder avec ~30 termes génériques intégrés plus une addition interactive guidée par catégorie, restaurés verbatim après traduction |
| Moteur de traduction | S'engager sur un seul | Double moteur Google Translate **et** Agent (Claude) — commutables dans le même pipeline avec une disposition de sortie identique |
| Sécurité du corps | La perte de traduction n'est repérée qu'après coup, voire jamais | Vérification obligatoire de la couverture par multiensemble de mots ; **< 80 % stoppe le pipeline et ne produit aucun Excel** — une sortie partielle est intolérable |
| Langue de sortie | Langue unique, en-têtes multilingues | Titre de feuille, en-têtes statiques et en-têtes de colonne entièrement localisés dans la langue cible — zéro mélange |
| Lot | Répétition par fichier | Lot sur dossier complet, indicateurs CI (`--no-input`) et exécution autonome par Agent |

### Ce que fait DIaT

**DIaT** (le nom est un acronyme provisoire) transforme un tel PDF en un
classeur Excel structuré et traduit en une seule commande :

1. **Extraire** le texte du corps du PDF — fusion à 4 stratégies (mise en page →
   mots → tableaux → caractères) avec suppression automatique des
   en-têtes/pieds de page et repli OCR pour PDF numérisés.
2. **Décomposer** le document en exigences hiérarchiques, en conservant le chemin
   chapitre/section de chaque item.
3. **Segmenter** les phrases par langue source (pt / en / zh / ja / ko / es /
   fr / de / …).
4. **Traduire** chaque exigence dans deux langues cibles — l'anglais est toujours
   une colonne ; vous choisissez l'autre.
5. **Valider** qu'aucun texte du corps n'a été silencieusement abandonné
   (abandonne si couverture < 80 % — une sortie partielle est intolérable).
6. **Exporter** un classeur Excel : `ID / Chapitre / Section / Source / English / <votre
   langue>`.

### À qui il s'adresse

- Ingénieurs projet et personnel achats travaillant avec des spécifications et
  appels d'offres multilingues.
- Traducteurs techniques ayant besoin d'une première passe de traduction
  automatique ancrée à la structure du document.
- Réviseurs conformité / QA ayant besoin de tracer chaque exigence jusqu'à son
  chapitre source.
- Agents IA (Claude, etc.) qui orchestrent des pipelines de traitement de
  documents et ont besoin d'un outil déterministe et auto-validant.

---

## 2. Mode d'emploi — Méthodes recommandées

### ▶ Recommandé : mode interactif (exécutez-le simplement)

La manière la plus simple et recommandée d'utiliser DIaT est de l'exécuter en
mode **interactif** et de laisser le script vous guider. Vous n'avez qu'à
répondre à trois questions ; tout le reste est automatique :

```bash
# Assurez-vous d'être à la racine du projet
cd "<project-root>"

# Exécutez — c'est tout. Le script vous pose 3 questions, puis produit le Excel.
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf"
```

Vous serez invité, dans l'ordre :

| # | Question | Par défaut |
|---|----------|---------|
| (a) | **Choisissez UNE seule langue cible non anglaise** — l'anglais (`en`) est toujours une cible ; vous ne choisissez que la seconde | `zh-cn` (chinois simplifié) |
| (b) | **Choisissez le moteur de traduction** — `google` (API Translate) ou `agent` (Claude s'auto-traduit via une file JSON) | `google` |
| (c) | **Ajoutez des termes noms propres** par catégorie (nom de personne, code projet, entreprise, …) — ou appuyez sur Entrée pour passer | aucun (environ 30 termes génériques intégrés) |

Après les invites, le pipeline s'exécute jusqu'au bout et écrit le Excel dans
`output/<your-file>_requirements.xlsx`.

> **Astuce :** si la langue source détectée automatiquement est égale à l'une de
> vos cibles, cette colonne conserve le texte original automatement — aucun
> appel API supplémentaire.

### ▶ Mode non interactif (lot / CI / indicateurs explicites)

Si vous connaissez déjà tous les choix et souhaitez passer les invites, passez
les indicateurs explicitement :

```bash
# Anglais + japonais, Google, non interactif
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    -l ja -e google --no-input

# Anglais + chinois, mode Agent, non interactif
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    -l zh-cn -e agent --no-input

# Extraire + séparer + exporter Excel uniquement, pas de traduction
PYTHONIOENCODING=utf-8 python 005_main/main.py "your-file.pdf" \
    --no-translate --json --no-input

# Lot sur un dossier complet (non interactif)
PYTHONIOENCODING=utf-8 python 005_main/main.py ./pdfs --no-input
```

> **Remarque :** l'anglais (`en`) est toujours ajouté automatiquement — `-l`
> prend uniquement la langue *non anglaise*. `-l en` est rejeté avec un message
> clair.

### ▶ Exécution par Agent / automatisée (auto-installer les dépendances d'abord)

Lorsqu'un agent IA exécute DIaT, les dépendances peuvent ne pas être présentes.
Le script peut les installer depuis le `requirements.txt` du projet sans saisie
humaine :

```bash
# 1. (Facultatif) auto-installer les dépendances manquantes — non interactif dans un non-TTY.
#    Ignorez si vous avez déjà exécuté `pip install -r requirements.txt`.
python -m 005_main.main --install-deps

# 2. Installez aussi les extras optionnels (meilleure segmentation + OCR PDF numérisés)
python -m 005_main.main --install-deps --with-optional

# 3. Exécutez le pipeline réel
python -m 005_main.main "your-file.pdf" -l ja -e google --no-input
```

### ▶ Installation manuelle humaine (une commande)

```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt   # optionnel : pysbd + ocrmypdf
```

---

## 3. Installer la compétence et invoquer l'Agent

### Installer la compétence dans votre agent

DIaT est un projet Python simple — « installer la compétence » signifie rendre
le dossier du projet disponible pour l'agent afin qu'il puisse exécuter
`005_main/main.py`.

1. **Clonez** le dépôt à un emplacement permanent sur l'hôte de l'agent
   (ou votre propre machine) :
   ```bash
   git clone https://github.com/Aggre-Cloud/DIAT.git
   cd DIaT
   ```
2. **Installez les dépendances une fois** (l'agent peut aussi s'auto-installer
   via `--install-deps`, mais une installation manuelle est plus rapide) :
   ```bash
   pip install -r requirements.txt
   ```
3. **Pointez l'agent vers la racine du projet.** Aucun enregistrement ni fichier
   de configuration n'est nécessaire — lorsque vous voulez qu'un PDF soit
   traité, indiquez à l'agent le chemin absolu vers la racine du projet et le
   fichier d'entrée :

   ```
   Traitez ce PDF avec DIaT :
     projet → D:/Tool Development/Skills Development/DIaT
     entrée → D:/.../my-spec.pdf
   ```

C'est l'intégralité de l'« installation » — un clone plus un `pip install`.

### Ordonner à l'agent de commencer le travail

Une fois le projet sur le disque de l'agent et les dépendances installées,
invoquez-le avec une courte instruction. L'agent connaît déjà la compétence via
`AGENT_GUIDE.md` ; votre message n'a qu'à nommer le document et les choix non
par défaut. Exemples :

| Votre message à l'agent | Ce que fait l'agent |
|---|---|
| `用 DIaT 处理 02.pdf` | S'exécute en mode interactif — demande la langue / le moteur / les noms propres, puis produit le Excel |
| `用 DIaT 处理 02.pdf，目标语言 ja，Google，不要问` : | Non interactif : `-l ja -e google --no-input` |
| `把 spec.pdf 条目化成 Excel，不翻译` | Extraire + séparer + Excel uniquement : `--no-translate --json --no-input` |
| `批量处理 ./pdfs 全部，zh-cn，agent 翻译` | Lot du dossier en mode Agent (`-e agent`) |

**Recommandé :** soyez concis et laissez l'agent exécuter les trois invites
(langue / moteur / noms propres) — ce flux interactif est le chemin le plus
sûr et vous apprend ce que l'outil peut faire. Ne spécifiez les indicateurs
(`-l`, `-e`, `--no-input`) que lorsque vous souhaitez délibérément passer les
invites.

---

## 4. Protocole d'exécution par l'Agent — Ce que l'Agent devrait recommander

Lorsqu'un agent IA orchestre DIaT pour le compte d'un utilisateur, **le
comportement recommandé est** :

1. **Par défaut, interagir.** Ne PAS passer `--no-input` pour le compte de
   l'utilisateur — ne le passez que lorsque l'utilisateur demande explicitement
   une exécution non interactive / par lot / entièrement automatisée.
2. **Poser à l'utilisateur les trois questions (a) / (b) / (c) ci-dessus** avant
   d'exécuter, même si les indicateurs CLI pourraient fournir des valeurs par
   défaut. C'est la liste de contrôle pré-exécution obligatoire du projet (voir
   `AGENT_GUIDE.md §2`).
3. **Recommander le chemin interactif** (`python 005_main/main.py "file.pdf"`)
   comme manière principale d'utiliser la compétence — c'est le moins source
   d'erreurs et cela apprend à l'utilisateur ce que l'outil peut faire.
4. **Vérifier les dépendances** avant la première exécution : invoquez
   `--install-deps` si un import requis est manquant, puis réexécutez.

L'outil est finalement **destiné à des personnes** — le travail de l'agent est
de placer l'utilisateur devant les trois invites, et non de décider
silencieusement en son nom.

---

## 5. Dépendances installées

| Paquet | Requis ? | Objet |
|--------|-----------|---------|
| `openpyxl` | requis | Lecture/écriture de classeurs Excel |
| `pdfplumber` | requis | Extraction de texte PDF (fusion à 4 stratégies) |
| `PyPDF2` | requis | Sondage de pages PDF / métadonnées |
| `pypdfium2` | requis | Rendu PDF / images de pages |
| `googletrans` | requis | Moteur Google Translate (uniquement avec `-e google`) |
| `pysbd` | optionnel | Segmentation de phrases sensible à la langue (repli par regex si absent) |
| `ocrmypdf` | optionnel | Repli OCR pour PDF numérisés (nécessite tesseract + ghostscript système) |

---

## 6. Limites de capacité

### ✅ Pris en charge

| Dimension | Portée |
|-----------|-------|
| Entrée | Fichier PDF unique, ou dossier de PDF (lot) |
| Type de structure | Documents à numérotation hiérarchique (contrats, spécifications, réglementations, appels d'offres, normes…) |
| En-têtes / pieds de page | Détection automatique des blocs répétitifs (≥ 75 % des pages) et suppression |
| PDF numérisés | Sondage, puis appel à `ocrmypdf --language <config>` pour le repli OCR (import paresseux, pas une dépendance dure) |
| Marqueurs de hiérarchie | `Art. 1º` / `CAPÍTULO` / `SEÇÃO` / `§ 1º` / `I.` / `1.` / `1.2` / `1.2.1` / `（1）` / `(a)` / `•` / `(1)` / chiffres romains / nombres cerclés |
| Langue source | pysbd (optionnel) + repli par regex intégré ; pt / en / es / fr / de / zh / ja / ko ont chacun des règles de segmentation dédiées |
| Langue cible | Anglais (fixe) + une langue choisie par l'utilisateur (tout googletrans / Claude code) |
| Moteur de traduction | Google Translate (direct) ou Agent (Claude traduit de lui-même) |
| Protection des noms propres | Substitution par placeholder (environ 30 termes génériques intégrés + ajouts fournis par l'utilisateur), restaurée après traduction |
| Format de sortie | Classeur Excel (ID / Chapitre / Section / Source / English / <votre langue>) |
| Validation du corps | Vérification obligatoire de la couverture ; < 80 % stoppe le pipeline sans sortie |
| Préservation des titres | Les lignes d'en-tête sont toujours émises comme partie du corps de chaque exigence (pour l'audit de couverture + le traçage de contexte) ; les en-têtes à corps vide sont auto-synthétisés |
| Interaction par défaut | Interactif par défaut — invite pour la langue cible / le moteur de traduction / les ajouts de noms propres ; ne passe que si l'utilisateur le demande explicitement ou passe `--no-input` |
| Filtrage des lignes de tableau | Lors de la correspondance d'un en-tête `D1/D2/D3`, rejette les lignes contenant `;` (séparateur de cellule), `(` (annotation d'unité), un « - mot court » final (paire libellé/valeur) ou des chiffres — évite de méprendre des lignes de tableau PDF pour des en-têtes de section |

### ⚠️ Prérequis

- Le PDF doit être numérique **sélectionnable en texte**, ou numérisé à ≥ 200 dpi
- L'accès à l'API Google Translate (direct ou via proxy à l'étranger) est requis sauf si vous utilisez le mode Agent
- Exécution : Python 3.9+ ; dépendances listées en §4
- Les fichiers volumineux (> 100 pages) augmentent significativement le temps de traitement ; le repli OCR s'exécute à environ 1-5 s par page

---

## 7. Architecture / Pipeline

```
Fichier PDF
   │
   ▼
[003_pdf_extractor]  extract_with_meta()
   │  Fusion à 4 stratégies : mise en page → mots → tableaux → chars   (cascading de repli)
   │  Suppression des blocs répétitifs  +  sentinelles __PAGE_N__
   │  Sondage PDF numérisé → ocrmypdf → réouverture
   ▼
raw_text  +  ExtractionMeta
   │
   ▼
[001_text_splitter]  parse_text(raw_text, lang)
   │  ChapterSectionParser  — regex par ordre de priorité + constructeur de pile
   │  SentenceSegmenter     — règles de bonnes pratiques par langue
   ▼
ParseResult  { roots, items, meta, raw_rows }
   │
   ├──▶ [007_validator]  assert_body_intact(raw_text, items)
   │       Ratio de couverture par multiensemble de mots  →  BodyLossError si < 80 %
   │
   ▼
[002_translator]  (optionnel)  Traduction Google / Agent
   │
   ▼
[004_excel_generator]  Classeur Excel
        ID | Chapitre | Section | Source | English | <votre langue>
```

### Invariants clés

1. La couverture du corps de `raw_text` vers `items['content']` **ne doit jamais descendre sous 80 %** (seuil dur).
2. Chaque page est marquée par une sentinelle `__PAGE_N__` afin que l'attribution de page survive à la suppression des en-têtes.
3. Chaque ligne d'exigence porte un `hierarchy_path` complet (par ex. `1 Sistemas > 1.2 MDC > 1.2.1 Condições Gerais`).

---

## 8. Structure du projet

```
DIaT/
├── 001_text_splitter/
│   └── text_splitter.py        # ChapterSectionParser (12 schémas de numérotation, arbre à 5 niveaux basé sur une pile) + SentenceSegmenter
├── 002_translator/
│   └── translator.py           # TranslationService (Google + Agent) + assistants d'en-tête/titre localisés
├── 003_pdf_extractor/
│   └── pdf_extractor.py        # Extraction par fusion à 4 stratégies + suppression des blocs répétitifs + repli OCR
├── 004_excel_generator/
│   └── excel_generator.py      # Sortie Excel sur une seule feuille (en-têtes localisés ; anglais + une langue utilisateur)
├── 005_main/
│   └── main.py                 # Point d'entrée CLI + orchestration du pipeline + écrivain de file d'agent
├── 006_config/
│   └── config.py               # Configuration globale + tableaux ABBR + catégories DO_NOT_TRANSLATE + seuils VALIDATION
├── 007_validator/
│   └── validator.py            # assert_body_intact — vérification de survie du corps
├── sample doc/                 # PDF d'exemple (multilingues) pour les tests
├── output/                     # Excel généré + intermédiaires JSON (ignoré par git)
├── requirements.txt            # Dépendances d'exécution épinglées
├── requirements-optional.txt   # pysbd + ocrmypdf (meilleure segmentation, OCR PDF numérisés)
├── README.md                   # documentation utilisateur (anglais)
├── docs/
│   ├── README_zh.md            # documentation utilisateur (chinois)
│   ├── README_pt.md            # documentation utilisateur (portugais)
│   ├── README_es.md            # documentation utilisateur (espagnol)
│   ├── README_fr.md            # ce fichier — documentation utilisateur (français)
│   ├── README_de.md            # documentation utilisateur (allemand)
│   └── README_ja.md            # documentation utilisateur (japonais)
├── AGENT_GUIDE.md              # Principes d'utilisation pour l'orchestrateur / sous-agent
└── LICENSE                     # Licence du projet
```

---

## 9. Arguments CLI

| Argument | Description |
|----------|-------------|
| `input` | Chemin vers un fichier PDF ou un dossier |
| `-o, --output` | Dossier de sortie (par défaut `output/`) |
| `--no-translate` | Ignorer la traduction |
| `--json` | Émettre aussi l'intermédiaire JSON |
| `-l, --lang` | La langue cible NON anglaise (par ex. `pt`, `ja`). L'anglais est toujours ajouté automatiquement |
| `-e, --engine` | Moteur de traduction `google` (par défaut) ou `agent` |
| `--no-input` | Mode non interactif **explicite** (en + zh-cn + Google). Par défaut interactif ; à ne passer que sur demande explicite |
| `--display-lang` | Remplacer la langue des en-têtes / de la feuille Excel (par défaut : la cible non anglaise) |
| `--install-deps` | Installer les paquets tiers manquants depuis `requirements.txt`, puis quitter. Non interactif quand stdin n'est pas un TTY (agent / tube) ; demande confirmation dans un TTY |
| `--with-optional` | Combiné avec `--install-deps`, installe aussi les extras optionnels (`pysbd`, `ocrmypdf`) |

### Règles de sélection des langues de traduction

1. **L'anglais est toujours une cible** — vous ne choisissez que la seconde langue.
2. **Ignorance si source égale cible** — si la langue source est égale à une cible, cette colonne conserve le texte original (aucun appel API).
3. **En-têtes localisés** — Les en-têtes statiques Excel, les en-têtes de colonne et le titre de feuille s'affichent dans la langue cible non anglaise (par ex. `en + ja` → feuille `要求事項`, en-têtes `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`). Aucun en-tête multilingue.

---

## 10. Flux interactif — Session d'exemple

```
$ PYTHONIOENCODING=utf-8 python 005_main/main.py example.pdf

  =======================================================
    Sélection de la langue de traduction cible
  =======================================================
  Source détectée : pt (Português)

    L'anglais (en) est toujours une cible.
    Choisissez UNE langue supplémentaire pour la seconde colonne.
    Par défaut : zh-cn
    zh-cn    — 中文（简体）
    pt       — Português ← source
    es       — Español
    ...

  Entrez un code de langue (ou appuyez sur Entrée pour le défaut zh-cn) : pt
  → Cibles : en + pt
  ⚠ La source est pt (Português) → la colonne Português affichera le texte original.

  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Sélection du moteur de traduction
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    1. API Google Translate   (par défaut — rapide, externe)
    2. Agent  — Claude lit le JSON, traduit, réécrit

  Entrez 1 ou 2 (ou appuyez sur Entrée pour le défaut Google) : 1

  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Protection des noms propres
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  Les catégories de termes suivantes sont conservées verbatim pendant la traduction :
    [abréviations techniques]  API, HTTP, HTTPS, JSON, XML, CSV, TCP, UDP, IP, VPN, … (17)
    [organismes de normes]     IEC, IEEE, ISO, ITU, ANSI, IETF, W3C                (7)
    [réseau / infrastructure]  RF, PLC, LAN, WAN, HAN                              (5)
    [unités de mesure]         GWh, MWh, kWh, Hz, kV, kW, kVA, MVA, ms, s        (10)
    [noms de sociétés/produits] Google, Microsoft, Amazon, Apple                   (4)

  Les catégories suivantes vides et remplies par document :
     1. Noms de personnes             6. Organismes de réglementation
     2. Noms de lieux                 7. Références légales / de documents
     3. Codes produit / projet        8. Termes spécifiques à l'industrie
     4. Société (ce document)        9. Rôles / responsabilités
    10. ＋ Créer une nouvelle catégorie…
     0. Terminé — continuer vers la traduction

  Sélectionnez un numéro de catégorie (1-10 pour ajouter, 0=terminé) : 3
  → [Codes produit / projet] actuellement vide
    Ajoutez des termes séparés par des virgules (Entrée pour passer) : SCADA,AMI,MDM,MDC
    + ajouté(s) 4 terme(s).

  Sélectionnez un numéro de catégorie (1-10 pour ajouter, 0=terminé) : 0
  ✓ Protection des noms propres configurée. 1 catégorie, 4 termes au total.

  [3/4] Traduction (moteur=google, langues=['en', 'pt'])...
  ...

  [OK] Terminé !
  [OK] Fichier de sortie : output/example_requirements.xlsx
  [OK] Nombre total d'exigences : 393
  [OK] Exigences valides : 393 (100,0 %)
  [OK] Couverture du corps : 100,7 %
```

---

## 11. Garantie de préservation du corps

La perte de corps silencieuse est **intolérable** — `007_validator` s'exécute inconditionnellement avant la génération du Excel :

1. Parcourir `raw_text` ligne par ligne, en ignorant les lignes d'en-tête/pied de page/sommaire → produire `body_lines`.
2. Normaliser chaque `item['content']` en un multiensemble de mots.
3. Correspondance gloutonne : `coverage = Σ mots_couverts / Σ mots_corps`.
4. Couverture `< 80 %` → lever `BodyLossError`, **stopper le pipeline, aucun Excel n'est émis**.
5. Les lignes non couvertes sont écrites dans `{prefix}_orphans.json` pour triage.

La normalisation lexicale réduit toutes les espaces blances à un seul espace avant de découper en jetons, de sorte que les différences d'indentation liées aux sauts de ligne pdfplumber ne sont pas comptées à tort comme une perte de corps.

Les seuils résident dans `006_config/config.py::VALIDATION` :

```python
VALIDATION = {
    'min_char_coverage': 0.80,   # taux de survie minimum du corps
    'min_word_coverage': 0.85,
    'write_orphans': True,
    'sentence_target_min': 50,    # caractères min par phrase
    'sentence_target_max': 500,   # caractères max par phrase
}
```

---

## 12. Protection des noms propres

Avant la traduction, les classes de termes suivantes sont remplacées par des placeholders
`__PROPER<uuid>`__ afin que Google Translate les laisse intacts, et sont
restaurées ensuite :

`006_config/config.py::DO_NOT_TRANSLATE` est un **dictionnaire catégorisé**
(`category → {label, items}`) ; la grille intégrée ne contient que des **termes
génériques inter-industrie** (~30), organisés par catégorie :

- Abréviations techniques (API, HTTP, HTTPS, JSON, XML, CSV, TCP, UDP, IP, SSH, …)
- Organismes de normes (IEC, IEEE, ISO, ITU, ANSI, IETF, W3C)
- Réseau / infrastructure (RF, PLC, LAN, WAN, HAN)
- Unités de mesure (GWh, MWh, kWh, Hz, kV, kW, kVA, MVA, ms, s)
- Noms génériques de sociétés / produits (Google, Microsoft, Amazon, Apple)

Les **catégories vides** suivantes sont remplies lors de l'étape interactive (c),
par document : noms de personnes, noms de lieux, codes produit / projet, société
(ce document), organismes de réglementation, références légales / de documents,
termes spécifiques à l'industrie, rôles / responsabilités — et l'utilisateur peut
**créer arbitrairement de nouvelles catégories** à l'exécution.

> L'ensemble des catégories est **ouvert** : les termes spécifiques à l'industrie
> (par ex. `SCADA/AMI/MDM/MDC` pour les services électriques, les noms de
> médicaments pour la santé, les noms de tribunaux pour le droit) ne sont **pas**
> des semences versionnées — l'utilisateur les remplit dans la catégorie
> correspondante lors du traitement d'un document concret. C'est le mécanisme
> central de l'outil pour la généralisation inter-industrie.

**Mécanisme** (`002_translator/translator.py`) :

```
original
  │
  ▼
_protect_proper_nouns()        ← remplacer les termes DO_NOT_TRANSLATE par des placeholders
  │
  ▼
API Google Translate
  │
  ▼
_restore_proper_nouns()        ← remplacer les placeholders par les termes originaux
  │
  ▼
traduction
```

La liste des termes est triée par longueur décroissante de sorte que
`Advanced Metering` soit apparié avant `AMI`.

---

## 13. Moteurs de traduction — Google vs. Agent

DIaT propose deux moteurs de traduction interchangeables sélectionnables avec
`-e google` (par défaut) ou `-e agent`. Les deux alimentent la même disposition Excel,
les deux respectent la même protection des noms propres et les deux sont validés par
la même vérification de survie du corps. Ils diffèrent par *qui* traduit et *comment*.

### Fonctionnement

| | Google Translate (`-e google`) | Agent / Claude (`-e agent`) |
|---|---|---|
| **Exécuteur** | API Google Translate, appelée morceau par morceau depuis `TranslationService._translate_with_google` | L'agent IA (Claude) lit une file JSON et réécrit les traductions |
| **Établissement de liaison** | Direct, en processus | `main.py` écrit `*_agent_queue.json` (langue source, langues cibles, exigences, `extra_do_not_translate`) → l'agent traduit → l'agent appelle `write_translations_to_excel()` |
| **Fenêtre de contexte** | Un morceau à la fois (≤ 4 500 caractères) ; aucune mémoire entre les exigences | La file entière est disponible ; l'agent peut imposer une cohérence terminologique entre les exigences et conserver le contexte des items antérieurs |
| **Réseau** | Nécessite l'accès au point de terminaison Google Translate (direct ou proxy à l'étranger) | Nécessite uniquement l'API Claude — les points de terminaison Google ne sont jamais sollicités |
| **Vitesse (par 100 exigences)** | Secondes — rapide, lié aux E/S | Minutes — chaque item est un passage de raisonnement distinct |
| **Coût** | Gratuit (limité en débit) | Consomme des jetons d'API Claude |

### Avantages et inconvénients

#### Google Translate (`-e google`)

**Avantages**
- **Rapide** — haut débit ; idéal pour une première passe rapide ou un grand lot
  de documents où « assez bon » est acceptable.
- **Aucun coût en jetons** — l'API Translate est gratuite (dans les limites de
  débit).
- **Qualité prévisible** — pour les paires de langues courantes (pt/en, en/es,
  en/zh) la prose générale est fluide.

**Inconvénients**
- **Par morceaux, sans contexte** — chaque morceau de ≤ 4 500 caractères est
  traduit isolément, donc une exigence coupée par une frontière de morceau
  perd la référence inter-phrases.
- **Plus faible sur la prose technique dense** — les spécifications longues
  avec clauses imbriquées, renvois et énoncés tabulaires laconiques peuvent
  revenir brouillées ou sous-traduites (la vérification de couverture peut alors
  refuser d'émettre).
- **Fragilité des noms propres** — sans la passe de placeholder, des acronymes
  comme `MDC`, `AMI`, `HPLC` sont régulièrement mis en minuscules ou
  translittérés ; la protection par placeholder atténue cela mais n'est pas
  infaillible pour les acronymes inédits.
- **Nécessite un réseau sortant** — inutilisable depuis un hôte CI verrouillé
  qui n'atteint que l'API Claude.

#### Agent / Claude (`-e agent`)

**Avantages**
- **Sensible au contexte** — Claude voit l'exigence entière et, si besoin,
  la file environnante, afin de maintenir une cohérence terminologique (`MDC`
  reste `MDC`, `last-gasp` est interprété au sens du comptage) et de gérer
  proprement les clauses imbriquées.
- **Idéal pour la prose technique dense et courte** — exactement la forme des
  exigences extraites de spécifications ; produit une sortie de niveau humain.
- **Aucune dépendance Google** — fonctionne là seulement où l'API Claude est
  accessible.
- **Auto-cohérent** — l'agent peut réutiliser la même traduction d'une phrase
  répétée dans tout le document, ce que Google Translate par morceaux peut
  rendre différemment à chaque fois.

**Inconvénients**
- **Plus lent** — chaque exigence est un passage de raisonnement ; un document
  de 400 items prend plusieurs minutes. Le script atténue cela en regroupant
  la file et en parallélisant les tours d'agent lorsque possible.
- **Coût en jetons** — facturé par 1 000 jetons ; les documents volumineux sont
  nettement plus chers que le chemin Google gratuit.
- **Variable sur la longue prose fluide** — pour les paragraphes narratifs
  courants (rares dans les listes d'exigences), un moteur fluide peut
  occasionnellement « améliorer » la formulation au lieu de traduire
  fidèlement ; la vérification de survie du corps détecte la perte de contenu
  mais pas la dérive stylistique.

### Comment choisir

| Situation | Moteur recommandé |
|---|---|
| Aperçu rapide, grand lot, prose fluide | `-e google` |
| Spécifications techniques denses, la cohérence terminologique compte | `-e agent` |
| Réseau verrouillé (seule l'API Claude accessible) | `-e agent` |
| Seconde passe pour nettoirer un brouillon Google | exécuter Google d'abord, puis l'Agent sur la file |

> **Remarque :** en mode Agent la liste `extra_do_not_translate` est elle aussi
> appliquée ; l'agent substitue les mêmes placeholders `__PROPER_<uuid>__`
> avant la traduction (le même contrat `_protect_proper_nouns` /
> `_restore_proper_nouns` que le chemin Google utilise), donc le comportement
> de protection est identique entre les moteurs.

---

## 14. Format de sortie

Définition des colonnes de la feuille Excel (titre de feuille et en-têtes localisés
dans la langue cible non anglaise) :

| Colonne | Champ | Description |
|--------|-------|-------------|
| A | ID | REQ-0001, incrémentiel |
| B | Chapitre | Numéro et titre du chapitre de plus haut niveau |
| C | Section | Numéro et titre du sous-chapitre |
| D | Source | Phrase complète dans la langue source |
| E | Traduction anglaise | Toujours présente |
| F | Traduction <votre langue> | La langue choisie par l'utilisateur |

- Quand les cibles sont `en` + une autre langue, les en-têtes statiques + le
  titre de feuille s'affichent dans cette langue — par ex. `en + ja` → feuille
  `要求事項`, en-têtes `ID / 章 / 節 / 原文 / 英語翻訳 / 日本語翻訳`. Aucun
  en-tête multilingue.
- Quand la langue source correspond à une cible, cette colonne conserve le
  texte original (aucun appel API).
- Largeurs de colonne : `[10, 32, 32, 65, 65]`.
- Remplacer la langue des en-têtes avec `--display-lang <code>`.

---

## 15. Feuille de route

- [ ] Permettre de spécifier la langue source sur la CLI (ignorer la détection automatique)
- [ ] Ajouter les formats de sortie docx / odt
- [ ] Améliorer la stratégie de fusion de plusieurs paragraphes (actuellement basée sur les phrases)
- [ ] Adaptation plus large aux documents officiels en d'autres langues
- [ ] Traitement incrémental : extraire les deltas entre deux révisions du même PDF

---

## 16. Licence et attribution

© **Aggre-Cloud 聚云科技** — <https://www.acdatech.com>

Développé et maintenu par Aggre-Cloud (聚云科技).