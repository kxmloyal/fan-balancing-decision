# ML 历史数据导入 — 设计方案

**日期**：2026-05-20
**状态**：已审批
**方案**：A — 型号选择器 + 自动格式转换

---

## 1. 问题

ML 页面（`/ml`）4 个面板当前仅支持手动粘贴 JSON 或加载硬编码 SAMPLE_DATA，无法使用系统已上传的历史数据。用户需要：
- 从系统数据库导入已分析型号的历史数据
- 支持外部 JSON/CSV 文件导入

## 2. 架构

新增 3 个模块，改动 4 个现有文件：

```
ml.html           ← 新增数据源栏（型号下拉 + 端面选择 + 文件上传）
ml.js             ← 新增型号加载/面板填充/文件解析逻辑
ml_bp.py          ← 新增 2 个 API
ml_data_adapter.py ← 新文件：格式转换模块
ml.css            ← 新增数据源栏样式
```

不改动：现有 textarea 逻辑、4 个面板的 API、SAMPLE_DATA、"填充示例"按钮。

## 3. 数据流

```
用户选型号 "SN300-12"
  → GET /api/ml/models              → 返回型号列表
  → GET /api/ml/model_data/SN300-12 → 返回原始数据 + 统计
    → ml_data_adapter.to_xxx_format(data, face) → 转换
      → 填入当前面板 textarea
        → 用户审阅/编辑 → 点"开始分析"
```

## 4. API 设计

### 4.1 GET `/api/ml/models`

返回系统数据库中已分析过的所有型号列表。

**响应**：
```json
{
  "success": true,
  "models": [
    {"fan_model": "SN300-12", "record_count": 24, "last_analysis": "2026-05-15", "speeds": 8},
    {"fan_model": "SN400-05", "record_count": 18, "last_analysis": "2026-05-10", "speeds": 6}
  ]
}
```

**数据来源**：`analysis_results` + `upload_files` 表，按 fan_model 分组聚合。

**错误处理**：
- 数据库未连接 → `{"success": false, "error": "数据库未连接"}`
- 无数据 → `{"success": true, "models": []}`

### 4.2 GET `/api/ml/model_data/<fan_model>`

返回指定型号的完整原始数据，供前端转换。

**响应**：
```json
{
  "success": true,
  "fan_model": "SN300-12",
  "speeds": ["800rpm","1000rpm","1200rpm","1500rpm","1800rpm","2000rpm","2200rpm","2500rpm"],
  "faces": {
    "P1": {"800rpm": [0.12,0.11,0.13], "1000rpm": [0.15,0.16], "1200rpm": [...]},
    "P2": {"800rpm": [0.08,0.09,0.10], "1000rpm": [0.10,0.11], "1200rpm": [...]},
    "ST": {"800rpm": [0.21,0.22], "1000rpm": [0.24,0.25], "1200rpm": [...]}
  },
  "stats": {
    "record_count": 24,
    "total_speeds": 8,
    "faces_available": ["P1","P2","ST"],
    "min_speed": "800rpm",
    "max_speed": "2500rpm"
  }
}
```

**数据来源**：从 `analysis_results` 找到该型号所有记录 → 读原始 CSV/Excel → `parse_single_surface_file` 解析 → 按 speed 聚合各端面样本值数组。

**性能考虑**：同一型号数据缓存 60 秒（`functools.lru_cache`）。

## 5. 格式转换规则

### 5.1 趋势预测 / 异常检测

转换函数：`to_trend_format(data, face="P1")`

```
输入: 原始数据 + 端面选择
输出: [{"date":"800rpm","value":0.120},{"date":"1000rpm","value":0.155},...]

规则: 对每个 speed, value = mean(该speed下选定面的所有样本)
```

端面可通过数据源栏的端面选择器切换（P1/P2/ST）。

### 5.2 关键指标预测

转换函数：`to_metrics_format(data)`

