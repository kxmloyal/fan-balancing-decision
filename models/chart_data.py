#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图表数据模型

定义用于图表生成的数据模型
"""

from typing import Any, Dict, List


class ChartData:
    """图表数据模型"""

    def __init__(self, chart_type: str, title: str, data: Dict[str, Any]):
        """初始化图表数据

        Args:
            chart_type: 图表类型
            title: 图表标题
            data: 图表数据
        """
        self.chart_type = chart_type
        self.title = title
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {"chart_type": self.chart_type, "title": self.title, "data": self.data}


class BoxPlotData:
    """箱线图数据模型"""

    def __init__(
        self,
        speeds: List[str],
        p1_data: List[List[float]],
        p2_data: List[List[float]],
        sum_data: List[List[float]],
    ):
        """初始化箱线图数据

        Args:
            speeds: 转速列表
            p1_data: P1面数据
            p2_data: P2面数据
            sum_data: 总和数据
        """
        self.speeds = speeds
        self.p1_data = p1_data
        self.p2_data = p2_data
        self.sum_data = sum_data

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "speeds": self.speeds,
            "p1_data": self.p1_data,
            "p2_data": self.p2_data,
            "sum_data": self.sum_data,
        }


class ScatterPlotData:
    """散点图数据模型"""

    def __init__(self, x_data: List[float], y_data: List[float], labels: List[str]):
        """初始化散点图数据

        Args:
            x_data: X轴数据
            y_data: Y轴数据
            labels: 数据标签
        """
        self.x_data = x_data
        self.y_data = y_data
        self.labels = labels

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {"x_data": self.x_data, "y_data": self.y_data, "labels": self.labels}


class TrendPlotData:
    """趋势图数据模型"""

    def __init__(self, speeds: List[str], metrics: Dict[str, List[float]]):
        """初始化趋势图数据

        Args:
            speeds: 转速列表
            metrics: 指标数据
        """
        self.speeds = speeds
        self.metrics = metrics

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {"speeds": self.speeds, "metrics": self.metrics}


class RadarChartData:
    """雷达图数据模型"""

    def __init__(self, categories: List[str], values: List[float], title: str):
        """初始化雷达图数据

        Args:
            categories: 类别列表
            values: 值列表
            title: 图表标题
        """
        self.categories = categories
        self.values = values
        self.title = title

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {"categories": self.categories, "values": self.values, "title": self.title}
