# -*- coding: utf-8 -*-
"""
主蓝图：包含首页和文件上传功能
"""

import os
from statistics import (calculate_optimal_speed_evaluation,
                        generate_single_surface_stats, generate_stats,
                        generate_stats_data)

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.utils import secure_filename

from chart_generation import (CHART_TYPE_CONFIG, generate_plots,
                              generate_single_surface_plots)
from data_processing import allowed_file, parse_single_surface_file
from utils.data_validator import generate_data_warning, validate_and_align_data
from utils.file_manager import file_manager
from utils.error_handler import error_handler

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET", "POST"])
def index():
    """首页：文件上传+结果展示"""
    from flask import current_app

    if request.method == "POST":
        current_app.logger.info("=== 开始处理表单提交 ===")
        current_app.logger.info(f"请求方法: {request.method}")
        current_app.logger.info(f"表单字段: {list(request.form.keys())}")
        current_app.logger.info(f"文件字段: {list(request.files.keys())}")
        # 检查是否是图表类型更新请求
        p1_file = request.files.get("p1_file")
        p2_file = request.files.get("p2_file")
        st_file = request.files.get("st_file")

        # 更准确地检测图表更新请求，确保文件对象存在且文件名不为空
        is_chart_update = (
            "chart_types" in request.form or "chart_update" in request.form
        ) and not (
            (p1_file and p1_file.filename != "" and p1_file.filename is not None)
            or (p2_file and p2_file.filename != "" and p2_file.filename is not None)
            or (st_file and st_file.filename != "" and st_file.filename is not None)
        )

        # 检查是否是组合图表请求
        is_combined_chart = "combined_chart" in request.form

        if is_combined_chart:
            # 组合图表请求
            saved_results = session.get("saved_results")
            if not saved_results:
                flash("会话已过期，请重新上传数据文件！")
                return redirect(request.url)

            # 获取表单数据
            chart_types = request.form.get("chart_types", "box").split(",")
            chart_layout = request.form.get("chartLayout", "stacked")

            # 更新Session中的图表设置
            saved_results["chart_types"] = chart_types
            saved_results["chart_layout"] = chart_layout

            # 根据数据类型重新生成图表
            parsed_data = saved_results.get("parsed_data")
            output_prefix = saved_results.get("output_prefix")
            single_surface = saved_results.get("single_surface")

            try:
                if single_surface:
                    # 单一表面的图表生成
                    plots = generate_single_surface_plots(
                        parsed_data,
                        output_prefix,
                        single_surface,
                        current_app.config["OUTPUT_FOLDER"],
                        chart_types,
                    )
                else:
                    # 多表面的图表生成
                    plots = generate_plots(
                        parsed_data,
                        output_prefix,
                        current_app.config["OUTPUT_FOLDER"],
                        chart_types,
                    )
            except Exception as e:
                user_id = session.get("user_id", "anonymous")
                ip_address = request.remote_addr
                error_message = error_handler.handle_exception(e, "main_bp", user_id, ip_address)
                flash(f"组合图表生成失败：{error_message}")
                return redirect(request.url)

            # 更新Session中的图表数据
            saved_results["plots"] = plots
            session["saved_results"] = saved_results

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
            )

        elif is_chart_update:
            # 图表类型更新请求，从session获取数据
            saved_results = session.get("saved_results")
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
                    # 单一面情况
                    plots = generate_single_surface_plots(
                        saved_results["parsed_data"],
                        saved_results["output_prefix"],
                        saved_results["single_surface"],
                        current_app.config["OUTPUT_FOLDER"],
                        chart_types,
                    )
                else:
                    # 双面或多面情况
                    plots = generate_plots(
                        saved_results["parsed_data"],
                        saved_results["output_prefix"],
                        current_app.config["OUTPUT_FOLDER"],
                        chart_types,
                    )
            except Exception as e:
                user_id = session.get("user_id", "anonymous")
                ip_address = request.remote_addr
                error_message = error_handler.handle_exception(e, "main_bp", user_id, ip_address)
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify(
                        {"success": False, "message": f"图表生成失败：{error_message}"}
                    )
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

            session["saved_results"] = saved_results

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

        # 文件上传处理流程
        surface_data = {}
        upload_files = []

        # 获取扇叶型号
        fan_model = request.form.get("fan_model", "").strip()
        if not fan_model:
            flash("请输入扇叶型号！")
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

        # 解析P1面文件（如果上传）
        if p1_file and p1_file.filename != "":
            if allowed_file(p1_file.filename, current_app.config["ALLOWED_EXTENSIONS"]):
                # 检查文件大小
                if not file_manager.check_file_size(p1_file.content_length):
                    flash(f"P1面文件大小超过限制！当前大小：{p1_file.content_length / (1024 * 1024):.2f}MB，限制：100MB")
                    return redirect(request.url)
                
                p1_filename = secure_filename(f"p1_{p1_file.filename}")
                p1_path = os.path.join(current_app.config["UPLOAD_FOLDER"], p1_filename)
                p1_file.save(p1_path)
                upload_files.append(p1_filename)
                try:
                    surface_data["p1"] = parse_single_surface_file(p1_path)
                except Exception as e:
                    user_id = session.get("user_id", "anonymous")
                    ip_address = request.remote_addr
                    error_message = error_handler.handle_exception(e, "main_bp", user_id, ip_address)
                    flash(f"P1面文件处理失败：{error_message}")
                    return redirect(request.url)
            else:
                flash(f"P1面文件格式不支持：{p1_file.filename}，仅支持CSV/XLSX/XLS")
                return redirect(request.url)

        # 解析P2面文件（如果上传）
        if p2_file and p2_file.filename != "":
            if allowed_file(p2_file.filename, current_app.config["ALLOWED_EXTENSIONS"]):
                # 检查文件大小
                if not file_manager.check_file_size(p2_file.content_length):
                    flash(f"P2面文件大小超过限制！当前大小：{p2_file.content_length / (1024 * 1024):.2f}MB，限制：100MB")
                    return redirect(request.url)
                
                p2_filename = secure_filename(f"p2_{p2_file.filename}")
                p2_path = os.path.join(current_app.config["UPLOAD_FOLDER"], p2_filename)
                p2_file.save(p2_path)
                upload_files.append(p2_filename)
                try:
                    surface_data["p2"] = parse_single_surface_file(p2_path)
                except Exception as e:
                    user_id = session.get("user_id", "anonymous")
                    ip_address = request.remote_addr
                    error_message = error_handler.handle_exception(e, "main_bp", user_id, ip_address)
                    flash(f"P2面文件处理失败：{error_message}")
                    return redirect(request.url)
            else:
                flash(f"P2面文件格式不支持：{p2_file.filename}，仅支持CSV/XLSX/XLS")
                return redirect(request.url)

        # 解析ST面文件（如果上传）
        if st_file and st_file.filename != "":
            if allowed_file(st_file.filename, current_app.config["ALLOWED_EXTENSIONS"]):
                # 检查文件大小
                if not file_manager.check_file_size(st_file.content_length):
                    flash(f"ST面文件大小超过限制！当前大小：{st_file.content_length / (1024 * 1024):.2f}MB，限制：100MB")
                    return redirect(request.url)
                
                st_filename = secure_filename(f"st_{st_file.filename}")
                st_path = os.path.join(current_app.config["UPLOAD_FOLDER"], st_filename)
                st_file.save(st_path)
                upload_files.append(st_filename)
                try:
                    surface_data["st"] = parse_single_surface_file(st_path)
                except Exception as e:
                    user_id = session.get("user_id", "anonymous")
                    ip_address = request.remote_addr
                    error_message = error_handler.handle_exception(e, "main_bp", user_id, ip_address)
                    flash(f"ST面文件处理失败：{error_message}")
                    return redirect(request.url)
            else:
                flash(f"ST面文件格式不支持：{st_file.filename}，仅支持CSV/XLSX/XLS")
                return redirect(request.url)

        # 必须至少上传一个文件
        if not surface_data:
            flash("请至少上传一个面的数据文件！")
            return redirect(request.url)

        # 生成输出前缀
        output_prefix = "_".join([os.path.splitext(f)[0] for f in upload_files])
        plots = {}
        stats_html = None
        stats_csv = None

        current_app.logger.info(f"处理后的surface_data: {list(surface_data.keys())}")

        # 场景1：同时上传P1和P2面（可能还有ST面）
        if "p1" in surface_data and "p2" in surface_data:
            current_app.logger.info("=== 进入双面对比场景 ===")
            p1_speeds = sorted(surface_data["p1"].keys())
            p2_speeds = sorted(surface_data["p2"].keys())
            st_data = surface_data.get("st", {})
            current_app.logger.info(f"P1转速: {p1_speeds}")
            current_app.logger.info(f"P2转速: {p2_speeds}")
            current_app.logger.info(
                f"ST数据: {list(st_data.keys()) if st_data else '无'}"
            )

            # 存储数据到Session，供匹配页面使用
            session["p1_data"] = surface_data["p1"]
            session["p2_data"] = surface_data["p2"]
            session["st_data"] = st_data
            session["output_prefix"] = output_prefix

            # 转速完全一致：直接生成结果
            if set(p1_speeds) == set(p2_speeds):
                common_speeds = p1_speeds
                parsed_data = []
                # 对应的数据验证对齐
                data_warnings = []
                for speed in common_speeds:
                    # 数据验证对齐
                    st_samples_for_speed = (
                        st_data.get(speed) if speed in st_data else None
                    )
                    p1_aligned, p2_aligned, st_samples, data_info = (
                        validate_and_align_data(
                            surface_data["p1"][speed],
                            surface_data["p2"][speed],
                            st_samples_for_speed,
                        )
                    )

                    # 数据警告（存在即添加）
                    warning_msg = generate_data_warning(data_info, speed)
                    if warning_msg:
                        data_warnings.append(warning_msg)

                    parsed_data.append(
                        {
                            "speed": speed,
                            "p1_samples": p1_aligned,
                            "p2_samples": p2_aligned,
                            "sum_samples": st_samples,
                        }
                    )

                # 数据警告如果有的话，添加到flash消息
                if data_warnings:
                    flash("数据警告：" + "; ".join(data_warnings))
                plots = generate_plots(
                    parsed_data, output_prefix, current_app.config["OUTPUT_FOLDER"]
                )
                try:
                    stats_html, stats_csv = generate_stats(
                        parsed_data, output_prefix, current_app.config["OUTPUT_FOLDER"]
                    )
                    # 计算最优转速评估
                    evaluation_report = calculate_optimal_speed_evaluation(
                        generate_stats_data(parsed_data)
                    )
                except Exception as e:
                    user_id = session.get("user_id", "anonymous")
                    ip_address = request.remote_addr
                    error_message = error_handler.handle_exception(e, "main_bp", user_id, ip_address)
                    flash(f"统计报告生成失败：{error_message}")
                    return redirect(request.url)

                # 页面变量
                has_p1 = bool(surface_data.get("p1"))
                has_p2 = bool(surface_data.get("p2"))
                has_st = bool(surface_data.get("st"))

                # 保存结果到session，用于图表更新
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
                    "chart_types": ["box"],  # 默认图表类型
                    "chart_layout": "stacked",  # 默认图表布局
                    "fan_model": fan_model,
                }
                session["saved_results"] = saved_results

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
                )
            # 转速不一致：跳转到匹配页面
            else:
                # 将数据保存到session，供匹配页面使用
                session["p1_data"] = surface_data["p1"]
                session["p2_data"] = surface_data["p2"]
                session["st_data"] = st_data
                session["output_prefix"] = output_prefix
                return redirect(url_for("main.match_speeds"))

        # 场景2：仅上传单一文件（P1、P2或ST）
        else:
            # 确定上传的是哪个面
            surface_type = list(surface_data.keys())[0]  # 只有一个键
            speeds = sorted(surface_data[surface_type].keys())

            # 构造数据结构
            parsed_data = []
            for speed in speeds:
                data_item = {
                    "speed": speed,
                    "p1_samples": (
                        surface_data[surface_type][speed]
                        if surface_type == "p1"
                        else []
                    ),
                    "p2_samples": (
                        surface_data[surface_type][speed]
                        if surface_type == "p2"
                        else []
                    ),
                    "sum_samples": (
                        surface_data[surface_type][speed]
                        if surface_type == "st"
                        else []
                    ),
                }
                parsed_data.append(data_item)

            # 生成图表和统计信息
            plots = generate_single_surface_plots(
                parsed_data,
                output_prefix,
                surface_type,
                current_app.config["OUTPUT_FOLDER"],
            )
            try:
                stats_html, stats_csv = generate_single_surface_stats(
                    parsed_data,
                    output_prefix,
                    surface_type,
                    current_app.config["OUTPUT_FOLDER"],
                )
                # 计算最优转速评估
                evaluation_report = calculate_optimal_speed_evaluation(
                    generate_stats_data(parsed_data)
                )
            except Exception as e:
                user_id = session.get("user_id", "anonymous")
                ip_address = request.remote_addr
                error_message = error_handler.handle_exception(e, "main_bp", user_id, ip_address)
                flash(f"统计报告生成失败：{error_message}")
                return redirect(request.url)

            # 页面变量
            has_p1 = surface_type == "p1"
            has_p2 = surface_type == "p2"
            has_st = surface_type == "st"

            # 保存结果到session，用于图表更新
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
                "chart_types": ["box"],  # 默认图表类型
                "chart_layout": "stacked",  # 默认图表布局
                "fan_model": fan_model,
            }
            session["saved_results"] = saved_results

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

    # GET请求：空页面渲染
    default_evaluation_report = {
        "best_speeds": [],
        "speed_detailed_scores": {},
        "detailed_scores": {},  # 保持与之前的兼容性
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
    )


