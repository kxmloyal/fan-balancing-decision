# 导出配置模块

# 导出配置
EXPORT_CONFIG = {
    # 输出目录配置
    'OUTPUT_FOLDER': 'outputs',
    
    # 历史记录配置
    'MAX_HISTORY_ITEMS': 100,
    
    # 任务管理配置
    'MAX_CONCURRENT_TASKS': 3,
    
    # 图表配置
    'CHART_CONFIG': {
        'default_height': 400,
        'default_width': 800,
        'quality': 'high'
    },
    
    # 报告配置
    'REPORT_CONFIG': {
        'default_title': '设备不平衡量分析报告',
        'default_header': '扇叶平衡补土转速评估工具',
        'default_footer': '本报告由扇叶平衡补土转速评估工具自动生成'
    }
}

# 依赖检查配置
DEPENDENCY_CONFIG = {
    'weasyprint': {
        'required': True,
        'install_command': 'pip install weasyprint',
        'windows_deps': '需要安装GTK+运行时，请参考WEASYPRINT_INSTALLATION_GUIDE.md',
        'linux_deps': '需要安装系统依赖: sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info'
    },
    'python-docx': {
        'required': False,
        'install_command': 'pip install python-docx'
    },
    'openpyxl': {
        'required': False,
        'install_command': 'pip install openpyxl'
    }
}
