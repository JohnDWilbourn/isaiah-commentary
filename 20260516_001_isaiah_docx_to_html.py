#!/usr/bin/env python3
"""
20260516_001_isaiah_docx_to_html.py
=====================================
Converts isaiah53.docx to isaiah53.html for the Isaiah commentary site.

Usage:
    python3 20260516_001_isaiah_docx_to_html.py <input.docx> <output.html>
"""

import sys
import re
import zipfile
import html as htmlmod
from pathlib import Path
from xml.etree import ElementTree as ET

W  = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
WN = f'{{{W}}}'

GLOSSARY_HEADING_STYLES = {'GlossaryTableHeading'}
GLOSSARY_CELL_STYLES    = {'GlossaryTermColumn1','GreekGlossaryTerm',
                            'GreekGlossaryTransliteration','GlossaryDefinitionText'}
GLOSSARY_TABLE_STYLES   = GLOSSARY_HEADING_STYLES | GLOSSARY_CELL_STYLES
DATA_HEADING_STYLES     = {'TableHeading'}
DATA_CELL_STYLES        = {'TableContents'}
DATA_TABLE_STYLES       = DATA_HEADING_STYLES | DATA_CELL_STYLES

def _get_style(para):
    pPr = para.find(f'{WN}pPr')
    if pPr is None: return ''
    ps = pPr.find(f'{WN}pStyle')
    return ps.get(f'{WN}val', '') if ps is not None else ''

def _text(elem):
    parts = []
    for t in elem.iter(f'{WN}t'):
        parts.append(t.text or '')
    return ''.join(parts)

def _rich_text(para):
    parts = []
    for run in para.findall(f'{WN}r'):
        rpr  = run.find(f'{WN}rPr')
        text = ''.join(t.text or '' for t in run.findall(f'{WN}t'))
        if not text:
            continue
        text = htmlmod.escape(text)
        bold   = rpr is not None and rpr.find(f'{WN}b')   is not None
        italic = rpr is not None and rpr.find(f'{WN}i')   is not None
        if bold and italic:
            text = f'<strong><em>{text}</em></strong>'
        elif bold:
            text = f'<strong>{text}</strong>'
        elif italic:
            text = f'<em>{text}</em>'
        parts.append(text)
    return ''.join(parts)

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:80].strip('-')

def is_glossary_table(table):
    for row in table.findall(f'{WN}tr')[:2]:
        for cell in row.findall(f'{WN}tc'):
            for para in cell.findall(f'{WN}p'):
                s = _get_style(para)
                if s in GLOSSARY_TABLE_STYLES: return True
                if _text(para).strip().lower() == 'term': return True
    return False

def is_data_table(table):
    for row in table.findall(f'{WN}tr')[:2]:
        for cell in row.findall(f'{WN}tc'):
            for para in cell.findall(f'{WN}p'):
                if _get_style(para) in DATA_TABLE_STYLES: return True
    return False

def render_glossary_table(table, glossary_index):
    rows = table.findall(f'{WN}tr')
    lines = [
        f'<div class="glossary-wrap" id="glossary-{glossary_index}">',
        '  <p class="glossary-label">Glossary</p>',
        '  <table class="glossary-table"><tbody>',
    ]
    for row_idx, row in enumerate(rows):
        cells = row.findall(f'{WN}tc')
        is_header = row_idx == 0
        row_class = 'header-row' if is_header else ('' if row_idx % 2 == 0 else 'alt-row')
        lines.append(f'    <tr class="{row_class}">')
        for col_idx, cell in enumerate(cells):
            paras = cell.findall(f'{WN}p')
            cell_class = 'greek-cell' if col_idx == 1 else ''
            lines.append(f'      <td class="{cell_class}">')
            cell_parts = []
            for para in paras:
                t = _text(para).strip()
                if t: cell_parts.append(htmlmod.escape(t))
            lines.append('\n'.join(cell_parts))
            lines.append('      </td>')
        lines.append('    </tr>')
    lines += ['  </tbody></table>', '</div>']
    return '\n'.join(lines)

def render_data_table(table):
    rows = table.findall(f'{WN}tr')
    lines = ['<div class="data-table-wrap">', '  <table class="data-table"><tbody>']
    for row_idx, row in enumerate(rows):
        cells = row.findall(f'{WN}tc')
        first_styles = set()
        for cell in cells:
            for para in cell.findall(f'{WN}p'):
                s = _get_style(para)
                if s: first_styles.add(s)
        is_header = bool(first_styles & DATA_HEADING_STYLES) or row_idx == 0
        row_class = 'header-row' if is_header else ('' if row_idx % 2 == 0 else 'alt-row')
        tag = 'th' if is_header else 'td'
        lines.append(f'    <tr class="{row_class}">')
        for cell in cells:
            paras = cell.findall(f'{WN}p')
            cell_parts = [htmlmod.escape(_text(p).strip()) for p in paras if _text(p).strip()]
            lines.append(f'      <{tag}>{" ".join(cell_parts)}</{tag}>')
        lines.append('    </tr>')
    lines += ['  </tbody></table>', '</div>']
    return '\n'.join(lines)

