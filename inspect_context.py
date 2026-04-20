#!/usr/bin/env python3
import re

path = r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py'
with open(path, 'rb') as f:
    raw = f.read()

# Decode as latin-1 to see the textual context
text_latin1 = raw.decode('latin-1')

# Find the problematic positions and show context in text
bad_positions = [33, 94, 106, 133, 137, 180, 249, 290, 415, 441]
for pos in bad_positions[:10]:
    # Convert byte position to character index (latin-1 1:1 mapping)
    # Show context string
    start = max(0, pos-30)
    end = min(len(text_latin1), pos+30)
    context = text_latin1[start:end]
    print(f'Pos {pos} (byte offset):')
    print(f'  Context: {repr(context)}')
    # Also show the exact corrupted sequence
    print(f'  Corrupt seq: {repr(text_latin1[pos:pos+3])}')
    print()
