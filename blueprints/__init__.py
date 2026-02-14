# -*- coding: utf-8 -*-
"""
蓝图包初始化文件
"""

from .main_bp import main_bp
from .ml_bp import ml_bp
from .outputs_bp import outputs_bp
from .report_bp import report_bp
from .settings_bp import settings_bp

__all__ = ["main_bp", "report_bp", "ml_bp", "outputs_bp", "settings_bp"]
