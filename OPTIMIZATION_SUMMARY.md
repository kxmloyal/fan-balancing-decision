# 项目优化总结

本文档记录扇叶平衡补土转速评估工具项目的各项优化工作，涵盖前端交互、算法科学性、安全性、工程规范等维度。

---

## 一、核心算法科学可靠性优化（2026-05-09）⭐ 最新

基于对深入分析算法的全面科学可靠性评估，完成 10 项算法优化，覆盖趋势分析、异常检测、聚类分析和最优转速评分的全链路。

### 1.1 趋势分析 X 轴修复

**优化前**: `LinearRegression` 使用 DataFrame 行索引 (0, 1, 2) 作为自变量，而非实际转速值 (800, 1000, 1200)。当数据条数或转速间隔变化时，斜率和 R² 完全不可信。

**优化后**: 新增 `_extract_numeric_x()` 方法，自动从 4 种格式中提取数值：
- `800rpm` → 800
- `800` → 800
- `转速800` → 800
- 纯数字 → 直接使用

配合 `_infer_x_unit()` 自动推断转速单位，输出有物理意义的斜率（如 "每增加 100rpm，不平衡量增加 0.05g"）。

### 1.2 幅值维度评分

**优化前**: `calculate_face_score()` 仅使用 IQR + CV 双维度（各 50%），只评估测量一致性，不考虑不平衡量绝对值是否合理。极端情况：完全偏离的异常转速可能因"内部一致性高"而获得高分。

**优化后**: 三维度加权评分（IQR 40% + CV 40% + 幅值 20%），引入幅值因子：

```
magnitude_factor = 1 / (1 + |mean - median| / median)
```

当某转速的不平衡量均值偏离所有转速的中位数时，该转速得分被抑制。支持 `include_magnitude` 参数控制是否启用。

### 1.3 自适应 Z-score 异常检测

**优化前**: 对所有数据统一使用 (x - μ)/σ 计算 Z-score，未检验正态分布前提条件。小样本或偏态分布下误报率高。

**优化后**: 两阶段自适应策略：
- **n ≥ 8**: 执行 D'Agostino-Pearson 正态性检验 → 通过则使用标准 Z-score，不通过则降级为 Modified Z-score
- **n < 8**: 直接使用 Modified Z-score (MAD × 0.6745)，对小样本更稳健

默认阈值统一为 2.5（可配置）。

### 1.4 CV 全链路统一

**优化前**: `data_analysis.py` 输出纯比值 (0.05)，`project_statistics.py` 输出百分比 (5)，`skill_evaluation.py` 自行计算比值 (0.05)，三处格式不一致导致评分偏差。

**优化后**: 全链路统一为百分比格式 `std/mean × 100`：
- `data_analysis.py._calculate_advanced_stats()` → 输出百分比 CV
- `project_statistics.py` → 直接使用百分比 CV
- `skill_evaluation.py._calculate_skill_score()` → 从 `basic_stats['cv']` 直接读取百分比值

### 1.5 可配置阈值体系

**优化前**: 硬编码的魔法数字散落在各处：
- CV 阈值: 5%, 10%
- 异常阈值: 2 或 3（不一致）
- 权重: 0.5/0.5
- 质量加分/扣分: 0.10

**优化后**: 集中定义类常量：

| 常量 | 值 | 位置 |
|------|-----|------|
| `DEFAULT_FACE_WEIGHTS` | `{P1:0.4, P2:0.4, ST:0.2}` | `project_statistics.py` |
| `FACE_INTERNAL_WEIGHTS` | `{iqr:0.4, cv:0.4, magnitude:0.2}` | `project_statistics.py` |
| `CV_EXCELLENT` | `5.0` | `skill_evaluation.py` |
| `CV_GOOD` | `10.0` | `skill_evaluation.py` |
| `QUALITY_BONUS_EXCELLENT` | `0.10` | `skill_evaluation.py` |
| `QUALITY_BONUS_GOOD` | `0.05` | `skill_evaluation.py` |
| `ANOMALY_PENALTY_THRESHOLD` | `2` | `skill_evaluation.py` |
| `ANOMALY_PENALTY` | `0.10` | `skill_evaluation.py` |
| `ANOMALY_FILTER_Z_THRESHOLD` | `2.5` | `skill_evaluation.py` |
| `MIN_SAMPLES_PER_SPEED` | `2` | `skill_evaluation.py` |
| `MIN_SPEED_COUNT` | `2` | `skill_evaluation.py` |

### 1.6 非线性趋势检测

**优化前**: 仅支持线性回归，无法识别 U 型/倒 U 型等曲线趋势。

**优化后**: 新增 `_try_quadratic_fit()` 方法：
- 使用 `PolynomialFeatures(degree=2)` 进行二次多项式拟合
- 输出：曲率类型（U 型/倒 U 型/近似线性）、顶点位置、ΔR²（非线性贡献量）
- 当二次 R² 显著高于线性 R² 时提示非线性趋势

