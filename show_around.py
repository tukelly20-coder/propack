#!/usr/bin/env python3
with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'r', encoding='utf-8') as f:
    text = f.read()
lines = text.splitlines()
# in lines 885-895 an escaped
for i in range(884, min(895, len(lines))):
    line_escaped = lines[i].encode('unicode_escape').decode('ascii')
    print(f'{i+1}: {line_escaped}')
