import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


# ========== 辅助函数：计算单个面的统计量 ==========
def calculate_surface_stats(samples: List[float], face_prefix: str) -> Dict[str, str]:
    """
    计算单个面的统计量

    Args:
        samples: 样本数据列表
        face_prefix: 面的前缀（如'P1'、'P2'、'ST面'）

    Returns:
        dict: 包含该面所有统计量的字典
    """
    # 过滤NaN值
    filtered_samples: List[float] = [val for val in samples if not pd.isna(val)]
    if not filtered_samples:
        return {}

    # 只创建一次Series对象，提高性能，使用过滤后的数据避免"Mean of empty slice"错误
    series = pd.Series(filtered_samples)

    # 计算统计量
    mean_val = float(series.mean())
    std_val = float(series.std())
    median_val = float(series.median())
    q25 = float(series.quantile(0.25))
    q75 = float(series.quantile(0.75))
    iqr_val = q75 - q25
    cv_val = (std_val / mean_val * 100) if mean_val != 0 else "inf"
    min_val = min(filtered_samples)
    max_val = max(filtered_samples)

    # 构建统计结果字典
    stats = {
        f"{face_prefix}-平均值": str(round(mean_val, 2)),
        f"{face_prefix}-中位数": str(round(median_val, 2)),
        f"{face_prefix}-标准差": str(round(std_val, 2)),
        f"{face_prefix}-最小值": str(round(min_val, 2)),
        f"{face_prefix}-最大值": str(round(max_val, 2)),
        f"{face_prefix}-IQR": str(round(iqr_val, 2)),
        f"{face_prefix}-CV": str(round(float(cv_val), 2)) if cv_val != "inf" else "inf",
    }

    return stats


