#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据处理模块单元测试
"""

import os
import sys
import tempfile
import pandas as pd
import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processing import allowed_file, parse_single_surface_file


def test_allowed_file():
    """测试allowed_file函数"""
    # 测试允许的文件格式
    assert allowed_file('test.csv', {'csv', 'xlsx', 'xls'}) == True
    assert allowed_file('test.xlsx', {'csv', 'xlsx', 'xls'}) == True
    assert allowed_file('test.xls', {'csv', 'xlsx', 'xls'}) == True
    
    # 测试不允许的文件格式
    assert allowed_file('test.txt', {'csv', 'xlsx', 'xls'}) == False
    assert allowed_file('test.pdf', {'csv', 'xlsx', 'xls'}) == False
    
    # 测试没有扩展名的文件
    assert allowed_file('test', {'csv', 'xlsx', 'xls'}) == False
    
    # 测试空文件名
    assert allowed_file('', {'csv', 'xlsx', 'xls'}) == False


def test_parse_single_surface_file():
    """测试parse_single_surface_file函数"""
    # 创建一个临时的CSV文件用于测试
    test_data = "3000rpm,4000rpm\n17.2,16.2\n17.1,16.1\n16.8,15.9\n17.0,16.0\n16.9,16.1"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(test_data)
        temp_file_path = f.name
    
    try:
        # 测试解析CSV文件
        parsed_data = parse_single_surface_file(temp_file_path)
        
        # 验证解析结果
        assert isinstance(parsed_data, dict)
        assert '3000rpm' in parsed_data
        assert '4000rpm' in parsed_data
        assert len(parsed_data['3000rpm']) == 5
        assert len(parsed_data['4000rpm']) == 5
        assert parsed_data['3000rpm'][0] == 17.2
        assert parsed_data['4000rpm'][0] == 16.2
    finally:
        # 删除临时文件
        os.unlink(temp_file_path)


def test_parse_single_surface_file_invalid_format():
    """测试解析无效格式的文件"""
    # 创建一个无效的文件
    invalid_data = "This is not a valid CSV file"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(invalid_data)
        temp_file_path = f.name
    
    try:
        # 测试解析无效文件应该抛出异常
        with pytest.raises(ValueError):
            parse_single_surface_file(temp_file_path)
    finally:
        # 删除临时文件
        os.unlink(temp_file_path)


def test_parse_single_surface_file_empty():
    """测试解析空文件"""
    # 创建一个空文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_file_path = f.name
    
    try:
        # 测试解析空文件应该抛出异常
        with pytest.raises(ValueError):
            parse_single_surface_file(temp_file_path)
    finally:
        # 删除临时文件
        os.unlink(temp_file_path)
