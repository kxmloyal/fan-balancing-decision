#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图表生成（优化版）——主编排模块

已按职责拆分为 5 个子模块（防臃肿）：
  - app/services/chart_utils.py               通用工具（转速排序/图表配置/JSON截断）
  - app/services/chart_cache.py               缓存管理（内存 LRU + 数据库）
  - app/services/chart_plotly_renderer.py     Plotly HTML 渲染
  - app/services/chart_matplotlib_renderer.py Matplotlib PNG 渲染
  - app/services/chart_fallback.py            回退占位图像生成

本文件保留图表生成链路的核心编排与全部公开 API。
"""

import hashlib
import logging
import os
from datetime import datetime

import numpy as np
import pandas as pd

from app.services.chart_cache import (
    _chart_cache_metadata,
    _chart_data_cache,
    _clean_expired_cache,
    clean_expired_chart_cache,
    get_chart_cache,
    save_chart_cache,
)
from app.services.chart_fallback import _generate_fallback_image
from app.services.chart_matplotlib_renderer import _generate_matplotlib_png
from app.services.chart_plotly_renderer import _generate_plotly_html
from app.services.chart_utils import _truncate_large_json, get_speed_numeric
from app.utils.chart_resource_manager import chart_resource_manager
from chart_style_config import CHART_TYPE_CONFIG
from utils.model_utils import sanitize_model_name

logger = logging.getLogger(__name__)


def build_report_charts(
    parsed_data, output_prefix, output_folder, chart_types=None, fan_model=None
):
    """生成双面对比图表（对比图+P1单面带+P2单面带+ST面图）"""
    if chart_types is None:
        chart_types = ["box"]  # 默认只生成箱线图

    try:
        # 生成数据哈希值，用于图表ID生成
        data_hash = chart_resource_manager.generate_data_hash(parsed_data)

        # 准备绘图数据
        p1_data = []  # P1面单独图数据
        p2_data = []  # P2面单独图数据
        sum_data = []  # ST面图数据

        # 关键优化1：分离P1和P2的中位数计算，确保互不干扰
        p1_median_dict = {}  # 存储P1面各转速的中位数：{转速: 中位数}
        p2_median_dict = {}  # 存储P2面各转速的中位数：{转速: 中位数}

        for item in parsed_data:
            # 处理ParsedDataItem对象或字典
            if hasattr(item, "speed"):
                speed = str(item.speed)
                p1_samples = item.p1_samples
                p2_samples = item.p2_samples
                sum_samples = item.sum_samples
            else:
                speed = str(item["speed"])
                p1_samples = item["p1_samples"]
                p2_samples = item["p2_samples"]
                sum_samples = item["sum_samples"]

            # 单面带数据
            for val in p1_samples:
                p1_data.append({"转速": speed, "不平衡量": val})
            for val in p2_samples:
                p2_data.append({"转速": speed, "不平衡量": val})

            # ST面数据
            for val in sum_samples:
                sum_data.append({"转速": speed, "不平衡量ST面": val})

            # 关键优化2：单独计算P1面中位数（仅基于P1样本）
            # 计算P1面中位数，确保数据不为空
            filtered_p1 = [val for val in p1_samples if not pd.isna(val)]
            p1_median = pd.Series(filtered_p1).median() if filtered_p1 else None
            p1_median_dict[speed] = p1_median

            # 关键优化3：单独计算P2面中位数（仅基于P2样本）
            # 计算P2面中位数，确保数据不为空
            filtered_p2 = [val for val in p2_samples if not pd.isna(val)]
            p2_median = pd.Series(filtered_p2).median() if filtered_p2 else None
            p2_median_dict[speed] = p2_median

        # 关键优化4：按转速顺序排序（确保连线顺序正确）
        # 提取所有转速并按数字大小排序（兼容"3000rpm"、"4000"等格式）
        all_speeds = sorted(p1_median_dict.keys(), key=get_speed_numeric)

        # 提取排序后的中位数数据（确保P1和P2的转速顺序完全一致）
        p1_median_values = [p1_median_dict[speed] for speed in all_speeds]
        p2_median_values = [p2_median_dict[speed] for speed in all_speeds]

        plots = {}

        all_y_values = []
        for item in p1_data:
            if isinstance(item, dict) and "不平衡量" in item:
                all_y_values.append(item["不平衡量"])
        for item in p2_data:
            if isinstance(item, dict) and "不平衡量" in item:
                all_y_values.append(item["不平衡量"])
        for item in sum_data:
            if isinstance(item, dict) and "不平衡量ST面" in item:
                all_y_values.append(item["不平衡量ST面"])

        global_y_min = min(all_y_values) if all_y_values else None
        global_y_max = max(all_y_values) if all_y_values else None
        y_range = (
            (global_y_min, global_y_max)
            if global_y_min is not None and global_y_max is not None
            else None
        )
        if y_range:
            padding = (global_y_max - global_y_min) * 0.05 if global_y_max != global_y_min else 1.0
            y_range = (global_y_min - padding, global_y_max + padding)

        # 1. P1面图表
        if p1_data:
            # 生成P1面图表
            plots["p1"] = generate_generic_charts(
                data=p1_data,
                median_dict=p1_median_dict,
                surface_name="P1面",
                color="#1f77b4",
                output_prefix=output_prefix,
                output_folder=output_folder,
                chart_types=chart_types,
                is_st_surface=False,
                sorted_speeds=all_speeds,
                median_values=p1_median_values,
                data_hash=data_hash,
                surface_type="p1",
                y_range=y_range,
                fan_model=fan_model,
            )

        # 2. P2面图表
        if p2_data:
            # 生成P2面图表
            plots["p2"] = generate_generic_charts(
                data=p2_data,
                median_dict=p2_median_dict,
                surface_name="P2面",
                color="#ff7f0e",
                output_prefix=output_prefix,
                output_folder=output_folder,
                chart_types=chart_types,
                is_st_surface=False,
                sorted_speeds=all_speeds,
                median_values=p2_median_values,
                data_hash=data_hash,
                surface_type="p2",
                y_range=y_range,
                fan_model=fan_model,
            )

        # 3. ST面图表
        if sum_data:
            st_median_dict = {}
            for item in parsed_data:
                # 处理ParsedDataItem对象或字典
                if hasattr(item, "speed"):
                    speed = str(item.speed)
                    st_samples = item.sum_samples
                else:
                    speed = str(item["speed"])
                    st_samples = item["sum_samples"]
                # 计算ST面中位数，确保数据不为空
                filtered_st = [val for val in st_samples if not pd.isna(val)]
                st_median_dict[speed] = pd.Series(filtered_st).median() if filtered_st else None

            # 生成ST面图表
            plots["sum"] = generate_generic_charts(
                data=sum_data,
                median_dict=st_median_dict,
                surface_name="ST面",
                color="#2ca02c",
                output_prefix=output_prefix,
                output_folder=output_folder,
                chart_types=chart_types,
                is_st_surface=True,
                data_hash=data_hash,
                surface_type="st",
                y_range=y_range,
                fan_model=fan_model,
            )

        return plots
    except (ValueError, IOError, TypeError) as e:
        raise Exception(f"图表生成失败：{str(e)}")


def generate_single_surface_plots(
    parsed_data, output_prefix, surface_type, output_folder, chart_types=None, fan_model=None
):
    """生成单个面（P1/P2/ST）的图表（添加中文字体配置）"""
    if chart_types is None:
        chart_types = ["box"]  # 默认只生成箱线图

    try:
        # 生成数据哈希值，用于图表ID生成
        data_hash = chart_resource_manager.generate_data_hash(parsed_data)

        # 准备图表数据
        plot_data = []
        median_dict = {}  # 存储当前面各转速的中位数

        for item in parsed_data:
            # 处理ParsedDataItem对象或字典
            if hasattr(item, "speed"):
                speed = str(item.speed)
                if surface_type == "p1":
                    samples = item.p1_samples
                elif surface_type == "p2":
                    samples = item.p2_samples
                else:
                    samples = item.sum_samples
            else:
                speed = str(item["speed"])
                samples = (
                    item["p1_samples"]
                    if surface_type == "p1"
                    else (item["p2_samples"] if surface_type == "p2" else item["sum_samples"])
                )
            for val in samples:
                plot_data.append({"转速": speed, "不平衡量": val})
            # 单独计算当前面的中位数
            # 计算中位数，确保数据不为空
            filtered_samples = [val for val in samples if not pd.isna(val)]
            median_dict[speed] = pd.Series(filtered_samples).median() if filtered_samples else None

        # 按转速排序
        sorted_speeds = sorted(median_dict.keys(), key=get_speed_numeric)
        median_values = [median_dict[speed] for speed in sorted_speeds]

        # 生成图表
        color_map = {"p1": "#1f77b4", "p2": "#ff7f0e", "st": "#2ca02c"}
        title_map = {"p1": "P1面", "p2": "P2面", "st": "ST面"}
        color = color_map.get(surface_type, "#1f77b4")
        title = f"{title_map.get(surface_type, surface_type.upper())}面"

        # 生成图表，根据surface_type确定是否为ST面
        is_st = surface_type == "st"
        charts = generate_generic_charts(
            data=plot_data,
            median_dict=median_dict,
            surface_name=title,
            color=color,
            output_prefix=output_prefix,
            output_folder=output_folder,
            chart_types=chart_types,
            is_st_surface=is_st,
            sorted_speeds=sorted_speeds,
            median_values=median_values,
            data_hash=data_hash,
            surface_type=surface_type,
            fan_model=fan_model,
        )

        # Return charts with appropriate keys based on surface type
        if surface_type == "p1":
            return {"p1": charts}
        elif surface_type == "p2":
            return {"p2": charts}
        elif surface_type == "st":
            return {"sum": charts}
        else:
            # 确保单面数据也能被正确处理
            return {"single": charts}
    except (ValueError, IOError, TypeError) as e:  # 捕获特定的异常类型
        raise Exception(f"单面带图表生成失败：{str(e)}")


def fetch_chart_data(data, chart_type):
    """
    生成图表兼容的数据格式（支持Plotly）

    参数:
        data: 原始数据，格式为列表，每个元素为字典，包含"转速"和值字段
        chart_type: 图表类型

    返回:
        适合Plotly使用的数据格式，Python对象格式
    """
    # 清理过期缓存
    _clean_expired_cache()

    # 生成缓存键（使用参数摘要哈希避免大对象序列化）
    param_hash = hashlib.md5(str(data).encode("utf-8")).hexdigest()
    cache_key = f"{chart_type}_{param_hash}"

    # 检查缓存
    if cache_key in _chart_data_cache:
        # 更新访问时间
        _chart_cache_metadata[cache_key]["timestamp"] = datetime.now()
        return _chart_data_cache[cache_key]

    if not data or not isinstance(data, list):
        # 返回默认数据，避免渲染错误
        default_data = {
            "box": [{"name": "默认数据", "data": [0, 0, 0, 0, 0]}],
            "trend": [{"name": "默认数据", "value": 0}],
            "scatter": [],
            "heatmap": [],
            "histogram": [],
            "bubble": [{"name": "默认数据", "value": ["默认", 0, 0]}],
            "violin": [{"name": "默认数据", "data": [0]}],
            "3d": [],
            "parallel": [],
        }.get(chart_type, [])
        _chart_data_cache[cache_key] = default_data
        _chart_cache_metadata[cache_key] = {
            "timestamp": datetime.now(),
            "size": len(str(default_data)),
        }
        return default_data

    # 确保数据格式正确
    try:
        # 验证数据中的每个元素是否是字典
        valid_data = []
        for item in data:
            if isinstance(item, dict):
                valid_data.append(item)
        if not valid_data:
            # 返回默认数据，避免渲染错误
            default_data = {
                "box": [{"name": "默认数据", "data": [0, 0, 0, 0, 0]}],
                "trend": [{"name": "默认数据", "value": 0}],
                "scatter": [],
                "heatmap": [],
                "histogram": [],
                "bubble": [{"name": "默认数据", "value": ["默认", 0, 0]}],
                "violin": [{"name": "默认数据", "data": [0]}],
                "3d": [],
                "parallel": [],
            }.get(chart_type, [])
            _chart_data_cache[cache_key] = default_data
            _chart_cache_metadata[cache_key] = {
                "timestamp": datetime.now(),
                "size": len(str(default_data)),
            }
            return default_data
        data = valid_data
    except (ValueError, IOError, TypeError):  # 捕获特定的异常类型
        # 返回默认数据，避免渲染错误
        default_data = {
            "box": [{"name": "默认数据", "data": [0, 0, 0, 0, 0]}],
            "trend": [{"name": "默认数据", "value": 0}],
            "scatter": [],
            "heatmap": [],
            "histogram": [],
            "bubble": [{"name": "默认数据", "value": ["默认", 0, 0]}],
            "violin": [{"name": "默认数据", "data": [0]}],
            "3d": [],
            "parallel": [],
        }.get(chart_type, [])
        _chart_data_cache[cache_key] = default_data
        _chart_cache_metadata[cache_key] = {
            "timestamp": datetime.now(),
            "size": len(str(default_data)),
        }
        return default_data

    # 自动检测值字段
    value_field = "不平衡量"
    if data and isinstance(data[0], dict):
        if "不平衡量ST面" in data[0]:
            value_field = "不平衡量ST面"
        elif "不平衡量" not in data[0]:
            # 尝试找到包含"不平衡量"的字段
            for key in data[0].keys():
                if "不平衡量" in key:
                    value_field = key
                    break

    # 按转速分组
    grouped_data = {}
    for item in data:
        speed = str(item.get("转速", "未知"))
        value = item.get(value_field, 0)
        if speed not in grouped_data:
            grouped_data[speed] = []
        grouped_data[speed].append(value)

    # 根据图表类型生成不同的数据格式
    result = []
    if chart_type == "box":
        # 箱线图数据格式
        box_data = []
        for speed, values in grouped_data.items():
            # 过滤掉None和NaN值
            values = [v for v in values if v is not None and not pd.isna(v)]
            values.sort()
            n = len(values)
            if n == 0:
                continue

            # 计算四分位数
            q1 = np.percentile(values, 25)
            q2 = np.percentile(values, 50)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            min_val = max(values[0], q1 - 1.5 * iqr)
            max_val = min(values[-1], q3 + 1.5 * iqr)

            box_data.append(
                {
                    "name": speed,
                    "data": [float(min_val), float(q1), float(q2), float(q3), float(max_val)],
                }
            )
        # 确保返回有效的箱线图数据结构
        if not box_data:
            box_data = [{"name": "默认数据", "data": [0, 0, 0, 0, 0]}]
        result = box_data

    elif chart_type == "trend":
        # 趋势图数据格式
        trend_data = []
        for speed, values in grouped_data.items():
            median = np.percentile(values, 50)
            trend_data.append({"name": speed, "value": float(median)})
        result = trend_data

    elif chart_type == "scatter":
        # 散点图数据格式
        scatter_data = []
        for speed, values in grouped_data.items():
            for value in values:
                scatter_data.append([speed, float(value)])
        result = scatter_data

    elif chart_type == "heatmap":
        # 热力图数据格式
        heatmap_data = []
        for speed, values in grouped_data.items():
            for i, value in enumerate(values):
                heatmap_data.append([speed, i, float(value)])
        result = heatmap_data

    elif chart_type == "histogram":
        # 直方图数据格式
        all_values = []
        for values in grouped_data.values():
            all_values.extend(values)

        if not all_values:
            result = []
        else:
            # 计算直方图bins
            min_val = min(all_values)
            max_val = max(all_values)
            bin_count = 30
            bin_width = (max_val - min_val) / bin_count

            histogram_data = [0] * bin_count
            for val in all_values:
                if not np.isnan(val):
                    bin_idx = min(int((val - min_val) / bin_width), bin_count - 1)
                    histogram_data[bin_idx] += 1

            result = histogram_data

    elif chart_type == "bubble":
        # 气泡图数据格式
        bubble_data = []
        for speed, values in grouped_data.items():
            median = np.percentile(values, 50)
            bubble_data.append({"name": speed, "value": [speed, float(median), len(values)]})
        result = bubble_data

    elif chart_type == "violin":
        # 小提琴图数据格式
        violin_data = []
        for speed, values in grouped_data.items():
            violin_data.append({"name": speed, "data": [float(v) for v in values]})
        result = violin_data

    elif chart_type == "3d":
        # 3D散点图数据格式
        scatter3d_data = []
        for speed, values in grouped_data.items():
            for i, value in enumerate(values):
                scatter3d_data.append([speed, i, float(value)])
        result = scatter3d_data

    elif chart_type == "parallel":
        # 平行坐标图数据格式
        parallel_data = []
        for speed, values in grouped_data.items():
            if values:
                median = np.percentile(values, 50)
                mean = np.mean(values)
                parallel_data.append([speed, float(median), float(mean)])
        result = parallel_data

    else:
        # 默认返回原始数据
        result = data

    # 缓存结果
    _chart_data_cache[cache_key] = result
    _chart_cache_metadata[cache_key] = {"timestamp": datetime.now(), "size": len(str(result))}
    return result


def _build_chart_result(
    chart_type,
    chart_data_json_str,
    surface_name,
    color,
    output_prefix,
    output_folder,
    is_st_surface,
    sorted_speeds,
    median_values,
    chart_id,
    png_path,
    html_path,
):
    """构建图表结果字典

    Args:
        chart_type: 图表类型字符串
        chart_data_json_str: 图表数据的JSON字符串
        surface_name: 面名称
        color: 图表颜色
        output_prefix: 输出文件前缀
        output_folder: 输出文件夹
        is_st_surface: 是否为ST面
        sorted_speeds: 排序后的转速列表
        median_values: 中位数值列表
        chart_id: 图表唯一标识符
        png_path: 图像文件路径
        html_path: HTML文件路径

    Returns:
        dict: 包含 png, html, chart_data, chart_properties 的结果字典
    """
    return {
        "png": os.path.basename(png_path),
        "html": os.path.basename(html_path),
        "chart_data": chart_data_json_str,
        "chart_properties": {
            "surface_name": surface_name,
            "color": color,
            "chart_type": chart_type,
            "output_prefix": output_prefix,
            "output_folder": output_folder,
            "is_st_surface": is_st_surface,
            "sorted_speeds": sorted_speeds,
            "median_values": median_values,
            "chart_id": chart_id,
        },
    }


def generate_generic_charts(
    data,
    median_dict,
    surface_name,
    color,
    output_prefix,
    output_folder,
    chart_types,
    is_st_surface=False,
    sorted_speeds=None,
    median_values=None,
    data_hash=None,
    surface_type=None,
    y_range=None,
    fan_model=None,
):
    """生成通用图表（支持普通面和ST面）"""
    charts = {}

    model_output_dir = output_folder
    if fan_model:
        model_output_dir = os.path.join(output_folder, sanitize_model_name(fan_model))
        os.makedirs(model_output_dir, exist_ok=True)

    chart_data = {}
    for chart_type in chart_types:
        raw_data = fetch_chart_data(data, chart_type)
        chart_data[chart_type] = _truncate_large_json(raw_data, chart_type)

    for chart_type in chart_types:
        chart_id = None
        if data_hash and surface_type:
            chart_id = chart_resource_manager.generate_chart_id(
                data_hash, surface_type, chart_type, scope=model_output_dir
            )
        else:
            chart_zh_name = CHART_TYPE_CONFIG.get(chart_type, {}).get("name", chart_type)
            chart_filename = f"{output_prefix}_{surface_name}_{chart_zh_name}"

        if chart_id and chart_resource_manager.is_chart_generated(chart_id):
            resource_info = chart_resource_manager.get_chart_resource(chart_id)
            if resource_info:
                png_path = resource_info.get("png_path")
                html_path = resource_info.get("html_path")
                if png_path and html_path:
                    charts[chart_type] = _build_chart_result(
                        chart_type,
                        chart_data[chart_type],
                        surface_name,
                        color,
                        output_prefix,
                        model_output_dir,
                        is_st_surface,
                        sorted_speeds,
                        median_values,
                        chart_id,
                        png_path,
                        html_path,
                    )
                    continue

        if chart_id:
            chart_resource_manager.mark_chart_generating(
                chart_id, chart_type, surface_name, data_hash
            )

        if chart_id:
            chart_filename = chart_id
        else:
            chart_zh_name = CHART_TYPE_CONFIG.get(chart_type, {}).get("name", chart_type)
            chart_filename = f"{output_prefix}_{surface_name}_{chart_zh_name}"

        png_path = os.path.join(model_output_dir, f"{chart_filename}.png")
        html_path = os.path.join(model_output_dir, f"{chart_filename}.html")

        html_content = _generate_plotly_html(
            chart_data[chart_type], chart_type, surface_name, color, y_range
        )
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        if not _generate_matplotlib_png(
            chart_data[chart_type], chart_type, surface_name, png_path, y_range
        ):
            png_path = _generate_fallback_image(surface_name, chart_type, png_path)

        if chart_id:
            chart_resource_manager.mark_chart_generated(chart_id, png_path)

        charts[chart_type] = _build_chart_result(
            chart_type,
            chart_data[chart_type],
            surface_name,
            color,
            output_prefix,
            model_output_dir,
            is_st_surface,
            sorted_speeds,
            median_values,
            chart_id,
            png_path,
            html_path,
        )

    return charts


# ========== 向后兼容别名 ==========
# 保留旧函数名作为别名，确保外部引用不中断
generate_plots = build_report_charts
generate_chart_data = fetch_chart_data
