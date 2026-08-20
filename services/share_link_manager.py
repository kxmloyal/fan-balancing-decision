#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分享链接管理器（ShareLinkManager）

从 services/report_exporter.py 拆分而来——第 42 轮技术债清理。
独立管理报告分享链接的创建、查询、撤销与过期清理。

职责：
  - create_link: 创建分享链接（含过期时间）
  - revoke_link: 撤销分享链接
  - get_link / list_links: 查询分享链接
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ShareLinkManager:
    """分享链接管理器——独立管理报告分享链接的创建、查询和撤销"""

    def __init__(self, output_folder="outputs"):
        self.output_folder = output_folder
        self._links_file = os.path.join(self.output_folder, "shareable_links.json")

    def _read_links(self):
        if not os.path.exists(self._links_file):
            return []
        try:
            with open(self._links_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def _write_links(self, links):
        try:
            os.makedirs(self.output_folder, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.error("无法创建分享目录 %s: %s", self.output_folder, e)
            raise RuntimeError("分享功能暂不可用：无法写入存储目录") from e
        try:
            tmp_file = self._links_file + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(links, f, ensure_ascii=False, indent=2)
            os.replace(tmp_file, self._links_file)
        except (OSError, IOError) as e:
            logger.error("写入分享链接文件失败 %s: %s", self._links_file, e)
            raise RuntimeError("分享链接操作失败：磁盘写入错误") from e

    def create_link(self, report_path, ttl_days=7):
        link_id = str(uuid.uuid4())
        expires_at = (datetime.now() + timedelta(days=ttl_days)).isoformat()

        share_info = {
            "link_id": link_id,
            "report_path": report_path,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "ttl_days": ttl_days,
            "filename": os.path.basename(report_path),
        }

        links = self._read_links()
        now = datetime.now()
        links = [
            l
            for l in links
            if "expires_at" not in l or datetime.fromisoformat(l["expires_at"]) > now
        ]
        links.append(share_info)
        self._write_links(links)
        return link_id

    def revoke_link(self, link_id):
        links = self._read_links()
        original_count = len(links)
        links = [l for l in links if l.get("link_id") != link_id]
        if len(links) == original_count:
            return False
        self._write_links(links)
        return True

    def get_link(self, link_id):
        links = self._read_links()
        now = datetime.now()
        for link in links:
            if link.get("link_id") == link_id:
                if "expires_at" in link and datetime.fromisoformat(link["expires_at"]) <= now:
                    return None
                return link
        return None

    def list_links(self):
        links = self._read_links()
        now = datetime.now()
        return [
            l
            for l in links
            if "expires_at" not in l or datetime.fromisoformat(l["expires_at"]) > now
        ]
