#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
设置模块蓝图：包含数据库连接参数配置和管理功能
"""

import logging
import os

logger = logging.getLogger(__name__)

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from database_connections import (
    DatabaseConnection,
    connection_manager,
    connection_tester,
    test_connection_with_timeout,
)
from utils.config_manager import config_manager

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings")
def settings():
    current_config = config_manager.get_db_config()
    face_weights = config_manager.get_face_weights()

    db_types = [
        {"value": "mysql", "label": "MySQL"},
        {"value": "postgresql", "label": "PostgreSQL"},
        {"value": "sqlite", "label": "SQLite"},
    ]

    balancer_models = []
    _BalancerModel, _ = _get_balancer_model_class()
    if _BalancerModel is not None:
        try:
            with current_app.app_context():
                records = _BalancerModel.query.order_by(_BalancerModel.updated_at.desc()).all()
                for m in records:
                    balancer_models.append(
                        {
                            "id": m.id,
                            "model_name": m.model_name,
                            "manufacturer": m.manufacturer or "",
                            "max_speed": m.max_speed or "",
                            "max_radius": m.max_radius or "",
                            "description": m.description or "",
                            "is_active": m.is_active,
                            "created_at": m.created_at.strftime("%Y-%m-%d %H:%M")
                            if m.created_at
                            else "",
                            "updated_at": m.updated_at.strftime("%Y-%m-%d %H:%M")
                            if m.updated_at
                            else "",
                        }
                    )
        except Exception as e:
            current_app.logger.warning("加载平衡机型号列表失败: %s", str(e))

    return render_template(
        "settings.html",
        db_config=current_config,
        db_types=db_types,
        face_weights=face_weights,
        balancer_models=balancer_models,
        active_tab="database",
    )


@settings_bp.route("/test_db_connection", methods=["POST"])
def test_db_connection():
    """测试数据库连接（带超时保护）"""
    try:
        db_type = request.form.get("db_type")
        host = request.form.get("host")
        port = request.form.get("port")
        database = request.form.get("database")
        username = request.form.get("username")
        password = request.form.get("password")

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

        if db_type == "sqlite" and not database:
            database = "data.db"

        connection = DatabaseConnection(
            connection_id=0,
            name="test_connection",
            connection_type=db_type,
            host=host,
            port=int(port) if port else None,
            database=database,
            username=username,
            password=password,
        )

        result = test_connection_with_timeout(connection)

        pool_status = _get_connection_pool_status()

        if result["success"]:
            return jsonify(
                {"success": True, "message": "连接测试成功！", "pool_status": pool_status}
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "message": "连接测试失败：{}".format(result.get("message", "未知错误")),
                    "pool_status": pool_status,
                }
            )

    except Exception:
        current_app.logger.error("测试数据库连接出错", exc_info=True)
        return jsonify({"success": False, "message": "连接测试失败，请检查数据库配置"})


@settings_bp.route("/save_db_config", methods=["POST"])
def save_db_config():
    """保存数据库连接配置（同步写入 config_manager + connection_manager）

    修复要点：
    - 密码掩码 "********" 检测：复用旧密码，不覆盖
    - 防止双重加密：encrypt_password 已内置前缀检测
    - 重载失败 → flash 通知用户
    """
    try:
        db_type = request.form.get("db_type")
        host = request.form.get("host")
        port = request.form.get("port")
        database = request.form.get("database")
        username = request.form.get("username")
        password = request.form.get("password")
        name = request.form.get("name", "").strip()
        connection_id_str = request.form.get("connection_id", "").strip()
        save_method = request.form.get("save_method", "file")

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

        if db_type == "sqlite" and not database:
            database = "data.db"
        if not name:
            name = f"{db_type}_{host or 'local'}_{database}"

        # 密码掩码检测：前端表单密码域显示 "********" 表示用户未修改密码
        # 此时应从已有连接中复用旧密码，避免覆盖为无效值
        existing_conn = None
        conn_id_int = 0
        if connection_id_str and connection_id_str.isdigit():
            conn_id_int = int(connection_id_str)
            existing_conn = connection_manager.get_connection(conn_id_int)

        if password in ("********", "") and existing_conn is not None:
            password = existing_conn.password

        config = {
            "db_type": db_type,
            "host": host,
            "port": port,
            "database": database,
            "username": username,
            "password": password,
        }

        success = config_manager.save_db_config(config, save_method)

        _port_int = int(port) if port else None
        conn = DatabaseConnection(
            connection_id=conn_id_int,
            name=name,
            connection_type=db_type,
            host=host,
            port=_port_int,
            database=database,
            username=username,
            password=password,
            is_primary=True,
        )

        if connection_id_str and connection_id_str.isdigit():
            try:
                if existing_conn:
                    connection_manager.update_connection(conn)
                    flash("数据库连接配置更新成功！" if success else "连接配置已更新（系统配置保存异常）", "success" if success else "warning")
                else:
                    connection_manager.add_connection(conn)
                    flash("数据库连接配置保存成功！" if success else "数据库连接配置已保存（系统配置保存异常）", "success" if success else "warning")
            except ValueError:
                flash("无效的连接ID", "error")
        else:
            connection_manager.add_connection(conn)
            flash("数据库连接配置保存成功！" if success else "数据库连接配置已保存（系统配置保存异常）", "success" if success else "warning")

        # 将该连接设为主连接，其余取消主连接标记
        for c in connection_manager.get_all_connections():
            if c.id != conn.id:
                c.is_primary = False
        connection_manager._save_configs()

        # 自动重载数据库连接（切换数据库后无需重启应用）
        reload_ok = False
        try:
            from urllib.parse import quote_plus as _qp
            from sqlalchemy import text as _sa_text

            from db_models import db as _app_db

            _db_type = conn.type.lower()
            _enc_user = _qp(conn.username or "")
            _enc_pass = _qp(conn.password or "")
            if _db_type == "mysql":
                _uri = (
                    f"mysql+pymysql://{_enc_user}:{_enc_pass}"
                    f"@{conn.host}:{conn.port}/{conn.database}?charset=utf8mb4"
                )
            elif _db_type == "postgresql":
                _uri = (
                    f"postgresql://{_enc_user}:{_enc_pass}"
                    f"@{conn.host}:{conn.port}/{conn.database}"
                )
            else:
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                _uri = f"sqlite:///{os.path.join(BASE_DIR, conn.database or 'app.db')}"
            current_app.config["SQLALCHEMY_DATABASE_URI"] = _uri
            # 清除 flask_sqlalchemy 引擎缓存，强制用新 URI 创建引擎
            if _app_db is not None:
                _app_db.engine.dispose()
                if hasattr(_app_db, '_app_engines'):
                    _app = current_app._get_current_object()
                    _app_db._app_engines.get(_app, {}).pop(None, None)
            with current_app.app_context():
                _app_db.session.execute(_sa_text("SELECT 1"))
            reload_ok = True
            # 更新全局数据库状态标志，让状态面板反映最新连接状态
            try:
                import db_models
                db_models.DB_CONNECTED = True
                db_models.DB_ERROR_MESSAGE = ""
            except Exception:
                pass
            current_app.logger.info("数据库连接已自动切换到 %s", conn.name)
        except Exception as _re:
            current_app.logger.warning("自动重载数据库连接失败: %s", str(_re))
            flash(f"数据库连接已保存，但自动切换失败：{_re}", "warning")

    except Exception:
        current_app.logger.error("保存配置时出现错误", exc_info=True)
        flash("保存配置时出现错误，请稍后重试", "error")

    return redirect(url_for("settings.settings"))


@settings_bp.route("/load_db_config")
def load_db_config():
    try:
        config = config_manager.get_db_config()
        if config and "password" in config and config["password"]:
            config["password"] = "********"
        return jsonify({"success": True, "config": config})
    except Exception:
        current_app.logger.error("加载配置时出现错误", exc_info=True)
        return jsonify({"success": False, "message": "加载配置时出现错误，请稍后重试"})


@settings_bp.route("/reset_db_config")
def reset_db_config():
    """重置数据库连接配置"""
    try:
        success = config_manager.reset_db_config()
        if success:
            flash("数据库连接配置已重置", "success")
        else:
            flash("重置配置失败", "error")
    except Exception:
        current_app.logger.error("重置配置时出现错误", exc_info=True)
        flash("重置配置时出现错误，请稍后重试", "error")

    return redirect(url_for("settings.settings"))


@settings_bp.route("/database_connections", methods=["POST"])
def delete_database_connection():
    """删除已保存的数据库连接配置"""
    action = request.form.get("action")
    if action == "delete":
        connection_id = request.form.get("connection_id")
        if connection_id:
            try:
                if connection_manager.delete_connection(int(connection_id)):
                    return jsonify({"success": True, "message": "连接配置已删除"})
                else:
                    return jsonify({"success": False, "error": "连接配置删除失败"})
            except ValueError:
                return jsonify({"success": False, "error": "无效的连接ID"})
    return jsonify({"success": False, "error": "无效的操作"})


@settings_bp.route("/test_connection", methods=["POST"])
def test_connection():
    """测试数据库连接（跨平台带超时保护）"""
    try:
        name = request.form.get("connection_name")
        connection_type = request.form.get("connection_type")
        host = request.form.get("host")
        port = request.form.get("port", type=int) if request.form.get("port") else None
        database = request.form.get("database")
        username = request.form.get("username")
        password = request.form.get("password")

        if not name or not connection_type or not host:
            return jsonify({"success": False, "message": "连接名称、类型和主机不能为空！"})

        if port is not None and (not isinstance(port, int) or port <= 0 or port > 65535):
            return jsonify({"success": False, "message": "端口号必须是有效的整数（1-65535）！"})

        connection = DatabaseConnection(
            connection_id=0,
            name=name,
            connection_type=connection_type,
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
        )

        result = test_connection_with_timeout(connection)

        if result.get("success"):
            connection.status = "active"

        pool_status = {
            "total_connections": len(connection_manager.get_all_connections()),
            "cached_connections": len(connection_tester._connection_cache)
            if hasattr(connection_tester, "_connection_cache")
            else 0,
        }

        return jsonify(
            {
                "success": result.get("success", False),
                "message": result.get("message", "未知错误"),
                "pool_status": pool_status,
            }
        )
    except (ValueError, TypeError, OSError):
        return jsonify({"success": False, "message": "连接测试失败，请检查配置参数"})


@settings_bp.route("/get_connection")
def get_connection():
    """获取连接详情"""
    connection_id = request.args.get("id", type=int)
    if not connection_id:
        return jsonify({"success": False, "message": "连接ID不能为空"})

    connection = connection_manager.get_connection(connection_id)
    if not connection:
        return jsonify({"success": False, "message": "连接配置不存在"})

    return jsonify({"success": True, "connection": connection.to_dict()})


@settings_bp.route("/face_weights")
def get_face_weights():
    """获取端面权重配置"""
    weights = config_manager.get_face_weights()
    return jsonify({"success": True, "weights": weights})


@settings_bp.route("/save_face_weights", methods=["POST"])
def save_face_weights():
    """保存端面权重配置"""
    try:
        data = request.get_json(force=True)
        if data is None:
            data = request.form.to_dict()
        weights = {
            "P1": float(data.get("P1", 0.4)),
            "P2": float(data.get("P2", 0.4)),
            "ST": float(data.get("ST", 0.2)),
        }
        for key, val in weights.items():
            if val < 0 or val > 1:
                return jsonify({"success": False, "message": f"{key}端面权重必须在0-1之间"})
        success = config_manager.save_face_weights(weights)
        if success:
            return jsonify({"success": True, "message": "权重配置已保存", "weights": weights})
        else:
            return jsonify({"success": False, "message": "保存失败，请检查文件权限"})
    except (ValueError, TypeError) as e:
        return jsonify({"success": False, "message": f"权重值格式错误: {str(e)}"})


@settings_bp.route("/reset_face_weights")
def reset_face_weights():
    """重置端面权重为默认经验值"""
    success = config_manager.reset_face_weights()
    if success:
        default_weights = config_manager.get_face_weights()
        return jsonify(
            {"success": True, "message": "权重已重置为默认经验值", "weights": default_weights}
        )
    else:
        return jsonify({"success": False, "message": "重置失败，请检查文件权限"})


def _get_balancer_model_class():
    """获取 BalancerModel 类及 SQLAlchemy db 实例

    优先使用 init_db 设置的全局变量。如果 init_db 未成功运行
    （全局为 None），则尝试从已存在的 db 实例动态构建模型类。
    """
    from db_models import BalancerModel
    from db_models import db as _app_db

    if BalancerModel is not None:
        return BalancerModel, _app_db
    if _app_db is not None:
        try:
            from db_models import define_models

            models = define_models(_app_db)
            for _m in models:
                if getattr(_m, "__tablename__", None) == "balancer_models":
                    return _m, _app_db
        except Exception:
            pass
    return None, None


@settings_bp.route("/api/balancer_models", methods=["GET"])
def api_list_balancer_models():
    _BalancerModel, _ = _get_balancer_model_class()
    if _BalancerModel is None:
        return jsonify({"success": False, "message": "数据库未连接"})
    try:
        with current_app.app_context():
            records = _BalancerModel.query.order_by(_BalancerModel.updated_at.desc()).all()
            result = []
            for m in records:
                result.append(
                    {
                        "id": m.id,
                        "model_name": m.model_name,
                        "manufacturer": m.manufacturer or "",
                        "max_speed": m.max_speed or "",
                        "max_radius": m.max_radius or "",
                        "description": m.description or "",
                        "is_active": m.is_active,
                        "created_at": m.created_at.strftime("%Y-%m-%d %H:%M")
                        if m.created_at
                        else "",
                        "updated_at": m.updated_at.strftime("%Y-%m-%d %H:%M")
                        if m.updated_at
                        else "",
                    }
                )
            return jsonify({"success": True, "data": result})
    except Exception as e:
        current_app.logger.error("获取平衡机型号列表失败: %s", str(e))
        return jsonify({"success": False, "message": "获取型号列表失败"})


@settings_bp.route("/api/balancer_models", methods=["POST"])
def api_create_balancer_model():
    _BalancerModel, _app_db = _get_balancer_model_class()
    if _BalancerModel is None or _app_db is None:
        return jsonify({"success": False, "message": "数据库未连接"})
    try:
        data = request.get_json()
        if not data or not data.get("model_name", "").strip():
            return jsonify({"success": False, "message": "型号名称不能为空"})
        model_name = data["model_name"].strip()
        existing = _BalancerModel.query.filter_by(model_name=model_name).first()
        if existing:
            return jsonify({"success": False, "message": "型号名称已存在"})
        m = _BalancerModel(
            model_name=model_name,
            manufacturer=data.get("manufacturer", "").strip() or None,
            max_speed=data.get("max_speed", "").strip() or None,
            max_radius=data.get("max_radius", "").strip() or None,
            description=data.get("description", "").strip() or None,
            is_active=data.get("is_active", True),
        )
        _app_db.session.add(m)
        _app_db.session.commit()
        return jsonify({"success": True, "message": "型号添加成功", "id": m.id})
    except Exception as e:
        _app_db.session.rollback()
        current_app.logger.error("添加平衡机型号失败: %s", str(e))
        return jsonify({"success": False, "message": "添加失败"})


@settings_bp.route("/api/balancer_models/<int:model_id>", methods=["PUT"])
def api_update_balancer_model(model_id):
    _BalancerModel, _app_db = _get_balancer_model_class()
    if _BalancerModel is None or _app_db is None:
        return jsonify({"success": False, "message": "数据库未连接"})
    try:
        data = request.get_json()
        m = _BalancerModel.query.get(model_id)
        if not m:
            return jsonify({"success": False, "message": "型号不存在"})
        if "model_name" in data:
            new_name = data["model_name"].strip()
            if not new_name:
                return jsonify({"success": False, "message": "型号名称不能为空"})
            existing = _BalancerModel.query.filter(
                _BalancerModel.model_name == new_name, _BalancerModel.id != model_id
            ).first()
            if existing:
                return jsonify({"success": False, "message": "型号名称已存在"})
            m.model_name = new_name
        if "manufacturer" in data:
            m.manufacturer = data["manufacturer"].strip() or None
        if "max_speed" in data:
            m.max_speed = data["max_speed"].strip() or None
        if "max_radius" in data:
            m.max_radius = data["max_radius"].strip() or None
        if "description" in data:
            m.description = data["description"].strip() or None
        if "is_active" in data:
            m.is_active = bool(data["is_active"])
        _app_db.session.commit()
        return jsonify({"success": True, "message": "型号更新成功"})
    except Exception as e:
        _app_db.session.rollback()
        current_app.logger.error("更新平衡机型号失败: %s", str(e))
        return jsonify({"success": False, "message": "更新失败"})


@settings_bp.route("/api/balancer_models/<int:model_id>", methods=["DELETE"])
def api_delete_balancer_model(model_id):
    _BalancerModel, _app_db = _get_balancer_model_class()
    if _BalancerModel is None or _app_db is None:
        return jsonify({"success": False, "message": "数据库未连接"})
    try:
        m = _BalancerModel.query.get(model_id)
        if not m:
            return jsonify({"success": False, "message": "型号不存在"})
        _app_db.session.delete(m)
        _app_db.session.commit()
        return jsonify({"success": True, "message": "型号已删除"})
    except Exception as e:
        _app_db.session.rollback()
        current_app.logger.error("删除平衡机型号失败: %s", str(e))
        return jsonify({"success": False, "message": "删除失败"})


@settings_bp.route("/api/db_status")
def api_db_status():
    """获取数据库整体连接状态 — 供前端状态面板使用"""
    status = {
        "main_db": _get_main_db_status(),
        "saved_connections": _get_saved_connections_status(),
        "pool_status": _get_connection_pool_status(),
    }
    return jsonify({"success": True, "data": status})


@settings_bp.route("/api/reload_db_connection", methods=["POST"])
def api_reload_db_connection():
    """重新加载数据库连接（切换数据库后无需重启应用）"""
    import os as _os

    try:
        from urllib.parse import quote_plus as _qp
        from sqlalchemy import text as _sa_text

        from db_models import db as _app_db

        # 找到主连接
        conns = connection_manager.get_all_connections()
        primary = None
        for c in conns:
            if c.is_primary:
                primary = c
                break
        if not primary and conns:
            primary = conns[0]

        if not primary:
            return jsonify({"success": False, "message": "没有找到可用的数据库连接配置"})

        # 构建 SQLAlchemy URI（URL 编码防止密码特殊字符导致 URI 解析错误）
        db_type = primary.type.lower()
        _enc_user = _qp(primary.username or "")
        _enc_pass = _qp(primary.password or "")
        if db_type == "mysql":
            _uri = (
                f"mysql+pymysql://{_enc_user}:{_enc_pass}"
                f"@{primary.host}:{primary.port}/{primary.database}?charset=utf8mb4"
            )
        elif db_type == "postgresql":
            _uri = (
                f"postgresql://{_enc_user}:{_enc_pass}"
                f"@{primary.host}:{primary.port}/{primary.database}"
            )
        else:
            base_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
            _uri = f"sqlite:///{_os.path.join(base_dir, primary.database or 'app.db')}"

        current_app.config["SQLALCHEMY_DATABASE_URI"] = _uri

        # 释放旧连接池 + 清除引擎缓存，后续查询将使用新 URI
        if _app_db is not None:
            _app_db.engine.dispose()
            if hasattr(_app_db, '_app_engines'):
                _app = current_app._get_current_object()
                _app_db._app_engines.get(_app, {}).pop(None, None)

        # 告之 Session 原会话可能失效
        import db_models as _dm

        _msg = f"数据库连接已切换到 {primary.name} ({primary.type}@{primary.host})"
        try:
            with current_app.app_context():
                _app_db.session.execute(_sa_text("SELECT 1"))
            # 更新全局数据库状态标志
            _dm.DB_CONNECTED = True
            _dm.DB_ERROR_MESSAGE = ""
            logger.info(_msg)
            return jsonify({"success": True, "message": _msg + " — 连接验证通过"})
        except Exception as e:
            logger.warning("新连接验证失败: %s", str(e))
            return jsonify({"success": True, "message": _msg + f" (验证未通过: {str(e)})"})
    except Exception as e:
        current_app.logger.error("重载数据库连接失败: %s", str(e))
        return jsonify({"success": False, "message": f"重载失败: {str(e)}"})


def _sanitize_db_error(raw_error: str) -> str:
    """清洗数据库错误消息，去除 SQLAlchemy/pymysql 冗长堆栈信息

    将 (pymysql.err.OperationalError) (1045, "Access denied...")
    转换为 MySQL连接失败 (1045): Access denied for user 'zs'@'...'
    """
    if not raw_error:
        return ""
    import re

    # 匹配 pymysql 错误码和消息
    match = re.search(r"\(pymysql\.err\.\w+\)\s*\((\d+),\s*\"([^\"]+)\"", raw_error)
    if match:
        code, msg = match.group(1), match.group(2)
        return f"MySQL连接失败 ({code}): {msg}"

    # 匹配 psycopg2 错误
    match = re.search(r"\(psycopg2\.\w+\)\s*(.+)", raw_error, re.DOTALL)
    if match:
        return f"PostgreSQL连接失败: {match.group(1).strip().split(chr(10))[0]}"

    # 匹配 sqlite3 错误
    match = re.search(r"\(sqlite3\.\w+\)\s*(.+)", raw_error, re.DOTALL)
    if match:
        return f"SQLite连接失败: {match.group(1).strip().split(chr(10))[0]}"

    # 通用清理：去掉 SQLAlchemy help URL 后缀
    raw_error = re.sub(r"\s*\(Background on this error at:.*?\)", "", raw_error)
    if len(raw_error) > 200:
        raw_error = raw_error[:200] + "…"
    return raw_error.strip()


def _get_main_db_status():
    """获取主数据库（SQLAlchemy）连接状态"""
    try:
        from sqlalchemy import text as _sa_text

        from db_models import DB_CONNECTED, DB_ERROR_MESSAGE
        from db_models import db as _global_db

        # 清洗 DB_ERROR_MESSAGE：去掉 SQLAlchemy/pymysql 冗长堆栈信息
        _sanitized_error = _sanitize_db_error(DB_ERROR_MESSAGE or "")

        status = {
            "connected": bool(DB_CONNECTED),
            "error": _sanitized_error or None,
        }

        # 从 URI 推断数据库类型
        _uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if _uri.startswith("mysql"):
            status["db_type"] = "MySQL"
        elif _uri.startswith("postgresql"):
            status["db_type"] = "PostgreSQL"
        elif _uri.startswith("sqlite"):
            status["db_type"] = "SQLite"
        else:
            status["db_type"] = "未知"
        if DB_CONNECTED and _global_db is not None:
            try:
                with current_app.app_context():
                    _global_db.session.execute(_sa_text("SELECT 1"))
                    status["responsive"] = True
            except Exception as e:
                status["responsive"] = False
                status["latency_error"] = str(e)
        else:
            status["responsive"] = False
        return status
    except Exception as e:
        return {"connected": False, "responsive": False, "error": str(e)}


def _get_saved_connections_status():
    """获取所有已保存连接的摘要状态"""
    try:
        connections = connection_manager.get_all_connections()
        result = []
        for conn in connections:
            result.append(
                {
                    "id": conn.id,
                    "name": conn.name,
                    "type": conn.type,
                    "host": conn.host,
                    "status": conn.status,
                    "updated_at": conn.updated_at,
                }
            )
        return result
    except Exception as e:
        return {"error": str(e)}


def _get_connection_pool_status():
    """获取连接池/缓存状态"""
    try:
        cached_count = len(connection_tester._connection_cache)
        config_count = len(connection_manager.get_all_connections())
        return {
            "available": True,
            "total_connections": config_count,
            "cached_connections": cached_count,
        }
    except Exception as e:
        return {
            "available": False,
            "total_connections": 0,
            "cached_connections": 0,
            "error": str(e),
        }


@settings_bp.route("/api/connection_health", methods=["POST"])
def api_connection_health():
    """对单条已保存连接执行健康检查"""
    try:
        connection_id = request.form.get("connection_id", type=int)
        if not connection_id:
            return jsonify({"success": False, "message": "连接ID不能为空"})

        conn = connection_manager.get_connection(connection_id)
        if not conn:
            return jsonify({"success": False, "message": "连接配置不存在"})

        result = test_connection_with_timeout(conn, timeout=5)
        if result.get("success"):
            conn.status = "active"
            return jsonify(
                {
                    "success": True,
                    "message": "连接正常",
                    "latency": result.get("latency"),
                    "status": "active",
                }
            )
        else:
            conn.status = "error"
            return jsonify(
                {
                    "success": False,
                    "message": result.get("message", "连接失败"),
                    "status": "error",
                }
            )
    except Exception as e:
        current_app.logger.error("连接健康检查失败: %s", str(e))
        return jsonify({"success": False, "message": "健康检查异常", "status": "error"})


@settings_bp.route("/api/clear_connection_cache", methods=["POST"])
def api_clear_connection_cache():
    """清除连接测试缓存，强制下次测试重新连接"""
    try:
        connection_tester.clear_cache()
        return jsonify({"success": True, "message": "连接缓存已清除"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
