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

# 项目状态 (2026-08-20) ⭐ 最新

## 项目定位

扇叶动平衡补土工艺决策支持系统。采集同一产品在多个转速下各端面（P1/P2/ST）的不平衡量测试数据，通过统计学分析和算法模型，推荐最适合进行平衡作业的转速。

## 三省六部全量评估 (2026-05-14)

七路并行 Agent 调研全项目源码层，覆盖架构/质量/数据流/UI/交互/安全/算法七大维度，发现 23 项问题。

| 部门 | 维度 | 评分 | 问题数 |
|------|------|------|--------|
| 中书省 | 架构设计 | 6.5 | 4 |
| 吏部 | 代码质量 | 7.0 | 3 |
| 户部 | 数据流 | 6.5 | 3 |
| 礼部 | UI/UX | 7.5 | 5 |
| 兵部 | 交互性 | 7.5 | 2 |
| 刑部 | 安全 | 5.0 ⚠️ | 5 |
| 工部 | 算法 | 7.0 | 1 |
| **加权** | **综合** | **6.67** | **23** |

### 关键发现

| 优先级 | 发现 | 说明 |
|--------|------|------|
| P0 | modal-manager.js XSS | L178 `error.message`→`innerHTML` 未转义，可执行恶意脚本 |
| P1 | 134 处 console.log | 12 个 JS 文件生产环境调试残留 |
| P1 | 2 文件 print() 替代 logging | chart_generation.py + data_processing.py |
| P1 | 13 处硬编码颜色 | style.css 中 `#3498db`(6)/`#e0e0e0`/`#eee`/`#dee2e6` 脱离设计令牌 |
| P1 | 3 项安全加固 | Magic bytes/CSRF强制/日志脱敏 |
| P2 | 14 项工程健壮性 | 暗色模式/表格响应式/bcrypt/Type hints等 |

### 误报确认
- ❌ 刑部路径穿越告警 → 已确认 outputs_bp.py 有 `os.path.normpath` + `startswith("..")` 防护，**状态安全**

### 迭代计划
- **第二十八轮**：P0+P1 安全加固+质量基线（9项）
- **第二十九轮**：P2 工程健壮性（6项）
- **第三十轮**：P2 工程健壮性续 + TRAE文档同步（6项）
- **第三十一轮**：导出文件中文命名（3项）

## 最近重大变更

### 第四十二轮修复：ShareLinkManager 拆分 + 测试基线清零（2026-08-20）

执行 P0 技术债：拆分 400 行压线的 `report_exporter.py`，并将 3 个既有失败测试用例清零（全量 64 passed）：

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | ShareLinkManager 独立 | `services/share_link_manager.py`（新建） | `report_exporter.py` 有效代码 400 行压线（100%）→ 拆分后 329 行（82%）；share link 5 方法（create/revoke/get/list + 读写）整体迁移，`report_exporter.py` 改导入，根级转发层零改动 |
| P0 | 空文件检测 ValueError | `data_processing.py` + `app/services/data_processing.py` | 空 CSV 原走编码循环抛 `Exception("无法识别编码")`，与 `parse_single_surface_file` 契约不符（期望 `ValueError`）；`getsize()==0` 提前抛 `ValueError("文件内容为空")`，两副本同步 |
| P1 | 测试对齐当前 API | `tests/test_data_validator.py` | 2 用例过时：`validate_and_align_data` 断言旧"填充30点"→ 当前截断到 `min_length`；`generate_data_warning` 用旧 data_info 键（p1_valid/is_complete）→ 当前 `aligned_length/p1_has_nan` 结构，补 NaN 过滤/警告分支断言 |

**结果**：全量 `pytest tests/` **64 passed**（此前 3 个既有失败：`test_parse_single_surface_file_empty` + `test_data_validator`×2 全部清零），7 warnings 均为既有 sklearn R² 与 pytest return 提示，与本次无关。

### 第四十三轮修复：报告与前端三差异对齐（评分明细/表格样式/图表布局）（2026-08-20）

用户对比浏览器前端与分析报告，指出 3 项差异并确认业务逻辑（"评分明细只展示有数据的面 + 0 分计入总分"）。全链路修复：

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | 报告 has_* 死逻辑修复 | `services/report_renderer.py` | `_build_context` 原用 `bool(evaluation.get("has_p*")) or any(k.startswith("P*") for k in scores)`——scores 键是转速而非面，`startswith` 恒为 False 的死判定；新增 `_has_face_scores()` 以 face_score 是否非 None 判定面是否有数据，has_* 键仅作兼容兜底 |
| P0 | 评分明细只展示有数据的面 | `services/report_renderer.py` | `face_labels` 动态列（仅 has 的面），`_render_scores` 表头与单元格均按 face_labels 渲染，无数据面不显示列 |
| P0 | 前端评分表动态列 | `templates/index.html` | 表头与单元格改用 `{% if evaluation_report.has_p1 %}` 等条件包裹，与报告"只展示有数据的面"对齐；0 分计入总分逻辑在算法层（`calculate_face_score` 缺键返回 0.0 加权）保持不变 |
| P1 | 报告表格样式对齐前端 | `report_export_css.py` | EXPORTER_CSS 补 Bootstrap 兼容类（`.table`/`.table-striped`/`.table-success` 等）+ `.table-statistics` 系列面配色（对齐前端 style.css L732-773），stats_html 在报告中视觉与前端一致 |
| P1 | 报告图表布局对齐前端 | `services/report_renderer.py` | 并列布局"面为列"（chart-row > chart-col，`.chart-col{flex:1;min-width:300px}`）；修复 `_SURFACE_NAMES`（sum→ST面/single→单面）+ `_resolve_surface_name` 处理单面场景 |
| P1 | 新增面列测试 | `tests/test_report_renderer_faces.py`（新建） | 2 用例：`test_scores_only_available_faces`（P1-only 报告评分明细仅 P1 列）+ `test_scores_face_scores_fallback_without_has_keys`（无 has_* 键时以 face_score 兜底）；定位用 `html.split('id="sec-scores"')[1]`（勿用章节名分割——TOC 重复出现） |
| P1 | 图表缓存跨目录失效修复 | `app/utils/chart_resource_manager.py` + `chart_generation_optimized.py` | 差异3验证发现真实 bug：`chart_id` 仅由数据 hash 派生，缓存命中复用首次生成的完整路径——不同型号/输出目录分析相同数据时，二次报告按 basename 拼当前目录找不到图（"暂无预览"）。修复：① `generate_chart_id` 增加 scope 参数（model_output_dir 短哈希入 id，不同目录不同 id）；② `is_chart_generated` 增加 `os.path.exists(png_path)` 校验，缓存路径失效视为未生成并重建 |

**结果**：全量 `pytest tests/` **66 passed**（64 + 2 新增）；P1-only 真实链路端到端验证通过——算法层 `has_p2=False`/`has_st=False`、total=0.4×P1 得分（0 分计入总分），前端评分明细仅 P1 列，导出报告评分明细仅 `<th class="face">P1面</th>` 列。另确认此前"Jinja 渲染与磁盘模板不符"为验证脚本假警报（`plots={}` 空 dict 导致模板 L200 `{% if plots %}` 分析结果区域整体不渲染），非模板缓存问题。

差异2/3 验证：三面完整数据（P1+P2+ST）生成报告，EXPORTER_CSS 14 项 Bootstrap/table-statistics 类全部命中，stats_html 三面表格完整渲染；parallel 布局 `.chart-row > .chart-col` 三面三列、stacked 布局 `.chart-group` 三面堆叠，两布局报告均嵌入 base64 图表；跨型号同数据（MODEL-A/B）两份报告均含图（缓存修复验证通过）。

### 第四十四轮修复：报告导出链路 + 重置 CSRF 全链路收尾（2026-08-20）

用户端到端验收（上传→分析→导出→重置）发现 4 项真实缺陷，全部修复并经真实链路验证（17:39 导出 `outputs/9324/9324_动平衡分析报告_20260820_173912.html` 含全部修复，66 测试全通过）：

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | face_labels 匹配恒 False | `services/report_renderer.py` | 评分明细数据行用 face 键 `"P1"` 与 `face_labels` 存的标签 `"P1面"` 做 `in` 判断恒 False → P2/综合得分列永远无数据；改为 `label in face_labels` 按标签匹配 |
| P0 | 箱线图缺中位数折线 | `services/report_constants.py` | `PLOTLY_DUAL_TRACK_SCRIPT` 双轨交互图 box 分支只画箱体，替换掉含折线的静态 PNG（与前端不一致）；叠加中位数 scatter 虚线（对齐 `plotly-chart-builders.js`），`len>1` 时渲染 |
| P0 | 导出文件写入不可见位置 | `blueprints/report_bp.py` | gunicorn CWD 异常 + `_init_report_exporter` 内 `hasattr(exporter,"output_folder")` 因构造时已设相对路径恒 False → `init_app` 永不执行，绝对路径不生效，报告"消失"；强制 `exporter.init_app(app)` + `load_export_history()` |
| P0 | 重置后 CSRF 失效 400 | `blueprints/main_bp.py` + `wsgi.py` | 双根因：① `/reset` 的 `session.clear()` 删除 `csrf_token`，Flask-WTF 下次渲染生成新 token，浏览器（bfcache/缓存）仍持旧 token → 上传必 400；修复为 clear 前保存、clear 后恢复 token 不轮换；② 动态页面无缓存头导致旧 token 页面被缓存 → `after_request` 对非 `/static/` 响应加 `Cache-Control: no-store, no-cache, must-revalidate` + `Pragma: no-cache` + `Expires: 0` |

**结果**：全量 `pytest tests/` **66 passed**；curl 实测动态页返回 no-store 头；test_client 验证重置前后 token 一致（`T1==T3`）、重置后用旧 token 提交 302 成功；17:39 真实导出报告 `P1面`×6 + `P2面`×6 + `综合得分`×4 三列齐全、`中位线` 出现、`chart-row/flex-wrap` 并列布局命中。控制台 "loaded over an insecure connection" 为 HTTP 访问时 Chrome 例行提示，非错误（部署 HTTPS 可消除）。

### 第四十五轮修复：导出报告全维度审查整改（2026-08-20）

