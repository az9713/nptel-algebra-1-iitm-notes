#!/usr/bin/env python3
"""Check that internal anchor links resolve, and warn about unlinked section refs.

- Every  href="#id"  must point to an element with a matching  id="id".
- Reports (advisory) any bare  §N / §N.M / §§N-M  references that are NOT wrapped
  in a link (one of this skill's pillars is that section cross-refs are clickable;
  run autolink_sections.py to fix).

Usage:  python check_links.py FILE.html
Exits 1 only if there are BROKEN links; bare refs are a warning, not a failure.
"""
import re, sys


def main(path):
    s = open(path, encoding="utf-8").read()
    ids = set(re.findall(r'\sid="([^"]+)"', s))
    hrefs = re.findall(r'href="#([^"]+)"', s)
    broken = sorted({h for h in hrefs if h and h not in ids})

    stripped = re.sub(r'<a\b[^>]*>.*?</a>', '', s, flags=re.S)
    bare = re.findall(r'§§?\s*\d+(?:\.\d+)?(?:\s*[–,\-]\s*\d+(?:\.\d+)?)*', stripped)

    print(f"[check_links] {path}: {len(hrefs)} internal link(s), {len(broken)} broken; "
          f"{len(bare)} unlinked section ref(s)")
    if broken:
        print("  BROKEN targets (no matching id):", broken)
    if bare:
        print("  unlinked § refs (run autolink_sections.py):", bare[:20])
    return 1 if broken else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python check_links.py FILE.html"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
