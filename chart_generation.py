import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os
import gc


def generate_plots(parsed_data, output_prefix, output_folder, chart_types=None):
    """生成双面对比图表（对比图+P1单面带+P2单面带+ST面图）"""
    if chart_types is None:
        chart_types = ['box']  # 默认只生成箱线图
    
    try:
        # 准备绘图数据
        p1_data = []       # P1面单独图数据
        p2_data = []       # P2面单独图数据
        sum_data = []      # ST面图数据
        
        # 关键优化1：分离P1和P2的中位数计算，确保互不干扰
        p1_median_dict = {}  # 存储P1面各转速的中位数：{转速: 中位数}
        p2_median_dict = {}  # 存储P2面各转速的中位数：{转速: 中位数}
        
        for item in parsed_data:
            speed = str(item['speed'])
            p1_samples = item['p1_samples']
            p2_samples = item['p2_samples']
            
            # 单面带数据
            for val in p1_samples:
                p1_data.append({'转速': speed, '不平衡量': val})
            for val in p2_samples:
                p2_data.append({'转速': speed, '不平衡量': val})
            
            # ST面数据
            for val in item['sum_samples']:
                sum_data.append({'转速': speed, '不平衡量ST面': val})
            
            # 关键优化2：单独计算P1面中位数（仅基于P1样本）
            p1_median = pd.Series(p1_samples).median()
            p1_median_dict[speed] = p1_median
            
            # 关键优化3：单独计算P2面中位数（仅基于P2样本）
            p2_median = pd.Series(p2_samples).median()
            p2_median_dict[speed] = p2_median
        
        # 关键优化4：按转速顺序排序（确保连线顺序正确）
        # 提取所有转速并按数字大小排序（兼容"3000rpm"、"4000"等格式）
        all_speeds = sorted(p1_median_dict.keys(), key=lambda x: float(''.join(filter(str.isdigit, x))))
        
        # 提取排序后的中位数数据（确保P1和P2的转速顺序完全一致）
        p1_median_values = [p1_median_dict[speed] for speed in all_speeds]
        p2_median_values = [p2_median_dict[speed] for speed in all_speeds]
        
        plots = {}
        
        # 1. P1面图表
        if p1_data:
            plots['p1'] = generate_surface_charts(
                p1_data, 
                p1_median_dict, 
                all_speeds, 
                p1_median_values, 
                'P1面', 
                '#1f77b4', 
                output_prefix, 
                output_folder, 
                chart_types
            )
        
        # 强制垃圾回收以释放内存
        del p1_data
        gc.collect()
        
        # 2. P2面图表
        if p2_data:
            plots['p2'] = generate_surface_charts(
                p2_data, 
                p2_median_dict, 
                all_speeds, 
                p2_median_values, 
                'P2面', 
                '#ff7f0e', 
                output_prefix, 
                output_folder, 
                chart_types
            )
        
        # 强制垃圾回收以释放内存
        del p2_data
        gc.collect()
        
        # 3. ST面图表
        if sum_data:
            st_median_dict = {}
            for item in parsed_data:
                speed = str(item['speed'])
                st_samples = item['sum_samples']
                st_median_dict[speed] = pd.Series(st_samples).median()
            
            plots['sum'] = generate_st_chart(
                sum_data, 
                st_median_dict, 
                'ST面', 
                '#2ca02c', 
                output_prefix, 
                output_folder, 
                chart_types
            )
            
            # 强制垃圾回收以释放内存
            del sum_data
            gc.collect()
        
        return plots
    except Exception as e:
        raise Exception(f"图表生成失败：{str(e)}")


def generate_single_surface_plots(parsed_data, output_prefix, surface_type, output_folder, chart_types=None):
    """生成单个面（P1/P2/ST）的图表（添加中文字体配置）"""
    if chart_types is None:
        chart_types = ['box']  # 默认只生成箱线图
    
    try:
        plot_data = []
        median_dict = {}  # 存储当前面各转速的中位数
        
        for item in parsed_data:
            speed = str(item['speed'])
            samples = item['p1_samples'] if surface_type == 'p1' else (
                      item['p2_samples'] if surface_type == 'p2' else item['sum_samples'])
            for val in samples:
                plot_data.append({'转速': speed, '不平衡量': val})
            # 单独计算当前面的中位数
            median_dict[speed] = pd.Series(samples).median()
        
        # 按转速排序
        sorted_speeds = sorted(median_dict.keys(), key=lambda x: float(''.join(filter(str.isdigit, x))))
        median_values = [median_dict[speed] for speed in sorted_speeds]
        
        # 生成图表
        color_map = {'p1': '#1f77b4', 'p2': '#ff7f0e', 'st': '#2ca02c'}
        title_map = {'p1': 'P1面', 'p2': 'P2面', 'st': 'ST面'}
        color = color_map.get(surface_type, '#1f77b4')
        title = f'{title_map.get(surface_type, surface_type.upper())}面'
        
        charts = generate_surface_charts(
            plot_data, 
            median_dict, 
            sorted_speeds, 
            median_values, 
            title, 
            color, 
            output_prefix, 
            output_folder, 
            chart_types
        )
        
        # 强制垃圾回收以释放内存
        del plot_data
        gc.collect()
        
        # Return charts with appropriate keys based on surface type
        if surface_type == 'p1':
            return {'p1': charts}
        elif surface_type == 'p2':
            return {'p2': charts}
        elif surface_type == 'st':
            return {'sum': charts}
        else:
            # 确保单面数据也能被正确处理
            return {'single': charts}
    except Exception as e:
        raise Exception(f"单面带图表生成失败：{str(e)}")


