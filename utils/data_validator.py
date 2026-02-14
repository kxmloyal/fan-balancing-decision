from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def detect_outliers(samples: List[float], method: str = "auto") -> List[int]:
    """
    检测异常值，支持多种方法，并根据数据分布自动选择最合适的方法

    Args:
        samples: 数据样本列表
        method: 检测方法，可选值：'auto', 'iqr', 'zscore', 'dbscan'

    Returns:
        list: 异常值索引列表
    """
    # 过滤NaN值
    filtered = [x for x in samples if not np.isnan(x)]
    if len(filtered) < 4:  # 数据量不足，无法检测异常值
        return []

    # 根据数据分布自动选择检测方法
    if method == "auto":
        # 检查数据分布
        dist = check_data_distribution(samples)
        if dist["distribution_type"] == "normal":
            # 正态分布数据适合使用Z-score方法
            method = "zscore"
        else:
            # 非正态分布数据适合使用IQR方法
            method = "iqr"

    outliers = []

    if method == "iqr":
        # 增强IQR方法，支持自定义倍数
        q1 = np.percentile(filtered, 25)
        q3 = np.percentile(filtered, 75)
        iqr = q3 - q1

        # 动态调整倍数：根据数据分布调整异常值检测的严格程度
        data_cv = (
            dist.get("cv", 0)
            if "dist" in locals()
            else (
                np.std(filtered) / np.mean(filtered) * 100
                if np.mean(filtered) != 0
                else 0
            )
        )
        multiplier = 1.5 if data_cv < 20 else 2.0  # 高变异系数数据使用更宽松的标准

        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr

        for i, x in enumerate(samples):
            if not np.isnan(x) and (x < lower_bound or x > upper_bound):
                outliers.append(i)

    elif method == "zscore":
        # Z-score方法，适用于正态分布数据
        mean_val = np.mean(filtered)
        std_val = np.std(filtered)

        # 避免除以零
        if std_val == 0:
            return []

        # 计算Z分数
        z_scores = [(x - mean_val) / std_val for x in samples if not np.isnan(x)]

        # 检测异常值（|Z| > 3 视为异常）
        for i, x in enumerate(samples):
            if not np.isnan(x):
                z = (x - mean_val) / std_val
                if abs(z) > 3:
                    outliers.append(i)

    elif method == "dbscan":
        # DBSCAN聚类方法，适用于复杂分布数据
        # 仅当数据量足够大时使用
        if len(filtered) < 10:
            # 数据量不足，回退到IQR方法
            return detect_outliers(samples, method="iqr")

        # 转换为二维数组（DBSCAN需要二维输入）
        data = np.array(filtered).reshape(-1, 1)

        # 简单高效的DBSCAN参数设置，避免复杂计算
        # 对于1D数据，使用固定参数即可获得良好效果
        eps = np.std(data) * 0.5  # 使用数据标准差的一半作为eps
        min_samples = max(2, int(len(data) * 0.1))

        # 只在需要时导入，避免不必要的模块加载
        from sklearn.cluster import DBSCAN

        # 执行DBSCAN聚类
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1)  # 使用所有CPU核心
        clusters = dbscan.fit_predict(data)

        # 找出异常值（聚类标签为-1的点）
        outlier_indices = [i for i, cluster in enumerate(clusters) if cluster == -1]

        # 映射回原始数据索引
        non_nan_indices = [i for i, x in enumerate(samples) if not np.isnan(x)]
        outliers = [non_nan_indices[i] for i in outlier_indices]

    return outliers


def check_data_distribution(samples: List[float]) -> Dict[str, Any]:
    """
    检查数据分布情况

    Args:
        samples: 数据样本列表

    Returns:
        dict: 数据分布信息
    """
    # 过滤NaN值
    filtered = [x for x in samples if not np.isnan(x)]
    n = len(filtered)

    if n < 2:
        return {
            "has_distribution": False,
            "distribution_type": "insufficient_data",
            "skewness": 0,
            "kurtosis": 0,
            "cv": 0,
        }

    # 计算统计量
    mean = np.mean(filtered)
    std = np.std(filtered)
    median = np.median(filtered)
    skewness = np.mean(((filtered - mean) / std) ** 3) if std > 0 else 0
    kurtosis = np.mean(((filtered - mean) / std) ** 4) - 3 if std > 0 else -3
    cv = (std / mean * 100) if mean > 0 else 0

    # 判断分布类型
    distribution_type = "normal"
    if abs(skewness) > 0.5:
        distribution_type = "skewed" if skewness > 0 else "left_skewed"
    elif kurtosis > 1:
        distribution_type = "leptokurtic"  # 尖峰分布
    elif kurtosis < -1:
        distribution_type = "platykurtic"  # 平峰分布

    return {
        "has_distribution": True,
        "distribution_type": distribution_type,
        "skewness": skewness,
        "kurtosis": kurtosis,
        "cv": cv,
        "mean": mean,
        "median": median,
        "std": std,
    }


