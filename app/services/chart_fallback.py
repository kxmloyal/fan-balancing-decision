#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图表回退图像生成器（chart_generation_optimized 拆分模块）

当 PNG 渲染失败时，生成简化占位图像（matplotlib 简图或 SVG）。
"""

import logging
import os

import matplotlib.pyplot as plt

from chart_style_config import CHART_TYPE_CONFIG

logger = logging.getLogger(__name__)


def _generate_fallback_image(surface_name, chart_type, png_path):
    """当PNG生成失败时，创建回退图像（matplotlib简图或SVG占位图）

    Args:
        surface_name: 面名称
        chart_type: 图表类型字符串
        png_path: 原始PNG文件路径

    Returns:
        str: 实际生成的文件路径（可能是PNG或SVG）
    """
    display_name = CHART_TYPE_CONFIG.get(chart_type, {}).get("name", chart_type)
    fig = None
    try:
        plt.rcParams["font.family"] = ["sans-serif"]
        plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False
        plt.rcParams["text.usetex"] = False
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f"{surface_name} {display_name}", ha="center", va="center", fontsize=12)
        ax.axis("off")
        plt.savefig(png_path, dpi=150, bbox_inches="tight")
        plt.close()
        return png_path
    except Exception as e2:
        logger.error(f"创建占位图像也失败: {str(e2)}")
        if fig is not None:
            plt.close(fig)
        svg_path = os.path.splitext(png_path)[0] + ".svg"
        svg_content = f"""
<svg width="800" height="480" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#f5f5f5"/>
  <text x="400" y="240" font-family="Arial" font-size="24"
  text-anchor="middle" fill="#333">
    {surface_name} {display_name}
  </text>
  <text x="400" y="280" font-family="Arial" font-size="16"
  text-anchor="middle" fill="#666">
    图表生成失败
  </text>
</svg>
"""
        try:
            with open(svg_path, "w") as f:
                f.write(svg_content)
        except (IOError, OSError) as e:
            logger.error("SVG文件写入失败 %s: %s", svg_path, str(e))
        return svg_path
