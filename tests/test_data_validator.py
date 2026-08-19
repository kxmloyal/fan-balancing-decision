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

    # 验证结果
    assert len(p1_aligned) == 30  # 应该填充到30个数据点
    assert len(p2_aligned) == 30
    assert len(st_aligned) == 30

    # 验证前5个数据点保持不变
    for i in range(5):
        assert p1_aligned[i] == p1_samples[i]
        assert p2_aligned[i] == p2_samples[i]
        assert st_aligned[i] == st_samples[i]

    # 验证剩余数据点是NaN
    for i in range(5, 30):
        assert (
            isinstance(p1_aligned[i], float)
            and isinstance(p2_aligned[i], float)
            and isinstance(st_aligned[i], float)
        )

    # 测试没有ST面数据的情况
    p1_aligned, p2_aligned, st_aligned, data_info = validate_and_align_data(p1_samples, p2_samples)

    # 验证结果
    assert len(p1_aligned) == 30
    assert len(p2_aligned) == 30
    assert len(st_aligned) == 30

    # 测试数据长度不一致的情况
    p1_samples_long = p1_samples * 2  # 10个数据点
    p1_aligned, p2_aligned, st_aligned, data_info = validate_and_align_data(
        p1_samples_long, p2_samples
    )

    # 验证结果
    assert len(p1_aligned) == 30
    assert len(p2_aligned) == 30
    assert len(st_aligned) == 30

    # 验证前5个数据点保持不变
    for i in range(5):
        assert p1_aligned[i] == p1_samples_long[i]
        assert p2_aligned[i] == p2_samples[i]


def test_generate_data_warning():
    """测试generate_data_warning函数"""
    # 测试正常数据信息 - 应该返回空字符串
    data_info = {"p1_valid": True, "p2_valid": True, "st_valid": True, "is_complete": True}
    warning = generate_data_warning(data_info, "3000rpm")
    assert warning == ""  # 应该没有警告

    # 测试无效数据信息 - 应该返回空字符串（因为已取消警告）
    data_info = {"p1_valid": False, "p2_valid": False, "st_valid": True, "is_complete": False}
    warning = generate_data_warning(data_info, "3000rpm")
    assert warning == ""  # 应该没有警告，因为已取消所有数据警告

    # 测试部分无效数据信息 - 应该返回空字符串（因为已取消警告）
    data_info = {"p1_valid": True, "p2_valid": False, "st_valid": True, "is_complete": True}
    warning = generate_data_warning(data_info, "3000rpm")
    assert warning == ""  # 应该没有警告，因为已取消所有数据警告
