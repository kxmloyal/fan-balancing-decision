#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ML 历史数据导入 — 格式转换适配器

将 outputs/ 统计CSV 的行式数据转换为各 ML 面板所需的 JSON 格式。
输入数据格式: {speeds: [...], rows: [{speed, p1_mean, p1_std, p1_cv, p2_mean, ...}, ...]}
"""

import math
from typing import Any, Dict, List


def to_trend_format(
    raw_data: Dict[str, Any], face: str = "P1"
) -> List[Dict[str, Any]]:
    """
    转换为趋势预测/异常检测格式: [{date, value}, ...]

    Args:
        raw_data: 行式数据，rows[i] 含 speed + {face}_mean
        face: 端面名 (P1/P2/ST)
    """
    rows = raw_data.get("rows", [])
    face_lower = face.lower()
    value_key = f"{face_lower}_mean"

    result = []
    for r in rows:
        val = r.get(value_key, 0)
        if val:
            result.append({"date": r["speed"], "value": round(val, 6)})
    return result


def to_metrics_format(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    转换为关键指标预测格式: [{date, p1_mean, p1_cv, p1_std, p2_mean, ...}, ...]

    直接从 CSV 预计算统计量映射，不做重新计算。
    """
    rows = raw_data.get("rows", [])
    result = []

    for r in rows:
        row = {"date": r["speed"]}

        # 直接映射各端面的预计算统计量（mean, cv, std, max）
        for face in ["p1", "p2", "st"]:
            for stat in ["mean", "cv", "std", "max"]:
                key = f"{face}_{stat}"
                if key in r:
                    row[key] = r[key]

        # total = √(p1_mean² + p2_mean²)
        p1_m = row.get("p1_mean", 0)
        p2_m = row.get("p2_mean", 0)
        row["total"] = round(math.sqrt(p1_m**2 + p2_m**2), 6)

        result.append(row)
    return result


def to_multi_format(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    转换为多维度分析格式: [{speed, p1_amplitude, p2_amplitude, p1_std, ...}, ...]

    将 mean→amplitude 重命名，保留 std。
    """
    rows = raw_data.get("rows", [])
    result = []

    for r in rows:
        row = {"speed": r["speed"]}

        # p1_mean → p1_amplitude, p2_mean → p2_amplitude, st_mean → st_amplitude
        for face in ["p1", "p2", "st"]:
            mean_key = f"{face}_mean"
            std_key = f"{face}_std"
            if mean_key in r:
                row[f"{face}_amplitude"] = r[mean_key]
            if std_key in r:
                row[f"{face}_std"] = r[std_key]

        # P1/P2 幅值比
        p1_a = row.get("p1_amplitude", 0)
        p2_a = row.get("p2_amplitude", 0)
        row["p1_p2_ratio"] = round(p1_a / p2_a, 4) if p2_a != 0 else 0.0

        result.append(row)
    return result