def generate_surface_charts(data, median_dict, sorted_speeds, median_values, surface_name, color, output_prefix, output_folder, chart_types):
    """为单个面生成多种类型的图表"""
    charts = {}
    
    # 生成各种图表
    for chart_type in chart_types:
        try:
            if chart_type == 'box':
                fig = create_box_plot(data, median_dict, sorted_speeds, median_values, surface_name, color)
            elif chart_type == 'violin':
                fig = create_violin_plot(data, surface_name, color)
            elif chart_type == 'scatter':
                fig = create_scatter_plot(data, median_dict, sorted_speeds, median_values, surface_name, color)
            elif chart_type == 'trend':
                fig = create_trend_plot(median_dict, sorted_speeds, median_values, surface_name, color)
            elif chart_type == 'heatmap':
                fig = create_heatmap_plot(data, surface_name, color)
            elif chart_type == 'histogram':
                fig = create_histogram_plot(data, surface_name, color)
            elif chart_type == '3d':
                fig = create_3d_scatter_plot(data, median_dict, sorted_speeds, median_values, surface_name, color)
            else:
                continue
                
            chart_filename = f"{output_prefix}_{surface_name.lower().replace('面', '')}_{chart_type}"
            png_path = os.path.join(output_folder, f"{chart_filename}.png")
            html_path = os.path.join(output_folder, f"{chart_filename}.html")
            
            # 保存图片
            pio.write_image(fig, png_path, format='png', width=1200, height=600, scale=1.5)  # 减小尺寸以节省内存
            
            # 保存HTML
            div_content = pio.to_html(fig, include_plotlyjs=True, full_html=False)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write('<!DOCTYPE html>\n<html>\n<head>\n')
                f.write('<meta charset="utf-8">\n')
                f.write('<title>交互式图表</title>\n')
                f.write('</head>\n<body>\n')
                f.write(div_content)
                f.write('\n</body>\n</html>')
            
            # 释放图表对象以节省内存
            fig = None
            
            charts[chart_type] = {
                'png': os.path.basename(png_path),
                'html': os.path.basename(html_path)
            }
        except Exception as e:
            print(f"生成图表类型 '{chart_type}' 时出错: {str(e)}")
            # 即使某个图表类型失败，也要继续处理其他图表类型
            continue
    
    # 强制垃圾回收
    gc.collect()
    
    return charts


def generate_st_chart(data, median_dict, surface_name, color, output_prefix, output_folder, chart_types):
    """为ST面生成图表（ST面支持多种图表类型）"""
    charts = {}
    
    # 生成各种图表
    for chart_type in chart_types:
        try:
            if chart_type == 'box':
                fig = create_st_box_plot(data, surface_name, color)
            elif chart_type == 'violin':
                fig = create_st_violin_plot(data, surface_name, color)
            elif chart_type == 'scatter':
                fig = create_st_scatter_plot(data, median_dict, surface_name, color)
            elif chart_type == 'trend':
                fig = create_st_trend_plot(median_dict, surface_name, color)
            elif chart_type == 'heatmap':
                fig = create_st_heatmap_plot(data, surface_name)
            elif chart_type == 'histogram':
                fig = create_st_histogram_plot(data, surface_name, color)
            elif chart_type == '3d':
                fig = create_st_3d_scatter_plot(data, surface_name, color)
            else:
                continue
                
            chart_filename = f"{output_prefix}_{surface_name.lower().replace('面', '')}_{chart_type}"
            png_path = os.path.join(output_folder, f"{chart_filename}.png")
            html_path = os.path.join(output_folder, f"{chart_filename}.html")
            
            # 保存图片
            pio.write_image(fig, png_path, format='png', width=1400, height=700, scale=2)
            
            # 保存HTML
            div_content = pio.to_html(fig, include_plotlyjs=True, full_html=False)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write('<!DOCTYPE html>\n<html>\n<head>\n')
                f.write('<meta charset="utf-8">\n')
                f.write('<title>交互式图表</title>\n')
                f.write('</head>\n<body>\n')
                f.write(div_content)
                f.write('\n</body>\n</html>')
            
            charts[chart_type] = {
                'png': os.path.basename(png_path),
                'html': os.path.basename(html_path)
            }
        except Exception as e:
            print(f"生成ST面图表类型 '{chart_type}' 时出错: {str(e)}")
            # 即使某个图表类型失败，也要继续处理其他图表类型
            continue
    
    return charts


