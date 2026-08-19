#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导出功能测试脚本
测试所有导出格式的完整性、准确性和可靠性
"""

import os
import tempfile

from report_exporter_extension import ReportExporter


def test_export_formats():
    """测试所有导出格式"""
    print("=== 导出功能测试 ===")

    # 创建临时输出目录
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"使用临时输出目录: {temp_dir}")

        # 初始化报告导出器
        exporter = ReportExporter(output_folder=temp_dir)

        # 测试数据
        test_data = {
            "fan_model": "测试扇叶",
            "evaluation_report": {
                "best_speeds": ["3000rpm"],
                "speed_detailed_scores": {
                    "3000rpm": {
                        "P1": {"face_score": 0.95},
                        "P2": {"face_score": 0.92},
                        "ST": {"face_score": 0.90},
                        "total_score": 0.93,
                    }
                },
            },
            "parsed_data": [],
            "statistics_data": [],
        }

        # 测试导出格式
        export_formats = ["html", "csv", "json", "excel"]

        for format_name in export_formats:
            print(f"\n测试 {format_name.upper()} 导出...")
            try:
                result = exporter.export(format_name, test_data)
                print(f"  ✓ 导出成功: {result}")
                print(f"  ✓ 文件大小: {os.path.getsize(result)} bytes")

                # 验证文件存在
                if os.path.exists(result):
                    print("  ✓ 文件存在")
                else:
                    print("  ✗ 文件不存在")

            except Exception as e:
                print(f"  ✗ 导出失败: {str(e)}")

        # 测试PDF导出
        print("\n测试 PDF 导出...")
        try:
            result = exporter.export_report_from_session(test_data)
            print(f"  ✓ PDF导出成功: {result}")
            if os.path.exists(result):
                print("  ✓ 文件存在")
                print(f"  ✓ 文件大小: {os.path.getsize(result)} bytes")
            else:
                print("  ✗ 文件不存在")
        except Exception as e:
            print(f"  ✗ PDF导出失败: {str(e)}")

        # 测试HTML导出（单独测试）
        print("\n测试 HTML 导出（单独方法）...")
        try:
            result = exporter.export_html(test_data)
            print(f"  ✓ HTML导出成功: {result}")
            if os.path.exists(result):
                print("  ✓ 文件存在")
                print(f"  ✓ 文件大小: {os.path.getsize(result)} bytes")
            else:
                print("  ✗ 文件不存在")
        except Exception as e:
            print(f"  ✗ HTML导出失败: {str(e)}")

        # 测试文件数量
        output_files = os.listdir(temp_dir)
        print(f"\n输出目录文件数量: {len(output_files)}")
        for file_name in output_files[:10]:  # 显示前10个文件
            print(f"  - {file_name}")
        if len(output_files) > 10:
            print(f"  ... 还有 {len(output_files) - 10} 个文件")


def test_error_handling():
    """测试错误处理机制"""
    print("\n=== 错误处理测试 ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = ReportExporter(output_folder=temp_dir)

        # 测试无效格式
        print("测试无效导出格式...")
        try:
            exporter.export("invalid_format", {})
            print("  ✗ 应该抛出异常")
        except Exception as e:
            print(f"  ✓ 正确抛出异常: {str(e)}")

        # 测试空数据
        print("测试空数据导出...")
        try:
            result = exporter.export("html", {})
            print(f"  ✓ 空数据导出成功: {result}")
        except Exception as e:
            print(f"  ✗ 空数据导出失败: {str(e)}")


def test_performance():
    """测试性能表现"""
    print("\n=== 性能测试 ===")

    import time

    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = ReportExporter(output_folder=temp_dir)

        # 生成大量数据
        large_data = {
            "fan_model": "测试扇叶",
            "evaluation_report": {"best_speeds": ["3000rpm"], "speed_detailed_scores": {}},
        }

        # 添加100个转速数据
        for i in range(100):
            speed = f"{1000 + i * 50}rpm"
            large_data["evaluation_report"]["speed_detailed_scores"][speed] = {
                "P1": {"face_score": 0.9 + i / 1000},
                "P2": {"face_score": 0.88 + i / 1000},
                "ST": {"face_score": 0.85 + i / 1000},
                "total_score": 0.88 + i / 1000,
            }

        # 测试HTML导出性能
        print("测试HTML导出性能（100个转速）...")
        start_time = time.time()
        try:
            result = exporter.export("html", large_data)
            end_time = time.time()
            print(f"  ✓ 导出成功，耗时: {end_time - start_time:.2f} 秒")
            print(f"  ✓ 文件大小: {os.path.getsize(result)} bytes")
        except Exception as e:
            print(f"  ✗ 导出失败: {str(e)}")


if __name__ == "__main__":
    test_export_formats()
    test_error_handling()
    test_performance()
    print("\n=== 测试完成 ===")
