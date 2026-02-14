# 报告导出功能 API文档与使用指南

## 1. 功能概述

报告导出功能提供了多格式的报告导出能力，支持HTML、PDF、Word、Excel、CSV和JSON等多种格式，为用户提供了灵活的报告生成和分享选项。

## 2. 核心类与方法

### 2.1 ReportExporter 主类

#### 初始化方法
```python
from report_export import ReportExporter

# 基本初始化
exporter = ReportExporter()

# 与Flask应用集成
exporter = ReportExporter(app)
exporter.init_app(app)  # 或使用延迟初始化
```

#### 通用导出方法
```python
# 导出为HTML
exporter.export('html', session_data, 'report.html')

# 导出为PDF
exporter.export('pdf', session_data, 'report.pdf')

# 导出为Word
exporter.export('docx', session_data, 'report.docx')

# 导出为Excel
exporter.export('excel', session_data, 'report.xlsx')

# 导出为CSV
exporter.export('csv', session_data, 'report.csv')

# 导出为JSON
exporter.export('json', session_data, 'report.json')
```

#### 批量导出
```python
export_tasks = [
    {'session_data': session_data, 'export_type': 'html', 'output_filename': 'report1.html'},
    {'session_data': session_data, 'export_type': 'pdf', 'output_filename': 'report1.pdf'}
]

# 顺序执行
results = exporter.batch_export(export_tasks)

# 并发执行
results = exporter.batch_export(export_tasks, concurrent=True)
```

#### 任务队列管理
```python
# 添加任务到队列
task_id = exporter.add_to_queue('pdf', session_data, 'report.pdf')

# 获取任务状态
task_status = exporter.get_task_status(task_id)

# 获取队列状态
queue_status = exporter.get_queue_status()

# 清空队列
exporter.clear_queue()

# 设置最大并发任务数
exporter.set_max_concurrent_tasks(5)
```

#### 导出历史管理
```python
# 获取导出历史
history = exporter.get_export_history(limit=10)

# 搜索导出历史
filtered_history = exporter.search_export_history(
    search_term='test',
    export_type='pdf',
    start_date='2024-01-01',
    end_date='2024-01-31',
    fan_model='Model A'
)

# 获取导出统计
export_stats = exporter.get_export_statistics()
```

#### 报告定制化
```python
# 获取默认配置
default_config = exporter.get_default_report_config()

# 设置默认配置
exporter.set_default_report_config({
    'title': '自定义报告标题',
    'include_summary': True,
    'include_stats': True,
    'include_charts': True,
    'chart_types': ['box', 'violin', 'scatter'],
    'chart_layout': 'stacked'
})

# 重置默认配置
exporter.reset_default_report_config()

# 导出时指定配置
exporter.export('html', session_data, report_config={
    'title': '临时报告标题',
    'include_summary': False,
    'custom_css': 'body { font-size: 12px; }'
})
```

#### 图表缓存管理
```python
# 清空图表缓存
exporter.clear_chart_cache()

# 获取缓存状态
cache_status = exporter.get_cache_status()
```

#### 可分享链接
```python
# 创建可分享链接
link_id = exporter.create_shareable_link('path/to/report.pdf', expire_hours=48)

# 获取共享报告
report_path = exporter.get_shared_report(link_id)
```

## 3. 配置选项

### 3.1 环境配置

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| OUTPUT_FOLDER | 导出文件保存目录 | 'outputs' |
| MAX_CONCURRENT_TASKS | 最大并发任务数 | 3 |
| MAX_CACHE_SIZE | 图表缓存最大容量 | 100 |

### 3.2 报告配置

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| title | 报告标题 | '设备不平衡量分析报告' |
| include_summary | 是否包含分析摘要 | True |
| include_stats | 是否包含统计分析结果 | True |
| include_charts | 是否包含图表 | True |
| include_methodology | 是否包含统计分析方法说明 | True |
| include_recommendations | 是否包含优化建议 | True |
| include_usage_notes | 是否包含使用注意事项 | True |
| include_technical_details | 是否包含技术细节 | True |
| chart_types | 包含的图表类型 | ['box', 'violin', 'scatter', 'histogram'] |
| chart_layout | 图表布局方式 | 'parallel' |
| custom_css | 自定义CSS样式 | '' |
| custom_header | 自定义头部内容 | '' |
| custom_footer | 自定义底部内容 | '' |