# ========== 统计数据生成函数 ==========
def generate_stats_data(parsed_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    从解析后的数据生成统计数据结构

    Args:
        parsed_data: 解析后的数据，包含各个转速下的P1/P2/ST面数据

    Returns:
        list: 统计数据列表，每个元素包含一个转速的所有面统计数据
    """
    stats_data: List[Dict[str, str]] = []
    for item in parsed_data:
        speed = str(item["speed"])
        stat_row: Dict[str, str] = {"转速": speed}

        # P1面数据处理
        if "p1_samples" in item and item["p1_samples"]:
            stat_row.update(calculate_surface_stats(item["p1_samples"], "P1"))

        # P2面数据处理
        if "p2_samples" in item and item["p2_samples"]:
            stat_row.update(calculate_surface_stats(item["p2_samples"], "P2"))

        # ST面数据处理
        if "sum_samples" in item and item["sum_samples"]:
            stat_row.update(calculate_surface_stats(item["sum_samples"], "ST面"))

        stats_data.append(stat_row)

    return stats_data


# ========== 辅助函数：从统计数据中提取面的最小IQR和CV值 ==========
def extract_min_values(
    stats_data: List[Dict[str, str]],
) -> Tuple[Dict[str, List[float]], Dict[str, Optional[float]]]:
    """
    从统计数据中提取各面的最小IQR值和最小CV值

    Args:
        stats_data: 统计数据列表

    Returns:
        tuple: (extracted_values, min_values)
               - extracted_values: 各面的IQR和CV值列表
               - min_values: 各面的最小IQR值和最小CV值
    """
    # 初始化提取的值
    extracted_values: Dict[str, List[float]] = {
        "p1_iqr": [],
        "p1_cv": [],
        "p2_iqr": [],
        "p2_cv": [],
        "st_iqr": [],
        "st_cv": [],
    }

    # 安全提取各面数据
    for row in stats_data:
        # P1面数据
        if "P1-IQR" in row:
            try:
                extracted_values["p1_iqr"].append(float(row["P1-IQR"]))
            except (ValueError, TypeError):
                pass
        if "P1-CV" in row and row["P1-CV"] != "inf":
            try:
                extracted_values["p1_cv"].append(float(row["P1-CV"]))
            except (ValueError, TypeError):
                pass

        # P2面数据
        if "P2-IQR" in row:
            try:
                extracted_values["p2_iqr"].append(float(row["P2-IQR"]))
            except (ValueError, TypeError):
                pass
        if "P2-CV" in row and row["P2-CV"] != "inf":
            try:
                extracted_values["p2_cv"].append(float(row["P2-CV"]))
            except (ValueError, TypeError):
                pass

        # ST面数据
        if "ST面-IQR" in row:
            try:
                extracted_values["st_iqr"].append(float(row["ST面-IQR"]))
            except (ValueError, TypeError):
                pass
        if "ST面-CV" in row and row["ST面-CV"] != "inf":
            try:
                extracted_values["st_cv"].append(float(row["ST面-CV"]))
            except (ValueError, TypeError):
                pass

    # 计算最小值
    min_values = {
        "min_p1_iqr": (
            min(extracted_values["p1_iqr"]) if extracted_values["p1_iqr"] else None
        ),
        "min_p1_cv": (
            min(extracted_values["p1_cv"]) if extracted_values["p1_cv"] else None
        ),
        "min_p2_iqr": (
            min(extracted_values["p2_iqr"]) if extracted_values["p2_iqr"] else None
        ),
        "min_p2_cv": (
            min(extracted_values["p2_cv"]) if extracted_values["p2_cv"] else None
        ),
        "min_st_iqr": (
            min(extracted_values["st_iqr"]) if extracted_values["st_iqr"] else None
        ),
        "min_st_cv": (
            min(extracted_values["st_cv"]) if extracted_values["st_cv"] else None
        ),
    }

    return extracted_values, min_values


# ========== 辅助函数：获取最小IQR和CV对应的转速 ==========
def get_min_value_speeds(
    stats_data: List[Dict[str, str]], min_values: Dict[str, Optional[float]]
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    获取各面最小IQR和最小CV对应的转速

    Args:
        stats_data: 统计数据列表
        min_values: 各面的最小IQR值和最小CV值

    Returns:
        tuple: (all_min_iqr_speeds, all_min_cv_speeds)
               - all_min_iqr_speeds: 各面最小IQR对应的转速
               - all_min_cv_speeds: 各面最小CV对应的转速
    """
    all_min_iqr_speeds = {}
    all_min_cv_speeds = {}

    # 定义面的配置，避免重复代码
    face_configs = [
        ("P1", "P1-IQR", "P1-CV", "min_p1_iqr", "min_p1_cv"),
        ("P2", "P2-IQR", "P2-CV", "min_p2_iqr", "min_p2_cv"),
        ("ST", "ST面-IQR", "ST面-CV", "min_st_iqr", "min_st_cv"),
    ]

    # 遍历所有面，统一处理逻辑
    for face_name, iqr_key, cv_key, min_iqr_key, min_cv_key in face_configs:
        # 处理IQR
        if min_values[min_iqr_key] is not None:
            min_iqr = min_values[min_iqr_key]
            min_iqr_speeds = [
                row["转速"]
                for row in stats_data
                if iqr_key in row and float(row[iqr_key]) == min_iqr
            ]
            all_min_iqr_speeds[face_name] = min_iqr_speeds

        # 处理CV
        if min_values[min_cv_key] is not None:
            min_cv = min_values[min_cv_key]
            min_cv_speeds = [
                row["转速"]
                for row in stats_data
                if cv_key in row and float(row[cv_key]) == min_cv
            ]
            all_min_cv_speeds[face_name] = min_cv_speeds

    return all_min_iqr_speeds, all_min_cv_speeds


# ========== 辅助函数：计算单个面的得分 ==========
def calculate_face_score(
    row: Dict[str, str], face_prefix: str, weights: Dict[str, float]
) -> Tuple[float, Dict[str, Any]]:
    """
    计算单个面的得分

    Args:
        row: 单个转速的统计数据
        face_prefix: 面前缀（如'P1'、'P2'、'ST面'）
        weights: 各面的权重

    Returns:
        tuple: (face_score, detailed_face_score)
               - face_score: 该面的得分
               - detailed_face_score: 该面的详细得分信息
    """
    face_key = face_prefix.split("-")[0] if "-" in face_prefix else face_prefix
    iqr_key = f"{face_prefix}-IQR"
    cv_key = f"{face_prefix}-CV"

    face_score = 0.0
    detailed_face_score: Dict[str, Optional[float]] = {
        "iqr": None,
        "cv": None,
        "iqr_score": None,
        "cv_score": None,
        "face_score": None,
    }

    if iqr_key in row and cv_key in row:
        try:
            iqr_val = float(row[iqr_key])
            cv_val = float(row[cv_key]) if row[cv_key] != "inf" else None

            if cv_val is not None and cv_val != float("inf"):
                # 归一化处理，值越小得分越高
                iqr_score = 1.0 / (1.0 + iqr_val)
                cv_score = 1.0 / (1.0 + cv_val / 100.0)  # CV是百分比，适当缩放
                # 面内综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分
                face_score = 0.5 * iqr_score + 0.5 * cv_score
                # 面间综合：总得分 += 面权重 × 面得分
                face_score *= weights.get(face_key, 0.0)

                detailed_face_score = {
                    "iqr": iqr_val,
                    "cv": cv_val,
                    "iqr_score": iqr_score,
                    "cv_score": cv_score,
                    "face_score": face_score
                    / weights.get(face_key, 1.0),  # 保存归一化前的面得分
                }
        except (ValueError, TypeError):
            pass

    return face_score, detailed_face_score


# ========== 统计报告生成函数（保持之前的修复，键名统一） ==========
def calculate_optimal_speed_evaluation(
    stats_data: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    计算最优转速并生成详细评估报告

    Args:
        stats_data: 统计数据，包含各个转速下的P1/P2/ST面数据

    Returns:
        dict: 包含最优转速评估详细信息的字典
    """
    # 提取最小值
    _, min_values = extract_min_values(stats_data)

    # 获取最小IQR和CV对应的转速
    all_min_iqr_speeds, all_min_cv_speeds = get_min_value_speeds(stats_data, min_values)

    # 使用加权评分法（P1/P2/ST面按0.4/0.4/0.2权重）
    weights = {"P1": 0.4, "P2": 0.4, "ST": 0.2}
    speed_scores: Dict[str, float] = {}
    speed_detailed_scores: Dict[str, Dict[str, Any]] = {}

    # 面配置，避免重复代码
    face_processing = [("P1", "P1"), ("P2", "P2"), ("ST", "ST面")]

    # 计算每个转速的详细得分信息
    for row in stats_data:
        speed = row["转速"]
        total_score = 0.0

        # 初始化详细得分
        detailed_scores = {
            "P1": {
                "iqr": None,
                "cv": None,
                "iqr_score": None,
                "cv_score": None,
                "face_score": None,
            },
            "P2": {
                "iqr": None,
                "cv": None,
                "iqr_score": None,
                "cv_score": None,
                "face_score": None,
            },
            "ST": {
                "iqr": None,
                "cv": None,
                "iqr_score": None,
                "cv_score": None,
                "face_score": None,
            },
            "total_score": 0.0,
        }

        # 遍历所有面，统一计算得分
        for face_name, face_prefix in face_processing:
            face_score, detailed_scores[face_name] = calculate_face_score(
                row, face_prefix, weights
            )
            total_score += face_score

        # 保存得分
        speed_scores[speed] = total_score
        detailed_scores["total_score"] = total_score
        speed_detailed_scores[speed] = detailed_scores

    # 选出得分最高的转速作为最优转速
    best_speeds: List[str] = []
    best_score: Optional[float] = None

    if speed_scores:
        best_score = max(speed_scores.values())
        best_speeds = [
            speed for speed, score in speed_scores.items() if score == best_score
        ]

    # 确定有哪些面需要显示（只有当该面在任何一行中有数据时才显示）
    has_p1 = any("P1-IQR" in row for row in stats_data)
    has_p2 = any("P2-IQR" in row for row in stats_data)
    has_st = any("ST面-IQR" in row for row in stats_data)

    # 生成最优转速评估报告
    return {
        "best_speeds": best_speeds,
        "best_score": best_score,
        "speed_detailed_scores": speed_detailed_scores,
        "weights": weights,
        "has_p1": has_p1,
        "has_p2": has_p2,
        "has_st": has_st,
        "all_min_iqr_speeds": all_min_iqr_speeds,
        "all_min_cv_speeds": all_min_cv_speeds,
    }


# ========== 辅助函数：生成HTML头部 ==========
def generate_html_header(best_comprehensive_speeds: List[str], has_st: bool) -> str:
    """
    生成统计报告HTML头部

    Args:
        best_comprehensive_speeds: 综合评估最优转速列表
        has_st: 是否存在ST面数据

    Returns:
        str: HTML头部内容
    """
    stats_html = f"""
        <div class="mb-2">
            <i class="bi bi-star text-success"></i> 最优转速（综合评估）：{', '.join(best_comprehensive_speeds)}
            <span class="text-muted ms-2">（综合考虑IQR和变异系数，采用加权评分法）</span>
        </div>
        """

    if has_st:
        stats_html += """
        <div class="mb-2 text-muted">
            <i class="bi bi-info-circle me-1"></i> ST面数据基于上传文件数据
        </div>
        """

    return stats_html


# ========== 辅助函数：生成HTML表格结构 ==========
def generate_table_structure(has_p1: bool, has_p2: bool, has_st: bool) -> str:
    """
    生成统计报告HTML表格结构

    Args:
        has_p1: 是否存在P1面数据
        has_p2: 是否存在P2面数据
        has_st: 是否存在ST面数据

    Returns:
        str: HTML表格结构内容
    """
    table_html = """
        <table class="table table-striped table-hover table-sm table-statistics">
            <thead class="header-main">
                <tr>
                    <th rowspan="2" class="align-middle text-center">转速</th>
    """

    # 添加表头列
    if has_p1:
        table_html += '<th colspan="7" class="text-center face-p1">P1面</th>'
    if has_p2:
        table_html += '<th colspan="7" class="text-center face-p2">P2面</th>'
    if has_st:
        table_html += '<th colspan="7" class="text-center face-st">ST面</th>'

    table_html += (
        '<th rowspan="2" class="align-middle text-center evaluation-col">综合评估</th>'
    )
    table_html += (
        '<th rowspan="2" class="align-middle text-center evaluation-col">稳定等级</th>'
    )

    table_html += """
                </tr>
                <tr class="header-sub">
    """

    # 添加子表头
    if has_p1:
        table_html += '<th class="face-p1">平均值</th><th class="face-p1">中位数</th><th class="face-p1">标准差</th><th class="face-p1">最小值</th><th class="face-p1">最大值</th><th class="face-p1">IQR</th><th class="face-p1">CV(%)</th>'
    if has_p2:
        table_html += '<th class="face-p2">平均值</th><th class="face-p2">中位数</th><th class="face-p2">标准差</th><th class="face-p2">最小值</th><th class="face-p2">最大值</th><th class="face-p2">IQR</th><th class="face-p2">CV(%)</th>'
    if has_st:
        table_html += '<th class="face-st">平均值</th><th class="face-st">中位数</th><th class="face-st">标准差</th><th class="face-st">最小值</th><th class="face-st">最大值</th><th class="face-st">IQR</th><th class="face-st">CV(%)</th>'

    table_html += """
                </tr>
            </thead>
            <tbody>
        """

    return table_html


# ========== 辅助函数：计算转速评分和排名 ==========
def calculate_speed_rankings(
    stats_data: List[Dict[str, str]], speed_detailed_scores: Dict[str, Dict[str, Any]]
) -> Tuple[Dict[str, float], Dict[str, int], List[str]]:
    """
    计算每个转速的综合评分和排名

    Args:
        stats_data: 统计数据列表
        speed_detailed_scores: 各转速的详细得分信息

    Returns:
        tuple: (speed_scores, rankings, best_speeds)
               - speed_scores: 各转速的综合评分
               - rankings: 各转速的排名
               - best_speeds: 最优转速列表
    """
    # 计算每个转速的综合评分
    speed_scores = {
        row["转速"]: speed_detailed_scores[row["转速"]]["total_score"]
        for row in stats_data
        if row["转速"] in speed_detailed_scores
    }

    # 根据综合得分排序，计算排名
    sorted_scores = sorted(speed_scores.items(), key=lambda x: x[1], reverse=True)
    rankings = {speed: rank + 1 for rank, (speed, score) in enumerate(sorted_scores)}

    # 确定最优转速（综合得分最高的转速）
    best_speeds = [item[0] for item in sorted_scores[:1]] if sorted_scores else []

    return speed_scores, rankings, best_speeds


# ========== 辅助函数：生成HTML行数据 ==========
def generate_html_row(
    row: Dict[str, str],
    has_p1: bool,
    has_p2: bool,
    has_st: bool,
    min_values: Dict[str, Optional[float]],
    speed_scores: Dict[str, float],
    rankings: Dict[str, int],
    best_speeds: List[str],
) -> str:
    """
    生成统计报告HTML表格的行数据

    Args:
        row: 单个转速的统计数据
        has_p1: 是否存在P1面数据
        has_p2: 是否存在P2面数据
        has_st: 是否存在ST面数据
        min_values: 各面的最小IQR和CV值
        speed_scores: 各转速的综合评分
        rankings: 各转速的排名
        best_speeds: 最优转速列表

    Returns:
        str: HTML表格行内容
    """
    # 最优转速行添加浅绿色高亮
    is_best_speed = row["转速"] in best_speeds
    row_highlight = "table-success" if is_best_speed else ""

    row_html = f'<tr class="{row_highlight}"><td>{row["转速"]}</td>'

    # 添加P1面数据
    if has_p1:
        if "P1-IQR" in row:
            p1_iqr_highlight = (
                "table-warning"
                if min_values["min_p1_iqr"] is not None
                and float(row["P1-IQR"]) == min_values["min_p1_iqr"]
                else ""
            )
            row_html += f"""
                    <!-- P1面数据 -->
                    <td>{row['P1-平均值']}</td><td>{row['P1-中位数']}</td><td>{row['P1-标准差']}</td>
                    <td>{row['P1-最小值']}</td><td>{row['P1-最大值']}</td><td class="{p1_iqr_highlight}">{row['P1-IQR']}</td><td>{row['P1-CV']}</td>
                    """
        else:
            row_html += "<!-- P1面数据缺失 --><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>"

    # 添加P2面数据
    if has_p2:
        if "P2-IQR" in row:
            p2_iqr_highlight = (
                "table-warning"
                if min_values["min_p2_iqr"] is not None
                and float(row["P2-IQR"]) == min_values["min_p2_iqr"]
                else ""
            )
            row_html += f"""
                    <!-- P2面数据 -->
                    <td>{row['P2-平均值']}</td><td>{row['P2-中位数']}</td><td>{row['P2-标准差']}</td>
                    <td>{row['P2-最小值']}</td><td>{row['P2-最大值']}</td><td class="{p2_iqr_highlight}">{row['P2-IQR']}</td><td>{row['P2-CV']}</td>
                    """
        else:
            row_html += "<!-- P2面数据缺失 --><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>"

    # 添加ST面数据
    if has_st:
        if "ST面-IQR" in row:
            st_iqr_highlight = (
                "table-warning"
                if min_values["min_st_iqr"] is not None
                and float(row["ST面-IQR"]) == min_values["min_st_iqr"]
                else ""
            )
            row_html += f"""
                    <!-- ST面数据 -->
                    <td>{row['ST面-平均值']}</td><td>{row['ST面-中位数']}</td><td>{row['ST面-标准差']}</td>
                    <td>{row['ST面-最小值']}</td><td>{row['ST面-最大值']}</td><td class="{st_iqr_highlight}">{row['ST面-IQR']}</td><td>{row['ST面-CV']}</td>
                    """
        else:
            row_html += "<!-- ST面数据缺失 --><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>"

    # 综合评价和稳定等级
    score = speed_scores.get(row["转速"], 0)
    comprehensive_rating = f"{score:.2f}" if score else "N/A"
    stability_level = rankings.get(row["转速"], len(rankings))
    row_html += f"<td>{comprehensive_rating}</td><td>{stability_level}</td>"

    row_html += "</tr>"
    return row_html


# ========== 主函数：生成统计报告 ==========
def generate_stats(
    parsed_data: List[Dict[str, Any]], output_prefix: str, output_folder: str
) -> Tuple[str, str]:
    """
    生成P1/P2/ST面三栏对比统计报告，高亮最优转速

    Args:
        parsed_data: 解析后的数据，包含各个转速下的P1/P2/ST面数据
        output_prefix: 输出文件名前缀
        output_folder: 输出文件夹路径

    Returns:
        tuple: (stats_html, stats_csv)
               - stats_html: 统计报告HTML内容
               - stats_csv: 统计报告CSV文件路径
    """
    try:
        # 收集所有面的数据
        stats_data = generate_stats_data(parsed_data)

        # 计算各面的最小IQR值和最小CV值
        _, min_values = extract_min_values(stats_data)

        # 确定有哪些面需要显示
        has_p1 = any("P1-IQR" in row for row in stats_data)
        has_p2 = any("P2-IQR" in row for row in stats_data)
        has_st = any("ST面-IQR" in row for row in stats_data)

        # 使用统一的加权评分法确定最优转速
        evaluation_report = calculate_optimal_speed_evaluation(stats_data)
        best_comprehensive_speeds = evaluation_report["best_speeds"]
        speed_detailed_scores = evaluation_report["speed_detailed_scores"]

        # 生成HTML报告
        stats_html = generate_html_header(best_comprehensive_speeds, has_st)
        stats_html += generate_table_structure(has_p1, has_p2, has_st)

        # 计算转速评分和排名
        speed_scores, rankings, best_speeds = calculate_speed_rankings(
            stats_data, speed_detailed_scores
        )

        # 生成表格行数据
        for row in stats_data:
            stats_html += generate_html_row(
                row,
                has_p1,
                has_p2,
                has_st,
                min_values,
                speed_scores,
                rankings,
                best_speeds,
            )

        # 结束表格标签
        stats_html += "        </tbody></table>"

        # 生成CSV报告
        stats_df = pd.DataFrame(stats_data)
        stats_csv = os.path.join(output_folder, f"{output_prefix}_stats.csv")
        stats_df.to_csv(stats_csv, index=False, encoding="utf-8-sig")

        return stats_html, stats_csv
    except Exception as e:
        raise Exception(f"统计报告生成失败：{str(e)}")


def generate_single_surface_stats(
    parsed_data: List[Dict[str, Any]],
    output_prefix: str,
    surface_type: str,
    output_folder: str,
) -> Tuple[str, str]:
    """
    生成单个面（P1/P2/ST）的统计报告，高亮最优转速（IQR最小）

    Args:
        parsed_data: 解析后的数据，包含各个转速下的单一面数据
        output_prefix: 输出文件名前缀
        surface_type: 面类型（'p1', 'p2', 'st'）
        output_folder: 输出文件夹路径

    Returns:
        tuple: (stats_html, stats_csv)
               - stats_html: 统计报告HTML内容
               - stats_csv: 统计报告CSV文件路径
    """
    try:
        stats_data: List[Dict[str, str]] = []

        # 确定面的名称和数据键
        surface_name_map = {"p1": "P1", "p2": "P2", "st": "ST面"}
        surface_name = surface_name_map.get(surface_type, "未知面")

        for item in parsed_data:
            speed = str(item["speed"])
            samples = (
                item["p1_samples"]
                if surface_type == "p1"
                else (
                    item["p2_samples"] if surface_type == "p2" else item["sum_samples"]
                )
            )

            # 只有当有数据时才进行统计计算
            if samples:
                # 使用现有的calculate_surface_stats函数计算统计量
                surface_stats = calculate_surface_stats(samples, surface_name)
                if surface_stats:
                    # 转换为单个面报告所需的格式
                    stats_data.append(
                        {
                            "转速": speed,
                            "平均值": surface_stats.get(f"{surface_name}-平均值", "-"),
                            "中位数": surface_stats.get(f"{surface_name}-中位数", "-"),
                            "标准差": surface_stats.get(f"{surface_name}-标准差", "-"),
                            "最小值": surface_stats.get(f"{surface_name}-最小值", "-"),
                            "最大值": surface_stats.get(f"{surface_name}-最大值", "-"),
                            "IQR（四分位距）": surface_stats.get(
                                f"{surface_name}-IQR", "-"
                            ),
                            "变异系数(%)": surface_stats.get(f"{surface_name}-CV", "-"),
                        }
                    )

        # 使用统一的加权评分法确定最优转速
        if stats_data:
            # 计算每个转速的综合得分（基于IQR和CV）
            speed_scores: Dict[str, float] = {}

            for row in stats_data:
                speed = row["转速"]
                iqr_val = (
                    float(row["IQR（四分位距）"])
                    if row["IQR（四分位距）"] != "-"
                    else None
                )
                cv_val = (
                    float(row["变异系数(%)"])
                    if row["变异系数(%)"] != "-" and row["变异系数(%)"] != "inf"
                    else None
                )

                if (
                    iqr_val is not None
                    and cv_val is not None
                    and cv_val != float("inf")
                ):
                    # 归一化处理，值越小得分越高
                    iqr_score = 1.0 / (1.0 + iqr_val)
                    cv_score = 1.0 / (1.0 + cv_val / 100.0)  # CV是百分比，适当缩放
                    # IQR和CV各占50%权重
                    score = 0.5 * iqr_score + 0.5 * cv_score
                    speed_scores[speed] = score
                else:
                    speed_scores[speed] = 0.0

            # 选出得分最高的转速作为最优转速
            if speed_scores:
                best_score = max(speed_scores.values())
                best_speeds = [
                    speed
                    for speed, score in speed_scores.items()
                    if score == best_score
                ]
            else:
                best_speeds = []

            # 根据综合得分排序，计算排名
            sorted_scores = sorted(
                speed_scores.items(), key=lambda x: x[1], reverse=True
            )
            rankings = {
                speed: rank + 1 for rank, (speed, score) in enumerate(sorted_scores)
            }
        else:
            best_speeds = []
            speed_scores = {}
            rankings = {}

        # 生成HTML表格
        surface_name_display = {"p1": "P1", "p2": "P2", "st": "ST"}[surface_type]

        # 生成HTML表格头部
        stats_html = f"""
        <div class="mb-2">
            <i class="bi bi-star text-success"></i> 最优转速{('（' + surface_name_display + '面数据最集中，IQR最小）：' + ', '.join(best_speeds)) if best_speeds else '：无'}
            <span class="text-muted ms-2">（IQR：反映中间50%数据的离散程度，越小越稳定，不受极端值干扰）</span>
        </div>
        """

        # 当没有最优转速时（这种情况实际上不会出现，因为我们总是会选择得分最高的转速）
        if not best_speeds:
            stats_html += f"""
            <div class="mb-2">
                <i class="bi bi-star text-success"></i> 最优转速（综合评估）：无
                <span class="text-muted ms-2">（综合考虑IQR和变异系数，采用加权评分法）</span>
            </div>
            """

        stats_html += f"""        <table class="table table-striped table-hover table-sm">
            <thead class="table-light">
                <tr>
                    <th rowspan="2" class="align-middle text-center">转速</th>
                    <th colspan="7" class="text-center bg-primary text-white">{surface_name_display}面</th>
                    <th rowspan="2" class="align-middle text-center">综合评估</th>
                    <th rowspan="2" class="align-middle text-center">稳定等级</th>
                </tr>
                <tr>
                    <th>平均值</th><th>中位数</th><th>标准差</th><th>最小值</th><th>最大值</th><th>IQR（四分位距）</th><th>变异系数(%)</th>
                </tr>
            </thead>
            <tbody>
        """

        for row in stats_data:
            # 最优转速行添加浅绿色高亮
            is_best_speed = row["转速"] in best_speeds
            row_highlight = (
                "table-success" if is_best_speed else ""
            )  # 使用Bootstrap的table-success类

            # IQR最小值单元格高亮
            iqr_values_list = [float(r["IQR（四分位距）"]) for r in stats_data]
            min_iqr = min(iqr_values_list) if iqr_values_list else None
            iqr_highlight = (
                "table-warning"
                if min_iqr is not None and float(row["IQR（四分位距）"]) == min_iqr
                else ""
            )  # 使用Bootstrap的table-warning类

            # 综合评价和稳定等级
            # 综合评价显示最优转速选择方法的计算结果，保留两位小数
            score = speed_scores.get(row["转速"], 0.0)
            comprehensive_rating = f"{score:.2f}" if score else "N/A"
            stability_level = rankings.get(row["转速"], len(rankings))

            stats_html += f"""
                <tr class="{row_highlight}">
                    <td>{row['转速']}</td>
                    <td>{row['平均值']}</td><td>{row['中位数']}</td><td>{row['标准差']}</td>
                    <td>{row['最小值']}</td><td>{row['最大值']}</td><td class="{iqr_highlight}">{row['IQR（四分位距）']}</td><td>{row['变异系数(%)']}</td><td>{comprehensive_rating}</td><td>{stability_level}</td>
                </tr>
            """
        stats_html += "</tbody></table>"

        # 生成CSV报告
        stats_df = pd.DataFrame(list(stats_data))  # 确保stats_data是列表而不是生成器
        stats_csv = os.path.join(
            output_folder, f"{output_prefix}_{surface_type}_stats.csv"
        )
        stats_df.to_csv(stats_csv, index=False, encoding="utf-8-sig")

        return stats_html, stats_csv
    except Exception as e:
        raise Exception(f"单面带统计报告生成失败：{str(e)}")
