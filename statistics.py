import pandas as pd
import os

# ========== 统计报告生成函数（保持之前的修复，键名统一） ==========
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
        
        # 生成HTML统计表格（带高亮）
        html_table = generate_stats_html(stats_data, has_p1, has_p2, has_st, 
                                        min_p1_iqr, min_p2_iqr, min_sum_iqr_val, 
                                        min_p1_cv, min_p2_cv, min_sum_cv_val, 
                                        best_speeds)
        
        # 生成CSV文件
        csv_path = generate_stats_csv(stats_data, output_prefix, output_folder)
        
        return html_table, csv_path
    except Exception as e:
        print(f"生成统计报告失败: {str(e)}")
        raise


def generate_single_surface_stats(parsed_data, output_prefix, surface_type, output_folder):
    """生成单个面（P1/P2/ST）的统计报告，高亮最优转速（IQR最小）"""
    try:
        stats_data = []
        for item in parsed_data:
            speed = str(item['speed'])
            stat_row = {'转速': speed}
            
            # 选择对应的面数据
            if surface_type == 'p1':
                samples = item['p1_samples']
                has_data = any(not pd.isna(val) for val in samples)
                prefix = 'P1'
            elif surface_type == 'p2':
                samples = item['p2_samples']
                has_data = any(not pd.isna(val) for val in samples)
                prefix = 'P2'
            else:  # st
                samples = item['sum_samples']
                has_data = any(not pd.isna(val) for val in samples)
                prefix = 'ST面'
            
            # 计算统计数据
            if has_data:
                q1 = float(pd.Series(samples).quantile(0.25))
                q3 = float(pd.Series(samples).quantile(0.75))
                iqr = round(q3 - q1, 2)
                mean = float(pd.Series(samples).mean())
                std = float(pd.Series(samples).std())
                cv = round((std / mean * 100), 2) if mean != 0 else float('inf')
                
                stat_row[f'{prefix}-平均值'] = str(round(mean, 2))
                stat_row[f'{prefix}-中位数'] = str(round(float(pd.Series(samples).median()), 2))
                stat_row[f'{prefix}-标准差'] = str(round(std, 2))
                stat_row[f'{prefix}-最小值'] = str(round(float(min(samples)), 2))
                stat_row[f'{prefix}-最大值'] = str(round(float(max(samples)), 2))
                stat_row[f'{prefix}-IQR'] = str(iqr)
                stat_row[f'{prefix}-CV'] = str(cv)
            
            stats_data.append(stat_row)
        
        # 找出最优转速（IQR最小）
        iqr_values = [float(row[f'{prefix}-IQR']) for row in stats_data if f'{prefix}-IQR' in row]
        min_iqr = min(iqr_values) if iqr_values else None
        best_speeds = [row['转速'] for row in stats_data if f'{prefix}-IQR' in row and float(row[f'{prefix}-IQR']) == min_iqr]
        
        # 生成HTML统计表格（带高亮）
        html_table = generate_stats_html(stats_data, 
                                        surface_type == 'p1', 
                                        surface_type == 'p2', 
                                        surface_type == 'st', 
                                        min_iqr if surface_type == 'p1' else None, 
                                        min_iqr if surface_type == 'p2' else None, 
                                        min_iqr if surface_type == 'st' else None, 
                                        None, None, None, 
                                        best_speeds)
        
        # 生成CSV文件
        csv_path = generate_stats_csv(stats_data, output_prefix, output_folder)
        
        return html_table, csv_path
    except Exception as e:
        print(f"生成单一面统计报告失败: {str(e)}")
        raise


