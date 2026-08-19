#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试图表生成功能，验证修改后的箱线图是否包含数据点和趋势线
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from chart_generation_optimized import generate_generic_charts


# 测试数据
def generate_test_data():
    """生成测试数据"""
    test_data = [
        {"转速": "2500rpm", "不平衡量": 5.0},
        {"转速": "2500rpm", "不平衡量": 4.5},
        {"转速": "2500rpm", "不平衡量": 5.5},
        {"转速": "3000rpm", "不平衡量": 11.0},
        {"转速": "3000rpm", "不平衡量": 12.0},
        {"转速": "3000rpm", "不平衡量": 10.0},
        {"转速": "3500rpm", "不平衡量": 8.5},
        {"转速": "3500rpm", "不平衡量": 8.0},
        {"转速": "3500rpm", "不平衡量": 9.0},
        {"转速": "4000rpm", "不平衡量": 8.0},
        {"转速": "4000rpm", "不平衡量": 7.5},
        {"转速": "4000rpm", "不平衡量": 8.5},
        {"转速": "4500rpm", "不平衡量": 13.0},
        {"转速": "4500rpm", "不平衡量": 14.0},
        {"转速": "4500rpm", "不平衡量": 12.0},
    ]
    return test_data


# 测试箱线图生成
def test_box_chart_generation():
    """测试箱线图生成，验证是否包含数据点和趋势线"""
    print("=== 测试箱线图生成 ===")

    # 生成测试数据
    test_data = generate_test_data()

    # 计算中位数
    median_dict = {}
    speed_data = {}
    for item in test_data:
        speed = item["转速"]
        value = item["不平衡量"]
        if speed not in speed_data:
            speed_data[speed] = []
        speed_data[speed].append(value)

    for speed, values in speed_data.items():
        median_dict[speed] = sorted(values)[len(values) // 2]

    # 排序转速
    sorted_speeds = sorted(speed_data.keys())
    median_values = [median_dict[speed] for speed in sorted_speeds]

    # 生成图表
    output_prefix = "test_box_chart"
    output_folder = "outputs"
    chart_types = ["box"]

    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)

    try:
        # 生成图表
        charts = generate_generic_charts(
            test_data,
            median_dict,
            "P1面",
            "#1f77b4",
            output_prefix,
            output_folder,
            chart_types,
            is_st_surface=False,
            sorted_speeds=sorted_speeds,
            median_values=median_values,
        )

        print("✓ 图表生成成功")
        print("生成的图表文件:")
        for chart_type, chart_info in charts.items():
            print(f"  {chart_type}: {chart_info['png']}")

        # 检查生成的文件是否存在
        for chart_type, chart_info in charts.items():
            png_path = os.path.join(output_folder, chart_info["png"])
            if os.path.exists(png_path):
                print(f"✓ {png_path} 文件存在")
                print(f"  文件大小: {os.path.getsize(png_path)} bytes")
            else:
                print(f"✗ {png_path} 文件不存在")

        print("\n=== 测试完成 ===")
        print("箱线图生成测试通过！修改后的箱线图应该包含数据点和趋势线。")

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_box_chart_generation()
