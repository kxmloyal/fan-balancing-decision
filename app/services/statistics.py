#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统计服务模块
包含统计分析、最优转速评估等功能
"""

import logging
import os

import numpy as np

logger = logging.getLogger(__name__)


def calculate_optimal_speed_evaluation(stats_data):
    """
    计算最优转速评估
    优化评估逻辑，更合理地评估每个转速的质量

    Args:
        stats_data: 统计数据

    Returns:
        Dict: 评估结果，包含最佳转速和详细评分
    """
    # 从stats_data中提取转速和统计数据
    speeds = []
    stats = []

    for item in stats_data:
        speed = item.get("speed")
        if speed:
            speeds.append(speed)
            stats.append(
                {
                    "speed": speed,
                    "p1_median": item.get("p1_median", 0),
                    "p2_median": item.get("p2_median", 0),
                    "p1_std": item.get("p1_std", 0),
                    "p2_std": item.get("p2_std", 0),
                    "p1_cv": item.get("p1_cv", 0),
                    "p2_cv": item.get("p2_cv", 0),
                    "p1_count": item.get("p1_count", 0),
                    "p2_count": item.get("p2_count", 0),
                    "p1_min": item.get("p1_min", 0),
                    "p1_max": item.get("p1_max", 0),
                    "p2_min": item.get("p2_min", 0),
                    "p2_max": item.get("p2_max", 0),
                    "st_median": item.get("st_median", 0),
                    "st_std": item.get("st_std", 0),
                    "st_cv": item.get("st_cv", 0),
                    "st_count": item.get("st_count", 0),
                    "st_min": item.get("st_min", 0),
                    "st_max": item.get("st_max", 0),
                }
            )

    # 计算每个转速的评分
    speed_scores = {}
    speed_detailed_scores = {}

    for stat in stats:
        speed = stat["speed"]
        score = 0
        detailed_scores = {}

        # 1. 中位数评估（权重：40%）
        # 计算P1和P2的平均中位数，越小越好
        p1_median = stat.get("p1_median", 0)
        p2_median = stat.get("p2_median", 0)
        median_avg = (
            (p1_median + p2_median) / 2 if (p1_median and p2_median) else max(p1_median, p2_median)
        )

        # 中位数得分：越小越好，采用倒数变换
        if median_avg > 0:
            median_score = 100 / (1 + median_avg)
        else:
            median_score = 100
        score += median_score * 0.4
        detailed_scores["median"] = median_score

        # 2. 标准差评估（权重：30%）
        # 计算P1和P2的平均标准差，越小越好
        p1_std = stat.get("p1_std", 0)
        p2_std = stat.get("p2_std", 0)
        std_avg = (p1_std + p2_std) / 2 if (p1_std and p2_std) else max(p1_std, p2_std)

        # 标准差得分：越小越好，采用倒数变换
        if std_avg > 0:
            std_score = 100 / (1 + std_avg)
        else:
            std_score = 100
        score += std_score * 0.3
        detailed_scores["std"] = std_score

        # 3. 变异系数评估（权重：20%）
        # 计算P1和P2的平均变异系数，越小越好
        p1_cv = stat.get("p1_cv", 0)
        p2_cv = stat.get("p2_cv", 0)
        cv_avg = (p1_cv + p2_cv) / 2 if (p1_cv and p2_cv) else max(p1_cv, p2_cv)

        # 变异系数得分：越小越好，采用倒数变换
        if cv_avg > 0:
            cv_score = 100 / (1 + cv_avg)
        else:
            cv_score = 100
        score += cv_score * 0.2
        detailed_scores["cv"] = cv_score

        # 4. 数据量评估（权重：10%）
        # 计算P1和P2的数据量，越大越好
        p1_count = stat.get("p1_count", 0)
        p2_count = stat.get("p2_count", 0)
        count_avg = (p1_count + p2_count) / 2

        # 数据量得分：越大越好，最大30个数据点
        count_score = min(count_avg / 30 * 100, 100)
        score += count_score * 0.1
        detailed_scores["count"] = count_score

        # 5. ST面数据奖励（额外10分）
        if stat.get("st_median", 0) > 0:
            st_median = stat["st_median"]
            st_score = max(0, 10 - st_median / 10)
            score += st_score
            detailed_scores["st_bonus"] = st_score

        speed_scores[speed] = score
        speed_detailed_scores[speed] = detailed_scores

    # 排序并选择最佳转速
    sorted_speeds = sorted(speed_scores.items(), key=lambda x: x[1], reverse=True)
    best_speeds = [speed for speed, score in sorted_speeds[:3]]

    return {
        "best_speeds": best_speeds,
        "speed_detailed_scores": speed_detailed_scores,
        "detailed_scores": speed_detailed_scores,  # 保持与之前的兼容性
    }


def generate_stats_data(parsed_data):
    """
    生成统计数据，用于最优转速评估

    Args:
        parsed_data: 解析后的数据

    Returns:
        List[Dict]: 统计数据列表
    """
    stats_data = []

    for item in parsed_data:
        speed = item.get("speed")
        if not speed:
            continue

        # P1面统计
        p1_samples = item.get("p1_samples", [])
        p1_median = np.median(p1_samples) if p1_samples else 0
        p1_std = np.std(p1_samples) if p1_samples else 0
        p1_cv = p1_std / p1_median if p1_median > 0 else 0
        p1_count = len(p1_samples)
        p1_min = min(p1_samples) if p1_samples else 0
        p1_max = max(p1_samples) if p1_samples else 0

        # P2面统计
        p2_samples = item.get("p2_samples", [])
        p2_median = np.median(p2_samples) if p2_samples else 0
        p2_std = np.std(p2_samples) if p2_samples else 0
        p2_cv = p2_std / p2_median if p2_median > 0 else 0
        p2_count = len(p2_samples)
        p2_min = min(p2_samples) if p2_samples else 0
        p2_max = max(p2_samples) if p2_samples else 0

        # ST面统计
        st_samples = item.get("sum_samples", [])
        st_median = np.median(st_samples) if st_samples else 0
        st_std = np.std(st_samples) if st_samples else 0
        st_cv = st_std / st_median if st_median > 0 else 0
        st_count = len(st_samples)
        st_min = min(st_samples) if st_samples else 0
        st_max = max(st_samples) if st_samples else 0

        stats_data.append(
            {
                "speed": speed,
                "p1_median": p1_median,
                "p2_median": p2_median,
                "p1_std": p1_std,
                "p2_std": p2_std,
                "p1_cv": p1_cv,
                "p2_cv": p2_cv,
                "p1_count": p1_count,
                "p2_count": p2_count,
                "p1_min": p1_min,
                "p1_max": p1_max,
                "p2_min": p2_min,
                "p2_max": p2_max,
                "st_median": st_median,
                "st_std": st_std,
                "st_cv": st_cv,
                "st_count": st_count,
                "st_min": st_min,
                "st_max": st_max,
            }
        )

    return stats_data


def generate_stats(parsed_data, output_prefix, output_folder):
    """
    生成统计报告（HTML和CSV）

    Args:
        parsed_data: 解析后的数据
        output_prefix: 输出前缀
        output_folder: 输出文件夹

    Returns:
        Tuple[str, str]: HTML报告路径和CSV报告路径
    """
    # 生成统计数据
    stats_data = generate_stats_data(parsed_data)

    # 生成HTML报告
    html_content = generate_stats_html(stats_data)
    html_path = os.path.join(output_folder, f"{output_prefix}_stats.html")
    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    except (IOError, OSError) as e:
        logger.error("写入文件失败 %s: %s", html_path, str(e))

    # 生成CSV报告
    csv_content = generate_stats_csv(stats_data)
    csv_path = os.path.join(output_folder, f"{output_prefix}_stats.csv")
    try:
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(csv_content)
    except (IOError, OSError) as e:
        logger.error("写入文件失败 %s: %s", csv_path, str(e))

    return html_path, csv_path


def generate_single_surface_stats(parsed_data, output_prefix, surface_type, output_folder):
    """
    生成单个面的统计报告（HTML和CSV）

    Args:
        parsed_data: 解析后的数据
        output_prefix: 输出前缀
        surface_type: 表面类型（p1, p2, st）
        output_folder: 输出文件夹

    Returns:
        Tuple[str, str]: HTML报告路径和CSV报告路径
    """
    # 生成统计数据
    stats_data = []

    for item in parsed_data:
        speed = item.get("speed")
        if not speed:
            continue

        # 根据表面类型获取样本数据
        if surface_type == "p1":
            samples = item.get("p1_samples", [])
        elif surface_type == "p2":
            samples = item.get("p2_samples", [])
        else:  # st
            samples = item.get("sum_samples", [])

        # 计算统计数据
        median = np.median(samples) if samples else 0
        std = np.std(samples) if samples else 0
        cv = std / median if median > 0 else 0
        count = len(samples)
        min_val = min(samples) if samples else 0
        max_val = max(samples) if samples else 0

        stats_data.append(
            {
                "speed": speed,
                f"{surface_type}_median": median,
                f"{surface_type}_std": std,
                f"{surface_type}_cv": cv,
                f"{surface_type}_count": count,
                f"{surface_type}_min": min_val,
                f"{surface_type}_max": max_val,
            }
        )

    # 生成HTML报告
    html_content = generate_single_surface_stats_html(stats_data, surface_type)
    html_path = os.path.join(output_folder, f"{output_prefix}_{surface_type}_stats.html")
    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    except (IOError, OSError) as e:
        logger.error("写入文件失败 %s: %s", html_path, str(e))

    # 生成CSV报告
    csv_content = generate_single_surface_stats_csv(stats_data, surface_type)
    csv_path = os.path.join(output_folder, f"{output_prefix}_{surface_type}_stats.csv")
    try:
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(csv_content)
    except (IOError, OSError) as e:
        logger.error("写入文件失败 %s: %s", csv_path, str(e))

    return html_path, csv_path


def generate_stats_html(stats_data):
    """
    生成统计报告HTML

    Args:
        stats_data: 统计数据

    Returns:
        str: HTML内容
    """
    html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>统计分析报告</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .stats-container { max-width: 1200px; margin: 0 auto; }
        </style>
    </head>
    <body>
        <div class="stats-container">
            <h1 class="text-center">统计分析报告</h1>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>转速</th>
                        <th>P1面中位数</th>
                        <th>P1面标准差</th>
                        <th>P1面变异系数</th>
                        <th>P1面数据量</th>
                        <th>P2面中位数</th>
                        <th>P2面标准差</th>
                        <th>P2面变异系数</th>
                        <th>P2面数据量</th>
                        <th>ST面中位数</th>
                        <th>ST面标准差</th>
                        <th>ST面变异系数</th>
                        <th>ST面数据量</th>
                    </tr>
                </thead>
                <tbody>
    """

    for item in stats_data:
        html += f"""
                    <tr>
                        <td>{item.get("speed", "")}</td>
                        <td>{item.get("p1_median", 0):.2f}</td>
                        <td>{item.get("p1_std", 0):.2f}</td>
                        <td>{item.get("p1_cv", 0):.2f}</td>
                        <td>{item.get("p1_count", 0)}</td>
                        <td>{item.get("p2_median", 0):.2f}</td>
                        <td>{item.get("p2_std", 0):.2f}</td>
                        <td>{item.get("p2_cv", 0):.2f}</td>
                        <td>{item.get("p2_count", 0)}</td>
                        <td>{item.get("st_median", 0):.2f}</td>
                        <td>{item.get("st_std", 0):.2f}</td>
                        <td>{item.get("st_cv", 0):.2f}</td>
                        <td>{item.get("st_count", 0)}</td>
                    </tr>
        """

    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    return html


