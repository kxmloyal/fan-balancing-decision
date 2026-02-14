# PDF导出器模块
import os
from datetime import datetime

class PdfExporter:
    def __init__(self, report_exporter):
        """
        PDF导出器
        
        Args:
            report_exporter: 报告导出器实例
        """
        self.report_exporter = report_exporter
        self.output_folder = getattr(report_exporter, 'output_folder', 'outputs')
        self.weasyprint_available = False
        
        # 尝试导入weasyprint
        try:
            from weasyprint import HTML, CSS
            self.weasyprint_available = True
            self.HTML = HTML
            self.CSS = CSS
        except ImportError as e:
            print(f"weasyprint导入失败: {str(e)}")
            print("PDF导出功能将不可用")
            print("详细安装指南请参考项目根目录下的WEASYPRINT_INSTALLATION_GUIDE.md文件")
    
    def export(self, session_data, output_filename=None, task_id=None):
        """
        从会话数据导出PDF报告
        
        Args:
            session_data: 会话数据，包含分析结果
            output_filename: 输出文件名
            task_id: 任务ID（可选）
            
        Returns:
            str: PDF文件路径
            
        Raises:
            Exception: 当weasyprint不可用或PDF导出失败时抛出异常
        """
        # 检查weasyprint是否可用
        if not self.weasyprint_available:
            raise Exception("PDF导出功能依赖的weasyprint库不可用，请安装weasyprint及其依赖（在Windows上需要GTK+运行时）。详细安装指南请参考项目根目录下的WEASYPRINT_INSTALLATION_GUIDE.md文件。")
        
        try:
            # 如果提供了任务ID，更新任务状态
            if task_id:
                self.report_exporter.task_manager.update_task_status(
                    task_id, 'in_progress', progress=20, message='开始构建HTML内容'
                )
            
            # 构建HTML内容
            html_content = self.build_report_html(session_data)
            
            # 更新任务进度
            if task_id:
                self.report_exporter.task_manager.update_task_status(
                    task_id, 'in_progress', progress=50, message='HTML内容构建完成，开始转换为PDF'
                )
            
            # 导出为PDF
            pdf_path = self.export_html_to_pdf(html_content, output_filename)
            
            # 更新任务进度
            if task_id:
                self.report_exporter.task_manager.update_task_status(
                    task_id, 'in_progress', progress=90, message='PDF转换完成'
                )
            
            # 添加到导出历史
            export_info = {
                'type': 'pdf',
                'filename': os.path.basename(pdf_path),
                'path': pdf_path,
                'fan_model': session_data.get('fan_model', '未知')
            }
            self.report_exporter.history_manager.add_record(export_info)
            
            # 更新任务状态为完成
            if task_id:
                self.report_exporter.task_manager.update_task_status(
                    task_id, 'completed', progress=100, message='PDF报告导出完成', result=pdf_path
                )
            
            return pdf_path
        except Exception as e:
            # 更新任务状态为失败
            if task_id:
                self.report_exporter.task_manager.update_task_status(
                    task_id, 'failed', progress=0, message='PDF报告导出失败', error=str(e)
                )
            print(f"导出PDF报告失败: {str(e)}")
            raise
    
    def export_html_to_pdf(self, html_content, output_filename=None):
        """
        将HTML内容转换为PDF格式
        
        Args:
            html_content: HTML内容
            output_filename: 输出文件名
            
        Returns:
            str: PDF文件路径
        """
        try:
            # 确保output_folder存在
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
            header_text = '扇叶平衡补土转速评估工具'
            footer_text = f'生成时间: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}'
            
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
            css = self.CSS(string=css_string)
            
            # 将HTML转换为PDF
            html = self.HTML(string=html_content)
            html.write_pdf(output_path, stylesheets=[css])
            
            return output_path
        except Exception as e:
            print(f"PDF导出失败: {str(e)}")
            raise
    
    def build_report_html(self, session_data):
        """
        从会话数据构建报告HTML
        
        Args:
            session_data: 会话数据，包含分析结果
            
        Returns:
            str: HTML内容
        """
        # 填充报告信息
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fan_model = session_data.get('fan_model', '未知')
        
        # 获取最优转速
        best_speed = "未知"
        if 'evaluation_report' in session_data and 'best_speeds' in session_data['evaluation_report']:
            best_speed = session_data['evaluation_report']['best_speeds'][0] if session_data['evaluation_report']['best_speeds'] else "未知"
        
        # 基础HTML结构
        html = '''
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>设备不平衡量分析报告 - $fan_model</title>
            <style>
                body {
                    font-family: SimSun, serif;
                    font-size: 11pt;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }
                .container {
                    max-width: 210mm;
                    margin: 0 auto;
                    padding: 20mm;
                }
                .header {
                    text-align: center;
                    margin-bottom: 20mm;
                    padding-bottom: 10mm;
                    border-bottom: 1px solid #ddd;
                }
                .header h1 {
                    margin: 0;
                    font-size: 24pt;
                    color: #007bff;
                }
                .header h2 {
                    margin: 10mm 0 0 0;
                    font-size: 16pt;
                    font-weight: normal;
                    color: #666;
                }
                .report-info {
                    margin-bottom: 20mm;
                    padding: 10mm;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }
                .report-info-item {
                    margin: 5mm 0;
                }
                .content {
                    margin-bottom: 20mm;
                }
                h2 {
                    color: #007bff;
                    border-left: 4px solid #007bff;
                    padding-left: 10mm;
                    margin: 15mm 0 10mm 0;
                    font-size: 16pt;
                }
                h3 {
                    color: #333;
                    margin: 10mm 0 5mm 0;
                    font-size: 14pt;
                }
                .summary-box {
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    padding: 10mm;
                    border-radius: 5px;
                    margin: 10mm 0;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 10mm 0;
                }
                table, th, td {
                    border: 1px solid #ddd;
                }
                th, td {
                    padding: 5mm;
                    text-align: center;
                }
                th {
                    background-color: #007bff;
                    color: white;
                    font-weight: bold;
                }
                tr:nth-child(even) {
                    background-color: #f8f9fa;
                }
                .chart-container {
                    margin: 15mm 0;
                    text-align: center;
                }
                .chart-container img {
                    max-width: 100%;
                    height: auto;
                }
                ul, ol {
                    margin: 5mm 0;
                    padding-left: 20mm;
                }
                li {
                    margin: 3mm 0;
                }
                .footer {
                    text-align: center;
                    margin-top: 20mm;
                    padding-top: 10mm;
                    border-top: 1px solid #ddd;
                    font-size: 10pt;
                    color: #666;
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
                    <div class="report-info-item"><strong>报告类型:</strong> PDF格式分析报告</div>
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
        
        # 替换模板变量
        html = html.replace('$timestamp', timestamp)
        html = html.replace('$fan_model', fan_model)
        html = html.replace('$best_speed', best_speed)
        
        # 添加统计分析结果
        if 'stats_html' in session_data:
            # 替换变量$best_speed
            stats_html_with_best_speed = session_data['stats_html'].replace('$best_speed', best_speed)
            html += f"""
            <h2>统计分析结果</h2>
            <p><strong>最优转速（综合评估）：</strong>{best_speed}（综合考虑IQR和变异系数，采用加权评分法）</p>
            <div class="table-container">
                {stats_html_with_best_speed}
            </div>
            """
        else:
            # 添加默认的统计分析结果
            html += f"""
            <h2>统计分析结果</h2>
            <p><strong>最优转速（综合评估）：</strong>{best_speed}（综合考虑IQR和变异系数，采用加权评分法）</p>
            <p>测试统计数据</p>
            """
        
        # 添加图表
        if 'plots' in session_data:
            plots = session_data['plots']
            html += '<h2>图表分析</h2>'
            
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
                html += f'<h3>{clean_surface_name}面数据图表</h3>'
                
                for chart_type, chart_info in charts:
                    # 检查是否有PNG图像文件
                    png_filename = chart_info.get('png', '')
                    if png_filename:
                        # 构建PNG图像的完整路径
                        output_folder = getattr(self.report_exporter, 'output_folder', 'outputs')
                        png_path = os.path.join(output_folder, png_filename)
                        
                        # 尝试读取PNG图像并转换为base64编码
                        try:
                            if os.path.exists(png_path):
                                import base64
                                with open(png_path, 'rb') as f:
                                    image_data = base64.b64encode(f.read()).decode('utf-8')
                                # 添加图像到HTML
                                html += f"""
                                <div class="chart-container">
                                    <img src="data:image/png;base64,{image_data}" alt="{clean_surface_name}面图表">
                                    <p>{clean_surface_name}面数据图表</p>
                                </div>
                                """
                        except Exception as e:
                            print(f"读取图表图像失败: {str(e)}")
        
        # 添加关于统计分析方法的说明
        html += '''
            <h2>关于统计分析方法</h2>
            <h3>统计指标说明：</h3>
            <ul>
                <li><strong>平均值：</strong>反映数据的集中趋势</li>
                <li><strong>中位数：</strong>不受极值影响的中心位置度量</li>
                <li><strong>标准偏差：</strong>衡量数据的离散程度</li>
                <li><strong>最小值：</strong>数据中的最小值</li>
                <li><strong>最大值：</strong>数据中的最大值</li>
                <li><strong>IQR（四分位距）：</strong>衡量中间50%数据的离散程度，比标准偏差更稳健</li>
                <li><strong>变异系数(CV)：</strong>标准偏差与平均值的比值，消除了量纲影响，更适合比较不同平均水平的数据波动性</li>
            </ul>
            
            <h3>最优转速选择方法（综合评估）：</h3>
            <ol>
                <li><strong>指标归一化处理：</strong>对每个面(P1/P2/ST)分别计算IQR和变异系数(CV)，并进行归一化处理：得分 = 1 / (1 + 指标值)</li>
                <li><strong>面内综合得分计算：</strong>对每个面的IQR得分和CV得分进行加权综合：面得分 = 0.5 × IQR得分 + 0.5 × CV得分</li>
                <li><strong>面间综合总得分计算：</strong>根据不同面的重要性进行加权综合：
                    <ul>
                        <li>P1面权重：40%</li>
                        <li>P2面权重：40%</li>
                        <li>ST面权重：20%</li>
                        <li>总得分 = 0.4 × P1得分 + 0.4 × P2得分 + 0.2 × ST得分</li>
                    </ul>
                </li>
                <li><strong>最优转速选择：</strong>根据总得分排序，得分最高的转速为最优转速</li>
            </ol>
            
            <h2>优化建议</h2>
            <ol>
                <li><strong>首选推荐转速：</strong>建议优先选用推荐的最优运行转速，该转速下设备表现出最佳的运行稳定性</li>
                <li><strong>次优转速选择：</strong>如果最优转速因工艺限制无法使用，可参考统计表格中其他IQR和CV值较小的转速点</li>
                <li><strong>定期监测：</strong>建议在选定转速下建立长期监测机制，持续跟踪设备运行状态</li>
                <li><strong>数据质量提升：</strong>为进一步提高分析准确性，建议增加每组转速下的测量样本数量</li>
                <li><strong>多维度评估：</strong>除不平衡量外，还可结合温度、振动等其他关键指标进行综合评估</li>
            </ol>
            
            <h2>技术细节说明</h2>
            <ul>
                <li>所有数据均经过预处理，去除明显异常值以保证分析结果的可靠性</li>
                <li>IQR和CV作为互补指标，分别从绝对和相对角度评估数据稳定性</li>
                <li>加权评分法考虑了不同测量面的重要性差异，更符合实际工程情况</li>
                <li>图表采用箱线图和小提琴图形式，能够直观展示数据分布特征和离群点情况</li>
                <li>分析结果受测量精度和样本数量影响，建议结合实际情况进行判断</li>
            </ul>
            
            <h2>注意事项</h2>
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
            <p>生成时间：$timestamp</p>
        </div>
    </div>
</body>
</html>
        '''
        
        # 替换模板变量
        html = html.replace('$timestamp', timestamp)
        
        return html
