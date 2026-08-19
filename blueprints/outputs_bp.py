#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
输出文件蓝图：包含输出文件管理功能
"""

import hashlib
import io
import json
import logging
import os
import zipfile
from datetime import datetime
from urllib.parse import quote

import pandas as pd
from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
)

from app.utils.api_response import ApiResponse
from app.utils.cache_utils import file_cache, query_cache

_db_resources = None


def _get_db_resources():
    global _db_resources
    if _db_resources is None:
        try:
            from app import db as _db
            from db_models import DB_CONNECTED
            from db_models import Output as _Output

            if not DB_CONNECTED:
                _db_resources = (None, None)
            else:
                _db_resources = (_db, _Output)
        except Exception:
            _db_resources = (None, None)
    return _db_resources


logger = logging.getLogger(__name__)

outputs_bp = Blueprint("outputs", __name__)

INTERNAL_METADATA_FILES = frozenset(
    {
        "export_history.json",
        "shareable_links.json",
    }
)


def validate_filename(filename):
    if not filename:
        return False
    if ".." in filename or "/" in filename or "\\" in filename:
        return False
    if filename.startswith("."):
        return False
    return True


def _detect_fan_model_from_path(file_path, filename, history_cache=None):
    parent_dir = os.path.basename(os.path.dirname(file_path))
    if parent_dir and parent_dir != os.path.basename(
        os.path.dirname(os.path.dirname(file_path)) or ""
    ):
        if parent_dir not in ("outputs", "output", "static", "templates"):
            return parent_dir

    try:
        if history_cache is not None:
            records = history_cache
        else:
            output_folder = current_app.config.get("OUTPUT_FOLDER", "outputs")
            history_file = os.path.join(output_folder, "export_history.json")
            if not os.path.exists(history_file):
                records = []
            else:
                with open(history_file, "r", encoding="utf-8") as f:
                    records = json.load(f)

        for record in records:
            if record.get("filename") == filename or record.get("path", "").endswith(filename):
                return record.get("fan_model")
    except RuntimeError:
        pass
    except Exception as e:
        logger.warning("检测fan_model失败: %s", str(e))

    chinese_keywords = ["动平衡分析报告", "统计数据", "分析数据", "分析报告"]
    for kw in chinese_keywords:
        marker = "_{}_".format(kw)
        if marker in filename:
            prefix = filename.split(marker)[0]
            if prefix and not prefix.replace("-", "").replace(".", "").isdigit():
                return prefix

    known_models = _get_known_model_names()
    filename_lower = filename.lower()
    for model_name in known_models:
        if model_name.lower() in filename_lower:
            return model_name

    return None


def _get_known_model_names():
    try:
        output_folder = current_app.config.get("OUTPUT_FOLDER", "outputs")
        if not os.path.exists(output_folder):
            return []
        models = []
        for entry in os.listdir(output_folder):
            entry_path = os.path.join(output_folder, entry)
            if (
                os.path.isdir(entry_path)
                and not entry.startswith(".")
                and entry not in ("export_history.json",)
            ):
                models.append(entry)
        models.sort(key=lambda x: (len(x), x), reverse=True)
        return models
    except Exception:
        return []


def _load_export_history():
    try:
        output_folder = current_app.config.get("OUTPUT_FOLDER", "outputs")
        history_file = os.path.join(output_folder, "export_history.json")
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _list_filesystem_files(filters=None):
    output_folder = current_app.config["OUTPUT_FOLDER"]
    outputs_list = []
    history_records = _load_export_history()

    def _scan_dir(directory, model_name=None):
        if not os.path.exists(directory):
            return
        for entry in os.listdir(directory):
            entry_path = os.path.join(directory, entry)
            if os.path.isdir(entry_path):
                _scan_dir(entry_path, entry)
            elif os.path.isfile(entry_path):
                if model_name is None and entry in INTERNAL_METADATA_FILES:
                    continue
                filename = entry
                file_type = filename.split(".")[-1].lower() if "." in filename else "unknown"
                file_size = os.path.getsize(entry_path)
                created_at = datetime.fromtimestamp(os.path.getctime(entry_path))
                updated_at = datetime.fromtimestamp(os.path.getmtime(entry_path))

                fan_model = model_name or _detect_fan_model_from_path(
                    entry_path, filename, history_records
                )

                outputs_list.append(
                    {
                        "id": hashlib.md5(entry_path.encode()).hexdigest()[:12],
                        "filename": filename,
                        "file_path": entry_path,
                        "file_type": file_type,
                        "file_size": file_size,
                        "status": "completed",
                        "description": None,
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "user_id": None,
                        "fan_model": fan_model,
                        "analysis_type": None,
                        "project_id": None,
                    }
                )

    _scan_dir(output_folder)

    if filters:
        if filters.get("file_type"):
            outputs_list = [o for o in outputs_list if o["file_type"] == filters["file_type"]]
        if filters.get("search"):
            search_term = filters["search"].lower()
            outputs_list = [o for o in outputs_list if search_term in o["filename"].lower()]

    outputs_list.sort(key=lambda x: x["updated_at"], reverse=True)
    return outputs_list


def get_output_files(filters=None, page=1, per_page=20):
    """获取outputs文件夹内的所有文件信息，支持筛选和分页

    Args:
        filters: 筛选条件，包含file_type, status, user_id, fan_model, analysis_type,
        project_id等
        page: 当前页码，默认为1
        per_page: 每页显示数量，默认为20

    Returns:
        tuple: (outputs_list, total_count)
    """
    # 检查数据库连接状态
    if current_app.config.get("DATABASE_ERROR"):
        outputs_list = _list_filesystem_files(filters)
        total_count = len(outputs_list)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_list = outputs_list[start:end]

        return paginated_list, total_count

    try:
        _db, Output = _get_db_resources()
        if _db is None or Output is None:
            raise RuntimeError("Database not available")

        sync_outputs_from_filesystem()

        query = Output.query

        if filters:
            if filters.get("file_type"):
                query = query.filter_by(file_type=filters["file_type"])
            if filters.get("status"):
                query = query.filter_by(status=filters["status"])
            if filters.get("user_id"):
                query = query.filter_by(user_id=filters["user_id"])
            if filters.get("fan_model"):
                query = query.filter_by(fan_model=filters["fan_model"])
            if filters.get("analysis_type"):
                query = query.filter_by(analysis_type=filters["analysis_type"])
            if filters.get("project_id"):
                query = query.filter_by(project_id=filters["project_id"])
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    Output.filename.like(search_term) | Output.description.like(search_term)
                )

        query = query.order_by(Output.updated_at.desc())

        total_count = query.count()

        outputs = query.with_entities(
            Output.id,
            Output.filename,
            Output.file_path,
            Output.file_type,
            Output.file_size,
            Output.status,
            Output.description,
            Output.created_at,
            Output.updated_at,
            Output.user_id,
            Output.fan_model,
            Output.analysis_type,
            Output.project_id,
        ).paginate(page=page, per_page=per_page, error_out=False)

        # 转换为前端需要的格式，使用namedtuple而不是dict，提高性能
        outputs_list = []
        for o in outputs.items:
            outputs_list.append(
                {
                    "id": o.id,
                    "filename": o.filename,
                    "file_path": o.file_path,
                    "file_type": o.file_type,
                    "file_size": o.file_size,
                    "status": o.status,
                    "description": o.description,
                    "created_at": o.created_at,
                    "updated_at": o.updated_at,
                    "user_id": o.user_id,
                    "fan_model": o.fan_model,
                    "analysis_type": o.analysis_type,
                    "project_id": o.project_id,
                }
            )

        return outputs_list, total_count
    except Exception as e:
        logger.warning("数据库操作失败: %s，降级为文件系统模式", str(e))
        outputs_list = _list_filesystem_files(filters)
        total_count = len(outputs_list)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_list = outputs_list[start:end]

        return paginated_list, total_count


def sync_outputs_from_filesystem():
    """从文件系统同步导出文件到数据库"""
    output_folder = current_app.config["OUTPUT_FOLDER"]

    if not os.path.exists(output_folder):
        return

    all_files = []

    def _collect_files(directory, model_name=None):
        for entry in os.listdir(directory):
            entry_path = os.path.join(directory, entry)
            if os.path.isdir(entry_path):
                _collect_files(entry_path, entry)
            elif os.path.isfile(entry_path):
                if model_name is None and entry in INTERNAL_METADATA_FILES:
                    continue
                all_files.append((entry, entry_path, model_name))

    _collect_files(output_folder)

    if not all_files:
        return

    try:
        _db, Output = _get_db_resources()
        if _db is None or Output is None:
            return

        existing_files = _db.session.query(Output.filename, Output.file_path).all()
        existing_set = set((f[0], f[1]) for f in existing_files)
        existing_map = {
            (f[0], f[1]): f
            for f in _db.session.query(
                Output.filename, Output.file_path, Output.fan_model, Output.id
            ).all()
        }

        new_records = []
        updates_needed = []
        for filename, file_path, model_name in all_files:
            if model_name is None:
                detected = _detect_fan_model_from_path(file_path, filename)
                if detected:
                    model_name = detected

            if (filename, file_path) not in existing_set:
                file_type = filename.split(".")[-1].lower() if "." in filename else "unknown"
                file_size = os.path.getsize(file_path)
                created_at = datetime.fromtimestamp(os.path.getctime(file_path))
                updated_at = datetime.fromtimestamp(os.path.getmtime(file_path))

                fan_model = model_name

                new_records.append(
                    Output(
                        filename=filename,
                        file_path=file_path,
                        file_type=file_type,
                        file_size=file_size,
                        fan_model=fan_model,
                        status="completed",
                        created_at=created_at,
                        updated_at=updated_at,
                    )
                )
            else:
                existing = existing_map.get((filename, file_path))
                if existing and existing[2] is None and model_name is not None:
                    updates_needed.append((existing[3], model_name))

        if new_records:
            _db.session.add_all(new_records)

        if updates_needed:
            for record_id, fan_model in updates_needed:
                _db.session.query(Output).filter(Output.id == record_id).update(
                    {"fan_model": fan_model}, synchronize_session=False
                )

        if new_records or updates_needed:
            _db.session.commit()
            # 新文件入库后失效相关缓存
            file_cache.clear()
            query_cache.delete("ml_models_db_rows")
            query_cache.delete("outputs_stats")
    except Exception as e:
        logger.warning("同步文件到数据库失败: %s", str(e))


@outputs_bp.route("/outputs")
def outputs():
    """显示outputs列表，支持筛选、搜索和分页"""
    # 获取筛选参数
    filters = {
        "file_type": request.args.get("file_type"),
        "status": request.args.get("status"),
        "fan_model": request.args.get("fan_model"),
        "analysis_type": request.args.get("analysis_type"),
        "search": request.args.get("search"),
    }

    # 获取分页参数
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # 获取outputs列表和总记录数
    output_files, total_count = get_output_files(filters, page, per_page)

    # 获取视图类型参数
    view = request.args.get("view", "list")

    # 获取所有可能的文件类型、状态、扇叶型号和分析类型，用于筛选选项
    filter_options = {
        "file_types": [],
        "statuses": [],
        "fan_models": [],
        "analysis_types": [],
    }

    try:
        _db, Output = _get_db_resources()
        if _db is None or Output is None:
            raise RuntimeError("Database not available")

        file_types = _db.session.query(Output.file_type).distinct().order_by(Output.file_type).all()
        statuses = _db.session.query(Output.status).distinct().order_by(Output.status).all()
        fan_models = (
            _db.session.query(Output.fan_model)
            .filter(Output.fan_model.isnot(None))
            .distinct()
            .order_by(Output.fan_model)
            .all()
        )
        analysis_types = (
            _db.session.query(Output.analysis_type)
            .filter(Output.analysis_type.isnot(None))
            .distinct()
            .order_by(Output.analysis_type)
            .all()
        )

        # 格式化选项列表
        filter_options = {
            "file_types": [ft[0] for ft in file_types],
            "statuses": [s[0] for s in statuses],
            "fan_models": [fm[0] for fm in fan_models if fm[0]],
            "analysis_types": [at[0] for at in analysis_types if at[0]],
        }
    except Exception as e:
        logger.warning("获取筛选选项失败: %s", str(e))

    # 计算总页数
    total_pages = (total_count + per_page - 1) // per_page

    return render_template(
        "outputs.html",
        output_files=output_files,
        view=view,
        filter_options=filter_options,
        filters=filters,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_count=total_count,
    )


@outputs_bp.route("/outputs_stats")
def outputs_stats():
    """返回输出文件统计数据"""
    # 统计数据缓存 60 秒，减少文件系统扫描
    cached_stats = file_cache.get("outputs_stats")
    if cached_stats is not None:
        return jsonify(cached_stats)

    try:
        output_folder = current_app.config["OUTPUT_FOLDER"]
        output_files, _ = get_output_files()

        type_distribution = {}
        status_distribution = {}
        monthly_map = {}
        daily_map = {}
        fan_model_map = {}
        analysis_type_map = {}

        for f in output_files:
            ft = f.get("file_type", "unknown")
            type_distribution[ft] = type_distribution.get(ft, 0) + 1

            st = f.get("status", "unknown")
            status_distribution[st] = status_distribution.get(st, 0) + 1

            fm = f.get("fan_model")
            if fm:
                fan_model_map[fm] = fan_model_map.get(fm, 0) + 1

            at = f.get("analysis_type")
            if at:
                analysis_type_map[at] = analysis_type_map.get(at, 0) + 1

            ct = f.get("created_at")
            if ct:
                month_key = ct.strftime("%Y-%m")
                monthly_map[month_key] = monthly_map.get(month_key, 0) + 1
                date_key = ct.strftime("%Y-%m-%d")
                daily_map[date_key] = daily_map.get(date_key, 0) + 1

        type_data = [{"file_type": k, "count": v} for k, v in type_distribution.items()]
        status_data = [{"status": k, "count": v} for k, v in status_distribution.items()]
        monthly_data = sorted(
            [{"month": k, "count": v} for k, v in monthly_map.items()], key=lambda x: x["month"]
        )
        recent_daily = sorted(
            [{"date": k, "count": v} for k, v in daily_map.items()],
            key=lambda x: x["date"],
            reverse=True,
        )[:30]
        fan_model_data = sorted(
            [{"fan_model": k, "count": v} for k, v in fan_model_map.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]
        analysis_type_data = [
            {"analysis_type": k, "count": v} for k, v in analysis_type_map.items()
        ]

        stats_data = {
            "type": type_data,
            "status": status_data,
            "monthly": monthly_data,
            "recent_daily": recent_daily,
            "fan_model": fan_model_data,
            "analysis_type": analysis_type_data,
        }
        file_cache.set("outputs_stats", stats_data, ttl=60)
        return jsonify(stats_data)
    except Exception as e:
        logger.error(f"获取输出文件统计失败: {e}")
        return ApiResponse.error("获取统计数据失败"), 500


@outputs_bp.route("/download_file/<path:filename>")
def download_file(filename):
    """下载文件"""
    safe_path = os.path.normpath(filename)
    if safe_path.startswith("..") or os.path.isabs(safe_path):
        return ApiResponse.error("路径不合法"), 400
    base = os.path.basename(safe_path)
    if not validate_filename(base):
        return ApiResponse.error("文件名不合法"), 400

    return send_from_directory(current_app.config["OUTPUT_FOLDER"], safe_path, as_attachment=True)


@outputs_bp.route("/view_chart/<path:filename>")
def view_chart(filename):
    """查看PNG图表"""
    safe_path = os.path.normpath(filename)
    if safe_path.startswith("..") or os.path.isabs(safe_path):
        return ApiResponse.error("路径不合法"), 400
    base = os.path.basename(safe_path)
    if not validate_filename(base):
        return ApiResponse.error("文件名不合法"), 400
    return send_from_directory(current_app.config["OUTPUT_FOLDER"], safe_path)


@outputs_bp.route("/view_chart_html/<path:filename>")
def view_chart_html(filename):
    """在线查看图表HTML文件"""
    safe_path = os.path.normpath(filename)
    if safe_path.startswith("..") or os.path.isabs(safe_path):
        return ApiResponse.error("路径不合法"), 400
    base = os.path.basename(safe_path)
    if not validate_filename(base):
        return ApiResponse.error("文件名不合法"), 400
    return send_from_directory(current_app.config["OUTPUT_FOLDER"], safe_path)


@outputs_bp.route("/view_pdf/<path:filename>")
def view_pdf(filename):
    safe_path = os.path.normpath(filename)
    if safe_path.startswith("..") or os.path.isabs(safe_path):
        return ApiResponse.error("路径不合法"), 400
    base = os.path.basename(safe_path)
    if not validate_filename(base):
        return ApiResponse.error("文件名不合法"), 400
    return send_from_directory(current_app.config["OUTPUT_FOLDER"], safe_path)


@outputs_bp.route("/export_outputs/<format>")
def export_outputs(format):
    """导出输出文件列表为不同格式"""

    # 获取所有输出文件
    output_files, _ = get_output_files()

    # 准备导出数据
    export_data = []
    for file in output_files:
        export_data.append(
            {
                "filename": file["filename"],
                "file_type": file["file_type"],
                "file_size": file["file_size"],
                "status": file["status"],
                "created_at": file["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                if file["created_at"]
                else "",
                "updated_at": file["updated_at"].strftime("%Y-%m-%d %H:%M:%S")
                if file["updated_at"]
                else "",
                "user_id": file["user_id"] or "",
                "fan_model": file["fan_model"] or "",
                "analysis_type": file["analysis_type"] or "",
                "project_id": file["project_id"] or "",
            }
        )

    # 根据格式导出
    if format == "csv":
        # 导出为CSV
        df = pd.DataFrame(export_data)
        output = io.StringIO()
        df.to_csv(output, index=False, encoding="utf-8-sig")
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8-sig")),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"outputs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )

    elif format == "json":
        # 导出为JSON
        output = io.StringIO()
        json.dump(export_data, output, ensure_ascii=False, indent=2)
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            mimetype="application/json",
            as_attachment=True,
            download_name=f"outputs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )

    elif format == "xlsx":
        # 导出为Excel
        df = pd.DataFrame(export_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Outputs")
        output.seek(0)

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"outputs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        )

    else:
        # 不支持的格式
        return ApiResponse.error("不支持的导出格式"), 400


def _delete_by_hash_file_id(file_id, output_folder):
    for entry in os.listdir(output_folder):
        entry_path = os.path.join(output_folder, entry)
        if os.path.isfile(entry_path):
            if hashlib.md5(entry_path.encode()).hexdigest()[:12] == file_id:
                os.remove(entry_path)
                return True
        elif os.path.isdir(entry_path):
            for sub_entry in os.listdir(entry_path):
                sub_path = os.path.join(entry_path, sub_entry)
                if os.path.isfile(sub_path):
                    if hashlib.md5(sub_path.encode()).hexdigest()[:12] == file_id:
                        os.remove(sub_path)
                        return True
    return False


@outputs_bp.route("/delete_output_file/<int:output_id>", methods=["POST"])
def delete_output_file(output_id):
    try:
        if current_app.config.get("DATABASE_ERROR"):
            output_folder = current_app.config["OUTPUT_FOLDER"]
            file_id = str(output_id)
            if _delete_by_hash_file_id(file_id, output_folder):
                return ApiResponse.success(message="文件删除成功")
            return ApiResponse.error("文件不存在"), 404

        _db, Output = _get_db_resources()
        if _db is None or Output is None:
            return jsonify({"success": False, "message": "数据库连接失败，无法删除文件"}), 500

        output = Output.query.get(output_id)
        if not output:
            return ApiResponse.error("文件不存在"), 404

        file_path = output.file_path

        _db.session.delete(output)
        _db.session.commit()

        if file_path and os.path.exists(file_path):
            os.remove(file_path)

        file_cache.clear()  # 清除文件列表缓存
        query_cache.delete("ml_models_db_rows")  # 失效 ML 型号列表 DB 查询缓存
        return ApiResponse.success(message="文件删除成功")
    except Exception as e:
        logger.error("删除文件失败: %s", str(e))
        _db.session.rollback()
        return ApiResponse.error("删除文件失败，请稍后重试"), 500


@outputs_bp.route("/api/outputs/list", methods=["GET"])
def api_output_list():
    """输出文件列表API——支持分页和类型过滤（返回JSON）"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        page = max(1, page)
        per_page = min(max(per_page, 1), 100)

        filters = {
            "file_type": request.args.get("file_type"),
            "status": request.args.get("status"),
            "search": request.args.get("search"),
            "fan_model": request.args.get("fan_model"),
            "analysis_type": request.args.get("analysis_type"),
            "project_id": request.args.get("project_id"),
        }
        filters = {k: v for k, v in filters.items() if v is not None}

        output_files, total_count = get_output_files(filters, page, per_page)

        serialized_files = []
        for f in output_files:
            serialized_files.append(
                {
                    "id": f["id"],
                    "filename": f["filename"],
                    "file_type": f["file_type"],
                    "file_size": f["file_size"],
                    "status": f["status"],
                    "description": f.get("description"),
                    "created_at": f["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                    if f.get("created_at")
                    else None,
                    "updated_at": f["updated_at"].strftime("%Y-%m-%d %H:%M:%S")
                    if f.get("updated_at")
                    else None,
                    "fan_model": f.get("fan_model"),
                    "analysis_type": f.get("analysis_type"),
                    "project_id": f.get("project_id"),
                }
            )

        total_pages = (total_count + per_page - 1) // per_page

        return jsonify(
            {
                "success": True,
                "data": serialized_files,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_count": total_count,
                    "total_pages": total_pages,
                },
            }
        )
    except Exception as e:
        logger.error(f"获取输出文件列表失败: {e}")
        return jsonify({"success": False, "error": "获取文件列表失败，请稍后重试"}), 500


