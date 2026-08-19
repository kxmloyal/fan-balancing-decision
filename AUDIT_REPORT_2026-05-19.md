# 三省六部全维度审计报告 — 2026-05-19

> **审计范围**：全项目 7 个蓝图 + 12 个模板 + 47 个 JS/CSS 文件 + 20+ Python 模块  
> **审计 Agent**：6 路并行（中书省/吏部/户部/礼部/兵部/刑部+工部）  
> **审计轮次**：第 42 轮  

---

## 一、综合评分

| 部门 | 维度 | 评分 | 问题数 | P0 | P1 | P2 |
|------|------|------|--------|----|----|-----|
| 中书省 | 架构设计 | 7.0 | 10 | 2 | 4 | 4 |
| 吏部 | 代码质量 | 4.7 | 24 | 7 | 5 | 12 |
| 户部 | 数据流 | 6.2 | 14 | 2 | 7 | 5 |
| 礼部 | UI/UX | 6.5 | 18 | 3 | 10 | 5 |
| 兵部 | 交互性 | 7.0 | 22 | 6 | 7 | 9 |
| 刑部 | 安全 | 6.0 | 10 | 1 | 1 | 8 |
| 工部 | 算法 | 7.5 | 4 | 0 | 0 | 4 |
| **加权** | **综合** | **6.34** | **102** | **21** | **34** | **47** |

> **评议**：项目经 219 项累计修复后整体可用性良好（8 模块皆 200），但深水区问题开始浮现——架构层面 main_bp.py 膨胀、数据层面双配置系统分裂、代码质量层面 489 行死码 + 443 处 var 残留、安全层面 5 处 XSS 注入点 + 上传校验缺失。建议分 3 个迭代周期逐步消化。

---

## 二、各部门详情

### 中书省 — 架构设计（7.0/10）⭐ 较上轮 +0.5

**✅ 良好项**：
- 蓝图注册 7/7 全覆盖，无死蓝图残留
- 循环导入已解决（services/ 独立于 app/ 包外）
- 模块化注册 + 配置外部化已完成（第 29/30 轮）

**🔴 P0（2 项）**：
| # | 问题 | 文件 |
|---|------|------|
| A1 | main_bp.py 22 import + 三套路径混用（重耦合） | `blueprints/main_bp.py` |
| A2 | utils/ vs services/ 双路径分裂，6 文件使用三种路径组合 | 多个文件 |

**🟡 P1（4 项）**：
| # | 问题 | 文件 |
|---|------|------|
| A3 | settings_bp.py 路由函数数膨胀至 22 个 | `blueprints/settings_bp.py` |
| A4 | 根目录 .py 文件 8 个，职责划分不清晰 | 根目录 |
| A5 | wsgi.py 职责过多（初始化+scheduler+cleanup+中间件） | `wsgi.py` |
| A6 | tests/ 目录 34 文件但覆盖未知 | `tests/` |

### 吏部 — 代码质量（4.7/10）🔴 较上轮 −2.3

**✅ 良好项**：
- Python print() 已全量清理（仅 1 处测试文件残留）
- JS console.log 已全量注释化（0 处活跃）
- Module docstring 覆盖率 100%（app/services/）

**🔴 P0（7 项）**：
| # | 问题 | 文件 |
|---|------|------|
| B1 | statistics.py 整文件 489 行死代码 | `app/services/statistics.py` |
| B2 | CHART_TYPE_CONFIG 4 处重复定义 | 4 个文件 |
| B3 | data_processing.py 双份文件（根级 + app/services/） | 2 个文件 |
| B4 | project_statistics.py 与 statistics.py 函数名冲突 | 2 个文件 |
| B5 | outputs_bp.py 核心路由全无 docstring | `blueprints/outputs_bp.py` |
| B6 | SystemLog 死模型（6 个模型中唯一 0 处写入） | `db_models.py` |
| B7 | 蓝图层 type hints 覆盖率 <5% | 6 个蓝图文件 |

**🟡 P1（5 项）**：
| # | 问题 | 文件 |
|---|------|------|
| B8 | 443 处 var 残留（11 个 JS 文件） | `static/js/*.js` |
| B9 | settings_bp.py 10+ 路由缺 docstring | `blueprints/settings_bp.py` |
| B10 | main_bp.py 8+ 路由缺 docstring | `blueprints/main_bp.py` |
| B11 | analysis_bp.py 12+ 路由缺 docstring | `blueprints/analysis_bp.py` |
| B12 | chart_generation 双文件重复功能 | 2 个文件 |

### 户部 — 数据流（6.2/10）

