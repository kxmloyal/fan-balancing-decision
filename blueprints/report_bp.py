# -*- coding: utf-8 -*-
"""
报告蓝图：包含报告导出功能
"""

import base64
import json
import os
import re
from datetime import datetime
from statistics import generate_stats_data

from flask import (
    Blueprint, current_app, flash, redirect, render_template, request,
    send_file, send_from_directory, session, url_for, jsonify
)

from chart_generation import CHART_TYPE_CONFIG
from report_export import ReportExporter

report_bp = Blueprint("report", __name__)

# 初始化ReportExporter
report_exporter = ReportExporter()


@report_bp.route("/report")
def report():
    """报告页面"""
    return render_template("report.html")


@report_bp.route("/export_report", methods=["GET"])
def export_report():
    """导出报告"""
    try:
        # 确保json模块在函数内部可访问
        global json
        
        # 获取报告类型参数
        report_type = request.args.get("report_type", "html")

        # 确保报告类型是支持的格式
        if report_type not in ["html", "pdf", "csv", "json", "xlsx"]:
            flash("仅支持HTML、PDF、CSV、JSON和Excel格式报告导出！")
            return redirect(url_for("main.index"))

        # 从session获取分析结果
        saved_results = session.get("saved_results")
        if not saved_results:
            flash("无分析数据可供导出，请先进行分析！")
            return redirect(url_for("main.index"))

        # 生成HTML报告内容
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 准备统计分析数据
        stats_html = saved_results.get("stats_html", "<p>暂无统计分析数据</p>")

        # 提取最优转速信息用于摘要
        optimal_speed_info = "未找到最优转速信息"
        if stats_html:
            # 查找最优转速信息
            optimal_match = re.search(r"最优转速[^：]*：([^<]+)", stats_html)
            if optimal_match:
                optimal_speed_info = optimal_match.group(1).strip()

        # 准备图表信息
        plots = saved_results.get("plots", {})
        has_p1 = saved_results.get("has_p1", False)
        has_p2 = saved_results.get("has_p2", False)
        has_st = saved_results.get("has_st", False)

        # 构建图表部分的HTML
        charts_html = ""
        if plots:
            # 获取保存的布局设置，默认为堆叠显示
            saved_layout = saved_results.get("chart_layout", "stacked")

            # 根据布局选择只生成一套图表
            if saved_layout == "parallel":
                # 开始并列显示区域
                charts_html += (
                    '<div class="chart-parallel" id="parallelChartContainer">'
                )

                # 并列显示的图表组
                charts_html += '<div class="chart-row">'

                # 通用图表生成函数
                def generate_chart_html(
                    surface_name, surface_key, has_surface, plots_dict
                ):
                    # 确保json模块在嵌套函数内部可访问
                    global json
                    
                    if not plots_dict.get(surface_key) or not has_surface:
                        return ""
                    
                    surface_html = f"""
                    <div class="chart-col">
                        <div class="chart-group">
                            <h3 class="chart-section-title">{surface_name}面数据图表</h3>
                            """

                    for chart_type, chart_files in plots_dict[surface_key].items():
                        chart_title = f"{surface_name}面不平衡量{CHART_TYPE_CONFIG.get(chart_type, {}).get('name', chart_type)}"
                        # 使用url_for生成正确的链接
                        chart_png_url = url_for(
                            "outputs.view_chart", filename=chart_files["png"]
                        )

                        # 为导出报告添加base64编码的图像数据
                        png_file_path = os.path.join(
                            current_app.config["OUTPUT_FOLDER"], chart_files["png"]
                        )
                        img_base64 = ""
                        if os.path.exists(png_file_path):
                            try:
                                with open(png_file_path, "rb") as img_file:
                                    img_data = img_file.read()
                                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                                # 不再检查图像格式，允许任何图像数据
                                # 打印调试信息
                                print(f"图表图像: {chart_files['png']}")
                                print(f"图像文件大小: {len(img_data)} bytes")
                                print(f"Base64前缀: {img_base64[:20]}")
                            except Exception as e:
                                print(f"读取图表图像失败: {str(e)}")
                                img_base64 = ""
                        else:
                            print(f"图表图像文件不存在: {png_file_path}")

                        # 获取图表说明
                        chart_annotation = CHART_TYPE_CONFIG.get(chart_type, {}).get(
                            "annotation", ""
                        )

                        # 获取图表属性
                        chart_properties = chart_files.get('chart_properties', {})

                        surface_html += f"""
                            <div class="chart-section mb-5 p-4 bg-white rounded shadow-sm">
                                <h4 class="chart-title mb-3">{chart_title}</h4>
                                <div class="chart-img-container text-center mb-4">
                        """
                        if img_base64:
                            # 根据文件扩展名确定图像MIME类型
                            if chart_files['png'].endswith('.svg'):
                                surface_html += f"""<img src="data:image/svg+xml;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                            else:
                                surface_html += f"""<img src="data:image/png;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                        else:
                            surface_html += f"""<img src="{chart_png_url}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                        surface_html += f"""
                                </div>
                                """

                        # 添加图表说明
                        if chart_annotation:
                            surface_html += f"""
                                <div class="chart-annotation bg-light p-3 rounded mb-3">
                                    {chart_annotation}
                                </div>
                                """

                        # 添加图表属性信息（可选，用于调试）
                        if chart_properties:
                            surface_html += f"""
                                <div class="chart-properties mt-2">
                                    <small class="text-muted">
                                        图表属性: {json.dumps(chart_properties, ensure_ascii=False)}
                                    </small>
                                </div>
                                """

                        # 添加其他图表类型的标签
                        other_charts = [
                            other_type
                            for other_type in plots_dict[surface_key]
                            if other_type != chart_type
                        ]
                        if other_charts:
                            surface_html += f"""
                                <div class="chart-type-tags mt-3">
                        """
                            for other_chart_type in other_charts:
                                surface_html += f'<span class="badge bg-secondary chart-type-badge me-1">{CHART_TYPE_CONFIG.get(other_chart_type, {}).get("name", other_chart_type)}</span>'
                            surface_html += f"""                                </div>
                                """

                        surface_html += f"""                            </div>
                        """


                    surface_html += """
                        </div>
                    </div>
                    """
                    return surface_html

                # 生成各面图表HTML
                charts_html += generate_chart_html("P1", "p1", has_p1, plots)
                charts_html += generate_chart_html("P2", "p2", has_p2, plots)
                charts_html += generate_chart_html("ST", "sum", has_st, plots)

                # 单面图（当只有一个面时）
                if plots.get("single"):
                    surface_type = saved_results.get("single_surface", "未知")
                    surface_name = {"p1": "P1", "p2": "P2", "st": "ST"}.get(
                        surface_type, surface_type
                    )

                    charts_html += f"""
                    <div class="chart-col">
                        <div class="chart-group">
                            <h3 class="chart-section-title">{surface_name}面数据图表</h3>
                            """

                    for chart_type, chart_files in plots["single"].items():
                        chart_title = f"{surface_name}面不平衡量{CHART_TYPE_CONFIG.get(chart_type, {}).get('name', chart_type)}"
                        # 使用url_for生成正确的链接
                        chart_png_url = url_for(
                            "outputs.view_chart", filename=chart_files["png"]
                        )

                        # 为导出报告添加base64编码的图像数据
                        png_file_path = os.path.join(
                            current_app.config["OUTPUT_FOLDER"], chart_files["png"]
                        )
                        img_base64 = ""
                        if os.path.exists(png_file_path):
                            try:
                                with open(png_file_path, "rb") as img_file:
                                    img_data = img_file.read()
                                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                                # 不再检查图像格式，允许任何图像数据
                            except Exception as e:
                                print(f"读取图表图像失败: {str(e)}")
                                img_base64 = ""

                        # 获取图表说明
                        chart_annotation = CHART_TYPE_CONFIG.get(chart_type, {}).get(
                            "annotation", ""
                        )

                        # 获取图表属性
                        chart_properties = chart_files.get('chart_properties', {})

                        charts_html += f"""
                            <div class="chart-section mb-5 p-4 bg-white rounded shadow-sm">
                                <h4 class="chart-title mb-3">{chart_title}</h4>
                                <div class="chart-img-container text-center mb-4">
                    """
                        if img_base64:
                            # 根据文件扩展名确定图像MIME类型
                            if chart_files['png'].endswith('.svg'):
                                charts_html += f"""<img src="data:image/svg+xml;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                            else:
                                charts_html += f"""<img src="data:image/png;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                        else:
                            charts_html += f"""<img src="{chart_png_url}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                        charts_html += f"""
                                </div>
                                """

                        # 添加图表说明
                        if chart_annotation:
                            charts_html += f"""
                                <div class="chart-annotation bg-light p-3 rounded mb-3">
                                    {chart_annotation}
                                </div>
                                """

                        # 添加图表属性信息（可选，用于调试）
                        if chart_properties:
                            charts_html += f"""
                                <div class="chart-properties mt-2">
                                    <small class="text-muted">
                                        图表属性: {json.dumps(chart_properties, ensure_ascii=False)}
                                    </small>
                                </div>
                                """

                        # 添加其他图表类型的标签
                        other_charts = [
                            other_type
                            for other_type in plots["single"]
                            if other_type != chart_type
                        ]
                        if other_charts:
                            charts_html += f"""
                                <div class="chart-type-tags mt-3">
                    """
                            for other_chart_type in other_charts:
                                charts_html += f'<span class="badge bg-secondary chart-type-badge me-1">{CHART_TYPE_CONFIG.get(other_chart_type, {}).get("name", other_chart_type)}</span>'
                            charts_html += f"""                                </div>
                                """

                        charts_html += """                            </div>
                        """


                    charts_html += """        </div>
                    </div>"""

                # 结束并列显示区域
                charts_html += "</div></div>"
            else:
                # 默认使用堆叠显示区域
                charts_html += '<div class="chart-stacked" id="chartContainer">'

                # P1面图
                if plots.get("p1") and has_p1:
                    charts_html += '<div class="chart-group mb-6">'
                    charts_html += (
                        '<h3 class="chart-section-title mb-4">P1面数据图表</h3>'
                    )
                    for chart_type, chart_files in plots["p1"].items():
                        chart_title = f"P1面不平衡量{CHART_TYPE_CONFIG.get(chart_type, {}).get('name', chart_type)}"
                        # 使用url_for生成正确的链接
                        chart_png_url = url_for(
                            "outputs.view_chart", filename=chart_files["png"]
                        )
                        chart_html_url = url_for(
                            "outputs.view_chart_html", filename=chart_files["html"]
                        )

                        # 为导出报告添加base64编码的图像数据
                        png_file_path = os.path.join(
                            current_app.config["OUTPUT_FOLDER"], chart_files["png"]
                        )
                        img_base64 = ""
                        if os.path.exists(png_file_path):
                            try:
                                with open(png_file_path, "rb") as img_file:
                                    img_data = img_file.read()
                                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                                # 不再检查图像格式，允许任何图像数据
                            except Exception as e:
                                print(f"读取图表图像失败: {str(e)}")
                                img_base64 = ""

                        # 获取图表说明
                        chart_annotation = CHART_TYPE_CONFIG.get(chart_type, {}).get(
                            "annotation", ""
                        )

                        # 获取图表属性
                        chart_properties = chart_files.get('chart_properties', {})

                        charts_html += f"""
                            <div class="chart-section mb-5 p-4 bg-white rounded shadow-sm">
                                <h4 class="chart-title mb-3">{chart_title}</h4>
                                <div class="chart-img-container text-center mb-4">
                        """
                        if img_base64:
                            # 根据文件扩展名确定图像MIME类型
                            if chart_files['png'].endswith('.svg'):
                                charts_html += f"""<img src="data:image/svg+xml;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                            else:
                                charts_html += f"""<img src="data:image/png;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                        else:
                            charts_html += f"""<img src="{chart_png_url}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                        charts_html += f"""
                                </div>
                                """

                        # 添加图表说明
                        if chart_annotation:
                            charts_html += f"""
                                <div class="chart-annotation bg-light p-3 rounded mb-3">
                                    {chart_annotation}
                                </div>
                                """

                        # 添加图表属性信息（可选，用于调试）
                        if chart_properties:
                            charts_html += f"""
                                <div class="chart-properties mt-2">
                                    <small class="text-muted">
                                        图表属性: {json.dumps(chart_properties, ensure_ascii=False)}
                                    </small>
                                </div>
                                """

                        # 添加其他图表类型的标签
                        other_charts = [
                            other_type
                            for other_type in plots["p1"]
                            if other_type != chart_type
                        ]
                        if other_charts:
                            charts_html += f"""
                                <div class="chart-type-tags mt-3">
                        """
                            for other_chart_type in other_charts:
                                charts_html += f'<span class="badge bg-secondary chart-type-badge me-1">{CHART_TYPE_CONFIG.get(other_chart_type, {}).get("name", other_chart_type)}</span>'
                            charts_html += f"""                                </div>
                                """

                        charts_html += f"""                            </div>
                        """
                    charts_html += "</div>"

                # P2面图
                if plots.get("p2") and has_p2:
                    charts_html += '<div class="chart-group mb-6">'
                    charts_html += (
                        '<h3 class="chart-section-title mb-4">P2面数据图表</h3>'
                    )
                    for chart_type, chart_files in plots["p2"].items():
                        chart_title = f"P2面不平衡量{CHART_TYPE_CONFIG.get(chart_type, {}).get('name', chart_type)}"
                        # 使用url_for生成正确的链接
                        chart_png_url = url_for(
                            "outputs.view_chart", filename=chart_files["png"]
                        )
                        chart_html_url = url_for(
                            "outputs.view_chart_html", filename=chart_files["html"]
                        )

                        # 为导出报告添加base64编码的图像数据
                        png_file_path = os.path.join(
                            current_app.config["OUTPUT_FOLDER"], chart_files["png"]
                        )
                        img_base64 = ""
                        if os.path.exists(png_file_path):
                            try:
                                with open(png_file_path, "rb") as img_file:
                                    img_data = img_file.read()
                                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                                # 不再检查图像格式，允许任何图像数据
                            except Exception as e:
                                print(f"读取图表图像失败: {str(e)}")
                                img_base64 = ""

                        # 获取图表说明
                        chart_annotation = CHART_TYPE_CONFIG.get(chart_type, {}).get(
                            "annotation", ""
                        )

                        # 获取图表属性
                        chart_properties = chart_files.get('chart_properties', {})

                        charts_html += f"""
                            <div class="chart-section mb-5 p-4 bg-white rounded shadow-sm">
                                <h4 class="chart-title mb-3">{chart_title}</h4>
                                <div class="chart-img-container text-center mb-4">
                        """
                        if img_base64:
                            # 根据文件扩展名确定图像MIME类型
                            if chart_files['png'].endswith('.svg'):
                                charts_html += f"""<img src="data:image/svg+xml;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                            else:
                                charts_html += f"""<img src="data:image/png;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                        else:
                            charts_html += f"""<img src="{chart_png_url}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                        charts_html += f"""
                                </div>
                                """

                        # 添加图表说明
                        if chart_annotation:
                            charts_html += f"""
                                <div class="chart-annotation bg-light p-3 rounded mb-3">
                                    {chart_annotation}
                                </div>
                                """

                        # 添加图表属性信息（可选，用于调试）
                        if chart_properties:
                            charts_html += f"""
                                <div class="chart-properties mt-2">
                                    <small class="text-muted">
                                        图表属性: {json.dumps(chart_properties, ensure_ascii=False)}
                                    </small>
                                </div>
                                """

                        # 添加其他图表类型的标签
                        other_charts = [
                            other_type
                            for other_type in plots["p2"]
                            if other_type != chart_type
                        ]
                        if other_charts:
                            charts_html += f"""
                                <div class="chart-type-tags mt-3">
                        """
                            for other_chart_type in other_charts:
                                charts_html += f'<span class="badge bg-secondary chart-type-badge me-1">{CHART_TYPE_CONFIG.get(other_chart_type, {}).get("name", other_chart_type)}</span>'
                            charts_html += f"""                                </div>
                                """

                        charts_html += f"""                            </div>
                        """
                    charts_html += "</div>"

                # ST面图
                if plots.get("sum") and has_st:
                    charts_html += '<div class="chart-group mb-6">'
                    charts_html += (
                        '<h3 class="chart-section-title mb-4">ST面数据图表</h3>'
                    )
                    for chart_type, chart_files in plots["sum"].items():
                        chart_title = f"ST面不平衡量{CHART_TYPE_CONFIG.get(chart_type, {}).get('name', chart_type)}"
                        # 使用url_for生成正确的链接
                        chart_png_url = url_for(
                            "outputs.view_chart", filename=chart_files["png"]
                        )
                        chart_html_url = url_for(
                            "outputs.view_chart_html", filename=chart_files["html"]
                        )

                        # 为导出报告添加base64编码的图像数据
                        png_file_path = os.path.join(
                            current_app.config["OUTPUT_FOLDER"], chart_files["png"]
                        )
                        img_base64 = ""
                        if os.path.exists(png_file_path):
                            try:
                                with open(png_file_path, "rb") as img_file:
                                    img_data = img_file.read()
                                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                                # 不再检查图像格式，允许任何图像数据
                            except Exception as e:
                                print(f"读取图表图像失败: {str(e)}")
                                img_base64 = ""

                        # 获取图表说明
                        chart_annotation = CHART_TYPE_CONFIG.get(chart_type, {}).get(
                            "annotation", ""
                        )

                        # 获取图表属性
                        chart_properties = chart_files.get('chart_properties', {})

                        charts_html += f"""
                            <div class="chart-section mb-5 p-4 bg-white rounded shadow-sm">
                                <h4 class="chart-title mb-3">{chart_title}</h4>
                                <div class="chart-img-container text-center mb-4">
                        """
                        if img_base64:
                            # 根据文件扩展名确定图像MIME类型
                            if chart_files['png'].endswith('.svg'):
                                charts_html += f"""<img src="data:image/svg+xml;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                            else:
                                charts_html += f"""<img src="data:image/png;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                        else:
                            charts_html += f"""<img src="{chart_png_url}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                        charts_html += f"""
                                </div>
                                """

                        # 添加图表说明
                        if chart_annotation:
                            charts_html += f"""
                                <div class="chart-annotation bg-light p-3 rounded mb-3">
                                    {chart_annotation}
                                </div>
                                """

                        # 添加图表属性信息（可选，用于调试）
                        if chart_properties:
                            charts_html += f"""
                                <div class="chart-properties mt-2">
                                    <small class="text-muted">
                                        图表属性: {json.dumps(chart_properties, ensure_ascii=False)}
                                    </small>
                                </div>
                                """

                        # 添加其他图表类型的标签
                        other_charts = [
                            other_type
                            for other_type in plots["sum"]
                            if other_type != chart_type
                        ]
                        if other_charts:
                            charts_html += f"""
                                <div class="chart-type-tags mt-3">
                        """
                            for other_chart_type in other_charts:
                                charts_html += f'<span class="badge bg-secondary chart-type-badge me-1">{CHART_TYPE_CONFIG.get(other_chart_type, {}).get("name", other_chart_type)}</span>'
                            charts_html += f"""                                </div>
                                """

                        charts_html += f"""                            </div>
                        """
                    charts_html += "</div>"

                # 单面图（当只有一个面时）
                if plots.get("single"):
                    surface_type = saved_results.get("single_surface", "未知")
                    surface_name = {"p1": "P1", "p2": "P2", "st": "ST"}.get(
                        surface_type, surface_type
                    )
                    charts_html += '<div class="chart-group mb-6">'
                    charts_html += f'<h3 class="chart-section-title mb-4">{surface_name}面数据图表</h3>'
                    for chart_type, chart_files in plots["single"].items():
                        chart_title = f"{surface_name}面不平衡量{CHART_TYPE_CONFIG.get(chart_type, {}).get('name', chart_type)}"
                        # 使用url_for生成正确的链接
                        chart_png_url = url_for(
                            "outputs.view_chart", filename=chart_files["png"]
                        )
                        chart_html_url = url_for(
                            "outputs.view_chart_html", filename=chart_files["html"]
                        )

                        # 为导出报告添加base64编码的图像数据
                        png_file_path = os.path.join(
                            current_app.config["OUTPUT_FOLDER"], chart_files["png"]
                        )
                        img_base64 = ""
                        if os.path.exists(png_file_path):
                            try:
                                with open(png_file_path, "rb") as img_file:
                                    img_data = img_file.read()
                                    img_base64 = base64.b64encode(img_data).decode("utf-8")
                                # 不再检查图像格式，允许任何图像数据
                            except Exception as e:
                                print(f"读取图表图像失败: {str(e)}")
                                img_base64 = ""

                        # 获取图表说明
                        chart_annotation = CHART_TYPE_CONFIG.get(chart_type, {}).get(
                            "annotation", ""
                        )

                        # 获取图表属性
                        chart_properties = chart_files.get('chart_properties', {})

                        charts_html += f"""
                            <div class="chart-section mb-5 p-4 bg-white rounded shadow-sm">
                                <h4 class="chart-title mb-3">{chart_title}</h4>
                                <div class="chart-img-container text-center mb-4">
                        """
                        if img_base64:
                            # 根据文件扩展名确定图像MIME类型
                            if chart_files['png'].endswith('.svg'):
                                charts_html += f"""<img src="data:image/svg+xml;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                            else:
                                charts_html += f"""<img src="data:image/png;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                        else:
                            charts_html += f"""<img src="{chart_png_url}" alt="{chart_title}" style="max-width: 100%; height: auto;" class="chart-img img-fluid">"""
                        charts_html += f"""
                                </div>
                                """

                        # 添加图表说明
                        if chart_annotation:
                            charts_html += f"""
                                <div class="chart-annotation bg-light p-3 rounded mb-3">
                                    {chart_annotation}
                                </div>
                                """

                        # 添加图表属性信息（可选，用于调试）
                        if chart_properties:
                            charts_html += f"""
                                <div class="chart-properties mt-2">
                                    <small class="text-muted">
                                        图表属性: {json.dumps(chart_properties, ensure_ascii=False)}
                                    </small>
                                </div>
                                """

                        # 添加其他图表类型的标签
                        other_charts = [
                            other_type
                            for other_type in plots["single"]
                            if other_type != chart_type
                        ]
                        if other_charts:
                            charts_html += f"""
                                <div class="chart-type-tags mt-3">
                        """
                            for other_chart_type in other_charts:
                                charts_html += f'<span class="badge bg-secondary chart-type-badge me-1">{CHART_TYPE_CONFIG.get(other_chart_type, {}).get("name", other_chart_type)}</span>'
                            charts_html += f"""                                </div>
                                """

                        charts_html += f"""                            </div>
                        """
                    charts_html += "</div>"

                # 结束堆叠显示区域
                charts_html += "</div>"
        # 从saved_results获取扇叶型号
        fan_model = saved_results.get("fan_model", "未知型号")

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>设备不平衡量分析报告 - {fan_model}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body {{
            font-family: "SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background-color: #007bff;
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .header h2 {{
            margin: 10px 0 0 0;
            font-size: 20px;
            font-weight: normal;
            opacity: 0.9;
        }}
        .report-info {{
            background-color: #e9ecef;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
        }}
        .report-info-item {{
            margin: 5px 0;
        }}
        .content {{
            padding: 30px;
        }}
        h2.section-title {{
            color: #007bff;
            border-left: 4px solid #007bff;
            padding-left: 15px;
            margin: 30px 0 20px 0;
        }}
        .summary-box {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary-box h3 {{
            margin-top: 0;
            color: #155724;
        }}
        /* 表格样式优化 */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 5px;
            overflow: hidden;
        }}
        table, th, td {{
            border: 1px solid #dee2e6;
        }}
        th, td {{
            padding: 12px 8px;
            text-align: center;
            word-wrap: break-word;
        }}
        th {{
            background-color: #007bff;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        tr:hover {{
            background-color: #e9ecef;
        }}
        /* 表头特殊样式 */
        table thead tr:first-child th {{
            background-color: #0056b3;
            font-size: 14px;
        }}
        table thead tr:nth-child(2) th {{
            background-color: #007bff;
            font-size: 12px;
        }}
        /* 特殊列宽度设置 */
        table thead tr:first-child th:first-child {{
            width: 80px;
        }}
        /* 综合评价列 */
        table thead tr:first-child th:last-child,
        table thead tr:nth-child(2) th:last-child {{
            width: 100px;
        }}
        table tbody tr td:last-child {{
            font-weight: bold;
            background-color: #f1f8ff;
        }}
        /* 最优转速行 */
        table tbody tr.table-success {{
            background-color: #d4edda !important;
        }}
        table tbody tr.table-success td:last-child {{
            background-color: #c3e6cb !important;
        }}
        /* 高亮IQR最小值 */
        table tbody tr td.table-warning {{
            background-color: #fff3cd !important;
            font-weight: bold;
        }}
        /* 响应式表格 */
        .table-responsive {{
            overflow-x: auto;
            margin: 15px 0;
        }}
        /* 图表部分样式 */
        .chart-group {{
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            background-color: #f8f9fa;
        }}
        .chart-group h3 {{
            color: #007bff;
            margin-top: 0;
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 10px;
        }}
        .chart-section {{
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            background-color: white;
        }}
        .chart-section h4 {{
            margin-top: 0;
            color: #333;
        }}
        .chart-img-container {{
            text-align: center;
            margin: 15px 0;
        }}
        .chart-img-container img {{
            max-width: 100%;
            height: auto;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-radius: 3px;
        }}
        .chart-embed-container {{
            margin: 20px 0;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            overflow: hidden;
        }}
        .chart-links {{
            text-align: center;
            margin: 10px 0;
        }}
        .chart-links a {{
            display: inline-block;
            margin: 0 5px;
            padding: 5px 10px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 3px;
            font-size: 14px;
        }}
        .chart-links a:hover {{
            background-color: #0056b3;
        }}
        .info-box {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .recommendations-box {{
            background-color: #e2e3e5;
            border: 1px solid #d6d8db;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .technical-details-box {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
        }}
        
        /* 图表布局样式 - 与前端保持一致 */
        .chart-display-control {{
            margin-bottom: 20px;
        }}
        .chart-row {{
            display: flex;
            flex-wrap: nowrap;
            gap: 0;
            margin: 0 -10px;
            width: calc(100% + 20px);
        }}
        .chart-col {{
            flex: 1;
            min-width: 0;
            padding: 0 10px;
        }}
        .chart-col > .chart-container {{
            display: flex;
            flex-direction: column;
            height: 100%;
            margin: 0;
            padding: 0;
            background-color: transparent;
            border: none;
            border-radius: 0;
            box-shadow: none;
        }}
        .chart-stacked .chart-container {{
            margin-bottom: 30px;
        }}
        .chart-parallel .chart-col {{
            display: flex;
            flex-direction: column;
            height: 100%;
        }}
        .chart-parallel .chart-section {{
            flex-grow: 1;
            margin: 0;
            padding: 15px;
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 5px;
        }}
        /* 确保图表部分均匀分布 */
        .chart-parallel .chart-section-title {{
            margin-top: 0;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #dee2e6;
        }}
        /* 确保图表部分均匀分布 */
        .chart-parallel .chart-section-title {{
            margin-top: 0;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #dee2e6;
        }}
        /* 确保图表图片显示 */
        .chart-section .chart-img-container {{
            margin: 15px 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 300px;
        }}
        .chart-section .chart-img-container img {{
            max-height: 500px;
            width: auto;
            max-width: 100%;
            object-fit: contain;
        }}
        /* 确保所有图表列高度一致 */
        .chart-col {{
            display: flex;
            flex-direction: column;
        }}
        .chart-col > .chart-container {{
            flex-grow: 1;
        }}
        /* 响应式改进 */
        @media (min-width: 1400px) {{
            .container {{
                max-width: 1320px;
            }}
            .chart-col {{
                min-width: 350px;
            }}
        }}
        
        @media (min-width: 1600px) {{
            .container {{
                max-width: 1520px;
            }}
            .chart-col {{
                min-width: 400px;
            }}
        }}
        
        @media (min-width: 1900px) {{
            .container {{
                max-width: 1720px;
            }}
            .chart-col {{
                min-width: 450px;
            }}
        }}
        
        /* 1920x1080 分辨率优化 */
        @media (min-width: 1920px) and (min-height: 1080px) {{
            .container {{
                max-width: 1720px;
                padding: 40px;
            }}
            
            .chart-container {{
                padding: 30px;
            }}
        }}
        
        /* 16:9 屏幕优化 */
        @media (min-aspect-ratio: 16/9) {{
            .container {{
                max-width: 90vw;
            }}
            .chart-container {{
                padding: 25px;
            }}
        }}
        
        @media (min-aspect-ratio: 16/9) and (min-width: 1200px) {{
            .container {{
                max-width: 85vw;
            }}
            .chart-container {{
                padding: 30px;
            }}
        }}
        
        @media (min-aspect-ratio: 16/9) and (min-width: 1600px) {{
            .container {{
                max-width: 80vw;
            }}
            .chart-container {{
                padding: 35px;
            }}
        }}
        
        /* 图表容器响应式調整 */
        .chart-container {{
            margin: 20px 0;
            padding: 20px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        
        @media (min-width: 1200px) {{
            .chart-container {{
                padding: 25px;
            }}
        }}
        
        @media (min-width: 1400px) {{
            .chart-container {{
                padding: 30px;
            }}
        }}
        
        @media print {{
            body {{
                background-color: white;
                font-size: 12pt;
            }}
            .container {{
                box-shadow: none;
                max-width: 100%;
                padding: 0;
            }}
            .chart-links a {{
                background-color: #ccc;
                color: #333;
                text-decoration: none;
            }}
            /* 确保所有容器和表格都在页面范围内 */
            .table-responsive {{
                overflow: visible;
                width: 100%;
            }}
            table {{
                page-break-inside: avoid;
                width: 100% !important;
            }}
            /* 优化图表容器打印样式 */
            .chart-container {{
                box-shadow: none;
                padding: 15px;
                margin: 10px 0;
            }}
            .chart-img-container img {{
                max-width: 100% !important;
                height: auto !important;
                page-break-inside: avoid;
            }}
            /* 优化报告结构打印 */
            .header, .report-info, .content {{
                page-break-inside: avoid;
            }}
            /* 调整边距和间距 */
            h1, h2, h3, h4 {{
                page-break-after: avoid;
                page-break-inside: avoid;
            }}
            /* 确保章节不被分割 */
            .section-title {{
                page-break-after: avoid;
            }}
            /* 优化列表和段落 */
            ul, ol, p {{
                page-break-inside: avoid;
            }}
            /* 移除不必要的元素 */
            .chart-display-control {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>设备不平衡量分析报告</h1>
            <h2>{fan_model}</h2>
        </div>
        
        <div class="report-info">
            <div class="report-info-item"><strong>报告生成时间:</strong> {timestamp}</div>
            <div class="report-info-item"><strong>报告类型:</strong> HTML格式分析报告</div>
            <div class="report-info-item"><strong>扇叶型号:</strong> {fan_model}</div>
        </div>
        
        <div class="content">
            <div class="summary-box">
                <h3>分析摘要</h3>
                <p>通过对设备在不同转速下的不平衡量数据进行统计分析，得到以下关键结论：</p>
                <p><strong>推荐最优运行转速：</strong>{optimal_speed_info}</p>
                <p>该转速点是基于IQR（四分位距）和变异系数综合评估确定的，这两个指标反映了数据的离散程度，数值越小表示设备运行越稳定。</p>
            </div>
            
            <h2 class="section-title">统计分析结果</h2>
            <div class="table-responsive">
                {stats_html}
            </div>
            
            {charts_html}
            
            <div class="info-box">
                <h3>关于统计分析方法</h3>
                <p><strong>统计指标说明：</strong></p>
                <ul>
                    <li><strong>平均值：</strong>反映数据的集中趋势</li>
                    <li><strong>中位数：</strong>不受极值影响的中心位置度量</li>
                    <li><strong>标准偏差：</strong>衡量数据的离散程度</li>
                    <li><strong>IQR（四分位距）：</strong>衡量中间50%数据的离散程度，比标准偏差更稳健</li>
                    <li><strong>变异系数(CV)：</strong>标准偏差与平均值的比值，消除了量纲影响，更适合比较不同平均水平的数据波动性</li>
                </ul>
                <p><strong>最优转速选择方法（综合评估）：</strong></p>
                <ul>
                    <li>采用三级评估模型确定最优转速：</li>
                    <li>1. <strong>指标归一化处理：</strong>对每个面(P1/P2/ST)分别计算IQR和变异系数(CV)，并进行归一化处理：得分 = 1 / (1 + 指标值)</li>
                    <li>2. <strong>面内综合得分计算：</strong>对每个面的IQR得分和CV得分进行加权综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分</li>
                    <li>3. <strong>面间综合总得分计算：</strong>根据不同面的重要性进行加权综合：
                        <ul>
                            <li>P1面权重：40%</li>
                            <li>P2面权重：40%</li>
                            <li>ST面权重：20%</li>
                            <li>总得分 = 0.4 × P1得分 + 0.4 × P2得分 + 0.2 × ST得分</li>
                        </ul>
                    </li>
                    <li>4. <strong>最优转速选择：</strong>根据总得分排序，得分最高的转速为最优转速</li>
                </ul>
            </div>
            
            <div class="recommendations-box">
                <h3>优化建议</h3>
                <p><strong>基于数据分析结果，我们提出以下优化建议：</strong></p>
                <ol>
                    <li><strong>首选推荐转速：</strong>建议优先选用推荐的最优运行转速，该转速下设备表现出最佳的运行稳定性</li>
                    <li><strong>次优转速选择：</strong>如果最优转速因工艺限制无法使用，可参考统计表格中其他IQR和CV值较小的转速点</li>
                    <li><strong>定期监测：</strong>建议在选定转速下建立长期监测机制，持续跟踪设备运行状态</li>
                    <li><strong>数据质量提升：</strong>为进一步提高分析准确性，建议增加每组转速下的测量样本数量</li>
                    <li><strong>多维度评估：</strong>除不平衡量外，还可结合温度、振动等其他关键指标进行综合评估</li>
                </ol>
            </div>
            
            <div class="technical-details-box">
                <h3>技术细节说明</h3>
                <p><strong>关于数据处理和分析方法的技术说明：</strong></p>
                <ul>
                    <li>所有数据均经过预处理，去除明显异常值以保证分析结果的可靠性</li>
                    <li>IQR和CV作为互补指标，分别从绝对和相对角度评估数据稳定性</li>
                    <li>加权评分法考虑了不同测量面的重要性差异，更符合实际工程情况</li>
                    <li>图表采用箱线图形式，能够直观展示数据分布特征和离群点情况</li>
                    <li>分析结果受测量精度和样本数量影响，建议结合实际情况进行判断</li>
                </ul>
            </div>
            
            <h2 class="section-title">使用说明</h2>
            <p>详细的分析数据和图表请参考上述内容，包括：</p>
            <ul>
                <li>各转速点的统计分析结果</li>
                <li>不同面的不平衡量图表（PNG和交互式HTML格式）</li>
            </ul>
            
            <h2 class="section-title">注意事项</h2>
            <ul>
                <li>IQR（四分位距）和变异系数反映了数据的离散程度，数值越小表示数据越稳定</li>
                <li>建议关注这些指标较小的转速点，这些点通常代表设备运行较稳定的状态</li>
                <li>如需进一步分析，请结合设备的实际运行情况进行综合判断</li>
                <li>本报告提供的最优转速建议仅供参考，实际应用中还需考虑工艺要求和其他工程因素</li>
                <li>报告中的图表和数据可下载保存，供后续分析和汇报使用</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>本报告由扇叶平衡补土转速评估工具自动生成</p>
        </div>
    </div>
</body>
</html>"""

        # 生成HTML报告文件
        if report_type == "html":
            # 使用report_exporter生成HTML报告
            from report_export import report_exporter
            
            # 确保report_exporter已初始化
            if not hasattr(report_exporter, 'output_folder'):
                report_exporter.output_folder = current_app.config.get("OUTPUT_FOLDER", "outputs")
                report_exporter.history_file = os.path.join(report_exporter.output_folder, 'export_history.json')
                report_exporter.load_export_history()
            
            # 生成HTML文件路径
            filepath = report_exporter.export_html(saved_results)
            
            # 创建可分享链接
            link_id = report_exporter.create_shareable_link(filepath)
            
            # 返回文件下载
            return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))

        # 生成PDF报告
        elif report_type == "pdf":
            try:
                # 使用report_exporter生成PDF报告
                from report_export import report_exporter
                
                # 确保report_exporter已初始化
                if not hasattr(report_exporter, 'output_folder'):
                    report_exporter.output_folder = current_app.config.get("OUTPUT_FOLDER", "outputs")
                    report_exporter.history_file = os.path.join(report_exporter.output_folder, 'export_history.json')
                    report_exporter.load_export_history()
                
                # 生成PDF文件路径
                filepath = report_exporter.export_report_from_session(saved_results)
                
                # 创建可分享链接
                link_id = report_exporter.create_shareable_link(filepath)
                
                # 发送PDF文件
                return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))
            except Exception as e:
                current_app.logger.error(f"PDF导出失败: {str(e)}")
                flash(f"PDF导出失败: {str(e)}")
                return redirect(url_for("main.index"))

        # 生成CSV报告
        elif report_type == "csv":
            try:
                import pandas as pd

                # 从stats_html中提取表格数据，或者直接从parsed_data生成
                parsed_data = saved_results.get("parsed_data")
                if not parsed_data:
                    flash("无分析数据可供导出！")
                    return redirect(url_for("main.index"))

                # 生成统计数据
                stats_data = generate_stats_data(parsed_data)

                # 转换为DataFrame
                df = pd.DataFrame(stats_data)

                # 生成文件名
                filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = os.path.join(current_app.config["OUTPUT_FOLDER"], filename)

                # 保存为CSV
                df.to_csv(filepath, index=False, encoding="utf-8-sig")

                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=filename,
                    mimetype="text/csv",
                )

            except Exception as e:
                flash(f"CSV报告生成失败：{str(e)}")
                return redirect(url_for("main.index"))

        # 生成JSON报告
        elif report_type == "json":
            try:
                # 从session获取分析结果
                parsed_data = saved_results.get("parsed_data")
                stats_data = generate_stats_data(parsed_data)

                # 构建JSON数据
                json_data = {
                    "report_info": {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "fan_model": fan_model,
                        "report_type": "JSON格式分析报告",
                    },
                    "optimal_speed_info": optimal_speed_info,
                    "stats_data": stats_data,
                    "parsed_data": parsed_data,
                }

                # 生成文件名
                filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = os.path.join(current_app.config["OUTPUT_FOLDER"], filename)

                # 保存为JSON
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)

                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=filename,
                    mimetype="application/json",
                )

            except Exception as e:
                flash(f"JSON报告生成失败：{str(e)}")
                return redirect(url_for("main.index"))

        # 生成Excel报告
        elif report_type == "xlsx":
            try:
                import pandas as pd

                # 从stats_html中提取表格数据，或者直接从parsed_data生成
                parsed_data = saved_results.get("parsed_data")
                if not parsed_data:
                    flash("无分析数据可供导出！")
                    return redirect(url_for("main.index"))

                # 生成统计数据
                stats_data = generate_stats_data(parsed_data)

                # 转换为DataFrame
                df = pd.DataFrame(stats_data)

                # 生成文件名
                filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                filepath = os.path.join(current_app.config["OUTPUT_FOLDER"], filename)

                # 保存为Excel
                with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="统计数据")

                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=filename,
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            except Exception as e:
                flash(f"Excel报告生成失败：{str(e)}")
                return redirect(url_for("main.index"))

    except Exception as e:
        flash(f"报告导出失败：{str(e)}")
        return redirect(url_for("main.index"))


