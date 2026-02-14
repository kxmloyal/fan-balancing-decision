import json
import os
from chart_generation import generate_generic_charts

# 测试修改后的图表生成和导出功能
print("测试修改后的图表生成和导出功能...")

# 模拟测试数据
test_data = [
    {"转速": "2500rpm", "不平衡量": 1.1},
    {"转速": "2500rpm", "不平衡量": 2.2},
    {"转速": "2500rpm", "不平衡量": 3.3},
    {"转速": "3000rpm", "不平衡量": 4.4},
    {"转速": "3000rpm", "不平衡量": 5.5},
    {"转速": "3000rpm", "不平衡量": 6.6},
]

# 测试参数
output_prefix = "test"
output_folder = "outputs"
surface_name = "P1面"
color = "#1f77b4"
chart_types = ["box"]
is_st_surface = False
sorted_speeds = ["2500rpm", "3000rpm"]
median_values = [2.2, 5.5]

# 确保输出目录存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 生成图表
try:
    print("生成图表...")
    charts = generate_generic_charts(
        data=test_data,
        median_dict={"2500rpm": 2.2, "3000rpm": 5.5},
        surface_name=surface_name,
        color=color,
        output_prefix=output_prefix,
        output_folder=output_folder,
        chart_types=chart_types,
        is_st_surface=is_st_surface,
        sorted_speeds=sorted_speeds,
        median_values=median_values
    )
    print(f"图表生成成功: {charts}")
    
    # 检查图表属性是否正确保存
    for chart_type, chart_info in charts.items():
        print(f"\n图表类型: {chart_type}")
        print(f"图表文件: {chart_info['png']}")
        print(f"图表HTML: {chart_info['html']}")
        print(f"图表属性: {json.dumps(chart_info.get('chart_properties', {}), ensure_ascii=False, indent=2)}")
        
    print("\n测试成功！图表生成和属性保存正常。")
except Exception as e:
    print(f"测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n测试完成！")