def create_combined_chart(parsed_data, chart_types, output_prefix, output_folder, combine_faces=False):
    """创建组合图表，支持多图表联动"""
    charts = {}
    
    try:
        # 生成各种图表类型
        for chart_type in chart_types:
            fig = None
            try:
                if chart_type == 'trend':  # 趋势图（折线图）
                    fig = create_combined_trend_chart(parsed_data, combine_faces)
                elif chart_type == 'scatter':  # 散点图
                    if combine_faces:
                        # 合并所有面的数据
                        combined_data = []
                        for item in parsed_data:
                            speed = str(item['speed'])
                            # 添加P1面数据
                            for val in item['p1_samples']:
                                combined_data.append({'转速': speed, '不平衡量': val, '面': 'P1'})
                            # 添加P2面数据
                            for val in item['p2_samples']:
                                combined_data.append({'转速': speed, '不平衡量': val, '面': 'P2'})
                            # 添加ST面数据
                            for val in item['sum_samples']:
                                combined_data.append({'转速': speed, '不平衡量': val, '面': 'ST'})
                        
                        df = pd.DataFrame(combined_data)
                        fig = create_combined_scatter_chart(df, combine_faces)
                    else:
                        # 不合并面，分别处理每个面
                        p1_data = []
                        p2_data = []
                        st_data = []
                        
                        for item in parsed_data:
                            speed = str(item['speed'])
                            # P1面数据
                            for val in item['p1_samples']:
                                p1_data.append({'转速': speed, '不平衡量': val})
                            # P2面数据
                            for val in item['p2_samples']:
                                p2_data.append({'转速': speed, '不平衡量': val})
                            # ST面数据
                            for val in item['sum_samples']:
                                st_data.append({'转速': speed, '不平衡量ST面': val})
                        
                        p1_df = pd.DataFrame(p1_data) if p1_data else None
                        p2_df = pd.DataFrame(p2_data) if p2_data else None
                        st_df = pd.DataFrame(st_data) if st_data else None
                        fig = create_separate_scatter_charts(p1_df, p2_df, st_df)
                elif chart_type == 'box':  # 箱线图
                    if combine_faces:
                        # 合并所有面的数据
                        combined_data = []
                        for item in parsed_data:
                            speed = str(item['speed'])
                            # 添加P1面数据
                            for val in item['p1_samples']:
                                combined_data.append({'转速': speed, '不平衡量': val, '面': 'P1'})
                            # 添加P2面数据
                            for val in item['p2_samples']:
                                combined_data.append({'转速': speed, '不平衡量': val, '面': 'P2'})
                            # 添加ST面数据
                            for val in item['sum_samples']:
                                combined_data.append({'转速': speed, '不平衡量': val, '面': 'ST'})
                        
                        df = pd.DataFrame(combined_data)
                        fig = create_combined_box_chart(df, combine_faces)
                    else:
                        # 不合并面，分别处理每个面
                        p1_data = []
                        p2_data = []
                        st_data = []
                        
                        for item in parsed_data:
                            speed = str(item['speed'])
                            # P1面数据
                            for val in item['p1_samples']:
                                p1_data.append({'转速': speed, '不平衡量': val})
                            # P2面数据
                            for val in item['p2_samples']:
                                p2_data.append({'转速': speed, '不平衡量': val})
                            # ST面数据
                            for val in item['sum_samples']:
                                st_data.append({'转速': speed, '不平衡量ST面': val})
                        
                        p1_df = pd.DataFrame(p1_data) if p1_data else None
                        p2_df = pd.DataFrame(p2_data) if p2_data else None
                        st_df = pd.DataFrame(st_data) if st_data else None
                        fig = create_separate_box_charts(p1_df, p2_df, st_df)
                else:
                    continue
                    
                if fig is None:
                    continue
                    
                chart_filename = f"{output_prefix}_combined_{chart_type}"
                png_path = os.path.join(output_folder, f"{chart_filename}.png")
                html_path = os.path.join(output_folder, f"{chart_filename}.html")
                
                # 保存图片
                pio.write_image(fig, png_path, format='png', width=1400, height=700, scale=2)
                
                # 保存HTML
                div_content = pio.to_html(fig, include_plotlyjs=True, full_html=False)
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write('<!DOCTYPE html>\n<html>\n<head>\n')
                    f.write('<meta charset="utf-8">\n')
                    f.write('<title>交互式图表</title>\n')
                    f.write('</head>\n<body>\n')
                    f.write(div_content)
                    f.write('\n</body>\n</html>')
                
                charts[chart_type] = {
                    'png': os.path.basename(png_path),
                    'html': os.path.basename(html_path)
                }
            except Exception as e:
                print(f"生成组合图表类型 '{chart_type}' 时出错: {str(e)}")
                # 即使某个图表类型失败，也要继续处理其他图表类型
                continue
        
        return charts
    except Exception as e:
        raise Exception(f"组合图表生成失败：{str(e)}")


