import importlib
import sys

def check_module(module_name):
    try:
        module = importlib.import_module(module_name)
        print(f"✓ {module_name} 导入成功")
        return True
    except Exception as e:
        print(f"✗ {module_name} 导入失败: {e}")
        return False

# 添加当前目录到sys.path
sys.path.insert(0, '.')

# 检查主要模块
modules_to_check = [
    'app',
    'data_processing',
    'chart_generation',
    'statistics',
    'utils.data_validator',
    'utils.chart_cache'
]

print("开始检查模块导入...")
print("=" * 50)

for module in modules_to_check:
    check_module(module)

print("=" * 50)
print("检查完成!")