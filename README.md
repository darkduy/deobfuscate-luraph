# Luraph Deobfuscation Tool

Script `deobfuscate_luraph.py` là công cụ hỗ trợ deobfuscate cho file được protect bằng Luraph.

## Tính năng
- Phát hiện chữ ký Luraph trong file `.lua/.luau`.
- Tự động tách payload đã encode.
- Decode payload theo block 5 ký tự (kiểu base85 thường thấy trong nhiều version Luraph).
- Trích xuất chuỗi printable để hỗ trợ reverse.

## Cách dùng
```bash
python3 deobfuscate_luraph.py main.luau -o out
```

## Kết quả
Thư mục output gồm:
- `payload.txt`: payload mã hoá thô.
- `decoded.bin`: bytes sau khi decode bước đầu.
- `strings.txt`: string printable tìm thấy trong `decoded.bin`.

> Lưu ý: đây là **bootstrap tool** để phục vụ quá trình reverse, chưa phải full VM devirtualizer cho mọi mẫu Luraph.
