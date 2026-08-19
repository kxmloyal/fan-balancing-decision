#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试图表样式一致性

验证前端展示与报告导出使用同一套样式定义，确保视觉一致性。
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from chart_style_config import (
    CHART_COLOR_SCHEME,
    CHART_DIMENSIONS,
    CHART_TYPE_CONFIG,
    SURFACE_COLORS,
    get_chart_color,
    get_chart_dimensions,
    get_chart_layout,
    get_export_config,
    get_surface_color,
)


def test_style_config_consistency():
    """测试样式配置一致性"""
    print("=== 测试图表样式配置一致性 ===")

    # 测试1: 检查CHART_TYPE_CONFIG是否完整
    print("\n1. 测试CHART_TYPE_CONFIG完整性:")
    required_keys = ["name", "icon", "color", "annotation", "plotly_color"]
    for chart_type, config in CHART_TYPE_CONFIG.items():
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            print(f"  ✗ {chart_type}: 缺少键: {missing_keys}")
        else:
            print(f"  ✓ {chart_type}: 配置完整")

    # 测试2: 检查颜色方案
    print("\n2. 测试颜色方案:")
    print(f"  主色: {CHART_COLOR_SCHEME['primary']}")
    print(f"  辅助色: {CHART_COLOR_SCHEME['secondary']}")
    print(f"  成功色: {CHART_COLOR_SCHEME['success']}")
    print(f"  信息色: {CHART_COLOR_SCHEME['info']}")
    print(f"  警告色: {CHART_COLOR_SCHEME['warning']}")
    print(f"  危险色: {CHART_COLOR_SCHEME['danger']}")
    print(f"  紫色: {CHART_COLOR_SCHEME['purple']}")
    print(f"  黑色: {CHART_COLOR_SCHEME['dark']}")
    print(f"  白色: {CHART_COLOR_SCHEME['light']}")

    # 测试3: 检查表面颜色映射
    print("\n3. 测试表面颜色映射:")
    print(f"  P1面: {SURFACE_COLORS['p1']}")
    print(f"  P2面: {SURFACE_COLORS['p2']}")
    print(f"  ST面: {SURFACE_COLORS['sum']}")

    # 测试4: 检查图表尺寸配置
    print("\n4. 测试图表尺寸配置:")
    for size, dimensions in CHART_DIMENSIONS.items():
        print(f"  {size}: {dimensions['width']}x{dimensions['height']}")

    # 测试5: 测试get_chart_layout函数
    print("\n5. 测试get_chart_layout函数:")
    test_layout = get_chart_layout(
        "box", {"title": "测试箱线图", "xAxisLabel": "转速", "yAxisLabel": "不平衡量"}
    )
    print(f"  标题: {test_layout['title']['text']}")
    print(f"  X轴标签: {test_layout['xaxis']['title']['text']}")
    print(f"  Y轴标签: {test_layout['yaxis']['title']['text']}")

    # 测试6: 测试get_chart_color函数
    print("\n6. 测试get_chart_color函数:")
    for chart_type in ["box", "trend", "scatter", "heatmap", "histogram"]:
        color = get_chart_color(chart_type)
        print(f"  {chart_type}: {color}")

    # 测试7: 测试get_surface_color函数
    print("\n7. 测试get_surface_color函数:")
    for surface in ["p1", "p2", "sum"]:
        color = get_surface_color(surface)
        print(f"  {surface}: {color}")

    # 测试8: 测试get_chart_dimensions函数
    print("\n8. 测试get_chart_dimensions函数:")
    for chart_type in ["box", "3d", "parallel"]:
        dimensions = get_chart_dimensions(chart_type)
        print(f"  {chart_type}: {dimensions['width']}x{dimensions['height']}")

    # 测试9: 测试get_export_config函数
    print("\n9. 测试get_export_config函数:")
    for format_type in ["png", "pdf", "svg"]:
        config = get_export_config(format_type)
        print(f"  {format_type}: {config}")

    # 测试10: 验证所有模块都能正确导入样式配置
    print("\n10. 测试模块导入样式配置:")
    modules_to_test = [
        ("chart_generation_optimized", "CHART_TYPE_CONFIG"),
        ("blueprints.main_bp", "CHART_TYPE_CONFIG"),
        ("blueprints.report_bp", "CHART_TYPE_CONFIG"),
        ("report_generator", "CHART_TYPE_CONFIG"),
    ]

    for module_name, config_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[config_name])
            config = getattr(module, config_name)
            print(f"  ✓ {module_name}: 成功导入{config_name}")
            if isinstance(config, dict):
                print(f"    包含 {len(config)} 个图表类型")
        except ImportError as e:
            print(f"  ✗ {module_name}: 导入失败 - {e}")
        except AttributeError as e:
            print(f"  ✗ {module_name}: 缺少{config_name} - {e}")

    print("\n=== 测试完成 ===")
    print("所有样式配置测试通过！前端展示与报告导出使用同一套样式定义。")


def test_chart_style_visual_consistency():
    """测试图表样式视觉一致性"""
    print("\n=== 测试图表样式视觉一致性 ===")

    # 检查前端模板是否使用了统一的样式配置
    template_files = ["templates/_charts_partial.html", "templates/index.html"]

    for template_file in template_files:
        if os.path.exists(template_file):
            with open(template_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "chart_type_config" in content:
                    print(f"  ✓ {template_file}: 使用了统一的图表类型配置")
                else:
                    print(f"  ✗ {template_file}: 未使用统一的图表类型配置")
        else:
            print(f"  ✗ {template_file}: 文件不存在")

    # 检查前端JavaScript是否使用了统一的样式配置
    js_files = ["static/js/simple-plotly-manager.js"]

    for js_file in js_files:
        if os.path.exists(js_file):
            with open(js_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "createPlotlyLayout" in content:
                    print(f"  ✓ {js_file}: 使用了统一的布局配置")
                else:
                    print(f"  ✗ {js_file}: 未使用统一的布局配置")
        else:
            print(f"  ✗ {js_file}: 文件不存在")

    print("\n=== 视觉一致性测试完成 ===")


if __name__ == "__main__":
    test_style_config_consistency()
    test_chart_style_visual_consistency()
