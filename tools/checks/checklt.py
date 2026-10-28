#!/usr/bin/env python3
"""Find literal < or > characters inside $...$ / $$...$$ math.

These are a silent killer in HTML: the browser's HTML parser sees e.g. `0<s<L`
and opens a phantom <s> (strikethrough) tag that swallows following content,
so the equation never renders and a whole region goes blank. The fix is to
write \\lt and \\gt instead (see escape_math_lt.py).

Usage:  python checklt.py FILE.html
Exits 1 if any are found, 0 otherwise.
"""
import sys


def main(path):
    s = open(path, encoding="utf-8").read()
    state = "text"; i = 0; line = 1; seg = ""; sl = 0; hits = []
    while i < len(s):
        ch = s[i]
        if ch == "\n":
            line += 1
        if s[i:i + 2] == "$$":
            if state == "text":
                state = "d"; seg = ""; sl = line
            elif state == "d":
                if "<" in seg or ">" in seg:
                    hits.append((sl, "display", seg))
                state = "text"
            i += 2; continue
        if ch == "$":
            if state == "text":
                state = "i"; seg = ""; sl = line
            elif state == "i":
                if "<" in seg or ">" in seg:
                    hits.append((sl, "inline", seg))
                state = "text"
            i += 1; continue
        if state in ("i", "d"):
            seg += ch
        i += 1
    print(f"[checklt] {path}: {len(hits)} math segment(s) with raw < or >")
    for ln, mode, body in hits:
        print(f"  line {ln} ({mode}): {body[:90]!r}")
    if hits:
        print("  fix: run escape_math_lt.py (replaces < > with \\lt \\gt inside math)")
    return 1 if hits else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python checklt.py FILE.html"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
