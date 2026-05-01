#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

HEADER_RE = re.compile(r"^\s*--\s*This file was protected using Luraph.*$", re.I | re.M)

TRACE_INJECT_POINT = "local T=P[H];"
TRACE_SNIPPET = (
    "local T=P[H]; "
    "if __LURAPH_TRACE then __LURAPH_TRACE(H, T, d, S) end;"
)


def make_traceable(input_code: str) -> str:
    code = HEADER_RE.sub("", input_code)
    if TRACE_INJECT_POINT not in code:
        raise ValueError("Cannot locate VM dispatch point `local T=P[H];` for this sample")
    code = code.replace(TRACE_INJECT_POINT, TRACE_SNIPPET, 1)

    prelude = r'''
local __trace_file = "trace.jsonl"
local __trace_fh = io.open(__trace_file, "w")
local function __safe(v)
    local t = type(v)
    if t == "number" or t == "boolean" or t == "string" or t == "nil" then
        return v
    end
    return "<" .. t .. ">"
end
function __LURAPH_TRACE(pc, op, regs, upvals)
    if not __trace_fh then return end
    local row = {pc=pc, op=op, r0=__safe(regs and regs[0]), r1=__safe(regs and regs[1]), r2=__safe(regs and regs[2])}
    local line = string.format('{"pc":%s,"op":%s,"r0":%q,"r1":%q,"r2":%q}\n', tostring(row.pc), tostring(row.op), tostring(row.r0), tostring(row.r1), tostring(row.r2))
    __trace_fh:write(line)
end
'''
    postlude = "\nif __trace_fh then __trace_fh:close() end\n"
    return prelude + "\n" + code + postlude


def summarize_trace(path: Path) -> dict:
    op_count = {}
    pcs = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.search(r'"pc":([^,]+),"op":([^,]+),', line)
        if not m:
            continue
        pc, op = m.group(1), m.group(2)
        pcs.add(pc)
        op_count[op] = op_count.get(op, 0) + 1
    return {"unique_pc": len(pcs), "op_hist": dict(sorted(op_count.items(), key=lambda kv: kv[1], reverse=True))}


def cmd_trace_prepare(args):
    src = Path(args.input).read_text(encoding="utf-8", errors="ignore")
    out = make_traceable(src)
    Path(args.output).write_text(out, encoding="utf-8")
    print(f"[+] wrote traceable script: {args.output}")
    print("[i] run it in Lua/Luau runtime to produce trace.jsonl")


def cmd_trace_summarize(args):
    data = summarize_trace(Path(args.trace))
    Path(args.output).write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[+] wrote: {args.output}")


def main():
    ap = argparse.ArgumentParser(description="Luraph devirtualization pipeline (trace-first)")
    sub = ap.add_subparsers(required=True)

    p1 = sub.add_parser("prepare-trace")
    p1.add_argument("input")
    p1.add_argument("-o", "--output", default="traceable_main.luau")
    p1.set_defaults(func=cmd_trace_prepare)

    p2 = sub.add_parser("summarize-trace")
    p2.add_argument("trace")
    p2.add_argument("-o", "--output", default="trace_summary.json")
    p2.set_defaults(func=cmd_trace_summarize)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
