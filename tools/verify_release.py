"""Verify the public edition using only its distributed inputs and evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    required = ['index.html', 'book-overview.html', 'source-map.html',
                'references.html', 'numerical-lab.html', 'analysis-ir.json',
                'validation/summary.json', 'validation/editorial-review.json',
                'validation/chapter-code-checks.json', 'validation/content-checks.json',
                'validation/reader-checks.json', '.nojekyll', 'README.md', 'LICENSE']
    for name in required:
        assert (ROOT/name).is_file(), f'Missing required release artifact: {name}'
    manifest = read('source-manifest.json')
    assert len(manifest['chapters']) == 25
    assert [v['lecture_number'] for v in manifest['lectures']] == list(range(46))
    assert len({v['id'] for v in manifest['lectures']}) == 46
    assert [n for c in manifest['chapters'] for n in c['lecture_numbers']] == list(range(46))
    editorial = read('validation/editorial-review.json')['chapters']
    analysis = read('analysis-ir.json')['chapters']
    stats = read('validation/content-statistics.json')
    assert len(editorial) == len(analysis) == len(stats) == 25
    for c, r, a, s in zip(manifest['chapters'], editorial, analysis, stats):
        n = c['order']
        assert n == r['chapter'] == a['chapter'] == s['chapter']
        body_hash = sha(ROOT/c['manuscript'])
        assert body_hash == r['body_sha256'] == a['body_sha256'] == s['body_sha256']
        assert r['accepted'] and r['remaining_blocking_findings'] == 0
        assert a['complete_source_text_reading'] == c['lecture_numbers']
        assert a['ledger_sha256'] == sha(ROOT/f'chapters/ch{n:02d}.sources.json')
        assert s['problems'] == 6 and s['python_listings'] == 1
        page = (ROOT/c['file']).read_text(encoding='utf-8')
        body = page.split('<!-- BOOK-CONTENT-START -->', 1)[1].split('<!-- BOOK-CONTENT-END -->', 1)[0]
        assert hashlib.sha256(body.encode()).hexdigest() == body_hash
    code = read('validation/chapter-code-checks.json')
    assert len(code) == 25
    for c, result in zip(manifest['chapters'], code):
        assert result['manuscript_sha256'] == sha(ROOT/c['manuscript'])
        assert result['exit_code'] == 0 and result['displayed_output_matched']
    checks = read('validation/content-checks.json')
    assert checks['passed'] and all(r['exit_code'] == 0 for r in checks['results'])
    for result in checks['results']:
        assert result['input_sha256'] == sha(ROOT/result['file'])
    reader = read('validation/reader-checks.json')
    assert len(reader['static']) == 30 and len(reader['browser']) == 60
    for result in reader['static'] + reader['browser']:
        assert result['sha256'] == sha(ROOT/result['file']), result['file']
    for name, expected in reader['render_assets'].items():
        assert sha(ROOT/name) == expected, name
    support = read('validation/editorial-review.json')['support_review']
    assert support['accepted'] and support['remaining_blocking_findings'] == 0
    for entry in support['support_files']:
        assert sha(ROOT/entry['path']) == entry['sha256']
    summary = read('validation/summary.json')
    assert summary['status'] == 'passed'
    assert summary['chapters'] == 25 and summary['recordings'] == 46
    print('Public release integrity passed: 25 chapters,46 recordings,150 solutions,60 browser views.')


if __name__ == '__main__':
    main()
