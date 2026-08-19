// 主题与UI管理器 — 扩展 SimplePlotlyManager 的原型方法
// 此文件必须在 simple-plotly-manager.js 之前加载


SimplePlotlyManager.prototype.applyColorSchemeToPage = function() {
        const scheme = this.colorSchemes[this.currentColorScheme];
        
        // 更新导航栏颜色
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.style.backgroundColor = scheme.primary;
        }
        
        // 更新按钮颜色
        const buttons = document.querySelectorAll('.btn-primary');
        buttons.forEach(button => {
            button.style.backgroundColor = scheme.primary;
        });
        
        // 更新图表容器背景
        const chartContainers = document.querySelectorAll('.plotly-chart');
        chartContainers.forEach(container => {
            container.style.backgroundColor = scheme.background;
        });
    }
SimplePlotlyManager.prototype.rerenderAllCharts = function() {
        // 重新渲染所有图表
        const chartContainers = document.querySelectorAll('.plotly-chart');
        chartContainers.forEach(container => {
            const chartId = container.getAttribute('id');
            const chartType = container.getAttribute('data-chart-type');
            const chartTitle = container.getAttribute('data-chart-title');
            const chartColor = container.getAttribute('data-chart-color');
            const chartData = container.getAttribute('data-chart-data');
            
            if (chartId && chartData) {
                try {
                    const unescapedChartData = chartData.replace(/&quot;/g, '"');
                    const data = JSON.parse(unescapedChartData);
                    this.initChart(chartId, chartType, data, {
                        title: chartTitle,
                        color: chartColor
                    });
                } catch (error) {
                    console.error(`重新渲染图表失败: ${chartId}`, error);
                }
            }
        });
        
    }
SimplePlotlyManager.prototype.getCurrentColorScheme = function() {
        return this.currentColorScheme;
    }
SimplePlotlyManager.prototype.getColorSchemeColors = function(schemeName = this.currentColorScheme) {
        return this.colorSchemes[schemeName] || this.colorSchemes.scheme1;
    }
SimplePlotlyManager.prototype.getSpeedColor = function(speedValue) {
        try {
            const speedStr = speedValue.toString();
            
            // 首先尝试从映射表中获取颜色
            if (this.speedColorMap[speedStr]) {
                return this.speedColorMap[speedStr];
            }
            
            // 如果映射表中没有，使用默认颜色数组
            const speedColors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'];
            
            // 基于转速值的数字部分计算索引
            const speedNum = parseInt(speedStr.replace(/[^0-9]/g, ''));
            if (!isNaN(speedNum)) {
                const index = speedNum % speedColors.length;
                return speedColors[index];
            }
            
            // 如果无法提取数字，基于字符串长度计算索引
            const index = speedStr.length % speedColors.length;
            return speedColors[index];
        } catch (error) {
            // 如果出错，返回默认颜色
            return '#1f77b4';
        }
    }
SimplePlotlyManager.prototype.getSpeedColorMap = function() {
        return this.speedColorMap;
    }
SimplePlotlyManager.prototype.getSpeedColors = function() {
        // 返回转速颜色映射表中的颜色值
        return Object.values(this.speedColorMap);
    }
SimplePlotlyManager.prototype.getRecommendedColorScheme = function(chartType) {
        // 根据图表类型推荐合适的配色方案
        const recommendations = {
            'box': 'scheme1', // 专业科技蓝 - 适合箱线图的清晰对比
            'trend': 'scheme3', // 活力创新橙 - 适合趋势图的视觉冲击力
            'scatter': 'scheme4', // 清新自然绿 - 适合散点图的区分度
            'heatmap': 'scheme5', // 沉稳专业紫 - 适合热力图的层次感
            'histogram': 'scheme2', // 现代商务灰 - 适合直方图的专业感
            'violin': 'scheme1', // 专业科技蓝 - 适合小提琴图的清晰对比
            '3d': 'scheme3', // 活力创新橙 - 适合3D图表的视觉效果
            'parallel': 'scheme4', // 清新自然绿 - 适合平行坐标图的多维度展示
            'bubble': 'scheme5', // 沉稳专业紫 - 适合气泡图的层次感
            'regression': 'scheme2' // 现代商务灰 - 适合回归图的专业感
        };
        
        return recommendations[chartType] || 'scheme1';
    }
