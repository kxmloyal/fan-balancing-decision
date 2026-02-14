import json
import matplotlib.pyplot as plt
import numpy as np
import os

# 从实际文件中读取图表数据
try:
    # 检查是否存在测试图表文件
    test_files = os.listdir('/www/wwwroot/xiangxiantu/outputs/')
    chart_files = [f for f in test_files if f.endswith('_box.html')]
    
    if chart_files:
        chart_file = chart_files[-1]  # 取最新的图表文件
        chart_file_path = os.path.join('/www/wwwroot/xiangxiantu/outputs/', chart_file)
        print(f"读取图表数据文件: {chart_file_path}")
        
        # 读取图表数据文件
        with open(chart_file_path, 'r') as f:
            content = f.read()
        
        # 提取图表数据
        import re
        match = re.search(r'var chartData = (.*?);', content)
        if match:
            chart_data_str = match.group(1)
            print(f"提取的图表数据: {chart_data_str[:200]}...")
            
            # 测试图表生成
            surface_name = 'P1'
            chart_type = 'box'
            png_path = '/www/wwwroot/xiangxiantu/test_chart.png'
            
            try:
                print("开始测试图表生成...")
                # 设置中文字体
                plt.rcParams['font.family'] = ['sans-serif']
                plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
                plt.rcParams['text.usetex'] = False
                
                # 解析图表数据
                chart_data_json = json.loads(chart_data_str)
                print(f"解析的图表数据: {chart_data_json}")
                
                # 根据图表类型生成不同的图像
                fig, ax = plt.subplots(figsize=(10, 6))
                
                if chart_type == 'box':
                    # 箱线图
                    box_data = []
                    labels = []
                    for item in chart_data_json:
                        if 'data' in item and 'name' in item:
                            box_data.append(item['data'])
                            labels.append(item['name'])
                    print(f"箱线图数据: {box_data}")
                    print(f"标签: {labels}")
                    if box_data:
                        ax.boxplot(box_data)
                        ax.set_xticklabels(labels, rotation=45, ha='right')
                        ax.set_title(f"{surface_name} 箱线图")
                        ax.set_ylabel('不平衡量')
                
                # 保存图像
                plt.tight_layout()
                plt.savefig(png_path, dpi=150, bbox_inches='tight')
                plt.close()
                print(f"图表生成成功: {png_path}")
                print(f"文件大小: {os.path.getsize(png_path)} 字节")
            except Exception as e:
                print(f"生成图表图像失败: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print("无法提取图表数据")
    else:
        print("没有找到图表文件")
except Exception as e:
    print(f"读取文件失败: {str(e)}")
    import traceback
    traceback.print_exc()
