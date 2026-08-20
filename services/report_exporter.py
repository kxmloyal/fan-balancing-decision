#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告导出器核心（ReportExporter）

从 report_export.py（1350行）拆分而来——P2-14 方案 A 三层委派架构。
包含 ReportExporter 核心类及 HtmlExporter；ShareLinkManager 独立于
services/share_link_manager.py。

职责：
  - __init__ / init_app: 初始化与 Flask 集成
  - export: 通用导出编排（委派给 html_builder / data_exporter）
  - share link 管理（委托给 ShareLinkManager）
  - 导出历史管理
  - 会话数据清理（_sanitize_session_data / _sanitize_html）
  - PDF 降级处理（export_report_from_session）
"""

import html as _html
import json
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import WEASYPRINT_AVAILABLE

try:
    from chart_generation_optimized import CHART_TYPE_CONFIG
except ImportError:
    CHART_TYPE_CONFIG = {
        "box": {"name": "箱线图"},
        "violin": {"name": "小提琴图"},
        "scatter": {"name": "散点图"},
        "histogram": {"name": "直方图"},
        "trend": {"name": "趋势图"},
    }

from report_export_css import EXPORTER_CSS
from services.report_constants import PLOTLY_CDN_URL, PLOTLY_DUAL_TRACK_SCRIPT
from services.share_link_manager import ShareLinkManager
from utils.model_utils import sanitize_model_name

logger = logging.getLogger(__name__)


def _html_exporter_css():
    return EXPORTER_CSS


# ============================================================================
#  HtmlExporter —— 简单 HTML 导出器（兼容旧版 API）
# ============================================================================


class HtmlExporter:
    """简单版 HTML 导出器，留给旧版 exporters 兼容"""

    def __init__(self, report_exporter):
        self.report_exporter = report_exporter

    @property
    def output_folder(self):
        return self.report_exporter.output_folder

    def export(self, session_data, output_filename=None, task_id=None, report_config=None):
        try:
            html_content = self.report_exporter.html_builder.render(session_data, report_config)
            fan_model = session_data.get("fan_model", "未知")
            safe_model = sanitize_model_name(fan_model)
            if not output_filename:
                output_filename = (
                    f"{safe_model}_动平衡分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                )
            if not output_filename.endswith(".html"):
                output_filename += ".html"

            model_dir = sanitize_model_name(fan_model)
            model_output_dir = os.path.join(self.output_folder, model_dir)
            os.makedirs(model_output_dir, exist_ok=True)

            output_path = os.path.join(model_output_dir, output_filename)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            export_info = {
                "type": "html",
                "filename": os.path.basename(output_path),
                "path": output_path,
                "fan_model": fan_model,
                "model_dir": model_dir,
            }
            if hasattr(self.report_exporter, "add_to_history"):
                self.report_exporter.add_to_history(export_info)
            return output_path
        except (ValueError, IOError, TypeError) as e:
            logger.error("导出HTML报告失败: %s", str(e))
            raise


# ============================================================================
#  ShareLinkManager —— 已拆分至 services/share_link_manager.py
# ============================================================================


# ============================================================================
#  ReportExporter —— 报告导出器核心
# ============================================================================


class ReportExporter:
    def __init__(self, app=None, output_folder=None):
        self.app = app
        self.output_folder = output_folder or "outputs"

        self.share_link_manager = ShareLinkManager(self.output_folder)

        self.exporters = {"html": HtmlExporter(self)}

        self.default_report_config = {
            "title": "设备不平衡量分析报告",
            "include_summary": True,
            "include_stats": True,
            "include_charts": True,
            "include_methodology": True,
            "include_recommendations": True,
            "chart_types": ["box", "violin", "scatter", "histogram"],
            "chart_layout": "parallel",
        }

        self.export_history = []
        self.history_file = os.path.join(self.output_folder, "export_history.json")

        self._base64_cache = {}
        self._base64_cache_max_size = 200
        self._base64_cache_max_age = 3600

        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.output_folder = app.config.get("OUTPUT_FOLDER", "outputs")
        os.makedirs(self.output_folder, exist_ok=True)
        self.share_link_manager = ShareLinkManager(self.output_folder)
        self.history_file = os.path.join(self.output_folder, "export_history.json")

    # ========================================================================
    #  委派属性：html_builder / data_exporter（惰性初始化）
    # ========================================================================

    @property
    def html_builder(self):
        if not hasattr(self, "_html_builder"):
            from services.report_renderer import ReportRenderer

            self._html_builder = ReportRenderer(self)
        return self._html_builder

    @property
    def data_exporter(self):
        if not hasattr(self, "_data_exporter"):
            from services.report_data_export import ReportDataExporter

            self._data_exporter = ReportDataExporter(self)
        return self._data_exporter

    # ========================================================================
    #  公开 API
    # ========================================================================

    def export_html(self, session_data, output_filename=None, task_id=None, report_config=None):
        return self.html_builder.export_html(session_data, output_filename, task_id, report_config)

    def export(self, export_type, session_data, output_filename=None, task_id=None, **kwargs):
        supported_types = set(self.exporters.keys()) | {"csv", "json", "excel"}
        if export_type not in supported_types:
            raise ValueError(f"不支持的导出类型: {export_type}")

        # csv/json/excel 仅消费标量与 evaluation_report/stats_data，无 HTML 渲染面，
        # 跳过整树深拷贝与白清洗，避免含 plots 的大 session 重复拷贝
        if export_type in ("csv", "json", "excel"):
            sanitized_session_data = session_data
        else:
            sanitized_session_data = self._sanitize_session_data(session_data)

        if export_type == "csv":
            return self.data_exporter.export_csv(sanitized_session_data, output_filename)
        elif export_type == "json":
            return self.data_exporter.export_json(sanitized_session_data, output_filename)
        elif export_type == "excel":
            return self.data_exporter.export_excel(sanitized_session_data, output_filename)

        return self.exporters[export_type].export(
            sanitized_session_data, output_filename, task_id, **kwargs
        )

    def export_report_from_session(self, session_data, output_filename=None, report_config=None):
        # report_config 必须透传，否则 PDF 分支会丢失 include_charts/include_stats 等配置
        html_path = self.export_html(session_data, output_filename, report_config=report_config)

        if WEASYPRINT_AVAILABLE:
            try:
                from weasyprint import HTML

                fan_model = str(session_data.get("fan_model", "未知"))
                model_dir = sanitize_model_name(fan_model)
                # PDF 与 HTML 一致写入型号子目录，保持 outputs 页面按型号分组一致
                pdf_filename = os.path.splitext(os.path.basename(html_path))[0] + ".pdf"
                pdf_path = os.path.join(self.output_folder, model_dir, pdf_filename)
                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                HTML(filename=html_path).write_pdf(pdf_path)
                self.add_to_history(
                    {
                        "type": "pdf",
                        "filename": os.path.basename(pdf_path),
                        "path": pdf_path,
                        "fan_model": fan_model,
                        "model_dir": model_dir,
                    }
                )

                return pdf_path
            except Exception as e:
                logger.warning("PDF转换失败，返回HTML: %s", e)
                return html_path
        return html_path

    # ========================================================================
    #  历史管理
    # ========================================================================

    def add_to_history(self, export_info):
        export_info["timestamp"] = datetime.now().isoformat()
        self.export_history.insert(0, export_info)
        if len(self.export_history) > 100:
            self.export_history = self.export_history[:100]
        self.save_export_history()

    def save_export_history(self):
        try:
            tmp_file = self.history_file + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(self.export_history, f, ensure_ascii=False, indent=2)
            # 原子替换：避免多 worker 并发写坏历史文件
            os.replace(tmp_file, self.history_file)
        except IOError as e:
            logger.error("保存导出历史失败: %s", e)

    def load_export_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.export_history = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error("加载导出历史失败: %s", e)
            self.export_history = []

    # ========================================================================
    #  分享链接
    # ========================================================================

    def create_shareable_link(self, report_path: str, ttl_days: int = 7) -> str:
        return self.share_link_manager.create_link(report_path, ttl_days)

    def revoke_shareable_link(self, link_id: str) -> bool:
        return self.share_link_manager.revoke_link(link_id)

    # ========================================================================
    #  配置合并
    # ========================================================================

    def _merge_report_config(self, user_config):
        config = self.default_report_config.copy()
        if user_config:
            config.update(user_config)
        return config

    # ========================================================================
    #  会话数据清理
    # ========================================================================

    def _sanitize_session_data(self, session_data):
        if not isinstance(session_data, dict):
            return {}

        sanitized_data = {}

        for key, value in session_data.items():
            if key in ["chart_data", "stats_html"]:
                sanitized_data[key] = value
            elif key == "plots":
                if isinstance(value, dict):
                    sanitized_plots = {}
                    for plot_name, plot_data in value.items():
                        if isinstance(plot_data, dict):
                            sanitized_plot_data = {}
                            for chart_type, chart_info in plot_data.items():
                                if isinstance(chart_info, dict):
                                    sanitized_chart_info = {}
                                    for info_key, info_value in chart_info.items():
                                        if info_key == "chart_data":
                                            sanitized_chart_info[info_key] = info_value
                                        elif isinstance(info_value, str):
                                            sanitized_chart_info[info_key] = self._sanitize_html(
                                                info_value
                                            )
                                        else:
                                            sanitized_chart_info[info_key] = info_value
                                    sanitized_plot_data[chart_type] = sanitized_chart_info
                                else:
                                    sanitized_plot_data[chart_type] = plot_data
                            sanitized_plots[plot_name] = sanitized_plot_data
                        else:
                            sanitized_plots[plot_name] = plot_data
                    sanitized_data[key] = sanitized_plots
                else:
                    sanitized_data[key] = value
            elif isinstance(value, list):
                sanitized_list = []
                for item in value:
                    if isinstance(item, dict):
                        sanitized_list.append(self._sanitize_session_data(item.copy()))
                    elif isinstance(item, str):
                        sanitized_list.append(self._sanitize_html(item))
                    elif isinstance(item, list):
                        sanitized_list.append(
                            [self._sanitize_html(s) if isinstance(s, str) else s for s in item]
                        )
                    else:
                        sanitized_list.append(item)
                sanitized_data[key] = sanitized_list
            elif isinstance(value, str):
                sanitized_data[key] = self._sanitize_html(value)
            else:
                sanitized_data[key] = value

        return sanitized_data

    def _sanitize_html(self, html_content):
        if not html_content:
            return ""

        if "<!DOCTYPE html>" in html_content or "<html" in html_content:
            return html_content

        try:
            from html.parser import HTMLParser

            class _WhitelistSanitizer(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.result = []
                    self.safe_tags = {
                        "b",
                        "i",
                        "u",
                        "br",
                        "p",
                        "div",
                        "span",
                        "h1",
                        "h2",
                        "h3",
                        "h4",
                        "h5",
                        "h6",
                        "table",
                        "tr",
                        "td",
                        "th",
                        "thead",
                        "tbody",
                        "a",
                        "strong",
                        "em",
                        "small",
                        "code",
                    }

                def handle_starttag(self, tag, attrs):
                    if tag in self.safe_tags:
                        self.result.append(f"<{tag}>")

                def handle_endtag(self, tag):
                    if tag in self.safe_tags:
                        self.result.append(f"</{tag}>")

                def handle_data(self, data):
                    self.result.append(_html.escape(data))

            parser = _WhitelistSanitizer()
            parser.feed(html_content)
            return "".join(parser.result)
        except Exception:
            pass

        sanitized = _html.escape(html_content)

        safe_tags = [
            "b",
            "i",
            "u",
            "br",
            "p",
            "div",
            "span",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "table",
            "tr",
            "td",
            "th",
        ]

        for tag in safe_tags:
            sanitized = sanitized.replace(f"&lt;{tag}&gt;", f"<{tag}>")
            sanitized = sanitized.replace(f"&lt; {tag}&gt;", f"< {tag}>")
            sanitized = sanitized.replace(f"&lt;/{tag}&gt;", f"</{tag}>")
            sanitized = sanitized.replace(f"&lt;/ {tag}&gt;", f"</{tag}>")

        return sanitized
