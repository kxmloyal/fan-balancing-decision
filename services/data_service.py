#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据处理服务
负责处理文件上传、解析和数据提取
"""

import os

from data_processing import allowed_file, parse_single_surface_file
from models.analysis_data import ParsedDataItem, SurfaceData
from utils.data_validator import generate_data_warning, validate_and_align_data


class DataProcessingService:
    """数据处理服务类"""

    def __init__(self, upload_folder):
        """初始化数据处理服务

        Args:
            upload_folder: 上传文件目录
        """
        self.upload_folder = upload_folder

    def process_file(self, file, file_prefix):
        """处理上传的文件

        Args:
            file: 上传的文件对象
            file_prefix: 文件前缀（p1_, p2_, st_）

        Returns:
            tuple: (file_path, surface_data, error_message)
        """
        try:
            allowed_extensions = {"csv", "xlsx", "xls", "json", "xml", "txt"}
            if allowed_file(file.filename, allowed_extensions):
                filename = f"{file_prefix}{file.filename}"
                file_path = os.path.join(self.upload_folder, filename)
                file.save(file_path)

                parsed_data = parse_single_surface_file(file_path)
                surface_type = file_prefix.rstrip("_")
                surface_data = SurfaceData(surface_type, parsed_data)
                return file_path, surface_data, None
            else:
                return None, None, f"文件格式不支持：{file.filename}"
        except Exception as e:
            return None, None, f"文件处理失败：{str(e)}"

    def validate_and_align(self, p1_data, p2_data, st_data=None):
        """验证和对齐数据

        Args:
            p1_data: P1面数据（SurfaceData对象或字典）
            p2_data: P2面数据（SurfaceData对象或字典）
            st_data: ST面数据（SurfaceData对象或字典，可选）

        Returns:
            tuple: (parsed_data, data_warnings)
        """
        # 处理不同类型的输入
        if isinstance(p1_data, SurfaceData):
            p1_data_dict = p1_data.data
        else:
            p1_data_dict = p1_data

        if isinstance(p2_data, SurfaceData):
            p2_data_dict = p2_data.data
        else:
            p2_data_dict = p2_data

        if isinstance(st_data, SurfaceData):
            st_data_dict = st_data.data
        else:
            st_data_dict = st_data

        parsed_data = []
        data_warnings = []

        common_speeds = set(p1_data_dict.keys()) & set(p2_data_dict.keys())

        for speed in sorted(common_speeds):
            st_samples_for_speed = st_data_dict.get(speed) if st_data_dict else None

            p1_aligned, p2_aligned, st_samples, data_info = validate_and_align_data(
                p1_data_dict[speed], p2_data_dict[speed], st_samples_for_speed
            )

            warning_msg = generate_data_warning(data_info, speed)
            if warning_msg:
                data_warnings.append(warning_msg)

            parsed_data_item = ParsedDataItem(
                speed=speed, p1_samples=p1_aligned, p2_samples=p2_aligned, sum_samples=st_samples
            )
            parsed_data.append(parsed_data_item.to_dict())

        return parsed_data, data_warnings
