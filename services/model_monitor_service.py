#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
机型监控服务 — 记录每个机型最新推荐的平衡转速与使用设备，
供「机型监控看板」聚合展示（含停机/完整性/转速漂移告警）。

存储：outputs/model_monitor.json（机型 → 历史记录列表，每机型保留 30 条）
"""
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

MONITOR_FILE = "model_monitor.json"
STALE_DAYS = 7
OLD_DAYS = 30
MAX_RECORDS_PER_MODEL = 30


def _monitor_path(output_folder):
    return os.path.join(output_folder, MONITOR_FILE)


def load_monitor_data(output_folder):
    """读取机型监控记录；缺失/损坏返回 {}"""
    try:
        with open(_monitor_path(output_folder), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (IOError, ValueError):
        return {}


def _atomic_write(path, data):
    """tmp + os.replace 原子写，防多 worker 并发写坏"""
    tmp = "%s.tmp" % path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _invalidate_dashboard_caches():
    """新分析记录落地后，失效仪表盘与机型监控看板的缓存。

    - file_cache：_list_filesystem_files 30s 缓存——新生成的报告文件必须立即可见，
      否则新分析完成后最长 30s 仪表盘扫不到新报告（第 62 轮 P2-1 引入缓存后的回归点）
    - query_cache（60s TTL）：dashboard_data / model_monitor 必须立即反映新记录

    FS 模式（DATABASE_ERROR 降级）不经过 data_processing 的 DB 分支，
    只有在这里统一失效，仪表盘 KPI/转速分布/看板卡片才能立即反映新记录。
    """
    try:
        from app.utils.cache_utils import file_cache, query_cache

        file_cache.clear()
        query_cache.delete("dashboard_data")
        query_cache.delete("model_monitor")
    except Exception:
        pass


def record_model_monitor(output_folder, fan_model, evaluation_report, balance_machine_model):
    """分析完成时记录该机型最新推荐转速与设备。成功返回 True，否则 False。

    每次分析都追加记录（不再去重）：完整历史是「历史次数/转速变化」检测的前提，
    展示层 history 仅取最近 5 条，不会因记录增长刷屏。
    """
    if not fan_model or not evaluation_report:
        return False
    best_speeds = evaluation_report.get("best_speeds") or []
    if not best_speeds:
        return False
    data = load_monitor_data(output_folder)
    records = data.setdefault(fan_model, [])
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "best_speeds": best_speeds,
        "best_score": round(float(evaluation_report.get("best_score") or 0), 4),
        "balance_machine_model": balance_machine_model or "",
        "has_p1": bool(evaluation_report.get("has_p1")),
        "has_p2": bool(evaluation_report.get("has_p2")),
        "has_st": bool(evaluation_report.get("has_st")),
    }
    records.append(entry)
    data[fan_model] = records[-MAX_RECORDS_PER_MODEL:]
    try:
        _atomic_write(_monitor_path(output_folder), data)
        _invalidate_dashboard_caches()
        return True
    except OSError as e:
        logger.warning("机型监控记录写入失败: %s", e)
        return False


def _calc_status(latest_time):
    """按距今天数计算状态，与 outputs 健康度语义一致：fresh/recent/stale/old"""
    try:
        latest = datetime.strptime(latest_time, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return "old"
    days = (datetime.now() - latest).total_seconds() / 86400
    if days < 1:
        return "fresh"
    if days < STALE_DAYS:
        return "recent"
    if days < OLD_DAYS:
        return "stale"
    return "old"


def build_model_monitor(output_folder, by_model_groups=None):
    """聚合看板数据：监控记录 + outputs 扫描信息 + 告警规则。"""
    data = load_monitor_data(output_folder)
    groups = {g.get("model"): g for g in (by_model_groups or [])}
    models = set(data.keys()) | set(groups.keys())
    items = []
    for model in sorted(models):
        records = data.get(model) or []
        group = groups.get(model)
        latest = records[-1] if records else {}
        latest_time = latest.get("time", "")
        # 无监控记录但有 outputs 文件时，以文件最新时间判定状态，避免误报超期
        if not latest_time and group and group.get("latest_date"):
            latest_time = group["latest_date"]
        status = _calc_status(latest_time) if latest_time else "old"
        # 转速漂移：历史推荐转速超过 1 种
        speed_set = set()
        for r in records:
            sp = r.get("best_speeds") or []
            if sp:
                speed_set.add(sp[0])
        speed_changed = len(speed_set) > 1
        best_speeds = latest.get("best_speeds") or []
        best_speed = best_speeds[0] if best_speeds else ""
        summary = (group or {}).get("summary") or {}
        tb = summary.get("type_breakdown") or {}
        has_html = "html" in tb or "htm" in tb
        has_image = bool({k for k in tb if k in ("png", "jpg", "jpeg", "svg", "webp")})
        file_count = summary.get("file_count") or 0
        missing = []
        if not has_html:
            missing.append("缺HTML")
        if not has_image and file_count >= 2:
            missing.append("缺图表")
        items.append({
            "model": model,
            "best_speed": best_speed,
            "best_score": latest.get("best_score", ""),
            "device": latest.get("balance_machine_model", ""),
            "latest_time": latest_time,
            "status": status,
            "speed_changed": speed_changed,
            "history_count": len(records),
            "report_count": file_count,
            "missing": "、".join(missing),
            "history": [
                {
                    "time": r["time"],
                    "best_speeds": r.get("best_speeds") or [],
                    "device": r.get("balance_machine_model", ""),
                }
                for r in records[-5:]
            ],
        })
    rank = {"old": 0, "stale": 1, "recent": 2, "fresh": 3}
    items.sort(key=lambda x: (rank.get(x["status"], 9), x["latest_time"] or ""))
    alert_count = sum(
        1 for i in items
        if i["status"] in ("stale", "old") or i["speed_changed"] or i["missing"]
    )
    critical_count = sum(1 for i in items if i["status"] == "old")
    return {
        "success": True,
        "items": items,
        "alert_count": alert_count,
        "critical_count": critical_count,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
