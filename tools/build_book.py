"""Build a source-free offline reading edition from authored HTML fragments."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
START = '<!-- BOOK-CONTENT-START -->'
END = '<!-- BOOK-CONTENT-END -->'


def esc(value):
    return html.escape(str(value), quote=True)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def page(title, content, manifest, chapter=None):
    links = [('index.html', 'Chapters'), ('book-overview.html', 'Study guide'),
             ('source-map.html', 'Source map'), ('references.html', 'References'),
             ('numerical-lab.html', 'Algebra laboratory')]
    nav = ''.join(f'<a href="{p}">{label}</a>' for p, label in links)
    toc = '<aside class="toc" id="chapter-toc" aria-label="On this page"><h2>On this page</h2></aside>' if chapter else ''
    turns = ''
    if chapter:
        i = chapter['order']-1
        chapters = manifest['chapters']
        prev = f'<a rel="prev" href="{esc(chapters[i-1]["file"])}">Previous chapter</a>' if i else '<span>First chapter</span>'
        nxt = f'<a rel="next" href="{esc(chapters[i+1]["file"])}">Next chapter</a>' if i+1 < len(chapters) else '<span>End of book</span>'
        turns = f'<nav class="page-turn" aria-label="Chapter navigation">{prev}<a href="index.html">Chapter index</a>{nxt}</nav>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark light"><meta name="book-content-sha256" content="{digest(content.encode())}">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'none'; base-uri 'none'; object-src 'none'">
<meta name="description" content="Independent transcript-grounded Algebra 1 textbook: proofs, worked examples, exercises, and offline mathematics.">
<title>{esc(title)} · Algebra 1: Foundations</title><link rel="stylesheet" href="assets/book.css">
<script src="assets/math-config.js"></script><script defer src="assets/mathjax-tex-svg.js"></script><script defer src="assets/book.js"></script><script defer src="assets/lab.js"></script></head>
<body><a class="skip" href="#main">Skip to content</a><header class="site-header"><a class="brand" href="index.html">Algebra 1: Foundations · NPTEL</a><nav class="course-nav" aria-label="Book">{nav}</nav></header>
<div class="layout{'' if chapter else ' no-toc'}">{toc}<main id="main"><div class="reading-tools" aria-label="Reading controls"><button id="theme-toggle" aria-pressed="false">Light theme</button><button id="text-toggle" aria-pressed="false">Larger text</button><button id="solutions-toggle" aria-pressed="false">Expand solutions</button><button id="print-page">Print with solutions</button></div>
<article id="chapter-content">{START}{content}{END}</article>{turns}</main></div>
<footer class="site-footer">Independent educational edition of Jaikrishnan J's NPTEL course, IIT Palakkad; coordinating institution IIT Madras. Recordings determine topic order. Added proofs, examples, code, and exercises are original teaching material. Attribution does not imply endorsement. <a href="WORKFLOW.md">Workflow</a> · <a href="source-manifest.json">Source inventory</a> · <a href="validation/summary.json">Validation</a>.</footer></body></html>'''


def build(draft=False):
    manifest = json.loads((ROOT/'source-manifest.json').read_text(encoding='utf-8'))
    source_map, rows, ledger = [], [], []
    statistics = []
    for chapter in manifest['chapters']:
        path = ROOT/chapter['manuscript']
        if not path.exists():
            if draft:
                continue
            raise FileNotFoundError(path)
        content = path.read_text(encoding='utf-8')
        doc = BeautifulSoup(content, 'html.parser')
        assert doc.h1 and doc.h1.get_text().startswith(str(chapter['order'])+'.')
        for h in doc.select('h2, h3'):
            if not h.get('id'):
                raise ValueError(f'Missing heading ID: {path}, {h.get_text()}')
        (ROOT/chapter['file']).write_text(page(chapter['title'], content, manifest, chapter), encoding='utf-8', newline='\n')
        lectures = [v for v in manifest['lectures'] if v['chapter_order'] == chapter['order']]
        labels = ', '.join('Introduction' if v['lecture_number'] == 0 else str(v['lecture_number']) for v in lectures)
        rows.append(f'<li data-lecture><h2><a href="{esc(chapter["file"])}">{chapter["order"]:02d}. {esc(chapter["title"])}</a></h2><p class="lecture-meta">Source lessons: {esc(labels)}</p></li>')
        section_map = []
        for h in doc.select('h2,h3'):
            urls = [a['href'] for a in h.select('a[href]') if 'youtube.com/' in a['href']]
            if urls:
                section_map.append({'heading': h.get_text(' ', strip=True), 'anchor': h['id'], 'recording_urls': urls})
        entry = {'chapter': chapter['order'], 'file': chapter['file'], 'lecture_numbers': chapter['lecture_numbers'], 'sections': section_map}
        source_map.append(entry)
        prose_doc = BeautifulSoup(content, 'html.parser')
        for pre in prose_doc.select('pre'):
            pre.decompose()
        stat = {'chapter': chapter['order'], 'body_sha256': digest(content.encode()),
                'words_excluding_code': len(prose_doc.get_text(' ', strip=True).split()),
                'problems': len(doc.select('details')), 'python_listings': len(doc.select('code.language-python')),
                'timestamp_anchors': sum(len(s['recording_urls']) for s in section_map)}
        statistics.append(stat)
        sidecar = {**chapter, **stat, 'sections': section_map}
        (ROOT/chapter['file'].replace('.html','.meta.json')).write_text(json.dumps(sidecar, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    count = len(statistics)
    words = sum(s['words_excluding_code'] for s in statistics)
    problems = sum(s['problems'] for s in statistics)
    intro = (ROOT/'chapters/_index.html').read_text(encoding='utf-8')
    intro += f'<p class="source-note">This edition contains {count} chapters, approximately {words:,} words excluding code, and {problems} worked problems.</p>'
    intro += '<label class="search-label" for="lecture-search">Find a chapter or topic</label><input id="lecture-search" type="search" placeholder="Try quotients, induction, eigenvalues, or Jordan"><p id="search-status" role="status">'+str(count)+' chapters shown</p><ul class="lecture-list">'+''.join(rows)+'</ul>'
    (ROOT/'index.html').write_text(page('Chapter index', intro, manifest), encoding='utf-8', newline='\n')
    ledger.append('<h1>Recording and timestamp map</h1><p>All 46 playlist entries are retained. The official NPTEL course page fixes the order of 45 teaching lessons; the introduction is placed first. Original playlist positions remain visible. Timestamp links identify related discussion, not the provenance of every added proof or example.</p><table><thead><tr><th>Lesson</th><th>Original position</th><th>Recording</th><th>Duration</th><th>Chapter</th></tr></thead><tbody>')
    for v in manifest['lectures']:
        c = manifest['chapters'][v['chapter_order']-1]
        n = v['lecture_number'] or 'Introduction'
        ledger.append(f'<tr><td>{esc(n)}</td><td>{v["playlist_position"]}</td><td><a href="{esc(v["url"])}">{esc(v["title"])}</a></td><td>{v["duration_seconds"]//60}:{v["duration_seconds"]%60:02d}</td><td><a href="{esc(c["file"])}">{c["order"]}</a></td></tr>')
    ledger.append('</tbody></table>')
    for c in source_map:
        ledger.append(f'<h2 id="chapter-{c["chapter"]}">Chapter {c["chapter"]}</h2><ul>')
        for s in c['sections']:
            ledger.append(f'<li><a href="{esc(c["file"])}#{esc(s["anchor"])}">{esc(s["heading"])}</a></li>')
        ledger.append('</ul>')
    (ROOT/'source-map.html').write_text(page('Recording map', ''.join(ledger), manifest), encoding='utf-8', newline='\n')
    (ROOT/'source-map.json').write_text(json.dumps(source_map, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for source, dest in [('_overview.html','book-overview.html'),('_references.html','references.html'),('_lab.html','numerical-lab.html')]:
        path = ROOT/'chapters'/source
        if not path.exists() and not draft:
            raise FileNotFoundError(path)
        if path.exists():
            content = path.read_text(encoding='utf-8')
            title = BeautifulSoup(content,'html.parser').h1.get_text()
            (ROOT/dest).write_text(page(title, content, manifest), encoding='utf-8', newline='\n')
    (ROOT/'validation/content-statistics.json').write_text(json.dumps(statistics, indent=2)+'\n', encoding='utf-8')
    print(f'Built {count} chapters; {words:,} words excluding code; {problems} worked problems.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--draft', action='store_true', help='Permit absent manuscripts during production.')
    build(parser.parse_args().draft)
