# -*- coding: utf-8 -*-
"""outputs 报告管理页全链路回归测试（FS 分支 + 文件名内嵌时间戳口径）"""
import json
import os
import re

import pytest

from app.utils.cache_utils import file_cache
from blueprints.outputs_bp import (
    _parse_report_timestamp,
    get_output_files,
)

_REPORT_HTML = "<html><body>test report</body></html>"


@pytest.fixture
def fs_app(tmp_path):
    """构造临时 outputs 目录 + 强制 FS 分支，测试后恢复全局配置"""
    import wsgi

    app = wsgi.app
    app.config["TESTING"] = True
    old_folder = app.config.get("OUTPUT_FOLDER")
    old_db_err = app.config.get("DATABASE_ERROR")

    # 型号 9324：2 个报告文件（含文件名内嵌导出时间戳）+ 1 个 png
    # 文件 mtime 统一固定到报告导出时刻（图表 png 文件名无内嵌时间戳，
    # created_at 回退 mtime，测试中不控制会取到"当前时间"导致 latest_report 漂移）
    model_dir = tmp_path / "9324"
    model_dir.mkdir()
    for ts in ("20260820_202822", "20260820_222019"):
        p = model_dir / f"9324_动平衡分析报告_{ts}.html"
        p.write_text(_REPORT_HTML, encoding="utf-8")
        os.utime(p, (1700000000, 1700000000))
    png = model_dir / "9324_动平衡分析报告_20260820_222019.png"
    png.write_text("PNGDATA", encoding="utf-8")
    os.utime(png, (1700000000, 1700000000))
    (tmp_path / "export_history.json").write_text(
        json.dumps(
            [{"filename": "9324_动平衡分析报告_20260820_202822.html", "fan_model": "9324"}]
        ),
        encoding="utf-8",
    )

    app.config["OUTPUT_FOLDER"] = str(tmp_path)
    app.config["DATABASE_ERROR"] = "test-force-fs"
    file_cache.clear()
    try:
        yield app
    finally:
        app.config["OUTPUT_FOLDER"] = old_folder
        if old_db_err is None:
            app.config.pop("DATABASE_ERROR", None)
        else:
            app.config["DATABASE_ERROR"] = old_db_err
        file_cache.clear()


def _get_csrf_token(client):
    page = client.get("/outputs").get_data(as_text=True)
    m = re.search(r'name="csrf_token" value="([^"]+)"', page)
    return m.group(1) if m else ""


def test_parse_report_timestamp_precedence():
    """文件名内嵌时间戳优先于 mtime/ctime（第 58 轮修复后口径）"""
    ts = _parse_report_timestamp("9324_动平衡分析报告_20260820_202822.html")
    assert ts is not None
    assert ts.strftime("%Y-%m-%d %H:%M:%S") == "2026-08-20 20:28:22"
    assert _parse_report_timestamp("chart_abc.png") is None
    assert _parse_report_timestamp("9324_动平衡分析报告_20261399_202822.html") is None


def test_get_output_files_default_full(fs_app):
    """get_output_files() 默认全量返回，不静默截断（历史 bug：默认 per_page=20）"""
    with fs_app.app_context():
        files, total = get_output_files()
    assert total == 3
    assert len(files) == 3


def test_outputs_page_renders(fs_app):
    client = fs_app.test_client()
    r = client.get("/outputs")
    assert r.status_code == 200
    assert "报告管理" in r.get_data(as_text=True)


def test_by_model_groups(fs_app):
    client = fs_app.test_client()
    d = client.get("/api/outputs/by_model").get_json()
    assert d["success"] is True
    assert d["total_items"] == 3
    group = d["data"][0]
    assert group["model"] == "9324"
    s = group["summary"]
    assert s["file_count"] == 3
    assert s["type_breakdown"]["html"] == 2
    assert s["type_breakdown"]["png"] == 1
    assert s["latest_report"] == "2026-08-20 22:20:19"
    assert s["health"] in ("fresh", "recent", "stale", "old")

    # 测试批次编号：2 份报告（文件名内嵌时间戳）→ 第1次/第2次测试
    assert s["test_count"] == 2
    files = group["files"]
    report1 = next(f for f in files if f["filename"].endswith("20260820_202822.html"))
    report2 = next(f for f in files if f["filename"].endswith("20260820_222019.html"))
    assert report1["test_no"] == 1
    assert report2["test_no"] == 2
    # 图表 png（无内嵌时间戳，mtime 固定为 2023-11-14，早于所有报告）
    # → 无报告时间 ≤ 图表时间，回退归最早一次报告（第1次批次）
    png = next(f for f in files if f["filename"].endswith(".png"))
    assert png["test_no"] == 1


