#!/usr/bin/env python3
"""Best-effort Luraph source deobfuscator -> real Luau code output.

This script rewrites obfuscated Luau into a more readable Luau file by:
- normalizing hex/binary numeric literals (including underscore-heavy forms)
- decoding Lua escape sequences inside quoted strings
- applying lightweight formatting (statement separators / indentation)

Usage:
  python3 deobfuscate_luraph.py main.luau -o deobfuscated.luau
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path

NUM_RE = re.compile(r"(?<![\w.])([+-]?)(0[xX][0-9A-Fa-f_]+|0[bB][01_]+)(?![\w.])")
STR_RE = re.compile(r'"([^"\\]|\\.)*"')
HEADER_RE = re.compile(r"^\s*--\s*This file was protected using Luraph.*$", re.IGNORECASE | re.MULTILINE)


def normalize_number_token(tok: str) -> str:
    sign = ""
    if tok[:1] in "+-":
        sign, tok = tok[0], tok[1:]
    body = tok.replace("_", "")
    if body.lower().startswith("0x"):
        n = int(body, 16)
    elif body.lower().startswith("0b"):
        n = int(body, 2)
    else:
        return sign + tok
    return f"{sign}{n}"


def normalize_numbers(src: str) -> str:
    return NUM_RE.sub(lambda m: normalize_number_token((m.group(1) or "") + m.group(2)), src)


def decode_lua_string_literal(s: str) -> str:
    # decode standard escapes safely via python parser when possible
    try:
        decoded = ast.literal_eval(s)
        if isinstance(decoded, str):
            return decoded
    except Exception:
        pass
    return s[1:-1]


def reencode_lua_string(s: str) -> str:
    s = s.replace('\\', '\\\\').replace('"', '\\"')
    s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return f'"{s}"'


def normalize_strings(src: str) -> str:
    def _sub(m: re.Match[str]) -> str:
        lit = m.group(0)
        return reencode_lua_string(decode_lua_string_literal(lit))

    return STR_RE.sub(_sub, src)


def lightweight_format(src: str) -> str:
    src = src.replace(";", ";\n")
    src = re.sub(r"\belse\b", "\nelse\n", src)
    src = re.sub(r"\bend\b", "\nend\n", src)
    src = re.sub(r"\n{3,}", "\n\n", src)

    lines = []
    indent = 0
    for raw in src.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("end") or line.startswith("else") or line.startswith("until"):
            indent = max(0, indent - 1)
        lines.append(("    " * indent) + line)
        if re.search(r"\b(function|then|do|repeat)\b", line) and not line.startswith("end"):
            indent += 1
        if line.startswith("else"):
            indent += 1
    return "\n".join(lines) + "\n"


def deobfuscate(src: str) -> str:
    src = HEADER_RE.sub("", src)
    src = normalize_numbers(src)
    src = normalize_strings(src)
    src = lightweight_format(src)
    banner = "-- deobfuscated (best-effort readable Luau)\n"
    return banner + src


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=Path("deobfuscated.luau"))
    args = ap.parse_args()

    source = args.input.read_text(encoding="utf-8", errors="ignore")
    out = deobfuscate(source)
    args.output.write_text(out, encoding="utf-8")

    print(f"[+] wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
