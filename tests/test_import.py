#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 测试从app.py导入app对象
try:
    from app import app

    print("Successfully imported app from app.py")
    print(f"App name: {app.name}")
except Exception as e:
    print(f"Failed to import app from app.py: {e}")

# 测试从wsgi.py导入app对象
try:
    from wsgi import app

    print("Successfully imported app from wsgi.py")
    print(f"App name: {app.name}")
except Exception as e:
    print(f"Failed to import app from wsgi.py: {e}")
