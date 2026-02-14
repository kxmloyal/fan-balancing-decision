# 历史记录管理器模块
import os
import json
from datetime import datetime
from .config import EXPORT_CONFIG

class HistoryManager:
    def __init__(self, output_folder=None):
        """
        历史记录管理器
        
        Args:
            output_folder: 输出目录路径
        """
        self.output_folder = output_folder or EXPORT_CONFIG['OUTPUT_FOLDER']
        self.history_file = os.path.join(self.output_folder, 'export_history.json')
        self.export_history = []
        
        # 确保输出目录存在
        os.makedirs(self.output_folder, exist_ok=True)
        
        # 加载历史记录
        self.load_history()
    
    def load_history(self):
        """
        加载导出历史记录
        """
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.export_history = json.load(f)
        except Exception as e:
            print(f"加载导出历史失败: {str(e)}")
            self.export_history = []
    
    def save_history(self):
        """
        保存导出历史记录
        """
        try:
            # 限制历史记录数量
            max_items = EXPORT_CONFIG['MAX_HISTORY_ITEMS']
            if len(self.export_history) > max_items:
                self.export_history = self.export_history[:max_items]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.export_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存导出历史失败: {str(e)}")
    
    def add_record(self, export_info):
        """
        添加导出记录
        
        Args:
            export_info: 导出信息字典
        """
        # 添加时间戳
        export_info['timestamp'] = datetime.now().isoformat()
        
        # 添加到历史记录
        self.export_history.insert(0, export_info)
        
        # 保存历史记录
        self.save_history()
    
    def get_history(self, limit=None):
        """
        获取导出历史记录
        
        Args:
            limit: 限制返回的记录数
            
        Returns:
            list: 导出历史记录
        """
        if limit:
            return self.export_history[:limit]
        return self.export_history
    
    def search_history(self, search_term=None, export_type=None, start_date=None, end_date=None, fan_model=None):
        """
        搜索和筛选导出历史记录
        
        Args:
            search_term: 搜索关键词
            export_type: 导出类型
            start_date: 开始日期
            end_date: 结束日期
            fan_model: 扇叶型号
            
        Returns:
            list: 筛选后的导出历史记录
        """
        filtered_history = self.export_history.copy()
        
        # 按导出类型筛选
        if export_type:
            filtered_history = [item for item in filtered_history if item.get('type') == export_type]
        
        # 按扇叶型号筛选
        if fan_model:
            filtered_history = [item for item in filtered_history if item.get('fan_model') == fan_model]
        
        # 按日期范围筛选
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            filtered_history = [item for item in filtered_history if datetime.fromisoformat(item.get('timestamp')) >= start_dt]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            filtered_history = [item for item in filtered_history if datetime.fromisoformat(item.get('timestamp')) <= end_dt]
        
        # 按搜索关键词筛选
        if search_term:
            search_term_lower = search_term.lower()
            filtered_history = [item for item in filtered_history if 
                              search_term_lower in str(item.get('filename', '')).lower() or 
                              search_term_lower in str(item.get('path', '')).lower() or 
                              search_term_lower in str(item.get('fan_model', '')).lower()]
        
        return filtered_history
    
    def get_statistics(self):
        """
        获取导出统计信息
        
        Returns:
            dict: 导出统计信息
        """
        stats = {
            'total_exports': len(self.export_history),
            'exports_by_type': {},
            'exports_by_model': {},
            'recent_exports': []
        }
        
        # 按类型统计
        for item in self.export_history:
            export_type = item.get('type', 'unknown')
            if export_type not in stats['exports_by_type']:
                stats['exports_by_type'][export_type] = 0
            stats['exports_by_type'][export_type] += 1
            
            # 按型号统计
            fan_model = item.get('fan_model', '未知')
            if fan_model not in stats['exports_by_model']:
                stats['exports_by_model'][fan_model] = 0
            stats['exports_by_model'][fan_model] += 1
        
        # 获取最近的5条导出记录
        stats['recent_exports'] = self.export_history[:5]
        
        return stats
    
    def clear_history(self):
        """
        清空导出历史记录
        """
        self.export_history = []
        self.save_history()
        return {'message': '导出历史已清空'}
