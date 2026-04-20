#!/usr/bin/env python3
path = r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py'
with open(path, 'rb') as f:
    raw = f.read()

candidates = []
for i in range(len(raw)-3):
    if raw[i]==0xE1 and raw[i+1]==0xBB and raw[i+2]==0x83:
        # Check surrounding
        before = raw[max(0,i-2):i]
        after = raw[i+3:i+4]
        candidates.append((i, before, after))

print(f'Found {len(candidates)} e1 bb 83 sequences')
for pos, before, after in candidates:
    before_asc = ''.join(chr(b) if 32<=b<127 else '.' for b in before)
    after_asc = chr(after[0]) if after and 32<=after[0]<127 else ('.' if after else '')
    print(f'{pos}: before="{before_asc}" after="{after_asc}" raw: {raw[pos:pos+3].hex()}')
