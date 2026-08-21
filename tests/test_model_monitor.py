# -*- coding: utf-8 -*-
"""机型监控服务与看板接口测试"""
from datetime import datetime, timedelta

from app.utils.cache_utils import query_cache
from services.model_monitor_service import (
    _calc_status,
    build_model_monitor,
    load_monitor_data,
    record_model_monitor,
)


def _evaluation(best="2000rpm", score=0.85, p1=True, p2=True):
    return {
        "best_speeds": [best],
        "best_score": score,
        "has_p1": p1,
        "has_p2": p2,
        "has_st": False,
        "speed_detailed_scores": {},
    }


def test_record_and_load(tmp_path):
    assert record_model_monitor(str(tmp_path), "9324", _evaluation(), "平衡机A") is True
    data = load_monitor_data(str(tmp_path))
    assert "9324" in data
    rec = data["9324"][0]
    assert rec["best_speeds"] == ["2000rpm"]
    assert rec["balance_machine_model"] == "平衡机A"
    assert rec["has_p1"] is True


def test_record_skips_without_evaluation(tmp_path):
    assert record_model_monitor(str(tmp_path), "M1", None, "设备A") is False
    assert record_model_monitor(str(tmp_path), "", _evaluation(), "设备A") is False
    assert record_model_monitor(str(tmp_path), "M1", {"best_speeds": []}, "设备A") is False
    assert load_monitor_data(str(tmp_path)) == {}


def test_record_appends_each_analysis(tmp_path):
    """每次分析都保留记录：完整历史是「历史次数/转速变化」检测的前提"""
    rec = _evaluation()
    record_model_monitor(str(tmp_path), "M1", rec, "设备A")
    record_model_monitor(str(tmp_path), "M1", rec, "设备A")
    data = load_monitor_data(str(tmp_path))
    assert len(data["M1"]) == 2  # 相同推荐转速也逐次记录（不再去重丢弃）
    out = build_model_monitor(str(tmp_path))
    item = next(i for i in out["items"] if i["model"] == "M1")
    assert item["history_count"] == 2
    assert len(item["history"]) == 2  # 展示层 history 取最近 5 条，不受历史增长影响


def test_speed_change_detection(tmp_path):
    record_model_monitor(str(tmp_path), "M2", _evaluation("2000rpm"), "设备A")
    record_model_monitor(str(tmp_path), "M2", _evaluation("3000rpm"), "设备B")
    out = build_model_monitor(str(tmp_path))
    item = next(i for i in out["items"] if i["model"] == "M2")
    assert item["speed_changed"] is True
    assert item["best_speed"] == "3000rpm"


def test_status_calc():
    assert _calc_status(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) == "fresh"
    recent = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    assert _calc_status(recent) == "recent"
    stale = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
    assert _calc_status(stale) == "stale"
    old = (datetime.now() - timedelta(days=31)).strftime("%Y-%m-%d %H:%M:%S")
    assert _calc_status(old) == "old"
    assert _calc_status("bad-format") == "old"
    assert _calc_status("") == "old"


def test_status_falls_back_to_group_latest_date(tmp_path):
    """无监控记录但有 outputs 文件时，以文件最新时间判定状态，避免误报超期"""
    recent = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    groups = [
        {
            "model": "M9",
            "files": [{"id": "1"}],
            "latest_date": recent,
            "summary": {"file_count": 1, "type_breakdown": {"html": 1}},
        }
    ]
    out = build_model_monitor(str(tmp_path), groups)
    item = next(i for i in out["items"] if i["model"] == "M9")
    assert item["status"] == "recent"  # 1 天前 → recent，而非误报 old


def test_build_merge_groups(tmp_path):
    record_model_monitor(str(tmp_path), "M3", _evaluation("1500rpm"), "设备X")
    groups = [
        {
            "model": "M3",
            "files": [{"id": "1"}, {"id": "2"}],
            "summary": {"file_count": 2, "type_breakdown": {"html": 1, "png": 1}},
        }
    ]
    out = build_model_monitor(str(tmp_path), groups)
    assert out["success"] is True
    item = next(i for i in out["items"] if i["model"] == "M3")
    assert item["report_count"] == 2
    assert item["missing"] == ""
    assert item["history"]  # 含历史明细


