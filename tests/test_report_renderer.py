#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""数据驱动报告渲染器测试（方案A+/B+/C+：封面/目录/评分明细/双轨图表/页眉脚）"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.report_exporter import ReportExporter

SAMPLE_SESSION = {
    "fan_model": "SN300-12",
    "balance_machine_model": "YWD-200",
    "chart_layout": "stacked",
    "stats_html": "<table><tr><th>转速</th><th>P1-平均值</th></tr></table>",
    "evaluation_report": {
        "best_speeds": ["3000rpm"],
        "best_score": 0.85,
        "has_p1": True,
        "has_p2": True,
        "has_st": False,
        "speed_detailed_scores": {
            "1500rpm": {"P1": {"face_score": 0.42}, "P2": {"face_score": 0.38}, "total_score": 0.32},
            "3000rpm": {"P1": {"face_score": 0.91}, "P2": {"face_score": 0.89}, "total_score": 0.85},
        },
        "all_min_iqr_speeds": {"P1": "3000rpm"},
        "all_min_cv_speeds": {"P1": "3000rpm"},
    },
    "parsed_data": [
        {"speed": "1500rpm", "p1_samples": [1, 2, 3], "p2_samples": [], "sum_samples": []},
    ],
    "plots": {
        "p1": {
            "box": {
                "png": "",
                "chart_data": '[{"name":"1500rpm","data":[1,2,3]}]',
            }
        }
    },
}


def _render(session_data):
    exporter = ReportExporter()
    return exporter.html_builder.render(session_data)


def test_render_full_structure():
    """完整结构：封面/目录/章节编号/页眉脚/双轨图表"""
    html = _render(SAMPLE_SESSION)
    assert 'class="cover"' in html
    assert 'class="toc"' in html
    assert "一、分析摘要" in html
    assert "二、最优转速评分明细" in html
    assert "六、优化建议与注意事项" in html
    assert 'class="page-header"' in html
    assert 'class="page-footer"' in html
    assert 'class="chart-plotly-container"' in html
    assert "chart_data" in html or "application/json" in html


def test_render_data_driven():
    """数据驱动：最优转速/得分/评分明细表/样本量附注"""
    html = _render(SAMPLE_SESSION)
    assert "3000rpm" in html
    assert "综合得分 0.850" in html
    assert "0.850" in html  # total_score
    assert "样本量说明" in html
    assert "P1:3组" in html


def test_render_scientific_accuracy():
    """科学性：幅值维度/归一化公式/异常过滤说明齐全，无 ECharts"""
    html = _render(SAMPLE_SESSION)
    assert "幅值合理性" in html
    assert "归一化指标值" in html
    assert "Modified Z-score" in html
    assert "echarts" not in html.lower()


def test_render_degradation_without_evaluation():
    """降级：无 evaluation_report 时不崩溃，评分章节按需隐藏"""
    session = {
        "fan_model": "SN300-12",
        "plots": {},
        "stats_html": "",
        "parsed_data": [],
    }
    html = _render(session)
    assert "未找到" in html
    assert "二、最优转速评分明细" not in html  # 无得分数据不渲染该章节
    assert "四、数据图表" not in html  # 无图表不渲染该章节
    assert "</html>" in html


def test_render_export_html_writes_file():
    """export_html 写文件 + 历史记录"""
    with tempfile.TemporaryDirectory() as tmp:
        exporter = ReportExporter()
        exporter.output_folder = tmp
        path = exporter.export_html(SAMPLE_SESSION, output_filename="renderer_check.html")
        assert os.path.exists(path)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert 'class="cover"' in content
        assert os.path.basename(path) == "renderer_check.html"


def test_render_json_escape():
    """chart_data 注入无 </script> 闭合注入风险"""
    session = dict(SAMPLE_SESSION)
    session["plots"] = {
        "p1": {"box": {"png": "", "chart_data": '[{"name":"x</script><script>alert(1)</script>"}]'}}
    }
    html = _render(session)
    assert "</script><script>alert(1)" not in html
    assert "application/json" in html
