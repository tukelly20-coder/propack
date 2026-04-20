#!/usr/bin/env python3
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

print(f'Total triple-quote occurrences: {len(quotes)}')
print('Checking pairs...')
for i in range(0, len(quotes), 2):
    if i+1 >= len(quotes):
        print(f'UNTERMINATED: starts at position {quotes[i]}')
        print('Context:', repr(text[quotes[i]:quotes[i]+100]))
        break
    start = quotes[i]
    end = quotes[i+1]
    block_content = text[start+3:end]  # nội dung giữa hai """
    # Kiểm tra xem có dấu đóng thực sự không (đôi khi có """ trong nội dung)
    # Nhưng thường thì đúng rồi
    pass

# Cũng có thể có raw string với r""" nhưng ít phổ biến
# Kiểm tra thêm単 quotes
single_quotes = []
pos = 0
while True:
    idx = text.find("'''", pos)
    if idx == -1:
        break
    single_quotes.append(idx)
    pos = idx + 3
print(f"Single triple quotes ('''): {len(single_quotes)}")
if single_quotes:
    print('Positions:', single_quotes)
