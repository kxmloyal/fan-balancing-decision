# 扇叶平衡补土转速评估工具

## 项目简介

扇叶平衡补土转速评估工具是一个专门用于分析扇叶平衡数据并评估最优转速选择的Web应用程序。该工具支持P1/P2/ST三面数据分析，具备转速匹配、统计分析、图表生成和报告导出等功能。

## 核心功能

1. **多面数据上传与处理**
   - 支持P1/P2/ST三面数据分析
   - 支持多种文件格式（CSV/XLSX/XLS/JSON/XML/TXT）
   - 转速匹配功能（当P1和P2面转速不一致时）

2. **统计分析**
   - 计算平均值、中位数、标准差、IQR（四分位距）、变异系数等指标
   - 最优转速评估（基于加权评分法）
   - 数据高亮显示（最优转速和最小IQR）

3. **数据可视化**
   - 支持多种图表类型：箱线图、小提琴图、散点图、趋势图、热力图、直方图、3D散点图
   - 组合图表展示功能（多面数据联动分析）
   - 图表交互功能（点击放大查看、动态切换）

4. **报告生成与导出**
   - HTML格式详细分析报告
   - CSV格式统计数据导出

## 环境要求

- Python 3.7+
- 依赖包见requirements.txt
- 系统级依赖：wkhtmltopdf（用于PDF生成功能）

## 安装步骤

1. 克隆项目代码：
   ```
   git clone <项目地址>
   cd xiangxiantu
   ```

2. 安装Python依赖：
   ```
   pip install -r requirements.txt
   ```

3. 安装系统级依赖（可选，用于PDF导出功能）：
   - Ubuntu/Debian: `apt-get install wkhtmltopdf`
   - CentOS/RHEL: `yum install wkhtmltopdf`
   - Windows: 从官网下载安装

## 启动方式

### 开发模式
```
python app.py
```
默认监听端口1322：http://localhost:1322

### 生产模式

#### 使用Gunicorn
```
gunicorn -c gunicorn_conf.py app:app
```

#### 使用uWSGI
```
uwsgi --ini uwsgi.ini
```

## 部署配置

### 配置文件说明

1. **config.py** - 应用基本配置
   - SECRET_KEY: Flask密钥
   - SESSION_TYPE: 会话存储类型
   - UPLOAD_FOLDER: 上传文件存储路径
   - OUTPUT_FOLDER: 输出文件存储路径
   - MAX_CONTENT_LENGTH: 最大上传文件大小

2. **gunicorn_conf.py** - Gunicorn部署配置
   - workers: 进程数
   - threads: 线程数
   - bind: 监听地址和端口
   - 日志配置等

3. **uwsgi.ini** - uWSGI部署配置
   - processes: 进程数
   - threads: 线程数
   - http: 监听地址和端口
   - 日志配置等

### 宝塔面板部署

项目支持在宝塔面板中部署，使用Nginx反向代理转发请求至1322端口，并通过Supervisor管理Gunicorn进程。

## 使用指南

1. 访问应用主页
2. 上传P1/P2/ST面数据文件
3. 系统自动进行数据分析和统计
4. 查看统计结果和图表
5. 选择需要的图表类型进行展示
6. 导出分析报告

## 项目结构

```
扇叶平衡补土转速评估工具/
├── app.py                  # 主应用程序文件
├── config.py               # 配置文件
├── requirements.txt        # 依赖包列表
├── data_processing.py      # 数据处理模块
├── chart_generation.py     # 图表生成模块
├── statistics.py           # 统计分析模块
├── utils/                  # 工具模块
│   ├── data_validator.py   # 数据验证器
│   └── chart_cache.py      # 图表缓存管理
├── templates/              # HTML模板文件
├── static/                 # 静态资源文件
├── uploads/                # 上传文件存储目录
├── outputs/                # 输出文件存储目录
└── reports/                # 报告存储目录
```

## 最优转速评估算法

采用三级评估模型确定最优转速：

1. **指标归一化处理**：
   - 单个指标得分 = 1 / (1 + 指标值)
   - 指标值越小，得分越高

2. **面内综合得分计算**：
   - 面得分 = 0.5 × IQR得分 + 0.5 × CV得分

3. **面间综合总得分计算**：
   - 总得分 = 0.4 × P1面得分 + 0.4 × P2面得分 + 0.2 × ST面得分

4. **最优转速选择**：
   - 按总得分降序排序，选择得分最高的转速

## 贡献者

- 项目开发团队

## 许可证

本项目仅供内部使用。