#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""图表资源管理器"""

import hashlib
import json
import os
import threading
from datetime import datetime


class ChartResourceManager:
    """图表资源管理器类"""

    def __init__(self):
        """初始化图表资源管理器"""
        self.chart_resources = {}
        self.generating_charts = set()
        self.lock = threading.Lock()

    def generate_data_hash(self, data):
        """生成数据哈希值"""
        try:
            data_str = json.dumps(data, sort_keys=True)
            return hashlib.md5(data_str.encode()).hexdigest()
        except Exception:
            return str(datetime.now().timestamp())

    def generate_chart_id(self, data_hash, surface_type, chart_type, scope=None):
        """生成图表唯一标识符（scope 为输出目录/型号等维度，短哈希避免跨目录缓存复用失效路径）"""
        scope_part = ""
        if scope:
            scope_part = "_" + hashlib.md5(str(scope).encode()).hexdigest()[:8]
        return f"chart_{data_hash}{scope_part}_{surface_type}_{chart_type}"

    def is_chart_generated(self, chart_id):
        """检查图表是否已生成（缓存路径失效时视为未生成，触发重新生成）"""
        with self.lock:
            res = self.chart_resources.get(chart_id)
            if res is None:
                return False
            # 缓存记录的是首次生成的完整路径；文件已被清理或目录变化（如不同型号/输出目录）
            # 时按 basename 拼出的当前目录找不到该文件，此时应视为未生成并重新生成
            if not os.path.exists(res.get("png_path", "")):
                return False
            return True

    def get_chart_resource(self, chart_id):
        """获取图表资源信息"""
        with self.lock:
            return self.chart_resources.get(chart_id)

    def mark_chart_generating(self, chart_id, chart_type, surface_name, data_hash):
        """标记图表正在生成"""
        with self.lock:
            self.generating_charts.add(chart_id)

    def mark_chart_generated(self, chart_id, png_path):
        """标记图表生成完成"""
        with self.lock:
            if chart_id in self.generating_charts:
                self.generating_charts.remove(chart_id)

            # 生成HTML路径
            html_path = os.path.splitext(png_path)[0] + ".html"

            self.chart_resources[chart_id] = {
                "png_path": png_path,
                "html_path": html_path,
                "generated_at": datetime.now().isoformat(),
            }

    def clear_expired_resources(self, hours=24):
        """清理过期的图表资源"""
        with self.lock:
            expired = []
            cutoff_time = datetime.now().timestamp() - (hours * 3600)

            for chart_id, resource in self.chart_resources.items():
                generated_at = datetime.fromisoformat(resource["generated_at"]).timestamp()
                if generated_at < cutoff_time:
                    expired.append(chart_id)

            for chart_id in expired:
                # 尝试删除文件
                resource = self.chart_resources[chart_id]
                for path_key in ["png_path", "html_path"]:
                    if path_key in resource:
                        try:
                            if os.path.exists(resource[path_key]):
                                os.remove(resource[path_key])
                        except Exception:
                            pass

                del self.chart_resources[chart_id]

            return len(expired)

    def get_resource_stats(self):
        """获取资源统计信息"""
        with self.lock:
            return {
                "total_resources": len(self.chart_resources),
                "generating_charts": len(self.generating_charts),
                "resource_ids": list(self.chart_resources.keys()),
            }


# 创建全局图表资源管理器实例
chart_resource_manager = ChartResourceManager()
