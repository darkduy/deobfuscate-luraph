#!/usr/bin/env python3
"""Deobfuscate Luraph script to a single Luau output file.

Goal requested by user: produce ONE .luau file as output.
This script performs best-effort static deobfuscation:
- strips Luraph header comments
- extracts and decodes long embedded payload strings (base85-like blocks)
- extracts printable strings from decoded bytes
- writes one luau file containing recovered artifacts + runnable stub

Usage:
  python3 deobfuscate_luraph.py input.luau -o deobfuscated.luau
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

HEADER_RE = re.compile(r"^\s*--\s*This file was protected using Luraph.*$", re.IGNORECASE | re.MULTILINE)
LONG_STR_RE = re.compile(r'"([^"\\]|\\.){120,}"', re.DOTALL)


def decode_base85_like(block: str) -> bytes:
    out = bytearray()
    usable = len(block) - (len(block) % 5)
    for i in range(0, usable, 5):
        val = 0
        chunk = block[i : i + 5]
        for ch in chunk:
            val = val * 85 + (ord(ch) - 33)
        out.extend(((val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF))
    return bytes(out)


def printable_strings(data: bytes, min_len: int = 4) -> list[str]:
    out: list[str] = []
    cur: list[str] = []
    for b in data:
        if 32 <= b <= 126:
            cur.append(chr(b))
        else:
            if len(cur) >= min_len:
                out.append("".join(cur))
            cur.clear()
    if len(cur) >= min_len:
        out.append("".join(cur))
    return out


def recover_payload(text: str) -> str:
    cands = [m.group(0)[1:-1] for m in LONG_STR_RE.finditer(text)]
    if not cands:
        return ""
    return max(cands, key=len)


def build_output_luau(original: str, payload: str, decoded: bytes, strings: list[str]) -> str:
    clean = HEADER_RE.sub("", original).strip()
    safe_preview = "\n".join(f"-- {s}" for s in strings[:120])
    hex_blob = decoded.hex()

    return f"""-- Decompiled/Recovered from Luraph (best-effort)
-- NOTE: This is NOT guaranteed full semantic deobfuscation.
-- It is a single Luau file output as requested.

-- Recovered printable strings preview:
{safe_preview if safe_preview else '-- (none)'}

local recovered = {{}}
recovered.payload_len = {len(payload)}
recovered.decoded_len = {len(decoded)}
recovered.decoded_hex = [[{hex_blob}]]

-- Original script body (header removed):
local original_source = [==[
{clean}
]==]

-- You can now continue manual reversing from `original_source`
-- and `recovered.decoded_hex`.

return {{
    original_source = original_source,
    recovered = recovered,
}}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Luraph -> single Luau output (best-effort)")
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=Path("deobfuscated.luau"))
    args = ap.parse_args()

    text = args.input.read_text(encoding="utf-8", errors="ignore")
    payload = recover_payload(text)
    decoded = decode_base85_like(payload) if payload else b""
    strings = printable_strings(decoded)

    out = build_output_luau(text, payload, decoded, strings)
    args.output.write_text(out, encoding="utf-8")

    print(f"[+] Wrote: {args.output}")
    print(f"[+] payload_len={len(payload)} decoded_len={len(decoded)} strings={len(strings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
