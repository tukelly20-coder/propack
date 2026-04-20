#!/usr/bin/env python3
with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = 35918
print('Char at position 35918:', repr(text[pos]))
print('Snippet 35910-35930:', repr(text[35910:35930]))
print('Snippet 35915-35950:', repr(text[35915:35950]))
# Also find nearest triple quote before and after
before = text.rfind('"""', 0, pos)
after = text.find('"""', pos)
print(f'Prev triple quote at: {before}')
print(f'Next triple quote at: {after}')
if before >= 0:
    print('Before snippet:', repr(text[before:before+50]))
if after >= 0:
    print('After snippet:', repr(text[after:after+50]))
