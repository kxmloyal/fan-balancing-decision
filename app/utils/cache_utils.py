#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
轻量级 TTL 内存缓存工具

用于缓存文件系统扫描结果和数据库聚合查询，减少重复 I/O 开销。
线程安全，适用于 gunicorn 多 worker 场景（各 worker 独立缓存）。
"""

import functools
import threading
import time


class TTLCache:
    """带过期时间的线程安全内存缓存"""

    def __init__(self, default_ttl=60):
        self._store = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl

    def get(self, key):
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.monotonic() > entry["expires"]:
                del self._store[key]
                return None
            return entry["value"]

    def set(self, key, value, ttl=None):
        with self._lock:
            self._store[key] = {
                "value": value,
                "expires": time.monotonic() + (ttl or self._default_ttl),
            }

    def delete(self, key):
        with self._lock:
            self._store.pop(key, None)

    def clear(self):
        with self._lock:
            self._store.clear()

    def cached(self, ttl=None, key_fn=None):
        """装饰器：自动缓存函数返回值

        Args:
            ttl: 缓存过期秒数（默认使用实例 default_ttl）
            key_fn: 自定义缓存键生成函数，接收原函数参数
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if key_fn:
                    cache_key = key_fn(*args, **kwargs)
                else:
                    cache_key = f"{func.__module__}.{func.__name__}:{args}:{sorted(kwargs.items())}"
                cached_val = self.get(cache_key)
                if cached_val is not None:
                    return cached_val
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result

            wrapper._cache = self
            return wrapper

        return decorator


# 全局缓存实例
file_cache = TTLCache(default_ttl=30)    # 文件系统扫描：30秒
query_cache = TTLCache(default_ttl=60)   # 数据库查询：60秒