SimplePlotlyManager.prototype.applyRecommendedColorScheme = function(containerId, chartType) {
        const recommendedScheme = this.getRecommendedColorScheme(chartType);
        this.setColorScheme(recommendedScheme);
    }
SimplePlotlyManager.prototype.setupSelectionEvents = function(containerId) {
        const chart = this.charts[containerId];
        if (!chart) return;
        
        // 移除现有的选择事件监听器
        if (this.eventListeners[containerId]) {
            this.eventListeners[containerId].forEach(listener => {
                chart.off('plotly_selected', listener);
            });
        }
        
        // 添加新的选择事件监听器
        const selectionListener = (eventData) => {
            this.handleSelection(containerId, eventData);
        };
        
        chart.on('plotly_selected', selectionListener);
        
        if (!this.eventListeners[containerId]) {
            this.eventListeners[containerId] = [];
        }
        this.eventListeners[containerId].push(selectionListener);
    }
    
    /**
     * 处理图表选择事件
     * @param {string} containerId - 图表容器ID
     * @param {object} eventData - 选择事件数据
     */
SimplePlotlyManager.prototype.handleSelection = function(containerId, eventData) {
        if (!eventData || !eventData.points) return;
        
        const selectedPoints = eventData.points;
        this.selectionState[containerId] = selectedPoints;
        
        
        // 更新其他联动图表
        this.updateLinkedCharts(containerId, selectedPoints);
    }
    
    /**
     * 更新联动图表
     * @param {string} sourceContainerId - 源图表容器ID
     * @param {array} selectedPoints - 选择的数据点
     */
SimplePlotlyManager.prototype.updateLinkedCharts = function(sourceContainerId, selectedPoints) {
        // 提取选择的数据点的关键信息
        const selectedValues = new Set();
        selectedPoints.forEach(point => {
            // 提取数据点的关键值（如转速、类别等）
            if (point.x) selectedValues.add(point.x.toString());
            if (point.y) selectedValues.add(point.y.toString());
            if (point.name) selectedValues.add(point.name);
        });
        
        // 更新其他联动图表
        this.linkedCharts.forEach(containerId => {
            if (containerId !== sourceContainerId) {
                this.highlightLinkedChartData(containerId, selectedValues);
            }
        });
    }
SimplePlotlyManager.prototype.applyAnimationToLayout = function(layout) {
        if (!this.animationConfig.enabled) {
            return layout;
        }
        
        return {
            ...layout,
            transition: {
                duration: this.animationConfig.duration,
                easing: this.animationConfig.easing
            }
        };
    }
    
    /**
     * 应用动画配置到图表数据
     * @param {array} data - 图表数据数组
     * @returns {array} 应用了动画配置的数据数组
     */
SimplePlotlyManager.prototype.applyAnimationToData = function(data) {
        if (!this.animationConfig.enabled) {
            return data;
        }
        
        return data.map(trace => ({
            ...trace,
            animation: {
                duration: this.animationConfig.duration,
                easing: this.animationConfig.easing
            }
        }));
    }
    /**
     * 加载保存的主题
     */
SimplePlotlyManager.prototype.loadSavedTheme = function() {
        try {
            const savedTheme = localStorage.getItem('selectedTheme');
            if (savedTheme && (this.themes[savedTheme] || this.customThemes[savedTheme])) {
                this.currentTheme = savedTheme;
            }
        } catch (error) {
            console.error('加载保存的主题失败:', error);
        }
    }
    
    /**
     * 保存主题
     * @param {string} themeName - 主题名称
     */
SimplePlotlyManager.prototype.saveTheme = function(themeName) {
        try {
            localStorage.setItem('selectedTheme', themeName);
        } catch (error) {
            console.error('保存主题失败:', error);
        }
    }
    
    /**
     * 设置主题
     * @param {string} themeName - 主题名称
     */
