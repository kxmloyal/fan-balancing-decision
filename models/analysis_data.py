#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析数据模型

定义用于数据处理和分析的数据模型
"""

from typing import Any, Dict, List


class SurfaceData:
    """表面数据模型"""

    def __init__(self, surface_type: str, data: Dict[str, List[float]]):
        """初始化表面数据

        Args:
            surface_type: 表面类型（p1, p2, st）
            data: 转速到样本数据的映射
        """
        self.surface_type = surface_type
        self.data = data

    def get_speeds(self) -> List[str]:
        """获取所有转速"""
        return sorted(self.data.keys())

    def get_samples(self, speed: str) -> List[float]:
        """获取指定转速的样本数据"""
        return self.data.get(speed, [])

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {"surface_type": self.surface_type, "data": self.data}


class ParsedDataItem:
    """解析数据项模型"""

    def __init__(
        self, speed: str, p1_samples: List[float], p2_samples: List[float], sum_samples: List[float]
    ):
        """初始化解析数据项

        Args:
            speed: 转速
            p1_samples: P1面样本数据
            p2_samples: P2面样本数据
            sum_samples: 总和样本数据
        """
        self.speed = speed
        self.p1_samples = p1_samples
        self.p2_samples = p2_samples
        self.sum_samples = sum_samples

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "speed": self.speed,
            "p1_samples": self.p1_samples,
            "p2_samples": self.p2_samples,
            "sum_samples": self.sum_samples,
        }


class StatisticsData:
    """统计数据模型"""

    def __init__(
        self,
        speed: str,
        p1_stats: Dict[str, float],
        p2_stats: Dict[str, float],
        sum_stats: Dict[str, float],
    ):
        """初始化统计数据

        Args:
            speed: 转速
            p1_stats: P1面统计数据
            p2_stats: P2面统计数据
            sum_stats: 总和统计数据
        """
        self.speed = speed
        self.p1_stats = p1_stats
        self.p2_stats = p2_stats
        self.sum_stats = sum_stats

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "speed": self.speed,
            "p1_stats": self.p1_stats,
            "p2_stats": self.p2_stats,
            "sum_stats": self.sum_stats,
        }


class OptimalSpeedEvaluation:
    """最优转速评估模型"""

    def __init__(self, best_speeds: List[str], speed_detailed_scores: Dict[str, Dict[str, float]]):
        """初始化最优转速评估

        Args:
            best_speeds: 最优转速列表
            speed_detailed_scores: 各转速的详细得分
        """
        self.best_speeds = best_speeds
        self.speed_detailed_scores = speed_detailed_scores

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "best_speeds": self.best_speeds,
            "speed_detailed_scores": self.speed_detailed_scores,
            "detailed_scores": self.speed_detailed_scores,  # 保持兼容性
        }
