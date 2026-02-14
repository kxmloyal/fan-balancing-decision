import sys
import traceback

try:
    from app import app
    print("✓ 成功导入app模块")
    print("✓ app对象创建成功")
except Exception as e:
    print("✗ 导入app模块失败")
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {str(e)}")
    print("\n详细堆栈信息:")
    traceback.print_exc()
    sys.exit(1)