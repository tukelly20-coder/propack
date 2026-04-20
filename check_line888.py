#!/usr/bin/env python3
with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8')
lines = text.splitlines()

line_num = 887
print('Line 888 length:', len(lines[line_num]))
print('Line 888 content (escaped):', lines[line_num].encode('unicode_escape').decode('ascii'))
# Count triple quotes using a simple method
count = 0
i = 0
while i < len(lines[line_num]) - 2:
    if lines[line_num][i:i+3] == '"""':
        count += 1
        i += 3
    else:
        i += 1
print('Triple quote count in line 888:', count)
print('Ends with triple quote?', lines[line_num].rstrip().endswith('"""'))

# Also check last line of file
print('Last line:', repr(lines[-1]))
print('File ends with newline?', text.endswith('\n'))
