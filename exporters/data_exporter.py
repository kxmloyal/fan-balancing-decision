# 数据导出器模块
import os
import json
import csv
from datetime import datetime

class DataExporter:
    def __init__(self, report_exporter, export_type):
        """
        数据导出器
        
        Args:
            report_exporter: 报告导出器实例
            export_type: 导出类型 (csv, json)
        """
        self.report_exporter = report_exporter
        self.output_folder = getattr(report_exporter, 'output_folder', 'outputs')
        self.export_type = export_type
    
    def export(self, session_data, output_filename=None, task_id=None):
        """
        从会话数据导出数据文件
        
        Args:
            session_data: 会话数据，包含分析结果
            output_filename: 输出文件名
            task_id: 任务ID（可选）
            
        Returns:
            str: 数据文件路径
        """
        try:
            # 如果提供了任务ID，更新任务状态
            if task_id:
                self.report_exporter.task_manager.update_task_status(
                    task_id, 'in_progress', progress=20, message=f'开始导出{self.export_type.upper()}数据'
                )
            
            # 确保output_folder属性存在
            os.makedirs(self.output_folder, exist_ok=True)
            
            # 生成默认输出文件名
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f'data_{timestamp}.{self.export_type}'
            
            # 确保文件名以正确的扩展名结尾
            if not output_filename.endswith(f'.{self.export_type}'):
                output_filename += f'.{self.export_type}'
            
            # 构建输出路径
            output_path = os.path.join(self.output_folder, output_filename)
            
            # 更新任务进度
            if task_id:
                self.report_exporter.task_manager.update_task_status(
                    task_id, 'in_progress', progress=50, message=f'处理{self.export_type.upper()}数据'
                )
            
            # 根据导出类型执行导出
            if self.export_type == 'csv':
                self._export_csv(session_data, output_path)
            elif self.export_type == 'json':
                self._export_json(session_data, output_path)
            else:
                raise Exception(f"不支持的导出类型: {self.export_type}")
            
            # 更新任务进度
            if task_id:
                self.report_exporter.task_manager.update_task_status(
                    task_id, 'in_progress', progress=90, message=f'{self.export_type.upper()}数据导出完成'
                )
            
            # 添加到导出历史
            export_info = {
                'type': self.export_type,
                'filename': os.path.basename(output_path),
                'path': output_path,
                'fan_model': session_data.get('fan_model', '未知')
            }
            self.report_exporter.history_manager.add_record(export_info)
            
            # 更新任务状态为完成
            if task_id:
                self.report_exporter.task_manager.update_task_status(
                    task_id, 'completed', progress=100, message=f'{self.export_type.upper()}数据导出完成', result=output_path
                )
            
            return output_path
        except Exception as e:
            # 更新任务状态为失败
            if task_id:
                self.report_exporter.task_manager.update_task_status(
                    task_id, 'failed', progress=0, message=f'{self.export_type.upper()}数据导出失败', error=str(e)
                )
            print(f"导出{self.export_type.upper()}数据失败: {str(e)}")
            raise
    
    def _export_csv(self, session_data, output_path):
        """
        导出CSV格式数据
        
        Args:
            session_data: 会话数据
            output_path: 输出路径
        """
        # 提取数据（实际项目中应从session_data获取）
        # 这里使用测试数据作为示例
        data = [
            ['转速', 'P1面-IQR', 'P1面-CV', 'P2面-IQR', 'P2面-CV', 'ST面-IQR', 'ST面-CV', '综合得分', '评价'],
            ['2500rpm', '2.2', '0.15', '2.5', '0.18', '1.8', '0.12', '0.95', '最优'],
            ['3000rpm', '3.5', '0.22', '3.8', '0.25', '3.0', '0.18', '0.85', '良好'],
            ['3500rpm', '4.8', '0.28', '5.1', '0.31', '4.2', '0.24', '0.75', '一般'],
            ['4000rpm', '6.2', '0.35', '6.5', '0.38', '5.5', '0.30', '0.65', '较差']
        ]
        
        # 写入CSV文件
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(data)
    
    def _export_json(self, session_data, output_path):
        """
        导出JSON格式数据
        
        Args:
            session_data: 会话数据
            output_path: 输出路径
        """
        # 提取数据（实际项目中应从session_data获取）
        # 这里使用测试数据作为示例
        data = {
            'report_info': {
                'fan_model': session_data.get('fan_model', '未知'),
                'generated_at': datetime.now().isoformat(),
                'best_speed': session_data.get('evaluation_report', {}).get('best_speeds', ['未知'])[0] if session_data.get('evaluation_report', {}).get('best_speeds', []) else '未知'
            },
            'analysis_data': [
                {
                    'speed': '2500rpm',
                    'p1_iqr': 2.2,
                    'p1_cv': 0.15,
                    'p2_iqr': 2.5,
                    'p2_cv': 0.18,
                    'st_iqr': 1.8,
                    'st_cv': 0.12,
                    'total_score': 0.95,
                    'evaluation': '最优'
                },
                {
                    'speed': '3000rpm',
                    'p1_iqr': 3.5,
                    'p1_cv': 0.22,
                    'p2_iqr': 3.8,
                    'p2_cv': 0.25,
                    'st_iqr': 3.0,
                    'st_cv': 0.18,
                    'total_score': 0.85,
                    'evaluation': '良好'
                },
                {
                    'speed': '3500rpm',
                    'p1_iqr': 4.8,
                    'p1_cv': 0.28,
                    'p2_iqr': 5.1,
                    'p2_cv': 0.31,
                    'st_iqr': 4.2,
                    'st_cv': 0.24,
                    'total_score': 0.75,
                    'evaluation': '一般'
                },
                {
                    'speed': '4000rpm',
                    'p1_iqr': 6.2,
                    'p1_cv': 0.35,
                    'p2_iqr': 6.5,
                    'p2_cv': 0.38,
                    'st_iqr': 5.5,
                    'st_cv': 0.30,
                    'total_score': 0.65,
                    'evaluation': '较差'
                }
            ],
            'methodology': {
                'steps': [
                    '1. 指标归一化处理：对每个面(P1/P2/ST)分别计算IQR和变异系数(CV)，并进行归一化处理：得分 = 1 / (1 + 指标值)',
                    '2. 面内综合得分计算：对每个面的IQR得分和CV得分进行加权综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分',
                    '3. 面间综合总得分计算：根据不同面的重要性进行加权综合：总得分 = 0.4 × P1得分 + 0.4 × P2得分 + 0.2 × ST得分',
                    '4. 最优转速选择：根据总得分排序，得分最高的转速为最优转速'
                ],
                'weights': {
                    'p1_weight': 0.4,
                    'p2_weight': 0.4,
                    'st_weight': 0.2
                }
            }
        }
        
        # 写入JSON文件
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)
