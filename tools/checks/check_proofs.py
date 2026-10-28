#!/usr/bin/env python3
"""Flag an *asserted proposition*: a .prop / .thm / .lem block NOT immediately
followed by a .proof. This is the one mechanically-reliable slice of the
"uniform rigor across siblings" rule (pedagogy-checklist.md §4): a Proposition or
Theorem stated with no proof beside proved neighbours reads as "the author ran out
of steam." (Definitions use .def and need no proof, so they are ignored.)

It does NOT catch the subtler sibling case the Module 6 §6 gap was — a boxed
constitutive law left in a .keyresult with only an inline "…gives X" derivation while
its peer law got a full .prop+.proof. That distinction (is this boxed result a mere
substitution/definition, or a substantive result that deserves a proof?) is an
editorial judgement no syntactic checker can make. So this stays ADVISORY, and the
real safeguard is the rule now in SKILL.md Pillar 4 plus a per-section read-through:
list the section's boxed results and confirm peers of equal weight are proved alike.

Usage:  python check_proofs.py FILE.html      (advisory; prints findings, exits 0)
"""
import re, sys

OPEN = re.compile(r'<div class="(prop|thm|lem|theorem|proof|def|definition|keyresult)"')
LABEL = re.compile(r'<b>([^<.]*?(?:Proposition|Theorem|Lemma)[^<]*?)\.?</b>')


def main(path):
    s = open(path, encoding="utf-8").read()
    blocks = [(m.start(), m.group(1)) for m in OPEN.finditer(s)]
    asserted = []
    for i, (pos, kind) in enumerate(blocks):
        if kind not in ("prop", "thm", "lem", "theorem"):
            continue
        nxt = blocks[i + 1][1] if i + 1 < len(blocks) else None
        if nxt != "proof":
            end = blocks[i + 1][0] if i + 1 < len(blocks) else len(s)
            lab = LABEL.search(s, pos, end)
            name = lab.group(1).strip() if lab else f"{kind} block"
            line = s.count("\n", 0, pos) + 1
            asserted.append((line, name))
    print(f"[check_proofs] {path}: {len(asserted)} asserted proposition(s) (no adjacent .proof)")
    for line, name in asserted:
        print(f"  - line {line}: \"{name}\" has no .proof — prove it, or demote to .def/.keyresult")
    if not asserted:
        print("  every proposition/theorem/lemma is proved. "
              "(Still eyeball boxed .keyresult siblings — an unproved sibling law is a judgement call this can't see.)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python check_proofs.py FILE.html"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