## 4. 依赖安装

### 4.1 基本依赖
```bash
pip install flask
```

### 4.2 PDF导出依赖 (WeasyPrint)

#### Windows
1. 安装GTK+运行时：https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
2. 安装WeasyPrint：`pip install weasyprint`

#### Linux
```bash
# Ubuntu/Debian
apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
pip install weasyprint

# CentOS/RHEL
yum install gcc-c++ python3-devel cairo-devel pango-devel gdk-pixbuf2-devel
pip install weasyprint
```

#### macOS
```bash
brew install cairo pango gdk-pixbuf libffi
pip install weasyprint
```

### 4.3 文档导出依赖
```bash
# Word导出
pip install python-docx

# Excel导出
pip install openpyxl
```

## 5. 使用示例

### 5.1 基本使用示例

```python
from report_export import ReportExporter

# 初始化导出器
exporter = ReportExporter()

# 准备会话数据
session_data = {
    'fan_model': 'Model A',
    'evaluation_report': {
        'best_speeds': ['1500rpm'],
        'analysis_results': {...}
    },
    'stats_html': '<table>...</table>'
}

# 导出为多种格式
try:
    # 导出HTML
    html_path = exporter.export('html', session_data, 'analysis_report.html')
    print(f'HTML报告已生成: {html_path}')
    
    # 导出PDF
    pdf_path = exporter.export('pdf', session_data, 'analysis_report.pdf')
    print(f'PDF报告已生成: {pdf_path}')
    
    # 导出Word
    docx_path = exporter.export('docx', session_data, 'analysis_report.docx')
    print(f'Word报告已生成: {docx_path}')
    
    # 导出Excel
    excel_path = exporter.export('excel', session_data, 'analysis_report.xlsx')
    print(f'Excel报告已生成: {excel_path}')
    
    # 导出数据文件
    csv_path = exporter.export('csv', session_data, 'analysis_data.csv')
    print(f'CSV数据已生成: {csv_path}')
    
    json_path = exporter.export('json', session_data, 'analysis_data.json')
    print(f'JSON数据已生成: {json_path}')
    
    print('所有格式导出完成！')
except Exception as e:
    print(f'导出失败: {str(e)}')
```

### 5.2 批量导出示例

```python
from report_export import ReportExporter

# 初始化导出器
exporter = ReportExporter()

# 准备会话数据
session_data = {
    'fan_model': 'Model A',
    'evaluation_report': {
        'best_speeds': ['1500rpm'],
        'analysis_results': {...}
    },
    'stats_html': '<table>...</table>'
}

# 定义批量导出任务
export_tasks = [
    {'session_data': session_data, 'export_type': 'html', 'output_filename': 'report_html.html'},
    {'session_data': session_data, 'export_type': 'pdf', 'output_filename': 'report_pdf.pdf'},
    {'session_data': session_data, 'export_type': 'docx', 'output_filename': 'report_word.docx'},
    {'session_data': session_data, 'export_type': 'excel', 'output_filename': 'report_excel.xlsx'},
    {'session_data': session_data, 'export_type': 'csv', 'output_filename': 'report_csv.csv'},
    {'session_data': session_data, 'export_type': 'json', 'output_filename': 'report_json.json'}
]

print('开始批量导出...')

# 并发执行批量导出
results = exporter.batch_export(export_tasks, concurrent=True)

print('\n批量导出结果:')
print(f'成功: {len(results["success"])}')
print(f'失败: {len(results["failed"])}')

if results['success']:
    print('\n成功导出:')
    for item in results['success']:
        print(f'  - 任务 {item["task_index"]}: {item["result"]}')

if results['failed']:
    print('\n失败导出:')
    for item in results['failed']:
        print(f'  - 任务 {item["task_index"]}: {item["error"]}')

print('\n批量导出完成！')
```

### 5.3 自定义报告示例

