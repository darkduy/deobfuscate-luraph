# Luraph Full Devirtualization Pipeline (Python)

OK làm full theo pipeline liền mạch:

## 1) Prepare trace
```bash
python3 deobfuscate_luraph.py prepare-trace main.luau -o traceable_main.luau
```

## 2) Run `traceable_main.luau` trong Lua/Luau runtime
Sinh ra `trace.jsonl`.

## 3) Summarize trace
```bash
python3 deobfuscate_luraph.py summarize-trace trace.jsonl -o trace_summary.json
```

## 4) Infer opcode behaviors
```bash
python3 deobfuscate_luraph.py infer-opcodes trace.jsonl -o opcode_inferred.json
```

## 5) Emit handler template
```bash
python3 deobfuscate_luraph.py emit-lifter opcode_inferred.json -o lifter_template.luau
```

## 6) Lift trace -> devirtualized Luau
```bash
python3 deobfuscate_luraph.py lift-trace trace.jsonl -i opcode_inferred.json -o devirtualized_from_trace.luau
```
Bước này tạo code Luau devirtualized từ execution trace (concrete execution) với:
- label theo PC
- annotation opcode/guess
- goto theo nhánh runtime thực tế

## Lưu ý quan trọng
- `devirtualized_from_trace.luau` là kết quả lift theo **trace đã chạy** (path-sensitive), không tự động cover mọi path chưa execute.
- Để gần “full” hơn, cần thu nhiều trace với input/path khác nhau rồi merge.
