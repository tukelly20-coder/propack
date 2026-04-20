#!/usr/bin/env python3
import re

path = r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py'
with open(path, 'rb') as f:
    raw = f.read()

text_latin1 = raw.decode('latin-1')

# Find all e1 bb 3f positions
positions = []
for i in range(len(raw)-2):
    if raw[i]==0xE1 and raw[i+1]==0xBB and raw[i+2]==0x3F:
        positions.append(i)

print(f'Found {len(positions)} bad sequences. Contexts:')

out_lines = []
for pos in positions:
    start = max(0, pos-40)
    end = min(len(text_latin1), pos+40)
    before = text_latin1[start:pos]
    after = text_latin1[pos+3:end]
    # Represent non-ascii as escape codes for safe display
    before_rep = before.encode('ascii', 'backslashreplace').decode('ascii')
    after_rep = after.encode('ascii', 'backslashreplace').decode('ascii')
    out_lines.append(f'Pos {pos}: ...{before_rep}[E1 BB 3F]{after_rep}...')

with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\all_contexts.txt', 'w', encoding='utf-8') as fout:
    fout.write('\n'.join(out_lines))
print('Written to all_contexts.txt')
