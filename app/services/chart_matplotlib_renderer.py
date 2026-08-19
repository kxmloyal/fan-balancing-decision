#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Matplotlib PNG 图表渲染器（chart_generation_optimized 拆分模块）

负责将图表数据渲染为 PNG 静态图像，以及失败时的回退图像。
"""

import json
import logging
import os
import traceback

import matplotlib.pyplot as plt
import numpy as np

from chart_style_config import CHART_TYPE_CONFIG
from app.services.chart_utils import _prepare_chart_config, get_speed_numeric

logger = logging.getLogger(__name__)


def _generate_matplotlib_png(chart_data_json_str, chart_type, surface_name, png_path, y_range=None):
    """使用matplotlib生成PNG静态图像

    Args:
        chart_data_json_str: 图表数据的JSON字符串
        chart_type: 图表类型字符串
        surface_name: 面名称
        png_path: PNG文件保存路径
        y_range: Y轴范围元组(min, max)，用于跨面对齐刻度

    Returns:
        bool: 文件成功生成返回True，失败返回False
    """
    fig = None
    try:
        plt.switch_backend("Agg")
        try:
            from chart_style_config import (
                CHART_COLOR_SCHEME,
                CHART_FONT_CONFIG,
                CHART_TYPE_CONFIG,
                GRID_STYLE,
            )
        except ImportError:
            CHART_FONT_CONFIG = {"family": "sans-serif", "size": 12, "color": "#333333"}
            CHART_COLOR_SCHEME = {
                "primary": "#2563eb",
                "info": "#3b82f6",
                "success": "#10b981",
                "warning": "#f59e0b",
                "purple": "#8b5cf6",
                "secondary": "#64748b",
            }
            CHART_TYPE_CONFIG = {
                "box": {"plotly_color": "#2563eb"},
                "trend": {"plotly_color": "#10b981"},
                "scatter": {"plotly_color": "#3b82f6"},
            }
        font_family = CHART_FONT_CONFIG.get("family", "sans-serif")
        plt.rcParams["font.family"] = ["sans-serif"]
        plt.rcParams["font.sans-serif"] = [
            "Noto Sans CJK SC",
            "WenQuanYi Zen Hei",
            "Microsoft YaHei",
            "DejaVu Sans",
        ]
        plt.rcParams["axes.unicode_minus"] = False
        plt.rcParams["text.usetex"] = False

        chart_data_json = json.loads(chart_data_json_str)
        chart_config = _prepare_chart_config(chart_type, surface_name, "")

        fig, ax = plt.subplots(figsize=(14, 5))
        plt.subplots_adjust(left=0.08, right=0.98, top=0.9, bottom=0.35)

        if chart_type == "box":
            box_data = []
            labels = []
            medians = []
            all_points = []
            all_x = []

            for i, item in enumerate(chart_data_json):
                if "data" in item and "name" in item:
                    box_data.append(item["data"])
                    labels.append(item["name"])
                    if item["data"]:
                        median = sorted(item["data"])[len(item["data"]) // 2]
                        medians.append(median)
                    else:
                        medians.append(0)
                    for j, point in enumerate(item["data"]):
                        all_points.append(point)
                        all_x.append(i + 1)

            if box_data:
                plotly_color = CHART_TYPE_CONFIG.get("box", {}).get(
                    "plotly_color", CHART_COLOR_SCHEME["primary"]
                )
                box = ax.boxplot(box_data, patch_artist=True, notch=False)
                box_colors = [
                    CHART_COLOR_SCHEME[k]
                    for k in ["primary", "info", "success", "warning", "purple"]
                ]
                for i, patch in enumerate(box["boxes"]):
                    patch.set_facecolor(box_colors[i % len(box_colors)])
                    patch.set_alpha(0.5)
                for median in box["medians"]:
                    median.set_color(plotly_color)
                    median.set_linewidth(2)
                ax.scatter(
                    all_x, all_points, color=CHART_COLOR_SCHEME["secondary"], alpha=0.6, s=30
                )
                if medians:
                    ax.plot(
                        range(1, len(medians) + 1),
                        medians,
                        "o-",
                        color=plotly_color,
                        linewidth=2,
                        alpha=0.8,
                    )
                ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
                ax.tick_params(axis="x", which="major", pad=10)
                ax.set_title(chart_config["title"])
                ax.set_ylabel("不平衡量")
                ax.grid(True, linestyle="--", alpha=0.3)
                try:
                    plt.tight_layout()
                except Exception:
                    pass

        elif chart_type == "trend":
            x = []
            y = []
            labels = []
            for i, item in enumerate(chart_data_json):
                if "value" in item and "name" in item:
                    x.append(i)
                    y.append(item["value"])
                    labels.append(item["name"])
            if x and y:
                trend_color = CHART_TYPE_CONFIG.get("trend", {}).get(
                    "plotly_color", CHART_COLOR_SCHEME["success"]
                )
                ax.plot(x, y, "o-", color=trend_color, linewidth=2)
                ax.set_xticks(x)
                ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
                ax.tick_params(axis="x", which="major", pad=10)
                ax.set_title(chart_config["title"])
                ax.set_ylabel("不平衡量")
                plt.tight_layout()

        elif chart_type == "scatter":
            x = []
            y = []
            for item in chart_data_json:
                if isinstance(item, list) and len(item) >= 2:
                    x.append(item[0])
                    y.append(item[1])
            if x and y:
                scatter_color = CHART_TYPE_CONFIG.get("scatter", {}).get(
                    "plotly_color", CHART_COLOR_SCHEME["info"]
                )
                x_indices = list(range(len(x)))
                ax.scatter(x_indices, y, color=scatter_color, alpha=0.7, s=30)
                step = max(1, len(x_indices) // 10)
                ax.set_xticks(x_indices[::step])
                ax.set_xticklabels(
                    [x[i] for i in x_indices[::step]], rotation=45, ha="right", fontsize=9
                )
                ax.tick_params(axis="x", which="major", pad=10)
                ax.set_title(chart_config["title"])
                ax.set_ylabel("不平衡量")
                plt.tight_layout()

        elif chart_type == "violin":
            violin_data = []
            labels = []
            for item in chart_data_json:
                if "data" in item and "name" in item:
                    violin_data.append([v for v in item["data"] if not np.isnan(v)])
                    labels.append(item["name"])
            if violin_data:
                v_color = CHART_TYPE_CONFIG.get("violin", {}).get(
                    "plotly_color", CHART_COLOR_SCHEME["purple"]
                )
                positions = list(range(1, len(violin_data) + 1))
                vp = ax.violinplot(
                    violin_data, positions=positions, showmeans=False, showmedians=True
                )
                for body in vp["bodies"]:
                    body.set_facecolor(v_color)
                    body.set_alpha(0.5)
                for partname in ("cbars", "cmins", "cmaxes"):
                    if partname in vp:
                        vp[partname].set_color(v_color)
                        vp[partname].set_alpha(0.6)
                vp["cmedians"].set_color(v_color)
                vp["cmedians"].set_linewidth(2)
                ax.set_xticks(positions)
                ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
                ax.tick_params(axis="x", which="major", pad=10)
                ax.set_title(chart_config["title"])
                ax.set_ylabel("不平衡量")
                ax.grid(True, linestyle="--", alpha=0.3)
                plt.tight_layout()

        elif chart_type == "heatmap":
            speeds = []
            values_by_speed = {}
            for item in chart_data_json:
                if isinstance(item, list) and len(item) >= 3:
                    speed, idx, val = item[0], item[1], item[2]
                    if speed not in values_by_speed:
                        values_by_speed[speed] = []
                        speeds.append(speed)
                    values_by_speed[speed].append(val)
            if speeds and values_by_speed:
                max_len = max(len(v) for v in values_by_speed.values())
                data_matrix = np.full((max_len, len(speeds)), np.nan)
                for j, speed in enumerate(speeds):
                    vals = values_by_speed[speed]
                    data_matrix[: len(vals), j] = vals
                im = ax.imshow(data_matrix, aspect="auto", cmap="YlOrRd")
                ax.set_xticks(range(len(speeds)))
                ax.set_xticklabels(speeds, rotation=45, ha="right", fontsize=9)
                ax.set_title(chart_config["title"])
                ax.set_xlabel("转速")
                ax.set_ylabel("数据点索引")
                plt.colorbar(im, ax=ax, label="不平衡量")
                plt.tight_layout()

        elif chart_type == "histogram":
            all_values = []
            for v in chart_data_json:
                if v is not None and not np.isnan(float(v)):
                    all_values.append(float(v))
            if all_values:
                h_color = CHART_TYPE_CONFIG.get("histogram", {}).get(
                    "plotly_color", CHART_COLOR_SCHEME["warning"]
                )
                ax.hist(
                    all_values,
                    bins=min(30, len(all_values)),
                    color=h_color,
                    alpha=0.7,
                    edgecolor="white",
                )
                ax.set_title(chart_config["title"])
                ax.set_xlabel("不平衡量")
                ax.set_ylabel("频次")
                ax.grid(True, linestyle="--", alpha=0.3)
                plt.tight_layout()

        elif chart_type == "bubble":
            bubble_x = []
            bubble_y = []
            bubble_sizes = []
            labels = []
            for i, item in enumerate(chart_data_json):
                if "value" in item and isinstance(item["value"], list) and len(item["value"]) >= 3:
                    bubble_x.append(i)
                    bubble_y.append(float(item["value"][1]))
                    bubble_sizes.append(max(float(item["value"][2]) * 20, 10))
                    labels.append(item.get("name", str(i)))
            if bubble_x:
                b_color = CHART_TYPE_CONFIG.get("bubble", {}).get(
                    "plotly_color", CHART_COLOR_SCHEME["primary"]
                )
                ax.scatter(
                    bubble_x, bubble_y, s=bubble_sizes, color=b_color, alpha=0.6, edgecolors="white"
                )
                ax.set_xticks(bubble_x)
                ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
                ax.tick_params(axis="x", which="major", pad=10)
                ax.set_title(chart_config["title"])
                ax.set_xlabel("转速")
                ax.set_ylabel("不平衡量")
                ax.grid(True, linestyle="--", alpha=0.3)
                plt.tight_layout()

        elif chart_type == "3d":
            plt.close(fig)
            fig = plt.figure(figsize=(14, 8))
            ax = fig.add_subplot(111, projection="3d")
            x_vals = []
            y_vals = []
            z_vals = []
            speed_labels = []
            for item in chart_data_json:
                if isinstance(item, list) and len(item) >= 3:
                    speed_labels.append(str(item[0]))
                    y_vals.append(item[1])
                    z_vals.append(float(item[2]))
            if z_vals:
                unique_speeds = sorted(set(speed_labels), key=get_speed_numeric)
                speed_to_x = {s: i for i, s in enumerate(unique_speeds)}
                x_vals = [speed_to_x[s] for s in speed_labels]
                sc = ax.scatter(x_vals, y_vals, z_vals, c=z_vals, cmap="viridis", alpha=0.7, s=30)
                ax.set_xticks(list(range(len(unique_speeds))))
                ax.set_xticklabels(unique_speeds, rotation=45, ha="right", fontsize=9)
                ax.set_xlabel("转速")
                ax.set_ylabel("数据点索引")
                ax.set_zlabel("不平衡量")
                ax.set_title(chart_config["title"])
                plt.colorbar(sc, ax=ax, label="不平衡量", shrink=0.6)
                try:
                    plt.tight_layout()
                except Exception:
                    pass

        elif chart_type == "parallel":
            speeds = []
            medians = []
            means = []
            for item in chart_data_json:
                if isinstance(item, list) and len(item) >= 3:
                    speeds.append(str(item[0]))
                    medians.append(float(item[1]))
                    means.append(float(item[2]))
            if speeds:
                x_indices = list(range(len(speeds)))
                p_color = CHART_TYPE_CONFIG.get("parallel", {}).get(
                    "plotly_color", CHART_COLOR_SCHEME["info"]
                )
                ax.plot(x_indices, medians, "o-", color=p_color, linewidth=2, label="中位数")
                ax.plot(
                    x_indices,
                    means,
                    "s--",
                    color=CHART_COLOR_SCHEME["warning"],
                    linewidth=1.5,
                    alpha=0.7,
                    label="均值",
                )
                ax.set_xticks(x_indices)
                ax.set_xticklabels(speeds, rotation=45, ha="right", fontsize=9)
                ax.tick_params(axis="x", which="major", pad=10)
                ax.set_title(chart_config["title"])
                ax.set_xlabel("转速")
                ax.set_ylabel("不平衡量")
                ax.legend(loc="best", fontsize=9)
                ax.grid(True, linestyle="--", alpha=0.3)
                try:
                    plt.tight_layout()
                except Exception:
                    pass

        elif chart_type == "radar":
            radar_labels = []
            radar_values = []
            for item in chart_data_json:
                if isinstance(item, dict):
                    speed = str(item.get("转速", ""))
                    val = item.get("不平衡量", 0)
                    if speed:
                        radar_labels.append(speed)
                        radar_values.append(float(val))
            if radar_labels and len(radar_labels) >= 3:
                plt.close(fig)
                angles = np.linspace(0, 2 * np.pi, len(radar_labels), endpoint=False).tolist()
                radar_values_closed = radar_values + radar_values[:1]
                angles_closed = angles + angles[:1]
                fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
                r_color = CHART_TYPE_CONFIG.get("radar", {}).get(
                    "plotly_color", CHART_COLOR_SCHEME["secondary"]
                )
                ax.fill(angles_closed, radar_values_closed, color=r_color, alpha=0.25)
                ax.plot(angles_closed, radar_values_closed, "o-", color=r_color, linewidth=2)
                ax.set_xticks(angles)
                ax.set_xticklabels(radar_labels, fontsize=9)
                ax.set_title(chart_config["title"], pad=20)
                try:
                    plt.tight_layout()
                except Exception:
                    pass

        else:
            display_name = CHART_TYPE_CONFIG.get(chart_type, {}).get("name", chart_type)
            ax.text(
                0.5,
                0.5,
                f"{surface_name} {display_name}",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=14,
                color="#888",
            )
            ax.set_title(chart_config["title"])
            ax.axis("off")

        plt.tight_layout()

        if y_range and len(y_range) == 2:
            try:
                plt.gca().set_ylim(y_range[0], y_range[1])
            except Exception:
                pass

        plt.savefig(png_path, dpi=150, bbox_inches="tight")
    except Exception as e:
        logger.error(f"生成图表图像失败 [{chart_type}]: {str(e)}\n{traceback.format_exc()}")
    finally:
        if fig is not None:
            plt.close(fig)

    return os.path.exists(png_path)
