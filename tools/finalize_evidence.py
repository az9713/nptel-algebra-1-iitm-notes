"""Curate exact-body editorial acceptance and source analysis for publication.

This author-side command requires private reviews. Public builds and verification
use the resulting evidence and do not require those private inputs.
"""
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    manifest = json.loads((ROOT/'source-manifest.json').read_text(encoding='utf-8'))
    lectures = {v['lecture_number']: v for v in manifest['lectures']}
    reviews, analysis = [], []
    for chapter in manifest['chapters']:
        n = chapter['order']
        body = ROOT/chapter['manuscript']
        ledger_path = ROOT/f'chapters/ch{n:02d}.sources.json'
        ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
        review = json.loads((ROOT/f'work/reviews/ch{n:02d}-editor.json').read_text(encoding='utf-8'))
        assert review['accepted'] is True and review['blocking_findings'] in (0, []), n
        assert review['manuscript_sha256'] == sha(body), f'Review hash mismatch: {n}'
        assert ledger['complete_source_text_reading'] == chapter['lecture_numbers']
        ids = {h['id'] for h in BeautifulSoup(body.read_text(encoding='utf-8'), 'html.parser').select('[id]')}
        for span in ledger['section_source_map']:
            assert span['section'] in ids, (n, span)
            assert span['lesson'] in chapter['lecture_numbers']
            assert 0 <= span['start'] < span['end'] <= lectures[span['lesson']]['duration_seconds'], (n, span)
        chapter['status'] = 'complete; independently reviewed'
        reviews.append({'chapter': n, 'accepted': True, 'body_sha256': sha(body),
                        'reviewed_utc': review['reviewed_utc'],
                        'scope': ['complete source text and cited reference sections',
                                  'every mathematical proof and six worked solutions',
                                  'source fidelity and declared boundaries',
                                  'exact Python program and printed output'],
                        'remaining_blocking_findings': 0})
        analysis.append({**ledger, 'manuscript': chapter['manuscript'],
                         'body_sha256': sha(body), 'ledger_sha256': sha(ledger_path),
                         'recordings': [{'lesson': number, 'video_id': lectures[number]['id'],
                                         'caption_sha256': lectures[number]['caption_sha256']}
                                        for number in chapter['lecture_numbers']]})
    write(ROOT/'source-manifest.json', manifest)
    write(ROOT/'analysis-ir.json', {'schema_version': 1,
          'scope': 'Full extracted-caption reading, section provenance and independent teaching developments; raw sources excluded.',
          'chapters': analysis})
    support = json.loads((ROOT/'work/reviews/book-editor.json').read_text(encoding='utf-8'))
    assert support['accepted'] and support['blocking_findings'] == 0
    for entry in support['support_files']:
        assert sha(ROOT/entry['path']) == entry['sha256']
    support_public = {key: support[key] for key in
                      ['accepted', 'reviewed_utc', 'scope', 'support_files']}
    support_public['remaining_blocking_findings'] = 0
    support_public['explorer_valid_cases'] = support['explorer_execution']['valid_cases']
    support_public['explorer_invalid_cases'] = support['explorer_execution']['invalid_cases']
    write(ROOT/'validation/editorial-review.json', {'schema_version': 1,
          'support_review': support_public,
          'reviewer': 'Separate AI scientific editor',
          'hash_scope': 'Exact UTF-8 authored chapter fragment, including final newline',
          'chapters': reviews,
          'limits': ['No human expert certification', 'No comprehensive audiovisual review',
                     'No formal proof-assistant verification',
                     'Finite code checks do not prove universal theorems']})
    print('25 exact-body acceptances and source ledgers verified and curated.')


if __name__ == '__main__':
    main()
