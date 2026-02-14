import os
import tempfile
import json
from datetime import datetime
import uuid

# 导入图表类型配置
from chart_generation import CHART_TYPE_CONFIG

# 尝试导入weasyprint
try:
    from weasyprint import HTML, CSS
    # 在较新版本的weasyprint中，FontConfiguration不再需要
    WEASYPRINT_AVAILABLE = True
except ImportError as e:
    print(f"weasyprint导入失败: {str(e)}")
    print("PDF导出功能将不可用")
    WEASYPRINT_AVAILABLE = False

class ReportExporter:
    def __init__(self, app=None):
        self.app = app
        self.export_history = []
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
            raise Exception("PDF导出功能依赖的weasyprint库不可用，请安装weasyprint及其依赖（在Windows上需要GTK+运行时）")
        
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
            raise Exception("PDF导出功能依赖的weasyprint库不可用，请安装weasyprint及其依赖")
        
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
    
    def export_html(self, session_data, output_filename=None):
        """
        从会话数据导出HTML报告
        
        Args:
            session_data: 会话数据，包含分析结果
            output_filename: 输出文件名
            
        Returns:
            str: HTML文件路径
        """
        try:
            # 构建HTML内容
            html_content = self.build_report_html(session_data)
            
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
            
            # 写入HTML文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 添加到导出历史
            export_info = {
                'type': 'html',
                'filename': os.path.basename(output_path),
                'path': output_path,
                'fan_model': session_data.get('fan_model', '未知')
            }
            self.add_to_history(export_info)
            
            return output_path
        except Exception as e:
            print(f"导出HTML报告失败: {str(e)}")
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
                    
                    # 获取图表属性
                    chart_properties = chart_info.get('chart_properties', {})
                    
                    # 生成图表HTML
                    html += f"""
                            <div class="chart-section">
                                <h4>{clean_surface_name}面不平衡量{chart_name}</h4>
                                <div class="chart-img-container">
                                    {image_html}
                                </div>
                                <div class="chart-links">
                                    <a href="#" class="btn btn-sm btn-outline-secondary" download>
                                        <i class="bi bi-download me-1"></i>下载PNG图表
                                    </a> | 
                                    <a href="#" class="btn btn-sm btn-outline-primary chart-link" download>
                                        <i class="bi bi-download me-1"></i>下载交互式HTML图表
                                    </a>
                                </div>
                            </div>
                    """
                
                html += f"""
                        </div>
                    </div>
                """
            
            html += f"""
                </div>
            </div>
            """
        
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