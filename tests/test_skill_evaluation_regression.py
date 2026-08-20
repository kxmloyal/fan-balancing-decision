#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回归测试：退化面数据（st/p2 无数据、缺字段）时评估不再抛 division by zero

历史 bug：data_analysis._compute_z_scores 对空数组/单元素做 np.std(ddof=1)，
numpy 内部 Python 除法路径抛 ZeroDivisionError，导致深入分析 500。
"""

from app.services.skill_evaluation import skill_evaluation_service


def _mk(rows, missing_key=False):
    out = []
    for i, row in enumerate(rows):
        speed, p1, p2, st = row
        item = {"speed": speed, "p1_samples": p1, "p2_samples": p2}
        if not missing_key:
            item["sum_samples"] = st
        out.append(item)
    return out


def test_evaluate_with_st_empty():
    """st 面无样本（surface_data 仅 p1/p2）→ 不抛异常"""
    data = _mk([
        (800 + i * 100, [50.0 + (i % 5) * 2, 52.0, 49.0], [55.0, 53.0, 56.0], [])
        for i in range(22)
    ])
    result = skill_evaluation_service.evaluate_skill(data)
    assert "advanced_analysis" in result


def test_evaluate_with_only_p1():
    """仅 p1 面有数据（p2/st 全空）→ 不抛异常"""
    data = _mk([
        (800 + i * 100, [50.0 + (i % 4), 52.0, 49.0], [], [])
        for i in range(22)
    ])
    result = skill_evaluation_service.evaluate_skill(data)
    assert "comprehensive_evaluation" in result


def test_evaluate_with_missing_sum_samples_key():
    """数据缺少 sum_samples 字段 → 不抛异常"""
    data = _mk([
        (800 + i * 100, [50.0 + (i % 4), 52.0, 49.0], [55.0, 53.0, 56.0], None)
        for i in range(22)
    ], missing_key=True)
    result = skill_evaluation_service.evaluate_skill(data)
    assert "optimal_speed_evaluation" in result
