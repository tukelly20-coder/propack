#!/usr/bin/env python3
with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'rb') as f:
    raw = f.read()

# Decode thành lines
text = raw.decode('utf-8')
lines = text.splitlines()

# In ra dòng 888 (index 887)
line_num = 887  # 0-index
print(f'Line 888 ({len(lines[line_num])} chars): {repr(lines[line_num])}')
# Đếm số """ trong dòng này
print(f'Count of triple quotes in line: {lines[line_num].count(\'\"\"\"\')}')

# Kiểm tra xem dòng 888 có kết thúc bằng """ không
if lines[line_num].strip().endswith('"""'):
    print('Line ends with triple quote')
else:
    print('Line does NOT end with triple quote')
    # Tìm vị trí cuối cùng của """
    last_quote = lines[line_num].rfind('"""')
    print(f'Last triple quote at column: {last_quote}')
    print(f'After last quote: {repr(lines[line_num][last_quote+3:])}')

# Kiểm tra xem file có kết thúc bằng newline không
print(f'File ends with newline? {text.endswith("\\n")}')
print(f'Last 10 bytes of file: {raw[-10:].hex()}')
print(f'Last line of file: {repr(lines[-1])}')
