# 导入模块
import gc
import json
import os
import html
from typing import Dict

import numpy as np
import pandas as pd

from utils.chart_cache import chart_cache

# 数据库连接配置
DB_CONNECTED = False
db = None
ChartCache = None

print("图表生成模块初始化成功")

# 图表类型配置 - 统一管理所有图表类型的名称、图标、颜色和说明
CHART_TYPE_CONFIG = {
    "trend": {
        "name": "趋势图",
        "icon": "bi-trend-up",
        "color": "text-success",
        "annotation": "<b>图表指标说明：</b><br>• 线条：中位数变化趋势<br>• X轴：转速<br>• Y轴：中位数<br>• 圆点：各转速的具体中位数值",
    },
    "scatter": {
        "name": "散点图",
        "icon": "bi-scatter",
        "color": "text-info",
        "annotation": "<b>图表指标说明：</b><br>• 圆点：各数据点<br>• 彩色线和圆点：各转速中位数<br>• 线条走势：中位数变化趋势<br>• 点的密集程度：数据离散情况",
    },
    "box": {
        "name": "箱线图",
        "icon": "bi-box-seam",
        "color": "text-primary",
        "annotation": "<b>图表指标说明：</b><br>• 箱体：包含50%数据的四分位距(IQR)<br>• 中位数线：数据的中位数<br>• 上下须：数据范围(1.5×IQR内)<br>• 圆点：异常值",
    },
    "violin": {
        "name": "小提琴图",
        "icon": "bi-music-note-list",
        "color": "text-purple",
        "annotation": "<b>图表指标说明：</b><br>• 小提琴形状：数据分布密度<br>• 中间粗线：数据中位数<br>• 形状宽度：数据密度<br>• 形状高度：数据范围",
    },
    "heatmap": {
        "name": "热力图",
        "icon": "bi-thermometer-half",
        "color": "text-warning",
        "annotation": "<b>图表指标说明：</b><br>• X轴：转速<br>• Y轴：数据点索引<br>• 颜色深浅：不平衡量数值大小<br>• 颜色越黄：数值越大<br>• 颜色越蓝：数值越小",
    },
    "histogram": {
        "name": "直方图",
        "icon": "bi-bar-chart-line",
        "color": "text-danger",
        "annotation": "<b>图表指标说明：</b><br>• X轴：不平衡量数值区间<br>• Y轴：落在各区间的频次<br>• 柱形高度：数据分布情况<br>• 峰值位置：数据集中的区间",
    },
    "radar": {
        "name": "雷达图",
        "icon": "bi-radar",
        "color": "text-dark",
        "annotation": "<b>图表指标说明：</b><br>• 多边形：各项指标的数值<br>• 轴数：指标数量<br>• 多边形大小：数值大小比较<br>• 数据点：显示具体数值<br>• 渐变色填充：增强区分度",
    },
    "3d": {
        "name": "3D散点图",
        "icon": "bi-cube",
        "color": "text-secondary",
        "annotation": "<b>图表指标说明：</b><br>• X轴：转速<br>• Y轴：数据点索引<br>• Z轴：不平衡量<br>• 点的分布：三维数据关系<br>• 旋转视图：多角度观察<br>• 点大小与透明度：避免视觉重叠",
    },
    "parallel": {
        "name": "平行坐标图",
        "icon": "bi-parallel",
        "color": "text-info",
        "annotation": "<b>图表指标说明：</b><br>• 平行线：各数据点维度<br>• 连线：同一转速下的数据点<br>• 颜色：不同转速区分<br>• 线条交叉：数据点间的关系",
    },
    "bubble": {
        "name": "气泡图",
        "icon": "bi-bubbles",
        "color": "text-primary",
        "annotation": "<b>图表指标说明：</b><br>• X轴：转速<br>• Y轴：不平衡量<br>• 气泡大小：数据点数量<br>• 气泡颜色：中位数大小<br>• 气泡位置：数值分布",
    },
}


