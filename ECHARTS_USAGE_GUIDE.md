# ECharts数据可视化开发指南

## 1. 项目概述

本文档旨在规范项目中ECharts数据可视化的开发流程，确保所有图表功能统一使用ECharts实现，保持图表风格、交互体验和数据处理逻辑的一致性。

### 1.1 技术栈

- **前端图表库**：ECharts 5.x
- **3D可视化**：ECharts GL
- **底层渲染**：ZRender
- **框架集成**：Vue.js + vue-echarts
- **微信小程序适配**：echarts-for-weixin

## 2. 组件封装规范

### 2.1 组件结构

项目采用模块化的组件结构，将ECharts图表封装为可复用的组件：

```
static/js/components/echarts/
├── index.js        # 基础组件类和具体图表组件
├── config.js       # 统一配置管理
└── utils.js        # 工具函数
```

### 2.2 基础组件类

`BaseEChartsComponent` 是所有图表组件的基类，提供以下核心功能：

- 统一的图表初始化流程
- 响应式布局支持
- 主题管理
- 加载状态处理
- 错误处理
- 性能优化

### 2.3 具体图表组件

基于基础组件类，实现了以下具体图表类型：

| 图表类型 | 组件类名 | 适用场景 |
|---------|---------|----------|
| 箱线图 | BoxChartComponent | 数据分布分析 |
| 趋势图 | TrendChartComponent | 数据变化趋势 |
| 散点图 | ScatterChartComponent | 数据分布可视化 |
| 热力图 | HeatmapChartComponent | 数据密度分析 |
| 直方图 | HistogramChartComponent | 数据频次分布 |
| 气泡图 | BubbleChartComponent | 三维数据可视化 |
| 3D散点图 | Scatter3DChartComponent | 三维空间数据 |
| 平行坐标图 | ParallelChartComponent | 多维度数据比较 |

### 2.4 组件工厂

使用 `ChartComponentFactory` 工厂类统一创建图表组件，简化组件实例化过程：

```javascript
import { ChartComponentFactory } from './components/echarts';

// 创建箱线图组件
const boxChart = ChartComponentFactory.create('chart-container', 'box', {
  theme: 'light',
  responsive: true
});

// 初始化图表
await boxChart.init(data);
```

## 3. 配置接口说明

### 3.1 全局配置

`GLOBAL_CONFIG` 包含全局图表配置，包括：

- 响应式配置
- 动画配置
- 性能配置
- 渲染配置
- 数据处理配置
- 错误处理配置

### 3.2 主题配置

项目提供三种内置主题：

| 主题名称 | 适用场景 | 特点 |
|---------|---------|------|
| default | 通用场景 | 白色背景，深色文字 |
| dark | 暗色模式 | 深色背景，浅色文字 |
| light | 简约风格 | 浅灰背景，清晰布局 |

### 3.3 图表类型配置

每种图表类型都有默认配置，包括：

- 系列样式
- 提示框格式
- 交互行为
- 视觉效果

### 3.4 配置合并规则

配置采用优先级从高到低的合并规则：

1. 用户传入的配置
2. 图表类型默认配置
3. 主题配置
4. 全局配置

## 4. 使用示例

### 4.1 基础用法

```javascript
// 导入组件工厂
import { ChartComponentFactory } from './components/echarts';

// 创建图表组件
const chart = ChartComponentFactory.create('chart-container', 'box', {
  theme: 'default',
  responsive: true
});

// 准备数据
const data = [
  { name: '3000rpm', data: [10, 20, 30, 40, 50] },
  { name: '4000rpm', data: [15, 25, 35, 45, 55] }
];

// 初始化图表
await chart.init(data, {
  title: {
    text: '箱线图示例',
    left: 'center'
  },
  tooltip: {
    trigger: 'item'
  }
});

// 更新数据
chart.update(newData);

// 销毁图表
chart.destroy();
```

