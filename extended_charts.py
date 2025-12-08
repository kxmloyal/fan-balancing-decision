import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os

def create_heatmap(data, surface_name, color):
    """创建热力图"""
    # 将数据转换为适合热力图的格式
    df = pd.DataFrame(data)
    
    # 创建透视表，转速为行，数据值为列
    pivot_table = df.pivot_table(index='转速', values='不平衡量', aggfunc='count')
    
    fig = go.Figure(data=go.Heatmap(
        z=df['不平衡量'],
        x=df['转速'],
        y=df['不平衡量'],
        colorscale='Viridis'
    ))
    
    fig.update_layout(
        title=f'{surface_name}数据分布热力图',
        xaxis_title='转速',
        yaxis_title='不平衡量（单位：g·mm）',
        title_x=0.5,
        font={
            'size': 11,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50}
    )
    
    return fig

def create_histogram(data, surface_name, color):
    """创建直方图"""
    df = pd.DataFrame(data)
    
    fig = px.histogram(
        df,
        x='不平衡量',
        title=f'{surface_name}数据分布直方图',
        color_discrete_sequence=[color],
        template='plotly_white'
    )
    
    fig.update_layout(
        xaxis_title='不平衡量（单位：g·mm）',
        yaxis_title='频次',
        title_x=0.5,
        font={
            'size': 11,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50}
    )
    
    return fig

def create_radar_chart(median_dict, surface_name, color):
    """创建雷达图"""
    categories = list(median_dict.keys())
    values = list(median_dict.values())
    
    # 为了形成闭合图形，需要在末尾添加第一个点
    categories.append(categories[0])
    values.append(values[0])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=surface_name,
        line=dict(color=color)
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[min(values), max(values)]
            )
        ),
        title=f'{surface_name}各转速中位数雷达图',
        title_x=0.5,
        font={
            'size': 11,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        }
    )
    
    return fig

def create_3d_scatter(data, median_dict, surface_name, color):
    """创建3D散点图"""
    df = pd.DataFrame(data)
    
    # 添加中位数信息
    df['中位数'] = df['转速'].map(median_dict)
    
    fig = px.scatter_3d(
        df,
        x='转速',
        y='不平衡量',
        z='中位数',
        title=f'{surface_name} 3D数据分布图',
        color_discrete_sequence=[color],
        template='plotly_white'
    )
    
    fig.update_layout(
        scene=dict(
            xaxis_title='转速',
            yaxis_title='不平衡量（单位：g·mm）',
            zaxis_title='中位数（单位：g·mm）'
        ),
        title_x=0.5,
        font={
            'size': 11,
            'family': '"SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif'
        },
        margin={'l': 50, 'r': 20, 't': 60, 'b': 50}
    )
    
    return fig

def save_extended_chart(fig, output_prefix, surface_name, chart_type, output_folder):
    """保存扩展图表"""
    chart_filename = f"{output_prefix}_{surface_name.lower().replace('面', '')}_{chart_type}"
    png_path = os.path.join(output_folder, f"{chart_filename}.png")
    html_path = os.path.join(output_folder, f"{chart_filename}.html")
    
    # 保存图片
    fig.write_image(png_path, format='png', width=1400, height=700, scale=2)
    
    # 保存HTML
    div_content = fig.to_html(include_plotlyjs=True, full_html=False)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write('<!DOCTYPE html>\n<html>\n<head>\n')
        f.write('<meta charset="utf-8">\n')
        f.write('<title>交互式图表</title>\n')
        f.write('</head>\n<body>\n')
        f.write(div_content)
        f.write('\n</body>\n</html>')
    
    return {
        'png': os.path.basename(png_path),
        'html': os.path.basename(html_path)
    }