def generate_plots(parsed_data, output_prefix, output_folder, chart_types=None):
    """生成双面对比图表（对比图+P1单面带+P2单面带+ST面图）"""
    if chart_types is None:
        chart_types = ["box"]  # 默认只生成箱线图

    try:
        # 生成数据哈希值，用于缓存键
        data_hash = chart_cache.generate_data_hash(parsed_data)

        # 准备绘图数据
        p1_data = []  # P1面单独图数据
        p2_data = []  # P2面单独图数据
        sum_data = []  # ST面图数据

        # 关键优化1：分离P1和P2的中位数计算，确保互不干扰
        p1_median_dict = {}  # 存储P1面各转速的中位数：{转速: 中位数}
        p2_median_dict = {}  # 存储P2面各转速的中位数：{转速: 中位数}

        for item in parsed_data:
            speed = str(item["speed"])
            p1_samples = item["p1_samples"]
            p2_samples = item["p2_samples"]

            # 单面带数据
            for val in p1_samples:
                p1_data.append({"转速": speed, "不平衡量": val})
            for val in p2_samples:
                p2_data.append({"转速": speed, "不平衡量": val})

            # ST面数据
            for val in item["sum_samples"]:
                sum_data.append({"转速": speed, "不平衡量ST面": val})

            # 关键优化2：单独计算P1面中位数（仅基于P1样本）
            # 计算P1面中位数，确保数据不为空
            filtered_p1 = [val for val in p1_samples if not pd.isna(val)]
            p1_median = pd.Series(filtered_p1).median() if filtered_p1 else None
            p1_median_dict[speed] = p1_median

            # 关键优化3：单独计算P2面中位数（仅基于P2样本）
            # 计算P2面中位数，确保数据不为空
            filtered_p2 = [val for val in p2_samples if not pd.isna(val)]
            p2_median = pd.Series(filtered_p2).median() if filtered_p2 else None
            p2_median_dict[speed] = p2_median

        # 关键优化4：按转速顺序排序（确保连线顺序正确）
        # 提取所有转速并按数字大小排序（兼容"3000rpm"、"4000"等格式）
        # 处理无数字的情况
        def get_speed_numeric(speed_str):
            """提取转速字符串中的数字部分，返回数值，处理无数字的情况"""
            numeric_part = "".join(filter(str.isdigit, str(speed_str)))
            # 如果没有数字，返回0或按字符串排序
            return float(numeric_part) if numeric_part else float("-inf")

        all_speeds = sorted(p1_median_dict.keys(), key=get_speed_numeric)

        # 提取排序后的中位数数据（确保P1和P2的转速顺序完全一致）
        p1_median_values = [p1_median_dict[speed] for speed in all_speeds]
        p2_median_values = [p2_median_dict[speed] for speed in all_speeds]

        plots = {}

        # 1. P1面图表
        if p1_data:
            # 生成P1面缓存键
            p1_cache_key = chart_cache.generate_cache_key(data_hash, "p1", chart_types)
            # 尝试获取缓存
            cached_p1 = chart_cache.get_cache(p1_cache_key)
            cache_valid = True

            # 检查缓存是否有效（文件是否存在）
            if cached_p1:
                for chart_type, chart_files in cached_p1.items():
                    png_path = os.path.join(output_folder, chart_files["png"])
                    html_path = os.path.join(output_folder, chart_files["html"])
                    if not os.path.exists(png_path) or not os.path.exists(html_path):
                        cache_valid = False
                        break

            if cached_p1 and cache_valid:
                plots["p1"] = cached_p1
            else:
                # 缓存不存在或文件已过期，重新生成图表
                plots["p1"] = generate_generic_charts(
                    data=p1_data,
                    median_dict=p1_median_dict,
                    surface_name="P1面",
                    color="#1f77b4",
                    output_prefix=output_prefix,
                    output_folder=output_folder,
                    chart_types=chart_types,
                    is_st_surface=False,
                    sorted_speeds=all_speeds,
                    median_values=p1_median_values,
                )
                # 存储缓存
                chart_cache.set_cache(p1_cache_key, plots["p1"])

        # 强制垃圾回收以释放内存
        del p1_data
        gc.collect()

        # 2. P2面图表
        if p2_data:
            # 生成P2面缓存键
            p2_cache_key = chart_cache.generate_cache_key(data_hash, "p2", chart_types)
            # 尝试获取缓存
            cached_p2 = chart_cache.get_cache(p2_cache_key)
            cache_valid = True

            # 检查缓存是否有效（文件是否存在）
            if cached_p2:
                for chart_type, chart_files in cached_p2.items():
                    png_path = os.path.join(output_folder, chart_files["png"])
                    html_path = os.path.join(output_folder, chart_files["html"])
                    if not os.path.exists(png_path) or not os.path.exists(html_path):
                        cache_valid = False
                        break

            if cached_p2 and cache_valid:
                plots["p2"] = cached_p2
            else:
                # 缓存不存在或文件已过期，重新生成图表
                plots["p2"] = generate_generic_charts(
                    data=p2_data,
                    median_dict=p2_median_dict,
                    surface_name="P2面",
                    color="#ff7f0e",
                    output_prefix=output_prefix,
                    output_folder=output_folder,
                    chart_types=chart_types,
                    is_st_surface=False,
                    sorted_speeds=all_speeds,
                    median_values=p2_median_values,
                )
                # 存储缓存
                chart_cache.set_cache(p2_cache_key, plots["p2"])

        # 强制垃圾回收以释放内存
        del p2_data
        gc.collect()

        # 3. ST面图表
        if sum_data:
            st_median_dict = {}
            for item in parsed_data:
                speed = str(item["speed"])
                st_samples = item["sum_samples"]
                # 计算ST面中位数，确保数据不为空
                filtered_st = [val for val in st_samples if not pd.isna(val)]
                st_median_dict[speed] = (
                    pd.Series(filtered_st).median() if filtered_st else None
                )

            # 生成ST面缓存键
            st_cache_key = chart_cache.generate_cache_key(data_hash, "st", chart_types)
            # 尝试获取缓存
            cached_st = chart_cache.get_cache(st_cache_key)
            cache_valid = True

            # 检查缓存是否有效（文件是否存在）
            if cached_st:
                for chart_type, chart_files in cached_st.items():
                    png_path = os.path.join(output_folder, chart_files["png"])
                    html_path = os.path.join(output_folder, chart_files["html"])
                    if not os.path.exists(png_path) or not os.path.exists(html_path):
                        cache_valid = False
                        break

            if cached_st and cache_valid:
                plots["sum"] = cached_st
            else:
                # 缓存不存在或文件已过期，重新生成图表
                plots["sum"] = generate_generic_charts(
                    data=sum_data,
                    median_dict=st_median_dict,
                    surface_name="ST面",
                    color="#2ca02c",
                    output_prefix=output_prefix,
                    output_folder=output_folder,
                    chart_types=chart_types,
                    is_st_surface=True,
                )
                # 存储缓存
                chart_cache.set_cache(st_cache_key, plots["sum"])

            # 强制垃圾回收以释放内存
            del sum_data
            gc.collect()

        return plots
    except Exception as e:
        raise Exception(f"图表生成失败：{str(e)}")


