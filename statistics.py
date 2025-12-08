import pandas as pd
import os

# ========== 统分报告生成函数（保持之前的修复，键名统一） ==========
def generate_stats(parsed_data, output_prefix, output_folder):
    """生成P1/P2/ST面三栏对比统计报告，高亮最优转速（ST面IQR最小）"""
    try:
        stats_data = []
        for item in parsed_data:
            speed = str(item['speed'])
            stat_row = {'转速': speed}
            
            # P1面统计（仅当有数据时计算）
            has_p1_data = any(not pd.isna(val) for val in item['p1_samples'])
            if has_p1_data:
                p1_samples = item['p1_samples']
                p1_q1 = float(pd.Series(p1_samples).quantile(0.25))
                p1_q3 = float(pd.Series(p1_samples).quantile(0.75))
                p1_iqr = round(p1_q3 - p1_q1, 2)
                p1_mean = float(pd.Series(p1_samples).mean())
                p1_std = float(pd.Series(p1_samples).std())
                p1_cv = round((p1_std / p1_mean * 100), 2) if p1_mean != 0 else float('inf')
                
                stat_row['P1-平均值'] = str(round(p1_mean, 2))
                stat_row['P1-中位数'] = str(round(float(pd.Series(p1_samples).median()), 2))
                stat_row['P1-标准差'] = str(round(p1_std, 2))
                stat_row['P1-最小值'] = str(round(float(min(p1_samples)), 2))
                stat_row['P1-最大值'] = str(round(float(max(p1_samples)), 2))
                stat_row['P1-IQR'] = str(p1_iqr)
                stat_row['P1-CV'] = str(p1_cv)
            
            # P2面统计（仅当有数据时计算）
            has_p2_data = any(not pd.isna(val) for val in item['p2_samples'])
            if has_p2_data:
                p2_samples = item['p2_samples']
                p2_q1 = float(pd.Series(p2_samples).quantile(0.25))
                p2_q3 = float(pd.Series(p2_samples).quantile(0.75))
                p2_iqr = round(p2_q3 - p2_q1, 2)
                p2_mean = float(pd.Series(p2_samples).mean())
                p2_std = float(pd.Series(p2_samples).std())
                p2_cv = round((p2_std / p2_mean * 100), 2) if p2_mean != 0 else float('inf')
                
                stat_row['P2-平均值'] = str(round(p2_mean, 2))
                stat_row['P2-中位数'] = str(round(float(pd.Series(p2_samples).median()), 2))
                stat_row['P2-标准差'] = str(round(p2_std, 2))
                stat_row['P2-最小值'] = str(round(float(min(p2_samples)), 2))
                stat_row['P2-最大值'] = str(round(float(max(p2_samples)), 2))
                stat_row['P2-IQR'] = str(p2_iqr)
                stat_row['P2-CV'] = str(p2_cv)
            
            # ST面统计（仅当有数据时计算）
            has_st_data = any(not pd.isna(val) for val in item['sum_samples'])
            if has_st_data:
                sum_samples = item['sum_samples']
                sum_q1 = float(pd.Series(sum_samples).quantile(0.25))
                sum_q3 = float(pd.Series(sum_samples).quantile(0.75))
                sum_iqr = round(sum_q3 - sum_q1, 2)
                sum_mean = float(pd.Series(sum_samples).mean())
                sum_std = float(pd.Series(sum_samples).std())
                sum_cv = round((sum_std / sum_mean * 100), 2) if sum_mean != 0 else float('inf')
                
                stat_row['ST面-平均值'] = str(round(sum_mean, 2))
                stat_row['ST面-中位数'] = str(round(float(pd.Series(sum_samples).median()), 2))
                stat_row['ST面-标准差'] = str(round(sum_std, 2))
                stat_row['ST面-最小值'] = str(round(float(min(sum_samples)), 2))
                stat_row['ST面-最大值'] = str(round(float(max(sum_samples)), 2))
                stat_row['ST面-IQR'] = str(sum_iqr)
                stat_row['ST面-CV'] = str(sum_cv)
            
            stats_data.append(stat_row)
        
        # 找出各列的最小IQR值和最小CV值，用于高亮显示（仅对存在的面）
        # 确保列表是实际的列表而不是生成器
        p1_iqr_values = [float(row['P1-IQR']) for row in stats_data if 'P1-IQR' in row] if any('P1-IQR' in row for row in stats_data) else []
        min_p1_iqr = min(p1_iqr_values) if p1_iqr_values else None
        p1_cv_values = [float(row['P1-CV']) for row in stats_data if 'P1-CV' in row and row['P1-CV'] != 'inf'] if any('P1-CV' in row for row in stats_data) else []
        min_p1_cv = min(p1_cv_values) if p1_cv_values else None
        
        p2_iqr_values = [float(row['P2-IQR']) for row in stats_data if 'P2-IQR' in row] if any('P2-IQR' in row for row in stats_data) else []
        min_p2_iqr = min(p2_iqr_values) if p2_iqr_values else None
        p2_cv_values = [float(row['P2-CV']) for row in stats_data if 'P2-CV' in row and row['P2-CV'] != 'inf'] if any('P2-CV' in row for row in stats_data) else []
        min_p2_cv = min(p2_cv_values) if p2_cv_values else None
        
        st_iqr_values_check = [float(row['ST面-IQR']) for row in stats_data if 'ST面-IQR' in row] if any('ST面-IQR' in row for row in stats_data) else []
        min_sum_iqr_val = min(st_iqr_values_check) if st_iqr_values_check else None
        st_cv_values = [float(row['ST面-CV']) for row in stats_data if 'ST面-CV' in row and row['ST面-CV'] != 'inf'] if any('ST面-CV' in row for row in stats_data) else []
        min_sum_cv_val = min(st_cv_values) if st_cv_values else None
        
        # 找出最优转速（ST面IQR最小，仅当有ST数据时）
        best_speeds = []
        if any('ST面-IQR' in row for row in stats_data):
            # 确保列表是实际的列表而不是生成器
            st_iqr_values = [float(row['ST面-IQR']) for row in stats_data if 'ST面-IQR' in row]
            if st_iqr_values:  # 确保列表不为空
                min_sum_iqr = min(st_iqr_values)
                best_speeds = [row['转速'] for row in stats_data if 'ST面-IQR' in row and float(row['ST面-IQR']) == min_sum_iqr]
        
        # 确定有哪些面需要显示（只有当该面在任何一行中有数据时才显示）
        has_p1 = any('P1-IQR' in row for row in stats_data)
        has_p2 = any('P2-IQR' in row for row in stats_data)
        has_st = any('ST面-IQR' in row for row in stats_data)
        
        # 生成HTML表格头部
        stats_html = f"""
        <div class="mb-2">
            <i class="bi bi-star text-success"></i> 最优转速{('（ST面数据最集中，IQR最小）：' + ', '.join(best_speeds)) if best_speeds else '：无'}
            <span class="text-muted ms-2">（IQR：反映中间50%数据的离散程度，越小越稳定，不受极端值干扰）</span>
        </div>
        """
        
        # 当ST面没有数据或ST面最优转速为空时，通过综合评估确定最优转速
        if not best_speeds:
            # 收集所有面的最小IQR和最小CV对应的转速
            all_min_iqr_speeds = {}
            all_min_cv_speeds = {}
            
            # P1面最小IQR转速
            if min_p1_iqr is not None:
                p1_min_iqr_speeds = [row['转速'] for row in stats_data if 'P1-IQR' in row and float(row['P1-IQR']) == min_p1_iqr]
                all_min_iqr_speeds['P1'] = p1_min_iqr_speeds
                
            # P1面最小CV转速
            if min_p1_cv is not None:
                p1_min_cv_speeds = [row['转速'] for row in stats_data if 'P1-CV' in row and float(row['P1-CV']) == min_p1_cv]
                all_min_cv_speeds['P1'] = p1_min_cv_speeds
            
            # P2面最小IQR转速
            if min_p2_iqr is not None:
                p2_min_iqr_speeds = [row['转速'] for row in stats_data if 'P2-IQR' in row and float(row['P2-IQR']) == min_p2_iqr]
                all_min_iqr_speeds['P2'] = p2_min_iqr_speeds
                
            # P2面最小CV转速
            if min_p2_cv is not None:
                p2_min_cv_speeds = [row['转速'] for row in stats_data if 'P2-CV' in row and float(row['P2-CV']) == min_p2_cv]
                all_min_cv_speeds['P2'] = p2_min_cv_speeds
            
            # ST面最小IQR转速
            if min_sum_iqr_val is not None:
                st_min_iqr_speeds = [row['转速'] for row in stats_data if 'ST面-IQR' in row and float(row['ST面-IQR']) == min_sum_iqr_val]
                all_min_iqr_speeds['ST'] = st_min_iqr_speeds
                
            # ST面最小CV转速
            if min_sum_cv_val is not None:
                st_min_cv_speeds = [row['转速'] for row in stats_data if 'ST面-CV' in row and float(row['ST面-CV']) == min_sum_cv_val]
                all_min_cv_speeds['ST'] = st_min_cv_speeds
            
            # 使用加权评分法（P1/P2/ST面按0.4/0.4/0.2权重）
            speed_scores = {}
            weights = {'P1': 0.4, 'P2': 0.4, 'ST': 0.2}
            
            # 计算每个转速的综合得分（基于IQR和CV）
            for row in stats_data:
                speed = row['转速']
                score = 0
                
                # P1面得分计算
                if 'P1-IQR' in row and 'P1-CV' in row:
                    p1_iqr = float(row['P1-IQR'])
                    p1_cv = float(row['P1-CV']) if row['P1-CV'] != 'inf' else None
                    if p1_iqr is not None and p1_cv is not None and p1_cv != float('inf'):
                        # 归一化处理，值越小得分越高
                        iqr_score = 1 / (1 + p1_iqr)
                        cv_score = 1 / (1 + p1_cv/100)  # CV是百分比，适当缩放
                        # 面内综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分
                        p1_score = 0.5 * iqr_score + 0.5 * cv_score
                        # 面间综合：总得分 += 面权重 × 面得分
                        score += weights['P1'] * p1_score
                
                # P2面得分计算
                if 'P2-IQR' in row and 'P2-CV' in row:
                    p2_iqr = float(row['P2-IQR'])
                    p2_cv = float(row['P2-CV']) if row['P2-CV'] != 'inf' else None
                    if p2_iqr is not None and p2_cv is not None and p2_cv != float('inf'):
                        # 归一化处理，值越小得分越高
                        iqr_score = 1 / (1 + p2_iqr)
                        cv_score = 1 / (1 + p2_cv/100)  # CV是百分比，适当缩放
                        # 面内综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分
                        p2_score = 0.5 * iqr_score + 0.5 * cv_score
                        # 面间综合：总得分 += 面权重 × 面得分
                        score += weights['P2'] * p2_score
                
                # ST面得分计算
                if 'ST面-IQR' in row and 'ST面-CV' in row:
                    st_iqr = float(row['ST面-IQR'])
                    st_cv = float(row['ST面-CV']) if row['ST面-CV'] != 'inf' else None
                    if st_iqr is not None and st_cv is not None and st_cv != float('inf'):
                        # 归一化处理，值越小得分越高
                        iqr_score = 1 / (1 + st_iqr)
                        cv_score = 1 / (1 + st_cv/100)  # CV是百分比，适当缩放
                        # 面内综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分
                        st_score = 0.5 * iqr_score + 0.5 * cv_score
                        # 面间综合：总得分 += 面权重 × 面得分
                        score += weights['ST'] * st_score
                
                speed_scores[speed] = score
            
            # 选出得分最高的转速作为最优转速
            if speed_scores:
                best_score = max(speed_scores.values())
                best_comprehensive_speeds = [speed for speed, score in speed_scores.items() if score == best_score]
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
        
        stats_html += """
        <table class="table table-striped table-hover table-sm table-statistics">
            <thead class="header-main">
                <tr>
                    <th rowspan="2" class="align-middle text-center">转速</th>
        """
        
        # 添加表头列（仅显示有数据的面）
        if has_p1:
            stats_html += '<th colspan="7" class="text-center face-p1">P1面</th>'
        if has_p2:
            stats_html += '<th colspan="7" class="text-center face-p2">P2面</th>'
        if has_st:
            stats_html += '<th colspan="7" class="text-center face-st">ST面</th>'
        
        stats_html += '<th rowspan="2" class="align-middle text-center evaluation-col">综合评估</th>'
        stats_html += '<th rowspan="2" class="align-middle text-center evaluation-col">稳定等级</th>'
        
        stats_html += """
                </tr>
                <tr class="header-sub">
        """
        
        # 添加子表头（仅显示有数据的面）
        if has_p1:
            stats_html += '<th class="face-p1">平均值</th><th class="face-p1">中位数</th><th class="face-p1">标准差</th><th class="face-p1">最小值</th><th class="face-p1">最大值</th><th class="face-p1">IQR</th><th class="face-p1">CV(%)</th>'
        if has_p2:
            stats_html += '<th class="face-p2">平均值</th><th class="face-p2">中位数</th><th class="face-p2">标准差</th><th class="face-p2">最小值</th><th class="face-p2">最大值</th><th class="face-p2">IQR</th><th class="face-p2">CV(%)</th>'
        if has_st:
            stats_html += '<th class="face-st">平均值</th><th class="face-st">中位数</th><th class="face-st">标准差</th><th class="face-st">最小值</th><th class="face-st">最大值</th><th class="face-st">IQR</th><th class="face-st">CV(%)</th>'
        
        stats_html += """
                </tr>
            </thead>
            <tbody>
        """
        
        # 计算每个转速的综合评分（与最优转速选择方法保持一致）
        speed_scores = {}
        weights = {'P1': 0.4, 'P2': 0.4, 'ST': 0.2}
        
        # 收集所有面的IQR和CV值用于评分计算
        p1_values = {row['转速']: (float(row['P1-IQR']), float(row['P1-CV']) if row['P1-CV'] != 'inf' else None) for row in stats_data if 'P1-IQR' in row}
        p2_values = {row['转速']: (float(row['P2-IQR']), float(row['P2-CV']) if row['P2-CV'] != 'inf' else None) for row in stats_data if 'P2-IQR' in row}
        st_values = {row['转速']: (float(row['ST面-IQR']), float(row['ST面-CV']) if row['ST面-CV'] != 'inf' else None) for row in stats_data if 'ST面-IQR' in row}
        
        # 计算每个转速的综合得分
        for row in stats_data:
            speed = row['转速']
            score = 0
            
            # P1面得分计算
            if speed in p1_values:
                p1_iqr, p1_cv = p1_values[speed]
                if p1_iqr is not None and p1_cv is not None and p1_cv != float('inf'):
                    # 归一化处理，值越小得分越高
                    iqr_score = 1 / (1 + p1_iqr)
                    cv_score = 1 / (1 + p1_cv/100)  # CV是百分比，适当缩放
                    # 面内综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分
                    p1_score = 0.5 * iqr_score + 0.5 * cv_score
                    # 面间综合：总得分 += 面权重 × 面得分
                    score += weights['P1'] * p1_score
            
            # P2面得分计算
            if speed in p2_values:
                p2_iqr, p2_cv = p2_values[speed]
                if p2_iqr is not None and p2_cv is not None and p2_cv != float('inf'):
                    # 归一化处理，值越小得分越高
                    iqr_score = 1 / (1 + p2_iqr)
                    cv_score = 1 / (1 + p2_cv/100)  # CV是百分比，适当缩放
                    # 面内综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分
                    p2_score = 0.5 * iqr_score + 0.5 * cv_score
                    # 面间综合：总得分 += 面权重 × 面得分
                    score += weights['P2'] * p2_score
            
            # ST面得分计算
            if speed in st_values:
                st_iqr, st_cv = st_values[speed]
                if st_iqr is not None and st_cv is not None and st_cv != float('inf'):
                    # 归一化处理，值越小得分越高
                    iqr_score = 1 / (1 + st_iqr)
                    cv_score = 1 / (1 + st_cv/100)  # CV是百分比，适当缩放
                    # 面内综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分
                    st_score = 0.5 * iqr_score + 0.5 * cv_score
                    # 面间综合：总得分 += 面权重 × 面得分
                    score += weights['ST'] * st_score
            
            speed_scores[speed] = score
        
        # 找出最高得分
        max_score = max(speed_scores.values()) if speed_scores else 0
        
        # 根据综合得分排序，计算排名
        sorted_scores = sorted(speed_scores.items(), key=lambda x: x[1], reverse=True)
        rankings = {speed: rank + 1 for rank, (speed, score) in enumerate(sorted_scores)}
        
        # 确定最优转速（综合得分最高的转速）
        best_speeds = [item[0] for item in sorted_scores[:1]] if sorted_scores else []
        
        for row in stats_data:
            # 最优转速行添加浅绿色高亮
            is_best_speed = row['转速'] in best_speeds
            row_highlight = 'table-success' if is_best_speed else ''
            
            stats_html += f'<tr class="{row_highlight}"><td>{row["转速"]}</td>'
            
            # 添加P1面数据（仅当存在时）
            if has_p1:
                if 'P1-IQR' in row:
                    p1_iqr_highlight = 'table-warning' if min_p1_iqr is not None and float(row['P1-IQR']) == min_p1_iqr else ''
                    stats_html += f"""
                    <!-- P1面数据 -->
                    <td>{row['P1-平均值']}</td><td>{row['P1-中位数']}</td><td>{row['P1-标准差']}</td>
                    <td>{row['P1-最小值']}</td><td>{row['P1-最大值']}</td><td class="{p1_iqr_highlight}">{row['P1-IQR']}</td><td>{row['P1-CV']}</td>
                    """
                else:
                    stats_html += '<!-- P1面数据缺失 --><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>'
            
            # 添加P2面数据（仅当存在时）
            if has_p2:
                if 'P2-IQR' in row:
                    p2_iqr_highlight = 'table-warning' if min_p2_iqr is not None and float(row['P2-IQR']) == min_p2_iqr else ''
                    stats_html += f"""
                    <!-- P2面数据 -->
                    <td>{row['P2-平均值']}</td><td>{row['P2-中位数']}</td><td>{row['P2-标准差']}</td>
                    <td>{row['P2-最小值']}</td><td>{row['P2-最大值']}</td><td class="{p2_iqr_highlight}">{row['P2-IQR']}</td><td>{row['P2-CV']}</td>
                    """
                else:
                    stats_html += '<!-- P2面数据缺失 --><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>'
            
            # 添加ST面数据（仅当存在时）
            if has_st:
                if 'ST面-IQR' in row:
                    sum_iqr_highlight = 'table-warning' if min_sum_iqr_val is not None and float(row['ST面-IQR']) == min_sum_iqr_val else ''
                    stats_html += f"""
                    <!-- ST面数据 -->
                    <td>{row['ST面-平均值']}</td><td>{row['ST面-中位数']}</td><td>{row['ST面-标准差']}</td>
                    <td>{row['ST面-最小值']}</td><td>{row['ST面-最大值']}</td><td class="{sum_iqr_highlight}">{row['ST面-IQR']}</td><td>{row['ST面-CV']}</td>
                    """
                else:
                    stats_html += '<!-- ST面数据缺失 --><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td>'
            
            # 综合评价和稳定等级
            # 综合评价显示最优转速选择方法的计算结果，保留两位小数
            score = speed_scores.get(row['转速'], 0)
            comprehensive_rating = f"{score:.2f}" if score else "N/A"
            stability_level = rankings.get(row['转速'], len(rankings))
            stats_html += f'<td>{comprehensive_rating}</td><td>{stability_level}</td>'
            
            stats_html += '</tr>'
        
        stats_html += "</tbody></table>"
        
        # 生成CSV报告
        stats_df = pd.DataFrame(stats_data)
        stats_csv = os.path.join(output_folder, f'{output_prefix}_stats.csv')
        stats_df.to_csv(stats_csv, index=False, encoding='utf-8-sig')
        
        return stats_html, stats_csv
    except Exception as e:
        raise Exception(f"统计报告生成失败：{str(e)}")