@outputs_bp.route("/api/outputs/batch_delete", methods=["POST"])
def batch_delete_outputs():
    """批量删除输出文件"""
    try:
        data = request.get_json()
        if not data:
            return ApiResponse.error("请提供有效的JSON数据"), 400

        file_ids = data.get("ids", [])
        if not file_ids or not isinstance(file_ids, list) or len(file_ids) == 0:
            return ApiResponse.error("请提供要删除的文件ID列表"), 400

        if len(file_ids) > 100:
            return ApiResponse.error("单次批量删除不能超过100个文件"), 400

        if current_app.config.get("DATABASE_ERROR"):
            output_folder = current_app.config["OUTPUT_FOLDER"]
            deleted_count = 0
            failed_ids = []
            for file_id in file_ids:
                fid = str(file_id)
                if _delete_by_hash_file_id(fid, output_folder):
                    deleted_count += 1
                else:
                    failed_ids.append(file_id)
            return jsonify(
                {
                    "success": True,
                    "message": f"成功删除 {deleted_count} 个文件",
                    "deleted_count": deleted_count,
                    "failed_ids": failed_ids,
                    "total_requested": len(file_ids),
                }
            )

        _db, Output = _get_db_resources()
        if _db is None or Output is None:
            output_folder = current_app.config["OUTPUT_FOLDER"]
            deleted_count = 0
            failed_ids = []
            for file_id in file_ids:
                fid = str(file_id)
                if _delete_by_hash_file_id(fid, output_folder):
                    deleted_count += 1
                else:
                    failed_ids.append(file_id)
            return jsonify(
                {
                    "success": True,
                    "message": f"成功删除 {deleted_count} 个文件",
                    "deleted_count": deleted_count,
                    "failed_ids": failed_ids,
                    "total_requested": len(file_ids),
                }
            )

        deleted_count = 0
        failed_ids = []
        removed_paths = []

        for file_id in file_ids:
            try:
                output = Output.query.get(file_id)
                if not output:
                    failed_ids.append(file_id)
                    continue

                file_path = output.file_path
                _db.session.delete(output)
                if file_path:
                    removed_paths.append(file_path)
                deleted_count += 1
            except Exception:
                failed_ids.append(file_id)

        _db.session.commit()

        for file_path in removed_paths:
            if os.path.exists(file_path):
                os.remove(file_path)

        file_cache.clear()  # 清除文件列表缓存
        query_cache.delete("ml_models_db_rows")  # 失效 ML 型号列表 DB 查询缓存
        return jsonify(
            {
                "success": True,
                "message": f"成功删除 {deleted_count} 个文件",
                "deleted_count": deleted_count,
                "failed_ids": failed_ids,
                "total_requested": len(file_ids),
            }
        )
    except Exception as e:
        logger.error("批量删除文件失败: %s", str(e))
        _db.session.rollback()
        return ApiResponse.error("批量删除文件失败，请稍后重试"), 500


