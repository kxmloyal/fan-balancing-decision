# 简单测试修复是否有效
import sys
import os

# 添加当前目录到sys.path
sys.path.insert(0, '.')

try:
    print("测试1: 导入statistics模块")
    from statistics import generate_stats, generate_single_surface_stats
    print("✓ statistics模块导入成功")
    
    print("测试2: 导入chart_generation模块")
    from chart_generation import generate_plots, generate_single_surface_plots, create_combined_chart
    print("✓ chart_generation模块导入成功")
    
    print("测试3: 导入utils.data_validator模块")
    from utils.data_validator import validate_and_align_data, generate_data_warning
    print("✓ utils.data_validator模块导入成功")
    
    print("\n所有测试通过！修复成功！")
    
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
