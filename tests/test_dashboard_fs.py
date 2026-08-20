# -*- coding: utf-8 -*-
"""数据仪表盘 FS 数据源回归测试（方案A：仪表盘并入机型监控后不再依赖 DB）"""
import json

from app.utils.cache_utils import query_cache
from blueprints.main_bp import _get_dashboard_data


def _clean_cache():
    query_cache.delete("dashboard_data")


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

        with app.app_context():
            files = _list_filesystem_files()
        assert len(files) == 1
        assert files[0]["created_at"].strftime("%Y-%m-%d %H:%M:%S") == "2026-08-20 20:28:22"
    finally:
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

        with app.app_context():
            files = _list_filesystem_files()
        assert len(files) == 1
        # created_at 应等于 mtime（而非 ctime）
        assert files[0]["created_at"] == files[0]["updated_at"]
        assert files[0]["created_at"].date().year >= 2020
    finally:
        if old is not None:
            app.config["OUTPUT_FOLDER"] = old
