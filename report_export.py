#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
兼容转发层 —— 指向 services.report_exporter 三层委派架构

P2-14 方案 A：将原 1350 行单体拆分为多模块：
  services/report_exporter.py     — ReportExporter 核心 + HtmlExporter
  services/share_link_manager.py  — ShareLinkManager 分享链接管理（第42轮拆分）
  services/report_renderer.py     — ReportRenderer (数据驱动 HTML 报告生成)
  services/report_data_export.py  — ReportDataExporter (CSV/JSON/Excel)

本文件保留根目录兼容性，所有 from report_export import Xxx 自动转发到新模块。
不包含任何业务逻辑。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_export_css import EXPORTER_CSS
from services.report_exporter import (
    HtmlExporter,
    ReportExporter,
    ShareLinkManager,
    _html_exporter_css,
)

try:
    from chart_generation_optimized import CHART_TYPE_CONFIG
except ImportError:
    CHART_TYPE_CONFIG = {}

from config import EXCEL_AVAILABLE, WEASYPRINT_AVAILABLE
from utils.model_utils import sanitize_model_name

__all__ = [
    "HtmlExporter",
    "ShareLinkManager",
    "ReportExporter",
    "_html_exporter_css",
    "EXPORTER_CSS",
    "CHART_TYPE_CONFIG",
    "EXCEL_AVAILABLE",
    "WEASYPRINT_AVAILABLE",
    "sanitize_model_name",
]
