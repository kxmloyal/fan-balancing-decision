#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图表缓存管理（chart_generation_optimized 拆分模块）

包含内存缓存（LRU+过期清理）与数据库缓存（默认禁用，DB_CONNECTED 为占位）。
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict

logger = logging.getLogger(__name__)

# 数据库连接配置（占位，与 db_models 解耦；未接入时数据库缓存默认禁用）
DB_CONNECTED = False
db = None
ChartCache = None

# 内存缓存
_chart_data_cache = {}
_chart_cache_metadata = {}  # 缓存元数据：{cache_key: {timestamp, size}}
_MAX_CACHE_SIZE = 100  # 最大缓存数量
_CACHE_EXPIRY_HOURS = 24  # 缓存过期时间（小时）


def _clean_expired_cache():
    """清理过期和超量的缓存"""
    now = datetime.now()
    expiry_time = timedelta(hours=_CACHE_EXPIRY_HOURS)

    # 清理过期缓存
    expired_keys = []
    for key, meta in list(_chart_cache_metadata.items()):
        if now - meta["timestamp"] > expiry_time:
            expired_keys.append(key)

    for key in expired_keys:
        _chart_data_cache.pop(key, None)
        _chart_cache_metadata.pop(key, None)

    # 清理超量缓存（使用LRU策略）
    if len(_chart_data_cache) > _MAX_CACHE_SIZE:
        # 按时间戳排序，删除最旧的缓存
        sorted_keys = sorted(
            _chart_cache_metadata.keys(), key=lambda k: _chart_cache_metadata[k]["timestamp"]
        )
        keys_to_remove = sorted_keys[: len(_chart_cache_metadata) - _MAX_CACHE_SIZE]
        for key in keys_to_remove:
            _chart_data_cache.pop(key, None)
            _chart_cache_metadata.pop(key, None)


# ========== 数据库缓存函数 ==========
def save_chart_cache(cache_key: str, chart_data: Dict) -> bool:
    """
    保存图表缓存到数据库

    Args:
        cache_key: 缓存键
        chart_data: 图表数据

    Returns:
        bool: 保存是否成功
    """
    if not DB_CONNECTED:
        return False

    # 检查数据库连接和ChartCache是否可用
    if not DB_CONNECTED or ChartCache is None:
        return False

    try:
        existing_cache = ChartCache.query.filter_by(cache_key=cache_key).first()
        if existing_cache:
            # 更新现有缓存
            existing_cache.chart_data = json.dumps(chart_data)
            existing_cache.last_accessed = datetime.utcnow()
        else:
            # 创建新缓存
            new_cache = ChartCache(cache_key=cache_key, chart_data=json.dumps(chart_data))
            db.session.add(new_cache)
        db.session.commit()
        return True
    except (ValueError, IOError, TypeError) as e:  # 捕获特定的异常类型
        logger.error(f"保存图表缓存到数据库失败: {str(e)}")
        db.session.rollback()
        return False


def get_chart_cache(cache_key: str) -> Dict:
    """
    从数据库获取图表缓存

    Args:
        cache_key: 缓存键

    Returns:
        Dict: 图表数据，如果不存在返回None
    """
    if not DB_CONNECTED or ChartCache is None:
        return None

    try:
        cache = ChartCache.query.filter_by(cache_key=cache_key).first()
        if cache:
            # 更新最后访问时间
            cache.last_accessed = datetime.utcnow()
            db.session.commit()
            return json.loads(cache.chart_data)
        return None
    except (ValueError, IOError, TypeError) as e:  # 捕获特定的异常类型
        logger.error(f"从数据库获取图表缓存失败: {str(e)}")
        return None


def clean_expired_chart_cache(days: int = 7) -> int:
    """
    清理过期的图表缓存

    Args:
        days: 过期天数

    Returns:
        int: 清理的缓存数量
    """
    if not DB_CONNECTED or ChartCache is None:
        return 0

    try:
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        expired_caches = ChartCache.query.filter(ChartCache.last_accessed < cutoff_time).all()
        count = len(expired_caches)
        for cache in expired_caches:
            db.session.delete(cache)
        db.session.commit()
        return count
    except (ValueError, IOError, TypeError) as e:  # 捕获特定的异常类型
        logger.error(f"清理过期图表缓存失败: {str(e)}")
        db.session.rollback()
        return 0