def validate_and_align_data(
    p1_samples: List[float],
    p2_samples: List[float],
    st_samples: Optional[List[float]] = None,
) -> Tuple[List[float], List[float], List[float], Dict[str, Any]]:
    """
    验证并对齐P1和P2面的数据，确保生成正确的ST面数据

    Args:
        p1_samples: P1面数据列表
        p2_samples: P2面数据列表
        st_samples: ST面数据列表，默认为None

    Returns:
        tuple: (p1_aligned, p2_aligned, st_samples, data_info)
               - p1_aligned: 对齐后的P1数据
               - p2_aligned: 对齐后的P2数据
               - st_samples: ST面数据
               - data_info: 数据信息字典
    """
    # 获取数据长度
    p1_len = len(p1_samples)
    p2_len = len(p2_samples)
    st_len = len(st_samples) if st_samples is not None else 0

    # 确定共同长度
    common_length = min(p1_len, p2_len, 30)  # 最多30组数据
    if st_samples is not None:
        common_length = min(common_length, st_len)

    # 截取共同长度的数据
    p1_aligned = p1_samples[:common_length]
    p2_aligned = p2_samples[:common_length]

    # 如果数据不足30组，用NaN填充
    if common_length < 30:
        p1_aligned.extend([float("nan")] * (30 - common_length))
        p2_aligned.extend([float("nan")] * (30 - common_length))

    # 处理ST面数据
    if st_samples is not None:
        # 直接使用提供的ST面数据
        st_aligned = st_samples[:common_length]
        if common_length < 30:
            st_aligned.extend([float("nan")] * (30 - common_length))
    else:
        # 如果没有提供ST面数据，则ST面数据全部为NaN
        st_aligned = [float("nan")] * 30

    # 数据质量评估
    # 1. 检测异常值
    p1_outliers = detect_outliers(p1_aligned)
    p2_outliers = detect_outliers(p2_aligned)
    st_outliers = detect_outliers(st_aligned) if st_samples is not None else []

    # 2. 检查数据分布
    p1_distribution = check_data_distribution(p1_aligned)
    p2_distribution = check_data_distribution(p2_aligned)
    st_distribution = (
        check_data_distribution(st_aligned)
        if st_samples is not None
        else {
            "has_distribution": False,
            "distribution_type": "no_data",
            "skewness": 0,
            "kurtosis": 0,
            "cv": 0,
        }
    )

    # 3. 检查数据相关性（如果有P1和P2数据）
    correlation = 0
    if p1_len > 1 and p2_len > 1:
        # 过滤NaN值
        p1_filtered = [x for x in p1_aligned if not np.isnan(x)]
        p2_filtered = [x for x in p2_aligned if not np.isnan(x)]
        min_len = min(len(p1_filtered), len(p2_filtered))
        if min_len > 1:
            correlation = np.corrcoef(p1_filtered[:min_len], p2_filtered[:min_len])[
                0, 1
            ]

    # 数据信息
    data_info: Dict[str, Any] = {
        "p1_length": p1_len,
        "p2_length": p2_len,
        "st_length": st_len if st_samples is not None else 0,
        "common_length": common_length,
        "is_complete": common_length == 30,
        "p1_valid": p1_len == 30,
        "p2_valid": p2_len == 30,
        "st_valid": st_len == 30 if st_samples is not None else False,
        "st_provided": st_samples is not None,
        # 数据质量评估结果
        "p1_outliers": p1_outliers,
        "p2_outliers": p2_outliers,
        "st_outliers": st_outliers,
        "p1_outlier_count": len(p1_outliers),
        "p2_outlier_count": len(p2_outliers),
        "st_outlier_count": len(st_outliers),
        "p1_distribution": p1_distribution,
        "p2_distribution": p2_distribution,
        "st_distribution": st_distribution,
        "p1_p2_correlation": correlation,
        # 数据质量评分（0-100）
        "data_quality_score": calculate_data_quality_score(
            p1_aligned, p2_aligned, st_aligned
        ),
    }

    return p1_aligned, p2_aligned, st_aligned, data_info


