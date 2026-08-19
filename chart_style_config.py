#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一的图表样式配置文件

这个文件定义了所有图表的样式配置，确保前端展示与报告导出使用同一套样式定义。
"""

from typing import Any, Dict

# 图表类型配置
CHART_TYPE_CONFIG = {
    "trend": {
        "name": "趋势图",
        "icon": "bi-trend-up",
        "color": "text-success",
        "annotation": "<b>图表指标说明：</b><br>• 线条：中位数变化趋势<br>• X轴：转速<br>• Y轴：中位数<br>• 圆点：各转速的具体中位数值",
        "plotly_color": "#10b981",
    },
    "scatter": {
        "name": "散点图",
        "icon": "bi-scatter",
        "color": "text-info",
        "annotation": "<b>图表指标说明：</b><br>• 圆点：各数据点<br>• 彩色线和圆点：各转速中位数<br>• 线条走势：中位数变化趋势<br>• 点的密集程度：数据离散情况",
        "plotly_color": "#3b82f6",
    },
    "box": {
        "name": "箱线图",
        "icon": "bi-box-seam",
        "color": "text-primary",
        "annotation": "<b>图表指标说明：</b><br>• 箱体：包含50%数据的四分位距(IQR)<br>• 中位数线：数据的中位数<br>• 上下须：数据范围(1.5×IQR内)<br>• 圆点：异常值",
        "plotly_color": "#2563eb",
    },
    "violin": {
        "name": "小提琴图",
        "icon": "bi-music-note-list",
        "color": "text-purple",
        "annotation": "<b>图表指标说明：</b><br>• 小提琴形状：数据分布密度<br>• 中间粗线：数据中位数<br>• 形状宽度：数据密度<br>• 形状高度：数据范围",
        "plotly_color": "#8b5cf6",
    },
    "heatmap": {
        "name": "热力图",
        "icon": "bi-thermometer-half",
        "color": "text-warning",
        "annotation": "<b>图表指标说明：</b><br>• X轴：转速<br>• Y轴：数据点索引<br>• 颜色深浅：不平衡量数值大小<br>• 颜色越黄：数值越大<br>• 颜色越蓝：数值越小",
        "plotly_color": "#f59e0b",
    },
    "histogram": {
        "name": "直方图",
        "icon": "bi-bar-chart-line",
        "color": "text-danger",
        "annotation": "<b>图表指标说明：</b><br>• X轴：不平衡量数值区间<br>• Y轴：落在各区间的频次<br>• 柱形高度：数据分布情况<br>• 峰值位置：数据集中的区间",
        "plotly_color": "#ef4444",
    },
    "radar": {
        "name": "雷达图",
        "icon": "bi-radar",
        "color": "text-dark",
        "annotation": "<b>图表指标说明：</b><br>• 多边形：各项指标的数值<br>• 轴数：指标数量<br>• 多边形大小：数值大小比较<br>• 数据点：显示具体数值<br>• 渐变色填充：增强区分度",
        "plotly_color": "#1e293b",
    },
    "3d": {
        "name": "3D散点图",
        "icon": "bi-cube",
        "color": "text-secondary",
        "annotation": "<b>图表指标说明：</b><br>• X轴：转速<br>• Y轴：数据点索引<br>• Z轴：不平衡量<br>• 点的分布：三维数据关系<br>• 旋转视图：多角度观察<br>• 点大小与透明度：避免视觉重叠",
        "plotly_color": "#64748b",
    },
    "parallel": {
        "name": "平行坐标图",
        "icon": "bi-parallel",
        "color": "text-info",
        "annotation": "<b>图表指标说明：</b><br>• 平行线：各数据点维度<br>• 连线：同一转速下的数据点<br>• 颜色：不同转速区分<br>• 线条交叉：数据点间的关系",
        "plotly_color": "#3b82f6",
    },
    "bubble": {
        "name": "气泡图",
        "icon": "bi-bubbles",
        "color": "text-primary",
        "annotation": "<b>图表指标说明：</b><br>• X轴：转速<br>• Y轴：不平衡量<br>• 气泡大小：数据点数量<br>• 气泡颜色：中位数大小<br>• 气泡位置：数值分布",
        "plotly_color": "#2563eb",
    },
}

# 图表布局配置
CHART_LAYOUT_CONFIG = {
    "common": {
        "title": {"text": "图表", "x": 0.5, "font": {"size": 16, "weight": "bold"}},
        "margin": {"l": 50, "r": 50, "b": 80, "t": 50, "pad": 4},
        "hovermode": "closest",
        "hoverlabel": {
            "bgcolor": "rgba(255, 255, 255, 0.95)",
            "bordercolor": "#2563eb",
            "borderwidth": 1,
            "font": {"color": "#333"},
        },
        "showlegend": False,
    },
    "xaxis": {
        "title": {"text": "类别"},
        "tickangle": 0,
        "tickfont": {"size": 11},
        "automargin": True,
        "tickmode": "auto",
        "nticks": "auto",
        "tickformat": "",
        "tickposition": "outside",
        "ticklen": 5,
        "tickwidth": 1,
        "showgrid": False,
        "range": "auto",
    },
    "yaxis": {
        "title": {"text": "值"},
        "tickfont": {"size": 11},
        "automargin": True,
        "range": "auto",
    },
    "heatmap": {
        "xaxis": {"tickangle": 45, "tickfont": {"size": 11}, "automargin": True},
        "yaxis": {"tickfont": {"size": 11}, "automargin": True},
        "coloraxis": {"colorscale": "Viridis", "colorbar": {"title": "值"}},
    },
    "3d": {
        "scene": {
            "xaxis": {"title": "X", "showgrid": True, "gridwidth": 1, "gridcolor": "#e0e0e0"},
            "yaxis": {"title": "Y", "showgrid": True, "gridwidth": 1, "gridcolor": "#e0e0e0"},
            "zaxis": {"title": "值", "showgrid": True, "gridwidth": 1, "gridcolor": "#e0e0e0"},
            "camera": {
                "autorotate": True,
                "autorotateSpeed": 5,
                "eye": {"x": 1.2, "y": 1.2, "z": 1.2},
            },
            "aspectmode": "data",
            "aspectratio": {"x": 1, "y": 1, "z": 1},
        },
        "margin": {"l": 10, "r": 10, "b": 10, "t": 50, "pad": 4},
    },
}

# 图表配置
CHART_CONFIG = {
    "responsive": True,
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["sendDataToCloud", "toImage"],
    "scrollZoom": True,
    "toImageButtonOptions": {
        "format": "png",
        "filename": "chart",
        "height": 500,
        "width": 700,
        "scale": 2,
    },
    "staticPlot": False,
}

# 图表颜色方案（与设计Token对齐）
CHART_COLOR_SCHEME = {
    "primary": "#2563eb",
    "secondary": "#64748b",
    "success": "#10b981",
    "info": "#3b82f6",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "purple": "#8b5cf6",
    "dark": "#1e293b",
    "light": "#f1f5f9",
}

# 表面颜色映射
SURFACE_COLORS = {
    "p1": "#1f77b4",  # 蓝色
    "p2": "#ff7f0e",  # 橙色
    "sum": "#28a745",  # 绿色
}

# 字体配置
CHART_FONT_CONFIG = {
    "family": "'Helvetica Neue', Arial, sans-serif",
    "size": 12,
    "color": "#333333",
}

# 网格线样式
GRID_STYLE = {"color": "#e0e0e0", "width": 1, "dash": "solid"}

# 线条样式
LINE_STYLE = {"width": 2, "dash": "solid"}

# 数据点样式
MARKER_STYLE = {"size": 8, "symbol": "circle", "line": {"width": 1}}

# 图表尺寸配置
CHART_DIMENSIONS = {
    "default": {"width": 800, "height": 420},
    "small": {"width": 600, "height": 300},
    "large": {"width": 1000, "height": 500},
    "parallel": {"width": 900, "height": 450},
    "3d": {"width": 800, "height": 500},
}

# 图表边距配置
CHART_MARGINS = {
    "default": {"l": 50, "r": 50, "b": 80, "t": 50, "pad": 4},
    "small": {"l": 40, "r": 40, "b": 60, "t": 40, "pad": 4},
    "3d": {"l": 10, "r": 10, "b": 10, "t": 50, "pad": 4},
}

# 导出格式配置
EXPORT_CONFIG = {
    "png": {"width": 1200, "height": 675, "scale": 2},
    "pdf": {"width": 8.5, "height": 11, "unit": "in"},
    "svg": {"width": 1200, "height": 675},
}


def get_chart_layout(chart_type: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    获取图表布局配置

    参数:
        chart_type: 图表类型
        options: 配置选项

    返回:
        布局配置字典
    """
    options = options or {}
    layout = {
        **CHART_LAYOUT_CONFIG["common"],
        "title": {
            **CHART_LAYOUT_CONFIG["common"]["title"],
            "text": options.get("title", CHART_LAYOUT_CONFIG["common"]["title"]["text"]),
        },
    }

    # 添加坐标轴配置
    if chart_type in ["box", "trend", "scatter", "violin", "histogram", "bubble"]:
        layout["xaxis"] = {
            **CHART_LAYOUT_CONFIG["xaxis"],
            "title": {
                "text": options.get("xAxisLabel", CHART_LAYOUT_CONFIG["xaxis"]["title"]["text"])
            },
        }
        layout["yaxis"] = {
            **CHART_LAYOUT_CONFIG["yaxis"],
            "title": {
                "text": options.get("yAxisLabel", CHART_LAYOUT_CONFIG["yaxis"]["title"]["text"])
            },
        }
    elif chart_type == "heatmap":
        layout["xaxis"] = {**CHART_LAYOUT_CONFIG["heatmap"]["xaxis"]}
        layout["yaxis"] = {**CHART_LAYOUT_CONFIG["heatmap"]["yaxis"]}
        layout["coloraxis"] = {
            **CHART_LAYOUT_CONFIG["heatmap"]["coloraxis"],
            "colorbar": {
                "title": options.get(
                    "yAxisLabel", CHART_LAYOUT_CONFIG["heatmap"]["coloraxis"]["colorbar"]["title"]
                )
            },
        }
    elif chart_type == "3d":
        layout["scene"] = {
            **CHART_LAYOUT_CONFIG["3d"]["scene"],
            "zaxis": {
                **CHART_LAYOUT_CONFIG["3d"]["scene"]["zaxis"],
                "title": options.get(
                    "yAxisLabel", CHART_LAYOUT_CONFIG["3d"]["scene"]["zaxis"]["title"]
                ),
            },
        }
        layout["margin"] = {**CHART_LAYOUT_CONFIG["3d"]["margin"]}

    return layout


