print("开始测试导入...")

try:
    import app
    print("✓ app 导入成功")
except Exception as e:
    print(f"✗ app 导入失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n---\n")

try:
    import data_processing
    print("✓ data_processing 导入成功")
except Exception as e:
    print(f"✗ data_processing 导入失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n---\n")

try:
    import chart_generation
    print("✓ chart_generation 导入成功")
except Exception as e:
    print(f"✗ chart_generation 导入失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n---\n")

try:
    import statistics
    print("✓ statistics 导入成功")
except Exception as e:
    print(f"✗ statistics 导入失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n---\n")

try:
    from utils import data_validator
    print("✓ utils.data_validator 导入成功")
except Exception as e:
    print(f"✗ utils.data_validator 导入失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n---\n")

try:
    from utils import chart_cache
    print("✓ utils.chart_cache 导入成功")
except Exception as e:
    print(f"✗ utils.chart_cache 导入失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()