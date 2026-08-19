#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试报告分享链接功能
"""

import os

from report_exporter_extension import ReportExporter

# 测试数据
test_data = {
    "fan_model": "测试扇叶型号",
    "evaluation_report": {"best_speeds": ["3000rpm", "4000rpm"]},
    "stats_html": "<table><tr><th>转速</th><th>不平衡量</th></tr><tr><td>3000rpm</td><td>10.5</td></tr><tr><td>4000rpm</td><td>8.2</td></tr></table>",
    "plots": {
        "P1面": {
            "box": {
                "chart_data": [
                    {"name": "3000rpm", "data": [5, 8, 10, 12, 15]},
                    {"name": "4000rpm", "data": [3, 6, 9, 11, 14]},
                ],
                "chart_properties": {"surface_name": "P1面", "color": "#1f77b4"},
            }
        }
    },
}

# 测试配置
test_config = {
    "title": "设备不平衡量分析报告",
    "include_summary": True,
    "include_stats": True,
    "include_charts": True,
    "include_methodology": True,
    "include_recommendations": True,
    "chart_types": ["box"],
}


def test_shareable_link():
    """测试可分享链接功能"""
    print("开始测试可分享链接功能...")
    try:
        # 初始化报告导出器
        exporter = ReportExporter(output_folder="outputs")

        # 导出报告
        report_path = exporter.export(test_data, "html", test_config)
        print(f"报告导出成功：{report_path}")
        print(f"报告文件存在：{os.path.exists(report_path)}")

        # 创建可分享链接
        shareable_link = exporter.create_shareable_link(report_path)
        print(f"可分享链接生成成功：{shareable_link}")
        print(f"可分享链接非空：{bool(shareable_link)}")

        # 验证分享链接文件是否创建
        shareable_links_file = os.path.join("outputs", "shareable_links.json")
        print(f"分享链接文件存在：{os.path.exists(shareable_links_file)}")

        if os.path.exists(shareable_links_file):
            import json

            with open(shareable_links_file, "r", encoding="utf-8") as f:
                links = json.load(f)
            print(f"分享链接文件包含 {len(links)} 个链接")

        print("✓ 可分享链接功能测试通过")
        return True
    except Exception as e:
        print(f"测试失败：{str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs("outputs", exist_ok=True)

    # 运行测试
    test_passed = test_shareable_link()

    # 总结测试结果
    print("\n测试总结：")
    if test_passed:
        print("✓ 可分享链接功能测试通过！")
    else:
        print("✗ 可分享链接功能测试失败，需要进一步检查。")
