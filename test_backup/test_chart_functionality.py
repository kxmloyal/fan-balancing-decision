#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图表功能测试脚本
用于验证重构后的图表功能模块在不同场景下的表现
"""

import json
import os
import time
import unittest
from unittest.mock import patch, MagicMock

import requests


class TestChartFunctionality(unittest.TestCase):
    """图表功能测试类"""

    def setUp(self):
        """设置测试环境"""
        self.base_url = "http://127.0.0.1:1324"
        self.test_data_dir = "tests"
        self.p1_test_file = os.path.join(self.test_data_dir, "test_p1_data.xlsx")
        self.p2_test_file = os.path.join(self.test_data_dir, "test_p2_data.xlsx")
        
    def test_server_connection(self):
        """测试服务器连接是否正常"""
        try:
            response = requests.get(self.base_url, timeout=10)
            self.assertEqual(response.status_code, 200)
            print("✓ 服务器连接测试通过")
        except requests.RequestException as e:
            self.fail(f"服务器连接失败: {e}")

    def test_chart_data_generation(self):
        """测试图表数据生成功能"""
        # 导入图表生成模块进行测试
        try:
            from chart_generation import generate_echarts_data
            
            # 测试数据
            test_data = [
                {"转速": "3000rpm", "不平衡量": 1.5},
                {"转速": "4000rpm", "不平衡量": 2.3},
                {"转速": "5000rpm", "不平衡量": 1.8},
                {"转速": "6000rpm", "不平衡量": 2.7},
            ]
            
            # 测试不同类型的图表数据生成
            chart_types = ["box", "scatter", "trend", "violin", "heatmap"]
            for chart_type in chart_types:
                result = generate_echarts_data(test_data, chart_type)
                self.assertIsInstance(result, list)
                print(f"✓ {chart_type} 图表数据生成测试通过")
                
        except ImportError as e:
            self.fail(f"导入图表生成模块失败: {e}")
        except Exception as e:
            self.fail(f"图表数据生成测试失败: {e}")

    def test_chart_data_validation(self):
        """测试图表数据验证功能"""
        # 由于数据验证功能在前端实现，这里跳过测试
        print("✓ 图表数据验证测试 (前端实现，跳过)")

    def test_responsive_design(self):
        """测试响应式设计功能"""
        # 由于响应式设计功能在前端实现，这里跳过测试
        print("✓ 响应式设计测试 (前端实现，跳过)")

    def test_performance_optimization(self):
        """测试性能优化功能"""
        # 测试大数据集处理
        try:
            from chart_generation import generate_echarts_data
            
            # 生成大数据集
            large_data = []
            for speed in ["3000rpm", "4000rpm", "5000rpm", "6000rpm", "7000rpm"]:
                for i in range(100):
                    large_data.append({"转速": speed, "不平衡量": i * 0.1})
            
            # 测试处理时间
            start_time = time.time()
            result = generate_echarts_data(large_data, "box")
            processing_time = time.time() - start_time
            
            self.assertIsInstance(result, list)
            self.assertLess(processing_time, 1.0)  # 处理时间应小于1秒
            print(f"✓ 大数据集处理测试通过，耗时: {processing_time:.2f}秒")
            
        except ImportError as e:
            self.fail(f"导入图表生成模块失败: {e}")
        except Exception as e:
            self.fail(f"性能优化测试失败: {e}")

    def test_error_handling(self):
        """测试错误处理功能"""
        # 测试异常数据处理
        try:
            from chart_generation import generate_echarts_data
            
            # 测试空数据
            empty_data = []
            result = generate_echarts_data(empty_data, "box")
            self.assertEqual(result, [])
            print("✓ 空数据处理测试通过")
            
            # 测试无效数据格式
            invalid_data = "not a list"
            result = generate_echarts_data(invalid_data, "box")
            self.assertEqual(result, [])
            print("✓ 无效数据格式处理测试通过")
            
        except ImportError as e:
            self.fail(f"导入图表生成模块失败: {e}")
        except Exception as e:
            self.fail(f"错误处理测试失败: {e}")


if __name__ == "__main__":
    print("开始图表功能测试...\n")
    unittest.main(verbosity=2)
    print("\n图表功能测试完成！")
