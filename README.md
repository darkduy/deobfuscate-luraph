# Luraph Devirtualization (trace-first)

OK bro, bắt đầu pipeline **full devirtualization** theo hướng chuẩn: trace VM trước rồi lift opcode.

## 1) Tạo script traceable
```bash
python3 deobfuscate_luraph.py prepare-trace main.luau -o traceable_main.luau
```
Script này inject hook tại dispatch `local T=P[H];` để log `(pc, opcode, register snapshot)`.

## 2) Chạy `traceable_main.luau` trong runtime Lua/Luau
Nó sẽ tạo `trace.jsonl`.

## 3) Tóm tắt trace
```bash
python3 deobfuscate_luraph.py summarize-trace trace.jsonl -o trace_summary.json
```

## Trạng thái
- Đây là bước nền bắt buộc cho full devirtualization VM Luraph.
- Sau khi có trace, bước tiếp theo là map opcode semantics -> lift ra Luau AST.
