# 三省六部审查 — 剩余待修复项报告

> 生成日期: 2026-05-10
> 审查基准: 三省六部全量审查（2026-05-09）
> 已修复: 8 项 🔴 + 2 项留中待问
> 本文档: 🟡 剩余 11 项 + 4 项待改进

---

## 一、已完成的修复（本轮）

### 🔴 严重问题 — 8 项全部修复

| # | 问题 | 状态 |
|:--:|------|:--:|
| 1 | crypto_utils XOR → PBKDF2HMAC+Fernet AES 加密升级 | ✅ |
| 2 | in_depth_analysis_bp + skill_evaluation_bp → analysis_bp 统一蓝图 | ✅ |
| 3 | HtmlExporter 内联到 report_export.py，消除导出层分离 | ✅ |
| 4 | database_bp 路由合并到 settings_bp，数据库配置统一入口 | ✅ |
| 5 | project_statistics.py 迁移到 app/services/ 统一服务层 | ✅ |
| 6 | db_models.py 移除 globals() + datetime.utcnow 修复 | ✅ |
| 7 | simple-plotly-manager.js 拆分为 3 文件（core + builders + theme） | ✅ |
| 8 | Prism.js 从 CDN 迁移到本地 static/libs/prism/ | ✅ |

### 🔵 留中待问 — 2 项已处理

| # | 问题 | 结论 |
|:--:|------|------|
| ① | DEFAULT_FACE_WEIGHTS 经验值 → 可配置界面 | ✅ Settings 页面新增权重配置卡片 + 动态说明联动 |
| ② | chart_style_config.py 配置项是否全被有效调用 | ✅ 审计完成 — 仅 CHART_TYPE_CONFIG 在生产中使用，其余仅测试引用 |

---

## 二、剩余 🟡 问题清单（11 项）

### 吏部（架构）— 1 项

| # | 严重度 | 文件 | 问题 |
|:--:|:--:|------|------|
| R1 | 🟡 | `database_connections.py` | 单体文件过大（~450行），承载模型定义 + 连接池管理 + 连接测试三种职责，违反单一职责原则。建议拆分为 `models/connection_models.py` + `services/connection_manager.py` + `services/connection_tester.py` |

<div style="page-break-after: always;"></div>

### 户部（数据资源）— 2 项

| # | 严重度 | 文件 | 问题 |
|:--:|:--:|------|------|
| R2 | 🟡 | `app/utils/file_manager.py` / 上传端点 | 文件上传缺少 MIME 类型白名单验证。当前仅检查文件扩展名，未校验实际 MIME 类型。应添加 `ALLOWED_MIME_TYPES = {'text/csv', 'application/vnd.ms-excel', ...}` 并使用 `mimetypes` 或 `python-magic` 验证 |
| R3 | 🟡 | `app/utils/config_manager.py` | `os.path.dirname(os.path.dirname(os.path.dirname(__file__)))` 三重链式推路径推导项目根目录，脆弱且不直观。建议改用 `pathlib.Path(__file__).resolve().parents[2]` 或环境变量 `PROJECT_ROOT` |

### 礼部（API 规范）— 2 项

| # | 严重度 | 文件 | 问题 |
|:--:|:--:|------|------|
| R4 | 🟡 | 全蓝图路由 | 缺少统一 `ApiResponse` 响应封装类。各路由自行构造 `{"success": bool, "message": str, "data": ...}`，容易出现字段名不一致（如 `error` vs `message`）。建议创建 `app/utils/api_response.py` |
| R5 | 🟡 | `analysis_bp.py` 趋势/聚类端点 | 计算密集型接口缺少速率限制。趋势分析、聚类分析等端点可能被高频调用耗尽 CPU。建议集成 `flask-limiter` 对 `/api/analysis/*` 路径设置 `@limiter.limit("10 per minute")` |

### 兵部（安全）— 2 项

| # | 严重度 | 文件 | 问题 |
|:--:|:--:|------|------|
| R6 | 🟡 | `app/utils/error_handler.py` | `handle_generic_exception` 异常响应暴露 `error_type` 字段（如 `ValueError`、`KeyError`），向外部泄露内部实现细节。生产环境建议脱敏为通用 `"InternalError"` |
| R7 | 🟡 | `app/utils/error_handler.py` / 响应中间件 | gzip 压缩后手动设置 `Content-Length` header 可能不正确。压缩后响应体字节数改变，若 `Content-Length` 基于未压缩大小计算，客户端可能截断或挂起。建议使用 WSGI 中间件自动处理 |

### 刑部（算法）— 1 项

| # | 严重度 | 文件 | 问题 |
|:--:|:--:|------|------|
| R8 | 🟡 | `app/services/data_analysis.py` `_elbow_method()` | KMeans 初始化缺少固定 `random_state` 参数。每次运行聚类结果可能不同，影响分析可复现性。修复方式: `KMeans(n_clusters=k, random_state=42, n_init='auto')` |

