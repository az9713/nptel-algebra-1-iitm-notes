#!/usr/bin/env python3
"""Static SVG-label and figure checks for rigorous-explainer documents.

Catches classes of defect that recur across documents and that the prose rules
in references/*.md did not prevent on their own:

  HARD (exit 1):
    - malformed viewBox (not exactly 4 numeric values)   [the "0 0 0 0 W H" bug]
    - literal '_' or '^' inside <text> labels            [F_m, 10^3 — use a
      Unicode subscript/superscript or <tspan baseline-shift="sub"/"super">]

  ADVISORY (printed, does NOT fail the build):
    - ASCII math placeholders in <text> (theta, omega, Pi, sqrt, ...)
    - figures present but never referenced by "Fig. N" in prose
    - mixed <summary> disclosure labels ("Answer" vs "solution")
    - very heavy polylines (>120 points) / large file

Rationale and the rules behind these: references/figures-and-animation.md.

Usage:  python check_svg.py FILE.html
Exits 1 if any HARD issue is found, 0 otherwise (advisories never fail).
"""
import sys, re, os

# Windows consoles default to cp1252; labels contain ≈, θ, ×, etc.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Whole-word tokens that in an SVG label are almost always a mis-typed Greek
# letter or function name rather than English — advisory, because prose labels
# ("vertical", "precession") are legitimately English.
PLACEHOLDERS = {
    "theta", "omega", "phi", "lambda", "sigma", "tau", "alpha", "beta", "gamma",
    "delta", "epsilon", "rho", "psi", "kappa", "Pi", "Omega", "Sigma", "Delta",
    "Phi", "Psi", "Gamma", "Lambda", "Theta", "sqrt",
}


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def main(path):
    s = open(path, encoding="utf-8").read()
    hard, adv = [], []

    # --- viewBox arity: exactly 4 numeric values ---
    for m in re.finditer(r'viewBox\s*=\s*"([^"]*)"', s):
        vals = m.group(1).replace(",", " ").split()
        ok = len(vals) == 4 and all(re.fullmatch(r"-?\d+(\.\d+)?", v) for v in vals)
        if not ok:
            hard.append(f'malformed viewBox="{m.group(1)}" (need exactly 4 numbers)')

    # --- <text> label content: underscores, carets, ASCII placeholders ---
    for m in re.finditer(r"<text\b[^>]*>(.*?)</text>", s, re.S):
        inner = strip_tags(m.group(1))
        label = inner.strip()[:50]
        if "_" in inner:
            hard.append(f'literal "_" in label {label!r} '
                        '(use a Unicode subscript or <tspan baseline-shift="sub">)')
        if "^" in inner:
            hard.append(f'literal "^" in label {label!r} '
                        '(use a Unicode superscript or <tspan baseline-shift="super">)')
        bad = set(re.findall(r"[A-Za-z]+", inner)) & PLACEHOLDERS
        if bad:
            adv.append(f'possible ASCII math placeholder {sorted(bad)} in label {label!r}')

    # --- figures referenced by number? (figcaption "Fig. N" is CSS-generated, so
    #     any literal "Fig. N" in the source is a genuine prose reference) ---
    nfig = len(re.findall(r"<figcaption\b", s))
    nref = len(re.findall(r"Fig\.\s*\d+", s))
    if nfig >= 3 and nref == 0:
        adv.append(f'{nfig} figures but no "Fig. N" reference in prose (cite them by number)')

    # --- mixed <summary> disclosure labels ---
    sums = [strip_tags(x).strip().lower()
            for x in re.findall(r"<summary\b[^>]*>(.*?)</summary>", s, re.S)]
    if any("answer" in x for x in sums) and any("solution" in x for x in sums):
        adv.append('mixed disclosure labels: both "Answer" and "solution" in <summary> (unify)')

    # --- heavy polylines / large file ---
    heavy = 0
    for m in re.finditer(r'<polyline[^>]*points="([^"]*)"', s):
        ntok = len(m.group(1).replace(",", " ").split())
        if ntok / 2 > 120:
            heavy += 1
    if heavy:
        adv.append(f"{heavy} polyline(s) with >120 points (consider decimating to ~40-60)")
    kb = os.path.getsize(path) / 1024
    if kb > 400:
        adv.append(f"large file: {kb:.0f} KB")

    print(f"[check_svg] {path}: {len(hard)} hard issue(s), {len(adv)} advisory")
    for h in hard:
        print("  HARD: " + h)
    for a in adv:
        print("  adv : " + a)
    return 1 if hard else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python check_svg.py FILE.html"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
