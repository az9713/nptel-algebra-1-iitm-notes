#!/usr/bin/env python3
"""check_prose.py FILE.html  — flag a small set of high-signal awkward constructions.

This is NOT a grammar/style linter: most awkward or non-native phrasing is NOT
regex-detectable and still needs the read-aloud audit in
references/pedagogy-checklist.md ("Sentence-level prose craft"). This catches only
the mechanical, near-zero-false-positive patterns that have actually shipped —
a cheap backstop, advisory (never fails the build), like check_frame.

Strips <svg>/<script>/<style>/<pre>/<code> so it audits prose, not markup, then
tests the visible text of each <p>/<li>/<figcaption>/<td>/box <div>.
Prints file:line + the offending snippet. Extend SUSPECT with new patterns as
real ones are found (keep them low-false-positive).
"""
import re, sys, html, bisect

# (label, compiled pattern). Keep every pattern low-false-positive: it must flag
# a genuine defect essentially every time it matches, or it trains people to ignore it.
SUSPECT = [
    ("tautological copula 'X is X'",
     re.compile(r"\b(\w{3,})\b\s+(?:is|are|was|were)\s+\1\b", re.I)),
    ("invented idiom 'VERB VERB-ing happen/occur'",
     re.compile(r"\b(?:worth|watch|see|hear|feel|enjoy)\s+\w+ing\s+(?:happen|occur|going)\b", re.I)),
    ("doubled function word (typo)",
     re.compile(r"\b(the|a|an|is|are|of|to|and|in|on|that|with|for)\s+\1\b", re.I)),
    ("'the/a <noun> of which' stiff relative — consider recasting",
     re.compile(r"\b(?:the|a|an)\s+\w+\s+of\s+which\b", re.I)),
    ("'allows to/allow to' (missing object)",
     re.compile(r"\ballows?\s+to\s+\w+", re.I)),
    ("'more <adj>er' / 'most <adj>est' double comparative",
     re.compile(r"\bmore\s+\w+er\b|\bmost\s+\w+est\b", re.I)),
]

BLOCK = re.compile(r"<(svg|script|style|pre|code)\b.*?</\1>", re.S | re.I)
ELEM  = re.compile(r"<(p|li|figcaption|td|div)\b[^>]*>(.*?)</\1>", re.S | re.I)
TAG   = re.compile(r"<[^>]+>")

def main(path):
    src = open(path, encoding="utf-8").read()
    starts = [0]
    for ln in src.split("\n"):
        starts.append(starts[-1] + len(ln) + 1)
    lineno = lambda pos: bisect.bisect_right(starts, pos)
    masked = BLOCK.sub(lambda m: " " * len(m.group(0)), src)

    hits = []
    for m in ELEM.finditer(masked):
        raw = m.group(2)
        text = html.unescape(TAG.sub("", raw))
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        base = m.start(2)
        for label, pat in SUSPECT:
            for mm in pat.finditer(text):
                # locate the hit back in the source for a line number (best-effort)
                frag = mm.group(0)
                pos = masked.find(raw.strip()[:40], base) if raw.strip() else base
                hits.append((lineno(m.start()), label, frag,
                             text[max(0, mm.start()-25):mm.end()+25]))

    # de-dupe (same line + fragment)
    seen, out = set(), []
    for ln, label, frag, ctx in hits:
        k = (ln, frag.lower())
        if k in seen:
            continue
        seen.add(k); out.append((ln, label, frag, ctx))

    print(f"[check_prose] {path}: {len(out)} advisory prose flag(s)")
    for ln, label, frag, ctx in sorted(out):
        print(f"  L{ln}: {label}\n        …{ctx}…")
    print("  (advisory — verify each; then read every paragraph aloud, generator-script prose included)")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
