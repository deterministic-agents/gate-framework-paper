#!/usr/bin/env python3
"""Build the single-file markdown export (dist/GATE-v1.4-current.md).

Assembles index.qmd plus the chapter files in book order, resolves Quarto
includes, and normalises Quarto and docx-migration constructs that plain
markdown consumers cannot render:

- Quarto heading attributes ({#sec-x .unnumbered}) are stripped.
- Pandoc hard line breaks (trailing backslash) become two-space breaks.
- Pandoc multiline tables (dash-ruler format) become pipe tables; the
  single-column dash frames around JSON examples become fenced code blocks.
- Figure images are replaced by their mermaid sources from diagrams/,
  with captions preserved.
- Enforcement symbols become text markers (glyph-dependent semantics are
  not portable across PDF font stacks): checkmark -> R, circle -> C in the
  tier and tool matrices, checkmark -> Y and cross -> N in the tool
  authorization matrix.

Run from the repo root: python3 tools/build_markdown_export.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHAPTERS = ['index.qmd'] + [f'chapters/{c}.qmd' for c in [
    '01-changelog', '02-executive-summary', '03-scope-and-non-goals',
    '04-design-principles', '05-threat-model', '06-reference-architecture',
    '07-controls-at-a-glance', '08-implementation-guidance',
    '09-control-plane-contracts', '10-reference-repository',
    '11-control-catalog-layer-1', '12-control-catalog-layer-2',
    '13-control-catalog-layer-3', '14-control-catalog-layer-4',
    '15-operationalization', '16-conformance',
    'A1-evidence-pack-index', 'A2-standard-mappings', 'A3-artifacts',
    'A4-day2-runbooks', 'A5-cloud-quickstart', 'A6-glossary', 'A7-references']]

INCLUDE = re.compile(r'\{\{<\s*include\s+(\S+)\s*>\}\}')
DASH_LINE = re.compile(r'^\s*-{25,}\s*$')
RULER_LINE = re.compile(r'^\s*-+(?:\s+-+)+\s*$')


def resolve_includes(base: Path, text: str) -> str:
    return INCLUDE.sub(
        lambda m: resolve_includes(base, (base / m.group(1)).resolve().read_text()),
        text)


def split_code_fences(text: str):
    """Yield (is_code, segment) preserving fenced code blocks untouched."""
    parts = re.split(r'(^```.*?^```\s*$)', text, flags=re.M | re.S)
    for part in parts:
        yield part.startswith('```'), part


GRID_BORDER = re.compile(r'^\s*\+[-=]{10,}\+\s*$')


def unescape(text: str) -> str:
    """Remove pandoc backslash-escapes before punctuation."""
    return re.sub(r'\\([^\w\s\\])', r'\1', text)


def convert_grid_blocks(seg: str) -> str:
    """Single-column pandoc grid tables: prose callouts (bold first line)
    become blockquotes; anything else becomes a fenced code block."""
    lines = seg.split('\n')
    out, i = [], 0
    while i < len(lines):
        if not GRID_BORDER.match(lines[i]):
            out.append(lines[i]); i += 1
            continue
        j = i + 1
        while j < len(lines) and not GRID_BORDER.match(lines[j]):
            j += 1
        if j >= len(lines):
            out.append(lines[i]); i += 1
            continue
        rows = [l for l in lines[i + 1:j] if l.lstrip().startswith('|')]
        cells = []
        for r in rows:
            c = r.strip()
            c = c[1:-1] if c.endswith('|') else c[1:]
            c = re.sub(r'(\s\s|\\)\s*$', '', c.rstrip())
            cells.append(unescape(c.strip()))
        while cells and not cells[0]:
            cells.pop(0)
        while cells and not cells[-1]:
            cells.pop()
        if cells and cells[0].startswith('**'):
            out += ['> ' + c if c else '>' for c in cells]
        else:
            out += ['```'] + cells + ['```']
        i = j + 1
    return '\n'.join(out)


def ruler_spans(ruler: str):
    return [(m.start(), m.end()) for m in re.finditer(r'-+', ruler)]


def slice_row(line: str, spans):
    """Slice a table line at the ruler spans, extending any boundary that
    would split a word (cells occasionally overflow their column)."""
    cells, pos = [], 0
    for i, (start, end) in enumerate(spans):
        begin = max(pos, start)
        if i == len(spans) - 1:
            stop = len(line)
        else:
            stop = min(end, len(line))
            while 0 < stop < len(line) and line[stop - 1] != ' ' and line[stop] != ' ':
                stop += 1
        cells.append(line[begin:stop].strip())
        pos = stop
    return cells


def convert_multiline_tables(seg: str) -> str:
    lines = seg.split('\n')
    out, i = [], 0
    while i < len(lines):
        if not DASH_LINE.match(lines[i]):
            out.append(lines[i]); i += 1
            continue
        # find the closing full-width dash line
        j = i + 1
        while j < len(lines) and not DASH_LINE.match(lines[j]):
            j += 1
        if j >= len(lines):
            out.append(lines[i]); i += 1
            continue
        block = lines[i + 1:j]
        if any(re.match(r'#{1,6}\s', l) for l in block):
            # orphan dash line, not a table frame: drop it and keep scanning
            i += 1
            continue
        ruler_idx = next((k for k, l in enumerate(block) if RULER_LINE.match(l)), None)
        if ruler_idx is None:
            # single-column frame around a code example -> fenced code block
            body = [unescape(re.sub(r'(\s\s|\\)$', '', l[2:] if l.startswith('  ') else l))
                    for l in block]
            while body and not body[0].strip():
                body.pop(0)
            while body and not body[-1].strip():
                body.pop()
            out += ['```'] + body + ['```']
        else:
            spans = ruler_spans(block[ruler_idx])
            header_lines = [l for l in block[:ruler_idx] if l.strip()]
            header = [' '.join(filter(None, cells)) for cells in
                      zip(*(slice_row(l, spans) for l in header_lines))] \
                if header_lines else [''] * len(spans)
            header = [re.sub(r'\*\*', '', h) for h in header]
            rows, current = [], None
            for l in block[ruler_idx + 1:]:
                if not l.strip():
                    if current:
                        rows.append(current); current = None
                    continue
                cells = slice_row(l, spans)
                if current is None:
                    current = cells
                else:
                    current = [(a + ' ' + b).strip() if b else a
                               for a, b in zip(current, cells)]
            if current:
                rows.append(current)
            esc = lambda c: c.replace('|', '\\|')
            out.append('| ' + ' | '.join(esc(h) for h in header) + ' |')
            out.append('|' + '|'.join('---' for _ in spans) + '|')
            for r in rows:
                out.append('| ' + ' | '.join(esc(c) for c in r) + ' |')
        i = j + 1
    return '\n'.join(out)


SENTINEL = '\x01'


def map_symbols(text: str, chapter: str) -> str:
    """Replace 2-column-wide glyphs with letter + sentinel (same display
    width) so multiline-table column slicing stays aligned; sentinels are
    stripped after table conversion. A3's authorization matrix reads
    allowed / denied (Y / N); the tier and tool matrices read required /
    conditional (R / C)."""
    if 'A3-artifacts' in chapter:
        pairs = {'✅': 'Y', '❌': 'N', '⭕': 'C'}
    else:
        pairs = {'✅': 'R', '⭕': 'C', '❌': 'N'}
    for glyph, letter in pairs.items():
        text = text.replace(glyph, letter + SENTINEL)
    return text


def build() -> str:
    parts = [map_symbols(
                 resolve_includes((ROOT / f).parent, (ROOT / f).read_text()),
                 f).strip() + '\n'
             for f in CHAPTERS]
    doc = '\n\n'.join(parts)
    doc = re.sub(r'\{\{<\s*pagebreak\s*>\}\}', '', doc)
    doc = doc.replace('![](assets/images/hero.png){fig-align="center" width="70%"}\n\n', '')

    pieces = []
    for is_code, seg in split_code_fences(doc):
        if is_code:
            pieces.append(seg)
            continue
        seg = seg.replace('\u200b', '')
        seg = re.sub(r'^(#{1,6} .*?)\s*\{[^}\n]*\}\s*$', r'\1', seg, flags=re.M)
        seg = re.sub(r'\\\n', '  \n', seg)
        seg = convert_grid_blocks(seg)
        seg = convert_multiline_tables(seg)
        seg = re.sub(r'^:::.*$\n?', '', seg, flags=re.M)
        pieces.append(seg)
    doc = ''.join(pieces)

    doc = doc.replace(SENTINEL, '')
    # final pass: unescape pandoc escapes in prose and table cells, leaving
    # fenced code (original and newly created) untouched
    cleaned = []
    for is_code, seg in split_code_fences(doc):
        cleaned.append(seg if is_code else unescape(seg))
    doc = ''.join(cleaned)
    doc = doc.replace('Legend: R required, C conditional',
                      'Legend: R = required, C = conditional')

    # figures -> mermaid fences
    img = re.compile(r'!\[(.*?)\]\(\.\./assets/images/(figure-[a-z0-9-]+)\.png\)\{[^}]*\}', re.S)

    def sub_img(m):
        mmd = (ROOT / 'diagrams' / f'{m.group(2)}.mmd').read_text().strip()
        block = '```mermaid\n' + mmd + '\n```\n'
        if m.group(1).strip():
            block += '\n*' + m.group(1).strip() + '*'
        return block

    doc = img.sub(sub_img, doc)
    # orphan closing rules from odd-count dash frames at chapter boundaries
    doc = '\n'.join(l for l in doc.split('\n') if not DASH_LINE.match(l))
    doc = re.sub(r'\n{3,}', '\n\n', doc)
    return doc


if __name__ == '__main__':
    text = build()
    out = ROOT / 'dist' / 'GATE-v1.4-current.md'
    out.write_text(text)
    checks = {
        'mermaid fences': text.count('```mermaid'),
        'leftover heading attrs': len(re.findall(r'^#{1,6} .*\{', text, flags=re.M)),
        'leftover hard breaks': text.count('\\\n'),
        'leftover dash tables': len([l for l in text.split('\n') if DASH_LINE.match(l)]),
        'leftover glyphs': sum(text.count(c) for c in '✅⭕❌'),
        'em dashes': text.count('—'),
    }
    print(out, f'{len(text)} chars')
    for k, v in checks.items():
        print(f'  {k}: {v}')
    bad = (checks['mermaid fences'] != 9 or checks['leftover heading attrs']
           or checks['leftover hard breaks'] or checks['leftover dash tables']
           or checks['leftover glyphs'] or checks['em dashes'])
    sys.exit(1 if bad else 0)
