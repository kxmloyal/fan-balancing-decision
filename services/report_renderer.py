#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""数据驱动报告渲染器（方案 A+/B+/C+ 统一落点）

替换旧 ReportHtmlBuilder 作为 ReportExporter 的 HTML 构建器，产出：
  - 封面页 + 目录（章节锚点导航）
  - 数据驱动摘要（最优转速 / 综合得分 / 各面 IQR、CV 最小转速）
  - 最优转速三维评分明细表（IQR/CV/幅值得分，黄色高亮最优行）
  - 统计分析结果（样本量说明附注于统计方法末尾）
  - 双轨数据图表（静态 base64 兜底 + Plotly 交互，复用 PLOTLY_DUAL_TRACK_SCRIPT）
  - 统计分析方法（补齐幅值维度、归一化公式、异常过滤说明）
  - 优化建议 + 注意事项、页眉页脚、报告版本号
统一使用 EXPORTER_CSS 设计令牌，消除旧双 CSS 视觉分裂。
"""

import base64
import json
import os
from datetime import datetime

from report_export_css import EXPORTER_CSS
from services.report_constants import PLOTLY_CDN_URL, PLOTLY_DUAL_TRACK_SCRIPT
from utils.model_utils import sanitize_model_name

REPORT_VERSION = "v2.0"
SYSTEM_NAME = "扇叶平衡补土转速评估工具"

_FACE_LABELS = [("P1", "P1面"), ("P2", "P2面"), ("ST", "ST面")]
_SURFACE_NAMES = {"p1": "P1面", "p2": "P2面", "sum": "ST面", "st": "ST面", "single": "单面"}
_CHART_CN = {
    "box": "箱线图", "violin": "小提琴图", "scatter": "散点图", "trend": "趋势图",
    "histogram": "直方图", "heatmap": "热力图", "bubble": "气泡图", "3d": "3D散点图",
    "parallel": "平行坐标图",
}


def _fmt(value, digits=3):
    """数字格式化，None/NaN/非法值显示为 —"""
    try:
        if value is None:
            return "—"
        v = float(value)
        if v != v:  # NaN
            return "—"
        return f"{v:.{digits}f}"
    except (ValueError, TypeError):
        return "—"


def _safe(text):
    text = str(text or "")
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class ReportRenderer:
    """数据驱动 HTML 报告渲染器（ReportExporter 的 html_builder 替代实现）。"""

    def __init__(self, exporter):
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

    # ================= 对外接口 =================

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
                f.write(self.render(session_data, config))

            self.add_to_history({
                "type": "html",
                "filename": os.path.basename(output_path),
                "path": output_path,
                "fan_model": fan_model,
                "model_dir": model_dir,
                "report_config": config,
            })
            return output_path
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("导出HTML报告失败: %s", str(e))
            raise

    def render(self, session_data, report_config=None):
        ctx = self._build_context(session_data, report_config)
        return self._assemble(ctx)

    # ================= 上下文构建 =================

    @staticmethod
    def _has_face_scores(scores, face):
        """该面是否有得分数据：任一转速的 face_score 非 None 即视为有数据"""
        return any((detail.get(face) or {}).get("face_score") is not None for detail in scores.values())

    def _build_context(self, session_data, report_config=None):
        sd = session_data or {}
        cfg = self._merge_report_config(report_config)
        evaluation = sd.get("evaluation_report", {}) or {}
        best_speeds = evaluation.get("best_speeds") or []
        scores = evaluation.get("speed_detailed_scores") or {}
        plots = sd.get("plots") or {}

        # 面是否有数据：以面得分（face_score）为准，evaluation.has_* 仅作兼容兜底
        # （scores 键是转速而非面，旧实现 any(k.startswith("P*")) 是无效判定）
        has_p1 = self._has_face_scores(scores, "P1") or bool(evaluation.get("has_p1"))
        has_p2 = self._has_face_scores(scores, "P2") or bool(evaluation.get("has_p2"))
        has_st = self._has_face_scores(scores, "ST") or bool(evaluation.get("has_st"))
        face_labels = [l for f, l in _FACE_LABELS if (f == "P1" and has_p1) or (f == "P2" and has_p2) or (f == "ST" and has_st)]
        if not face_labels:
            face_labels = [l for _, l in _FACE_LABELS]

        sections = [
            ("一、分析摘要", "sec-summary", cfg.get("include_summary", True)),
            # 评估报告开关 → 控制评分明细章节；include_scores 兼容旧配置名
            ("二、最优转速评分明细", "sec-scores", bool(scores) and cfg.get("include_scores", cfg.get("include_evaluation", True))),
            ("三、统计分析结果", "sec-stats", cfg.get("include_stats", True)),
            ("四、数据图表", "sec-charts", bool(plots) and cfg.get("include_charts", True)),
            ("五、统计分析方法", "sec-method", cfg.get("include_methodology", True)),
            ("六、优化建议与注意事项", "sec-advice", cfg.get("include_recommendations", True)),
        ]
        return {
            "fan_model": sd.get("fan_model", "未填写") or "未填写",
            "balancer": sd.get("balance_machine_model", "未填写") or "未填写",
            "model_dir": os.path.join(self.output_folder, sanitize_model_name(sd.get("fan_model", ""))) if sd.get("fan_model") else self.output_folder,
            "stats_html": str(sd.get("stats_html", "") or ""),
            "plots": plots,
            "chart_layout": sd.get("chart_layout", "stacked"),
            "best_speeds": best_speeds,
            "best_speed": best_speeds[0] if best_speeds else "未找到",
            "best_score": evaluation.get("best_score"),
            "scores": scores,
            "face_labels": face_labels,
            "has_p1": has_p1,
            "has_p2": has_p2,
            "has_st": has_st,
            "min_iqr": evaluation.get("all_min_iqr_speeds") or {},
            "min_cv": evaluation.get("all_min_cv_speeds") or {},
            "samples": self._collect_samples(sd.get("parsed_data") or []),
            "sections": [s for s in sections if s[2]],
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "config": cfg,
        }

    @staticmethod
    def _collect_samples(parsed_data):
        samples = {}
        for row in parsed_data or []:
            speed = str(row.get("speed", ""))
            if speed:
                samples[speed] = {
                    "P1": len(row.get("p1_samples") or []),
                    "P2": len(row.get("p2_samples") or []),
                    "ST": len(row.get("sum_samples") or []),
                }
        return samples

    # ================= HTML 组装 =================

    def _assemble(self, ctx):
        # 章节开关（include_*）同时作用于目录与正文
        enabled_ids = {s[1] for s in ctx["sections"]}
        sections_html = ""
        if "sec-summary" in enabled_ids:
            sections_html += self._render_summary(ctx)
        if "sec-scores" in enabled_ids:
            sections_html += self._render_scores(ctx)
        if "sec-stats" in enabled_ids:
            sections_html += self._render_stats(ctx)
        if "sec-charts" in enabled_ids:
            sections_html += self._render_charts(ctx)
        if "sec-method" in enabled_ids:
            sections_html += self._render_methodology(ctx)
        if "sec-advice" in enabled_ids:
            sections_html += self._render_recommendations(ctx)
        # 导出样式：standard/compact/detailed → body class（CSS 见 report_export_css.py）
        export_format = ctx["config"].get("export_format", "standard")
        body_cls = ""
        if export_format in ("compact", "detailed"):
            body_cls = f' class="report-{export_format}"'
        return (
            "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"UTF-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            f"<title>{_safe(ctx['config'].get('title') or (ctx['fan_model'] + '动平衡分析报告'))}</title>\n"
            f"<style>\n{EXPORTER_CSS}\n</style>\n</head>\n<body{body_cls}>\n"
            + self._render_cover(ctx)
            + self._render_toc(ctx)
            + self._render_page_header(ctx)
            + "<div class=\"content\">\n"
            + sections_html
            + "</div>\n"
            + self._render_page_footer(ctx)
            + f"<script src=\"{PLOTLY_CDN_URL}\" charset=\"utf-8\"></script>\n"
            + PLOTLY_DUAL_TRACK_SCRIPT
            + "\n</body>\n</html>\n"
        )

    def _render_cover(self, ctx):
        best = _safe("、".join(ctx["best_speeds"]) if ctx["best_speeds"] else "未找到")
        badge = f'<div class="cover-badge">推荐作业转速：{best}</div>' if ctx["best_speeds"] else ""
        cover_title = ctx["config"].get("title") or "扇叶平衡补土转速评估报告"
        return (
            '<div class="cover">\n'
            f"<h1>{_safe(cover_title)}</h1>\n"
            f"<h2>{_safe(ctx['fan_model'])} 动平衡数据分析</h2>\n"
            '<div class="cover-meta">\n'
            f"<p><strong>扇叶型号：</strong>{_safe(ctx['fan_model'])}</p>\n"
            f"<p><strong>平衡机型号：</strong>{_safe(ctx['balancer'])}</p>\n"
            f"<p><strong>报告版本：</strong>{REPORT_VERSION}</p>\n"
            f"<p><strong>生成时间：</strong>{ctx['generated_at']}</p>\n"
            f"<p><strong>生成系统：</strong>{SYSTEM_NAME}</p>\n"
            "</div>\n" + badge + "\n</div>\n"
        )

    def _render_toc(self, ctx):
        lis = "".join(f'<li><a href="#{s[1]}">{_safe(s[0])}</a></li>' for s in ctx["sections"])
        return '<div class="toc">\n<h3>目录</h3>\n<ol>\n' + lis + "\n</ol>\n</div>\n"

    def _render_page_header(self, ctx):
        return (
            '<div class="page-header">\n'
            f"<span>{_safe(ctx['fan_model'])} 动平衡分析报告</span>"
            "<span>系统自动生成 · 仅供参考</span>\n</div>\n"
        )

    def _render_page_footer(self, ctx):
        return (
            '<div class="page-footer">\n'
            f"<span>{SYSTEM_NAME}</span>"
            f"<span>{REPORT_VERSION} · {ctx['generated_at']}</span>\n</div>\n"
        )

    def _render_summary(self, ctx):
        score_txt = _fmt(ctx["best_score"])
        badge = f'<span class="best-badge">综合得分 {score_txt}</span>' if score_txt != "—" else ""
        iqr_txt = "、".join(f"{k}:{v}" for k, v in ctx["min_iqr"].items()) if ctx["min_iqr"] else "—"
        cv_txt = "、".join(f"{k}:{v}" for k, v in ctx["min_cv"].items()) if ctx["min_cv"] else "—"
        return (
            '<div class="summary-box" id="sec-summary">\n'
            "<h3>一、分析摘要</h3>\n"
            "<p>对设备在不同转速下的不平衡量数据进行统计分析与三维加权评分"
            "（IQR 稳定性 40% + CV 稳定性 40% + 幅值合理性 20%），得出以下结论：</p>\n"
            f"<p><strong>推荐最优作业转速：</strong>{_safe(ctx['best_speed'])}{badge}</p>\n"
            f"<p><strong>各面 IQR 最小转速：</strong>{_safe(iqr_txt)}</p>\n"
            f"<p><strong>各面 CV 最小转速：</strong>{_safe(cv_txt)}</p>\n"
            "<p>得分越高代表稳定性与量值合理性综合表现越好；IQR/CV 数值越小表示数据越稳定。</p>\n"
            "</div>\n"
        )

    def _render_scores(self, ctx):
        if not ctx["scores"]:
            return ""
        best_set = set(ctx["best_speeds"])
        face_labels = ctx["face_labels"]
        header = "<tr><th>转速</th>" + "".join(f'<th class="face">{f}</th>' for f in face_labels) + "<th>综合得分</th></tr>"
        rows = []
        for speed, detail in ctx["scores"].items():
            is_best = speed in best_set
            cls = ' class="best"' if is_best else ""
            face_cells = []
            for face, label in _FACE_LABELS:
                # face_labels 存的是标签（如 "P1面"），需按标签匹配而非 face 键（"P1"）
                if label in face_labels:
                    face_cells.append(f"<td>{_fmt((detail.get(face) or {}).get('face_score'))}</td>")
            mark = '<span class="best-badge">最优</span>' if is_best else ""
            rows.append(
                f"<tr{cls}><td>{_safe(speed)}{mark}</td>" + "".join(face_cells)
                + f"<td>{_fmt(detail.get('total_score'))}</td></tr>"
            )
        return (
            '<h2 class="section-title" id="sec-scores">二、最优转速评分明细</h2>\n'
            '<div class="table-responsive"><table class="score-table method-table">\n'
            "<thead>" + header + "</thead><tbody>\n" + "\n".join(rows)
            + "\n</tbody></table></div>\n"
            "<p class=\"sample-info\">面得分 = 0.4×IQR得分 + 0.4×CV得分 + 0.2×幅值得分；"
            "综合得分 = 各面得分 × 面权重的加权和（P1/P2 各 40%、ST 20%）。"
            "黄色高亮行为推荐转速。</p>\n"
        )

    def _render_stats(self, ctx):
        stats_html = ctx["stats_html"]
        return (
            '<h2 class="section-title" id="sec-stats">三、统计分析结果</h2>\n'
            + (f'<div class="table-responsive">{stats_html}</div>' if stats_html else "<p>暂无统计分析结果</p>")
        )

    def _render_charts(self, ctx):
        if not ctx["plots"]:
            return ""
        is_parallel = ctx["chart_layout"] == "parallel"
        out = ['<h2 class="section-title" id="sec-charts">四、数据图表</h2>\n']
        if is_parallel:
            # 并列布局：面为列（与前端 _charts_partial.html 的 row g-3 布局一致），面内图表垂直堆叠
            out.append('<div class="chart-row">\n')
            for surface_key, chart_dict in ctx["plots"].items():
                surface_name = self._resolve_surface_name(ctx, surface_key)
                out.append(f'<div class="chart-col">\n<h3 class="chart-group-title">{surface_name}</h3>\n')
                for chart_type, chart_info in chart_dict.items():
                    cn_name = _CHART_CN.get(chart_type, chart_type)
                    out.append(self._render_single_chart(surface_name, chart_type, cn_name, chart_info, ctx))
                out.append("</div>\n")
            out.append("</div>\n")
        else:
            # 堆叠布局：每个面独立分块，面内图表垂直排列
            for surface_key, chart_dict in ctx["plots"].items():
                surface_name = self._resolve_surface_name(ctx, surface_key)
                out.append(f'<div class="chart-group">\n<h3 class="chart-group-title">{surface_name}</h3>\n')
                for chart_type, chart_info in chart_dict.items():
                    cn_name = _CHART_CN.get(chart_type, chart_type)
                    out.append(self._render_single_chart(surface_name, chart_type, cn_name, chart_info, ctx))
                out.append("</div>\n")
        return "".join(out)

    @staticmethod
    def _resolve_surface_name(ctx, surface_key):
        """解析面名称：single 单面场景按实际存在的面命名（与前端一致）"""
        if surface_key == "single":
            if ctx.get("has_p1"):
                return "P1面"
            if ctx.get("has_p2"):
                return "P2面"
            return "ST面"
        return _SURFACE_NAMES.get(surface_key, surface_key)

    def _render_single_chart(self, surface_name, chart_type, cn_name, chart_info, ctx):
        png_file = chart_info.get("png", "")
        chart_data_obj = None
        chart_data_raw = chart_info.get("chart_data", "")
        if chart_data_raw:
            try:
                chart_data_obj = json.loads(chart_data_raw)
            except (ValueError, TypeError):
                chart_data_obj = None
        img_b64 = ""
        if png_file:
            for base_dir in (ctx["model_dir"], self.output_folder):
                p = os.path.join(base_dir, png_file)
                if os.path.exists(p):
                    img_b64 = self._load_b64(p)
                    break
        title = f"{surface_name}不平衡量{cn_name}"
        mime = "image/svg+xml" if png_file.endswith(".svg") else "image/png"
        parts = [f'<div class="chart-container">\n<h4>{title}</h4>\n']
        if img_b64:
            parts.append(f'<div class="chart-img-container"><img src="data:{mime};base64,{img_b64}" alt="{title}"></div>\n')
        else:
            parts.append('<div class="chart-img-container"><p>(图表暂无预览)</p></div>\n')
        if chart_data_obj is not None:
            data_json = json.dumps(chart_data_obj, ensure_ascii=False).replace("</", "<\\/")
            parts.append(
                f'<div class="chart-plotly-container" data-chart-type="{chart_type}" data-chart-title="{title}" style="display:none">\n'
                f'<script type="application/json">{data_json}</script>\n</div>\n'
            )
        parts.append("</div>\n")
        return "".join(parts)

    def _load_b64(self, path):
        key = (path, os.path.getmtime(path))
        if key in self._base64_cache:
            return self._base64_cache[key]
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        self._base64_cache[key] = b64
        return b64

    def _render_methodology(self, ctx):
        # 样本量说明以紧凑附注形式置于末尾（原三、章节的并列卡片移此）
        footer = ""
        samples = ctx.get("samples") or {}
        if samples:
            items = []
            for speed, counts in samples.items():
                cells = "、".join(f"{k}:{v}组" for k, v in counts.items() if v)
                items.append(f"{_safe(speed)}（{cells}）")
            footer = (
                '<div class="sample-note-footer"><strong>样本量说明：</strong>'
                + "；".join(items) + "</div>"
            )
        return (
            '<h2 class="section-title" id="sec-method">五、统计分析方法</h2>\n'
            '<div class="methodology-box">\n<h3>统计指标说明</h3>\n<ul>\n'
            "<li><strong>平均值：</strong>反映数据的集中趋势</li>\n"
            "<li><strong>中位数：</strong>不受极值影响的中心位置度量</li>\n"
            "<li><strong>标准偏差：</strong>衡量数据的离散程度</li>\n"
            "<li><strong>IQR（四分位距）：</strong>衡量中间50%数据的离散程度，比标准偏差更稳健</li>\n"
            "<li><strong>变异系数(CV)：</strong>标准偏差与平均值的比值（%），消除了量纲影响</li>\n"
            "<li><strong>幅值合理性：</strong>衡量转速点平均不平衡量与全转速中位值的偏离程度，"
            "因子 = 1 / (1 + |均值−中位值| / 中位值)</li>\n"
            "</ul>\n<div class=\"formula-box\">\n"
            "<p>指标得分（IQR/CV）：得分 = 1 / (1 + 归一化指标值)</p>\n"
            "<p>IQR 归一化：以该面全部转速的中位 IQR 为基准（IQR ÷ 中位 IQR），消除量纲差异；"
            "CV 归一化：除以 100（百分比无量纲）</p>\n"
            "<p>面得分 = 0.4 × IQR得分 + 0.4 × CV得分 + 0.2 × 幅值得分</p>\n"
            "<p>综合得分 = 各面得分 × 面权重（P1/P2 各 40%、ST 20%，面权重可配置）</p>\n"
            "<p>异常值过滤：样本量≥8 时采用 D'Agostino-Pearson 正态检验 + 标准 Z-score（阈值 2.5）；"
            "样本量&lt;8 时采用 Modified Z-score（MAD×0.6745）</p>\n"
            "</div>\n</div>\n"
            + footer
        )

    def _render_recommendations(self, ctx):
        bests = ctx["best_speeds"]
        best_txt = "、".join(bests) if bests else "未找到"
        sec_txt = "、".join(bests[1:]) if len(bests) > 1 else "IQR 与 CV 较小的转速点"
        return (
            '<h2 class="section-title" id="sec-advice">六、优化建议与注意事项</h2>\n'
            '<div class="recommendations-box">\n<h3>优化建议</h3>\n<ol>\n'
            f"<li><strong>首选推荐转速：</strong>优先选用推荐最优作业转速 {best_txt}。</li>\n"
            f"<li><strong>次优转速选择：</strong>如最优转速因工艺限制无法使用，可参考 {sec_txt}。</li>\n"
            "<li><strong>定期监测：</strong>建议在选定转速下建立长期监测机制，跟踪数据稳定性变化。</li>\n"
            "<li><strong>数据质量提升：</strong>增加每组转速下的测量样本数量可提高分析准确性。</li>\n"
            "<li><strong>多维度评估：</strong>除不平衡量外，可结合温度、振动等指标综合评估。</li>\n"
            "</ol>\n</div>\n"
            '<div class="technical-details-box">\n<h3>注意事项</h3>\n<ul>\n'
            "<li>本报告提供的最优转速建议仅供参考，实际应用中还需考虑工艺要求和其他工程因素。</li>\n"
            "<li>IQR 与 CV 数值越小表示数据越稳定；得分越高表示综合表现越好。</li>\n"
            "<li>分析结果受测量精度和样本数量影响，建议结合实际情况综合判断。</li>\n"
            "</ul>\n</div>\n"
        )