def generate_single_surface_plots(
    parsed_data, output_prefix, surface_type, output_folder, chart_types=None
):
    """生成单个面（P1/P2/ST）的图表（添加中文字体配置）"""
    if chart_types is None:
        chart_types = ["box"]  # 默认只生成箱线图

    try:
        # 生成数据哈希值，用于缓存键
        data_hash = chart_cache.generate_data_hash(parsed_data)

        # 生成缓存键
        cache_key = chart_cache.generate_cache_key(data_hash, surface_type, chart_types)

        # 尝试获取缓存
        cached_charts = chart_cache.get_cache(cache_key)
        cache_valid = True

        # 检查缓存是否有效（文件是否存在）
        if cached_charts:
            for chart_type, chart_files in cached_charts.items():
                png_path = os.path.join(output_folder, chart_files["png"])
                html_path = os.path.join(output_folder, chart_files["html"])
                if not os.path.exists(png_path) or not os.path.exists(html_path):
                    cache_valid = False
                    break

        if cached_charts and cache_valid:
            # 缓存存在且有效，直接返回
            if surface_type == "p1":
                return {"p1": cached_charts}
            elif surface_type == "p2":
                return {"p2": cached_charts}
            elif surface_type == "st":
                return {"sum": cached_charts}
            else:
                return {"single": cached_charts}

        # 缓存不存在或文件已过期，生成图表
        plot_data = []
        median_dict = {}  # 存储当前面各转速的中位数

        for item in parsed_data:
            speed = str(item["speed"])
            samples = (
                item["p1_samples"]
                if surface_type == "p1"
                else (
                    item["p2_samples"] if surface_type == "p2" else item["sum_samples"]
                )
            )
            for val in samples:
                plot_data.append({"转速": speed, "不平衡量": val})
            # 单独计算当前面的中位数
            # 计算中位数，确保数据不为空
            filtered_samples = [val for val in samples if not pd.isna(val)]
            median_dict[speed] = (
                pd.Series(filtered_samples).median() if filtered_samples else None
            )

        # 按转速排序
        sorted_speeds = sorted(
            median_dict.keys(), key=lambda x: float("".join(filter(str.isdigit, x)))
        )
        median_values = [median_dict[speed] for speed in sorted_speeds]

        # 生成图表
        color_map = {"p1": "#1f77b4", "p2": "#ff7f0e", "st": "#2ca02c"}
        title_map = {"p1": "P1面", "p2": "P2面", "st": "ST面"}
        color = color_map.get(surface_type, "#1f77b4")
        title = f"{title_map.get(surface_type, surface_type.upper())}面"

        # 生成图表，根据surface_type确定是否为ST面
        is_st = surface_type == "st"
        charts = generate_generic_charts(
            data=plot_data,
            median_dict=median_dict,
            surface_name=title,
            color=color,
            output_prefix=output_prefix,
            output_folder=output_folder,
            chart_types=chart_types,
            is_st_surface=is_st,
            sorted_speeds=sorted_speeds,
            median_values=median_values,
        )

        # 存储缓存
        chart_cache.set_cache(cache_key, charts)

        # 强制垃圾回收以释放内存
        del plot_data
        gc.collect()

        # Return charts with appropriate keys based on surface type
        if surface_type == "p1":
            return {"p1": charts}
        elif surface_type == "p2":
            return {"p2": charts}
        elif surface_type == "st":
            return {"sum": charts}
        else:
            # 确保单面数据也能被正确处理
            return {"single": charts}
    except Exception as e:
        raise Exception(f"单面带图表生成失败：{str(e)}")


