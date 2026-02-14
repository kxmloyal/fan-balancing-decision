#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统计分析模块单元测试
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statistics import (calculate_surface_stats, generate_stats_data,
                       calculate_optimal_speed_evaluation, generate_stats)


def test_calculate_surface_stats():
    """测试calculate_surface_stats函数"""
    # 测试正常数据
    samples = [17.2, 17.1, 16.8, 17.0, 16.9]
    stats = calculate_surface_stats(samples, 'P1')
    
    # 验证统计结果
    assert isinstance(stats, dict)
    assert 'P1-平均值' in stats
    assert 'P1-中位数' in stats
    assert 'P1-标准差' in stats
    assert 'P1-最小值' in stats
    assert 'P1-最大值' in stats
    assert 'P1-IQR' in stats
    assert 'P1-CV' in stats
    
    # 测试空数据
    empty_stats = calculate_surface_stats([], 'P1')
    assert empty_stats == {}


def test_generate_stats_data():
    """测试generate_stats_data函数"""
    # 测试数据
    parsed_data = [
        {
            'speed': '3000rpm',
            'p1_samples': [17.2, 17.1, 16.8, 17.0, 16.9],
            'p2_samples': [16.2, 16.1, 15.9, 16.0, 16.1],
            'sum_samples': [33.4, 33.2, 32.7, 33.0, 33.0]
        },
        {
            'speed': '4000rpm',
            'p1_samples': [16.8, 16.7, 16.5, 16.6, 16.7],
            'p2_samples': [15.8, 15.7, 15.5, 15.6, 15.7],
            'sum_samples': [32.6, 32.4, 32.0, 32.2, 32.4]
        }
    ]
    
    stats_data = generate_stats_data(parsed_data)
    
    # 验证生成的统计数据
    assert isinstance(stats_data, list)
    assert len(stats_data) == 2
    assert stats_data[0]['转速'] == '3000rpm'
    assert stats_data[1]['转速'] == '4000rpm'
    assert 'P1-平均值' in stats_data[0]
    assert 'P2-平均值' in stats_data[0]
    assert 'ST面-平均值' in stats_data[0]


def test_calculate_optimal_speed_evaluation():
    """测试calculate_optimal_speed_evaluation函数"""
    # 测试数据
    stats_data = [
        {
            '转速': '3000rpm',
            'P1-IQR': '0.2',
            'P1-CV': '1.0',
            'P2-IQR': '0.1',
            'P2-CV': '0.8',
            'ST面-IQR': '0.3',
            'ST面-CV': '0.9'
        },
        {
            '转速': '4000rpm',
            'P1-IQR': '0.1',
            'P1-CV': '0.5',
            'P2-IQR': '0.05',
            'P2-CV': '0.4',
            'ST面-IQR': '0.15',
            'ST面-CV': '0.6'
        }
    ]
    
    evaluation = calculate_optimal_speed_evaluation(stats_data)
    
    # 验证评估结果
    assert isinstance(evaluation, dict)
    assert 'best_speeds' in evaluation
    assert 'best_score' in evaluation
    assert 'speed_detailed_scores' in evaluation
    assert 'weights' in evaluation
    
    # 验证最优转速选择
    assert len(evaluation['best_speeds']) > 0
    assert evaluation['best_speeds'][0] == '4000rpm'  # 4000rpm的IQR和CV更小，应该是最优转速