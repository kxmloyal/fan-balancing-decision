#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""文件管理器"""

import os
import time


class FileManager:
    """文件管理器类"""

    def __init__(self):
        """初始化文件管理器"""
        self.app = None

    def init_app(self, app):
        """初始化应用"""
        self.app = app

    def allowed_file(self, filename):
        """检查文件是否允许上传"""
        if not self.app:
            return False
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in self.app.config["ALLOWED_EXTENSIONS"]
        )

    MAGIC_BYTES_MAP = {
        "csv": [b"PK\x03\x04", b"\xef\xbb\xbf"],  # UTF-8 BOM or plain text
        "xlsx": [b"PK\x03\x04"],
        "xls": [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],
        "json": [b"[", b"{"],
        "xml": [b"\xef\xbb\xbf<", b"<?xml", b"<"],
        "txt": [],
    }

    def validate_magic_bytes(self, file_storage):
        """校验文件头部魔数，防御扩展名伪造"""
        ext = (
            file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
        )
        if ext not in self.MAGIC_BYTES_MAP:
            return False
        expected_bytes = self.MAGIC_BYTES_MAP[ext]
        if not expected_bytes:
            return True
        file_storage.stream.seek(0)
        header = file_storage.stream.read(16)
        file_storage.stream.seek(0)
        return any(header.startswith(sig) for sig in expected_bytes)

    def get_upload_path(self, filename):
        """获取上传文件路径"""
        if not self.app:
            return None
        return os.path.join(self.app.config["UPLOAD_FOLDER"], filename)

    def get_output_path(self, filename):
        """获取输出文件路径"""
        if not self.app:
            return None
        return os.path.join(self.app.config["OUTPUT_FOLDER"], filename)

    def clean_old_files(self, days=7):
        """清理指定天数前的文件（仅清理临时上传目录，不触碰持久化报告输出目录）"""
        if not self.app:
            return 0

        cutoff_time = time.time() - (days * 24 * 60 * 60)
        cleaned_count = 0

        upload_folder = self.app.config.get("UPLOAD_FOLDER")
        if upload_folder and os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                filepath = os.path.join(upload_folder, filename)
                if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
                    try:
                        os.remove(filepath)
                        cleaned_count += 1
                    except Exception:
                        pass

        return cleaned_count

    def create_uploads_directory(self):
        """创建上传目录"""
        if not self.app:
            return
        upload_folder = self.app.config.get("UPLOAD_FOLDER")
        if upload_folder and not os.path.exists(upload_folder):
            try:
                os.makedirs(upload_folder)
            except Exception:
                pass

    def create_outputs_directory(self):
        """创建输出目录"""
        if not self.app:
            return
        output_folder = self.app.config.get("OUTPUT_FOLDER")
        if output_folder and not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder)
            except Exception:
                pass

    def check_total_storage(self):
        """检查总存储空间使用情况"""
        if not self.app:
            return True, 0

        total_size = 0
        upload_folder = self.app.config.get("UPLOAD_FOLDER")
        output_folder = self.app.config.get("OUTPUT_FOLDER")

        # 检查上传目录
        if upload_folder and os.path.exists(upload_folder):
            for root, dirs, files in os.walk(upload_folder):
                for file in files:
                    filepath = os.path.join(root, file)
                    if os.path.isfile(filepath):
                        total_size += os.path.getsize(filepath)

        # 检查输出目录
        if output_folder and os.path.exists(output_folder):
            for root, dirs, files in os.walk(output_folder):
                for file in files:
                    filepath = os.path.join(root, file)
                    if os.path.isfile(filepath):
                        total_size += os.path.getsize(filepath)

        # 检查是否超过5GB限制
        storage_limit = 5 * 1024 * 1024 * 1024  # 5GB
        storage_ok = total_size < storage_limit

        return storage_ok, total_size

    def check_user_file_limit(self, user_id):
        """检查用户文件数量限制"""
        if not self.app:
            return True, 0

        upload_folder = self.app.config.get("UPLOAD_FOLDER")
        if not upload_folder or not os.path.exists(upload_folder):
            return True, 0

        # 简单计算文件数量（实际项目中可能需要更复杂的用户文件跟踪）
        file_count = 0
        for root, dirs, files in os.walk(upload_folder):
            file_count += len(files)

        # 检查是否超过50个文件限制
        file_limit = 50
        file_limit_ok = file_count < file_limit

        return file_limit_ok, file_count

    def check_file_size(self, file_size):
        """检查文件大小是否超过限制"""
        if not self.app:
            return True

        max_size = self.app.config.get("MAX_CONTENT_LENGTH", 100 * 1024 * 1024)  # 默认100MB
        return file_size <= max_size


# 创建全局文件管理器实例
file_manager = FileManager()
