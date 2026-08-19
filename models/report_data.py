#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告数据模型

定义用于报告生成的数据模型
"""

from datetime import datetime
from typing import Any, Dict, List


class ReportData:
    """报告数据模型"""

    def __init__(self, title: str, fan_model: str, generated_at: datetime, data: Dict[str, Any]):
        """初始化报告数据

        Args:
            title: 报告标题
            fan_model: 扇叶型号
            generated_at: 生成时间
            data: 报告数据
        """
        self.title = title
        self.fan_model = fan_model
        self.generated_at = generated_at
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "fan_model": self.fan_model,
            "generated_at": self.generated_at.isoformat(),
            "data": self.data,
        }


class ReportSection:
    """报告章节模型"""

    def __init__(self, title: str, content: Any, section_type: str = "text"):
        """初始化报告章节

        Args:
            title: 章节标题
            content: 章节内容
            section_type: 章节类型（text, table, chart）
        """
        self.title = title
        self.content = content
        self.section_type = section_type

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {"title": self.title, "content": self.content, "section_type": self.section_type}


class ReportTable:
    """报告表格模型"""

    def __init__(self, headers: List[str], rows: List[List[Any]]):
        """初始化报告表格

        Args:
            headers: 表头
            rows: 表格行数据
        """
        self.headers = headers
        self.rows = rows

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {"headers": self.headers, "rows": self.rows}


class ReportChart:
    """报告图表模型"""

    def __init__(
        self, chart_type: str, title: str, data: Dict[str, Any], width: int = 800, height: int = 500
    ):
        """初始化报告图表

        Args:
            chart_type: 图表类型
            title: 图表标题
            data: 图表数据
            width: 图表宽度
            height: 图表高度
        """
        self.chart_type = chart_type
        self.title = title
        self.data = data
        self.width = width
        self.height = height

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chart_type": self.chart_type,
            "title": self.title,
            "data": self.data,
            "width": self.width,
            "height": self.height,
        }
