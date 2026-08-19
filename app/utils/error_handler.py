#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""错误处理器"""

import logging

from flask import current_app, render_template

logger = logging.getLogger(__name__)


class ErrorHandler:
    """错误处理器类"""

    def __init__(self):
        """初始化错误处理器"""
        self.app = None

    def init_app(self, app):
        """初始化应用"""
        self.app = app

    def handle_404(self, error):
        """处理404错误"""
        return render_template("404.html"), 404

    def handle_500(self, error):
        """处理500错误"""
        return render_template("error.html", error=error), 500

    def handle_400(self, error):
        """处理400错误"""
        return render_template("error.html", error=error), 400

    def handle_403(self, error):
        """处理403错误"""
        return render_template("error.html", error=error), 403

    def handle_exception(self, error, module="app", user_id=None, ip_address=None):
        """统一异常处理，返回用户友好消息"""
        if current_app and current_app.debug:
            logger.error(
                "模块=%s user=%s ip=%s 异常: %s",
                module,
                user_id or "-",
                ip_address or "-",
                str(error),
                exc_info=True,
            )
        else:
            logger.error("模块=%s 异常: %s", module, str(error))
        return getattr(error, "message", str(error))

    def log_error(self, level, module, message, user_id=None, ip_address=None):
        """记录错误日志"""
        log_func = getattr(logger, level.lower(), logger.error)
        if current_app and current_app.debug:
            log_func("模块=%s user=%s ip=%s %s", module, user_id or "-", ip_address or "-", message)
        else:
            log_func("模块=%s %s", module, message)


def register_error_handlers(app):
    """注册错误处理器"""
    error_handler = ErrorHandler()
    error_handler.init_app(app)

    app.register_error_handler(404, error_handler.handle_404)
    app.register_error_handler(500, error_handler.handle_500)
    app.register_error_handler(400, error_handler.handle_400)
    app.register_error_handler(403, error_handler.handle_403)


# 创建全局错误处理器实例
error_handler = ErrorHandler()
