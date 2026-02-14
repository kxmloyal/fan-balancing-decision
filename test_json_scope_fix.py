#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试json模块作用域修复
"""

import sys
import os
from report_export import ReportExporter

# 创建测试会话数据
test_session_data = {
    'fan_model': '测试型号',
    'stats_html': '<table><tr><th>转速</th><th>平均值</th></tr><tr><td>1000</td><td>0.5</td></tr></table>',
    'plots': {
        'p1': {
            'box': {
                'png': 'test_chart.png',
                'chart_data': '[{"name": "测试", "data": [1, 2, 3]}]',
                'chart_properties': {
                    'surface_name': 'P1',
                    'color': '#1f77b4',
                    'chart_type': 'box'
                }
            }
        }
    }
}

def test_report_export():
    """
    测试报告导出功能
    """
    try:
        # 创建报告导出器实例
        exporter = ReportExporter()
        
        # 测试构建HTML报告
        print("测试构建HTML报告...")
        html_content = exporter.build_report_html(test_session_data)
        print("✓ HTML报告构建成功")
        
        # 验证HTML内容包含预期的图表属性
        if '图表属性' in html_content:
            print("✓ HTML报告包含图表属性")
        else:
            print("✗ HTML报告不包含图表属性")
        
        # 验证JSON数据正确嵌入
        if 'chart_properties' in html_content:
            print("✓ JSON数据正确嵌入")
        else:
            print("✗ JSON数据未正确嵌入")
        
        print("\n测试完成！json模块作用域问题已修复。")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试json模块作用域修复...\n")
    success = test_report_export()
    sys.exit(0 if success else 1)
