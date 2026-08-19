#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""配置管理器"""

import json
import os
import sqlite3
from urllib.parse import quote_plus


class ConfigManager:
    """配置管理器类"""

    def __init__(self):
        """初始化配置管理器"""
        self.config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "db_config.json"
        )
        self.config = self._load_config()

    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # 返回默认配置
            return {
                "database": {
                    "type": "sqlite",
                    "name": "data.db",
                    "host": "localhost",
                    "port": 3306,
                    "user": "root",
                    "password": "",
                }
            }

    def get_sqlalchemy_uri(self):
        """获取SQLAlchemy数据库URI"""
        db_config = self.config.get("database", {})
        db_type = db_config.get("type", "sqlite")

        if db_type == "sqlite":
            db_name = db_config.get("name", "data.db")
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), db_name
            )
            return f"sqlite:///{db_path}"
        elif db_type == "mysql":
            host = db_config.get("host", "localhost")
            port = db_config.get("port", 3306)
            user = db_config.get("user", "root")
            password = db_config.get("password", "")
            db_name = db_config.get("name", "data")
            encoded_user = quote_plus(user) if user else ""
            encoded_pass = quote_plus(password) if password else ""
            return f"mysql+pymysql://{encoded_user}:{encoded_pass}@{host}:{port}/{db_name}?charset=utf8mb4"
        elif db_type == "postgresql":
            host = db_config.get("host", "localhost")
            port = db_config.get("port", 5432)
            user = db_config.get("user", "postgres")
            password = db_config.get("password", "")
            db_name = db_config.get("name", "data")
            encoded_user = quote_plus(user) if user else ""
            encoded_pass = quote_plus(password) if password else ""
            return f"postgresql://{encoded_user}:{encoded_pass}@{host}:{port}/{db_name}"
        else:
            # 默认使用SQLite
            db_name = db_config.get("name", "data.db")
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), db_name
            )
            return f"sqlite:///{db_path}"

    def get_all_config(self):
        """获取所有配置"""
        return self.config

    def set_config(self, key, value):
        """设置配置项"""
        # 支持嵌套配置，如 database.host
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save_config(self):
        """保存配置到文件（原子写入：先写临时文件，再原子替换）"""
        try:
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            temp_file = self.config_file + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_file, self.config_file)
            return True
        except Exception:
            return False

    def get_db_config(self):
        """获取数据库配置，兼容扁平结构和嵌套结构"""
        db_section = self.config.get("database", None)
        if isinstance(db_section, dict):
            db_config = db_section
            return {
                "db_type": db_config.get("type", "sqlite"),
                "host": db_config.get("host", "localhost"),
                "port": db_config.get("port", 3306),
                "database": db_config.get("name", "data.db"),
                "username": db_config.get("user", "root"),
                "password": db_config.get("password", ""),
            }
        else:
            return {
                "db_type": self.config.get("db_type", "sqlite"),
                "host": self.config.get("host", "localhost"),
                "port": self.config.get("port", 3306),
                "database": self.config.get("database", "data.db"),
                "username": self.config.get("username", "root"),
                "password": self.config.get("password", ""),
            }

    def save_db_config(self, config_dict, save_method="file"):
        """保存数据库配置（密码加密存储）"""
        from app.utils.crypto_utils import encrypt_password

        raw_password = config_dict.get("password", "")
        self.config["database"] = {
            "type": config_dict.get("db_type", "sqlite"),
            "name": config_dict.get("database", "data.db"),
            "host": config_dict.get("host", "localhost"),
            "port": config_dict.get("port", 3306),
            "user": config_dict.get("username", "root"),
            "password": encrypt_password(raw_password) if raw_password else "",
        }
        if save_method == "file":
            return self.save_config()
        return True

    def get_face_weights(self):
        """获取端面权重配置（P1/P2/ST），默认经验值"""
        default_weights = {"P1": 0.4, "P2": 0.4, "ST": 0.2}
        return self.config.get("face_weights", default_weights)

    def save_face_weights(self, weights_dict):
        """保存端面权重配置"""
        self.config["face_weights"] = {
            "P1": float(weights_dict.get("P1", 0.4)),
            "P2": float(weights_dict.get("P2", 0.4)),
            "ST": float(weights_dict.get("ST", 0.2)),
        }
        return self.save_config()

    def reset_face_weights(self):
        """重置端面权重为默认经验值"""
        self.config["face_weights"] = {"P1": 0.4, "P2": 0.4, "ST": 0.2}
        return self.save_config()

    def reset_db_config(self):
        """重置数据库配置为默认值"""
        return self.reset_config()

    def reset_config(self):
        """重置配置为默认值"""
        self.config = {
            "database": {
                "type": "sqlite",
                "name": "data.db",
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "",
            }
        }
        return self.save_config()

    def test_database_connection(self, db_config):
        """测试数据库连接"""
        try:
            db_type = db_config.get("db_type", "sqlite")

            if db_type == "sqlite":
                # 测试SQLite连接
                db_name = db_config.get("database", "data.db")
                db_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), db_name
                )
                # 确保目录存在
                db_dir = os.path.dirname(db_path)
                if not os.path.exists(db_dir):
                    os.makedirs(db_dir)
                # 测试连接
                conn = sqlite3.connect(db_path)
                conn.close()
                return {"success": True, "message": "SQLite连接成功！"}
            elif db_type == "mysql":
                # 测试MySQL连接
                try:
                    import pymysql

                    host = db_config.get("host", "localhost")
                    port = int(db_config.get("port", 3306))
                    user = db_config.get("username", "root")
                    password = db_config.get("password", "")
                    db = db_config.get("database", "data")

                    conn = pymysql.connect(
                        host=host, port=port, user=user, password=password, db=db, charset="utf8mb4"
                    )
                    conn.close()
                    return {"success": True, "message": "MySQL连接成功！"}
                except ImportError:
                    return {
                        "success": False,
                        "message": "缺少pymysql模块，请安装：pip install pymysql",
                    }
                except Exception as e:
                    return {"success": False, "message": f"MySQL连接失败：{str(e)}"}
            elif db_type == "postgresql":
                # 测试PostgreSQL连接
                try:
                    import psycopg2

                    host = db_config.get("host", "localhost")
                    port = int(db_config.get("port", 5432))
                    user = db_config.get("username", "postgres")
                    password = db_config.get("password", "")
                    db = db_config.get("database", "data")

                    conn = psycopg2.connect(
                        host=host, port=port, user=user, password=password, dbname=db
                    )
                    conn.close()
                    return {"success": True, "message": "PostgreSQL连接成功！"}
                except ImportError:
                    return {
                        "success": False,
                        "message": "缺少psycopg2模块，请安装：pip install psycopg2",
                    }
                except Exception as e:
                    return {"success": False, "message": f"PostgreSQL连接失败：{str(e)}"}
            else:
                return {"success": False, "message": f"不支持的数据库类型：{db_type}"}
        except Exception as e:
            return {"success": False, "message": f"测试连接失败：{str(e)}"}


# 创建全局配置管理器实例
config_manager = ConfigManager()