**🔴 P0（2 项）**：
| # | 问题 | 文件 |
|---|------|------|
| C1 | settings_bp.py 3 处 db.session.commit() 异常后不 rollback | `blueprints/settings_bp.py` L450/L489/L505 |
| C2 | Session 文件目录权限问题（flask_session_new/ 多 worker 冲突） | `wsgi.py` L116 |

**🔴 P1（7 项）**：
| # | 问题 | 文件 |
|---|------|------|
| C3 | config/db_config.json 与 data/connection_configs.json 双文件重叠存储凭证 | 2 个文件 |
| C4 | _base64_cache 无上限无 TTL，长时间运行 OOM | `services/report_exporter.py` L386 |
| C5 | statistics.py 4 处 open('w') 无异常处理 | `app/services/statistics.py` |
| C6 | chart_generation_optimized.py SVG 写入无异常处理 | L1383 |
| C7 | Session 大数据（含 base64 图表）存入 session → 文件缓存永不过期 | `main_bp.py` L80 |
| C8 | PDF 导出未记录到 export_history | `report_bp.py` L152 |
| C9 | 双配置系统使用不同加密方案（crypto_utils vs Fernet） | 2 个文件 |

### 礼部 — UI/UX（6.5/10）

**🔴 P0（3 项）**：
| # | 问题 | 文件 |
|---|------|------|
| D1 | skill_evaluation.html 内嵌 ~520 行 CSS + 210 行 JS | 模板 |
| D2 | in_depth_analysis.html 内嵌 ~200 行 CSS | 模板 |
| D3 | ml.html 缺少 ml.css 引用 | 模板 |

**🟡 P1（10 项）**：
| # | 问题 |
|---|------|
| D4 | 10/12 模板 script 标签无 defer，阻塞 HTML 解析 |
| D5 | 2 个 CSS 文件未在任何模板引用（dead-css） |
| D6 | 2 个 JS 文件未引用（dead-js） |
| D7 | dark mode 块缺 navbar 颜色覆盖 |
| D8 | 52 处 CSS 硬编码颜色未令牌化 |
| D9 | 移动端 4 页面无触控优化 |
| D10 | CDN 引用 2 处（ECharts + Plotly HTML 报告内） |
| D11 | 2 个模板 <style> 内嵌 CSS 未外部化 |
| D12 | 2 个模板 <script> 内嵌 JS 未外部化 |
| D13 | fonts/ 目录缺失 |

### 兵部 — 交互性（7.0/10）

**🔴 P0（6 项）**：
| # | 问题 | 文件 |
|---|------|------|
| E1 | modal-manager.js error.message 未转义 → XSS | L265-L274 |
| E2 | settings.js showToast message 未转义 → XSS | L22 |
| E3 | toast-helper.js showToast message 未转义 → XSS | L15 |
| E4 | skill_evaluation.html showToast message 未转义 → XSS | L719 |
| E5 | skill_evaluation.html rec.text 未转义 → XSS | L645 |
| E6 | upload.js 文件上传无前端类型/大小校验 | L35-L80 |

**🟡 P1（7 项）**：
| # | 问题 |
|---|------|
| E7 | dashboard.js 按钮加载态 setTimeout 2500ms 硬编码恢复 |
| E8 | ml.js 5 处 NaN 上调用 .toFixed() 无保护 |
| E9 | in_depth_analysis_enhanced.js toFixed NaN 不拦截 |
| E10 | settings.js setInterval 30s 轮询从未 clearInterval |
| E11 | simple-plotly-manager.js setInterval 依赖外部 destroy |
| E12 | 仅 outputs.js 支持键盘快捷键 |
| E13 | 自定义 :focus-visible 样式缺失 |

### 刑部 — 安全（6.0/10）

**🔴 P0（1 项）**：
| # | 问题 | 文件 |
|---|------|------|
| F1 | 文件上传 handler 有 magic_bytes 函数但未调用 | `data_processing.py` |

**🟡 P1（1 项）**：
| # | 问题 | 文件 |
|---|------|------|
| F2 | balance_machine_model 字段无验证，潜在存储型 XSS | `main_bp.py` |

**🟢 P2（8 项）**：
- bcrypt 替代 XOR 加密（crypto_utils.py）
- flask-limiter 速率限制校验
- 日志脱敏增强
- 密码复杂度要求
- CORS 策略

### 工部 — 算法科学（7.5/10）

**🟢 P2（4 项）**：
| # | 问题 |
|---|------|
| G1 | skill_evaluation 无多重比较校正（Bonferroni） |
| G2 | KMeans 聚类无 silhouette_score 自动化最优 K |
| G3 | 正态性检验功效分析未标注 |
| G4 | 小样本 D'Agostino-Pearson 检验功效不足（n<8 应强制 MAD） |

---

## 三、汇总：102 项问题的优先级分布

