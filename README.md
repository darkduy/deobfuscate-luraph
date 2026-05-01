# Luraph Deobfuscator (Python -> 1 Luau file)

Đúng theo yêu cầu: tool viết bằng **Python** và output ra **một file code Luau duy nhất**.

## Cách dùng
```bash
python3 deobfuscate_luraph.py main.luau -o deobfuscated.luau
```

## Kết quả
- Sinh ra `deobfuscated.luau`.
- File này chứa:
  - `original_source` (script gốc đã bỏ header Luraph),
  - `recovered.decoded_hex` (payload decode bước đầu),
  - danh sách printable strings (comment preview) để reverse nhanh.

> Đây là best-effort deobfuscation để gom dữ liệu reverse vào 1 file Luau, chưa phải full VM devirtualizer.
