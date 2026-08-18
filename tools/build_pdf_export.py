#!/usr/bin/env python3
"""Render dist/GATE-v1.4-current.md to a print PDF via WeasyPrint.

Mermaid fences are swapped for the rendered PNG figures (a print artifact
cannot execute mermaid), everything else renders from the markdown with a
deliberate print stylesheet. Requires: pip install markdown weasyprint.

Run from the repo root: python3 tools/build_pdf_export.py [output.pdf]
"""

import base64
import re
import sys
from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent.parent
NARROW = {'figure-ra-1', 'figure-c17-1', 'figure-c19-1'}

CSS = '''
@page { size: A4; margin: 22mm 20mm;
        @bottom-center { content: counter(page); font-size: 8.5pt; color: #666; } }
body { font-family: "DejaVu Sans", sans-serif; font-size: 9.5pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 19pt; line-height: 1.2; margin: 0 0 10pt 0; page-break-before: always; padding-top: 4pt; }
h1.first { page-break-before: avoid; }
h2 { font-size: 14pt; margin: 14pt 0 6pt; line-height: 1.25; }
h3 { font-size: 11.5pt; margin: 11pt 0 5pt; }
h4 { font-size: 10pt; margin: 9pt 0 4pt; }
h1, h2, h3, h4 { page-break-after: avoid; }
p { margin: 0 0 6pt 0; }
ul, ol { margin: 0 0 6pt 0; padding-left: 16pt; }
li { margin-bottom: 2.5pt; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 8pt; }
th, td { border: 0.5pt solid #999; padding: 3pt 5pt; text-align: left; vertical-align: top; }
th { background: #f0f0f0; font-weight: bold; }
tr { page-break-inside: avoid; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 8.3pt; background: #f4f4f4; padding: 0 2pt; }
pre { background: #f6f6f6; border: 0.5pt solid #ddd; padding: 6pt; font-size: 7.8pt;
      line-height: 1.3; white-space: pre-wrap; word-wrap: break-word; margin: 6pt 0; }
pre code { background: none; padding: 0; }
blockquote { margin: 6pt 0 6pt 12pt; padding-left: 8pt; border-left: 2pt solid #ccc; color: #444; }
.figure { text-align: center; margin: 10pt 0; page-break-inside: avoid; }
.fig-wide { max-width: 100%; max-height: 210mm; }
.fig-narrow { max-width: 72%; max-height: 215mm; }
.caption { font-size: 8.5pt; font-style: italic; color: #444; margin-top: 4pt; text-align: left; }
.hero { text-align: center; margin: 55mm 0 12mm; }
.pagebreak { page-break-after: always; }
.hero img { max-width: 60%; }
a { color: #1a4d8f; text-decoration: none; }
.toc { page-break-after: always; }
.toc-title { font-size: 19pt; font-weight: bold; margin: 0 0 14pt 0; }
.toc-l1 { font-weight: bold; margin-top: 7pt; font-size: 9.5pt; }
.toc-l2 { padding-left: 14pt; font-size: 9pt; margin-top: 2pt; font-weight: normal; }
.toc-l3 { padding-left: 28pt; font-size: 9pt; margin-top: 1.5pt; font-weight: normal; }
.toc a { color: #1a1a1a; }
.toc a::after { content: leader(". ") target-counter(attr(href), page); font-weight: normal; color: #444; }
'''


def b64_png(name: str) -> str:
    return base64.b64encode((ROOT / 'assets/images' / f'{name}.png').read_bytes()).decode()


def build_pdf(out_path: Path) -> None:
    doc = (ROOT / 'dist' / 'GATE-v1.4-current.md').read_text()
    fig_by_src = {m.read_text().strip(): m.stem
                  for m in (ROOT / 'diagrams').glob('figure-*.mmd')}
    fence = re.compile(r'```mermaid\n(.*?)\n```\n(?:\n\*(.*?)\*)?', re.S)

    def sub(m):
        fig = fig_by_src.get(m.group(1).strip())
        if fig is None:
            raise SystemExit('mermaid fence does not match any diagrams/*.mmd source')
        cls = 'fig-narrow' if fig in NARROW else 'fig-wide'
        out = f'<div class="figure"><img class="{cls}" src="data:image/png;base64,{b64_png(fig)}">'
        if m.group(2):
            out += f'<p class="caption">{m.group(2).strip()}</p>'
        return out + '</div>'

    doc = fence.sub(sub, doc)
    body = markdown.markdown(doc, extensions=['tables', 'fenced_code', 'sane_lists'])
    body = body.replace('<h1>', '<h1 class="first">', 1)
    # title page carries only the hero, title, and subtitle; the version,
    # licensing, and disclaimer front matter starts on page 2
    body = re.sub(r'(<h1 class="first">.*?</h1>\s*<p><em>.*?</em></p>)',
                  r'\1<div class="pagebreak"></div>', body, count=1, flags=re.S)
    # table of contents: h1 and h2 entries with layout-time page numbers
    headings = []

    def tag_heading(m):
        level, attrs, text = m.group(1), m.group(2), m.group(3)
        if 'class="first"' in attrs:
            return m.group(0)
        hid = f'sec-{len(headings)}'
        label = re.sub(r'<[^>]+>', '', text).strip()
        headings.append((level, hid, label))
        return f'<h{level}{attrs} id="{hid}">{text}</h{level}>'

    def tag_h3(m):
        attrs, text = m.group(1), m.group(2)
        label = re.sub(r'<[^>]+>', '', text).strip()
        if not label.startswith('Control '):
            return m.group(0)
        hid = f'sec-{len(headings)}'
        headings.append(('3', hid, label))
        return f'<h3{attrs} id="{hid}">{text}</h3>'

    body = re.sub(r'<h([12])([^>]*)>(.*?)</h\1>', tag_heading, body, flags=re.S)
    body = re.sub(r'<h3([^>]*)>(.*?)</h3>', tag_h3, body, flags=re.S)
    # re-sort TOC entries into document order (h3 pass appended after h1/h2)
    order = {hid: body.index(f'id="{hid}"') for _, hid, _ in headings}
    headings.sort(key=lambda h: order[h[1]])
    toc = ['<div class="toc"><div class="toc-title">Contents</div>']
    toc += [f'<div class="toc-l{lvl}"><a href="#{hid}">{label}</a></div>'
            for lvl, hid, label in headings]
    toc.append('</div>')
    body = body.replace('<div class="pagebreak"></div>',
                        '<div class="pagebreak"></div>' + ''.join(toc), 1)
    html = (f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f'<body><div class="hero"><img src="data:image/png;base64,{b64_png("hero")}"></div>'
            f'{body}</body></html>')
    HTML(string=html).write_pdf(str(out_path))
    print(out_path)


if __name__ == '__main__':
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'dist' / 'GATE-v1.4.pdf'
    build_pdf(target)
