import matplotlib.pyplot as plt
import numpy as np
import os

# 创建测试数据
data = np.random.normal(100, 15, 1000)

# 创建图表
plt.figure(figsize=(10, 6))
plt.hist(data, bins=30, alpha=0.7, color='blue', edgecolor='black')
plt.title('测试直方图')
plt.xlabel('值')
plt.ylabel('频率')
plt.grid(True, alpha=0.3)

# 保存图表
test_dir = '/www/wwwroot/xiangxiantu/static/charts'
if not os.path.exists(test_dir):
    os.makedirs(test_dir)

output_path = os.path.join(test_dir, 'test_chart.png')
plt.savefig(output_path)
plt.close()

# 检查文件是否生成
if os.path.exists(output_path):
    print(f"图表生成成功: {output_path}")
    print(f"文件大小: {os.path.getsize(output_path)} 字节")
else:
    print("图表生成失败")
