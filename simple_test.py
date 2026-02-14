# 简单测试脚本，只检查基本的模块导入
import sys
import traceback

def test_imports():
    """测试基本的模块导入"""
    print("开始测试基本模块导入...")
    
    try:
        print("1. 测试标准库导入...")
        import os
        import re
        import logging
        print("✓ 标准库导入成功")
    except Exception as e:
        print(f"✗ 标准库导入失败: {str(e)}")
        traceback.print_exc()
        return False
    
    try:
        print("\n2. 测试第三方库导入...")
        import pandas as pd
        import plotly.express as px
        import plotly.graph_objects as go
        print("✓ 第三方库导入成功")
    except Exception as e:
        print(f"✗ 第三方库导入失败: {str(e)}")
        traceback.print_exc()
        return False
    
    try:
        print("\n3. 测试自定义模块导入...")
        print("   测试data_processing模块...")
        from data_processing import parse_single_surface_file
        print("   ✓ data_processing模块导入成功")
        
        print("   测试utils.data_validator模块...")
        from utils.data_validator import validate_and_align_data, generate_data_warning
        print("   ✓ utils.data_validator模块导入成功")
        
        print("   测试chart_generation模块...")
        from chart_generation import generate_plots, generate_single_surface_plots, create_combined_chart
        print("   ✓ chart_generation模块导入成功")
        
        print("   测试statistics模块...")
        from statistics import generate_stats, generate_single_surface_stats
        print("   ✓ statistics模块导入成功")
        
        print("✓ 所有自定义模块导入成功")
    except Exception as e:
        print(f"✗ 自定义模块导入失败: {str(e)}")
        traceback.print_exc()
        return False
    
    try:
        print("\n4. 测试Flask模块导入...")
        from flask import Flask
        print("✓ Flask模块导入成功")
    except Exception as e:
        print(f"✗ Flask模块导入失败: {str(e)}")
        traceback.print_exc()
        return False
    
    print("\n✅ 所有模块导入测试通过！")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