### 工部（工程）— 3 项

| # | 严重度 | 文件 | 问题 |
|:--:|:--:|------|------|
| R9 | 🟡 | `report_export.py` `_html_exporter_css()` | CSS 内嵌为 Python 多行字符串（~70行），不利于样式维护和主题切换。建议外部化到 `static/css/report_style.css` 并在导出时读取 |
| R10 | 🟡 | `config.py` + `wsgi.py` | `config.py` 中 `SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-key')` 与 `wsgi.py` 的 `_get_or_create_secret_key()` 持久化逻辑存在潜在冲突。两处各自维护默认/持久化逻辑，应统一到一处 |
| R11 | 🟡 | 项目根目录 | 缺少 `ruff` / `black` / `mypy` 自动化代码检查工具链。无 `.pre-commit-config.yaml`、`pyproject.toml` [tool.ruff] 或 CI 配置 |

---

## 三、待改进项（下月优先级，4 项）

| # | 描述 | 涉及文件 |
|:--:|------|------|
| I1 | 集成 `python-dotenv` 环境变量管理，替代手动 `os.environ.get()` | `config.py`、`wsgi.py` |
| I2 | 添加 `flask-limiter` API 速率限制（与 R5 同一问题） | `wsgi.py`、高频端点 |
| I3 | `html_exporter.py` CSS 外部化（与 R9 同一问题） | `report_export.py` |
| I4 | `ruff` + `black` + `mypy` 自动化检查（与 R11 同一问题） | 项目根目录 |

---

## 四、修复优先级建议

### 本月（高优先级）

| 序号 | 编号 | 简述 | 预估影响范围 |
|:--:|:--:|------|:--|
| 1 | R6 | 生产环境异常信息脱敏 | 低风险 — 修改 error_handler 一处 |
| 2 | R8 | KMeans random_state 固定 | 低风险 — 算法可复现性修复 |
| 3 | R4 | ApiResponse 统一响应封装 | 中风险 — 涉及全部蓝图路由 |
| 4 | R1 | database_connections.py 拆分 | 中风险 — 架构重构 |

### 下月（中优先级）

| 序号 | 编号 | 简述 |
|:--:|:--:|------|
| 5 | R2 + R3 | 文件MIME验证 + 路径推导修复 |
| 6 | R9 + R10 | CSS外部化 + SECRET_KEY统一 |
| 7 | R5 + I2 | 速率限制 |
| 8 | R7 | gzip Content-Length 修复 |
| 9 | R11 + I1 + I4 | ruff/black/mypy + python-dotenv |

---

## 五、已完成修复对其他项的联动影响

| 已修项目 | 对剩余项的影响 |
|------|------|
| Fix 5 (project_statistics 迁移) | ✅ R0（吏部#1 已解决） |
| Fix 3 (HtmlExporter 内联) | R9 CSS 仍需外部化（CSS 从 exporters/html_exporter.py 移至 report_export.py，但仍是内嵌字符串） |
| Fix 4 (database_bp 合并) | R1 拆分与蓝图合并无关，仍需按职责拆分 models/manager/tester |
| 留中待问① (权重配置) | ✅ 经验值可配置 + 动态说明联动已完成 |
| 留中待问② (chart_style_config 审计) | ✅ 审计报告已完成（仅 CHART_TYPE_CONFIG 在生产中使用） |

---

## 附录 A：chart_style_config.py 审计摘要

| 项目 | 状态 | 说明 |
|------|:--:|------|
| CHART_TYPE_CONFIG | ✅ 在用 | main_bp.py(9次), chart_generation_optimized.py(2次), report_bp.py(回退) |
| 其余 11 个配置对象 | ❌ 未用 | 仅 tests/test_chart_style_consistency.py 引用 |
| 6 个 getter 函数 | ❌ 未用 | 全部仅在测试中被调用 |
| ⚠️ 重复定义 | — | app/services/chart_generation.py 也有一份 CHART_TYPE_CONFIG（缺少 plotly_color 字段） |

---

## 附录 B：DEFAULT_FACE_WEIGHTS 可配置界面摘要

| 组件 | 实现位置 |
|------|------|
| 持久化层 | `app/utils/config_manager.py` — `get_face_weights()` / `save_face_weights()` / `reset_face_weights()` |
| API 端点 | `blueprints/settings_bp.py` — GET `/face_weights` · POST `/save_face_weights` · GET `/reset_face_weights` |
| 前端 UI | `templates/settings.html` — 三滑块 + 实时公式展示 + 动态文字说明 + 保存/重置按钮 |
| 算法消费 | `app/services/project_statistics.py` — `_load_face_weights()` 尝试从 ConfigManager 读取，回退 DEFAULT_FACE_WEIGHTS |

**配置键**: `P1=0.4` (前端面) · `P2=0.4` (后端面) · `ST=0.2` (静平衡面)

---
