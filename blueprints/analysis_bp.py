#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一分析蓝图
合并原 skill_evaluation_bp 与 in_depth_analysis_bp，消除端点重复
"""

import logging
import os
import sys
import threading
from datetime import datetime
from io import BytesIO

from flask import Blueprint, current_app, jsonify, render_template, request, send_file, session

from app.services.skill_evaluation import SkillEvaluationService

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

_skill_evaluation_service = None
_data_analysis_service = None
_services_lock = threading.Lock()


def _get_services():
    global _skill_evaluation_service, _data_analysis_service
    if _skill_evaluation_service is None or _data_analysis_service is None:
        with _services_lock:
            if _skill_evaluation_service is None or _data_analysis_service is None:
                from app.services.data_analysis import data_analysis_service as das
                from app.services.skill_evaluation import skill_evaluation_service as ses

                _skill_evaluation_service = ses
                _data_analysis_service = das
    return _skill_evaluation_service, _data_analysis_service


def _validate_api_input(data, required_fields, field_types=None):
    if not data:
        return False, "请求体为空，请提供有效的JSON数据"
    if not isinstance(data, dict):
        return False, "请求数据必须是JSON对象格式"
    for field in required_fields:
        if field not in data or data[field] is None:
            return False, f"缺少必要参数: {field}"
    if field_types:
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                return (
                    False,
                    f"参数 {field} 类型错误，期望 {expected_type.__name__}，实际 {type(data[field]).__name__}",
                )
    return True, None


analysis_bp = Blueprint("analysis", __name__)


# ═══════════════════════════════════════════════════════════════
# 页面路由
# ═══════════════════════════════════════════════════════════════


@analysis_bp.route("/skill-evaluation")
def skill_evaluation():
    import json

    test_data = session.get("parsed_data", [])
    if not test_data:
        test_data = [
            {
                "speed": "1000rpm",
                "p1_samples": [1.1, 1.5, 1.3, 1.4, 1.6, 1.2, 1.3, 1.4, 1.5, 1.3],
                "p2_samples": [2.1, 2.5, 2.3, 2.4, 2.6, 2.2, 2.3, 2.4, 2.5, 2.3],
                "sum_samples": [3.2, 4.0, 3.6, 3.8, 4.2, 3.4, 3.6, 3.8, 4.0, 3.6],
            },
            {
                "speed": "2000rpm",
                "p1_samples": [1.0, 1.4, 1.2, 1.3, 1.5, 1.1, 1.2, 1.3, 1.4, 1.2],
                "p2_samples": [2.0, 2.4, 2.2, 2.3, 2.5, 2.1, 2.2, 2.3, 2.4, 2.2],
                "sum_samples": [3.0, 3.8, 3.4, 3.6, 4.0, 3.2, 3.4, 3.6, 3.8, 3.4],
            },
            {
                "speed": "3000rpm",
                "p1_samples": [0.9, 1.3, 1.1, 1.2, 1.4, 1.0, 1.1, 1.2, 1.3, 1.1],
                "p2_samples": [1.9, 2.3, 2.1, 2.2, 2.4, 2.0, 2.1, 2.2, 2.3, 2.1],
                "sum_samples": [2.8, 3.6, 3.2, 3.4, 3.8, 3.0, 3.2, 3.4, 3.6, 3.2],
            },
        ]
    test_data_json = json.dumps(test_data, ensure_ascii=False, indent=2)
    return render_template("skill_evaluation.html", test_data_json=test_data_json)


@analysis_bp.route("/in-depth-analysis")
def in_depth_analysis():
    import json

    test_data = session.get("parsed_data", [])
    test_data_json = json.dumps(test_data, ensure_ascii=False, indent=2)
    return render_template("in_depth_analysis.html", test_data_json=test_data_json)


# ═══════════════════════════════════════════════════════════════
# 会话数据（统一 handler，兼容两个 URL 前缀）
# ═══════════════════════════════════════════════════════════════


def _get_session_data_impl():
    saved_results = session.get("saved_results", {})
    parsed_data = saved_results.get("parsed_data", [])
    fan_model = saved_results.get("fan_model", "")
    if not parsed_data:
        parsed_data = session.get("parsed_data", [])
    if not fan_model:
        fan_model = session.get("fan_model", "")
    return jsonify({"success": True, "parsed_data": parsed_data, "fan_model": fan_model})


@analysis_bp.route("/api/skill-evaluation/get_session_data", methods=["GET"])
def get_session_data_se():
    try:
        return _get_session_data_impl()
    except Exception as e:
        logger.error("获取技能评估会话数据失败: %s", str(e))
        return jsonify(
            {
                "error": "数据库连接失败，无法获取评估数据",
                "detail": str(e) if current_app.debug else "",
            }
        ), 500


@analysis_bp.route("/api/in-depth-analysis/get_session_data", methods=["GET"])
def get_session_data_ida():
    try:
        return _get_session_data_impl()
    except Exception as e:
        logger.error("获取深入分析会话数据失败: %s", str(e))
        return jsonify({"success": False, "message": "获取会话数据失败，请稍后重试"})


# ═══════════════════════════════════════════════════════════════
# 评估端点
# ═══════════════════════════════════════════════════════════════


def _handle_evaluate():
    ses, _ = _get_services()
    data = request.get_json()
    valid, err = _validate_api_input(data, ["data"], {"data": list})
    if not valid:
        return jsonify({"code": 400, "message": err, "data": None})
    filters = data.get("filters", {})
    evaluation_results = ses.evaluate_skill(data["data"], filters)
    return jsonify({"code": 200, "message": "成功", "data": evaluation_results})


@analysis_bp.route("/api/skill-evaluation/evaluate", methods=["POST"])
def evaluate_skill_se():
    try:
        return _handle_evaluate()
    except Exception as e:
        logger.error("技能评估失败: %s", str(e))
        return jsonify({"code": 500, "message": f"技能评估失败：{str(e)}", "data": None})


@analysis_bp.route("/api/in-depth-analysis/evaluate", methods=["POST"])
def evaluate_skill_ida():
    try:
        return _handle_evaluate()
    except Exception as e:
        logger.error("深入分析失败: %s", str(e))
        return jsonify({"code": 500, "message": "深入分析失败，请稍后重试", "data": None})


# ═══════════════════════════════════════════════════════════════
# 报告端点
# ═══════════════════════════════════════════════════════════════


def _handle_generate_report():
    ses, _ = _get_services()
    data = request.get_json()
    valid, err = _validate_api_input(data, ["evaluation_results"], {"evaluation_results": dict})
    if not valid:
        return jsonify({"code": 400, "message": err, "data": None})
    report = ses.generate_skill_report(data["evaluation_results"])
    return jsonify({"code": 200, "message": "成功", "data": report})


@analysis_bp.route("/api/skill-evaluation/report", methods=["POST"])
def generate_report_se():
    try:
        return _handle_generate_report()
    except Exception as e:
        logger.error("生成技能评估报告失败: %s", str(e))
        return jsonify({"code": 500, "message": f"生成技能评估报告失败：{str(e)}", "data": None})


@analysis_bp.route("/api/in-depth-analysis/report", methods=["POST"])
def generate_report_ida():
    try:
        return _handle_generate_report()
    except Exception as e:
        logger.error("生成深入分析报告失败: %s", str(e))
        return jsonify({"code": 500, "message": "生成报告失败，请稍后重试", "data": None})


# ═══════════════════════════════════════════════════════════════
# 数据分析子端点 (advanced / trend / anomaly / cluster)
# ═══════════════════════════════════════════════════════════════


def _handle_advanced_analysis():
    _, das = _get_services()
    data = request.get_json()
    valid, err = _validate_api_input(data, ["data"], {"data": list})
    if not valid:
        return jsonify({"code": 400, "message": err, "data": None})
    analysis_result = das.advanced_statistical_analysis(data["data"])
    return jsonify({"code": 200, "message": "成功", "data": analysis_result})


@analysis_bp.route("/api/skill-evaluation/data-analysis/advanced", methods=["POST"])
def advanced_analysis_se():
    try:
        return _handle_advanced_analysis()
    except Exception as e:
        logger.error("高级数据分析失败: %s", str(e))
        return jsonify({"code": 500, "message": "数据分析失败，请稍后重试", "data": None})


@analysis_bp.route("/api/in-depth-analysis/data-analysis/advanced", methods=["POST"])
def advanced_analysis_ida():
    try:
        return _handle_advanced_analysis()
    except Exception as e:
        logger.error("高级数据分析失败: %s", str(e))
        return jsonify({"code": 500, "message": "数据分析失败，请稍后重试", "data": None})


def _handle_trend_analysis():
    _, das = _get_services()
    data = request.get_json()
    valid, err = _validate_api_input(data, ["data"], {"data": list})
    if not valid:
        return jsonify({"code": 400, "message": err, "data": None})
    analysis_result = das.trend_analysis(data["data"])
    return jsonify({"code": 200, "message": "成功", "data": analysis_result})


@analysis_bp.route("/api/skill-evaluation/data-analysis/trend", methods=["POST"])
def trend_analysis_se():
    try:
        return _handle_trend_analysis()
    except Exception as e:
        logger.error("趋势分析失败: %s", str(e))
        return jsonify({"code": 500, "message": "趋势分析失败，请稍后重试", "data": None})


@analysis_bp.route("/api/in-depth-analysis/data-analysis/trend", methods=["POST"])
def trend_analysis_ida():
    try:
        return _handle_trend_analysis()
    except Exception as e:
        logger.error("趋势分析失败: %s", str(e))
        return jsonify({"code": 500, "message": "趋势分析失败，请稍后重试", "data": None})


def _handle_anomaly_detection():
    _, das = _get_services()
    data = request.get_json()
    valid, err = _validate_api_input(data, ["data"], {"data": list})
    if not valid:
        return jsonify({"code": 400, "message": err, "data": None})
    threshold = data.get("threshold", 2.0)
    analysis_result = das.anomaly_detection(data["data"], threshold)
    return jsonify({"code": 200, "message": "成功", "data": analysis_result})


@analysis_bp.route("/api/skill-evaluation/data-analysis/anomaly", methods=["POST"])
def anomaly_detection_se():
    try:
        return _handle_anomaly_detection()
    except Exception as e:
        logger.error("异常检测失败: %s", str(e))
        return jsonify({"code": 500, "message": "异常检测失败，请稍后重试", "data": None})


@analysis_bp.route("/api/in-depth-analysis/data-analysis/anomaly", methods=["POST"])
def anomaly_detection_ida():
    try:
        return _handle_anomaly_detection()
    except Exception as e:
        logger.error("异常检测失败: %s", str(e))
        return jsonify({"code": 500, "message": "异常检测失败，请稍后重试", "data": None})


def _handle_cluster_analysis():
    _, das = _get_services()
    data = request.get_json()
    valid, err = _validate_api_input(data, ["data"], {"data": list})
    if not valid:
        return jsonify({"code": 400, "message": err, "data": None})
    n_clusters = data.get("n_clusters", 3)
    analysis_result = das.cluster_analysis(data["data"], n_clusters)
    return jsonify({"code": 200, "message": "成功", "data": analysis_result})


@analysis_bp.route("/api/skill-evaluation/data-analysis/cluster", methods=["POST"])
def cluster_analysis_se():
    try:
        return _handle_cluster_analysis()
    except Exception as e:
        logger.error("聚类分析失败: %s", str(e))
        return jsonify({"code": 500, "message": "聚类分析失败，请稍后重试", "data": None})


@analysis_bp.route("/api/in-depth-analysis/data-analysis/cluster", methods=["POST"])
def cluster_analysis_ida():
    try:
        return _handle_cluster_analysis()
    except Exception as e:
        logger.error("聚类分析失败: %s", str(e))
        return jsonify({"code": 500, "message": "聚类分析失败，请稍后重试", "data": None})


# ═══════════════════════════════════════════════════════════════
# 导出端点 (仅 in-depth-analysis 使用)
# ═══════════════════════════════════════════════════════════════


@analysis_bp.route("/api/in-depth-analysis/export", methods=["POST"])
def export_analysis():
    try:
        data = request.get_json()
        valid, err = _validate_api_input(data, ["evaluation_results", "format"])
        if not valid:
            return jsonify({"code": 400, "message": err, "data": None})

        fmt = data["format"]
        evaluation_results = data["evaluation_results"]

        if fmt == "json":
            import json

            content = json.dumps(evaluation_results, ensure_ascii=False, indent=2)
            mimetype = "application/json"
            filename = f"in_depth_analysis_{datetime.now().strftime('%Y%m%d')}.json"
        elif fmt == "excel":
            import pandas as pd

            rows = []
            for speed, scores in (
                evaluation_results.get("optimal_speed_evaluation", {})
                .get("speed_detailed_scores", {})
                .items()
            ):
                p1_face = scores.get("P1", {}) if isinstance(scores, dict) else {}
                p2_face = scores.get("P2", {}) if isinstance(scores, dict) else {}
                st_face = scores.get("ST", {}) if isinstance(scores, dict) else {}
                rows.append(
                    {
                        "转速": speed,
                        "综合得分": scores.get("total_score", 0) if isinstance(scores, dict) else 0,
                        "P1面得分": p1_face.get("face_score") or 0,
                        "P2面得分": p2_face.get("face_score") or 0,
                        "ST面得分": st_face.get("face_score") or 0,
                    }
                )
            df = pd.DataFrame(rows)
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="最优转速评估", index=False)
            output.seek(0)
            content = output.getvalue()
            mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"in_depth_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx"
        elif fmt == "pdf":
            import pdfkit

            html = _build_pdf_html(evaluation_results)
            try:
                content = pdfkit.from_string(html, False)
                mimetype = "application/pdf"
                filename = f"in_depth_analysis_{datetime.now().strftime('%Y%m%d')}.pdf"
            except Exception:
                return jsonify({"code": 500, "message": "PDF生成失败，请稍后重试", "data": None})
        else:
            return jsonify({"code": 400, "message": "不支持的导出格式", "data": None})

        if isinstance(content, str):
            content = content.encode("utf-8")
        return send_file(
            BytesIO(content), mimetype=mimetype, as_attachment=True, download_name=filename
        )
    except Exception as e:
        logger.error("导出分析结果失败: %s", str(e))
        return jsonify({"code": 500, "message": "导出失败，请稍后重试", "data": None})


@analysis_bp.route("/api/in-depth-analysis/generate-report", methods=["POST"])
def generate_full_report():
    try:
        data = request.get_json()
        valid, err = _validate_api_input(
            data, ["evaluation_results", "format"], {"evaluation_results": dict}
        )
        if not valid:
            return jsonify({"code": 400, "message": err, "data": None})

        evaluation_results = data["evaluation_results"]
        template = data.get("template", "standard")
        fmt = data["format"]
        include = data.get("include", {})

        if fmt == "html":
            html_content = generate_html_report(evaluation_results, template, include)
            content = html_content.encode("utf-8")
            mimetype = "text/html"
            filename = f"analysis_report_{datetime.now().strftime('%Y%m%d')}.html"
        elif fmt == "pdf":
            html_content = generate_html_report(evaluation_results, template, include)
            try:
                import pdfkit

                content = pdfkit.from_string(html_content, False)
                mimetype = "application/pdf"
                filename = f"analysis_report_{datetime.now().strftime('%Y%m%d')}.pdf"
            except ImportError:
                return jsonify(
                    {
                        "code": 500,
                        "message": "PDF生成失败：缺少 pdfkit/wkhtmltopdf 依赖，请联系管理员安装",
                        "data": None,
                    }
                )
            except Exception as e:
                logger.error("PDF生成失败: %s", str(e))
                return jsonify({"code": 500, "message": "PDF生成失败，请稍后重试", "data": None})
        elif fmt == "excel":
            import pandas as pd

            flat_results = _flatten_evaluation_results(evaluation_results)
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                if include.get("summary", True):
                    summary_data = []
                    summary_data.append({"项目": "分析摘要", "内容": "数据分析结果摘要"})
                    if "comprehensive_evaluation" in flat_results:
                        comp = flat_results["comprehensive_evaluation"]
                        if "overall_score" in comp:
                            summary_data.append({"项目": "综合评分", "内容": comp["overall_score"]})
                        if "data_quality" in comp:
                            summary_data.append({"项目": "数据质量", "内容": comp["data_quality"]})
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name="分析摘要", index=False)
                if include.get("basicStats", True) and "basic_stats" in flat_results:
                    pd.DataFrame(flat_results["basic_stats"]).T.to_excel(
                        writer, sheet_name="基本统计"
                    )
                if include.get("advancedStats", True) and "advanced_stats" in flat_results:
                    pd.DataFrame(flat_results["advanced_stats"]).T.to_excel(
                        writer, sheet_name="高级统计"
                    )
                if include.get("trendAnalysis", True) and "trend_analysis" in flat_results:
                    pd.DataFrame(flat_results["trend_analysis"]).T.to_excel(
                        writer, sheet_name="趋势分析"
                    )
                if include.get("anomalyDetection", True) and "anomaly_detection" in flat_results:
                    anomaly_rows = []
                    for face, anomaly in flat_results["anomaly_detection"].items():
                        if anomaly and "anomaly_values" in anomaly:
                            for val in anomaly["anomaly_values"]:
                                anomaly_rows.append({"面": face, "异常值": val})
                    if anomaly_rows:
                        pd.DataFrame(anomaly_rows).to_excel(writer, sheet_name="异常检测")
                if (
                    include.get("recommendations", True)
                    and "comprehensive_evaluation" in flat_results
                ):
                    comp = flat_results["comprehensive_evaluation"]
                    if "recommendations" in comp:
                        recs = [
                            {"序号": i, "建议": r} for i, r in enumerate(comp["recommendations"], 1)
                        ]
                        pd.DataFrame(recs).to_excel(writer, sheet_name="改进建议", index=False)
            output.seek(0)
            content = output.getvalue()
            mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"analysis_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        elif fmt == "word":
            return jsonify(
                {
                    "code": 400,
                    "message": "Word格式暂不支持，请使用HTML或Excel格式导出",
                    "data": None,
                }
            )
        else:
            return jsonify({"code": 400, "message": "不支持的格式", "data": None})

        return send_file(
            BytesIO(content), mimetype=mimetype, as_attachment=True, download_name=filename
        )
    except Exception as e:
        logger.error("生成报告失败: %s", str(e))
        return jsonify({"code": 500, "message": "生成报告失败，请稍后重试", "data": None})


@analysis_bp.route("/api/in-depth-analysis/share-link/<link_id>", methods=["DELETE"])
def revoke_share_link(link_id):
    try:
        from report_export import ReportExporter

        exporter = ReportExporter(app=current_app._get_current_object())
        success = exporter.revoke_shareable_link(link_id)
        if success:
            return jsonify({"code": 200, "message": "分享链接已撤销", "data": None})
        else:
            return jsonify({"code": 404, "message": "分享链接不存在或已过期", "data": None})
    except Exception as e:
        logger.error("撤销分享链接失败: %s", str(e))
        return jsonify({"code": 500, "message": "撤销链接失败，请稍后重试", "data": None})


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════


def _build_pdf_html(evaluation_results):
    rows_html = ""
    for speed, scores in (
        evaluation_results.get("optimal_speed_evaluation", {})
        .get("speed_detailed_scores", {})
        .items()
    ):
        p1_face = scores.get("P1", {}) if isinstance(scores, dict) else {}
        p2_face = scores.get("P2", {}) if isinstance(scores, dict) else {}
        st_face = scores.get("ST", {}) if isinstance(scores, dict) else {}
        rows_html += f"""
            <tr>
                <td>{speed}</td>
                <td>{scores.get("total_score", 0) if isinstance(scores, dict) else 0}</td>
                <td>{p1_face.get("face_score") or 0}</td>
                <td>{p2_face.get("face_score") or 0}</td>
                <td>{st_face.get("face_score") or 0}</td>
            </tr>
        """
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>深入分析报告</title>
    <style>
        body {{ font-family: "SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>深入分析报告</h1>
    <h2>综合评估</h2>
    <p>总体评估: {evaluation_results.get("comprehensive_evaluation", {}).get("overall_assessment", "未知")}</p>
    <p>分析得分: {evaluation_results.get("comprehensive_evaluation", {}).get("skill_score", 0)}</p>
    <p>数据质量: {evaluation_results.get("comprehensive_evaluation", {}).get("data_quality", "未知")}</p>
    <p>工艺稳定性: {evaluation_results.get("comprehensive_evaluation", {}).get("process_stability", "未知")}</p>
    <p>异常评估: {evaluation_results.get("comprehensive_evaluation", {}).get("anomaly_evaluation", "无异常")}</p>
    <h2>最优转速评估</h2>
    <table>
        <tr><th>转速</th><th>综合得分</th><th>P1面得分</th><th>P2面得分</th><th>ST面得分</th></tr>
        {rows_html}
    </table>
</body>
</html>"""


