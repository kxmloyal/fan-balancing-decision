import os
import hashlib
import json
import time
from functools import wraps

class ChartCache:
    def __init__(self, cache_dir='chart_cache', expiry_time=1800):
        """
        初始化图表缓存
        
        Args:
            cache_dir (str): 缓存目录
            expiry_time (int): 缓存过期时间（秒）- 设置为30分钟以节省空间
        """
        self.cache_dir = cache_dir
        self.expiry_time = expiry_time
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        # 限制缓存文件数量
        self._cleanup_old_cache()
    
    def _get_cache_key(self, func_name, *args, **kwargs):
        """
        生成缓存键
        
        Args:
            func_name (str): 函数名
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            str: 缓存键
        """
        # 创建参数的哈希值
        hash_input = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key):
        """
        获取缓存文件路径
        
        Args:
            cache_key (str): 缓存键
            
        Returns:
            str: 缓存文件路径
        """
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _cleanup_old_cache(self):
        """
        清理旧的缓存文件，防止占用过多磁盘空间
        """
        try:
            cache_files = os.listdir(self.cache_dir)
            current_time = time.time()
            
            # 删除过期的缓存文件
            for file_name in cache_files:
                if file_name.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, file_name)
                    if current_time - os.path.getmtime(file_path) > self.expiry_time:
                        os.remove(file_path)
            
            # 如果缓存文件过多，删除最旧的文件
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
            if len(cache_files) > 50:  # 限制最多50个缓存文件
                cache_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.cache_dir, x)))
                for file_name in cache_files[:-30]:  # 保留最新的30个
                    os.remove(os.path.join(self.cache_dir, file_name))
        except Exception:
            pass  # 忽略清理过程中的错误
    
    def get(self, cache_key):
        """
        从缓存获取数据
        
        Args:
            cache_key (str): 缓存键
            
        Returns:
            dict or None: 缓存数据，如果不存在或过期则返回None
        """
        cache_path = self._get_cache_path(cache_key)
        if not os.path.exists(cache_path):
            return None
            
        # 检查是否过期
        if time.time() - os.path.getmtime(cache_path) > self.expiry_time:
            os.remove(cache_path)
            return None
            
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return None
    
    def set(self, cache_key, data):
        """
        设置缓存数据
        
        Args:
            cache_key (str): 缓存键
            data (dict): 要缓存的数据
        """
        # 在设置新缓存前进行清理
        self._cleanup_old_cache()
        
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass  # 忽略缓存写入错误
    
    def cache_chart(self, func):
        """
        图表生成函数装饰器
        
        Args:
            func: 被装饰的函数
            
        Returns:
            function: 装饰器函数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = self._get_cache_key(func.__name__, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = self.get(cache_key)
            if cached_result is not None:
                return cached_result
                
            # 调用原函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            self.set(cache_key, result)
            
            return result
        return wrapper

# 创建全局缓存实例，减小过期时间和缓存数量
chart_cache = ChartCache(expiry_time=1800)  # 30分钟过期