#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据验证模块（兼容层 — 委托给 app.utils.data_validator）
"""

from app.utils.data_validator import generate_data_warning, validate_and_align_data

__all__ = ["generate_data_warning", "validate_and_align_data"]