### 1.7 肘部法自动 K 值

**优化前**: `cluster_analysis()` 需手动指定 K 值。

**优化后**: 新增 `_elbow_method()` 方法：
- 遍历 K=1..min(8, n-1) 计算 inertia
- 对 inertia 曲线进行曲率分析，自动检测"肘部"拐点
- 参数 `auto_k=True` 默认自动选择

### 1.8 数据充足性验证

**优化前**: 无输入验证，1 个样本或 1 个转速下统计学指标无意义也不报错。

**优化后**: 新增 `_validate_data_sufficiency()` 方法：
- 检查每转速至少 2 个样本 (`MIN_SAMPLES_PER_SPEED=2`)
- 检查至少 2 个不同转速 (`MIN_SPEED_COUNT=2`)
- `_evaluate_data_quality()` 升级为三维度评估（样本数量 + CV 合格率 + 异常值比例）

### 优化文件汇总

| 文件 | 变更行数 | 主要改动 |
|------|---------|---------|
| `app/services/data_analysis.py` | ~156 行 | 趋势修复、自适应 Z-score、非线性检测、肘部法 |
| `project_statistics.py` | ~64 行 | 幅值维度、可配置权重 |
| `app/services/skill_evaluation.py` | ~80 行 | 可配置阈值、三维度质量、样本验证 |

---

## 二、深入分析页面交互优化

### 2.1 创建增强脚本文件

- 位置: `static/js/in_depth_analysis_enhanced.js`
- 功能: JSON 格式实时验证、错误提示显示优化、加载状态可视化、从 session 加载数据增强

### 2.2 优化的功能列表

#### ✅ JSON 实时验证
- 输入数据时自动验证 JSON 格式
- 显示 "✓ 格式正确" 或 "✗ 格式错误" 状态
- 错误信息包含具体的行号和列号
- 验证状态用颜色区分（绿色/红色）

#### ✅ 错误处理显示优化
- 添加专门的错误提示容器
- 支持不同类型的错误警告（危险/警告/信息）
- 提供网络错误的专门提示

#### ✅ 从结果加载优化
- 加载时显示"加载中..."状态
- 按钮禁用防止重复点击
- 加载成功后自动更新 JSON 验证状态

#### ✅ 表单提交改进
- 提交前先验证 JSON 格式
- 分析中显示加载状态
- 30 秒超时保护
- 更好的错误反馈

### 2.3 技术改进点

- 使用防抖 (debounce) 减少验证频率
- 动态创建 DOM 元素避免直接修改模板
- 错误恢复机制确保按钮状态正确
- 向后兼容设计，不破坏原有功能

---

## 三、数据库安全优化

### 3.1 密码加密存储
- 文件: `app/utils/crypto_utils.py`（新建）
- 方案: XOR + SHA-256 派生密钥 + Base64 编码
- 密钥派生: `hashlib.sha256(SECRET_KEY.encode()).digest()`
- 配置文件不再以明文存储数据库密码

### 3.2 原子文件写入
- `ConnectionManager._save_configs()` 采用 temp 文件 + `fsync` + `os.replace` 模式
- 避免写入中断导致配置文件损坏

### 3.3 LRU 连接缓存
- `ConnectionTester._connection_cache` 实现 100 条上限 LRU 缓存
- 逐出时主动 `close()` 连接，防止资源泄漏
- 缓存 key 格式: `type_host_port_database`

### 3.4 跨平台超时保护
- `test_connection_with_timeout()` 使用 `threading.Thread` + `join(timeout=...)` 实现
- 替代仅 Linux 有效的 `signal.alarm()` 方案
- 统一超时时间 `DB_CONNECTION_TIMEOUT = 10`

### 3.5 配置文件 URL 编码
- `config_manager.py` 使用 `urllib.parse.quote_plus()` 对用户名密码进行 URL 编码
- 防止特殊字符破坏 SQLAlchemy 连接字符串

---

## 四、性能与缓存优化

### 4.1 图表缓存策略 (`chart_generation_optimized.py`)
- 缓存元数据管理（`_chart_cache_metadata`）
- 24 小时过期策略
- 最大缓存数量限制（100 个）
- LRU 最近最少使用清理策略

### 4.2 Gzip 压缩
- `wsgi.py` 中 `after_request` 钩子对 JSON 响应自动 gzip 压缩
- 静态资源 24 小时浏览器缓存（`Cache-Control: max-age=86400`）

### 4.3 定时文件清理
- APScheduler 每天凌晨 2:00 清理 7 天前的上传/输出文件
- 每 100 次请求自动检查并清理超过 1 小时的临时文件

---

## 五、部署状态

增强脚本已在 `in_depth_analysis.html` 中正确加载：

```html
<script src="{{ url_for('static', filename='js/in_depth_analysis_enhanced.js') }}"></script>
```

全部功能已激活运行。
