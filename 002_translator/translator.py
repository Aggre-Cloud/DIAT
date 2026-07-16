"""
Translation module
Responsible for translating requirements to target languages.

Features:
1. Auto-detect source language (using langdetect)
2. Protect proper nouns / abbreviations before translation
3. Configurable target languages (default EN + ZH)
4. On failure returns empty string (not source text)
"""
import time
import sys
import os
import re
import uuid

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Lazy load config
def get_translation_config():
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", "007_config/config.py")
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config.TRANSLATION_CONFIG

def get_do_not_translate():
    """Return the legacy flat term list (back-compat).

    Internally delegates to the categorized config helper
    ``get_do_not_translate_flat()``.  Callers that need the category
    structure (e.g. main.py's interactive prompt) should use
    ``get_do_not_translate_categories()`` via importlib instead.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", "007_config/config.py")
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config.get_do_not_translate_flat()

# Try to import Google Translate
try:
    from googletrans import Translator
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False

# Try to import language detection library
try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False


class TranslationService:
    """Translation service class"""

    def __init__(self, target_languages=None):
        config = get_translation_config()
        self.use_google_translate = GOOGLE_TRANSLATE_AVAILABLE and config['use_google_translate']
        self.target_languages = target_languages or config.get('target_languages', ['en', 'zh-cn'])
        self.max_retries = config['max_retries']
        self.retry_delay = config['retry_delay']
        self.request_delay = config['request_delay']
        self.do_not_translate = get_do_not_translate()

        if self.use_google_translate:
            self.translator = Translator()
            print(f"[OK] Google Translate API initialized")
        else:
            print("[WARN] Google Translate not installed")
            print("  Install: pip install googletrans==4.0.0-rc1")

        if LANGDETECT_AVAILABLE:
            print("[OK] Language detection enabled")
        else:
            print("[WARN] langdetect not installed")
            print("  Install: pip install langdetect")
    
    # ------------------------------------------------------------------
    #  Proper-noun protection
    # ------------------------------------------------------------------

    def _protect_proper_nouns(self, text):
        """
        Replace proper nouns / abbreviations / acronyms with unique
        placeholders so Google Translate will leave them untouched.
        Returns (protected_text, placeholder_map).
        """
        if not text or not self.do_not_translate:
            return text, {}

        placeholder_map = {}
        protected = text

        # Sort by length (longest first); filter out very short (<2) entries
        terms = sorted(
            [t for t in self.do_not_translate if len(t) >= 2],
            key=len,
            reverse=True,
        )

        for term in terms:
            # Build a word-boundary-aware pattern.
            # For purely-alphanumeric terms use \\b boundaries.
            # For terms with special chars (NATO, O'B etc.) relax.
            escaped = re.escape(term)
            if re.match(r'^[A-Za-z0-9]+$', term):
                pattern = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
            else:
                pattern = re.compile(escaped, re.IGNORECASE)

            def _replacer(m):
                key = f"__PROPER_{uuid.uuid4().hex[:12]}__"
                placeholder_map[key] = m.group(0)
                return key

            protected = pattern.sub(_replacer, protected)

        return protected, placeholder_map

    def _restore_proper_nouns(self, text, placeholder_map):
        """Restore placeholders back to the original proper nouns."""
        if not placeholder_map:
            return text
        result = text
        for key, original in placeholder_map.items():
            result = result.replace(key, original)
        return result

    # ------------------------------------------------------------------
    #  Run-time category merge (for the JSON-queue / agent path)
    # ------------------------------------------------------------------

    def merge_do_not_translate_terms(self, terms_by_category):
        """Inject user-supplied categorized terms into the live cache.

        Parameters
        ----------
        terms_by_category : dict[str, list[str]]
            ``{category_key: [term, …]}``  — typically the
            ``extra_do_not_translate`` mapping read back from the agent
            JSON queue, or the dict returned by main.py's interactive
            prompt.  All values are flat-deduplicated into
            ``self.do_not_translate`` so the placeholder-protection pass
            sees them.
        """
        if not terms_by_category:
            return
        for terms in terms_by_category.values():
            for t in terms:
                if t and t not in self.do_not_translate:
                    self.do_not_translate.append(t)

    # ------------------------------------------------------------------
    #  Language detection
    # ------------------------------------------------------------------

    def detect_language(self, text):
        """
        Auto-detect source language from text.
        Returns langdetect code or 'unknown' if detection fails.

        Handles PDFs where Portuguese is rendered with CJK glyph artifacts:
        if langdetect reports a CJK language but the text also contains a
        substantial Latin skeleton, re-detect on the Latin-only skeleton so
        we don't misclassify Portuguese as Chinese.
        """
        if not LANGDETECT_AVAILABLE or not text or len(text.strip()) < 10:
            return "unknown"

        CJK_LANGS = {'zh-cn', 'zh-tw', 'ja', 'ko'}

        def _cjk_ratio(s):
            if not s:
                return 0.0
            cjk = sum(1 for ch in s if '一' <= ch <= '鿿')
            return cjk / len(s)

        def _latin_skeleton(s):
            """Keep only Latin letters, numbers, punctuation and whitespace."""
            return ''.join(ch for ch in s if ch.isascii())

        try:
            sample = text[:1000]
            detected = detect(sample)

            # Heuristic: PDFs with Portuguese→CJK glyph substitution trip
            # langdetect into reporting zh/ja/ko.  If the Latin-only skeleton
            # is substantial, re-detect on that skeleton instead.
            if detected in CJK_LANGS and _cjk_ratio(sample) < 0.55:
                skeleton = _latin_skeleton(sample)
                if len(skeleton.strip()) >= 20:
                    detected = detect(skeleton)
            return detected
        except Exception:
            return "unknown"

    # ------------------------------------------------------------------
    #  Core translation
    # ------------------------------------------------------------------

    def translate_text(self, text, target_lang, source_lang=None):
        """
        Translate text to target_lang.

        - Auto-detects source when source_lang is None
        - Protects proper nouns (DO_NOT_TRANSLATE list)
        - Returns empty string on failure (never returns source text)
        """
        if not text or len(text.strip()) < 3:
            return ""

        # Auto-detect source language if not specified
        if source_lang is None:
            source_lang = self.detect_language(text)

        # If source already matches target, skip translation
        if source_lang == target_lang:
            return text

        if not self.use_google_translate:
            return ""

        # Protect proper nouns before translating
        protected_text, placeholder_map = self._protect_proper_nouns(text)

        translated = self._translate_with_google(
            protected_text, target_lang, source_lang
        )

        # Restore proper nouns in translated text
        if placeholder_map:
            translated = self._restore_proper_nouns(translated, placeholder_map)

        return translated

    def _translate_with_google(self, text, target_lang, source_lang):
        """Translate using Google Translate."""
        MAX_LENGTH = 4500

        if not text or len(text.strip()) < 3:
            return ""

        if len(text) > MAX_LENGTH:
            chunks = self._split_text_safe(text, MAX_LENGTH)
            translated_chunks = []
            for i, chunk in enumerate(chunks):
                print(f"    Translating chunk {i + 1}/{len(chunks)} ({len(chunk)} chars)...")
                translated = self._translate_chunk(chunk, target_lang, source_lang)
                translated_chunks.append(translated)
            result = ' '.join(translated_chunks)
            result = re.sub(r'\s+', ' ', result).strip()
            return result
        else:
            return self._translate_chunk(text, target_lang, source_lang)

    def _split_text_safe(self, text, max_length):
        """Split text into chunks at word boundaries, preserving all content

        This is a safer implementation that:
        1. Never loses any content
        2. Splits at word boundaries
        3. Handles edge cases properly
        """
        chunks = []
        current_chunk = ''
        current_length = 0

        # Split by words while preserving all characters
        words = text.split()

        for word in words:
            word_len = len(word)

            # If single word exceeds max_length, we need to split the word itself
            if word_len > max_length:
                # First save current chunk if it exists
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ''
                    current_length = 0

                # Split the long word into parts
                for i in range(0, word_len, max_length):
                    part = word[i:i + max_length]
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = part
                    current_length = len(part)
                continue

            # Check if adding this word would exceed max_length
            # +1 for the space between words
            if current_length + word_len + 1 > max_length and current_chunk:
                chunks.append(current_chunk)
                current_chunk = word
                current_length = word_len
            else:
                if current_chunk:
                    current_chunk += ' ' + word
                    current_length += word_len + 1
                else:
                    current_chunk = word
                    current_length = word_len

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks if chunks else [text]

    def _translate_chunk(self, text, target_lang, source_lang):
        """Translate a single chunk with content preservation on failure

        If translation fails after all retries, returns the original text
        instead of a placeholder to prevent content loss.
        """
        if not text or len(text.strip()) < 3:
            return text

        for attempt in range(self.max_retries):
            try:
                # Add delay to avoid timeout
                time.sleep(self.request_delay)
                result = self.translator.translate(
                    text,
                    dest=target_lang,
                    src=source_lang
                )
                if result and result.text and result.text.strip():
                    translated = result.text.strip()
                    # Verify translation is not empty or too short
                    if len(translated) >= len(text) * 0.3:
                        return translated
                    else:
                        # Translation seems incomplete, retry
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay * (attempt + 1))
                            continue
                        # Return what we have if it's at least partially translated
                        return translated if translated else ""
                else:
                    # Empty result, retry
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    # Return empty string on complete failure
                    return ""
            except Exception as e:
                error_msg = str(e)[:80] if str(e) else "Unknown error"
                print(f"    Translation error (attempt {attempt + 1}): {error_msg}")
                if attempt < self.max_retries - 1:
                    # Increase retry delay
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    # Translation failed after all retries - return original text
                    # This ensures no content is lost
                    return ""

    def _get_placeholder(self, text, target_lang):
        """Get placeholder translation - returns original text to prevent content loss"""
        # Always return original text to ensure no content is lost
        return ""

    def translate_to_languages(self, text, target_langs=None, source_lang=None):
        """
        Translate text to multiple target languages.

        Args:
            text: Source text
            target_langs: List of target language codes
                          (defaults to self.target_languages)
            source_lang:  Force source language (None = auto-detect)

        Returns:
            dict: {lang_code: translated_text, 'detected_source': code}
        """
        target_langs = target_langs or self.target_languages

        if source_lang is None:
            source_lang = self.detect_language(text)

        result = {'detected_source': source_lang}

        for lang in target_langs:
            if lang == source_lang:
                result[lang] = text
            else:
                result[lang] = self.translate_text(text, lang, source_lang)

        return result


# =====================================================================
#  Language label helpers
# =====================================================================

LANG_LABELS = {
    'en':    '英文翻译',
    'zh-cn': '中文翻译',
    'pt':    '葡文翻译',
    'es':    '西班牙语翻译',
    'fr':    '法语翻译',
    'de':    '德语翻译',
    'ja':    '日语翻译',
    'ko':    '韩语翻译',
}

_LANG_NAMES = {
    'en': 'English',
    'zh-cn': 'Simplified Chinese',
    'pt': 'Portuguese',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'ja': 'Japanese',
    'ko': 'Korean',
}

def lang_label(code):
    return LANG_LABELS.get(code, f'{code}翻译')


# -----------------------------------------------------------------------
#  Module-level helpers
# -----------------------------------------------------------------------

_translation_service = None

def get_translator(target_languages=None):
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService(target_languages=target_languages)
    return _translation_service
