# Plotly.js 集成记录

## 当前版本

- Plotly: v3.3.1
- 日期: 2024-10-27

## 版本更新记录

### v5.18.0 (2024-10-27)
- 初始版本
- 从虚拟环境 `/venv/lib/python3.12/site-packages/plotly/package_data/plotly.min.js` 复制
- 支持所有标准图表类型

## 更新机制

### 手动更新步骤
1. 检查虚拟环境中Plotly的版本：`pip show plotly`
2. 从虚拟环境复制最新版本：
   ```bash
   cp /www/wwwroot/xiangxiantu/venv/lib/python3.12/site-packages/plotly/package_data/plotly.min.js /www/wwwroot/xiangxiantu/static/libs/plotly/
   ```
3. 更新本文件中的版本信息
4. 测试所有图表功能确保兼容性

### 自动更新建议
可以在构建脚本中添加自动更新步骤，确保Plotly库始终保持最新版本。

## 依赖管理
- 无外部依赖，使用本地引用方式
- 所有图表功能已迁移到Plotly实现

## 兼容性说明
- 支持所有现代浏览器
- 支持响应式设计
- 支持所有原ECharts图表类型的功能