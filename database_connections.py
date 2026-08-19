#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接配置管理模块（向后兼容 shim）

⚠️ 本文档已重构为三层架构，请优先使用新模块：
  - app/models/db_connection_config.py  → DatabaseConnection 数据模型
  - app/services/connection_manager.py  → ConnectionManager CRUD 管理
  - app/services/connection_tester.py   → ConnectionTester 连接测试

本文件保留所有原有导出符号以确保向后兼容，
现有 from database_connections import ... 无需修改。
"""

import importlib

_LAZY_ATTRS = {
    "DatabaseConnection": "app.models.db_connection_config",
    "ConnectionManager": "app.services.connection_manager",
    "ConnectionTester": "app.services.connection_tester",
    "connection_manager": "app.services.connection_manager",
    "connection_tester": "app.services.connection_tester",
    "test_connection_with_timeout": "app.services.connection_tester",
    "CACHE_MAX_SIZE": "app.services.connection_tester",
    "DB_CONNECTION_TIMEOUT": "app.services.connection_tester",
}

_loaded = {}


def __getattr__(name):
    if name in _loaded:
        return _loaded[name]
    if name in _LAZY_ATTRS:
        mod = importlib.import_module(_LAZY_ATTRS[name])
        attr = getattr(mod, name)
        _loaded[name] = attr
        return attr
    raise AttributeError(f"module 'database_connections' has no attribute '{name}'")


__all__ = list(_LAZY_ATTRS.keys())