@report_bp.route("/download_file/<filename>")
def download_file(filename):
    """下载文件"""
    return send_from_directory(
        current_app.config["OUTPUT_FOLDER"], filename, as_attachment=True
    )


@report_bp.route("/share_report", methods=["POST"])
def share_report():
    """创建可分享的报告链接"""
    try:
        from report_export import report_exporter
        
        # 获取报告文件路径
        report_path = request.json.get("report_path")
        if not report_path:
            return jsonify({"error": "缺少报告文件路径"}), 400
        
        # 确保report_exporter已初始化
        if not hasattr(report_exporter, 'output_folder'):
            report_exporter.output_folder = current_app.config.get("OUTPUT_FOLDER", "outputs")
            report_exporter.history_file = os.path.join(report_exporter.output_folder, 'export_history.json')
            report_exporter.load_export_history()
        
        # 创建可分享链接
        link_id = report_exporter.create_shareable_link(report_path)
        if not link_id:
            return jsonify({"error": "创建可分享链接失败"}), 500
        
        # 生成完整的分享URL
        share_url = url_for("report.view_shared_report", link_id=link_id, _external=True)
        
        return jsonify({"link_id": link_id, "share_url": share_url}), 200
    except Exception as e:
        current_app.logger.error(f"创建可分享链接失败: {str(e)}")
        return jsonify({"error": f"创建可分享链接失败: {str(e)}"}), 500


