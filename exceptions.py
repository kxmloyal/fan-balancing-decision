# -*- coding: utf-8 -*-
"""
自定义异常类
"""
import traceback
from datetime import datetime
from typing import Dict, Any, Optional


class AppException(Exception):
    """
    应用基础异常类
    """

    def __init__(self, message, status_code=500, error_code=None, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.timestamp = datetime.now().isoformat()
        self.traceback = traceback.format_exc()
        self.context = kwargs.get('context', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将异常转换为字典
        """
        return {
            'message': self.message,
            'status_code': self.status_code,
            'error_code': self.error_code,
            'timestamp': self.timestamp,
            'error_type': self.__class__.__name__,
            'context': self.context
        }
    
    def get_user_friendly_message(self) -> str:
        """
        获取用户友好的错误消息
        """
        return self.message
    
    @classmethod
    def from_exception(cls, exc: Exception, message: Optional[str] = None) -> 'AppException':
        """
        从普通异常创建AppException
        """
        return cls(
            message or str(exc),
            status_code=500,
            error_code='INTERNAL_ERROR',
            context={'original_exception': str(exc)}
        )


class FileProcessingError(AppException):
    """
    文件处理异常
    """

    def __init__(self, message, filename=None, *args, **kwargs):
        super().__init__(
            message,
            status_code=400,
            error_code="FILE_PROCESSING_ERROR",
            *args,
            **kwargs
        )
        self.filename = filename
        self.context['filename'] = filename
    
    def get_user_friendly_message(self) -> str:
        """
        获取用户友好的错误消息
        """
        if self.filename:
            return f"文件处理失败 ({self.filename}): {self.message}"
        return f"文件处理失败: {self.message}"


class DataValidationError(AppException):
    """
    数据验证异常
    """

    def __init__(self, message, field=None, *args, **kwargs):
        super().__init__(
            message,
            status_code=400,
            error_code="DATA_VALIDATION_ERROR",
            *args,
            **kwargs
        )
        self.field = field
        self.context['field'] = field
    
    def get_user_friendly_message(self) -> str:
        """
        获取用户友好的错误消息
        """
        if self.field:
            return f"数据验证失败 ({self.field}): {self.message}"
        return f"数据验证失败: {self.message}"


class ChartGenerationError(AppException):
    """
    图表生成异常
    """

    def __init__(self, message, chart_type=None, *args, **kwargs):
        super().__init__(
            message,
            status_code=500,
            error_code="CHART_GENERATION_ERROR",
            *args,
            **kwargs
        )
        self.chart_type = chart_type
        self.context['chart_type'] = chart_type
    
    def get_user_friendly_message(self) -> str:
        """
        获取用户友好的错误消息
        """
        if self.chart_type:
            return f"图表生成失败 ({self.chart_type}): {self.message}"
        return f"图表生成失败: {self.message}"


class DatabaseError(AppException):
    """
    数据库操作异常
    """

    def __init__(self, message, operation=None, *args, **kwargs):
        super().__init__(
            message, status_code=500, error_code="DATABASE_ERROR", *args, **kwargs
        )
        self.operation = operation
        self.context['operation'] = operation
    
    def get_user_friendly_message(self) -> str:
        """
        获取用户友好的错误消息
        """
        if self.operation:
            return f"数据库操作失败 ({self.operation}): {self.message}"
        return f"数据库操作失败: {self.message}"


class MLModelError(AppException):
    """
    机器学习模型异常
    """

    def __init__(self, message, model_type=None, *args, **kwargs):
        super().__init__(
            message, status_code=500, error_code="ML_MODEL_ERROR", *args, **kwargs
        )
        self.model_type = model_type
        self.context['model_type'] = model_type
    
    def get_user_friendly_message(self) -> str:
        """
        获取用户友好的错误消息
        """
        if self.model_type:
            return f"模型操作失败 ({self.model_type}): {self.message}"
        return f"模型操作失败: {self.message}"


class AuthenticationError(AppException):
    """
    认证异常
    """

    def __init__(self, message, *args, **kwargs):
        super().__init__(
            message, status_code=401, error_code="AUTHENTICATION_ERROR", *args, **kwargs
        )
    
    def get_user_friendly_message(self) -> str:
        """
        获取用户友好的错误消息
        """
        return f"认证失败: {self.message}"


class AuthorizationError(AppException):
    """
    授权异常
    """

    def __init__(self, message, *args, **kwargs):
        super().__init__(
            message, status_code=403, error_code="AUTHORIZATION_ERROR", *args, **kwargs
        )
    
    def get_user_friendly_message(self) -> str:
        """
        获取用户友好的错误消息
        """
        return f"授权失败: {self.message}"


class ResourceNotFoundError(AppException):
    """
    资源不存在异常
    """

    def __init__(self, message, resource_type=None, resource_id=None, *args, **kwargs):
        super().__init__(
            message, status_code=404, error_code="RESOURCE_NOT_FOUND", *args, **kwargs
        )
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.context['resource_type'] = resource_type
        self.context['resource_id'] = resource_id
    
    def get_user_friendly_message(self) -> str:
        """
        获取用户友好的错误消息
        """
        if self.resource_type and self.resource_id:
            return f"资源不存在 ({self.resource_type}: {self.resource_id}): {self.message}"
        elif self.resource_type:
            return f"资源不存在 ({self.resource_type}): {self.message}"
        return f"资源不存在: {self.message}"


class RateLimitExceededError(AppException):
    """
    速率限制异常
    """

    def __init__(self, message, limit=None, remaining=None, *args, **kwargs):
        super().__init__(
            message, status_code=429, error_code="RATE_LIMIT_EXCEEDED", *args, **kwargs
        )
        self.limit = limit
        self.remaining = remaining
        self.context['limit'] = limit
        self.context['remaining'] = remaining
    
    def get_user_friendly_message(self) -> str:
        """
        获取用户友好的错误消息
        """
        if self.limit:
            return f"请求过于频繁，请稍后再试。限制: {self.limit}/分钟"
        return f"请求过于频繁，请稍后再试"


class ServiceUnavailableError(AppException):
    """
    服务不可用异常
    """

    def __init__(self, message, service=None, *args, **kwargs):
        super().__init__(
            message, status_code=503, error_code="SERVICE_UNAVAILABLE", *args, **kwargs
        )
        self.service = service
        self.context['service'] = service
    
    def get_user_friendly_message(self) -> str:
        """
        获取用户友好的错误消息
        """
        if self.service:
            return f"服务暂时不可用 ({self.service}): {self.message}"
        return f"服务暂时不可用: {self.message}"


class TimeoutError(AppException):
    """
    超时异常
    """

    def __init__(self, message, timeout=None, *args, **kwargs):
        super().__init__(
            message, status_code=504, error_code="TIMEOUT_ERROR", *args, **kwargs
        )
        self.timeout = timeout
        self.context['timeout'] = timeout
    
    def get_user_friendly_message(self) -> str:
        """
        获取用户友好的错误消息
        """
        if self.timeout:
            return f"操作超时 ({self.timeout}秒): {self.message}"
        return f"操作超时: {self.message}"
