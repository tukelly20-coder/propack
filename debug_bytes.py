#!/usr/bin/env python3
with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'rb') as f:
    raw = f.read()

# Tìm vị trí trong raw bytes tương ứng với char index ~35918 trong decoded
# Cần decode lần lượt để biết tổng số bytes
# Cách đơn: tìm bytes cho sequence "...synchronous, for badge)""""
# Tìm chuỗi bytes 'synchronous, for badge)"""'
pattern = b'synchronous, for badge)"""'
idx = raw.find(pattern)
print(f'Pattern found at byte index: {idx}')
if idx != -1:
    # byte index của """ sau pattern là idx + len(pattern)
    triple_quote_byte_pos = idx + len(pattern)
    print(f'Triple quote bytes at: {triple_quote_byte_pos}')
    print('Bytes around:', raw[triple_quote_byte_pos:triple_quote_byte_pos+10].hex())
    # Hiển thị 5 bytes trước và 10 sau
    print('Context (before):', raw[triple_quote_byte_pos-5:triple_quote_byte_pos].hex())
    print('Context (after):', raw[triple_quote_byte_pos+3:triple_quote_byte_pos+13].hex())
