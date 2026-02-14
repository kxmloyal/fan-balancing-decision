#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的Flask服务器测试
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, Flask is working!'

if __name__ == '__main__':
    print('=== 启动测试服务器 ===')
    print('服务器将在 http://localhost:1324 上运行')
    print('按 Ctrl+C 停止服务器')
    app.run(host='0.0.0.0', port=1324, debug=True)
