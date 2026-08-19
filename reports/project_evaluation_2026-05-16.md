# 扇叶动平衡补土工艺决策支持系统 — 全维度评估报告

**评估日期**：2026-05-16
**评估框架**：三省六部式代码审查 + 五轴质量评审
**评估范围**：全项目源码（55 个 Python 文件 / 29 个 HTML 模板 / 752 个 JS / 17 个 CSS）
**代码规模**：~17,754 行 Python + ~102,497 行 JS + ~103,523 行 HTML + ~6,090 行 CSS

---

## 一、中书省 — 架构设计评审

### 1.1 项目结构总览

```
xiangxiantu/
├── wsgi.py                         # ★ WSGI唯一入口
├── config.py                       # 统一配置
├── machine_learning.py             # ML预测+异常检测+聚类 (724行)
├── chart_generation_optimized.py   # 图表生成优化（主要）
├── chart_style_config.py           # 图表样式配置
├── database_connections.py         # DB连接管理
├── db_models.py                    # DB模型
├── data_processing.py              # 数据处理（根目录shim）
├── project_statistics.py           # 最优转速评分（shim→app/services/）
├── report_export.py                # 报告导出
├── report_export_css.py            # 报告导出CSS外部化
├── report_exporter_extension.py    # 报告导出扩展
├── app/
│   ├── __init__.py                 # Flask应用工厂（备用）
│   ├── services/                   # ★ 核心服务层
│   │   ├── __init__.py             # 桶导出（含错误导入）
│   │   ├── chart_generation.py     # 图表生成（已废弃）
│   │   ├── data_analysis.py        # 深度分析（621行）
│   │   ├── data_processing.py      # 数据处理
│   │   ├── project_statistics.py   # 最优转速算法（998行）
│   │   ├── skill_evaluation.py     # 技能评估（835行）
│   │   └── statistics.py           # 统计服务（含重复算法）
│   └── utils/                      # ★ 工具层
│       ├── api_response.py         # 统一响应
│       ├── config_manager.py       # 配置管理
│       ├── crypto_utils.py         # ⚠️ 密码加密（含硬编码密钥）
│       ├── data_validator.py       # 数据验证
│       ├── error_handler.py        # 错误处理
│       └── file_manager.py         # 文件管理
├── blueprints/                     # ★ Flask蓝图路由层
│   ├── __init__.py                 # 桶导出（含死码引用）
│   ├── main_bp.py                  # 首页/仪表盘（1272行，最大蓝图）
│   ├── report_bp.py                # 报告查看
│   ├── ml_bp.py                    # ML预测
│   ├── outputs_bp.py               # 输出管理
│   ├── settings_bp.py              # 数据库配置
│   ├── database_bp.py              # ⚠️ 死码shim（2行）
│   └── analysis_bp.py              # 深度分析+技能评估（571行，路由重复）
├── services/                       # ⚠️ 根级重复services
│   └── data_service.py
├── utils/                          # ⚠️ 根级重复utils（6个文件）
├── exporters/                      # 报告导出器
├── models/                         # 数据模型
├── tests/                          # 34个测试文件
├── static/                         # 前端资源（752 JS + 17 CSS）
└── templates/                      # Jinja2模板（29个）
```

### 1.2 架构评分：6.5/10

| 维度 | 评分 | 说明 |
|------|------|------|
| 模块边界 | 5.0 | 根级文件与 `app/services/` 并存，`services/` 与 `app/services/` 重复 |
| 导入链路 | 6.0 | 桶导出（`__init__.py`）导入错误的 `statistics.py` 版本 |
| 代码组织 | 7.0 | 蓝图分层清晰，核心算法独立模块化 |
| 扩展性 | 7.5 | 蓝图注册函数化，设计令牌系统较完备 |
| 死码管理 | 4.5 | 存在 shim 文件 `database_bp.py`、废弃 `chart_generation.py`、根级重复目录 |

### 1.3 架构层面发现问题

