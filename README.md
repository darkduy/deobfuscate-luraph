# Luraph Devirtualization Pipeline (Python)

Repo này cung cấp tool `deobfuscate_luraph.py` để đi theo pipeline devirtualization VM Luraph.

## Yêu cầu
- Python 3.9+
- File đầu vào: script Luraph (ví dụ `main.luau`)

## Cách dùng nhanh

### Bước 1: Tạo file traceable
```bash
python3 deobfuscate_luraph.py prepare-trace main.luau -o traceable_main.luau
```
Lệnh này inject hook trace vào điểm dispatch VM (`local T=P[H];`).

### Bước 2: Chạy file traceable bằng Lua/Luau runtime
Sau khi chạy `traceable_main.luau`, bạn sẽ có file `trace.jsonl`.

### Bước 3: Tóm tắt trace
```bash
python3 deobfuscate_luraph.py summarize-trace trace.jsonl -o trace_summary.json
```
Output:
- `events`
- `unique_pc`
- `op_hist`

### Bước 4: Suy luận hành vi opcode
```bash
python3 deobfuscate_luraph.py infer-opcodes trace.jsonl -o opcode_inferred.json
```
Mỗi opcode có các chỉ số:
- `jump_ratio`
- `fallthrough_ratio`
- `reg_change_ratio`
- `guess`: `JUMP_OR_BRANCH` / `ALU_OR_LOAD` / `CALL_OR_MISC`

### Bước 5: Sinh lifter template
```bash
python3 deobfuscate_luraph.py emit-lifter opcode_inferred.json -o lifter_template.luau
```
File `lifter_template.luau` chứa handler stub cho từng opcode để bạn điền semantics.

---

## CLI help
```bash
python3 deobfuscate_luraph.py --help
python3 deobfuscate_luraph.py prepare-trace --help
python3 deobfuscate_luraph.py summarize-trace --help
python3 deobfuscate_luraph.py infer-opcodes --help
python3 deobfuscate_luraph.py emit-lifter --help
```

## Lưu ý
- Đây là pipeline hỗ trợ quá trình full devirtualization, không tự động reconstruct 100% semantics ngay lập tức.
- Chất lượng infer phụ thuộc vào độ đầy đủ của `trace.jsonl`.
