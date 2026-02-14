import sys
import traceback

# 测试顺序：基础库 → 第三方库 → 自定义模块
test_modules = [
    # 基础库
    'os',
    're',
    'logging',
    'datetime',
    'functools',
    # 第三方库
    'flask',
    'werkzeug',
    'pandas',
    'base64',
    # 自定义模块
    'data_processing',
    'utils.data_validator',
    'chart_generation',
    'statistics'
]

print("开始测试模块导入...")
print("=" * 50)

for module_name in test_modules:
    try:
        __import__(module_name)
        print(f"✓ {module_name}")
    except Exception as e:
        print(f"✗ {module_name}")
        print(f"  错误: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

print("=" * 50)
print("所有模块导入成功！")