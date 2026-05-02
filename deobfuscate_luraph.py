#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from collections import defaultdict, Counter

HEADER_RE = re.compile(r"^\s*--\s*This file was protected using Luraph.*$", re.I | re.M)
TRACE_INJECT_POINT = "local T=P[H];"
TRACE_SNIPPET = "local T=P[H]; if __LURAPH_TRACE then __LURAPH_TRACE(H, T, d, S) end;"


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
    if t == "number" or t == "boolean" or t == "string" or t == "nil" then return v end
    return "<" .. t .. ">"
end
function __LURAPH_TRACE(pc, op, regs, upvals)
    if not __trace_fh then return end
    local r0 = __safe(regs and regs[0]); local r1 = __safe(regs and regs[1]); local r2 = __safe(regs and regs[2]);
    local line = string.format('{"pc":%s,"op":%s,"r0":%q,"r1":%q,"r2":%q}\n', tostring(pc), tostring(op), tostring(r0), tostring(r1), tostring(r2))
    __trace_fh:write(line)
    __trace_fh:flush()
end
'''
    return prelude + "\n" + code + "\n"


def parse_trace_line(line: str):
    m = re.search(r'"pc":([^,]+),"op":([^,]+),"r0":"(.*?)","r1":"(.*?)","r2":"(.*?)"', line)
    if not m:
        return None
    return {"pc": m.group(1), "op": m.group(2), "r0": m.group(3), "r1": m.group(4), "r2": m.group(5)}


def load_trace(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        row = parse_trace_line(line)
        if row:
            rows.append(row)
    return rows


def summarize_trace(rows):
    op_count = Counter(r["op"] for r in rows)
    pcs = {r["pc"] for r in rows}
    return {"events": len(rows), "unique_pc": len(pcs), "op_hist": dict(op_count.most_common())}


def infer_opcode_behaviors(rows):
    by_op = defaultdict(list)
    for i in range(len(rows)-1):
        cur, nxt = rows[i], rows[i+1]
        by_op[cur["op"]].append((cur, nxt))

    behaviors = {}
    for op, pairs in by_op.items():
        jumps = 0
        falls = 0
        reg_writes = 0
        for cur, nxt in pairs[:5000]:
            try:
                pc_cur = int(float(cur["pc"]))
                pc_nxt = int(float(nxt["pc"]))
                if pc_nxt != pc_cur + 1:
                    jumps += 1
                else:
                    falls += 1
            except Exception:
                pass
            if cur["r0"] != nxt["r0"] or cur["r1"] != nxt["r1"] or cur["r2"] != nxt["r2"]:
                reg_writes += 1
        total = max(1, len(pairs))
        behaviors[op] = {
            "samples": len(pairs),
            "jump_ratio": jumps / total,
            "fallthrough_ratio": falls / total,
            "reg_change_ratio": reg_writes / total,
            "guess": "JUMP_OR_BRANCH" if jumps / total > 0.35 else ("ALU_OR_LOAD" if reg_writes / total > 0.45 else "CALL_OR_MISC"),
        }
    return behaviors


def emit_lifter_template(behaviors: dict, output: Path):
    lines = ["-- Auto-generated Luraph VM lifter template from trace", "local handlers = {}", ""]
    for op, info in sorted(behaviors.items(), key=lambda kv: float(kv[0])):
        lines.append(f"-- op={op} samples={info['samples']} jump_ratio={info['jump_ratio']:.2f} reg_change={info['reg_change_ratio']:.2f} guess={info['guess']}")
        lines.append(f"handlers[{op}] = function(state)")
        lines.append("    -- TODO: implement semantic lift for this opcode")
        lines.append("end\n")
    lines.append("return handlers")
    output.write_text("\n".join(lines), encoding="utf-8")


def lift_trace_to_luau(rows, behaviors):
    """Generate devirtualized linear Luau-like code from runtime trace.

    This is concrete-trace lifting: produces readable control-flow skeleton and
    opcode-level operations with observed register snapshots.
    """
    lines = [
        "-- devirtualized from runtime trace (concrete execution)",
        "local function devirtualized()",
    ]

    seen_labels = set()
    for i, cur in enumerate(rows):
        pc = cur["pc"]
        op = cur["op"]
        guess = behaviors.get(op, {}).get("guess", "UNKNOWN")

        label = f"L_{re.sub(r'[^0-9A-Za-z_]', '_', pc)}"
        if label not in seen_labels:
            lines.append(f"::{label}::")
            seen_labels.add(label)

        lines.append(f"    -- op {op} ({guess})")
        lines.append(f"    -- r0={cur['r0']!r}, r1={cur['r1']!r}, r2={cur['r2']!r}")

        if i + 1 < len(rows):
            nxt = rows[i+1]
            try:
                pc_cur = int(float(pc))
                pc_nxt = int(float(nxt["pc"]))
                if pc_nxt != pc_cur + 1:
                    lines.append(f"    goto L_{re.sub(r'[^0-9A-Za-z_]', '_', nxt['pc'])}")
            except Exception:
                pass

        lines.append("")

    lines.append("end")
    lines.append("return devirtualized")
    return "\n".join(lines) + "\n"


def cmd_prepare_trace(args):
    src = Path(args.input).read_text(encoding="utf-8", errors="ignore")
    Path(args.output).write_text(make_traceable(src), encoding="utf-8")
    print(f"[+] wrote traceable script: {args.output}")


def cmd_summarize_trace(args):
    rows = load_trace(Path(args.trace))
    Path(args.output).write_text(json.dumps(summarize_trace(rows), indent=2), encoding="utf-8")
    print(f"[+] wrote: {args.output}")


def cmd_infer_opcodes(args):
    rows = load_trace(Path(args.trace))
    inferred = infer_opcode_behaviors(rows)
    Path(args.output).write_text(json.dumps(inferred, indent=2), encoding="utf-8")
    print(f"[+] wrote: {args.output}")


def cmd_emit_lifter(args):
    inferred = json.loads(Path(args.inferred).read_text(encoding="utf-8"))
    emit_lifter_template(inferred, Path(args.output))
    print(f"[+] wrote: {args.output}")


def cmd_lift_trace(args):
    rows = load_trace(Path(args.trace))
    if args.inferred and Path(args.inferred).exists():
        behaviors = json.loads(Path(args.inferred).read_text(encoding="utf-8"))
    else:
        behaviors = infer_opcode_behaviors(rows)
    out = lift_trace_to_luau(rows, behaviors)
    Path(args.output).write_text(out, encoding="utf-8")
    print(f"[+] wrote: {args.output}")


def main():
    ap = argparse.ArgumentParser(description="Luraph full devirtualization helper")
    sub = ap.add_subparsers(required=True)

    p1 = sub.add_parser("prepare-trace")
    p1.add_argument("input")
    p1.add_argument("-o", "--output", default="traceable_main.luau")
    p1.set_defaults(func=cmd_prepare_trace)

    p2 = sub.add_parser("summarize-trace")
    p2.add_argument("trace")
    p2.add_argument("-o", "--output", default="trace_summary.json")
    p2.set_defaults(func=cmd_summarize_trace)

    p3 = sub.add_parser("infer-opcodes")
    p3.add_argument("trace")
    p3.add_argument("-o", "--output", default="opcode_inferred.json")
    p3.set_defaults(func=cmd_infer_opcodes)

    p4 = sub.add_parser("emit-lifter")
    p4.add_argument("inferred")
    p4.add_argument("-o", "--output", default="lifter_template.luau")
    p4.set_defaults(func=cmd_emit_lifter)

    p5 = sub.add_parser("lift-trace")
    p5.add_argument("trace")
    p5.add_argument("-i", "--inferred", default="opcode_inferred.json")
    p5.add_argument("-o", "--output", default="devirtualized_from_trace.luau")
    p5.set_defaults(func=cmd_lift_trace)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
