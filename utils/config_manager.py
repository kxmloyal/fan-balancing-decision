# -*- coding: utf-8 -*-
"""
配置管理工具类：用于管理数据库连接参数的配置
"""

import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

class ConfigManager:
    """配置管理类"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "db_config.json")
        self.key_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "secret.key")
        self.secret_key = self._load_or_generate_key()
        self.cipher_suite = Fernet(self.secret_key)
        
        # 确保配置目录存在
        config_dir = os.path.dirname(self.config_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
    
    def _load_or_generate_key(self):
        """加载或生成加密密钥"""
        # 确保配置目录存在
        config_dir = os.path.dirname(self.key_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                return f.read()
        else:
            # 生成新密钥
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            # 设置密钥文件权限（仅当前用户可读写）
            try:
                os.chmod(self.key_file, 0o600)
            except Exception:
                # 在某些系统上可能无法设置权限，忽略错误
                pass
            return key
    
    def encrypt(self, data):
        """加密数据"""
        if not data:
            return data
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, data):
        """解密数据"""
        if not data:
            return data
        try:
            return self.cipher_suite.decrypt(data.encode()).decode()
        except Exception:
            return data
    
    def get_db_config(self):
        """获取数据库连接配置"""
        # 首先尝试从环境变量获取
        env_config = self._get_config_from_env()
        if env_config:
            return env_config
        
        # 然后尝试从配置文件获取
        file_config = self._get_config_from_file()
        if file_config:
            return file_config
        
        # 返回默认配置
        return {
            "db_type": "sqlite",
            "host": "",
            "port": "",
            "database": "",
            "username": "",
            "password": ""
        }
    
    def _get_config_from_env(self):
        """从环境变量获取配置"""
        db_type = os.environ.get("DB_TYPE")
        if not db_type:
            return None
        
        return {
            "db_type": db_type,
            "host": os.environ.get("DB_HOST", ""),
            "port": os.environ.get("DB_PORT", ""),
            "database": os.environ.get("DB_NAME", ""),
            "username": os.environ.get("DB_USER", ""),
            "password": self.decrypt(os.environ.get("DB_PASSWORD", ""))
        }
    
    def _get_config_from_file(self):
        """从配置文件获取配置"""
        if not os.path.exists(self.config_file):
            return None
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 解密密码
            if "password" in config:
                config["password"] = self.decrypt(config["password"])
            
            return config
        except Exception:
            return None
    
    def save_db_config(self, config, save_method="file"):
        """保存数据库连接配置"""
        try:
            # 加密密码
            config_to_save = config.copy()
            if "password" in config_to_save:
                config_to_save["password"] = self.encrypt(config_to_save["password"])
            
            if save_method == "file":
                # 保存到文件
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(config_to_save, f, ensure_ascii=False, indent=2)
                # 设置配置文件权限（仅当前用户可读写）
                os.chmod(self.config_file, 0o600)
            elif save_method == "env":
                # 保存到环境变量
                os.environ["DB_TYPE"] = config_to_save["db_type"]
                os.environ["DB_HOST"] = config_to_save.get("host", "")
                os.environ["DB_PORT"] = config_to_save.get("port", "")
                os.environ["DB_NAME"] = config_to_save.get("database", "")
                os.environ["DB_USER"] = config_to_save.get("username", "")
                os.environ["DB_PASSWORD"] = config_to_save.get("password", "")
            
            return True
        except Exception:
            return False
    
    def reset_db_config(self):
        """重置数据库连接配置"""
        try:
            # 删除配置文件
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            
            # 清除环境变量
            env_vars = ["DB_TYPE", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
            for var in env_vars:
                if var in os.environ:
                    del os.environ[var]
            
            return True
        except Exception:
            return False
    
    def get_sqlalchemy_uri(self):
        """获取SQLAlchemy连接URI"""
        config = self.get_db_config()
        db_type = config.get("db_type", "sqlite")
        
        if db_type == "sqlite":
            base_dir = os.path.dirname(os.path.dirname(__file__))
            return f"sqlite:///{os.path.join(base_dir, 'data.db')}"
        elif db_type == "mysql":
            return f"mysql+pymysql://{config.get('username')}:{config.get('password')}@{config.get('host')}:{config.get('port')}/{config.get('database')}"
        elif db_type == "postgresql":
            return f"postgresql://{config.get('username')}:{config.get('password')}@{config.get('host')}:{config.get('port')}/{config.get('database')}"
        else:
            base_dir = os.path.dirname(os.path.dirname(__file__))
            return f"sqlite:///{os.path.join(base_dir, 'data.db')}"


# 创建全局配置管理器实例
config_manager = ConfigManager()
