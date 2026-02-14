#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图表缓存模块
用于缓存已生成的图表，避免重复生成相同的图表，提高系统性能
"""

import hashlib
import json
import logging
import os
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ChartCache:
    """图表缓存类

    实现图表的缓存管理，包括：
    1. 生成图表缓存键
    2. 存储图表缓存
    3. 获取图表缓存
    4. 清理过期缓存
    5. 缓存统计和监控
    6. 缓存预热和预加载
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        max_age: int = 3600,
        max_size_mb: int = 1024,
    ):
        """初始化图表缓存

        Args:
            cache_dir: 缓存目录路径，默认为当前目录下的.chart_cache目录
            max_age: 缓存最大生存时间（秒），默认为1小时
            max_size_mb: 缓存最大大小（MB），默认为1GB
        """
        self.cache_dir: str = cache_dir or os.path.join(os.getcwd(), ".chart_cache")
        self.max_age: int = max_age
        self.max_size_mb: int = max_size_mb

        # 确保缓存目录存在
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # 缓存统计信息
        self.stats: Dict[str, int] = {
            "hits": 0,  # 缓存命中次数
            "misses": 0,  # 缓存未命中次数
            "generated": 0,  # 缓存生成次数
            "cleaned": 0,  # 缓存清理次数
            "expired": 0,  # 过期缓存数
            "total_size": 0,  # 当前缓存总大小（字节）
            "total_files": 0,  # 当前缓存文件数
        }

        # 线程锁，确保统计信息的线程安全
        self._stats_lock = threading.Lock()

        # 缓存预加载队列
        self._preload_queue = []

        # 初始化时清理过期缓存和超过大小限制的缓存
        self.cleanup()
        self._update_cache_stats()

    def _update_cache_stats(self) -> None:
        """更新缓存统计信息"""
        if not os.path.exists(self.cache_dir):
            return

        total_size = 0
        total_files = 0

        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
                total_files += 1

        with self._stats_lock:
            self.stats["total_size"] = total_size
            self.stats["total_files"] = total_files

    def generate_cache_key(
        self, data_hash: str, surface_type: str, chart_types: Optional[List[str]]
    ) -> str:
        """生成图表缓存键

        Args:
            data_hash: 数据的哈希值
            surface_type: 表面类型（p1, p2, st）
            chart_types: 图表类型列表

        Returns:
            str: 唯一的缓存键
        """
        # 将图表类型列表排序，确保相同类型的不同顺序生成相同的键
        sorted_chart_types = sorted(chart_types) if chart_types else []

        # 生成缓存键，增加版本号以支持缓存格式升级
        version = "v1"
        cache_key = (
            f"{version}_{data_hash}_{surface_type}_{'_'.join(sorted_chart_types)}"
        )

        # 使用SHA256生成固定长度的哈希值
        return hashlib.sha256(cache_key.encode()).hexdigest()

    def generate_data_hash(self, data: Any) -> str:
        """生成数据的哈希值
        优化：使用更高效的方式处理大数据量

        Args:
            data: 要生成哈希值的数据

        Returns:
            str: 数据的哈希值
        """
        # 优化：对于大型数据，只取关键部分生成哈希值，减少计算时间
        if isinstance(data, list) and len(data) > 1000:
            # 对于大型列表，只取前100项、中间100项和后100项生成哈希值
            sample_data = (
                data[:100]
                + data[len(data) // 2 - 50 : len(data) // 2 + 50]
                + data[-100:]
            )
            data_str = json.dumps(
                sample_data, sort_keys=True, default=str, ensure_ascii=False
            )
        else:
            # 对于小型数据，使用完整数据生成哈希值
            data_str = json.dumps(data, sort_keys=True, default=str, ensure_ascii=False)

        return hashlib.sha256(data_str.encode()).hexdigest()

    def get_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取图表缓存
        优化：增加缓存命中统计

        Args:
            cache_key: 缓存键

        Returns:
            Optional[Dict[str, Any]]: 缓存的图表数据，如果不存在或已过期则返回None
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        if not os.path.exists(cache_file):
            with self._stats_lock:
                self.stats["misses"] += 1
            return None

        # 检查缓存是否过期
        mtime = os.path.getmtime(cache_file)
        if datetime.now().timestamp() - mtime > self.max_age:
            # 删除过期缓存
            try:
                os.remove(cache_file)
                with self._stats_lock:
                    self.stats["misses"] += 1
                    self.stats["expired"] += 1
            except OSError:
                # 如果文件正在使用或无法删除，忽略它
                pass
            return None

        # 读取缓存数据
        with open(cache_file, "r", encoding="utf-8") as f:
            try:
                result = json.load(f)
                with self._stats_lock:
                    self.stats["hits"] += 1
                return result
            except json.JSONDecodeError:
                # 如果缓存文件损坏，删除它
                try:
                    os.remove(cache_file)
                    with self._stats_lock:
                        self.stats["misses"] += 1
                except OSError:
                    # 如果文件正在使用或无法删除，忽略它
                    pass
                return None

    def set_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """设置图表缓存
        优化：增加缓存生成统计，自动清理超过大小限制的缓存

        Args:
            cache_key: 缓存键
            data: 要缓存的数据
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        # 写入缓存数据
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        with self._stats_lock:
            self.stats["generated"] += 1

        # 更新缓存统计信息
        self._update_cache_stats()

        # 检查是否超过大小限制，如果超过则清理最旧的缓存
        current_size_mb = self.stats["total_size"] / (1024 * 1024)
        if current_size_mb > self.max_size_mb:
            logger.info(
                f"缓存大小超过限制（{current_size_mb:.2f}MB > {self.max_size_mb}MB），开始清理最旧的缓存"
            )
            self._cleanup_oldest()

    def _cleanup_oldest(self, percentage: float = 0.1) -> None:
        """清理最旧的缓存文件

        Args:
            percentage: 要清理的缓存文件百分比，默认为10%
        """
        if not os.path.exists(self.cache_dir):
            return

        # 获取所有缓存文件及其修改时间
        cache_files = []
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(file_path):
                cache_files.append((file_path, os.path.getmtime(file_path)))

        # 按修改时间排序（最旧的在前）
        cache_files.sort(key=lambda x: x[1])

        # 计算要清理的文件数量
        files_to_clean = int(len(cache_files) * percentage)
        if files_to_clean < 1:
            files_to_clean = 1

        # 清理最旧的缓存文件
        for i in range(files_to_clean):
            try:
                os.remove(cache_files[i][0])
                with self._stats_lock:
                    self.stats["cleaned"] += 1
            except OSError:
                # 如果文件正在使用或无法删除，跳过
                pass

        # 更新缓存统计信息
        self._update_cache_stats()

    def cleanup(self) -> None:
        """清理过期缓存和损坏的缓存文件"""
        if not os.path.exists(self.cache_dir):
            return

        now = datetime.now().timestamp()
        cleaned_count = 0

        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(file_path):
                # 检查缓存是否过期
                mtime = os.path.getmtime(file_path)
                if now - mtime > self.max_age:
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                    except OSError:
                        # 如果文件正在使用或无法删除，忽略它
                        pass
                # 检查缓存文件是否损坏
                else:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            json.load(f)
                    except (json.JSONDecodeError, OSError):
                        # 如果文件损坏，删除它
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                        except OSError:
                            # 如果文件正在使用或无法删除，忽略它
                            pass

        with self._stats_lock:
            self.stats["cleaned"] += cleaned_count

        # 更新缓存统计信息
        self._update_cache_stats()

        logger.info(f"清理了 {cleaned_count} 个过期或损坏的缓存文件")

    def clear(self) -> None:
        """清空所有缓存"""
        if not os.path.exists(self.cache_dir):
            return

        cleared_count = 0
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    cleared_count += 1
                except OSError:
                    # 如果文件正在使用或无法删除，忽略它
                    pass

        with self._stats_lock:
            self.stats["cleaned"] += cleared_count
            self.stats["total_size"] = 0
            self.stats["total_files"] = 0

        logger.info(f"清空了 {cleared_count} 个缓存文件")

    def preload_cache(
        self, data: Any, surface_type: str, chart_types: List[str]
    ) -> None:
        """预加载缓存

        Args:
            data: 要预加载的数据
            surface_type: 表面类型（p1, p2, st）
            chart_types: 图表类型列表
        """
        # 生成数据哈希和缓存键
        data_hash = self.generate_data_hash(data)
        cache_key = self.generate_cache_key(data_hash, surface_type, chart_types)

        # 添加到预加载队列
        self._preload_queue.append((cache_key, data, surface_type, chart_types))

        logger.info(f"添加缓存到预加载队列：{cache_key}")

    def get_stats(self) -> Dict[str, int]:
        """获取缓存统计信息

        Returns:
            Dict[str, int]: 缓存统计信息
        """
        with self._stats_lock:
            return self.stats.copy()

    def get_cache_usage(self) -> Dict[str, Any]:
        """获取缓存使用情况

        Returns:
            Dict[str, Any]: 缓存使用情况
        """
        self._update_cache_stats()

        return {
            "current_size_mb": self.stats["total_size"] / (1024 * 1024),
            "max_size_mb": self.max_size_mb,
            "usage_percentage": (
                (self.stats["total_size"] / (self.max_size_mb * 1024 * 1024)) * 100
                if self.max_size_mb > 0
                else 0
            ),
            "total_files": self.stats["total_files"],
            "hit_rate": (
                (self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])) * 100
                if (self.stats["hits"] + self.stats["misses"]) > 0
                else 0
            ),
            **self.get_stats(),
        }

    def get_cache_dir(self) -> str:
        """获取缓存目录路径

        Returns:
            str: 缓存目录路径
        """
        return self.cache_dir


# 创建全局图表缓存实例
chart_cache = ChartCache(max_age=3600, max_size_mb=1024)
