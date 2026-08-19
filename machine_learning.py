from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def _sanitize_metrics(d: Dict[str, Any]) -> Dict[str, Any]:
    """替换 dict 中的 NaN/Inf 为 None，防止 JSON 序列化失败"""
    for k, v in d.items():
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            d[k] = None
        elif isinstance(v, dict):
            _sanitize_metrics(v)
    return d


# ========== 机器学习模型包装类 ==========
class MLModel:
    """
    机器学习模型包装类，支持多种回归模型
    """

    def __init__(self, model_type: str = "linear"):
        """
        初始化模型

        Args:
            model_type: 模型类型，可选值：'linear', 'ridge', 'random_forest',
            'gradient_boosting'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.metrics = {}

        # 初始化模型
        if model_type == "linear":
            self.model = LinearRegression()
        elif model_type == "ridge":
            self.model = Ridge(alpha=1.0)
        elif model_type == "random_forest":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(
                n_estimators=100, learning_rate=0.1, random_state=42
            )
        else:
            raise ValueError(f"不支持的模型类型：{model_type}")

    def train(self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2) -> Dict[str, float]:
        """
        训练模型

        Args:
            X: 特征数据
            y: 目标变量
            test_size: 测试集比例

        Returns:
            dict: 模型评估指标
        """
        # 确保训练集非空
        n_samples = len(X)
        if n_samples < 2:
            # 数据量不足，返回默认指标
            return {
                "train_r2": 0.0,
                "test_r2": 0.0,
                "train_mse": 0.0,
                "test_mse": 0.0,
                "train_rmse": 0.0,
                "test_rmse": 0.0,
            }

        # 确保测试集大小合理
        n_test = max(1, min(int(n_samples * test_size), n_samples - 1))
        test_size = n_test / n_samples

        # 标准化特征
        self.scaler = StandardScaler()
        X = self.scaler.fit_transform(X)

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, shuffle=False
        )

        # 确保训练集非空
        if len(X_train) == 0:
            return {
                "train_r2": 0.0,
                "test_r2": 0.0,
                "train_mse": 0.0,
                "test_mse": 0.0,
                "train_rmse": 0.0,
                "test_rmse": 0.0,
            }

        # 训练模型
        self.model.fit(X_train, y_train)

        # 评估模型
        y_train_pred = self.model.predict(X_train)
        y_test_pred = self.model.predict(X_test)

        # 计算评估指标
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        train_mse = mean_squared_error(y_train, y_train_pred)
        test_mse = mean_squared_error(y_test, y_test_pred)

        # 保存评估指标
        self.metrics = {
            "train_r2": train_r2,
            "test_r2": test_r2,
            "train_mse": train_mse,
            "test_mse": test_mse,
            "train_rmse": np.sqrt(train_mse),
            "test_rmse": np.sqrt(test_mse),
        }

        self.is_trained = True

        return self.metrics

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        使用训练好的模型进行预测

        Args:
            X: 输入特征数据

        Returns:
            np.ndarray: 预测结果
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")

        if self.scaler is not None:
            X = self.scaler.transform(X)

        return self.model.predict(X)


# ========== 趋势预测函数 ==========
def predict_trend(
    historical_data: List[Dict[str, Any]],
    prediction_days: int = 7,
    model_type: str = "random_forest",
) -> Dict[str, Any]:
    """
    基于历史数据预测未来趋势

    Args:
        historical_data: 历史数据，包含日期和数值
        prediction_days: 预测天数
        model_type: 模型类型

    Returns:
        dict: 预测结果，包含历史数据、预测数据和模型评估指标
    """
    df = pd.DataFrame(historical_data)

    # 尝试解析日期 → 失败时使用序数编码（支持 "2800rpm" 等非日期格式）
    use_ordinal = False
    try:
        df["_date_dt"] = pd.to_datetime(df["date"])
        df = df.sort_values("_date_dt")
        df["day_of_week"] = df["_date_dt"].dt.dayofweek
        df["month"] = df["_date_dt"].dt.month
        df["day_of_year"] = df["_date_dt"].dt.dayofyear
    except (ValueError, TypeError):
        use_ordinal = True
        df = df.reset_index(drop=True)
        df["_ordinal"] = range(1, len(df) + 1)

    # 添加滞后特征
    for i in range(1, 4):
        df[f"lag_{i}"] = df["value"].shift(i)

    df = df.dropna()

    if use_ordinal:
        features = ["_ordinal", "lag_1", "lag_2", "lag_3"]
        future_start = int(df["_ordinal"].max()) + 1
    else:
        features = ["day_of_week", "month", "day_of_year", "lag_1", "lag_2", "lag_3"]

    # 数据量不足 → 简单平均
    if len(df) < 3:
        avg_value = float(df["value"].mean()) if len(df) > 0 else 0.0
        future_predictions = [{"date": f"预测{i + 1}", "value": avg_value} for i in range(prediction_days)]
        return _sanitize_metrics({
            "historical_data": df[["date", "value"]].to_dict("records"),
            "prediction_data": future_predictions,
            "model_metrics": {"method": "simple_average", "avg_value": avg_value, "n_samples": len(df)},
            "model_type": "simple_average",
            "prediction_days": prediction_days,
        })

    X = df[features].values
    y = df["value"].values

    model = MLModel(model_type=model_type)
    metrics = _sanitize_metrics(model.train(X, y))

    # 生成预测
    last_values = df["value"].tail(3).tolist()
    if len(last_values) < 3:
        last_values = [last_values[-1]] * 3
    last_values = last_values[::-1]

    future_predictions = []
    current_lags = list(last_values)
    base_ordinal = future_start if use_ordinal else 0
    last_date_dt = df["_date_dt"].max() if not use_ordinal else None

    for step in range(prediction_days):
        if use_ordinal:
            sample = np.array([[base_ordinal + step + 1, current_lags[0], current_lags[1], current_lags[2]]])
        else:
            next_date = last_date_dt + pd.Timedelta(days=step + 1)
            sample = np.array([[next_date.dayofweek, next_date.month, next_date.dayofyear, current_lags[0], current_lags[1], current_lags[2]]])

        pred = float(model.predict(sample)[0])
        future_predictions.append({"date": f"预测{step + 1}", "value": pred})
        current_lags = current_lags[1:] + [pred]

    return _sanitize_metrics({
        "historical_data": df[["date", "value"]].to_dict("records"),
        "prediction_data": future_predictions,
        "model_metrics": metrics,
        "model_type": model_type,
        "prediction_days": prediction_days,
    })


# ========== 关键指标预测函数 ==========
def predict_key_metrics(
    historical_metrics: List[Dict[str, Any]],
    prediction_periods: int = 12,
    model_type: str = "gradient_boosting",
) -> Dict[str, Any]:
    """
    基于历史指标数据预测未来关键指标

    Args:
        historical_metrics: 历史指标数据
        prediction_periods: 预测周期数
        model_type: 模型类型

    Returns:
        dict: 预测结果
    """
    # 转换为DataFrame
    df = pd.DataFrame(historical_metrics)

    # 如果数据量不足，使用简单平均预测
    if len(df) < 5:
        # 准备特征和目标变量
        metrics = [col for col in df.columns if col not in ["date"]]

        predictions = {}
        metrics_results = {}

        # 对每个指标进行预测
        for metric in metrics:
            # 使用简单的平均预测
            avg_value = df[metric].mean()

            # 生成预测
            future_predictions = [avg_value for _ in range(prediction_periods)]

            # 保存结果
            predictions[metric] = future_predictions
            metrics_results[metric] = {
                "method": "simple_average",
                "avg_value": float(avg_value),
                "n_samples": len(df),
            }

        # 构建结果
        result = _sanitize_metrics({
            "historical_data": df.to_dict("records"),
            "predictions": predictions,
            "metrics_results": metrics_results,
            "model_type": "simple_average",
            "prediction_periods": prediction_periods,
        })

        return result

    # 准备特征和目标变量
    metrics = [col for col in df.columns if col not in ["date"]]

    predictions = {}
    metrics_results = {}

    # 对每个指标进行预测
    for metric in metrics:
        # 特征工程：添加滞后特征
        df_copy = df.copy()
        for i in range(1, 4):
            df_copy[f"lag_{i}"] = df_copy[metric].shift(i)

        # 删除包含NaN值的行
        df_copy = df_copy.dropna()

        if len(df_copy) < 5:
            # 数据量不足，使用简单平均预测
            avg_value = df_copy[metric].mean()
            future_predictions = [avg_value for _ in range(prediction_periods)]

            # 保存结果
            predictions[metric] = future_predictions
            metrics_results[metric] = {
                "method": "simple_average",
                "avg_value": float(avg_value),
                "n_samples": len(df_copy),
            }
        else:
            # 准备训练数据
            features = [f"lag_{i}" for i in range(1, 4)]
            X = df_copy[features].values
            y = df_copy[metric].values

            # 初始化并训练模型
            model = MLModel(model_type=model_type)
            metrics = model.train(X, y)

            # 生成预测数据
            last_values = df_copy[metric].tail(3).values[::-1]

            # 进行多步预测
            future_predictions = []
            current_lags = list(last_values)

            for _ in range(prediction_periods):
                # 使用当前滞后值进行预测
                X_future = np.array([current_lags]).reshape(1, -1)
                pred = model.predict(X_future)[0]

                # 添加到预测结果
                future_predictions.append(pred)

                # 更新滞后值
                current_lags = current_lags[1:] + [pred]

            # 保存结果
            predictions[metric] = [float(pred) for pred in future_predictions]
            metrics_results[metric] = metrics

    # 构建结果
    result = _sanitize_metrics({
        "historical_data": df.to_dict("records"),
        "predictions": predictions,
        "metrics_results": metrics_results,
        "model_type": model_type,
        "prediction_periods": prediction_periods,
    })

    return result


# ========== 多维度数据分析函数 ==========
def multi_dimensional_analysis(
    data: List[Dict[str, Any]], dimensions: List[str], metrics: List[str]
) -> Dict[str, Any]:
    """
    多维度数据分析

    Args:
        data: 输入数据
        dimensions: 分析维度
        metrics: 分析指标

    Returns:
        dict: 分析结果
    """
    # 转换为DataFrame
    df = pd.DataFrame(data)

    # 确保维度和指标存在于数据中
    for dim in dimensions:
        if dim not in df.columns:
            raise ValueError(f"维度 {dim} 不存在于数据中")

    for metric in metrics:
        if metric not in df.columns:
            raise ValueError(f"指标 {metric} 不存在于数据中")

    # 计算统计量
    analysis_result = {
        "dimensions": dimensions,
        "metrics": metrics,
        "summary": {},
        "detailed": [],
    }

    # 计算整体统计量
    overall_stats = {}
    for metric in metrics:
        values = pd.to_numeric(df[metric], errors="coerce").dropna()
        if len(values) == 0:
            overall_stats[metric] = {
                "mean": 0,
                "median": 0,
                "std": 0,
                "min": 0,
                "max": 0,
                "count": 0,
            }
            continue
        overall_stats[metric] = {
            "mean": float(values.mean()),
            "median": float(values.median()),
            "std": float(values.std()),
            "min": float(values.min()),
            "max": float(values.max()),
            "count": int(values.count()),
        }

    analysis_result["summary"]["overall"] = overall_stats

    # 使用Python字典手动实现分组，避免groupby的类型问题
    # 分组键 -> 该组的数据列表
    groups = {}

    for _, row in df.iterrows():
        if len(dimensions) == 1:
            group_key = row[dimensions[0]]
        else:
            group_key = tuple(row[dim] for dim in dimensions)

        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(row)

    for group_key, group_rows in groups.items():
        group_df = pd.DataFrame(group_rows)

        detailed_entry = {}

        if len(dimensions) == 1:
            detailed_entry[dimensions[0]] = str(group_key)
        else:
            for i, dim in enumerate(dimensions):
                detailed_entry[dim] = str(group_key[i])

        group_stats = {}
        for metric in metrics:
            metric_values = pd.to_numeric(group_df[metric], errors="coerce").dropna()
            if len(metric_values) == 0:
                group_stats[metric] = {
                    "mean": 0,
                    "median": 0,
                    "std": 0,
                    "min": 0,
                    "max": 0,
                    "count": 0,
                }
                continue
            metric_std = float(metric_values.std()) if len(metric_values) >= 2 else 0.0
            group_stats[metric] = {
                "mean": float(metric_values.mean()),
                "median": float(metric_values.median()),
                "std": metric_std,
                "min": float(metric_values.min()),
                "max": float(metric_values.max()),
                "count": int(len(metric_values)),
            }

        analysis_result["summary"][str(group_key)] = group_stats

        for metric in metrics:
            detailed_entry[f"{metric}_mean"] = group_stats[metric]["mean"]
            detailed_entry[f"{metric}_median"] = group_stats[metric]["median"]
            detailed_entry[f"{metric}_std"] = group_stats[metric]["std"]
            detailed_entry[f"{metric}_count"] = group_stats[metric]["count"]

        analysis_result["detailed"].append(detailed_entry)

    return analysis_result


# ========== 异常模式检测函数 ==========
def detect_anomaly_patterns(
    data: List[Dict[str, Any]], window_size: int = 7, threshold: float = 2.0
) -> List[Dict[str, Any]]:
    """
    检测时间序列数据中的异常模式

    Args:
        data: 时间序列数据 [{date, value}, ...]
        window_size: 滑动窗口大小
        threshold: 异常检测阈值

    Returns:
        list: 异常模式列表
    """
    df = pd.DataFrame(data)

    if "date" in df.columns and "value" in df.columns:
        # 尝试解析日期 → 失败时保持原始 date 字符串
        try:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")
        except (ValueError, TypeError):
            pass

    # 计算滑动窗口统计量
    df["rolling_mean"] = df["value"].rolling(window=min(window_size, len(df)), min_periods=2).mean()
    df["rolling_std"] = df["value"].rolling(window=min(window_size, len(df)), min_periods=2).std()

    # 计算Z分数
    df["z_score"] = (df["value"] - df["rolling_mean"]) / df["rolling_std"]

    valid_mask = df["z_score"].notna() & ~np.isinf(df["z_score"])
    df["z_score"] = df["z_score"].where(valid_mask, 0.0)

    n_valid = valid_mask.sum()
    if n_valid < 2:
        return []

    # 检测异常
    anomalies = df[abs(df["z_score"]) > threshold]

    anomaly_list = []
    for _, row in anomalies.iterrows():
        item = {"date": str(row["date"]), "value": float(row["value"]), "z_score": float(row["z_score"])}
        item["anomaly_type"] = "high" if item["z_score"] > threshold else "low"
        anomaly_list.append(item)

    return anomaly_list


def detect_outliers_iqr(data: List[float]) -> Dict[str, Any]:
    """
    使用 IQR 方法检测异常值（适用于小样本场景）

    Args:
        data: 数值列表

    Returns:
        dict: 异常值检测结果，包含异常值列表、边界值和IQR
    """
    if not data or len(data) < 4:
        return {
            "outliers": [],
            "lower_bound": None,
            "upper_bound": None,
            "iqr": None,
            "q1": None,
            "q3": None,
        }

    arr = np.array(data, dtype=float)
    q1 = float(np.percentile(arr, 25))
    q3 = float(np.percentile(arr, 75))
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = [float(x) for x in arr if x < lower_bound or x > upper_bound]

    return {
        "outliers": outliers,
        "outlier_count": len(outliers),
        "total_count": len(data),
        "outlier_ratio": round(len(outliers) / len(data), 4),
        "lower_bound": round(lower_bound, 6),
        "upper_bound": round(upper_bound, 6),
        "iqr": round(iqr, 6),
        "q1": round(q1, 6),
        "q3": round(q3, 6),
    }


def cluster_balance_data(
    surface_data: List[Dict[str, Any]], n_clusters: int = 3, random_state: int = 42
) -> Dict[str, Any]:
    """
    对平衡面测量数据进行 KMeans 聚类分析

    基于 P1/P2 面的中位数和标准差构建 4 维特征向量进行聚类，
    适用于将不同转速/条件下的测量数据分组为相似工艺组。

    Args:
        surface_data: 平衡面数据列表，每项包含 speed/p1_samples/p2_samples
        n_clusters: 聚类数量
        random_state: 随机种子

    Returns:
        dict: 聚类结果，包含标签、中心点、特征和转速标注
    """
    features = []
    speed_labels = []
    valid_indices = []

    for i, item in enumerate(surface_data):
        p1_samples = item.get("p1_samples", [])
        p2_samples = item.get("p2_samples", [])

        if not p1_samples and not p2_samples:
            continue

        p1_med = float(np.median(p1_samples)) if p1_samples else 0.0
        p1_std = float(np.std(p1_samples)) if len(p1_samples) >= 2 else 0.0
        p2_med = float(np.median(p2_samples)) if p2_samples else 0.0
        p2_std = float(np.std(p2_samples)) if len(p2_samples) >= 2 else 0.0

        features.append([p1_med, p1_std, p2_med, p2_std])
        speed_labels.append(str(item.get("speed", f"item_{i}")))
        valid_indices.append(i)

    if len(features) < 2:
        return {"clusters": [], "speed_labels": [], "error": "数据量不足，至少需要2组以上有效数据"}

    actual_clusters = min(n_clusters, len(features))
    if actual_clusters < n_clusters:
        n_clusters = actual_clusters

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    cluster_labels = kmeans.fit_predict(scaled_features)

    centers_orig = scaler.inverse_transform(kmeans.cluster_centers_)
    cluster_centers = []
    for center in centers_orig:
        cluster_centers.append(
            {
                "p1_median": round(float(center[0]), 6),
                "p1_std": round(float(center[1]), 6),
                "p2_median": round(float(center[2]), 6),
                "p2_std": round(float(center[3]), 6),
            }
        )

    inertia = float(kmeans.inertia_)

    cluster_summary = {}
    for label in range(n_clusters):
        members = [
            speed_labels[i] for i in range(len(cluster_labels)) if cluster_labels[i] == label
        ]
        cluster_summary[str(label)] = {
            "count": len(members),
            "members": members,
        }

    return {
        "clusters": [int(c) for c in cluster_labels],
        "cluster_centers": cluster_centers,
        "speed_labels": speed_labels,
        "inertia": round(inertia, 6),
        "n_clusters": n_clusters,
        "cluster_summary": cluster_summary,
    }


def analyze_balance_data(
    balance_records: List[Dict[str, Any]],
    fan_model: str = "",
) -> Dict[str, Any]:
    """
    平衡数据综合 ML 分析——一次调用完成趋势+聚类+异常三合一分析

    Args:
        balance_records: 平衡测量记录列表，每项含 speed/p1_samples/p2_samples/p1_value/p2_value/st_value
        fan_model: 扇叶型号（元数据标注）

    Returns:
        dict: 综合分析结果，包含 trend/cluster/anomaly 三个子结果
    """
    if not balance_records:
        return {"error": "无有效数据", "fan_model": fan_model}

    result = {"fan_model": fan_model, "n_records": len(balance_records)}

    cluster_result = cluster_balance_data(balance_records)
    result["cluster_analysis"] = cluster_result

    anomaly_records = []
    for rec in balance_records:
        for face in ["p1", "p2", "st"]:
            samples_key = f"{face}_samples"
            samples = rec.get(samples_key, [])
            if samples:
                iqr_result = detect_outliers_iqr(samples)
                if iqr_result["outliers"]:
                    anomaly_records.append(
                        {
                            "speed": str(rec.get("speed", "")),
                            "surface": face.upper(),
                            "anomalies": iqr_result["outliers"],
                            "outlier_ratio": iqr_result["outlier_ratio"],
                            "iqr": iqr_result["iqr"],
                        }
                    )
    result["anomaly_analysis"] = {
        "total_anomalies": len(anomaly_records),
        "anomaly_details": anomaly_records,
        "method": "IQR_1.5x",
    }

    today = datetime.now().date()
    trend_data = []
    for i, rec in enumerate(balance_records):
        p1_val = rec.get("p1_value")
        p2_val = rec.get("p2_value")
        st_val = rec.get("st_value")

        available = [v for v in [p1_val, p2_val, st_val] if v is not None]
        if available:
            value = float(np.mean(available))
        else:
            value = 0.0

        trend_data.append(
            {
                "date": (today - timedelta(days=len(balance_records) - 1 - i)).strftime("%Y-%m-%d"),
                "value": value,
            }
        )

    trend_result = predict_trend(trend_data)
    result["trend_analysis"] = trend_result

    return result