三省六部全链路评审导出功能（report_bp → report_exporter → report_renderer / report_data_export / share_link_manager + 前端入口），裁决 1 🔴 + 8 🟡 全部落地，新增 7 个测试用例，全量 **73 passed**：

| 修复项 | 文件 | 说明 |
|--------|------|------|
| CSV 空统计导出必失败 | `services/report_data_export.py` + `blueprints/report_bp.py` | 无统计数据时原返回不存在的文件路径 → send_file 404、提示缺失；现抛 `ValueError("暂无统计数据...")`，路由层精确 flash |
| 型号 ".." 目录穿越拦截 | `utils/model_utils.py` + `blueprints/main_bp.py` | `sanitize_model_name` 拦截 "."/".."/点开头 → "未分类"（`os.path.join(outputs,"..")` 会把报告写进父目录）；main_bp 校验层双保险 |
| 删除死方法 | `services/report_exporter.py` | `_clean_base64_cache` 零调用 + 淘汰语义错误（用文件 mtime 当缓存时间戳），直接删除 |
| PDF 路径 + 配置透传 | `services/report_exporter.py` | PDF 原写 `outputs/` 根目录（与 history 的 model_dir 漂移）→ 对齐写入型号子目录；并修复 PDF 分支 `report_config` 不生效 bug（此前 `export_report_from_session` 不透传配置） |
| 原子写 | `services/report_exporter.py` + `services/share_link_manager.py` | 导出历史 `export_history.json` 与分享链接 `shareable_links.json` 改 temp + `os.replace`，防多 worker 并发写坏 |
| 导出 GET → POST | `blueprints/report_bp.py` + `static/js/export-manager.js`(新建) + 4 模板 + `guide.js` + `wsgi.py` | 导出是写文件副作用，改 POST-only（全局 CSRF 生效）；前端统一 fetch POST + blob 下载（CSRF token 经 navbar 宏全局注入）；wsgi 通用异常处理器放行 werkzeug HTTPException（405 不再被吞成 500）；guide 引导选择器同步 |
| 死参数收敛 | `blueprints/report_bp.py` + `templates/report.html` | 删除 `include_raw_data`（零消费）、`report_settings` 死数据、`_check_export_format` 的 `method` 键、report.html "包含原始数据" 无效 checkbox |
| 性能 + 日志 | `services/report_exporter.py` + `services/share_link_manager.py` | `export()` 对 csv/json/excel 跳过整树 `_sanitize_session_data` 深拷贝（三格式仅消费标量，无 HTML 渲染面）；logging f-string 改 `%s` 惰性求值 |

**结果**：`pytest tests/` **73 passed**（新增 `tests/test_export_route.py` 4 用例：GET 405 / POST+CSRF 200 / CSV 空数据 302+提示 / 无 token 400；`test_report_exporter.py` 新增 3 用例：CSV 空抛 ValueError / sanitize 拦截 ".." / PDF report_config 透传）。全部文件 `py_compile` SYNTAX_OK。

### 第四十六轮修复：默认Y轴对齐（2026-08-20）

用户要求"默认Y轴对齐"（首页 + 导出报告都默认对齐），覆盖 3 个文件 + 1 项现状确认：

| 修复项 | 文件 | 说明 |
|--------|------|------|
| 首页图表加载后自动对齐 | `static/js/chart-yaxis-align.js` | 新增 `autoAlignOnce()`：DOM 加载后轮询图表就绪（≤10s），自动执行 align + 按钮置"Y轴已对齐"；timer 防重复轮询 |
| 首页重绘后保持对齐 | `templates/_charts_partial.html` | reinitPlotlyCharts 末段由"重绘后 reset"改为：已对齐 → `realignIfAuto()` 重新对齐；未对齐 → `autoAlignOnce()` |
| 报告双轨交互图统一量程 | `services/report_constants.py` | `PLOTLY_DUAL_TRACK_SCRIPT` renderAll 两遍渲染：第一遍收集 box/violin/trend/scatter/bubble/histogram 全部 Y 值 → 全局 range（±5% padding）+ niceDtick；第二遍对可对齐类型注入 `layout.yaxis = {range, dtick}`（3d/parallel/heatmap 跳过） |
| 现状确认（无需改动） | `chart_generation_optimized.py` L121-128 | 报告静态 PNG 生成时已按 P1/P2/ST 全局 y_range 跨面对齐 |

**结果**：`node --check` JS 语法 OK；14 项相关测试全通过（0 失败）；真实导出报告 SMOKE_PASS（含 ALIGNABLE_TYPES / yaxis range / niceDtick / 中位线 / 静态图兜底）。

### 第四十七轮修复：堆叠显示图表右侧空白（2026-08-20）

用户反馈"堆叠显示的时候图表右边有空白"。浏览器实测确认根因：**不是容器宽度问题**（容器已 100% 占满），而是 Plotly 图内部空白——box 图默认右 margin 50px + 类别轴 autoexpand 扩展，右侧纯空白约 152px（占容器 16.8%），左侧被 y 轴刻度占据，视觉明显右偏空。

| 修复项 | 文件 | 说明 |
|--------|------|------|
| 首页 box/violin 收紧类别轴 + 收小右 margin | `static/js/simple-plotly-manager.js` | `initChart` 中按 trace 收集唯一类别 → `xaxis.type='category'` + `range=[-0.5, n-0.5]` 贴合末类，`margin.r=10` |
| 报告双轨交互图同步 | `services/report_constants.py` | renderAll 第一遍收集 box/violin 类别（`alignCats`），第二遍注入 xaxis range + margin.r=10，与前端一致 |

**验证**：browser_use 真实渲染实测——修复后两个箱线图右侧空白均为 11px ≈ **1.22%**（修复前 16.8%），达标（目标 1-2%）；`node --check` / `py_compile` OK；8 项相关测试全通过。

### 第五十七轮修复：报告页有效性/科学性全链路整改（2026-08-20）

评审报告页「有效性、科学性、链路用途」后修复：导出表单选项 6 项全失效（request.args 读取 POST body）、死开关、死选项，并打通报告页与 FS 资产闭环、IQR 评分无量纲化。全量 **90 passed**（86 + 4 新回归）：

| 修复项 | 文件 | 说明 |
|--------|------|------|
| P0-1 表单选项失效根因 | `blueprints/report_bp.py` | `include_charts/include_stats/include_evaluation/include_recommendations/report_title/export_format` 用 `request.args`（仅查询串）读取，表单 POST body 提交恒取默认值 → 统一改 `request.values` |
| P0-2 死开关接线 | `services/report_renderer.py` | `include_evaluation` 原来读取后从未入 report_config 且 renderer 无消费 → 接线为「评分明细章节」门控（`include_scores` 兼容旧名）；`include_recommendations` 原来 config 有但 renderer 恒显示 → 接线为「建议章节」门控 |
| export_format 死选项实现 | `report_export_css.py` + `report_renderer.py` | standard/compact/detailed 原仅校验不实现 → body 类 `report-compact/report-detailed` + CSS 字号/间距微调，样式选择真正生效 |
| report_title 死选项接线 | `report_renderer.py` | 封面 h1 与 `<title>` 原硬编码 → 使用 config.title |
| P1-2 报告页 FS 闭环 | `blueprints/report_bp.py` + `templates/report.html` | `/report` 展示最近导出的报告（export_history 前 8 条：型号/格式/时间/下载），不再与已导出资产脱节 |
| 科学性 IQR 无量纲化 | `app/services/project_statistics.py` | `iqr_score = 1/(1+iqr)` 有量纲（g·mm），量级大的面上 IQR 得分恒趋近 0 稀释 40% IQR 权重 → 按面内全部转速「中位 IQR」归一化 `1/(1+iqr/med)`；中位=0 防除零回退；三维评分（calculate_face_score）与单面路径两处同步；报告方法文案补充归一化说明 |
| 回归测试 | `tests/test_export_route.py` + `tests/test_statistics.py` | 新增表单 body 选项生效用例（标题/样式/4 开关全断言）；新增 IQR 归一化 3 用例（归一化得分恢复判别力、中位=0 防除零、端到端冒烟） |

**结果**：全部表单选项经冒烟验证真实生效；90 项测试全过。

### 第五十五轮修复：深入分析除零500 + 前端 progressFill 作用域（2026-08-20）

深入分析页报「评估失败 + ReferenceError: progressFill is not defined」两连错，全链路定位并修复：

| 修复项 | 文件 | 说明 |
|--------|------|------|
| 后端除零 500 根因 | `app/services/data_analysis.py` `_compute_z_scores` | 某面（st/p2）无数据时 `_compute_z_scores` 收到空数组/单元素，`np.std(data, ddof=1)` 在 n<=1 时 numpy 内部 Python 除法路径抛 ZeroDivisionError → 深入分析 500「异常检测失败：division by zero」（首页 p1/p2 分析无 st 面必触发）。修复：n==0 提前返回「无数据」；sigma 计算 `float(np.std(...)) if n > 1 else 0.0` 走「无变异性」分支 |
| 前端 progressFill 作用域 | `static/js/in_depth_analysis_enhanced.js` `setupFormSubmit` | `progressFill/progressInterval/progressDiv/progressPercent/requestPhase` 原声明在 try 块内（块级作用域），catch 块引用抛 ReferenceError；全部提升到 submit handler 函数体顶部 |
| 错误透出 | `blueprints/analysis_bp.py` 深入分析端点 | 笼统消息「深入分析失败，请稍后重试」→ 与技能评估端点一致透出真实错误 `{str(e)}`，避免黑盒 |
| 回归测试 | `tests/test_skill_evaluation_regression.py`（新增 3 用例） | st 空 / 仅 p1 / 缺 sum_samples 键三种退化面数据不再抛异常 |

**结果**：复现脚本（真实格式数据 + 无 st 面）原 4 场景 FAIL → 修复后全部 OK；全量 pytest **84 passed**（81 + 3 新回归）；JS 语法校验通过。

### 第五十四轮修复：全项目冗余/功能重叠全链路评审整改（J1-J4 四方案落地）（2026-08-20）

用户要求全链路评审全项目冗余功能与功能重叠，输出 J1-J4 四方案并全部批准实施。四域（前端JS/图表链路/蓝图路由/服务工具层）排查 + 全链路依赖校验后落地，全量 **81 passed**：