```python
from report_export import ReportExporter

# 初始化导出器
exporter = ReportExporter()

# 准备会话数据
session_data = {
    'fan_model': 'Model A',
    'evaluation_report': {
        'best_speeds': ['1500rpm'],
        'analysis_results': {...}
    },
    'stats_html': '<table>...</table>'
}

# 定义自定义报告配置
custom_config = {
    'title': '风机平衡分析报告',
    'include_summary': True,
    'include_stats': True,
    'include_charts': True,
    'include_methodology': False,  # 不包含方法说明
    'include_recommendations': True,
    'include_technical_details': False,  # 不包含技术细节
    'chart_types': ['box', 'scatter'],  # 只包含部分图表类型
    'chart_layout': 'stacked',  # 使用堆叠布局
    'custom_css': '''
        body { font-family: Arial, sans-serif; }
        .header { background-color: #003366; color: white; }
        .summary-box { border: 2px solid #003366; }
    ''',
    'custom_header': '<div style="text-align: center; padding: 20px;"><img src="logo.png" alt="Company Logo" style="max-width: 200px;"></div>',
    'custom_footer': '<div style="text-align: center; padding: 10px; font-size: 12px;">© 2024 Company Name. All rights reserved.</div>'
}

# 导出自定义报告
try:
    html_path = exporter.export('html', session_data, 'custom_report.html', report_config=custom_config)
    print(f'自定义HTML报告已生成: {html_path}')
    
    pdf_path = exporter.export('pdf', session_data, 'custom_report.pdf', report_config=custom_config)
    print(f'自定义PDF报告已生成: {pdf_path}')
    
    print('自定义报告导出完成！')
except Exception as e:
    print(f'导出失败: {str(e)}')
```

## 6. 常见问题与解决方案

### 6.1 PDF导出失败

**问题**: `PDF导出功能依赖的weasyprint库不可用`

**解决方案**:
1. 确保已安装weasyprint: `pip install weasyprint`
2. 确保已安装GTK+运行时（Windows系统）
3. 参考详细安装指南: WEASYPRINT_INSTALLATION_GUIDE.md

### 6.2 Word/Excel导出失败

**问题**: `No module named 'docx'` 或 `No module named 'openpyxl'`

**解决方案**:
- 安装python-docx: `pip install python-docx`
- 安装openpyxl: `pip install openpyxl`

### 6.3 内存不足

**问题**: 导出大报告时出现内存错误

**解决方案**:
- 启用报告分块生成 (已默认实现)
- 减少并发任务数: `exporter.set_max_concurrent_tasks(2)`
- 清理图表缓存: `exporter.clear_chart_cache()`

### 6.4 任务执行超时

**问题**: 任务执行时间过长

**解决方案**:
- 检查数据量大小
- 优化图表渲染
- 考虑增加服务器资源

## 7. 性能优化建议

1. **启用并发执行**: 对于批量导出，使用 `concurrent=True` 提高效率
2. **合理设置缓存大小**: 根据服务器内存情况调整 `cache_max_size`
3. **控制并发任务数**: 根据服务器CPU核心数设置 `max_concurrent_tasks`
4. **定期清理历史记录**: 避免导出历史过大影响性能
5. **使用图表缓存**: 相同图表数据会自动缓存，减少重复渲染
6. **按需定制报告**: 对于大型报告，可通过配置减少包含内容

## 8. 安全注意事项

1. **输入验证**: 确保会话数据中的内容经过验证，避免注入攻击
2. **文件路径安全**: 避免使用用户提供的路径直接作为文件路径
3. **内存限制**: 对大文件导出设置合理限制，防止内存耗尽
4. **权限控制**: 确保导出功能只对授权用户可用
5. **临时文件清理**: 确保临时文件及时清理，避免磁盘空间耗尽

## 9. 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| 1.0.0 | 2024-01 | 初始版本，支持HTML和PDF导出 |
| 1.1.0 | 2024-01 | 添加Word、Excel、CSV、JSON导出支持 |
| 1.2.0 | 2024-01 | 实现批量导出和任务队列管理 |
| 1.3.0 | 2024-01 | 添加报告定制化功能 |
| 1.4.0 | 2024-01 | 优化图表渲染性能，添加缓存机制 |
| 1.5.0 | 2024-01 | 重构代码结构，提升模块化程度 |

## 10. 联系方式

如需技术支持或功能咨询，请联系：
- Email: support@example.com
- Phone: +86 123 4567 8910
- Website: https://example.com/support

---

*本文档由系统自动生成，最后更新时间：2024年1月*