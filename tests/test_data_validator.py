import os
import sys

from utils.data_validator import generate_data_warning, validate_and_align_data

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据验证模块单元测试
"""


# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_validate_and_align_data():
    """测试validate_and_align_data函数"""
    # 测试正常数据
    p1_samples = [17.2, 17.1, 16.8, 17.0, 16.9]
    p2_samples = [16.2, 16.1, 15.9, 16.0, 16.1]
    st_samples = [33.4, 33.2, 32.7, 33.0, 33.0]

    p1_aligned, p2_aligned, st_aligned, data_info = validate_and_align_data(
        p1_samples, p2_samples, st_samples
    )

    # 对齐到三面最小长度
    assert len(p1_aligned) == 5
    assert len(p2_aligned) == 5
    assert len(st_aligned) == 5
    assert data_info["aligned_length"] == 5

    # 验证数据保持不变
    for i in range(5):
        assert p1_aligned[i] == p1_samples[i]
        assert p2_aligned[i] == p2_samples[i]
        assert st_aligned[i] == st_samples[i]

    # 测试没有ST面数据的情况
    p1_aligned, p2_aligned, st_aligned, data_info = validate_and_align_data(p1_samples, p2_samples)

    # ST面为空列表，P1/P2对齐到最小长度
    assert len(p1_aligned) == 5
    assert len(p2_aligned) == 5
    assert st_aligned == []

    # 测试数据长度不一致的情况（P1更长，截断到P2长度）
    p1_samples_long = p1_samples * 2  # 10个数据点
    p1_aligned, p2_aligned, st_aligned, data_info = validate_and_align_data(
        p1_samples_long, p2_samples
    )

    assert len(p1_aligned) == 5
    assert len(p2_aligned) == 5
    assert data_info["aligned_length"] == 5

    # 验证前5个数据点保持不变
    for i in range(5):
        assert p1_aligned[i] == p1_samples_long[i]
        assert p2_aligned[i] == p2_samples[i]

    # 测试NaN过滤：P1含None/NaN时被剔除
    p1_with_nan = [17.2, None, 16.8, float("nan"), 16.9]
    p1_aligned, p2_aligned, st_aligned, data_info = validate_and_align_data(
        p1_with_nan, p2_samples
    )

    assert len(p1_aligned) == 3
    assert data_info["p1_has_nan"] is True


def test_generate_data_warning():
    """测试generate_data_warning函数"""
    # 测试正常数据 - 应该返回空字符串
    data_info = {
        "aligned_length": 10,
        "filtered_p1_length": 10,
        "filtered_p2_length": 10,
        "p1_has_nan": False,
        "p2_has_nan": False,
        "st_has_nan": False,
    }
    warning = generate_data_warning(data_info, "3000rpm")
    assert warning == ""  # 样本充足且无NaN、无长度差异

    # 样本数不足时给出警告
    data_info = {
        "aligned_length": 5,
        "filtered_p1_length": 5,
        "filtered_p2_length": 5,
        "p1_has_nan": False,
        "p2_has_nan": False,
        "st_has_nan": False,
    }
    warning = generate_data_warning(data_info, "3000rpm")
    assert "样本数较少" in warning

    # P1含空值时给出警告
    data_info = {
        "aligned_length": 10,
        "filtered_p1_length": 8,
        "filtered_p2_length": 10,
        "p1_has_nan": True,
        "p2_has_nan": False,
        "st_has_nan": False,
    }
    warning = generate_data_warning(data_info, "3000rpm")
    assert "P1面数据包含空值" in warning

    # P1/P2长度不一致时给出警告
    data_info = {
        "aligned_length": 10,
        "filtered_p1_length": 10,
        "filtered_p2_length": 8,
        "p1_has_nan": False,
        "p2_has_nan": False,
        "st_has_nan": False,
    }
    warning = generate_data_warning(data_info, "3000rpm")
    assert "P1和P2面数据长度不一致" in warning
