#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查所有必要的模块是否能正常导入
"""

import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("=== 开始检查模块导入 ===")

# 检查核心模块
core_modules = [
    'pandas',
    'flask',
    'flask_sqlalchemy',
    'werkzeug.utils',
    'apscheduler.schedulers.background',
]

for module in core_modules:
    try:
        __import__(module)
        print(f"✓ {module} 导入成功")
    except Exception as e:
        print(f"✗ {module} 导入失败: {e}")

# 检查自定义模块
custom_modules = [
    'utils.file_manager',
    'utils.config_manager',
    'utils.error_handler',
    'chart_generation',
    'data_processing',
    'statistics',
    'blueprints.main_bp',
    'blueprints.report_bp',
    'blueprints.ml_bp',
    'blueprints.outputs_bp',
    'blueprints.settings_bp',
]

for module in custom_modules:
    try:
        __import__(module)
        print(f"✓ {module} 导入成功")
    except Exception as e:
        print(f"✗ {module} 导入失败: {e}")
        import traceback
        traceback.print_exc()

print("=== 模块导入检查完成 ===")
