#!/usr/bin/env python3
path = r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py'
with open(path, 'rb') as f:
    raw = f.read()

# Find all e1 bb 3f positions
positions = [i for i in range(len(raw)-2) if raw[i]==0xE1 and raw[i+1]==0xBB and raw[i+2]==0x3F]

print(f'Found {len(positions)} bad bytes')
for pos in positions:
    start = max(0, pos-10)
    end = min(len(raw), pos+10)
    chunk = raw[start:end]
    print(f'{pos}: {chunk.hex()}')
