"""Check static integrity and offline desktop/mobile reader behavior."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def static_checks():
    manifest = json.loads((ROOT/'source-manifest.json').read_text(encoding='utf-8'))
    videos = {v['id']: v for v in manifest['lectures']}
    assert len(videos) == 46
    assert [v['lecture_number'] for v in manifest['lectures']] == list(range(46))
    assigned = [n for c in manifest['chapters'] for n in c['lecture_numbers']]
    assert assigned == list(range(46)), 'Missing, duplicated, or reordered source assignment'
    assert len({v['playlist_position'] for v in videos.values()}) == 46
    checks = []
    for path in sorted(ROOT.glob('*.html')):
        text = path.read_text(encoding='utf-8')
        soup = BeautifulSoup(text, 'html.parser')
        assert soup.html.get('lang') == 'en'
        assert soup.title and soup.select_one('#main') and soup.select_one('#chapter-content')
        ids = [e['id'] for e in soup.select('[id]')]
        assert len(ids) == len(set(ids)), f'Duplicate IDs: {path.name}'
        body = text.split('<!-- BOOK-CONTENT-START -->',1)[1].split('<!-- BOOK-CONTENT-END -->',1)[0]
        expected = soup.select_one('meta[name="book-content-sha256"]')['content']
        assert hashlib.sha256(body.encode()).hexdigest() == expected, path.name
        for e in soup.select('a[href],script[src],link[href],img[src]'):
            url = e.get('href', e.get('src',''))
            split = urlsplit(url)
            if split.scheme in ('https','http'):
                if split.netloc == 'www.youtube.com' and split.path == '/watch':
                    args = parse_qs(split.query)
                    vid = args['v'][0]
                    assert vid in videos, (path.name, vid)
                    if 't' in args:
                        value = args['t'][0].removesuffix('s')
                        assert value.isdigit() and 0 <= int(value) < videos[vid]['duration_seconds']
                continue
            if split.scheme or not url:
                continue
            target = (path.parent/unquote(split.path)).resolve() if split.path else path
            assert target.is_relative_to(ROOT), (path.name, 'path escape', url)
            assert target.exists(), (path.name, 'missing target', url)
            if split.fragment and target.suffix == '.html':
                doc = BeautifulSoup(target.read_text(encoding='utf-8'),'html.parser')
                assert doc.find(id=unquote(split.fragment)), (path.name,'missing anchor',url)
        for pre in soup.select('pre code.language-python'):
            compile(pre.get_text(), path.name, 'exec')
        assert not re.search(r'\[(?:PROOF NEEDED|CITATION NEEDED|AUTHOR DECISION NEEDED|NUMBER NOT YET COMPUTED)', body)
        assert not re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', text)
        checks.append({'file':path.name,'sha256':sha(path),'links_and_anchors':'passed','body_digest':'passed'})
    return checks


def browser_checks(only=None):
    from playwright.sync_api import sync_playwright
    paths = [ROOT/only] if only else sorted(ROOT.glob('*.html'))
    results = []
    temp = ROOT/'work/browser-tmp'
    temp.mkdir(parents=True, exist_ok=True)
    os.environ['TEMP'] = os.environ['TMP'] = str(temp)
    with sync_playwright() as p:
        chrome = Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
        executable = str(chrome) if chrome.exists() else p.chromium.executable_path
        browser = p.chromium.launch(headless=True, executable_path=executable)
        context = browser.new_context(viewport={'width':1440,'height':1000})
        page = context.new_page()
        page.set_default_timeout(8000)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        external = []
        def route(request):
            if request.request.url.startswith(('http://','https://')):
                external.append(request.request.url)
                request.abort()
            else:
                request.continue_()
        page.route('**/*', route)
        for path in paths:
            errors.clear()
            for width in (1440,390):
                page.set_viewport_size({'width':width,'height':1000})
                page.goto(path.as_uri(),wait_until='load')
                page.wait_for_function('window.MathJax && MathJax.startup && MathJax.startup.promise')
                page.evaluate('async()=>{await MathJax.startup.promise;}')
                assert page.locator('mjx-merror,[data-mml-node="merror"],[data-mjx-error]').count() == 0, path.name
                assert not errors, (path.name, errors)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+2'), (path.name,width,'overflow')
                assert page.locator('#theme-toggle').get_attribute('aria-pressed') == 'false'
                page.locator('#theme-toggle').click()
                assert page.locator('body').evaluate("e=>e.classList.contains('light')")
                page.locator('#theme-toggle').click()
                page.locator('#text-toggle').click()
                assert page.locator('body').evaluate("e=>e.classList.contains('large-text')")
                page.locator('#text-toggle').click()
                if page.locator('article details').count():
                    page.locator('#solutions-toggle').click()
                    assert page.locator('article details:not([open])').count() == 0
                    page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
                    assert page.locator('details:not([open])').count() == 0
                    page.evaluate("window.dispatchEvent(new Event('afterprint'))")
                if path.name.startswith('chapter-'):
                    assert page.locator('#chapter-toc a').count() >= 1
                    first = page.locator('#chapter-toc a').first
                    anchor = first.get_attribute('href')
                    if not first.is_visible():
                        page.locator('#chapter-toc summary').click()
                    first.click()
                    assert page.url.endswith(anchor)
                if path.name=='index.html':
                    page.locator('#lecture-search').fill('Jordan')
                    assert page.locator('[data-lecture]:visible').count() >= 1
                    page.locator('#lecture-search').fill('no_such_topic_123')
                    assert page.locator('[data-lecture]:visible').count() == 0
                    page.locator('#lecture-search').fill('')
                if path.name == 'numerical-lab.html':
                    page.locator('#block-sizes').fill('2,2')
                    page.locator('#explore-chains').click()
                    assert '2 blocks; dimension 4; largest block 2.' in page.locator('#chain-status').inner_text()
                    assert page.locator('#chain-table tbody tr').nth(1).inner_text().split() == ['1', '2', '2']
                    page.locator('#block-sizes').fill('0,99')
                    page.locator('#explore-chains').click()
                    assert page.locator('#chain-table table').count() == 0
                    page.locator('#block-sizes').fill('3,2,1')
                    page.locator('#explore-chains').click()
                    assert page.locator('#chain-diagram .chain-row').count() == 3
                results.append({'file':path.name,'width':width,'math_errors':0,'page_errors':0,'horizontal_overflow':False,'controls':'passed','sha256':sha(path)})
                if path.name=='index.html' and width==1440:
                    page.goto(path.as_uri(),wait_until='load')
                    page.evaluate('async()=>{await MathJax.startup.promise;}')
                    page.screenshot(path=str(ROOT/'assets/site-preview.png'))
            print(f'{path.name}: offline desktop/mobile passed',flush=True)
        assert not external, external
        browser.close()
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser',action='store_true')
    parser.add_argument('--pilot',help='Only browser-check this file; skip full static inventory.')
    args = parser.parse_args()
    result = {'static': [] if args.pilot else static_checks(),
              'browser': browser_checks(args.pilot) if args.browser else [],
              'scope':'offline source order, links, digests, rendering, and reading controls; not formal verification',
              'render_assets': {name: sha(ROOT/name) for name in [
                  'assets/book.css', 'assets/book.js', 'assets/lab.js',
                  'assets/math-config.js', 'assets/mathjax-tex-svg.js']}} 
    dest = 'pilot-reader.json' if args.pilot else 'reader-checks.json'
    (ROOT/'validation'/dest).write_text(json.dumps(result, indent=2)+'\n',encoding='utf-8')
    print('Validation passed.')


if __name__ == '__main__':
    main()