SimplePlotlyManager.prototype.setTheme = function(themeName) {
        if (this.themes[themeName] || this.customThemes[themeName]) {
            this.currentTheme = themeName;
            this.saveTheme(themeName);
            this.applyThemeToPage();
            this.rerenderAllCharts();
        } else {
            console.error('未知的主题:', themeName);
        }
    }
    
    /**
     * 创建自定义主题
     * @param {string} themeName - 主题名称
     * @param {object} themeConfig - 主题配置
     */
SimplePlotlyManager.prototype.createCustomTheme = function(themeName, themeConfig) {
        this.customThemes[themeName] = {
            name: themeConfig.name || themeName,
            colors: themeConfig.colors || this.themes.default.colors,
            font: themeConfig.font || this.themes.default.font,
            layout: themeConfig.layout || this.themes.default.layout
        };
        this.saveCustomThemes();
    }
    
    /**
     * 保存自定义主题
     */
SimplePlotlyManager.prototype.saveCustomThemes = function() {
        try {
            localStorage.setItem('customThemes', JSON.stringify(this.customThemes));
        } catch (error) {
            console.error('保存自定义主题失败:', error);
        }
    }
    
    /**
     * 加载自定义主题
     */
SimplePlotlyManager.prototype.loadCustomThemes = function() {
        try {
            const savedCustomThemes = localStorage.getItem('customThemes');
            if (savedCustomThemes) {
                this.customThemes = JSON.parse(savedCustomThemes);
            }
        } catch (error) {
            console.error('加载自定义主题失败:', error);
        }
    }
    
    /**
     * 删除自定义主题
     * @param {string} themeName - 主题名称
     */
SimplePlotlyManager.prototype.deleteCustomTheme = function(themeName) {
        if (this.customThemes[themeName]) {
            delete this.customThemes[themeName];
            this.saveCustomThemes();
        }
    }
    
    /**
     * 获取主题名称
     * @param {string} themeName - 主题名称
     * @returns {string} 主题显示名称
     */
SimplePlotlyManager.prototype.getThemeName = function(themeName) {
        if (this.themes[themeName]) {
            return this.themes[themeName].name;
        } else if (this.customThemes[themeName]) {
            return this.customThemes[themeName].name;
        }
        return themeName;
    }
    
    /**
     * 获取当前主题
     * @returns {string} 当前主题名称
     */
SimplePlotlyManager.prototype.getCurrentTheme = function() {
        return this.currentTheme;
    }
SimplePlotlyManager.prototype.applyThemeToPage = function() {
        const theme = this.getThemeConfig();
        const colors = theme.colors;
        
        // 更新导航栏颜色
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.style.backgroundColor = colors.primary;
            navbar.style.color = colors.text;
        }
        
        // 更新按钮颜色
        const buttons = document.querySelectorAll('.btn-primary');
        buttons.forEach(button => {
            button.style.backgroundColor = colors.primary;
            button.style.color = '#ffffff';
        });
        
        // 更新卡片和容器
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            card.style.backgroundColor = colors.background;
            card.style.color = colors.text;
        });
        
        // 更新图表容器背景
        const chartContainers = document.querySelectorAll('.plotly-chart');
        chartContainers.forEach(container => {
            container.style.backgroundColor = colors.background;
        });
        
        // 更新页面背景
        document.body.style.backgroundColor = colors.background;
        document.body.style.color = colors.text;
        
        // 更新链接颜色
        const links = document.querySelectorAll('a');
        links.forEach(link => {
            link.style.color = colors.primary;
        });
        
        // 更新表单元素
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.style.backgroundColor = colors.background;
            input.style.color = colors.text;
            input.style.borderColor = colors.secondary;
        });
    }
    /**
     * 创建主题选择器UI
     * @param {string} containerId - 容器ID
     * @param {function} callback - 主题切换后的回调函数
     */
