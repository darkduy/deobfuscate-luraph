#!/usr/bin/env python3
"""Simple Luraph deobfuscation helper.

This tool does not fully emulate Lua VM, but it automates the first steps:
1) Detect Luraph-protected files.
2) Extract the encoded payload after `]=]`.
3) Decode common Luraph base-36 chunks into bytes when possible.
4) Dump readable strings and save decoded blobs for further reversing.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

HEADER_RE = re.compile(r"Luraph Obfuscator", re.IGNORECASE)
PAYLOAD_RE = re.compile(r"\]=\]\s*;", re.MULTILINE)
CHUNK_RE = re.compile(r"[!-z]{5}")


def is_luraph(text: str) -> bool:
    return bool(HEADER_RE.search(text))


def extract_payload(text: str) -> str:
    """Get the big encoded section that Luraph injects near the tail."""
    # Heuristic: the largest quote-heavy region before the `]=];if ...` gate.
    pivot = text.find("]=];if")
    if pivot == -1:
        pivot = len(text)
    head = text[:pivot]
    # Find the last long quoted segment.
    matches = list(re.finditer(r'"([^"\\]|\\.){100,}"', head, re.DOTALL))
    if not matches:
        return ""
    raw = matches[-1].group(0)
    return raw[1:-1]


def decode_base36_block(block: str) -> bytes:
    """Decode 5-char base-85-like groups used in many Luraph generations."""
    out = bytearray()
    for i in range(0, len(block) - len(block) % 5, 5):
        chunk = block[i : i + 5]
        val = 0
        for ch in chunk:
            val = val * 85 + (ord(ch) - 33)
        out.extend([(val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF])
    return bytes(out)


def printable_ratio(data: bytes) -> float:
    if not data:
        return 0.0
    printable = sum(1 for b in data if 32 <= b <= 126 or b in (9, 10, 13))
    return printable / len(data)


def dump_strings(data: bytes, min_len: int = 4) -> list[str]:
    s = []
    cur = []
    for b in data:
        if 32 <= b <= 126:
            cur.append(chr(b))
        else:
            if len(cur) >= min_len:
                s.append("".join(cur))
            cur = []
    if len(cur) >= min_len:
        s.append("".join(cur))
    return s


def main() -> int:
    ap = argparse.ArgumentParser(description="Luraph deobfuscation bootstrap tool")
    ap.add_argument("input", type=Path, help="Path to obfuscated .lua/.luau file")
    ap.add_argument("-o", "--out", type=Path, default=Path("out"), help="Output directory")
    args = ap.parse_args()

    text = args.input.read_text(encoding="utf-8", errors="ignore")
    if not is_luraph(text):
        print("[!] Input does not look like a Luraph-protected file.")
        return 1

    payload = extract_payload(text)
    if not payload:
        print("[!] Could not extract encoded payload automatically.")
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    payload_path = args.out / "payload.txt"
    payload_path.write_text(payload, encoding="utf-8")

    decoded = decode_base36_block(payload)
    decoded_path = args.out / "decoded.bin"
    decoded_path.write_bytes(decoded)

    ratio = printable_ratio(decoded)
    strings = dump_strings(decoded)
    strings_path = args.out / "strings.txt"
    strings_path.write_text("\n".join(strings), encoding="utf-8")

    print("[+] Luraph signature detected")
    print(f"[+] Payload length: {len(payload):,} chars -> {payload_path}")
    print(f"[+] Decoded length: {len(decoded):,} bytes -> {decoded_path}")
    print(f"[+] Printable ratio: {ratio:.2%}")
    print(f"[+] Extracted strings: {len(strings):,} -> {strings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