| 方案 | 修复项 | 文件 | 说明 |
|------|--------|------|------|
| J1 | 死代码清理（7 组 0 引用） | `static/js/app.js`、`static/js/components/ChartComponent.vue`、`static/js/types/index.js.map`、`exporters/` 整包、顶层 `project_statistics.py`、`app/services/statistics.py`、`ml_data_adapter.py` | 全部 0 引用（含 `from app.services.statistics` 无消费方）；同步清理 `app/services/__init__.py` 假存活重导出 |
| J2 | #resetButton 双绑定解除 | `static/js/reset-manager.js` | 同按钮被 page-initializer.js（服务端 /reset+刷新）与 reset-manager.js（客户端清表单+formReset）双绑定，一次点击两 confirm+互斥操作；reset-manager 排除该按钮，服务端逻辑独占 |
| J2 | toast 全局签名统一 `(type,message)` | `static/js/toast-helper.js` + `static/js/outputs.js` | 原 toast-helper 用 `(message,type)`，与 settings/skill_evaluation/in_depth_analysis 的 `(type,message)` 分叉，同页加载会覆盖导致参数错乱；统一为项目主流签名（4 处调用同步改） |
| J2 | page-initializer 死函数清理 | `static/js/page-initializer.js` | 删除定义未调用的 `initChartLazyLoading`（第 4 份图表初始化副本） |
| J3 | 图表初始化双重触发修复 | `static/js/match-result.js`（删除）+ `templates/match_result.html` | 该文件全文仅重复调用 `initAllChartFeatures`（charts.js DOMContentLoaded 已执行），导致每次页面加载初始化两次；删除冗余文件+移除模板引用 |
| J4-1 | outputs_bp DB 分支可达性修复 | `blueprints/outputs_bp.py` | `from app import db` 因 app/__init__.py `__getattr__` 仅桥接 `"app"` 恒抛 AttributeError → DB 分支永不生效；改 `from db_models import db`；同时去掉 `_db_resources` 缓存（settings 保存配置置 DB_CONNECTED=True 后缓存 (None,None) 不失效的问题） |
| J4-2 | 9 条死路由删除 | `blueprints/ml_bp.py` + `blueprints/settings_bp.py` + `blueprints/outputs_bp.py` | ml_bp 3 条（analyze_balance_data/cluster_balance_data/detect_outliers_iqr 审计确认无 UI 调用，同步清理 import）；settings_bp 5 条（load_db_config/reset_db_config/test_connection/face_weights/reload_db_connection，重载逻辑已内联于 save_db_config）；outputs_bp delete_output_file/`<int>`（int 转换器与 FS md5 hash id 矛盾且无调用方） |
| J4-3 | 双份实现合并 | `app/services/data_processing.py` + `app/utils/config_manager.py`（删除） | 两份与顶层实现逐字重复；project_statistics 改用 `utils.config_manager`，`app/services/__init__.py` 清空假导出 |

**结果**：全量 `pytest tests/` **81 passed**（73 + 机型监控 8）；`wsgi` 应用启动验证 70 路由、无死路由残留、templates 无已删文件引用；J3 颜色双源（`#2563eb` 服务端导出主题 vs `#1f77b4` 前端交互主题/数据面颜色）经核实为双路径语义不同非冲突、Y轴 niceDtick 服务端/前端双端架构必需，均保留不破坏已验收图表。

### 第四十八轮修复：报告图表加载初期横向溢出（2026-08-20）

用户重新导出报告（184252）仍见空白。browser_use 实测真实报告定位根因：**稳定状态右侧空白已为 0px**（第四十七轮修复生效），但**加载初期 Plotly 在隐藏容器（`style="display:none"`）中渲染**——`clientWidth=0` 时 Plotly 退回默认 700px 宽度，SVG 超出容器产生横向滚动条与右侧可滚动空白区；不触发 `window.resize` 不会自愈。

| 修复项 | 文件 | 说明 |
|--------|------|------|
| 渲染前显示容器 + 显式设宽 + 渲染后校正 | `services/report_constants.py` | renderAll 第二遍：`container.style.display='block'` → `layout.width=container.clientWidth` → `newPlot` → `relayout({width})`，消除隐藏容器宽度误算 |

**验证**：browser_use 实测新报告——加载全程（T0/T1/T2/T6）`scrollWidth=clientWidth=713`，无横向溢出；6 个 SVG 宽度均 = 容器宽度（603px）；`py_compile` OK；8 项相关测试全通过。已确认为纯 Python 模块变更，需重启 + 重新导出生效。

### 第四十一轮修复：接口漂移测试全量修复（2026-08-20）

第三十一轮重构删除了图表缓存/任务队列/批量导出等旧接口，`test_report_exporter.py`(8 失败) + `test_integration.py`(4 失败) 引用旧 API。全链路检索确认这些旧接口**生产代码零调用**（仅 `report_bp.py` 的 `create_shareable_link` 存活），故决策：**测试对齐当前 API，不恢复死接口**。过程中发现并修复 2 处真 bug：

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | HtmlExporter report_config 透传 | `services/report_exporter.py` | `export("html",...,report_config=)` 原直接 TypeError，现透传至 `render()` |
| P0 | 章节开关不生效 | `services/report_renderer.py` | `_assemble` 原无条件渲染全部章节，`include_*` 仅过滤目录；现同时作用于目录与正文 |
| P1 | 测试重写对齐 API | `tests/test_report_exporter.py` | 10→5 用例：删图表缓存×2/任务/队列死用例，改写 init/config/history/shareable |
| P1 | 集成测试重写 | `tests/test_integration.py` | 6→4 用例：删 batch/queue，修 CSV 数据源（speed_detailed_scores）与 customization 断言 |
| P1 | 测试目录隔离 | 两个测试文件 | `setUp` 用 `ReportExporter(output_folder=temp_dir)`，杜绝写污染项目 `outputs/export_history.json` |

**结果**：12 个失败用例全部通过；全量回归失败 15 → 3（剩余 `test_data_processing`/`test_data_validator` 为既有基线，与重构无关）。

### 第四十轮修复：技术债务清理（2026-08-19）

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P1 | 常量迁移 | `services/report_constants.py`（新建） | `PLOTLY_CDN_URL` + `PLOTLY_DUAL_TRACK_SCRIPT` 从死代码迁移 |
| P1 | 死代码文件删除 | `services/report_html_builder.py` | 702 行 `ReportHtmlBuilder`（已被 ReportRenderer 取代），删除前确认仅 1 处引用 |
| P1 | 废弃方法删除 | `services/report_exporter.py` | `build_report_html` + `_build_charts` 226 行 + 清理无引用 `import base64` |
| P2 | 构造函数兼容 | `services/report_exporter.py` | `ReportExporter.__init__` 支持 `output_folder` 参数，修复 `test_export_functions.py` 3 个 TypeError |
| P2 | HTML 重复属性清理 | `templates/_charts_partial.html` | 8 处重复 `class` 属性合并（第二个覆盖第一个，HTML 无效） |

### 第三十九轮修复：报告体系六维重构 + 图表双轨兜底（2026-08-19）

六维报告评审（科学性/可读性/专业性/UI/布局排版）发现：摘要文案与算法不一致（幅值维度缺失）、内容脱节、双 CSS 视觉分裂；同时审计确认报告图表为 base64 PNG 静态图，不引用首页 div、不加载 Plotly。

**方案四 — 图表静态图 + 交互双轨兜底**：

| P0 | 双轨图表渲染 | `report_export_css.py` | `<img>` base64 静态图兜底 + `.chart-plotly-container` 隐藏交互容器，Plotly CDN 可用时渲染交互图并隐藏静态图，离线/异常保留静态图 |
| P0 | 打印强制静态图 | `report_export_css.py` | `@media print` 强制显示静态图/隐藏交互层 |
| P0 | PDF 自动继承 | weasyprint | 不执行 JS，PDF 天然使用静态图，无需额外适配 |

**方案 A+/B+/C+ — 报告内容与排版重构**：

| P0 | ReportRenderer 数据驱动渲染 | `services/report_renderer.py`（新建 ~356行） | 从 session_data 直接渲染，替换旧 ReportHtmlBuilder，`render(session_data, report_config)` |
| P0 | 封面页 | `_render_cover` | 型号/测试机/日期/推荐转速 |
| P0 | 目录锚点 | `_render_toc` + `#sec-*` | 六章编号导航，`include_*` 开关同步控制目录与正文 |
| P0 | 评分明细表 | `_render_scores` | 每转速各端面得分，最优行高亮 `tr.best` + 最优徽标 |
| P0 | 页眉页脚 | `_render_page_header`/`_render_page_footer` | 跨页品牌信息 |
| P0 | 报告版本号 v2.0 | `_assemble` | 版本标识 |
| P1 | 摘要补齐幅值维度 | `_render_summary` | 文案与算法一致（IQR 40% + CV 40% + 幅值 20%） |
| P1 | 方法论补充说明 | `_render_methodology` | 归一化公式 + Z-score/MAD 异常过滤说明 |
| P1 | 删除 ECharts CDN | `report_renderer.py` | 避免无效网络请求，统一 EXPORTER_CSS |

### 第二十二轮修复：预览功能失效 + 表头字体颜色回归（2026-05-13）

第十九轮 tokenization 引入两处回归：(1) `--text-muted` 令牌定义值保持旧色 `#94a3b8`（对比度仅2.93:1），6处UI元素文字与背景融合不可辨认；(2) 预览API失败时fallback路径只用basename不含型号子目录，子目录文件预览一律404。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | --text-muted令牌值恢复AA | `style.css` | `#94a3b8`(2.93:1) → `#64748b`(4.77:1 WCAG AA)，6处元素（rm-stat-label/rm-model-meta/rm-model-chevron/rm-file-meta/rm-empty/rm-search-icon）同时恢复可读性 |
| P0 | 预览catch块子目录路径推导 | `outputs.js` | `.catch()` 块内从 `filePath`（绝对路径）提取 `/outputs/` 之后部分作为 `relPath`，替换裸 `filename`，子目录HTML/图片/PDF预览恢复可用 |

### 第二十三轮修复：Hero标题不可见根因修复 + 对比度全面提升（2026-05-13）