SimplePlotlyManager.prototype.createThemeSelector = function(containerId, callback) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // 清空容器
        container.innerHTML = '';
        
        // 创建主题选择面板
        const themePanel = document.createElement('div');
        themePanel.className = 'theme-selector';
        themePanel.style.padding = '15px';
        themePanel.style.backgroundColor = '#f8f9fa';
        themePanel.style.borderRadius = '8px';
        themePanel.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        
        // 添加标题
        const title = document.createElement('h4');
        title.textContent = '选择主题';
        title.style.marginTop = '0';
        title.style.marginBottom = '15px';
        themePanel.appendChild(title);
        
        // 获取所有可用主题
        const themes = this.getAvailableThemes();
        
        // 创建主题选项
        themes.forEach(theme => {
            const themeOption = document.createElement('div');
            themeOption.className = 'theme-option';
            themeOption.style.display = 'flex';
            themeOption.style.alignItems = 'center';
            themeOption.style.padding = '8px 12px';
            themeOption.style.marginBottom = '8px';
            themeOption.style.borderRadius = '4px';
            themeOption.style.cursor = 'pointer';
            themeOption.style.transition = 'background-color 0.2s ease';
            
            // 主题颜色预览
            const colorPreview = document.createElement('div');
            colorPreview.style.width = '20px';
            colorPreview.style.height = '20px';
            colorPreview.style.borderRadius = '50%';
            colorPreview.style.marginRight = '10px';
            colorPreview.style.backgroundColor = this.getThemeConfig(theme.name).colors.primary;
            
            // 主题名称
            const themeName = document.createElement('span');
            themeName.textContent = theme.displayName;
            themeName.style.flex = '1';
            
            // 主题类型标签
            const themeType = document.createElement('span');
            themeType.textContent = theme.isDefault ? '预设' : '自定义';
            themeType.style.fontSize = '10px';
            themeType.style.padding = '2px 6px';
            themeType.style.borderRadius = '10px';
            themeType.style.backgroundColor = theme.isDefault ? '#e3f2fd' : '#e8f5e8';
            themeType.style.color = theme.isDefault ? '#1976d2' : '#388e3c';
            
            // 组装
            themeOption.appendChild(colorPreview);
            themeOption.appendChild(themeName);
            themeOption.appendChild(themeType);
            
            // 添加点击事件
            themeOption.addEventListener('click', () => {
                this.setTheme(theme.name);
                if (callback) callback(theme.name);
                
                // 更新选中状态
                document.querySelectorAll('.theme-option').forEach(opt => {
                    opt.style.backgroundColor = '';
                    opt.style.border = '';
                });
                themeOption.style.backgroundColor = '#e3f2fd';
                themeOption.style.border = '1px solid #1976d2';
            });
            
            // 标记当前主题
            if (theme.name === this.currentTheme) {
                themeOption.style.backgroundColor = '#e3f2fd';
                themeOption.style.border = '1px solid #1976d2';
            }
            
            themePanel.appendChild(themeOption);
        });
        
        // 添加到容器
        container.appendChild(themePanel);
    }
    /**
     * 应用主题到图表布局
     * @param {object} layout - 图表布局对象
     * @returns {object} 应用了主题的布局对象
     */
SimplePlotlyManager.prototype.applyThemeToLayout = function(layout) {
        // 直接返回原始布局，不应用主题，确保布局结构不变
        return layout;
    }
    
    /**
     * 应用主题到图表数据
     * @param {array} data - 图表数据数组
     * @returns {array} 应用了主题的数据数组
     */
SimplePlotlyManager.prototype.applyThemeToData = function(data) {
        // 直接返回原始数据，不应用主题，确保数据结构不变
        return data;
    }
    /**
     * 显示加载状态
     * @param {string} containerId - 图表容器ID
     * @param {string} message - 加载消息
     */