| 等级 | 数量 | 占比 | 说明 |
|------|------|------|------|
| 🔴 P0 | 21 | 20.6% | 阻断性：功能不可用 / XSS / 数据丢失 |
| 🟡 P1 | 34 | 33.3% | 高影响：安全 / 数据一致性 / 架构债务 |
| 🟢 P2 | 47 | 46.1% | 工程健壮性：质量 / 体验 / 可维护性 |

---

## 四、升级迭代方案路线

### 方案一：安全优先（🛡️ 保守稳健）⭐⭐⭐ 推荐

```
第42轮 (P0安全+XSS) → 第43轮 (P0数据完整性) → 第44轮 (P1安全) → 第45轮 (P2收尾)
```

| 轮次 | 焦点 | 问题数 | 预计变更 |
|------|------|--------|----------|
| **第42轮** | 🔴 P0 安全 + XSS | 8 项 | 5 处 XSS 修复、上传校验、rollback 补齐、3 模块外部化 |
| **第43轮** | 🔴 P0 数据完整性 | 7 项 | Session 权限、双配置合并、缓存限制、PDF 历史 |
| **第44轮** | 🟡 P0 架构清理 | 6 项 | 死码删除、数据合并、docstring 补齐 |
| **第45轮** | 🟡 P1 全部 | 34 项 | var→let/const、硬编码令牌化、defer、docstring、NaN 保护 |
| **第46轮** | 🟢 P2 全部 | 47 项 | CSS 令牌化、type hints、dark mode、算法增强 |

**优点**：风险最低，每轮纯增量，可随时中止  
**缺点**：5 轮完成，周期较长  

---

### 方案二：快速修复（⚡ 激进冲刺）

```
第42轮 (全部P0 21项) → 第43轮 (全部P1 34项) → 第44轮 (全部P2 47项)
```

| 轮次 | 焦点 | 问题数 |
|------|------|--------|
| **第42轮** | 🔴 全部 P0 | 21 项 |
| **第43轮** | 🟡 全部 P1 | 34 项 |
| **第44轮** | 🟢 全部 P2 | 47 项 |

**优点**：3 轮完成，周期短  
**缺点**：单轮改动量大（21 项），回归风险较高  

---

### 方案三：模块聚焦（🎯 按功能模块）

```
第42轮 (设置+安全模块) → 第43轮 (仪表盘+首页模块) → 第44轮 (报告+ML模块) → 第45轮 (分析+评估模块)
```

| 轮次 | 模块 | 涵盖问题 |
|------|------|----------|
| **第42轮** | 设置 + 安全加固 | XSS(5) + 上传(2) + rollback(3) + 双配置(2) + 死模型(1) = 13 项 |
| **第43轮** | 首页 + 仪表盘 | main_bp 重耦合 + docstring + 数据完整性(7) = 10 项 |
| **第44轮** | 报告 + ML + 输出管理 | 死代码(4) + 缓存(3) + PDF历史(2) + docstring(5) = 14 项 |
| **第45轮** | 深入分析 + 技能评估 + 全局收尾 | 外部化(3) + var→let(1) + type hints(1) + P2(47) |

**优点**：每次聚焦单一模块，测试范围可控  
**缺点**：跨模块问题（如重复配置）需多轮处理  

---

## 五、actionable summary

### 本次审计确认无问题的维度 ✅

- ✅ CSRF 保护全链路完整（所有 POST 路由 + fetch 头 + 模板 token）
- ✅ SQL 注入防护（仅 1 处参数化 execute 调用，无动态拼接）
- ✅ 路径穿越防护（所有 send_from_directory 有 normpath + startswith("..") 检查）
- ✅ Python print() 已全面清理（仅 1 处测试文件残留）
- ✅ JS console.log 已全面注释化（0 处活跃）
- ✅ 蓝图注册 7/7 全覆盖，0 死蓝图
- ✅ 核心算法（IQR/CV/Z-score 计算、权重归一化）正确
- ✅ Module docstring 覆盖率 100%
- ✅ fetch .catch() 覆盖率 100%

### 累计修复全景

| 里程碑 | 轮次 | 修复项 | 说明 |
|--------|------|--------|------|
| 项目启动 | 1-38 | 186 | 功能开发 + 早期修复 |
| 全维度审计 P0 | 39 | 5 | ML页面重构 + CSRF + 校验 |
| 全维度审计 P1 | 40 | 9 | 异常处理 + 死代码 + UI 优化 |
| 全维度审计 P2 | 41 | 14 | 死码清理 + var/let + 架构拆分 |
| **本次审计** | **42** | **0→102** | **三省六部 6 路 Agent 全项目审计** |
| **累计** | **1-41** | **219** | **已修复项** |

---

*报告由三省六部 Agent 系统自动生成*  
*2026-05-19 — 第 42 轮审计*
