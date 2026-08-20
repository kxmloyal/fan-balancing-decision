#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WSGI 入口 — 扇叶平衡补土转速评估工具
Gunicorn 生产入口，同时支持 python wsgi.py 开发运行
"""

import json
import logging
import os
import secrets
import stat
import sys
import threading
import time
import traceback

# ═══════ 最早期的环境设置，必须在其他导入之前 ═══════
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_config"

try:
    from dotenv import load_dotenv

    _env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(_env_file):
        load_dotenv(_env_file)
except ImportError:
    pass

import matplotlib

matplotlib.use("Agg")

# 确保项目根目录在 Python 路径中
_current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _current_dir)

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect

from config import BASE_CONFIG

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    _limiter_available = True
except ImportError:
    _limiter_available = False

# ═══════ 日志配置 ═══════
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ═══════ Flask 应用创建 ═══════
BASE_DIR = os.path.abspath(_current_dir)
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, BASE_CONFIG.get("STATIC_FOLDER", "static")),
    static_url_path=BASE_CONFIG.get("STATIC_URL_PATH", "/static"),
    template_folder=os.path.join(BASE_DIR, "templates"),
)

application = app

# ═══════ 安全配置 ═══════
_secret = os.environ.get("SECRET_KEY")
if not _secret:
    # 从文件读取持久化密钥，确保多 worker 共享（否则 CSRF/session 将乱套）
    _key_file = os.path.join(BASE_DIR, "flask_session_new", ".secret_key")
    try:
        if os.path.exists(_key_file):
            with open(_key_file, "r") as f:
                _secret = f.read().strip()
            if not _secret:
                raise ValueError("密钥文件为空")
        else:
            _secret = secrets.token_hex(32)
            os.makedirs(os.path.dirname(_key_file), exist_ok=True)
            with open(_key_file, "w") as f:
                f.write(_secret)
            os.chmod(_key_file, 0o600)
            logger.info("已生成持久化 SECRET_KEY 到 %s", _key_file)
    except (IOError, ValueError) as e:
        _secret = secrets.token_hex(32)
        logger.error("读取/生成密钥文件失败(%s)，使用临时密钥（多 worker 将不可用）", e)
app.config["SECRET_KEY"] = _secret
os.environ["SECRET_KEY"] = _secret  # 同步到环境变量，供 crypto_utils 在无 Flask 上下文时使用

# CRYPTO_SALT — 密码加密盐值（必须配置，不允许默认值）
_crypto_salt = os.environ.get("CRYPTO_SALT")
if not _crypto_salt:
    _salt_file = os.path.join(BASE_DIR, "flask_session_new", ".crypto_salt")
    try:
        if os.path.exists(_salt_file):
            with open(_salt_file, "r") as f:
                _crypto_salt = f.read().strip()
            if not _crypto_salt:
                raise ValueError("加密盐文件为空")
        else:
            _crypto_salt = secrets.token_hex(16)
            os.makedirs(os.path.dirname(_salt_file), exist_ok=True)
            with open(_salt_file, "w") as f:
                f.write(_crypto_salt)
            os.chmod(_salt_file, 0o600)
            logger.info("已生成持久化 CRYPTO_SALT 到 %s", _salt_file)
    except (IOError, ValueError) as e:
        _crypto_salt = secrets.token_hex(16)
        logger.error("读取/生成加密盐文件失败(%s)，使用临时盐值", e)
os.environ["CRYPTO_SALT"] = _crypto_salt

app.config["SESSION_TYPE"] = "filesystem"
app.config["PERMANENT_SESSION_LIFETIME"] = 3600
# 会话目录支持环境变量覆盖：开发/测试服务器必须与生产隔离（避免权限冲突）
app.config["SESSION_FILE_DIR"] = os.environ.get("SESSION_FILE_DIR") or os.path.join(
    BASE_DIR, "flask_session_new"
)

session_dir = app.config["SESSION_FILE_DIR"]
os.makedirs(session_dir, exist_ok=True)
# session 目录权限设为 777，避免 gunicorn master(root) 创建后 worker(www) 无法写入
try:
    os.chmod(session_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
except (PermissionError, OSError):
    pass  # 非所有者运行时不强制修改权限

# 修复历史遗留的异常 session 文件（属主 www:root 权限 600，导致 CSRF token 丢失）
# 删除这些文件让用户重新获取 session，而非尝试 chown（需要 root 权限）
for _fname in os.listdir(session_dir):
    if _fname.startswith("."):
        continue
    _fpath = os.path.join(session_dir, _fname)
    try:
        _st = os.stat(_fpath)
        # 权限不是 666/777 或组不是 www，则删除重建
        if _st.st_gid != os.stat(session_dir).st_gid or not (_st.st_mode & stat.S_IWGRP):
            os.remove(_fpath)
    except (PermissionError, OSError):
        pass

app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
app.config["OUTPUT_FOLDER"] = os.path.join(BASE_DIR, "outputs")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB
app.config["ALLOWED_EXTENSIONS"] = {"csv", "xlsx", "xls", "json", "xml", "txt"}


def _build_sqlalchemy_uri(conn):
    """从连接字典构建 SQLAlchemy URI（含 URL 编码，防止密码特殊字符导致 URI 解析错误）"""
    from urllib.parse import quote_plus as _qp

    db_type = conn.get("type", "").lower()
    host = conn.get("host", "")
    port = conn.get("port", "")
    user = conn.get("username", conn.get("user", ""))
    password = conn.get("password", "")
    database = conn.get("database", conn.get("name", ""))

    if password:
        try:
            from app.utils.crypto_utils import decrypt_password

            password = decrypt_password(password)
        except Exception as _e:
            logger.warning("数据库密码解密失败，将使用原始值尝试连接: %s", _e)

    _enc_user = _qp(user) if user else ""
    _enc_pass = _qp(password) if password else ""

    if db_type == "mysql":
        return f"mysql+pymysql://{_enc_user}:{_enc_pass}@{host}:{port}/{database}?charset=utf8mb4"
    elif db_type == "postgresql":
        return f"postgresql://{_enc_user}:{_enc_pass}@{host}:{port}/{database}"
    else:
        return f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"


def _load_db_uri_from_connections():
    """从 connection_configs.json 获取主数据库连接 URI（优先 is_primary）"""
    conn_file = os.path.join(BASE_DIR, "data", "connection_configs.json")
    try:
        if os.path.exists(conn_file):
            with open(conn_file, "r", encoding="utf-8") as f:
                connections = json.load(f)
            for conn in connections:
                if conn.get("is_primary"):
                    return _build_sqlalchemy_uri(conn)
            if connections:
                return _build_sqlalchemy_uri(connections[0])
    except (IOError, ValueError, KeyError) as e:
        logger.warning("读取连接配置失败: %s", str(e))
    return None


def _load_db_uri_from_legacy_config():
    """fallback: 从旧版 config/db_config.json 读取连接"""
    try:
        from utils.config_manager import config_manager

        return config_manager.get_sqlalchemy_uri()
    except Exception as e:
        logger.warning("读取旧版db_config.json失败: %s", str(e))
    return None


db_uri = _load_db_uri_from_connections()
if not db_uri:
    db_uri = _load_db_uri_from_legacy_config()
if not db_uri:
    db_uri = os.environ.get(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///" + os.path.join(BASE_DIR, "app.db")
    )
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
# SQLAlchemy 连接池优化 — 减少频繁建连开销
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": 10,          # 持久连接数
    "max_overflow": 20,       # 突发时额外连接
    "pool_pre_ping": True,    # 使用前检测连接活性，避免 stale connection 报错
    "pool_recycle": 1800,     # 30 分钟回收，防止 MySQL wait_timeout 断连
}

# ═══════ CSRF 保护 ═══════
csrf = CSRFProtect(app)
app.config["WTF_CSRF_HEADERS"] = ["X-CSRFToken"]

# ═══════ HTTP 安全头 ═══════
try:
    from flask_talisman import Talisman

    _talisman_kwargs = {
        "force_https": False,  # 生产环境由反向代理处理 HTTPS
        "session_cookie_secure": True,
        "session_cookie_http_only": True,
        "session_cookie_samesite": "Lax",
        "frame_options": "DENY",
        "frame_options_allow_from": None,
        "strict_transport_security": True,
        "strict_transport_security_max_age": 31536000,
        "strict_transport_security_include_subdomains": True,
        "content_security_policy": {
            "default-src": ["'self'"],
            "script-src": [
                "'self'",
                "'unsafe-inline'",
                "'unsafe-eval'",
                "https://cdn.plot.ly",
                "https://cdn.jsdelivr.net",
            ],
            "style-src": [
                "'self'",
                "'unsafe-inline'",
                "https://cdn.jsdelivr.net",
                "https://cdn.plot.ly",
            ],
            "img-src": ["'self'", "data:", "blob:"],
            "font-src": ["'self'", "https://cdn.jsdelivr.net"],
            "connect-src": ["'self'"],
            "frame-src": ["'self'", "blob:"],
            "object-src": ["'none'"],
        },
        "content_security_policy_nonce_in": [],
    }
    Talisman(app, **_talisman_kwargs)
    logger.info("flask-talisman 安全头已启用（CSP/HSTS/X-Frame-Options/X-Content-Type-Options）")
except ImportError:
    logger.warning("flask-talisman 未安装，HTTP 安全头未启用。请运行: pip install flask-talisman")
except Exception as e:
    logger.warning("flask-talisman 初始化失败: %s", e)

# ═══════ API 速率限制 ═══════
if _limiter_available:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )
else:
    limiter = None

# ═══════ 模板与静态文件配置 ═══════
# 仅 debug 模式开启模板自动重载，生产环境关闭以避免每请求 stat() I/O
_debug_mode = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")
app.config["TEMPLATES_AUTO_RELOAD"] = _debug_mode
# 静态文件浏览器缓存 30 天（带版本哈希时可设更长）
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 2592000

# ═══════ 目录创建 ═══════
for _folder in [
    app.config["UPLOAD_FOLDER"],
    app.config["OUTPUT_FOLDER"],
    app.config["SESSION_FILE_DIR"],
    os.path.join(BASE_DIR, "logs"),
    os.path.join(BASE_DIR, "tmp"),
]:
    os.makedirs(_folder, exist_ok=True)

# ═══════ 会话管理 ═══════
try:
    from flask_session import Session

    session_manager = Session()
    session_manager.init_app(app)
    logger.info("flask_session 初始化成功")
except ImportError:
    logger.warning("flask_session 未安装，使用内存会话（生产环境请安装 flask_session）")

    class _MockSession:
        def init_app(self, _app):
            for _f in [
                _app.config.get("UPLOAD_FOLDER", "uploads"),
                _app.config.get("OUTPUT_FOLDER", "outputs"),
                _app.config.get("SESSION_FILE_DIR", "flask_session_new"),
            ]:
                os.makedirs(_f, exist_ok=True)

    _MockSession().init_app(app)

# ═══════ 核心服务初始化 ═══════
from app.utils.error_handler import error_handler
from app.utils.file_manager import file_manager
from db_models import init_db
from report_exporter_extension import ReportExporter

file_manager.init_app(app)
error_handler.init_app(app)
init_db(app)

# ═══════ 数据库迁移 ═══════
try:
    from flask_migrate import Migrate

    from db_models import db as _app_db

    if _app_db is not None:
        migrate = Migrate(app, _app_db)
        logger.info("Flask-Migrate 数据库迁移已启用")
    else:
        logger.warning("数据库未连接，Flask-Migrate 未启用")
except ImportError:
    logger.warning("Flask-Migrate 未安装，数据库迁移不可用")
except Exception as e:
    logger.warning("Flask-Migrate 初始化失败: %s", e)

try:
    report_exporter = ReportExporter(app=app)
    logger.info("报告导出器初始化成功")
except Exception:
    logger.warning("报告导出器初始化失败，导出功能可能不可用", exc_info=True)

# ═══════ 定时任务（APScheduler） ═══════
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=lambda: file_manager.clean_old_files(days=7),
    trigger="cron",
    hour=2,
    minute=0,
    id="clean_old_files",
    name="清理7天前的文件",
    replace_existing=True,
)
try:
    scheduler.start()
    logger.info("APScheduler 定时任务已启动")
except Exception:
    logger.warning("APScheduler 启动失败，定时清理不可用", exc_info=True)


# ═══════ 蓝图导入与注册 ═══════
def _register_blueprints(app):
    """注册所有蓝图，可独立测试"""
    logger.info("正在导入蓝图...")
    try:
        from blueprints.analysis_bp import analysis_bp
        from blueprints.main_bp import main_bp
        from blueprints.ml_bp import ml_bp
        from blueprints.model_monitor_bp import model_monitor_bp
        from blueprints.outputs_bp import outputs_bp
        from blueprints.report_bp import report_bp
        from blueprints.settings_bp import settings_bp

        logger.info("蓝图导入成功")
    except Exception:
        logger.error("蓝图导入失败", exc_info=True)
        raise

    app.register_blueprint(main_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(outputs_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(model_monitor_bp)
    logger.info("蓝图注册完成")


_register_blueprints(app)


# ═══════ 核心路由 ═══════
@app.route("/")
def index():
    try:
        return redirect(url_for("main.index"))
    except Exception as e:
        logger.error("根路径重定向失败", exc_info=True)
        return f"服务异常: {str(e)}", 500


@app.route("/health")
def health():
    return "Healthy"


# ═══════ 错误处理 ═══════
@app.errorhandler(404)
def handle_404(error):
    logger.warning("404: %s", str(error))
    return render_template("404.html", error_message="页面不存在，请检查URL是否正确"), 404


@app.errorhandler(500)
def handle_500(error):
    error_trace = traceback.format_exc()
    logger.error(f"500: {error}\n{error_trace}")
    if app.debug:
        return f"500 Internal Server Error: {error}\n{error_trace}", 500
    return render_template("error.html", error_message="服务器内部错误，请稍后重试"), 500


@app.errorhandler(Exception)
def handle_generic_exception(error):
    from flask_wtf.csrf import CSRFError as _CSRFError
    from werkzeug.exceptions import HTTPException

    if isinstance(error, _CSRFError):
        if request.path == "/frontend-analytics":
            return jsonify({"success": False, "message": "分析数据已接收"}), 200
        logger.error("CSRF验证失败: %s", str(error))
        return jsonify({"success": False, "message": "安全验证失败，请刷新页面后重试"}), 400
    if isinstance(error, HTTPException):
        # 405/404/400 等 HTTP 语义异常按原生状态码返回，避免被统一吞成 500
        return error
    logger.error("未捕获异常: %s", str(error), exc_info=True)
    user_friendly = "服务器内部错误，请稍后重试"
    if app.debug:
        user_friendly = getattr(error, "message", str(error))
    if request.headers.get("Accept") and "application/json" in request.headers.get("Accept"):
        body = {"success": False, "message": user_friendly}
        if app.debug:
            body["error_type"] = type(error).__name__
        return jsonify(body), 500
    return render_template("error.html", error_message=user_friendly), 500


# ═══════ 请求钩子 ═══════
_request_count = 0
_cleanup_lock = threading.Lock()


@app.before_request
def before_request():
    """每 100 个请求触发一次后台清理（异步，不阻塞当前请求）"""
    global _request_count
    _request_count += 1
    if _request_count >= 100:
        _request_count = 0
        # 后台线程执行清理，避免阻塞请求
        if not _cleanup_lock.locked():
            threading.Thread(target=_cleanup_stale_files, daemon=True).start()


@app.after_request
def after_request(response):
    # 静态文件长期缓存（nginx 也会处理 gzip，Python 层不再做压缩以减少 CPU 开销）
    if request.path.startswith("/static/"):
        response.cache_control.max_age = 300  # 5 分钟（活跃迭代期防浏览器旧缓存；发布稳定后可调回 2592000）
        response.cache_control.public = True
        response.headers["X-Content-Type-Options"] = "nosniff"
    else:
        # 动态页面禁用缓存：页面含 csrf_token，缓存会导致 reset/session 变更后
        # 浏览器继续使用旧 token 提交表单，触发 "CSRF tokens do not match"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# ═══════ 辅助函数 ═══════
def _cleanup_stale_files():
    """清理上传目录中的陈旧文件（>1小时），加锁防止并发执行"""
    if not _cleanup_lock.acquire(blocking=False):
        return
    try:
        _protected_exts = (".json", ".db", ".sqlite", ".sqlite3", ".ini", ".cfg", ".py")
        _now = time.time()
        for _dir in [app.config["UPLOAD_FOLDER"]]:
            if not os.path.exists(_dir):
                continue
            for _root, _subdirs, _files in os.walk(_dir):
                for _fname in _files:
                    _fpath = os.path.join(_root, _fname)
                    if any(_fname.endswith(ext) for ext in _protected_exts):
                        continue
                    try:
                        if _now - os.path.getmtime(_fpath) > 3600:
                            os.remove(_fpath)
                    except OSError:
                        pass
    except Exception:
        pass
    finally:
        _cleanup_lock.release()


# ═══════ 开发服务器（仅直接运行时生效） ═══════
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1333))
    debug = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)