@outputs_bp.route("/api/outputs/by_model", methods=["GET"])
def output_files_by_model():
    search = request.args.get("search", "").strip()
    file_type = request.args.get("file_type", "").strip()

    # 缓存键：仅依赖搜索参数，30秒内复用文件系统扫描结果
    cache_key = f"by_model:{search}:{file_type}"
    cached = file_cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)

    filters = {}
    if search:
        filters["search"] = search
    if file_type and file_type != "all":
        filters["file_type"] = file_type

    output_files, _ = get_output_files(filters=filters, page=1, per_page=500)

    history_records = _load_export_history()
    models_to_update = {}
    groups = {}
    for f in output_files:
        model = f.get("fan_model")
        file_path = f.get("file_path", "")
        filename = f.get("filename", "")
        if not model:
            model = _detect_fan_model_from_path(file_path or filename, filename, history_records)
            if model:
                record_id = f.get("id")
                if record_id and record_id not in models_to_update:
                    models_to_update[record_id] = model
        model = model or "未分类"
        if model not in groups:
            groups[model] = {
                "model": model,
                "files": [],
                "first_date": None,
                "latest_date": None,
            }
        created = f.get("created_at")
        created_str = ""
        if created:
            created_str = (
                created.strftime("%Y-%m-%d %H:%M:%S")
                if hasattr(created, "strftime")
                else str(created)
            )
            if groups[model]["first_date"] is None or created_str < groups[model]["first_date"]:
                groups[model]["first_date"] = created_str
            if groups[model]["latest_date"] is None or created_str > groups[model]["latest_date"]:
                groups[model]["latest_date"] = created_str
        file_entry = {
            "id": f.get("id"),
            "filename": filename,
            "file_type": f.get("file_type"),
            "file_size": f.get("file_size", 0),
            "file_path": file_path,
            "created_at": created_str,
        }
        groups[model]["files"].append(file_entry)

    from datetime import datetime, timedelta

    now = datetime.now()
    for model_name, group in groups.items():
        files = group["files"]
        type_counts = {}
        total_size = 0
        for f in files:
            ft = f.get("file_type", "unknown")
            type_counts[ft] = type_counts.get(ft, 0) + 1
            total_size += f.get("file_size", 0) or 0
        health = "old"
        if group["latest_date"]:
            try:
                latest_dt = datetime.strptime(group["latest_date"], "%Y-%m-%d %H:%M:%S")
                delta = now - latest_dt
                if delta <= timedelta(hours=24):
                    health = "fresh"
                elif delta <= timedelta(days=7):
                    health = "recent"
                elif delta <= timedelta(days=30):
                    health = "stale"
            except ValueError:
                pass
        group["summary"] = {
            "file_count": len(files),
            "type_breakdown": type_counts,
            "total_size": total_size,
            "first_report": group["first_date"] or "",
            "latest_report": group["latest_date"] or "",
            "health": health,
        }
        del group["first_date"]

    result = sorted(groups.values(), key=lambda x: x.get("latest_date", "") or "", reverse=True)
    total_items = sum(len(g["files"]) for g in result)

    if models_to_update:
        try:
            _db, Output = _get_db_resources()
            if _db is not None and Output is not None:
                for record_id, fan_model in models_to_update.items():
                    _db.session.query(Output).filter(Output.id == record_id).update(
                        {"fan_model": fan_model}, synchronize_session=False
                    )
                _db.session.commit()
        except Exception:
            pass

    response_data = {
        "success": True,
        "data": result,
        "total_items": total_items,
    }
    file_cache.set(cache_key, response_data, ttl=30)
    return jsonify(response_data)