| ID | 优先级 | 问题 | 位置 | 说明 |
|----|--------|------|------|------|
| A1 | P1 | 死码shim蓝图 | [database_bp.py](file:///www/wwwroot/xiangxiantu/blueprints/database_bp.py) | 2行文件仅做 `from blueprints.settings_bp import settings_bp as database_bp`，仍在 `__init__.py` 桶导出中 |
| A2 | P1 | 算法双重实现 | [statistics.py](file:///www/wwwroot/xiangxiantu/app/services/statistics.py) vs [project_statistics.py](file:///www/wwwroot/xiangxiantu/app/services/project_statistics.py) | `calculate_optimal_speed_evaluation` 存在两个版本：statistics.py（5因子中位数/标准差/CV/数据量/ST奖励）vs project_statistics.py（3D IQR/CV/幅值）。`__init__.py` 桶导出错误指向 5 因子版本 |
| A3 | P1 | 根级重复目录 | `services/` `utils/` vs `app/services/` `app/utils/` | 两套目录并存（7个重复文件），架构混乱 |
| A4 | P2 | 废弃模块仍被导出 | [chart_generation.py](file:///www/wwwroot/xiangxiantu/app/services/chart_generation.py) | docstring 标注"已废弃，由 chart_generation_optimized.py 取代"，但仍在 `app/services/__init__.py` 桶导出中 |
| A5 | P2 | sys.path 运行时修改 | [analysis_bp.py:L17](file:///www/wwwroot/xiangxiantu/blueprints/analysis_bp.py#L17) | `sys.path.insert(0, ...)` 污染全局模块搜索路径 |
| A6 | P2 | 路由端点重复注册 | [analysis_bp.py](file:///www/wwwroot/xiangxiantu/blueprints/analysis_bp.py#L60-L304) | 每对端点（如 `/api/skill-evaluation/evaluate` 和 `/api/in-depth-analysis/evaluate`）共享相同 `_handle_*()` 实现，重复 10 对 |

---

## 二、尚书省 — 跨维度交叉影响分析

### 2.1 安全 × 架构交叉风险

最严重的架构-安全交叉点：

```
crypto_utils.py (hardcoded salt/key)
    → ConfigManager.encrypt_db_password()
    → 所有数据库密码可被源码阅读者解密
    → 生产环境数据库暴露风险
```

```
main_bp.py (pickle session cache)
    → session缓存写入 outputs/.session_cache/
    → 如攻击者能写入该目录 → pickle.load() 反序列化 → RCE
```

### 2.2 算法 × 数据流交叉风险

```
machine_learning.py predict_trend (lag order bug)
    → 模型训练时特征顺序 [lag_1, lag_2, lag_3]
    → 预测时 last_values = tail(3) = [v_{t-2}, v_{t-1}, v_t]
    → 实际作为 [v_{t-2}(→lag_1), v_{t-1}(→lag_2), v_t(→lag_3)]
    → 训练时 lag_1 = 最近值，预测时 lag_1 = 最远值
    → 滚动多步预测全部偏差
```

---

## 三、六部 — 专项评审

### 3.1 吏部 — 代码质量评审 [7.0/10]

| ID | 优先级 | 问题 | 文件 | 行号 |
|----|--------|------|------|------|
| Q1 | P2 | 变量名遮蔽 | [machine_learning.py](file:///www/wwwroot/xiangxiantu/machine_learning.py#L366-L368) | `metrics` 在内层作用域被覆盖 |
| Q2 | P2 | scipy.stats 双重导入 | [data_analysis.py](file:///www/wwwroot/xiangxiantu/app/services/data_analysis.py#L14,L29) | 模块级 + `__init__` 级两次 `import scipy.stats` |
| Q3 | P2 | 死参数 y_mean | [data_analysis.py:L390](file:///www/wwwroot/xiangxiantu/app/services/data_analysis.py#L390) | `_try_quadratic_fit` 参数 `y_mean` 从未在函数体中使用 |
| Q4 | P2 | 裸 except Exception | [project_statistics.py:L25](file:///www/wwwroot/xiangxiantu/app/services/project_statistics.py#L25) | `_load_face_weights()` 中 `except Exception: return dict(...)` 吞没所有异常 |
| Q5 | P2 | 裸 except | [skill_evaluation.py:L211](file:///www/wwwroot/xiangxiantu/app/services/skill_evaluation.py#L211) | `_filter_by_data_quality` `except (ZeroDivisionError, Exception)` 过宽 |
| Q6 | P2 | 统计值过早字符串化 | [project_statistics.py:L72-L81](file:///www/wwwroot/xiangxiantu/app/services/project_statistics.py#L72-L81) | `calculate_surface_stats` 返回 Dict[str,str]，下游所有函数强制 `float()` 回转换 |

### 3.2 户部 — 数据流评审 [6.5/10]

| ID | 优先级 | 问题 | 文件 | 说明 |
|----|--------|------|------|------|
| D1 | P1 | 跨面样本混合计数 | [skill_evaluation.py:L119-L145](file:///www/wwwroot/xiangxiantu/app/services/skill_evaluation.py#L119-L145) | `_validate_data_sufficiency()` 将 P1+P2+ST 三面样本求和，单面 <2 时不出错 |
| D2 | P1 | dropna() 后空 df 未保护 | [machine_learning.py:L182-L186](file:///www/wwwroot/xiangxiantu/machine_learning.py#L182-L186) | lag 特征 join + dropna() 后 df 为空 → `df["value"].mean()` = NaN → 所有预测 NaN |
| D3 | P1 | CV 精确零值比较 | [project_statistics.py:L67](file:///www/wwwroot/xiangxiantu/app/services/project_statistics.py#L67) | `mean_val != 0` 精确比较应改用 `abs(mean_val) < epsilon` |
| D4 | P1 | 技能分仅取最高转速 | [skill_evaluation.py:L531](file:///www/wwwroot/xiangxiantu/app/services/skill_evaluation.py#L531) | `max(valid_scores)` 仅统计最佳转速得分，不反映整体工艺质量 |
| D5 | P1 | 统计计算重复实现 | [skill_evaluation.py:L326-L409](file:///www/wwwroot/xiangxiantu/app/services/skill_evaluation.py#L326-L409) | `_evaluate_optimal_speed` 重复 project_statistics.py 已有的统计计算逻辑 |

### 3.3 礼部 — UI/UX 评审 [7.5/10]

前端整体质量良好，第19-27轮重设计奠定了设计令牌体系。主要残余问题：

| ID | 优先级 | 问题 | 文件 |
|----|--------|------|------|
| U1 | P1 | 内联样式残留 | [dashboard.html](file:///www/wwwroot/xiangxiantu/templates/dashboard.html) | ~80行内联 `<style>` 含硬编码颜色 `#0d6efd` |
| U2 | P1 | :root 覆盖 | [in_depth_analysis.html](file:///www/wwwroot/xiangxiantu/templates/in_depth_analysis.html) | 内联 `:root` 块覆盖全局设计令牌 |
| U3 | P1 | 零设计令牌CSS | [upload.css](file:///www/wwwroot/xiangxiantu/static/css/upload.css) | 全文无 `var(--*)` 引用，颜色硬编码 |
| U4 | P1 | 缺失style.css | [404.html](file:///www/wwwroot/xiangxiantu/templates/404.html) | 错误页面未加载主样式表 |
| U5 | P2 | CSS重复块 | [style.css](file:///www/wwwroot/xiangxiantu/static/css/style.css) | 存在重复CSS规则块 |
| U6 | P2 | 超大JS文件 | [simple-plotly-manager.js](file:///www/wwwroot/xiangxiantu/static/js/simple-plotly-manager.js) | 2,134行，职责混杂 |

### 3.4 兵部 — 交互性评审 [7.5/10]

交互体系较成熟（Toast通知/safeFetch CSRF/模态管理器）。主要残余问题：

| ID | 优先级 | 问题 | 文件 | 行号 |
|----|--------|------|------|------|
| I1 | P1 | debounce() 4处重复定义 | 4个JS文件 | 相同的防抖函数分散定义 |
| I2 | P2 | 419处硬编码颜色残留 | navbar.html + chart_macros.html等 | 早期模板未迁移到设计令牌 |

### 3.5 刑部 — 安全评审 [5.0/10]

> ⚠️ **安全评分最低维度，存在2个可远程利用的严重漏洞。**

#### CRITICAL

| ID | 漏洞 | 文件 | 行号 | CVSS估值 |
|----|------|------|------|----------|
| S1 | **Pickle 反序列化 RCE** | [main_bp.py](file:///www/wwwroot/xiangxiantu/blueprints/main_bp.py#L66-L84) | L66-84 | 8.1 (HIGH) |
| S2 | **硬编码密码学密钥** | [crypto_utils.py](file:///www/wwwroot/xiangxiantu/app/utils/crypto_utils.py#L13,L27,L29) | L13, L27, L29 | 7.5 (HIGH) |

**S1 详细分析**：

```python
# main_bp.py L66: 写入pickle（无签名/无加密）
with open(cache_file, "wb") as f:
    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

# main_bp.py L81: 读取pickle（无条件信任）
with open(cache_file, "rb") as f:
    return pickle.load(f)
```

- 缓存路径：`outputs/.session_cache/{key}_{session.sid}.pkl`
- session.sid 可从 Cookie 获取
- 若攻击者可写入 `outputs/` 目录 → 可构造恶意 pickle → RCE
- **缓解**：`pickle.load()` 签名验证 + HMAC + 限制缓存目录写入权限

**S2 详细分析**：

```python
# L13: 盐值硬编码
salt = os.environ.get('CRYPTO_SALT', 'xiangxiantu_fan_balance').encode()

# L27: 应用密钥硬编码回退
return current_app.config.get('SECRET_KEY', 'default-insecure-key')

# L29: 环境变量硬编码回退
return os.environ.get('SECRET_KEY', 'default-insecure-key')
```

- 源码阅读者→已知盐值+默认密钥→可解密所有 `fernet:` 前缀的数据库密码
- **修复**：移除硬编码回退值，启动时强制检查 `SECRET_KEY` 和 `CRYPTO_SALT` 已设置

#### HIGH

| ID | 问题 | 文件 | 说明 |
|----|------|------|------|
| S3 | 缺失HTTP安全头 | [wsgi.py](file:///www/wwwroot/xiangxiantu/wsgi.py) | 无 X-Content-Type-Options / X-Frame-Options / CSP / HSTS |
| S4 | Session Cookie未加固 | [wsgi.py](file:///www/wwwroot/xiangxiantu/wsgi.py) | 缺 SECURE / HTTPONLY / SAMESITE 属性 |
| S5 | 无认证授权体系 | 全部蓝图 | 所有路由公开可访问，无登录/权限/速率限制 |
| S6 | 错误信息泄露 | [wsgi.py:L185-L202](file:///www/wwwroot/xiangxiantu/wsgi.py#L185-L202) | `str(e)` 直接返回响应体，500错误含完整 traceback |

#### MEDIUM

| ID | 问题 | 文件 | 说明 |
|----|------|------|------|
| S7 | os.listdir() 跟随符号链接 | [file_manager.py:L73-L93](file:///www/wwwroot/xiangxiantu/app/utils/file_manager.py#L73-L93) | `clean_old_files()` 可能遍历到系统目录 |
| S8 | 遗留 XOR 加密 | [database_connections.py:L31-L34](file:///www/wwwroot/xiangxiantu/database_connections.py#L31-L34) | XOR密码 + import失败时的明文回退 |

### 3.6 工部 — 算法科学性评审 [7.0/10]

#### P0 — 算法Bug

| ID | 严重 | 问题 | 文件 | 行号 |
|----|------|------|------|------|
| ALG1 | **P0** | **predict_trend 滞后阶数反转** | [machine_learning.py](file:///www/wwwroot/xiangxiantu/machine_learning.py#L244-L260) | L244-260 |

**ALG1 根因分析**：

```python
# BUG (L244): tail(3) 返回时间升序 [v_{t-2}, v_{t-1}, v_t]
# 但模型特征定义：lag_1 = 最近一天值，lag_2 = 前2天，lag_3 = 前3天
# 即期望顺序 [v_t, v_{t-1}, v_{t-2}]

last_values = df["value"].tail(3).tolist()    # → [v_{t-2}, v_{t-1}, v_t]
current_lags = list(last_values)              # → [v_{t-2}(→lag_1), v_{t-1}(→lag_2), v_t(→lag_3)]

# 对比：predict_key_metrics (L368) 正确使用了 [::-1] 反转
recent_values = [item['value'] for item in sorted_metrics[-3:]][::-1]
```

**影响**：训练-预测特征空间错位，所有使用 `predict_trend` 的趋势预测均存在系统性偏差。模型训练时 lag_1 学的是最近值，但预测时 lag_1 输入的是最远值。

**修复**：

```python
last_values = df["value"].tail(3).tolist()[::-1]  # [v_t, v_{t-1}, v_{t-2}]
```

#### P1 — 科学性问题

| ID | 问题 | 文件 | 行号 | 说明 |
|----|------|------|------|------|
| ALG2 | 滑动窗口 std=0 静默归零 | [machine_learning.py](file:///www/wwwroot/xiangxiantu/machine_learning.py#L539-L542) | L539-542 | `z_score = (x-μ)/0` → inf → `where(valid_mask, 0.0)` 静默替换为 0，掩盖真实异常 |
| ALG3 | 肘部法 K 上限过保守 | [data_analysis.py](file:///www/wwwroot/xiangxiantu/app/services/data_analysis.py#L87) | L87 | `max_k = min(max_k, 5)`，大数据集最优K可能>5 |
| ALG4 | 非线性检测用启发式阈值 | [data_analysis.py](file:///www/wwwroot/xiangxiantu/app/services/data_analysis.py#L400-L401) | L400-401 | `delta_r2 > 0.05` 为 `_try_quadratic_fit` 的判定阈值，未用 F-test 统计检验 |
| ALG5 | 硬编码权重无文献支撑 | [project_statistics.py](file:///www/wwwroot/xiangxiantu/app/services/project_statistics.py#L11-L17) | L11-17 | `DEFAULT_FACE_WEIGHTS = {'P1':0.4, 'P2':0.4, 'ST':0.2}` 和 `FACE_INTERNAL_WEIGHTS = {'iqr':0.4, 'cv':0.4, 'magnitude':0.2}` 硬编码无注释说明来源 |

---

## 四、门下省 — 终审汇总

### 4.1 评分汇总

| 部门 | 维度 | 评分 | 发现问题数 |
|------|------|------|------------|
| 中书省 | 架构设计 | 6.5 | 6 |
| 吏部 | 代码质量 | 7.0 | 6 |
| 户部 | 数据流 | 6.5 | 5 |
| 礼部 | UI/UX | 7.5 | 6 |
| 兵部 | 交互性 | 7.5 | 2 |
| 刑部 | 安全 | **5.0** ⚠️ | 8 |
| 工部 | 算法 | 7.0 | 5 |
| **加权** | **综合** | **6.67** | **38** |

### 4.2 优先级分布

| 优先级 | 数量 | 说明 |
|--------|------|------|
| **CRITICAL** | 2 | Pickle RCE + 硬编码密钥 → 生产部署前必须修复 |
| **P0** | 1 | predict_trend lag 反转 → 算法输出系统性错误 |
| **P1 (HIGH)** | 10 | 缺失安全头/无认证/双重算法实现等 |
| **P2 (MEDIUM)** | 14 | 死码/代码质量/目录重复 |
| **P2 (LOW)** | 11 | CSS残留/重复函数/废弃模块 |

### 4.3 与上轮评估（2026-05-14）对比

| 指标 | 上轮 | 本轮 | 变化 |
|------|------|------|------|
| 综合评分 | 6.67 | 6.67 | — |
| 发现问题 | 23 | 38 | +15 |
| 安全评分 | 5.0 | 5.0 | — (CRITICAL未修) |
| 已修复项 | 170 | 170 | — |
| 死码文件 | 2 (已删shim) | 3 (database_bp.py新增) | +1 |

> 综合评分持平但发现问题增加 15 项，反映本轮审查深度提升（全量扫描>专项审查），而非代码质量退化。

---

## 五、锦衣卫 — 独立复核

### 5.1 已确认修复（误报排除）

| 原报 | 复核结论 | 原因 |
|------|----------|------|
| `chart_generation.py` 被 `main_bp.py` 导入 | **误报** | `main_bp.py` 实际导入 `chart_generation_optimized.py`，废弃模块仅在 `app/services/__init__.py` 桶导出中 |
| `project_statistics.py` 与 `statistics.py` 算法重复 | **部分属实** | 两个版本算法不同（5因子 vs 3D），但所有调用方直接导入 `app.services.project_statistics`，桶导出虽错误但未造成运行时问题 |
| CSRF 缺失 | **已修复** | 第28轮已全局审查确认 Flask-WTF 自动保护 |

### 5.2 新发现（本轮新增）

| ID | 首次发现 | 说明 |
|----|----------|------|
| ALG1 | ✅ | `predict_trend` lag order bug — 此前31轮均未发现 |
| ALG2 | ✅ | Rolling std=0 静默归零 |
| ALG3 | ✅ | 肘部法 K 上限过保守 |
| ALG5 | ✅ | 硬编码权重无文献支撑 |
| D1 | ✅ | 跨面样本混合计数 |
| D2 | ✅ | dropna() 后空 df 未保护 |
| D5 | ✅ | 统计计算在 skill_evaluation 中重复 |
| A3 | ✅ | 根级 services/utils 与 app/services/utils 重复 |

---

## 六、改进路线图

### 6.1 CRITICAL（生产部署阻塞项）— 建议第三十二轮

| 优先级 | 修复项 | 文件 | 修复方案 |
|--------|--------|------|----------|
| CRITICAL | Pickle RCE | `main_bp.py` | 替换 `pickle` 为 `json` 序列化，或增加 HMAC 签名验证 |
| CRITICAL | 硬编码密钥 | `crypto_utils.py` | 移除所有硬编码回退值，启动时强制检查环境变量 |

### 6.2 P0（算法正确性）— 建议第三十二轮

| 优先级 | 修复项 | 文件 | 修复方案 |
|--------|--------|------|----------|
| P0 | predict_trend lag反转 | `machine_learning.py:244` | `tail(3).tolist()[::-1]` — 一行修复 |

### 6.3 P1（安全加固+架构清理）— 建议第三十三至三十四轮

| 轮次 | 修复项 | 数量 |
|------|--------|------|
| 第三十三轮 | 安全：HTTP头/Session加固/错误脱敏/速率限制 | 4 |
| 第三十四轮 | 架构：死码清理/桶导出修正/目录去重/路由合并 | 6 |

### 6.4 P2（工程质量）— 建议第三十五至三十六轮

| 轮次 | 修复项 | 数量 |
|------|--------|------|
| 第三十五轮 | 算法：滚动std保护/肘部K/F-test/权重文档化/统计去重 | 5 |
| 第三十六轮 | UI：内联样式清理/设计令牌补齐/CSS去重/debounce统一 | 6 |

### 6.5 长期改进

| 领域 | 建议 |
|------|------|
| 认证授权 | 引入 Flask-Login + 基于角色的权限控制（至少区分管理员/操作员） |
| 速率限制 | 引入 Flask-Limiter，API 端点 100 req/min |
| 日志审计 | 结构化日志（JSON格式）+ 操作审计 trail |
| 依赖锁定 | `requirements.txt` 固定所有版本号（当前使用 `>=` 范围约束） |
| 静态分析 | CI 集成 `ruff` + `mypy` + `bandit` 安全扫描 |
| 密钥管理 | 引入 `python-dotenv`，统一管理 SECRET_KEY/CRYPTO_SALT/DB_PASSWORD |

---

## 附：评估方法论

本次评估采用以下工具链：

1. **三省六部审查框架**（`review-sslb` 技能）：中书省（架构）→ 尚书省（交叉影响）→ 六部（吏户礼兵刑工 6 维度）→ 门下省（终审）→ 锦衣卫（独立复核）
2. **五轴代码质量评审**（`code-review-and-quality` 技能）：正确性 / 可读性 / 架构 / 安全性 / 性能
3. **GitNexus 代码智能**：影响分析 + 变更检测 + 执行流追踪
4. **手动验证**：源码阅读关键文件验证所有告警

共扫描 **55 个 Python 文件**（~17,754 行）、**29 个 HTML 模板**（~103,523 行）、**752 个 JS 文件**（~102,497 行）、**17 个 CSS 文件**（~6,090 行）。

---

*报告生成：2026-05-16 14:30 CST | 三省六部 + 锦衣卫独立复核 | GitNexus 辅助代码智能*