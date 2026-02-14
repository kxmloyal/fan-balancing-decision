# ECharts残留排查报告

## 1. 排查概述

本报告详细记录了对扇叶平衡补土转速评估工具项目中ECharts库残留的全面排查结果。排查过程覆盖了所有代码目录、配置文件及资源文件，确保不遗漏任何潜在的ECharts残留引用或依赖。

### 1.1 排查范围

- 源代码文件（.py, .js, .ts等）
- 配置文件（package.json, tsconfig.json等）
- 构建配置文件
- 已编译/打包的输出文件
- 项目文档（README.md等）

### 1.2 排查方法

- 使用grep工具搜索ECharts相关关键词
- 检查依赖配置文件中的ECharts相关依赖
- 分析构建配置文件中的ECharts相关配置
- 检查编译输出目录中的ECharts相关代码
- 审查项目文档中的ECharts提及

## 2. 排查结果

### 2.1 源代码文件中的ECharts引用

| 文件路径 | 引用类型 | 具体引用内容 | 备注 |
|---------|---------|-------------|------|
| `static/js/chart-manager.js` | 核心代码 | 大量ECharts相关代码，包括初始化、配置、渲染等 | 主要ECharts实现文件 |
| `static/js/echarts-manager.js` | 核心代码 | ECharts管理器实现 | 专门的ECharts管理文件 |
| `chart_generation.py` | 核心代码 | ECharts数据生成相关函数 | 后端ECharts数据处理 |
| `static/js/plotly-manager.js` | 注释 | 文件头部注释提及"替代ECharts实现" | 正常迁移注释 |
| `templates/test_plotly.html` | 注释 | 页面描述提及"从ECharts迁移到Plotly" | 正常迁移注释 |

### 2.2 依赖配置文件中的ECharts依赖

**package.json** 文件中发现以下ECharts相关依赖：

| 依赖名称 | 版本 | 类型 | 备注 |
|---------|------|------|------|
| `echarts` | ^5.5.0 | 核心依赖 | ECharts主库 |
| `echarts-gl` | ^2.0.9 | 核心依赖 | ECharts 3D扩展 |
| `echarts-stat` | ^1.2.0 | 核心依赖 | ECharts统计扩展 |
| `vue-echarts` | ^6.0.0 | 核心依赖 | Vue ECharts组件 |
| `vue` | ^3.4.0 | 核心依赖 | Vue框架（与vue-echarts相关） |

### 2.3 构建配置文件中的ECharts配置

**未发现**直接的ECharts相关构建配置。

### 2.4 已编译/打包的输出文件中的ECharts代码

**未发现**明确的ECharts相关编译输出文件。

### 2.5 项目文档中的ECharts提及

| 文件路径 | 提及位置 | 具体内容 | 备注 |
|---------|---------|----------|------|
| `README.md` | 技术架构部分 | "数据可视化：ECharts + ECharts-Stat" | 需要更新 |
| `README.md` | 系统架构图 | "图表展示层 (ECharts图表)" | 需要更新 |
| `README.md` | 图表生成模块 | "基于ECharts和ECharts-Stat的专业统计图表" | 需要更新 |
| `PLOTLY_MIGRATION_PLAN.md` | 整体文档 | ECharts到Plotly迁移计划 | 正常迁移文档 |
| `PLOTLY_MIGRATION_GUIDE.md` | 整体文档 | ECharts到Plotly迁移指南 | 正常迁移文档 |

## 3. 残留分析

### 3.1 核心残留文件

1. **`static/js/chart-manager.js`**
   - 状态：**需要清理**
   - 原因：包含完整的ECharts实现，已被`plotly-manager.js`替代

2. **`static/js/echarts-manager.js`**
   - 状态：**需要清理**
   - 原因：专门的ECharts管理器，已被`plotly-manager.js`替代

3. **`chart_generation.py`**
   - 状态：**需要修改**
   - 原因：包含ECharts数据生成函数，需要更新为支持Plotly数据格式

4. **`package.json`**
   - 状态：**需要修改**
   - 原因：包含多个ECharts相关依赖，需要移除

### 3.2 文档残留

1. **`README.md`**
   - 状态：**需要更新**
   - 原因：多处提及ECharts，需要更新为Plotly

### 3.3 正常迁移文件

以下文件中的ECharts提及是正常的迁移相关内容，**不需要清理**：

