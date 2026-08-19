#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告导出器核心（ReportExporter）

从 report_export.py（1350行）拆分而来——P2-14 方案 A 三层委派架构。
包含 ReportExporter 核心类及 HtmlExporter、ShareLinkManager。

职责：
  - __init__ / init_app: 初始化与 Flask 集成
  - export: 通用导出编排（委派给 html_builder / data_exporter）
  - share link 管理（委托给 ShareLinkManager）
  - 导出历史管理
  - 会话数据清理（_sanitize_session_data / _sanitize_html）
  - PDF 降级处理（export_report_from_session）
"""

import base64
import html as _html
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timedelta

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

    def export(self, session_data, output_filename=None, task_id=None):
        try:
            html_content = self.build_report_html(session_data)
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

    def build_report_html(self, session_data):
        t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fan_model = str(session_data.get("fan_model", "未知"))
        balance_machine_model = str(session_data.get("balance_machine_model", ""))
        er = session_data.get("evaluation_report", {})
        best_speeds = er.get("best_speeds", [])
        best_speed = str(best_speeds[0] if best_speeds else "未找到")

        charts_html = self._build_charts(session_data)

        stats_html = str(session_data.get("stats_html", ""))
        stats_section = ""
        if stats_html:
            stats_section = f'            <h2 class="section-title">统计分析结果</h2>\n            <div class="table-responsive">{stats_html}</div>\n'
        else:
            stats_section = '            <h2 class="section-title">统计分析结果</h2>\n            <p>暂无统计分析结果</p>\n'

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
{_html_exporter_css()}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>扇叶动平衡补土工艺统计分析报告</h1>
            <h2>{fan_model}</h2>
        </div>

        <div class="report-info">
            <div class="report-info-item"><strong>报告生成时间:</strong> {t}</div>
            <div class="report-info-item"><strong>报告类型:</strong> 多转速不平衡量综合统计分析</div>
            <div class="report-info-item"><strong>扇叶型号:</strong> {fan_model}</div>
            <div class="report-info-item"><strong>平衡机型号:</strong> {balance_machine_model or "未指定"}</div>
            <div class="report-info-item"><strong>推荐作业转速:</strong> <span class="highlight-speed">{best_speed}</span></div>
        </div>

        <div class="content">
            <div class="summary-box">
                <h3>一、分析摘要</h3>
                <p>基于该扇叶型号在多个转速下各端面（P1面、P2面、ST面）的不平衡量测试数据，通过以下统计学方法进行综合评估：</p>
                <ul>
                    <li><strong>四分位距（IQR）分析：</strong>评估各转速下不平衡量的离散程度，IQR 越小表示数据越集中稳定</li>
                    <li><strong>变异系数（CV）分析：</strong>消除量纲影响后的相对离散度，CV 越小表示相对波动越小</li>
                    <li><strong>幅值合理性评估：</strong>检验数据分布对称性，抑制偏离中位数的异常波动</li>
                </ul>
                <p><strong>推荐最优作业转速：{best_speed}</strong> — 该转速在 IQR 稳定性、CV 稳定性及幅值合理性三个维度上综合得分最高。</p>
            </div>

{stats_section}
{charts_html}
            <h2 class="section-title">二、评分方法论</h2>
            <div class="methodology-box">
                <h3>最优转速三维加权评分模型</h3>
                <p>本系统采用三维度加权评分法对各候选转速进行综合评估，维度及权重如下：</p>
                <table class="method-table">
                    <tr><th>评分维度</th><th>权重</th><th>评估指标</th><th>说明</th></tr>
                    <tr><td>IQR 稳定性</td><td>40%</td><td>四分位距 (IQR)</td><td>衡量中间 50% 数据的离散程度，对异常值稳健</td></tr>
                    <tr><td>CV 稳定性</td><td>40%</td><td>变异系数 (CV = σ/μ × 100%)</td><td>相对离散度指标，消除量纲差异</td></tr>
                    <tr><td>幅值合理性</td><td>20%</td><td>1/(1+|mean−median|/median)</td><td>抑制均值偏离中位数的分布不对称</td></tr>
                </table>
                <p><strong>端面综合权重：</strong></p>
                <table class="method-table">
                    <tr><th>端面</th><th>权重</th><th>说明</th></tr>
                    <tr><td>P1面</td><td>40%</td><td>前缘迎风面，对平衡性能影响最大</td></tr>
                    <tr><td>P2面</td><td>40%</td><td>后缘尾流面，与P1面同等重要</td></tr>
                    <tr><td>ST面</td><td>20%</td><td>侧向端面，辅助参考</td></tr>
                </table>
                <p><strong>计算公式：</strong></p>
                <div class="formula-box">
                    <p>端面得分 = IQR得分 × 0.40 + CV得分 × 0.40 + 幅值得分 × 0.20</p>
                    <p>总得分 = P1得分 × 0.40 + P2得分 × 0.40 + ST得分 × 0.20</p>
                    <p>各指标得分 = 1 / (1 + 归一化指标值)</p>
                </div>
            </div>

            <h2 class="section-title">三、统计指标说明</h2>
            <div class="info-box">
                <table class="method-table">
                    <tr><th>指标</th><th>公式</th><th>解释</th></tr>
                    <tr><td>平均值 (Mean)</td><td>μ = Σxᵢ / n</td><td>反映数据的集中趋势</td></tr>
                    <tr><td>中位数 (Median)</td><td>排序后位于中间的值</td><td>不受极值影响的中心位置度量</td></tr>
                    <tr><td>标准差 (Std)</td><td>σ = √(Σ(xᵢ-μ)²/(n-1))</td><td>衡量数据的绝对离散程度</td></tr>
                    <tr><td>IQR</td><td>Q₃ − Q₁</td><td>中间50%数据的离散程度，对异常值稳健</td></tr>
                    <tr><td>变异系数 (CV)</td><td>CV = σ / μ × 100%</td><td>消除量纲影响后的相对离散度</td></tr>
                </table>
            </div>

            <h2 class="section-title">四、数据质量评估</h2>
            <div class="recommendations-box">
                <p><strong>基于分析结果的数据质量评估：</strong></p>
                <ol>
                    <li><strong>样本充分性：</strong>建议每转速至少 5 个以上样本以确保统计可靠性</li>
                    <li><strong>异常值检测：</strong>采用 Modified Z-score 法（阈值 2.5）识别潜在异常数据点</li>
                    <li><strong>正态性检验：</strong>大样本（n≥8）使用 D'Agostino-Pearson 检验，小样本使用稳健 MAD 估计</li>
                    <li><strong>趋势分析：</strong>含二次多项式非线性检测，识别 U 型/倒 U 型趋势模式</li>
                </ol>
            </div>

            <h2 class="section-title">五、工程优化建议</h2>
            <div class="technical-details-box">
                <ol>
                    <li><strong>首选推荐转速：</strong>优先选用推荐的最优作业转速进行平衡补土</li>
                    <li><strong>次优备用方案：</strong>如最优转速受工艺限制无法使用，参考 IQR 和 CV 值较小的次优转速点</li>
                    <li><strong>长期监测建议：</strong>在选定转速下建立定期监测机制，积累历史数据评估稳定性</li>
                    <li><strong>样本量提升：</strong>增加每组转速下的测量样本数量可提高统计分析的可信度</li>
                    <li><strong>多维度评估：</strong>结合振动、温度、噪声等指标综合评估补土工艺效果</li>
                </ol>
            </div>

            <h2 class="section-title">六、免责声明</h2>
            <ul>
                <li>本报告基于统计分析方法自动生成，推荐结果仅供参考</li>
                <li>实际补土工艺决策需结合设备特性、工艺要求和工程经验综合判断</li>
                <li>分析结果受测量精度和样本数量影响，数据质量不佳时置信度降低</li>
                <li>报告中的图表支持可交互操作，可在浏览器中缩放和查看详细数据</li>
            </ul>
        </div>

        <div class="footer">
            <p>本报告由扇叶平衡补土转速评估工具自动生成<br>-----技术支持By-KXM</p>
        </div>
    </div>
</body>
</html>"""

    def _build_charts(self, session_data):
        plots = session_data.get("plots", {})
        if not plots:
            return ""

        fan_model = session_data.get("fan_model", "")
        model_dir = sanitize_model_name(fan_model) if fan_model else ""
        model_output_dir = (
            os.path.join(self.output_folder, model_dir) if model_dir else self.output_folder
        )

        surface_map = {"p1": "P1", "p2": "P2", "sum": "ST", "st": "ST"}
        cn_map = {
            "box": "箱线图",
            "violin": "小提琴图",
            "scatter": "散点图",
            "trend": "趋势图",
            "histogram": "直方图",
            "heatmap": "热力图",
        }
        parts = []

        for sk, sp in plots.items():
            if not isinstance(sp, dict):
                continue
            items = [
                (ct, ci)
                for ct, ci in sp.items()
                if isinstance(ci, dict) and ci.get("chart_data", "")
            ]
            if not items:
                continue
            sn = surface_map.get(sk, sk.replace("面", ""))
            parts.append('            <div class="chart-group">\n')

            for ct, ci in items:
                cn = cn_map.get(ct, ct)
                png = ci.get("png", "")
                img_b64 = ""
                if png:
                    pp = os.path.join(model_output_dir, png)
                    if not os.path.exists(pp):
                        pp = os.path.join(self.output_folder, png)
                    if os.path.exists(pp):
                        try:
                            with open(pp, "rb") as f:
                                img_b64 = base64.b64encode(f.read()).decode("utf-8")
                        except Exception:
                            pass
                parts.append('                <div class="chart-container">\n')
                parts.append(f"                    <h4>{sn}面{cn}</h4>\n")
                if img_b64:
                    m = "image/svg+xml" if png.endswith(".svg") else "image/png"
                    parts.append('                    <div class="chart-img-container">\n')
                    parts.append(
                        f'                        <img src="data:{m};base64,{img_b64}" alt="{sn}面{cn}">\n'
                    )
                    parts.append("                    </div>\n")
                parts.append("                </div>\n")
            parts.append("            </div>\n")
        return "".join(parts)


