#!/usr/bin/env python3
import codecs

path = r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py'

with open(path, 'rb') as f:
    raw = f.read()

print(f'File size: {len(raw)} bytes')

# Kiểm tra toàn bộ có decode UTF-8 được không
try:
    decoded = raw.decode('utf-8')
    print('UTF-8 decode: OK')
except UnicodeDecodeError as e:
    print(f'UTF-8 decode error: {e}')
    # Tìm vị trí lỗi
    start = max(0, e.start-20)
    end = min(len(raw), e.end+20)
    print(f'Error bytes: {raw[start:end].hex()}')
    print(f'Context: {raw[start:end]}')

# Kiểm tra thêm với 'replace'
decoded_replace = raw.decode('utf-8', errors='replace')
# Tìm các ký tự replacement � (U+FFFD)
bad_positions = []
for i, ch in enumerate(decoded_replace):
    if ch == '\ufffd':
        bad_positions.append(i)
print(f'Number of replacement chars: {len(bad_positions)}')
if bad_positions:
    print('First 10 positions:', bad_positions[:10])
    # Hiển thị context
    for pos in bad_positions[:5]:
        start = max(0, pos-10)
        end = min(len(decoded_replace), pos+10)
        print(f' at {pos}: {repr(decoded_replace[start:end])}')
