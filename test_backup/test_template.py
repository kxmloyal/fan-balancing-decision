#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试模板渲染的脚本
"""

from flask import Flask, render_template

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'

with app.app_context():
    try:
        # 测试渲染index.html模板
        result = render_template('index.html')
        print("✓ index.html 模板渲染成功")
    except Exception as e:
        print(f"✗ index.html 模板渲染失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        # 测试渲染_charts_partial.html模板
        result = render_template('_charts_partial.html')
        print("✓ _charts_partial.html 模板渲染成功")
    except Exception as e:
        print(f"✗ _charts_partial.html 模板渲染失败: {e}")
        import traceback
        traceback.print_exc()
