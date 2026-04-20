#!/usr/bin/env python3
with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'rb') as f:
    raw = f.read()

# Tìm ''' (0x27 0x27 0x27)
pos = 0
single_triple = []
while True:
    idx = raw.find(b"'''", pos)
    if idx == -1:
        break
    single_triple.append(idx)
    pos = idx + 3

print(f'Single triple quotes (''\'): {len(single_triple)} occurrences')
print('Positions:', single_triple)

# Also check raw double quotes inside regular strings
# Find patterns like \"\"\" inside a string (escaped)
# But that would be \\"\\"\\" probably. Look for backslash before triple quote
pos = 0
escaped = []
while True:
    idx = raw.find(b'\\"""', pos)
    if idx == -1:
        break
    escaped.append(idx)
    pos = idx + 4
print(f'Escaped triple quotes (\\"""): {len(escaped)} at {escaped}')

pos = 0
escaped2 = []
while True:
    idx = raw.find(b'\\\'\\\'\\\'', pos)
    if idx == -1:
        break
    escaped2.append(idx)
    pos = idx + 6
print(f'Escaped single triple: {len(escaped2)} at {escaped2}')