def build_nav(sections):
    lines = ['<ul id="nav-list">']
    for sec_id, sec_title, level in sections:
        cls = f'nav-h{level}'
        lines.append(f'  <li class="{cls}"><a href="#{sec_id}">{htmlmod.escape(sec_title)}</a></li>')
    lines.append('</ul>')
    return '\n'.join(lines)

def convert(input_path: str, output_path: str):
    input_path  = Path(input_path)
    output_path = Path(output_path)

    with zipfile.ZipFile(input_path, 'r') as z:
        doc_xml = z.read('word/document.xml').decode('utf-8')

    root = ET.fromstring(doc_xml)
    body = root.find(f'{WN}body')

    content_lines = []
    nav_sections  = []
    glossary_count = 0
    used_ids = {}
    chapter_seen = False

    def unique_id(base):
        count = used_ids.get(base, 0) + 1
        used_ids[base] = count
        return base if count == 1 else f'{base}-{count}'

    elems = list(body)
    i = 0
    last_was_heading1 = False

    while i < len(elems):
        elem = elems[i]
        tag  = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

        if tag == 'tbl':
            if is_glossary_table(elem):
                glossary_count += 1
                content_lines.append(render_glossary_table(elem, glossary_count))
            else:
                content_lines.append(render_data_table(elem))
            i += 1
            continue

        if tag != 'p':
            i += 1
            continue

        style = _get_style(elem)
        text  = _text(elem).strip()
        rich  = _rich_text(elem)

        if not text:
            content_lines.append('<div class="spacer"></div>')
            i += 1
            continue

        if style == 'Heading1':
            chap_id = 'isaiah-53'
            content_lines.append(
                f'<h1 id="{chap_id}" class="chapter-title">{htmlmod.escape(text)}</h1>'
            )
            nav_sections.append((chap_id, text, 1))
            last_was_heading1 = True
            chapter_seen = True

        elif style == 'Header1Sub1':
            content_lines.append(
                f'<h2 class="chapter-subtitle">{htmlmod.escape(text)}</h2>'
            )
            last_was_heading1 = False

        elif style == 'BlockQuotation':
            content_lines.append(
                f'<blockquote class="esv-quote">{rich}</blockquote>'
            )

        elif style == 'Heading2':
            sec_id = unique_id(slugify(text))
            content_lines.append(
                f'<h2 id="{sec_id}"><strong>{htmlmod.escape(text)}</strong></h2>'
            )
            nav_sections.append((sec_id, text, 2))

        elif style == 'Heading3':
            sec_id = unique_id(slugify(text))
            content_lines.append(
                f'<h3 id="{sec_id}"><strong>{htmlmod.escape(text)}</strong></h3>'
            )
            nav_sections.append((sec_id, text, 3))

        elif style == 'Conclusions':
            sec_id = unique_id(slugify(text))
            content_lines.append(
                f'<h2 id="{sec_id}" class="conclusions-heading"><strong>{htmlmod.escape(text)}</strong></h2>'
            )
            nav_sections.append((sec_id, text, 2))

        elif style == 'ConclusionsfromChapter':
            content_lines.append(f'<p class="conclusions-point">{rich}</p>')

        elif style == 'Glossary':
            content_lines.append(
                f'<h2 id="glossary" class="glossary-section-heading"><strong>{htmlmod.escape(text)}</strong></h2>'
            )
            nav_sections.append(('glossary', text, 2))

        elif style in ('BodyText', 'Normal', ''):
            if text:
                content_lines.append(f'<p>{rich}</p>')

        else:
            if text:
                content_lines.append(f'<p>{rich}</p>')

        i += 1

    nav_html = build_nav(nav_sections)

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="A verse-by-verse exegetical commentary on Isaiah 53.">
  <title>Isaiah 53 — A Verse-by-Verse Commentary</title>
  <link rel="stylesheet" href="style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=EB+Garamond:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
</head>
<body>

<div id="progress-bar"></div>

<button id="menu-toggle" aria-label="Open navigation">
  <span></span><span></span><span></span>
</button>

<div id="sidebar-overlay"></div>

<nav id="sidebar">
  <div id="sidebar-header">
    <h2>Isaiah 53</h2>
    <p>The Suffering Servant</p>
  </div>
  <input id="nav-search" type="text" placeholder="Search sections…" aria-label="Search navigation">
  {nav_html}
</nav>

<main id="main">

{''.join(chr(10) + line for line in content_lines)}

<hr style="margin: 3rem 0 1rem; border: none; border-top: 1px solid var(--rule);">
<p style="font-family: \'Cinzel\', serif; font-size: 0.68rem; letter-spacing: 0.1em; color: #9a8060; text-align: center;">
  &copy; 2026 JohnDavid Wilbourn &nbsp;&middot;&nbsp; Isaiah 53 Commentary &nbsp;&middot;&nbsp; Based on the BHS / NA28 critical text
</p>

</main>

<a href="#" id="top-btn">&#8593; Top</a>

<script src="nav.js"></script>
</body>
</html>'''

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(page, encoding='utf-8')
    print(f"Done — {output_path}")
    print(f"  Nav sections: {len(nav_sections)}")
    print(f"  Glossaries:   {glossary_count}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 20260516_001_isaiah_docx_to_html.py <input.docx> <output.html>")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