def generate_stats_csv(stats_data):
    """
    生成统计报告CSV

    Args:
        stats_data: 统计数据

    Returns:
        str: CSV内容
    """
    csv = "转速,P1面中位数,P1面标准差,P1面变异系数,P1面数据量,P2面中位数,P2面标准差,P2面变异系数,P2面数据量,ST面中位数,ST面标准差,ST面变异系数,ST面数据量\n"

    for item in stats_data:
        csv += f"{item.get('speed', '')},{item.get('p1_median', 0):.2f},{item.get('p1_std', 0):.2f},{item.get('p1_cv', 0):.2f},{item.get('p1_count', 0)},{item.get('p2_median', 0):.2f},{item.get('p2_std', 0):.2f},{item.get('p2_cv', 0):.2f},{item.get('p2_count', 0)},{item.get('st_median', 0):.2f},{item.get('st_std', 0):.2f},{item.get('st_cv', 0):.2f},{item.get('st_count', 0)}\n"

    return csv


def generate_single_surface_stats_html(stats_data, surface_type):
    """
    生成单个面的统计报告HTML

    Args:
        stats_data: 统计数据
        surface_type: 表面类型

    Returns:
        str: HTML内容
    """
    surface_name = {"p1": "P1面", "p2": "P2面", "st": "ST面"}.get(
        surface_type, surface_type.upper()
    )

    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{surface_name}统计分析报告</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .stats-container {{ max-width: 800px; margin: 0 auto; }}
        </style>
    </head>
    <body>
        <div class="stats-container">
            <h1 class="text-center">{surface_name}统计分析报告</h1>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>转速</th>
                        <th>中位数</th>
                        <th>标准差</th>
                        <th>变异系数</th>
                        <th>数据量</th>
                        <th>最小值</th>
                        <th>最大值</th>
                    </tr>
                </thead>
                <tbody>
    """

    for item in stats_data:
        html += f"""
                    <tr>
                        <td>{item.get("speed", "")}</td>
                        <td>{item.get(f"{surface_type}_median", 0):.2f}</td>
                        <td>{item.get(f"{surface_type}_std", 0):.2f}</td>
                        <td>{item.get(f"{surface_type}_cv", 0):.2f}</td>
                        <td>{item.get(f"{surface_type}_count", 0)}</td>
                        <td>{item.get(f"{surface_type}_min", 0):.2f}</td>
                        <td>{item.get(f"{surface_type}_max", 0):.2f}</td>
                    </tr>
        """

    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    return html


def generate_single_surface_stats_csv(stats_data, surface_type):
    """
    生成单个面的统计报告CSV

    Args:
        stats_data: 统计数据
        surface_type: 表面类型

    Returns:
        str: CSV内容
    """
    csv = "转速,中位数,标准差,变异系数,数据量,最小值,最大值\n"

    for item in stats_data:
        csv += f"{item.get('speed', '')},{item.get(f'{surface_type}_median', 0):.2f},{item.get(f'{surface_type}_std', 0):.2f},{item.get(f'{surface_type}_cv', 0):.2f},{item.get(f'{surface_type}_count', 0)},{item.get(f'{surface_type}_min', 0):.2f},{item.get(f'{surface_type}_max', 0):.2f}\n"

    return csv
