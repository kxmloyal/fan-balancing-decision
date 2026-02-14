# -*- coding: utf-8 -*-
"""
输出文件蓝图：包含输出文件管理功能
"""

import os
from datetime import datetime

from flask import (Blueprint, render_template, request, send_file,
                   send_from_directory, current_app)

outputs_bp = Blueprint("outputs", __name__)


def get_output_files(filters=None, page=1, per_page=20):
    """获取outputs文件夹内的所有文件信息，支持筛选和分页

    Args:
        filters: 筛选条件，包含file_type, status, user_id, fan_model, analysis_type, project_id等
        page: 当前页码，默认为1
        per_page: 每页显示数量，默认为20

    Returns:
        tuple: (outputs_list, total_count)
    """
    # 检查数据库连接状态
    if current_app.config.get("DATABASE_ERROR"):
        # 数据库连接失败，使用文件系统模式
        output_folder = current_app.config["OUTPUT_FOLDER"]
        outputs_list = []

        if os.path.exists(output_folder):
            for filename in os.listdir(output_folder):
                file_path = os.path.join(output_folder, filename)
                if os.path.isfile(file_path):
                    file_type = (
                        filename.split(".")[-1].lower()
                        if "." in filename
                        else "unknown"
                    )
                    file_size = os.path.getsize(file_path)
                    created_at = datetime.fromtimestamp(os.path.getctime(file_path))
                    updated_at = datetime.fromtimestamp(os.path.getmtime(file_path))

                    outputs_list.append(
                        {
                            "id": hash(file_path),
                            "filename": filename,
                            "file_path": file_path,
                            "file_type": file_type,
                            "file_size": file_size,
                            "status": "completed",
                            "description": None,
                            "created_at": created_at,
                            "updated_at": updated_at,
                            "user_id": None,
                            "fan_model": None,
                            "analysis_type": None,
                            "project_id": None,
                        }
                    )

        # 应用筛选
        if filters:
            if filters.get("file_type"):
                outputs_list = [
                    o for o in outputs_list if o["file_type"] == filters["file_type"]
                ]
            if filters.get("search"):
                search_term = filters["search"].lower()
                outputs_list = [
                    o for o in outputs_list if search_term in o["filename"].lower()
                ]

        # 按更新时间排序
        outputs_list.sort(key=lambda x: x["updated_at"], reverse=True)

        # 应用分页
        total_count = len(outputs_list)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_list = outputs_list[start:end]

        return paginated_list, total_count

    try:
        # 延迟导入，避免循环导入
        from app import db, Output
        
        # 检查数据库中是否有记录
        query = Output.query

        # 应用筛选条件
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
            # 添加项目筛选
            if filters.get("project_id"):
                query = query.filter_by(project_id=filters["project_id"])
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    Output.filename.like(search_term)
                    | Output.description.like(search_term)
                )

        # 按更新时间排序
        query = query.order_by(Output.updated_at.desc())

        # 获取总记录数
        total_count = query.count()

        # 如果数据库中没有记录，从文件系统同步
        if total_count == 0:
            sync_outputs_from_filesystem()
            # 重新构建查询，确保使用最新数据
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
                # 重新应用项目筛选
                if filters.get("project_id"):
                    query = query.filter_by(project_id=filters["project_id"])
                if filters.get("search"):
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        Output.filename.like(search_term)
                        | Output.description.like(search_term)
                    )
            query = query.order_by(Output.updated_at.desc())
            total_count = query.count()

        # 应用分页，只查询需要的字段，减少数据传输
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
        # 数据库操作失败，使用文件系统模式
        print(f"数据库操作失败: {str(e)}")
        output_folder = current_app.config["OUTPUT_FOLDER"]
        outputs_list = []

        if os.path.exists(output_folder):
            for filename in os.listdir(output_folder):
                file_path = os.path.join(output_folder, filename)
                if os.path.isfile(file_path):
                    file_type = (
                        filename.split(".")[-1].lower()
                        if "." in filename
                        else "unknown"
                    )
                    file_size = os.path.getsize(file_path)
                    created_at = datetime.fromtimestamp(os.path.getctime(file_path))
                    updated_at = datetime.fromtimestamp(os.path.getmtime(file_path))

                    outputs_list.append(
                        {
                            "id": hash(file_path),
                            "filename": filename,
                            "file_path": file_path,
                            "file_type": file_type,
                            "file_size": file_size,
                            "status": "completed",
                            "description": None,
                            "created_at": created_at,
                            "updated_at": updated_at,
                            "user_id": None,
                            "fan_model": None,
                            "analysis_type": None,
                            "project_id": None,
                        }
                    )

        # 应用筛选
        if filters:
            if filters.get("file_type"):
                outputs_list = [
                    o for o in outputs_list if o["file_type"] == filters["file_type"]
                ]
            if filters.get("search"):
                search_term = filters["search"].lower()
                outputs_list = [
                    o for o in outputs_list if search_term in o["filename"].lower()
                ]

        # 按更新时间排序
        outputs_list.sort(key=lambda x: x["updated_at"], reverse=True)

        # 应用分页
        total_count = len(outputs_list)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_list = outputs_list[start:end]

        return paginated_list, total_count


