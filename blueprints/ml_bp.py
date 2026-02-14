# -*- coding: utf-8 -*-
"""
机器学习蓝图：包含机器学习API
"""

from flask import Blueprint, render_template, jsonify, request, current_app

from machine_learning import (detect_anomaly_patterns,
                              multi_dimensional_analysis, predict_key_metrics,
                              predict_trend)

ml_bp = Blueprint("ml", __name__)


@ml_bp.route("/ml")
def ml():
    """机器学习页面"""
    return render_template("ml.html")


@ml_bp.route("/api/predict_trend", methods=["POST"])
def api_predict_trend():
    """预测趋势"""
    try:
        # 获取JSON数据
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请提供有效的JSON数据"})

        historical_data = data.get("historical_data")
        prediction_days = data.get("prediction_days", 7)
        model_type = data.get("model_type", "random_forest")

        if not historical_data:
            return jsonify({"success": False, "message": "请提供历史数据"})

        # 调用机器学习模块的预测函数
        result = predict_trend(historical_data, prediction_days, model_type)

        return jsonify({"success": True, "result": result})
    except Exception as e:
        current_app.logger.error(f"趋势预测API错误: {str(e)}")
        return jsonify({"success": False, "message": str(e)})


@ml_bp.route("/api/predict_key_metrics", methods=["POST"])
def api_predict_key_metrics():
    """预测关键指标"""
    try:
        # 获取JSON数据
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请提供有效的JSON数据"})

        historical_metrics = data.get("historical_metrics")
        prediction_periods = data.get("prediction_periods", 12)
        model_type = data.get("model_type", "gradient_boosting")

        if not historical_metrics:
            return jsonify({"success": False, "message": "请提供历史指标数据"})

        # 调用机器学习模块的预测函数
        result = predict_key_metrics(historical_metrics, prediction_periods, model_type)

        return jsonify({"success": True, "result": result})
    except Exception as e:
        current_app.logger.error(f"关键指标预测API错误: {str(e)}")
        return jsonify({"success": False, "message": str(e)})


@ml_bp.route("/api/multi_dimensional_analysis", methods=["POST"])
def api_multi_dimensional_analysis():
    """多维度数据分析"""
    try:
        # 获取JSON数据
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请提供有效的JSON数据"})

        analysis_data = data.get("data")
        dimensions = data.get("dimensions")
        metrics = data.get("metrics")

        if not analysis_data or not dimensions or not metrics:
            return jsonify(
                {"success": False, "message": "请提供完整的分析数据、维度和指标"}
            )

        # 调用机器学习模块的多维度分析函数
        result = multi_dimensional_analysis(analysis_data, dimensions, metrics)

        return jsonify({"success": True, "result": result})
    except Exception as e:
        current_app.logger.error(f"多维度数据分析API错误: {str(e)}")
        return jsonify({"success": False, "message": str(e)})


@ml_bp.route("/api/detect_anomaly_patterns", methods=["POST"])
def api_detect_anomaly_patterns():
    """检测异常模式"""
    try:
        # 获取JSON数据
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请提供有效的JSON数据"})

        time_series_data = data.get("time_series_data")
        window_size = data.get("window_size", 7)
        threshold = data.get("threshold", 2.0)

        if not time_series_data:
            return jsonify({"success": False, "message": "请提供时间序列数据"})

        # 调用机器学习模块的异常检测函数
        result = detect_anomaly_patterns(time_series_data, window_size, threshold)

        return jsonify({"success": True, "result": result})
    except Exception as e:
        current_app.logger.error(f"异常模式检测API错误: {str(e)}")
        return jsonify({"success": False, "message": str(e)})
