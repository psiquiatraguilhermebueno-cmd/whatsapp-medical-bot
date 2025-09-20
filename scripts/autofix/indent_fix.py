#!/usr/bin/env python3
import sys, pathlib
if len(sys.argv) < 3:
    sys.exit(2)
p = pathlib.Path(sys.argv[1]); line_no = int(sys.argv[2])
txt = p.read_text(encoding="utf-8", errors="ignore").splitlines()
idx = max(0, min(len(txt)-1, line_no-1))
def indent(s): return len(s) - len(s.lstrip(" "))
ref = idx-1
while ref >= 0 and (txt[ref].strip()=="" or txt[ref].lstrip().startswith("#")):
    ref -= 1
if ref >= 0:
    ref_indent = indent(txt[ref])
    cur = txt[idx].lstrip(" ")
    txt[idx] = (" " * ref_indent) + cur
    p.write_text("\n".join(txt) + ("\n" if not txt[-1].endswith("\n") else ""), encoding="utf-8")
