# 检查模板文件中的控制结构标签匹配情况
import re

def check_jinja_tags(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有Jinja2控制结构标签
    if_tags = len(re.findall(r'{%\s*if', content))
    endif_tags = len(re.findall(r'{%\s*endif', content))
    
    for_tags = len(re.findall(r'{%\s*for', content))
    endfor_tags = len(re.findall(r'{%\s*endfor', content))
    
    print(f"IF 标签数量: {if_tags}")
    print(f"ENDIF 标签数量: {endif_tags}")
    print(f"FOR 标签数量: {for_tags}")
    print(f"ENDFOR 标签数量: {endfor_tags}")
    
    # 检查是否有不匹配的标签
    if if_tags != endif_tags:
        print(f"警告: IF 和 ENDIF 标签数量不匹配! IF: {if_tags}, ENDIF: {endif_tags}")
    
    if for_tags != endfor_tags:
        print(f"警告: FOR 和 ENDFOR 标签数量不匹配! FOR: {for_tags}, ENDFOR: {endfor_tags}")

if __name__ == "__main__":
    check_jinja_tags("templates/index.html")