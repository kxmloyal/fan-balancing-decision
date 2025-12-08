import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from scipy.stats import pearsonr
import os

def regression_analysis(parsed_data, surface_type='p1'):
    """
    回归分析：分析转速与不平衡量之间的关系
    
    Args:
        parsed_data: 解析后的数据
        surface_type: 面类型 ('p1', 'p2', 'sum')
    
    Returns:
        dict: 回归分析结果
    """
    # 提取数据
    speeds = []
    medians = []
    
    for item in parsed_data:
        speed = float(''.join(filter(str.isdigit, str(item['speed']))))
        samples = item['p1_samples'] if surface_type == 'p1' else (
                  item['p2_samples'] if surface_type == 'p2' else item['sum_samples'])
        
        if samples and not all(pd.isna(val) for val in samples):
            median_val = float(pd.Series(samples).median())
            speeds.append(speed)
            medians.append(median_val)
    
    if len(speeds) < 2:
        return {"error": "数据不足，无法进行回归分析"}
    
    # 线性回归分析
    try:
        from sklearn.linear_model import LinearRegression
        X = np.array(speeds).reshape(-1, 1)
        y = np.array(medians)
        
        model = LinearRegression()
        model.fit(X, y)
        
        # 计算R²值
        r_squared = model.score(X, y)
        
        return {
            "slope": model.coef_[0],
            "intercept": model.intercept_,
            "r_squared": r_squared,
            "equation": f"y = {model.coef_[0]:.4f}x + {model.intercept_:.4f}"
        }
    except ImportError:
        # 如果没有sklearn，手动实现线性回归
        X = np.array(speeds)
        y = np.array(medians)
        
        # 计算回归系数
        mean_x = np.mean(X)
        mean_y = np.mean(y)
        
        numerator = np.sum((X - mean_x) * (y - mean_y))
        denominator = np.sum((X - mean_x)**2)
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        intercept = mean_y - slope * mean_x
        
        # 计算R²值
        y_pred = slope * X + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - mean_y) ** 2)
        
        if ss_tot == 0:
            r_squared = 1
        else:
            r_squared = 1 - (ss_res / ss_tot)
        
        return {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_squared,
            "equation": f"y = {slope:.4f}x + {intercept:.4f}"
        }

def cluster_analysis(parsed_data, surface_type='p1', n_clusters=3):
    """
    聚类分析：将相似转速的数据分为一组
    
    Args:
        parsed_data: 解析后的数据
        surface_type: 面类型 ('p1', 'p2', 'sum')
        n_clusters: 聚类数量
    
    Returns:
        dict: 聚类分析结果
    """
    # 提取数据
    data_points = []
    speed_labels = []
    
    for item in parsed_data:
        speed = float(''.join(filter(str.isdigit, str(item['speed']))))
        samples = item['p1_samples'] if surface_type == 'p1' else (
                  item['p2_samples'] if surface_type == 'p2' else item['sum_samples'])
        
        if samples and not all(pd.isna(val) for val in samples):
            mean_val = float(pd.Series(samples).mean())
            std_val = float(pd.Series(samples).std())
            data_points.append([speed, mean_val, std_val])
            speed_labels.append(item['speed'])
    
    if len(data_points) < n_clusters:
        return {"error": "数据不足，无法进行聚类分析"}
    
    # 简单聚类实现（避免依赖sklearn）
    # 这里使用简单的K-means算法实现
    try:
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(data_points)
        
        # 组织结果
        cluster_results = {}
        for i in range(n_clusters):
            cluster_results[f"cluster_{i}"] = []
        
        for label, cluster in zip(speed_labels, clusters):
            cluster_results[f"cluster_{cluster}"].append(label)
        
        return {
            "clusters": cluster_results,
            "centers": kmeans.cluster_centers_.tolist()
        }
    except ImportError:
        # 如果没有sklearn，使用简单的聚类方法
        return {"error": "需要安装sklearn库才能进行聚类分析"}

def correlation_analysis(parsed_data):
    """
    相关性分析：分析不同面之间数据的相关性
    
    Args:
        parsed_data: 解析后的数据
    
    Returns:
        dict: 相关性分析结果
    """
    # 提取各面的中位数数据
    p1_medians = []
    p2_medians = []
    speeds = []
    
    for item in parsed_data:
        # 只有当P1和P2面都有数据时才考虑
        if (item['p1_samples'] and not all(pd.isna(val) for val in item['p1_samples']) and
            item['p2_samples'] and not all(pd.isna(val) for val in item['p2_samples'])):
            
            p1_median = float(pd.Series(item['p1_samples']).median())
            p2_median = float(pd.Series(item['p2_samples']).median())
            
            p1_medians.append(p1_median)
            p2_medians.append(p2_median)
            speeds.append(item['speed'])
    
    if len(p1_medians) < 2:
        return {"error": "数据不足，无法进行相关性分析"}
    
    # 计算皮尔逊相关系数
    try:
        from scipy.stats import pearsonr
        correlation, p_value = pearsonr(p1_medians, p2_medians)
        
        return {
            "correlation": correlation,
            "p_value": p_value,
            "interpretation": interpret_correlation(correlation)
        }
    except ImportError:
        # 如果没有scipy，手动计算相关系数
        # 简化的相关系数计算
        x = np.array(p1_medians)
        y = np.array(p2_medians)
        
        # 计算皮尔逊相关系数
        mean_x = np.mean(x)
        mean_y = np.mean(y)
        
        numerator = np.sum((x - mean_x) * (y - mean_y))
        denominator = np.sqrt(np.sum((x - mean_x)**2) * np.sum((y - mean_y)**2))
        
        if denominator == 0:
            correlation = 0
        else:
            correlation = numerator / denominator
        
        return {
            "correlation": correlation,
            "p_value": "N/A (需要scipy)",
            "interpretation": interpret_correlation(correlation)
        }

