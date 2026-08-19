# 导出配置模块
import os
import secrets

# 基础配置
BASE_CONFIG = {
    # ⚠ SECRET_KEY 在 wsgi.py 中统一管理（优先级: 环境变量 > 持久化文件 > 自动生成）
    # 这里仅作模块直接引用时的 fallback，生产环境 wsgi.py 会覆盖此值
    "SECRET_KEY": os.environ.get("SECRET_KEY", secrets.token_hex(32)),
    "UPLOAD_FOLDER": os.environ.get("UPLOAD_FOLDER", "uploads"),
    "OUTPUT_FOLDER": os.environ.get("OUTPUT_FOLDER", "outputs"),
    "STATIC_FOLDER": os.environ.get("STATIC_FOLDER", "static"),
    "STATIC_URL_PATH": os.environ.get("STATIC_URL_PATH", "/static"),
    "MAX_CONTENT_LENGTH": int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)),  # 16MB
    # Matplotlib配置
    "MPLCONFIGDIR": os.environ.get("MPLCONFIGDIR", "/tmp/matplotlib_config"),
    # 数据库配置
    "SQLALCHEMY_DATABASE_URI": os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///app.db"),
    # 服务器配置
    "HOST": os.environ.get("HOST", "0.0.0.0"),
    "PORT": int(os.environ.get("PORT", 1333)),
    # 调试模式
    "DEBUG": os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes"),
}

# 导出配置
EXPORT_CONFIG = {
    # 输出目录配置
    "OUTPUT_FOLDER": BASE_CONFIG["OUTPUT_FOLDER"],
    # 历史记录配置
    "MAX_HISTORY_ITEMS": int(os.environ.get("MAX_HISTORY_ITEMS", 100)),
    # 任务管理配置
    "MAX_CONCURRENT_TASKS": int(os.environ.get("MAX_CONCURRENT_TASKS", 3)),
    # 图表配置
    "CHART_CONFIG": {"default_height": 400, "default_width": 800, "quality": "high"},
    # 报告配置
    "REPORT_CONFIG": {
        "default_title": "设备不平衡量分析报告",
        "default_header": "扇叶平衡补土转速评估工具",
        "default_footer": "本报告由扇叶平衡补土转速评估工具自动生成\n-----技术支持By-KXM",
    },
}

# 平衡机型号预置列表（可自行增删改）
BALANCE_MACHINE_MODELS = [
    "申克 HM20BU",
    "申克 HM3BU",
    "申克 HM4U",
    "申克 HM6U",
    "申克 PASIO 5",
    "申克 PASIO 15",
    "申克 PASIO 50",
    "岛精 SH-T",
    "DSK WBE-3000",
    "DSK WBE-1000",
    "CEMB Z5",
    "CEMB Z10",
    "上海剑平 PHQ-100",
    "上海剑平 PHQ-300",
    "上海剑平 PHQ-500",
    "集智",
    "定制/其他",
]

# 依赖检查配置
DEPENDENCY_CONFIG = {
    "weasyprint": {
        "required": True,
        "install_command": "pip install weasyprint",
        "windows_deps": "需要安装GTK+运行时，请参考WEASYPRINT_INSTALLATION_GUIDE.md",
        "linux_deps": "需要安装系统依赖: sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info",
    },
    "python-docx": {"required": False, "install_command": "pip install python-docx"},
    "openpyxl": {"required": False, "install_command": "pip install openpyxl"},
}

# 检查weasyprint是否可用
WEASYPRINT_AVAILABLE = False
try:
    from weasyprint import CSS, HTML

    WEASYPRINT_AVAILABLE = True
except ImportError:
    # weasyprint不可用，PDF导出功能将不可用
    pass

# 检查python-docx是否可用
DOCX_AVAILABLE = False
try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    DOCX_AVAILABLE = True
except ImportError:
    # python-docx不可用，Word导出功能将不可用
    pass

# 检查openpyxl是否可用
EXCEL_AVAILABLE = False
try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    EXCEL_AVAILABLE = True
except ImportError:
    # openpyxl不可用，Excel导出功能将不可用
    pass
