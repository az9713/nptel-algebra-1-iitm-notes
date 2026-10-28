#!/usr/bin/env python3
"""check_code.py FILE.html  — every Python <pre><code> block must be clean PEP8.

WHY THIS EXISTS.  `<pre>` preserves whitespace verbatim, so blank lines *inside* a
code block render as visible gaps between statements — unlike the rest of the HTML,
where inter-tag newlines collapse and are invisible. A module authored with blank
lines between every source line therefore looks fine everywhere except in its code
listings, which come out triple-spaced and unreadable (this shipped in Module 8's
labs). Compact, PEP8-formatted code has no blank lines between related statements,
so this check both prevents the spacing bug and enforces PEP8.

WHAT IT CHECKS, per Python <pre><code> block (HTML entities un-escaped first):
  - PEP8 via pycodestyle if importable (full rule set, incl. E303 too-many-blank-
    lines — the spacing bug — and E501 line-too-long).
  - Fallback if pycodestyle is absent: any run of >=2 consecutive blank lines
    (the spacing bug) and any line > 79 characters.
Blocks that are not Python (no import / def / print( / '=' / 'np.') are skipped.

FAILS (exit 1) if any block has a violation. Author code compactly: one statement
per line, no blank lines between related statements (a single blank line to
separate logical groups is fine), lines <= 79 chars.
"""
import re
import sys
import html
import io
import contextlib

try:
    import pycodestyle
    HAVE_PYCODESTYLE = True
except Exception:
    HAVE_PYCODESTYLE = False


def looks_python(code):
    return bool(re.search(r"(^|\n)\s*(import |from |def |class |print\()", code)
                or ("=" in code and "np." in code))


if HAVE_PYCODESTYLE:
    class _Collect(pycodestyle.BaseReport):
        """A reporter that stores messages instead of printing (quiet swallows them)."""

        def __init__(self, options):
            super().__init__(options)
            self.collected = []

        def error(self, line_number, offset, text, check):
            code = super().error(line_number, offset, text, check)
            if code:
                self.collected.append(f"row {line_number}:{offset + 1}: {text}")
            return code


def pep8_issues(code):
    """Return pycodestyle issue lines for `code` (empty list if clean)."""
    if not code.endswith("\n"):
        code += "\n"
    opts = pycodestyle.StyleGuide(quiet=True).options
    report = _Collect(opts)
    chk = pycodestyle.Checker(lines=code.splitlines(True),
                              options=opts, report=report)
    chk.check_all()
    return report.collected


def fallback_issues(code):
    """No-dependency check: blank-line runs and over-long lines."""
    out = []
    lines = code.split("\n")
    run = 0
    for i, ln in enumerate(lines, 1):
        if ln.strip() == "":
            run += 1
            if run >= 2:
                out.append(f"row {i}: E303 too many blank lines (>=2); <pre> "
                           f"renders them as a visible gap")
        else:
            run = 0
        if len(ln) > 79:
            out.append(f"row {i}: E501 line too long ({len(ln)} > 79)")
    return out


def main(path):
    s = open(path, encoding="utf-8").read()
    blocks = re.findall(r"<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>", s, re.S)
    hard = 0
    checked = 0
    for i, raw in enumerate(blocks, 1):
        code = html.unescape(raw).replace("\r\n", "\n").replace("\r", "\n")
        if not looks_python(code):
            continue
        checked += 1
        issues = pep8_issues(code) if HAVE_PYCODESTYLE else fallback_issues(code)
        if issues:
            hard += len(issues)
            print(f"[check_code] {path}: block {i} -- {len(issues)} PEP8 issue(s):")
            for msg in issues[:12]:
                print("   ", msg)
    engine = "pycodestyle" if HAVE_PYCODESTYLE else "builtin fallback"
    print(f"[check_code] {path}: {checked} Python code block(s) checked "
          f"({engine}); {hard} issue(s).")
    if not HAVE_PYCODESTYLE:
        print("   (install pycodestyle for full PEP8 coverage: pip install pycodestyle)")
    return 1 if hard else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_code.py FILE.html")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
