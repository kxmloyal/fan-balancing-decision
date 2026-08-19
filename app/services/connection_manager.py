#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接配置管理器

从 database_connections.py 拆分出来的 CRUD 管理层，
负责连接配置的 JSON 文件持久化读写。
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Optional

from app.models.db_connection_config import DatabaseConnection

logger = logging.getLogger(__name__)

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "connection_configs.json",
)

os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)


class ConnectionManager:
    """数据库连接配置管理类"""

    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = config_file
        self.connections: List[DatabaseConnection] = self._load_configs()

    def _load_configs(self) -> List[DatabaseConnection]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return [DatabaseConnection.from_dict(conn) for conn in data]
        except (ValueError, IOError, TypeError) as e:
            logger.error("加载配置文件失败: %s", str(e))
        return []

    def _save_configs(self):
        """保存配置文件（原子写入，密码加密存储）"""
        try:
            temp_file = self.config_file + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                data = [conn.to_dict(include_password=True) for conn in self.connections]
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_file, self.config_file)
        except (ValueError, IOError, TypeError) as e:
            logger.error("保存配置文件失败: %s", str(e))

    def get_next_id(self) -> int:
        """获取下一个ID"""
        if not self.connections:
            return 1
        return max(conn.id for conn in self.connections) + 1

    def add_connection(self, connection: DatabaseConnection) -> DatabaseConnection:
        """添加连接配置"""
        connection.id = self.get_next_id()
        self.connections.append(connection)
        self._save_configs()
        return connection

    def update_connection(self, connection: DatabaseConnection) -> Optional[DatabaseConnection]:
        """更新连接配置"""
        for i, conn in enumerate(self.connections):
            if conn.id == connection.id:
                connection.updated_at = datetime.now().isoformat()
                self.connections[i] = connection
                self._save_configs()
                return connection
        return None

    def delete_connection(self, connection_id: int) -> bool:
        """删除连接配置"""
        for i, conn in enumerate(self.connections):
            if conn.id == connection_id:
                self.connections.pop(i)
                self._save_configs()
                return True
        return False

    def get_connection(self, connection_id: int) -> Optional[DatabaseConnection]:
        """获取连接配置"""
        for conn in self.connections:
            if conn.id == connection_id:
                return conn
        return None

    def get_all_connections(self) -> List[DatabaseConnection]:
        """获取所有连接配置"""
        return self.connections

    def search_connections(self, keyword: str) -> List[DatabaseConnection]:
        """搜索连接配置"""
        keyword = keyword.lower()
        return [
            conn
            for conn in self.connections
            if keyword in conn.name.lower() or keyword in conn.type.lower()
        ]


connection_manager = ConnectionManager()
