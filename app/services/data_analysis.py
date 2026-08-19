#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据分析服务模块
提供高级数据分析功能，增强技能评估能力
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler


class DataAnalysisService:
    """
    数据分析服务类
    提供高级数据分析功能
    """

    def __init__(self):
        """初始化数据分析服务"""
        import scipy.stats as stats

        self.stats = stats

    def advanced_statistical_analysis(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        高级统计分析

        Args:
            data: 输入数据，包含转速和各面的不平衡量

        Returns:
            Dict: 高级统计分析结果
        """
        try:
            # 转换数据为DataFrame
            df = self._convert_to_dataframe(data)

            # 计算基本统计量
            basic_stats = self._calculate_basic_stats(df)

            # 计算高级统计量
            advanced_stats = self._calculate_advanced_stats(df)

            # 相关性分析
            correlation_analysis = self._calculate_correlations(df)

            # 分布分析
            distribution_analysis = self._analyze_distributions(df)

            return {
                "basic_stats": basic_stats,
                "advanced_stats": advanced_stats,
                "correlation_analysis": correlation_analysis,
                "distribution_analysis": distribution_analysis,
            }
        except Exception as e:
            raise Exception(f"高级统计分析失败：{str(e)}")

    def cluster_analysis(
        self, data: List[Dict[str, Any]], n_clusters: int = 3, auto_k: bool = True
    ) -> Dict[str, Any]:
        """
        聚类分析（支持Elbow方法自动确定K值）

        Args:
            data: 输入数据
            n_clusters: 聚类数量（当auto_k=False时使用）
            auto_k: 是否使用Elbow方法自动确定最优K值

        Returns:
            Dict: 聚类分析结果
        """
        try:
            df = self._convert_to_dataframe(data)

            features = df[["p1_value", "p2_value", "st_value"]].dropna()

            if len(features) == 0:
                return {"error": "没有足够的数据进行聚类分析"}

            max_clusters = min(5, len(features) - 1)
            if max_clusters < 2:
                return {"error": "样本量不足，无法聚类"}

            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(features)

            if auto_k and max_clusters >= 3:
                n_clusters = self._elbow_method(scaled_features, max_clusters)

            actual_clusters = min(n_clusters, max_clusters)
            if actual_clusters < 2:
                actual_clusters = 2

            kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(scaled_features)

            cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
            cluster_stats = []

            for i in range(actual_clusters):
                cluster_data = features[clusters == i]
                cluster_stats.append(
                    {
                        "cluster_id": i,
                        "size": len(cluster_data),
                        "center": cluster_centers[i].tolist(),
                        "mean": cluster_data.mean().to_dict(),
                        "std": cluster_data.std().to_dict(),
                    }
                )

            return {
                "n_clusters": actual_clusters,
                "cluster_stats": cluster_stats,
                "inertia": float(kmeans.inertia_),
                "k_selection_method": "Elbow自动" if auto_k else "手动指定",
            }
        except Exception as e:
            raise Exception(f"聚类分析失败：{str(e)}")

    @staticmethod
    def _elbow_method(scaled_features: np.ndarray, max_k: int) -> int:
        max_k = min(max_k, 10)
        inertias = []
        ks = range(1, max_k + 1)
        for k in ks:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(scaled_features)
            inertias.append(kmeans.inertia_)
        if len(inertias) < 3:
            return max_k

        deltas = [inertias[i - 1] - inertias[i] for i in range(1, len(inertias))]
        if len(deltas) < 2:
            return 2

        curvatures = []
        for i in range(1, len(deltas)):
            curvatures.append(deltas[i] - deltas[i - 1])

        best_k = 2
        min_curv = curvatures[0]
        for i, c in enumerate(curvatures):
            if c < min_curv:
                min_curv = c
                best_k = i + 2
        return best_k

    def dimensionality_reduction(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        维度 reduction 分析

        Args:
            data: 输入数据

        Returns:
            Dict: 维度 reduction 结果
        """
        try:
            df = self._convert_to_dataframe(data)

            # 准备特征数据
            features = df[["p1_value", "p2_value", "st_value"]].dropna()

            if len(features) < 3:
                return {"error": "数据量不足，无法进行维度 reduction"}

            # 标准化数据
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(features)

            # 执行PCA
            pca = PCA(n_components=2)
            principal_components = pca.fit_transform(scaled_features)

            return {
                "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
                "cumulative_explained_variance": np.cumsum(pca.explained_variance_ratio_).tolist(),
                "components": pca.components_.tolist(),
                "principal_components": principal_components.tolist(),
            }
        except Exception as e:
            raise Exception(f"维度 reduction 分析失败：{str(e)}")

    def anomaly_detection(
        self, data: List[Dict[str, Any]], threshold: float = 2.5
    ) -> Dict[str, Any]:
        """
        异常检测（自适应选择Z-score或Modified Z-score方法）

        自动根据数据正态性和样本量选择最优方法：
        - 大样本且正态分布 → 标准 Z-score
        - 小样本或非正态分布 → Modified Z-score (MAD)

        Args:
            data: 输入数据
            threshold: 异常检测阈值（默认2.5，平衡灵敏度和特异性）

        Returns:
            Dict: 异常检测结果
        """
        try:
            df = self._convert_to_dataframe(data)

            anomalies = {}

            for face in ["p1_value", "p2_value", "st_value"]:
                if face in df.columns:
                    face_data = df[face].dropna()
                    if len(face_data) > 3:
                        method, z_scores = self._compute_z_scores(face_data.values)

                        anomaly_indices = np.where(z_scores > threshold)[0]

                        if len(anomaly_indices) > 0:
                            total_samples = len(face_data)
                            anomaly_ratio = len(anomaly_indices) / total_samples
                            anomalies[face] = {
                                "anomaly_indices": anomaly_indices.tolist(),
                                "anomaly_values": face_data.iloc[anomaly_indices].tolist(),
                                "z_scores": z_scores[anomaly_indices].tolist(),
                                "anomaly_ratio": anomaly_ratio,
                                "detection_method": method,
                                "threshold": threshold,
                                "total_samples": total_samples,
                            }
                    else:
                        method, z_scores = self._compute_z_scores(face_data.values)
                        anomalies[face] = {
                            "anomaly_indices": [],
                            "anomaly_values": [],
                            "z_scores": [],
                            "anomaly_ratio": 0.0,
                            "detection_method": method,
                            "threshold": threshold,
                            "total_samples": int(len(face_data)),
                        }

            return anomalies
        except Exception as e:
            raise Exception(f"异常检测失败：{str(e)}")

    @staticmethod
    def _compute_z_scores(data: np.ndarray) -> tuple:
        n = len(data)
        if n >= 20:
            try:
                stat, p_value = stats.normaltest(data)
                is_normal = p_value > 0.05
            except Exception:
                is_normal = False
        else:
            is_normal = False

        if is_normal:
            z_scores = np.abs(stats.zscore(data))
            return "Z-score (正态)", z_scores

        median = np.median(data)
        mad = np.median(np.abs(data - median))
        if mad > 0:
            z_scores = 0.6745 * np.abs(data - median) / mad
            return "Modified Z-score (MAD)", z_scores

        mu = np.mean(data)
        sigma = np.std(data, ddof=1)
        if sigma > 0:
            z_scores = np.abs(data - mu) / sigma
            return "Z-score (回退)", z_scores

        return "无变异性", np.zeros_like(data)

    def trend_analysis(
        self, data: List[Dict[str, Any]], time_column: str = "speed"
    ) -> Dict[str, Any]:
        """
        趋势分析（使用实际转速数值作为X轴，同时进行线性+二次回归检验）

        Args:
            data: 输入数据
            time_column: 时间/顺序列

        Returns:
            Dict: 趋势分析结果
        """
        try:
            df = self._convert_to_dataframe(data)

            if len(df) == 0:
                return {}

            trends = {}

            for face in ["p1_value", "p2_value", "st_value"]:
                if face in df.columns:
                    face_data = df[[time_column, face]].dropna()
                    if len(face_data) < 5:
                        continue
                    if len(face_data) > 2:
                        x_raw = face_data[time_column]
                        x = self._extract_numeric_x(x_raw)
                        if x is None:
                            continue
                        y = face_data[face].values

                        model = LinearRegression()
                        model.fit(x, y)

                        slope = model.coef_[0]
                        intercept = float(model.intercept_)
                        y_pred = model.predict(x)
                        r_squared = float(model.score(x, y))

                        x_range = float(np.ptp(x)) if len(x) > 0 else 1.0
                        total_change = slope * x_range

                        y_mean = float(np.mean(y))
                        y_mean_abs = float(np.mean(np.abs(y)))
                        epsilon = np.finfo(float).eps
                        relative_change_pct = (
                            float(total_change / (y_mean_abs + epsilon) * 100)
                            if y_mean_abs > epsilon
                            else 0.0
                        )

                        if r_squared < 0.3:
                            trend_direction = "无显著趋势"
                        else:
                            trend_direction = (
                                "上升" if slope > 0 else "下降" if slope < 0 else "稳定"
                            )

                        trend = {
                            "slope": float(slope),
                            "slope_unit": f"每{self._infer_x_unit(x_raw)}",
                            "intercept": intercept,
                            "r_squared": r_squared,
                            "trend_direction": trend_direction,
                            "total_change": float(total_change),
                            "relative_change_pct": relative_change_pct,
                            "data_points": len(face_data),
                        }

                        quadratic_result = self._try_quadratic_fit(
                            x, y, y_pred, r_squared, y_mean, epsilon
                        )
                        if quadratic_result:
                            trend.update(quadratic_result)

                        trends[face] = trend

            return trends
        except Exception as e:
            raise Exception(f"趋势分析失败：{str(e)}")

    @staticmethod
    def _extract_numeric_x(x_raw: pd.Series) -> pd.Series:
        try:
            x = x_raw.astype(float).values.reshape(-1, 1)
            x_flat = x.ravel()
            nan_mask = np.isnan(x_flat)
            if nan_mask.any():
                x_flat = x_flat[~nan_mask]
                if len(x_flat) == 0:
                    return None
                x = x_flat.reshape(-1, 1)
            if np.ptp(x_flat) < np.finfo(float).eps:
                return None
            return x
        except (ValueError, TypeError):
            pass
        try:
            extracted = x_raw.astype(str).str.extract(r"(\d+\.?\d*)")[0]
            x = extracted.astype(float).values.reshape(-1, 1)
            x_flat = x.ravel()
            if np.isnan(x_flat).all() or np.ptp(x_flat[~np.isnan(x_flat)]) < np.finfo(float).eps:
                return None
            return x
        except Exception:
            pass
        try:
            x = x_raw.reset_index(drop=True).index.values.reshape(-1, 1)
            return x
        except Exception:
            return None

    @staticmethod
    def _infer_x_unit(x_raw: pd.Series) -> str:
        raw_str = str(x_raw.iloc[0]) if len(x_raw) > 0 else ""
        import re

        match = re.search(r"([A-Za-z]+)", raw_str)
        if match:
            return match.group(1)
        return "单位"

    @staticmethod
    def _try_quadratic_fit(
        x: np.ndarray,
        y: np.ndarray,
        y_linear_pred: np.ndarray,
        linear_r2: float,
        y_mean: float,
        epsilon: float,
    ) -> Optional[dict]:
        try:
            n = len(y)
            if n < 6:
                return None
            poly = PolynomialFeatures(degree=2, include_bias=False)
            x_poly = poly.fit_transform(x)
            quad_model = LinearRegression()
            quad_model.fit(x_poly, y)
            quad_r2 = float(quad_model.score(x_poly, y))
            delta_r2 = quad_r2 - linear_r2
            if delta_r2 < 0.05:
                return None
            a = quad_model.coef_[1] if len(quad_model.coef_) > 1 else 0.0
            b = quad_model.coef_[0]
            curvature = "凸" if a > 0 else "凹"
            y_quad_pred = quad_model.predict(x_poly)
            vertex_x = float(-b / (2 * a)) if abs(a) > 1e-10 else None
            return {
                "quadratic_r_squared": quad_r2,
                "is_nonlinear": True,
                "nonlinear_type": f"{curvature}曲线（二次）",
                "quadratic_coefficient": float(a),
                "vertex_x": vertex_x,
                "nonlinear_delta_r2": float(delta_r2),
            }
        except Exception:
            return None

    def generate_analysis_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成分析报告

        Args:
            analysis_results: 分析结果

        Returns:
            Dict: 分析报告
        """
        try:
            report = {
                "summary": self._generate_summary(analysis_results),
                "detailed_analysis": analysis_results,
                "recommendations": self._generate_recommendations(analysis_results),
            }

            return report
        except Exception as e:
            raise Exception(f"生成分析报告失败：{str(e)}")

    def _convert_to_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        将输入数据转换为DataFrame（按转速聚合，一行包含P1/P2/ST三面均值）

        Args:
            data: 输入数据

        Returns:
            pd.DataFrame: 转换后的DataFrame
        """
        processed_data = []

        for item in data:
            if "speed" in item:
                speed = item["speed"]
                p1_vals = [x for x in item.get("p1_samples", []) if x is not None]
                p2_vals = [x for x in item.get("p2_samples", []) if x is not None]
                st_vals = [x for x in item.get("sum_samples", []) if x is not None]

                if p1_vals or p2_vals or st_vals:
                    processed_data.append(
                        {
                            "speed": speed,
                            "p1_value": np.mean(p1_vals).item() if p1_vals else None,
                            "p2_value": np.mean(p2_vals).item() if p2_vals else None,
                            "st_value": np.mean(st_vals).item() if st_vals else None,
                            "p1_count": len(p1_vals),
                            "p2_count": len(p2_vals),
                            "st_count": len(st_vals),
                        }
                    )
                elif "p1_value" in item:
                    processed_data.append(
                        {
                            "speed": speed,
                            "p1_value": item.get("p1_value"),
                            "p2_value": item.get("p2_value"),
                            "st_value": item.get("st_value"),
                        }
                    )
                else:
                    logger.warning(
                        "数据行缺少有效不平衡量数据（既无样本也无p1_value），已跳过 speed=%s",
                        str(speed)[:50],
                    )

        return pd.DataFrame(processed_data)

    def _calculate_basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算基本统计量
        """
        stats = {}
        for column in ["p1_value", "p2_value", "st_value"]:
            if column in df.columns:
                column_data = df[column].dropna()
                if len(column_data) > 0:
                    mean_val = float(column_data.mean())
                    std_val = float(column_data.std())
                    stats[column] = {
                        "mean": mean_val,
                        "median": float(column_data.median()),
                        "std": std_val,
                        "cv": float(std_val / mean_val * 100)
                        if abs(mean_val) > np.finfo(float).eps
                        else 0,
                        "min": float(column_data.min()),
                        "max": float(column_data.max()),
                        "count": int(len(column_data)),
                    }
        return stats

    def _calculate_advanced_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算高级统计量
        """
        stats = {}
        for column in ["p1_value", "p2_value", "st_value"]:
            if column in df.columns:
                column_data = df[column].dropna()
                if len(column_data) > 3:
                    stats[column] = {
                        "iqr": float(self.stats.iqr(column_data)),
                        "skewness": float(self.stats.skew(column_data)),
                        "kurtosis": float(self.stats.kurtosis(column_data)),
                        "cv": float(column_data.std() / column_data.mean() * 100)
                        if abs(column_data.mean()) > np.finfo(float).eps
                        else 0,
                    }
        return stats

    def _calculate_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        numeric_columns = ["p1_value", "p2_value", "st_value"]
        numeric_df = df[numeric_columns].dropna()

        if len(numeric_df) <= 3:
            return {}

        pearson = numeric_df.corr(method="pearson").to_dict()

        try:
            spearman = numeric_df.corr(method="spearman").to_dict()
        except Exception:
            spearman = None

        result = {"pearson": pearson}
        if spearman is not None:
            result["spearman"] = spearman
            result["method_note"] = (
                "Pearson假定线性+正态；Spearman对离群值鲁棒性更好，两者一致则结论可信"
            )

        return result

    def _analyze_distributions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析分布
        """
        distributions = {}
        for column in ["p1_value", "p2_value", "st_value"]:
            if column in df.columns:
                column_data = df[column].dropna()
                if len(column_data) > 10:
                    # 正态性检验
                    stat, p_value = stats.normaltest(column_data)
                    distributions[column] = {
                        "normal_test_statistic": float(stat),
                        "normal_test_p_value": float(p_value),
                        "is_normal": bool(p_value > 0.05),
                    }
        return distributions

    def _generate_summary(self, analysis_results: Dict[str, Any]) -> str:
        """
        生成分析摘要
        """
        summary = "数据分析摘要：\n"

        # 基本统计摘要
        if "basic_stats" in analysis_results:
            summary += "\n1. 基本统计信息：\n"
            for face, stats in analysis_results["basic_stats"].items():
                face_name = {"p1_value": "P1面", "p2_value": "P2面", "st_value": "ST面"}.get(
                    face, face
                )
                summary += f"   {face_name}：均值={stats['mean']:.2f}, 中位数={stats['median']:.2f}, 标准差={stats['std']:.2f}\n"

        # 趋势分析摘要
        if "trend_analysis" in analysis_results:
            summary += "\n2. 趋势分析：\n"
            for face, trend in analysis_results["trend_analysis"].items():
                face_name = {"p1_value": "P1面", "p2_value": "P2面", "st_value": "ST面"}.get(
                    face, face
                )
                summary += (
                    f"   {face_name}：{trend['trend_direction']}趋势，R²={trend['r_squared']:.2f}\n"
                )

        # 异常检测摘要
        if "anomaly_detection" in analysis_results:
            summary += "\n3. 异常检测：\n"
            for face, anomalies in analysis_results["anomaly_detection"].items():
                if anomalies:
                    face_name = {"p1_value": "P1面", "p2_value": "P2面", "st_value": "ST面"}.get(
                        face, face
                    )
                    summary += f"   {face_name}：发现{len(anomalies['anomaly_values'])}个异常值\n"

        return summary

    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """
        生成建议
        """
        recommendations = []

        # 基于统计分析的建议
        if "basic_stats" in analysis_results:
            for face, stats in analysis_results["basic_stats"].items():
                if stats["std"] > stats["mean"] * 0.5:
                    face_name = {"p1_value": "P1面", "p2_value": "P2面", "st_value": "ST面"}.get(
                        face, face
                    )
                    recommendations.append(f"{face_name}数据波动较大，建议检查测量设备和工艺稳定性")

        # 基于趋势分析的建议
        if "trend_analysis" in analysis_results:
            for face, trend in analysis_results["trend_analysis"].items():
                if abs(trend["slope"]) > 0.1 and trend["r_squared"] > 0.7:
                    face_name = {"p1_value": "P1面", "p2_value": "P2面", "st_value": "ST面"}.get(
                        face, face
                    )
                    direction = "上升" if trend["slope"] > 0 else "下降"
                    recommendations.append(
                        f"{face_name}呈现明显{direction}趋势，建议进一步分析原因"
                    )

        # 基于异常检测的建议
        if "anomaly_detection" in analysis_results:
            for face, anomalies in analysis_results["anomaly_detection"].items():
                if anomalies and len(anomalies["anomaly_values"]) > 3:
                    face_name = {"p1_value": "P1面", "p2_value": "P2面", "st_value": "ST面"}.get(
                        face, face
                    )
                    recommendations.append(
                        f"{face_name}存在多个异常值，建议检查测量过程和数据采集系统"
                    )

        return recommendations


# 创建全局数据分析服务实例
data_analysis_service = DataAnalysisService()