def interpret_correlation(correlation):
    """
    解释相关系数
    
    Args:
        correlation: 相关系数
    
    Returns:
        str: 相关性解释
    """
    abs_corr = abs(correlation)
    
    if abs_corr >= 0.9:
        strength = "非常强"
    elif abs_corr >= 0.7:
        strength = "强"
    elif abs_corr >= 0.5:
        strength = "中等"
    elif abs_corr >= 0.3:
        strength = "弱"
    else:
        strength = "非常弱"
    
    if correlation > 0:
        direction = "正"
    elif correlation < 0:
        direction = "负"
    else:
        direction = "无"
    
    return f"{direction}{strength}相关"

def time_series_analysis(parsed_data, surface_type='p1'):
    """
    时间序列分析（模拟实现）
    注意：当前数据模型不包含时间戳，这里提供一个框架
    
    Args:
        parsed_data: 解析后的数据
        surface_type: 面类型 ('p1', 'p2', 'sum')
    
    Returns:
        dict: 时间序列分析结果
    """
    # 当前数据模型不包含时间戳，所以这是一个框架实现
    # 在实际应用中，如果数据包含时间信息，可以进行更深入的时间序列分析
    
    return {
        "note": "当前数据模型不包含时间戳信息",
        "suggestion": "如果需要时间序列分析，请在数据中包含时间戳信息"
    }

def generate_extended_stats_report(parsed_data, output_prefix, output_folder):
    """
    生成扩展统计分析报告
    
    Args:
        parsed_data: 解析后的数据
        output_prefix: 输出文件前缀
        output_folder: 输出文件夹
    
    Returns:
        tuple: (HTML报告, CSV文件路径)
    """
    # 进行各种扩展分析
    p1_regression = regression_analysis(parsed_data, 'p1')
    p2_regression = regression_analysis(parsed_data, 'p2')
    
    clusters = cluster_analysis(parsed_data)
    correlation = correlation_analysis(parsed_data)
    
    # 生成HTML报告
    html_content = f"""
    <div class="extended-stats-report">
        <h4>扩展统计分析报告</h4>
        
        <div class="regression-analysis">
            <h5>回归分析结果</h5>
            <h6>P1面回归分析</h6>
            <p>回归方程: {p1_regression.get('equation', 'N/A')}</p>
            <p>斜率: {p1_regression.get('slope', 'N/A'):.4f}</p>
            <p>R²值: {p1_regression.get('r_squared', 'N/A'):.4f}</p>
            
            <h6>P2面回归分析</h6>
            <p>回归方程: {p2_regression.get('equation', 'N/A')}</p>
            <p>斜率: {p2_regression.get('slope', 'N/A'):.4f}</p>
            <p>R²值: {p2_regression.get('r_squared', 'N/A'):.4f}</p>
        </div>
        
        <div class="cluster-analysis">
            <h5>聚类分析结果</h5>
            """
    
    if "clusters" in clusters:
        for cluster_name, speeds in clusters["clusters"].items():
            html_content += f"<p><strong>{cluster_name}:</strong> {', '.join(speeds)}</p>"
    else:
        html_content += f"<p>聚类分析失败: {clusters.get('error', '未知错误')}</p>"
    
    html_content += f"""
        </div>
        
        <div class="correlation-analysis">
            <h5>相关性分析结果</h5>
            <p>皮尔逊相关系数: {correlation.get('correlation', 'N/A'):.4f}</p>
            <p>p值: {correlation.get('p_value', 'N/A'):.4f}</p>
            <p>相关性解释: {correlation.get('interpretation', 'N/A')}</p>
        </div>
    </div>
    """
    
    # 生成CSV报告
    csv_data = []
    csv_data.append(["分析类型", "结果"])
    
    # 添加回归分析结果
    csv_data.append(["P1面回归方程", p1_regression.get('equation', 'N/A')])
    csv_data.append(["P1面R²值", p1_regression.get('r_squared', 'N/A')])
    csv_data.append(["P2面回归方程", p2_regression.get('equation', 'N/A')])
    csv_data.append(["P2面R²值", p2_regression.get('r_squared', 'N/A')])
    
    # 添加聚类分析结果
    if "clusters" in clusters:
        for cluster_name, speeds in clusters["clusters"].items():
            csv_data.append([f"聚类{cluster_name}", ", ".join(speeds)])
    
    # 添加相关性分析结果
    csv_data.append(["皮尔逊相关系数", correlation.get('correlation', 'N/A')])
    csv_data.append(["相关性解释", correlation.get('interpretation', 'N/A')])
    
    # 保存CSV文件
    csv_filename = f"{output_prefix}_extended_stats.csv"
    csv_path = os.path.join(output_folder, csv_filename)
    
    df = pd.DataFrame(csv_data[1:], columns=csv_data[0])
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    return html_content, csv_path