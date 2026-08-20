import os
import shutil
import tempfile
import unittest

from report_export import ReportExporter


class TestReportExporter(unittest.TestCase):
    """
    报告导出器单元测试（对齐当前 ReportExporter API）
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
            "fan_model": "Test Model",
            "evaluation_report": {"best_speeds": ["1500rpm"], "analysis_results": {}},
            "stats_html": "<table><tr><th>Speed</th><th>Value</th></tr><tr><td>1000</td><td>1.0</td></tr></table>",
        }

    def tearDown(self):
        """
        测试后的清理
        """
        # 清理临时目录
        shutil.rmtree(self.temp_dir)

    def test_init(self):
        """
        测试初始化功能
        """
        self.assertIsInstance(self.exporter, ReportExporter)
        self.assertEqual(self.exporter.output_folder, self.temp_dir)
        self.assertIsNotNone(self.exporter.exporters)
        self.assertIn("html", self.exporter.exporters)
        # 核心导出接口
        self.assertTrue(hasattr(self.exporter, "export"))
        self.assertTrue(hasattr(self.exporter, "export_html"))
        # PDF 由 export_report_from_session 派生（weasyprint 可用时）
        self.assertTrue(hasattr(self.exporter, "export_report_from_session"))
        # CSV/JSON/Excel 由 data_exporter 分发
        self.assertTrue(hasattr(self.exporter, "data_exporter"))

    def test_report_config_operations(self):
        """
        测试报告配置操作
        """
        # 测试获取默认配置
        default_config = self.exporter.default_report_config
        self.assertIsInstance(default_config, dict)
        self.assertIn("title", default_config)
        self.assertEqual(default_config["title"], "设备不平衡量分析报告")

        # 测试合并配置：用户配置覆盖默认值，未指定项保持默认
        user_config = {"title": "Merged Report", "include_summary": False}
        merged_config = self.exporter._merge_report_config(user_config)
        self.assertEqual(merged_config["title"], "Merged Report")
        self.assertEqual(merged_config["include_summary"], False)
        self.assertTrue(merged_config["include_stats"])

        # report_config 经 export_html 透传生效：include_charts=False 时不渲染图表章节
        session_data = dict(self.test_session_data)
        session_data["plots"] = {"p1": {"box": {"png": "", "chart_data": "[]"}}}
        html_path = self.exporter.export_html(
            session_data, "config_test.html", report_config={"include_charts": False}
        )
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("一、分析摘要", content)
        self.assertNotIn("四、数据图表", content)

    def test_history_operations(self):
        """
        测试历史记录操作
        """
        # 测试添加历史记录
        export_info = {
            "type": "html",
            "filename": "test.html",
            "path": os.path.join(self.temp_dir, "test.html"),
            "fan_model": "Test Model",
        }
        self.exporter.add_to_history(export_info)

        # 测试获取历史记录
        history = self.exporter.export_history
        self.assertIsInstance(history, list)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["fan_model"], "Test Model")
        self.assertIn("timestamp", history[0])

        # 测试历史记录持久化：保存后重新加载
        self.exporter.save_export_history()
        self.exporter.export_history = []
        self.exporter.load_export_history()
        self.assertEqual(len(self.exporter.export_history), 1)
        self.assertEqual(self.exporter.export_history[0]["filename"], "test.html")

    def test_export_method(self):
        """
        测试通用导出方法
        """
        # 测试导出方法是否存在
        self.assertTrue(hasattr(self.exporter, "export"))

        # 测试不支持的导出类型
        with self.assertRaises(ValueError):
            self.exporter.export("unsupported", self.test_session_data)

    def test_csv_export_empty_stats_raises(self):
        """
        无统计数据时 CSV 导出必须抛 ValueError（此前返回不存在的文件路径导致 404）
        """
        empty_data = {"fan_model": "Test Model"}
        with self.assertRaises(ValueError) as ctx:
            self.exporter.export("csv", empty_data)
        self.assertIn("暂无统计数据", str(ctx.exception))

    def test_sanitize_model_name_dot(self):
        """
        型号名为 "." / ".." / 点开头时归入"未分类"，防止 os.path.join 写出 outputs 之外
        """
        from utils.model_utils import sanitize_model_name

        self.assertEqual(sanitize_model_name(".."), "未分类")
        self.assertEqual(sanitize_model_name("."), "未分类")
        self.assertEqual(sanitize_model_name(".hidden"), "未分类")
        # 正常含点型号不受影响
        self.assertEqual(sanitize_model_name("P1.2"), "P1.2")
        self.assertEqual(sanitize_model_name("SN300-12"), "SN300-12")

    def test_pdf_report_config_passthrough(self):
        """
        export_report_from_session 必须透传 report_config（此前 PDF 分支丢失 include_charts 配置）
        """
        from config import WEASYPRINT_AVAILABLE

        session_data = dict(self.test_session_data)
        session_data["plots"] = {"p1": {"box": {"png": "", "chart_data": "[]"}}}
        result = self.exporter.export_report_from_session(
            session_data, report_config={"include_charts": False}
        )
        self.assertTrue(os.path.exists(result))
        if WEASYPRINT_AVAILABLE:
            self.assertTrue(result.endswith(".pdf"))
        else:
            self.assertTrue(result.endswith(".html"))
            with open(result, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn("四、数据图表", content)

    def test_shareable_links(self):
        """
        测试可分享链接功能
        """
        # 创建临时文件用于测试
        test_file = os.path.join(self.temp_dir, "test.html")
        with open(test_file, "w") as f:
            f.write("<html><body>Test</body></html>")

        # 测试创建可分享链接（默认有效期）
        link_id = self.exporter.create_shareable_link(test_file)
        self.assertIsInstance(link_id, str)

        # 测试通过链接管理器查询
        link = self.exporter.share_link_manager.get_link(link_id)
        self.assertIsNotNone(link)
        self.assertEqual(link["report_path"], test_file)

        # 测试获取不存在的链接
        invalid_link = self.exporter.share_link_manager.get_link("invalid_link")
        self.assertIsNone(invalid_link)


if __name__ == "__main__":
    unittest.main()
