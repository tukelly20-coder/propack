#!/usr/bin/env python3
with open(r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py', 'rb') as f:
    raw = f.read()

for enc in ['utf-8', 'latin-1', 'cp1252', 'cp1258', 'utf-16']:
    try:
        decoded = raw.decode(enc)
        print(f'{enc}: SUCCESS, length {len(decoded)}')
        # Show first 200 chars with escapes
        preview = decoded[:200].encode('unicode_escape').decode('ascii')
        print(f'  preview: {preview}')
        break
    except Exception as e:
        print(f'{enc}: {str(e)[:100]}')
