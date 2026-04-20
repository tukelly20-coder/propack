#!/usr/bin/env python3
with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Tìm tất cả occurrences của """
quotes = []
pos = 0
while True:
    idx = text.find('"""', pos)
    if idx == -1:
        break
    quotes.append(idx)
    pos = idx + 3

print(f'Total occurrences: {len(quotes)}')
# Hiển thị cặp đầu tiên và cuối cùng
print('First 5:')
for i in range(min(5, len(quotes))):
    end = quotes[i+1] if i+1 < len(quotes) else 'None'
    snippet = text[quotes[i]:quotes[i]+30].replace('\n', '\\n')
    print(f'  [{i}] pos={quotes[i]}, end={end}, content={repr(snippet)}')

# Kiểm tra docstring gần cuối
print('\nDocstring around function get_pending_count_sync:')
# Tìm dòng "def get_pending_count_sync"
idx_def = text.find('def get_pending_count_sync')
print(f'def at index: {idx_def}')
# Tìm triple quotes sau def
idx_triple = text.find('"""', idx_def)
print(f'triple quote after def at: {idx_triple}')
print('Snippet:', repr(text[idx_triple:idx_triple+100]))
# Kiểm tra xem có closing không
next_triple = text.find('"""', idx_triple+3)
print(f'Closing triple at: {next_triple}')
if next_triple != -1:
    print('Docstring content:', repr(text[idx_triple+3:next_triple][:100]))
