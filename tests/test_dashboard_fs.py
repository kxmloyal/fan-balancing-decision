# -*- coding: utf-8 -*-
"""数据仪表盘 FS 数据源回归测试（方案A：仪表盘并入机型监控后不再依赖 DB）"""
import json

from app.utils.cache_utils import file_cache, query_cache
from blueprints.main_bp import _get_dashboard_data


def _clean_cache():
    # 同时清 file_cache：_list_filesystem_files 也有 30s TTL 缓存（第 62 轮起），
    # 不清会导致测试之间串到上一个 tmp_path 的扫描结果
    file_cache.clear()
    query_cache.delete("dashboard_data")
    query_cache.delete("model_monitor")


def test_dashboard_fs_reports(tmp_path):
    import wsgi

    app = wsgi.app
    app.config["TESTING"] = True
    old = app.config.get("OUTPUT_FOLDER")
    # 构造：型号目录下 1 份评估报告 HTML + 1 份机型监控记录
    model_dir = tmp_path / "9324"
    model_dir.mkdir()
    (model_dir / "9324_动平衡分析报告_20260820_120000.html").write_text(
        "<html>report</html>", encoding="utf-8"
    )
    (tmp_path / "model_monitor.json").write_text(
        json.dumps(
            {
                "9324": [
                    {
                        "time": "2026-08-20 12:00:00",
                        "best_speeds": ["4000rpm"],
                        "best_score": 0.7326,
                        "balance_machine_model": "BM.AT40",
                        "has_p1": True,
                        "has_p2": True,
                        "has_st": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    app.config["OUTPUT_FOLDER"] = str(tmp_path)
    try:
        _clean_cache()
        with app.app_context():
            data = _get_dashboard_data()
        assert data["total_evaluations"] == 1
        assert data["model_count"] == 1
        assert data["model_labels"] == ["9324"]
        assert data["model_counts"] == [1]
        assert data["optimal_speed"] == "4000rpm"
        assert data["speed_labels"] == ["4000rpm"]
        assert data["speed_stability"] == 100
        assert data["latest_evaluation"] != "暂无"
        assert len(data["evaluation_dates"]) == 7
        assert sum(data["evaluation_counts"]) == 1
        assert len(data["recent_records"]) == 1
        rec = data["recent_records"][0]
        assert rec["fan_model"] == "9324"
        assert rec["optimal_speed"] == "4000rpm"
        # 新格式文件名不含转速 → 回退监控推荐转速，不再显示"未知"
        assert rec["evaluated_speeds"] == "4000rpm"
        # 报告查看/下载相对路径
        assert rec["file_path_rel"].endswith("9324_动平衡分析报告_20260820_120000.html")
    finally:
        _clean_cache()
        if old is not None:
            app.config["OUTPUT_FOLDER"] = old


def test_dashboard_fs_empty(tmp_path):
    """无报告、无监控记录时仪表盘返回空结构而非报错"""
    import wsgi

    app = wsgi.app
    app.config["TESTING"] = True
    old = app.config.get("OUTPUT_FOLDER")
    app.config["OUTPUT_FOLDER"] = str(tmp_path)
    try:
        _clean_cache()
        with app.app_context():
            data = _get_dashboard_data()
        assert data["total_evaluations"] == 0
        assert data["model_count"] == 0
        assert data["optimal_speed"] == "—"
        assert data["recent_records"] == []
        assert len(data["evaluation_dates"]) == 7
        assert sum(data["evaluation_counts"]) == 0
    finally:
        _clean_cache()
        if old is not None:
            app.config["OUTPUT_FOLDER"] = old


def test_dashboard_report_time_uses_filename_timestamp(tmp_path):
    """报告时间以文件名内嵌时间戳为准：即使 ctime 相同/失真，也按真实导出时间排序展示。

    回归场景：outputs/9324 下多份报告 ctime 被统一触碰为同一时刻，旧实现按 ctime
    排序导致仪表盘出现多条"相同时间"的最近评估记录。文件名 20260820_120000 早于
    20260820_130000，修复后必须按文件名时间倒序，而非 ctime。
    """
    import wsgi

    app = wsgi.app
    app.config["TESTING"] = True
    old = app.config.get("OUTPUT_FOLDER")
    model_dir = tmp_path / "9324"
    model_dir.mkdir()
    # 先创建 12:00 的报告，再创建 13:00 的报告（后者的 ctime 更大）
    (model_dir / "9324_动平衡分析报告_20260820_120000.html").write_text(
        "<html>r1</html>", encoding="utf-8"
    )
    (model_dir / "9324_动平衡分析报告_20260820_130000.html").write_text(
        "<html>r2</html>", encoding="utf-8"
    )
    (tmp_path / "model_monitor.json").write_text("{}", encoding="utf-8")
    app.config["OUTPUT_FOLDER"] = str(tmp_path)
    try:
        _clean_cache()
        with app.app_context():
            data = _get_dashboard_data()
        assert data["total_evaluations"] == 2
        # 按文件名时间戳倒序：13:00 在前，12:00 在后（而非按 ctime）
        assert data["recent_records"][0]["timestamp"] == "2026-08-20 13:00:00"
        assert data["recent_records"][1]["timestamp"] == "2026-08-20 12:00:00"
        assert data["latest_evaluation"] == "2026-08-20 13:00"
    finally:
        _clean_cache()
        if old is not None:
            app.config["OUTPUT_FOLDER"] = old


def test_list_filesystem_files_report_created_at(tmp_path):
    """_list_filesystem_files 对报告文件 created_at 解析文件名内嵌时间戳"""
    import wsgi

    app = wsgi.app
    app.config["TESTING"] = True
    old = app.config.get("OUTPUT_FOLDER")
    model_dir = tmp_path / "9324"
    model_dir.mkdir()
    (model_dir / "9324_动平衡分析报告_20260820_202822.html").write_text(
        "<html>r</html>", encoding="utf-8"
    )
    app.config["OUTPUT_FOLDER"] = str(tmp_path)
    try:
        from blueprints.outputs_bp import _list_filesystem_files

        _clean_cache()
        with app.app_context():
            files = _list_filesystem_files()
        assert len(files) == 1
        assert files[0]["created_at"].strftime("%Y-%m-%d %H:%M:%S") == "2026-08-20 20:28:22"
    finally:
        _clean_cache()
        if old is not None:
            app.config["OUTPUT_FOLDER"] = old


def test_list_filesystem_files_no_ts_falls_back_to_mtime(tmp_path):
    """文件名无内嵌时间戳时回退 mtime（ctime 会被复制/触碰统一改变，不可靠）"""
    import wsgi

    app = wsgi.app
    app.config["TESTING"] = True
    old = app.config.get("OUTPUT_FOLDER")
    model_dir = tmp_path / "diff1_验证"
    model_dir.mkdir()
    (model_dir / "SN300-12_1500rpm_动平衡分析报告.html").write_text(
        "<html>r</html>", encoding="utf-8"
    )
    app.config["OUTPUT_FOLDER"] = str(tmp_path)
    try:
        from blueprints.outputs_bp import _list_filesystem_files

        _clean_cache()
        with app.app_context():
            files = _list_filesystem_files()
        assert len(files) == 1
        # created_at 应等于 mtime（而非 ctime）
        assert files[0]["created_at"] == files[0]["updated_at"]
        assert files[0]["created_at"].date().year >= 2020
    finally:
        _clean_cache()
        if old is not None:
            app.config["OUTPUT_FOLDER"] = old


def test_dashboard_delete_invalidates_cache(tmp_path):
    """删除报告后仪表盘数据（60s 缓存）必须立即反映，不得返回幽灵统计。

    回归：batch_delete 只清 file_cache，dashboard_data（query_cache 60s TTL）未失效，
    删除报告后仪表盘累计次数仍包含已删文件，最长 60s 内不刷新。
    """
    import wsgi

    app = wsgi.app
    app.config["TESTING"] = True
    old = app.config.get("OUTPUT_FOLDER")
    old_db_err = app.config.get("DATABASE_ERROR")
    model_dir = tmp_path / "9324"
    model_dir.mkdir()
    (model_dir / "9324_动平衡分析报告_20260820_120000.html").write_text(
        "<html>r</html>", encoding="utf-8"
    )
    (tmp_path / "model_monitor.json").write_text("{}", encoding="utf-8")
    app.config["OUTPUT_FOLDER"] = str(tmp_path)
    app.config["DATABASE_ERROR"] = "test-force-fs"
    try:
        _clean_cache()
        from blueprints.outputs_bp import _list_filesystem_files, batch_delete_outputs

        with app.app_context():
            files = _list_filesystem_files()
        assert len(files) == 1
        fid = files[0]["id"]

        with app.app_context():
            data = _get_dashboard_data()
        assert data["total_evaluations"] == 1

        # 走 batch_delete 删除该报告，随后立即重算仪表盘（不依赖 60s 缓存过期）
        with app.test_request_context(
            "/api/outputs/batch_delete", method="POST", json={"ids": [fid]}
        ):
            resp = batch_delete_outputs()
        assert resp.status_code == 200

        with app.app_context():
            data2 = _get_dashboard_data()
        assert data2["total_evaluations"] == 0
        assert data2["recent_records"] == []
    finally:
        _clean_cache()
        if old is not None:
            app.config["OUTPUT_FOLDER"] = old
        if old_db_err is None:
            app.config.pop("DATABASE_ERROR", None)
        else:
            app.config["DATABASE_ERROR"] = old_db_err