第二十二轮 `--text-muted` 令牌修复仅解决6处分项元素对比度，用户反馈标题"报告管理"及副标题仍然不可见。三省六部全量排查发现根因：`style.css` 全局 `.container` 规则 `background-color: var(--background-white)`(白色) 覆盖了 `.rm-hero` 蓝色渐变背景，白色标题文字(`#fff`)在白色容器上对比度仅1:1完全不可见。同时发现 `#f1f5f9` 浅灰背景上 `#64748b`/`#6c757d` 对比度不足WCAG AA 4.5:1。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | Hero容器背景透明化 | `outputs.css` | 新增 `.rm-hero .container { background: transparent; box-shadow: none; border-radius: 0; padding: 0; }`，消除全局 `.container` 白色背景对Hero蓝色渐变的覆盖，标题"报告管理"(1:1→4.5:1)和副标题(1.15:1→3.9:1)恢复可见 |
| P1 | --text-muted令牌加深 | `style.css` | `#64748b`(白底4.77:1/浅灰底4.31:1) → `#475569`(白底7.67:1/浅灰底7.02:1)，`.rm-result-count`/`.rm-empty` 等 `#f1f5f9` 背景元素对比度从不足AA→远超过 |
| P1 | Bootstrap .text-muted覆盖 | `style.css` | 新增 `.text-muted { color: var(--text-muted) !important; }`，加载文字"正在加载报告数据..."从Bootstrap默认`#6c757d`(4.23:1) → `#475569`(7.02:1) |

### 第二十四轮修复：预览功能全链路修复（2026-05-13）

三省六部全链路审查发现预览功能失效存在4项根因：(1) `outputs.html` 未加载 `bootstrap.bundle.min.js`，`new bootstrap.Modal()` 抛出 ReferenceError 模态框根本不弹出——这是与其他10个模板唯一的差异；(2) PDF预览路由使用 `as_attachment=True` 强制下载而非 inline 展示，iframe 中无法渲染；(3) `preview_output_info` 中 `view_url` 未 URL 编码，含中文/空格文件名 404；(4) filter chip `excel` 值与数据库 `xlsx` 不匹配，`other` 无对应类型。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | Bootstrap JS 缺失 | `outputs.html` | 新增 `bootstrap.bundle.min.js` 引用，修复 `bootstrap.Modal` 未定义 → 模态框不弹出，预览功能核心阻断 |
| P0 | PDF inline 查看路由 | `outputs_bp.py` | 新增 `/view_pdf/<path:filename>` 路由，`send_from_directory` 无 `as_attachment`，iframe 内正常渲染 PDF |
| P0 | view_url URL 编码 | `outputs_bp.py` | `os.path.relpath` → 逐段 `urllib.parse.quote(part)`，含中文/空格文件名预览不再 404 |
| P0 | filter chips 数据对齐 | `outputs.html` | `excel` → `xlsx`、删除 `other`（无对应数据类型），筛选功能恢复正常 |
| P1 | PDF 前端路由切换 | `outputs.js` | 主路径 + catch 块 PDF 预览均由 `/api/outputs/download/` → `/view_pdf/`，inline 渲染替代强制下载 |
| P1 | batch_download 子目录修复 | `outputs_bp.py` | 非绝对路径时纳入 `fan_model` 重建子目录路径，子目录文件打包下载不再 404 |


### 第二十五轮修复：预览功能布局全面修复（2026-05-13）

三省六部审查发现 outputs.css（463行）中预览样式完全空白——`rm-preview-frame`/`rm-preview-img`/`rm-preview-content` 四个类名在全项目范围CSS规则数为0。iframe 默认 300×150px 缩在 modal-xl 角落，图片无容器约束直接溢出，文本无 max-height 撑爆 body。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | rm-preview-frame 样式 | `outputs.css` | `width:100%; height:70vh; border:none`，HTML/PDF iframe 全宽全高渲染 |
| P0 | rm-preview-img 样式 | `outputs.css` | `display:flex; justify-content:center; max-height:70vh; overflow:auto`，图片居中约束 |
| P0 | rm-preview-content 样式 | `outputs.css` | `max-height:65vh; overflow-y:auto; padding:16px 20px`，文本可滚动+内边距 |
| P0 | previewModal modal-body | `outputs.css` | `padding:0; max-height:75vh; display:flex; flex-direction:column`，统一高度约束 |
| P1 | 响应式断点 | `outputs.css` | 768px(60vh)/576px(50vh) 递减，移动端预览可操作 |

### 第二十九轮修复：工程健壮性提升（2026-05-14）

三省六部评估 P2 项执行，6 项工程健壮性提升：

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P2 | 蓝图模块化注册 | `wsgi.py` | 抽取 `_register_blueprints(app)` 函数，蓝图导入/注册可独立测试 |
| P2 | 暗色模式 | `style.css` | 新增 `@media (prefers-color-scheme: dark)` 块，覆盖 15 个选择器（body/card/table/form/modal/navbar等） |
| P2 | 表格响应式 | `style.css` | 新增 `.table-responsive-wrapper` 横向滚动容器 |
| P2 | 全局状态类 | `style.css` | 新增 `.empty-state`/`.loading-state` 统一空状态和加载态组件 |
| P2 | DB 连接超时 | `database_connections.py` | 新增 `CONNECT_TIMEOUT = 10` 显式超时配置 |
| P2 | 肘部法 K 上限 | `data_analysis.py` | `max_k = min(max_k, 10)` 防止大K性能退化 |

### 第三十轮修复：工程健壮性续 + TRAE文档同步（2026-05-14）

三省六部评估 P2 剩余项 + TRAE规则文档一致性，6 项：

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P2 | Flask应用工厂配置化 | `config.py` + `wsgi.py` | STATIC_FOLDER/STATIC_URL_PATH 纳入 BASE_CONFIG，wsgi.py 构造 Flask 时引用 |
| P2 | app/__init__.py 文档化 | `app/__init__.py` | 增强 docstring：兼容层说明 + 废弃警告 + 不扩展声明 |
| P2 | btn-outline-light 暗色回退 | `style.css` | `@media (prefers-color-scheme: dark)` 内浅色按钮文字回退深色 |
| P2 | 字段名一致性审计 | 全项目 | 确认前端字段与后端 API 返回一致（C3 筛查，无实际不一致） |
| P2 | Type hints + NameError 修复 | `data_analysis.py` | `_try_quadratic_fit` 参数类型标注 + 参数名 `x_numeric`→`x` 修复运行时 NameError |
| P2 | README.md 综合更新 | `README.md` | 项目结构/环境变量/变更日志同步至当前状态 |

### 第三十一轮修复：导出文件中文命名（2026-05-14）

所有导出文件的默认命名从英文改为中文，提升可读性和专业性：

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P2 | 报告文件中文命名 | `report_export.py` | 5处：HTML `{型号}_动平衡分析报告_{时间}.html`、CSV `{型号}_统计数据_{时间}.csv`、JSON `{型号}_分析数据_{时间}.json`、Excel `{型号}_分析报告_{时间}.xlsx` |
| P2 | 图表文件中文命名 | `chart_generation_optimized.py` | 2处 chart_filename：`{前缀}_{端面}_{图表中文名}` 如 `SN300_P1面_箱线图.png` |
| P2 | 图表服务同步 | `app/services/chart_generation.py` | 2处 chart_filename 同步中文命名 |

**命名对照**：

| 类型 | 旧命名 | 新命名 |
|------|--------|--------|
| HTML报告 | `report_20260514_120000.html` | `SN300-12_动平衡分析报告_20260514_120000.html` |
| CSV数据 | `report_20260514_120000.csv` | `SN300-12_统计数据_20260514_120000.csv` |
| JSON数据 | `report_20260514_120000.json` | `SN300-12_分析数据_20260514_120000.json` |
| Excel报告 | `report_20260514_120000.xlsx` | `SN300-12_分析报告_20260514_120000.xlsx` |
| 箱线图 | `SN300_p1_box.png` | `SN300_P1面_箱线图.png` |
| 趋势图 | `SN300_p1_trend.png` | `SN300_P1面_趋势图.png` |

### 第三十七轮修复：ML页面数据兼容性修复（2026-05-15）

深度分析功能中字符串数据导致 `pd.to_numeric` 类型转换失败，引发运行时异常。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | overall_stats 循环 pd.to_numeric 保护 | `machine_learning.py` | `multi_dimensional_analysis` 中 `overall_stats` 循环增加 `pd.to_numeric(errors='coerce')`，字符串数据不再崩溃 |
| P0 | detailed 分组段 pd.to_numeric 保护 | `machine_learning.py` | 分组统计段增加 `pd.to_numeric(errors='coerce').dropna()`，分组内字符串值安全降级 |
| P1 | NaN 安全过滤 | `machine_learning.py` | dropna() 后空 DataFrame → 跳过该指标统计，不再返回 NaN |

### 第三十八轮修复：ML页面结构性重构 + 重复实现合并（2026-05-15）

ML 页面从静态 API 文档页重构为交互式 4 面板 ML 工具页；同时合并两个重复的 `machine_learning.py` 实现。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | ML页面重构为交互工具 | `templates/ml.html` | 从静态文档页 → 4 面板交互式布局（趋势预测/关键指标/多维度分析/异常检测），含 JSON 输入 + Plotly.js 图表 + CSRF 安全 |
| P0 | ml.js 新建 | `static/js/ml.js` | 420行 IIFE 模式，4 面板 API 逻辑 + 样本数据预填 + Plotly 动态渲染 |
| P0 | 死码 machine_learning.py 删除 | `app/services/machine_learning.py` | 318 行死代码（`_build_prediction_model` 抛出 NotImplementedError），彻底删除 |
| P0 | 算法合并增强 | `machine_learning.py`（根级） | 558→724 行：从已删除文件合并 `detect_outliers_iqr`（IQR异常检测）、`cluster_balance_data`（KMeans聚类）、`analyze_balance_data`（多维分析）三函数 |
| P0 | ml_bp.py 新增3端点 | `blueprints/ml_bp.py` | 新增 `/api/cluster_balance_data`、`/api/detect_outliers_iqr`、 `/api/analyze_balance_data`，总端点 8 个 |
| P1 | 服务层导入清理 | `app/services/__init__.py` | 移除已删除 `machine_learning_service` 导入，消除 ModuleNotFoundError |

