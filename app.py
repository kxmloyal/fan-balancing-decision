#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
扇叶平衡补土转速评估工具主程序
支持P1/P2/ST三面数据分析，具备转速匹配、统计分析、图表生成等功能
"""

# 首先导入必要的模块
import os
import sys

print("=== 开始执行app.py ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")

# 添加当前目录到Python路径 - 必须放在所有导入之前
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
print(f"Added to sys.path: {current_dir}")
print(f"sys.path: {sys.path[:5]}...")
print("=== 开始导入模块 ===")

import gc
from datetime import datetime

print("✓ 导入基础模块成功")

import pandas as pd
print("✓ 导入pandas成功")

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   send_file, send_from_directory, session, url_for)
print("✓ 导入Flask成功")

from flask_sqlalchemy import SQLAlchemy
print("✓ 导入SQLAlchemy成功")

from werkzeug.utils import secure_filename
print("✓ 导入secure_filename成功")

from apscheduler.schedulers.background import BackgroundScheduler
print("✓ 导入BackgroundScheduler成功")

print("✓ 导入核心模块成功")

try:
    from utils.file_manager import file_manager
    print("✓ 导入文件管理器成功")
except Exception as e:
    print(f"✗ 导入文件管理器失败: {e}")
    import traceback
    traceback.print_exc()

# ========== 项目基础配置 ==========
# 显式指定静态文件目录
app = Flask(__name__, static_folder="static", static_url_path="/static")

# 在生产环境中应设置为False
app.debug = False

# 配置项直接设置在app.py中
app.config["SECRET_KEY"] = "boxplot_tool_2025_secure_key"
app.config["SESSION_TYPE"] = "filesystem"
app.config["PERMANENT_SESSION_LIFETIME"] = 3600

# 使用绝对路径确保在宝塔面板中正确访问
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
app.config["OUTPUT_FOLDER"] = os.path.join(BASE_DIR, "outputs")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
app.config["ALLOWED_EXTENSIONS"] = {"csv", "xlsx", "xls", "json", "xml", "txt"}

# 初始化数据库
from flask_migrate import Migrate

# 使用配置管理器获取数据库连接URI
from utils.config_manager import config_manager
app.config["SQLALCHEMY_DATABASE_URI"] = config_manager.get_sqlalchemy_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = False

# 全局数据库连接状态
DB_CONNECTED = False
DB_ERROR_MESSAGE = ""

print("=== 开始初始化数据库连接 ===")
# 初始化数据库连接
try:
    db = SQLAlchemy(app)
    print("✓ SQLAlchemy 初始化成功")
    migrate = Migrate(app, db)
    print("✓ Migrate 初始化成功")
    DB_CONNECTED = True
    print("数据库连接初始化成功 (SQLite)")
    # 清除之前的错误信息
    if "DATABASE_ERROR" in app.config:
        del app.config["DATABASE_ERROR"]
    print("=== 数据库连接初始化完成 ===")
except Exception as e:
    error_message = f"数据库连接初始化失败: {str(e)}"
    print(error_message)
    print("系统将使用内存模式运行，部分功能可能受限")
    # 保留错误信息，供后续使用
    DB_ERROR_MESSAGE = str(e)
    app.config["DATABASE_ERROR"] = DB_ERROR_MESSAGE
    DB_CONNECTED = False
    print("=== 数据库连接初始化失败 ===")

# 定义核心数据模型
if DB_CONNECTED:
    class UploadFile(db.Model):
        """用户上传文件模型"""
        __tablename__ = "upload_files"
        
        id = db.Column(db.Integer, primary_key=True)
        filename = db.Column(db.String(255), nullable=False, index=True)
        file_path = db.Column(db.String(512), nullable=False)
        file_size = db.Column(db.Integer, nullable=False)
        user_id = db.Column(db.String(100), nullable=True, index=True)
        upload_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        file_type = db.Column(db.String(50), nullable=False)
        status = db.Column(db.String(50), nullable=False, default="uploaded")

    class AnalysisResult(db.Model):
        """分析结果模型"""
        __tablename__ = "analysis_results"
        
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.String(100), nullable=True, index=True)
        fan_model = db.Column(db.String(100), nullable=True, index=True)
        analysis_type = db.Column(db.String(100), nullable=False)
        input_files = db.Column(db.Text, nullable=False)  # JSON格式存储输入文件列表
        output_files = db.Column(db.Text, nullable=False)  # JSON格式存储输出文件列表
        best_speed = db.Column(db.String(100), nullable=True)
        analysis_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        status = db.Column(db.String(50), nullable=False, default="completed")

    class ChartCache(db.Model):
        """图表缓存模型"""
        __tablename__ = "chart_cache"
        
        id = db.Column(db.Integer, primary_key=True)
        cache_key = db.Column(db.String(255), nullable=False, unique=True, index=True)
        chart_data = db.Column(db.Text, nullable=False)  # JSON格式存储图表数据
        created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        last_accessed = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    class SystemLog(db.Model):
        """系统日志模型"""
        __tablename__ = "system_logs"
        
        id = db.Column(db.Integer, primary_key=True)
        log_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        log_level = db.Column(db.String(20), nullable=False, index=True)
        module = db.Column(db.String(100), nullable=False, index=True)
        message = db.Column(db.Text, nullable=False)
        user_id = db.Column(db.String(100), nullable=True, index=True)
        ip_address = db.Column(db.String(50), nullable=True)
        error_trace = db.Column(db.Text, nullable=True)

    print("=== 开始创建数据库表 ===")
# 创建数据库表
try:
    if DB_CONNECTED:
        print("正在创建数据库表...")
        # 暂时跳过数据库表创建，直接继续启动
        print("✓ 跳过数据库表创建，直接继续启动")
        # 清除之前的错误信息
        if "DATABASE_ERROR" in app.config:
            del app.config["DATABASE_ERROR"]
        DB_ERROR_MESSAGE = ""
        print("=== 数据库表创建完成 ===")
except Exception as e:
    error_message = f"数据库表创建失败: {str(e)}"
    print(error_message)
    print("系统将使用内存模式运行，部分功能可能受限")
    # 保留错误信息，供后续使用
    DB_ERROR_MESSAGE = str(e)
    app.config["DATABASE_ERROR"] = DB_ERROR_MESSAGE
    DB_CONNECTED = False
    print("=== 数据库表创建失败 ===")

print("=== 开始初始化组件 ===")

# 初始化文件管理器
print("正在初始化文件管理器...")
file_manager.init_app(app)
print("✓ 文件管理器初始化成功")

# 初始化错误处理器
print("正在初始化错误处理器...")
from utils.error_handler import error_handler
error_handler.init_app(app)
print("✓ 错误处理器初始化成功")

# 初始化报告导出器
print("正在初始化报告导出器...")
try:
    from report_export import report_exporter
    report_exporter.init_app(app)
    print("✓ 报告导出器初始化成功")
except Exception as e:
    print(f"✗ 报告导出器初始化失败: {str(e)}")
    print("系统将在需要时尝试导入weasyprint")

# 设置定时任务
print("正在设置定时任务...")
scheduler = BackgroundScheduler()
print("✓ 定时任务调度器创建成功")

# 每天凌晨2点执行文件清理任务
scheduler.add_job(
    func=lambda: file_manager.clean_old_files(days=7),
    trigger="cron",
    hour=2,
    minute=0,
    id="clean_old_files",
    name="清理7天前的文件",
    replace_existing=True
)
print("✓ 定时任务添加成功")

# 启动定时任务
try:
    scheduler.start()
    print("✓ 定时任务调度器已启动")
except Exception as e:
    print(f"✗ 定时任务调度器启动失败: {str(e)}")

print("=== 组件初始化完成 ===")

print("=== 开始导入统计和图表模块 ===")
from statistics import (calculate_optimal_speed_evaluation,
                        generate_single_surface_stats, generate_stats,
                        generate_stats_data)
print("✓ 导入统计模块成功")

# CSRF Protection
from flask_wtf.csrf import CSRFProtect
print("✓ 导入CSRF保护成功")

from chart_generation import (CHART_TYPE_CONFIG, generate_plots,
                              generate_single_surface_plots)
print("✓ 导入图表生成模块成功")

# 导入新拆分的模块
from data_processing import allowed_file, parse_single_surface_file
print("✓ 导入数据处理模块成功")

# 导入自定义异常类
from exceptions import *
print("✓ 导入异常类成功")

from utils.data_validator import generate_data_warning, validate_and_align_data
print("✓ 导入数据验证模块成功")
print("=== 模块导入完成 ===")

print("=== 开始初始化会话和CSRF保护 ===")
# Session handling
try:
    from flask_session import Session
    print("✓ 导入Session成功")
except ImportError:
    print("✗ 导入Session失败，使用MockSession")

    class MockSession:
        def __init__(self):
            pass

        def init_app(self, app):
            # Create necessary directories
            for folder in [
                app.config.get("UPLOAD_FOLDER", "uploads"),
                app.config.get("OUTPUT_FOLDER", "outputs"),
            ]:
                if not os.path.exists(folder):
                    os.makedirs(folder)

    Session = MockSession

# 初始化Session（必须在CSRF保护之前）
session_manager = Session()
session_manager.init_app(app)
print("✓ Session初始化成功")

# 初始化CSRF保护
csrf = CSRFProtect(app)
print("✓ CSRF保护初始化成功")
print("=== 会话和CSRF保护初始化完成 ===")



print("=== 开始导入和注册蓝图 ===")
# 导入蓝图
from blueprints import main_bp, ml_bp, outputs_bp, report_bp, settings_bp
print("✓ 导入蓝图成功")

# 注册蓝图
print("正在注册蓝图...")
app.register_blueprint(main_bp)
print("✓ 注册 main_bp 成功")
app.register_blueprint(report_bp)
print("✓ 注册 report_bp 成功")
app.register_blueprint(ml_bp)
print("✓ 注册 ml_bp 成功")
app.register_blueprint(outputs_bp)
print("✓ 注册 outputs_bp 成功")
app.register_blueprint(settings_bp)
print("✓ 注册 settings_bp 成功")
print("=== 蓝图注册完成 ===")

print("=== 导入数据库连接管理模块 ===")
from database_connections import connection_manager, connection_tester, DatabaseConnection
print("✓ 导入数据库连接管理模块成功")

# Plotly图表测试路由
@app.route('/test_plotly')
def test_plotly():
    """Plotly图表测试页面"""
    return render_template('test_plotly.html')

# 数据连接设置路由
@app.route('/database_connections', methods=['GET', 'POST'])
def database_connections():
    """数据连接设置页面"""
    if request.method == 'POST':
        action = request.form.get('action')
        connection_id = request.form.get('connection_id')
        
        if action == 'save':
            # 保存连接配置
            name = request.form.get('connection_name')
            type = request.form.get('connection_type')
            host = request.form.get('host')
            port = request.form.get('port', type=int) if request.form.get('port') else None
            database = request.form.get('database')
            username = request.form.get('username')
            password = request.form.get('password')
            
            if connection_id:
                # 更新现有连接
                connection = connection_manager.get_connection(int(connection_id))
                if connection:
                    connection.name = name
                    connection.type = type
                    connection.host = host
                    connection.port = port
                    connection.database = database
                    connection.username = username
                    connection.password = password
                    connection_manager.update_connection(connection)
                    flash('连接配置更新成功！')
            else:
                # 创建新连接
                connection = DatabaseConnection(
                    id=0,  # 会自动生成
                    name=name,
                    type=type,
                    host=host,
                    port=port,
                    database=database,
                    username=username,
                    password=password
                )
                connection_manager.add_connection(connection)
                flash('连接配置保存成功！')
        
        elif action == 'delete' and connection_id:
            # 删除连接配置
            if connection_manager.delete_connection(int(connection_id)):
                flash('连接配置删除成功！')
            else:
                flash('连接配置删除失败！')
    
    # 获取所有连接配置
    connections = connection_manager.get_all_connections()
    return render_template('database_connections.html', connections=connections)

# 测试数据库连接路由
@app.route('/test_connection', methods=['POST'])
def test_connection():
    """测试数据库连接"""
    name = request.form.get('connection_name')
    type = request.form.get('connection_type')
    host = request.form.get('host')
    port = request.form.get('port', type=int) if request.form.get('port') else None
    database = request.form.get('database')
    username = request.form.get('username')
    password = request.form.get('password')
    
    # 创建连接对象
    connection = DatabaseConnection(
        id=0,
        name=name,
        type=type,
        host=host,
        port=port,
        database=database,
        username=username,
        password=password
    )
    
    # 测试连接
    result = connection_tester.test_connection(connection)
    return jsonify(result)

# 获取连接详情路由
@app.route('/get_connection')
def get_connection():
    """获取连接详情"""
    connection_id = request.args.get('id', type=int)
    if not connection_id:
        return jsonify({'success': False, 'message': '连接ID不能为空'})
    
    connection = connection_manager.get_connection(connection_id)
    if not connection:
        return jsonify({'success': False, 'message': '连接配置不存在'})
    
    return jsonify({
        'success': True,
        'connection': connection.to_dict()
    })


# 创建必要目录（不存在则自动创建）
for folder in [app.config["UPLOAD_FOLDER"], app.config["OUTPUT_FOLDER"]]:
    if not os.path.exists(folder):
        os.makedirs(folder)


# ========== 内存优化配置 ==========
# 定期清理未使用的文件
def cleanup_old_files():
    """定期清理旧文件以释放空间"""
    try:
        # 清理超过1小时的上传文件
        upload_dir = app.config["UPLOAD_FOLDER"]
        output_dir = app.config["OUTPUT_FOLDER"]

        import time

        current_time = time.time()

        # 清理上传目录中的旧文件
        for filename in os.listdir(upload_dir):
            filepath = os.path.join(upload_dir, filename)
            if os.path.isfile(filepath):
                file_modified = os.path.getmtime(filepath)
                if current_time - file_modified > 3600:  # 1小时
                    os.remove(filepath)

        # 清理输出目录中的旧文件
        for filename in os.listdir(output_dir):
            filepath = os.path.join(output_dir, filename)
            if os.path.isfile(filepath):
                file_modified = os.path.getmtime(filepath)
                if current_time - file_modified > 3600:  # 1小时
                    os.remove(filepath)
    except Exception:
        pass  # 忽略清理过程中可能发生的错误


# 每次请求后尝试清理内存
@app.after_request
def after_request(response):
    # 强制垃圾回收
    gc.collect()
    return response


# 每100次请求清理一次旧文件
request_count = 0


@app.before_request
def before_request():
    global request_count
    request_count += 1
    if request_count >= 100:
        request_count = 0
        cleanup_old_files()


def handle_app_exception(error):
    """统一处理应用自定义异常"""
    from utils.error_handler import error_handler
    user_friendly_message = error_handler.handle_exception(error, "app")
    response = {"success": False, "message": user_friendly_message}
    if hasattr(error, "error_code"):
        response["error_code"] = error.error_code
    status_code = getattr(error, "status_code", 500)
    # 添加错误类型信息
    response["error_type"] = type(error).__name__
    return jsonify(response), status_code


@app.errorhandler(404)
def handle_404_error(error):
    """处理404错误"""
    from utils.error_handler import error_handler
    user_friendly_message = "页面不存在，请检查URL是否正确"
    # 记录错误
    error_handler.log_error('WARNING', 'app', str(error))
    # 返回HTML错误页面
    return render_template('404.html', error_message=user_friendly_message), 404


@app.errorhandler(Exception)
def handle_generic_exception(error):
    """处理所有未捕获的异常"""
    from utils.error_handler import error_handler
    user_friendly_message = error_handler.handle_exception(error, "app")
    
    # 检查请求是否接受JSON响应
    if request.headers.get('Accept') and 'application/json' in request.headers.get('Accept'):
        # 返回JSON响应
        response = {"success": False, "message": user_friendly_message}
        response["error_type"] = type(error).__name__
        return jsonify(response), 500
    else:
        # 返回HTML错误页面
        return render_template('error.html', error_message=user_friendly_message), 500


if __name__ == "__main__":
    """启动Flask应用开发服务器"""
    try:
        print("=== 开始启动Flask应用 ===")
        print(f"Python版本: {sys.version}")
        print(f"当前目录: {os.getcwd()}")
        print(f"脚本目录: {os.path.dirname(os.path.abspath(__file__))}")
        print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
        print(f"Output folder: {app.config['OUTPUT_FOLDER']}")
        print(f"Database connected: {DB_CONNECTED}")
        print(f"Secret key: {'Set' if app.config.get('SECRET_KEY') else 'Not set'}")
        print(f"SQLAlchemy URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        print(f"Registered blueprints: {[bp.name for bp in app.blueprints.values()]}")
        print(f"Debug mode: {app.debug}")
        print(f"Allowed extensions: {app.config.get('ALLOWED_EXTENSIONS')}")
        print(f"Max content length: {app.config.get('MAX_CONTENT_LENGTH')}")
        print("=== 服务器启动中... ===")
        
        # 尝试启动服务器
        app.run(host="0.0.0.0", port=1324, debug=True)
    except Exception as e:
        print(f"=== 服务器启动失败 ===")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        print("错误堆栈:")
        import traceback
        traceback.print_exc()