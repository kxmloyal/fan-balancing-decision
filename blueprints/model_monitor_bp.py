#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
机型监控看板 — 按机型监控「推荐平衡转速 + 使用设备 + 告警」。
页面：已并入「数据仪表盘」（GET /dashboard，区块复用 model-monitor.js）
数据：GET /api/outputs/model_monitor（聚合 model_monitor.json 与 outputs 扫描，60s TTL 缓存）
"""
import logging

from flask import Blueprint, current_app, jsonify, redirect, url_for

from blueprints.outputs_bp import output_files_by_model
from services.model_monitor_service import build_model_monitor

logger = logging.getLogger(__name__)

model_monitor_bp = Blueprint("model_monitor", __name__)


@model_monitor_bp.route("/model-monitor")
def model_monitor_page():
    """机型监控看板已并入仪表盘，旧地址重定向到仪表盘"""
    return redirect(url_for("main.dashboard"))


@model_monitor_bp.route("/api/outputs/model_monitor")
def model_monitor_api():
    """聚合看板数据：机型监控记录 + outputs 文件扫描 + 告警规则（60s TTL 缓存）"""
    from app.utils.cache_utils import query_cache

    cached = query_cache.get("model_monitor")
    if cached is not None:
        return jsonify(cached)
    try:
        groups_resp = output_files_by_model()
        groups = groups_resp.get_json().get("data") or []
    except Exception as e:  # outputs 扫描异常时降级，仅展示监控记录
        logger.warning("获取 outputs 分组失败(降级): %s", e)
        groups = []
    output_folder = current_app.config.get("OUTPUT_FOLDER", "outputs")
    result = build_model_monitor(output_folder, groups)
    query_cache.set("model_monitor", result, ttl=60)
    return jsonify(result)
