#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最小的Flask测试应用
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    print('Starting minimal Flask app...')
    app.run(host='0.0.0.0', port=5000, debug=True)
