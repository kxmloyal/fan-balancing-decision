#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试报告导出功能中的图表显示
"""

import os
import json
from datetime import datetime
from report_export import report_exporter

# 测试数据
mock_session_data = {
    'fan_model': '测试型号',
    'stats_html': '<table><tr><th>转速</th><th>中位数</th></tr><tr><td>2500rpm</td><td>2.2</td></tr><tr><td>3000rpm</td><td>5.5</td></tr></table>',
    'evaluation_report': {
        'best_speeds': ['2500rpm'],
        'speed_detailed_scores': {
            '2500rpm': 0.95,
            '3000rpm': 0.85
        }
    },
    'plots': {
        'P1': {
            'box': {
                'png': 'test_p1_box.png',
                'html': 'test_p1_box.html',
                'chart_data': json.dumps([
                    {'name': '2500rpm', 'data': [1.1, 1.65, 2.2, 2.75, 3.3]},
                    {'name': '3000rpm', 'data': [4.4, 4.95, 5.5, 6.05, 6.6]}
                ]),
                'chart_properties': {
                    'surface_name': 'P1面',
                    'color': '#1f77b4',
                    'chart_type': 'box',
                    'output_prefix': 'test',
                    'output_folder': 'outputs',
                    'is_st_surface': False,
                    'sorted_speeds': ['2500rpm', '3000rpm'],
                    'median_values': [2.2, 5.5]
                }
            }
        }
    }
}

# 确保outputs目录存在
if not os.path.exists('outputs'):
    os.makedirs('outputs')

# 创建一个简单的测试PNG文件作为备份
with open('outputs/test_p1_box.png', 'w') as f:
    f.write('PNG placeholder')

# 测试HTML报告生成
print("测试HTML报告生成...")
try:
    html_content = report_exporter.build_report_html(mock_session_data)
    print("HTML报告生成成功！")
    
    # 保存HTML报告
    html_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    html_path = os.path.join('outputs', html_filename)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML报告保存到: {html_path}")
    
    # 检查HTML内容是否包含图表div
    if 'plotly-chart' in html_content:
        print("✓ HTML报告包含前端风格的图表div")
    else:
        print("✗ HTML报告不包含前端风格的图表div")
    
    if 'Plotly.newPlot' in html_content:
        print("✓ HTML报告包含图表初始化脚本")
    else:
        print("✗ HTML报告不包含图表初始化脚本")
        
except Exception as e:
    print(f"HTML报告生成失败: {e}")
    import traceback
    traceback.print_exc()

# 测试PDF报告生成
print("\n测试PDF报告生成...")
try:
    pdf_path = report_exporter.export_report_from_session(mock_session_data, f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    print(f"PDF报告生成成功！保存到: {pdf_path}")
except Exception as e:
    print(f"PDF报告生成失败: {e}")

print("\n测试完成！")
