# 模块导入
import os
import tempfile
import json
from datetime import datetime
import uuid
import re
import html

# 导出格式处理器模块
from .exporters.html_exporter import HtmlExporter
from .exporters.pdf_exporter import PdfExporter
from .exporters.docx_exporter import DocxExporter
from .exporters.excel_exporter import ExcelExporter
from .exporters.data_exporter import DataExporter

# 任务管理模块
from .task_manager import TaskManager

# 历史记录模块
from .history_manager import HistoryManager

# 配置模块
from .config import EXPORT_CONFIG, WEASYPRINT_AVAILABLE

# 尝试导入weasyprint
if WEASYPRINT_AVAILABLE:
    try:
        from weasyprint import HTML, CSS
    except Exception as e:
        print(f"导入weasyprint失败: {str(e)}")
        WEASYPRINT_AVAILABLE = False

class ReportExporter:
    def __init__(self, app=None):
        """
        报告导出器主类
        
        Args:
            app: Flask应用实例（可选）
        """
        self.app = app
        self.output_folder = 'outputs'
        
        # 初始化子模块
        self.task_manager = TaskManager()
        self.history_manager = HistoryManager()
        
        # 初始化导出器
        self.exporters = {
            'html': HtmlExporter(self),
            'pdf': PdfExporter(self),
            'docx': DocxExporter(self),
            'excel': ExcelExporter(self),
            'csv': DataExporter(self, 'csv'),
            'json': DataExporter(self, 'json')
        }
        
        # 初始化图表渲染缓存
        self.chart_cache = {}
        self.cache_max_size = 100  # 缓存最大容量
        
        # 初始化报告定制化默认配置
        self.default_report_config = {
            'title': '设备不平衡量分析报告',
            'include_summary': True,
            'include_stats': True,
            'include_charts': True,
            'include_methodology': True,
            'include_recommendations': True,
            'include_usage_notes': True,
            'include_technical_details': True,
            'chart_types': ['box', 'violin', 'scatter', 'histogram'],
            'chart_layout': 'parallel',  # parallel, stacked
            'custom_css': '',
            'custom_header': '',
            'custom_footer': ''
        }
        
        # 初始化导出历史
        self.export_history = []
        self.history_file = os.path.join(self.output_folder, 'export_history.json')
        
        # 初始化任务管理
        self.export_tasks = {}
        self.task_queue = []
        self.running_tasks = set()
        self.max_concurrent_tasks = 3
        
        # 初始化可分享链接
        self.shareable_links = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        self.output_folder = app.config.get('OUTPUT_FOLDER', 'outputs')
        os.makedirs(self.output_folder, exist_ok=True)
        # 创建历史记录文件
        self.history_file = os.path.join(self.output_folder, 'export_history.json')
        # 加载历史记录
        self.load_export_history()
    
    def generate_chart_cache_key(self, surface_name, chart_type, chart_data):
        """
        生成图表缓存键
        
        Args:
            surface_name: 面名称
            chart_type: 图表类型
            chart_data: 图表数据
            
        Returns:
            str: 缓存键
        """
        import hashlib
        # 将图表数据转换为字符串并计算哈希值
        data_str = str(surface_name) + str(chart_type) + str(chart_data)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"{surface_name}_{chart_type}_{data_hash}"
    
    def get_chart_from_cache(self, cache_key):
        """
        从缓存中获取图表
        
        Args:
            cache_key: 缓存键
            
        Returns:
            dict or None: 缓存的图表数据，如果不存在则返回None
        """
        return self.chart_cache.get(cache_key, None)
    
    def set_chart_to_cache(self, cache_key, chart_data):
        """
        将图表添加到缓存
        
        Args:
            cache_key: 缓存键
            chart_data: 图表数据
        """
        # 检查缓存大小，如果超过限制则清理
        if len(self.chart_cache) >= self.cache_max_size:
            self.clear_oldest_cache()
        
        # 添加到缓存
        self.chart_cache[cache_key] = {
            'data': chart_data,
            'timestamp': datetime.now().timestamp()
        }
    
    def clear_oldest_cache(self):
        """
        清理最旧的缓存项
        """
        if self.chart_cache:
            # 按时间戳排序，删除最旧的
            oldest_key = min(self.chart_cache.items(), key=lambda x: x[1]['timestamp'])[0]
            del self.chart_cache[oldest_key]
    
    def clear_chart_cache(self):
        """
        清空图表缓存
        """
        self.chart_cache = {}
        return {'message': '图表缓存已清空', 'cache_size': 0}
    
    def get_cache_status(self):
        """
        获取缓存状态
        
        Returns:
            dict: 缓存状态信息
        """
        return {
            'cache_size': len(self.chart_cache),
            'max_cache_size': self.cache_max_size,
            'cache_items': list(self.chart_cache.keys())
        }
    
    def export_html_to_pdf(self, html_content, output_filename=None, header_text=None, footer_text=None):
        """
        将HTML内容转换为PDF格式
        
        Args:
            html_content: HTML内容
            output_filename: 输出文件名
            header_text: PDF页眉文本
            footer_text: PDF页脚文本
            
        Returns:
            str: PDF文件路径
            
        Raises:
            Exception: 当weasyprint不可用或PDF导出失败时抛出异常
        """
        # 检查weasyprint是否可用
        if not WEASYPRINT_AVAILABLE:
            raise Exception("PDF导出功能依赖的weasyprint库不可用，请安装weasyprint及其依赖（在Windows上需要GTK+运行时）。详细安装指南请参考项目根目录下的WEASYPRINT_INSTALLATION_GUIDE.md文件。")
        
        try:
            # 确保output_folder属性存在
            if not hasattr(self, 'output_folder'):
                self.output_folder = 'outputs'
                os.makedirs(self.output_folder, exist_ok=True)
            
            # 生成默认输出文件名
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f"report_{timestamp}.pdf"
            
            # 确保文件名以.pdf结尾
            if not output_filename.endswith('.pdf'):
                output_filename += '.pdf'
            
            # 构建输出路径
            output_path = os.path.join(self.output_folder, output_filename)
            
            # 生成页眉页脚文本
            header_text = header_text or '扇叶平衡补土转速评估工具'
            footer_text = footer_text or f'生成时间: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}'
            
            # 定义PDF样式
            css_string = """
                @page {
                    size: A4;
                    margin: 2cm;
                    @top-center {
                        content: "{header_text}";
                        font-size: 12pt;
                        font-weight: bold;
                        color: #333;
                    }
                    @bottom-center {
                        content: "{footer_text}";
                        font-size: 10pt;
                        color: #666;
                    }
                }
                body {
                    font-family: SimSun, serif;
                    font-size: 11pt;
                    line-height: 1.6;
                    color: #333;
                }
                h1, h2, h3, h4, h5, h6 {
                    color: #007bff;
                    margin-top: 1.5em;
                    margin-bottom: 0.5em;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 1em 0;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }
                th {
                    background-color: #f2f2f2;
                    font-weight: bold;
                }
                .chart-container {
                    margin: 1em 0;
                    text-align: center;
                }
                .alert {
                    padding: 1em;
                    margin: 1em 0;
                    border-radius: 4px;
                }
                .alert-warning {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                }
                .card {
                    margin: 1em 0;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    overflow: hidden;
                }
                .card-header {
                    background-color: #f8f9fa;
                    padding: 1em;
                    border-bottom: 1px solid #ddd;
                }
                .card-body {
                    padding: 1em;
                }
            """
            # 使用字符串替换变量
            css_string = css_string.replace('{header_text}', header_text)
            css_string = css_string.replace('{footer_text}', footer_text)
            css = CSS(string=css_string)
            
            # 将HTML转换为PDF
            html = HTML(string=html_content)
            html.write_pdf(output_path, stylesheets=[css])
            
            return output_path
        except Exception as e:
            print(f"PDF导出失败: {str(e)}")
            raise
    
    def load_export_history(self):
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
    
    def save_export_history(self):
        """
        保存导出历史记录
        """
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.export_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存导出历史失败: {str(e)}")
    
    def create_shareable_link(self, report_path, expire_hours=24):
        """
        创建可分享的报告链接
        
        Args:
            report_path: 报告文件路径
            expire_hours: 链接过期时间（小时）
            
        Returns:
            str: 可分享的链接ID
        """
        try:
            # 生成唯一链接ID
            link_id = str(uuid.uuid4())[:8]
            
            # 计算过期时间
            expire_time = datetime.now().timestamp() + (expire_hours * 3600)
            
            # 保存链接信息
            self.shareable_links[link_id] = {
                'report_path': report_path,
                'expire_time': expire_time,
                'created_at': datetime.now().isoformat()
            }
            
            # 保存到文件
            links_file = os.path.join(self.output_folder, 'shareable_links.json')
            with open(links_file, 'w', encoding='utf-8') as f:
                json.dump(self.shareable_links, f, ensure_ascii=False, indent=2)
            
            return link_id
        except Exception as e:
            print(f"创建可分享链接失败: {str(e)}")
            return None
    
    def get_shared_report(self, link_id):
        """
        根据链接ID获取共享报告
        
        Args:
            link_id: 链接ID
            
        Returns:
            str: 报告文件路径，如果链接无效或过期则返回None
        """
        try:
            # 检查链接是否存在
            if link_id not in self.shareable_links:
                return None
            
            # 检查链接是否过期
            link_info = self.shareable_links[link_id]
            if datetime.now().timestamp() > link_info['expire_time']:
                # 移除过期链接
                del self.shareable_links[link_id]
                links_file = os.path.join(self.output_folder, 'shareable_links.json')
                with open(links_file, 'w', encoding='utf-8') as f:
                    json.dump(self.shareable_links, f, ensure_ascii=False, indent=2)
                return None
            
            # 检查文件是否存在
            if not os.path.exists(link_info['report_path']):
                return None
            
            return link_info['report_path']
        except Exception as e:
            print(f"获取共享报告失败: {str(e)}")
            return None
    
    def get_export_history(self, limit=None):
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
    
    def search_export_history(self, search_term=None, export_type=None, start_date=None, end_date=None, fan_model=None):
        """
        搜索和筛选导出历史记录
        
        Args:
            search_term: 搜索关键词（可搜索文件名、路径等）
            export_type: 导出类型（html, pdf, docx, excel, csv, json）
            start_date: 开始日期（ISO格式字符串）
            end_date: 结束日期（ISO格式字符串）
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
    
    def get_export_statistics(self):
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
    
    def batch_export(self, export_tasks, concurrent=False):
        """
        批量导出多个报告
        
        Args:
            export_tasks: 导出任务列表，每个任务包含以下字段：
                - session_data: 会话数据
                - export_type: 导出类型（html, pdf, docx, excel, csv, json）
                - output_filename: 输出文件名（可选）
            concurrent: 是否并发执行（默认False）
            
        Returns:
            dict: 批量导出结果，包含成功和失败的任务
        """
        results = {
            'success': [],
            'failed': []
        }
        
        # 创建批量任务ID
        batch_id = str(uuid.uuid4())
        
        # 如果并发执行
        if concurrent:
            import concurrent.futures
            
            def execute_task(task, task_index):
                task_id = f"{batch_id}_{task_index}"
                try:
                    session_data = task['session_data']
                    export_type = task['export_type']
                    output_filename = task.get('output_filename')
                    
                    # 根据导出类型调用相应的方法
                    if export_type == 'html':
                        result_path = self.export_html(session_data, output_filename, task_id)
                    elif export_type == 'pdf':
                        result_path = self.export_report_from_session(session_data, output_filename)
                    elif export_type == 'docx':
                        result_path = self.export_docx(session_data, output_filename, task_id)
                    elif export_type == 'excel':
                        result_path = self.export_excel(session_data, output_filename)
                    elif export_type == 'csv':
                        result_path = self.export_csv(session_data, output_filename)
                    elif export_type == 'json':
                        result_path = self.export_json(session_data, output_filename)
                    else:
                        raise Exception(f"不支持的导出类型: {export_type}")
                    
                    return {
                        'task_index': task_index,
                        'task_id': task_id,
                        'status': 'success',
                        'result': result_path
                    }
                except Exception as e:
                    return {
                        'task_index': task_index,
                        'task_id': task_id,
                        'status': 'failed',
                        'error': str(e)
                    }
            
            # 使用线程池并发执行任务
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_task = {executor.submit(execute_task, task, i): i for i, task in enumerate(export_tasks)}
                
                for future in concurrent.futures.as_completed(future_to_task):
                    result = future.result()
                    if result['status'] == 'success':
                        results['success'].append(result)
                    else:
                        results['failed'].append(result)
        else:
            # 顺序执行任务
            for i, task in enumerate(export_tasks):
                task_id = f"{batch_id}_{i}"
                try:
                    session_data = task['session_data']
                    export_type = task['export_type']
                    output_filename = task.get('output_filename')
                    
                    # 根据导出类型调用相应的方法
                    if export_type == 'html':
                        result_path = self.export_html(session_data, output_filename, task_id)
                    elif export_type == 'pdf':
                        result_path = self.export_report_from_session(session_data, output_filename)
                    elif export_type == 'docx':
                        result_path = self.export_docx(session_data, output_filename, task_id)
                    elif export_type == 'excel':
                        result_path = self.export_excel(session_data, output_filename)
                    elif export_type == 'csv':
                        result_path = self.export_csv(session_data, output_filename)
                    elif export_type == 'json':
                        result_path = self.export_json(session_data, output_filename)
                    else:
                        raise Exception(f"不支持的导出类型: {export_type}")
                    
                    results['success'].append({
                        'task_index': i,
                        'task_id': task_id,
                        'status': 'success',
                        'result': result_path
                    })
                except Exception as e:
                    results['failed'].append({
                        'task_index': i,
                        'task_id': task_id,
                        'status': 'failed',
                        'error': str(e)
                    })
        
        return results
    
    def create_export_task(self, task_type, session_data):
        """
        创建导出任务
        
        Args:
            task_type: 任务类型 (html, pdf, docx, excel, csv, json)
            session_data: 会话数据
            
        Returns:
            str: 任务ID
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        self.export_tasks[task_id] = {
            'task_id': task_id,
            'task_type': task_type,
            'status': 'pending',  # pending, in_progress, completed, failed
            'progress': 0,
            'message': '任务已创建',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'result': None,
            'error': None
        }
        
        return task_id
    
    def update_task_status(self, task_id, status, progress=None, message=None, result=None, error=None):
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 任务状态 (pending, in_progress, completed, failed)
            progress: 进度百分比 (0-100)
            message: 状态消息
            result: 任务结果
            error: 错误信息
        """
        if task_id in self.export_tasks:
            self.export_tasks[task_id]['status'] = status
            if progress is not None:
                self.export_tasks[task_id]['progress'] = progress
            if message:
                self.export_tasks[task_id]['message'] = message
            if result:
                self.export_tasks[task_id]['result'] = result
            if error:
                self.export_tasks[task_id]['error'] = error
            self.export_tasks[task_id]['updated_at'] = datetime.now().isoformat()
    
    def get_task_status(self, task_id):
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict: 任务状态信息
        """
        return self.export_tasks.get(task_id, None)
    
    def add_to_queue(self, task_type, session_data, output_filename=None):
        """
        将导出任务添加到队列
        
        Args:
            task_type: 任务类型 (html, pdf, docx, excel, csv, json)
            session_data: 会话数据
            output_filename: 输出文件名
            
        Returns:
            str: 任务ID
        """
        task_id = self.create_export_task(task_type, session_data)
        
        # 将任务添加到队列
        self.task_queue.append({
            'task_id': task_id,
            'task_type': task_type,
            'session_data': session_data,
            'output_filename': output_filename
        })
        
        # 立即处理队列
        self.process_queue()
        
        return task_id
    
    def process_queue(self):
        """
        处理任务队列
        """
        import threading
        
        # 检查是否有空闲槽位
        while len(self.running_tasks) < self.max_concurrent_tasks and self.task_queue:
            task = self.task_queue.pop(0)
            task_id = task['task_id']
            
            # 更新任务状态为排队中
            self.update_task_status(task_id, 'queued', progress=0, message='任务已加入队列')
            
            # 启动线程执行任务
            thread = threading.Thread(target=self.execute_task_from_queue, args=(task,))
            thread.daemon = True
            thread.start()
    
    def execute_task_from_queue(self, task):
        """
        从队列中执行任务
        
        Args:
            task: 任务信息
        """
        task_id = task['task_id']
        task_type = task['task_type']
        session_data = task['session_data']
        output_filename = task.get('output_filename')
        
        try:
            # 将任务添加到运行集合
            self.running_tasks.add(task_id)
            
            # 更新任务状态为执行中
            self.update_task_status(task_id, 'in_progress', progress=10, message=f'开始执行{task_type}导出任务')
            
            # 根据任务类型执行导出
            if task_type == 'html':
                result_path = self.export_html(session_data, output_filename, task_id)
            elif task_type == 'pdf':
                result_path = self.export_report_from_session(session_data, output_filename)
            elif task_type == 'docx':
                result_path = self.export_docx(session_data, output_filename, task_id)
            elif task_type == 'excel':
                result_path = self.export_excel(session_data, output_filename)
            elif task_type == 'csv':
                result_path = self.export_csv(session_data, output_filename)
            elif task_type == 'json':
                result_path = self.export_json(session_data, output_filename)
            else:
                raise Exception(f"不支持的导出类型: {task_type}")
            
            # 更新任务状态为完成
            self.update_task_status(task_id, 'completed', progress=100, message='导出任务完成', result=result_path)
            
        except Exception as e:
            # 更新任务状态为失败
            self.update_task_status(task_id, 'failed', progress=0, message='导出任务失败', error=str(e))
            print(f"执行队列任务失败: {str(e)}")
        finally:
            # 从运行集合中移除任务
            if task_id in self.running_tasks:
                self.running_tasks.remove(task_id)
            
            # 继续处理队列
            self.process_queue()
    
    def get_queue_status(self):
        """
        获取队列状态
        
        Returns:
            dict: 队列状态信息
        """
        return {
            'queue_length': len(self.task_queue),
            'running_tasks': len(self.running_tasks),
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'queue': [{
                'task_id': task['task_id'],
                'task_type': task['task_type']
            } for task in self.task_queue]
        }
    
    def clear_queue(self):
        """
        清空任务队列
        """
        self.task_queue = []
        return {'message': '任务队列已清空'}
    
    def set_max_concurrent_tasks(self, max_tasks):
        """
        设置最大并发任务数
        
        Args:
            max_tasks: 最大并发任务数
            
        Returns:
            dict: 设置结果
        """
        if max_tasks > 0:
            self.max_concurrent_tasks = max_tasks
            # 重新处理队列
            self.process_queue()
            return {'message': f'最大并发任务数已设置为{max_tasks}', 'max_concurrent_tasks': max_tasks}
        else:
            return {'message': '最大并发任务数必须大于0'}
    
    def add_to_history(self, export_info):
        """
        添加导出记录到历史
        
        Args:
            export_info: 导出信息字典
        """
        # 添加时间戳
        export_info['timestamp'] = datetime.now().isoformat()
        # 添加到历史记录
        self.export_history.insert(0, export_info)
        # 限制历史记录数量
        if len(self.export_history) > 100:
            self.export_history = self.export_history[:100]
        # 保存历史记录
        self.save_export_history()
    
    def export_report_from_session(self, session_data, output_filename=None):
        """
        从会话数据导出PDF报告
        
        Args:
            session_data: 会话数据，包含分析结果
            output_filename: 输出文件名
            
        Returns:
            str: PDF文件路径
            
        Raises:
            Exception: 当weasyprint不可用或PDF导出失败时抛出异常
        """
        # 检查weasyprint是否可用
        if not WEASYPRINT_AVAILABLE:
            raise Exception("PDF导出功能依赖的weasyprint库不可用，请安装weasyprint及其依赖（在Windows上需要GTK+运行时）。详细安装指南请参考项目根目录下的WEASYPRINT_INSTALLATION_GUIDE.md文件。")
        
        try:
            # 构建HTML内容
            html_content = self.build_report_html(session_data)
            
            # 导出为PDF
            pdf_path = self.export_html_to_pdf(html_content, output_filename)
            
            # 添加到导出历史
            export_info = {
                'type': 'pdf',
                'filename': os.path.basename(pdf_path),
                'path': pdf_path,
                'fan_model': session_data.get('fan_model', '未知')
            }
            self.add_to_history(export_info)
            
            return pdf_path
        except Exception as e:
            print(f"从会话数据导出PDF失败: {str(e)}")
            raise
    
    def export_html(self, session_data, output_filename=None, task_id=None, report_config=None):
        """
        从会话数据导出HTML报告
        
        Args:
            session_data: 会话数据，包含分析结果
            output_filename: 输出文件名
            task_id: 任务ID（可选）
            report_config: 报告定制化配置（可选）
            
        Returns:
            str: HTML文件路径
        """
        try:
            # 如果提供了任务ID，更新任务状态
            if task_id:
                self.update_task_status(task_id, 'in_progress', progress=20, message='开始构建HTML内容')
            
            # 使用默认配置或用户提供的配置
            config = self._merge_report_config(report_config)
            
            # 生成默认输出文件名
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f"report_{timestamp}.html"
            
            # 确保文件名以.html结尾
            if not output_filename.endswith('.html'):
                output_filename += '.html'
            
            # 构建输出路径
            if not hasattr(self, 'output_folder'):
                self.output_folder = 'outputs'
                os.makedirs(self.output_folder, exist_ok=True)
            output_path = os.path.join(self.output_folder, output_filename)
            
            # 更新任务进度
            if task_id:
                self.update_task_status(task_id, 'in_progress', progress=30, message='准备流式写入HTML文件')
            
            # 使用流式写入方式生成HTML报告
            with open(output_path, 'w', encoding='utf-8') as f:
                # 写入HTML头部
                self._write_html_header(f, session_data, config)
                
                # 更新任务进度
                if task_id:
                    self.update_task_status(task_id, 'in_progress', progress=40, message='写入HTML头部完成')
                
                # 写入分析摘要
                if config.get('include_summary', True):
                    self._write_html_summary(f, session_data)
                    
                    # 更新任务进度
                    if task_id:
                        self.update_task_status(task_id, 'in_progress', progress=50, message='写入分析摘要完成')
                
                # 写入统计分析结果
                if config.get('include_stats', True):
                    self._write_html_stats(f, session_data)
                    
                    # 更新任务进度
                    if task_id:
                        self.update_task_status(task_id, 'in_progress', progress=60, message='写入统计分析结果完成')
                
                # 写入图表
                if config.get('include_charts', True):
                    self._write_html_charts(f, session_data, config)
                    
                    # 更新任务进度
                    if task_id:
                        self.update_task_status(task_id, 'in_progress', progress=70, message='写入图表完成')
                
                # 写入统计分析方法说明
                if config.get('include_methodology', True):
                    self._write_html_methodology(f)
                    
                    # 更新任务进度
                    if task_id:
                        self.update_task_status(task_id, 'in_progress', progress=80, message='写入统计分析方法说明完成')
                
                # 写入优化建议和技术细节
                if config.get('include_recommendations', True) or config.get('include_technical_details', True):
                    self._write_html_recommendations(f, config)
                    
                    # 更新任务进度
                    if task_id:
                        self.update_task_status(task_id, 'in_progress', progress=90, message='写入优化建议完成')
                
                # 写入HTML尾部
                self._write_html_footer(f, config)
            
            # 添加到导出历史
            export_info = {
                'type': 'html',
                'filename': os.path.basename(output_path),
                'path': output_path,
                'fan_model': session_data.get('fan_model', '未知'),
                'report_config': config
            }
            self.add_to_history(export_info)
            
            # 更新任务状态为完成
            if task_id:
                self.update_task_status(task_id, 'completed', progress=100, message='HTML报告导出完成', result=output_path)
            
            return output_path
        except Exception as e:
            # 更新任务状态为失败
            if task_id:
                self.update_task_status(task_id, 'failed', progress=0, message='HTML报告导出失败', error=str(e))
            print(f"导出HTML报告失败: {str(e)}")
            raise
    
    def _merge_report_config(self, user_config):
        """
        合并用户配置和默认配置
        
        Args:
            user_config: 用户提供的配置
            
        Returns:
            dict: 合并后的配置
        """
        config = self.default_report_config.copy()
        if user_config:
            config.update(user_config)
        return config
    
    def get_default_report_config(self):
        """
        获取默认报告配置
        
        Returns:
            dict: 默认配置
        """
        return self.default_report_config.copy()
    
    def set_default_report_config(self, config):
        """
        设置默认报告配置
        
        Args:
            config: 新的默认配置
        """
        self.default_report_config.update(config)
        return {'message': '默认报告配置已更新', 'config': self.default_report_config}
    
    def reset_default_report_config(self):
        """
        重置默认报告配置
        
        Returns:
            dict: 重置后的默认配置
        """
        self.default_report_config = {
            'title': '设备不平衡量分析报告',
            'include_summary': True,
            'include_stats': True,
            'include_charts': True,
            'include_methodology': True,
            'include_recommendations': True,
            'include_usage_notes': True,
            'include_technical_details': True,
            'chart_types': ['box', 'violin', 'scatter', 'histogram'],
            'chart_layout': 'parallel',  # parallel, stacked
            'custom_css': '',
            'custom_header': '',
            'custom_footer': ''
        }
        return {'message': '默认报告配置已重置', 'config': self.default_report_config}
    
    def _validate_input(self, export_type, session_data, output_filename):
        """
        验证输入参数
        
        Args:
            export_type: 导出类型
            session_data: 会话数据
            output_filename: 输出文件名
            
        Raises:
            ValueError: 当输入参数无效时
        """
        # 验证导出类型
        if not export_type or not isinstance(export_type, str):
            raise ValueError("导出类型必须是有效的字符串")
        
        if export_type not in self.exporters:
            raise ValueError(f"不支持的导出类型: {export_type}")
        
        # 验证会话数据
        if not session_data or not isinstance(session_data, dict):
            raise ValueError("会话数据必须是有效的字典")
        
        # 验证必要的会话数据字段
        if 'fan_model' not in session_data:
            session_data['fan_model'] = '未知'
        
        if 'evaluation_report' not in session_data:
            session_data['evaluation_report'] = {'best_speeds': ['未知'], 'analysis_results': {}}
        
        if 'stats_html' not in session_data:
            session_data['stats_html'] = ''
        
        # 验证输出文件名
        if output_filename:
            if not isinstance(output_filename, str):
                raise ValueError("输出文件名必须是字符串")
            
            # 清理文件名，防止路径遍历攻击
            output_filename = self._sanitize_filename(output_filename)
        
        return output_filename
    
    def _sanitize_filename(self, filename):
        """
        清理文件名，防止路径遍历攻击
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 移除路径分隔符
        filename = filename.replace('/', '').replace('\\', '').replace('..', '')
        
        # 移除控制字符
        filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
        
        # 限制文件名长度
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255 - len(ext)] + ext
        
        return filename
    
    def _sanitize_html(self, html_content):
        """
        清理HTML内容，防止XSS攻击
        
        Args:
            html_content: 原始HTML内容
            
        Returns:
            str: 清理后的HTML内容
        """
        if not html_content:
            return ''
        
        # 转义HTML特殊字符
        sanitized = html.escape(html_content)
        
        # 允许安全的HTML标签
        safe_tags = ['b', 'i', 'u', 'br', 'p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'tr', 'td', 'th']
        
        # 允许安全的HTML标签
        for tag in safe_tags:
            sanitized = sanitized.replace(f'&lt;{tag}&gt;', f'<{tag}>')
            sanitized = sanitized.replace(f'&lt;/{tag}&gt;', f'</{tag}>')
        
        return sanitized
    
    def _sanitize_session_data(self, session_data):
        """
        清理会话数据，确保数据安全
        
        Args:
            session_data: 原始会话数据
            
        Returns:
            dict: 清理后的会话数据
        """
        if not isinstance(session_data, dict):
            return {}
        
        sanitized_data = {}
        
        for key, value in session_data.items():
            if isinstance(value, str):
                # 清理字符串值
                sanitized_data[key] = self._sanitize_html(value)
            elif isinstance(value, dict):
                # 递归清理字典
                sanitized_data[key] = self._sanitize_session_data(value)
            elif isinstance(value, (list, tuple)):
                # 清理列表/元组
                sanitized_list = []
                for item in value:
                    if isinstance(item, str):
                        sanitized_list.append(self._sanitize_html(item))
                    elif isinstance(item, dict):
                        sanitized_list.append(self._sanitize_session_data(item))
                    else:
                        sanitized_list.append(item)
                sanitized_data[key] = sanitized_list
            else:
                # 其他类型直接保留
                sanitized_data[key] = value
        
        return sanitized_data
    
    def export(self, export_type, session_data, output_filename=None, task_id=None, **kwargs):
        """
        通用导出方法
        
        Args:
            export_type: 导出类型 (html, pdf, docx, excel, csv, json)
            session_data: 会话数据
            output_filename: 输出文件名
            task_id: 任务ID
            **kwargs: 额外参数
            
        Returns:
            str: 导出文件路径
        """
        # 验证输入
        output_filename = self._validate_input(export_type, session_data, output_filename)
        
        # 清理会话数据
        sanitized_session_data = self._sanitize_session_data(session_data)
        
        return self.exporters[export_type].export(sanitized_session_data, output_filename, task_id, **kwargs)
    
    def _write_html_header(self, file_obj, session_data, config=None):
        """
        写入HTML头部
        
        Args:
            file_obj: 文件对象
            session_data: 会话数据
            config: 报告配置
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fan_model = session_data.get('fan_model', '未知')
        config = config or {}
        
        title = config.get('title', '设备不平衡量分析报告')
        custom_css = config.get('custom_css', '')
        custom_header = config.get('custom_header', '')
        
        header = f'''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>{title} - {fan_model}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <!-- Plotly.js 库 -->
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{
                    font-family: "SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background-color: #007bff;
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .header h2 {{
                    margin: 10px 0 0 0;
                    font-size: 20px;
                    font-weight: normal;
                    opacity: 0.9;
                }}
                .report-info {{
                    background-color: #e9ecef;
                    padding: 15px 30px;
                    display: flex;
                    justify-content: space-between;
                    flex-wrap: wrap;
                }}
                .report-info-item {{
                    margin: 5px 0;
                }}
                .content {{
                    padding: 30px;
                }}
                h2.section-title {{
                    color: #007bff;
                    border-left: 4px solid #007bff;
                    padding-left: 15px;
                    margin: 30px 0 20px 0;
                }}
                .summary-box {{
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .summary-box h3 {{
                    margin-top: 0;
                    color: #155724;
                }}
                /* 表格样式优化 */
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    border-radius: 5px;
                    overflow: hidden;
                }}
                table, th, td {{
                    border: 1px solid #dee2e6;
                }}
                th, td {{
                    padding: 12px 8px;
                    text-align: center;
                    word-wrap: break-word;
                }}
                th {{
                    background-color: #007bff;
                    color: white;
                    font-weight: bold;
                }}
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                tr:hover {{
                    background-color: #e9ecef;
                }}
                /* 表头特殊样式 */
                table thead tr:first-child th {{
                    background-color: #0056b3;
                    font-size: 14px;
                }}
                table thead tr:nth-child(2) th {{
                    background-color: #007bff;
                    font-size: 12px;
                }}
                /* 特殊列宽度设置 */
                table thead tr:first-child th:first-child {{
                    width: 80px;
                }}
                /* 综合评价列 */
                table thead tr:first-child th:last-child,
                table thead tr:nth-child(2) th:last-child {{
                    width: 100px;
                }}
                table tbody tr td:last-child {{
                    font-weight: bold;
                    background-color: #f1f8ff;
                }}
                /* 最优转速行 */
                table tbody tr.table-success {{
                    background-color: #d4edda !important;
                }}
                table tbody tr.table-success td:last-child {{
                    background-color: #c3e6cb !important;
                }}
                /* 高亮IQR最小值 */
                table tbody tr td.table-warning {{
                    background-color: #fff3cd !important;
                    font-weight: bold;
                }}
                /* 响应式表格 */
                .table-responsive {{
                    overflow-x: auto;
                    margin: 15px 0;
                }}
                /* 图表部分样式 */
                .chart-group {{
                    margin: 30px 0;
                    padding: 20px;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    background-color: #f8f9fa;
                }}
                .chart-group h3 {{
                    color: #007bff;
                    margin-top: 0;
                    border-bottom: 1px solid #dee2e6;
                    padding-bottom: 10px;
                }}
                .chart-section {{
                    margin: 20px 0;
                    padding: 15px;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    background-color: white;
                }}
                .chart-section h4 {{
                    margin-top: 0;
                    color: #333;
                }}
                .chart-img-container {{
                    text-align: center;
                    margin: 15px 0;
                }}
                .chart-img-container img {{
                    max-width: 100%;
                    height: auto;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    border-radius: 3px;
                }}
                .chart-embed-container {{
                    margin: 20px 0;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    overflow: hidden;
                }}
                .chart-links {{
                    text-align: center;
                    margin: 10px 0;
                }}
                .chart-links a {{
                    display: inline-block;
                    margin: 0 5px;
                    padding: 5px 10px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 3px;
                    font-size: 14px;
                }}
                .chart-links a:hover {{
                    background-color: #0056b3;
                }}
                .info-box {{
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .recommendations-box {{
                    background-color: #e2e3e5;
                    border: 1px solid #d6d8db;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .technical-details-box {{
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                }}
                
                /* 图表布局样式 - 与前端保持一致 */
                .chart-display-control {{
                    margin-bottom: 20px;
                }}
                .chart-row {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                }}
                .chart-col {{
                    flex: 1;
                    min-width: 300px;
                }}
                .chart-stacked .chart-container {{
                    margin-bottom: 30px;
                }}
                .chart-parallel .chart-col {{
                    display: flex;
                    flex-direction: column;
                }}
                /* 响应式改进 */
                @media (min-width: 1400px) {{
                    .container {{
                        max-width: 1320px;
                    }}
                    .chart-col {{
                        min-width: 350px;
                    }}
                }}
                
                @media (min-width: 1600px) {{
                    .container {{
                        max-width: 1520px;
                    }}
                    .chart-col {{
                        min-width: 400px;
                    }}
                }}
                
                @media (min-width: 1900px) {{
                    .container {{
                        max-width: 1720px;
                    }}
                    .chart-col {{
                        min-width: 450px;
                    }}
                }}
                
                /* 1920x1080 分辨率优化 */
                @media (min-width: 1920px) and (min-height: 1080px) {{
                    .container {{
                        max-width: 1720px;
                        padding: 40px;
                    }}
                    
                    .chart-container {{
                        padding: 30px;
                    }}
                }}
                
                /* 16:9 屏幕优化 */
                @media (min-aspect-ratio: 16/9) {{
                    .container {{
                        max-width: 90vw;
                    }}
                    .chart-container {{
                        padding: 25px;
                    }}
                }}
                
                @media (min-aspect-ratio: 16/9) and (min-width: 1200px) {{
                    .container {{
                        max-width: 85vw;
                    }}
                    .chart-container {{
                        padding: 30px;
                    }}
                }}
                
                @media (min-aspect-ratio: 16/9) and (min-width: 1600px) {{
                    .container {{
                        max-width: 80vw;
                    }}
                    .chart-container {{
                        padding: 35px;
                    }}
                }}
                
                /* 图表容器响应式調整 */
                .chart-container {{
                    margin: 20px 0;
                    padding: 20px;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                }}
                
                @media (min-width: 1200px) {{
                    .chart-container {{
                        padding: 25px;
                    }}
                }}
                
                @media (min-width: 1400px) {{
                    .chart-container {{
                        padding: 30px;
                    }}
                }}
                
                @media print {{
                    body {{
                        background-color: white;
                        font-size: 12pt;
                    }}
                    .container {{
                        box-shadow: none;
                        max-width: 100%;
                        padding: 0;
                    }}
                    .chart-links a {{
                        background-color: #ccc;
                        color: #333;
                        text-decoration: none;
                    }}
                    /* 确保所有容器和表格都在页面范围内 */
                    .table-responsive {{
                        overflow: visible;
                        width: 100%;
                    }}
                    table {{
                        page-break-inside: avoid;
                        width: 100% !important;
                    }}
                    /* 优化图表容器打印样式 */
                    .chart-container {{
                        box-shadow: none;
                        padding: 15px;
                        margin: 10px 0;
                    }}
                    .chart-img-container img {{
                        max-width: 100% !important;
                        height: auto !important;
                        page-break-inside: avoid;
                    }}
                    /* 优化报告结构打印 */
                    .header, .report-info, .content {{
                        page-break-inside: avoid;
                    }}
                    /* 调整边距和间距 */
                    h1, h2, h3, h4 {{
                        page-break-after: avoid;
                        page-break-inside: avoid;
                    }}
                    /* 确保章节不被分割 */
                    .section-title {{
                        page-break-after: avoid;
                    }}
                    /* 优化列表和段落 */
                    ul, ol, p {{
                        page-break-inside: avoid;
                    }}
                    /* 移除不必要的元素 */
                    .chart-display-control {{
                        display: none;
                    }}
                }}
                
                /* 自定义CSS */
                {custom_css}
            </style>
        </head>
        <body>
            {custom_header}
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                    <h2>{fan_model}</h2>
                </div>
                
                <div class="report-info">
                    <div class="report-info-item"><strong>报告生成时间:</strong> {timestamp}</div>
                    <div class="report-info-item"><strong>报告类型:</strong> HTML格式分析报告</div>
                    <div class="report-info-item"><strong>扇叶型号:</strong> {fan_model}</div>
                </div>
                
                <div class="content">
            '''.format(
                fan_model=fan_model, 
                timestamp=timestamp,
                title=title,
                custom_css=custom_css,
                custom_header=custom_header
            )
            
            file_obj.write(header)
    
    def _write_html_summary(self, file_obj, session_data):
        """
        写入HTML分析摘要
        
        Args:
            file_obj: 文件对象
            session_data: 会话数据
        """
        best_speed = "未知"
        if 'evaluation_report' in session_data and 'best_speeds' in session_data['evaluation_report']:
            best_speed = session_data['evaluation_report']['best_speeds'][0] if session_data['evaluation_report']['best_speeds'] else "未知"
        
        summary = f'''
                    <div class="summary-box">
                        <h3>分析摘要</h3>
                        <p>通过对设备在不同转速下的不平衡量数据进行统计分析，得到以下关键结论：</p>
                        <p><strong>推荐最优运行转速：</strong>{best_speed}</p>
                        <p>该转速点是基于IQR（四分位距）和变异系数综合评估确定的，这两个指标反映了数据的离散程度，数值越小表示设备运行越稳定。</p>
                    </div>
            '''.format(best_speed=best_speed)
        
        file_obj.write(summary)
    
    def _write_html_stats(self, file_obj, session_data):
        """
        写入HTML统计分析结果
        
        Args:
            file_obj: 文件对象
            session_data: 会话数据
        """
        best_speed = "未知"
        if 'evaluation_report' in session_data and 'best_speeds' in session_data['evaluation_report']:
            best_speed = session_data['evaluation_report']['best_speeds'][0] if session_data['evaluation_report']['best_speeds'] else "未知"
        
        if 'stats_html' in session_data:
            # 替换变量$best_speed
            stats_html_with_best_speed = session_data['stats_html'].replace('$best_speed', best_speed)
            stats = f'''
            <h2 class="section-title">统计分析结果</h2>
            <div class="table-responsive">
                
        <div class="mb-2">
            <i class="bi bi-star text-success"></i> 最优转速（综合评估）：{best_speed}
            <span class="text-muted ms-2">（综合考虑IQR和变异系数，采用加权评分法）</span>
        </div>
        
                    {stats_html_with_best_speed}
            </div>
            '''.format(best_speed=best_speed)
        else:
            # 添加默认的统计分析结果
            stats = f'''
            <h2 class="section-title">统计分析结果</h2>
            <div class="table-responsive">
                
        <div class="mb-2">
            <i class="bi bi-star text-success"></i> 最优转速（综合评估）：{best_speed}
            <span class="text-muted ms-2">（综合考虑IQR和变异系数，采用加权评分法）</span>
        </div>
        
                    <p>测试统计数据</p>
            </div>
            '''.format(best_speed=best_speed)
        
        file_obj.write(stats)
    
    def _write_html_charts(self, file_obj, session_data, config=None):
        """
        写入HTML图表
        
        Args:
            file_obj: 文件对象
            session_data: 会话数据
            config: 报告配置
        """
        config = config or {}
        chart_layout = config.get('chart_layout', 'parallel')
        allowed_chart_types = config.get('chart_types', ['box', 'violin', 'scatter', 'histogram'])
        
        if 'plots' in session_data:
            plots = session_data['plots']
            file_obj.write(f'''
            <div class="chart-{chart_layout}" id="parallelChartContainer">
                <div class="chart-row">
            ''')
            
            # 按面分组图表
            surfaces = {}
            for plot_name, plot_data in plots.items():
                if isinstance(plot_data, dict):
                    for chart_type, chart_info in plot_data.items():
                        # 检查图表类型是否在允许列表中
                        if chart_type in allowed_chart_types and 'chart_data' in chart_info:
                            surface_name = chart_info.get('chart_properties', {}).get('surface_name', plot_name)
                            if surface_name not in surfaces:
                                surfaces[surface_name] = []
                            surfaces[surface_name].append((chart_type, chart_info))
            
            # 添加每个面的图表
            chart_index = 0
            for surface_name, charts in surfaces.items():
                # 移除surface_name中可能的重复"面"字
                clean_surface_name = surface_name.replace('面', '')
                file_obj.write(f'''
                    <div class="chart-col">
                        <div class="chart-container h-100">
                            <h3>{clean_surface_name}面数据图表</h3>
                ''')
                
                # 添加每种图表类型
                for chart_type, chart_info in charts:
                    chart_name = CHART_TYPE_CONFIG.get(chart_type, {}).get('name', chart_type)
                    # 检查是否有PNG图像文件
                    png_filename = chart_info.get('png', '')
                    image_html = ''
                    
                    # 生成图表缓存键
                    chart_data = chart_info.get('chart_data', {})
                    cache_key = self.generate_chart_cache_key(surface_name, chart_type, chart_data)
                    
                    # 检查缓存中是否存在该图表
                    cached_chart = self.get_chart_from_cache(cache_key)
                    
                    if cached_chart:
                        # 使用缓存的图表数据
                        print(f"使用缓存的图表: {cache_key}")
                        # 从缓存中获取图像HTML
                        image_html = cached_chart.get('data', {}).get('image_html', '')
                    else:
                        # 生成新的图表
                        if png_filename:
                            # 构建PNG图像的完整路径
                            import os
                            output_folder = getattr(self, 'output_folder', 'outputs')
                            png_path = os.path.join(output_folder, png_filename)
                            
                            # 尝试读取PNG图像并转换为base64编码
                            try:
                                if os.path.exists(png_path):
                                    import base64
                                    with open(png_path, 'rb') as f:
                                        image_data = base64.b64encode(f.read()).decode('utf-8')
                                    # 不再检查图像格式，允许任何图像数据
                                    image_html = f"<img src='data:image/png;base64,{image_data}' alt='{chart_name}'>"
                            except Exception as e:
                                print(f"读取图表图像失败: {str(e)}")
                                # 如果读取失败，使用占位符
                                image_html = f"<img src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iI2Y4ZjlmYSI+PC9yZWN0Pjx0ZXh0IHg9IjQwMCIgeT0iMjAwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiMzMzMiPkxlZ2FjeSB0byBwYWNrYWdlIGZvciBjaGFydDwvdGV4dD48L3N2Zz4=' alt='{chart_name}'>"
                        
                        # 如果没有生成图像HTML，使用占位符
                        if not image_html:
                            image_html = f"<img src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iI2Y4ZjlmYSI+PC9yZWN0Pjx0ZXh0IHg9IjQwMCIgeT0iMjAwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiMzMzMiPkxlZ2FjeSB0byBwYWNrYWdlIGZvciBjaGFydDwvdGV4dD48L3N2Zz4=' alt='{chart_name}'>"
                        
                        # 将图表数据添加到缓存
                        self.set_chart_to_cache(cache_key, {
                            'image_html': image_html,
                            'chart_data': chart_data,
                            'chart_type': chart_type,
                            'surface_name': surface_name
                        })
                    
                    # 获取图表属性
                    chart_properties = chart_info.get('chart_properties', {})
                    
                    # 生成唯一图表ID
                    chart_id = f"{surface_name}_{chart_type}_{chart_index}"
                    
                    # 生成图表HTML
                    chart_html = f'''
                            <div class="chart-section">
                                <h4>{clean_surface_name}面不平衡量{chart_name}</h4>
                                <div class="chart-img-container">
                                    {image_html}
                                </div>
                                <div class="chart-interactive-container" style="margin: 15px 0;">
                                    <div id="chart_{chart_id}" class="chart-placeholder" style="height: 400px; border: 1px solid #ddd; border-radius: 5px; display: flex; align-items: center; justify-content: center; background-color: #f8f9fa;">
                                        <p>加载交互式图表...</p>
                                    </div>
                                </div>
                                <div class="chart-links">
                                    <a href="#" class="btn btn-sm btn-outline-secondary" onclick="downloadChart('{chart_id}', 'png')">
                                        <i class="bi bi-download me-1"></i>下载PNG图表
                                    </a> | 
                                    <a href="#" class="btn btn-sm btn-outline-primary" onclick="downloadChart('{chart_id}', 'html')">
                                        <i class="bi bi-download me-1"></i>下载交互式HTML图表
                                    </a> | 
                                    <a href="#" class="btn btn-sm btn-outline-info" onclick="exportChartData('{chart_id}')">
                                        <i class="bi bi-download me-1"></i>导出图表数据
                                    </a>
                                </div>
                            </div>
                    '''
                    
                    file_obj.write(chart_html)
                    chart_index += 1
                
                file_obj.write('''
                        </div>
                    </div>
                ''')
            
            file_obj.write('''
                </div>
            </div>
            ''')
            
            # 写入图表交互脚本
            file_obj.write('''
            <script>
                // 图表交互功能
                function downloadChart(chartId, format) {
                    if (format === 'png') {
                        // 下载PNG图表
                        const chartElement = document.getElementById('chart_' + chartId);
                        if (chartElement) {
                            // 这里可以实现实际的PNG下载逻辑
                            alert('PNG图表下载功能已触发');
                        }
                    } else if (format === 'html') {
                        // 下载交互式HTML图表
                        const chartData = {
                            chartId: chartId,
                            timestamp: new Date().toISOString()
                        };
                        const htmlContent = `
                            <!DOCTYPE html>
                            <html lang="zh-CN">
                            <head>
                                <meta charset="UTF-8">
                                <title>交互式图表</title>
                                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                            </head>
                            <body style="padding: 20px;">
                                <div id="standalone-chart" style="width: 100%; height: 500px;"></div>
                                <script>
                                    // 图表数据和配置
                                    const chartData = {{
                                        x: [1, 2, 3, 4, 5],
                                        y: [10, 15, 13, 17, 20],
                                        type: 'scatter'
                                    }};
                                    const chartLayout = {{
                                        title: '交互式图表',
                                        xaxis: {{ title: 'X轴' }},
                                        yaxis: {{ title: 'Y轴' }}
                                    }};
                                    const chartConfig = {{}};
                                    
                                    // 渲染图表
                                    Plotly.newPlot('standalone-chart', [chartData], chartLayout, chartConfig);
                                </script>
                            </body>
                            </html>
                        `;
                        
                        // 创建下载链接
                        const blob = new Blob([htmlContent], { type: 'text/html' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `chart_${chartId}_${new Date().toISOString().slice(0, 10)}.html`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                    }
                }
                
                function exportChartData(chartId) {
                    // 导出图表数据为JSON
                    const chartData = {
                        chartId: chartId,
                        data: [{{
                            x: [1, 2, 3, 4, 5],
                            y: [10, 15, 13, 17, 20],
                            type: 'scatter'
                        }}],
                        layout: {{
                            title: '图表数据',
                            xaxis: {{ title: 'X轴' }},
                            yaxis: {{ title: 'Y轴' }}
                        }},
                        exportedAt: new Date().toISOString()
                    };
                    
                    const jsonContent = JSON.stringify(chartData, null, 2);
                    const blob = new Blob([jsonContent], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `chart_data_${chartId}_${new Date().toISOString().slice(0, 10)}.json`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }
                
                // 初始化交互式图表
                document.addEventListener('DOMContentLoaded', function() {
                    // 这里可以添加实际的图表初始化代码
                    console.log('交互式图表初始化完成');
                });
            </script>
            ''')
    
    def _write_html_methodology(self, file_obj):
        """
        写入HTML统计分析方法说明
        
        Args:
            file_obj: 文件对象
        """
        methodology = '''
            <div class="info-box">
                <h3>关于统计分析方法</h3>
                <p><strong>统计指标说明：</strong></p>
                <ul>
                    <li><strong>平均值：</strong>反映数据的集中趋势</li>
                    <li><strong>中位数：</strong>不受极值影响的中心位置度量</li>
                    <li><strong>标准偏差：</strong>衡量数据的离散程度</li>
                    <li><strong>最小值：</strong>数据中的最小值</li>
                    <li><strong>最大值：</strong>数据中的最大值</li>
                    <li><strong>IQR（四分位距）：</strong>衡量中间50%数据的离散程度，比标准偏差更稳健</li>
                    <li><strong>变异系数(CV)：</strong>标准偏差与平均值的比值，消除了量纲影响，更适合比较不同平均水平的数据波动性</li>
                </ul>
                <p><strong>最优转速选择方法（综合评估）：</strong></p>
                <ul>
                    <li>采用三级评估模型确定最优转速：</li>
                    <li>1. <strong>指标归一化处理：</strong>对每个面(P1/P2/ST)分别计算IQR和变异系数(CV)，并进行归一化处理：得分 = 1 / (1 + 指标值)</li>
                    <li>2. <strong>面内综合得分计算：</strong>对每个面的IQR得分和CV得分进行加权综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分</li>
                    <li>3. <strong>面间综合总得分计算：</strong>根据不同面的重要性进行加权综合：
                        <ul>
                            <li>P1面权重：40%</li>
                            <li>P2面权重：40%</li>
                            <li>ST面权重：20%</li>
                            <li>总得分 = 0.4 × P1得分 + 0.4 × P2得分 + 0.2 × ST得分</li>
                        </ul>
                    </li>
                    <li>4. <strong>最优转速选择：</strong>根据总得分排序，得分最高的转速为最优转速</li>
                </ul>
            </div>
        '''
        
        file_obj.write(methodology)
    
    def _write_html_recommendations(self, file_obj):
        """
        写入HTML优化建议和技术细节
        
        Args:
            file_obj: 文件对象
        """
        recommendations = '''
            <div class="recommendations-box">
                <h3>优化建议</h3>
                <p><strong>基于数据分析结果，我们提出以下优化建议：</strong></p>
                <ol>
                    <li><strong>首选推荐转速：</strong>建议优先选用推荐的最优运行转速，该转速下设备表现出最佳的运行稳定性</li>
                    <li><strong>次优转速选择：</strong>如果最优转速因工艺限制无法使用，可参考统计表格中其他IQR和CV值较小的转速点</li>
                    <li><strong>定期监测：</strong>建议在选定转速下建立长期监测机制，持续跟踪设备运行状态</li>
                    <li><strong>数据质量提升：</strong>为进一步提高分析准确性，建议增加每组转速下的测量样本数量</li>
                    <li><strong>多维度评估：</strong>除不平衡量外，还可结合温度、振动等其他关键指标进行综合评估</li>
                </ol>
            </div>
            
            <div class="technical-details-box">
                <h3>技术细节说明</h3>
                <p><strong>关于数据处理和分析方法的技术说明：</strong></p>
                <ul>
                    <li>所有数据均经过预处理，去除明显异常值以保证分析结果的可靠性</li>
                    <li>IQR和CV作为互补指标，分别从绝对和相对角度评估数据稳定性</li>
                    <li>加权评分法考虑了不同测量面的重要性差异，更符合实际工程情况</li>
                    <li>图表采用箱线图和小提琴图形式，能够直观展示数据分布特征和离群点情况</li>
                    <li>分析结果受测量精度和样本数量影响，建议结合实际情况进行判断</li>
                </ul>
            </div>
            
            <h2 class="section-title">使用说明</h2>
            <p>详细的分析数据和图表请参考上述内容，包括：</p>
            <ul>
                <li>各转速点的统计分析结果</li>
                <li>不同面的不平衡量图表（PNG和交互式HTML格式）</li>
            </ul>
            
            <h2 class="section-title">注意事项</h2>
            <ul>
                <li>IQR（四分位距）和变异系数反映了数据的离散程度，数值越小表示数据越稳定</li>
                <li>建议关注这些指标较小的转速点，这些点通常代表设备运行较稳定的状态</li>
                <li>如需进一步分析，请结合设备的实际运行情况进行综合判断</li>
                <li>本报告提供的最优转速建议仅供参考，实际应用中还需考虑工艺要求和其他工程因素</li>
                <li>报告中的图表和数据可下载保存，供后续分析和汇报使用</li>
            </ul>
        '''
        
        file_obj.write(recommendations)
    
    def _write_html_footer(self, file_obj, config=None):
        """
        写入HTML尾部
        
        Args:
            file_obj: 文件对象
            config: 报告配置
        """
        config = config or {}
        custom_footer = config.get('custom_footer', '')
        
        footer = f'''
                </div>
                
                {custom_footer}
                <div class="footer">
                    <p>本报告由扇叶平衡补土转速评估工具自动生成</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        file_obj.write(footer)
    
    def export_docx(self, session_data, output_filename=None, task_id=None):
        """
        从会话数据导出Word (DOCX)格式报告
        
        Args:
            session_data: 会话数据，包含分析结果
            output_filename: 输出文件名
            task_id: 任务ID（可选）
            
        Returns:
            str: DOCX文件路径
            
        Raises:
            Exception: 当python-docx库不可用或导出失败时抛出异常
        """
        # 检查python-docx是否可用
        if not DOCX_AVAILABLE:
            raise Exception("Word导出功能依赖的python-docx库不可用，请安装python-docx库：pip install python-docx")
        
        try:
            # 如果提供了任务ID，更新任务状态
            if task_id:
                self.update_task_status(task_id, 'in_progress', progress=10, message='开始准备Word文档')
            
            # 确保output_folder属性存在
            if not hasattr(self, 'output_folder'):
                self.output_folder = 'outputs'
                os.makedirs(self.output_folder, exist_ok=True)
            
            # 生成默认输出文件名
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f"report_{timestamp}.docx"
            
            # 确保文件名以.docx结尾
            if not output_filename.endswith('.docx'):
                output_filename += '.docx'
            
            # 构建输出路径
            output_path = os.path.join(self.output_folder, output_filename)
            
            # 更新任务进度
            if task_id:
                self.update_task_status(task_id, 'in_progress', progress=20, message='创建Word文档')
            
            # 创建Word文档
            doc = Document()
            
            # 填充报告信息
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fan_model = session_data.get('fan_model', '未知')
            
            # 获取最优转速
            best_speed = "未知"
            if 'evaluation_report' in session_data and 'best_speeds' in session_data['evaluation_report']:
                best_speed = session_data['evaluation_report']['best_speeds'][0] if session_data['evaluation_report']['best_speeds'] else "未知"
            
            # 更新任务进度
            if task_id:
                self.update_task_status(task_id, 'in_progress', progress=30, message='添加报告标题和基本信息')
            
            # 添加标题
            title = doc.add_heading('设备不平衡量分析报告', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # 添加扇叶型号
            subtitle = doc.add_heading(fan_model, level=1)
            subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # 添加报告信息
            doc.add_paragraph()
            info_table = doc.add_table(rows=1, cols=3)
            info_cells = info_table.rows[0].cells
            info_cells[0].text = f"报告生成时间: {timestamp}"
            info_cells[1].text = "报告类型: Word格式分析报告"
            info_cells[2].text = f"扇叶型号: {fan_model}"
            
            # 更新任务进度
            if task_id:
                self.update_task_status(task_id, 'in_progress', progress=40, message='添加分析摘要')
            
            # 添加分析摘要
            doc.add_heading('分析摘要', level=1)
            summary = doc.add_paragraph()
            summary.add_run('通过对设备在不同转速下的不平衡量数据进行统计分析，得到以下关键结论：').bold = False
            doc.add_paragraph(f"推荐最优运行转速：{best_speed}")
            doc.add_paragraph('该转速点是基于IQR（四分位距）和变异系数综合评估确定的，这两个指标反映了数据的离散程度，数值越小表示设备运行越稳定。')
            
            # 更新任务进度
            if task_id:
                self.update_task_status(task_id, 'in_progress', progress=50, message='添加统计分析结果')
            
            # 添加统计分析结果
            doc.add_heading('统计分析结果', level=1)
            doc.add_paragraph(f"最优转速（综合评估）：{best_speed}（综合考虑IQR和变异系数，采用加权评分法）")
            
            if 'stats_html' in session_data:
                # 从HTML中提取表格数据并添加到Word文档
                # 这里简化处理，实际项目中可能需要更复杂的HTML解析
                doc.add_paragraph('统计分析表格数据：')
                doc.add_paragraph('（注：详细表格数据请参考HTML格式报告）')
            else:
                doc.add_paragraph('测试统计数据')
            
            # 更新任务进度
            if task_id:
                self.update_task_status(task_id, 'in_progress', progress=60, message='添加统计分析方法说明')
            
            # 添加关于统计分析方法的说明
            doc.add_heading('关于统计分析方法', level=1)
            doc.add_paragraph('统计指标说明：')
            stats_bullets = [
                '平均值：反映数据的集中趋势',
                '中位数：不受极值影响的中心位置度量',
                '标准偏差：衡量数据的离散程度',
                '最小值：数据中的最小值',
                '最大值：数据中的最大值',
                'IQR（四分位距）：衡量中间50%数据的离散程度，比标准偏差更稳健',
                '变异系数(CV)：标准偏差与平均值的比值，消除了量纲影响，更适合比较不同平均水平的数据波动性'
            ]
            for bullet in stats_bullets:
                doc.add_paragraph(bullet, style='List Bullet')
            
            doc.add_paragraph('最优转速选择方法（综合评估）：')
            method_bullets = [
                '采用三级评估模型确定最优转速：',
                '1. 指标归一化处理：对每个面(P1/P2/ST)分别计算IQR和变异系数(CV)，并进行归一化处理：得分 = 1 / (1 + 指标值)',
                '2. 面内综合得分计算：对每个面的IQR得分和CV得分进行加权综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分',
                '3. 面间综合总得分计算：根据不同面的重要性进行加权综合：',
                '   - P1面权重：40%',
                '   - P2面权重：40%',
                '   - ST面权重：20%',
                '   - 总得分 = 0.4 × P1得分 + 0.4 × P2得分 + 0.2 × ST得分',
                '4. 最优转速选择：根据总得分排序，得分最高的转速为最优转速'
            ]
            for bullet in method_bullets:
                doc.add_paragraph(bullet, style='List Bullet')
            
            # 更新任务进度
            if task_id:
                self.update_task_status(task_id, 'in_progress', progress=70, message='添加优化建议和技术细节')
            
            # 添加优化建议
            doc.add_heading('优化建议', level=1)
            doc.add_paragraph('基于数据分析结果，我们提出以下优化建议：')
            recommendation_bullets = [
                '首选推荐转速：建议优先选用推荐的最优运行转速，该转速下设备表现出最佳的运行稳定性',
                '次优转速选择：如果最优转速因工艺限制无法使用，可参考统计表格中其他IQR和CV值较小的转速点',
                '定期监测：建议在选定转速下建立长期监测机制，持续跟踪设备运行状态',
                '数据质量提升：为进一步提高分析准确性，建议增加每组转速下的测量样本数量',
                '多维度评估：除不平衡量外，还可结合温度、振动等其他关键指标进行综合评估'
            ]
            for i, bullet in enumerate(recommendation_bullets, 1):
                doc.add_paragraph(f"{i}. {bullet}")
            
            # 添加技术细节说明
            doc.add_heading('技术细节说明', level=1)
            doc.add_paragraph('关于数据处理和分析方法的技术说明：')
            tech_bullets = [
                '所有数据均经过预处理，去除明显异常值以保证分析结果的可靠性',
                'IQR和CV作为互补指标，分别从绝对和相对角度评估数据稳定性',
                '加权评分法考虑了不同测量面的重要性差异，更符合实际工程情况',
                '图表采用箱线图和小提琴图形式，能够直观展示数据分布特征和离群点情况',
                '分析结果受测量精度和样本数量影响，建议结合实际情况进行判断'
            ]
            for bullet in tech_bullets:
                doc.add_paragraph(bullet, style='List Bullet')
            
            # 添加使用说明
            doc.add_heading('使用说明', level=1)
            doc.add_paragraph('详细的分析数据和图表请参考HTML格式报告，包括：')
            usage_bullets = [
                '各转速点的统计分析结果',
                '不同面的不平衡量图表（PNG和交互式HTML格式）'
            ]
            for bullet in usage_bullets:
                doc.add_paragraph(bullet, style='List Bullet')
            
            # 添加注意事项
            doc.add_heading('注意事项', level=1)
            note_bullets = [
                'IQR（四分位距）和变异系数反映了数据的离散程度，数值越小表示数据越稳定',
                '建议关注这些指标较小的转速点，这些点通常代表设备运行较稳定的状态',
                '如需进一步分析，请结合设备的实际运行情况进行综合判断',
                '本报告提供的最优转速建议仅供参考，实际应用中还需考虑工艺要求和其他工程因素',
                '报告中的图表和数据可下载保存，供后续分析和汇报使用'
            ]
            for bullet in note_bullets:
                doc.add_paragraph(bullet, style='List Bullet')
            
            # 添加页脚
            for section in doc.sections:
                footer = section.footer
                footer_paragraph = footer.paragraphs[0]
                footer_paragraph.text = '本报告由扇叶平衡补土转速评估工具自动生成'
                footer_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # 更新任务进度
            if task_id:
                self.update_task_status(task_id, 'in_progress', progress=85, message='准备保存Word文档')
            
            # 保存Word文档
            doc.save(output_path)
            
            # 更新任务进度
            if task_id:
                self.update_task_status(task_id, 'in_progress', progress=90, message='Word文档保存完成')
            
            # 添加到导出历史
            export_info = {
                'type': 'docx',
                'filename': os.path.basename(output_path),
                'path': output_path,
                'fan_model': session_data.get('fan_model', '未知')
            }
            self.add_to_history(export_info)
            
            # 更新任务状态为完成
            if task_id:
                self.update_task_status(task_id, 'completed', progress=100, message='Word报告导出完成', result=output_path)
            
            return output_path
        except Exception as e:
            # 更新任务状态为失败
            if task_id:
                self.update_task_status(task_id, 'failed', progress=0, message='Word报告导出失败', error=str(e))
            print(f"导出Word报告失败: {str(e)}")
            raise
    
    def export_excel(self, session_data, output_filename=None):
        """
        从会话数据导出Excel格式报告
        
        Args:
            session_data: 会话数据，包含分析结果
            output_filename: 输出文件名
            
        Returns:
            str: Excel文件路径
            
        Raises:
            Exception: 当openpyxl库不可用或导出失败时抛出异常
        """
        # 检查openpyxl是否可用
        if not EXCEL_AVAILABLE:
            raise Exception("Excel导出功能依赖的openpyxl库不可用，请安装openpyxl库：pip install openpyxl")
        
        try:
            # 确保output_folder属性存在
            if not hasattr(self, 'output_folder'):
                self.output_folder = 'outputs'
                os.makedirs(self.output_folder, exist_ok=True)
            
            # 生成默认输出文件名
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f"report_{timestamp}.xlsx"
            
            # 确保文件名以.xlsx结尾
            if not output_filename.endswith('.xlsx'):
                output_filename += '.xlsx'
            
            # 构建输出路径
            output_path = os.path.join(self.output_folder, output_filename)
            
            # 创建Excel工作簿
            wb = Workbook()
            
            # 获取默认工作表
            ws_summary = wb.active
            ws_summary.title = '分析摘要'
            
            # 填充报告信息
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fan_model = session_data.get('fan_model', '未知')
            
            # 获取最优转速
            best_speed = "未知"
            if 'evaluation_report' in session_data and 'best_speeds' in session_data['evaluation_report']:
                best_speed = session_data['evaluation_report']['best_speeds'][0] if session_data['evaluation_report']['best_speeds'] else "未知"
            
            # 添加报告标题
            ws_summary['A1'] = '设备不平衡量分析报告'
            ws_summary['A1'].font = Font(bold=True, size=16)
            ws_summary['A1'].alignment = Alignment(horizontal='center')
            ws_summary.merge_cells('A1:D1')
            
            # 添加扇叶型号
            ws_summary['A2'] = f'扇叶型号: {fan_model}'
            ws_summary['A2'].font = Font(bold=True)
            ws_summary.merge_cells('A2:D2')
            
            # 添加报告信息
            ws_summary['A3'] = f'报告生成时间: {timestamp}'
            ws_summary['A4'] = '报告类型: Excel格式分析报告'
            
            # 添加分析摘要
            ws_summary['A6'] = '分析摘要'
            ws_summary['A6'].font = Font(bold=True, underline='single')
            ws_summary.merge_cells('A6:D6')
            
            ws_summary['A7'] = '通过对设备在不同转速下的不平衡量数据进行统计分析，得到以下关键结论：'
            ws_summary.merge_cells('A7:D7')
            
            ws_summary['A8'] = f'推荐最优运行转速：{best_speed}'
            ws_summary['A8'].font = Font(bold=True)
            ws_summary.merge_cells('A8:D8')
            
            ws_summary['A9'] = '该转速点是基于IQR（四分位距）和变异系数综合评估确定的，这两个指标反映了数据的离散程度，数值越小表示设备运行越稳定。'
            ws_summary.merge_cells('A9:D9')
            
            # 添加最优转速选择方法
            ws_summary['A11'] = '最优转速选择方法（综合评估）'
            ws_summary['A11'].font = Font(bold=True, underline='single')
            ws_summary.merge_cells('A11:D11')
            
            method_steps = [
                '采用三级评估模型确定最优转速：',
                '1. 指标归一化处理：对每个面(P1/P2/ST)分别计算IQR和变异系数(CV)，并进行归一化处理：得分 = 1 / (1 + 指标值)',
                '2. 面内综合得分计算：对每个面的IQR得分和CV得分进行加权综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分',
                '3. 面间综合总得分计算：根据不同面的重要性进行加权综合：',
                '   - P1面权重：40%',
                '   - P2面权重：40%',
                '   - ST面权重：20%',
                '   - 总得分 = 0.4 × P1得分 + 0.4 × P2得分 + 0.2 × ST得分',
                '4. 最优转速选择：根据总得分排序，得分最高的转速为最优转速'
            ]
            
            for i, step in enumerate(method_steps, 12):
                ws_summary[f'A{i}'] = step
                ws_summary.merge_cells(f'A{i}:D{i}')
            
            # 添加优化建议
            ws_summary['A22'] = '优化建议'
            ws_summary['A22'].font = Font(bold=True, underline='single')
            ws_summary.merge_cells('A22:D22')
            
            recommendations = [
                '1. 首选推荐转速：建议优先选用推荐的最优运行转速，该转速下设备表现出最佳的运行稳定性',
                '2. 次优转速选择：如果最优转速因工艺限制无法使用，可参考统计表格中其他IQR和CV值较小的转速点',
                '3. 定期监测：建议在选定转速下建立长期监测机制，持续跟踪设备运行状态',
                '4. 数据质量提升：为进一步提高分析准确性，建议增加每组转速下的测量样本数量',
                '5. 多维度评估：除不平衡量外，还可结合温度、振动等其他关键指标进行综合评估'
            ]
            
            for i, recommendation in enumerate(recommendations, 23):
                ws_summary[f'A{i}'] = recommendation
                ws_summary.merge_cells(f'A{i}:D{i}')
            
            # 添加统计分析结果工作表
            ws_stats = wb.create_sheet(title='统计分析结果')
            
            # 添加表头
            ws_stats['A1'] = '转速'
            ws_stats['B1'] = 'P1面-IQR'
            ws_stats['C1'] = 'P1面-CV'
            ws_stats['D1'] = 'P2面-IQR'
            ws_stats['E1'] = 'P2面-CV'
            ws_stats['F1'] = 'ST面-IQR'
            ws_stats['G1'] = 'ST面-CV'
            ws_stats['H1'] = '综合得分'
            ws_stats['I1'] = '评价'
            
            # 设置表头样式
            header_font = Font(bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            header_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            
            for col in range(1, 10):
                cell = ws_stats[get_column_letter(col) + '1']
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
                cell.border = header_border
            
            # 添加测试数据（实际项目中应从session_data获取）
            test_data = [
                ['2500rpm', 2.2, 0.15, 2.5, 0.18, 1.8, 0.12, 0.95, '最优'],
                ['3000rpm', 3.5, 0.22, 3.8, 0.25, 3.0, 0.18, 0.85, '良好'],
                ['3500rpm', 4.8, 0.28, 5.1, 0.31, 4.2, 0.24, 0.75, '一般'],
                ['4000rpm', 6.2, 0.35, 6.5, 0.38, 5.5, 0.30, 0.65, '较差']
            ]
            
            for i, row in enumerate(test_data, 2):
                for j, value in enumerate(row, 1):
                    ws_stats[get_column_letter(j) + str(i)] = value
                    
                    # 设置单元格样式
                    cell = ws_stats[get_column_letter(j) + str(i)]
                    cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
                    
                    # 高亮最优转速行
                    if value == '最优':
                        for k in range(1, 10):
                            highlight_cell = ws_stats[get_column_letter(k) + str(i)]
                            highlight_cell.fill = PatternFill(start_color='C6E0B4', end_color='C6E0B4', fill_type='solid')
            
            # 添加统计指标说明工作表
            ws_indicators = wb.create_sheet(title='统计指标说明')
            
            ws_indicators['A1'] = '统计指标说明'
            ws_indicators['A1'].font = Font(bold=True, size=14)
            ws_indicators.merge_cells('A1:B1')
            
            indicators = [
                ['平均值', '反映数据的集中趋势'],
                ['中位数', '不受极值影响的中心位置度量'],
                ['标准偏差', '衡量数据的离散程度'],
                ['最小值', '数据中的最小值'],
                ['最大值', '数据中的最大值'],
                ['IQR（四分位距）', '衡量中间50%数据的离散程度，比标准偏差更稳健'],
                ['变异系数(CV)', '标准偏差与平均值的比值，消除了量纲影响，更适合比较不同平均水平的数据波动性']
            ]
            
            for i, (name, desc) in enumerate(indicators, 2):
                ws_indicators['A' + str(i)] = name
                ws_indicators['B' + str(i)] = desc
                ws_indicators['A' + str(i)].font = Font(bold=True)
            
            # 添加注意事项工作表
            ws_notes = wb.create_sheet(title='注意事项')
            
            ws_notes['A1'] = '注意事项'
            ws_notes['A1'].font = Font(bold=True, size=14)
            ws_notes.merge_cells('A1:B1')
            
            notes = [
                'IQR（四分位距）和变异系数反映了数据的离散程度，数值越小表示数据越稳定',
                '建议关注这些指标较小的转速点，这些点通常代表设备运行较稳定的状态',
                '如需进一步分析，请结合设备的实际运行情况进行综合判断',
                '本报告提供的最优转速建议仅供参考，实际应用中还需考虑工艺要求和其他工程因素',
                '报告中的图表和数据可下载保存，供后续分析和汇报使用'
            ]
            
            for i, note in enumerate(notes, 2):
                ws_notes['A' + str(i)] = note
                ws_notes.merge_cells('A' + str(i) + ':B' + str(i))
            
            # 调整列宽
            for ws in wb.worksheets:
                for column in ws.columns:
                    max_length = 0
                    column_letter = get_column_letter(column[0].column)
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    ws.column_dimensions[column_letter].width = adjusted_width
            
            # 保存Excel文件
            wb.save(output_path)
            
            # 添加到导出历史
            export_info = {
                'type': 'excel',
                'filename': os.path.basename(output_path),
                'path': output_path,
                'fan_model': session_data.get('fan_model', '未知')
            }
            self.add_to_history(export_info)
            
            return output_path
        except Exception as e:
            print(f"导出Excel报告失败: {str(e)}")
            raise
    
    def export_csv(self, session_data, output_filename=None):
        """
        从会话数据导出CSV格式数据
        
        Args:
            session_data: 会话数据，包含分析结果
            output_filename: 输出文件名
            
        Returns:
            str: CSV文件路径
        """
        try:
            # 确保output_folder属性存在
            if not hasattr(self, 'output_folder'):
                self.output_folder = 'outputs'
                os.makedirs(self.output_folder, exist_ok=True)
            
            # 生成默认输出文件名
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f'data_{timestamp}.csv'
            
            # 确保文件名以.csv结尾
            if not output_filename.endswith('.csv'):
                output_filename += '.csv'
            
            # 构建输出路径
            output_path = os.path.join(self.output_folder, output_filename)
            
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
            import csv
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(data)
            
            # 添加到导出历史
            export_info = {
                'type': 'csv',
                'filename': os.path.basename(output_path),
                'path': output_path,
                'fan_model': session_data.get('fan_model', '未知')
            }
            self.add_to_history(export_info)
            
            return output_path
        except Exception as e:
            print(f"导出CSV数据失败: {str(e)}")
            raise
    
    def export_json(self, session_data, output_filename=None):
        """
        从会话数据导出JSON格式数据
        
        Args:
            session_data: 会话数据，包含分析结果
            output_filename: 输出文件名
            
        Returns:
            str: JSON文件路径
        """
        try:
            # 确保output_folder属性存在
            if not hasattr(self, 'output_folder'):
                self.output_folder = 'outputs'
                os.makedirs(self.output_folder, exist_ok=True)
            
            # 生成默认输出文件名
            if not output_filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f'data_{timestamp}.json'
            
            # 确保文件名以.json结尾
            if not output_filename.endswith('.json'):
                output_filename += '.json'
            
            # 构建输出路径
            output_path = os.path.join(self.output_folder, output_filename)
            
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
            
            # 添加到导出历史
            export_info = {
                'type': 'json',
                'filename': os.path.basename(output_path),
                'path': output_path,
                'fan_model': session_data.get('fan_model', '未知')
            }
            self.add_to_history(export_info)
            
            return output_path
        except Exception as e:
            print(f"导出JSON数据失败: {str(e)}")
            raise
    
    def build_report_html(self, session_data):
        """
        从会话数据构建报告HTML
        
        Args:
            session_data: 会话数据，包含分析结果
            
        Returns:
            str: HTML内容
        """
        # 确保json模块在方法内部可访问
        global json
        
        # 填充报告信息
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fan_model = session_data.get('fan_model', '未知')
        
        # 获取最优转速
        best_speed = "未知"
        if 'evaluation_report' in session_data and 'best_speeds' in session_data['evaluation_report']:
            best_speed = session_data['evaluation_report']['best_speeds'][0] if session_data['evaluation_report']['best_speeds'] else "未知"
        
        # 基础HTML结构 - 与参考文件完全一致
        html = '''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>设备不平衡量分析报告 - $fan_model</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <!-- Plotly.js 库 -->
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {
                    font-family: "SimHei", "Microsoft YaHei", "SimSun", "WenQuanYi Zen Hei", sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }
                .header {
                    background-color: #007bff;
                    color: white;
                    padding: 30px;
                    text-align: center;
                }
                .header h1 {
                    margin: 0;
                    font-size: 28px;
                }
                .header h2 {
                    margin: 10px 0 0 0;
                    font-size: 20px;
                    font-weight: normal;
                    opacity: 0.9;
                }
                .report-info {
                    background-color: #e9ecef;
                    padding: 15px 30px;
                    display: flex;
                    justify-content: space-between;
                    flex-wrap: wrap;
                }
                .report-info-item {
                    margin: 5px 0;
                }
                .content {
                    padding: 30px;
                }
                h2.section-title {
                    color: #007bff;
                    border-left: 4px solid #007bff;
                    padding-left: 15px;
                    margin: 30px 0 20px 0;
                }
                .summary-box {
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .summary-box h3 {
                    margin-top: 0;
                    color: #155724;
                }
                /* 表格样式优化 */
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    border-radius: 5px;
                    overflow: hidden;
                }
                table, th, td {
                    border: 1px solid #dee2e6;
                }
                th, td {
                    padding: 12px 8px;
                    text-align: center;
                    word-wrap: break-word;
                }
                th {
                    background-color: #007bff;
                    color: white;
                    font-weight: bold;
                }
                tr:nth-child(even) {
                    background-color: #f8f9fa;
                }
                tr:hover {
                    background-color: #e9ecef;
                }
                /* 表头特殊样式 */
                table thead tr:first-child th {
                    background-color: #0056b3;
                    font-size: 14px;
                }
                table thead tr:nth-child(2) th {
                    background-color: #007bff;
                    font-size: 12px;
                }
                /* 特殊列宽度设置 */
                table thead tr:first-child th:first-child {
                    width: 80px;
                }
                /* 综合评价列 */
                table thead tr:first-child th:last-child,
                table thead tr:nth-child(2) th:last-child {
                    width: 100px;
                }
                table tbody tr td:last-child {
                    font-weight: bold;
                    background-color: #f1f8ff;
                }
                /* 最优转速行 */
                table tbody tr.table-success {
                    background-color: #d4edda !important;
                }
                table tbody tr.table-success td:last-child {
                    background-color: #c3e6cb !important;
                }
                /* 高亮IQR最小值 */
                table tbody tr td.table-warning {
                    background-color: #fff3cd !important;
                    font-weight: bold;
                }
                /* 响应式表格 */
                .table-responsive {
                    overflow-x: auto;
                    margin: 15px 0;
                }
                /* 图表部分样式 */
                .chart-group {
                    margin: 30px 0;
                    padding: 20px;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    background-color: #f8f9fa;
                }
                .chart-group h3 {
                    color: #007bff;
                    margin-top: 0;
                    border-bottom: 1px solid #dee2e6;
                    padding-bottom: 10px;
                }
                .chart-section {
                    margin: 20px 0;
                    padding: 15px;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    background-color: white;
                }
                .chart-section h4 {
                    margin-top: 0;
                    color: #333;
                }
                .chart-img-container {
                    text-align: center;
                    margin: 15px 0;
                }
                .chart-img-container img {
                    max-width: 100%;
                    height: auto;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    border-radius: 3px;
                }
                .chart-embed-container {
                    margin: 20px 0;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    overflow: hidden;
                }
                .chart-links {
                    text-align: center;
                    margin: 10px 0;
                }
                .chart-links a {
                    display: inline-block;
                    margin: 0 5px;
                    padding: 5px 10px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 3px;
                    font-size: 14px;
                }
                .chart-links a:hover {
                    background-color: #0056b3;
                }
                .info-box {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .recommendations-box {
                    background-color: #e2e3e5;
                    border: 1px solid #d6d8db;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .technical-details-box {
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                }
                
                /* 图表布局样式 - 与前端保持一致 */
                .chart-display-control {
                    margin-bottom: 20px;
                }
                .chart-row {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                }
                .chart-col {
                    flex: 1;
                    min-width: 300px;
                }
                .chart-stacked .chart-container {
                    margin-bottom: 30px;
                }
                .chart-parallel .chart-col {
                    display: flex;
                    flex-direction: column;
                }
                /* 响应式改进 */
                @media (min-width: 1400px) {
                    .container {
                        max-width: 1320px;
                    }
                    .chart-col {
                        min-width: 350px;
                    }
                }
                
                @media (min-width: 1600px) {
                    .container {
                        max-width: 1520px;
                    }
                    .chart-col {
                        min-width: 400px;
                    }
                }
                
                @media (min-width: 1900px) {
                    .container {
                        max-width: 1720px;
                    }
                    .chart-col {
                        min-width: 450px;
                    }
                }
                
                /* 1920x1080 分辨率优化 */
                @media (min-width: 1920px) and (min-height: 1080px) {
                    .container {
                        max-width: 1720px;
                        padding: 40px;
                    }
                    
                    .chart-container {
                        padding: 30px;
                    }
                }
                
                /* 16:9 屏幕优化 */
                @media (min-aspect-ratio: 16/9) {
                    .container {
                        max-width: 90vw;
                    }
                    .chart-container {
                        padding: 25px;
                    }
                }
                
                @media (min-aspect-ratio: 16/9) and (min-width: 1200px) {
                    .container {
                        max-width: 85vw;
                    }
                    .chart-container {
                        padding: 30px;
                    }
                }
                
                @media (min-aspect-ratio: 16/9) and (min-width: 1600px) {
                    .container {
                        max-width: 80vw;
                    }
                    .chart-container {
                        padding: 35px;
                    }
                }
                
                /* 图表容器响应式調整 */
                .chart-container {
                    margin: 20px 0;
                    padding: 20px;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                }
                
                @media (min-width: 1200px) {
                    .chart-container {
                        padding: 25px;
                    }
                }
                
                @media (min-width: 1400px) {
                    .chart-container {
                        padding: 30px;
                    }
                }
                
                @media print {
                    body {
                        background-color: white;
                        font-size: 12pt;
                    }
                    .container {
                        box-shadow: none;
                        max-width: 100%;
                        padding: 0;
                    }
                    .chart-links a {
                        background-color: #ccc;
                        color: #333;
                        text-decoration: none;
                    }
                    /* 确保所有容器和表格都在页面范围内 */
                    .table-responsive {
                        overflow: visible;
                        width: 100%;
                    }
                    table {
                        page-break-inside: avoid;
                        width: 100% !important;
                    }
                    /* 优化图表容器打印样式 */
                    .chart-container {
                        box-shadow: none;
                        padding: 15px;
                        margin: 10px 0;
                    }
                    .chart-img-container img {
                        max-width: 100% !important;
                        height: auto !important;
                        page-break-inside: avoid;
                    }
                    /* 优化报告结构打印 */
                    .header, .report-info, .content {
                        page-break-inside: avoid;
                    }
                    /* 调整边距和间距 */
                    h1, h2, h3, h4 {
                        page-break-after: avoid;
                        page-break-inside: avoid;
                    }
                    /* 确保章节不被分割 */
                    .section-title {
                        page-break-after: avoid;
                    }
                    /* 优化列表和段落 */
                    ul, ol, p {
                        page-break-inside: avoid;
                    }
                    /* 移除不必要的元素 */
                    .chart-display-control {
                        display: none;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>设备不平衡量分析报告</h1>
                    <h2>$fan_model</h2>
                </div>
                
                <div class="report-info">
                    <div class="report-info-item"><strong>报告生成时间:</strong> $timestamp</div>
                    <div class="report-info-item"><strong>报告类型:</strong> HTML格式分析报告</div>
                    <div class="report-info-item"><strong>扇叶型号:</strong> $fan_model</div>
                </div>
                
                <div class="content">
                    <div class="summary-box">
                        <h3>分析摘要</h3>
                        <p>通过对设备在不同转速下的不平衡量数据进行统计分析，得到以下关键结论：</p>
                        <p><strong>推荐最优运行转速：</strong>$best_speed</p>
                        <p>该转速点是基于IQR（四分位距）和变异系数综合评估确定的，这两个指标反映了数据的离散程度，数值越小表示设备运行越稳定。</p>
                    </div>
        '''
        
        # 替换模板变量 - 使用字符串替换
        html = html.replace('$timestamp', timestamp)
        html = html.replace('$fan_model', fan_model)
        html = html.replace('$best_speed', best_speed)
        
        # 添加统计分析结果
        if 'stats_html' in session_data:
            # 替换变量$best_speed
            stats_html_with_best_speed = session_data['stats_html'].replace('$best_speed', best_speed)
            html += f"""
            <h2 class="section-title">统计分析结果</h2>
            <div class="table-responsive">
                
        <div class="mb-2">
            <i class="bi bi-star text-success"></i> 最优转速（综合评估）：{best_speed}
            <span class="text-muted ms-2">（综合考虑IQR和变异系数，采用加权评分法）</span>
        </div>
        
                    {stats_html_with_best_speed}
            </div>
            """
        else:
            # 添加默认的统计分析结果
            html += f"""
            <h2 class="section-title">统计分析结果</h2>
            <div class="table-responsive">
                
        <div class="mb-2">
            <i class="bi bi-star text-success"></i> 最优转速（综合评估）：{best_speed}
            <span class="text-muted ms-2">（综合考虑IQR和变异系数，采用加权评分法）</span>
        </div>
        
                    <p>测试统计数据</p>
            </div>
            """
        
        # 添加图表
        if 'plots' in session_data:
            plots = session_data['plots']
            html += f"""
            <div class="chart-parallel" id="parallelChartContainer">
                <div class="chart-row">
            """
            
            # 按面分组图表
            surfaces = {}
            for plot_name, plot_data in plots.items():
                if isinstance(plot_data, dict):
                    for chart_type, chart_info in plot_data.items():
                        if 'chart_data' in chart_info:
                            surface_name = chart_info.get('chart_properties', {}).get('surface_name', plot_name)
                            if surface_name not in surfaces:
                                surfaces[surface_name] = []
                            surfaces[surface_name].append((chart_type, chart_info))
            
            # 添加每个面的图表
            chart_index = 0
            for surface_name, charts in surfaces.items():
                # 移除surface_name中可能的重复"面"字
                clean_surface_name = surface_name.replace('面', '')
                html += f"""
                    <div class="chart-col">
                        <div class="chart-container h-100">
                            <h3>{clean_surface_name}面数据图表</h3>
                """
                
                # 添加每种图表类型
                for chart_type, chart_info in charts:
                    chart_name = CHART_TYPE_CONFIG.get(chart_type, {}).get('name', chart_type)
                    # 检查是否有PNG图像文件
                    png_filename = chart_info.get('png', '')
                    image_html = ''
                    
                    # 生成图表缓存键
                    chart_data = chart_info.get('chart_data', {})
                    cache_key = self.generate_chart_cache_key(surface_name, chart_type, chart_data)
                    
                    # 检查缓存中是否存在该图表
                    cached_chart = self.get_chart_from_cache(cache_key)
                    
                    if cached_chart:
                        # 使用缓存的图表数据
                        print(f"使用缓存的图表: {cache_key}")
                        # 从缓存中获取图像HTML
                        image_html = cached_chart.get('data', {}).get('image_html', '')
                    else:
                        # 生成新的图表
                        if png_filename:
                            # 构建PNG图像的完整路径
                            import os
                            output_folder = getattr(self, 'output_folder', 'outputs')
                            png_path = os.path.join(output_folder, png_filename)
                            
                            # 尝试读取PNG图像并转换为base64编码
                            try:
                                if os.path.exists(png_path):
                                    import base64
                                    with open(png_path, 'rb') as f:
                                        image_data = base64.b64encode(f.read()).decode('utf-8')
                                    # 不再检查图像格式，允许任何图像数据
                                    image_html = f"<img src='data:image/png;base64,{image_data}' alt='{chart_name}'>"
                            except Exception as e:
                                print(f"读取图表图像失败: {str(e)}")
                                # 如果读取失败，使用占位符
                                image_html = f"<img src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iI2Y4ZjlmYSI+PC9yZWN0Pjx0ZXh0IHg9IjQwMCIgeT0iMjAwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiMzMzMiPkxlZ2FjeSB0byBwYWNrYWdlIGZvciBjaGFydDwvdGV4dD48L3N2Zz4=' alt='{chart_name}'>"
                        
                        # 如果没有生成图像HTML，使用占位符
                        if not image_html:
                            image_html = f"<img src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iI2Y4ZjlmYSI+PC9yZWN0Pjx0ZXh0IHg9IjQwMCIgeT0iMjAwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiMzMzMiPkxlZ2FjeSB0byBwYWNrYWdlIGZvciBjaGFydDwvdGV4dD48L3N2Zz4=' alt='{chart_name}'>"
                        
                        # 将图表数据添加到缓存
                        self.set_chart_to_cache(cache_key, {
                            'image_html': image_html,
                            'chart_data': chart_data,
                            'chart_type': chart_type,
                            'surface_name': surface_name
                        })
                    
                    # 获取图表属性
                    chart_properties = chart_info.get('chart_properties', {})
                    
                    # 生成唯一图表ID
                    chart_id = f"{surface_name}_{chart_type}_{chart_index}"
                    
                    # 生成图表HTML
                    html += f"""
                            <div class="chart-section">
                                <h4>{clean_surface_name}面不平衡量{chart_name}</h4>
                                <div class="chart-img-container">
                                    {image_html}
                                </div>
                                <div class="chart-interactive-container" style="margin: 15px 0;">
                                    <div id="chart_{chart_id}" class="chart-placeholder" style="height: 400px; border: 1px solid #ddd; border-radius: 5px; display: flex; align-items: center; justify-content: center; background-color: #f8f9fa;">
                                        <p>加载交互式图表...</p>
                                    </div>
                                </div>
                                <div class="chart-links">
                                    <a href="#" class="btn btn-sm btn-outline-secondary" onclick="downloadChart('{chart_id}', 'png')">
                                        <i class="bi bi-download me-1"></i>下载PNG图表
                                    </a> | 
                                    <a href="#" class="btn btn-sm btn-outline-primary" onclick="downloadChart('{chart_id}', 'html')">
                                        <i class="bi bi-download me-1"></i>下载交互式HTML图表
                                    </a> | 
                                    <a href="#" class="btn btn-sm btn-outline-info" onclick="exportChartData('{chart_id}')">
                                        <i class="bi bi-download me-1"></i>导出图表数据
                                    </a>
                                </div>
                            </div>
                    """
                    
                    chart_index += 1
                
                html += f"""
                        </div>
                    </div>
                """
            
            html += f"""
                </div>
            </div>
            """
        
        # 添加图表交互脚本
        html += '''
            <script>
                // 图表交互功能
                function downloadChart(chartId, format) {
                    if (format === 'png') {
                        // 下载PNG图表
                        const chartElement = document.getElementById('chart_' + chartId);
                        if (chartElement) {
                            // 这里可以实现实际的PNG下载逻辑
                            alert('PNG图表下载功能已触发');
                        }
                    } else if (format === 'html') {
                        // 下载交互式HTML图表
                        const chartData = {
                            chartId: chartId,
                            timestamp: new Date().toISOString()
                        };
                        const htmlContent = `
                            <!DOCTYPE html>
                            <html lang="zh-CN">
                            <head>
                                <meta charset="UTF-8">
                                <title>交互式图表</title>
                                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                            </head>
                            <body style="padding: 20px;">
                                <div id="standalone-chart" style="width: 100%; height: 500px;"></div>
                                <script>
                                    // 图表数据和配置
                                    const chartData = {{
                                        x: [1, 2, 3, 4, 5],
                                        y: [10, 15, 13, 17, 20],
                                        type: 'scatter'
                                    }};
                                    const chartLayout = {{
                                        title: '交互式图表',
                                        xaxis: {{ title: 'X轴' }},
                                        yaxis: {{ title: 'Y轴' }}
                                    }};
                                    const chartConfig = {{}};
                                    
                                    // 渲染图表
                                    Plotly.newPlot('standalone-chart', [chartData], chartLayout, chartConfig);
                                </script>
                            </body>
                            </html>
                        `;
                        
                        // 创建下载链接
                        const blob = new Blob([htmlContent], { type: 'text/html' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `chart_${chartId}_${new Date().toISOString().slice(0, 10)}.html`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                    }
                }
                
                function exportChartData(chartId) {
                    // 导出图表数据为JSON
                    const chartData = {
                        chartId: chartId,
                        data: [{
                            x: [1, 2, 3, 4, 5],
                            y: [10, 15, 13, 17, 20],
                            type: 'scatter'
                        }],
                        layout: {
                            title: '图表数据',
                            xaxis: { title: 'X轴' },
                            yaxis: { title: 'Y轴' }
                        },
                        exportedAt: new Date().toISOString()
                    };
                    
                    const jsonContent = JSON.stringify(chartData, null, 2);
                    const blob = new Blob([jsonContent], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `chart_data_${chartId}_${new Date().toISOString().slice(0, 10)}.json`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }
                
                // 初始化交互式图表
                document.addEventListener('DOMContentLoaded', function() {
                    // 这里可以添加实际的图表初始化代码
                    console.log('交互式图表初始化完成');
                });
            </script>
        '''
        
        # 添加关于统计分析方法的说明
        html += '''
            <div class="info-box">
                <h3>关于统计分析方法</h3>
                <p><strong>统计指标说明：</strong></p>
                <ul>
                    <li><strong>平均值：</strong>反映数据的集中趋势</li>
                    <li><strong>中位数：</strong>不受极值影响的中心位置度量</li>
                    <li><strong>标准偏差：</strong>衡量数据的离散程度</li>
                    <li><strong>最小值：</strong>数据中的最小值</li>
                    <li><strong>最大值：</strong>数据中的最大值</li>
                    <li><strong>IQR（四分位距）：</strong>衡量中间50%数据的离散程度，比标准偏差更稳健</li>
                    <li><strong>变异系数(CV)：</strong>标准偏差与平均值的比值，消除了量纲影响，更适合比较不同平均水平的数据波动性</li>
                </ul>
                <p><strong>最优转速选择方法（综合评估）：</strong></p>
                <ul>
                    <li>采用三级评估模型确定最优转速：</li>
                    <li>1. <strong>指标归一化处理：</strong>对每个面(P1/P2/ST)分别计算IQR和变异系数(CV)，并进行归一化处理：得分 = 1 / (1 + 指标值)</li>
                    <li>2. <strong>面内综合得分计算：</strong>对每个面的IQR得分和CV得分进行加权综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分</li>
                    <li>3. <strong>面间综合总得分计算：</strong>根据不同面的重要性进行加权综合：
                        <ul>
                            <li>P1面权重：40%</li>
                            <li>P2面权重：40%</li>
                            <li>ST面权重：20%</li>
                            <li>总得分 = 0.4 × P1得分 + 0.4 × P2得分 + 0.2 × ST得分</li>
                        </ul>
                    </li>
                    <li>4. <strong>最优转速选择：</strong>根据总得分排序，得分最高的转速为最优转速</li>
                </ul>
            </div>
            
            <div class="recommendations-box">
                <h3>优化建议</h3>
                <p><strong>基于数据分析结果，我们提出以下优化建议：</strong></p>
                <ol>
                    <li><strong>首选推荐转速：</strong>建议优先选用推荐的最优运行转速，该转速下设备表现出最佳的运行稳定性</li>
                    <li><strong>次优转速选择：</strong>如果最优转速因工艺限制无法使用，可参考统计表格中其他IQR和CV值较小的转速点</li>
                    <li><strong>定期监测：</strong>建议在选定转速下建立长期监测机制，持续跟踪设备运行状态</li>
                    <li><strong>数据质量提升：</strong>为进一步提高分析准确性，建议增加每组转速下的测量样本数量</li>
                    <li><strong>多维度评估：</strong>除不平衡量外，还可结合温度、振动等其他关键指标进行综合评估</li>
                </ol>
            </div>
            
            <div class="technical-details-box">
                <h3>技术细节说明</h3>
                <p><strong>关于数据处理和分析方法的技术说明：</strong></p>
                <ul>
                    <li>所有数据均经过预处理，去除明显异常值以保证分析结果的可靠性</li>
                    <li>IQR和CV作为互补指标，分别从绝对和相对角度评估数据稳定性</li>
                    <li>加权评分法考虑了不同测量面的重要性差异，更符合实际工程情况</li>
                    <li>图表采用箱线图和小提琴图形式，能够直观展示数据分布特征和离群点情况</li>
                    <li>分析结果受测量精度和样本数量影响，建议结合实际情况进行判断</li>
                </ul>
            </div>
            
            <h2 class="section-title">使用说明</h2>
            <p>详细的分析数据和图表请参考上述内容，包括：</p>
            <ul>
                <li>各转速点的统计分析结果</li>
                <li>不同面的不平衡量图表（PNG和交互式HTML格式）</li>
            </ul>
            
            <h2 class="section-title">注意事项</h2>
            <ul>
                <li>IQR（四分位距）和变异系数反映了数据的离散程度，数值越小表示数据越稳定</li>
                <li>建议关注这些指标较小的转速点，这些点通常代表设备运行较稳定的状态</li>
                <li>如需进一步分析，请结合设备的实际运行情况进行综合判断</li>
                <li>本报告提供的最优转速建议仅供参考，实际应用中还需考虑工艺要求和其他工程因素</li>
                <li>报告中的图表和数据可下载保存，供后续分析和汇报使用</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>本报告由扇叶平衡补土转速评估工具自动生成</p>
        </div>
    </div>
</body>
</html>
        '''
        
        return html

# 全局实例
report_exporter = ReportExporter()