def _calculate_scores(samples_data):
    """计算单个面的综合评分"""
    iqr_val = float(samples_data['IQR（四分位距）'])
    cv_val = float(samples_data['变异系数(%)']) if samples_data['变异系数(%)'] != 'inf' else None
    
    if iqr_val is not None and cv_val is not None and cv_val != float('inf'):
        # 归一化处理，值越小得分越高
        iqr_score = 1 / (1 + iqr_val)
        cv_score = 1 / (1 + cv_val/100)  # CV是百分比，适当缩放
        # IQR和CV各占50%权重
        score = 0.5 * iqr_score + 0.5 * cv_score
        return score
    else:
        return 0

def generate_single_surface_stats(parsed_data, output_prefix, surface_type, output_folder):
    """生成单个面（P1/P2/ST）的统计报告，高亮最优转速（IQR最小）"""
    try:
        stats_data = []
        for item in parsed_data:
            speed = str(item['speed'])
            samples = item['p1_samples'] if surface_type == 'p1' else (
                      item['p2_samples'] if surface_type == 'p2' else item['sum_samples'])
            
            # 只有当有数据时才进行统计计算
            has_data = any(not pd.isna(val) for val in samples)
            if has_data:
                # 计算IQR（四分位距：Q3 - Q1）
                q1 = float(pd.Series(samples).quantile(0.25))
                q3 = float(pd.Series(samples).quantile(0.75))
                iqr = round(q3 - q1, 2)
                
                # 计算平均值、标准差和变异系数
                mean_val = float(pd.Series(samples).mean())
                std_val = float(pd.Series(samples).std())
                cv_val = round((std_val / mean_val * 100), 2) if mean_val != 0 else float('inf')
                
                stats_data.append({
                    '转速': speed,
                    '平均值': str(round(mean_val, 2)),
                    '中位数': str(round(float(pd.Series(samples).median()), 2)),
                    '标准差': str(round(std_val, 2)),
                    '最小值': str(round(float(min(samples)), 2)),
                    '最大值': str(round(float(max(samples)), 2)),
                    'IQR（四分位距）': str(iqr),
                    '变异系数(%)': str(cv_val)
                })
        
        # 使用统一的加权评分法确定最优转速
        if stats_data:
            # 计算每个转速的综合得分（基于IQR和CV）
            speed_scores = {}
            
            for row in stats_data:
                speed_scores[row['转速']] = _calculate_scores(row)
            
            # 选出得分最高的转速作为最优转速
            if speed_scores:
                best_score = max(speed_scores.values())
                best_speeds = [speed for speed, score in speed_scores.items() if score == best_score]
            else:
                best_speeds = []
        else:
            best_speeds = []
        
        # 生成HTML表格
        surface_name = {'p1': 'P1', 'p2': 'P2', 'st': 'ST'}[surface_type]
        
        # 计算每个转速的综合评分（与最优转速选择方法保持一致）
        speed_scores = {}
        
        # 计算每个转速的综合得分（基于IQR和CV）
        for row in stats_data:
            speed_scores[row['转速']] = _calculate_scores(row)
        
        # 找出最高得分
        max_score = max(speed_scores.values()) if speed_scores else 0
        
        # 根据综合得分排序，计算排名
        sorted_scores = sorted(speed_scores.items(), key=lambda x: x[1], reverse=True)
        rankings = {item[0]: rank + 1 for rank, item in enumerate(sorted_scores)}
        
        # 确定最优转速（综合得分最高的转速）
        best_speeds = [item[0] for item in sorted_scores[:1]] if sorted_scores else []
        
        # 生成HTML表格头部
        stats_html = f"""
        <div class="mb-2">
            <i class="bi bi-star text-success"></i> 最优转速{('（' + surface_name + '面数据最集中，IQR最小）：' + ', '.join(best_speeds)) if best_speeds else '：无'}
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
        
        stats_html += f'''
        <table class="table table-striped table-hover table-sm">
            <thead class="table-light">
                <tr>
                    <th rowspan="2" class="align-middle text-center">转速</th>
                    <th colspan="7" class="text-center bg-primary text-white">{surface_name}面</th>
                    <th rowspan="2" class="align-middle text-center">综合评估</th>
                    <th rowspan="2" class="align-middle text-center">稳定等级</th>
                </tr>
                <tr>
                    <th>平均值</th><th>中位数</th><th>标准差</th><th>最小值</th><th>最大值</th><th>IQR（四分位距）</th><th>变异系数(%)</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        for row in stats_data:
            # 最优转速行添加浅绿色高亮
            is_best_speed = row['转速'] in best_speeds
            row_highlight = 'table-success' if is_best_speed else ''  # 使用Bootstrap的table-success类
            
            # IQR最小值单元格高亮
            iqr_values_list = [float(r['IQR（四分位距）']) for r in stats_data]
            min_iqr = min(iqr_values_list) if iqr_values_list else None
            iqr_highlight = 'table-warning' if min_iqr is not None and float(row['IQR（四分位距）']) == min_iqr else ''  # 使用Bootstrap的table-warning类
            
            # 综合评价和稳定等级
            # 综合评价显示最优转速选择方法的计算结果，保留两位小数
            score = speed_scores.get(row['转速'], 0)
            comprehensive_rating = f"{score:.2f}" if score else "N/A"
            stability_level = rankings.get(row['转速'], len(rankings))
            
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
        stats_csv = os.path.join(output_folder, f'{output_prefix}_{surface_type}_stats.csv')
        stats_df.to_csv(stats_csv, index=False, encoding='utf-8-sig')
        
        return stats_html, stats_csv
    except Exception as e:
        raise Exception(f"单面带统计报告生成失败：{str(e)}")