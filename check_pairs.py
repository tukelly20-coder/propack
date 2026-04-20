#!/usr/bin/env python3
with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'rb') as f:
    raw = f.read()

# Tìm tất cả vị trí """
pos = 0
quotes = []
while True:
    idx = raw.find(b'"""', pos)
    if idx == -1:
        break
    quotes.append(idx)
    pos = idx + 3

print(f'Total: {len(quotes)}')
# Giả sử cặp open-close: even index mở, odd index đóng
# Kiểm tra xem có cặp nào bị sai thứ tự không
for i in range(len(quotes)-1):
    # giả sử mở nên là ở trước, đóng sau
    # Thông thường, open thì close phải sau. Không kiểm tra nesting vì docstring không lồng.
    pass

# Kiểm tra xem có `"""` nào bên trong một docstring không (giữa hai """ khác)
bad = []
for i in range(0, len(quotes)-1, 2):
    if i+1 < len(quotes):
        start = quotes[i]
        end = quotes[i+1]
        # Kiểm tra between
        between = raw[start+3:end]
        if b'"""' in between:
            bad.append((i, start, end))
            print(f'Found inner triple quote in pair {i}: between {start} and {end}')
if not bad:
    print('No inner triple quotes inside docstrings')

# Nếu count lẻ, cặp cuối không có đóng
if len(quotes) % 2 != 0:
    print(f'Unpaired opening at index {quotes[-1]} (last one)')
else:
    print('All paired.')

# In ra cặp đầu và cuối để xem pattern
print('First pair:', quotes[0], quotes[1] if len(quotes)>1 else 'None')
print('Last pair:', quotes[-2], quotes[-1] if len(quotes)>=2 else 'None')
