#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
app 包 — 兼容桥接层

此模块是历史遗留兼容层，为以下旧式导入提供桥接：
    from app import app
    from app import db

实际 Flask 应用在 wsgi.py 中创建和管理。本模块不应扩展新逻辑，
所有蓝图注册、中间件配置、路由定义均在 wsgi.py 完成。
"""

import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

# 懒加载：避免在包导入阶段触发 wsgi.py（wsgi.py 导入蓝图时会反向引用本包）
_app = None


def __getattr__(name):
    if name == "app":
        global _app
        if _app is None:
            from wsgi import app as _wsgi_app

            _app = _wsgi_app
        return _app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["app"]
