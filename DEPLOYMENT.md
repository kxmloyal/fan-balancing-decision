# 扇叶平衡补土转速评估工具部署指南

## 部署环境要求

### 系统要求
- Linux发行版（Ubuntu/CentOS/Debian等）或Windows Server
- Python 3.7或更高版本
- 至少2GB内存（建议4GB以上）
- 至少10GB磁盘空间

### 软件依赖
- Python 3.7+
- pip包管理器
- Git（用于代码拉取）
- Nginx（生产环境推荐）
- Supervisor（生产环境推荐）

## 部署方式

### 开发环境部署

1. 克隆项目代码：
   ```bash
   git clone <项目地址>
   cd xiangxiantu
   ```

2. 创建虚拟环境（推荐）：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   ```

3. 安装Python依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 启动应用：
   ```bash
   python app.py
   ```

5. 访问应用：
   浏览器打开 http://localhost:1322

### 生产环境部署

#### 方式一：使用Gunicorn（推荐）

1. 安装Gunicorn：
   ```bash
   pip install gunicorn
   ```

2. 启动应用：
   ```bash
   gunicorn -c gunicorn_conf.py app:app
   ```

3. 配置说明（gunicorn_conf.py）：
   ```python
   # 项目目录
   chdir = '/www/wwwroot/xiangxiantu'
   
   # 指定进程数（根据服务器内存调整）
   workers = 2
   
   # 指定每个进程开启的线程数
   threads = 1
   
   # 启动用户
   user = 'www'
   
   # 启动模式
   worker_class = 'sync'
   
   # 绑定的ip与端口
   bind = '0.0.0.0:1322' 
   
   # 设置进程文件目录（用于停止服务和重启服务，请勿删除）
   pidfile = '/www/wwwroot/xiangxiantu/gunicorn.pid'
   
   # 设置访问日志和错误信息日志路径
   accesslog = '/www/wwwlogs/python/xiangxiantu/gunicorn_acess.log'
   errorlog = '/www/wwwlogs/python/xiangxiantu/gunicorn_error.log'
   
   # 日志级别
   loglevel = 'info'
   
   # 内存优化配置
   max_requests = 1000
   max_requests_jitter = 100
   ```
   
   内存优化说明：
   - workers: 减少工作进程数量可以显著降低内存使用
   - threads: 减少线程数量也可以节省内存
   - max_requests: 工作进程处理指定请求数后重启，有助于释放内存
   - max_requests_jitter: 随机化重启阈值，避免所有进程同时重启

#### 方式二：使用uWSGI

1. 安装uWSGI：
   ```bash
   pip install uwsgi
   ```

2. 启动应用：
   ```bash
   uwsgi --ini uwsgi.ini
   ```

3. 配置说明（uwsgi.ini）：
   ```ini
   [uwsgi]
   #项目目录
   chdir=/www/wwwroot/xiangxiantu
   
   #指定项目application
   wsgi-file=/www/wwwroot/xiangxiantu/app.py
   
   #python 程序内用以启动的application 变量名
   callable=app
   
   # 进程个数（根据服务器内存调整）
   processes=2
   
   # 线程个数
   threads=1
   
   #指定启动时的pid文件路径（用于停止服务和重启服务，请勿删除）
   pidfile=/www/wwwroot/xiangxiantu/uwsgi.pid
   
   # 指定ip及端口
   http=0.0.0.0:1322
   
   #启动uwsgi的用户名和用户组
   uid=www
   gid=www
   
   #启用主进程
   master=true
   
   # 设置缓冲区大小
   buffer-size = 32768
   
   # 后台运行,并输出日志
   daemonize = /www/wwwlogs/python/xiangxiantu/uwsgi.log
   ```

### 宝塔面板部署

项目支持在宝塔面板中部署，使用Nginx反向代理转发请求至1322端口，并通过Supervisor管理Gunicorn进程。

#### 部署步骤：

1. 在宝塔面板中创建网站，设置域名和根目录

2. 上传项目代码到网站根目录

3. 安装Python项目管理器插件

4. 在Python项目管理器中添加项目：
   - 项目名称：自定义
   - 项目路径：网站根目录
   - 启动文件：app.py
   - 启动命令：gunicorn -c gunicorn_conf.py app:app
   - 端口：1322

5. 配置Nginx反向代理：
   在网站设置中配置反向代理：
   ```
   代理目录: /
   目标URL: http://127.0.0.1:1322
   ```

6. 启动项目并访问网站

## 系统配置说明

### 配置文件（config.py）

```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'boxplot_tool_2025_secure_key'
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER') or 'outputs'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 5 * 1024 * 1024)
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json', 'xml', 'txt'}
```

配置项说明：
- SECRET_KEY: Flask应用密钥，用于会话加密
- SESSION_TYPE: 会话存储类型，当前使用文件系统存储
- PERMANENT_SESSION_LIFETIME: 会话生命周期（秒）
- UPLOAD_FOLDER: 上传文件存储目录
- OUTPUT_FOLDER: 输出文件存储目录
- MAX_CONTENT_LENGTH: 最大上传文件大小限制（字节）
- ALLOWED_EXTENSIONS: 允许上传的文件扩展名

### 系统级依赖

对于PDF导出功能，需要安装系统级依赖wkhtmltopdf：

## 故障排除

### 内存不足问题

如果你看到类似以下的日志信息：
```
[WARNING] Worker with pid XXXX was terminated due to signal 9
```

这通常表示系统内存不足，工作进程被操作系统强制终止。解决方案：

1. 减少Gunicorn/uWSGI的工作进程数和线程数（如上面配置所示）

2. 启用工作进程的自动重启机制：
   ```python
   # 在 gunicorn_conf.py 中添加
   max_requests = 1000
   max_requests_jitter = 100
   ```

3. 定期清理临时文件，在 [app.py](file:///z%3A/docker/baota/wwwroot/xiangxiantu/app.py) 中已经添加了自动清理机制

4. 增加服务器内存或升级服务器配置

### 其他常见问题

1. 如果遇到权限问题，请确保运行用户对项目目录有读写权限
2. 如果遇到端口占用问题，请检查端口是否已被其他进程占用
3. 如果遇到依赖问题，请确保所有依赖包都已正确安装

## 日志管理

应用会产生以下日志文件：

1. Gunicorn日志：
   - 访问日志：`/www/wwwlogs/python/xiangxiantu/gunicorn_access.log`
   - 错误日志：`/www/wwwlogs/python/xiangxiantu/gunicorn_error.log`

2. uWSGI日志：
   - 运行日志：`/www/wwwlogs/python/xiangxiantu/uwsgi.log`

3. Flask应用日志：
   - 存储在应用运行时的控制台输出中

## 常见问题处理

### 1. 启动失败

检查以下几点：
- 端口1322是否被占用
- Python依赖是否完整安装
- 配置文件是否正确

### 2. 图表显示异常

检查：
- 浏览器控制台是否有JavaScript错误
- 图表生成函数是否正常执行
- 数据格式是否正确

### 3. 文件上传失败

检查：
- 文件大小是否超过限制
- 文件格式是否在允许范围内
- 上传目录权限是否正确

### 4. 内存不足

调整配置：
- 减少Gunicorn/uWSGI的进程数和线程数
- 增加服务器内存
- 定期清理临时文件

## 维护建议

1. 定期备份重要数据和配置文件
2. 定期清理上传和输出目录，释放磁盘空间
3. 监控系统性能和资源使用情况
4. 定期更新依赖包以修复安全漏洞
5. 根据用户反馈优化用户体验