SimplePlotlyManager.prototype.showLoading = function(containerId, message = '加载中...') {
        if (!this.loadingConfig.enabled) return;
        
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // 保存原始内容
        this.loadingState[containerId] = {
            originalContent: container.innerHTML,
            progress: 0,
            error: null
        };
        
        // 创建加载动画容器
        const loadingContainer = document.createElement('div');
        loadingContainer.id = `${containerId}-loading`;
        loadingContainer.style.position = 'absolute';
        loadingContainer.style.top = '0';
        loadingContainer.style.left = '0';
        loadingContainer.style.width = '100%';
        loadingContainer.style.height = '100%';
        loadingContainer.style.display = 'flex';
        loadingContainer.style.flexDirection = 'column';
        loadingContainer.style.justifyContent = 'center';
        loadingContainer.style.alignItems = 'center';
        loadingContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        loadingContainer.style.zIndex = '1000';
        loadingContainer.style.borderRadius = '4px';
        
        // 创建加载动画
        const spinner = document.createElement('div');
        spinner.style.width = '40px';
        spinner.style.height = '40px';
        spinner.style.border = '4px solid #f3f3f3';
        spinner.style.borderTop = '4px solid this.getThemeConfig().colors.primary';
        spinner.style.borderRadius = '50%';
        spinner.style.animation = 'spin 1s linear infinite';
        
        // 创建加载消息
        const loadingMessage = document.createElement('div');
        loadingMessage.style.marginTop = '10px';
        loadingMessage.style.fontSize = '14px';
        loadingMessage.style.color = '#333';
        loadingMessage.textContent = message;
        
        // 创建进度条容器
        const progressContainer = document.createElement('div');
        progressContainer.style.width = '80%';
        progressContainer.style.marginTop = '10px';
        progressContainer.style.height = '6px';
        progressContainer.style.backgroundColor = '#f3f3f3';
        progressContainer.style.borderRadius = '3px';
        
        // 创建进度条
        const progressBar = document.createElement('div');
        progressBar.id = `${containerId}-progress`;
        progressBar.style.height = '100%';
        progressBar.style.backgroundColor = this.getThemeConfig().colors.primary;
        progressBar.style.borderRadius = '3px';
        progressBar.style.width = '0%';
        progressBar.style.transition = `width ${this.loadingConfig.animationDuration}ms ease`;
        
        // 组装加载容器
        progressContainer.appendChild(progressBar);
        loadingContainer.appendChild(spinner);
        loadingContainer.appendChild(loadingMessage);
        loadingContainer.appendChild(progressContainer);
        
        // 添加到容器
        container.style.position = 'relative';
        container.appendChild(loadingContainer);
        
        // 添加动画样式
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
    
    /**
     * 隐藏加载状态
     * @param {string} containerId - 图表容器ID
     */
SimplePlotlyManager.prototype.hideLoading = function(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const loadingContainer = document.getElementById(`${containerId}-loading`);
        if (loadingContainer) {
            loadingContainer.style.transition = `opacity ${this.loadingConfig.animationDuration}ms ease`;
            loadingContainer.style.opacity = '0';
            
            setTimeout(() => {
                if (loadingContainer.parentNode) {
                    loadingContainer.parentNode.removeChild(loadingContainer);
                }
            }, this.loadingConfig.animationDuration);
        }
        
        // 恢复原始内容（如果有）
        if (this.loadingState[containerId] && this.loadingState[containerId].originalContent) {
            container.innerHTML = this.loadingState[containerId].originalContent;
        }
        
        // 清除加载状态
        delete this.loadingState[containerId];
    }
    
    /**
     * 更新加载进度
     * @param {string} containerId - 图表容器ID
     * @param {number} progress - 进度值（0-100）
     */
SimplePlotlyManager.prototype.updateLoadingProgress = function(containerId, progress) {
        if (!this.loadingConfig.showProgress) return;
        
        const progressBar = document.getElementById(`${containerId}-progress`);
        if (progressBar) {
            progress = Math.max(0, Math.min(100, progress));
            progressBar.style.width = `${progress}%`;
            
            // 更新加载状态
            if (this.loadingState[containerId]) {
                this.loadingState[containerId].progress = progress;
            }
        }
    }
    
    /**
     * 显示错误信息
     * @param {string} containerId - 图表容器ID
     * @param {string} errorMessage - 错误信息
     * @param {function} retryCallback - 重试回调函数
     */
SimplePlotlyManager.prototype.showError = function(containerId, errorMessage, retryCallback) {
        if (!this.loadingConfig.showError) return;
        
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // 隐藏加载状态
        this.hideLoading(containerId);
        
        // 创建错误容器
        const errorContainer = document.createElement('div');
        errorContainer.id = `${containerId}-error`;
        errorContainer.style.position = 'absolute';
        errorContainer.style.top = '0';
        errorContainer.style.left = '0';
        errorContainer.style.width = '100%';
        errorContainer.style.height = '100%';
        errorContainer.style.display = 'flex';
        errorContainer.style.flexDirection = 'column';
        errorContainer.style.justifyContent = 'center';
        errorContainer.style.alignItems = 'center';
        errorContainer.style.backgroundColor = 'rgba(255, 240, 240, 0.8)';
        errorContainer.style.zIndex = '1000';
        errorContainer.style.borderRadius = '4px';
        
        // 创建错误图标
        const errorIcon = document.createElement('div');
        errorIcon.style.fontSize = '48px';
        errorIcon.style.color = '#d9534f';
        errorIcon.textContent = '⚠️';
        
        // 创建错误消息
        const errorText = document.createElement('div');
        errorText.style.marginTop = '10px';
        errorText.style.fontSize = '14px';
        errorText.style.color = '#333';
        errorText.style.textAlign = 'center';
        errorText.style.padding = '0 20px';
        errorText.textContent = errorMessage;
        
        // 创建重试按钮
        if (retryCallback) {
            const retryButton = document.createElement('button');
            retryButton.style.marginTop = '15px';
            retryButton.style.padding = '8px 16px';
            retryButton.style.backgroundColor = this.getThemeConfig().colors.primary;
            retryButton.style.color = 'white';
            retryButton.style.border = 'none';
            retryButton.style.borderRadius = '4px';
            retryButton.style.cursor = 'pointer';
            retryButton.style.fontSize = '14px';
            retryButton.textContent = '重试';
            
            retryButton.addEventListener('click', () => {
                // 隐藏错误信息
                if (errorContainer.parentNode) {
                    errorContainer.parentNode.removeChild(errorContainer);
                }
                // 调用重试回调
                retryCallback();
            });
            
            errorContainer.appendChild(retryButton);
        }
        
        // 组装错误容器
        errorContainer.appendChild(errorIcon);
        errorContainer.appendChild(errorText);
        
        // 添加到容器
        container.style.position = 'relative';
        container.appendChild(errorContainer);
        
        // 更新加载状态
        this.loadingState[containerId] = {
            error: errorMessage
        };
    }
    
    /**
     * 隐藏错误信息
     * @param {string} containerId - 图表容器ID
     */
SimplePlotlyManager.prototype.hideError = function(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const errorContainer = document.getElementById(`${containerId}-error`);
        if (errorContainer) {
            errorContainer.style.transition = `opacity ${this.loadingConfig.animationDuration}ms ease`;
            errorContainer.style.opacity = '0';
            
            setTimeout(() => {
                if (errorContainer.parentNode) {
                    errorContainer.parentNode.removeChild(errorContainer);
                }
            }, this.loadingConfig.animationDuration);
        }
        
        // 清除错误状态
        if (this.loadingState[containerId]) {
            this.loadingState[containerId].error = null;
        }
    }
    /**
     * 检查性能指标
     * @returns {object} 性能指标
     */
SimplePlotlyManager.prototype.getPerformanceMetrics = function() {
        const metrics = {
            chartCount: Object.keys(this.charts).length,
            linkedChartCount: this.linkedCharts.length,
            eventListenerCount: Object.keys(this.eventListeners).reduce((total, key) => {
                return total + this.eventListeners[key].length;
            }, 0),
            memoryUsage: performance.memory ? {
                usedJSHeapSize: performance.memory.usedJSHeapSize,
                totalJSHeapSize: performance.memory.totalJSHeapSize,
                jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
            } : null
        };
        
        return metrics;
    }
    /**
     * 加载保存的配置
     */
SimplePlotlyManager.prototype.loadSavedConfigs = function() {
        try {
            const savedConfigs = localStorage.getItem('chartConfigs');
            if (savedConfigs) {
                this.savedConfigs = JSON.parse(savedConfigs);
            }
        } catch (error) {
            console.error('加载保存的配置失败:', error);
        }
    }
SimplePlotlyManager.prototype.applyChartTemplate = function(containerId, templateName, data) {
        const template = this.getChartTemplate(templateName);
        if (!template) {
            console.error('未知的图表模板:', templateName);
            return null;
        }
        
        const { type, options } = template.config;
        return this.initChart(containerId, type, data, options);
    }
SimplePlotlyManager.prototype.loadChartConfig = function(configName) {
        return this.savedConfigs[configName] || null;
    }
    /**
     * 创建图表配置界面
     * @param {string} containerId - 容器ID
     * @param {function} callback - 配置完成后的回调函数
     */
SimplePlotlyManager.prototype.createChartConfigUI = function(containerId, callback) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // 清空容器
        container.innerHTML = '';
        
        // 创建配置面板
        const configPanel = document.createElement('div');
        configPanel.className = 'chart-config-panel';
        configPanel.style.padding = '20px';
        configPanel.style.backgroundColor = '#f8f9fa';
        configPanel.style.borderRadius = '8px';
        configPanel.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        
        // 添加标题
        const title = document.createElement('h3');
        title.textContent = '图表配置';
        title.style.marginTop = '0';
        configPanel.appendChild(title);
        
        // 图表类型选择
        const typeGroup = document.createElement('div');
        typeGroup.style.marginBottom = '20px';
        
        const typeLabel = document.createElement('label');
        typeLabel.textContent = '图表类型:';
        typeLabel.style.display = 'block';
        typeLabel.style.marginBottom = '8px';
        typeGroup.appendChild(typeLabel);
        
        const typeSelect = document.createElement('select');
        typeSelect.id = 'chart-type';
        typeSelect.style.width = '100%';
        typeSelect.style.padding = '8px';
        typeSelect.style.borderRadius = '4px';
        typeSelect.style.border = '1px solid #ced4da';
        
        const chartTypes = [
            { value: 'scatter', label: '散点图' },
            { value: 'trend', label: '趋势图' },
            { value: 'box', label: '箱线图' },
            { value: 'histogram', label: '直方图' },
            { value: 'violin', label: '小提琴图' },
            { value: 'heatmap', label: '热力图' },
            { value: '3d', label: '3D散点图' },
            { value: 'bubble', label: '气泡图' },
            { value: 'regression', label: '回归图' }
        ];
        
        chartTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type.value;
            option.textContent = type.label;
            typeSelect.appendChild(option);
        });
        typeGroup.appendChild(typeSelect);
        configPanel.appendChild(typeGroup);
        
        // 图表标题
        const titleGroup = document.createElement('div');
        titleGroup.style.marginBottom = '20px';
        
        const titleInputLabel = document.createElement('label');
        titleInputLabel.textContent = '图表标题:';
        titleInputLabel.style.display = 'block';
        titleInputLabel.style.marginBottom = '8px';
        titleGroup.appendChild(titleInputLabel);
        
        const titleInput = document.createElement('input');
        titleInput.type = 'text';
        titleInput.id = 'chart-title';
        titleInput.value = '图表标题';
        titleInput.style.width = '100%';
        titleInput.style.padding = '8px';
        titleInput.style.borderRadius = '4px';
        titleInput.style.border = '1px solid #ced4da';
        titleGroup.appendChild(titleInput);
        configPanel.appendChild(titleGroup);
        
        // Y轴标签
        const yAxisGroup = document.createElement('div');
        yAxisGroup.style.marginBottom = '20px';
        
        const yAxisLabel = document.createElement('label');
        yAxisLabel.textContent = 'Y轴标签:';
        yAxisLabel.style.display = 'block';
        yAxisLabel.style.marginBottom = '8px';
        yAxisGroup.appendChild(yAxisLabel);
        
        const yAxisInput = document.createElement('input');
        yAxisInput.type = 'text';
        yAxisInput.id = 'chart-yaxis';
        yAxisInput.value = '值';
        yAxisInput.style.width = '100%';
        yAxisInput.style.padding = '8px';
        yAxisInput.style.borderRadius = '4px';
        yAxisInput.style.border = '1px solid #ced4da';
        yAxisGroup.appendChild(yAxisInput);
        configPanel.appendChild(yAxisGroup);
        
        // 模板选择
        const templateGroup = document.createElement('div');
        templateGroup.style.marginBottom = '20px';
        
        const templateLabel = document.createElement('label');
        templateLabel.textContent = '图表模板:';
        templateLabel.style.display = 'block';
        templateLabel.style.marginBottom = '8px';
        templateGroup.appendChild(templateLabel);
        
        const templateSelect = document.createElement('select');
        templateSelect.id = 'chart-template';
        templateSelect.style.width = '100%';
        templateSelect.style.padding = '8px';
        templateSelect.style.borderRadius = '4px';
        templateSelect.style.border = '1px solid #ced4da';
        
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = '选择模板';
        templateSelect.appendChild(defaultOption);
        
        Object.entries(this.chartTemplates).forEach(([key, template]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = template.name;
            templateSelect.appendChild(option);
        });
        
        templateSelect.addEventListener('change', (e) => {
            const templateName = e.target.value;
            if (templateName) {
                const template = this.getChartTemplate(templateName);
                if (template) {
                    document.getElementById('chart-type').value = template.config.type;
                    document.getElementById('chart-title').value = template.config.options.title;
                    document.getElementById('chart-yaxis').value = template.config.options.yAxisLabel;
                }
            }
        });
        
        templateGroup.appendChild(templateSelect);
        configPanel.appendChild(templateGroup);
        
        // 保存配置选项
        const saveGroup = document.createElement('div');
        saveGroup.style.marginBottom = '20px';
        
        const saveLabel = document.createElement('label');
        saveLabel.textContent = '保存配置:';
        saveLabel.style.display = 'block';
        saveLabel.style.marginBottom = '8px';
        saveGroup.appendChild(saveLabel);
        
        const saveInput = document.createElement('input');
        saveInput.type = 'text';
        saveInput.id = 'save-config-name';
        saveInput.placeholder = '配置名称';
        saveInput.style.width = '100%';
        saveInput.style.padding = '8px';
        saveInput.style.borderRadius = '4px';
        saveInput.style.border = '1px solid #ced4da';
        saveGroup.appendChild(saveInput);
        configPanel.appendChild(saveGroup);
        
        // 按钮组
        const buttonGroup = document.createElement('div');
        buttonGroup.style.display = 'flex';
        buttonGroup.style.gap = '10px';
        
        // 创建按钮
        const createButton = document.createElement('button');
        createButton.textContent = '创建图表';
        createButton.style.flex = '1';
        createButton.style.padding = '10px';
        createButton.style.backgroundColor = this.getThemeConfig().colors.primary;
        createButton.style.color = 'white';
        createButton.style.border = 'none';
        createButton.style.borderRadius = '4px';
        createButton.style.cursor = 'pointer';
        
        createButton.addEventListener('click', () => {
            const config = {
                type: document.getElementById('chart-type').value,
                options: {
                    title: document.getElementById('chart-title').value,
                    yAxisLabel: document.getElementById('chart-yaxis').value
                }
            };
            
            // 保存配置（如果提供了名称）
            const saveName = document.getElementById('save-config-name').value;
            if (saveName) {
                this.saveChartConfig(saveName, config);
            }
            
            if (callback) {
                callback(config);
            }
        });
        buttonGroup.appendChild(createButton);
        
        // 取消按钮
        const cancelButton = document.createElement('button');
        cancelButton.textContent = '取消';
        cancelButton.style.flex = '1';
        cancelButton.style.padding = '10px';
        cancelButton.style.backgroundColor = '#6c757d';
        cancelButton.style.color = 'white';
        cancelButton.style.border = 'none';
        cancelButton.style.borderRadius = '4px';
        cancelButton.style.cursor = 'pointer';
        
        cancelButton.addEventListener('click', () => {
            if (callback) {
                callback(null);
            }
        });
        buttonGroup.appendChild(cancelButton);
        configPanel.appendChild(buttonGroup);
        
        container.appendChild(configPanel);
    }
