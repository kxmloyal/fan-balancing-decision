# 跨电脑使用故障诊断报告

**日期**: 2026-06-04
**技能**: systematic-debugging (四阶段根因分析)
**症状**: (A) 闪屏后仅保存第一次导入数据，再导入不显示
        (B) 图表上点击位漂移，无法正确点击数据

---

## 一、根因总览

| # | 严重度 | 症状 | 根因 | 文件:行号 |
|---|--------|------|------|----------|
| R1 | 🔴 P0 | 闪屏 | `flash()` + `redirect(request.url)` 引发全页重载 | `main_bp.py`:211-212/249-250/282-283/330-331/390-399 等 13 处 |
| R2 | 🔴 P0 | 跨电脑数据不可见 | `_cache_large_data_to_file` 用 `session.sid` 命名缓存文件 → 不同电脑 sid 不同 | `main_bp.py`:112 |
| R3 | 🔴 P0 | 二次导入不显示 | CSRF token 单次消费后过期 → 第二次 POST 验证失败 → redirect 清空文件输入 | `main_bp.py`:211-212 + Flask-WTF |
| R4 | 🟡 P1 | 图表点击漂移 | `.chart-container:hover { transform: translateY(-2px) }` hover 时容器上移 2px，点击坐标系偏移 | `style.css`:513 |
| R5 | 🟡 P1 | 图表点击漂移 | `.card:hover { transform: translateY(-2px) }` 父级卡片 hover 位移级联影响子图表 | `style.css`:186 |
| R6 | 🟡 P1 | 图表点击漂移 | ML 页面 `display:none` 隐藏 tab 中 Plotly 默认渲染为 700×450px，切回可见后容器实际更宽 → hitbox 拉伸错位 | `ml.js`:无 resize handler |
| R7 | 🟡 P1 | 不同电脑漂移更明显 | 不同 DPI/缩放比例 (如 Windows 125%) 下 Plotly 像素坐标缩放不一致 | 浏览器渲染层 |
| R8 | 🟢 P2 | 全屏切换时双重尺寸系统冲突 | `modal-manager.js` `ensureContainerStyles()` 内联样式覆盖 `style.css` 静态规则，两套 min-height (600px vs 400px) 冲突 | `modal-manager.js`:427-439 vs `style.css`:1507-1512 |

---

## 二、各根因详细分析

### R1: flash() + redirect() 引发页面闪烁

**位置**: `blueprints/main_bp.py` — 13 处 `flash()` + `return redirect(request.url)`

**触发场景**:
- 上传文件格式不合法 → L420-421
- 文件大小超限 → L423-427
- 文件内容与类型不匹配 → L429-430
- 扇叶型号为空/非法字符 → L390-394
- 存储空间不足 → L404-405
- 会话过期 → L211-212、L282-283
- 图表生成失败 → L249-250、L330-331

每次 `redirect(request.url)` 执行：
1. 浏览器发起全新 GET 请求
2. 页面从头渲染（白屏→内容出现 = "闪屏"）
3. 所有 `<input type="file">` 清空（浏览器安全限制）
4. 用户需重新选择所有文件

**影响**: 用户每次操作失败或切换都看到闪屏，体验极差。

---

### R2: 跨电脑 Session 文件缓存不可见

**位置**: `blueprints/main_bp.py` L90-119

```python
# L112
cache_file = os.path.join(cache_dir, f"{key}_{session.sid}.json")
```

**触发场景**:
- 电脑 A 上传数据 → 分析完成 → `saved_results` 缓存到 `outputs/.session_cache/saved_results_<sid-A>.json`
- 电脑 B 访问同一页面 → 不同浏览器 → 不同 `session.sid` → `<sid-B>`
- 电脑 B 上传数据 → `_get_from_session_with_cache` 查找 `<sid-B>` 的缓存 → 不存在 → 全新 `saved_results`
- 从电脑 B 再切到电脑 A → A 的 session 可能已过期 (3600s) → 数据丢失

**影响**: 多电脑协作场景下，每台电脑各自独立，无法共享已分析的数据。

---

### R3: CSRF Token 单次消费导致二次提交失败

