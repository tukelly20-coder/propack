#!/usr/bin/env python3
path = r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py'
with open(path, 'rb') as f:
    raw = f.read()

text_latin1 = raw.decode('latin-1')

# Find all e1 bb 3f positions
positions = []
for i in range(len(raw)-2):
    if raw[i]==0xE1 and raw[i+1]==0xBB and raw[i+2]==0x3F:
        positions.append(i)

print(f'Found {len(positions)} corrupted sequences (e1 bb 3f)')
for pos in positions:
    start = max(0, pos-20)
    end = min(len(text_latin1), pos+30)
    snippet = text_latin1[start:end]
    # Convert to ascii with backslashreplace to see bytes of non-ascii
    snippet_esc = snippet.encode('ascii', 'backslashreplace').decode('ascii')
    # Mark the corruption
    before = snippet_esc[:pos-start]
    corrupt = snippet_esc[pos-start:pos-start+3]
    after = snippet_esc[pos-start+3:]
    print(f'Pos {pos}: ...{before}[CORRUPT]{after}...')
    # Also print raw bytes hex around
    hexs = raw[start:end].hex()
    print(f'  hex: ...{hexs}...')
