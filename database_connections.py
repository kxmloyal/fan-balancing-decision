#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接配置管理模块
负责处理数据库连接配置的存储、管理和测试
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'connection_configs.json')

# 确保配置文件目录存在
os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

class DatabaseConnection:
    """数据库连接配置类"""
    
    def __init__(self, id: int, name: str, type: str, host: Optional[str] = None, 
                 port: Optional[int] = None, database: Optional[str] = None, 
                 username: Optional[str] = None, password: Optional[str] = None, 
                 status: str = 'inactive'):
        self.id = id
        self.name = name
        self.type = type
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.status = status
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'username': self.username,
            'password': self.password,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseConnection':
        """从字典创建实例"""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            type=data.get('type'),
            host=data.get('host'),
            port=data.get('port'),
            database=data.get('database'),
            username=data.get('username'),
            password=data.get('password'),
            status=data.get('status', 'inactive')
        )

class ConnectionManager:
    """
    数据库连接配置管理类
    """
    
    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = config_file
        self.connections: List[DatabaseConnection] = self._load_configs()
        self._connection_cache: Dict[int, Any] = {}  # 缓存数据库连接对象
    
    def _load_configs(self) -> List[DatabaseConnection]:
        """
        加载配置文件
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [DatabaseConnection.from_dict(conn) for conn in data]
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
        return []
    
    def _save_configs(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                data = [conn.to_dict() for conn in self.connections]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")
    
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
        """
        搜索连接配置
        """
        keyword = keyword.lower()
        return [conn for conn in self.connections if 
                keyword in conn.name.lower() or keyword in conn.type.lower()]
    
    def get_cached_connection(self, connection_id: int) -> Optional[Any]:
        """
        获取缓存的数据库连接
        
        Args:
            connection_id: 连接配置ID
            
        Returns:
            数据库连接对象，如果不存在返回None
        """
        return self._connection_cache.get(connection_id)
    
    def set_cached_connection(self, connection_id: int, connection: Any) -> None:
        """
        设置缓存的数据库连接
        
        Args:
            connection_id: 连接配置ID
            connection: 数据库连接对象
        """
        self._connection_cache[connection_id] = connection
    
    def clear_cached_connection(self, connection_id: int) -> None:
        """
        清除缓存的数据库连接
        
        Args:
            connection_id: 连接配置ID
        """
        if connection_id in self._connection_cache:
            try:
                # 尝试关闭连接
                conn = self._connection_cache[connection_id]
                if hasattr(conn, 'close'):
                    conn.close()
            except Exception:
                pass
            del self._connection_cache[connection_id]
    
    def clear_all_cached_connections(self) -> None:
        """
        清除所有缓存的数据库连接
        """
        for connection_id in list(self._connection_cache.keys()):
            self.clear_cached_connection(connection_id)

class ConnectionTester:
    """
    数据库连接测试类
    """
    
    # 连接缓存，减少重复连接的开销
    _connection_cache = {}
    
    @classmethod
    def test_connection(cls, connection: DatabaseConnection) -> Dict[str, Any]:
        """
        测试数据库连接
        """
        try:
            # 生成缓存键
            cache_key = f"{connection.type}_{connection.host}_{connection.port}_{connection.database}"
            
            # 检查缓存中是否有可用连接
            if cache_key in cls._connection_cache:
                cached_conn = cls._connection_cache[cache_key]
                try:
                    # 测试缓存连接是否有效
                    if cls._is_connection_valid(cached_conn, connection.type):
                        return {
                            'success': True,
                            'message': f'{connection.type}连接成功！(使用缓存连接)'
                        }
                except Exception:
                    # 缓存连接无效，删除它
                    del cls._connection_cache[cache_key]
            
            # 缓存中没有有效连接，创建新连接
            if connection.type == 'mysql':
                result = cls._test_mysql(connection)
            elif connection.type == 'postgresql':
                result = cls._test_postgresql(connection)
            elif connection.type == 'mongodb':
                result = cls._test_mongodb(connection)
            elif connection.type == 'sqlite':
                result = cls._test_sqlite(connection)
            else:
                return {
                    'success': False,
                    'message': f'不支持的连接类型: {connection.type}'
                }
            
            # 如果连接成功，缓存连接对象
            if result['success'] and 'connection' in result:
                cls._connection_cache[cache_key] = result['connection']
            
            return result
        except Exception as e:
            return {
                'success': False,
                'message': f'连接测试失败: {str(e)}'
            }
    
    @staticmethod
    def _is_connection_valid(connection: Any, connection_type: str) -> bool:
        """
        检查连接是否有效
        
        Args:
            connection: 数据库连接对象
            connection_type: 连接类型
            
        Returns:
            bool: 连接是否有效
        """
        try:
            if connection_type == 'mysql':
                # 测试MySQL连接
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')
                    cursor.fetchone()
            elif connection_type == 'postgresql':
                # 测试PostgreSQL连接
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')
                    cursor.fetchone()
            elif connection_type == 'mongodb':
                # 测试MongoDB连接
                connection.server_info()
            elif connection_type == 'sqlite':
                # 测试SQLite连接
                cursor = connection.cursor()
                cursor.execute('SELECT 1')
                cursor.fetchone()
            return True
        except Exception:
            return False
    
    @staticmethod
    def _test_mysql(connection: DatabaseConnection) -> Dict[str, Any]:
        """
        测试MySQL连接
        """
        try:
            import pymysql
            
            # 构建连接参数
            conn = pymysql.connect(
                host=connection.host,
                port=connection.port or 3306,
                user=connection.username,
                password=connection.password,
                db=connection.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            # 测试连接
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
            
            return {
                'success': True,
                'message': 'MySQL连接成功！',
                'connection': conn
            }
        except ImportError:
            return {
                'success': False,
                'message': '缺少MySQL驱动，请安装pymysql: pip install pymysql'
            }
    
    @staticmethod
    def _test_postgresql(connection: DatabaseConnection) -> Dict[str, Any]:
        """
        测试PostgreSQL连接
        """
        try:
            import psycopg2
            
            # 构建连接参数
            conn = psycopg2.connect(
                host=connection.host,
                port=connection.port or 5432,
                user=connection.username,
                password=connection.password,
                dbname=connection.database
            )
            
            # 测试连接
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
            
            return {
                'success': True,
                'message': 'PostgreSQL连接成功！',
                'connection': conn
            }
        except ImportError:
            return {
                'success': False,
                'message': '缺少PostgreSQL驱动，请安装psycopg2: pip install psycopg2-binary'
            }
    
    @staticmethod
    def _test_mongodb(connection: DatabaseConnection) -> Dict[str, Any]:
        """
        测试MongoDB连接
        """
        try:
            from pymongo import MongoClient
            
            # 构建连接字符串
            host = connection.host or 'localhost'
            port = connection.port or 27017
            username = connection.username
            password = connection.password
            database = connection.database
            
            if username and password:
                conn_str = f'mongodb://{username}:{password}@{host}:{port}/{database}'
            else:
                conn_str = f'mongodb://{host}:{port}/{database}'
            
            # 测试连接
            client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
            client.server_info()  # 这将触发连接
            
            return {
                'success': True,
                'message': 'MongoDB连接成功！',
                'connection': client
            }
        except ImportError:
            return {
                'success': False,
                'message': '缺少MongoDB驱动，请安装pymongo: pip install pymongo'
            }
    
    @staticmethod
    def _test_sqlite(connection: DatabaseConnection) -> Dict[str, Any]:
        """
        测试SQLite连接
        """
        try:
            # 测试SQLite文件路径
            db_path = connection.database
            if not db_path:
                return {
                    'success': False,
                    'message': '请指定SQLite数据库文件路径'
                }
            
            # 测试连接
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER)')
            cursor.execute('DROP TABLE IF EXISTS test')
            conn.commit()
            
            return {
                'success': True,
                'message': 'SQLite连接成功！',
                'connection': conn
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'SQLite连接失败: {str(e)}'
            }

# 全局连接管理器实例
connection_manager = ConnectionManager()
connection_tester = ConnectionTester()