def create_combined_trend_chart(parsed_data, combine_faces=False):
    """创建组合趋势图（折线图）"""
    fig = go.Figure()
    
    # 为每个面创建趋势线
    colors = {'P1': '#1f77b4', 'P2': '#ff7f0e', 'ST': '#2ca02c'}
    
    # P1面趋势线
    p1_speeds = []
    p1_medians = []
    for item in parsed_data:
        p1_speeds.append(str(item['speed']))
        p1_medians.append(pd.Series(item['p1_samples']).median())
    
    fig.add_trace(go.Scatter(
        x=p1_speeds,
        y=p1_medians,
        mode='lines+markers',
        line=dict(color=colors['P1'], width=3),
        marker=dict(size=8),
        name='P1面中位数趋势'
    ))
    
    # P2面趋势线
    p2_speeds = []
    p2_medians = []
    for item in parsed_data:
        p2_speeds.append(str(item['speed']))
        p2_medians.append(pd.Series(item['p2_samples']).median())
    
    fig.add_trace(go.Scatter(
        x=p2_speeds,
        y=p2_medians,
        mode='lines+markers',
        line=dict(color=colors['P2'], width=3),
        marker=dict(size=8),
        name='P2面中位数趋势'
    ))
    
    # ST面趋势线
    st_speeds = []
    st_medians = []
    for item in parsed_data:
        st_speeds.append(str(item['speed']))
        st_medians.append(pd.Series(item['sum_samples']).median())
    
    fig.add_trace(go.Scatter(
        x=st_speeds,
        y=st_medians,
        mode='lines+markers',
        line=dict(color=colors['ST'], width=3),
        marker=dict(size=8),
        name='ST面中位数趋势'
    ))
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• 不同颜色线条：各面中位数变化趋势<br>"
             "• X轴：转速<br>"
             "• Y轴：各转速下数据的中位数<br>"
             "• 圆点：各转速的具体中位数值",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title='多面中位数趋势对比图',
        xaxis_title='转速',
        yaxis_title='中位数（单位：g·mm）',
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    
    return fig


def create_combined_scatter_chart(df, combine_faces=True):
    """创建合并面的散点图"""
    fig = px.scatter(
        df,
        x='转速', y='不平衡量',
        color='面' if combine_faces else None,
        title='多面不平衡量散点图对比',
        labels={'不平衡量': '不平衡量（单位：g·mm）'},
        template='plotly_white'
    )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• 不同颜色点：不同面的数据点<br>"
             "• X轴：转速<br>"
             "• Y轴：不平衡量数值<br>"
             "• 点的分布：数据相关性分析",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    fig.update_traces(hoverinfo='skip')
    
    return fig


def create_separate_scatter_charts(p1_df, p2_df, st_df):
    """创建分离面的散点图（子图形式）"""
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('P1面不平衡量散点图', 'P2面不平衡量散点图', 'ST面不平衡量散点图'),
        vertical_spacing=0.08
    )
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    # P1面散点图
    if p1_df is not None:
        fig.add_trace(
            go.Scatter(
                x=p1_df['转速'],
                y=p1_df['不平衡量'],
                mode='markers',
                marker=dict(color=colors[0]),
                name='P1面',
                showlegend=False
            ),
            row=1, col=1
        )
    
    # P2面散点图
    if p2_df is not None:
        fig.add_trace(
            go.Scatter(
                x=p2_df['转速'],
                y=p2_df['不平衡量'],
                mode='markers',
                marker=dict(color=colors[1]),
                name='P2面',
                showlegend=False
            ),
            row=2, col=1
        )
    
    # ST面散点图
    if st_df is not None:
        fig.add_trace(
            go.Scatter(
                x=st_df['转速'],
                y=st_df['不平衡量ST面'],
                mode='markers',
                marker=dict(color=colors[2]),
                name='ST面',
                showlegend=False
            ),
            row=3, col=1
        )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• 三幅子图：分别显示各面数据点<br>"
             "• X轴：转速<br>"
             "• Y轴：不平衡量数值<br>"
             "• 点的分布：数据相关性分析",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12),
        yanchor="top"
    )
    
    fig.update_layout(
        title='多面不平衡量散点图对比',
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        height=900,
        legend=dict(
            font=dict(size=14)
        )
    )
    
    return fig


def create_combined_box_chart(df, combine_faces=True):
    """创建合并面的箱线图"""
    fig = px.box(
        df,
        x='转速', y='不平衡量',
        color='面' if combine_faces else None,
        title='多面不平衡量箱线图对比',
        labels={'不平衡量': '不平衡量（单位：g·mm）'},
        template='plotly_white'
    )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• 不同颜色箱体：不同面的数据分布<br>"
             "• 箱体：包含50%数据的四分位距(IQR)<br>"
             "• 中位数线：数据的中位数<br>"
             "• 上下须：数据范围(1.5×IQR内)<br>"
             "• 圆点：异常值",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    fig.update_traces(hoverinfo='skip')
    
    return fig