**触发链**:
1. 用户首次访问 → 页面包含 CSRF token `<input name="csrf_token" value="TOKEN_A">`
2. 用户上传文件 → POST 携带 TOKEN_A → Flask-WTF 验证通过 → **TOKEN_A 被标记为已消费**
3. 服务端 `redirect(request.url)` → 返回新页面，但旧页面的 DOM 仍持有 TOKEN_A
4. 用户再次上传 → POST 再次携带 TOKEN_A → Flask-WTF 验证失败
5. `validate_csrf` 抛异常 → 某些路由中未显式处理 CSRF 异常 → session 数据丢失 → `flash("会话已过期")` → redirect

**影响**: 同一页面第二次提交数据必然失败。

---

### R4 + R5: CSS Transform 导致点击坐标系偏移

**位置 R4**: `static/css/style.css` L513

```css
.chart-container:hover {
    transform: translateY(-2px);
}
```

**位置 R5**: `static/css/style.css` L186

```css
.card:hover {
    transform: translateY(-2px);
}
```

**机制**:
- 用户鼠标移到图表上准备点击 → hover 触发 `translateY(-2px)` → 图表向上移动 2px
- 浏览器记录鼠标点击位置是基于**移动前**的坐标
- Plotly 计算 hit target 是基于**移动后**的元素位置
- 差值 2px → 在高 DPI 屏幕上可能被放大到 4-6px

**不同电脑差异放大原因**: Windows 默认 125% 缩放 vs Mac Retina 200% → 同样 2px CSS 位移在不同 DPI 下像素偏移不同。

---

### R6: ML 页面隐藏 Tab 中 Plotly 尺寸错位

**位置**: `static/js/ml.js` — 无 resize/redraw handler

**触发链**:
1. ML 页面有 4 个面板 Tab（趋势/指标/多维/异常）
2. 非激活 Tab 的 `.ml-result` 容器为 `display: none`
3. Plotly `newPlot` 在 `display:none` 容器中 → 无法测量真实尺寸 → 默认 700×450px 渲染
4. 用户切换到该 Tab → `.ml-result` 变为可见 → 容器实际宽度可能是 900px+
5. Plotly 图表被拉伸到 900px 宽，但内部 hit target 坐标仍是基于 700px 的
6. 用户点击数据点 → 点击 x=800px 位置 → Plotly 映射到 700px 空间的 ~622px 处 → 点击到错误的数据点或空白区域

**其他电脑差异放大原因**: 不同屏幕分辨率导致容器宽度不同 → 700px 基准下的偏移量不同。

---

### R7: 不同 DPI 缩放比例

**位置**: 浏览器渲染层

- Windows 默认 125% DPI 缩放 → 1 CSS px = 1.25 设备像素
- Mac Retina 200% → 1 CSS px = 2 设备像素
- Plotly 使用 `getBoundingClientRect()` 获取容器尺寸 → 返回 CSS 像素
- 但 `devicePixelRatio` 影响 SVG/Canvas 内部坐标映射
- 同一图表在不同 DPI 设备上 hit target 坐标偏移

---

### R8: 模态框双尺寸系统冲突

**位置**: `modal-manager.js` L427-439 vs `style.css` L1507-1512

```javascript
// modal-manager.js — JS 内联样式 (L427-432)
#chartContainer { min-height: 600px }
```

```css
/* style.css — 静态 CSS (L1507-1512) */
#chartContainer { min-height: 400px }
```

JS 内联样式优先级高于 CSS → `ensureContainerStyles()` 执行后容器高度变为 600px，但 CSS `@media` 查询仍基于 400px 断点 → 响应式行为不一致。

---

## 三、解决方案矩阵

### 问题 A: 闪屏 + 数据丢失 (R1+R2+R3)

