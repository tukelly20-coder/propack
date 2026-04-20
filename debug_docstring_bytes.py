#!/usr/bin/env python3
with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'rb') as f:
    raw = f.read()

# Tìm pattern bytes của docstring này
# Ta biết nội dung: "Lấy sốlượng pending notices (synchronous, for badge)"
# Cần tìm bytes của phần đó và xem cấu trúc triple quotes
# Đơn giản: tìm vị trí bytes của 'Lấy' trong file
pattern_start = b'\xe1\xba\xa5'  # UTF-8 for Lấy
idx_start = raw.find(pattern_start)
print(f'"Lay" (bytes e1 ba a5) at byte index: {idx_start}')
if idx_start != -1:
    # Tìm về phía trước 3 bytes cho """
    before = raw[idx_start-10:idx_start]
    print(f'10 bytes before "Lấy": {before.hex()}')
    # Tìm sau đoạn này kết thúc bằng """
    # Nội dung roughly: "Lấy sốlượng pending notices (synchronous, for badge)"
    # Tìm closing """
    after_content = b'pending notices (synchronous, for badge)"""'
    idx_end = raw.find(after_content, idx_start)
    print(f'After content pattern at: {idx_end}')
    if idx_end != -1:
        closing_pos = idx_end + len(after_content) - 3  # start of """
        print(f'Closing triple quote at byte: {closing_pos}')
        print(f'Bytes around closing: {raw[closing_pos:closing_pos+10].hex()}')
        # Now find the opening triple quote before idx_start
        opening_search = raw.rfind(b'"""', 0, idx_start)
        print(f'Opening triple quote at byte: {opening_search}')
        if opening_search != -1:
            print(f'Opening snippet: {raw[opening_search:opening_search+10].hex()}')
            # Check if there are any triple quotes between opening and content start
            between = raw[opening_search+3:idx_start]
            if b'"""' in between:
                print('WARNING: Another triple quote inside!')
            else:
                print('OK: No extra triple quotes inside')
