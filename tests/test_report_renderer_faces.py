#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""评分明细"只展示有数据的面"逻辑测试（差异1修复：has_* 判定以 face_score 为准）"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.report_exporter import ReportExporter


def _render(session_data):
    exporter = ReportExporter()
    return exporter.html_builder.render(session_data)


def test_scores_only_available_faces():
    """仅 P1 有得分时，评分明细不含 P2/ST 列"""
    session = {
        "fan_model": "SN300-12",
        "stats_html": "",
        "evaluation_report": {
            "best_speeds": ["3000rpm"],
            "has_p1": True,
            "has_p2": False,
            "has_st": False,
            "speed_detailed_scores": {
                "3000rpm": {"P1": {"face_score": 0.9}, "P2": {"face_score": None}, "total_score": 0.36},
            },
        },
        "plots": {},
        "parsed_data": [],
    }
    html = _render(session)
    scores_sec = html.split('id="sec-scores"')[1]
    assert '<th class="face">P1面</th>' in scores_sec
    assert '<th class="face">P2面</th>' not in scores_sec
    assert '<th class="face">ST面</th>' not in scores_sec


def test_scores_face_scores_fallback_without_has_keys():
    """evaluation 缺 has_* 键时，基于 face_score 判定列（修复死逻辑：scores 键是转速非面）"""
    session = {
        "fan_model": "SN300-12",
        "stats_html": "",
        "evaluation_report": {
            "best_speeds": ["3000rpm"],
            "speed_detailed_scores": {
                "3000rpm": {"P1": {"face_score": 0.9}, "P2": {"face_score": 0.8}, "total_score": 0.68},
            },
        },
        "plots": {},
        "parsed_data": [],
    }
    html = _render(session)
    scores_sec = html.split('id="sec-scores"')[1]
    assert '<th class="face">P1面</th>' in scores_sec
    assert '<th class="face">P2面</th>' in scores_sec
    assert '<th class="face">ST面</th>' not in scores_sec  # ST 无 face_score → 不渲染