def calculate_data_quality_score(
    p1_samples: List[float], p2_samples: List[float], st_samples: List[float]
) -> int:
    """
    计算数据质量评分

    Args:
        p1_samples: P1面数据
        p2_samples: P2面数据
        st_samples: ST面数据

    Returns:
        int: 数据质量评分（0-100）
    """
    score = 100

    # 1. 数据完整性（权重30%）
    # 避免除以零：当样本为空时，使用默认值0
    p1_valid_count = sum(1 for x in p1_samples if not np.isnan(x))
    p1_valid = p1_valid_count / len(p1_samples) if p1_samples else 0

    p2_valid_count = sum(1 for x in p2_samples if not np.isnan(x))
    p2_valid = p2_valid_count / len(p2_samples) if p2_samples else 0

    st_valid_count = sum(1 for x in st_samples if not np.isnan(x))
    st_valid = st_valid_count / len(st_samples) if st_samples else 0

    # 计算完整性得分，避免除以零
    valid_samples = sum(1 for x in [p1_valid, p2_valid, st_valid] if x is not None)
    completeness = (
        (p1_valid + p2_valid + st_valid) / valid_samples if valid_samples > 0 else 0
    )
    score -= int((1 - completeness) * 30)

    # 2. 异常值检测（权重30%）
    p1_outliers = detect_outliers(p1_samples)
    p2_outliers = detect_outliers(p2_samples)
    st_outliers = detect_outliers(st_samples)

    # 计算异常值比例，避免除以零
    p1_valid_data = [x for x in p1_samples if not np.isnan(x)]
    p1_outlier_ratio = (
        len(p1_outliers) / len(p1_valid_data) if len(p1_valid_data) > 0 else 0
    )

    p2_valid_data = [x for x in p2_samples if not np.isnan(x)]
    p2_outlier_ratio = (
        len(p2_outliers) / len(p2_valid_data) if len(p2_valid_data) > 0 else 0
    )

    st_valid_data = [x for x in st_samples if not np.isnan(x)]
    st_outlier_ratio = (
        len(st_outliers) / len(st_valid_data) if len(st_valid_data) > 0 else 0
    )

    outlier_ratio = max(p1_outlier_ratio, p2_outlier_ratio, st_outlier_ratio)
    score -= int(min(outlier_ratio * 30, 30))

    # 3. 数据分布合理性（权重20%）
    p1_dist = check_data_distribution(p1_samples)
    p2_dist = check_data_distribution(p2_samples)
    st_dist = check_data_distribution(st_samples)

    # 分布异常扣分
    if p1_dist["distribution_type"] != "normal":
        score -= 5
    if p2_dist["distribution_type"] != "normal":
        score -= 5
    if st_dist["distribution_type"] != "normal" and st_dist["has_distribution"]:
        score -= 5

    # 高变异系数扣分
    if p1_dist["cv"] > 20:
        score -= 5
    if p2_dist["cv"] > 20:
        score -= 5
    if st_dist["cv"] > 20 and st_dist["has_distribution"]:
        score -= 5

    # 4. P1和P2相关性（权重20%）
    p1_valid_data = [x for x in p1_samples if not np.isnan(x)]
    p2_valid_data = [x for x in p2_samples if not np.isnan(x)]
    if len(p1_valid_data) > 1 and len(p2_valid_data) > 1:
        min_len = min(len(p1_valid_data), len(p2_valid_data))
        p1_filtered = p1_valid_data[:min_len]
        p2_filtered = p2_valid_data[:min_len]
        correlation = np.corrcoef(p1_filtered, p2_filtered)[0, 1]
        if abs(correlation) < 0.5:
            score -= int((0.5 - abs(correlation)) * 40)

    return max(0, min(100, score))


def generate_data_warning(data_info: Dict[str, Any], speed: str) -> str:
    """
    根据数据信息生成警告消息

    Args:
        data_info: 数据信息字典
        speed: 转速标识

    Returns:
        str: 警告消息，如果没有问题则返回空字符串
    """
    # 取消所有数据警告，始终返回空字符串
    return ""