def create_separate_box_charts(p1_df, p2_df, st_df):
    """创建分离面的箱线图（子图形式）"""
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('P1面不平衡量箱线图', 'P2面不平衡量箱线图', 'ST面不平衡量箱线图'),
        vertical_spacing=0.08
    )
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    # P1面箱线图
    if p1_df is not None:
        fig.add_trace(
            go.Box(
                x=p1_df['转速'],
                y=p1_df['不平衡量'],
                marker_color=colors[0],
                name='P1面',
                showlegend=False
            ),
            row=1, col=1
        )
    
    # P2面箱线图
    if p2_df is not None:
        fig.add_trace(
            go.Box(
                x=p2_df['转速'],
                y=p2_df['不平衡量'],
                marker_color=colors[1],
                name='P2面',
                showlegend=False
            ),
            row=2, col=1
        )
    
    # ST面箱线图
    if st_df is not None:
        fig.add_trace(
            go.Box(
                x=st_df['转速'],
                y=st_df['不平衡量ST面'],
                marker_color=colors[2],
                name='ST面',
                showlegend=False
            ),
            row=3, col=1
        )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• 三幅子图：分别显示各面数据分布<br>"
             "• 箱体：包含50%数据的四分位距(IQR)<br>"
             "• 中位数线：数据的中位数<br>"
             "• 上下须：数据范围(1.5×IQR内)<br>"
             "• 圆点：异常值",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=10),
        yanchor="top"
    )
    
    fig.update_layout(
        title='多面不平衡量箱线图对比',
        title_x=0.5,
        font={
            'size': 11,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        height=900
    )
    
    return fig


def create_box_plot(data, median_dict, sorted_speeds, median_values, surface_name, color):
    """创建箱线图"""
    df = pd.DataFrame(data)
    fig = px.box(
        df,
        x='转速', y='不平衡量',
        title=f'{surface_name}不平衡量箱线图',
        labels={'不平衡量': '不平衡量（单位：g·mm）'},
        color_discrete_sequence=[color],
        template='plotly_white'
    )
    
    # 添加中位数连线
    fig.add_scatter(
        x=sorted_speeds,
        y=median_values,
        mode='lines+markers',
        line=dict(color=color, width=2),
        marker=dict(size=6),
        name=f'{surface_name}中位数',
        showlegend=True
    )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• 箱体：包含50%数据的四分位距(IQR)<br>"
             "• 中位数线：数据的中位数<br>"
             "• 上下须：数据范围(1.5×IQR内)<br>"
             "• 圆点：异常值<br>"
             "• 彩色线：各转速中位数变化趋势",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    fig.update_traces(hoverinfo='skip')
    
    return fig


def create_violin_plot(data, surface_name, color):
    """创建小提琴图"""
    df = pd.DataFrame(data)
    fig = px.violin(
        df,
        x='转速', y='不平衡量',
        title=f'{surface_name}不平衡量小提琴图',
        labels={'不平衡量': '不平衡量（单位：g·mm）'},
        color_discrete_sequence=[color],
        template='plotly_white',
        box=True,  # 显示箱线图
        points='outliers'  # 显示异常值
    )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• 形状宽度：数据密度(越宽数据越多)<br>"
             "• 中间箱线：四分位距(IQR)<br>"
             "• 白色圆点：中位数<br>"
             "• 黑色线段：数据范围<br>"
             "• 圆点：异常值",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    fig.update_traces(hoverinfo='skip')
    
    return fig


def create_scatter_plot(data, median_dict, sorted_speeds, median_values, surface_name, color):
    """创建散点图"""
    df = pd.DataFrame(data)
    
    # 创建基础散点图
    fig = px.scatter(
        df,
        x='转速', y='不平衡量',
        title=f'{surface_name}不平衡量散点图',
        labels={'不平衡量': '不平衡量（单位：g·mm）'},
        color_discrete_sequence=[color],
        template='plotly_white'
    )
    
    # 添加中位数连线
    fig.add_scatter(
        x=sorted_speeds,
        y=median_values,
        mode='lines+markers',
        line=dict(color=color, width=2),
        marker=dict(size=6),
        name=f'{surface_name}中位数',
        showlegend=True
    )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• 圆点：各数据点<br>"
             "• 彩色线和圆点：各转速中位数<br>"
             "• 线条走势：中位数变化趋势<br>"
             "• 点的密集程度：数据离散情况",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    fig.update_traces(hoverinfo='skip')
    
    return fig


def create_trend_plot(median_dict, sorted_speeds, median_values, surface_name, color):
    """创建趋势图（仅显示中位数）"""
    fig = go.Figure()
    
    # 添加中位数趋势线
    fig.add_trace(go.Scatter(
        x=sorted_speeds,
        y=median_values,
        mode='lines+markers',
        line=dict(color=color, width=3),
        marker=dict(size=8),
        name=f'{surface_name}中位数趋势'
    ))
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• X轴：转速<br>"
             "• Y轴：各转速下数据的中位数<br>"
             "• 线条走势：中位数随转速变化趋势<br>"
             "• 圆点：各转速的具体中位数值",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title=f'{surface_name}中位数趋势图',
        xaxis_title='转速',
        yaxis_title='中位数（单位：g·mm）',
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    
    return fig


def create_heatmap_plot(data, surface_name, color):
    """创建热力图"""
    df = pd.DataFrame(data)
    
    # 检查是否有足够的数据
    if df.empty:
        # 如果没有数据，返回一个空图表
        fig = go.Figure()
        fig.update_layout(
            title=f'{surface_name}不平衡量热力图',
            annotations=[
                dict(
                    text="无数据可显示",
                    showarrow=False,
                    font=dict(size=16)
                )
            ]
        )
        return fig
    
    # 创建透视表
    try:
        pivot_table = df.pivot_table(values='不平衡量', index='转速', aggfunc=list)
    except Exception as e:
        # 如果透视表创建失败，返回一个空图表
        fig = go.Figure()
        fig.update_layout(
            title=f'{surface_name}不平衡量热力图',
            annotations=[
                dict(
                    text="数据格式不正确，无法创建热力图",
                    showarrow=False,
                    font=dict(size=16)
                )
            ]
        )
        return fig
    
    # 检查透视表是否为空
    if pivot_table.empty:
        # 如果透视表为空，返回一个空图表
        fig = go.Figure()
        fig.update_layout(
            title=f'{surface_name}不平衡量热力图',
            annotations=[
                dict(
                    text="无有效数据可显示",
                    showarrow=False,
                    font=dict(size=16)
                )
            ]
        )
        return fig
    
    # 准备热力图数据
    x_labels = []      # X轴标签（转速）
    heatmap_data = []  # 热力图数据
    max_len = 0        # 最大数组长度
    
    # 找到最长的数组长度
    for values in pivot_table.values:
        max_len = max(max_len, len(values))
    
    if max_len == 0:
        # 如果没有数据，返回一个空图表
        fig = go.Figure()
        fig.update_layout(
            title=f'{surface_name}不平衡量热力图',
            annotations=[
                dict(
                    text="无数据可显示",
                    showarrow=False,
                    font=dict(size=16)
                )
            ]
        )
        return fig
    
    y_labels = list(range(max_len))  # Y轴标签
    
    for speed in pivot_table.index:
        values = pivot_table.loc[speed]
        # 填充数据使所有数组长度一致
        if len(values) < max_len:
            padded_values = list(values) + [np.nan] * (max_len - len(values))
        else:
            padded_values = list(values)
        x_labels.extend([speed] * max_len)
        heatmap_data.extend(padded_values)
    
    # 创建一个新的DataFrame用于热力图
    # 确保所有列具有相同的长度
    y_labels_repeated = y_labels * len(pivot_table.index)
    
    heatmap_df = pd.DataFrame({
        '转速': x_labels,
        '数据点': y_labels_repeated,
        '不平衡量': heatmap_data
    })
    
    # 检查数据是否为空
    if heatmap_df.empty or heatmap_df['不平衡量'].dropna().empty:
        # 如果没有有效数据，返回一个空图表
        fig = go.Figure()
        fig.update_layout(
            title=f'{surface_name}不平衡量热力图',
            annotations=[
                dict(
                    text="无有效数据可显示",
                    showarrow=False,
                    font=dict(size=16)
                )
            ]
        )
        return fig
    
    try:
        fig = px.density_heatmap(
            heatmap_df,
            x='转速',
            y='数据点',
            z='不平衡量',
            title=f'{surface_name}不平衡量热力图',
            labels={'不平衡量': '不平衡量（单位：g·mm）'},
            color_continuous_scale='Viridis'
        )
    except Exception as e:
        # 如果热力图创建失败，返回一个空图表
        fig = go.Figure()
        fig.update_layout(
            title=f'{surface_name}不平衡量热力图',
            annotations=[
                dict(
                    text="图表生成失败：" + str(e),
                    showarrow=False,
                    font=dict(size=16)
                )
            ]
        )
        return fig
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• X轴：转速<br>"
             "• Y轴：数据点索引<br>"
             "• 颜色深浅：不平衡量数值大小<br>"
             "• 颜色越黄：数值越大<br>"
             "• 颜色越蓝：数值越小",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    
    return fig


def create_histogram_plot(data, surface_name, color):
    """创建直方图"""
    df = pd.DataFrame(data)
    fig = px.histogram(
        df,
        x='不平衡量',
        title=f'{surface_name}不平衡量直方图',
        labels={'不平衡量': '不平衡量（单位：g·mm）', 'count': '频次'},
        color_discrete_sequence=[color],
        template='plotly_white',
        nbins=30
    )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• X轴：不平衡量数值区间<br>"
             "• Y轴：落在各区间的频次<br>"
             "• 柱形高度：数据分布情况<br>"
             "• 峰值位置：数据集中的区间",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    
    return fig


def create_3d_scatter_plot(data, median_dict, sorted_speeds, median_values, surface_name, color):
    """创建3D散点图"""
    df = pd.DataFrame(data)
    
    # 为了创建3D图，我们需要三个维度：转速、数据点索引和不平衡量
    # 添加索引列
    df['index'] = df.groupby('转速').cumcount()
    
    fig = px.scatter_3d(
        df,
        x='转速',
        y='index',
        z='不平衡量',
        title=f'{surface_name}不平衡量3D散点图',
        labels={
            '转速': '转速',
            'index': '数据点索引',
            '不平衡量': '不平衡量（单位：g·mm）'
        },
        color_discrete_sequence=[color],
        template='plotly_white'
    )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• X轴：转速<br>"
             "• Y轴：数据点索引<br>"
             "• Z轴：不平衡量数值<br>"
             "• 点的空间分布：三维数据关系<br>"
             "• 点的高度：数值大小",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=00.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    
    return fig


def create_st_box_plot(data, surface_name, color):
    """创建ST面箱线图"""
    df = pd.DataFrame(data)
    fig = px.box(
        df,
        x='转速', y='不平衡量ST面',
        title=f'{surface_name}不平衡量箱线图',
        labels={'不平衡量ST面': '不平衡量ST面（单位：g·mm）'},
        color_discrete_sequence=[color],
        template='plotly_white'
    )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• 箱体：包含50%数据的四分位距(IQR)<br>"
             "• 中位数线：数据的中位数<br>"
             "• 上下须：数据范围(1.5×IQR内)<br>"
             "• 圆点：异常值",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    fig.update_traces(hoverinfo='skip')
    
    return fig


def create_st_violin_plot(data, surface_name, color):
    """创建ST面小提琴图"""
    df = pd.DataFrame(data)
    fig = px.violin(
        df,
        x='转速', y='不平衡量ST面',
        title=f'{surface_name}不平衡量小提琴图',
        labels={'不平衡量ST面': '不平衡量ST面（单位：g·mm）'},
        color_discrete_sequence=[color],
        template='plotly_white',
        box=True,  # 显示箱线图
        points='outliers'  # 显示异常值
    )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• 形状宽度：数据密度(越宽数据越多)<br>"
             "• 中间箱线：四分位距(IQR)<br>"
             "• 白色圆点：中位数<br>"
             "• 黑色线段：数据范围<br>"
             "• 圆点：异常值",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    fig.update_traces(hoverinfo='skip')
    
    return fig


def create_st_scatter_plot(data, median_dict, surface_name, color):
    """创建ST面散点图"""
    df = pd.DataFrame(data)
    
    # 计算中位数
    sorted_speeds = sorted(median_dict.keys(), key=lambda x: float(''.join(filter(str.isdigit, x))))
    median_values = [median_dict[speed] for speed in sorted_speeds]
    
    # 创建基础散点图
    fig = px.scatter(
        df,
        x='转速', y='不平衡量ST面',
        title=f'{surface_name}不平衡量散点图',
        labels={'不平衡量ST面': '不平衡量ST面（单位：g·mm）'},
        color_discrete_sequence=[color],
        template='plotly_white'
    )
    
    # 添加中位数连线
    fig.add_scatter(
        x=sorted_speeds,
        y=median_values,
        mode='lines+markers',
        line=dict(color=color, width=2),
        marker=dict(size=6),
        name=f'{surface_name}中位数',
        showlegend=True
    )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• 圆点：各数据点<br>"
             "• 彩色线和圆点：各转速中位数<br>"
             "• 线条走势：中位数变化趋势<br>"
             "• 点的密集程度：数据离散情况",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    fig.update_traces(hoverinfo='skip')
    
    return fig


def create_st_trend_plot(median_dict, surface_name, color):
    """创建ST面趋势图（仅显示中位数）"""
    fig = go.Figure()
    
    # 按转速排序
    sorted_speeds = sorted(median_dict.keys(), key=lambda x: float(''.join(filter(str.isdigit, x))))
    median_values = [median_dict[speed] for speed in sorted_speeds]
    
    # 添加中位数趋势线
    fig.add_trace(go.Scatter(
        x=sorted_speeds,
        y=median_values,
        mode='lines+markers',
        line=dict(color=color, width=3),
        marker=dict(size=8),
        name=f'{surface_name}中位数趋势'
    ))
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• X轴：转速<br>"
             "• Y轴：各转速下数据的中位数<br>"
             "• 线条走势：中位数随转速变化趋势<br>"
             "• 圆点：各转速的具体中位数值",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title=f'{surface_name}中位数趋势图',
        xaxis_title='转速',
        yaxis_title='中位数（单位：g·mm）',
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    
    return fig


def create_st_heatmap_plot(data, surface_name):
    """创建ST面热力图"""
    df = pd.DataFrame(data)
    
    # 检查是否有足够的数据
    if df.empty:
        # 如果没有数据，返回一个空图表
        fig = go.Figure()
        fig.update_layout(
            title=f'{surface_name}不平衡量热力图',
            annotations=[
                dict(
                    text="无数据可显示",
                    showarrow=False,
                    font=dict(size=16)
                )
            ]
        )
        return fig
    
    # 创建透视表
    try:
        pivot_table = df.pivot_table(values='不平衡量ST面', index='转速', aggfunc=list)
    except Exception as e:
        # 如果透视表创建失败，返回一个空图表
        fig = go.Figure()
        fig.update_layout(
            title=f'{surface_name}不平衡量热力图',
            annotations=[
                dict(
                    text="数据格式不正确，无法创建热力图",
                    showarrow=False,
                    font=dict(size=16)
                )
            ]
        )
        return fig
    
    # 检查透视表是否为空
    if pivot_table.empty:
        # 如果透视表为空，返回一个空图表
        fig = go.Figure()
        fig.update_layout(
            title=f'{surface_name}不平衡量热力图',
            annotations=[
                dict(
                    text="无有效数据可显示",
                    showarrow=False,
                    font=dict(size=16)
                )
            ]
        )
        return fig
    
    # 准备热力图数据
    x_labels = []      # X轴标签（转速）
    heatmap_data = []  # 热力图数据
    max_len = 0        # 最大数组长度
    
    # 找到最长的数组长度
    for values in pivot_table.values:
        max_len = max(max_len, len(values))
    
    if max_len == 0:
        # 如果没有数据，返回一个空图表
        fig = go.Figure()
        fig.update_layout(
            title=f'{surface_name}不平衡量热力图',
            annotations=[
                dict(
                    text="无数据可显示",
                    showarrow=False,
                    font=dict(size=16)
                )
            ]
        )
        return fig
    
    y_labels = list(range(max_len))  # Y轴标签
    
    for speed in pivot_table.index:
        values = pivot_table.loc[speed]
        # 填充数据使所有数组长度一致
        if len(values) < max_len:
            padded_values = list(values) + [np.nan] * (max_len - len(values))
        else:
            padded_values = list(values)
        x_labels.extend([speed] * max_len)
        heatmap_data.extend(padded_values)
    
    # 创建一个新的DataFrame用于热力图
    # 确保所有列具有相同的长度
    y_labels_repeated = y_labels * len(pivot_table.index)
    
    heatmap_df = pd.DataFrame({
        '转速': x_labels,
        '数据点': y_labels_repeated,
        '不平衡量ST面': heatmap_data
    })
    
    # 检查数据是否为空
    if heatmap_df.empty or heatmap_df['不平衡量ST面'].dropna().empty:
        # 如果没有有效数据，返回一个空图表
        fig = go.Figure()
        fig.update_layout(
            title=f'{surface_name}不平衡量热力图',
            annotations=[
                dict(
                    text="无有效数据可显示",
                    showarrow=False,
                    font=dict(size=16)
                )
            ]
        )
        return fig
    
    try:
        fig = px.density_heatmap(
            heatmap_df,
            x='转速',
            y='数据点',
            z='不平衡量ST面',
            title=f'{surface_name}不平衡量热力图',
            labels={'不平衡量ST面': '不平衡量ST面（单位：g·mm）'},
            color_continuous_scale='Viridis'
        )
    except Exception as e:
        # 如果热力图创建失败，返回一个空图表
        fig = go.Figure()
        fig.update_layout(
            title=f'{surface_name}不平衡量热力图',
            annotations=[
                dict(
                    text="图表生成失败：" + str(e),
                    showarrow=False,
                    font=dict(size=16)
                )
            ]
        )
        return fig
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• X轴：转速<br>"
             "• Y轴：数据点索引<br>"
             "• 颜色深浅：不平衡量数值大小<br>"
             "• 颜色越黄：数值越大<br>"
             "• 颜色越蓝：数值越小",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    
    return fig


def create_st_histogram_plot(data, surface_name, color):
    """创建ST面直方图"""
    df = pd.DataFrame(data)
    fig = px.histogram(
        df,
        x='不平衡量ST面',
        title=f'{surface_name}不平衡量直方图',
        labels={'不平衡量ST面': '不平衡量ST面（单位：g·mm）', 'count': '频次'},
        color_discrete_sequence=[color],
        template='plotly_white',
        nbins=30
    )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• X轴：不平衡量数值区间<br>"
             "• Y轴：落在各区间的频次<br>"
             "• 柱形高度：数据分布情况<br>"
             "• 峰值位置：数据集中的区间",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    
    return fig


def create_st_3d_scatter_plot(data, surface_name, color):
    """创建ST面3D散点图"""
    df = pd.DataFrame(data)
    
    # 为了创建3D图，我们需要三个维度：转速、数据点索引和不平衡量
    # 添加索引列
    df['index'] = df.groupby('转速').cumcount()
    
    fig = px.scatter_3d(
        df,
        x='转速',
        y='index',
        z='不平衡量ST面',
        title=f'{surface_name}不平衡量3D散点图',
        labels={
            '转速': '转速',
            'index': '数据点索引',
            '不平衡量ST面': '不平衡量ST面（单位：g·mm）'
        },
        color_discrete_sequence=[color],
        template='plotly_white'
    )
    
    # 添加图表说明
    fig.add_annotation(
        text="<b>图表指标说明：</b><br>"
             "• X轴：转速<br>"
             "• Y轴：数据点索引<br>"
             "• Z轴：不平衡量数值<br>"
             "• 点的空间分布：三维数据关系<br>"
             "• 点的高度：数值大小",
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1,
        align="left",
        font=dict(size=12)
    )
    
    fig.update_layout(
        title_x=0.5,
        font={
            'size': 14,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50},
        legend=dict(
            font=dict(size=14)
        )
    )
    
    return fig