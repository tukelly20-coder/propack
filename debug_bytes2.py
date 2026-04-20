#!/usr/bin/env python3
with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'rb') as f:
    raw = f.read()

# Timings using UTF-8 bytes for "Lấy": e1 ba a5
pattern_start = b'\xe1\xba\xa5'
idx_start = raw.find(pattern_start)
print(f'Byte index of "Lay" pattern: {idx_start}')
if idx_start != -1:
    before = raw[idx_start-10:idx_start]
    print(f'10 bytes before: {before.hex()}')
    after_content = b'pending notices (synchronous, for badge)"""'
    idx_end = raw.find(after_content, idx_start)
    print(f'After content pattern at byte: {idx_end}')
    if idx_end != -1:
        closing_pos = idx_end + len(after_content) - 3
        print(f'Closing triple quote at byte: {closing_pos}')
        print(f'Bytes around closing: {raw[closing_pos:closing_pos+10].hex()}')
        opening_search = raw.rfind(b'"""', 0, idx_start)
        print(f'Opening triple quote at byte: {opening_search}')
        if opening_search != -1:
            print(f'Opening snippet: {raw[opening_search:opening_search+10].hex()}')
            between = raw[opening_search+3:idx_start]
            if b'"""' in between:
                print('WARNING: Another triple quote inside docstring!')
            else:
                print('OK: No extra triple quotes inside')

# Also check for any raw bytes sequence 22 22 22 (""") not in pairs
print('\nAll triple-quote byte positions:')
pos = 0
quotes_bytes = []
while True:
    idx = raw.find(b'"""', pos)
    if idx == -1:
        break
    quotes_bytes.append(idx)
    pos = idx + 3
print(f'Total triple-quote sequences: {len(quotes_bytes)}')
print('Positions:', quotes_bytes)