def generate_generic_charts(
    data,
    median_dict,
    surface_name,
    color,
    output_prefix,
    output_folder,
    chart_types,
    is_st_surface=False,
    sorted_speeds=None,
    median_values=None,
):
    """生成通用图表（支持普通面和ST面）"""
    charts = {}

    # 准备ECharts数据
    echarts_data = {}
    for chart_type in chart_types:
        # 生成ECharts兼容的数据格式
        raw_data = generate_echarts_data(data, chart_type)
        # 将Python对象转换为JSON字符串，并确保它可以安全地嵌入到HTML属性中
        json_str = json.dumps(raw_data)
        # 对JSON字符串进行HTML转义，确保可以安全地嵌入到HTML属性中
        json_str = html.escape(json_str)
        # 优化：增加JSON字符串长度限制，确保数据完整性
        if len(json_str) > 50000:  # 增加限制，减少数据简化
            # 如果JSON字符串太长，使用简化版本
            simplified_data = []
            # 根据图表类型采用不同的简化策略
            if chart_type == 'box':
                # 箱线图：保留所有数据点，不做简化
                simplified_data = raw_data
            elif chart_type == 'scatter' or chart_type == '3d' or chart_type == 'heatmap':
                # 散点图、3D散点图、热力图：保留更多数据点
                simplified_data = raw_data[:100]  # 增加数据点数量
            elif chart_type == 'trend':
                # 趋势图：保留所有数据点
                simplified_data = raw_data
            elif chart_type == 'histogram':
                # 直方图：保留所有数据点
                simplified_data = raw_data
            elif chart_type == 'bubble':
                # 气泡图：保留更多数据点
                simplified_data = raw_data[:50]  # 增加数据点数量
            elif chart_type == 'violin':
                # 小提琴图：保留所有数据点
                simplified_data = raw_data
            elif chart_type == 'parallel':
                # 平行坐标图：保留更多数据点
                simplified_data = raw_data[:50]  # 增加数据点数量
            else:
                # 默认策略：保留更多数据点
                simplified_data = raw_data[:50]  # 增加数据点数量
            
            # 再次检查长度
            json_str = json.dumps(simplified_data)
            json_str = html.escape(json_str)
            if len(json_str) > 100000:  # 增加限制
                # 如果仍然太长，使用最小简化版本
                minimal_data = []
                if chart_type == 'box':
                    minimal_data = raw_data[:20]  # 保留前20个数据点
                elif chart_type == 'trend':
                    minimal_data = raw_data[:20]  # 保留前20个数据点
                elif chart_type == 'scatter':
                    minimal_data = raw_data[:50]  # 保留前50个数据点
                elif chart_type == 'heatmap':
                    minimal_data = raw_data[:50]  # 保留前50个数据点
                elif chart_type == 'histogram':
                    minimal_data = raw_data[:50]  # 保留前50个数据点
                elif chart_type == 'bubble':
                    minimal_data = raw_data[:20]  # 保留前20个数据点
                elif chart_type == 'violin':
                    minimal_data = raw_data[:20]  # 保留前20个数据点
                elif chart_type == '3d':
                    minimal_data = raw_data[:50]  # 保留前50个数据点
                elif chart_type == 'parallel':
                    minimal_data = raw_data[:20]  # 保留前20个数据点
                else:
                    minimal_data = raw_data[:20]  # 保留前20个数据点
                json_str = json.dumps(minimal_data)
                json_str = html.escape(json_str)
        echarts_data[chart_type] = json_str

    # 为每种图表类型生成空的占位文件路径（仅用于保持缓存结构兼容）
    for chart_type in chart_types:
        chart_filename = (
            f"{output_prefix}_{surface_name.lower().replace('面', '')}_{chart_type}"
        )
        png_path = os.path.join(output_folder, f"{chart_filename}.png")
        html_path = os.path.join(output_folder, f"{chart_filename}.html")

        # 创建空的HTML文件作为占位
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(f"<div id='chart-container' style='width: 100%; height: 400px;'></div>")

        # 保存图表文件路径和ECharts数据
        charts[chart_type] = {
            "png": os.path.basename(png_path),
            "html": os.path.basename(html_path),
            "echarts_data": echarts_data[chart_type]  # 添加ECharts数据
        }

    # 强制垃圾回收（仅在非ST面调用，因为ST面可能需要保留数据）
    if not is_st_surface:
        gc.collect()

    return charts