def test_build_incomplete_alert(tmp_path):
    record_model_monitor(str(tmp_path), "M4", _evaluation(), "设备Y")
    groups = [
        {
            "model": "M4",
            "files": [{"id": "1"}, {"id": "2"}],
            "summary": {"file_count": 2, "type_breakdown": {"csv": 2}},
        }
    ]
    out = build_model_monitor(str(tmp_path), groups)
    item = next(i for i in out["items"] if i["model"] == "M4")
    assert "缺HTML" in item["missing"]


def test_api_routes(tmp_path):
    import wsgi

    app = wsgi.app
    app.config["TESTING"] = True
    old = app.config.get("OUTPUT_FOLDER")
    app.config["OUTPUT_FOLDER"] = str(tmp_path)
    try:
        client = app.test_client()
        # 机型监控已并入仪表盘：旧地址重定向到 /dashboard
        r = client.get("/model-monitor")
        assert r.status_code == 302
        assert r.headers.get("Location", "").endswith("/dashboard")
        # 清缓存后再请求，避免 60s TTL 命中旧数据
        query_cache.delete("model_monitor")
        r = client.get("/api/outputs/model_monitor")
        assert r.status_code == 200
        body = r.get_json()
        assert body["success"] is True
    finally:
        query_cache.delete("model_monitor")
        if old is not None:
            app.config["OUTPUT_FOLDER"] = old


def test_record_invalidates_dashboard_cache(tmp_path):
    """record_model_monitor 写记录后必须失效 dashboard_data / model_monitor 缓存。

    回归：FS 模式（DATABASE_ERROR 降级）不经过 data_processing 的 DB 分支，
    新分析完成后仪表盘与看板最长 60s 不更新。
    """
    import wsgi

    from blueprints.main_bp import _get_dashboard_data

    app = wsgi.app
    app.config["TESTING"] = True
    old = app.config.get("OUTPUT_FOLDER")
    app.config["OUTPUT_FOLDER"] = str(tmp_path)
    try:
        query_cache.delete("dashboard_data")
        query_cache.delete("model_monitor")
        with app.app_context():
            data = _get_dashboard_data()
        assert data["total_evaluations"] == 0

        # 预置一份评估报告，再写入监控记录（模拟新分析完成）
        model_dir = tmp_path / "9324"
        model_dir.mkdir()
        (model_dir / "9324_动平衡分析报告_20260820_120000.html").write_text(
            "<html>r</html>", encoding="utf-8"
        )
        ok = record_model_monitor(str(tmp_path), "9324", _evaluation("4000rpm"), "BM.AT40")
        assert ok is True

        # 缓存必须已被失效，直接重算即可拿到新数据（无需等待 60s 过期）
        with app.app_context():
            data2 = _get_dashboard_data()
        assert data2["total_evaluations"] == 1
        assert data2["optimal_speed"] == "4000rpm"
    finally:
        query_cache.delete("dashboard_data")
        query_cache.delete("model_monitor")
        if old is not None:
            app.config["OUTPUT_FOLDER"] = old


def test_api_refresh_param_bypasses_cache(tmp_path):
    """/api/outputs/model_monitor?refresh=1 强制失效 60s 缓存，刷新按钮才有意义。

    回归：缓存期内点刷新按钮拿到的是旧数据，用户感知"刷新无效"。
    """
    import wsgi

    app = wsgi.app
    app.config["TESTING"] = True
    old = app.config.get("OUTPUT_FOLDER")
    app.config["OUTPUT_FOLDER"] = str(tmp_path)
    try:
        client = app.test_client()
        # 第一次请求写入 60s 缓存
        query_cache.delete("model_monitor")
        r1 = client.get("/api/outputs/model_monitor")
        assert r1.status_code == 200
        assert query_cache.get("model_monitor") is not None

        # 带 refresh=1 必须绕过缓存并重建
        r2 = client.get("/api/outputs/model_monitor?refresh=1")
        assert r2.status_code == 200
        assert r2.get_json()["success"] is True
    finally:
        query_cache.delete("model_monitor")
        if old is not None:
            app.config["OUTPUT_FOLDER"] = old