@outputs_bp.route("/api/outputs/preview/<file_id>", methods=["GET"])
def preview_output_file(file_id):
    """预览文本类输出文件内容"""
    output_files, _ = get_output_files(per_page=500)
    target = None
    for f in output_files:
        if str(f.get("id")) == file_id:
            target = f
            break
    if not target:
        return jsonify({"success": False, "error": "文件不存在"}), 404

    file_path = target.get("file_path", "")
    filename = target.get("filename", "")
    if not validate_filename(filename):
        return jsonify({"success": False, "error": "文件名不合法"}), 400

    full_path = file_path
    if not os.path.isabs(full_path):
        fan_model = target.get("fan_model", "")
        if fan_model and fan_model != "未分类":
            full_path = os.path.join(current_app.config["OUTPUT_FOLDER"], fan_model, filename)
        else:
            full_path = os.path.join(current_app.config["OUTPUT_FOLDER"], filename)

    if not os.path.isfile(full_path):
        return jsonify({"success": False, "error": "文件不存在"}), 404

    max_size = 10 * 1024 * 1024
    if os.path.getsize(full_path) > max_size:
        return jsonify({"success": False, "error": "文件过大，无法在线预览"}), 413

    try:
        import chardet

        with open(full_path, "rb") as f:
            raw = f.read(102400)
            result = chardet.detect(raw)
            encoding = result["encoding"] or "utf-8"
        with open(full_path, "r", encoding=encoding, errors="replace") as f:
            content = f.read()
    except ImportError:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

    return jsonify({"success": True, "data": content})