def generate_html_report(evaluation_results, template_name, include):
    from jinja2 import Environment

    flat_results = _flatten_evaluation_results(evaluation_results)
    template_map = {"standard": "report_template.html"}
    template_file = template_map.get(template_name, template_map["standard"])
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "templates", template_file
    )
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
    except FileNotFoundError:
        logger.warning("模板文件 %s 不存在，使用回退模板", template_file)
        return _generate_fallback_report(flat_results)
    env = Environment(autoescape=True)
    j2_template = env.from_string(template_content)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return j2_template.render(
        evaluation_results=flat_results, include=include, generated_at=generated_at
    )


def _flatten_evaluation_results(evaluation_results):
    flat = dict(evaluation_results)
    if "advanced_analysis" in flat and flat["advanced_analysis"]:
        adv = flat["advanced_analysis"]
        if "advanced_statistics" in adv and adv["advanced_statistics"]:
            stats = adv["advanced_statistics"]
            if "basic_stats" in stats:
                flat["basic_stats"] = stats["basic_stats"]
            if "advanced_stats" in stats:
                flat["advanced_stats"] = stats["advanced_stats"]
        if "trend_analysis" in adv:
            flat["trend_analysis"] = adv["trend_analysis"]
        if "anomaly_detection" in adv:
            flat["anomaly_detection"] = adv["anomaly_detection"]
    if "comprehensive_evaluation" in flat and flat["comprehensive_evaluation"]:
        comp = flat["comprehensive_evaluation"]
        if "overall_assessment" in comp and "overall_score" not in comp:
            comp["overall_score"] = comp["overall_assessment"]
        ses = SkillEvaluationService()
        comp["recommendations"] = ses._generate_recommendations(flat)
    return flat


def _generate_fallback_report(evaluation_results):
    comprehensive = evaluation_results.get("comprehensive_evaluation", {})
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>分析报告</title></head>
<body>
    <h1>分析报告</h1>
    <p>总体评估: {comprehensive.get("overall_assessment", "未知")}</p>
    <p>分析得分: {comprehensive.get("skill_score", 0)}</p>
    <p>数据质量: {comprehensive.get("data_quality", "未知")}</p>
    <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
</body>
</html>"""