def test_by_model_test_batch_with_two_generations(fs_app):
    """同一型号两次测试（两批报告+图表）时 test_no 正确区分批次。

    场景：9324 第一次测试生成 chart_a_* 图表 + 报告1；第二次测试生成
    chart_b_* 图表 + 报告2。图表按时间归属最近一次报告，报告按文件名时间戳编号。
    """
    from datetime import datetime
    from pathlib import Path

    from blueprints.outputs_bp import output_files_by_model

    def _ep(y, mo, d, h, mi):
        # 本地时区（GMT+8）的 epoch 秒，保证图表 created_at(mtime) 与报告
        # 文件名内嵌时间戳同口径比较
        return int(datetime(y, mo, d, h, mi).timestamp())

    with fs_app.app_context():
        model_dir = Path(fs_app.config["OUTPUT_FOLDER"]) / "9324"
        # 第一次测试（08-19）：报告 + 图表
        p1 = model_dir / "9324_动平衡分析报告_20260819_100000.html"
        p1.write_text(_REPORT_HTML, encoding="utf-8")
        os.utime(p1, (1700000000, 1700000000))
        c1 = model_dir / "chart_aaa111aaa111aaa111aaa111aaa11111_e876b9e1_p1_box.png"
        c1.write_bytes(b"PNG")
        # 图表 mtime 设在报告1之后、报告2之前 → 归属第1次批次
        os.utime(c1, (_ep(2026, 8, 19, 11, 0), _ep(2026, 8, 19, 11, 0)))
        # 第二次测试（08-20）：报告 + 图表
        p2 = model_dir / "9324_动平衡分析报告_20260820_150000.html"
        p2.write_text(_REPORT_HTML, encoding="utf-8")
        os.utime(p2, (1700000000, 1700000000))
        c2 = model_dir / "chart_bbb222bbb222bbb222bbb222bbb22222_e876b9e1_p1_box.png"
        c2.write_bytes(b"PNG")
        # 图表 mtime 设在报告2之后、报告3(20:28)之前 → 归属第2次批次
        os.utime(c2, (_ep(2026, 8, 20, 16, 0), _ep(2026, 8, 20, 16, 0)))

        with fs_app.test_request_context("/api/outputs/by_model"):
            resp = output_files_by_model()
        groups = resp.get_json()["data"]
        group = next(g for g in groups if g["model"] == "9324")
        assert group["summary"]["test_count"] == 4  # 含 fixture 的 2 份 + 本次 2 份

        files = group["files"]

        def _no(suffix):
            return next(f for f in files if f["filename"].endswith(suffix))["test_no"]

        # 按文件名时间戳升序编号：08-19(1) 08-20 15:00(2) 08-20 20:28(3) 08-20 22:20(4)
        assert _no("20260819_100000.html") == 1
        assert _no("chart_aaa111aaa111aaa111aaa111aaa11111_e876b9e1_p1_box.png") == 1
        assert _no("20260820_150000.html") == 2
        assert _no("chart_bbb222bbb222bbb222bbb222bbb22222_e876b9e1_p1_box.png") == 2


