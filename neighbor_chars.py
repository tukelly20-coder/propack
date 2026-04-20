#!/usr/bin/env python3
path = r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py'
with open(path, 'rb') as f:
    raw = f.read()

bad_positions = [i for i in range(len(raw)-2) if raw[i]==0xE1 and raw[i+1]==0xBB and raw[i+2]==0x3F]
print(f'{len(bad_positions)} positions.')

def char_repr(b):
    if 32 <= b < 127:
        return chr(b)
    return '.'

for pos in bad_positions:
    # Get 5 bytes before and after
    start = max(0, pos-5)
    before = raw[start:pos]
    after = raw[pos+3:pos+8]
    before_asc = ''.join(char_repr(b) for b in before)
    after_asc = ''.join(char_repr(b) for b in after)
    print(f'{pos:6d}: before="{before_asc}"  after="{after_asc}"')
