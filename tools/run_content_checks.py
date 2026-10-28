"""Run the inherited HTML content checks and retain actual exit statuses."""
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECKS = ['checktex', 'checklt', 'check_links', 'check_code',
          'check_proofs', 'check_prose', 'check_svg']


def check(task):
    path, name = task
    result = subprocess.run(
        [sys.executable, '-X', 'utf8', str(ROOT/'tools/checks'/f'{name}.py'), str(path)],
        cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=45)
    return {'file': str(path.relative_to(ROOT)).replace('\\', '/'),
            'checker': name, 'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'exit_code': result.returncode,
            'stdout': result.stdout.replace(str(ROOT), '.'),
            'stderr': result.stderr.replace(str(ROOT), '.')}


if __name__ == '__main__':
    paths = sorted((ROOT/'chapters').glob('*.html'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(check, [(p, c) for p in paths for c in CHECKS]))
    report = {'scope': 'Syntax and selected advisory prose/proof patterns; independent editorial review is separate.',
              'results': results, 'passed': all(r['exit_code'] == 0 for r in results)}
    (ROOT/'validation/content-checks.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    failures = [r for r in results if r['exit_code']]
    print(f'{len(results)} checker invocations; {len(failures)} failed.')
    for result in failures:
        print(result)
    for result in results:
        if result['checker'] in ('check_prose', 'check_proofs', 'check_links'):
            lines = result['stdout'].splitlines()
            if len(lines) > (2 if result['checker'] != 'check_links' else 1):
                print(result['file'], result['stdout'])
    raise SystemExit(bool(failures))
