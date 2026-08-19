#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接测试引擎

从 database_connections.py 拆分出来的连接测试层，
负责实际数据库连接验证和 LRU 缓存管理。
"""

import logging
import sqlite3
import threading
from typing import Any, Dict, List

import pymysql

from app.models.db_connection_config import DatabaseConnection

logger = logging.getLogger(__name__)

try:
    import psycopg2
except ImportError:
    psycopg2 = None

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None

CACHE_MAX_SIZE = 100
DB_CONNECTION_TIMEOUT = 5


class ConnectionTester:
    """数据库连接测试类"""

    _connection_cache: Dict[str, Any] = {}
    _cache_order: List[str] = []

    @classmethod
    def _evict_cache_if_needed(cls):
        """缓存超过上限时逐出最早的一半条目"""
        if len(cls._connection_cache) > CACHE_MAX_SIZE:
            evict_count = max(1, len(cls._connection_cache) // 2)
            for _ in range(evict_count):
                if cls._cache_order:
                    old_key = cls._cache_order.pop(0)
                    conn = cls._connection_cache.pop(old_key, None)
                    if conn and hasattr(conn, "close"):
                        try:
                            conn.close()
                        except Exception:
                            pass
            logger.info(
                "连接缓存逐出 %d 条记录，当前 %d 条", evict_count, len(cls._connection_cache)
            )

    @classmethod
    def _cache_put(cls, key: str, conn: Any):
        """放入缓存并维护LRU"""
        cls._evict_cache_if_needed()
        cls._connection_cache[key] = conn
        if key in cls._cache_order:
            cls._cache_order.remove(key)
        cls._cache_order.append(key)

    @classmethod
    def clear_cache(cls):
        """清空测试缓存"""
        for conn in cls._connection_cache.values():
            if hasattr(conn, "close"):
                try:
                    conn.close()
                except Exception:
                    pass
        cls._connection_cache.clear()
        cls._cache_order.clear()

    @classmethod
    def test_connection(cls, connection: DatabaseConnection) -> Dict[str, Any]:
        """测试数据库连接"""
        try:
            cache_key = (
                f"{connection.type}_{connection.host}_{connection.port}_{connection.database}"
            )

            if cache_key in cls._connection_cache:
                cached_conn = cls._connection_cache[cache_key]
                try:
                    if cls._is_connection_valid(cached_conn, connection.type):
                        cls._cache_order.remove(cache_key)
                        cls._cache_order.append(cache_key)
                        return {
                            "success": True,
                            "message": f"{connection.type}连接成功！(使用缓存连接)",
                        }
                except Exception:
                    del cls._connection_cache[cache_key]
                    if cache_key in cls._cache_order:
                        cls._cache_order.remove(cache_key)

            if connection.type == "mysql":
                result = cls._test_mysql(connection)
            elif connection.type == "postgresql":
                result = cls._test_postgresql(connection)
            elif connection.type == "mongodb":
                result = cls._test_mongodb(connection)
            elif connection.type == "sqlite":
                result = cls._test_sqlite(connection)
            else:
                return {"success": False, "message": f"不支持的连接类型: {connection.type}"}

            if result["success"] and "connection" in result:
                cls._cache_put(cache_key, result["connection"])

            return result
        except Exception as e:
            return {"success": False, "message": f"连接测试异常: {str(e)}"}

    @staticmethod
    def _is_connection_valid(connection: Any, connection_type: str) -> bool:
        """检查连接是否有效"""
        try:
            if connection_type == "mysql":
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            elif connection_type == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            elif connection_type == "mongodb":
                connection.server_info()
            elif connection_type == "sqlite":
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception:
            return False

    @staticmethod
    def _test_mysql(connection: DatabaseConnection) -> Dict[str, Any]:
        """测试MySQL连接"""
        try:
            conn = pymysql.connect(
                host=connection.host,
                port=connection.port or 3306,
                user=connection.username,
                password=connection.password,
                db=connection.database,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5,
                read_timeout=10,
                write_timeout=10,
            )
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {"success": True, "message": "MySQL连接成功！", "connection": conn}
        except ImportError:
            return {
                "success": False,
                "message": "缺少MySQL驱动，请安装pymysql: pip install pymysql",
            }
        except Exception as e:
            return {"success": False, "message": f"MySQL连接失败: {str(e)}"}

    @staticmethod
    def _test_postgresql(connection: DatabaseConnection) -> Dict[str, Any]:
        """测试PostgreSQL连接"""
        try:
            conn = psycopg2.connect(
                host=connection.host,
                port=connection.port or 5432,
                user=connection.username,
                password=connection.password,
                dbname=connection.database,
                connect_timeout=5,
            )
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {"success": True, "message": "PostgreSQL连接成功！", "connection": conn}
        except ImportError:
            return {
                "success": False,
                "message": "缺少PostgreSQL驱动，请安装psycopg2: pip install psycopg2-binary",
            }
        except AttributeError:
            return {
                "success": False,
                "message": "PostgreSQL驱动不可用，请重新安装: pip install psycopg2-binary",
            }
        except Exception as e:
            return {"success": False, "message": f"PostgreSQL连接失败: {str(e)}"}

    @staticmethod
    def _test_mongodb(connection: DatabaseConnection) -> Dict[str, Any]:
        """测试MongoDB连接"""
        try:
            host = connection.host or "localhost"
            port = connection.port or 27017
            username = connection.username
            password = connection.password
            database = connection.database

            if MongoClient is None:
                return {
                    "success": False,
                    "message": "缺少MongoDB驱动，请安装pymongo: pip install pymongo",
                }

            if username and password:
                client = MongoClient(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    authSource=database,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                )
            else:
                client = MongoClient(
                    host=host, port=port, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000
                )
            client.server_info()
            return {"success": True, "message": "MongoDB连接成功！", "connection": client}
        except Exception as e:
            return {"success": False, "message": f"MongoDB连接失败: {str(e)}"}

    @staticmethod
    def _test_sqlite(connection: DatabaseConnection) -> Dict[str, Any]:
        """测试SQLite连接"""
        try:
            db_path = connection.database
            if not db_path:
                return {"success": False, "message": "请指定SQLite数据库文件路径"}
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
            cursor.execute("DROP TABLE IF EXISTS test")
            conn.commit()
            return {"success": True, "message": "SQLite连接成功！", "connection": conn}
        except Exception as e:
            return {"success": False, "message": f"SQLite连接失败: {str(e)}"}


def test_connection_with_timeout(
    connection: DatabaseConnection, timeout: int = DB_CONNECTION_TIMEOUT
) -> Dict[str, Any]:
    """跨平台带超时的数据库连接测试（供 settings_bp 和 database_bp 共用）"""
    result = {"success": False, "message": "连接测试超时，请检查网络或数据库配置"}
    result_holder = {"done": False, "result": result}

    def _do_test():
        try:
            r = connection_tester.test_connection(connection)
            result_holder["result"] = r
        except Exception as e:
            logger.error("数据库连接测试异常: %s", str(e))
            result_holder["result"] = {"success": False, "message": f"连接测试异常: {str(e)}"}
        result_holder["done"] = True

    t = threading.Thread(target=_do_test, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if not result_holder["done"]:
        logger.warning(
            "数据库连接测试超时 (%ds): %s@%s:%s",
            timeout,
            connection.type,
            connection.host,
            connection.port,
        )
        return {"success": False, "message": f"连接测试超时（{timeout}秒），请检查网络或数据库配置"}

    return result_holder["result"]


connection_tester = ConnectionTester()
