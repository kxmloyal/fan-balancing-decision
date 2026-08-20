#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统计分析模块单元测试 — 适配当前 API

测试范围：
- calculate_surface_stats: 单面统计量
- generate_stats_data: 转速统计表
- calculate_optimal_speed_evaluation: 最优转速评分
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.project_statistics import (
    calculate_optimal_speed_evaluation,
    calculate_surface_stats,
    generate_stats_data,
)


def test_calculate_surface_stats_p1():
    """测试 P1 面统计数据"""
    samples = [1.1, 1.5, 1.3, 1.4, 1.6]
    stats = calculate_surface_stats(samples, "P1")
    assert stats["P1-平均值"] is not None
    assert stats["P1-中位数"] is not None
    assert stats["P1-标准差"] is not None
    assert stats["P1-IQR"] is not None
    assert stats["P1-CV"] is not None


def test_calculate_surface_stats_p2():
    """测试 P2 面统计数据"""
    samples = [2.1, 2.5, 2.3, 2.4, 2.6]
    stats = calculate_surface_stats(samples, "P2")
    assert stats["P2-平均值"] is not None
    assert float(stats["P2-平均值"]) > 2.0


def test_calculate_surface_stats_empty():
    """测试空数据过滤"""
    stats = calculate_surface_stats([], "P1")
    assert stats == {}


def test_generate_stats_data():
    """测试生成统计数据"""
    parsed_data = [
        {
            "speed": "2500",
            "p1_samples": [1.1, 1.5, 1.3, 1.4],
            "p2_samples": [2.1, 2.5, 2.3, 2.4],
            "sum_samples": [3.2, 4.0, 3.6, 3.8],
        },
        {
            "speed": "3000",
            "p1_samples": [1.0, 1.4, 1.2, 1.3],
            "p2_samples": [2.0, 2.4, 2.2, 2.3],
            "sum_samples": [3.0, 3.8, 3.4, 3.6],
        },
    ]
    stats_data = generate_stats_data(parsed_data)
    assert isinstance(stats_data, list)
    assert len(stats_data) == 2
    assert "转速" in stats_data[0]
    assert "P1-IQR" in stats_data[0]
    assert "P1-CV" in stats_data[0]


def test_calculate_optimal_speed_evaluation():
    """测试最优转速评估"""
    parsed_data = [
        {
            "speed": "2500",
            "p1_samples": [1.1, 1.5, 1.3, 1.4, 1.6, 1.2, 1.3, 1.4],
            "p2_samples": [2.1, 2.5, 2.3, 2.4, 2.6, 2.2, 2.3, 2.4],
            "sum_samples": [],
        },
        {
            "speed": "3000",
            "p1_samples": [1.0, 1.4, 1.2, 1.3, 1.5, 1.1, 1.2, 1.3],
            "p2_samples": [2.0, 2.4, 2.2, 2.3, 2.5, 2.1, 2.2, 2.3],
            "sum_samples": [],
        },
    ]
    stats_data = generate_stats_data(parsed_data)
    evaluation = calculate_optimal_speed_evaluation(stats_data)
    assert isinstance(evaluation, dict)
    assert "best_speeds" in evaluation
    assert "speed_detailed_scores" in evaluation


def test_face_score_iqr_normalization():
    """IQR 归一化：按面内中位 IQR 归一化，消除量纲差异对得分的稀释"""
    from app.services.project_statistics import calculate_face_score

    # 同一 IQR 绝对值，归一化后得分显著高于原始 1/(1+iqr)
    raw_score, raw_detail = calculate_face_score(
        {"P1-IQR": "100", "P1-CV": "5"}, "P1", {"P1": 1.0}, face_key="p1"
    )
    norm_score, norm_detail = calculate_face_score(
        {"P1-IQR": "100", "P1-CV": "5"},
        "P1",
        {"P1": 1.0},
        face_key="p1",
        iqr_median={"p1": 100.0},
    )
    assert norm_detail["iqr_score"] == 0.5  # 中位点归一化得分为 0.5
    assert norm_detail["iqr_score"] > raw_detail["iqr_score"]  # 0.5 > 1/101

    # 量级相近时相对差异仍可分辨：IQR=50 与 IQR=100（中位 75）
    lo_score, lo = calculate_face_score(
        {"P1-IQR": "50", "P1-CV": "5"}, "P1", {"P1": 1.0}, face_key="p1",
        iqr_median={"p1": 75.0},
    )
    hi_score, hi = calculate_face_score(
        {"P1-IQR": "100", "P1-CV": "5"}, "P1", {"P1": 1.0}, face_key="p1",
        iqr_median={"p1": 75.0},
    )
    assert lo["iqr_score"] > hi["iqr_score"]


def test_face_score_iqr_median_zero():
    """IQR 中位数为 0（全部转速 IQR 均为 0）时不得除零，得分回退为 1"""
    from app.services.project_statistics import calculate_face_score

    score, detail = calculate_face_score(
        {"P1-IQR": "0", "P1-CV": "2"}, "P1", {"P1": 1.0}, face_key="p1",
        iqr_median={"p1": 0.0},
    )
    assert detail["iqr_score"] == 1.0  # 1/(1+0)，无 ZeroDivisionError


def test_evaluation_smoke_with_iqr_normalization():
    """端到端冒烟：归一化后评估仍正常产出最优转速"""
    parsed_data = [
        {
            "speed": "2500",
            "p1_samples": [1.1, 1.5, 1.3, 1.4, 1.6, 1.2, 1.3, 1.4],
            "p2_samples": [2.1, 2.5, 2.3, 2.4, 2.6, 2.2, 2.3, 2.4],
            "sum_samples": [],
        },
        {
            "speed": "3000",
            "p1_samples": [1.0, 1.4, 1.2, 1.3, 1.5, 1.1, 1.2, 1.3],
            "p2_samples": [2.0, 2.4, 2.2, 2.3, 2.5, 2.1, 2.2, 2.3],
            "sum_samples": [],
        },
    ]
    stats_data = generate_stats_data(parsed_data)
    evaluation = calculate_optimal_speed_evaluation(stats_data)
    assert evaluation["best_speeds"]
    scores = evaluation["speed_detailed_scores"]
    for speed, detail in scores.items():
        for face in ("P1", "P2", "ST"):
            if detail[face]["face_score"] is not None:
                assert 0 <= detail[face]["face_score"] <= 1
