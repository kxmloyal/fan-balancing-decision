import json
import os
import shutil
import tempfile
import unittest

from report_export import ReportExporter


class TestIntegration(unittest.TestCase):
    """
    集成测试（对齐当前 ReportExporter API）
    """

    def setUp(self):
        """
        测试前的设置
        """
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()

        # 初始化导出器（output_folder 指向临时目录，避免污染项目 outputs/）
        self.exporter = ReportExporter(output_folder=self.temp_dir)

        # 准备测试数据
        self.test_session_data = {
            "fan_model": "Integration Test Model",
            "evaluation_report": {
                "best_speeds": ["1500rpm"],
                "analysis_results": {
                    "surface1": {
                        "speeds": [1000, 1200, 1400, 1600, 1800, 2000],
                        "iqr_values": [0.5, 0.4, 0.3, 0.6, 0.8, 1.0],
                        "cv_values": [0.1, 0.08, 0.06, 0.12, 0.16, 0.2],
                    }
                },
            },
            "stats_html": """
            <table>
               
                <tr><th>转速</th><th>平均值</th><th>标准差</th><th>IQR</th><th>变异系数</th><th>综合评价</th></tr>
               
                <tr><td>1000</td><td>1.0</td><td>0.1</td><td>0.5</td><td>0.1</td><td>良好</td></tr>
               
                <tr><td>1200</td><td>0.9</td><td>0.08</td><td>0.4</td><td>0.08</td><td>良好</td></tr>
               
                <tr><td>1400</td><td>0.8</td><td>0.06</td><td>0.3</td><td>0.06</td><td>优秀</td></tr>
               
                <tr><td>1600</td><td>1.2</td><td>0.12</td><td>0.6</td><td>0.12</td><td>一般</td></tr>
               
                <tr><td>1800</td><td>1.5</td><td>0.16</td><td>0.8</td><td>0.16</td><td>较差</td></tr>
               
                <tr><td>2000</td><td>1.8</td><td>0.2</td><td>1.0</td><td>0.2</td><td>较差</td></tr>
            </table>
            """,
        }

    def tearDown(self):
        """
        测试后的清理
        """
        # 清理临时目录
        shutil.rmtree(self.temp_dir)

    def test_html_export(self):
        """
        测试HTML导出
        """
        try:
            # 导出HTML
            html_path = self.exporter.export(
                "html", self.test_session_data, "test_integration.html"
            )

            # 验证文件存在
            self.assertTrue(os.path.exists(html_path))
            self.assertTrue(html_path.endswith(".html"))

            # 验证文件大小
            self.assertTrue(os.path.getsize(html_path) > 0)

            # 验证文件内容
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("Integration Test Model", content)
                self.assertIn("1500rpm", content)
                self.assertIn("分析摘要", content)
                self.assertIn("统计分析结果", content)

            print(f"HTML导出测试成功: {html_path}")
        except Exception as e:  # 注意：捕获了过于宽泛的异常
            self.fail(f"HTML导出测试失败: {str(e)}")

    def test_csv_export(self):
        """
        测试CSV导出
        """
        try:
            # 补充转速详细得分数据（CSV 导出的数据源）
            session_data = dict(self.test_session_data)
            session_data["evaluation_report"]["speed_detailed_scores"] = {
                "1500rpm": {
                    "P1": {"iqr": 0.3, "cv": 5.2, "face_score": 0.9},
                    "P2": {"iqr": 0.4, "cv": 6.1, "face_score": 0.85},
                    "total_score": 0.88,
                }
            }

            # 导出CSV
            csv_path = self.exporter.export("csv", session_data, "test_integration.csv")

            # 验证文件存在
            self.assertTrue(os.path.exists(csv_path))
            self.assertTrue(csv_path.endswith(".csv"))

            # 验证文件大小
            self.assertTrue(os.path.getsize(csv_path) > 0)

            # 验证文件内容
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                content = f.read()
                self.assertIn("转速", content)
                self.assertIn("1500rpm", content)
                self.assertIn("综合得分", content)
                self.assertIn("0.88", content)

            print(f"CSV导出测试成功: {csv_path}")
        except Exception as e:  # 注意：捕获了过于宽泛的异常
            self.fail(f"CSV导出测试失败: {str(e)}")

    def test_json_export(self):
        """
        测试JSON导出
        """
        try:
            # 导出JSON
            json_path = self.exporter.export(
                "json", self.test_session_data, "test_integration.json"
            )

            # 验证文件存在
            self.assertTrue(os.path.exists(json_path))
            self.assertTrue(json_path.endswith(".json"))

            # 验证文件大小
            self.assertTrue(os.path.getsize(json_path) > 0)

            # 验证文件内容
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertIsInstance(data, dict)
                self.assertIn("fan_model", data)
                self.assertEqual(data["fan_model"], "Integration Test Model")
                self.assertIn("evaluation_report", data)

            print(f"JSON导出测试成功: {json_path}")
        except Exception as e:  # 注意：捕获了过于宽泛的异常
            self.fail(f"JSON导出测试失败: {str(e)}")

    def test_report_customization(self):
        """
        测试报告定制化（report_config 章节开关）
        """
        try:
            # 定义自定义配置（当前渲染器支持的 include_* 开关）
            custom_config = {
                "include_summary": True,
                "include_stats": True,
                "include_charts": False,  # 不包含图表
                "include_methodology": False,  # 不包含方法说明
                "chart_layout": "stacked",
            }

            # 携带图表数据，验证 include_charts=False 时确实不渲染图表章节
            session_data = dict(self.test_session_data)
            session_data["plots"] = {"p1": {"box": {"png": "", "chart_data": "[]"}}}

            # 导出自定义报告
            html_path = self.exporter.export(
                "html", session_data, "custom_report.html", report_config=custom_config
            )

            # 验证文件存在
            self.assertTrue(os.path.exists(html_path))
            self.assertTrue(os.path.getsize(html_path) > 0)

            # 验证章节开关生效
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("一、分析摘要", content)  # include_summary=True
                self.assertNotIn("四、数据图表", content)  # include_charts=False
                self.assertNotIn("五、统计分析方法", content)  # include_methodology=False

            print(f"报告定制化测试成功: {html_path}")
        except Exception as e:  # 注意：捕获了过于宽泛的异常
            self.fail(f"报告定制化测试失败: {str(e)}")


if __name__ == "__main__":
    unittest.main()
