#!/usr/bin/env python3
with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'r', encoding='utf-8') as f:
    text = f.read()
lines = text.splitlines()
line = lines[887]  # dòng 888
print(f'Line length (without newline): {len(line)}')
print(f'Line (escaped): {line.encode("unicode_escape").decode("ascii")}')
# Column 64 (1-indexed) là index 63 (0-indexed)
col = 64
idx = col - 1
if idx < len(line):
    ch = line[idx]
    print(f'Character at column {col} (escaped): {ch.encode("unicode_escape").decode("ascii")}')
    snippet = line[max(0,idx-5):idx+5]
    print(f'Snippet (escaped): {snippet.encode("unicode_escape").decode("ascii")}')
else:
    print(f'Column {col} out of range (len={len(line)})')
# Also check if line ends with triple quote properly
if line.rstrip().endswith('"""'):
    print('Line ends with triple quote')
else:
    print('Line DOES NOT end with triple quote')
    # Find last triple quote
    last = line.rfind('"""')
    print(f'Last triple quote at index: {last}')
    after = line[last+3:]
    print(f'After last quote (escaped): {after.encode("unicode_escape").decode("ascii")}')
