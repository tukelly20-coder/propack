#!/usr/bin/env python3
path = r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py'
with open(path, 'rb') as f:
    raw = f.read()

bad_positions = [i for i in range(len(raw)-2) if raw[i]==0xE1 and raw[i+1]==0xBB and raw[i+2]==0x3F]
print(f'Corrupted count: {len(bad_positions)}')
for pos in bad_positions:
    start = max(0, pos-15)
    end = min(len(raw), pos+15)
    chunk = raw[start:end]
    # Format as hex with ASCII
    hexs = []
    asc = []
    for i,b in enumerate(chunk):
        hexs.append(f'{b:02x}')
        if 32 <= b < 127:
            asc.append(chr(b))
        else:
            asc.append('.')
    print(f'Pos {pos}: {" ".join(hexs)}')
    print(f'       {"".join(asc)}')
    print()
