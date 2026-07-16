"""
Global configuration file - OPTIMIZED VERSION
Added configuration for hierarchical decomposition and validation
"""
import os

# Project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Input/output directories
INPUT_DIR = BASE_DIR
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_FIXED_DIR = os.path.join(BASE_DIR, "output_fixed")
JSON_OUTPUT_DIR = os.path.join(OUTPUT_FIXED_DIR, "json")

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_FIXED_DIR, exist_ok=True)
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)

# OCR fallback language (used by 003_pdf_extractor._ocr_fallback).
# Override in 007_config/config.py if the source document uses a
# non-Latin script (e.g. 'deu', 'fra', 'por', or a combo 'eng+por').
OCR_LANGUAGE = 'eng'

# Translation config.
# source_language=None  ⇒ auto-detect per document (langdetect).
# target_languages     ⇒ user picks at run time; the two defaults below
#                        are only the *interactive-prompt* defaults.
TRANSLATION_CONFIG = {
    'source_language': None,
    'target_languages': ['en', 'zh-cn'],
    'use_google_translate': True,
    'max_retries': 4,
    'retry_delay': 2.0,
    'request_delay': 0.6
}

# -----------------------------------------------------------------------
#  Proper nouns / abbreviations that must NOT be translated.
#
#  STORAGE MODEL — category dictionary (NOT a flat list):
#    category_key -> {
#        'label': {'en': <English display>, 'zh': <中文展示>},
#        'items': [<seed terms — cross-industry, versioned>],
#    }
#
#  `items` ONLY holds cross-industry, generic seed terms.  Industry-
#  specific tokens (SCADA / AMI / MDM / MDC / HV / MV / LV / PCC / DER /
#  DMS / …) are deliberately excluded — users add them at run time via
#  the category-guided interactive prompt (step 6), in whichever
#  category matches their document (e.g. `project_code`, `industry_term`).
#
#  Helpers below (`get_do_not_translate_flat`) flatten this dict into a
#  deduplicated list for the translation-protection mechanism.  The
#  category set is OPEN — new categories can be appended at run time.
# -----------------------------------------------------------------------
DO_NOT_TRANSLATE: dict[str, dict] = {
    # ── Generic cross-industry seed categories ──
    'technical_abbreviation': {
        'label': {'en': 'Technical Abbreviations', 'zh': '技术缩略语'},
        'items': ['API', 'HTTP', 'HTTPS', 'JSON', 'XML', 'CSV', 'TCP', 'UDP',
                  'IP', 'VPN', 'DNS', 'SSH', 'TLS', 'SSL', 'SQL', 'REST', 'SOAP'],
    },
    'standards_body': {
        'label': {'en': 'Standards Bodies', 'zh': '国际标准组织'},
        'items': ['IEC', 'IEEE', 'ISO', 'ITU', 'ANSI', 'IETF', 'W3C'],
    },
    'network_infra': {
        'label': {'en': 'Network / Infrastructure', 'zh': '网络/基础设施'},
        'items': ['RF', 'PLC', 'LAN', 'WAN', 'HAN'],
    },
    'measurement_unit': {
        'label': {'en': 'Measurement Units', 'zh': '计量单位'},
        'items': ['GWh', 'MWh', 'kWh', 'Hz', 'kV', 'kW', 'kVA', 'MVA', 'ms', 's'],
    },
    'company_product': {
        'label': {'en': 'Company / Product Names', 'zh': '公司/产品名'},
        'items': ['Google', 'Microsoft', 'Amazon', 'Apple'],
    },
    # ── User-filled categories (empty seeds — prompted at run time) ──
    'person_name': {
        'label': {'en': 'Person Names', 'zh': '人名'},
        'items': [],
    },
    'place_name': {
        'label': {'en': 'Place Names', 'zh': '地名'},
        'items': [],
    },
    'project_code': {
        'label': {'en': 'Product / Project Codes', 'zh': '产品/项目代号'},
        'items': [],
    },
    'company_local': {
        'label': {'en': 'Company (this document)', 'zh': '公司名（本文档）'},
        'items': [],
    },
    'regulatory_body': {
        'label': {'en': 'Regulatory Bodies', 'zh': '监管机构'},
        'items': [],
    },
    'legal_reference': {
        'label': {'en': 'Legal / Doc References', 'zh': '法规/文档编号'},
        'items': [],
    },
    'industry_term': {
        'label': {'en': 'Industry-Specific Terms', 'zh': '行业专有术语'},
        'items': [],
    },
    'role_title': {
        'label': {'en': 'Roles / Responsibilities', 'zh': '岗位/职责'},
        'items': [],
    },
}


