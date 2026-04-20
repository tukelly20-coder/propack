#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'r', encoding='utf-8') as f:
    text = f.read()

quotes = []
pos = 0
while True:
    idx = text.find('"""', pos)
    if idx == -1:
        break
    quotes.append(idx)
    pos = idx + 3

print(f'Total occurrences: {len(quotes)}')
# Show last 10
print('Last 10 positions:')
for i in range(max(0, len(quotes)-10), len(quotes)):
    end = quotes[i+1] if i+1 < len(quotes) else 'None'
    snippet = text[quotes[i]:quotes[i]+40].replace('\n', '\\n')
    print(f'  [{i}] pos={quotes[i]}, end={end}, snippet={repr(snippet)}')

# Check get_pending_count_sync
idx_def = text.find('def get_pending_count_sync')
print(f'\ndef get_pending_count_sync at: {idx_def}')
if idx_def != -1:
    idx_triple = text.find('"""', idx_def)
    print(f'triple after def at: {idx_triple}')
    next_triple = text.find('"""', idx_triple+3)
    print(f'next triple at: {next_triple}')
    if next_triple != -1:
        docstring = text[idx_triple+3:next_triple]
        print(f'Docstring length: {len(docstring)}')
        print(f'Docstring: {repr(docstring[:100])}')
    else:
        print('ERROR: No closing triple quote found!')
        print('Remainder:', repr(text[idx_triple:idx_triple+100]))
