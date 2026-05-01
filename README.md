# Luraph Deobfuscator (Python)

Bạn đúng: mục tiêu là **deobfuscate ra code Luau** (không chỉ metadata).

Tool `deobfuscate_luraph.py` giờ sẽ tạo trực tiếp một file code `deobfuscated.luau` theo hướng readable:
- Chuẩn hoá số hex/binary obfuscate (`0x`, `0b`, underscore) về số thập phân.
- Decode escape string và re-encode gọn.
- Format lại code (tách `;`, block `if/else/end`, indent nhẹ).
- Bỏ header Luraph.

## Dùng
```bash
python3 deobfuscate_luraph.py main.luau -o deobfuscated.luau
```

> Lưu ý: đây là **best-effort source deobfuscation**, chưa phải full devirtualization VM của Luraph.
