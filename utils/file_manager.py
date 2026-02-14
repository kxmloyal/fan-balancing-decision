import os
import time
import shutil
from datetime import datetime, timedelta
import logging

class FileManager:
    def __init__(self, app=None):
        self.app = app
        self.uploads_dir = None
        self.outputs_dir = None
        self.logs_dir = None
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.max_total_size = 5 * 1024 * 1024 * 1024  # 5GB
        self.max_files_per_user = 50
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        self.uploads_dir = app.config.get('UPLOAD_FOLDER', 'uploads')
        self.outputs_dir = app.config.get('OUTPUT_FOLDER', 'outputs')
        self.logs_dir = app.config.get('LOGS_FOLDER', 'logs')
        
        # 确保目录存在
        for directory in [self.uploads_dir, self.outputs_dir, self.logs_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def clean_old_files(self, days=7):
        """清理指定天数前的文件"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        cleaned_files = []
        
        # 清理uploads目录
        for root, dirs, files in os.walk(self.uploads_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getmtime(file_path) < cutoff_time:
                    try:
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                    except Exception as e:
                        logging.error(f"清理文件失败 {file_path}: {e}")
        
        # 清理outputs目录
        for root, dirs, files in os.walk(self.outputs_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getmtime(file_path) < cutoff_time:
                    try:
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                    except Exception as e:
                        logging.error(f"清理文件失败 {file_path}: {e}")
        
        logging.info(f"清理完成，共删除 {len(cleaned_files)} 个文件")
        return cleaned_files
    
    def check_file_size(self, file_size):
        """检查文件大小是否符合限制"""
        return file_size <= self.max_file_size
    
    def get_total_storage_usage(self):
        """获取总存储使用量"""
        total_size = 0
        
        # 计算uploads目录大小
        for root, dirs, files in os.walk(self.uploads_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except Exception:
                    pass
        
        # 计算outputs目录大小
        for root, dirs, files in os.walk(self.outputs_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except Exception:
                    pass
        
        return total_size
    
    def check_total_storage(self):
        """检查总存储是否超过限制"""
        total_size = self.get_total_storage_usage()
        return total_size <= self.max_total_size, total_size
    
    def count_user_files(self, user_id):
        """统计用户上传的文件数量"""
        # 这里简化处理，实际项目中可能需要从数据库查询
        # 暂时返回目录中的文件总数
        count = 0
        for root, dirs, files in os.walk(self.uploads_dir):
            count += len(files)
        return count
    
    def check_user_file_limit(self, user_id):
        """检查用户文件数量是否超过限制"""
        count = self.count_user_files(user_id)
        return count < self.max_files_per_user, count
    
    def get_file_age(self, file_path):
        """获取文件年龄（天数）"""
        if not os.path.exists(file_path):
            return None
        
        file_mtime = os.path.getmtime(file_path)
        current_time = time.time()
        age_days = (current_time - file_mtime) / (24 * 60 * 60)
        return age_days
    
    def get_directory_info(self, directory):
        """获取目录信息"""
        file_count = 0
        total_size = 0
        oldest_file = None
        oldest_time = float('inf')
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_count += 1
                try:
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < oldest_time:
                        oldest_time = file_mtime
                        oldest_file = file_path
                except Exception:
                    pass
        
        return {
            'file_count': file_count,
            'total_size': total_size,
            'oldest_file': oldest_file,
            'oldest_time': oldest_time if oldest_time != float('inf') else None
        }
    
    def get_storage_report(self):
        """获取存储报告"""
        uploads_info = self.get_directory_info(self.uploads_dir)
        outputs_info = self.get_directory_info(self.outputs_dir)
        total_size = uploads_info['total_size'] + outputs_info['total_size']
        total_files = uploads_info['file_count'] + outputs_info['file_count']
        
        return {
            'uploads': uploads_info,
            'outputs': outputs_info,
            'total_size': total_size,
            'total_files': total_files,
            'max_total_size': self.max_total_size,
            'percentage_used': (total_size / self.max_total_size) * 100 if self.max_total_size > 0 else 0
        }

# 全局实例
file_manager = FileManager()