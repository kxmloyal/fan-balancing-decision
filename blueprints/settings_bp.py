# -*- coding: utf-8 -*-
"""
设置模块蓝图：包含数据库连接参数配置和管理功能
"""

import os
import json
from flask import (Blueprint, render_template, request, jsonify, flash, redirect, url_for,
                   current_app)
from utils.config_manager import config_manager
from database_connections import connection_tester, DatabaseConnection

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
def settings():
    """设置页面：数据库连接配置"""
    # 加载当前配置
    current_config = config_manager.get_db_config()
    
    # 预定义支持的数据库类型
    db_types = [
        {"value": "mysql", "label": "MySQL"},
        {"value": "postgresql", "label": "PostgreSQL"},
        {"value": "sqlite", "label": "SQLite"}
    ]
    
    return render_template(
        "settings.html",
        current_config=current_config,
        db_types=db_types,
        active_tab="database"
    )


@settings_bp.route("/test_db_connection", methods=["POST"])
def test_db_connection():
    """测试数据库连接"""
    try:
        # 获取表单数据
        db_type = request.form.get("db_type")
        host = request.form.get("host")
        port = request.form.get("port")
        database = request.form.get("database")
        username = request.form.get("username")
        password = request.form.get("password")
        
        # 输入验证
        if not db_type:
            return jsonify({"success": False, "message": "请选择数据库类型"})
        
        if db_type != "sqlite" and not host:
            return jsonify({"success": False, "message": "请输入主机地址"})
        
        if db_type != "sqlite" and not port:
            return jsonify({"success": False, "message": "请输入端口号"})
        
        if db_type != "sqlite" and not database:
            return jsonify({"success": False, "message": "请输入数据库名称"})
        
        if db_type != "sqlite" and not username:
            return jsonify({"success": False, "message": "请输入用户名"})
        
        # 创建连接对象
        connection = DatabaseConnection(
            id=0,
            name="test_connection",
            type=db_type,
            host=host,
            port=int(port) if port else None,
            database=database,
            username=username,
            password=password
        )
        
        # 测试连接
        result = connection_tester.test_connection(connection)
        
        if result["success"]:
            return jsonify({"success": True, "message": "连接测试成功！"})
        else:
            return jsonify({"success": False, "message": f"连接测试失败：{result['error']}"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"测试过程中出现错误：{str(e)}"})


@settings_bp.route("/save_db_config", methods=["POST"])
def save_db_config():
    """保存数据库连接配置"""
    try:
        # 获取表单数据
        db_type = request.form.get("db_type")
        host = request.form.get("host")
        port = request.form.get("port")
        database = request.form.get("database")
        username = request.form.get("username")
        password = request.form.get("password")
        save_method = request.form.get("save_method", "file")
        
        # 输入验证
        if not db_type:
            flash("请选择数据库类型", "error")
            return redirect(url_for("settings.settings"))
        
        if db_type != "sqlite" and not host:
            flash("请输入主机地址", "error")
            return redirect(url_for("settings.settings"))
        
        if db_type != "sqlite" and not port:
            flash("请输入端口号", "error")
            return redirect(url_for("settings.settings"))
        
        if db_type != "sqlite" and not database:
            flash("请输入数据库名称", "error")
            return redirect(url_for("settings.settings"))
        
        if db_type != "sqlite" and not username:
            flash("请输入用户名", "error")
            return redirect(url_for("settings.settings"))
        
        # 构建配置字典
        config = {
            "db_type": db_type,
            "host": host,
            "port": port,
            "database": database,
            "username": username,
            "password": password
        }
        
        # 保存配置
        success = config_manager.save_db_config(config, save_method)
        
        if success:
            flash("数据库连接配置保存成功！", "success")
        else:
            flash("数据库连接配置保存失败", "error")
            
    except Exception as e:
        flash(f"保存配置时出现错误：{str(e)}", "error")
    
    return redirect(url_for("settings.settings"))


@settings_bp.route("/load_db_config")
def load_db_config():
    """重新加载数据库连接配置"""
    try:
        config = config_manager.get_db_config()
        return jsonify({"success": True, "config": config})
    except Exception as e:
        return jsonify({"success": False, "message": f"加载配置时出现错误：{str(e)}"})


@settings_bp.route("/reset_db_config")
def reset_db_config():
    """重置数据库连接配置"""
    try:
        success = config_manager.reset_db_config()
        if success:
            flash("数据库连接配置已重置", "success")
        else:
            flash("重置配置失败", "error")
    except Exception as e:
        flash(f"重置配置时出现错误：{str(e)}", "error")
    
    return redirect(url_for("settings.settings"))