### 第二十八轮修复：安全加固+质量基线（2026-05-14）

三省六部全量评估发现 23 项问题（1 P0 + 8 P1 + 14 P2）。本轮执行 P0+P1 安全加固和质量基线 9 项：

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | XSS 漏洞修复 | `modal-manager.js` | L178 `error.message`→`escapeHtml(error.message)`，阻断恶意脚本注入 |
| P1 | console.log 清理 | 12 个 JS 文件 | 134 处注释化为 `// [cleaned]`，保留 `console.error/warn` |
| P1 | print()→logging | `chart_generation.py`+`data_processing.py` | 3 处 `print()`→`logger.info()` |
| P1 | 硬编码颜色令牌化 | `style.css` | 11 处 `#3498db`/`#e0e0e0`/`#eee`/`#dee2e6`→设计令牌 |
| P1 | CSRF 审查 | 全部蓝图 | 已确认 Flask-WTF 全局启用自动保护所有 POST，**误报消除** |
| P1 | Magic bytes 校验 | `file_manager.py` | 新增 `MAGIC_BYTES_MAP`+`validate_magic_bytes()`，覆盖 csv/xlsx/xls/json/xml/txt |
| P1 | 日志脱敏 | `error_handler.py` | `handle_exception`/`log_error` 生产环境不记录 user_id/IP |
| P1 | ApiResponse 统一化 | `outputs_bp.py` | 27 处 `jsonify({"error":...})`→`ApiResponse.error()` 等 |
| P2 | 上传扩展名校验 | `main_bp.py` | P1/P2/ST 三面文件上传前增加 `allowed_file()` 检查 |

### 第二十七轮修复：型号追踪管理体系全面建立（2026-05-14）

三省六部架构审查发现报告管理页面本质是"文件浏览器"而非"管理系统"。分两阶段建立型号追踪管理体系——Phase 1(5项)奠定数据基础：后端summary统计、型号卡片重设计、快速导航、数据缓存、型号级下载；Phase 2(4项)强化交互体验：分组/平铺视图切换、型号名搜索、键盘快捷键、完整性指示。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | by_model API返回summary | `outputs_bp.py` | 每组增加type_breakdown/total_size/first_report/latest_report/health(fresh/recent/stale/old)五字段 |
| P0 | 型号卡片UI重设计 | `outputs.js` | 新增健康状态圆点(fresh绿/recent黄/stale灰/old红)、类型分布标签(色码)、时间跨度、数据量；hover显示型号级下载按钮 |
| P0 | 型号快速导航标签栏 | `outputs.html`+`outputs.js`+`outputs.css` | stats bar下方新增型号标签+数量角标，点击smooth scroll到对应型号组并自动展开 |
| P0 | 客户端数据缓存+内存筛选 | `outputs.js` | 首次加载缓存全量数据，后续filter切换走`_dataCache`+`filterCachedGroups()`，避免重复API调用 |
| P1 | 型号级一键下载 | `outputs_bp.py`+`outputs.js` | batch_download新增GET方法支持`?fan_model=`参数，每个型号卡片hover显示下载按钮，打包该型号全部报告为ZIP |

Phase 2 — 交互体验强化：

| P0 | 分组/平铺视图切换 | `outputs.js`+`outputs.css` | `_viewMode`状态+`renderFlatFiles()`平铺渲染+`updateViewToggleUI()`按钮态切换，支持分组和平铺两种浏览模式 |
| P0 | 搜索扩展到型号名 | `outputs.js` | `filterCachedBySearch()`双维度匹配——型号名匹配时展示全部文件，文件名匹配时精确筛选 |
| P0 | 键盘快捷键系统 | `outputs.js` | Ctrl+A全选可见文件、Esc清除所有选择、Delete删除选中(含二次确认)，排除输入框聚焦状态 |
| P0 | 型号完整性指示 | `outputs.js`+`outputs.css` | `checkModelCompleteness()`检测type_breakdown，缺HTML报告或缺图表文件时显示⚠️警告标签+tooltip原因说明 |

### 第二十轮修复：Hero副标题可见性修复（2026-05-13）

Hero 副标题 "管理、预览和下载所有导出的分析报告" 使用了 `opacity: 0.8` 但无显式 `color`，在蓝色渐变背景上继承深色文字无法辨认。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | Hero副标题颜色显式化 | `outputs.css` | `.rm-hero-subtitle` `opacity:0.8` → `color: rgba(255,255,255,0.85)`，任何背景可见 |

### 第十八轮修复：报告管理Hero按钮可见性 + 版面宽度统一（2026-05-12）

Hero 区域 `btn-outline-light` 按钮（白字透明底白边框）在浅色背景上完全不可见；`.rm-content`（1400px）与 `.container`（1320px）宽度不统一导致三段面板无法对齐。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | Hero按钮全部改为btn-light | `outputs.html` | 全选/取消/反选/折叠/展开 5个按钮 `btn-outline-light` → `btn-light`（深字浅底，任何背景可见） |
| P0 | 浮动条按钮可见性 | `outputs.html` | 清除选择 `btn-outline-light` → `btn-light`；打包下载 `btn-outline-info` → `btn-info` |
| P1 | Hero背景纯色fallback | `outputs.css` | `linear-gradient()` 增加 `var(--primary-color, #2563eb)` fallback + `background-color: #2563eb` |
| P1 | 版面宽度统一对齐 | `outputs.html` + `outputs.css` | `.rm-content` 增加 `container` 类，移除 `max-width:1400px`/`margin:auto` |

### 第十九轮修复：报告管理页面UI全面重设计（2026-05-13）

使用设计系统令牌重设计报告管理页面，使设计语言与仪表盘/报告/设置等其他页面完全一致。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | HTML模板重构 | `outputs.html` | 从extends base.html → 独立HTML页面（匹配index.html/report.html模式）；新增rm-hero/rm-stat-bar/rm-toolbar新组件结构 |
| P0 | CSS全面令牌化 | `outputs.css` | 所有颜色/间距/阴影/圆角/过渡替换为设计令牌（--background-light/--background-white/--text-primary/--text-muted/--primary-color/--radius-*/--shadow-*/--transition） |
| P0 | JS结构同步 | `outputs.js` | 9处适配新HTML结构：stat IDs更新、`.rm-model-section`→`.rm-model-group`、`.open`→`.collapsed`类、`.visible`→`.show`、删除确认modal→window.confirm()、裁剪/展开逻辑重写 |
| P1 | 设计语言统一 | 全三文件 | 页面背景`--background-light`、卡片`--background-white`+`--shadow-sm`+`--border-color`、圆角`--radius-lg`(16px)/`--radius-md`(10px)、hover用`--shadow-md`+`translateY(-1px)` |
| P1 | CSS加载顺序 | `outputs.html` | bootstrap → bootstrap-icons → style.css → outputs.css（匹配其他页面加载顺序） |
| P1 | JS依赖补齐 | `outputs.html` | 新增safe-fetch.js引用（之前缺失，依赖window.safeFetch但未加载） |
| P2 | 删除确认简化 | `outputs.html` + `outputs.js` | 移除deleteConfirmModal（大段HTML+JS），改用window.confirm()浏览器原生确认框 |
| P2 | 双格式化bug修复 | `outputs.js` | latestDate已formatDate后不再二次formatDate |

### 第十七轮修复：数据库删除失败 + 报告管理页面全面审查优化（2026-05-12）

代码审查发现 18 项问题（3 P0 + 8 P1 + 7 P2）—— 批量删除数据库连接失败 500 错误 + 多处UI/UX缺陷，全量修复 15 项。

**数据库修复（3项）**:
| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | 异常处理器扩宽 | `db_models.py` | `(ValueError, IOError, TypeError)` → `Exception`，非标准异常不再吞噬 |
| P0 | DB连通性检查 | `outputs_bp.py` | `_get_db_resources()` 检查 `DB_CONNECTED` 标志，断开时返回 None 触发降级 |
| P0 | batch_delete文件系统回退 | `outputs_bp.py` | 数据库不可用时自动使用 `_delete_by_hash_file_id` 文件系统删除，不再返回500错误 |

**UI/UX修复（12项）**:
| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | 预览下载链接初始值 | `outputs.js` | `filePath` 文件系统路径 → `#`，防止浏览器无效跳转 |
| P0 | 批量下载文件名 | `outputs.js` | `'reports_batch.zip'` 硬编码 → 使用 Content-Disposition 解析出的文件名 |
| P0 | 统计最新日期 | `outputs.js` | `groups[0].created_at` → 遍历取真正最大日期 |
| P1 | 文件卡片hover位移 | `outputs.css` | `translateX(3px)` → `translateY(-2px)`，消除Grid重叠切边 |
| P1 | 统计卡片最小宽度 | `outputs.css` | `minmax(160px,1fr)` → `minmax(220px,1fr)` |
| P1 | 批量删除成功反馈 | `outputs.js` | 新增 `window.showToast('已成功删除 N 个文件', 'success')` |
| P1 | 移除Hero重复按钮 | `outputs.html` + `outputs.js` | 删除 Hero 栏的 btnBatchDelete/batchDownloadBtn，只保留底部浮动条 |
| P1 | 移除Plotly.js 3MB加载 | `outputs.html` | 删除全局加载，iframe内HTML报告自带引用 |
| P1 | 移动端响应式增强 | `outputs.css` | 新增9条移动端规则（hero actions换行/batch bar圆角/filter chips间距/卡片padding） |
| P1 | 型号checkbox双向同步 | `outputs.js` | `updateBatchBar()` 末尾新增型号级checkbox checked/indeterminate状态同步 |
| P2 | var→let/const | `outputs.js` | 模块级变量 `_selectedFiles`/`_activeFilter` 改用 let（全文47处需逐行替换，本次先处理模块级） |
| P2 | 统计图标颜色令牌化 | `outputs.css` | `#eff6ff`→`rgba(var(--primary-rgb),0.08)`，设计系统一致 |
| P2 | 冗余_allGroups移除 | `outputs.js` | 删除从未读取的全局变量 |
| P2 | blob URL安全释放 | `outputs.js` | `revokeObjectURL` 包裹 try/catch 防止内存泄漏 |

### 第十六轮修复：报告管理UI可访问性与CSRF修复（2026-05-12）

