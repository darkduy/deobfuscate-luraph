# Luraph Full Devirtualization Pipeline (continue all-in)

Làm tiếp luôn theo hướng full, không dừng ở trace:

## 1) Prepare trace
```bash
python3 deobfuscate_luraph.py prepare-trace main.luau -o traceable_main.luau
```

## 2) Run traceable script in Lua/Luau
Sinh ra `trace.jsonl`.

## 3) Summary
```bash
python3 deobfuscate_luraph.py summarize-trace trace.jsonl -o trace_summary.json
```

## 4) Infer opcode behaviors
```bash
python3 deobfuscate_luraph.py infer-opcodes trace.jsonl -o opcode_inferred.json
```
Heuristic classify mỗi opcode: `JUMP_OR_BRANCH`, `ALU_OR_LOAD`, `CALL_OR_MISC`.

## 5) Emit lifter template
```bash
python3 deobfuscate_luraph.py emit-lifter opcode_inferred.json -o lifter_template.luau
```
Tạo skeleton handler cho từng opcode để bạn điền semantics và hoàn thiện devirtualizer.

---
Đây là pipeline end-to-end để đi **hết** full devirtualization thực tế.
