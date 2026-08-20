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
