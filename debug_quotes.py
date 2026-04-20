#!/usr/bin/env python3
with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'r', encoding='utf-8') as f:
    text = f.read()

cnt = text.count('"""')
print(f'Number of triple double quotes: {cnt}')

# Tìm vị trí
pos = 0
quotes = []
while True:
    idx = text.find('"""', pos)
    if idx == -1:
        break
    quotes.append(idx)
    pos = idx + 3

print(f'Total triple-quote blocks: {len(quotes)}')
if len(quotes) % 2 != 0:
    print('WARNING: Odd number - unterminated string!')
    print('Positions:', quotes)
else:
    print('Even number - all strings terminated')
    for i in range(0, len(quotes), 2):
        start = quotes[i]
        end = quotes[i+1] if i+1 < len(quotes) else -1
        snippet = text[start:start+50] if start >= 0 else ''
        print(f'Block {i//2}: start={start}, end={end}, snippet: {snippet[:50]}')
