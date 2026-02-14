#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
详细测试模板渲染的脚本
"""

from flask import Flask, render_template, request

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'
app.config['SERVER_NAME'] = 'localhost:5000'
app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'http'

# 模拟请求环境
with app.test_request_context():
    try:
        # 测试渲染index.html模板
        result = render_template('index.html')
        print("✓ index.html 模板渲染成功")
        print(f"模板大小: {len(result)} 字符")
    except Exception as e:
        print(f"✗ index.html 模板渲染失败: {e}")
        import traceback
        traceback.print_exc()