@outputs_bp.route("/api/outputs/preview_info/<file_id>", methods=["GET"])
def preview_output_info(file_id):
    """获取导出文件元信息（类型/大小/日期）"""
    output_files, _ = get_output_files(per_page=500)
    target = None
    for f in output_files:
        if str(f.get("id")) == file_id:
            target = f
            break
    if not target:
        return jsonify({"success": False, "error": "文件不存在"}), 404

    filename = target.get("filename", "")
    if not validate_filename(filename):
        return jsonify({"success": False, "error": "文件名不合法"}), 400

    file_path = target.get("file_path", "")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"

    preview_type = "unknown"
    if ext in ("html", "htm"):
        preview_type = "html"
    elif ext in ("png", "jpg", "jpeg", "gif", "svg", "webp"):
        preview_type = "image"
    elif ext in ("csv", "json", "txt", "log", "md", "py", "js", "css"):
        preview_type = "text"
    elif ext == "pdf":
        preview_type = "pdf"

    file_size = target.get("file_size", 0)
    full_path = file_path
    if not os.path.isabs(full_path):
        fan_model = target.get("fan_model", "")
        if fan_model and fan_model != "未分类":
            full_path = os.path.join(current_app.config["OUTPUT_FOLDER"], fan_model, filename)
        else:
            full_path = os.path.join(current_app.config["OUTPUT_FOLDER"], filename)
    file_exists = os.path.isfile(full_path)

    view_url = None
    if file_exists and preview_type in ("html", "image"):
        rel = os.path.relpath(full_path, current_app.config["OUTPUT_FOLDER"])
        encoded_rel = "/".join(quote(part, safe="") for part in rel.split(os.sep))
        view_url = (
            f"/view_chart/{encoded_rel}"
            if preview_type == "image"
            else f"/view_chart_html/{encoded_rel}"
        )

    return jsonify(
        {
            "success": True,
            "data": {
                "filename": filename,
                "preview_type": preview_type,
                "file_size": file_size,
                "file_exists": file_exists,
                "view_url": view_url,
                "file_path": file_path,
                "file_type": ext,
                "fan_model": target.get("fan_model"),
            },
        }
    )


