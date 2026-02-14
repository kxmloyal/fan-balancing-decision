# 最基本的测试脚本，检查Python是否能正常运行
print("Python 环境测试")
print("------------------")
print("Python 版本:")
import sys
print(sys.version)
print("------------------")
print("当前工作目录:")
import os
print(os.getcwd())
print("------------------")
print("基本导入测试:")
try:
    import math
    print("✓ math 模块导入成功")
    print(f"  π 的值: {math.pi}")
except Exception as e:
    print(f"✗ math 模块导入失败: {e}")
print("------------------")
print("测试完成!")
