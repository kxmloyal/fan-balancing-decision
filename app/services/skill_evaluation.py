#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技能评估服务模块
提供综合技能评估功能，集成数据分析能力
"""

import hashlib
import json
import logging
import threading
import time
from typing import Any, Dict, List

from app.services.data_analysis import data_analysis_service
from app.services.project_statistics import calculate_optimal_speed_evaluation

logger = logging.getLogger(__name__)


class SkillEvaluationService:
    """
    技能评估服务类
    提供综合技能评估功能

    可配置阈值说明：
    - CV_EXCELLENT / CV_GOOD: CV百分比阈值，用于数据质量加分
    - QUALITY_BONUS_EXCELLENT / QUALITY_BONUS_GOOD: 对应的加分值
    - ANOMALY_PENALTY_THRESHOLD: 异常数量超过此值开始扣分
    - ANOMALY_PENALTY: 异常扣分值
    - MIN_SAMPLES_PER_SPEED: 每个转速最少有效样本数
    - MIN_SPEED_COUNT: 最少有效转速数
    - ANOMALY_FILTER_Z_THRESHOLD: 异常过滤Z-score阈值
    """

    CV_EXCELLENT = 5.0
    CV_GOOD = 10.0
    QUALITY_BONUS_EXCELLENT = 0.10
    QUALITY_BONUS_GOOD = 0.05
    ANOMALY_PENALTY_THRESHOLD = 2
    ANOMALY_PENALTY = 0.10
    MIN_SAMPLES_PER_SPEED = 2
    MIN_SPEED_COUNT = 2
    ANOMALY_FILTER_Z_THRESHOLD = 2.5

    _cache = {}
    _cache_lock = threading.Lock()
    _cache_ttl = 300

    def __init__(self):
        """初始化技能评估服务"""
        pass

    @classmethod
    def _cache_key(cls, prefix, data, **kwargs):
        raw = json.dumps(
            {"prefix": prefix, "len": len(data) if isinstance(data, list) else 0, "kwargs": kwargs},
            sort_keys=True,
        )
        return hashlib.md5(raw.encode()).hexdigest()

    @classmethod
    def _cache_get(cls, key):
        with cls._cache_lock:
            entry = cls._cache.get(key)
            if entry and (time.time() - entry["ts"]) < cls._cache_ttl:
                return entry["value"]
            if entry:
                del cls._cache[key]
        return None

    @classmethod
    def _cache_set(cls, key, value):
        with cls._cache_lock:
            cls._cache[key] = {"value": value, "ts": time.time()}
            if len(cls._cache) > 200:
                expired = [
                    k for k, v in cls._cache.items() if (time.time() - v["ts"]) > cls._cache_ttl
                ]
                for k in expired:
                    del cls._cache[k]

    def evaluate_skill(
        self, data: List[Dict[str, Any]], filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        综合技能评估

        Args:
            data: 输入数据，包含转速和各面的不平衡量
            filters: 筛选条件

        Returns:
            Dict: 综合技能评估结果
        """
        try:
            if not data:
                raise ValueError("输入数据为空")
            if not isinstance(data, list):
                raise ValueError("输入数据格式错误，应为列表类型")

            filtered_data = self._apply_filters(data, filters)

            if not filtered_data:
                raise ValueError("筛选后数据为空，请检查筛选条件")

            self._validate_data_sufficiency(filtered_data)

            optimal_speed_evaluation = self._evaluate_optimal_speed(filtered_data)

            advanced_analysis = self._perform_advanced_analysis(filtered_data)

            comprehensive_evaluation = self._comprehensive_evaluation(
                optimal_speed_evaluation, advanced_analysis
            )

            return {
                "optimal_speed_evaluation": optimal_speed_evaluation,
                "advanced_analysis": advanced_analysis,
                "comprehensive_evaluation": comprehensive_evaluation,
            }
        except ValueError as ve:
            raise Exception(f"输入数据验证失败：{str(ve)}")
        except Exception as e:
            raise Exception(f"技能评估失败：{str(e)}")

    def _validate_data_sufficiency(self, data: List[Dict[str, Any]]) -> None:
        speeds: Dict[str, int] = {}
        for item in data:
            speed = item.get("speed", str(item.get("转速", "")))
            if not speed:
                continue
            s = str(speed)
            sample_count = 0
            for key in ("p1_samples", "p2_samples", "sum_samples"):
                samples = item.get(key, [])
                if isinstance(samples, list):
                    sample_count += len([x for x in samples if x is not None])
            speeds[s] = speeds.get(s, 0) + sample_count

        valid_speeds = {k: v for k, v in speeds.items() if v >= self.MIN_SAMPLES_PER_SPEED}

        if len(valid_speeds) < self.MIN_SPEED_COUNT:
            total_samples = sum(speeds.values())
            speed_names = list(speeds.keys())
            detail = (
                f"数据不足以进行可靠分析。"
                f"需要至少 {self.MIN_SPEED_COUNT} 个转速各 {self.MIN_SAMPLES_PER_SPEED} 个以上有效样本。"
                f"当前：{len(speed_names)} 个转速（{', '.join(speed_names[:5])}），"
                f"合计 {total_samples} 个有效样本。"
            )
            raise ValueError(detail)

    def _apply_filters(
        self, data: List[Dict[str, Any]], filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        应用筛选条件

        Args:
            data: 输入数据
            filters: 筛选条件

        Returns:
            List[Dict[str, Any]]: 筛选后的数据
        """
        if not filters:
            return data

        filtered_data = data.copy()

        # 转速范围筛选
        speed_range = filters.get("speed_range")
        if speed_range and speed_range != "all":
            filtered_data = [
                item for item in filtered_data if self._filter_speed(item, speed_range)
            ]

        # 数据面筛选
        data_surface = filters.get("data_surface")
        if data_surface and data_surface != "all":
            filtered_data = [
                item for item in filtered_data if self._filter_surface(item, data_surface)
            ]

        # 异常值筛选
        anomaly_filter = filters.get("anomaly_filter")
        if anomaly_filter == "no_anomaly":
            filtered_data = [item for item in filtered_data if self._filter_anomalies(item)]

        # 数据质量筛选
        data_quality = filters.get("data_quality")
        if data_quality and data_quality != "all":
            filtered_data = self._filter_by_data_quality(filtered_data, data_quality)

        return filtered_data

    def _filter_by_data_quality(
        self, data: List[Dict[str, Any]], quality: str
    ) -> List[Dict[str, Any]]:
        """按数据质量阈值筛选样本"""
        if not data:
            return data
        threshold_map = {
            "excellent": 0.10,
            "good": 0.15,
            "average": 0.30,
            "poor": 1.0,
            "high": 0.15,
            "medium": 0.30,
            "low": 1.0,
        }
        threshold = threshold_map.get(quality, 1.0)
        result = []
        for item in data:
            all_samples = []
            for key in ("p1_samples", "p2_samples", "sum_samples"):
                samples = [x for x in item.get(key, []) if x is not None]
                all_samples.extend(samples)
            if not all_samples:
                continue
            mean_val = sum(all_samples) / len(all_samples)
            if mean_val == 0:
                continue
            if threshold < 1.0:
                from statistics import stdev

                try:
                    cv = stdev(all_samples) / mean_val if len(all_samples) > 1 else 0
                    if cv <= threshold:
                        result.append(item)
                except (ZeroDivisionError, Exception):
                    result.append(item)
            else:
                result.append(item)
        return result

    def _filter_speed(self, item: Dict[str, Any], speed_range: str) -> bool:
        """
        筛选转速范围

        Args:
            item: 数据项
            speed_range: 转速范围

        Returns:
            bool: 是否符合条件
        """
        try:
            speed = item.get("speed", "")
            if not speed:
                return False

            # 提取转速数值
            digits = "".join(filter(str.isdigit, speed))
            if not digits:
                return False

            speed_num = int(digits)

            if speed_range == "low":
                return speed_num <= 1000
            elif speed_range == "medium":
                return 1000 < speed_num <= 3000
            elif speed_range == "high":
                return speed_num > 3000
            return True
        except (ValueError, TypeError):
            return False

    def _filter_surface(self, item: Dict[str, Any], data_surface: str) -> bool:
        """
        筛选数据面

        Args:
            item: 数据项
            data_surface: 数据面

        Returns:
            bool: 是否符合条件
        """
        if data_surface == "p1":
            return "p1_samples" in item and item["p1_samples"]
        elif data_surface == "p2":
            return "p2_samples" in item and item["p2_samples"]
        elif data_surface == "st":
            return "sum_samples" in item and item["sum_samples"]
        return True

    def _filter_anomalies(self, item: Dict[str, Any]) -> bool:
        p1_samples = [x for x in item.get("p1_samples", []) if x is not None]
        p2_samples = [x for x in item.get("p2_samples", []) if x is not None]
        sum_samples = [x for x in item.get("sum_samples", []) if x is not None]
        all_samples = p1_samples + p2_samples + sum_samples

        if len(all_samples) < 4:
            return True

        import numpy as np

        arr = np.array(all_samples)

        median = np.median(arr)
        mad = np.median(np.abs(arr - median))
        if mad > 0:
            z_scores = 0.6745 * np.abs(arr - median) / mad
            method = "MAD"
        else:
            mean = np.mean(arr)
            std = np.std(arr)
            if std == 0:
                return True
            z_scores = np.abs((arr - mean) / std)
            method = "标准差"

        threshold = self.ANOMALY_FILTER_Z_THRESHOLD
        anomaly_count = np.sum(z_scores > threshold)
        total_count = len(arr)
        ratio = anomaly_count / total_count

        if ratio >= 0.3:
            logger.debug(f"数据项被过滤：异常比例 {ratio:.2%} (方法: {method})")

        return ratio < 0.3

    def generate_skill_report(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成技能评估报告

        Args:
            evaluation_results: 评估结果

        Returns:
            Dict: 技能评估报告
        """
        try:
            report = {
                "summary": self._generate_summary(evaluation_results),
                "detailed_evaluation": evaluation_results,
                "recommendations": self._generate_recommendations(evaluation_results),
                "skill_level": self._determine_skill_level(evaluation_results),
            }

            return report
        except Exception as e:
            raise Exception(f"生成技能评估报告失败：{str(e)}")

    def _evaluate_optimal_speed(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        cache_key = self._cache_key("optimal_speed", data)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            import numpy as np

            stats_data = []
            for item in data:
                if "speed" in item:
                    speed = item["speed"]
                    p1_samples = [x for x in item.get("p1_samples", []) if x is not None]
                    p2_samples = [x for x in item.get("p2_samples", []) if x is not None]
                    sum_samples = [x for x in item.get("sum_samples", []) if x is not None]

                    stat_row = {"转速": str(speed)}

                    # P1面统计量
                    if p1_samples:
                        arr = np.array(p1_samples, dtype=float)
                        arr = arr[np.isfinite(arr)]
                        if len(arr) > 0:
                            arr_mean = float(np.mean(arr))
                            q25, q75 = np.percentile(arr, [25, 75])
                            iqr = q75 - q25
                            cv = (
                                (float(np.std(arr)) / arr_mean * 100)
                                if arr_mean != 0
                                else float("inf")
                            )
                            stat_row.update(
                                {
                                    "P1-平均值": str(round(arr_mean, 2)),
                                    "P1-中位数": str(round(float(np.median(arr)), 2)),
                                    "P1-标准差": str(round(float(np.std(arr)), 2)),
                                    "P1-最小值": str(round(float(np.min(arr)), 2)),
                                    "P1-最大值": str(round(float(np.max(arr)), 2)),
                                    "P1-IQR": str(round(float(iqr), 2)),
                                    "P1-CV": str(round(cv, 2)) if cv != float("inf") else "inf",
                                }
                            )

                    if p2_samples:
                        arr = np.array(p2_samples, dtype=float)
                        arr = arr[np.isfinite(arr)]
                        if len(arr) > 0:
                            arr_mean = float(np.mean(arr))
                            q25, q75 = np.percentile(arr, [25, 75])
                            iqr = q75 - q25
                            cv = (
                                (float(np.std(arr)) / arr_mean * 100)
                                if arr_mean != 0
                                else float("inf")
                            )
                            stat_row.update(
                                {
                                    "P2-平均值": str(round(arr_mean, 2)),
                                    "P2-中位数": str(round(float(np.median(arr)), 2)),
                                    "P2-标准差": str(round(float(np.std(arr)), 2)),
                                    "P2-最小值": str(round(float(np.min(arr)), 2)),
                                    "P2-最大值": str(round(float(np.max(arr)), 2)),
                                    "P2-IQR": str(round(float(iqr), 2)),
                                    "P2-CV": str(round(cv, 2)) if cv != float("inf") else "inf",
                                }
                            )

                    if sum_samples:
                        arr = np.array(sum_samples, dtype=float)
                        arr = arr[np.isfinite(arr)]
                        if len(arr) > 0:
                            arr_mean = float(np.mean(arr))
                            q25, q75 = np.percentile(arr, [25, 75])
                            iqr = q75 - q25
                            cv = (
                                (float(np.std(arr)) / arr_mean * 100)
                                if arr_mean != 0
                                else float("inf")
                            )
                            stat_row.update(
                                {
                                    "ST面-平均值": str(round(arr_mean, 2)),
                                    "ST面-中位数": str(round(float(np.median(arr)), 2)),
                                    "ST面-标准差": str(round(float(np.std(arr)), 2)),
                                    "ST面-最小值": str(round(float(np.min(arr)), 2)),
                                    "ST面-最大值": str(round(float(np.max(arr)), 2)),
                                    "ST面-IQR": str(round(float(iqr), 2)),
                                    "ST面-CV": str(round(cv, 2)) if cv != float("inf") else "inf",
                                }
                            )

                    stats_data.append(stat_row)

            if not stats_data:
                result = {
                    "best_speeds": [],
                    "best_score": None,
                    "speed_detailed_scores": {},
                    "weights": {},
                }
                self._cache_set(cache_key, result)
                return result

            evaluation_result = calculate_optimal_speed_evaluation(stats_data)
            self._cache_set(cache_key, evaluation_result)
            return evaluation_result
        except Exception as e:
            raise Exception(f"最优转速评估失败：{str(e)}")

    def _perform_advanced_analysis(
        self,
        data: List[Dict[str, Any]],
        include_clustering: bool = False,
        include_pca: bool = False,
    ) -> Dict[str, Any]:
        """
        执行高级数据分析（统计、趋势、异常、可选聚类/PCA）

        Args:
            data: 输入数据
            include_clustering: 是否执行聚类分析（前端未展示，默认跳过）
            include_pca: 是否执行PCA降维（前端未展示，默认跳过）

        Returns:
            Dict: 高级分析结果
        """
        cache_key = self._cache_key(
            "advanced_analysis",
            data,
            include_clustering=include_clustering,
            include_pca=include_pca,
        )
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            # 执行高级统计分析
            advanced_stats = data_analysis_service.advanced_statistical_analysis(data)

            # 执行趋势分析
            trend_analysis = data_analysis_service.trend_analysis(data)

            # 执行异常检测
            anomaly_detection = data_analysis_service.anomaly_detection(data)

            # 聚类分析（按需执行，避免前端丢弃结果造成浪费）
            cluster_result = None
            if include_clustering:
                cluster_result = data_analysis_service.cluster_analysis(data)

            # 维度 reduction 分析（按需执行）
            pca_result = None
            if include_pca:
                pca_result = data_analysis_service.dimensionality_reduction(data)

            result = {
                "advanced_statistics": advanced_stats,
                "trend_analysis": trend_analysis,
                "anomaly_detection": anomaly_detection,
                "cluster_analysis": cluster_result,
                "dimensionality_reduction": pca_result,
            }
            self._cache_set(cache_key, result)
            return result
        except Exception as e:
            raise Exception(f"高级数据分析失败：{str(e)}")

    def _comprehensive_evaluation(
        self, optimal_speed_eval: Dict[str, Any], advanced_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        综合评估

        Args:
            optimal_speed_eval: 最优转速评估结果
            advanced_analysis: 高级分析结果

        Returns:
            Dict: 综合评估结果
        """
        try:
            # 计算技能得分
            skill_score = self._calculate_skill_score(optimal_speed_eval, advanced_analysis)

            # 数据不足时的处理
            if skill_score is None:
                return {
                    "skill_score": None,
                    "data_quality": "未知",
                    "process_stability": "未知",
                    "anomaly_evaluation": "未知",
                    "overall_assessment": "数据不足，无法完成综合评估",
                    "insufficient_data": True,
                }
            # 评估数据质量
            data_quality = self._evaluate_data_quality(advanced_analysis)

            # 评估工艺稳定性
            process_stability = self._evaluate_process_stability(advanced_analysis)

            # 评估异常情况
            anomaly_evaluation = self._evaluate_anomalies(advanced_analysis)

            return {
                "skill_score": skill_score,
                "data_quality": data_quality,
                "process_stability": process_stability,
                "anomaly_evaluation": anomaly_evaluation,
                "overall_assessment": self._generate_overall_assessment(
                    skill_score, data_quality, process_stability, anomaly_evaluation
                ),
            }
        except Exception as e:
            raise Exception(f"综合评估失败：{str(e)}")

    def _calculate_skill_score(
        self, optimal_speed_eval: Dict[str, Any], advanced_analysis: Dict[str, Any]
    ) -> float:
        """
        计算技能得分（使用可配置阈值）

        Args:
            optimal_speed_eval: 最优转速评估结果
            advanced_analysis: 高级分析结果

        Returns:
            float: 技能得分，数据不足时返回 None
        """
        base_score = 0.0
        has_valid_score = False
        if "speed_detailed_scores" in optimal_speed_eval:
            scores = list(optimal_speed_eval["speed_detailed_scores"].values())
            if scores:
                valid_scores = [
                    score.get("total_score", 0)
                    for score in scores
                    if score.get("total_score", 0) > 0
                ]
                if valid_scores:
                    base_score = max(valid_scores)
                    has_valid_score = True

        if not has_valid_score:
            return None

        data_quality_bonus = 0.0
        if "advanced_statistics" in advanced_analysis:
            stats = advanced_analysis["advanced_statistics"]
            if "basic_stats" in stats:
                for face, face_stats in stats["basic_stats"].items():
                    try:
                        cv = face_stats.get("cv")
                        if cv is not None and cv >= 0:
                            if cv < self.CV_EXCELLENT:
                                data_quality_bonus += self.QUALITY_BONUS_EXCELLENT
                            elif cv < self.CV_GOOD:
                                data_quality_bonus += self.QUALITY_BONUS_GOOD
                    except (TypeError, ValueError):
                        continue

        anomaly_penalty = 0.0
        if "anomaly_detection" in advanced_analysis:
            anomalies = advanced_analysis["anomaly_detection"]
            for face, face_anomalies in anomalies.items():
                if (
                    face_anomalies
                    and len(face_anomalies.get("anomaly_values", []))
                    > self.ANOMALY_PENALTY_THRESHOLD
                ):
                    anomaly_penalty += self.ANOMALY_PENALTY

        final_score = min(1.0, max(0.0, base_score + data_quality_bonus - anomaly_penalty))
        return final_score

    def _evaluate_data_quality(self, advanced_analysis: Dict[str, Any]) -> str:
        """
        评估数据质量（多维度：样本量+变异系数+异常比例+正态性）

        Returns:
            str: 优秀 / 良好 / 一般 / 不足 / 未知
        """
        quality_scores = []

        if "advanced_statistics" in advanced_analysis:
            stats = advanced_analysis["advanced_statistics"]

            if "basic_stats" in stats:
                total_count = 0
                face_count = 0
                min_cv = float("inf")
                max_cv = 0.0

                for face, face_stats in stats["basic_stats"].items():
                    count = face_stats.get("count", 0)
                    if count > 0:
                        total_count += count
                        face_count += 1
                    cv = face_stats.get("cv")
                    if cv is not None and cv >= 0:
                        min_cv = min(min_cv, cv)
                        max_cv = max(max_cv, cv)

                sample_score = 0
                if total_count >= 100:
                    sample_score = 4
                elif total_count >= 50:
                    sample_score = 3
                elif total_count >= 20:
                    sample_score = 2
                elif total_count >= 5:
                    sample_score = 1

                cv_score = 0
                if min_cv != float("inf"):
                    avg_cv = (min_cv + max_cv) / 2
                    if avg_cv < 5:
                        cv_score = 4
                    elif avg_cv < 10:
                        cv_score = 3
                    elif avg_cv < 20:
                        cv_score = 2
                    elif avg_cv < 50:
                        cv_score = 1

                quality_scores.append(sample_score)
                quality_scores.append(cv_score)

        anomaly_score = 0
        if "anomaly_detection" in advanced_analysis:
            anomalies = advanced_analysis["anomaly_detection"]
            anomaly_ratios = []
            for face, face_anomalies in anomalies.items():
                if face_anomalies:
                    ratio = face_anomalies.get("anomaly_ratio", 0)
                    anomaly_ratios.append(ratio)

            if anomaly_ratios:
                avg_ratio = sum(anomaly_ratios) / len(anomaly_ratios)
                if avg_ratio < 0.05:
                    anomaly_score = 4
                elif avg_ratio < 0.1:
                    anomaly_score = 3
                elif avg_ratio < 0.2:
                    anomaly_score = 2
                else:
                    anomaly_score = 1
            else:
                anomaly_score = 4

        quality_scores.append(anomaly_score)

        if not quality_scores:
            return "未知"

        avg = sum(quality_scores) / len(quality_scores)
        if avg >= 3.5:
            return "优秀"
        elif avg >= 2.5:
            return "良好"
        elif avg >= 1.5:
            return "一般"
        else:
            return "不足"

    def _evaluate_process_stability(self, advanced_analysis: Dict[str, Any]) -> str:
        """
        评估工艺稳定性
        """
        if "trend_analysis" in advanced_analysis:
            trends = advanced_analysis["trend_analysis"]
            unstable_faces = 0

            for face, trend in trends.items():
                try:
                    slope = trend.get("slope")
                    r_squared = trend.get("r_squared")
                    if slope is not None and r_squared is not None:
                        if abs(float(slope)) > 0.05 and float(r_squared) > 0.6:
                            unstable_faces += 1
                except (TypeError, ValueError):
                    continue

            if unstable_faces == 0:
                return "稳定"
            elif unstable_faces == 1:
                return "基本稳定"
            else:
                return "不稳定"
        return "未知"

    def _evaluate_anomalies(self, advanced_analysis: Dict[str, Any]) -> str:
        """
        评估异常情况
        """
        if "anomaly_detection" in advanced_analysis:
            anomalies = advanced_analysis["anomaly_detection"]
            total_anomalies = 0

            for face, face_anomalies in anomalies.items():
                if face_anomalies:
                    total_anomalies += len(face_anomalies.get("anomaly_values", []))

            if total_anomalies == 0:
                return "无异常"
            elif total_anomalies <= 3:
                return "少量异常"
            else:
                return "较多异常"
        return "未知"

    def _generate_overall_assessment(
        self, skill_score: float, data_quality: str, process_stability: str, anomaly_evaluation: str
    ) -> str:
        """
        生成总体评估
        """
        if (
            skill_score >= 0.9
            and data_quality in ["优秀", "良好"]
            and process_stability in ["稳定", "基本稳定"]
            and anomaly_evaluation in ["无异常", "少量异常"]
        ):
            return "优秀"
        elif (
            skill_score >= 0.7
            and data_quality in ["良好", "一般"]
            and process_stability in ["基本稳定"]
            and anomaly_evaluation in ["少量异常"]
        ):
            return "良好"
        elif (
            skill_score >= 0.5
            and data_quality in ["一般"]
            and process_stability in ["基本稳定", "不稳定"]
            and anomaly_evaluation in ["少量异常", "较多异常"]
        ):
            return "一般"
        else:
            return "需要改进"

    def _generate_summary(self, evaluation_results: Dict[str, Any]) -> str:
        """
        生成评估摘要
        """
        summary = "技能评估摘要：\n"

        # 最优转速摘要
        if "optimal_speed_evaluation" in evaluation_results:
            opt_eval = evaluation_results["optimal_speed_evaluation"]
            if "best_speeds" in opt_eval and opt_eval["best_speeds"]:
                best = opt_eval["best_speeds"][0]
                if isinstance(best, dict):
                    summary += f"\n1. 最优转速：{best.get('id', 'N/A')} (得分: {best.get('score', 0):.4f})\n"
                else:
                    summary += f"\n1. 最优转速：{best}\n"

        # 综合评估摘要
        if "comprehensive_evaluation" in evaluation_results:
            comp_eval = evaluation_results["comprehensive_evaluation"]
            skill_score = comp_eval.get("skill_score")
            if skill_score is not None:
                summary += f"\n2. 技能得分：{skill_score:.2f}\n"
            else:
                summary += "\n2. 技能得分：N/A\n"
            summary += f"   数据质量：{comp_eval['data_quality']}\n"
            summary += f"   工艺稳定性：{comp_eval['process_stability']}\n"
            summary += f"   异常情况：{comp_eval['anomaly_evaluation']}\n"
            summary += f"   总体评估：{comp_eval['overall_assessment']}\n"

        return summary

    def _generate_recommendations(self, evaluation_results: Dict[str, Any]) -> List[str]:
        """
        生成建议（基于多维度评估结果）

        Returns:
            List[str]: 改进建议列表
        """
        recommendations: List[str] = []

        if "comprehensive_evaluation" in evaluation_results:
            comp_eval = evaluation_results["comprehensive_evaluation"]

            dq = comp_eval.get("data_quality")
            ps = comp_eval.get("process_stability")
            ae = comp_eval.get("anomaly_evaluation")
            ss = comp_eval.get("skill_score")

            has_recommendation = False

            if dq and dq == "不足":
                recommendations.append(
                    "数据质量不足：建议增加测量样本数量（每转速≥5个样本），"
                    "并检查测量系统的重复性和再现性"
                )
                has_recommendation = True
            elif dq and dq == "一般":
                recommendations.append("数据质量一般：建议适量增加样本，减小测量变异系数")
                has_recommendation = True

            if ps and ps == "不稳定":
                recommendations.append(
                    "工艺稳定性较差：不平衡量随转速变化明显，建议检查设备状态、工装定位和操作流程"
                )

            if ae and ae == "较多异常":
                recommendations.append(
                    "存在较多异常值：建议检查测量过程校准状态，排查传感器松动、振动干扰等潜在问题"
                )

            if ss is not None and ss < 0.7:
                recommendations.append("综合评分偏低：建议加强操作培训和工艺优化")

            if not recommendations:
                recommendations.append("当前数据质量良好，工艺稳定，继续维持现有操作规范")

        if "advanced_analysis" in evaluation_results:
            adv_analysis = evaluation_results["advanced_analysis"]

            if "trend_analysis" in adv_analysis:
                trends = adv_analysis["trend_analysis"]
                for face, trend in trends.items():
                    if "trend_direction" in trend and trend["trend_direction"] != "稳定":
                        face_name = {
                            "p1_value": "P1面",
                            "p2_value": "P2面",
                            "st_value": "ST面",
                        }.get(face, face)
                        direction = trend.get("trend_direction", "")
                        msg = f"{face_name}存在{direction}趋势"
                        if "is_nonlinear" in trend and trend.get("is_nonlinear"):
                            msg += f"（{trend.get('nonlinear_type', '非线性')}）"
                        if "r_squared" in trend:
                            msg += f"，拟合度R²={trend['r_squared']:.3f}"
                        recommendations.append(msg + "，建议关注该转速范围内不平衡量的变化规律")

        return recommendations

    def _determine_skill_level(self, evaluation_results: Dict[str, Any]) -> str:
        """
        确定技能等级
        """
        if "comprehensive_evaluation" in evaluation_results:
            comp_eval = evaluation_results["comprehensive_evaluation"]
            overall = comp_eval["overall_assessment"]

            if overall == "优秀":
                return "专家级"
            elif overall == "良好":
                return "熟练级"
            elif overall == "一般":
                return "基础级"
            else:
                return "需要提升"
        return "未知"


# 创建全局技能评估服务实例
skill_evaluation_service = SkillEvaluationService()