- `static/js/plotly-manager.js`：文件头部注释提及"替代ECharts实现"
- `templates/test_plotly.html`：页面描述提及"从ECharts迁移到Plotly"
- `PLOTLY_MIGRATION_PLAN.md`：ECharts到Plotly迁移计划文档
- `PLOTLY_MIGRATION_GUIDE.md`：ECharts到Plotly迁移指南文档

## 4. 清理建议

### 4.1 核心文件清理

1. **移除ECharts相关JavaScript文件**
   - `static/js/chart-manager.js`
   - `static/js/echarts-manager.js`

2. **修改后端代码**
   - 更新 `chart_generation.py`，移除ECharts专用数据格式，统一使用Plotly兼容的数据格式
   - 保留核心数据处理逻辑，仅修改数据输出格式

3. **更新依赖配置**
   - 从 `package.json` 中移除以下依赖：
     - `echarts: ^5.5.0`
     - `echarts-gl: ^2.0.9`
     - `echarts-stat: ^1.2.0`
     - `vue-echarts: ^6.0.0`
     - `vue: ^3.4.0`（如果不再使用）

### 4.2 文档更新

1. **更新 README.md**
   - 将技术架构中的"数据可视化：ECharts + ECharts-Stat"更新为"数据可视化：Plotly"
   - 将系统架构图中的"图表展示层 (ECharts图表)"更新为"图表展示层 (Plotly图表)"
   - 将图表生成模块中的"基于ECharts和ECharts-Stat的专业统计图表"更新为"基于Plotly的专业统计图表"

### 4.3 清理步骤

1. **备份重要文件**
   - 在清理前备份 `chart_generation.py` 等核心文件

2. **移除ECharts相关文件**
   - 删除 `static/js/chart-manager.js` 和 `static/js/echarts-manager.js`

3. **更新依赖配置**
   - 修改 `package.json`，移除ECharts相关依赖
   - 运行 `npm install` 更新依赖

4. **修改后端代码**
   - 更新 `chart_generation.py`，移除ECharts专用数据格式
   - 确保数据格式兼容Plotly

5. **更新文档**
   - 修改 `README.md` 中的ECharts提及

6. **测试验证**
   - 运行应用，确保所有图表功能正常
   - 检查控制台是否有ECharts相关错误
   - 验证所有图表类型都能正常渲染

## 5. 风险评估

### 5.1 清理风险

| 风险项 | 影响程度 | 应对措施 |
|-------|---------|----------|
| 后端数据格式不兼容 | 高 | 确保修改后的 `chart_generation.py` 输出格式兼容Plotly |
| 前端代码引用错误 | 高 | 确保所有前端代码使用 `plotly-manager.js` 而不是 `chart-manager.js` |
| 依赖冲突 | 中 | 移除ECharts依赖后运行 `npm install` 确保依赖一致性 |
| 文档不一致 | 低 | 仔细更新所有文档中的ECharts提及 |

### 5.2 缓解策略

1. **渐进式清理**：先备份，再逐步清理
2. **测试验证**：每步清理后进行功能测试
3. **回滚机制**：保留备份，必要时可回滚
4. **详细记录**：记录每步清理操作，便于追踪

## 6. 结论

### 6.1 残留总结

本次排查发现了以下ECharts残留：

- **核心代码残留**：2个JavaScript文件，1个Python文件
- **依赖残留**：4个ECharts相关依赖
- **文档残留**：多处README.md中的ECharts提及

### 6.2 清理优先级

1. **高优先级**：移除核心ECharts实现文件，更新依赖配置
2. **中优先级**：修改后端代码中的ECharts数据格式
3. **低优先级**：更新文档中的ECharts提及

### 6.3 预期效果

清理完成后，项目将：

- 不再依赖ECharts库
- 完全使用Plotly进行数据可视化
- 减少不必要的依赖和代码冗余
- 文档与实际实现保持一致

## 7. 后续建议

1. **定期审查**：定期检查项目中是否有新的ECharts残留
2. **自动化检测**：考虑添加CI/CD步骤检测ECharts残留
3. **迁移验证**：建立完整的图表功能测试套件
4. **文档维护**：确保文档与代码实现同步更新

---

**排查完成时间**：2026-02-05
**排查人员**：系统自动排查
**报告版本**：1.0