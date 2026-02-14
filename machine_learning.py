import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# ========== 机器学习模型包装类 ==========
class MLModel:
    """
    机器学习模型包装类，支持多种回归模型
    """

    def __init__(self, model_type: str = "linear"):
        """
        初始化模型

        Args:
            model_type: 模型类型，可选值：'linear', 'ridge', 'random_forest', 'gradient_boosting'
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

    def train(
        self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2
    ) -> Dict[str, float]:
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

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
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
    # 转换为DataFrame
    df = pd.DataFrame(historical_data)

    # 确保日期列是datetime类型
    df["date"] = pd.to_datetime(df["date"])

    # 按日期排序
    df = df.sort_values("date")

    # 特征工程：添加时间序列特征
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear

    # 添加滞后特征
    for i in range(1, 4):
        df[f"lag_{i}"] = df["value"].shift(i)

    # 删除包含NaN值的行
    df = df.dropna()

    # 如果数据量不足，使用简单平均预测
    if len(df) < 5:
        avg_value = df["value"].mean()

        # 准备预测数据
        last_date = df["date"].max()
        future_dates = [
            last_date + pd.Timedelta(days=i + 1) for i in range(prediction_days)
        ]

        # 使用平均值进行预测
        future_predictions = [avg_value for _ in range(prediction_days)]

        # 构建结果
        result = {
            "historical_data": df[["date", "value"]].to_dict("records"),
            "prediction_data": [
                {"date": date.strftime("%Y-%m-%d"), "value": float(pred)}
                for date, pred in zip(future_dates, future_predictions)
            ],
            "model_metrics": {
                "method": "simple_average",
                "avg_value": float(avg_value),
                "n_samples": len(df),
            },
            "model_type": "simple_average",
            "prediction_days": prediction_days,
        }

        return result

    # 准备训练数据
    features = ["day_of_week", "month", "day_of_year", "lag_1", "lag_2", "lag_3"]
    X = df[features].values
    y = df["value"].values

    # 初始化并训练模型
    model = MLModel(model_type=model_type)
    metrics = model.train(X, y)

    # 准备预测数据
    last_date = df["date"].max()
    future_dates = [
        last_date + pd.Timedelta(days=i + 1) for i in range(prediction_days)
    ]

    # 生成预测特征
    future_df = pd.DataFrame({"date": future_dates})
    future_df["day_of_week"] = future_df["date"].dt.dayofweek
    future_df["month"] = future_df["date"].dt.month
    future_df["day_of_year"] = future_df["date"].dt.dayofyear

    # 使用最近的历史值作为滞后特征
    for i in range(1, 4):
        future_df[f"lag_{i}"] = df["value"].iloc[-i]

    # 进行预测
    X_future = future_df[features].values
    future_predictions = model.predict(X_future)

    # 构建结果
    result = {
        "historical_data": df[["date", "value"]].to_dict("records"),
        "prediction_data": [
            {"date": date.strftime("%Y-%m-%d"), "value": float(pred)}
            for date, pred in zip(future_dates, future_predictions)
        ],
        "model_metrics": metrics,
        "model_type": model_type,
        "prediction_days": prediction_days,
    }

    return result


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
        result = {
            "historical_data": df.to_dict("records"),
            "predictions": predictions,
            "metrics_results": metrics_results,
            "model_type": "simple_average",
            "prediction_periods": prediction_periods,
        }

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
    result = {
        "historical_data": df.to_dict("records"),
        "predictions": predictions,
        "metrics_results": metrics_results,
        "model_type": model_type,
        "prediction_periods": prediction_periods,
    }

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
        overall_stats[metric] = {
            "mean": float(df[metric].mean()),
            "median": float(df[metric].median()),
            "std": float(df[metric].std()),
            "min": float(df[metric].min()),
            "max": float(df[metric].max()),
            "count": int(df[metric].count()),
        }

    analysis_result["summary"]["overall"] = overall_stats

    # 使用Python字典手动实现分组，避免groupby的类型问题
    # 分组键 -> 该组的数据列表
    groups = {}

    for _, row in df.iterrows():
        # 生成分组键
        if len(dimensions) == 1:
            group_key = str(row[dimensions[0]])
        else:
            group_key = tuple(str(row[dim]) for dim in dimensions)
            group_key = "_".join(group_key)

        # 将数据添加到对应分组
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(row)

    # 对每个分组计算统计量
    for group_key, group_rows in groups.items():
        # 将分组数据转换为DataFrame
        group_df = pd.DataFrame(group_rows)

        # 创建详细数据条目
        detailed_entry = {}

        # 填充维度值
        if len(dimensions) == 1:
            detailed_entry[dimensions[0]] = group_key
        else:
            # 从group_key中解析出各维度值
            dimension_values = group_key.split("_")
            for i, dim in enumerate(dimensions):
                detailed_entry[dim] = dimension_values[i]

        # 计算分组统计量
        group_stats = {}
        for metric in metrics:
            metric_values = group_df[metric]
            group_stats[metric] = {
                "mean": float(metric_values.mean()),
                "median": float(metric_values.median()),
                "std": float(metric_values.std()),
                "min": float(metric_values.min()),
                "max": float(metric_values.max()),
                "count": int(metric_values.count()),
            }

        # 保存分组统计量
        analysis_result["summary"][group_key] = group_stats

        # 填充详细数据的统计量
        for metric in metrics:
            detailed_entry[f"{metric}_mean"] = group_stats[metric]["mean"]
            detailed_entry[f"{metric}_median"] = group_stats[metric]["median"]
            detailed_entry[f"{metric}_std"] = group_stats[metric]["std"]
            detailed_entry[f"{metric}_count"] = group_stats[metric]["count"]

        # 添加到详细数据列表
        analysis_result["detailed"].append(detailed_entry)

    return analysis_result


# ========== 异常模式检测函数 ==========
def detect_anomaly_patterns(
    data: List[Dict[str, Any]], window_size: int = 7, threshold: float = 2.0
) -> List[Dict[str, Any]]:
    """
    检测时间序列数据中的异常模式

    Args:
        data: 时间序列数据
        window_size: 滑动窗口大小
        threshold: 异常检测阈值

    Returns:
        list: 异常模式列表
    """
    # 转换为DataFrame
    df = pd.DataFrame(data)

    # 确保日期列是datetime类型
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

    # 计算滑动窗口统计量
    df["rolling_mean"] = df["value"].rolling(window=window_size).mean()
    df["rolling_std"] = df["value"].rolling(window=window_size).std()

    # 计算Z分数
    df["z_score"] = (df["value"] - df["rolling_mean"]) / df["rolling_std"]
    df["z_score"] = df["z_score"].fillna(0)  # 处理NaN值

    # 检测异常
    anomalies = df[abs(df["z_score"]) > threshold]

    # 转换为结果格式
    anomaly_list = anomalies.to_dict("records")

    # 添加异常类型
    for anomaly in anomaly_list:
        if anomaly["z_score"] > threshold:
            anomaly["anomaly_type"] = "high"
        else:
            anomaly["anomaly_type"] = "low"

    return anomaly_list