def generate_stats_html(stats_data, has_p1, has_p2, has_st, 
                        min_p1_iqr, min_p2_iqr, min_sum_iqr_val, 
                        min_p1_cv, min_p2_cv, min_sum_cv_val, 
                        best_speeds):
    """生成统计报告的HTML表格"""
    html = '''
    <table class="table table-striped table-hover">
        <thead>
            <tr>
                <th>转速</th>
    '''
    
    # 根据数据情况动态生成表头
    if has_p1:
        html += '''
                <th colspan="7" style="text-align: center;">P1面</th>
        '''
    if has_p2:
        html += '''
                <th colspan="7" style="text-align: center;">P2面</th>
        '''
    if has_st:
        html += '''
                <th colspan="7" style="text-align: center;">ST面</th>
        '''
    
    html += '''
            </tr>
            <tr>
                <th></th>
    '''
    
    # 添加各面的子表头
    for _ in range(3):  # 每个面7个指标
        if has_p1:
            html += '''
                <th>平均值</th>
                <th>中位数</th>
                <th>标准差</th>
                <th>最小值</th>
                <th>最大值</th>
                <th>IQR</th>
                <th>CV (%)</th>
        '''
        if has_p2:
            html += '''
                <th>平均值</th>
                <th>中位数</th>
                <th>标准差</th>
                <th>最小值</th>
                <th>最大值</th>
                <th>IQR</th>
                <th>CV (%)</th>
        '''
        if has_st:
            html += '''
                <th>平均值</th>
                <th>中位数</th>
                <th>标准差</th>
                <th>最小值</th>
                <th>最大值</th>
                <th>IQR</th>
                <th>CV (%)</th>
        '''
    
    html += '''
            </tr>
        </thead>
        <tbody>
    '''
    
    # 生成数据行
    for row in stats_data:
        html += f'''<tr {'class="table-success"' if row['转速'] in best_speeds else ''}>
                <td>{row['转速']}</td>
        '''
        
        # P1面数据（如果有）
        if has_p1:
            html += f'''<td>{row.get('P1-平均值', '')}</td>
                <td>{row.get('P1-中位数', '')}</td>
                <td>{row.get('P1-标准差', '')}</td>
                <td>{row.get('P1-最小值', '')}</td>
                <td>{row.get('P1-最大值', '')}</td>
                <td {'style="background-color: #ffcccc; font-weight: bold;"' if 'P1-IQR' in row and float(row['P1-IQR']) == min_p1_iqr else ''}>
                    {row.get('P1-IQR', '')}
                </td>
                <td>{row.get('P1-CV', '')}</td>
        '''
        
        # P2面数据（如果有）
        if has_p2:
            html += f'''<td>{row.get('P2-平均值', '')}</td>
                <td>{row.get('P2-中位数', '')}</td>
                <td>{row.get('P2-标准差', '')}</td>
                <td>{row.get('P2-最小值', '')}</td>
                <td>{row.get('P2-最大值', '')}</td>
                <td {'style="background-color: #ffcccc; font-weight: bold;"' if 'P2-IQR' in row and float(row['P2-IQR']) == min_p2_iqr else ''}>
                    {row.get('P2-IQR', '')}
                </td>
                <td>{row.get('P2-CV', '')}</td>
        '''
        
        # ST面数据（如果有）
        if has_st:
            html += f'''<td>{row.get('ST面-平均值', '')}</td>
                <td>{row.get('ST面-中位数', '')}</td>
                <td>{row.get('ST面-标准差', '')}</td>
                <td>{row.get('ST面-最小值', '')}</td>
                <td>{row.get('ST面-最大值', '')}</td>
                <td {'style="background-color: #ffcccc; font-weight: bold;"' if 'ST面-IQR' in row and float(row['ST面-IQR']) == min_sum_iqr_val else ''}>
                    {row.get('ST面-IQR', '')}
                </td>
                <td>{row.get('ST面-CV', '')}</td>
        '''
        
        html += '''</tr>
    '''
    
    html += '''
        </tbody>
    </table>
    '''
    
    return html


def generate_stats_csv(stats_data, output_prefix, output_folder):
    """生成统计报告的CSV文件"""
    try:
        # 创建DataFrame
        df = pd.DataFrame(stats_data)
        
        # 保存CSV文件
        csv_filename = f'{output_prefix}_stats.csv'
        csv_path = os.path.join(output_folder, csv_filename)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        return csv_path
    except Exception as e:
        print(f"生成CSV文件失败: {str(e)}")
        raise