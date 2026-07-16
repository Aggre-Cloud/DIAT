#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Post-processing script: Split multi-item requirements into individual rows.

Reads the existing JSON output, detects item markers (a), b), ..., z), aa), bb),
i., ii., iii., etc.), splits content/translations by those markers, and generates
a new fully itemized JSON + XLSX.

Usage:
    python split_items_postprocess.py [input_json] [output_dir]
"""
import sys
import os
import re
import json
import importlib.util
from pathlib import Path

# Ensure UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent to path for excel_generator
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def detect_item_style(content):
    """
    Detect the primary item marker style in content text.
    Returns: 'bare_letter', 'roman', 'parenthesized', or None
    """
    if not content:
        return None

    # Check for bare letter items: a), b), c), ..., z), aa), bb)
    # Can be preceded by whitespace, semicolon, period, newline, or start of string
    bare_pattern = r'(?:^|[\s;,.])([a-z]{1,2})\)\s'
    bare_matches = re.findall(bare_pattern, content)
    if len(bare_matches) >= 2:
        return 'bare_letter'

    # Check for roman numeral items: i., ii., iii., iv., v., etc.
    roman_pattern = r'(?:^|[\s;,.])(i{1,3}|i[vx]|v?i{0,3})\.\s'
    roman_matches = re.findall(roman_pattern, content, re.IGNORECASE)
    if len(roman_matches) >= 2:
        return 'roman'

    # Check for parenthesized items: (a), (b), (i), (ii)
    paren_pattern = r'(?:^|[\s;,.])\(([a-z]{1,2}|i{1,3}|i[vx]|v?i{0,3})\)\s'
    paren_matches = re.findall(paren_pattern, content, re.IGNORECASE)
    if len(paren_matches) >= 2:
        return 'parenthesized'

    return None


def _find_bare_letter_matches(text):
    """Find all bare letter marker positions in text."""
    pattern = r'(?:^|[\s;,.])([a-z]{1,2})\)\s'
    return list(re.finditer(pattern, text))


def _find_roman_matches(text):
    """Find all roman numeral marker positions in text."""
    pattern = r'(?:^|[\s;,.])(i{1,3}|i[vx]|v?i{0,3})\.\s'
    return list(re.finditer(pattern, text, re.IGNORECASE))


def split_by_bare_letters(text):
    """
    Split text by bare letter markers: a), b), c), ..., z), aa), bb), cc)
    Returns list of (marker, content) tuples.
    """
    if not text:
        return []

    matches = _find_bare_letter_matches(text)

    if len(matches) < 2:
        # Not enough markers to split
        return [('', text.strip())]

    parts = []
    for i, match in enumerate(matches):
        marker = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        # Clean up: remove trailing header/footer contamination
        content = clean_trailing_garbage(content)
        parts.append((f'{marker})', content))

    return parts


def split_by_roman_numerals(text):
    """
    Split text by roman numeral markers: i., ii., iii., iv., v., etc.
    Returns list of (marker, content) tuples.
    """
    if not text:
        return []

    matches = _find_roman_matches(text)

    if len(matches) < 2:
        return [('', text.strip())]

    parts = []
    for i, match in enumerate(matches):
        marker = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        content = clean_trailing_garbage(content)
        parts.append((f'{marker}.', content))

    return parts


def clean_trailing_garbage(text):
    """
    Remove PDF header/footer contamination from text.
    """
    if not text:
        return text

    # Remove "N.Documento: Categoria: Versão: ..." patterns
    text = re.sub(r'N\.?Documento:.*$', '', text, flags=re.IGNORECASE)
    # Remove "Tipo de Documento: ..." patterns
    text = re.sub(r'Tipo de Documento:.*$', '', text, flags=re.IGNORECASE)
    # Remove standalone page numbers
    text = re.sub(r'Página\s+\d+\s+de\s+\d+.*$', '', text, flags=re.IGNORECASE)
    # Remove classification lines
    text = re.sub(r'Classificação:.*$', '', text, flags=re.IGNORECASE)
    # Remove revision control
    text = re.sub(r'Controle de Revisão.*$', '', text, flags=re.IGNORECASE)

    return text.strip()


def find_translation_segments(translation_text, num_segments):
    """
    Try to split a translation text into segments matching the original items.
    Uses common translation patterns for markers.

    Returns list of segment strings (may be empty strings for failed splits).
    """
    if not translation_text or num_segments <= 1:
        return [translation_text] if translation_text else ['']

    segments = []

    # Strategy 1: Try bare letter markers (most common)
    # In English translations, markers are often preserved as a), b), c)
    bare_matches = _find_bare_letter_matches(translation_text)

    if len(bare_matches) >= num_segments:
        for i, match in enumerate(bare_matches[:num_segments]):
            start = match.end()
            end = bare_matches[i + 1].start() if i + 1 < len(bare_matches) else len(translation_text)
            seg = translation_text[start:end].strip()
            seg = clean_trailing_garbage(seg)
            segments.append(seg)
        return segments

    # Strategy 2: Try roman numeral markers
    roman_matches = _find_roman_matches(translation_text)

    if len(roman_matches) >= num_segments:
        for i, match in enumerate(roman_matches[:num_segments]):
            start = match.end()
            end = roman_matches[i + 1].start() if i + 1 < len(roman_matches) else len(translation_text)
            seg = translation_text[start:end].strip()
            seg = clean_trailing_garbage(seg)
            segments.append(seg)
        return segments

    # Strategy 3: If translation has same number of sentences as segments,
    # try splitting by sentence boundaries after markers
    # Fallback: return full text as single segment
    return [translation_text] + [''] * (num_segments - 1)


def split_requirement(req):
    """
    Split a single requirement into multiple requirements if it contains
    multiple items.

    Returns list of requirement dicts.
    """
    content = req.get('content', '')
    english = req.get('english', '')
    chinese = req.get('chinese', '')

    if not content:
        return [req]

    # Detect item style
    style = detect_item_style(content)

    if style is None:
        # No items to split
        return [req]

    # Split by detected style
    if style == 'bare_letter':
        items = split_by_bare_letters(content)
    elif style == 'roman':
        items = split_by_roman_numerals(content)
    else:
        return [req]

    if len(items) <= 1:
        return [req]

    # Split translations to match
    en_segments = find_translation_segments(english, len(items))
    zh_segments = find_translation_segments(chinese, len(items))

    # Create new requirements for each item
    results = []
    for idx, (marker, item_content) in enumerate(items):
        if not item_content.strip():
            # Skip empty items (likely just header/footer garbage)
            continue

        en_seg = en_segments[idx] if idx < len(en_segments) else ''
        zh_seg = zh_segments[idx] if idx < len(zh_segments) else ''

        new_req = {
            'id': '',  # Will be renumbered later
            '章': req.get('章', ''),
            '节': req.get('节', ''),
            '条': req.get('条', ''),
            'content': f'{marker} {item_content}' if marker else item_content,
            'category': req.get('category', ''),
            'is_product': req.get('is_product', 'No'),
            'english': en_seg,
            'chinese': zh_seg,
            'is_valid': req.get('is_valid', True),
            'note': req.get('note', '')
        }
        results.append(new_req)

    return results if results else [req]


def process_json(input_path, output_dir):
    """
    Main processing function.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load JSON
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    requirements = data.get('requirements', [])
    language = data.get('metadata', {}).get('detected_language', 'pt')

    print(f"Loaded {len(requirements)} requirements from {input_path.name}")

    # Split requirements
    new_requirements = []
    split_count = 0
    for req in requirements:
        split_reqs = split_requirement(req)
        if len(split_reqs) > 1:
            split_count += 1
        new_requirements.extend(split_reqs)

    print(f"Split {split_count} requirements with multiple items")
    print(f"Total after splitting: {len(new_requirements)} requirements")

    # Renumber all requirements
    for idx, req in enumerate(new_requirements, 1):
        req['id'] = f'REQ-{idx:04d}'

    # Save JSON
    output_json = output_dir / f'{input_path.stem}_split.json'
    json_output = {
        'version': '3.1',
        'metadata': {
            'total_requirements': len(new_requirements),
            'detected_language': language,
            'post_processed': True,
            'split_count': split_count
        },
        'requirements': new_requirements
    }
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, ensure_ascii=False, indent=2)
    print(f"JSON saved: {output_json}")

    # Generate XLSX
    try:
        excel_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  '005_excel_generator', 'excel_generator_v3.py')
        spec = importlib.util.spec_from_file_location('excel_generator_v3', excel_path)
        excel_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(excel_module)
        excel_gen = excel_module.ExcelGeneratorV3()
        output_xlsx = output_dir / f'{input_path.stem}_split.xlsx'
        excel_gen.generate(new_requirements, str(output_xlsx), language)
        print(f"XLSX saved: {output_xlsx}")
    except Exception as e:
        print(f"Warning: Could not generate XLSX: {e}")

    return str(output_json)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Post-process: split multi-item requirements')
    parser.add_argument('input', nargs='?', default=None, help='Input JSON file')
    parser.add_argument('-o', '--output', default=None, help='Output directory')
    args = parser.parse_args()

    if args.input:
        input_path = args.input
    else:
        input_path = input('  Enter input JSON path: ').strip()
        if not input_path:
            print('  [ERROR] No input given.')
            return

    if args.output:
        output_dir = args.output
    else:
        output_dir = os.path.join(os.path.dirname(input_path), 'split')

    process_json(input_path, output_dir)


if __name__ == '__main__':
    main()
