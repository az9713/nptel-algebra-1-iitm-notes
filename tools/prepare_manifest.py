"""Bind the exact playlist to the official NPTEL lesson order."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'work' / 'sources'

CHAPTERS = [
    ('Mathematical statements, sets, and logic', [0, 1, 2, 3]),
    ('Proofs, counterexamples, and set identities', [4, 5, 6]),
    ('Functions and the information they preserve', [7]),
    ('Equivalence, quotients, and canonical factorization', [8, 9, 10]),
    ('Binary operations and groups', [11, 12]),
    ('Rings, integral domains, and foundational assumptions', [13, 14]),
    ('Integers, order, and induction', [15, 16]),
    ('Inductive constructions and uniqueness of the integers', [17, 18]),
    ('Cardinality and the limits of enumeration', [19]),
    ('Division, greatest common divisors, and Euclid', [20]),
    ('Congruences and prime factorization', [21, 22]),
    ('Fields and the construction of rational numbers', [23]),
    ('Real numbers and completeness', [24]),
    ('Complex numbers and polynomial arithmetic', [25, 26]),
    ('Linear systems and Gaussian elimination', [27, 28]),
    ('Matrix algebra and square systems', [29, 30]),
    ('The geometry and parameters of a solution set', [31]),
    ('Vector spaces, subspaces, and direct sums', [32, 33]),
    ('Spanning, independence, bases, and dimension', [34, 35]),
    ('Linear maps and rank–nullity', [36, 37]),
    ('Matrix representations and change of basis', [38, 39]),
    ('Eigenvalues and invariant subspaces', [40]),
    ('Minimal polynomials and operator decomposition', [41, 42]),
    ('Triangular forms and invariant flags', [43]),
    ('Jordan chains and canonical forms', [44, 45]),
]


def main():
    playlist = json.loads((WORK/'playlist-original.json').read_text(encoding='utf-8-sig'))
    official = (ROOT/'work/references/course-1.html').read_text(encoding='utf-8')
    lessons = [{'lecture_number': int(m[0]), 'official_title': m[1], 'id': m[2]}
               for m in re.findall(r'\{id:(\d+),name:"([^"]+)",youtube_id:"([^"]+)"', official)]
    assert [v['lecture_number'] for v in lessons] == list(range(1, 46))
    lessons.insert(0, {'lecture_number': 0, 'official_title': 'Course introduction', 'id': 'h8NcKBOo91c'})
    positions = {e['id']: i+1 for i, e in enumerate(playlist['entries'])}
    assert set(positions) == {v['id'] for v in lessons}
    chapters = []
    for i, (title, numbers) in enumerate(CHAPTERS, 1):
        slug = re.sub('[^a-z0-9]+', '-', title.lower()).strip('-')
        chapters.append({'order': i, 'title': title, 'lecture_numbers': numbers,
                         'file': f'chapter-{i:02d}-{slug}.html',
                         'manuscript': f'chapters/ch{i:02d}.html', 'status': 'planned'})
    records = []
    for v in lessons:
        raw = json.loads((WORK/f"{v['id']}.source.json").read_text(encoding='utf-8'))
        chapter = next(c for c in chapters if v['lecture_number'] in c['lecture_numbers'])
        records.append({**v, 'playlist_position': positions[v['id']],
                        'url': f"https://www.youtube.com/watch?v={v['id']}",
                        'title': raw['title'], 'chapter_order': chapter['order'],
                        **{k: raw[k] for k in ['duration_seconds', 'upload_date', 'caption_language',
                             'caption_label', 'caption_kind', 'caption_sha256',
                             'caption_first_second', 'caption_last_second', 'retrieved_utc']},
                        'segment_count': len(raw['segments'])})
    manifest = {'course': 'Algebra 1: Foundations', 'instructor': 'Jaikrishnan J',
                'institution': 'IIT Palakkad', 'coordinating_institution': 'IIT Madras',
                'course_url': 'https://nptel.ac.in/courses/111106763',
                'playlist_url': playlist['webpage_url'],
                'order_basis': 'Official NPTEL courseOutline units and lessons; introduction prepended',
                'official_order_sha256': hashlib.sha256(official.encode()).hexdigest(),
                'lectures': records, 'chapters': chapters}
    (ROOT/'source-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f"Bound {len(records)} videos to {len(chapters)} chapters in official teaching order.")
    for v in records:
        end_gap = v['duration_seconds']-v['caption_last_second']
        if end_gap > 45 or end_gap < -3:
            print('INSPECT TIMING', v['lecture_number'], v['title'], v['duration_seconds'], v['caption_last_second'])


if __name__ == '__main__':
    main()