@main_bp.route("/match_speeds", methods=["GET", "POST"])
def match_speeds():
    """转速匹配页面"""
    from flask import current_app
    
    # 从session获取数据
    p1_data = session.get("p1_data")
    p2_data = session.get("p2_data")
    st_data = session.get("st_data", {})
    output_prefix = session.get("output_prefix", "output")
    
    # 检查数据是否存在
    if not p1_data or not p2_data:
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
            
            # 处理匹配的转速
            for p1_speed in p1_speeds:
                if p1_speed in matches:
                    p2_speed = matches[p1_speed]
                    p2_samples = p2_data.get(p2_speed, [])
                    st_samples_for_speed = st_data.get(p1_speed, [])
                    
                    # 验证和对齐数据
                    p1_aligned, p2_aligned, st_samples, data_info = validate_and_align_data(
                        p1_data[p1_speed],
                        p2_samples,
                        st_samples_for_speed
                    )
                    
                    parsed_data.append({
                        "speed": p1_speed,
                        "p1_samples": p1_aligned,
                        "p2_samples": p2_aligned,
                        "sum_samples": st_samples
                    })
                    
                    # 从unmatched_p2中移除已匹配的P2转速
                    if p2_speed in unmatched_p2:
                        unmatched_p2.remove(p2_speed)
                else:
                    # 未匹配的P1转速
                    unmatched_p1.append(p1_speed)
            
            # 生成图表
            plots = generate_plots(
                parsed_data, output_prefix, current_app.config["OUTPUT_FOLDER"]
            )
            
            # 生成统计报告
            stats_html, stats_csv = generate_stats(
                parsed_data, output_prefix, current_app.config["OUTPUT_FOLDER"]
            )
            
            # 计算最优转速评估
            evaluation_report = calculate_optimal_speed_evaluation(
                generate_stats_data(parsed_data)
            )
            
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
                "unmatched_p2": list(unmatched_p2)
            }
            session["saved_results"] = saved_results
            
            # 跳转到匹配结果页面
            return redirect(url_for("main.match_result"))
            
        except Exception as e:
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
        
        default_matches.append({
            "p1_speed": p1_speed,
            "matched_p2": matched_p2
        })
    
    return render_template(
        "match_speeds.html",
        default_matches=default_matches,
        p2_speeds=p2_speeds
    )


