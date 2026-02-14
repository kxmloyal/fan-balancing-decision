#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有模块导入是否正确
"""

import sys
import os

# 将当前目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有模块导入"""
    print("开始测试模块导入...")
    
    # 测试核心模块
    modules_to_test = [
        'data_processing',
        'chart_generation',
        'statistics',
        'utils.data_validator',
        'utils.chart_cache',
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✓ 成功导入模块: {module_name}")
        except ImportError as e:
            print(f"✗ 导入模块失败: {module_name}")
            print(f"  错误信息: {e}")
        except Exception as e:
            print(f"✗ 导入模块时发生其他错误: {module_name}")
            print(f"  错误信息: {e}")
    
    # 测试具体函数导入
    print("\n开始测试具体函数导入...")
    
    function_imports = [
        ('data_processing', 'parse_single_surface_file'),
        ('chart_generation', 'generate_plots'),
        ('chart_generation', 'generate_single_surface_plots'),
        ('chart_generation', 'create_combined_chart'),
        ('statistics', 'generate_stats'),
        ('statistics', 'generate_single_surface_stats'),
        ('utils.data_validator', 'validate_and_align_data'),
        ('utils.data_validator', 'generate_data_warning'),
    ]
    
    for module_name, function_name in function_imports:
        try:
            module = __import__(module_name, fromlist=[function_name])
            getattr(module, function_name)
            print(f"✓ 成功导入函数: {module_name}.{function_name}")
        except ImportError as e:
            print(f"✗ 导入函数失败: {module_name}.{function_name}")
            print(f"  错误信息: {e}")
        except AttributeError as e:
            print(f"✗ 函数不存在: {module_name}.{function_name}")
            print(f"  错误信息: {e}")
        except Exception as e:
            print(f"✗ 导入函数时发生其他错误: {module_name}.{function_name}")
            print(f"  错误信息: {e}")

if __name__ == '__main__':
    test_imports()
    print("\n测试完成!")
