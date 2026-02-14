# ECharts到Plotly迁移指南

## 1. 迁移概述

本指南详细介绍了从ECharts图表库迁移到Plotly图表库的过程、方法和最佳实践。迁移后，您将获得更现代化、交互性更强的图表体验。

### 1.1 迁移原因

- **更强大的交互功能**：Plotly提供丰富的内置交互功能，如缩放、悬停、点击等
- **更美观的视觉效果**：现代化的默认样式和丰富的自定义选项
- **更好的性能**：优化的渲染引擎和大数据集处理能力
- **更丰富的图表类型**：支持所有现有ECharts图表类型，且提供更多高级图表
- **更活跃的社区支持**：持续更新和完善

### 1.2 迁移范围

本次迁移涵盖以下图表类型：
- 散点图 (Scatter Plot)
- 趋势图 (Trend Plot)
- 箱线图 (Box Plot)
- 小提琴图 (Violin Plot)
- 热力图 (Heatmap)
- 直方图 (Histogram)
- 气泡图 (Bubble Plot)
- 3D散点图 (3D Scatter Plot)
- 平行坐标图 (Parallel Coordinates)

## 2. 技术架构

### 2.1 前端架构

- **旧架构**：使用ECharts库，通过`chart-manager.js`管理图表
- **新架构**：使用Plotly库，通过`plotly-manager.js`管理图表

### 2.2 核心文件

| 文件 | 功能 | 说明 |
|------|------|------|
| `static/js/plotly-manager.js` | Plotly图表管理器 | 替代原有的`chart-manager.js` |
| `templates/test_plotly.html` | 测试页面 | 用于测试迁移后的图表功能 |
| `app.py` | 后端路由 | 添加了`/test_plotly`路由 |

## 3. 迁移步骤

### 3.1 前端迁移

1. **引入Plotly库**
   在HTML文件中添加Plotly库的引用：
   ```html
   <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
   ```

2. **引入Plotly管理器**
   ```html
   <script src="static/js/plotly-manager.js"></script>
   ```

3. **初始化图表**
   使用与ECharts相同的API接口：
   ```javascript
   // 散点图示例
   plotlyManager.initChart('chart-container', 'scatter', data, {
       title: '散点图标题',
       xAxisLabel: 'X轴标签',
       yAxisLabel: 'Y轴标签'
   });
   ```

### 3.2 后端迁移

后端代码无需修改，因为Plotly管理器保持了与ECharts管理器相同的API接口。

## 4. API参考

### 4.1 初始化图表

```javascript
plotlyManager.initChart(containerId, chartType, data, options);
```

**参数说明**：
- `containerId`：图表容器的DOM元素ID
- `chartType`：图表类型（'scatter', 'trend', 'box', 'violin', 'heatmap', 'histogram', 'bubble', '3d', 'parallel'）
- `data`：图表数据
- `options`：配置选项

**返回值**：
- Plotly图表实例

### 4.2 更新图表

```javascript
plotlyManager.updateChart(containerId, data, options);
```

**参数说明**：
- `containerId`：图表容器的DOM元素ID
- `data`：新的图表数据
- `options`：配置选项

### 4.3 调整图表大小

```javascript
plotlyManager.resizeChart(containerId);
```

**参数说明**：
- `containerId`：图表容器的DOM元素ID

### 4.4 销毁图表

```javascript
plotlyManager.destroyChart(containerId);
```

**参数说明**：
- `containerId`：图表容器的DOM元素ID

## 5. 数据格式

### 5.1 散点图数据格式

```javascript
[
    ['3000rpm', 1.2],
    ['4000rpm', 2.5],
    ['5000rpm', 1.8]
]
```

### 5.2 趋势图数据格式

```javascript
[
    {name: '3000rpm', value: 1.2},
    {name: '4000rpm', value: 2.5},
    {name: '5000rpm', value: 1.8}
]
```

### 5.3 箱线图数据格式

```javascript
[
    {name: '3000rpm', data: [0.8, 1.0, 1.2, 1.4, 1.6]},
    {name: '4000rpm', data: [2.0, 2.2, 2.5, 2.8, 3.0]}
]
```

### 5.4 小提琴图数据格式

```javascript
[
    {name: '3000rpm', data: [0.8, 1.0, 1.1, 1.2, 1.3, 1.4, 1.6]},
    {name: '4000rpm', data: [2.0, 2.1, 2.2, 2.5, 2.7, 2.8, 3.0]}
]
```

### 5.5 热力图数据格式

```javascript
[
    ['3000rpm', 0, 1.2],
    ['3000rpm', 1, 1.5],
    ['4000rpm', 0, 2.2],
    ['4000rpm', 1, 2.5]
]
```

### 5.6 直方图数据格式

```javascript
[1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 5]
```

### 5.7 气泡图数据格式

```javascript
[
    {name: '3000rpm', value: ['3000rpm', 1.2, 5]},
    {name: '4000rpm', value: ['4000rpm', 2.5, 8]}
]
```

### 5.8 3D散点图数据格式

```javascript
[
    ['3000rpm', 0, 1.2],
    ['4000rpm', 1, 2.5],
    ['5000rpm', 2, 1.8]
]
```

