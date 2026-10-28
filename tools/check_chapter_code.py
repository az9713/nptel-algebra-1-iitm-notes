"""Execute each chapter's Python listings and compare declared output."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def main():
    results = []
    for path in sorted((ROOT/'chapters').glob('ch[0-9][0-9].html')):
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        listings = soup.select('code.language-python')
        code = '\n\n'.join(c.get_text() for c in listings)
        if not code:
            continue
        result = subprocess.run([sys.executable, '-X', 'utf8', '-c', code], cwd=ROOT,
                                text=True, capture_output=True, timeout=30)
        expected = '\n'.join(c.get_text().strip() for c in soup.select('pre.output'))
        assert result.returncode == 0, f'{path.name}: {result.stderr}'
        if expected:
            assert result.stdout.strip() == expected.strip(), (path.name, result.stdout, expected)
        results.append({'chapter': path.stem, 'listings': len(listings),
                        'manuscript_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'output': result.stdout, 'displayed_output_matched': bool(expected),
                        'exit_code': result.returncode})
        print(f'{path.stem}: {len(listings)} listings passed')
    (ROOT/'validation/chapter-code-checks.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
