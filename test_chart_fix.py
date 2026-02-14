import json
import matplotlib.pyplot as plt
import numpy as np
import os

# 测试修复后的图表数据生成
def test_chart_data_generation():
    """测试图表数据生成是否正常"""
    try:
        print("开始测试修复后的图表数据生成...")
        
        # 模拟测试数据
        test_data = [
            {"转速": "2500rpm", "不平衡量": 1.1},
            {"转速": "2500rpm", "不平衡量": 2.2},
            {"转速": "2500rpm", "不平衡量": 3.3},
            {"转速": "3000rpm", "不平衡量": 4.4},
            {"转速": "3000rpm", "不平衡量": 5.5},
            {"转速": "3000rpm", "不平衡量": 6.6},
        ]
        
        # 导入生成图表数据的函数
        from chart_generation import generate_chart_data
        
        # 生成箱线图数据
        chart_type = "box"
        raw_data = generate_chart_data(test_data, chart_type)
        print(f"生成的原始数据: {raw_data}")
        
        # 将Python对象转换为JSON字符串
        json_str = json.dumps(raw_data)
        print(f"生成的JSON字符串: {json_str}")
        
        # 测试JSON解析
        try:
            parsed_data = json.loads(json_str)
            print(f"解析成功的JSON数据: {parsed_data}")
        except Exception as e:
            print(f"JSON解析失败: {str(e)}")
            return False
        
        # 测试图表生成
        surface_name = 'P1'
        png_path = '/www/wwwroot/xiangxiantu/test_chart.png'
        
        try:
            print("开始测试图表生成...")
            # 设置中文字体
            plt.rcParams['font.family'] = ['sans-serif']
            plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['text.usetex'] = False
            
            # 解析图表数据
            chart_data_json = json.loads(json_str)
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
            return True
        except Exception as e:
            print(f"生成图表图像失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chart_data_generation()
    if success:
        print("\n测试成功！图表数据生成和解析正常。")
    else:
        print("\n测试失败！图表数据生成或解析出现问题。")