def generate_echarts_data(data, chart_type):
    """
    生成ECharts兼容的数据格式
    
    参数:
        data: 原始数据，格式为列表，每个元素为字典，包含"转速"和值字段
        chart_type: 图表类型
    
    返回:
        适合ECharts使用的数据格式，Python对象格式
    """
    import time
    start_time = time.time()
    
    if not data or not isinstance(data, list):
        print(f"数据为空或格式错误，耗时: {time.time() - start_time:.4f}s")
        return []
    
    # 确保数据格式正确
    try:
        # 验证数据中的每个元素是否是字典
        valid_data = []
        for item in data:
            if isinstance(item, dict):
                valid_data.append(item)
        if not valid_data:
            print(f"无有效数据元素，耗时: {time.time() - start_time:.4f}s")
            return []
        data = valid_data
    except Exception as e:
        print(f"数据格式验证失败: {str(e)}, 耗时: {time.time() - start_time:.4f}s")
        return []
    
    # 自动检测值字段
    value_field = "不平衡量"
    if data and isinstance(data[0], dict):
        if "不平衡量ST面" in data[0]:
            value_field = "不平衡量ST面"
        elif "不平衡量" not in data[0]:
            # 尝试找到包含"不平衡量"的字段
            for key in data[0].keys():
                if "不平衡量" in key:
                    value_field = key
                    break
    
    # 按转速分组
    grouped_data = {}
    for item in data:
        speed = str(item.get("转速", "未知"))
        value = item.get(value_field, 0)
        if speed not in grouped_data:
            grouped_data[speed] = []
        grouped_data[speed].append(value)
    
    # 根据图表类型生成不同的数据格式
    result = []
    if chart_type == "box":
        # 箱线图数据格式
        box_data = []
        for speed, values in grouped_data.items():
            # 过滤掉None和NaN值
            values = [v for v in values if v is not None and not pd.isna(v)]
            values.sort()
            n = len(values)
            if n == 0:
                continue
            
            # 计算四分位数
            q1 = np.percentile(values, 25)
            q2 = np.percentile(values, 50)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            min_val = max(values[0], q1 - 1.5 * iqr)
            max_val = min(values[-1], q3 + 1.5 * iqr)
            
            box_data.append({
                "name": speed,
                "data": [float(min_val), float(q1), float(q2), float(q3), float(max_val)]
            })
        # 确保返回有效的箱线图数据结构
        if not box_data:
            box_data = [{"name": "默认数据", "data": [0, 0, 0, 0, 0]}]
        result = box_data
    
    elif chart_type == "trend":
        # 趋势图数据格式
        trend_data = []
        for speed, values in grouped_data.items():
            median = np.percentile(values, 50)
            trend_data.append({
                "name": speed,
                "value": float(median)
            })
        result = trend_data
    
    elif chart_type == "scatter":
        # 散点图数据格式
        scatter_data = []
        for speed, values in grouped_data.items():
            for value in values:
                scatter_data.append([speed, float(value)])
        result = scatter_data
    
    elif chart_type == "heatmap":
        # 热力图数据格式
        heatmap_data = []
        for speed, values in grouped_data.items():
            for i, value in enumerate(values):
                heatmap_data.append([speed, i, float(value)])
        result = heatmap_data
    
    elif chart_type == "histogram":
        # 直方图数据格式
        all_values = []
        for values in grouped_data.values():
            all_values.extend(values)
        
        if not all_values:
            print(f"直方图数据为空，耗时: {time.time() - start_time:.4f}s")
            return []
        
        # 计算直方图bins
        min_val = min(all_values)
        max_val = max(all_values)
        bin_count = 30
        bin_width = (max_val - min_val) / bin_count
        
        histogram_data = [0] * bin_count
        for val in all_values:
            bin_idx = min(int((val - min_val) / bin_width), bin_count - 1)
            histogram_data[bin_idx] += 1
        
        result = histogram_data
    
    elif chart_type == "bubble":
        # 气泡图数据格式
        bubble_data = []
        for speed, values in grouped_data.items():
            median = np.percentile(values, 50)
            bubble_data.append({
                "name": speed,
                "value": [speed, float(median), len(values)]
            })
        result = bubble_data
    
    elif chart_type == "violin":
        # 小提琴图数据格式
        violin_data = []
        for speed, values in grouped_data.items():
            violin_data.append({
                "name": speed,
                "data": [float(v) for v in values]
            })
        result = violin_data
    
    elif chart_type == "3d":
        # 3D散点图数据格式
        scatter3d_data = []
        for speed, values in grouped_data.items():
            for i, value in enumerate(values):
                scatter3d_data.append([speed, i, float(value)])
        result = scatter3d_data
    
    elif chart_type == "parallel":
        # 平行坐标图数据格式
        parallel_data = []
        for speed, values in grouped_data.items():
            if values:
                median = np.percentile(values, 50)
                mean = np.mean(values)
                parallel_data.append([speed, float(median), float(mean)])
        result = parallel_data
    
    else:
        # 默认返回原始数据
        result = data
    
    print(f"生成{chart_type}图表数据成功，耗时: {time.time() - start_time:.4f}s, 数据长度: {len(result)}")
    return result


