#!/usr/bin/env python3
"""
Comprehensive fix for encoding corruption in NoticeTab.py.
Corruption types:
  A: \xE1\xBB\x3F (60) -> replace third byte with correct value (Vietnamese letters)
  B: \xE1\xBA\x3F (4)  -> replace third byte with correct value (Vietnamese letters)
  C: \xE2\x8F\x3F and \xE2\x9C\x3F (3) -> delete entire 3-byte sequence
  D: \xF0\x9F\x92\x3F (1) -> replace fourth byte (broken emoji, e.g., laptop)
"""

import sys

path = r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py'

with open(path, 'rb') as f:
    raw = bytearray(f.read())

actions = []  # (pos, type, offset, new_byte) offset relative to pos, or delete

# ---- Type A: \xE1\xBB\x3F (replace third byte) ----
pat_a = b'\xE1\xBB\x3F'
pos_a = []
i = 0
while True:
    i = raw.find(pat_a, i)
    if i == -1: break
    pos_a.append(i)
    i += 3
print(f'Type A: {len(pos_a)} sequences')
repl_a = [
    0x8B, 0x83, 0x8B, 0x9D, 0xAD, 0x8B, 0x9D, 0x81, 0x83, 0x91,
    0x9D, 0x83, 0xAB, 0x83, 0x91, 0xAB, 0x83, 0x8B, 0x81, 0x83,
    0xAF, 0xAB, 0xAD, 0xAD, 0xAD, 0xAD, 0x81, 0xAD, 0xAD, 0x8B,
    0xAB, 0xAB, 0xAF, 0x9F, 0xAB, 0x8B, 0xAB, 0xAB, 0xAF, 0x9F,
    0xAB, 0xAD, 0xAD, 0x8B, 0xAB, 0xAB, 0xAF, 0x9F, 0x9D, 0x87,
    0x81, 0x87, 0x83, 0xAB, 0xAB, 0xAF, 0x9F, 0x91, 0xAD, 0x91
]
if len(pos_a) != len(repl_a):
    print(f'ERROR: Type A count mismatch {len(pos_a)} vs {len(repl_a)}', file=sys.stderr)
    sys.exit(1)
for idx, pos in enumerate(pos_a):
    actions.append( (pos, 'replace', 2, repl_a[idx]) )

# ---- Type B: \xE1\xBA\x3F (replace third byte) ----
pat_b = b'\xE1\xBA\x3F'
pos_b = []
i = 0
while True:
    i = raw.find(pat_b, i)
    if i == -1: break
    pos_b.append(i)
    i += 3
print(f'Type B: {len(pos_b)} sequences')
repl_b = [0xA3, 0xA3, 0xA3, 0xBC]
if len(pos_b) != len(repl_b):
    print(f'ERROR: Type B count mismatch {len(pos_b)} vs {len(repl_b)}', file=sys.stderr)
    sys.exit(1)
for idx, pos in enumerate(pos_b):
    actions.append( (pos, 'replace', 2, repl_b[idx]) )

# ---- Type C: delete stray E2 sequences (3-byte) ----
pat_c_list = [b'\xE2\x8F\x3F', b'\xE2\x9C\x3F']
pos_c = []
for pat in pat_c_list:
    i = 0
    while True:
        i = raw.find(pat, i)
        if i == -1: break
        pos_c.append(i)
        i += 1
print(f'Type C: {len(pos_c)} sequences to delete')
for pos in pos_c:
    actions.append( (pos, 'delete', None, None) )

# ---- Type D: fix broken 4-byte emoji sequence F0 9F 92 3F (replace fourth byte) ----
pat_d = b'\xF0\x9F\x92\x3F'
pos_d = []
i = 0
while True:
    i = raw.find(pat_d, i)
    if i == -1: break
    pos_d.append(i)
    i += 1
print(f'Type D: {len(pos_d)} sequences (emoji fix)')
if len(pos_d) != 1:
    print(f'ERROR: expected 1 type-D pattern, got {len(pos_d)}', file=sys.stderr)
    sys.exit(1)
# Replace fourth byte (offset 3) with 0xBB (laptop emoji)
for pos in pos_d:
    actions.append( (pos, 'replace', 3, 0xBB) )

# ---- Apply actions in descending order of position ----
actions.sort(key=lambda x: x[0], reverse=True)
for (pos, typ, offset, new_val) in actions:
    if typ == 'delete':
        del raw[pos:pos+3]
    elif typ == 'replace':
        idx = pos + offset
        raw[idx] = new_val
    else:
        pass

# ---- Write result ----
with open(path, 'wb') as f:
    f.write(raw)

print('All fixes applied successfully.')