def test_by_model_reportless_group_is_first_batch(fs_app):
    """有型号但无报告锚点（分析未导出报告）→ test_no=1 视为第1次测试，
    不得落入"未归类文件"（仅"未分类"组 test_no=0 才是未归类）"""
    from pathlib import Path

    from blueprints.outputs_bp import output_files_by_model

    with fs_app.app_context():
        model_dir = Path(fs_app.config["OUTPUT_FOLDER"]) / "1118"
        model_dir.mkdir()
        chart = model_dir / "chart_abc111abc111abc111abc111abc11111_e876b9e1_p1_box.png"
        chart.write_bytes(b"PNG")

        with fs_app.test_request_context("/api/outputs/by_model"):
            resp = output_files_by_model()
        group = next(g for g in resp.get_json()["data"] if g["model"] == "1118")
        assert group["summary"]["test_count"] == 0  # 无报告锚点
        assert all(f["test_no"] == 1 for f in group["files"])


def test_preview_info_relative_urls_no_abs_leak(fs_app):
    client = fs_app.test_client()
    d = client.get("/api/outputs/by_model").get_json()
    # 明确选 HTML 报告文件（文件顺序受 mtime/目录扫描顺序影响，不能依赖 files[0]）
    html_file = next(f for f in d["data"][0]["files"] if f["filename"].endswith(".html"))
    fid = str(html_file["id"])
    info = client.get(f"/api/outputs/preview_info/{fid}").get_json()["data"]
    assert info["file_exists"] is True
    assert info["preview_type"] == "html"
    assert info["view_url"].startswith("/view_chart_html/")
    assert info["download_url"].startswith("/api/outputs/download/")
    # 修复前返回绝对路径 file_path，前端下载必 400；现在不应包含绝对路径
    assert "wwwroot" not in json.dumps(info)
    assert "file_path" not in info

    # 下载与预览端点应可访问
    assert client.get(info["download_url"]).status_code == 200
    assert client.get(info["view_url"]).status_code == 200


def test_preview_info_pdf_view_url(fs_app, tmp_path):
    (tmp_path / "9324" / "9324_动平衡分析报告_20260820_222019.pdf").write_bytes(b"%PDF-1.4 fake")
    client = fs_app.test_client()
    d = client.get("/api/outputs/by_model").get_json()
    pdf = next(f for f in d["data"][0]["files"] if f["filename"].endswith(".pdf"))
    info = client.get(f"/api/outputs/preview_info/{pdf['id']}").get_json()["data"]
    assert info["preview_type"] == "pdf"
    assert info["view_url"].startswith("/view_pdf/")


def test_batch_download_post_with_csrf(fs_app):
    client = fs_app.test_client()
    token = _get_csrf_token(client)
    d = client.get("/api/outputs/by_model").get_json()
    fid = str(d["data"][0]["files"][0]["id"])
    r = client.post(
        "/api/outputs/batch_download",
        json={"ids": [fid]},
        headers={"X-CSRFToken": token},
    )
    assert r.status_code == 200
    assert r.content_type == "application/zip"


def test_batch_delete_invalidates_by_model_cache(fs_app):
    """删除后 /api/outputs/by_model（30s 缓存）必须立即反映，不得返回已删文件。

    回归：batch_delete 的 FS 分支曾只删文件不清 file_cache，by_model 的 30s TTL
    缓存仍返回已删文件，前端删后刷新/重载列表都看到幽灵文件。
    """
    client = fs_app.test_client()
    token = _get_csrf_token(client)
    d = client.get("/api/outputs/by_model").get_json()
    files = d["data"][0]["files"]
    assert len(files) == 3
    target = files[0]
    fid = str(target["id"])
    filename = target["filename"]

    r = client.post(
        "/api/outputs/batch_delete",
        json={"ids": [fid]},
        headers={"X-CSRFToken": token},
    )
    assert r.status_code == 200
    assert r.get_json()["success"] is True

    # 再次请求必须命中缓存失效后的新数据：文件与文件数都应减少
    d2 = client.get("/api/outputs/by_model").get_json()
    remain = d2["data"][0]["files"]
    assert len(remain) == 2
    assert all(f["filename"] != filename for f in remain)


def test_dead_endpoints_removed(fs_app):
    """已删除的无调用方端点应返回 404"""
    client = fs_app.test_client()
    for url in ("/outputs_stats", "/export_outputs/csv", "/api/outputs/list"):
        assert client.get(url).status_code == 404