### 5.9 平行坐标图数据格式

```javascript
[
    [0.8, 1.2, 0.9, 1.1],
    [1.5, 2.2, 1.8, 2.0],
    [2.1, 2.8, 2.4, 2.6]
]
```

## 6. 配置选项

### 6.1 通用配置选项

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `title` | String | 图表类型名称 | 图表标题 |
| `xAxisLabel` | String | 自动生成 | X轴标签 |
| `yAxisLabel` | String | 自动生成 | Y轴标签 |
| `zAxisLabel` | String | 自动生成 | Z轴标签（仅3D图表） |
| `config` | Object | {} | Plotly配置选项 |

### 6.2 Plotly配置选项

```javascript
{
    responsive: true,        // 响应式布局
    displayModeBar: true,    // 显示模式栏
    displaylogo: false,      // 隐藏Plotly logo
    scrollZoom: true,        // 启用滚轮缩放
    modeBarButtonsToAdd: ['resetScale2d'],  // 添加重置缩放按钮
    toImageButtonOptions: {  // 导出图片选项
        format: 'png',
        filename: 'chart',
        height: 400,
        width: 800,
        scale: 2
    }
}
```

## 7. 最佳实践

### 7.1 性能优化

- **大数据集处理**：对于超过1000个数据点的图表，Plotly会自动启用性能优化
- **减少动画**：大数据集时禁用动画以提高性能
- **合理设置图表大小**：避免过大的图表尺寸
- **使用适当的图表类型**：根据数据特点选择合适的图表类型

### 7.2 样式优化

- **统一颜色方案**：使用一致的颜色主题
- **合理设置字体大小**：确保标签清晰可读
- **适当的边距**：为图表元素留出足够空间
- **响应式设计**：确保图表在不同设备上都能正常显示

### 7.3 交互优化

- **添加适当的悬停提示**：提供有意义的悬停信息
- **启用缩放功能**：对于大数据集尤为重要
- **添加重置按钮**：方便用户恢复初始视图
- **合理设置图例**：确保图例清晰易读

## 8. 故障排除

### 8.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 图表不显示 | Plotly库未加载 | 确保正确引入Plotly库 |
| 数据渲染错误 | 数据格式不正确 | 检查数据格式是否符合要求 |
| 图表大小异常 | 容器大小设置不当 | 确保容器有明确的宽度和高度 |
| 交互功能失效 | 配置选项不正确 | 检查Plotly配置选项 |
| 性能问题 | 数据量过大 | 启用性能优化选项 |

### 8.2 调试技巧

- **查看浏览器控制台**：检查是否有错误信息
- **使用测试页面**：访问`/test_plotly`页面测试图表功能
- **简化数据**：使用少量测试数据定位问题
- **检查容器大小**：确保图表容器有足够的空间

## 9. 示例代码

### 9.1 散点图示例

```javascript
// 数据
const scatterData = [
    ['3000rpm', 1.2],
    ['4000rpm', 2.5],
    ['5000rpm', 1.8],
    ['6000rpm', 3.2]
];

// 初始化图表
plotlyManager.initChart('scatter-container', 'scatter', scatterData, {
    title: '转速与数值关系',
    xAxisLabel: '转速',
    yAxisLabel: '数值'
});
```

### 9.2 趋势图示例

```javascript
// 数据
const trendData = [
    {name: '3000rpm', value: 1.2},
    {name: '4000rpm', value: 2.5},
    {name: '5000rpm', value: 1.8},
    {name: '6000rpm', value: 3.2}
];

// 初始化图表
plotlyManager.initChart('trend-container', 'trend', trendData, {
    title: '转速趋势分析',
    xAxisLabel: '转速',
    yAxisLabel: '数值'
});
```

### 9.3 箱线图示例

```javascript
// 数据
const boxData = [
    {name: '3000rpm', data: [0.8, 1.0, 1.2, 1.4, 1.6]},
    {name: '4000rpm', data: [2.0, 2.2, 2.5, 2.8, 3.0]},
    {name: '5000rpm', data: [1.5, 1.6, 1.8, 2.0, 2.2]}
];

// 初始化图表
plotlyManager.initChart('box-container', 'box', boxData, {
    title: '不同转速下的数值分布',
    xAxisLabel: '转速',
    yAxisLabel: '数值'
});
```

## 10. 总结

### 10.1 迁移成果

- **功能完整性**：成功迁移了所有9种图表类型
- **API兼容性**：保持了与ECharts相同的API接口
- **性能提升**：优化了大数据集处理能力
- **用户体验**：提供了更现代化、交互性更强的图表体验
- **代码质量**：编写了清晰、可维护的代码

### 10.2 未来建议

- **持续优化**：根据实际使用情况进一步优化性能
- **扩展功能**：探索Plotly的高级功能，如子图、动画等
- **文档更新**：及时更新文档以反映最新的功能和最佳实践
- **用户反馈**：收集用户反馈，不断改进图表体验

---

通过本指南，您应该能够顺利完成从ECharts到Plotly的迁移，并充分利用Plotly的强大功能创建更加美观、交互性更强的图表。如果您在迁移过程中遇到任何问题，请参考本指南的故障排除部分或联系技术支持。