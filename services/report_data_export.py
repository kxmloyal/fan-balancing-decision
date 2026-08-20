#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据格式导出器（CSV / JSON / Excel）

从 report_export.py（1350行）拆分而来——P2-14 方案 A 三层委派架构。
负责 ReportExporter 中 CSV/JSON/Excel 三种格式的导出逻辑。

职责：
  - _export_csv: CSV 格式导出
  - _export_json: JSON 格式导出
  - _export_excel: Excel 格式导出
  - _extract_stats_for_export: 从 session 数据提取统计表
"""

import json
import logging
import os
from datetime import datetime

from utils.model_utils import sanitize_model_name

logger = logging.getLogger(__name__)


class ReportDataExporter:
    """数据格式导出器——负责 CSV/JSON/Excel 导出"""

    def __init__(self, exporter):
        """
        Args:
            exporter: ReportExporter 实例，提供 output_folder/add_to_history
        """
        self._exporter = exporter

    @property
    def output_folder(self):
        return self._exporter.output_folder

    def add_to_history(self, export_info):
        self._exporter.add_to_history(export_info)

    # ========================================================================
    #  CSV 导出
    # ========================================================================

    def export_csv(self, session_data, output_filename=None):
        fan_model = str(session_data.get("fan_model", "未知"))
        safe_model = sanitize_model_name(fan_model)
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{safe_model}_统计数据_{timestamp}.csv"
        if not output_filename.endswith(".csv"):
            output_filename += ".csv"

        model_dir = sanitize_model_name(fan_model)
        model_output_dir = os.path.join(self.output_folder, model_dir)
        os.makedirs(model_output_dir, exist_ok=True)

        output_path = os.path.join(model_output_dir, output_filename)

        try:
            import pandas as pd
        except ImportError:
            raise RuntimeError("导出CSV需要安装pandas: pip install pandas")

        stats_data = self._extract_stats_for_export(session_data)
        if not stats_data:
            # 无可导出数据时不得返回不存在的文件路径（否则 send_file 404、无明确提示）
            raise ValueError("暂无统计数据可供导出，请先完成数据分析")
        df = pd.DataFrame(stats_data)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")

        self.add_to_history(
            {
                "type": "csv",
                "filename": os.path.basename(output_path),
                "path": output_path,
                "fan_model": fan_model,
                "model_dir": model_dir,
            }
        )
        return output_path

    # ========================================================================
    #  JSON 导出
    # ========================================================================

    def export_json(self, session_data, output_filename=None):
        fan_model = str(session_data.get("fan_model", "未知"))
        safe_model = sanitize_model_name(fan_model)
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{safe_model}_分析数据_{timestamp}.json"
        if not output_filename.endswith(".json"):
            output_filename += ".json"

        model_dir = sanitize_model_name(fan_model)
        model_output_dir = os.path.join(self.output_folder, model_dir)
        os.makedirs(model_output_dir, exist_ok=True)

        output_path = os.path.join(model_output_dir, output_filename)

        export_data = {
            "export_time": datetime.now().isoformat(),
            "fan_model": session_data.get("fan_model", ""),
            "balance_machine_model": session_data.get("balance_machine_model", ""),
            "evaluation_report": session_data.get("evaluation_report", {}),
            "stats_data": self._extract_stats_for_export(session_data),
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        self.add_to_history(
            {
                "type": "json",
                "filename": os.path.basename(output_path),
                "path": output_path,
                "fan_model": fan_model,
                "model_dir": model_dir,
            }
        )
        return output_path

    # ========================================================================
    #  Excel 导出
    # ========================================================================

    def export_excel(self, session_data, output_filename=None):
        try:
            import pandas as pd
        except ImportError:
            raise RuntimeError("导出Excel需要安装pandas和openpyxl: pip install pandas openpyxl")

        fan_model = str(session_data.get("fan_model", "未知"))
        safe_model = sanitize_model_name(fan_model)
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{safe_model}_分析报告_{timestamp}.xlsx"
        if not output_filename.endswith(".xlsx"):
            output_filename += ".xlsx"

        model_dir = sanitize_model_name(fan_model)
        model_output_dir = os.path.join(self.output_folder, model_dir)
        os.makedirs(model_output_dir, exist_ok=True)

        output_path = os.path.join(model_output_dir, output_filename)

        stats_data = self._extract_stats_for_export(session_data)
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            if stats_data:
                df = pd.DataFrame(stats_data)
                df.to_excel(writer, sheet_name="统计数据", index=False)

            evaluation_report = session_data.get("evaluation_report", {})
            if evaluation_report:
                eval_rows = []
                for key, value in evaluation_report.items():
                    if isinstance(value, (str, int, float, bool)):
                        eval_rows.append({"指标": key, "值": value})
                    elif isinstance(value, list):
                        eval_rows.append({"指标": key, "值": ", ".join(str(v) for v in value)})
                if eval_rows:
                    pd.DataFrame(eval_rows).to_excel(writer, sheet_name="评估结果", index=False)

        self.add_to_history(
            {
                "type": "excel",
                "filename": os.path.basename(output_path),
                "path": output_path,
                "fan_model": fan_model,
                "model_dir": model_dir,
            }
        )
        return output_path

    # ========================================================================
    #  工具方法
    # ========================================================================

    def _extract_stats_for_export(self, session_data):
        """从session数据提取可用于表格导出的统计信息"""
        evaluation_report = session_data.get("evaluation_report", {})
        speed_scores = evaluation_report.get("speed_detailed_scores", {})
        stats_data = session_data.get("stats_data", [])

        if stats_data:
            return stats_data

        if speed_scores:
            rows = []
            for speed, scores in speed_scores.items():
                if isinstance(scores, dict):
                    row = {"转速": speed}
                    for face in ["P1", "P2", "ST"]:
                        face_data = scores.get(face, {})
                        if isinstance(face_data, dict):
                            row[f"{face}-IQR"] = face_data.get("iqr")
                            row[f"{face}-CV"] = face_data.get("cv")
                            row[f"{face}-得分"] = face_data.get("face_score")
                    row["综合得分"] = scores.get("total_score")
                    rows.append(row)
            return rows

        return []