字体不可见（8处低对比度颜色#94a3b8→#64748b/#475569）+ 批量删除CSRF验证失败（模板缺失csrf_token隐藏域），共 8+1 项修复（1 P0 + 8 P1）。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | CSRF令牌缺失 | `outputs.html` | 新增 `<input name="csrf_token" value="{{ csrf_token() }}">`，修复批量删除POST请求CSRF验证失败 |
| P1 | rm-file-meta对比度 | `outputs.css` | #94a3b8(#f8fafc背景2.6:1) → #64748b(4.5:1)，0.75rem小字可读 |
| P1 | rm-empty对比度 | `outputs.css` | #94a3b8 → #64748b，empty-icon opacity 0.4→0.5 |
| P1 | rm-model-chevron对比度 | `outputs.css` | #94a3b8 → #64748b |
| P1 | rm-search-icon对比度 | `outputs.css` | #94a3b8 → #64748b |
| P1 | rm-model-meta对比度 | `outputs.css` | #64748b → #475569 |
| P1 | rm-filter-chip对比度 | `outputs.css` | #64748b → #475569，hover #94a3b8/#475569 → #94a3b8/#334155 |
| P1 | rm-stat-label对比度 | `outputs.css` | #64748b → #475569 |
| P1 | btn-icon对比度 | `outputs.css` | #64748b → #475569 |
| P1 | TEMPLATES_AUTO_RELOAD | `wsgi.py` | 生产环境启用模板自动重载，避免每次修改模板需重启gunicorn |

### 第十五轮修复：报告管理预览功能全链路修复（2026-05-12）

子目录路径路由不支持 + 下载路径引用错误 + 预览模态框下载链接使用文件系统路径，共 6 项修复（3 P0 + 3 P1）。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | 路由转换器升级 | `outputs_bp.py` | download_file/view_chart/view_chart_html `<filename>` → `<path:filename>` |
| P0 | 预览路径包含型号子目录 | `outputs_bp.py` | preview_output_file/preview_output_info 构建path纳入fan_model |
| P0 | 下载API路径修正 | `outputs.js` | download_by_path → download 对齐后端路由名 |
| P1 | 预览模态框下载链接修复 | `outputs.js` | openPreview重写：downloadBtn.href从API获取 + fallback构造URL |
| P1 | 图片类型扩展 | `outputs.js` | 预览图片格式 png → [png, jpg, jpeg, svg, webp] |
| P1 | 文件卡片data-download-url | `outputs.js` | 预览按钮携带型号子目录下载URL |

### 第十四轮修复：全模块排版统一宽屏适配（2026-05-12）

