#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查所有Jinja2模板文件的语法
"""

import os
from jinja2 import Template, FileSystemLoader, Environment


def check_template_syntax(filepath):
    """检查单个模板文件的语法"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # 创建Jinja2环境，模拟模板加载
        env = Environment(loader=FileSystemLoader(os.path.dirname(filepath) or '.'))
        # 尝试解析模板
        template = env.from_string(content)
        return True, None
    except Exception as e:
        return False, str(e)


def main():
    """检查所有模板文件"""
    templates_dir = '/www/wwwroot/xiangxiantu/templates'
    error_files = []
    
    print(f"开始检查模板文件语法...")
    print(f"检查目录: {templates_dir}")
    print("=" * 80)
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                is_valid, error = check_template_syntax(filepath)
                if is_valid:
                    print(f"✓ {filepath} - 语法正确")
                else:
                    print(f"✗ {filepath} - 语法错误: {error}")
                    error_files.append((filepath, error))
    
    print("=" * 80)
    if error_files:
        print(f"发现 {len(error_files)} 个语法错误:")
        for filepath, error in error_files:
            print(f"  - {filepath}: {error}")
        return 1
    else:
        print("所有模板文件语法正确！")
        return 0


if __name__ == '__main__':
    exit(main())