@report_bp.route("/shared/<link_id>")
def view_shared_report(link_id):
    """查看共享的报告"""
    try:
        from report_export import report_exporter
        
        # 确保report_exporter已初始化
        if not hasattr(report_exporter, 'output_folder'):
            report_exporter.output_folder = current_app.config.get("OUTPUT_FOLDER", "outputs")
            report_exporter.history_file = os.path.join(report_exporter.output_folder, 'export_history.json')
            report_exporter.load_export_history()
        
        # 获取共享报告路径
        report_path = report_exporter.get_shared_report(link_id)
        if not report_path:
            flash("报告链接无效或已过期")
            return redirect(url_for("main.index"))
        
        # 返回报告文件
        return send_file(report_path, as_attachment=False)
    except Exception as e:
        current_app.logger.error(f"查看共享报告失败: {str(e)}")
        flash(f"查看共享报告失败: {str(e)}")
        return redirect(url_for("main.index"))


@report_bp.route("/export_history")
def get_export_history():
    """获取导出历史记录"""
    try:
        from report_export import report_exporter
        
        # 确保report_exporter已初始化
        if not hasattr(report_exporter, 'output_folder'):
            report_exporter.output_folder = current_app.config.get("OUTPUT_FOLDER", "outputs")
            report_exporter.history_file = os.path.join(report_exporter.output_folder, 'export_history.json')
            report_exporter.load_export_history()
        
        # 获取历史记录
        history = report_exporter.get_export_history()
        
        return jsonify({"history": history}), 200
    except Exception as e:
        current_app.logger.error(f"获取导出历史失败: {str(e)}")
        return jsonify({"error": f"获取导出历史失败: {str(e)}"}), 500


@report_bp.route("/view_chart/<filename>")
def view_chart(filename):
    """查看PNG图表"""
    return send_from_directory(current_app.config["OUTPUT_FOLDER"], filename)


@report_bp.route("/view_chart_html/<filename>")
def view_chart_html(filename):
    """查看HTML交互式图表"""
    return send_from_directory(current_app.config["OUTPUT_FOLDER"], filename)
