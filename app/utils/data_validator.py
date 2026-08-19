#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""数据验证器"""

import numpy as np


def validate_and_align_data(p1_samples, p2_samples, st_samples=None):
    """验证并对齐数据

    Args:
        p1_samples: P1面样本数据
        p2_samples: P2面样本数据
        st_samples: ST面样本数据（可选）

    Returns:
        tuple: (p1_aligned, p2_aligned, st_aligned, data_info)
    """
    # 确保样本数据是列表
    if not isinstance(p1_samples, list):
        p1_samples = list(p1_samples)
    if not isinstance(p2_samples, list):
        p2_samples = list(p2_samples)
    if st_samples and not isinstance(st_samples, list):
        st_samples = list(st_samples)

    # 移除空值
    p1_filtered = [x for x in p1_samples if x is not None and not np.isnan(x)]
    p2_filtered = [x for x in p2_samples if x is not None and not np.isnan(x)]
    st_filtered = []
    if st_samples:
        st_filtered = [x for x in st_samples if x is not None and not np.isnan(x)]

    # 确定最小样本数
    min_length = min(len(p1_filtered), len(p2_filtered))
    if st_samples:
        min_length = min(min_length, len(st_filtered))

    # 对齐数据长度
    p1_aligned = p1_filtered[:min_length]
    p2_aligned = p2_filtered[:min_length]
    st_aligned = st_filtered[:min_length] if st_samples else []

    # 数据信息
    data_info = {
        "original_p1_length": len(p1_samples),
        "original_p2_length": len(p2_samples),
        "original_st_length": len(st_samples) if st_samples else 0,
        "filtered_p1_length": len(p1_filtered),
        "filtered_p2_length": len(p2_filtered),
        "filtered_st_length": len(st_filtered),
        "aligned_length": min_length,
        "p1_has_nan": len(p1_filtered) < len(p1_samples),
        "p2_has_nan": len(p2_filtered) < len(p2_samples),
        "st_has_nan": st_samples and len(st_filtered) < len(st_samples),
    }

    return p1_aligned, p2_aligned, st_aligned, data_info


def generate_data_warning(data_info, speed):
    """生成数据警告信息

    Args:
        data_info: 数据信息字典
        speed: 转速

    Returns:
        str: 警告信息，如果没有警告则返回空字符串
    """
    warnings = []

    # 检查数据长度
    if data_info["aligned_length"] < 10:
        warnings.append(f"转速 {speed} 的样本数较少（{data_info['aligned_length']}个）")

    # 检查空值
    if data_info["p1_has_nan"]:
        warnings.append(f"转速 {speed} 的P1面数据包含空值")
    if data_info["p2_has_nan"]:
        warnings.append(f"转速 {speed} 的P2面数据包含空值")
    if data_info["st_has_nan"]:
        warnings.append(f"转速 {speed} 的ST面数据包含空值")

    # 检查数据长度差异
    p1_p2_diff = abs(data_info["filtered_p1_length"] - data_info["filtered_p2_length"])
    if p1_p2_diff > 0:
        warnings.append(f"转速 {speed} 的P1和P2面数据长度不一致")

    return "; ".join(warnings) if warnings else ""