def get_chart_config() -> Dict[str, Any]:
    """
    获取图表配置

    返回:
        图表配置字典
    """
    return CHART_CONFIG.copy()


def get_chart_color(chart_type: str) -> str:
    """
    获取图表颜色

    参数:
        chart_type: 图表类型

    返回:
        颜色代码
    """
    return CHART_TYPE_CONFIG.get(chart_type, {}).get("plotly_color", CHART_COLOR_SCHEME["primary"])


def get_surface_color(surface_type: str) -> str:
    """
    获取表面颜色

    参数:
        surface_type: 表面类型 (p1, p2, sum)

    返回:
        颜色代码
    """
    return SURFACE_COLORS.get(surface_type, CHART_COLOR_SCHEME["primary"])


def get_chart_dimensions(chart_type: str, size: str = "default") -> Dict[str, int]:
    """
    获取图表尺寸

    参数:
        chart_type: 图表类型
        size: 尺寸类型 (default, small, large)

    返回:
        尺寸字典
    """
    if chart_type == "3d":
        return CHART_DIMENSIONS["3d"]
    elif chart_type == "parallel":
        return CHART_DIMENSIONS["parallel"]
    else:
        return CHART_DIMENSIONS.get(size, CHART_DIMENSIONS["default"])


def get_export_config(format_type: str) -> Dict[str, Any]:
    """
    获取导出配置

    参数:
        format_type: 导出格式 (png, pdf, svg)

    返回:
        导出配置字典
    """
    return EXPORT_CONFIG.get(format_type, EXPORT_CONFIG["png"])