def sync_outputs_from_filesystem():
    """从文件系统同步outputs到数据库"""
    from flask import current_app
    output_folder = current_app.config["OUTPUT_FOLDER"]

    if not os.path.exists(output_folder):
        return

    # 获取所有文件路径，然后批量处理
    all_files = []
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        if os.path.isfile(file_path):
            all_files.append((filename, file_path))

    if not all_files:
        return

    try:
        # 延迟导入，避免循环导入
        from app import db, Output
        
        # 批量查询已存在的记录，减少数据库查询次数
        existing_files = db.session.query(Output.filename, Output.file_path).all()
        existing_set = set((f[0], f[1]) for f in existing_files)

        # 准备要添加的新记录
        new_records = []
        for filename, file_path in all_files:
            if (filename, file_path) not in existing_set:
                # 提取文件信息
                file_type = (
                    filename.split(".")[-1].lower() if "." in filename else "unknown"
                )
                file_size = os.path.getsize(file_path)
                created_at = datetime.fromtimestamp(os.path.getctime(file_path))
                updated_at = datetime.fromtimestamp(os.path.getmtime(file_path))

                # 创建新记录，不设置project_id，默认为null
                new_records.append(
                    Output(
                        filename=filename,
                        file_path=file_path,
                        file_type=file_type,
                        file_size=file_size,
                        status="completed",
                        created_at=created_at,
                        updated_at=updated_at,
                    )
                )

        # 批量添加新记录
        if new_records:
            db.session.add_all(new_records)
            db.session.commit()
    except Exception as e:
        print(f"同步文件到数据库失败: {str(e)}")


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
        # 延迟导入，避免循环导入
        from app import db, Output
        
        file_types = (
            db.session.query(Output.file_type).distinct().order_by(Output.file_type).all()
        )
        statuses = db.session.query(Output.status).distinct().order_by(Output.status).all()
        fan_models = (
            db.session.query(Output.fan_model)
            .filter(Output.fan_model.isnot(None))
            .distinct()
            .order_by(Output.fan_model)
            .all()
        )
        analysis_types = (
            db.session.query(Output.analysis_type)
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
        print(f"获取筛选选项失败: {str(e)}")

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


@outputs_bp.route("/download_file/<filename>")
def download_file(filename):
    """下载文件"""
    from flask import current_app

    return send_from_directory(
        current_app.config["OUTPUT_FOLDER"], filename, as_attachment=True
    )


@outputs_bp.route("/view_chart/<filename>")
def view_chart(filename):
    """查看PNG图表"""
    from flask import current_app

    return send_from_directory(current_app.config["OUTPUT_FOLDER"], filename)


@outputs_bp.route("/view_chart_html/<filename>")
def view_chart_html(filename):
    """查看HTML交互式图表"""
    from flask import current_app

    return send_from_directory(current_app.config["OUTPUT_FOLDER"], filename)


@outputs_bp.route("/export_outputs/<format>")
def export_outputs(format):
    """导出输出文件列表为不同格式"""
    from flask import current_app, send_file
    import pandas as pd
    import json
    import io
    from datetime import datetime

    # 获取所有输出文件
    output_files, _ = get_output_files()

    # 准备导出数据
    export_data = []
    for file in output_files:
        export_data.append({
            "filename": file["filename"],
            "file_type": file["file_type"],
            "file_size": file["file_size"],
            "status": file["status"],
            "created_at": file["created_at"].strftime("%Y-%m-%d %H:%M:%S") if file["created_at"] else "",
            "updated_at": file["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if file["updated_at"] else "",
            "user_id": file["user_id"] or "",
            "fan_model": file["fan_model"] or "",
            "analysis_type": file["analysis_type"] or "",
            "project_id": file["project_id"] or ""
        })

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
            download_name=f"outputs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
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
            download_name=f"outputs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
            download_name=f"outputs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
    
    else:
        # 不支持的格式
        from flask import jsonify
        return jsonify({"error": "不支持的导出格式"}), 400


@outputs_bp.route("/delete_output_file/<int:output_id>", methods=["POST"])
def delete_output_file(output_id):
    """删除输出文件"""
    from flask import jsonify, current_app
    
    try:
        # 检查数据库连接状态
        if current_app.config.get("DATABASE_ERROR"):
            # 数据库连接失败，使用文件系统模式
            # 由于在文件系统模式下，output_id 是文件路径的哈希值，无法直接使用
            # 这里返回错误信息
            return jsonify({"success": False, "message": "数据库连接失败，无法删除文件"}), 500
        
        # 延迟导入，避免循环导入
        from app import db, Output
        
        # 查找要删除的文件
        output = Output.query.get(output_id)
        if not output:
            return jsonify({"success": False, "message": "文件不存在"}), 404
        
        # 保存文件路径，用于后续删除
        file_path = output.file_path
        
        # 从数据库中删除记录
        db.session.delete(output)
        db.session.commit()
        
        # 从文件系统中删除文件
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({"success": True, "message": "文件删除成功"})
    except Exception as e:
        # 数据库操作失败，返回错误信息
        return jsonify({"success": False, "message": f"删除文件失败：{str(e)}"}), 500