### 4.2 高级用法

#### 4.2.1 主题切换

```javascript
// 创建图表时指定主题
const chart = ChartComponentFactory.create('chart-container', 'trend', {
  theme: 'dark'
});

// 动态切换主题
const darkTheme = ChartUtils.getTheme('dark');
chart.chartInstance.setOption(darkTheme);
```

#### 4.2.2 响应式配置

```javascript
const chart = ChartComponentFactory.create('chart-container', 'scatter', {
  responsive: true,
  renderer: 'svg' // 使用SVG渲染器获得更好的清晰度
});
```

#### 4.2.3 性能优化

```javascript
const chart = ChartComponentFactory.create('chart-container', 'heatmap', {
  lazyLoad: true, // 启用懒加载
  useDirtyRect: true, // 使用脏矩形渲染优化
  useCoarsePointer: true // 在移动设备上使用粗指针优化
});

// 大数据集优化
const optimizedData = ChartUtils.optimizeLargeDataSet(rawData, 500);
await chart.init(optimizedData);
```

### 4.3 与Vue框架集成

使用 `vue-echarts` 组件在Vue项目中集成ECharts：

```vue
<template>
  <v-chart
    class="chart"
    :option="chartOption"
    :theme="theme"
    :autoresize="true"
  />
</template>

<script>
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, GridComponent } from 'echarts/components';
import VChart from 'vue-echarts';

// 注册必要的组件
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent
]);

export default {
  components: {
    VChart
  },
  data() {
    return {
      theme: 'default',
      chartOption: {
        title: {
          text: '趋势图示例'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: ['3000rpm', '4000rpm', '5000rpm']
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          data: [10, 20, 30],
          type: 'line'
        }]
      }
    };
  }
};
</script>

<style scoped>
.chart {
  width: 100%;
  height: 400px;
}
</style>
```

### 4.4 微信小程序适配

使用 `echarts-for-weixin` 在微信小程序中使用ECharts：

```json
// app.json
{
  "usingComponents": {
    "ec-canvas": "echarts-for-weixin/ec-canvas"
  }
}
```

```wxml
<!-- page.wxml -->
<view class="container">
  <ec-canvas id="mychart-dom-bar" canvas-id="mychart-bar" ec="{{ ec }}"></ec-canvas>
</view>
```

```javascript
// page.js
import * as echarts from 'echarts-for-weixin';

Page({
  data: {
    ec: {
      onInit: function(canvas, width, height) {
        const chart = echarts.init(canvas, null, {
          width: width,
          height: height
        });
        canvas.setChart(chart);
        
        const option = {
          title: {
            text: '小程序图表示例'
          },
          series: [{
            type: 'bar',
            data: [10, 20, 30]
          }]
        };
        
        chart.setOption(option);
        return chart;
      }
    }
  }
});
```

## 5. 最佳实践

### 5.1 性能优化

1. **懒加载**：使用IntersectionObserver实现图表的懒加载
2. **数据采样**：对大数据集进行采样处理
3. **缓存机制**：缓存计算结果和配置
4. **渲染器选择**：根据场景选择合适的渲染器（canvas/svg）
5. **响应式调整**：使用ResizeObserver优化响应式布局

### 5.2 数据处理

1. **数据验证**：确保数据格式正确
2. **数据转换**：统一数据格式转换逻辑
3. **异常处理**：处理空数据和异常值
4. **数据聚合**：对大量数据进行聚合处理

### 5.3 代码规范

1. **命名规范**：使用语义化的变量和函数命名
2. **注释规范**：为关键代码添加注释
3. **错误处理**：完善的错误捕获和处理机制
4. **日志记录**：关键操作添加日志

## 6. 常见问题与解决方案

### 6.1 图表不显示

**可能原因**：
- 容器未设置宽高
- ECharts库未加载
- 数据格式错误
- 配置项错误

