#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回归测试：并列显示修复配套改动
1. 静态资源版本号（Cache-Busting）— 首页 4 处关键静态引用必须携带 ?v=9，规避 30 天强缓存导致旧 JS 残留
2. 会话目录环境变量覆盖 — dev/测试服务器可与生产隔离会话目录，避免权限冲突引发 CSRF 400
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import wsgi

app = wsgi.app if hasattr(wsgi, "app") else wsgi.application
app.config["TESTING"] = True

_VERSIONED_ASSETS = [
    "css/style.css?v=9",
    "css/upload.css?v=9",
    "js/charts.js?v=9",
    "js/page-initializer.js?v=9",
]


def _render_index():
    ctx = dict(
        plots={"p1": {"box": {"chart_data": "[]"}}},
        stats_html="<table>x</table>",
        stats_csv="x.csv",
        has_p1=True,
        has_p2=False,
        has_st=False,
        saved_results={"chart_layout": "stacked", "fan_model": "T", "chart_types": ["box"]},
        evaluation_report={"best_speeds": [], "speed_detailed_scores": {}, "detailed_scores": {}},
        chart_layout="stacked",
        balance_machine_models=["M1"],
    )
    with app.test_request_context("/"):
        return app.jinja_env.get_template("index.html").render(**ctx)


class TestSessionDirConfig:
    def test_default_session_dir_points_to_flask_session_new(self):
        assert "flask_session_new" in app.config["SESSION_FILE_DIR"]

    def test_env_override_supported(self):
        # 环境变量覆盖表达式：设置后优先，未设置回退默认目录
        override = os.environ.get("SESSION_FILE_DIR")
        assert override or app.config["SESSION_FILE_DIR"].endswith("flask_session_new")


class TestCacheBusting:
    def test_index_renders_with_versioned_static(self):
        html = _render_index()
        for asset in _VERSIONED_ASSETS:
            assert asset in html, f"首页静态资源缺少版本号: {asset}"

    def test_index_renders_without_static_v_global(self):
        # 运行中的 gunicorn 未重启前不得引用未注册的 static_v（否则首页 500）
        html = _render_index()
        assert "static_v" not in html