@outputs_bp.route("/api/outputs/batch_download", methods=["GET", "POST"])
def batch_download_outputs():
    if request.method == "GET":
        fan_model = request.args.get("fan_model", "").strip()
        if not fan_model:
            return ApiResponse.error("请提供fan_model参数"), 400
        output_files, _ = get_output_files(per_page=500)
        matched = [f for f in output_files if f.get("fan_model", "") == fan_model]
        if not matched:
            return ApiResponse.error("未找到该型号的文件"), 404
        file_ids = [f.get("id") for f in matched if f.get("id")]
        return _build_zip_response(file_ids)
    try:
        data = request.get_json()
        if not data:
            return ApiResponse.error("请提供有效的JSON数据"), 400

        file_ids = data.get("ids", [])
        if not file_ids or not isinstance(file_ids, list) or len(file_ids) == 0:
            return ApiResponse.error("请提供要下载的文件ID列表"), 400

        if len(file_ids) > 100:
            return ApiResponse.error("单次批量下载不能超过100个文件"), 400

        return _build_zip_response(file_ids)
    except Exception as e:
        logger.error("批量下载文件失败: %s", str(e))
        return ApiResponse.error("批量下载文件失败，请稍后重试"), 500


def _build_zip_response(file_ids):
    output_files, _ = get_output_files(per_page=500)
    id_to_file = {}
    for f in output_files:
        id_to_file[str(f.get("id"))] = f

    zip_buffer = io.BytesIO()
    added_files = 0
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_id in file_ids:
            target = id_to_file.get(str(file_id))
            if not target:
                continue
            filename = target.get("filename", "")
            file_path = target.get("file_path", "")
            if not validate_filename(filename):
                continue

            full_path = file_path
            if not os.path.isabs(full_path):
                fan_model = target.get("fan_model", "")
                if fan_model and fan_model != "未分类":
                    full_path = os.path.join(
                        current_app.config["OUTPUT_FOLDER"], fan_model, filename
                    )
                else:
                    full_path = os.path.join(current_app.config["OUTPUT_FOLDER"], filename)

            if not os.path.isfile(full_path):
                continue

            fan_model = target.get("fan_model") or "未分类"
            arcname = f"{fan_model}/{filename}"
            zf.write(full_path, arcname=arcname)
            added_files += 1

    if added_files == 0:
        return ApiResponse.error("没有可下载的文件"), 404

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"reports_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
    )


@outputs_bp.route("/api/outputs/download/<path:subpath>")
def download_output_by_path(subpath):
    """通过相对路径下载文件（支持子目录）"""
    safe_path = os.path.normpath(subpath)
    if safe_path.startswith("..") or os.path.isabs(safe_path):
        return ApiResponse.error("路径不合法"), 400

    filename = os.path.basename(safe_path)
    if not validate_filename(filename):
        return ApiResponse.error("文件名不合法"), 400

    return send_from_directory(current_app.config["OUTPUT_FOLDER"], safe_path, as_attachment=True)