@main_bp.route("/reset", methods=["POST"])
def reset():
    """重置所有数据和文件"""
    from flask import current_app
    
    # 实现重置逻辑
    # 这里只是一个占位符，需要根据实际业务逻辑实现
    session.clear()
    flash("已成功重置所有数据和文件")
    return redirect(url_for("main.index"))


@main_bp.route("/dashboard")
def dashboard():
    """数据仪表盘页面"""
    from flask import current_app
    import os
    import glob
    from datetime import datetime, timedelta
    
    # 模拟数据 - 实际项目中应从数据库获取
    total_evaluations = 128
    optimal_speed = "3000rpm"
    file_count = len(glob.glob(os.path.join(current_app.config["UPLOAD_FOLDER"], "*")))
    
    # 计算存储空间使用
    def get_folder_size(folder):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
    
    upload_folder_size = get_folder_size(current_app.config["UPLOAD_FOLDER"])
    output_folder_size = get_folder_size(current_app.config["OUTPUT_FOLDER"])
    storage_usage = round((upload_folder_size + output_folder_size) / (1024 * 1024), 2)
    storage_limit = 10240  # 10GB
    storage_percentage = min(round((storage_usage / storage_limit) * 100, 2), 100)
    
    # 生成评估趋势数据
    evaluation_dates = []
    evaluation_counts = []
    today = datetime.now()
    for i in range(7, 0, -1):
        date = today - timedelta(days=i)
        evaluation_dates.append(date.strftime("%Y-%m-%d"))
        # 模拟数据
        evaluation_counts.append(10 + i * 2)
    
    # 生成转速分布数据
    speed_labels = ["3000rpm", "4000rpm", "5000rpm", "6000rpm", "7000rpm"]
    speed_counts = [45, 30, 25, 15, 13]
    
    # 生成最近评估记录
    recent_records = [
        {
            "id": 1,
            "timestamp": "2026-02-14 10:30:00",
            "fan_model": "ZM-100",
            "evaluated_speeds": "3000-7000rpm",
            "optimal_speed": "3000rpm"
        },
        {
            "id": 2,
            "timestamp": "2026-02-14 09:15:00",
            "fan_model": "ZM-200",
            "evaluated_speeds": "3000-6000rpm",
            "optimal_speed": "4000rpm"
        },
        {
            "id": 3,
            "timestamp": "2026-02-13 16:45:00",
            "fan_model": "ZM-100",
            "evaluated_speeds": "3000-5000rpm",
            "optimal_speed": "3000rpm"
        }
    ]
    
    # 系统状态数据
    db_response_time = 12
    system_load = 45
    
    return render_template(
        "dashboard.html",
        total_evaluations=total_evaluations,
        optimal_speed=optimal_speed,
        file_count=file_count,
        storage_usage=storage_usage,
        storage_limit=storage_limit,
        storage_percentage=storage_percentage,
        evaluation_dates=evaluation_dates,
        evaluation_counts=evaluation_counts,
        speed_labels=speed_labels,
        speed_counts=speed_counts,
        recent_records=recent_records,
        db_response_time=db_response_time,
        system_load=system_load
    )


@main_bp.route("/match_result")
def match_result():
    """匹配结果页面"""
    # 从session获取匹配结果
    saved_results = session.get("saved_results")
    if not saved_results:
        flash("未找到匹配结果，请先进行转速匹配！")
        return redirect(url_for("main.index"))
    
    return render_template(
        "match_result.html",
        plots=saved_results.get("plots"),
        stats_html=saved_results.get("stats_html"),
        stats_csv=os.path.basename(saved_results.get("stats_csv")) if saved_results.get("stats_csv") else None,
        has_p1=saved_results.get("has_p1", False),
        has_p2=saved_results.get("has_p2", False),
        has_st=saved_results.get("has_st", False),
        evaluation_report=saved_results.get("evaluation_report"),
        saved_results=saved_results,
        chart_type_config=CHART_TYPE_CONFIG,
        unmatched_p1=saved_results.get("unmatched_p1", []),
        unmatched_p2=saved_results.get("unmatched_p2", [])
    )
