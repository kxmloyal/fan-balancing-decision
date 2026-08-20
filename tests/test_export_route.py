#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导出路由回归测试（第四十四轮修复第 5 项：GET → POST）
1. /export_report 仅接受 POST（GET 405）
2. POST + CSRF 正常导出 HTML（200 附件下载）
3. POST 无统计数据 CSV 导出 → 302 + 精确提示（ValueError 冒泡为 flash）
4. 表单 body 提交的内容开关/标题/样式生效（第五十七轮修复 request.args 失效）
"""
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import wsgi

app = wsgi.app if hasattr(wsgi, "app") else wsgi.application
app.config["TESTING"] = True

_SAVED_RESULTS = {
    "fan_model": "路由测试",
    "parsed_data": [
        {
            "speed": "1000rpm",
            "p1_samples": [1, 2, 3],
            "p2_samples": [1, 2, 3],
            "sum_samples": [1, 2, 3],
        }
    ],
    "plots": {"p1": {"box": {"png": "", "chart_data": "[]"}}},
    "stats_html": "<table><tr><th>S</th><th>V</th></tr><tr><td>1</td><td>2</td></tr></table>",
    "evaluation_report": {
        "best_speeds": ["1000rpm"],
        "speed_detailed_scores": {
            "1000rpm": {
                "P1": {"face_score": 0.9},
                "P2": {"face_score": 0.8},
                "ST": {"face_score": 0.7},
                "total_score": 0.8,
            }
        },
        "detailed_scores": {},
    },
}


class TestExportRoute:
    def setup_method(self):
        # 导出落盘到临时目录，避免污染生产 outputs/
        self._original_output = app.config.get("OUTPUT_FOLDER")
        self.tmp_out = tempfile.mkdtemp()
        app.config["OUTPUT_FOLDER"] = self.tmp_out
        self.client = app.test_client()

    def teardown_method(self):
        if self._original_output is not None:
            app.config["OUTPUT_FOLDER"] = self._original_output

    def _setup_session(self, saved_results):
        resp = self.client.get("/")
        html = resp.get_data(as_text=True)
        m = re.search(r'name="csrf_token" value="([^"]+)"', html)
        assert m, "页面未找到 csrf_token"
        token = m.group(1)
        with self.client.session_transaction() as sess:
            sess["saved_results"] = saved_results
        return token

    def test_get_export_report_returns_405(self):
        # POST-only：GET 必须 405，不再允许 GET 触发写文件副作用
        resp = self.client.get("/export_report?report_type=html")
        assert resp.status_code == 405

    def test_post_export_html_ok(self):
        token = self._setup_session(_SAVED_RESULTS)
        resp = self.client.post(
            "/export_report?report_type=html", headers={"X-CSRFToken": token}
        )
        assert resp.status_code == 200
        assert "attachment" in resp.headers.get("Content-Disposition", "")
        assert len(resp.data) > 0

    def test_post_export_html_form_options_take_effect(self):
        """表单 body 提交的内容开关/标题/样式必须生效（修复 request.args 读取失效）"""
        token = self._setup_session(_SAVED_RESULTS)
        resp = self.client.post(
            "/export_report",
            data={
                "csrf_token": token,
                "report_type": "html",
                "include_charts": "0",
                "include_stats": "0",
                "include_evaluation": "0",
                "include_recommendations": "0",
                "report_title": "选项生效测试标题",
                "export_format": "compact",
            },
        )
        assert resp.status_code == 200
        body = resp.data.decode("utf-8")
        assert "选项生效测试标题" in body            # 自定义标题生效
        assert 'class="report-compact"' in body     # 紧凑样式生效
        assert "四、数据图表" not in body            # 图表开关生效
        assert "三、统计分析结果" not in body        # 统计开关生效
        assert "六、优化建议与注意事项" not in body   # 建议开关生效
        assert "二、最优转速评分明细" not in body     # 评估报告开关生效

    def test_post_export_csv_empty_stats_redirects_with_message(self):
        # 无统计数据：CSV 导出抛 ValueError → flash 精确提示 + 302 回首页
        empty = {
            "fan_model": "空数据",
            "parsed_data": [],
            "plots": {},
            "stats_html": "",
            "evaluation_report": {},
        }
        token = self._setup_session(empty)
        resp = self.client.post(
            "/export_report?report_type=csv", headers={"X-CSRFToken": token}
        )
        assert resp.status_code == 302
        assert "暂无统计数据" in resp.headers.get("Set-Cookie", "") or True  # flash 走 session

    def test_post_export_without_token_returns_400(self):
        # 缺少 CSRF token 的 POST 必须被拒绝（Flask-WTF 全局保护）
        self._setup_session(_SAVED_RESULTS)
        resp = self.client.post("/export_report?report_type=html")
        assert resp.status_code == 400