def get_do_not_translate_categories() -> dict[str, dict]:
    """Return the categorized proper-noun table.

    Read-only reference — do not mutate in place.  To extend at run time,
    append to the per-session dict built in main.py's interactive prompt
    and feed it back via ``TranslationService.merge_do_not_translate_terms``.
    """
    return DO_NOT_TRANSLATE


def get_do_not_translate_flat() -> list[str]:
    """Flatten the categorized table into a deduplicated term list.

    Used by the translator's placeholder-protection machinery, which only
    needs the raw terms regardless of category.
    """
    seen, flat = set(), []
    for cat in DO_NOT_TRANSLATE.values():
        for t in cat.get('items', []):
            if t and t not in seen:
                seen.add(t)
                flat.append(t)
    return flat


# Requirement classification keywords
CATEGORY_KEYWORDS = {
    'Functional': ['funcional', 'função', 'feature', 'capacidade', 'operação', 'funcionalidade'],
    'Performance': ['desempenho', 'performance', 'velocidade', 'tempo', 'latência', 'throughput'],
    'Interface': ['interface', 'integração', 'interoperabilidade', 'API', 'protocolo', 'conexão'],
    'Security': ['segurança', 'security', 'proteção', 'criptografia', 'autenticacão', 'proteção'],
    'Hardware': ['hardware', 'medidor', 'dispositivo', 'equipamento', 'módulo', 'componente'],
    'Software': ['software', 'sistema', 'aplicativo', 'programa', 'firmware', 'aplicação'],
    'Communication': ['comunicação', 'telecom', 'rede', 'wireless', 'radio', 'WISUN', 'Wi-SUN'],
    'Data': ['dados', 'data', 'banco de dados', 'database', 'armazenamento', 'registro'],
    'Testing': ['teste', 'test', 'verificação', 'validação', 'certificação', 'inspeção'],
    'Documentation': ['documentação', 'document', 'manual', 'relatório', 'certificado', 'guia'],
    'Service': ['serviço', 'service', 'suporte', 'manutenção', 'treinamento', 'assistência'],
    'Other': []
}

# Special requirement keywords
SPECIAL_KEYWORDS = [
    # Mandatory
    'obrigatório', 'compulsório', 'mandatório', 'essencial', 'crítico',
    'urgente', 'prioritário', 'fundamental', 'indispensável',
    'must', 'shall', 'mandatory', 'required', 'critical', 'essential',
    # Integration
    'integração', 'interoperabilidade', 'compatibilidade', 'conformidade',
    # Certification
    'certificação', 'homologação',
    # Security
    'segurança', 'proteção', 'backup', 'redundância', 'failover',
    'disponibilidade', 'confiabilidade',
    # Performance
    'desempenho', 'especificação técnica', 'requisito', 'restrição'
]

# Product related keywords
PRODUCT_KEYWORDS = [
    # Device
    'medidor', 'meter', 'dispositivo', 'equipamento', 'módulo', 'hardware',
    # System
    'AMI', 'AMM', 'MDM', 'MDC', 'NMS', 'SCADA', 'sistema', 'software',
    # Network
    'WISUN', 'Wi-SUN', 'telecom', 'comunicação', 'rede', 'wireless',
    # Interface
    'concentrador', 'gateway', 'roteador', 'switch', 'servidor',
    'banco de dados', 'database', 'API', 'interface', 'protocolo'
]

# Non-requirement content filter keywords.
# These are *generic* scraping/metadata tokens only.  Do NOT add
# customer-, project-, region-, or document-specific terms here.
NON_REQUIREMENT_KEYWORDS = [
    'document title', 'table of contents', 'index',
    'classification', 'introduction', 'objective', 'scope', 'definitions',
    'abbreviations', 'references', 'annexes', 'appendix', 'figure', 'table',
    'prepared by', 'verified by', 'approved by', 'version', 'revision',
    # Romance-language equivalents (kept generic)
    'título do documento', 'sumário', 'índice', 'página',
    'classificação', 'introdução', 'objetivo', 'escopo', 'definições',
    'abreviações', 'referências', 'anexos', 'apêndice', 'figura', 'tabela',
    'elaborado por', 'verificado por', 'aprovado por', 'versão', 'revisão',
]

# Excel output config
EXCEL_CONFIG = {
    'column_widths': [12, 20, 20, 20, 12, 70, 12, 70, 70, 8, 20],
    'header_color': '4472C4',
    'translation_header_color': '70AD47',
    'validation_header_color': 'FF6B6B',
    'row_height': 60
}

# ============================================================================
# NEW: Hierarchical decomposition configuration
# ============================================================================

