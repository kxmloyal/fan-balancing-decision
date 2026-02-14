import unittest
import os
import tempfile
import json
from datetime import datetime
from report_export import ReportExporter

class TestReportExporter(unittest.TestCase):
    """
    报告导出器单元测试
    """
    
    def setUp(self):
        """
        测试前的设置
        """
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        
        # 初始化导出器
        self.exporter = ReportExporter()
        self.exporter.output_folder = self.temp_dir
        
        # 准备测试数据
        self.test_session_data = {
            'fan_model': 'Test Model',
            'evaluation_report': {
                'best_speeds': ['1500rpm'],
                'analysis_results': {}
            },
            'stats_html': '<table><tr><th>Speed</th><th>Value</th></tr><tr><td>1000</td><td>1.0</td></tr></table>'
        }
    
    def tearDown(self):
        """
        测试后的清理
        """
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """
        测试初始化功能
        """
        self.assertIsInstance(self.exporter, ReportExporter)
        self.assertEqual(self.exporter.output_folder, self.temp_dir)
        self.assertIsNotNone(self.exporter.exporters)
        self.assertIn('html', self.exporter.exporters)
        self.assertIn('pdf', self.exporter.exporters)
        self.assertIn('docx', self.exporter.exporters)
        self.assertIn('excel', self.exporter.exporters)
        self.assertIn('csv', self.exporter.exporters)
        self.assertIn('json', self.exporter.exporters)
    
    def test_generate_chart_cache_key(self):
        """
        测试图表缓存键生成
        """
        cache_key = self.exporter.generate_chart_cache_key('surface1', 'box', {'data': [1, 2, 3]})
        self.assertIsInstance(cache_key, str)
        self.assertIn('surface1', cache_key)
        self.assertIn('box', cache_key)
    
    def test_chart_cache_operations(self):
        """
        测试图表缓存操作
        """
        # 生成缓存键
        cache_key = self.exporter.generate_chart_cache_key('surface1', 'box', {'data': [1, 2, 3]})
        
        # 测试设置缓存
        chart_data = {'chart': 'data'}
        self.exporter.set_chart_to_cache(cache_key, chart_data)
        
        # 测试获取缓存
        cached_data = self.exporter.get_chart_from_cache(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['data'], chart_data)
        
        # 测试缓存状态
        cache_status = self.exporter.get_cache_status()
        self.assertIsInstance(cache_status, dict)
        self.assertIn('cache_size', cache_status)
        self.assertIn('max_cache_size', cache_status)
        self.assertIn('cache_items', cache_status)
        
        # 测试清空缓存
        clear_result = self.exporter.clear_chart_cache()
        self.assertEqual(clear_result['message'], '图表缓存已清空')
        self.assertEqual(clear_result['cache_size'], 0)
    
    def test_report_config_operations(self):
        """
        测试报告配置操作
        """
        # 测试获取默认配置
        default_config = self.exporter.get_default_report_config()
        self.assertIsInstance(default_config, dict)
        self.assertIn('title', default_config)
        
        # 测试设置默认配置
        new_config = {'title': 'Test Report'}
        set_result = self.exporter.set_default_report_config(new_config)
        self.assertEqual(set_result['message'], '默认报告配置已更新')
        self.assertEqual(set_result['config']['title'], 'Test Report')
        
        # 测试重置默认配置
        reset_result = self.exporter.reset_default_report_config()
        self.assertEqual(reset_result['message'], '默认报告配置已重置')
        self.assertEqual(reset_result['config']['title'], '设备不平衡量分析报告')
        
        # 测试合并配置
        user_config = {'title': 'Merged Report', 'include_summary': False}
        merged_config = self.exporter._merge_report_config(user_config)
        self.assertEqual(merged_config['title'], 'Merged Report')
        self.assertEqual(merged_config['include_summary'], False)
        self.assertTrue(merged_config['include_stats'])  # 保持默认值
    
    def test_history_operations(self):
        """
        测试历史记录操作
        """
        # 测试添加历史记录
        export_info = {
            'type': 'html',
            'filename': 'test.html',
            'path': os.path.join(self.temp_dir, 'test.html'),
            'fan_model': 'Test Model'
        }
        self.exporter.add_to_history(export_info)
        
        # 测试获取历史记录
        history = self.exporter.get_export_history()
        self.assertIsInstance(history, list)
        self.assertEqual(len(history), 1)
        
        # 测试搜索历史记录
        filtered_history = self.exporter.search_export_history(
            export_type='html',
            fan_model='Test Model'
        )
        self.assertIsInstance(filtered_history, list)
        
        # 测试获取统计信息
        stats = self.exporter.get_export_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_exports', stats)
        self.assertIn('exports_by_type', stats)
        self.assertIn('exports_by_model', stats)
        self.assertIn('recent_exports', stats)
    
    def test_task_operations(self):
        """
        测试任务操作
        """
        # 测试创建任务
        task_id = self.exporter.create_export_task('html', self.test_session_data)
        self.assertIsInstance(task_id, str)
        
        # 测试获取任务状态
        task_status = self.exporter.get_task_status(task_id)
        self.assertIsInstance(task_status, dict)
        self.assertEqual(task_status['task_id'], task_id)
        self.assertEqual(task_status['status'], 'pending')
        
        # 测试更新任务状态
        self.exporter.update_task_status(
            task_id, 'in_progress', progress=50, message='Processing'
        )
        updated_status = self.exporter.get_task_status(task_id)
        self.assertEqual(updated_status['status'], 'in_progress')
        self.assertEqual(updated_status['progress'], 50)
        self.assertEqual(updated_status['message'], 'Processing')
    
    def test_queue_operations(self):
        """
        测试队列操作
        """
        # 测试添加任务到队列
        task_id = self.exporter.add_to_queue('html', self.test_session_data)
        self.assertIsInstance(task_id, str)
        
        # 测试获取队列状态
        queue_status = self.exporter.get_queue_status()
        self.assertIsInstance(queue_status, dict)
        self.assertIn('queue_length', queue_status)
        self.assertIn('running_tasks', queue_status)
        self.assertIn('max_concurrent_tasks', queue_status)
        
        # 测试清空队列
        clear_result = self.exporter.clear_queue()
        self.assertEqual(clear_result['message'], '任务队列已清空')
        
        # 测试设置最大并发任务数
        set_result = self.exporter.set_max_concurrent_tasks(5)
        self.assertEqual(set_result['message'], '最大并发任务数已设置为5')
        self.assertEqual(set_result['max_concurrent_tasks'], 5)
    
    def test_export_method(self):
        """
        测试通用导出方法
        """
        # 测试导出方法是否存在
        self.assertTrue(hasattr(self.exporter, 'export'))
        
        # 测试不支持的导出类型
        with self.assertRaises(ValueError):
            self.exporter.export('unsupported', self.test_session_data)
    
    def test_shareable_links(self):
        """
        测试可分享链接功能
        """
        # 创建临时文件用于测试
        test_file = os.path.join(self.temp_dir, 'test.html')
        with open(test_file, 'w') as f:
            f.write('<html><body>Test</body></html>')
        
        # 测试创建可分享链接
        link_id = self.exporter.create_shareable_link(test_file, expire_hours=1)
        self.assertIsInstance(link_id, str)
        
        # 测试获取共享报告
        report_path = self.exporter.get_shared_report(link_id)
        self.assertEqual(report_path, test_file)
        
        # 测试获取不存在的链接
        invalid_path = self.exporter.get_shared_report('invalid_link')
        self.assertIsNone(invalid_path)

if __name__ == '__main__':
    unittest.main()
