#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主蓝图模块
包含首页、仪表盘和核心功能路由
"""

import glob
import json
import logging
import os

# pickle 已替换为 json（安全：防止反序列化 RCE）
import sys
import time
from datetime import datetime, timedelta

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template
from flask_wtf.csrf import ValidationError, validate_csrf

from app.services.project_statistics import calculate_optimal_speed_evaluation
from app.utils.cache_utils import query_cache
from chart_generation_optimized import build_report_charts, generate_single_surface_plots
from chart_style_config import CHART_TYPE_CONFIG

from config import BALANCE_MACHINE_MODELS
from services.data_service import DataProcessingService
from services.model_monitor_service import record_model_monitor
from utils.data_validator import validate_and_align_data
from utils.error_handler import error_handler
from utils.file_manager import file_manager


def _get_balancer_models():
    from db_models import DB_CONNECTED as _db_ok
    from db_models import BalancerModel

    if _db_ok and BalancerModel is not None:
        try:
            with current_app.app_context():
                records = (
                    BalancerModel.query.filter_by(is_active=True)
                    .order_by(BalancerModel.model_name)
                    .all()
                )
                if records:
                    return [m.model_name for m in records]
        except Exception:
            pass
    return BALANCE_MACHINE_MODELS


AnalysisResult = None
db = None

# 导入缺失的模块
from flask import request, session, url_for

from app.services.project_statistics import (
    generate_single_surface_stats,
    generate_stats,
    generate_stats_data,
)

# 创建蓝图
main_bp = Blueprint("main", __name__)

# Session session 数据大小阈值（字节）—— 超过则使用文件缓存
SESSION_DATA_SIZE_LIMIT = 500 * 1024  # 500KB
SESSION_CACHE_MAX_AGE = 86400  # 24小时
SESSION_CACHE_MAX_SIZE = 50  # 最多50个缓存文件


def _estimate_data_size(data):
    """估算数据结构的近似内存大小"""
    try:
        return sys.getsizeof(str(data))
    except Exception:
        return 0


def _get_session_cache_dir():
    """获取session文件缓存目录"""
    cache_dir = os.path.join(current_app.config.get("OUTPUT_FOLDER", "outputs"), ".session_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _cache_large_data_to_file(key, data, namespace=None):
    """将大型数据缓存到文件，返回缓存引用（JSON 安全序列化，防止 pickle RCE）
    
    namespace: 命名空间标识符。默认使用 session.sid（每浏览器独立），
               传入 fan_model 则跨电脑共享该型号的缓存。
    """
    cache_dir = _get_session_cache_dir()

    now = time.time()
    for fname in os.listdir(cache_dir):
        fpath = os.path.join(cache_dir, fname)
        try:
            if now - os.path.getmtime(fpath) > SESSION_CACHE_MAX_AGE:
                os.remove(fpath)
        except OSError:
            pass
    files = sorted(
        [os.path.join(cache_dir, f) for f in os.listdir(cache_dir)],
        key=lambda p: os.path.getmtime(p),
    )
    while len(files) > SESSION_CACHE_MAX_SIZE:
        try:
            os.remove(files.pop(0))
        except OSError:
            pass

    if namespace is None:
        namespace = session.sid
    safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in str(namespace))
    cache_file = os.path.join(cache_dir, f"{key}_{safe_name}.json")
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)
        return {"_cached": True, "_cache_file": cache_file, "_cache_key": key}
    except Exception as e:
        current_app.logger.error(f"Session data file cache failed: {e}")
        return data


def _load_cached_data(cache_ref):
    """从文件缓存加载数据（JSON 优先，兼容旧 pickle 文件）"""
    if isinstance(cache_ref, dict) and cache_ref.get("_cached"):
        cache_file = cache_ref.get("_cache_file")
        if cache_file and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                try:
                    import pickle

                    with open(cache_file, "rb") as f:
                        data = pickle.load(f)
                    current_app.logger.warning(
                        "Loaded legacy pickle cache, converting to JSON: %s", cache_file
                    )
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, default=str)
                    return data
                except Exception:
                    pass
            except Exception as e:
                current_app.logger.error("Load cached session data failed: %s", e)
    return cache_ref


def _save_to_session_with_limit(session_dict, session_key, data, namespace=None):
    """保存数据到session，大数据使用文件缓存
    
    namespace: 缓存命名空间。传入 fan_model 可实现跨电脑共享该型号数据。
              为 None 时自动从 data 中提取 fan_model。
    """
    if namespace is None and isinstance(data, dict):
        namespace = data.get("fan_model") or data.get("model_name")
    if _estimate_data_size(data) > SESSION_DATA_SIZE_LIMIT:
        session_dict[session_key] = _cache_large_data_to_file(session_key, data, namespace)
    else:
        session_dict[session_key] = data


def _get_from_session_with_cache(session_dict, session_key):
    """从session获取数据，自动从文件缓存恢复"""
    val = session_dict.get(session_key)
    return _load_cached_data(val) if val is not None else None


@main_bp.route("/", methods=["GET", "POST"])
def index():
    """首页：文件上传+结果展示"""
    if request.method == "POST":
        # 检查是否是图表类型更新请求
        p1_file = request.files.get("p1_file")
        p2_file = request.files.get("p2_file")
        st_file = request.files.get("st_file")

        # 检测是否是图表更新请求
        is_chart_update = is_chart_update_request(p1_file, p2_file, st_file)

        # 检查是否是组合图表请求
        is_combined_chart = "combined_chart" in request.form

        if is_combined_chart:
            return handle_combined_chart_request()
        elif is_chart_update:
            return handle_chart_update_request()
        else:
            return handle_file_upload(p1_file, p2_file, st_file)
    else:
        return handle_get_request()


def is_chart_update_request(p1_file, p2_file, st_file):
    """
    检测是否是图表更新请求

    图表更新请求的条件：
    1. 请求中包含 chart_types 或 chart_update 参数
    2. 没有新的文件上传（所有文件对象都不存在或文件名为空）
    """
    has_chart_params = "chart_types" in request.form or "chart_update" in request.form
    no_new_files = not (
        (p1_file and p1_file.filename and p1_file.filename != "")
        or (p2_file and p2_file.filename and p2_file.filename != "")
        or (st_file and st_file.filename and st_file.filename != "")
    )
    return has_chart_params and no_new_files


def handle_combined_chart_request():
    """处理组合图表请求"""
    saved_results = _get_from_session_with_cache(session, "saved_results")
    if not saved_results:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "message": "会话已过期，请重新上传数据文件！"}), 401
        flash("会话已过期，请重新上传数据文件！")
        return redirect(request.url)

    # 获取表单数据
    chart_types = request.form.get("chart_types", "box").split(",")
    chart_layout = request.form.get("chartLayout", "stacked")

    # 更新Session中的图表设置
    saved_results["chart_types"] = chart_types
    saved_results["chart_layout"] = chart_layout

    # 从session中恢复大型数据
    parsed_data = _load_cached_data(saved_results.get("parsed_data"))
    output_prefix = saved_results.get("output_prefix")
    single_surface = saved_results.get("single_surface")

    try:
        if single_surface:
            plots = generate_single_surface_plots(
                parsed_data,
                output_prefix,
                single_surface,
                current_app.config["OUTPUT_FOLDER"],
                chart_types,
                fan_model=saved_results.get("fan_model"),
            )
        else:
            plots = build_report_charts(
                parsed_data,
                output_prefix,
                current_app.config["OUTPUT_FOLDER"],
                chart_types,
                fan_model=saved_results.get("fan_model"),
            )
    except (ValueError, IOError, TypeError) as e:  # 捕获具体异常类型
        user_id = session.get("user_id", "anonymous")
        ip_address = request.remote_addr
        error_message = error_handler.handle_exception(e, "main_bp", user_id, ip_address)
        flash(f"组合图表生成失败：{error_message}")
        return redirect(request.url)

    # 更新Session中的图表数据
    saved_results["plots"] = plots
    _save_to_session_with_limit(session, "saved_results", saved_results)

    # 返回完整页面
    return render_template(
        "index.html",
        plots=plots,
        stats_html=saved_results["stats_html"],
        stats_csv=saved_results["stats_csv"],
        has_p1=saved_results["has_p1"],
        has_p2=saved_results["has_p2"],
        has_st=saved_results["has_st"],
        saved_results=saved_results,
        chart_type_config=CHART_TYPE_CONFIG,
        balance_machine_models=_get_balancer_models(),
    )


def handle_chart_update_request():
    """处理图表类型更新请求"""
    saved_results = _get_from_session_with_cache(session, "saved_results")
    if not saved_results:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(
                {
                    "success": False,
                    "message": "会话已过期，请重新上传数据文件！",
                }
            )
        flash("会话已过期，请重新上传数据文件！")
        return redirect(request.url)

    # 获取图表类型选择，优先从隐藏字段获取
    chart_types_str = request.form.get("chart_types", None)
    if chart_types_str:
        chart_types = chart_types_str.split(",")
    else:
        # 尝试从复选框字段获取图表类型
        chart_types = request.form.getlist("chart_types[]")
        if not chart_types:
            # 尝试从其他可能的字段获取
            chart_types = request.form.getlist("chart_types")
            if not chart_types:
                chart_types = ["box"]

    # 获取图表布局选择
    chart_layout = request.form.get("chartLayout", "stacked")

    # 记录日志以便调试
    current_app.logger.info(f"图表类型: {chart_types}")
    current_app.logger.info(f"图表布局: {chart_layout}")

    # 重新生成图表
    try:
        if saved_results.get("single_surface"):
            plots = generate_single_surface_plots(
                _load_cached_data(saved_results["parsed_data"]),
                saved_results["output_prefix"],
                saved_results["single_surface"],
                current_app.config["OUTPUT_FOLDER"],
                chart_types,
                fan_model=saved_results.get("fan_model"),
            )
        else:
            plots = build_report_charts(
                _load_cached_data(saved_results["parsed_data"]),
                saved_results["output_prefix"],
                current_app.config["OUTPUT_FOLDER"],
                chart_types,
                fan_model=saved_results.get("fan_model"),
            )
    except (ValueError, IOError, TypeError) as e:  # 捕获具体异常类型
        user_id = session.get("user_id", "anonymous")
        ip_address = request.remote_addr
        error_message = error_handler.handle_exception(e, "main_bp", user_id, ip_address)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "message": f"图表生成失败：{error_message}"})
        flash(f"图表生成失败：{error_message}")
        return redirect(request.url)

    # 页面变量
    has_p1 = saved_results["has_p1"]
    has_p2 = saved_results["has_p2"]
    has_st = saved_results["has_st"]

    # 更新保存的结果
    saved_results["plots"] = plots
    saved_results["chart_types"] = chart_types  # 保存图表类型选择
    saved_results["chart_layout"] = chart_layout  # 保存图表布局选择

    _save_to_session_with_limit(session, "saved_results", saved_results)

    # 检查是否是 AJAX 请求
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        # 渲染图表部分模板
        charts_html = render_template(
            "_charts_partial.html",
            plots=plots,
            has_p1=has_p1,
            has_p2=has_p2,
            has_st=has_st,
            chart_layout=chart_layout,
            chart_type_config=CHART_TYPE_CONFIG,
        )
        # 返回包含图表HTML的JSON响应
        return jsonify(
            {
                "success": True,
                "message": "图表更新成功",
                "chart_types": chart_types,
                "chart_layout": chart_layout,
                "charts_html": charts_html,
            }
        )
    else:
        # 返回完整页面
        return render_template(
            "index.html",
            plots=plots,
            stats_html=saved_results["stats_html"],
            stats_csv=saved_results["stats_csv"],
            has_p1=has_p1,
            has_p2=has_p2,
            has_st=has_st,
            saved_results=saved_results,
            chart_type_config=CHART_TYPE_CONFIG,
            chart_layout=chart_layout,
        )


def handle_file_upload(p1_file, p2_file, st_file):
    """处理文件上传"""
    surface_data = {}
    upload_files = []
    data_quality_warnings = []

    fan_model = request.form.get("fan_model", "").strip()
    if not fan_model:
        flash("请输入扇叶型号！")
        return redirect(request.url)
    if not all(c.isalnum() or c in " -_." for c in fan_model):
        flash("扇叶型号只能包含字母、数字、空格、连字符、下划线和点！")
        return redirect(request.url)
    if fan_model in (".", "..") or fan_model.startswith("."):
        flash("扇叶型号不能以点开头！")
        return redirect(request.url)

    balance_machine_model = request.form.get("balance_machine_model", "").strip()
    if not balance_machine_model:
        flash("请选择平衡机型号！")
        return redirect(request.url)

    # 检查总存储是否超过限制
    storage_ok, total_size = file_manager.check_total_storage()
    if not storage_ok:
        flash(f"存储空间不足！当前总存储：{total_size / (1024 * 1024 * 1024):.2f}GB，限制：5GB")
        return redirect(request.url)

    # 检查用户文件数量是否超过限制
    user_id = session.get("user_id", "anonymous")
    file_limit_ok, file_count = file_manager.check_user_file_limit(user_id)
    if not file_limit_ok:
        flash(f"文件数量超过限制！当前文件数：{file_count}，限制：50个")
        return redirect(request.url)

    # 初始化数据处理服务
    data_service = DataProcessingService(current_app.config["UPLOAD_FOLDER"])

    # 解析P1面文件（如果上传）
    if p1_file and p1_file.filename != "":
        if not file_manager.allowed_file(p1_file.filename):
            flash("不支持的文件类型，请上传CSV或Excel文件")
            return redirect(request.url)
        if not file_manager.check_file_size(p1_file.content_length):
            flash(
                f"P1面文件大小超过限制！当前大小：{
                    p1_file.content_length / (1024 * 1024):.2f}MB，限制：100MB"
            )
            return redirect(request.url)
        if not file_manager.validate_magic_bytes(p1_file):
            flash("P1面文件类型与内容不匹配，请上传有效的CSV/Excel文件")
            return redirect(request.url)

        p1_path, p1_data, error_message = data_service.process_file(p1_file, "p1_")
        if error_message:
            flash(f"P1面文件处理失败：{error_message}")
            return redirect(request.url)
        else:
            upload_files.append(os.path.basename(p1_path))
            surface_data["p1"] = p1_data.data

    # 解析P2面文件（如果上传）
    if p2_file and p2_file.filename != "":
        if not file_manager.allowed_file(p2_file.filename):
            flash("不支持的文件类型，请上传CSV或Excel文件")
            return redirect(request.url)
        if not file_manager.check_file_size(p2_file.content_length):
            flash(
                f"P2面文件大小超过限制！当前大小：{
                    p2_file.content_length / (1024 * 1024):.2f}MB，限制：100MB"
            )
            return redirect(request.url)
        if not file_manager.validate_magic_bytes(p2_file):
            flash("P2面文件类型与内容不匹配，请上传有效的CSV/Excel文件")
            return redirect(request.url)

        p2_path, p2_data, error_message = data_service.process_file(p2_file, "p2_")
        if error_message:
            flash(f"P2面文件处理失败：{error_message}")
            return redirect(request.url)
        else:
            upload_files.append(os.path.basename(p2_path))
            surface_data["p2"] = p2_data.data

    # 解析ST面文件（如果上传）
    if st_file and st_file.filename != "":
        if not file_manager.allowed_file(st_file.filename):
            flash("不支持的文件类型，请上传CSV或Excel文件")
            return redirect(request.url)
        if not file_manager.check_file_size(st_file.content_length):
            flash(
                f"ST面文件大小超过限制！当前大小：{
                    st_file.content_length / (1024 * 1024):.2f}MB，限制：100MB"
            )
            return redirect(request.url)
        if not file_manager.validate_magic_bytes(st_file):
            flash("ST面文件类型与内容不匹配，请上传有效的CSV/Excel文件")
            return redirect(request.url)

        st_path, st_data, error_message = data_service.process_file(st_file, "st_")
        if error_message:
            flash(f"ST面文件处理失败：{error_message}")
            return redirect(request.url)
        else:
            upload_files.append(os.path.basename(st_path))
            surface_data["st"] = st_data.data
    if not surface_data:
        flash("请至少上传一个面的数据文件！")
        return redirect(request.url)

    # 数据质量检查
    for surface_name, data_dict in surface_data.items():
        empty_speeds = []
        outlier_speeds = []
        for speed, samples in data_dict.items():
            if not samples or len(samples) == 0:
                empty_speeds.append(str(speed))
                continue
            if len(samples) < 3:
                data_quality_warnings.append(
                    f"{surface_name.upper()}面转速 {speed} 的数据量不足（仅{len(samples)}个样本），"
                    f"统计结果可能不准确"
                )
            mean_val = sum(samples) / len(samples)
            if mean_val != 0:
                for s in samples:
                    if abs(s / mean_val) > 100:
                        outlier_speeds.append(str(speed))
                        break
        if empty_speeds:
            data_quality_warnings.append(
                f"{surface_name.upper()}面转速 {', '.join(empty_speeds)} 的数据为空，已自动跳过"
            )
        if outlier_speeds:
            data_quality_warnings.append(
                f"{surface_name.upper()}面转速 {', '.join(outlier_speeds)} "
                f"存在异常大的值，请检查数据是否正确"
            )
    for warning in data_quality_warnings:
        flash(warning)

    # 生成输出前缀
    output_prefix = "_".join([os.path.splitext(f)[0] for f in upload_files])

    current_app.logger.info(f"处理后的surface_data: {list(surface_data.keys())}")

    # 场景1：同时上传P1和P2面（可能还有ST面）
    if "p1" in surface_data and "p2" in surface_data:
        return handle_double_surface_case(
            surface_data, output_prefix, fan_model, balance_machine_model
        )
    # 场景2：仅上传单一文件（P1、P2或ST）
    else:
        return handle_single_surface_case(
            surface_data, output_prefix, fan_model, balance_machine_model
        )


def handle_double_surface_case(surface_data, output_prefix, fan_model, balance_machine_model):
    """处理双表面情况"""
    p1_speeds = sorted(surface_data["p1"].keys())
    p2_speeds = sorted(surface_data["p2"].keys())
    st_data = surface_data.get("st", {})
    _save_to_session_with_limit(session, "p1_data", surface_data["p1"])
    _save_to_session_with_limit(session, "p2_data", surface_data["p2"])
    _save_to_session_with_limit(session, "st_data", st_data)
    session["output_prefix"] = output_prefix

    # 转速完全一致：直接生成结果
    if set(p1_speeds) == set(p2_speeds):
        # 初始化数据处理服务
        data_service = DataProcessingService(current_app.config["UPLOAD_FOLDER"])

        # 使用数据处理服务验证和对齐数据
        parsed_data, data_warnings = data_service.validate_and_align(
            surface_data["p1"], surface_data["p2"], st_data
        )

        # 数据警告如果有的话，添加到flash消息
        if data_warnings:
            flash("数据警告：" + "; ".join(data_warnings))
        plots = build_report_charts(
            parsed_data, output_prefix, current_app.config["OUTPUT_FOLDER"], fan_model=fan_model
        )
        logger = logging.getLogger(__name__)
        logger.info("图表生成完成: plots keys=%s", list(plots.keys()) if plots else "None/empty")
        try:
            stats_html, stats_csv = generate_stats(
                parsed_data, output_prefix, current_app.config["OUTPUT_FOLDER"]
            )
            # 计算最优转速评估
            evaluation_report = calculate_optimal_speed_evaluation(generate_stats_data(parsed_data))
        except (ValueError, IOError, TypeError) as e:  # 捕获具体异常类型
            user_id = session.get("user_id", "anonymous")
            ip_address = request.remote_addr
            error_message = error_handler.handle_exception(e, "main_bp", user_id, ip_address)
            flash(f"统计报告生成失败：{error_message}")
            return redirect(request.url)

        # 页面变量
        has_p1 = bool(surface_data.get("p1"))
        has_p2 = bool(surface_data.get("p2"))
        has_st = bool(surface_data.get("st"))

        # 保存结果到session，用于图表更新——大数据集使用文件缓存
        saved_results = {
            "parsed_data": parsed_data,
            "output_prefix": output_prefix,
            "stats_html": stats_html,
            "stats_csv": stats_csv,
            "evaluation_report": evaluation_report,
            "has_p1": has_p1,
            "has_p2": has_p2,
            "has_st": has_st,
            "plots": plots,
            "chart_types": ["box"],
            "chart_layout": "stacked",
            "fan_model": fan_model,
            "balance_machine_model": balance_machine_model,
        }
        _save_to_session_with_limit(session, "saved_results", saved_results)
        record_model_monitor(current_app.config.get("OUTPUT_FOLDER", "outputs"), fan_model, evaluation_report, balance_machine_model)

        logger.info(
            "准备渲染模板: has_p1=%s, has_p2=%s, stats_html长度=%d, evaluation_report=%s",
            has_p1,
            has_p2,
            len(stats_html) if stats_html else 0,
            "有" if evaluation_report else "无",
        )

        return render_template(
            "index.html",
            plots=plots,
            stats_html=stats_html,
            stats_csv=os.path.basename(stats_csv) if stats_csv else None,
            evaluation_report=evaluation_report,
            has_p1=has_p1,
            has_p2=has_p2,
            has_st=has_st,
            saved_results=saved_results,
            chart_type_config=CHART_TYPE_CONFIG,
            balance_machine_models=_get_balancer_models(),
        )
    # 转速不一致：跳转到匹配页面
    else:
        # 将数据保存到session，供匹配页面使用——大数据集使用文件缓存
        _save_to_session_with_limit(session, "p1_data", surface_data["p1"])
        _save_to_session_with_limit(session, "p2_data", surface_data["p2"])
        _save_to_session_with_limit(session, "st_data", st_data)
        session["output_prefix"] = output_prefix
        session["fan_model"] = fan_model
        session["balance_machine_model"] = balance_machine_model
        return redirect(url_for("main.match_speeds"))


def handle_single_surface_case(surface_data, output_prefix, fan_model, balance_machine_model):
    """处理单表面情况"""
    # 确定上传的是哪个面
    surface_type = list(surface_data.keys())[0]  # 只有一个键
    speeds = sorted(surface_data[surface_type].keys())

    # 构造数据结构
    parsed_data = []
    for speed in speeds:
        data_item = {
            "speed": speed,
            "p1_samples": (surface_data[surface_type][speed] if surface_type == "p1" else []),
            "p2_samples": (surface_data[surface_type][speed] if surface_type == "p2" else []),
            "sum_samples": (surface_data[surface_type][speed] if surface_type == "st" else []),
        }
        parsed_data.append(data_item)

    # 生成图表和统计信息
    plots = generate_single_surface_plots(
        parsed_data,
        output_prefix,
        surface_type,
        current_app.config["OUTPUT_FOLDER"],
        fan_model=fan_model,
    )
    try:
        stats_html, stats_csv = generate_single_surface_stats(
            parsed_data,
            output_prefix,
            surface_type,
            current_app.config["OUTPUT_FOLDER"],
        )
        # 计算最优转速评估
        evaluation_report = calculate_optimal_speed_evaluation(generate_stats_data(parsed_data))
    except (ValueError, IOError, TypeError) as e:  # 捕获具体异常类型
        user_id = session.get("user_id", "anonymous")
        ip_address = request.remote_addr
        error_message = error_handler.handle_exception(e, "main_bp", user_id, ip_address)
        flash(f"统计报告生成失败：{error_message}")
        return redirect(request.url)

    # 页面变量
    has_p1 = surface_type == "p1"
    has_p2 = surface_type == "p2"
    has_st = surface_type == "st"

    # 保存结果到session，用于图表更新——大数据集使用文件缓存
    saved_results = {
        "parsed_data": parsed_data,
        "output_prefix": output_prefix,
        "stats_html": stats_html,
        "stats_csv": stats_csv,
        "has_p1": has_p1,
        "has_p2": has_p2,
        "has_st": has_st,
        "single_surface": surface_type,
        "plots": plots,
        "chart_types": ["box"],
        "chart_layout": "stacked",
        "fan_model": fan_model,
        "balance_machine_model": balance_machine_model,
    }
    _save_to_session_with_limit(session, "saved_results", saved_results)
    record_model_monitor(current_app.config.get("OUTPUT_FOLDER", "outputs"), fan_model, evaluation_report, balance_machine_model)

    # 结果渲染
    return render_template(
        "index.html",
        plots=plots,
        stats_html=stats_html,
        stats_csv=os.path.basename(stats_csv) if stats_csv else None,
        has_p1=has_p1,
        has_p2=has_p2,
        has_st=has_st,
        saved_results=saved_results,
        chart_type_config=CHART_TYPE_CONFIG,
        evaluation_report=evaluation_report,
    )


def handle_get_request():
    """处理GET请求"""
    # 检查session中是否有保存的结果
    saved_results = _get_from_session_with_cache(session, "saved_results")
    if saved_results:
        # 从session中恢复之前的分析状态
        return render_template(
            "index.html",
            plots=saved_results.get("plots"),
            stats_html=saved_results.get("stats_html"),
            stats_csv=os.path.basename(saved_results.get("stats_csv"))
            if saved_results.get("stats_csv")
            else None,
            has_p1=saved_results.get("has_p1", False),
            has_p2=saved_results.get("has_p2", False),
            has_st=saved_results.get("has_st", False),
            saved_results=saved_results,
            chart_type_config=CHART_TYPE_CONFIG,
            evaluation_report=saved_results.get(
                "evaluation_report",
                {
                    "best_speeds": [],
                    "speed_detailed_scores": {},
                    "detailed_scores": {},  # 保持与之前的兼容性
                },
            ),
            chart_layout=saved_results.get("chart_layout", "stacked"),
            balance_machine_models=_get_balancer_models(),
        )
    else:
        default_evaluation_report = {
            "best_speeds": [],
            "speed_detailed_scores": {},
            "detailed_scores": {},
        }
        return render_template(
            "index.html",
            plots=None,
            stats_html=None,
            stats_csv=None,
            has_p1=False,
            has_p2=False,
            has_st=False,
            chart_type_config=CHART_TYPE_CONFIG,
            evaluation_report=default_evaluation_report,
            balance_machine_models=_get_balancer_models(),
        )


@main_bp.route("/match_speeds", methods=["GET", "POST"])
def match_speeds():
    """转速匹配页面"""

    # 从session获取数据
    p1_data = _get_from_session_with_cache(session, "p1_data")
    p2_data = _get_from_session_with_cache(session, "p2_data")
    st_data = _get_from_session_with_cache(session, "st_data") or {}
    output_prefix = session.get("output_prefix", "output")

    # 检查数据是否存在
    if not p1_data or not p2_data:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "message": "会话已过期，请重新上传文件！"}), 401
        flash("未找到转速数据，请重新上传文件！")
        return redirect(url_for("main.index"))

    # 获取P1和P2的转速列表
    p1_speeds = sorted(p1_data.keys())
    p2_speeds = sorted(p2_data.keys())

    # 处理POST请求
    if request.method == "POST":
        try:
            # 收集匹配结果
            matches = {}
            for p1_speed in p1_speeds:
                matched_p2 = request.form.get(f"match_{p1_speed}", "none")
                if matched_p2 != "none":
                    matches[p1_speed] = matched_p2

            # 生成匹配后的数据结构
            parsed_data = []
            unmatched_p1 = []
            unmatched_p2 = set(p2_speeds)

            # 初始化数据处理服务
            data_service = DataProcessingService(current_app.config["UPLOAD_FOLDER"])

            # 处理匹配的转速
            for p1_speed in p1_speeds:
                if p1_speed in matches:
                    p2_speed = matches[p1_speed]
                    p2_samples = p2_data.get(p2_speed, [])
                    st_samples_for_speed = st_data.get(p1_speed, [])

                    # 验证和对齐数据
                    p1_aligned, p2_aligned, st_samples, data_info = validate_and_align_data(
                        p1_data[p1_speed], p2_samples, st_samples_for_speed
                    )

                    parsed_data.append(
                        {
                            "speed": p1_speed,
                            "p1_samples": p1_aligned,
                            "p2_samples": p2_aligned,
                            "sum_samples": st_samples,
                        }
                    )

                    # 从unmatched_p2中移除已匹配的P2转速
                    if p2_speed in unmatched_p2:
                        unmatched_p2.remove(p2_speed)
                else:
                    # 未匹配的P1转速
                    unmatched_p1.append(p1_speed)

            existing_saved = _get_from_session_with_cache(session, "saved_results") or {}
            fan_model = existing_saved.get("fan_model")
            balance_machine_model = existing_saved.get("balance_machine_model", "")

            # 生成图表
            plots = build_report_charts(
                parsed_data, output_prefix, current_app.config["OUTPUT_FOLDER"], fan_model=fan_model
            )

            # 生成统计报告
            stats_html, stats_csv = generate_stats(
                parsed_data, output_prefix, current_app.config["OUTPUT_FOLDER"]
            )

            # 计算最优转速评估
            evaluation_report = calculate_optimal_speed_evaluation(generate_stats_data(parsed_data))

            # 保存结果到session
            saved_results = {
                "parsed_data": parsed_data,
                "output_prefix": output_prefix,
                "stats_html": stats_html,
                "stats_csv": stats_csv,
                "evaluation_report": evaluation_report,
                "has_p1": True,
                "has_p2": True,
                "has_st": bool(st_data),
                "plots": plots,
                "chart_types": ["box"],
                "chart_layout": "stacked",
                "unmatched_p1": unmatched_p1,
                "unmatched_p2": list(unmatched_p2),
                "fan_model": fan_model,
                "balance_machine_model": balance_machine_model,
            }
            _save_to_session_with_limit(session, "saved_results", saved_results)
            record_model_monitor(current_app.config.get("OUTPUT_FOLDER", "outputs"), fan_model, evaluation_report, balance_machine_model)

            # 跳转到匹配结果页面
            return redirect(url_for("main.match_result"))

        except (ValueError, IOError, TypeError) as e:  # 捕获具体异常类型
            user_id = session.get("user_id", "anonymous")
            ip_address = request.remote_addr
            error_message = error_handler.handle_exception(e, "main_bp", user_id, ip_address)
            flash(f"匹配处理失败：{error_message}")
            return redirect(request.url)

    # GET请求：生成默认匹配列表
    default_matches = []
    for p1_speed in p1_speeds:
        # 尝试自动匹配最接近的P2转速
        matched_p2 = None
        # 对于字符串类型的转速名称，直接检查是否有对应的P2转速
        # 例如："卓茂P1" -> "卓茂P2"
        corresponding_p2_speed = p1_speed.replace("P1", "P2")
        if corresponding_p2_speed in p2_speeds:
            matched_p2 = corresponding_p2_speed

        default_matches.append({"p1_speed": p1_speed, "matched_p2": matched_p2})

    return render_template(
        "match_speeds.html", default_matches=default_matches, p2_speeds=p2_speeds
    )


@main_bp.route("/reset", methods=["POST"])
def reset():
    """重置所有数据和文件"""
    try:
        validate_csrf(request.headers.get("X-CSRFToken") or request.form.get("csrf_token", ""))
    except ValidationError:
        flash("安全验证失败，请刷新页面后重试")
        return redirect(url_for("main.index"))

    # 保留 CSRF token 不轮换：session.clear() 会删除 csrf_token，下次渲染生成新 token，
    # 而浏览器 reload 可能命中缓存/bfcache 仍持有旧 token，导致提交报 "CSRF tokens do not match"
    _csrf_token = session.get("csrf_token")
    session.clear()
    if _csrf_token:
        session["csrf_token"] = _csrf_token

    # 清除所有可能的分析相关数据
    keys_to_clear = [
        "saved_results",
        "p1_data",
        "p2_data",
        "st_data",
        "output_prefix",
        "analysis_results",
        "chart_cache",
    ]
    for key in keys_to_clear:
        if key in session:
            del session[key]

    cache_dir = os.path.join(current_app.config.get("OUTPUT_FOLDER", "outputs"), ".session_cache")
    if os.path.exists(cache_dir):
        pattern = os.path.join(cache_dir, f"*_{session.sid}.json")
        for f in glob.glob(pattern):
            try:
                os.remove(f)
            except OSError:
                pass

    flash("已成功重置所有分析数据、表单输入和上传文件")
    return redirect(url_for("main.index"))


def _extract_speed_from_filename(filename):
    """从报告文件名提取转速（SN300-12_1500rpm_动平衡分析报告.html → 1500rpm）"""
    for part in filename.replace("动平衡分析报告", "").replace(".", " ").split("_"):
        p = part.strip()
        if p.lower().endswith("rpm"):
            return p
    return "未知"


def _lookup_latest_speed(monitor_data, fan_model):
    """查机型监控记录中该型号最近一次推荐转速"""
    if not fan_model or fan_model == "未知":
        return "未知"
    records = monitor_data.get(fan_model) or []
    if records:
        best_speeds = records[-1].get("best_speeds") or []
        if best_speeds:
            return str(best_speeds[0])
    return "未知"


def _get_dashboard_data():
    # 60秒 TTL 缓存：仪表盘数据变更频率低，避免每次刷新重复扫描文件系统
    cached = query_cache.get("dashboard_data")
    if cached is not None:
        return cached

    # FS 数据源：outputs 报告文件扫描 + 机型监控记录（model_monitor.json）。
    # DB_CONNECTED 未启用时仪表盘不再空壳，直接使用文件系统真实数据。
    from blueprints.outputs_bp import _list_filesystem_files
    from services.model_monitor_service import load_monitor_data

    output_folder = current_app.config.get("OUTPUT_FOLDER", "outputs")
    files = _list_filesystem_files()
    monitor = load_monitor_data(output_folder)

    # 只统计「评估报告」HTML（排除 chart_ 图表与内部元数据文件）
    reports = [
        f
        for f in files
        if f.get("file_type") == "html"
        and not f.get("filename", "").startswith("chart_")
        and "动平衡分析报告" in f.get("filename", "")
    ]
    reports.sort(key=lambda x: x.get("created_at") or x.get("updated_at"), reverse=True)

    total_evaluations = len(reports)

    latest_evaluation = "暂无"
    if reports:
        latest_created = reports[0].get("created_at") or reports[0].get("updated_at")
        if latest_created:
            latest_evaluation = latest_created.strftime("%Y-%m-%d %H:%M")

    recent_records = []
    for f in reports[:10]:
        created = f.get("created_at") or f.get("updated_at")
        fan_model = f.get("fan_model") or "未知"
        # 评估转速：优先文件名内嵌转速；新格式文件名不含转速时回退该型号
        # 最近一次监控推荐转速，避免列表大面积显示"未知"
        evaluated_speeds = _extract_speed_from_filename(f["filename"])
        if evaluated_speeds == "未知":
            evaluated_speeds = _lookup_latest_speed(monitor, fan_model)
        recent_records.append(
            {
                "id": f.get("id") or f["filename"],
                "filename": f["filename"],
                # 相对 OUTPUT_FOLDER 路径，供报告查看/下载链接使用
                "file_path_rel": os.path.relpath(f["file_path"], output_folder),
                "timestamp": created.strftime("%Y-%m-%d %H:%M:%S") if created else "",
                "fan_model": fan_model,
                "evaluated_speeds": evaluated_speeds,
                "optimal_speed": _lookup_latest_speed(monitor, fan_model),
            }
        )

    # 7日评估趋势（按报告文件创建时间，含今天共 7 个点）
    today = datetime.now()
    date_counts = {}
    for f in reports:
        created = f.get("created_at") or f.get("updated_at")
        if created and created >= today - timedelta(days=6):
            ds = created.strftime("%Y-%m-%d")
            date_counts[ds] = date_counts.get(ds, 0) + 1
    evaluation_dates = []
    evaluation_counts = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        evaluation_dates.append(d.strftime("%m-%d"))
        evaluation_counts.append(date_counts.get(d.strftime("%Y-%m-%d"), 0))

    # 型号分布 + 已评估型号数（按报告 fan_model 聚合）
    model_count_map = {}
    for f in reports:
        fm = f.get("fan_model") or "未知"
        model_count_map[fm] = model_count_map.get(fm, 0) + 1
    model_rows = sorted(model_count_map.items(), key=lambda x: x[1], reverse=True)[:6]
    model_labels = [m for m, _ in model_rows]
    model_counts = [c for _, c in model_rows]
    model_count = len(model_count_map)

    # 转速分布 + 最常见最优转速 + 稳定性（来源：机型监控记录 best_speeds）
    speed_count_map = {}
    for records in monitor.values():
        for r in records:
            for sp in r.get("best_speeds") or []:
                key = str(sp)
                speed_count_map[key] = speed_count_map.get(key, 0) + 1
    speed_rows = sorted(speed_count_map.items(), key=lambda x: x[1], reverse=True)[:6]
    speed_labels = [s for s, _ in speed_rows]
    speed_counts = [c for _, c in speed_rows]
    optimal_speed = "—"
    speed_stability = 0
    if speed_rows:
        optimal_speed = speed_rows[0][0]
        total_with_speed = sum(speed_counts)
        if total_with_speed > 0:
            speed_stability = round(speed_rows[0][1] / total_with_speed * 100)

    result = {
        "total_evaluations": total_evaluations,
        "optimal_speed": optimal_speed,
        "model_count": model_count,
        "latest_evaluation": latest_evaluation,
        "speed_stability": speed_stability,
        "evaluation_dates": evaluation_dates,
        "evaluation_counts": evaluation_counts,
        "speed_labels": speed_labels,
        "speed_counts": speed_counts,
        "model_labels": model_labels,
        "model_counts": model_counts,
        "recent_records": recent_records,
    }
    query_cache.set("dashboard_data", result, ttl=60)
    return result


@main_bp.route("/dashboard")
def dashboard():
    data = _get_dashboard_data()
    return render_template("dashboard.html", **data)


@main_bp.route("/api/dashboard/data")
def api_dashboard_data():
    try:
        data = _get_dashboard_data()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        current_app.logger.error("Dashboard API failed: %s", str(e))
        return jsonify({"success": False, "error": "获取仪表盘数据失败，请稍后重试"}), 500


@main_bp.route("/match_result")
def match_result():
    """匹配结果页面"""
    # 从session获取匹配结果
    saved_results = _get_from_session_with_cache(session, "saved_results")
    if not saved_results:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "message": "会话已过期，请重新进行转速匹配！"}), 401
        flash("未找到匹配结果，请先进行转速匹配！")
        return redirect(url_for("main.index"))

    return render_template(
        "match_result.html",
        plots=saved_results.get("plots"),
        stats_html=saved_results.get("stats_html"),
        stats_csv=os.path.basename(saved_results.get("stats_csv"))
        if saved_results.get("stats_csv")
        else None,
        has_p1=saved_results.get("has_p1", False),
        has_p2=saved_results.get("has_p2", False),
        has_st=saved_results.get("has_st", False),
        evaluation_report=saved_results.get("evaluation_report"),
        saved_results=saved_results,
        chart_type_config=CHART_TYPE_CONFIG,
        unmatched_p1=saved_results.get("unmatched_p1", []),
        unmatched_p2=saved_results.get("unmatched_p2", []),
    )


@main_bp.route("/frontend-analytics", methods=["POST"])
def frontend_analytics():
    """处理前端分析数据"""
    try:
        if len(request.data) > 100 * 1024:
            return jsonify({"success": False, "message": "请求数据过大"}), 413

        last_request = session.get("_analytics_last_request", 0)
        now = time.time()
        if now - last_request < 2:
            return jsonify({"success": False, "message": "请求过于频繁，请稍后再试"}), 429
        session["_analytics_last_request"] = now

        analytics_data = request.get_json()
        if analytics_data:
            session["frontend_analytics"] = analytics_data
            current_app.logger.info("前端分析数据已保存")
            return jsonify({"success": True, "message": "前端分析数据已保存"})
        else:
            return jsonify({"success": False, "message": "未接收到分析数据"})
    except (ValueError, TypeError, KeyError) as e:
        current_app.logger.warning("前端分析数据处理异常: %s", str(e))
        return jsonify({"success": False, "message": "处理分析数据失败"})
    except Exception as e:
        current_app.logger.error("前端分析数据处理失败: %s", str(e), exc_info=True)
        return jsonify({"success": False, "message": "处理分析数据失败"})


# ========== 项目管理 API ==========

@main_bp.route("/api/projects", methods=["GET"])
def api_list_projects():
    """列出所有项目"""
    try:
        from db_models import DB_CONNECTED, Project

        if not DB_CONNECTED or Project is None:
            return jsonify({"success": True, "projects": []})

        projects = Project.query.order_by(Project.updated_at.desc()).all()
        return jsonify({
            "success": True,
            "projects": [
                {"id": p.id, "name": p.name, "description": p.description or "",
                 "created_at": p.created_at.isoformat(), "updated_at": p.updated_at.isoformat()}
                for p in projects
            ],
        })
    except Exception as e:
        current_app.logger.error("api_list_projects error: %s", e, exc_info=True)
        return jsonify({"success": False, "message": "获取项目列表失败"}), 500


@main_bp.route("/api/projects", methods=["POST"])
def api_create_project():
    """创建新项目"""
    try:
        from db_models import DB_CONNECTED, Project

        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"success": False, "message": "项目名称不能为空"}), 400
        if len(name) > 200:
            return jsonify({"success": False, "message": "项目名称不能超过200个字符"}), 400

        if not DB_CONNECTED or Project is None:
            return jsonify({"success": False, "message": "数据库未连接，无法创建项目"}), 503

        existing = Project.query.filter_by(name=name).first()
        if existing:
            return jsonify({"success": True, "project": {
                "id": existing.id, "name": existing.name, "description": existing.description or "",
            }, "message": "项目已存在"})

        description = (data.get("description") or "").strip()[:500]
        project = Project(name=name, description=description)
        db.session.add(project)
        db.session.commit()

        return jsonify({
            "success": True,
            "project": {"id": project.id, "name": project.name, "description": project.description or ""},
        }), 201
    except Exception as e:
        current_app.logger.error("api_create_project error: %s", e, exc_info=True)
        db.session.rollback()
        return jsonify({"success": False, "message": "创建项目失败"}), 500