**解决方案**：
- 确保容器设置了明确的宽高
- 检查ECharts库是否正确加载
- 验证数据格式是否符合要求
- 使用 `console.log` 输出配置项检查错误

### 6.2 图表响应式问题

**可能原因**：
- 未启用响应式配置
- ResizeObserver未正确初始化
- 容器尺寸变化未触发重绘

**解决方案**：
- 设置 `responsive: true`
- 确保正确初始化ResizeObserver
- 手动调用 `chart.resize()` 方法

### 6.3 大数据集性能问题

**可能原因**：
- 数据量过大
- 渲染方式不当
- 动画效果影响性能

**解决方案**：
- 使用 `ChartUtils.optimizeLargeDataSet()` 优化数据
- 选择合适的渲染器（canvas）
- 禁用或简化动画效果
- 启用懒加载和脏矩形渲染

### 6.4 3D图表无法显示

**可能原因**：
- ECharts GL未加载
- 浏览器不支持WebGL
- 配置项错误

**解决方案**：
- 确保ECharts GL正确加载
- 检查浏览器WebGL支持情况
- 验证3D配置项是否正确

## 7. 开发流程

### 7.1 新增图表

1. **需求分析**：明确图表类型和功能需求
2. **数据准备**：准备符合格式要求的数据
3. **组件选择**：选择合适的图表组件
4. **配置设置**：根据需求设置图表配置
5. **测试验证**：在不同场景下测试图表显示
6. **性能优化**：根据需要进行性能优化

### 7.2 图表维护

1. **定期检查**：检查图表是否正常显示
2. **性能监控**：监控图表渲染性能
3. **响应式测试**：测试不同设备下的显示效果
4. **兼容性测试**：测试不同浏览器的兼容性

## 8. 版本管理

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-02-04 | 初始化文档，建立ECharts组件封装规范 |
| 1.1.0 | YYYY-MM-DD | 添加新图表类型和配置选项 |
| 1.2.0 | YYYY-MM-DD | 优化性能和添加新功能 |

## 9. 附录

### 9.1 数据源格式

#### 9.1.1 箱线图数据格式

```javascript
[
  { name: '3000rpm', data: [min, q1, median, q3, max] },
  { name: '4000rpm', data: [min, q1, median, q3, max] }
]
```

#### 9.1.2 趋势图数据格式

```javascript
[
  { name: '3000rpm', value: 10 },
  { name: '4000rpm', value: 20 },
  { name: '5000rpm', value: 30 }
]
```

#### 9.1.3 散点图数据格式

```javascript
[
  ['3000rpm', 10],
  ['3000rpm', 15],
  ['4000rpm', 20],
  ['4000rpm', 25]
]
```

### 9.2 工具函数参考

| 函数名 | 功能 | 参数 | 返回值 |
|--------|------|------|--------|
| `getTheme()` | 获取主题配置 | themeName: string | Object |
| `getChartTypeConfig()` | 获取图表类型配置 | chartType: string | Object |
| `mergeConfig()` | 合并配置 | base: Object, override: Object | Object |
| `generateChartConfig()` | 生成图表配置 | chartType: string, data: Object, options: Object, theme: string | Object |
| `optimizeLargeDataSet()` | 优化大数据集 | data: Array, maxPoints: number | Array |
| `calculateDataRange()` | 计算数据范围 | data: Array | { min: number, max: number } |
| `generateColorPalette()` | 生成颜色数组 | count: number | Array<string> |

### 9.3 配置项参考

详细的ECharts配置项请参考[官方文档](https://echarts.apache.org/zh/option.html)。

## 10. 总结

本指南为项目中的ECharts数据可视化开发提供了统一的规范和最佳实践，确保图表功能的一致性和可维护性。通过遵循本指南，开发团队可以更高效地实现数据可视化需求，同时保证图表的性能和用户体验。

---

**文档维护者**：技术团队
**最后更新**：2026-02-04