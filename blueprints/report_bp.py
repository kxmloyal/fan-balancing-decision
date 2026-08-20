#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告蓝图：包含报告导出功能
"""

import logging
import os
import sys

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from markupsafe import escape

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logger = logging.getLogger(__name__)

from report_export import ReportExporter

try:
    from chart_style_config import CHART_TYPE_CONFIG
except ImportError:
    logger.warning("从chart_style_config导入失败，使用chart_generation_optimized中的配置")


report_bp = Blueprint("report", __name__)

# 初始化ReportExporter
report_exporter = ReportExporter()


@report_bp.route("/report")
def report():
    """报告页面：导出表单 + 最近导出的报告（打通 FS 资产闭环）"""
    recent_exports = []
    try:
        from blueprints.outputs_bp import _load_export_history

        for item in _load_export_history()[:8]:
            model_dir = item.get("model_dir", "")
            filename = item.get("filename", "")
            recent_exports.append(
                {
                    "filename": filename,
                    "fan_model": item.get("fan_model", "未知"),
                    "type": item.get("type", ""),
                    "timestamp": item.get("timestamp", ""),
                    "download_path": f"{model_dir}/{filename}" if model_dir else filename,
                }
            )
    except Exception:
        current_app.logger.warning("报告页加载导出历史失败", exc_info=True)

    return render_template("report.html", recent_exports=recent_exports)


@report_bp.route("/export_report", methods=["POST"])
def export_report():
    """导出报告——支持优雅降级：部分数据缺失时仍可生成报告"""

    def _init_report_exporter(exporter, app):
        # 强制同步 app 配置的绝对输出目录：gunicorn CWD 可能异常，
        # 相对路径 "outputs" 会把报告写入不可见位置，导致导出文件"消失"
        exporter.init_app(app)
        exporter.load_export_history()

    def _safe_create_shareable_link(exporter, filepath):
        try:
            exporter.create_shareable_link(filepath)
        except Exception as e:
            current_app.logger.warning("创建分享链接失败: %s", str(e))

    def _check_export_format(export_type):
        available = {
            "html": "html",
            "pdf": "pdf",
            "csv": "csv",
            "json": "json",
            "xlsx": "excel",
        }
        return available.get(export_type)

    def _validate_saved_results(saved_results):
        issues = []
        if not saved_results.get("parsed_data"):
            issues.append("缺少分析数据")
        if not saved_results.get("plots"):
            issues.append("缺少图表数据")
        if not saved_results.get("stats_html"):
            issues.append("缺少统计报告")
        if not saved_results.get("evaluation_report"):
            issues.append("缺少评估报告")
        return issues

    try:
        report_type = request.values.get("report_type", "html")

        if report_type not in ["html", "pdf", "csv", "json", "xlsx"]:
            flash("仅支持HTML、PDF、CSV、JSON和Excel格式报告导出！")
            return redirect(url_for("main.index"))

        export_info = _check_export_format(report_type)
        if export_info is None:
            flash(f"不支持的导出格式：{report_type}")
            return redirect(url_for("main.index"))

        # 表单以 POST body 提交，须用 request.values 读取（request.args 只含查询串，
        # 会导致「包含图表/统计数据/评估/建议、标题、样式」选项全部取默认值而失效）
        include_charts = request.values.get("include_charts", "1") == "1"
        include_stats = request.values.get("include_stats", "1") == "1"
        include_evaluation = request.values.get("include_evaluation", "1") == "1"
        include_recommendations = request.values.get("include_recommendations", "1") == "1"
        report_title = escape(request.values.get("report_title", "设备不平衡量分析报告"))
        export_format = request.values.get("export_format", "standard")
        if export_format not in ["standard", "compact", "detailed"]:
            export_format = "standard"

        saved_results = session.get("saved_results")
        if not saved_results:
            flash("无分析数据可供导出，请先进行分析！")
            return redirect(url_for("main.index"))

        data_issues = _validate_saved_results(saved_results)
        if data_issues:
            issue_msg = "报告数据不完整：" + "；".join(data_issues) + "。将生成包含可用数据的报告。"
            flash(issue_msg)
            current_app.logger.warning("报告数据不完整，降级生成: %s", ", ".join(data_issues))

        report_config = {
            "title": report_title,
            "include_stats": include_stats,
            "include_charts": include_charts,
            "include_evaluation": include_evaluation,
            "include_recommendations": include_recommendations,
            "export_format": export_format,
        }

        _init_report_exporter(report_exporter, current_app)

        if report_type == "html":
            filepath = report_exporter.export_html(saved_results, report_config=report_config)
            _safe_create_shareable_link(report_exporter, filepath)
            return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))

        elif report_type == "pdf":
            filepath = report_exporter.export_report_from_session(
                saved_results, report_config=report_config
            )
            _safe_create_shareable_link(report_exporter, filepath)
            if not filepath.lower().endswith(".pdf"):
                flash("PDF 生成失败，已降级为 HTML 格式，请检查 WeasyPrint 是否已安装")
            return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))

        elif report_type in ("csv", "json", "xlsx"):
            try:
                export_key = export_info
                if report_type == "xlsx":
                    export_key = "excel"
                filepath = report_exporter.export(export_key, saved_results)
            except ValueError as e:
                flash(str(e))
                return redirect(url_for("main.index"))
            except AttributeError:
                flash("该导出功能暂时不可用")
                return redirect(url_for("main.index"))
            _safe_create_shareable_link(report_exporter, filepath)
            return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))

    except Exception as e:
        current_app.logger.error("导出报告失败: %s", str(e), exc_info=True)
        flash("导出失败，请稍后重试")
        return redirect(url_for("main.index"))
