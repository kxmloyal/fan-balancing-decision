#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTML 报告构建器

从 report_export.py（1350行）拆分而来——P2-14 方案 A 三层委派架构。
负责 ReportExporter.export_html() 和所有 _write_html_* 方法。

职责：
  - export_html(): 完整 HTML 报告导出流程（写文件 + 历史记录）
  - _write_html_header / _write_html_charts / _write_html_summary /
    _write_html_stats / _write_html_methodology / _write_html_footer
  - 依赖 ReportExporter 实例的 output_folder、_base64_cache、add_to_history 等属性
"""

import base64
import logging
import os
from datetime import datetime

from utils.model_utils import sanitize_model_name

logger = logging.getLogger(__name__)


class ReportHtmlBuilder:
    """HTML 报告构建器——负责 HTML 报告的结构化生成"""

    def __init__(self, exporter):
        """
        Args:
            exporter: ReportExporter 实例，提供 output_folder/_base64_cache/add_to_history
        """
        self._exporter = exporter

    @property
    def output_folder(self):
        return self._exporter.output_folder

    @property
    def _base64_cache(self):
        return self._exporter._base64_cache

    def add_to_history(self, export_info):
        self._exporter.add_to_history(export_info)

    def _merge_report_config(self, user_config):
        return self._exporter._merge_report_config(user_config)

    # ========================================================================
    #  HTML 报告导出主流程
    # ========================================================================

    def export_html(self, session_data, output_filename=None, task_id=None, report_config=None):
        try:
            config = self._merge_report_config(report_config)

            fan_model = str(session_data.get("fan_model", "未知"))
            safe_model = sanitize_model_name(fan_model)

            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{safe_model}_动平衡分析报告_{timestamp}.html"

            if not output_filename.endswith(".html"):
                output_filename += ".html"

            model_dir = sanitize_model_name(fan_model)
            model_output_dir = os.path.join(self.output_folder, model_dir)
            os.makedirs(model_output_dir, exist_ok=True)

            output_path = os.path.join(model_output_dir, output_filename)

            with open(output_path, "w", encoding="utf-8") as f:
                self._write_html_header(f, session_data, config)

                if config.get("include_summary", True):
                    self._write_html_summary(f, session_data)

                if config.get("include_stats", True):
                    self._write_html_stats(f, session_data)

                if config.get("include_charts", True):
                    self._write_html_charts(f, session_data, config)

                if config.get("include_methodology", True):
                    self._write_html_methodology(f)

                self._write_html_footer(f)

            export_info = {
                "type": "html",
                "filename": os.path.basename(output_path),
                "path": output_path,
                "fan_model": fan_model,
                "model_dir": model_dir,
                "report_config": config,
            }
            self.add_to_history(export_info)

            return output_path
        except Exception as e:
            logger.error("导出HTML报告失败: %s", str(e))
            raise

    # ========================================================================
    #  HTML 片段写入方法
    # ========================================================================

    def _write_html_header(self, file_obj, session_data, config=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fan_model = str(session_data.get("fan_model", "未知"))
        balance_machine_model = str(session_data.get("balance_machine_model", ""))
        config = config or {}

        title = str(config.get("title", "设备不平衡量分析报告"))

        evaluation_report = session_data.get("evaluation_report", {})
        best_speeds = evaluation_report.get("best_speeds", [])
        optimal_speed = str(best_speeds[0] if best_speeds else "未确定")

        file_obj.write(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js"></script>
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
            background-color: #2563eb;
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
            color: #2563eb;
            border-left: 4px solid #2563eb;
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
            background-color: #2563eb;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        tr:hover {{
            background-color: #e9ecef;
        }}
        table thead tr:first-child th {{
            background-color: #1d4ed8;
            font-size: 14px;
        }}
        table thead tr:nth-child(2) th {{
            background-color: #2563eb;
            font-size: 12px;
        }}
        table thead tr:first-child th:first-child {{
            width: 80px;
        }}
        table thead tr:first-child th:last-child,
        table thead tr:nth-child(2) th:last-child {{
            width: 100px;
        }}
        table tbody tr td:last-child {{
            font-weight: bold;
            background-color: #f1f8ff;
        }}
        table tbody tr.table-success {{
            background-color: #d4edda !important;
        }}
        table tbody tr.table-success td:last-child {{
            background-color: #c3e6cb !important;
        }}
        table tbody tr td.table-warning {{
            background-color: #fff3cd !important;
            font-weight: bold;
        }}
        .table-responsive {{
            overflow-x: auto;
            margin: 15px 0;
        }}
        .chart-group {{
            margin: 15px 0;
            padding: 12px;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            background-color: #f8f9fa;
        }}
        .chart-group h3 {{
            color: #2563eb;
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
            margin: 8px 0;
        }}
        .chart-img-container img {{
            max-width: 100%;
            height: auto;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-radius: 3px;
        }}
        .chart-links {{
            text-align: center;
            margin: 10px 0;
        }}
        .chart-links a {{
            display: inline-block;
            margin: 0 5px;
            padding: 5px 10px;
            background-color: #2563eb;
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
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .chart-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .chart-col {{
            flex: 1;
            min-width: 300px;
        }}
        .chart-stacked .chart-container {{
            margin-bottom: 15px;
        }}
        .chart-parallel .chart-col {{
            display: flex;
            flex-direction: column;
        }}
        .chart-container {{
            margin: 10px 0;
            padding: 12px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
        @media (min-width: 1400px) {{
            .container {{ max-width: 1320px; }}
            .chart-col {{ min-width: 350px; }}
        }}
        @media (min-width: 1600px) {{
            .container {{ max-width: 1520px; }}
            .chart-col {{ min-width: 400px; }}
        }}
        @media (min-width: 1900px) {{
            .container {{ max-width: 1720px; }}
            .chart-col {{ min-width: 450px; }}
        }}
        @media print {{
            @page {{
                size: A4 landscape;
                margin: 12mm 10mm;
            }}
            body {{ background-color: white; font-size: 10pt; print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
            .container {{ box-shadow: none; max-width: none; width: 100%; padding: 0; }}
            .chart-links a {{ background-color: #ccc; color: #333; text-decoration: none; }}
            .table-responsive {{ overflow: visible; width: 100%; }}
            table {{ page-break-inside: avoid; width: 100% !important; font-size: 9pt; }}
            table thead {{ display: table-header-group; }}
            table tbody {{ page-break-inside: auto; }}
            tr {{ page-break-inside: avoid; page-break-after: auto; }}
            .chart-container {{ box-shadow: none; padding: 12px; margin: 8px 0; page-break-inside: avoid; }}
            .chart-img-container img {{ max-width: 100% !important; height: auto !important; max-height: 380px; page-break-inside: avoid; }}
            .header {{ background-color: #2563eb !important; print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
            .header, .report-info, .content {{ page-break-inside: avoid; }}
            h1, h2, h3, h4 {{ page-break-after: avoid; page-break-inside: avoid; }}
            .section-title {{ page-break-after: avoid; }}
            ul, ol, p {{ page-break-inside: avoid; }}
            .chart-display-control {{ display: none; }}
            .chart-row {{ display: block; }}
            .chart-col {{ flex: none; min-width: auto; width: 100%; page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <h2>{fan_model}</h2>
        </div>

        <div class="report-info">
            <div class="report-info-item"><strong>报告生成时间:</strong> {timestamp}</div>
            <div class="report-info-item"><strong>报告类型:</strong> HTML格式分析报告</div>
            <div class="report-info-item"><strong>扇叶型号:</strong> {fan_model}</div>
            <div class="report-info-item"><strong>平衡机型号:</strong> {balance_machine_model or "未指定"}</div>
        </div>

        <div class="content">
""")

    def _write_html_charts(self, file_obj, session_data, config=None):
        config = config or {}
        plots = session_data.get("plots", {})
        output_folder = getattr(self, "output_folder", "outputs")
        chart_layout = session_data.get("chart_layout", "stacked")

        fan_model = session_data.get("fan_model", "")
        model_dir = sanitize_model_name(fan_model) if fan_model else ""
        model_output_dir = os.path.join(output_folder, model_dir) if model_dir else output_folder

        if not plots:
            file_obj.write("<p>暂无图表数据</p>\n")
            return

        surface_name_map = {"p1": "P1", "p2": "P2", "sum": "ST", "st": "ST"}

        chart_name_cn = {
            "box": "箱线图",
            "violin": "小提琴图",
            "scatter": "散点图",
            "trend": "趋势图",
            "histogram": "直方图",
            "heatmap": "热力图",
        }

        is_parallel = chart_layout == "parallel"
        if is_parallel:
            file_obj.write('<div class="chart-parallel" id="parallelChartContainer">\n')
            file_obj.write('    <div class="chart-row">\n')

        for surface_key, surface_plots in plots.items():
            if not isinstance(surface_plots, dict):
                continue
            chart_items = []
            for chart_type, chart_info in surface_plots.items():
                if not isinstance(chart_info, dict):
                    continue
                chart_data = chart_info.get("chart_data", "")
                if chart_data:
                    chart_items.append((chart_type, chart_info))
            if not chart_items:
                continue

            surface_name = surface_name_map.get(surface_key, surface_key.replace("面", ""))

            if is_parallel:
                file_obj.write('        <div class="chart-col">\n')
                file_obj.write('            <div class="chart-group">\n')
            else:
                file_obj.write('    <div class="chart-group">\n')

            for chart_type, chart_info in chart_items:
                cn_name = chart_name_cn.get(chart_type, chart_type)
                png_file = chart_info.get("png", "")
                html_file = chart_info.get("html", "")

                img_base64 = ""
                if png_file:
                    png_path = os.path.join(model_output_dir, png_file)
                    if not os.path.exists(png_path):
                        png_path = os.path.join(output_folder, png_file)
                    if os.path.exists(png_path):
                        try:
                            png_mtime = os.path.getmtime(png_path)
                            cache_key = (png_path, png_mtime)
                            if cache_key in self._base64_cache:
                                img_base64 = self._base64_cache[cache_key]
                            else:
                                with open(png_path, "rb") as img_f:
                                    img_base64 = base64.b64encode(img_f.read()).decode("utf-8")
                                self._base64_cache[cache_key] = img_base64
                                if len(self._base64_cache) > 200:
                                    keys = list(self._base64_cache.keys())
                                    for k in keys[: len(keys) - 100]:
                                        self._base64_cache.pop(k, None)
                        except Exception:
                            img_base64 = ""

                file_obj.write('        <div class="chart-container">\n')
                file_obj.write(f"            <h4>{surface_name}面{cn_name}</h4>\n")
                if img_base64:
                    mime = "image/svg+xml" if png_file.endswith(".svg") else "image/png"
                    file_obj.write('            <div class="chart-img-container">\n')
                    file_obj.write(
                        f'                <img src="data:{mime};base64,{img_base64}" alt="{surface_name}面{cn_name}">\n'
                    )
                    file_obj.write("            </div>\n")
                else:
                    file_obj.write('            <div class="chart-img-container">\n')
                    file_obj.write("                <p>(图表暂无预览)</p>\n")
                    file_obj.write("            </div>\n")
                file_obj.write("        </div>\n")

            if is_parallel:
                file_obj.write("            </div>\n")
                file_obj.write("        </div>\n")
            else:
                file_obj.write("    </div>\n")

        if is_parallel:
            file_obj.write("    </div>\n")
            file_obj.write("</div>\n")

    def _write_html_summary(self, file_obj, session_data):
        evaluation_report = session_data.get("evaluation_report", {})
        best_speeds = evaluation_report.get("best_speeds", [])
        best_speed = str(best_speeds[0] if best_speeds else "未找到")

        file_obj.write('    <div class="summary-box">\n')
        file_obj.write("        <h3>分析摘要</h3>\n")
        file_obj.write(
            "        <p>通过对设备在不同转速下的不平衡量数据进行统计分析，得到以下关键结论：</p>\n"
        )
        file_obj.write(f"        <p><strong>推荐最优运行转速：</strong>{best_speed}</p>\n")
        file_obj.write(
            "        <p>该转速点是基于IQR（四分位距）和变异系数综合评估确定的，数值越小表示设备运行越稳定。</p>\n"
        )
        file_obj.write("    </div>\n")

    def _write_html_stats(self, file_obj, session_data):
        stats_html = str(session_data.get("stats_html", ""))

        file_obj.write('    <h2 class="section-title">统计分析结果</h2>\n')
        if stats_html:
            file_obj.write('    <div class="table-responsive">\n')
            file_obj.write(stats_html)
            file_obj.write("    </div>\n")
        else:
            file_obj.write("    <p>暂无统计分析结果</p>\n")

    def _write_html_methodology(self, file_obj):
        file_obj.write('    <h2 class="section-title">关于统计分析方法</h2>\n')
        file_obj.write('    <div class="info-box">\n')
        file_obj.write("        <h3>统计指标说明</h3>\n")
        file_obj.write("        <ul>\n")
        file_obj.write("            <li><strong>平均值：</strong>反映数据的集中趋势</li>\n")
        file_obj.write("            <li><strong>中位数：</strong>不受极值影响的中心位置度量</li>\n")
        file_obj.write("            <li><strong>标准偏差：</strong>衡量数据的离散程度</li>\n")
        file_obj.write(
            "            <li><strong>IQR（四分位距）：</strong>衡量中间50%数据的离散程度，比标准偏差更稳健</li>\n"
        )
        file_obj.write(
            "            <li><strong>变异系数(CV)：</strong>标准偏差与平均值的比值，消除了量纲影响</li>\n"
        )
        file_obj.write("        </ul>\n")
        file_obj.write("        <p><strong>最优转速选择方法（综合评估）：</strong></p>\n")
        file_obj.write("        <ul>\n")
        file_obj.write("            <li>采用三维加权评分模型确定最优转速：</li>\n")
        file_obj.write(
            "            <li>1. <strong>指标归一化处理：</strong>得分 = 1 / (1 + 指标值)</li>\n"
        )
        file_obj.write(
            "            <li>2. <strong>端面内综合得分：</strong>面得分 = 0.4 × IQR得分 + 0.4 × CV得分 + 0.2 × 幅值得分</li>\n"
        )
        file_obj.write(
            "            <li>3. <strong>端面间综合总得分：</strong>总得分 = 0.4 × P1得分 + 0.4 × P2得分 + 0.2 × ST得分</li>\n"
        )
        file_obj.write(
            "            <li>4. <strong>最优转速选择：</strong>总得分最高的转速即为最优转速</li>\n"
        )
        file_obj.write("        </ul>\n")
        file_obj.write("    </div>\n")

        file_obj.write('    <div class="recommendations-box">\n')
        file_obj.write("        <h3>优化建议</h3>\n")
        file_obj.write("        <p><strong>基于数据分析结果，我们提出以下优化建议：</strong></p>\n")
        file_obj.write("        <ol>\n")
        file_obj.write(
            "            <li><strong>首选推荐转速：</strong>优先选用推荐的最优运行转速</li>\n"
        )
        file_obj.write(
            "            <li><strong>次优转速选择：</strong>如最优转速因工艺限制无法使用，可参考IQR和CV值较小的转速点</li>\n"
        )
        file_obj.write(
            "            <li><strong>定期监测：</strong>建议在选定转速下建立长期监测机制</li>\n"
        )
        file_obj.write(
            "            <li><strong>数据质量提升：</strong>增加每组转速下的测量样本数量可提高分析准确性</li>\n"
        )
        file_obj.write(
            "            <li><strong>多维度评估：</strong>除不平衡量外，可结合温度、振动等指标综合评估</li>\n"
        )
        file_obj.write("        </ol>\n")
        file_obj.write("    </div>\n")

        file_obj.write('    <div class="technical-details-box">\n')
        file_obj.write("        <h3>技术细节说明</h3>\n")
        file_obj.write("        <ul>\n")
        file_obj.write(
            "            <li>所有数据均经过预处理，去除明显异常值以保证分析结果的可靠性</li>\n"
        )
        file_obj.write(
            "            <li>IQR和CV作为互补指标，分别从绝对和相对角度评估数据稳定性</li>\n"
        )
        file_obj.write(
            "            <li>加权评分法考虑了不同测量面的重要性差异，更符合实际工程情况</li>\n"
        )
        file_obj.write(
            "            <li>图表采用箱线图形式，能够直观展示数据分布特征和离群点情况</li>\n"
        )
        file_obj.write(
            "            <li>分析结果受测量精度和样本数量影响，建议结合实际情况进行判断</li>\n"
        )
        file_obj.write("        </ul>\n")
        file_obj.write("    </div>\n")

        file_obj.write('    <h2 class="section-title">使用说明</h2>\n')
        file_obj.write("    <p>详细的分析数据和图表请参考上述内容，包括：</p>\n")
        file_obj.write("    <ul>\n")
        file_obj.write("        <li>各转速点的统计分析结果</li>\n")
        file_obj.write("        <li>不同面的不平衡量图表（PNG和交互式HTML格式）</li>\n")
        file_obj.write("    </ul>\n")

        file_obj.write('    <h2 class="section-title">注意事项</h2>\n')
        file_obj.write("    <ul>\n")
        file_obj.write(
            "        <li>IQR（四分位距）和变异系数反映了数据的离散程度，数值越小表示数据越稳定</li>\n"
        )
        file_obj.write(
            "        <li>建议关注这些指标较小的转速点，这些点通常代表设备运行较稳定的状态</li>\n"
        )
        file_obj.write("        <li>如需进一步分析，请结合设备的实际运行情况进行综合判断</li>\n")
        file_obj.write(
            "        <li>本报告提供的最优转速建议仅供参考，实际应用中还需考虑工艺要求和其他工程因素</li>\n"
        )
        file_obj.write("        <li>报告中的图表和数据可下载保存，供后续分析和汇报使用</li>\n")
        file_obj.write("    </ul>\n")

    def _write_html_footer(self, file_obj):
        file_obj.write("        </div>\n")
        file_obj.write('        <div class="footer">\n')
        file_obj.write(
            "            <p>本报告由扇叶平衡补土转速评估工具自动生成<br>-----技术支持By-KXM</p>\n"
        )
        file_obj.write("        </div>\n")
        file_obj.write("    </div>\n")
        file_obj.write("</body>\n")
        file_obj.write("</html>\n")
