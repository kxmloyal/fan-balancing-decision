#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接配置数据模型

从 database_connections.py 拆分出来的纯粹数据模型层，
不包含文件 I/O 或连接测试逻辑。
"""

from datetime import datetime
from typing import Any, Dict, Optional

try:
    from app.utils.crypto_utils import decrypt_password as _decrypt
    from app.utils.crypto_utils import encrypt_password as _encrypt
except ImportError:
    _encrypt = lambda p: p
    _decrypt = lambda p: p


class DatabaseConnection:
    """数据库连接配置数据模型"""

    def __init__(
        self,
        connection_id: int,
        name: str,
        connection_type: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        status: str = "inactive",
        is_primary: bool = False,
    ):
        self.id = connection_id
        self.name = name
        self.type = connection_type
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.status = status
        self.is_primary = is_primary
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self, include_password: bool = False) -> Dict[str, Any]:
        """转换为字典

        Args:
            include_password: 是否包含密码字段（API返回应设为False）
        """
        data = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "status": self.status,
            "is_primary": self.is_primary,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if include_password:
            data["password"] = _encrypt(self.password) if self.password else ""
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatabaseConnection":
        """从字典创建实例（自动解密存储的密码）"""
        password = data.get("password", "")
        if password:
            try:
                password = _decrypt(password)
            except Exception:
                pass
        return cls(
            connection_id=data.get("id"),
            name=data.get("name"),
            connection_type=data.get("type"),
            host=data.get("host"),
            port=data.get("port"),
            database=data.get("database"),
            username=data.get("username"),
            password=password,
            status=data.get("status", "inactive"),
            is_primary=data.get("is_primary", False),
        )
