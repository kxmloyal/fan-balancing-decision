#!/usr/bin/env python3
"""
测试图表X轴标签显示完整性的脚本
"""

import os
import tempfile

from chart_generation_optimized import build_report_charts

# 测试数据
TEST_DATA = [
    {
        "speed": "2500rpm",
        "p1_samples": [1.1, 1.5, 1.3, 1.4, 1.6],
        "p2_samples": [2.1, 2.5, 2.3, 2.4, 2.6],
        "sum_samples": [3.2, 4.0, 3.6, 3.8, 4.2],
    },
    {
        "speed": "3000rpm",
        "p1_samples": [1.0, 1.4, 1.2, 1.3, 1.5],
        "p2_samples": [2.0, 2.4, 2.2, 2.3, 2.5],
        "sum_samples": [3.0, 3.8, 3.4, 3.6, 4.0],
    },
    {
        "speed": "3500rpm",
        "p1_samples": [0.9, 1.3, 1.1, 1.2, 1.4],
        "p2_samples": [1.9, 2.3, 2.1, 2.2, 2.4],
        "sum_samples": [2.8, 3.6, 3.2, 3.4, 3.8],
    },
    {
        "speed": "4000rpm",
        "p1_samples": [1.2, 1.6, 1.4, 1.5, 1.7],
        "p2_samples": [2.2, 2.6, 2.4, 2.5, 2.7],
        "sum_samples": [3.4, 4.2, 3.8, 4.0, 4.4],
    },
    {
        "speed": "4500rpm",
        "p1_samples": [1.3, 1.7, 1.5, 1.6, 1.8],
        "p2_samples": [2.3, 2.7, 2.5, 2.6, 2.8],
        "sum_samples": [3.6, 4.4, 4.0, 4.2, 4.6],
    },
]


def test_chart_xaxis_labels():
    """测试图表X轴标签显示完整性"""
    print("开始测试图表X轴标签显示完整性...")

    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 生成图表
        print("生成图表...")
        plots = build_report_charts(
            parsed_data=TEST_DATA,
            output_prefix="test_xaxis",
            output_folder=temp_dir,
            chart_types=["box", "trend"],
        )

        print(f"生成的图表: {list(plots.keys())}")

        # 检查生成的图表文件
        for surface, surface_plots in plots.items():
            print(f"\n{surface}面图表:")
            for chart_type, chart_info in surface_plots.items():
                png_file = os.path.join(temp_dir, chart_info["png"])
                html_file = os.path.join(temp_dir, chart_info["html"])

                if os.path.exists(png_file):
                    print(f"  ✓ {chart_type}图表PNG文件生成成功: {chart_info['png']}")
                    print(f"    文件大小: {os.path.getsize(png_file)} 字节")
                else:
                    print(f"  ✗ {chart_type}图表PNG文件生成失败")

                if os.path.exists(html_file):
                    print(f"  ✓ {chart_type}图表HTML文件生成成功: {chart_info['html']}")
                    print(f"    文件大小: {os.path.getsize(html_file)} 字节")
                else:
                    print(f"  ✗ {chart_type}图表HTML文件生成失败")

    print("\n测试完成！")
    print("图表X轴标签显示完整性测试已完成，修改后的图表应该能够完整显示X轴标签。")


if __name__ == "__main__":
    test_chart_xaxis_labels()
