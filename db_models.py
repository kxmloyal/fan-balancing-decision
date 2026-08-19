from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

DB_CONNECTED = False
DB_ERROR_MESSAGE = ""
db = None

UploadFile = None
AnalysisResult = None
ChartCache = None
SystemLog = None
Output = None
BalancerModel = None
Project = None


def _utcnow():
    return datetime.now(timezone.utc)


def init_db(app):
    global db, DB_CONNECTED, DB_ERROR_MESSAGE
    global UploadFile, AnalysisResult, ChartCache, SystemLog, Output, BalancerModel, Project
    try:
        db = SQLAlchemy(app)
        DB_CONNECTED = True
        if "DATABASE_ERROR" in app.config:
            del app.config["DATABASE_ERROR"]
        DB_ERROR_MESSAGE = ""

        models = define_models(db)
        UploadFile, AnalysisResult, ChartCache, SystemLog, Output, BalancerModel, Project = models

        try:
            with app.app_context():
                db.create_all()
        except Exception as e:
            DB_ERROR_MESSAGE = str(e)
            app.config["DATABASE_ERROR"] = DB_ERROR_MESSAGE
            DB_CONNECTED = False

        return db
    except Exception as e:
        DB_ERROR_MESSAGE = str(e)
        app.config["DATABASE_ERROR"] = DB_ERROR_MESSAGE
        DB_CONNECTED = False
        return None


def define_models(db):
    class UploadFile(db.Model):
        """用户上传文件模型

        存储用户上传的文件信息，包括文件名、路径、大小、类型等

        Attributes:
            id: 主键，自增整数
            filename: 文件名，最大255个字符，非空，创建索引
            file_path: 文件存储路径，最大512个字符，非空
            file_size: 文件大小（字节），非空
            user_id: 用户ID，最大100个字符，可为空，创建索引
            upload_time: 上传时间，默认为当前时间，非空
            file_type: 文件类型，最大50个字符，非空
            status: 文件状态，最大50个字符，默认为"uploaded"，非空
        """

        __tablename__ = "upload_files"

        id = db.Column(db.Integer, primary_key=True)
        filename = db.Column(db.String(255), nullable=False, index=True)
        file_path = db.Column(db.String(512), nullable=False)
        file_size = db.Column(db.Integer, nullable=False)
        user_id = db.Column(db.String(100), nullable=True, index=True)
        upload_time = db.Column(db.DateTime, nullable=False, default=_utcnow)
        file_type = db.Column(db.String(50), nullable=False)
        status = db.Column(db.String(50), nullable=False, default="uploaded")

    class AnalysisResult(db.Model):
        """分析结果模型

        存储扇叶平衡补土转速评估的分析结果

        Attributes:
            id: 主键，自增整数
            user_id: 用户ID，最大100个字符，可为空，创建索引
            fan_model: 扇叶型号，最大100个字符，可为空，创建索引
            analysis_type: 分析类型，最大100个字符，非空
            input_files: 输入文件列表，JSON格式存储，非空
            output_files: 输出文件列表，JSON格式存储，非空
            best_speed: 最优转速，最大100个字符，可为空
            analysis_time: 分析时间，默认为当前时间，非空
            status: 分析状态，最大50个字符，默认为"completed"，非空
        """

        __tablename__ = "analysis_results"

        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.String(100), nullable=True, index=True)
        fan_model = db.Column(db.String(100), nullable=True, index=True)
        analysis_type = db.Column(db.String(100), nullable=False)
        input_files = db.Column(db.Text, nullable=False)  # JSON格式存储输入文件列表
        output_files = db.Column(db.Text, nullable=False)  # JSON格式存储输出文件列表
        best_speed = db.Column(db.String(100), nullable=True)
        analysis_time = db.Column(db.DateTime, nullable=False, default=_utcnow)
        status = db.Column(db.String(50), nullable=False, default="completed")

    class ChartCache(db.Model):
        """图表缓存模型

        存储生成的图表数据，用于缓存和重用

        Attributes:
            id: 主键，自增整数
            cache_key: 缓存键，最大255个字符，非空，唯一，创建索引
            chart_data: 图表数据，JSON格式存储，非空
            created_at: 创建时间，默认为当前时间，非空
            last_accessed: 最后访问时间，默认为当前时间，非空
        """

        __tablename__ = "chart_cache"

        id = db.Column(db.Integer, primary_key=True)
        cache_key = db.Column(db.String(255), nullable=False, unique=True, index=True)
        chart_data = db.Column(db.Text, nullable=False)  # JSON格式存储图表数据
        created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
        last_accessed = db.Column(db.DateTime, nullable=False, default=_utcnow)

    class SystemLog(db.Model):
        """系统日志模型

        存储系统运行日志，用于监控和调试

        Attributes:
            id: 主键，自增整数
            log_time: 日志时间，默认为当前时间，非空
            log_level: 日志级别，最大20个字符，非空，创建索引
            module: 模块名称，最大100个字符，非空，创建索引
            message: 日志消息，非空
            user_id: 用户ID，最大100个字符，可为空，创建索引
            ip_address: IP地址，最大50个字符，可为空
            error_trace: 错误堆栈信息，可为空
        """

        __tablename__ = "system_logs"

        id = db.Column(db.Integer, primary_key=True)
        log_time = db.Column(db.DateTime, nullable=False, default=_utcnow)
        log_level = db.Column(db.String(20), nullable=False, index=True)
        module = db.Column(db.String(100), nullable=False, index=True)
        message = db.Column(db.Text, nullable=False)
        user_id = db.Column(db.String(100), nullable=True, index=True)
        ip_address = db.Column(db.String(50), nullable=True)
        error_trace = db.Column(db.Text, nullable=True)

    class Output(db.Model):
        __tablename__ = "outputs"

        id = db.Column(db.Integer, primary_key=True)
        filename = db.Column(db.String(255), nullable=False, index=True)
        file_path = db.Column(db.String(512), nullable=False)
        file_type = db.Column(db.String(20), nullable=False, default="unknown")
        file_size = db.Column(db.BigInteger, nullable=False, default=0)
        status = db.Column(db.String(50), nullable=False, default="completed")
        description = db.Column(db.Text, nullable=True)
        created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
        updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
        user_id = db.Column(db.String(100), nullable=True, index=True)
        fan_model = db.Column(db.String(100), nullable=True)
        analysis_type = db.Column(db.String(100), nullable=True)
        project_id = db.Column(db.Integer, nullable=True)

    class BalancerModel(db.Model):
        __tablename__ = "balancer_models"

        id = db.Column(db.Integer, primary_key=True)
        model_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
        manufacturer = db.Column(db.String(100), nullable=True)
        max_speed = db.Column(db.String(50), nullable=True)
        max_radius = db.Column(db.String(50), nullable=True)
        description = db.Column(db.Text, nullable=True)
        is_active = db.Column(db.Boolean, nullable=False, default=True)
        created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
        updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    class Project(db.Model):
        """项目管理模型

        用项目名称组织分析数据，支持跨电脑共享和历史回看。
        """

        __tablename__ = "projects"

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(200), nullable=False, unique=True, index=True)
        description = db.Column(db.Text, nullable=True)
        created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
        updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    return UploadFile, AnalysisResult, ChartCache, SystemLog, Output, BalancerModel, Project