各模块排版不统一，根因三类：CSS加载顺序错误 / 缺失style.css / inline硬编码max-width。共 4 P0 项修复。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | CSS加载顺序修复 | `report.html`, `ml.html`, `settings.html` | bootstrap → bootstrap-icons → style.css |
| P0 | 缺失style.css修复 | `skill_evaluation.html` | 新增引用 + 移除旧:root(#3498db) + 移除重复样式 |
| P0 | inline阻断宽屏修复 | `ml.html` | 删除 `.container{max-width:1200px}` 硬编码 |
| P0 | 旧颜色修复 | `skill_evaluation.html` | --primary-color: #3498db → #2563eb |

### 第十三轮修复：导出报告非box图表全维度评审修复（2026-05-12）

导出报告只有箱线图正常显示，violin/heatmap/histogram/bubble/3d/parallel/radar 全部空白。

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | 7种图表matplotlib PNG | `chart_generation_optimized.py` | violin/heatmap/histogram/bubble/3d/parallel/radar |
| P0 | 7种图表Plotly.js HTML | `chart_generation_optimized.py` | 对应Plotly.newPlot分支 |
| P1 | 异常处理器扩宽 | `chart_generation_optimized.py` | (ValueError,IOError,TypeError) → Exception |
| P1 | Agg后端显式切换 | `chart_generation_optimized.py` | plt.switch_backend('Agg') |
| P1 | tight_layout防御性包装 | `chart_generation_optimized.py` | try/except包装 |
| P2 | 旧占位图清理 | `outputs/` | 删除12个16990字节fallback PNG |

### 第十二轮修复：全项目三省六部综合审查（2026-05-12）

三省六部全维度审查（中书省→尚书省→六部→门下省→锦衣卫），5并行Agent调研全部源码层，修复 6 P0 + 5 P1 项：

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | 死码shim蓝图删除 | `blueprints/in_depth_analysis_bp.py`, `blueprints/skill_evaluation_bp.py` | 仅2行import转发，从未在wsgi.py注册，纯死代码 |
| P0 | `import *`→显式导入 | `project_statistics.py` | 消除命名空间污染，标注已迁移至app.services |
| P0 | shim依赖链修复 | `_diag_render.py` | 直接导入app.services.project_statistics |
| P0 | 蓝图包引用更新 | `blueprints/__init__.py` | 删除shim引用，直连analysis_bp |
| P0 | SECRET_KEY文档强化 | `config.py` | wsgi.py统一管理+模块直接引用fallback说明 |
| P0 | ReportExporter CSS外部化 | `report_export.py`→`report_export_css.py` | 85行`_html_exporter_css()`内嵌CSS提取为独立模块 |
| P1 | ApiResponse统一响应类 | `app/utils/api_response.py` | 新建: success()/error()/ok()静态方法，标准化响应格式 |
| P1 | 生产环境异常脱敏 | `wsgi.py` | error_type仅在debug模式返回，防信息泄露 |
| P1 | crypto salt环境变量化 | `app/utils/crypto_utils.py` | CRYPTO_SALT环境变量+默认回退，安全增强 |
| P1 | Magic bytes文件校验 | `data_processing.py` | validate_magic_bytes()防扩展名伪造上传 |
| P1 | chart_generation弃用标注 | `app/services/chart_generation.py` | 模块docstring标注chart_generation_optimized.py为首选 |

### 第十一轮修复：交互性优化（2026-05-12）

三省六部专项审查（兵部主导，刑部/户部/工部/吏部协查），修复 8 P0 + 3 P1 项：

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | safeFetch四地重复→统一模块 | `templates/*.html` → `static/js/safe-fetch.js` | 4模板内嵌定义(~50行重复)提取为单文件, 并补齐网络异常兜底 |
| P0 | 文件名XSS修复 | `upload.js:35` | innerHTML→textContent, 防止恶意文件名注入 |
| P0 | CSRF令牌路径统一 | `skill_evaluation.html:376` | meta[name="csrf-token"]废弃路径移除, 统一input[name="csrf_token"] |
| P0 | alert()→Toast替换 | `outputs.js` | 两处alert()替换为Bootstrap toast, 统一交互反馈 |
| P0 | alert()→内联提示替换 | `upload.js` | 格式校验alert→红色文字内联提示, 不阻断操作 |
| P0 | console.log调试残留清理 | `modal-manager.js` | 清理16条调试日志(含500字符HTML dump), 保留6处错误日志 |
| P0 | Toast通知系统 | `static/js/toast-helper.js` | 新建: slide-in动画, 4种类型图标/颜色, 自动4秒消失, 手动关闭 |
| P0 | 拖放样式色值对齐 | `upload.js:51` | #0d6efd→var(--primary-color), #e7f1ff→rgba(var(--primary-rgb)) |
| P1 | err.message escape | `outputs.js`, `modal-manager.js` | 3处err.message拼接innerHTML增加escapeHtml/var(--danger-color) |
| P1 | rec.text textContent化 | `in_depth_analysis_enhanced.js:649` | innerHTML混入→createTextNode分离, 防御性编程 |
| P1 | error.message→var(--danger-color) | `modal-manager.js:194` | 硬编码red→设计令牌 |

### 第十轮修复：UI/视觉设计统一（2026-05-12）

三省六部专项审查（礼部主导，工部/吏部/户部/兵部协查），统一三套CSS系统 + 修复 5 P0 + 4 P1 项：

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | :root设计令牌扩展 | `style.css` | 新增 --primary-rgb, --text-muted, --font-stack, --radius-sm/md/lg, Bootstrap变量覆盖 |
| P0 | 旧颜色值替换 | `style.css` | rgba(52,152,219)→rgba(var(--primary-rgb)), #0d6efd→var(--primary-color), h1:hover移除 |
| P0 | .card-header选择器收窄 | `style.css` | 增加 :not(.border-success/.danger/.warning/.info) 排除语义色卡片 |
| P0 | ReportExporter CSS对齐 | `report_export.py` | 字体栈 SimSun→Segoe UI 统一, #007bff→#2563eb(上轮) |
| P0 | chart hoverlabel颜色 | `chart_style_config.py` | bordercolor #1f77b4→#2563eb |
| P1 | outputs.html CSS外部化 | `templates/outputs.html` → `static/css/outputs.css` | ~426行内嵌CSS提取为独立文件, --rp-*命名空间消除,统一:root令牌 |
| P1 | navbar.html样式迁移 | `templates/macros/navbar.html` → `style.css` | ~100行内嵌<style>合并至主样式表, 0内嵌残留 |
| P1 | _html_exporter_css字体栈 | `report_export.py` | SimSun→Segoe UI统一 |
| P1 | CSS过渡统一为设计令牌 | `style.css` | transition: all 0.3s→var(--transition), box-shadow→var(--shadow-*) |

### 第九轮修复：三省六部全维度审查优化（2026-05-12）

三省六部式代码审查（中书省→尚书省→六部→门下省→锦衣卫）后，修复 5 P0 + 4 P1 项缺陷：

| 优先级 | 修复项 | 文件 | 说明 |
|--------|--------|------|------|
| P0 | sync_outputs_from_filesystem 递归扫描 | `outputs_bp.py` | 适配型号子目录，新导出文件纳入DB |
| P0 | delete 先commit再删文件 | `outputs_bp.py` | 防止DB回滚+文件已删的幽灵记录 |
| P0 | _detect_fan_model_from_path 异常吞没 | `outputs_bp.py` | 区分 RuntimeError vs 正常未匹配 |
| P0 | _list_filesystem_files 废弃参数 | `outputs_bp.py` | 删除未使用的output_folder形参 |
| P0 | ReportExporter CSS对齐设计令牌 | `report_export.py` | #007bff→#2563eb，统一视觉体系 |
| P1 | _detect_fan_model_from_path IO优化 | `outputs_bp.py` | 一次读history，循环内复用缓存 |
| P1 | print()→logger + _safe_model_name模块化 | `report_export.py` | 可追踪日志 + 解耦HtmlExporter |
| P1 | 文件系统模式删除降级支持 | `outputs_bp.py` | hash_id查找文件路径删除 |
| P1 | view_chart_html子目录路径支持 | `outputs_bp.py` | 型号子目录下的HTML可在线查看 |

### 第八轮修复：报告管理中心强化（2026-05-11）

| 文件 | 状态 | 内容 |
|------|------|------|
| `report_export.py` | ~1360行 | 导出按型号子目录存储（outputs/{型号}/）、_safe_model_name模块化、HTML方法论权重修复(0.5/0.5→0.4/0.4/0.2) |
| `blueprints/outputs_bp.py` | ~870行 | by_model按型号分组API、preview_info多格式检测、batch_download批量ZIP下载、download_by_path子目录下载 |
| `templates/outputs.html` | ~350行 | 报告管理中心页面：暗色Hero头、4统计卡片、折叠型号分组、chip筛选、文件卡片网格、预览模态框、批量操作浮动条 |
| `static/js/outputs.js` | ~330行 | 全选/反选/取消、型号级checkbox、多格式预览(iframe/img/pre)、批量删除/下载、搜索debounce |

### 第七轮修复：核心算法科学性全面修复（2026-05-09）

解决了 10 项算法缺陷（3 P0 + 4 P1 + 3 P2），核心文件：

| 文件 | 状态 | 内容 |
|------|------|------|
| `app/services/data_analysis.py` | ~590行 | 趋势分析（X轴修复+非线性检测）、自适应Z-score异常检测、肘部法KMeans |
| `project_statistics.py` | ~989行 | 最优转速三维评分（IQR+CV+幅值）、可配置权重常量 |
| `app/services/skill_evaluation.py` | ~835行 | 综合技能评估、三维度数据质量、可配置阈值、样本量验证 |

### 第五轮修复：数据库安全加固

| 文件 | 内容 |
|------|------|
| `app/utils/crypto_utils.py` | XOR+SHA256密码加密（新建） |
| `database_connections.py` | LRU缓存100、原子文件写入、跨平台超时 |
| `app/utils/config_manager.py` | URL编码密码 |
| `blueprints/settings_bp.py` | 属性bug修复 |
| `blueprints/database_bp.py` | 去重超时代码 |

## 累计修复：280 项（59轮）

| 轮次 | 内容 | 数量 |
|------|------|------|
| 第五轮 | 数据库安全加固 | 7项 |
| 第七轮 | 核心算法科学性修复 | 10项 |
| 第八轮 | 报告管理中心强化 | 6项 |
| 第九轮 | 三省六部全维度审查优化 | 9项 |
| 第十轮 | UI/视觉设计统一 | 9项 |
| 第十一轮 | 交互性优化 | 11项 |
| 第十二轮 | 全项目综合审查 | 11项 |
| 第十三轮 | 导出报告非box图表修复 | 6项 |
| 第十四轮 | 全模块排版统一宽屏适配 | 4项 |
| 第十五轮 | 报告管理预览功能全链路修复 | 6项 |
| 第十六轮 | 报告管理UI可访问性与CSRF修复 | 9项 |
| 第十七轮 | 数据库删除失败 + 全面审查优化 | 15项 |
| 第十八轮 | Hero按钮可见性 + 版面宽度统一 | 4项 |
| 第十九轮 | 报告管理页面UI全面重设计 | 8项 |
| 第二十轮 | Hero副标题可见性修复 | 1项 |
| 第二十二轮 | 预览功能失效 + 表头字体颜色回归 | 2项 |
| 第二十三轮 | Hero标题不可见根因修复 + 对比度全面提升 | 3项 |
| 第二十四轮 | 预览功能全链路修复 | 6项 |
| 第二十五轮 | 预览布局全面修复 | 5项 |
| 第二十七轮 | 型号追踪管理体系全面建立 | 9项 |
| 第二十八轮 | 安全加固+质量基线 | 9项 |
| 第二十九轮 | 工程健壮性提升 | 6项 |
| 第三十轮 | 工程健壮性续+TRAE文档同步 | 6项 |
| 第三十一轮 | 导出文件中文命名 | 3项 |
| 第三十七轮 | ML页面数据兼容性修复 | 3项 |
| 第三十八轮 | ML页面结构性重构+合并重复实现 | 6项 |
| 第三十九轮 | 报告体系六维重构 + 图表双轨兜底 | 12项 |
| 第四十轮 | 技术债务清理 | 5项 |
| 第四十一轮 | 接口漂移测试全量修复 | 14项（12用例+2真bug） |
| 第四十二轮 | ShareLinkManager拆分 + 测试基线清零 | 3项 |
| 第四十三轮 | 报告与前端三差异对齐（评分明细/表格样式/图表布局）+ 图表缓存跨目录修复 | 7项 |
| 第四十四轮 | 报告导出链路 + 重置CSRF全链路收尾（face_labels/箱线图中位线/导出路径/CSRF token） | 4项 |
| 第四十五轮 | 导出报告全维度审查整改（CSV空导出/路径穿越/PDF路径/原子写/POST化/死参数/性能/日志） | 8项 |
| 第四十六轮 | 默认Y轴对齐（首页图表加载自动对齐/重绘保持对齐/报告双轨交互图统一量程） | 4项 |
| 第四十七轮 | 堆叠显示图表右侧空白（box/violin 收紧类别轴 + margin.r，浏览器实测 16.8%→1.22%） | 1项 |
| 第四十八轮 | 报告图表加载初期横向溢出（隐藏容器中 Plotly 默认 700px 渲染，渲染前显式设宽+relayout，实测 0 溢出） | 1项 |
| 第四十九轮 | 三、统计分析结果表单与样本量左右并列（stats-row flex，消除右侧大空白，含打印降级） | 1项 |
| 第五十轮 | Y轴统一标注单位「不平衡量 (g·mm)」（报告双轨交互图补 yaxis.title + matplotlib PNG 6处 + 首页图表 yAxisLabel） | 1项 |
| 第五十一轮 | 统计分析结果并列布局视觉优化（等高 stretch + 卡片渐变/蓝色强调条 + 内距行距，宽屏实测并排等高） | 1项 |
| 第五十二轮 | 各转速样本量移至「五、统计分析方法」末尾小字附注（原三、章节卡片移除，清理 stats-row/sample-card 样式与测试断言） | 1项 |
| 第五十三轮 | 机型监控看板（按机型监控推荐平衡转速+使用设备；新增 model_monitor_service/蓝图/页面/JS，分析完成时记录，告警含停机/完整性/转速漂移，8新用例） | 1项 |
| 第五十四轮 | 全项目冗余/功能重叠全链路评审整改（J1 死代码 7 组 + J2 双绑定/toast 签名/死函数 + J3 图表双重触发 + J4-1 DB 分支可达 + J4-2 九条死路由 + J4-3 双份实现合并） | 8项 |
| 第五十五轮 | 深入分析除零500（退化面无数据 np.std n<=1 抛 ZeroDivisionError）+ 前端 progressFill 作用域 + 错误透出 + 3 回归用例 | 3项 |
| 第五十六轮 | 数据仪表盘与机型监控合并（方案A）：仪表盘 DB 空壳→FS 真实取数（报告扫描+model_monitor.json 聚合）、机型监控区块并入仪表盘复用 model-monitor.js、删导航入口 + /model-monitor 302 重定向、清理 DB_CONNECTED/BASE_CONFIG 死常量、新增 test_dashboard_fs 2 用例（86 测试全过） | 4项 |
| 第五十七轮 | 报告页有效性/科学性整改：表单 6 选项 request.args→request.values 全部生效、include_evaluation/include_recommendations 死开关接线、export_format/report_title 死选项实现、/report 接入最近导出报告闭环、IQR 按面内中位归一化无量纲化（防除零+报告文案）、新增 4 回归用例（90 测试全过） | 7项 |
| 第五十八轮 | 仪表盘最近评估记录重复：ctime 被统一触碰（19 报告同 ctime 21:55:47）致 10 条记录同时间戳。_list_filesystem_files 报告 created_at 优先解析文件名内嵌时间戳（YYYYMMDD_HHMMSS）回退 mtime（非 ctime），仪表盘最近记录/7日趋势/最近评估时间与 outputs 统计同步修正；新增 3 回归用例（93 测试全过） | 2项 |
| 第五十九轮 | 仪表盘全链路审查整改：评估转速回退监控推荐转速（新格式文件名无转速不再"未知"）、record_model_monitor 去重丢弃改存储全量（历史次数/转速变化检测失真）、最近记录查看/下载按钮接入具体报告（view_chart_html/download_file）、机型监控状态回退 outputs 文件时间（无监控记录误报超期）、KPI 重复语义修正（Top1 出现次数）、三图刷新按钮各自只刷对应图、model_monitor API 60s TTL 缓存 + dashboard 补 csrf_token；新增 3 回归用例（94 测试全过） | 5项 |
| **合计** | | **280项** |

---

## 项目架构

### 统一入口

- **唯一入口**: `wsgi.py` — 开发模式 `python wsgi.py`，生产模式 `gunicorn wsgi:application`
- **备用入口**: `app/__init__.py` — Flask 应用工厂
- **配置**: `config.py` — 统一配置常量

### 核心目录

```
/www/wwwroot/xiangxiantu/
├── wsgi.py                           # ★ WSGI入口（唯一启动文件）
├── config.py                         # 统一配置
├── machine_learning.py               # 机器学习预测/聚类/异常检测（根级，724行）
├── database_connections.py           # 数据库连接管理（模型+管理器+测试器）
├── data_processing.py                # 数据处理
├── chart_generation_optimized.py     # ★ 图表生成（10种图表 matplotlib PNG + Plotly HTML）
├── chart_style_config.py             # 图表样式配置（CHART_TYPE_CONFIG）
├── db_models.py                      # 数据库模型
├── gunicorn_conf.py                  # Gunicorn 配置
├── report_export.py                  # 报告导出兼容转发层（36行，无业务逻辑）
├── report_export_css.py              # ★ 报告导出CSS外部化模块（EXPORTER_CSS）
├── report_exporter_extension.py      # 报告导出扩展（兼容层）
├── services/                         # ★ 报告导出核心服务（第39-42轮重构）
│   ├── report_exporter.py            # ReportExporter核心 + HtmlExporter（第42轮拆分 ShareLinkManager）
│   ├── share_link_manager.py         # ★ ShareLinkManager 分享链接管理（第42轮新建）
│   ├── report_renderer.py            # ★ ReportRenderer（数据驱动HTML报告渲染）
│   ├── report_data_export.py         # ReportDataExporter（CSV/JSON/Excel）
│   ├── report_constants.py           # PLOTLY常量（CDN + 双轨脚本）
│   └── data_service.py               # 数据服务
├── app/
│   ├── __init__.py                   # Flask应用工厂（备用入口）
│   ├── services/
│   │   ├── project_statistics.py     # ★ 最优转速评分算法（核心，998行）
│   │   ├── data_analysis.py          # ★ 深度分析（趋势/异常/聚类/高级统计）
│   │   ├── skill_evaluation.py       # ★ 综合技能评估编排
│   │   ├── chart_generation.py       # 图表生成服务（弃用标注，指向根级 optimized 版）
│   │   ├── chart_plotly_renderer.py  # Plotly 图表渲染
│   │   ├── chart_matplotlib_renderer.py # Matplotlib 图表渲染
│   │   ├── chart_cache.py            # 图表缓存
│   │   ├── chart_utils.py            # 图表工具
│   │   ├── chart_fallback.py         # 图表回退
│   │   ├── connection_manager.py     # 连接管理
│   │   └── connection_tester.py      # 连接测试
│   └── utils/
│       ├── crypto_utils.py           # 密码加密/解密
│       ├── file_manager.py           # 文件管理
│       ├── error_handler.py          # 错误处理
│       ├── data_validator.py         # 数据验证
│       ├── chart_resource_manager.py # 图表资源管理
│       ├── cache_utils.py            # 缓存工具
│       └── api_response.py           # API统一响应类
├── blueprints/                       # Flask蓝图路由层
│   ├── main_bp.py                    # 首页/仪表盘/数据上传
│   ├── report_bp.py                  # 报告查看/分享
│   ├── ml_bp.py                      # 机器学习预测
│   ├── outputs_bp.py                 # 输出管理
│   ├── settings_bp.py                # 数据库连接配置
│   ├── database_bp.py                # 数据连接管理
│   └── analysis_bp.py                # 统一分析蓝图（深度分析+技能评估）
├── templates/                        # Jinja2 HTML模板 (14个)
├── static/
│   ├── js/                           # JavaScript (23个)
│   └── css/                          # CSS样式 (8个)
├── exporters/                        # 报告导出器（兼容）
├── models/                           # 数据模型
├── tests/                            # 测试文件 (18个)
└── outputs/                          # 导出报告输出目录
```

---

## 核心算法说明

### 1. 最优转速评分 (`project_statistics.py`)

三维度加权（IQR 40% + CV 40% + 幅值 20%），端面权重 P1=0.4 / P2=0.4 / ST=0.2（可配置 `DEFAULT_FACE_WEIGHTS`）。

幅值因子：`1/(1+|mean-median|/median)` — 抑制偏离中位数的转速。

### 2. 深度分析 (`app/services/data_analysis.py`)

- **趋势分析**: `_extract_numeric_x()` 解析4种转速格式 + 线性回归 + `_try_quadratic_fit()` 二次非线性检测
- **异常检测**: `_compute_z_scores()` — n≥8 D'Agostino-Pearson正态检验 → 标准Z-score；n<8 Modified Z-score(MAD×0.6745)；阈值2.5
- **聚类分析**: `_elbow_method()` 曲率法自动选K
- **CV统一**: 全链路百分比格式 `std/mean×100`

### 3. 技能评估 (`app/services/skill_evaluation.py`)

类常量体系：`CV_EXCELLENT=5.0`, `CV_GOOD=10.0`, `ANOMALY_FILTER_Z_THRESHOLD=2.5`, `MIN_SAMPLES_PER_SPEED=2`, `MIN_SPEED_COUNT=2` 等。

三维度数据质量评估（样本量+CV合格率+异常比），质量加分/异常惩罚。

---

## 安全性

| 措施 | 实现 |
|------|------|
| CSRF保护 | Flask-WTF 全局启用 |
| 密码加密 | Fernet(PBKDF2HMAC+SHA256)+Base64 (`crypto_utils.py`) |
| 加密盐值 | 环境变量CRYPTO_SALT + 内置回退（第12轮强化） |
| SECRET_KEY持久化 | 文件存储，权限600，多worker共享 |
| 生产异常脱敏 | error_type仅debug模式返回（第12轮修复） |
| 文件上传校验 | Magic bytes头验证防扩展名伪造（第12轮新增） |
| 原子文件写入 | temp+fsync+os.replace (`database_connections.py`) |
| LRU连接缓存 | 100条上限，逐出时主动close |
| 跨平台超时 | threading.Thread+join(timeout=10) |

---

## 代码约定

- **语言**: Python 3.8+，中文注释
- **风格**: PEP 8，4空格缩进
- **命名**: 函数/变量 snake_case，类 PascalCase
- **导入**: 标准库 → 第三方 → 本地模块，绝对导入
- **类型**: 关键模块需 typing 标注（`from typing import ...`）
- **日志**: 使用 `app.utils.error_handler` 中的 logger，不是 `print()`
- **无注释规则**: 不要无故添加注释——代码应自解释
- **Flask**: 蓝图注册在 `wsgi.py` 中完成，所有配置通过 `config.py` 统一管理
- **安全**: 绝对不要提交密钥/密码到仓库；配置文件密码必须加密存储

---

## 测试

```bash
python -m pytest tests/
```

- 测试文件位于 `tests/` 目录（18个）
- 核心算法修改后必须运行相关测试验证
- 语法检查: `python -c "import ast; ast.parse(open('file.py').read())"`
- 已知遗留失败: `test_data_processing.py`(1) + `test_data_validator.py`(2)，与报告导出链路无关

---

## 部署

### 开发模式
```bash
python wsgi.py
# 默认 0.0.0.0:1333
```

### 生产模式
```bash
gunicorn -w 4 -b 0.0.0.0:1333 wsgi:application
```

### 环境变量
| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SECRET_KEY` | 自动生成并持久化 | Flask密钥 |
| `CRYPTO_SALT` | xiangxiantu_fan_balance | 密码加密盐值（第12轮新增） |
| `PORT` | 1333 | 监听端口 |
| `DEBUG` | false | 调试模式 |
| `UPLOAD_FOLDER` | uploads | 上传目录 |
| `MAX_CONTENT_LENGTH` | 16777216 | 最大上传(16MB) |

---

## 已知问题与待改进项

### 本月内（优先级高）
1. ~~迁移 `project_statistics.py` 到 `app/services/`~~ ✅ 第十二轮已确认：实际代码已在 `app/services/project_statistics.py`(998行)，根目录为兼容shim
2. ~~拆分 `database_connections.py`（模型/管理器/测试器分离）~~ ✅ 已完成：现为42行兼容shim，逻辑已迁至 `app/models/db_connection_config.py` + `app/services/connection_manager.py` + `app/services/connection_tester.py`
3. ~~添加 `ApiResponse` 统一响应封装类~~ ✅ 第十二轮已创建 `app/utils/api_response.py`
4. ~~生产环境异常信息脱敏~~ ✅ 第十二轮已修复：`error_type` 仅debug模式返回
5. ~~`services/report_exporter.py` 已达 400 行上限~~ ✅ 第四十二轮已拆分：ShareLinkManager 独立至 `services/share_link_manager.py`，有效代码 400→329 行（82%）
6. ~~修复 `tests/test_data_processing.py::test_parse_single_surface_file_empty` + `tests/test_data_validator.py` 2 用例~~ ✅ 第四十二轮已清零：空文件检测抛 `ValueError("文件内容为空")`（两副本），`test_data_validator` 对齐当前 API；全量 **64 passed**

### 下月内（优先级中）
7. 集成 `python-dotenv` 环境变量管理
8. 添加 `ruff` + `black` + `mypy` 自动化代码检查
9. 添加 `flask-limiter` API 速率限制
10. ~~`html_exporter.py` CSS 外部化~~ ✅ 第十二轮已创建 `report_export_css.py`（web端+exporter CSS全外部化）

### 已确认修复验证通过
- ✅ 246/246 项修复全部确认有效（48轮审查验证，详见上方累计表）
- 第四十八轮：报告图表加载初期横向溢出 — 1项 ✅ 浏览器实测通过（加载全程 scrollWidth=clientWidth，SVG 与容器严格等宽）
- 第四十七轮：堆叠显示图表右侧空白 — 1项 ✅ 浏览器实测通过（右侧空白 16.8%→1.22%）
- 第四十六轮：默认Y轴对齐 — 4项 ✅ 全部有效（首页自动对齐 + 报告双轨交互图统一量程，14+ 测试通过 + 报告 SMOKE_PASS）
- 第四十五轮：导出报告全维度审查整改 — 8项 ✅ 全部有效（73 测试全通过 + 线上 POST/CSRF/405 实测通过 + 浏览器回归验收通过）
- 第四十四轮：报告导出链路 + 重置CSRF全链路收尾 — 4项 ✅ 全部有效（17:39 真实导出报告含全部修复）
- 第四十三轮：报告与前端三差异对齐 + 图表缓存跨目录修复 — 7项 ✅ 全部有效

---

## 文档

| 文件 | 用途 |
|------|------|
| [README.md](file:///www/wwwroot/xiangxiantu/README.md) | 项目介绍与API文档 |
| [REPAIR_REPORT.md](file:///www/wwwroot/xiangxiantu/REPAIR_REPORT.md) | 修复报告 ~57项 |
| [OPTIMIZATION_SUMMARY.md](file:///www/wwwroot/xiangxiantu/OPTIMIZATION_SUMMARY.md) | 优化详情 |
| [CLAUDE.md](file:///www/wwwroot/xiangxiantu/CLAUDE.md) | Claude专用上下文 |
