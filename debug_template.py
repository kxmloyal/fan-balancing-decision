#!/usr/bin/env python
# -*- coding: utf-8 -*-

def debug_template():
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if_count = 0
    endif_count = 0
    for_count = 0
    endfor_count = 0
    
    for i, line in enumerate(lines, 1):
        if '{%' in line:
            print(f"Line {i}: {line.strip()}")
            if '{% if' in line:
                if_count += 1
            elif '{% endif' in line:
                endif_count += 1
            elif '{% for' in line:
                for_count += 1
            elif '{% endfor' in line:
                endfor_count += 1
    
    print(f"\nSummary:")
    print(f"IF statements: {if_count}")
    print(f"ENDIF statements: {endif_count}")
    print(f"FOR statements: {for_count}")
    print(f"ENDFOR statements: {endfor_count}")
    
    if if_count != endif_count:
        print(f"MISMATCH: IF/ENDIF difference: {if_count - endif_count}")
    if for_count != endfor_count:
        print(f"MISMATCH: FOR/ENDFOR difference: {for_count - endfor_count}")

if __name__ == '__main__':
    debug_template()