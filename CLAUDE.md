<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **xiangxiantu** (1419 symbols, 3138 relationships, 99 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/xiangxiantu/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|--------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/xiangxiantu/context` | Codebase overview, check index freshness |
| `gitnexus://repo/xiangxiantu/clusters` | All functional areas |
| `gitnexus://repo/xiangxiantu/processes` | All execution flows |
| `gitnexus://repo/xiangxiantu/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

- Re-index: `npx gitnexus analyze`
- Check freshness: `npx gitnexus status`
- Generate docs: `npx gitnexus wiki`

<!-- gitnexus:end -->

---

# 项目上下文 — 扇叶平衡补土转速评估工具

> **最后更新**: 2026-08-20 | **项目规模**: ~120源文件 · ~38,000行 · Python + JS + HTML/CSS  
> **综合评级**: 🟢 良好+偏优 (算法90 · 视觉87 · 交互83 · 安全85 · 架构82 · 工程78 · 生产就绪82)

---

## 一、项目是什么

这是一个 Flask Web 应用，用于评估 **扇叶动平衡补土工艺中应该选择哪个转速进行平衡作业**。

> **业务场景**: 同一个风扇产品，在 800rpm / 1000rpm / 1200rpm 等多个转速下分别测试，每个转速测量多组数据（P1端面不平衡量、P2端面不平衡量、ST端面不平衡量）。系统通过统计学分析评估哪个转速的测量数据最稳定、最可靠，推荐该转速作为平衡作业转速。

**技术栈**: Flask 2.x + Pandas + NumPy + Scikit-learn + Matplotlib（服务端）+ Plotly.js 3.3.1（前端）

---

## 二、核心业务链路

```
数据上传→解析导入→project_statistics.py(最优转速评分)
  → data_analysis.py(深度分析: 趋势+异常+聚类)
  → skill_evaluation.py(综合评估: 数据质量+技能等级+推荐)
→ 报告导出(HTML/PDF/CSV/JSON/Excel) — services/report_* 三层架构
  → ReportRenderer 数据驱动渲染(封面/目录/评分明细表/页眉脚/版本v2.0)
  → 图表双轨兜底(静态PNG + Plotly交互, PDF天然静态图)
```

---

## 三、项目架构全景

### 3.1 启动方式

| 模式 | 命令 | 入口 |
|------|------|------|
| 开发 | `python wsgi.py` | wsgi.py → 0.0.0.0:1333 |
| 生产 | `gunicorn -w 4 -b 0.0.0.0:1333 wsgi:application` | wsgi.py → application callable |
| 备用 | `python -m app` | app/__init__.py 应用工厂 |

**只有一个入口文件**: `wsgi.py`。不要创建 `app.py`、`main.py`、`run.py` 等其他入口。

### 3.2 目录职责

```
/www/wwwroot/xiangxiantu/
│
├── wsgi.py                               ★ 唯一启动入口
├── config.py                              配置常量（UPLOAD_FOLDER/PORT/MAX_CONTENT_LENGTH等）
├── project_statistics.py                  最优转速评分（兼容shim，核心在 app/services/）
├── machine_learning.py                    机器学习/聚类/异常检测（根级，724行）
├── database_connections.py                数据库连接管理
├── report_export.py                       报告导出兼容转发层（无业务逻辑）
├── report_exporter_extension.py           报告导出扩展
├── report_export_css.py                   报告导出CSS外部化（EXPORTER_CSS）
├── chart_generation_optimized.py          图表生成（含缓存，10种图表）
├── chart_style_config.py                  图表样式配置
├── data_processing.py                     数据处理
├── db_models.py                           数据库模型
├── ml_data_adapter.py                     ML数据适配
├── gunicorn_conf.py                       Gunicorn 配置
│
├── services/                               ★ 报告导出核心服务（三层架构）
│   ├── report_exporter.py                 ReportExporter核心 + HtmlExporter（ShareLinkManager 已独立）
│   ├── report_renderer.py                 ★ ReportRenderer 数据驱动HTML报告渲染（第39轮新建）
│   ├── report_data_export.py              ReportDataExporter（CSV/JSON/Excel）
│   ├── report_constants.py                PLOTLY常量（CDN + 双轨脚本）
│   ├── share_link_manager.py              ★ ShareLinkManager 分享链接管理（第42轮拆分）
│   └── data_service.py                    数据服务
│
├── app/                                   Flask应用包
│   ├── __init__.py                        应用工厂（备用入口，非主入口）
│   ├── services/                          核心服务层
│   │   ├── project_statistics.py          ★ 最优转速评分算法（核心，998行）
│   │   ├── data_analysis.py               ★ 深度分析：趋势/异常/聚类/高级统计
│   │   ├── skill_evaluation.py            ★ 综合评估：编排+质量+评分+推荐
│   │   ├── statistics.py                  统计服务
│   │   ├── chart_generation.py            图表生成服务（弃用标注，指向根级 optimized）
│   │   ├── chart_plotly_renderer.py       Plotly 图表渲染
│   │   ├── chart_matplotlib_renderer.py   Matplotlib 图表渲染
│   │   ├── chart_cache.py                 图表缓存
│   │   ├── chart_utils.py / chart_fallback.py  图表工具/回退
│   │   ├── data_processing.py             数据处理服务
│   │   └── connection_manager.py / connection_tester.py  连接管理/测试
│   └── utils/                             工具模块
│       ├── crypto_utils.py                密码加密（Fernet/PBKDF2HMAC，解密兼容旧XOR格式）
│       ├── config_manager.py              配置管理（URL编码密码、原子写入）
│       ├── file_manager.py                文件操作
│       ├── error_handler.py               日志与错误处理
│       ├── data_validator.py              数据验证
│       ├── chart_resource_manager.py      图表资源管理
│       ├── cache_utils.py                 缓存工具
│       └── api_response.py                API统一响应类
│
├── blueprints/                            Flask蓝图路由（7个）
│   ├── main_bp.py                         首页/仪表盘/数据上传
│   ├── analysis_bp.py                     统一分析蓝图（深度分析+技能评估）
│   ├── report_bp.py                       报告查看/分享
│   ├── ml_bp.py                           机器学习预测
│   ├── outputs_bp.py                      输出管理
│   ├── settings_bp.py                     数据库连接配置页面
│   └── database_bp.py                     数据库连接管理API
│
├── templates/                             Jinja2模板（14个）
├── static/                                前端静态资源
│   ├── js/                                JavaScript（23个）
│   └── css/                               CSS样式（8个）
├── exporters/                             导出器（兼容）
├── models/                                数据模型
├── tests/                                 测试文件（18个）
├── utils/                                 app/utils/ 兼容层
└── outputs/                               输出目录
```

### 3.3 关键文件职责速查

| 我需要修改... | 应该看... |
|--------------|----------|
| 最优转速评分逻辑 | `app/services/project_statistics.py` |
| 趋势分析/异常检测/聚类 | `app/services/data_analysis.py` |
| 综合技能评估流程 | `app/services/skill_evaluation.py` |
| 图表生成 | `chart_generation_optimized.py` 或 `app/services/chart_generation.py` |
| API路由 | `blueprints/analysis_bp.py` |
| 数据库密码加密 | `app/utils/crypto_utils.py` |
| 配置文件管理 | `app/utils/config_manager.py` |
| 报告导出(HTML/PDF) | `services/report_exporter.py`（核心）或 `report_export.py`（兼容转发层） |
| 报告HTML渲染 | `services/report_renderer.py` |
| 报告数据导出(CSV/JSON/Excel) | `services/report_data_export.py` |
| 报告图表双轨/PLOTLY常量 | `report_export_css.py` + `services/report_constants.py` |
| 报告管理API | `blueprints/outputs_bp.py` |
| 报告管理页面 | `templates/outputs.html` + `static/js/outputs.js` |
| 前端深度分析交互 | `static/js/in_depth_analysis_enhanced.js` |
| 日志工具 | `app/utils/error_handler.py` |
| 数据验证 | `app/utils/data_validator.py` |
| 数据处理 | `data_processing.py` 或 `app/services/data_processing.py` |
| 数据库模型 | `db_models.py` 或 `models/` |
| 机器学习预测 | `machine_learning.py`（根级） |

---

## 四、核心算法深度说明（修改前必读）

### 4.1 最优转速评分 `project_statistics.py`

```
总分 = P1分×0.4 + P2分×0.4 + ST分×0.2
端面分 = IQR稳定性×0.4 + CV稳定性×0.4 + 幅值合理性×0.2
幅值因子 = 1/(1+|mean−median|/median)
```

- `DEFAULT_FACE_WEIGHTS`: 端面权重，可函数参数覆盖
- `FACE_INTERNAL_WEIGHTS`: 维度权重（iqr/cv/magnitude）
- `include_magnitude` 参数控制是否启用幅值维度

**CV 统一为百分比格式**: 全链路 `std/mean × 100`，不要再出现纯比值 0.05。

### 4.2 趋势分析 `data_analysis.py`

```
输入转速格式：'800rpm' / '800' / '转速800' / 800（纯数字）
    ↓ _extract_numeric_x() → 提取数值 [800, 1000, 1200]
    ↓ LinearRegression → 线性斜率、R²、方向
    ↓ _try_quadratic_fit() → PolynomialFeatures(degree=2)
        → 曲率类型（U型/倒U型/近似线性）
        → 顶点位置
        → ΔR²（非线性贡献）
```

**关键方法**:
- `_extract_numeric_x()` — 4种格式转速提取
- `_infer_x_unit()` — 自动推断单位（rpm）
- `_try_quadratic_fit()` — 二次多项式非线性检测
- `trend_analysis()` — 主入口，返回结构化的趋势结果

### 4.3 异常检测 `data_analysis.py`

```
n >= 8: D'Agostino-Pearson 正态性检验
    ├── 通过 → 标准 Z-score = (x-μ)/σ
    └── 不通过 → Modified Z-score = 0.6745×(x-median)/MAD
n < 8: 直接 Modified Z-score（小样本更稳健）

默认阈值: 2.5
```

**关键方法**: `_compute_z_scores()`, `anomaly_detection()`

### 4.4 聚类分析 `data_analysis.py`

- KMeans + `_elbow_method()` 曲率法自动选最优 K
- 遍历 K=1..min(8, n-1) 计算 inertia
- 对 inertia 曲线做曲率分析检测拐点
- `auto_k=True` 默认自动选择

### 4.5 综合技能评估 `skill_evaluation.py`

**数据质量**: 三维度评估（样本量 50% + CV合格率 30% + 异常比例 20%）

**质量加分**:  
- CV < 5% → +10% (`QUALITY_BONUS_EXCELLENT=0.10`)  
- CV < 10% → +5% (`QUALITY_BONUS_GOOD=0.05`)

**异常惩罚**: 异常数 ≥ 2 → -10% (`ANOMALY_PENALTY=0.10`)

**关键常量**（类级别）:
- `CV_EXCELLENT = 5.0`
- `CV_GOOD = 10.0`
- `ANOMALY_FILTER_Z_THRESHOLD = 2.5`
- `MIN_SAMPLES_PER_SPEED = 2`
- `MIN_SPEED_COUNT = 2`

### 4.6 报告导出体系（第39-42轮重构，修改前必读）

**三层架构**（根目录 `report_export.py` 仅为兼容转发层，无业务逻辑）:

| 层 | 文件 | 职责 |
|----|------|------|
| 核心 | `services/report_exporter.py` | `ReportExporter`（导出编排/历史/分享）+ `HtmlExporter`。`__init__(app=None, output_folder=None)` |
| 分享 | `services/share_link_manager.py` | `ShareLinkManager`（第42轮从 report_exporter.py 拆分）：create_link/revoke_link/get_link/list_links，`shareable_links.json` 持久化 |
| 渲染 | `services/report_renderer.py` | `ReportRenderer` 数据驱动渲染：`render(session_data, report_config=None)`。六章节（一分析摘要/二评分明细/三统计结果/四数据图表/五方法/六建议），`include_*` 开关**同时控制目录与正文** |
| 数据导出 | `services/report_data_export.py` | `ReportDataExporter`：CSV/JSON/Excel |
| 常量 | `services/report_constants.py` | `PLOTLY_CDN_URL` + `PLOTLY_DUAL_TRACK_SCRIPT`（图表双轨脚本） |

**图表双轨兜底**：报告内每个图表同时输出 `<img>` base64 静态图 + 隐藏的 `.chart-plotly-container` 交互容器。Plotly CDN 可用时 JS 渲染交互图并隐藏静态图；离线/异常保留静态图；`@media print` 强制静态图。PDF 经 weasyprint 不执行 JS，天然静态图。

**关键结构**（`ReportRenderer._build_context` 消费）:
- `session_data.evaluation_report`: `best_speeds`(list) / `best_score` / `speed_detailed_scores`(**Dict[转速str, Dict]**) / `all_min_iqr_speeds`(**Dict[面, 转速]**) / `all_min_cv_speeds` / `has_p1/has_p2/has_st`
- `session_data.plots`: `{p1|p2|sum: {chart_type: {png, chart_data}}}`（嵌套 dict，不是 surface_plots）
- `session_data.parsed_data`: **list** of `{speed, p1_samples, p2_samples, sum_samples}`
- 已删除接口（勿引用）：`build_report_html`/`_build_charts`/`add_to_queue`/`create_export_task`/`batch_export`/`generate_chart_cache_key` 等图表缓存/任务队列系列

---

## 五、安全注意事项

| 措施 | 实现位置 | 注意 |
|------|---------|------|
| CSRF | Flask-WTF 全局 | wsgi.py 中 `CSRFProtect(app)` |
| 密码加密 | `app/utils/crypto_utils.py` | Fernet(PBKDF2HMAC+SHA256)，可逆加密 |
| 加密盐值 | `app/utils/crypto_utils.py` | 环境变量CRYPTO_SALT + 内置回退（第12轮强化） |
| SECRET_KEY | wsgi.py 中持久化到文件 | 权限600，多worker共享 |
| 生产异常脱敏 | `wsgi.py` → `handle_generic_exception` | error_type仅debug模式返回（第12轮修复） |
| 文件上传校验 | `data_processing.py` → `validate_magic_bytes()` | Magic bytes头验证防扩展名伪造（第12轮新增） |
| 原子写入 | `database_connections.py` | temp+fsync+os.replace |
| LRU缓存 | `database_connections.py` | 100条上限，逐出close连接 |
| 超时保护 | `database_connections.py` | Thread+join(timeout=10)，跨平台 |
| URL编码 | `app/utils/config_manager.py` | quote_plus() 编码密码 |

**绝对不要**: 提交密钥/密码到仓库；配置文件密码必须加密存储。

---

## 六、代码约定（必须遵守）

- **语言**: Python 3.8+，中文注释
- **风格**: PEP 8，4空格缩进
- **命名**: 函数/变量 snake_case，类 PascalCase
- **导入顺序**: 标准库 → 第三方 → 本地模块，绝对导入
- **类型标注**: 关键模块 `from typing import Dict, List, Optional, Tuple, Any`
- **日志**: 使用 `app.utils.error_handler` 中的 logger，不用 `print()`
- **无注释规则**: 不要无故添加注释，代码应自解释
- **Flask约定**: 蓝图在 `wsgi.py` 中注册，配置通过 `config.py` 统一管理
- **响应格式**: `{"success": bool, "message": str, "data": ...}`

---

## 七、三省六部全量审查结论（2026-08-20 更新）

### 7.1 总体评级：🟢 良好+偏优

| 维度 | 评分 | 说明 |
|------|:----:|------|
| 算法科学性 | 90 | 趋势/异常/聚类/评分全链路稳定 + 报告摘要幅值维度补齐 |
| 视觉一致性 | 87 | 三套CSS统一设计令牌 + 报告体系六维重构（封面/目录/评分明细表/页眉脚） |
| 交互安全性 | 83 | XSS/CSRF修复, safeFetch统一, alert→toast, console.log清理 |
| 安全性 | 85 | CSRF+密码加密+盐值外置+异常脱敏+Magic bytes校验 |
| 代码架构 | 82 | 报告导出三层架构（exporter/renderer/data_export），死代码清除 |
| 工程规范 | 78 | ApiResponse统一响应+Type hints；待lint/format |
| 生产就绪度 | 82 | Gunicorn多worker+健康检查+异常脱敏+PDF静态图继承 |

### 7.2 六部关键发现（2026-05-12 最新审查：第9-19轮合并）

**兵部（安全，第12轮已完成 3 P0 + 2 P1）**:
- ✅ `handle_generic_exception` 异常脱敏：`error_type` 仅debug模式返回，生产环境不泄露内部类名
- ✅ crypto salt环境变量化：`CRYPTO_SALT` 环境变量 + 内置回退，安全增强
- ✅ Magic bytes文件校验：`validate_magic_bytes()` 防扩展名伪造上传
- ✅ 死码shim蓝图删除：`in_depth_analysis_bp.py` / `skill_evaluation_bp.py` 仅2行转发从未注册，删除
- ✅ `import *` → 显式导入：`project_statistics.py` 消除命名空间污染

**工部（架构/工程，第12轮已完成 3 P0 + 3 P1）**:
- ✅ ReportExporter CSS外部化：`report_export.py` 中 `_html_exporter_css()` 85行CSS → `report_export_css.py` 独立模块
- ✅ ApiResponse统一响应类：新建 `app/utils/api_response.py`，success()/error()/ok()静态方法
- ✅ chart_generation弃用标注：`app/services/chart_generation.py` 模块docstring指向 `chart_generation_optimized.py`
- ✅ `_diag_render.py` 直接导入 `app.services.project_statistics`（不使用shim）
- ✅ `blueprints/__init__.py` 清除shim引用，直连analysis_bp
- ✅ `config.py` SECRET_KEY文档强化

**兵部（安全/交互，第11轮已完成 5 P0）**:
- ✅ 文件名XSS修复：`innerHTML` → `textContent`（upload.js:35）
- ✅ CSRF令牌路径统一：废弃 `meta[name="csrf-token"]`，统一 `input[name="csrf_token"]`（skill_evaluation.html）
- ✅ safeFetch四地重复→独立JS模块：outputs/index/report/dashboard统一引用 `safe-fetch.js`
- ✅ 拖放样式色值对齐设计令牌（upload.js:51）

**刑部（错误处理，第11轮已完成 3 P0）**:
- ✅ alert()→Toast替换：outputs.js两处alert()改为Bootstrap toast，不再阻断操作
- ✅ upload.js格式校验alert→内联红色文字提示
- ✅ modal-manager.js 16条console.log调试残留清理，保留6处错误日志

**工部（架构/工程，第11轮已完成 1 P0 + 2 P1）**:
- ✅ 新建统一Toast通知系统（`toast-helper.js`）：slide-in动画、4种类型、自动消失
- ✅ err.message拼接innerHTML时escape（outputs.js + modal-manager.js + in_depth_analysis_enhanced.js）
- ✅ 硬编码red→var(--danger-color)（modal-manager.js）

**礼部（外观/UI，第10轮已完成 5 P0 + 4 P1）**:
- ✅ `:root` 设计令牌扩展（--primary-rgb, --font-stack, --radius-*, Bootstrap变量）
- ✅ 三套CSS系统统一：outputs.html→outputs.css, navbar→style.css, exporter字体对齐
- ✅ `--rp-*` 命名空间消除，全页面统一 :root 令牌
- ✅ 旧颜色值替换：rgba(52,152,219)/#0d6efd/#1f77b4→设计令牌
- ✅ outputs.html ~426行 + navbar.html ~100行内嵌Style全外部化，0残留

**刑部（已完成 5 P0）**:
- ✅ `sync_outputs_from_filesystem` 递归扫描适配型号子目录
- ✅ `delete_output_file` 先commit再删文件，消灭幽灵记录
- ✅ `_detect_fan_model_from_path` 区分 RuntimeError vs 正常未匹配
- ✅ `_list_filesystem_files` 删除未使用的 output_folder 形参
- ✅ `output_files_by_model` file_path为空时仍尝试filename匹配

**工部（已完成 3 P0 + 1 P1）**:
- ✅ `ReportExporter` 流式HTML CSS对齐设计令牌 `#007bff→#2563eb`
- ✅ `view_chart_html` 支持型号子目录路径
- ✅ 两套HTML生成路径(thead/section-title/header) CSS已全部对齐
- ~~⚠️ `project_statistics.py` 根目录游离~~ ✅ 第十二轮确认：实际代码已在 `app/services/project_statistics.py`(998行)

**兵部（安全）**:
- ✅ `print()` → `logger.error()` 全局替换
- ✅ `config.py` 密钥冲突已标记为需后续处理
- ~~⚠️ `handle_generic_exception` 中 `error_type` 泄露~~ ✅ 第十二轮修复：仅debug模式返回

**户部（已完成 1 P1）**:
- ✅ `_detect_fan_model_from_path` IO优化：`_load_export_history`一次读，循环内复用缓存

**吏部（架构）**:
- ⚠️ `database_connections.py` 单体过大（模型+管理器+测试器），应拆分

**工部（工程）**:
- ~~⚠️ `html_exporter.py` 内嵌70行CSS字符串~~ ✅ 第十二轮已创建 `report_export_css.py`，Python端+Web端CSS全外部化
- ⚠️ 缺少 `ruff`/`black`/`mypy` 自动化检查

### 7.3 锦衣卫监察：修复验证

| 修复批次 | 数量 | 确认状态 |
|---------|:----:|:--------:|
| 数据库密码加密（第五轮） | 7项 | ✅ 全部有效 |
| 算法科学修复（第七轮） | 10项 | ✅ 全部有效 |
| 报告管理中心升级（第八轮） | 6项 | ✅ 全部有效 |
| 三省六部审查优化（第九轮） | 9项 | ✅ 全部有效 |
| UI/视觉设计统一（第十轮） | 9项 | ✅ 全部有效 |
| 交互性优化（第十一轮） | 11项 | ✅ 全部有效 |
| 全项目综合审查（第十二轮） | 11项 | ✅ 全部有效 |
| 导出报告非box图表修复（第十三轮） | 6项 | ✅ 全部有效 |
| 全模块排版统一宽屏适配（第十四轮） | 4项 | ✅ 全部有效 |
| 报告管理预览功能全链路修复（第十五轮） | 6项 | ✅ 全部有效 |
| 报告管理UI可访问性与CSRF修复（第十六轮） | 9项 | ✅ 全部有效 |
| 数据库删除失败 + 全面审查优化（第十七轮） | 15项 | ✅ 全部有效 |
| Hero按钮可见性 + 版面宽度统一（第十八轮） | 4项 | ✅ 全部有效 |
| 报告管理页面UI全面重设计（第十九轮） | 8项 | ✅ 全部有效 |
| Hero副标题可见性修复（第二十轮） | 1项 | ✅ 全部有效 |
| 预览功能失效 + 表头字体颜色回归（第二十二轮） | 2项 | ✅ 全部有效 |
| Hero标题不可见根因修复 + 对比度全面提升（第二十三轮） | 3项 | ✅ 全部有效 |
| 预览功能全链路修复（第二十四轮） | 6项 | ✅ 全部有效 |
| 预览布局全面修复（第二十五轮） | 5项 | ✅ 全部有效 |
| 型号追踪管理体系全面建立（第二十七轮） | 9项 | ✅ 全部有效 |
| 第二十八轮：安全加固+质量基线 | 9项 | ✅ 全部有效 |
| 第二十九轮：工程健壮性提升 | 6项 | ✅ 全部有效 |
| 第三十轮：工程健壮性续+TRAE文档同步 | 6项 | ✅ 全部有效 |
| 第三十一轮：导出文件中文命名 | 3项 | ✅ 全部有效 |
| 第三十七轮：ML页面数据兼容性修复 | 3项 | ✅ 全部有效 |
| 第三十八轮：ML页面结构性重构+合并重复实现 | 6项 | ✅ 全部有效 |
| 第三十九轮：报告体系六维重构 + 图表双轨兜底 | 12项 | ✅ 全部有效 |
| 第四十轮：技术债务清理 | 5项 | ✅ 全部有效 |
| 第四十一轮：接口漂移测试全量修复 | 14项 | ✅ 全部有效 |
| 第四十二轮：ShareLinkManager拆分 + 测试基线清零 | 3项 | ✅ 全部有效 |
| **合计** | **222项** | **100%** |

### 7.4 待改进项优先级

**立即（无阻断性问题）**

**本月**:
1. ~~迁移 `project_statistics.py` → `app/services/`~~ ✅ 第十二轮已确认已就位
2. ~~拆分 `database_connections.py`~~ ✅ 已完成：42行兼容shim，逻辑在 `app/models/db_connection_config.py` + `app/services/connection_manager.py` + `connection_tester.py`
3. ~~添加 `ApiResponse` 类~~ ✅ 第十二轮已创建
4. ~~生产环境异常信息脱敏~~ ✅ 第十二轮已修复
5. ~~`services/report_exporter.py` 400 行压线~~ ✅ 第四十二轮已拆分：ShareLinkManager → `services/share_link_manager.py`，有效代码 400→329 行
6. ~~修复 `test_data_processing.py`(1) + `test_data_validator.py`(2) 既有失败~~ ✅ 第四十二轮已清零：空文件检测抛 ValueError（两副本）+ 测试对齐当前 API；全量 64 passed

**下月**:
7. python-dotenv 集成
8. ruff+black+mypy
9. flask-limiter
10. ~~`_html_exporter_css()` Python内嵌CSS外部化~~ ✅ 第十二轮已完成（web端+Python端全部外部化）

---

## 八、数据格式约定

技能评估输入格式：

```json
{
  "data": [
    {
      "speed": "800rpm",
      "p1_samples": [1.1, 1.5, 1.3, 1.4, 1.6],
      "p2_samples": [2.1, 2.5, 2.3, 2.4, 2.6],
      "st_samples": [3.2, 4.0, 3.6, 3.8, 4.2]
    },
    {
      "speed": "1000rpm",
      "p1_samples": [1.0, 1.2, 1.4, 1.1, 1.3],
      "p2_samples": [2.3, 2.1, 2.7, 2.2, 2.4],
      "st_samples": [3.5, 3.8, 4.1, 3.9, 3.7]
    }
  ]
}
```

> - 转速值支持 4 种格式: `800rpm` / `800` / `转速800` / 纯数字
> - 每转速至少 2 个样本 (`MIN_SAMPLES_PER_SPEED=2`)
> - 至少 2 个不同转速 (`MIN_SPEED_COUNT=2`)
> - 端面字段名兼容 P1/P2/ST（大小写均可）

---

## 九、测试与验证

```bash
# 运行所有测试
python -m pytest tests/

# 快速语法验证（单个文件）
python -c "import ast; ast.parse(open('path/to/file.py').read()); print('OK')"

# 导入测试
python -c "import ast; compile(open('path/to/file.py').read(), 'file.py', 'exec'); print('OK')"

# 启动开发服务器
python wsgi.py
```

---

## 十、部署快速参考

| 变量 | 默认值 |
|------|--------|
| `PORT` | 1333 |
| `DEBUG` | false |
| `UPLOAD_FOLDER` | uploads |
| `MAX_CONTENT_LENGTH` | 16777216 (16MB) |

```bash
# 开发
python wsgi.py

# 生产
gunicorn -w 4 -b 0.0.0.0:1333 wsgi:application
```

---

## 十一、配套文档索引

| 文件 | 用途 |
|------|------|
| `README.md` | 项目介绍 / API文档 / 部署指南 |
| `REPAIR_REPORT.md` | 全部 ~57 项修复详情（7轮） |
| `OPTIMIZATION_SUMMARY.md` | 算法优化 / 安全优化 / 性能优化详情 |
| `AGENTS.md` | AI Agent 通用指南（GitNexus规则+项目速览） |
