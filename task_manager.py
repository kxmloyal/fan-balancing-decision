# 任务管理器模块
import threading
import uuid
from datetime import datetime
from .config import EXPORT_CONFIG

class TaskManager:
    def __init__(self):
        """
        任务管理器
        """
        self.export_tasks = {}  # 存储导出任务状态
        self.task_queue = []  # 任务队列
        self.running_tasks = set()  # 运行中的任务
        self.max_concurrent_tasks = EXPORT_CONFIG['MAX_CONCURRENT_TASKS']
    
    def create_task(self, task_type, session_data):
        """
        创建导出任务
        
        Args:
            task_type: 任务类型 (html, pdf, docx, excel, csv, json)
            session_data: 会话数据
            
        Returns:
            str: 任务ID
        """
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        self.export_tasks[task_id] = {
            'task_id': task_id,
            'task_type': task_type,
            'status': 'pending',  # pending, queued, in_progress, completed, failed
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
            status: 任务状态
            progress: 进度百分比
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
    
    def add_to_queue(self, task_info):
        """
        将任务添加到队列
        
        Args:
            task_info: 任务信息字典
            
        Returns:
            str: 任务ID
        """
        task_id = task_info['task_id']
        
        # 将任务添加到队列
        self.task_queue.append(task_info)
        
        # 立即处理队列
        self.process_queue()
        
        return task_id
    
    def process_queue(self):
        """
        处理任务队列
        """
        # 检查是否有空闲槽位
        while len(self.running_tasks) < self.max_concurrent_tasks and self.task_queue:
            task = self.task_queue.pop(0)
            task_id = task['task_id']
            
            # 更新任务状态为排队中
            self.update_task_status(task_id, 'queued', progress=0, message='任务已加入队列')
            
            # 启动线程执行任务
            thread = threading.Thread(target=self.execute_task, args=(task,))
            thread.daemon = True
            thread.start()
    
    def execute_task(self, task):
        """
        执行任务
        
        Args:
            task: 任务信息
        """
        task_id = task['task_id']
        task_type = task['task_type']
        session_data = task['session_data']
        output_filename = task.get('output_filename')
        exporter = task.get('exporter')
        
        try:
            # 将任务添加到运行集合
            self.running_tasks.add(task_id)
            
            # 更新任务状态为执行中
            self.update_task_status(task_id, 'in_progress', progress=10, message=f'开始执行{task_type}导出任务')
            
            # 执行导出
            if exporter and hasattr(exporter, 'export'):
                result_path = exporter.export(session_data, output_filename, task_id)
            else:
                raise Exception('导出器未定义或缺少export方法')
            
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
    
    def get_all_tasks(self):
        """
        获取所有任务
        
        Returns:
            dict: 所有任务信息
        """
        return self.export_tasks
    
    def cleanup_tasks(self, days=7):
        """
        清理过期任务
        
        Args:
            days: 保留天数
        """
        import time
        cutoff_time = time.time() - (days * 24 * 3600)
        
        expired_tasks = []
        for task_id, task_info in self.export_tasks.items():
            created_at = datetime.fromisoformat(task_info['created_at']).timestamp()
            if created_at < cutoff_time:
                expired_tasks.append(task_id)
        
        for task_id in expired_tasks:
            del self.export_tasks[task_id]
        
        return {'message': f'已清理{len(expired_tasks)}个过期任务'}
