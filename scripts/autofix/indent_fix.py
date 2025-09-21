#!/usr/bin/env python3
import sys, pathlib
if len(sys.argv) < 3:
    print("usage: indent_fix.py <file> <line>", file=sys.stderr); sys.exit(2)
p = pathlib.Path(sys.argv[1])
line_no = int(sys.argv[2])
lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
if not (1 <= line_no <= len(lines)): sys.exit(0)
def ind(s): return len(s) - len(s.lstrip(" "))
# fixa a indentação do bloco "pai" (a linha alvo vira múltiplo de 4)
idx = line_no - 1
# acha o "pai" com dois-pontos acima
parent = idx - 1
while parent >= 0:
    s = lines[parent].rstrip()
    if s.strip() and s.strip().endswith(":"):
        break
    parent -= 1
target = ind(lines[parent]) + 4 if parent >= 0 else 0
lines[idx] = (" " * target) + lines[idx].lstrip(" ")
p.write_text("\n".join(lines) + ("\n" if not lines[-1].endswith("\n") else ""), encoding="utf-8")
print(f"fixed {p} at line {line_no} -> indent {target}")
