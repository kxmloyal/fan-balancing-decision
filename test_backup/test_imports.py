#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试模块导入情况
"""

import sys
import os

print("=== 测试模块导入 ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# 测试基础模块
print("\n1. 测试基础模块导入:")
try:
    import gc
    import datetime
    print("✓ 基础模块导入成功")
except Exception as e:
    print(f"✗ 基础模块导入失败: {e}")

# 测试pandas
print("\n2. 测试pandas导入:")
try:
    import pandas as pd
    print(f"✓ pandas导入成功，版本: {pd.__version__}")
except Exception as e:
    print(f"✗ pandas导入失败: {e}")

# 测试Flask
print("\n3. 测试Flask导入:")
try:
    import flask
    print(f"✓ Flask导入成功，版本: {flask.__version__}")
except Exception as e:
    print(f"✗ Flask导入失败: {e}")

# 测试SQLAlchemy
print("\n4. 测试SQLAlchemy导入:")
try:
    from flask_sqlalchemy import SQLAlchemy
    print("✓ SQLAlchemy导入成功")
except Exception as e:
    print(f"✗ SQLAlchemy导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试APScheduler
print("\n5. 测试APScheduler导入:")
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    print("✓ APScheduler导入成功")
except Exception as e:
    print(f"✗ APScheduler导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试自定义模块
print("\n6. 测试自定义模块导入:")
try:
    from utils.file_manager import file_manager
    print("✓ file_manager导入成功")
except Exception as e:
    print(f"✗ file_manager导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试完成 ===")
