#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图表生成通用工具（chart_generation_optimized 拆分模块）

存放图表生成链路中的纯工具函数，无内部业务依赖。
"""

import json

from chart_style_config import CHART_TYPE_CONFIG


def get_speed_numeric(speed_str):
    """提取转速字符串中的数字部分，返回数值，处理无数字的情况"""
    numeric_part = "".join(filter(str.isdigit, str(speed_str)))
    # 如果没有数字，返回0或按字符串排序
    return float(numeric_part) if numeric_part else float("-inf")


def _prepare_chart_config(chart_type, surface_name, color):
    """准备图表配置信息

    Args:
        chart_type: 图表类型字符串
        surface_name: 面名称
        color: 图表颜色

    Returns:
        dict: 包含 display_name, title, color, chart_type 的配置字典
    """
    display_name = CHART_TYPE_CONFIG.get(chart_type, {}).get("name", chart_type)
    return {
        "display_name": display_name,
        "title": f"{surface_name} {display_name}",
        "color": color,
        "chart_type": chart_type,
    }


def _truncate_large_json(raw_data, chart_type):
    """截断过大的JSON数据，根据图表类型采用不同截断策略

    Args:
        raw_data: 原始Python数据对象（列表）
        chart_type: 图表类型字符串

    Returns:
        str: JSON字符串，可能已经截断
    """
    json_str = json.dumps(raw_data)
    if len(json_str) > 50000:
        simplified_data = []
        if chart_type == "box":
            simplified_data = raw_data
        elif chart_type == "scatter" or chart_type == "3d" or chart_type == "heatmap":
            simplified_data = raw_data[:100]
        elif chart_type == "trend":
            simplified_data = raw_data
        elif chart_type == "histogram":
            simplified_data = raw_data
        elif chart_type == "bubble":
            simplified_data = raw_data[:50]
        elif chart_type == "violin":
            simplified_data = raw_data
        elif chart_type == "parallel":
            simplified_data = raw_data[:50]
        else:
            simplified_data = raw_data[:50]

        json_str = json.dumps(simplified_data)
        if len(json_str) > 100000:
            minimal_data = []
            if chart_type == "box":
                minimal_data = raw_data[:20]
            elif chart_type == "trend":
                minimal_data = raw_data[:20]
            elif chart_type == "scatter":
                minimal_data = raw_data[:50]
            elif chart_type == "heatmap":
                minimal_data = raw_data[:50]
            elif chart_type == "histogram":
                minimal_data = raw_data[:50]
            elif chart_type == "bubble":
                minimal_data = raw_data[:20]
            elif chart_type == "violin":
                minimal_data = raw_data[:20]
            elif chart_type == "3d":
                minimal_data = raw_data[:50]
            elif chart_type == "parallel":
                minimal_data = raw_data[:20]
            else:
                minimal_data = raw_data[:20]
            json_str = json.dumps(minimal_data)
    return json_str
