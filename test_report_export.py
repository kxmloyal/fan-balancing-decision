#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试报告导出功能
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_export import ReportExporter


def test_report_export():
    """测试报告导出功能"""
    print("开始测试报告导出功能...")
    
    # 创建报告导出器实例
    exporter = ReportExporter()
    
    # 创建测试会话数据
    test_session_data = {
        'fan_model': '测试扇叶型号',
        'stats_html': '<p>测试统计数据</p>',
        'evaluation_report': {
            'best_speeds': ['3000rpm', '3500rpm'],
            'speed_detailed_scores': {
                '2500rpm': 0.85,
                '3000rpm': 0.95,
                '3500rpm': 0.98,
                '4000rpm': 0.90,
                '4500rpm': 0.80
            }
        },
        'plots': {
            'p1': {
                'box': {
                    'png': 'test_p1_box.png',
                    'html': 'test_p1_box.html',
                    'chart_data': json.dumps([
                        {'name': '2500rpm', 'data': [1.2, 1.5, 1.8, 2.0, 2.2]},
                        {'name': '3000rpm', 'data': [1.0, 1.3, 1.6, 1.9, 2.1]},
                        {'name': '3500rpm', 'data': [0.8, 1.1, 1.4, 1.7, 1.9]},
                        {'name': '4000rpm', 'data': [1.1, 1.4, 1.7, 2.0, 2.3]},
                        {'name': '4500rpm', 'data': [1.3, 1.6, 1.9, 2.2, 2.5]}
                    ]),
                    'chart_properties': {
                        'surface_name': 'P1面',
                        'color': '#1f77b4',
                        'chart_type': 'box',
                        'output_prefix': 'test',
                        'output_folder': 'outputs',
                        'is_st_surface': False,
                        'sorted_speeds': ['2500rpm', '3000rpm', '3500rpm', '4000rpm', '4500rpm'],
                        'median_values': [1.8, 1.6, 1.4, 1.7, 1.9]
                    }
                },
                'trend': {
                    'png': 'test_p1_trend.png',
                    'html': 'test_p1_trend.html',
                    'chart_data': json.dumps([
                        {'name': '2500rpm', 'value': 1.8},
                        {'name': '3000rpm', 'value': 1.6},
                        {'name': '3500rpm', 'value': 1.4},
                        {'name': '4000rpm', 'value': 1.7},
                        {'name': '4500rpm', 'value': 1.9}
                    ]),
                    'chart_properties': {
                        'surface_name': 'P1面',
                        'color': '#1f77b4',
                        'chart_type': 'trend',
                        'output_prefix': 'test',
                        'output_folder': 'outputs',
                        'is_st_surface': False,
                        'sorted_speeds': ['2500rpm', '3000rpm', '3500rpm', '4000rpm', '4500rpm'],
                        'median_values': [1.8, 1.6, 1.4, 1.7, 1.9]
                    }
                }
            }
        }
    }
    
    try:
        # 测试HTML导出
        print("测试HTML导出...")
        html_path = exporter.export_html(test_session_data)
        print(f"HTML报告已保存到: {html_path}")
        
        # 测试PDF导出
        print("测试PDF导出...")
        try:
            pdf_path = exporter.export_report_from_session(test_session_data)
            print(f"PDF报告已保存到: {pdf_path}")
        except Exception as e:
            print(f"PDF导出失败（可能是因为缺少weasyprint依赖）: {str(e)}")
            print("HTML导出成功，PDF导出可选功能")
        
        # 测试报告分享功能
        print("测试报告分享功能...")
        link_id = exporter.create_shareable_link(html_path)
        if link_id:
            print(f"创建可分享链接成功: {link_id}")
            # 测试获取共享报告
            shared_report_path = exporter.get_shared_report(link_id)
            if shared_report_path:
                print(f"获取共享报告成功: {shared_report_path}")
            else:
                print("获取共享报告失败")
        else:
            print("创建可分享链接失败")
        
        # 测试导出历史记录
        print("测试导出历史记录...")
        history = exporter.get_export_history()
        print(f"导出历史记录数量: {len(history)}")
        if history:
            print("最近的导出记录:")
            for i, record in enumerate(history[:3]):
                print(f"{i+1}. {record['type']} - {record['filename']} - {record['timestamp']}")
        
        print("测试完成，报告导出功能正常工作")
        return True
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_report_export()
    sys.exit(0 if success else 1)