```
输出: [{"date":"800rpm","p1_mean":0.120,"p2_mean":0.090,"st_mean":0.220,
        "p1_cv":5.2,"p2_cv":4.8,"st_cv":6.1,
        "p1_max":0.130,"p2_max":0.100,"st_max":0.250,"total":0.262},...]

指标定义:
  p{N}_mean = mean(该面该speed样本)
  p{N}_cv   = std/mean*100
  p{N}_max  = max(该面该speed样本)
  total     = sqrt(p1_mean² + p2_mean²)   (P1+P2合成,不含ST)
```

注：total 为动平衡常用合成量 `√(P1²+P2²)`，ST 单独列出不参与合成（ST 是轴端面，物理含义不同）。

### 5.3 多维度分析

转换函数：`to_multi_format(data)`

```
输出: [{"speed":"800rpm","p1_amplitude":0.120,"p2_amplitude":0.090,
        "st_amplitude":0.220,"p1_p2_ratio":1.333,"p1_std":0.010,
        "p2_std":0.008,"st_std":0.015},...]

维度定义:
  p{N}_amplitude = mean(该面该speed样本)
  p1_p2_ratio    = p1_mean / p2_mean
  p{N}_std       = std(该面该speed样本)
```

## 6. UI 组件

### 6.1 数据源栏（Hero 与 Tab 之间）

```
┌─ 数据源 ─────────────────────────────────────────────┐
│ 📦 型号: [SN300-12 ▼]  端面: [P1 ▼]  🔄 刷新  │ 📁 │
│ 共 24 条记录 | P1面 8个转速 | P2面 8个转速 | ST面 8个转速 │
└──────────────────────────────────────────────────────┘
```

**端面选择器**：仅在趋势预测/异常检测面板显示，关键指标/多维度面板隐藏。

**📁 按钮**：触发隐藏的 `<input type="file" accept=".json,.csv">`，选中后前端读取 FileReader → 解析 JSON（或 CSV→JSON）→ 填入 textarea。

### 6.2 状态处理

| 状态 | UI 表现 |
|------|--------|
| 数据库无连接 | 型号下拉置灰 + tooltip "数据库未连接，请先在设置中配置" |
| 型号列表为空 | 下拉显示 "暂无历史数据" |
| API 加载中 | 型号下拉右侧 spinner 动画 |
| 加载失败 | toast 错误提示 + 自动回退到手填模式 |
| 数据库中无该型号原始文件 | toast "该型号原始数据文件缺失，无法加载" |

## 7. 文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `ml_bp.py` | 修改 | 新增 `/api/ml/models`、`/api/ml/model_data/<fan_model>` |
| `ml_data_adapter.py` | **新建** | `to_trend_format()`, `to_metrics_format()`, `to_multi_format()` |
| `ml.html` | 修改 | 新增数据源栏 HTML（型号下拉+端面选择+文件上传+数据摘要） |
| `ml.js` | 修改 | 新增 `loadModels()`, `onModelSelect()`, `file upload`, `fillPanel()` |
| `ml.css` | 修改 | 新增 `.ml-datasource` 栏样式 |
| `data_processing.py` | 修改 | 新增 `get_model_history_data(fan_model)` 聚合查询函数 |

## 8. 兼容性

- 现有 textarea 逻辑**完全保留**，型号选择器仅做填充动作
- "填充示例"按钮优先级低于型号数据（填示例会覆盖型号数据，符合预期）
- 如果用户手动修改 textarea 后切型号，**覆盖用户编辑**（有 toast 提示）
- 数据库不可用时，整个数据源栏自动隐藏，UX 退化为当前纯手填模式

## 9. 安全性

- `fan_model` 参数做 SQL 注入防护（参数化查询）
- 文件上传校验扩展名（`.json`, `.csv`）
- 文件大小限制 1MB（前端限制，后端 `MAX_PAYLOAD_SIZE` 已有 1MB 限制）
- CSRF token 沿用现有机制