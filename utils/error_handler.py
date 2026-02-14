import logging
import os
import traceback
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Dict, Any, Optional

# 导入自定义异常类
from exceptions import AppException

class ErrorHandler:
    def __init__(self, app=None):
        self.app = app
        self.logs_dir = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        self.logs_dir = app.config.get('LOGS_FOLDER', 'logs')
        os.makedirs(self.logs_dir, exist_ok=True)
        self.setup_logging()
    
    def setup_logging(self):
        """
        设置分级日志系统
        """
        # 创建日志记录器
        logger = logging.getLogger('fan_tool')
        logger.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        if logger.handlers:
            return
        
        # 创建按天分割的文件处理器
        log_file = os.path.join(self.logs_dir, 'app.log')
        file_handler = TimedRotatingFileHandler(
            log_file, 
            when='midnight', 
            interval=1, 
            backupCount=30,  # 保留30天的日志
            encoding='utf-8'
        )
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(module)s - %(message)s - %(pathname)s:%(lineno)d'
        )
        file_handler.setFormatter(formatter)
        
        # 添加处理器到记录器
        logger.addHandler(file_handler)
        
        # 如果是开发环境，也输出到控制台
        if self.app and self.app.debug:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
    
    def log_error(self, level, module, message, user_id=None, ip_address=None, error_trace=None, context=None):
        """
        记录日志
        """
        logger = logging.getLogger('fan_tool')
        log_message = f"{message}"
        if user_id:
            log_message += f" - User: {user_id}"
        if ip_address:
            log_message += f" - IP: {ip_address}"
        if context:
            log_message += f" - Context: {context}"
        if error_trace:
            log_message += f"\n{error_trace}"
        
        if level == 'INFO':
            logger.info(log_message)
        elif level == 'WARNING':
            logger.warning(log_message)
        elif level == 'ERROR':
            logger.error(log_message)
        elif level == 'CRITICAL':
            logger.critical(log_message)
    
    def handle_exception(self, exception, module, user_id=None, ip_address=None, context=None):
        """
        处理异常
        """
        error_trace = traceback.format_exc()
        error_message = str(exception)
        
        # 记录异常
        log_context = context or {}
        if isinstance(exception, AppException):
            log_context.update(exception.context)
        
        self.log_error('ERROR', module, error_message, user_id, ip_address, error_trace, log_context)
        
        # 返回用户友好的错误信息
        return self.get_user_friendly_message(exception)
    
    def get_user_friendly_message(self, exception):
        """
        获取用户友好的错误信息
        """
        if isinstance(exception, AppException):
            return exception.get_user_friendly_message()
        
        exception_type = type(exception).__name__
        
        # 定义不同异常类型的用户友好信息
        error_messages = {
            'FileNotFoundError': '文件不存在，请检查文件路径是否正确',
            'PermissionError': '没有文件访问权限，请检查文件权限设置',
            'UnicodeDecodeError': '文件编码错误，无法读取文件内容',
            'ValueError': '数据格式错误，请检查文件内容是否符合要求',
            'TypeError': '数据类型错误，请检查文件内容是否正确',
            'ZeroDivisionError': '计算错误，出现除零操作',
            'OverflowError': '计算错误，数值溢出',
            'DatabaseError': '数据库错误，请稍后重试',
            'ConnectionError': '连接错误，请检查网络连接',
            'TimeoutError': '操作超时，请稍后重试',
            'FileTooLargeError': '文件大小超过限制，请上传小于100MB的文件',
            'FileCountExceededError': '文件数量超过限制，请删除部分文件后再上传',
            'StorageFullError': '存储空间不足，请删除部分文件后再上传',
            'InvalidFileFormatError': '文件格式不支持，请上传CSV、XLSX或XLS格式的文件',
            'EmptyFileError': '文件内容为空，请检查文件是否包含有效数据',
            'DataValidationError': '数据验证失败，请检查文件内容是否符合要求',
            'CalculationError': '计算错误，请检查数据是否正确',
            'ChartGenerationError': '图表生成失败，请稍后重试',
            'ReportGenerationError': '报告生成失败，请稍后重试',
            'SessionExpiredError': '会话已过期，请重新上传数据文件',
            'MissingRequiredFieldError': '缺少必填字段，请检查表单填写是否完整',
        }
        
        # 返回对应的用户友好信息，如果没有找到则返回默认信息
        return error_messages.get(exception_type, f'操作失败：{str(exception)}')
    
    def handle_error_response(self, exception, status_code=500):
        """
        处理错误响应
        """
        if isinstance(exception, AppException):
            error_dict = exception.to_dict()
            return error_dict, exception.status_code
        
        # 处理普通异常
        app_exception = AppException.from_exception(exception)
        return app_exception.to_dict(), status_code

# 全局实例
error_handler = ErrorHandler()