#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
机器学习蓝图：包含机器学习API
"""

import os
from functools import lru_cache

from flask import Blueprint, current_app, jsonify, render_template, request

from app.utils.cache_utils import file_cache, query_cache
from machine_learning import (
    analyze_balance_data,
    cluster_balance_data,
    detect_anomaly_patterns,
    detect_outliers_iqr,
    multi_dimensional_analysis,
    predict_key_metrics,
    predict_trend,
)

ml_bp = Blueprint("ml", __name__)

MAX_PAYLOAD_SIZE = 1024 * 1024
MIN_DATA_POINTS = 5


def _check_payload_size():
    if len(request.data) > MAX_PAYLOAD_SIZE:
        return True
    return False


def _validate_time_series_data(data, field_name, endpoint_name):
    """验证时间序列数据格式和最小数据量"""
    if not isinstance(data, list):
        return (
            None,
            jsonify({"success": False, "error": f"{field_name}格式错误：应为数组格式"}),
            400,
        )
    if len(data) < 2:
        return (
            None,
            jsonify(
                {
                    "success": False,
                    "error": f"{field_name}数据量不足（当前{len(data)}条），至少需要2条数据",
                }
            ),
            400,
        )
    if len(data) < MIN_DATA_POINTS:
        current_app.logger.warning(
            "%s: 数据量偏少(%d条)，预测结果置信度较低", endpoint_name, len(data)
        )
    for item in data:
        if not isinstance(item, dict):
            return (
                None,
                jsonify({"success": False, "error": f"{field_name}中每项应为字典格式"}),
                400,
            )
        if "value" not in item or "date" not in item:
            return (
                None,
                jsonify(
                    {"success": False, "error": f"{field_name}中每项需包含'date'和'value'字段"}
                ),
                400,
            )
    return data, None, None


def _validate_metrics_data(data, field_name, endpoint_name):
    """验证指标数据格式和最小数据量"""
    if not isinstance(data, list):
        return (
            None,
            jsonify({"success": False, "error": f"{field_name}格式错误：应为数组格式"}),
            400,
        )
    if len(data) < 2:
        return (
            None,
            jsonify(
                {
                    "success": False,
                    "error": f"{field_name}数据量不足（当前{len(data)}条），至少需要2条数据",
                }
            ),
            400,
        )
    if len(data) < MIN_DATA_POINTS:
        current_app.logger.warning(
            "%s: 数据量偏少(%d条)，预测结果置信度较低", endpoint_name, len(data)
        )
    for item in data:
        if not isinstance(item, dict):
            return (
                None,
                jsonify({"success": False, "error": f"{field_name}中每项应为字典格式"}),
                400,
            )
    return data, None, None


def _validate_analysis_data(data, field_name, endpoint_name):
    """验证分析数据格式和最小数据量"""
    if not isinstance(data, list):
        return (
            None,
            jsonify({"success": False, "error": f"{field_name}格式错误：应为数组格式"}),
            400,
        )
    if len(data) < 1:
        return (
            None,
            jsonify({"success": False, "error": f"{field_name}数据为空，请提供有效数据"}),
            400,
        )
    if len(data) < MIN_DATA_POINTS:
        current_app.logger.warning(
            "%s: 数据量偏少(%d条)，分析结果可能不够精确", endpoint_name, len(data)
        )
    for item in data:
        if not isinstance(item, dict):
            return (
                None,
                jsonify({"success": False, "error": f"{field_name}中每项应为字典格式"}),
                400,
            )
    return data, None, None


def _build_confidence_info(model_metrics, n_samples, model_type):
    """构建置信度/可解释性信息"""
    confidence = {
        "n_samples": n_samples,
        "model_type": model_type,
        "confidence_level": "low",
    }
    if isinstance(model_metrics, dict):
        r2 = model_metrics.get("test_r2", 0)
        if r2 is None:
            r2 = 0
        confidence["r2_score"] = round(float(r2), 4)
        confidence["rmse"] = round(float(model_metrics.get("test_rmse", 0)), 6)
        if r2 > 0.8:
            confidence["confidence_level"] = "high"
        elif r2 > 0.5:
            confidence["confidence_level"] = "medium"
        elif r2 <= 0 and n_samples >= MIN_DATA_POINTS:
            confidence["confidence_level"] = "very_low"
        else:
            confidence["confidence_level"] = "low"
    return confidence


@ml_bp.route("/ml")
def ml():
    """机器学习页面"""
    return render_template("ml.html")


@ml_bp.route("/api/predict_trend", methods=["POST"])
def api_predict_trend():
    """预测趋势"""
    try:
        if _check_payload_size():
            return jsonify({"success": False, "error": "请求数据过大，请减少数据量后重试"}), 413

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请提供有效的JSON数据"})

        historical_data = data.get("historical_data")
        prediction_days = data.get("prediction_days", 7)
        model_type = data.get("model_type", "random_forest")

        if not historical_data:
            return jsonify({"success": False, "error": "请提供历史数据"})

        validated_data, error_response, status_code = _validate_time_series_data(
            historical_data, "历史数据", "predict_trend"
        )
        if error_response:
            return error_response, status_code

        if not isinstance(prediction_days, int) or prediction_days < 1 or prediction_days > 365:
            prediction_days = 7

        valid_models = ["linear", "ridge", "random_forest", "gradient_boosting"]
        if model_type not in valid_models:
            model_type = "random_forest"

        result = predict_trend(historical_data, prediction_days, model_type)

        n_samples = len(historical_data)
        confidence = _build_confidence_info(
            result.get("model_metrics", {}), n_samples, result.get("model_type", model_type)
        )
        result["confidence"] = confidence

        return jsonify({"success": True, "result": result})
    except Exception as e:
        current_app.logger.error(f"predict_trend error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "模型训练/预测失败，请稍后重试"}), 500


@ml_bp.route("/api/analyze_balance_data", methods=["POST"])
def api_analyze_balance_data():
    """⚠️ 外部API — 暂无前端UI面板调用
    平衡数据综合 ML 分析——趋势+聚类+异常三合一"""
    try:
        if _check_payload_size():
            return jsonify({"success": False, "error": "请求数据过大，请减少数据量后重试"}), 413

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请提供有效的JSON数据"})

        balance_records = data.get("balance_records")
        fan_model = data.get("fan_model", "")

        if (
            not balance_records
            or not isinstance(balance_records, list)
            or len(balance_records) == 0
        ):
            return jsonify({"success": False, "error": "请提供有效的平衡测量数据"}), 400

        for rec in balance_records:
            if not isinstance(rec, dict):
                return jsonify({"success": False, "error": "平衡数据中每项应为字典格式"}), 400

        result = analyze_balance_data(balance_records, fan_model)

        return jsonify({"success": True, "result": result})
    except ValueError as e:
        current_app.logger.warning(f"analyze_balance_data ValueError: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"analyze_balance_data error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "分析失败，请稍后重试"}), 500


@ml_bp.route("/api/cluster_balance_data", methods=["POST"])
def api_cluster_balance_data():
    """⚠️ 外部API — 暂无前端UI面板调用
    KMeans 聚类分析"""
    try:
        if _check_payload_size():
            return jsonify({"success": False, "error": "请求数据过大，请减少数据量后重试"}), 413

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请提供有效的JSON数据"})

        surface_data = data.get("surface_data")
        n_clusters = data.get("n_clusters", 3)

        if not surface_data or not isinstance(surface_data, list) or len(surface_data) < 2:
            return jsonify({"success": False, "error": "请提供至少2组有效的平衡面数据"}), 400

        if not isinstance(n_clusters, int) or n_clusters < 2 or n_clusters > 10:
            n_clusters = 3

        result = cluster_balance_data(surface_data, n_clusters)

        return jsonify({"success": True, "result": result})
    except ValueError as e:
        current_app.logger.warning(f"cluster_balance_data ValueError: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"cluster_balance_data error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "聚类分析失败，请稍后重试"}), 500


@ml_bp.route("/api/detect_outliers_iqr", methods=["POST"])
def api_detect_outliers_iqr():
    """⚠️ 外部API — 暂无前端UI面板调用
    IQR 异常值检测"""
    try:
        if _check_payload_size():
            return jsonify({"success": False, "error": "请求数据过大，请减少数据量后重试"}), 413

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请提供有效的JSON数据"})

        values = data.get("values")

        if not values or not isinstance(values, list) or len(values) < 2:
            return jsonify({"success": False, "error": "请提供至少2个数值"}), 400

        result = detect_outliers_iqr(values)

        return jsonify({"success": True, "result": result})
    except ValueError as e:
        current_app.logger.warning(f"detect_outliers_iqr ValueError: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"detect_outliers_iqr error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "异常检测失败，请稍后重试"}), 500


@ml_bp.route("/api/predict_key_metrics", methods=["POST"])
def api_predict_key_metrics():
    """预测关键指标"""
    try:
        if _check_payload_size():
            return jsonify({"success": False, "error": "请求数据过大，请减少数据量后重试"}), 413

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请提供有效的JSON数据"})

        historical_metrics = data.get("historical_metrics")
        prediction_periods = data.get("prediction_periods", 12)
        model_type = data.get("model_type", "gradient_boosting")

        if not historical_metrics:
            return jsonify({"success": False, "error": "请提供历史指标数据"})

        validated_data, error_response, status_code = _validate_metrics_data(
            historical_metrics, "历史指标数据", "predict_key_metrics"
        )
        if error_response:
            return error_response, status_code

        if (
            not isinstance(prediction_periods, int)
            or prediction_periods < 1
            or prediction_periods > 120
        ):
            prediction_periods = 12

        valid_models = ["linear", "ridge", "random_forest", "gradient_boosting"]
        if model_type not in valid_models:
            model_type = "gradient_boosting"

        result = predict_key_metrics(historical_metrics, prediction_periods, model_type)

        n_samples = len(historical_metrics)
        metrics_list = [k for k in result.get("metrics_results", {})]
        confidence_info = {}
        for metric_name in metrics_list:
            metric_result = result.get("metrics_results", {}).get(metric_name, {})
            if isinstance(metric_result, dict) and "test_r2" in metric_result:
                confidence_info[metric_name] = _build_confidence_info(
                    metric_result, n_samples, result.get("model_type", model_type)
                )
            else:
                confidence_info[metric_name] = {
                    "n_samples": n_samples,
                    "model_type": result.get("model_type", "simple_average"),
                    "confidence_level": "low",
                }
        result["confidence"] = confidence_info

        return jsonify({"success": True, "result": result})
    except Exception as e:
        current_app.logger.error(f"predict_key_metrics error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "模型训练/预测失败，请稍后重试"}), 500


@ml_bp.route("/api/multi_dimensional_analysis", methods=["POST"])
def api_multi_dimensional_analysis():
    """多维度数据分析"""
    try:
        if _check_payload_size():
            return jsonify({"success": False, "error": "请求数据过大，请减少数据量后重试"}), 413

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请提供有效的JSON数据"})

        analysis_data = data.get("data")
        dimensions = data.get("dimensions")
        metrics = data.get("metrics")

        if not analysis_data or not dimensions or not metrics:
            return jsonify({"success": False, "error": "请提供完整的分析数据、维度和指标"})

        validated_data, error_response, status_code = _validate_analysis_data(
            analysis_data, "分析数据", "multi_dimensional_analysis"
        )
        if error_response:
            return error_response, status_code

        if not isinstance(dimensions, list) or len(dimensions) == 0:
            return jsonify({"success": False, "error": "请提供至少一个分析维度"}), 400
        if not isinstance(metrics, list) or len(metrics) == 0:
            return jsonify({"success": False, "error": "请提供至少一个分析指标"}), 400

        result = multi_dimensional_analysis(analysis_data, dimensions, metrics)

        n_samples = len(analysis_data)
        confidence = {
            "n_samples": n_samples,
            "n_dimensions": len(dimensions),
            "n_metrics": len(metrics),
            "n_groups": len(result.get("detailed", [])),
            "confidence_level": "high"
            if n_samples >= 30
            else "medium"
            if n_samples >= 10
            else "low",
        }
        result["confidence"] = confidence

        return jsonify({"success": True, "result": result})
    except ValueError as e:
        current_app.logger.warning(f"multi_dimensional_analysis ValueError: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"multi_dimensional_analysis error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "模型训练/预测失败，请稍后重试"}), 500


@ml_bp.route("/api/detect_anomaly_patterns", methods=["POST"])
def api_detect_anomaly_patterns():
    """检测异常模式"""
    try:
        if _check_payload_size():
            return jsonify({"success": False, "error": "请求数据过大，请减少数据量后重试"}), 413

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请提供有效的JSON数据"})

        time_series_data = data.get("time_series_data")
        window_size = data.get("window_size", 7)
        threshold = data.get("threshold", 2.0)

        if not time_series_data:
            return jsonify({"success": False, "error": "请提供时间序列数据"})

        validated_data, error_response, status_code = _validate_time_series_data(
            time_series_data, "时间序列数据", "detect_anomaly_patterns"
        )
        if error_response:
            return error_response, status_code

        if not isinstance(window_size, int) or window_size < 2 or window_size > 100:
            window_size = 7
        if not isinstance(threshold, (int, float)) or threshold <= 0:
            threshold = 2.0

        result = detect_anomaly_patterns(time_series_data, window_size, threshold)

        total_points = len(time_series_data)
        anomaly_count = len(result)
        if total_points < window_size:
            diagnostic = {
                "status": "insufficient_data",
                "message": f"数据量({total_points}条)不足窗口大小({window_size})，无法计算滑动统计量",
                "required": window_size,
                "actual": total_points,
            }
        elif anomaly_count == 0:
            diagnostic = {
                "status": "no_anomalies",
                "message": "未检测到异常点",
            }
        else:
            diagnostic = {
                "status": "ok",
                "message": f"检测到{anomaly_count}个异常点",
            }

        anomaly_rate = round(anomaly_count / max(total_points, 1) * 100, 2)
        confidence = {
            "n_samples": total_points,
            "anomaly_count": anomaly_count,
            "anomaly_rate_percent": anomaly_rate,
            "window_size": window_size,
            "threshold": threshold,
            "confidence_level": "high"
            if anomaly_count > 0 and total_points >= 30
            else "medium"
            if total_points >= 10
            else "low",
        }
        response_data = {
            "anomalies": result,
            "confidence": confidence,
            "diagnostic": diagnostic,
        }

        return jsonify({"success": True, "result": response_data})
    except Exception as e:
        current_app.logger.error(f"detect_anomaly_patterns error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "模型训练/预测失败，请稍后重试"}), 500


# ========== 历史数据导入 API ==========

_OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")


def _extract_model_from_stats_csv(csv_filename: str) -> str:
    """从 stats CSV 文件名提取型号名。模式: p1_{MODEL}_p2_{MODEL}_stats.csv"""
    fname = os.path.basename(csv_filename)
    # 去掉文件扩展名
    if fname.endswith(".csv"):
        fname = fname[:-4]
    # 去掉 _stats 后缀
    if fname.endswith("_stats"):
        fname = fname[:-6]
    # 分割: p1_MODEL_p2_MODEL
    p2_marker = "_p2_"
    idx = fname.find(p2_marker)
    if idx > 0 and fname.startswith("p1_"):
        return fname[len("p1_"):idx]
    # 回退: 不含明确 p1/p2 标记的，返回整个文件名（去掉 _stats 后）
    return fname


def _scan_stats_csv_files():
    """扫描 outputs/ 目录，返回 stats CSV 文件列表及其型号名"""
    # 30秒 TTL 缓存：避免每次 /api/ml/models 都做文件系统遍历
    cached = file_cache.get("ml_scan_stats_csv")
    if cached is not None:
        return cached
    result = {}
    if not os.path.isdir(_OUTPUTS_DIR):
        file_cache.set("ml_scan_stats_csv", result, ttl=30)
        return result
    for entry in os.listdir(_OUTPUTS_DIR):
        entry_path = os.path.join(_OUTPUTS_DIR, entry)
        if not os.path.isfile(entry_path):
            continue
        if "stats" not in entry.lower() or not entry.endswith(".csv"):
            continue
        model = _extract_model_from_stats_csv(entry)
        if not model:
            continue
        if model not in result:
            result[model] = {
                "fan_model": model,
                "csv_path": entry_path,
                "csv_filename": entry,
                "file_size": os.path.getsize(entry_path),
                "mtime": os.path.getmtime(entry_path),
            }
    file_cache.set("ml_scan_stats_csv", result, ttl=30)
    return result


@ml_bp.route("/api/ml/models", methods=["GET"])
def api_ml_models():
    """返回系统中已分析的型号列表"""
    try:
        # 优先扫描 outputs/ 目录（stats CSV 文件的 fan_model 可能不在 DB 中）
        scanned = _scan_stats_csv_files()

        models = []
        if scanned:
            for model_name, info in scanned.items():
                from datetime import datetime
                mtime_dt = datetime.fromtimestamp(info["mtime"])
                models.append({
                    "fan_model": model_name,
                    "record_count": 1,
                    "last_analysis": mtime_dt.strftime("%Y-%m-%d %H:%M"),
                    "speeds": 0,
                })

        # 补充：从 Output 表查询额外的型号（（可能有但不在 outputs/ 根目录的））
        try:
            from db_models import DB_CONNECTED, Output
            if DB_CONNECTED and Output is not None:
                # 60秒 TTL 缓存 DB 查询结果（文件系统扫描已单独缓存）
                db_rows = query_cache.get("ml_models_db_rows")
                if db_rows is None:
                    from sqlalchemy import func
                    db_rows = (
                        Output.query
                        .with_entities(
                            Output.fan_model,
                            func.count(Output.id).label("record_count"),
                            func.max(Output.updated_at).label("last_analysis"),
                        )
                        .filter(Output.fan_model.isnot(None))
                        .filter(Output.fan_model != "")
                        .group_by(Output.fan_model)
                        .order_by(func.max(Output.updated_at).desc())
                        .all()
                    )
                    # 序列化为可缓存的基本类型
                    db_rows = [
                        (fm, cnt, la.strftime("%Y-%m-%d %H:%M") if la else "")
                        for fm, cnt, la in db_rows
                    ]
                    query_cache.set("ml_models_db_rows", db_rows, ttl=60)
                for fan_model, record_count, last_analysis in db_rows:
                    if fan_model and fan_model not in scanned:
                        models.append({
                            "fan_model": fan_model,
                            "record_count": record_count,
                            "last_analysis": last_analysis,
                            "speeds": 0,
                        })
        except Exception:
            pass

        if not models:
            return jsonify({"success": False, "error": "outputs/ 目录下未找到统计CSV文件。请先执行分析并导出报告。"}), 404

        # 按 last_analysis 降序排列
        models.sort(key=lambda m: m.get("last_analysis", ""), reverse=True)
        return jsonify({"success": True, "models": models})
    except Exception as e:
        current_app.logger.error(f"api_ml_models error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "获取型号列表失败"}), 500


@lru_cache(maxsize=32)
def _build_model_data(fan_model: str) -> dict:
    """从 outputs/ stats CSV 读取预计算数据，构建行式结构"""
    import csv as csv_module

    # 优先从 outputs/ 目录扫描（不依赖 DB 中的 fan_model 字段）
    scanned = _scan_stats_csv_files()
    if fan_model in scanned:
        csv_path = scanned[fan_model]["csv_path"]
    else:
        # 回退：从 Output 表查询
        from db_models import DB_CONNECTED, Output
        if not DB_CONNECTED or Output is None:
            raise ValueError(f"未找到型号 {fan_model} 的统计CSV文件")
        stats_files = (
            Output.query
            .filter(Output.fan_model == fan_model)
            .filter(Output.filename.ilike("%stats%.csv"))
            .order_by(Output.updated_at.desc())
            .all()
        )
        if not stats_files:
            raise ValueError(f"未找到型号 {fan_model} 的统计CSV文件。请先执行分析并导出报告。")
        csv_path = stats_files[0].file_path
        if not os.path.exists(csv_path):
            raise ValueError(f"统计CSV文件不存在: {csv_path}")

    # 读取 CSV 并转换为行式结构
    rows = []
    all_speeds = []

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv_module.DictReader(f)
        headers = reader.fieldnames or []

        # 动态检测可用端面和统计量
        face_stats = {}
        stat_map = {
            "平均值": "mean", "中位数": "median", "标准差": "std",
            "最小值": "min", "最大值": "max", "IQR": "iqr",
            "CV": "cv", "变异系数": "cv",
        }
        for h in headers:
            if not h or h.strip() == "转速":
                continue
            parts = h.split("-", 1)
            if len(parts) == 2:
                face = parts[0].strip()
                stat = parts[1].strip()
                stat_key = stat_map.get(stat)
                if stat_key and face:
                    if face not in face_stats:
                        face_stats[face] = {}
                    face_stats[face][stat_key] = h

        for row_dict in reader:
            speed = row_dict.get("转速", "").strip()
            if not speed:
                continue

            all_speeds.append(speed)
            flat_row = {"speed": speed}

            for face, stats in face_stats.items():
                face_lower = face.lower()
                for stat_key, col_name in stats.items():
                    val_str = row_dict.get(col_name, "").strip()
                    try:
                        flat_row[f"{face_lower}_{stat_key}"] = float(val_str)
                    except (ValueError, TypeError):
                        flat_row[f"{face_lower}_{stat_key}"] = 0.0

            rows.append(flat_row)

    if not rows:
        raise ValueError(f"统计CSV文件 {os.path.basename(csv_path)} 无有效数据")

    faces_available = list(face_stats.keys())

    return {
        "fan_model": fan_model,
        "speeds": all_speeds,
        "rows": rows,
        "stats": {
            "record_count": len(rows),
            "total_speeds": len(all_speeds),
            "faces_available": faces_available,
            "min_speed": all_speeds[0] if all_speeds else "",
            "max_speed": all_speeds[-1] if all_speeds else "",
        },
    }


@ml_bp.route("/api/ml/model_data/<fan_model>", methods=["GET"])
def api_ml_model_data(fan_model):
    """返回指定型号的预计算统计数据，供前端转换为面板 JSON 格式"""
    try:
        result = _build_model_data(fan_model)
        return jsonify({"success": True, **result})
    except RuntimeError as e:
        return jsonify({"success": False, "error": str(e)}), 503
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"api_ml_model_data error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "获取型号数据失败"}), 500
