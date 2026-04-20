#!/usr/bin/env python3
import ast
import tokenize
import io

path = r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py'

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Tokenize first to see where the error is
try:
    tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    print('Tokenize OK, total tokens:', len(tokens))
except tokenize.TokenError as e:
    print('Tokenize error:', e)
    print('At line:', e.args[1])
    # Show lines around
    lines = text.splitlines()
    start_line = e.args[1][0] if len(e.args) > 1 else 0
    print('Lines around:')
    for i in range(max(0, start_line-5), min(len(lines), start_line+5)):
        print(f'{i+1}: {repr(lines[i])}')

# Also try ast.parse with more details
try:
    tree = ast.parse(text)
    print('AST parse OK')
except SyntaxError as e:
    print(f'SyntaxError: {e.msg}')
    print(f'Line: {e.lineno}, offset: {e.offset}')
    print(f'Text: {repr(e.text)}')
    lines = text.splitlines()
    # Print surrounding lines
    s = max(0, e.lineno-3)
    for i in range(s, min(len(lines), e.lineno+2)):
        marker = '-->' if i == e.lineno-1 else '   '
        print(f'{marker} {i+1}: {repr(lines[i])}')
