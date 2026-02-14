import unittest
import os
import tempfile
import json
from datetime import datetime
from report_export import ReportExporter

class TestIntegration(unittest.TestCase):
    """
    集成测试
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
            'fan_model': 'Integration Test Model',
            'evaluation_report': {
                'best_speeds': ['1500rpm'],
                'analysis_results': {
                    'surface1': {
                        'speeds': [1000, 1200, 1400, 1600, 1800, 2000],
                        'iqr_values': [0.5, 0.4, 0.3, 0.6, 0.8, 1.0],
                        'cv_values': [0.1, 0.08, 0.06, 0.12, 0.16, 0.2]
                    }
                }
            },
            'stats_html': '''
            <table>
                <tr><th>转速</th><th>平均值</th><th>标准差</th><th>IQR</th><th>变异系数</th><th>综合评价</th></tr>
                <tr><td>1000</td><td>1.0</td><td>0.1</td><td>0.5</td><td>0.1</td><td>良好</td></tr>
                <tr><td>1200</td><td>0.9</td><td>0.08</td><td>0.4</td><td>0.08</td><td>良好</td></tr>
                <tr><td>1400</td><td>0.8</td><td>0.06</td><td>0.3</td><td>0.06</td><td>优秀</td></tr>
                <tr><td>1600</td><td>1.2</td><td>0.12</td><td>0.6</td><td>0.12</td><td>一般</td></tr>
                <tr><td>1800</td><td>1.5</td><td>0.16</td><td>0.8</td><td>0.16</td><td>较差</td></tr>
                <tr><td>2000</td><td>1.8</td><td>0.2</td><td>1.0</td><td>0.2</td><td>较差</td></tr>
            </table>
            '''
        }
    
    def tearDown(self):
        """
        测试后的清理
        """
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_html_export(self):
        """
        测试HTML导出
        """
        try:
            # 导出HTML
            html_path = self.exporter.export('html', self.test_session_data, 'test_integration.html')
            
            # 验证文件存在
            self.assertTrue(os.path.exists(html_path))
            self.assertTrue(html_path.endswith('.html'))
            
            # 验证文件大小
            self.assertTrue(os.path.getsize(html_path) > 0)
            
            # 验证文件内容
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('Integration Test Model', content)
                self.assertIn('1500rpm', content)
                self.assertIn('分析摘要', content)
                self.assertIn('统计分析结果', content)
                
            print(f"HTML导出测试成功: {html_path}")
        except Exception as e:
            self.fail(f"HTML导出测试失败: {str(e)}")
    
    def test_csv_export(self):
        """
        测试CSV导出
        """
        try:
            # 导出CSV
            csv_path = self.exporter.export('csv', self.test_session_data, 'test_integration.csv')
            
            # 验证文件存在
            self.assertTrue(os.path.exists(csv_path))
            self.assertTrue(csv_path.endswith('.csv'))
            
            # 验证文件大小
            self.assertTrue(os.path.getsize(csv_path) > 0)
            
            # 验证文件内容
            with open(csv_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('转速', content)
                self.assertIn('平均值', content)
                self.assertIn('标准差', content)
                self.assertIn('1000', content)
                self.assertIn('1.0', content)
                
            print(f"CSV导出测试成功: {csv_path}")
        except Exception as e:
            self.fail(f"CSV导出测试失败: {str(e)}")
    
    def test_json_export(self):
        """
        测试JSON导出
        """
        try:
            # 导出JSON
            json_path = self.exporter.export('json', self.test_session_data, 'test_integration.json')
            
            # 验证文件存在
            self.assertTrue(os.path.exists(json_path))
            self.assertTrue(json_path.endswith('.json'))
            
            # 验证文件大小
            self.assertTrue(os.path.getsize(json_path) > 0)
            
            # 验证文件内容
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.assertIsInstance(data, dict)
                self.assertIn('fan_model', data)
                self.assertEqual(data['fan_model'], 'Integration Test Model')
                self.assertIn('evaluation_report', data)
                
            print(f"JSON导出测试成功: {json_path}")
        except Exception as e:
            self.fail(f"JSON导出测试失败: {str(e)}")
    
    def test_batch_export(self):
        """
        测试批量导出
        """
        try:
            # 定义批量导出任务
            export_tasks = [
                {'session_data': self.test_session_data, 'export_type': 'html', 'output_filename': 'batch_html.html'},
                {'session_data': self.test_session_data, 'export_type': 'csv', 'output_filename': 'batch_csv.csv'},
                {'session_data': self.test_session_data, 'export_type': 'json', 'output_filename': 'batch_json.json'}
            ]
            
            # 执行批量导出
            results = self.exporter.batch_export(export_tasks, concurrent=False)
            
            # 验证结果
            self.assertIsInstance(results, dict)
            self.assertIn('success', results)
            self.assertIn('failed', results)
            
            # 验证成功的任务数
            self.assertEqual(len(results['success']), 3)
            self.assertEqual(len(results['failed']), 0)
            
            # 验证文件存在
            for item in results['success']:
                result_path = item['result']
                self.assertTrue(os.path.exists(result_path))
                self.assertTrue(os.path.getsize(result_path) > 0)
                print(f"批量导出成功: {result_path}")
                
            print("批量导出测试成功")
        except Exception as e:
            self.fail(f"批量导出测试失败: {str(e)}")
    
    def test_report_customization(self):
        """
        测试报告定制化
        """
        try:
            # 定义自定义配置
            custom_config = {
                'title': 'Custom Integration Test Report',
                'include_summary': True,
                'include_stats': True,
                'include_charts': False,  # 不包含图表
                'include_methodology': False,  # 不包含方法说明
                'include_recommendations': True,
                'include_technical_details': False,  # 不包含技术细节
                'chart_layout': 'stacked',
                'custom_css': 'body { font-family: Arial, sans-serif; }',
                'custom_header': '<div style="text-align: center; padding: 20px;"><h3>Custom Header</h3></div>',
                'custom_footer': '<div style="text-align: center; padding: 20px;"><p>Custom Footer</p></div>'
            }
            
            # 导出自定义报告
            html_path = self.exporter.export('html', self.test_session_data, 'custom_report.html', report_config=custom_config)
            
            # 验证文件存在
            self.assertTrue(os.path.exists(html_path))
            self.assertTrue(os.path.getsize(html_path) > 0)
            
            # 验证文件内容
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('Custom Integration Test Report', content)
                self.assertIn('Custom Header', content)
                self.assertIn('Custom Footer', content)
                self.assertIn('font-family: Arial, sans-serif', content)
                
            print(f"报告定制化测试成功: {html_path}")
        except Exception as e:
            self.fail(f"报告定制化测试失败: {str(e)}")
    
    def test_task_queue(self):
        """
        测试任务队列
        """
        try:
            # 添加任务到队列
            task_id = self.exporter.add_to_queue('html', self.test_session_data, 'queue_test.html')
            self.assertIsInstance(task_id, str)
            
            # 获取任务状态
            task_status = self.exporter.get_task_status(task_id)
            self.assertIsInstance(task_status, dict)
            self.assertEqual(task_status['task_id'], task_id)
            
            # 获取队列状态
            queue_status = self.exporter.get_queue_status()
            self.assertIsInstance(queue_status, dict)
            self.assertIn('queue_length', queue_status)
            self.assertIn('running_tasks', queue_status)
            
            # 清空队列
            clear_result = self.exporter.clear_queue()
            self.assertEqual(clear_result['message'], '任务队列已清空')
            
            print("任务队列测试成功")
        except Exception as e:
            self.fail(f"任务队列测试失败: {str(e)}")

if __name__ == '__main__':
    unittest.main()
