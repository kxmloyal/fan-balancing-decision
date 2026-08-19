#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图表生成服务（向后兼容 shim）

⚠ 真实实现已统一至根目录 chart_generation_optimized.py（含型号子目录、数据缓存、
   全类型 Plotly/Matplotlib 渲染）。本文件保留原公开符号，
   避免 from app.services.chart_generation import ... 调用断裂。

公开符号（与重构前一致）：
  - CHART_TYPE_CONFIG           统一来自 chart_style_config
  - build_report_charts
  - generate_single_surface_plots
  - generate_generic_charts
  - fetch_chart_data
"""

from chart_generation_optimized import (  # noqa: F401
    build_report_charts,
    fetch_chart_data,
    generate_generic_charts,
    generate_single_surface_plots,
)
from chart_style_config import CHART_TYPE_CONFIG  # noqa: F401

__all__ = [
    "CHART_TYPE_CONFIG",
    "build_report_charts",
    "fetch_chart_data",
    "generate_generic_charts",
    "generate_single_surface_plots",
]
