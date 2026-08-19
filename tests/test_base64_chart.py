#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试实际图表文件的base64编码
"""

import base64
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 获取outputs目录中的第一个png文件
outputs_dir = "outputs"
png_files = [f for f in os.listdir(outputs_dir) if f.endswith(".png")]

if png_files:
    test_file = os.path.join(outputs_dir, png_files[0])
    print(f"测试文件: {test_file}")
    print(f"文件大小: {os.path.getsize(test_file)} bytes")

    # 读取文件并转换为base64
    with open(test_file, "rb") as img_file:
        img_data = img_file.read()
        img_base64 = base64.b64encode(img_data).decode("utf-8")

    print(f"Base64长度: {len(img_base64)} 字符")
    print(f"Base64前缀: {img_base64[:50]}...")
    print("\n文件存在，可以正常读取！")
else:
    print("没有找到PNG文件")
