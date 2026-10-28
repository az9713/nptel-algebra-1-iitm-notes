#!/usr/bin/env python3
"""Check MathJax delimiter balance in an HTML (or Markdown) file.

Scans the file as a state machine: $$ toggles display math, $ toggles inline.
Flags: $$ opened inside inline math, single $ inside display, EOF mid-math,
and per-segment {} / \\left-\\right / \\begin-\\end imbalance and stray \\boxed.
Also flags stray control chars (TAB/VT/FF/BS/BEL/CR) outside <pre> — the fingerprint
of $…$/backslash math text mangled by a double-quoted shell or a non-raw Python
string (\\text -> <TAB>ext), which leaves *valid* TeX that other checks miss.

Usage:  python checktex.py FILE.html
Exits 1 if any issue is found, 0 otherwise.
"""
import re, sys


# Stray control chars injected when $…$/backslash text is passed through a
# double-quoted shell or a non-raw Python string: \t→TAB, \v→VT, \f→FF, \b→BS,
# \a→BEL, \r→CR (e.g. \tau, \nu, \varepsilon, \boxed, \text losing its backslash).
# \n is a legitimate line break and is NOT flagged. <pre> code is exempt.
CTRL = {"\x07": r"\a (BEL, from \\a...)", "\x08": r"\b (BS, from \\boxed...)",
        "\x09": r"\t (TAB, from \\tau/\\text...)", "\x0b": r"\v (VT, from \\varepsilon...)",
        "\x0c": r"\f (FF, from \\frac...)", "\x0d": r"\r (CR, from \\rho...)"}


def _ctrl_issues(s):
    masked = re.sub(r"<pre\b.*?</pre>", lambda m: re.sub(r"[^\n]", " ", m.group()), s, flags=re.S)
    out = []
    line = 1
    for ch in masked:
        if ch == "\n":
            line += 1
        elif ch in CTRL:
            out.append(f"line {line}: stray control char {CTRL[ch]} -- likely shell/format "
                       f"mangling of a math macro (author with Write/Edit or a raw string)")
    return out


def main(path):
    s = open(path, encoding="utf-8").read()
    state = "text"  # text | inline | display
    i = 0; line = 1
    issues = []; segments = []; seg_start = None; buf = ""
    while i < len(s):
        ch = s[i]
        if ch == "\n":
            line += 1
        if s[i:i + 2] == "$$":
            if state == "text":
                state = "display"; seg_start = line; buf = ""
            elif state == "display":
                segments.append(("display", seg_start, buf)); state = "text"
            else:
                issues.append(f"line {line}: '$$' inside INLINE math (started line {seg_start})")
                state = "text"
            i += 2; continue
        if ch == "$":
            if state == "text":
                state = "inline"; seg_start = line; buf = ""
            elif state == "inline":
                segments.append(("inline", seg_start, buf)); state = "text"
            else:
                issues.append(f"line {line}: single '$' inside DISPLAY math (started line {seg_start})")
            i += 1; continue
        if state != "text":
            buf += ch
        i += 1
    if state != "text":
        issues.append(f"EOF: still open in {state} math (started line {seg_start})")

    for mode, ln, body in segments:
        if body.count("{") != body.count("}"):
            issues.append(f"line {ln} ({mode}): brace imbalance :: {body[:60]!r}")
        if len(re.findall(r"\\left(?![A-Za-z])", body)) != len(re.findall(r"\\right(?![A-Za-z])", body)):
            issues.append(f"line {ln} ({mode}): \\left/\\right imbalance :: {body[:60]!r}")
        if body.count(r"\begin") != body.count(r"\end"):
            issues.append(f"line {ln} ({mode}): \\begin/\\end imbalance :: {body[:60]!r}")
        for m in re.finditer(r"\\boxed(.?)", body):
            if m.group(1) != "{":
                issues.append(f"line {ln} ({mode}): \\boxed not followed by '{{' :: {body[:60]!r}")

    issues += _ctrl_issues(s)

    print(f"[checktex] {path}: {len(segments)} math segment(s), {len(issues)} issue(s)")
    for x in issues:
        print("  -", x)
    return 1 if issues else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python checktex.py FILE.html"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