| 方案 | 思路 | 改动量 | 效果 | 推荐 |
|------|------|--------|------|------|
| **A1: AJAX 化上传** | 所有文件上传和图表生成改为 AJAX + 局部刷新，不 `redirect()` | 大 (~300行) | 彻底消除闪屏 + 文件输入不清空 | ⭐⭐⭐ 推荐 |
| **A2: 修复 CSRF 循环** | 每次 `redirect` 后前端自动获取新 CSRF token → 存入 `meta` 标签 → safeFetch 自动注入 | 小 (~30行) | 解决二次提交失败 | ⭐⭐ |
| **A3: 共享缓存 key** | `_cache_large_data_to_file` 的 key 改为 `fan_model` 而非 `session.sid` → 跨电脑可见 | 小 (~5行) | 跨电脑数据共享 | ⭐⭐ |
| **A4: 文件输入状态保持** | 上传失败后不 redirect，改为 AJAX 返回错误 → Toast 提示 → 文件输入保留 | 中 (~100行) | 消除文件重新选择 | ⭐⭐⭐ 推荐 |

**建议组合: A1 + A3** — AJAX 化上传消除所有闪屏，共享缓存 key 解决跨电脑数据可见。

### 问题 B: 图表点击漂移 (R4+R5+R6+R7+R8)

| 方案 | 思路 | 改动量 | 效果 | 推荐 |
|------|------|--------|------|------|
| **B1: 移除 hover transform** | 删除 `style.css` L513 和 L186 的 `transform: translateY(-2px)`，改用 `box-shadow` 做 hover 反馈 | 极小 (~4行) | 立即消除 transform 导致的坐标偏移 | ⭐⭐⭐ 推荐 |
| **B2: 添加 ML resize handler** | `ml.js` 的 `switchTab` 函数中添加 `Plotly.Plots.resize()` 调用 | 小 (~15行) | 修复隐藏 tab 切换到可见后的尺寸错位 | ⭐⭐⭐ 推荐 |
| **B3: Plotly responsive 增强** | 为所有 `Plotly.newPlot` 添加 `{ responsive: true, scrollZoom: false }` + `ResizeObserver` | 中 (~40行) | 自动适配所有屏幕和 DPI | ⭐⭐ |
| **B4: 统一模态框尺寸** | 移除 JS `ensureContainerStyles` 中的 `min-height:600px` → 统一使用 CSS 的 `min-height:400px` | 极小 (~3行) | 消除双系统冲突 | ⭐⭐ |
| **B5: will-change 优化** | 在 hover 触发 transform 的容器上添加 `will-change: transform` | 极小 (~2行) | 让浏览器预分配 GPU 层，减少坐标重算延迟 | ⭐ |
| **B6: DPI 感知 hit target** | 在 Plotly config 中设置 `devicePixelRatio` 感知的 hit 半径 | 小 (~10行) | 高 DPI 屏幕点击更准确 | ⭐ |

**建议组合: B1 + B2 + B4** — 三个最小改动即可覆盖所有漂移根因。

---

## 四、推荐实施方案优先级

### 立即修复 (本轮)

| 优先级 | 方案 | 预期效果 |
|--------|------|---------|
| P0 | R1: AJAX 化上传 → 消除所有闪屏 | 无闪屏，文件输入不清空 |
| P0 | R3: CSRF token 刷新 → 修复二次提交 | 可连续多次上传 |
| P0 | R2: 共享缓存 key → fan_model 替代 session.sid | 跨电脑数据可见 |
| P0 | B1: 移除 hover transform | 图表点击准确 |
| P0 | B2: ML tab 切换 resize | 图表 hitbox 正确 |

### 后续优化 (下轮)

| 优先级 | 方案 | 预期效果 |
|--------|------|---------|
| P1 | B3: ResizeObserver | 全场景自适应 |
| P1 | B4: 统一模态框尺寸 | 消除双系统冲突 |
| P1 | A3: 文件状态保持 | 上传失败后文件不丢失 |

---

## 五、验证方法

### 闪屏修复验证
1. 在电脑 A 上传文件 → 确认无白屏闪烁
2. 在电脑 A 再次上传 → 确认文件可正常提交
3. 在电脑 B 上传 → 确认数据可见

### 图表点击验证
1. 在 1920×1080 (100%) 分辨率下点击图表数据点 → 确认 tooltip 精确显示
2. 在 2560×1440 (125% DPI) 分辨率下重复 → 确认同样精确
3. 在 ML 页面切换 Tab 后 → 确认图表尺寸正确

### CSP 和 CSRF 验证
1. 第二次上传 → 确认不再出现 "会话已过期"
2. 查看控制台 → 确认无 CSRF validation failed