# ========== 数据库缓存函数 ==========
def save_chart_cache(cache_key: str, chart_data: Dict) -> bool:
    """
    保存图表缓存到数据库
    
    Args:
        cache_key: 缓存键
        chart_data: 图表数据
        
    Returns:
        bool: 保存是否成功
    """
    if not DB_CONNECTED:
        return False
    
    try:
        # 检查缓存是否已存在
        existing_cache = ChartCache.query.filter_by(cache_key=cache_key).first()
        if existing_cache:
            # 更新现有缓存
            existing_cache.chart_data = json.dumps(chart_data)
            existing_cache.last_accessed = datetime.utcnow()
        else:
            # 创建新缓存
            new_cache = ChartCache(
                cache_key=cache_key,
                chart_data=json.dumps(chart_data)
            )
            db.session.add(new_cache)
        db.session.commit()
        return True
    except Exception as e:
        print(f"保存图表缓存到数据库失败: {str(e)}")
        db.session.rollback()
        return False


def get_chart_cache(cache_key: str) -> Dict:
    """
    从数据库获取图表缓存
    
    Args:
        cache_key: 缓存键
        
    Returns:
        Dict: 图表数据，如果不存在返回None
    """
    if not DB_CONNECTED:
        return None
    
    try:
        cache = ChartCache.query.filter_by(cache_key=cache_key).first()
        if cache:
            # 更新最后访问时间
            cache.last_accessed = datetime.utcnow()
            db.session.commit()
            return json.loads(cache.chart_data)
        return None
    except Exception as e:
        print(f"从数据库获取图表缓存失败: {str(e)}")
        return None


def clean_expired_chart_cache(days: int = 7) -> int:
    """
    清理过期的图表缓存
    
    Args:
        days: 过期天数
        
    Returns:
        int: 清理的缓存数量
    """
    if not DB_CONNECTED:
        return 0
    
    try:
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        expired_caches = ChartCache.query.filter(ChartCache.last_accessed < cutoff_time).all()
        count = len(expired_caches)
        for cache in expired_caches:
            db.session.delete(cache)
        db.session.commit()
        return count
    except Exception as e:
        print(f"清理过期图表缓存失败: {str(e)}")
        db.session.rollback()
        return 0


# 导入datetime和timedelta
from datetime import datetime, timedelta