# ============================================================================
#  ShareLinkManager —— 分享链接管理器
# ============================================================================


class ShareLinkManager:
    """分享链接管理器——独立管理报告分享链接的创建、查询和撤销"""

    def __init__(self, output_folder="outputs"):
        self.output_folder = output_folder
        self._links_file = os.path.join(self.output_folder, "shareable_links.json")

    def _read_links(self):
        if not os.path.exists(self._links_file):
            return []
        try:
            with open(self._links_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def _write_links(self, links):
        try:
            os.makedirs(self.output_folder, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.error(f"无法创建分享目录 {self.output_folder}: {str(e)}")
            raise RuntimeError("分享功能暂不可用：无法写入存储目录") from e
        try:
            with open(self._links_file, "w", encoding="utf-8") as f:
                json.dump(links, f, ensure_ascii=False, indent=2)
        except (OSError, IOError) as e:
            logger.error(f"写入分享链接文件失败 {self._links_file}: {str(e)}")
            raise RuntimeError("分享链接操作失败：磁盘写入错误") from e

    def create_link(self, report_path, ttl_days=7):
        link_id = str(uuid.uuid4())
        expires_at = (datetime.now() + timedelta(days=ttl_days)).isoformat()

        share_info = {
            "link_id": link_id,
            "report_path": report_path,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "ttl_days": ttl_days,
            "filename": os.path.basename(report_path),
        }

        links = self._read_links()
        now = datetime.now()
        links = [
            l
            for l in links
            if "expires_at" not in l or datetime.fromisoformat(l["expires_at"]) > now
        ]
        links.append(share_info)
        self._write_links(links)
        return link_id

    def revoke_link(self, link_id):
        links = self._read_links()
        original_count = len(links)
        links = [l for l in links if l.get("link_id") != link_id]
        if len(links) == original_count:
            return False
        self._write_links(links)
        return True

    def get_link(self, link_id):
        links = self._read_links()
        now = datetime.now()
        for link in links:
            if link.get("link_id") == link_id:
                if "expires_at" in link and datetime.fromisoformat(link["expires_at"]) <= now:
                    return None
                return link
        return None

    def list_links(self):
        links = self._read_links()
        now = datetime.now()
        return [
            l
            for l in links
            if "expires_at" not in l or datetime.fromisoformat(l["expires_at"]) > now
        ]


# ============================================================================
#  ReportExporter —— 报告导出器核心
# ============================================================================


class ReportExporter:
    def __init__(self, app=None):
        self.app = app
        self.output_folder = "outputs"

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
            from services.report_html_builder import ReportHtmlBuilder

            self._html_builder = ReportHtmlBuilder(self)
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

    def export_report_from_session(self, session_data, output_filename=None):
        html_path = self.export_html(session_data, output_filename)

        if WEASYPRINT_AVAILABLE:
            try:
                from weasyprint import HTML

                pdf_filename = os.path.splitext(os.path.basename(html_path))[0] + ".pdf"
                pdf_path = os.path.join(self.output_folder, pdf_filename)
                HTML(filename=html_path).write_pdf(pdf_path)

                fan_model = str(session_data.get("fan_model", "未知"))
                model_dir = sanitize_model_name(fan_model)
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
                logger.warning(f"PDF转换失败，返回HTML: {str(e)}")
                return html_path
        return html_path

    # ========================================================================
    #  历史管理
    # ========================================================================

    def _clean_base64_cache(self):
        now = time.time()
        if self._base64_cache_max_age > 0:
            expired = [
                k
                for k, v in list(self._base64_cache.items())
                if isinstance(k, tuple) and len(k) >= 2 and now - k[1] > self._base64_cache_max_age
            ]
            for k in expired:
                self._base64_cache.pop(k, None)
        if len(self._base64_cache) > self._base64_cache_max_size:
            keys = list(self._base64_cache.keys())
            for k in keys[: len(keys) - 100]:
                self._base64_cache.pop(k, None)

    def add_to_history(self, export_info):
        export_info["timestamp"] = datetime.now().isoformat()
        self.export_history.insert(0, export_info)
        if len(self.export_history) > 100:
            self.export_history = self.export_history[:100]
        self.save_export_history()

    def save_export_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.export_history, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"保存导出历史失败: {str(e)}")

    def load_export_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.export_history = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"加载导出历史失败: {str(e)}")
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
