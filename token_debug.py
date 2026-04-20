#!/usr/bin/env python3
import tokenize
import io

path = r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\src\NoticeTab.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

try:
    tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
except tokenize.TokenError as e:
    print(f'TokenError: {e}')
    # e.args[1] is (lineno, offset)
    error_line = e.args[1][0]
    error_offset = e.args[1][1]
    print(f'Error at line: {error_line}, offset: {error_offset}')
    lines = text.splitlines()
    # Show lines from error_line-5 to +5
    start = max(0, error_line-1-3)
    end = min(len(lines), error_line+3)
    print(f'Lines around line {error_line}:')
    for i in range(start, end):
        marker = '>>>' if i == error_line-1 else '   '
        # safely print with escapes
        line_esc = lines[i].encode('unicode_escape').decode('ascii')
        print(f'{marker} {i+1}: {line_esc}')
    # Also check if there is any unterminated string before
    # We'll manually scan for triple quotes and single quotes from start to error_line
    print('\n--- Scanning for open strings before error line ---')
    # Simple state machine: track if inside string, and what delimiter
    in_string = False
    string_delim = None
    line_num = 0
    for i, line in enumerate(lines):
        j = 0
        while j < len(line):
            ch = line[j]
            if in_string:
                # Check for closing delimiter
                if string_delim in ('"', "'"):
                    if ch == '\\':
                        j += 2  # skip escaped char
                        continue
                    elif ch == string_delim:
                        in_string = False
                        string_delim = None
                elif string_delim in ('"""', "'''"):
                    if j+2 < len(line) and line[j:j+3] == string_delim:
                        in_string = False
                        string_delim = None
                        j += 2  # skip next two
                # else: keep scanning
            else:
                # Not in string: look for opening
                if ch in ('"', "'"):
                    # Check if triple
                    if j+2 < len(line) and line[j:j+3] == ch*3:
                        in_string = True
                        string_delim = ch*3
                        j += 2
                    else:
                        in_string = True
                        string_delim = ch
                elif ch == '#':
                    break  # comment, ignore rest
            j += 1
        if in_string:
            print(f'String still open at end of line {i+1}, delimiter: {string_delim}')
            # Show snippet of that line
            print(f'  Snippet: {line[max(0,j-10):j+10].encode("unicode_escape").decode("ascii")}')
            break
    else:
        print('No open string found before error line')
except Exception as e:
    print('Other error:', e)
