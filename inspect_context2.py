#!/usr/bin/env python3
import re

path = r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py'
with open(path, 'rb') as f:
    raw = f.read()

text_latin1 = raw.decode('latin-1')

bad_positions = [33, 94, 106, 133, 137, 180, 249, 290, 415, 441]
out_lines = []
for pos in bad_positions[:15]:
    start = max(0, pos-30)
    end = min(len(text_latin1), pos+30)
    context = text_latin1[start:end]
    # Encode to ascii with backslashreplace to see code points
    rep = context.encode('ascii', 'backslashreplace').decode('ascii')
    out_lines.append(f'Pos {pos}: {rep}')
    # Show the three-byte sequence at pos
    seq = text_latin1[pos:pos+3]
    seq_rep = seq.encode('ascii', 'backslashreplace').decode('ascii')
    out_lines.append(f'  corrupt: {seq_rep}')
    out_lines.append('')

with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\context_dump.txt', 'w', encoding='utf-8') as out:
    out.write('\n'.join(out_lines))
print('Wrote context to context_dump.txt')