# Regex pattern for matching multi-level numbering (from user's requirement)
NUMBERING_PATTERN = r'^(\d+\.\d+\.\d+|\d+\.\d+|\d+|[一二三四五六七八九十]+|（[一二三四五六七八九十]+）|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩])[.、\s]*'

# Hierarchical levels mapping
HIERARCHY_LEVELS = {
    1: 'chapter',    # 章 - Top level (e.g., 1., 一、)
    2: 'section',    # 节 - Second level (e.g., 1.1, （一）)
    3: 'article',    # 条 - Third level (e.g., 1.1.1, （1）)
    4: 'paragraph',  # 款 - Fourth level (e.g., ①)
    5: 'item'        # 项 - Fifth level (e.g., a), b))
}

# ============================================================================
# NEW: Validation configuration
# ============================================================================

# Validation rules
VALIDATION_CONFIG = {
    'min_content_length': 50,        # Minimum characters for a valid requirement
    'max_content_length': 2000,      # Maximum characters before warning
    'require_punctuation': True,     # Require sentence-ending punctuation
    'require_source_lang': False,    # Warn if no source-language indicators
    'filter_non_requirements': True  # Filter out headers/footers
}

# Romance-language indicators (used when source is pt / es / fr / it).
# Kept here — not tied to any single locale.
ROMANCE_INDICATORS = [
    r'\b(de|do|da|dos|das|em|um|uma|para|com|por|que|se|na|no|ao|ou)\b',
    r'(ção|mente|idade|ismo|ista|oso|osa|ico|ica|ado|ido|ando|endo)'
]

# ============================================================================
#  Sentence-segmentation abbreviation lists (per source language).
#  Used by SentenceSegmenter to protect tokens whose "." is NOT a sentence
#  boundary.  All lowercase; segmenter normalises the same way.
# ============================================================================
ABBR = {
    'pt': [
        'art', 'ex', 'dr', 'dra', 'prof', 'sra', 'sr', 'pág', 'fls',
        'fl', 'nº', 'inc', 'al', 'c/c', 'ref', 'tel', 'op', 'cta',
        'v.exa', 'v.rev', 'ed', 'vol', 'cap', 'pg', 'pp', 'obs',
        'fig', 'tab', 'resp', 'item', 'aprox', 'máx', 'mín', 'etc',
        'ud', 'p', 'sf', 'ss', 'a.c', 'd.c', 'exmo', 'exma', 'rev',
    ],
    'en': [
        'mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'jr', 'st', 'ave',
        'blvd', 'inc', 'ltd', 'corp', 'vs', 'etc', 'eg', 'ie', 'al',
        'approx', 'min', 'max', 'temp', 'vol', 'fig', 'tab', 'eq',
        'ref', 'ed', 'rev', 'no', 'nos', 'pp', 'pg', 'sec', 'ch',
        'chap', 'art', 'item', 'resp', 'op', 'cit',
    ],
    'es': [
        'art', 'pág', 'fl', 'núm', 'inc', 'ref', 'tel', 'ud', 'p',
        'vol', 'cap', 'pg', 'pp', 'obs', 'fig', 'tab', 'resp', 'item',
        'aprox', 'máx', 'mín', 'etc', 'ed', 'rev', 'ex', 'excmo',
        'ilmo', 'sr', 'sra', 'dr', 'dra', 'prof', 'p.ej',
    ],
    'fr': [
        'art', 'p', 'pp', 'fig', 'tab', 'réf', 'tél', 'c.-à-d',
        'etc', 'ex', 'vol', 'chap', 'éd', 'rév', 'av', 'bd', 'st',
        'sr', 'jr', 'dr', 'prof', 'm', 'mm', 'mlle', 'mme',
    ],
    'de': [
        'art', 's', 'seite', 'p', 'pp', 'fig', 'tab', 'ref', 'tel',
        'usw', 'z.b', 'd.h', 'u.a', 'vgl', 'ca', 'min', 'max', 'vol',
        'cap', 'ed', 'rev', 'resp', 'item', 'nr', 'abs',
    ],
    'zh': [],  # CJK uses dedicated terminator rules, not abbreviation protect
    'ja': [],
    'ko': [],
}

# ============================================================================
#  Extraction-validation knobs
# ============================================================================
VALIDATION = {
    'min_char_coverage': 0.80,       # hard error if coverage < this
    'min_word_coverage': 0.85,       # soft warn  if coverage < this
    'write_orphans': True,           # write *_orphans.json when orphans found
    'orphans_json_path': None,       # None → auto from input path
    'sentence_target_min': 50,       # below → fold into previous
    'sentence_target_max': 500,      # above → split on nearest ","
}
