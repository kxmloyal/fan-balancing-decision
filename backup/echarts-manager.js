// ECharts图表管理器
class MemoryCache {
    constructor() {
        this.cache = new Map();
        this.maxSize = 100;
        this.ttl = 3600000; // 1小时
    }

    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;

        if (Date.now() - item.timestamp > this.ttl) {
            this.cache.delete(key);
            return null;
        }

        return item.value;
    }

    set(key, value) {
        if (this.cache.size >= this.maxSize) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }

        this.cache.set(key, {
            value,
            timestamp: Date.now()
        });
    }

    has(key) {
        return this.cache.has(key);
    }

    delete(key) {
        this.cache.delete(key);
    }

    clear() {
        this.cache.clear();
    }
}

class EChartsManager {
    constructor() {
        this.charts = {};
        this.chartData = {};
        this.loadingStates = {};
        this.resizeObserver = null;
        this.supportedTypes = ['box', 'scatter', 'trend', 'violin', 'heatmap', 'histogram', '3d', 'parallel', 'bubble'];
        this.eventListeners = {};
        this.dataCache = new MemoryCache();
        this.configCache = new MemoryCache();
        this.batchProcessing = false;
        this.batchQueue = [];
        this.initialized = false;
        this.echartsLoaded = false;

        this.initEChartsLibraryCheck();
        this.initResizeObserver();
        this.initResponsiveListeners();
        this.initResponsiveLayoutListeners();
        this.initialized = true;
        console.log('EChartsManager 初始化完成');
    }

    initEChartsLibraryCheck() {
        if (typeof echarts !== 'undefined') {
            this.echartsLoaded = true;
            console.log('ECharts库已加载');
        } else {
            this.echartsLoaded = false;
            console.warn('ECharts库未加载，将在需要时尝试重新检查');
            setTimeout(() => {
                this.checkEChartsLibrary();
            }, 1000);
        }
    }

    checkEChartsLibrary() {
        if (typeof echarts !== 'undefined') {
            if (!this.echartsLoaded) {
                this.echartsLoaded = true;
                console.log('ECharts库加载成功');
            }
            return true;
        } else {
            this.echartsLoaded = false;
            console.warn('ECharts库未加载');
            return false;
        }
    }

    isInitialized() {
        return this.initialized && this.echartsLoaded;
    }

    initResizeObserver() {
        if (typeof ResizeObserver !== 'undefined') {
            this.resizeObserver = new ResizeObserver((entries) => {
                entries.forEach((entry) => {
                    const containerId = entry.target.id;
                    if (this.charts[containerId]) {
                        this.resizeChart(containerId);
                    }
                });
            });
        }
    }

    initChart(containerId, chartType, data, options = {}) {
        console.log(`开始初始化图表: ${containerId}, 类型: ${chartType}`);
        
        try {
            if (!this.initialized) {
                console.error('EChartsManager未初始化');
                this.showError(containerId, '图表管理器未初始化');
                return null;
            }

            if (!this.checkEChartsLibrary()) {
                console.error('ECharts库未加载');
                this.showError(containerId, 'ECharts库未加载');
                return null;
            }

            const container = document.getElementById(containerId);
            if (!container) {
                console.error(`图表容器不存在: ${containerId}`);
                this.showError(containerId, '图表容器不存在');
                return null;
            }

            const cacheKey = `${containerId}_${chartType}_${JSON.stringify(options)}`;
            const dataCacheKey = `${cacheKey}_data`;
            
            const cachedConfig = this.configCache.get(cacheKey);
            const cachedData = this.dataCache.get(dataCacheKey);
            
            if (cachedConfig && cachedData) {
                console.log(`使用缓存的图表配置和数据: ${containerId}`);
                if (this.charts[containerId]) {
                    this.destroyChart(containerId);
                }
                
                this.showLoading(containerId);
                
                try {
                    const renderer = window.devicePixelRatio > 1 ? 'canvas' : 'svg';
                    const chart = echarts.init(container, null, {
                        renderer: renderer,
                        devicePixelRatio: window.devicePixelRatio || 1,
                        lazyUpdate: true
                    });
                    
                    this.charts[containerId] = chart;
                    this.chartData[containerId] = cachedData;
                    
                    chart.setOption(cachedConfig);
                    
                    const resizeHandler = this.debounce(() => {
                        if (this.charts[containerId]) {
                            try {
                                this.resizeChart(containerId);
                            } catch (resizeError) {
                                console.warn('调整图表大小时出错:', resizeError.message);
                            }
                        }
                    }, 100);
                    
                    window.addEventListener('resize', resizeHandler);
                    if (!this.eventListeners[containerId]) {
                        this.eventListeners[containerId] = [];
                    }
                    this.eventListeners[containerId].push(resizeHandler);
                    
                    if (this.resizeObserver) {
                        this.resizeObserver.observe(container);
                    }
                    
                    this.hideLoading(containerId);
                    console.log(`使用缓存初始化图表成功: ${containerId}`);
                    return chart;
                } catch (cacheError) {
                    console.error('使用缓存初始化图表时出错:', cacheError);
                    console.error('错误详情:', cacheError.stack);
                    this.hideLoading(containerId);
                    this.showError(containerId, '图表初始化失败');
                    return null;
                }
            }

            this.showLoading(containerId);

            if (this.charts[containerId]) {
                this.destroyChart(containerId);
            }

            if (!data) {
                console.warn('图表数据为空:', containerId);
                this.hideLoading(containerId);
                this.showError(containerId, '暂无数据');
                return null;
            }

            if (Array.isArray(data) && data.length === 0) {
                console.warn('图表数据为空数组:', containerId);
                this.hideLoading(containerId);
                this.showError(containerId, '暂无数据');
                return null;
            }

            if (!chartType || !this.supportedTypes.includes(chartType)) {
                console.error(`不支持的图表类型: ${chartType}`);
                this.hideLoading(containerId);
                this.showError(containerId, `不支持的图表类型: ${chartType}`);
                return null;
            }

            if (typeof data !== 'object') {
                console.error('图表数据类型错误，期望对象或数组:', typeof data);
                this.hideLoading(containerId);
                this.showError(containerId, '图表数据格式错误');
                return null;
            }

            if (!this.validateChartData(data, chartType, containerId)) {
                console.warn(`数据格式与图表类型不匹配: ${containerId}, 类型: ${chartType}`);
                this.hideLoading(containerId);
                this.showError(containerId, '图表数据格式错误');
                return null;
            }

            try {
                console.log(`开始创建ECharts实例: ${containerId}`);
                console.log(`图表类型: ${chartType}`);
                console.log(`图表数据长度: ${Array.isArray(data) ? data.length : '对象'}`);
                
                const renderer = window.devicePixelRatio > 1 ? 'canvas' : 'svg';
                console.log(`选择的渲染器: ${renderer}`);
                
                const chart = echarts.init(container, null, {
                    renderer: renderer,
                    devicePixelRatio: window.devicePixelRatio || 1,
                    lazyUpdate: true,
                    useDirtyRect: true
                });
                
                console.log(`ECharts实例创建成功: ${containerId}`);
                this.charts[containerId] = chart;
                this.chartData[containerId] = data;
                
                const resizeHandler = this.debounce(() => {
                    if (this.charts[containerId]) {
                        try {
                            this.resizeChart(containerId);
                            console.log(`图表大小调整成功: ${containerId}`);
                        } catch (resizeError) {
                            console.warn('调整图表大小时出错:', resizeError.message);
                        }
                    }
                }, 100);
                
                window.addEventListener('resize', resizeHandler);
                if (!this.eventListeners[containerId]) {
                    this.eventListeners[containerId] = [];
                }
                this.eventListeners[containerId].push(resizeHandler);
                
                if (this.resizeObserver) {
                    this.resizeObserver.observe(container);
                    console.log(`已添加到ResizeObserver: ${containerId}`);
                }
                console.log(`ECharts实例配置完成: ${containerId}`);
            } catch (initError) {
                console.error('创建ECharts实例时出错:', initError);
                console.error('错误详情:', initError.stack);
                this.hideLoading(containerId);
                this.showError(containerId, '图表实例创建失败');
                return null;
            }

            try {
                this.renderChart(containerId, chartType, data, options);
                
                const chart = this.charts[containerId];
                if (chart) {
                    const currentOption = chart.getOption();
                    this.configCache.set(cacheKey, currentOption);
                    this.dataCache.set(dataCacheKey, data);
                    console.log(`图表配置和数据已缓存: ${containerId}`);
                }
            } catch (renderError) {
                console.error('渲染ECharts图表时出错:', renderError);
                console.error('错误详情:', renderError.stack);
                this.hideLoading(containerId);
                this.showError(containerId, '图表渲染失败');
                return null;
            }

            // 应用响应式布局
            this.responsiveResize(containerId);
            
            this.hideLoading(containerId);
            console.log(`ECharts图表初始化成功: ${containerId}`);
            return this.charts[containerId];
        } catch (error) {
            console.error('初始化ECharts图表时出错:', error);
            console.error('错误详情:', error.stack);
            this.hideLoading(containerId);
            this.showError(containerId, `图表初始化失败: ${error.message}`);
            return null;
        }
    }

    validateChartData(data, chartType, containerId) {
        try {
            console.log(`[图表 ${containerId}] 开始验证数据格式，图表类型: ${chartType}`);
            console.log(`[图表 ${containerId}] 原始数据: ${JSON.stringify(data)}`);
            console.log(`[图表 ${containerId}] 数据类型: ${typeof data}, 是否为数组: ${Array.isArray(data)}, 长度: ${Array.isArray(data) ? data.length : (typeof data === 'object' ? Object.keys(data).length : '非对象')}`);
            
            // 首先检查data是否为基本类型
            if (data === null || typeof data !== 'object') {
                console.warn(`[图表 ${containerId}] 图表数据类型错误: ${typeof data}，期望对象或数组`);
                return false;
            }
            
            // 检查data是否为数组
            if (!Array.isArray(data)) {
                console.warn(`[图表 ${containerId}] 图表数据不是数组: ${typeof data}`);
                return false;
            }
            
            // 检查数组是否为空
            if (data.length === 0) {
                console.warn(`[图表 ${containerId}] 图表数据数组为空`);
                return false;
            }
            
            switch (chartType) {
                case 'box':
                    console.log(`[图表 ${containerId}] 验证箱线图数据格式`);
                    let boxValidationError = false;
                    data.forEach((item, index) => {
                        console.log(`[图表 ${containerId}] 验证箱线图数据元素 ${index}: ${JSON.stringify(item)}`);
                        if (typeof item !== 'object' || item === null) {
                            console.warn(`[图表 ${containerId}] 箱线图数据元素 ${index} 不是对象: ${typeof item}`);
                            boxValidationError = true;
                        } else if (!('name' in item)) {
                            console.warn(`[图表 ${containerId}] 箱线图数据元素 ${index} 缺少name属性`);
                            boxValidationError = true;
                        } else if (!('data' in item)) {
                            console.warn(`[图表 ${containerId}] 箱线图数据元素 ${index} 缺少data属性`);
                            boxValidationError = true;
                        } else if (!Array.isArray(item.data)) {
                            console.warn(`[图表 ${containerId}] 箱线图数据元素 ${index} 的data不是数组: ${typeof item.data}`);
                            boxValidationError = true;
                        } else if (item.data.length !== 5) {
                            console.warn(`[图表 ${containerId}] 箱线图数据元素 ${index} 的data长度不是5: ${item.data.length}`);
                            boxValidationError = true;
                        } else {
                            console.log(`[图表 ${containerId}] 箱线图数据元素 ${index} 验证通过`);
                        }
                    });
                    return !boxValidationError;
                case 'trend':
                    console.log(`[图表 ${containerId}] 验证趋势图数据格式`);
                    return data.every((item, index) => {
                        if (typeof item !== 'object' || item === null) {
                            console.warn(`[图表 ${containerId}] 趋势图数据元素 ${index} 不是对象: ${typeof item}`);
                            return false;
                        } else if (!('name' in item)) {
                            console.warn(`[图表 ${containerId}] 趋势图数据元素 ${index} 缺少name属性`);
                            return false;
                        } else if (!('value' in item)) {
                            console.warn(`[图表 ${containerId}] 趋势图数据元素 ${index} 缺少value属性`);
                            return false;
                        } else if (typeof item.value !== 'number') {
                            console.warn(`[图表 ${containerId}] 趋势图数据元素 ${index} 的value不是数字: ${typeof item.value}`);
                            return false;
                        }
                        return true;
                    });
                case 'scatter':
                    console.log(`[图表 ${containerId}] 验证散点图数据格式`);
                    return data.every((item, index) => {
                        if (!Array.isArray(item)) {
                            console.warn(`[图表 ${containerId}] 散点图数据元素 ${index} 不是数组: ${typeof item}`);
                            return false;
                        } else if (item.length !== 2) {
                            console.warn(`[图表 ${containerId}] 散点图数据元素 ${index} 长度不是2: ${item.length}`);
                            return false;
                        }
                        return true;
                    });
                case 'heatmap':
                    console.log(`[图表 ${containerId}] 验证热力图数据格式`);
                    return data.every((item, index) => {
                        if (!Array.isArray(item)) {
                            console.warn(`[图表 ${containerId}] 热力图数据元素 ${index} 不是数组: ${typeof item}`);
                            return false;
                        } else if (item.length !== 3) {
                            console.warn(`[图表 ${containerId}] 热力图数据元素 ${index} 长度不是3: ${item.length}`);
                            return false;
                        }
                        return true;
                    });
                case 'histogram':
                    console.log(`[图表 ${containerId}] 验证直方图数据格式`);
                    return data.every((item, index) => {
                        if (typeof item !== 'number') {
                            console.warn(`[图表 ${containerId}] 直方图数据元素 ${index} 不是数字: ${typeof item}`);
                            return false;
                        }
                        return true;
                    });
                case 'bubble':
                    console.log(`[图表 ${containerId}] 验证气泡图数据格式`);
                    return data.every((item, index) => {
                        if (typeof item !== 'object' || item === null) {
                            console.warn(`[图表 ${containerId}] 气泡图数据元素 ${index} 不是对象: ${typeof item}`);
                            return false;
                        } else if (!('name' in item)) {
                            console.warn(`[图表 ${containerId}] 气泡图数据元素 ${index} 缺少name属性`);
                            return false;
                        } else if (!('value' in item)) {
                            console.warn(`[图表 ${containerId}] 气泡图数据元素 ${index} 缺少value属性`);
                            return false;
                        } else if (!Array.isArray(item.value)) {
                            console.warn(`[图表 ${containerId}] 气泡图数据元素 ${index} 的value不是数组: ${typeof item.value}`);
                            return false;
                        } else if (item.value.length !== 3) {
                            console.warn(`[图表 ${containerId}] 气泡图数据元素 ${index} 的value长度不是3: ${item.value.length}`);
                            return false;
                        }
                        return true;
                    });
                case 'violin':
                    console.log(`[图表 ${containerId}] 验证小提琴图数据格式`);
                    return data.every((item, index) => {
                        if (typeof item !== 'object' || item === null) {
                            console.warn(`[图表 ${containerId}] 小提琴图数据元素 ${index} 不是对象: ${typeof item}`);
                            return false;
                        } else if (!('name' in item)) {
                            console.warn(`[图表 ${containerId}] 小提琴图数据元素 ${index} 缺少name属性`);
                            return false;
                        } else if (!('data' in item)) {
                            console.warn(`[图表 ${containerId}] 小提琴图数据元素 ${index} 缺少data属性`);
                            return false;
                        } else if (!Array.isArray(item.data)) {
                            console.warn(`[图表 ${containerId}] 小提琴图数据元素 ${index} 的data不是数组: ${typeof item.data}`);
                            return false;
                        }
                        return true;
                    });
                case '3d':
                    console.log(`[图表 ${containerId}] 验证3D散点图数据格式`);
                    return data.every((item, index) => {
                        if (!Array.isArray(item)) {
                            console.warn(`[图表 ${containerId}] 3D散点图数据元素 ${index} 不是数组: ${typeof item}`);
                            return false;
                        } else if (item.length !== 3) {
                            console.warn(`[图表 ${containerId}] 3D散点图数据元素 ${index} 长度不是3: ${item.length}`);
                            return false;
                        }
                        return true;
                    });
                case 'parallel':
                    console.log(`[图表 ${containerId}] 验证平行坐标图数据格式`);
                    return data.every((item, index) => {
                        if (!Array.isArray(item)) {
                            console.warn(`[图表 ${containerId}] 平行坐标图数据元素 ${index} 不是数组: ${typeof item}`);
                            return false;
                        } else if (item.length < 2) {
                            console.warn(`[图表 ${containerId}] 平行坐标图数据元素 ${index} 长度小于2: ${item.length}`);
                            return false;
                        }
                        return true;
                    });
                default:
                    console.warn(`[图表 ${containerId}] 未知的图表类型: ${chartType}`);
                    return true;
            }
        } catch (error) {
            console.error(`[图表 ${containerId}] 验证数据格式时出错: ${error.message}`);
            console.error(`[图表 ${containerId}] 错误详情: ${error.stack}`);
            return false;
        }
    }

    renderChart(containerId, chartType, data, options = {}) {
        const chart = this.charts[containerId];
        if (!chart) {
            console.warn(`图表实例不存在: ${containerId}`);
            return;
        }

        try {
            let option = {};

            if (!this.supportedTypes.includes(chartType)) {
                console.warn(`未支持的图表类型: ${chartType}`);
                this.showError(containerId, `不支持的图表类型: ${chartType}`);
                return;
            }

            if (!data || (Array.isArray(data) && data.length === 0)) {
                console.warn(`图表数据为空: ${containerId}`);
                this.showError(containerId, '图表数据为空');
                return;
            }

            console.log(`开始渲染图表: ${containerId}, 类型: ${chartType}`);
            
            const dataSize = Array.isArray(data) ? data.length : Object.keys(data).length;
            const isLargeData = dataSize > 1000;
            
            if (isLargeData) {
                console.log(`检测到大数据集: ${dataSize} 数据点，启用性能优化`);
                options = { ...options, largeData: true };
            }

            switch (chartType) {
                case 'box':
                    option = this.createBoxPlotOption(data, options);
                    break;
                case 'scatter':
                    option = this.createScatterPlotOption(data, options);
                    break;
                case 'trend':
                    option = this.createTrendPlotOption(data, options);
                    break;
                case 'violin':
                    option = this.createViolinPlotOption(data, options);
                    break;
                case 'heatmap':
                    option = this.createHeatmapOption(data, options);
                    break;
                case 'histogram':
                    option = this.createHistogramOption(data, options);
                    break;
                case '3d':
                    option = this.create3DScatterOption(data, options);
                    break;
                case 'parallel':
                    option = this.createParallelOption(data, options);
                    break;
                case 'bubble':
                    option = this.createBubbleOption(data, options);
                    break;
                default:
                    console.warn(`未支持的图表类型: ${chartType}`);
                    this.showError(containerId, `不支持的图表类型: ${chartType}`);
                    return;
            }

            if (!option || typeof option !== 'object') {
                console.error('图表配置生成失败');
                this.showError(containerId, '图表配置生成失败');
                return;
            }

            const responsiveConfig = this.getResponsiveConfig(containerId);
            option = this.mergeOptions(option, responsiveConfig);

            if (isLargeData) {
                option = this.mergeOptions(option, {
                    animation: false,
                    animationDuration: 0,
                    animationEasing: 'linear',
                    animationThreshold: 10000,
                    progressive: 1000,
                    progressiveThreshold: 1000,
                    tooltip: {
                        confine: true
                    },
                    series: option.series?.map((series) => ({
                        ...series,
                        large: true,
                        largeThreshold: 2000,
                        symbolSize: 4,
                        itemStyle: {
                            ...series.itemStyle,
                            opacity: 0.6
                        }
                    }))
                });
            }

            console.log(`图表配置生成成功: ${containerId}, 类型: ${chartType}`);

            chart.setOption(option, true);
            console.log(`ECharts图表渲染成功: ${containerId} (${chartType})`);
        } catch (error) {
            console.error('渲染ECharts图表时出错:', error);
            console.error('错误详情:', error.stack);
            this.showError(containerId, `图表渲染失败: ${error.message}`);
        }
    }

    resizeChart(containerId) {
        const chart = this.charts[containerId];
        if (chart) {
            try {
                chart.resize({
                    animation: {
                        duration: 300
                    }
                });
            } catch (error) {
                console.warn('调整图表大小时出错:', error.message);
            }
        }
    }

    destroyChart(containerId) {
        const chart = this.charts[containerId];
        if (chart && typeof chart.dispose === 'function') {
            try {
                chart.dispose();
                console.log(`已销毁图表实例: ${containerId}`);
            } catch (error) {
                console.warn('销毁图表实例时出错:', error.message);
            }
        }
        delete this.charts[containerId];
        delete this.chartData[containerId];
        delete this.loadingStates[containerId];

        if (this.eventListeners[containerId]) {
            this.eventListeners[containerId].forEach(listener => {
                window.removeEventListener('resize', listener);
            });
            delete this.eventListeners[containerId];
        }

        const container = document.getElementById(containerId);
        if (container && this.resizeObserver) {
            this.resizeObserver.unobserve(container);
        }
    }

    destroyAllCharts() {
        Object.keys(this.charts).forEach(containerId => {
            this.destroyChart(containerId);
        });
        this.charts = {};
        this.chartData = {};
        this.loadingStates = {};
        this.eventListeners = {};
        
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        
        console.log('所有图表实例已销毁');
    }

    resizeAllCharts() {
        const resizeHandler = this.throttle(() => {
            Object.keys(this.charts).forEach(containerId => {
                this.resizeChart(containerId);
            });
        }, 100);
        
        resizeHandler();
    }

    initResponsiveListeners() {
        const resizeHandler = this.throttle(() => {
            this.resizeAllCharts();
        }, 100);
        
        window.addEventListener('resize', resizeHandler);
        
        if (window.matchMedia) {
            const orientationHandler = this.throttle(() => {
                this.resizeAllCharts();
            }, 100);
            
            window.matchMedia('(orientation: portrait)').addEventListener('change', orientationHandler);
        }
        
        console.log('响应式监听已初始化');
    }

    getResponsiveConfig(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return {};
        
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        const isTablet = window.innerWidth >= 768 && window.innerWidth < 1024;
        
        console.log(`响应式配置检测: 宽度=${width}, 高度=${height}, 移动设备=${isMobile}, 平板=${isTablet}`);
        
        if (width < 480 || isMobile) {
            return {
                title: {
                    textStyle: {
                        fontSize: 10
                    }
                },
                legend: {
                    show: false
                },
                tooltip: {
                    position: 'top',
                    confine: true
                },
                xAxis: {
                    axisLabel: {
                        fontSize: 8,
                        rotate: 60,
                        interval: 'auto'
                    }
                },
                yAxis: {
                    axisLabel: {
                        fontSize: 8
                    }
                }
            };
        } else if (width < 768 || isTablet) {
            return {
                title: {
                    textStyle: {
                        fontSize: 12
                    }
                },
                legend: {
                    show: false,
                    textStyle: {
                        fontSize: 10
                    }
                },
                tooltip: {
                    position: 'top'
                },
                xAxis: {
                    axisLabel: {
                        fontSize: 9,
                        rotate: 45
                    }
                },
                yAxis: {
                    axisLabel: {
                        fontSize: 9
                    }
                }
            };
        } else if (width < 992) {
            return {
                title: {
                    textStyle: {
                        fontSize: 14
                    }
                },
                legend: {
                    show: true,
                    textStyle: {
                        fontSize: 11
                    }
                },
                tooltip: {
                    position: 'top'
                },
                xAxis: {
                    axisLabel: {
                        fontSize: 11,
                        rotate: 45
                    }
                },
                yAxis: {
                    axisLabel: {
                        fontSize: 11
                    }
                }
            };
        } else if (width < 1200) {
            return {
                title: {
                    textStyle: {
                        fontSize: 15
                    }
                },
                legend: {
                    show: true,
                    textStyle: {
                        fontSize: 12
                    }
                },
                tooltip: {
                    position: 'top'
                },
                xAxis: {
                    axisLabel: {
                        fontSize: 12,
                        rotate: 45
                    }
                },
                yAxis: {
                    axisLabel: {
                        fontSize: 12
                    }
                }
            };
        } else {
            return {
                title: {
                    textStyle: {
                        fontSize: 16
                    }
                },
                legend: {
                    show: true,
                    textStyle: {
                        fontSize: 13
                    }
                },
                tooltip: {
                    position: 'top'
                },
                xAxis: {
                    axisLabel: {
                        fontSize: 13,
                        rotate: 45
                    }
                },
                yAxis: {
                    axisLabel: {
                        fontSize: 13
                    }
                }
            };
        }
    }
    
    responsiveResize(containerId) {
        const container = document.getElementById(containerId);
        const chart = this.charts[containerId];
        
        if (!container || !chart) return;
        
        const width = container.clientWidth;
        
        if (width < 480) {
            container.style.height = '250px';
        } else if (width < 768) {
            container.style.height = '300px';
        } else if (width < 1200) {
            container.style.height = '400px';
        } else {
            container.style.height = '500px';
        }
        
        this.resizeChart(containerId);
    }
    
    initResponsiveLayoutListeners() {
        const resizeHandler = this.debounce(() => {
            Object.keys(this.charts).forEach(containerId => {
                this.responsiveResize(containerId);
            });
        }, 150);
        
        window.addEventListener('resize', resizeHandler);
        
        if (window.matchMedia) {
            const orientationHandler = this.debounce(() => {
                Object.keys(this.charts).forEach(containerId => {
                    this.responsiveResize(containerId);
                });
            }, 150);
            
            window.matchMedia('(orientation: portrait)').addEventListener('change', orientationHandler);
        }
        
        console.log('响应式布局监听器已初始化');
    }

    showLoading(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.classList.add('loading');
            this.loadingStates[containerId] = true;
            container.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <p class="mt-2 text-muted">图表加载中...</p>
                </div>
            `;
        }
    }

    hideLoading(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.classList.remove('loading');
            this.loadingStates[containerId] = false;
        }
    }

    showError(containerId, message) {
        const container = document.getElementById(containerId);
        if (container) {
            container.classList.remove('loading');
            container.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                    <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem; margin-bottom: 10px;"></i>
                    <p class="text-danger text-center">${message}</p>
                </div>
            `;
        }
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    mergeOptions(target, source) {
        if (!source) return target;
        
        const result = { ...target };
        for (const key in source) {
            if (source.hasOwnProperty(key)) {
                if (typeof source[key] === 'object' && source[key] !== null && !Array.isArray(source[key])) {
                    result[key] = this.mergeOptions(result[key] || {}, source[key]);
                } else {
                    result[key] = source[key];
                }
            }
        }
        return result;
    }

    batchInitCharts(chartConfigs) {
        if (!Array.isArray(chartConfigs)) return;
        
        this.batchProcessing = true;
        this.batchQueue = chartConfigs;
        
        console.log(`开始批量初始化图表，共 ${chartConfigs.length} 个图表`);
        
        const devicePerformance = this.detectDevicePerformance();
        const batchSize = devicePerformance === 'high' ? 5 : devicePerformance === 'medium' ? 3 : 2;
        
        console.log(`根据设备性能调整批处理大小: ${batchSize}`);
        
        const batches = [];
        
        for (let i = 0; i < chartConfigs.length; i += batchSize) {
            batches.push(chartConfigs.slice(i, i + batchSize));
        }
        
        batches.forEach((batch, index) => {
            setTimeout(() => {
                console.log(`处理第 ${index + 1} 批次，共 ${batch.length} 个图表`);
                
                requestAnimationFrame(() => {
                    batch.forEach(config => {
                        this.initChart(
                            config.containerId,
                            config.chartType,
                            config.data,
                            config.options
                        );
                    });
                });
            }, index * 150);
        });
        
        setTimeout(() => {
            this.batchProcessing = false;
            this.batchQueue = [];
            console.log('批量初始化图表完成');
        }, batches.length * 150 + 1000);
    }
    
    detectDevicePerformance() {
        if (typeof navigator === 'undefined') return 'medium';
        
        const deviceMemory = navigator.deviceMemory || 4;
        const hardwareConcurrency = navigator.hardwareConcurrency || 4;
        
        console.log(`设备性能检测: 内存 ${deviceMemory}GB, CPU核心数 ${hardwareConcurrency}`);
        
        if (deviceMemory >= 8 && hardwareConcurrency >= 8) {
            return 'high';
        } else if (deviceMemory >= 4 && hardwareConcurrency >= 4) {
            return 'medium';
        } else {
            return 'low';
        }
    }

    createBoxPlotOption(data, options = {}) {
        const { title = '箱线图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
        
        const seriesData = this.convertToBoxPlotData(data);
        const xAxisData = seriesData.map(item => item.name);
        const boxData = seriesData.map(item => item.data);
        
        // 提取中位数数据用于折线图
        const medianData = seriesData.map(item => item.data[2]);

        return {
            title: {
                text: title,
                left: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                },
                formatter: function(params) {
                    let result = '';
                    params.forEach((param) => {
                        if (param.seriesName === '箱线图') {
                            const boxData = param.data;
                            result += `
                                <div style="padding: 10px;">
                                    <h6 style="margin: 0 0 5px 0; color: ${color};">${param.name}</h6>
                                    <div style="line-height: 1.6;">
                                        <p>最小值: <strong>${boxData[0].toFixed(2)}</strong></p>
                                        <p>第一四分位数: <strong>${boxData[1].toFixed(2)}</strong></p>
                                        <p>中位数: <strong>${boxData[2].toFixed(2)}</strong></p>
                                        <p>第三四分位数: <strong>${boxData[3].toFixed(2)}</strong></p>
                                        <p>最大值: <strong>${boxData[4].toFixed(2)}</strong></p>
                                    </div>
                                </div>
                            `;
                        } else if (param.seriesName === '中位数连线') {
                            result += `
                                <div style="padding: 10px;">
                                    <h6 style="margin: 0 0 5px 0; color: #ff7f0e;">${param.seriesName}</h6>
                                    <div style="line-height: 1.6;">
                                        <p>中位数: <strong>${param.value.toFixed(2)}</strong></p>
                                    </div>
                                </div>
                            `;
                        }
                    });
                    return result;
                },
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: color,
                borderWidth: 1,
                borderRadius: 5
            },
            legend: {
                data: ['箱线图', '中位数连线'],
                bottom: 10,
                textStyle: {
                    fontSize: 12
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: xAxisData,
                axisLabel: {
                    rotate: 45,
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                }
            },
            yAxis: {
                type: 'value',
                name: yAxisLabel,
                nameTextStyle: {
                    fontSize: 12
                },
                axisLabel: {
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#f0f0f0',
                        type: 'dashed'
                    }
                }
            },
            series: [{
                name: '箱线图',
                type: 'boxplot',
                data: boxData,
                itemStyle: {
                    color: color,
                    borderWidth: 1
                },
                emphasis: {
                    itemStyle: {
                        color: color,
                        borderWidth: 2
                    }
                },
                label: {
                    show: false,
                    position: 'top'
                }
            }, {
                name: '中位数连线',
                type: 'line',
                data: medianData,
                smooth: false,
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: {
                    color: '#ff7f0e',
                    width: 2
                },
                itemStyle: {
                    color: '#ff7f0e',
                    borderWidth: 2,
                    borderColor: '#fff'
                },
                emphasis: {
                    itemStyle: {
                        symbolSize: 8,
                        shadowBlur: 10,
                        shadowColor: 'rgba(0, 0, 0, 0.3)'
                    }
                }
            }],
            toolbox: {
                feature: {
                    dataZoom: {
                        yAxisIndex: 'none'
                    },
                    restore: {},
                    saveAsImage: {
                        pixelRatio: 2,
                        backgroundColor: '#fff'
                    }
                },
                right: 10,
                top: 10
            },
            dataZoom: [
                {
                    type: 'inside',
                    start: 0,
                    end: 100,
                    xAxisIndex: [0]
                },
                {
                    start: 0,
                    end: 100,
                    xAxisIndex: [0]
                }
            ]
        };
    }

    createScatterPlotOption(data, options = {}) {
        const { title = '散点图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
        
        const seriesData = this.convertToScatterData(data);
        const xAxisData = [...new Set(seriesData.map(item => item[0]))];

        return {
            title: {
                text: title,
                left: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                trigger: 'item',
                formatter: function(params) {
                    return `
                        <div style="padding: 10px;">
                            <h6 style="margin: 0 0 5px 0; color: ${color};">散点数据</h6>
                            <div style="line-height: 1.6;">
                                <p>转速: <strong>${params.data[0]}</strong></p>
                                <p>不平衡量: <strong>${params.data[1].toFixed(2)}</strong></p>
                            </div>
                        </div>
                    `;
                },
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: color,
                borderWidth: 1,
                borderRadius: 5
            },
            legend: {
                data: ['散点图'],
                bottom: 10,
                textStyle: {
                    fontSize: 12
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: xAxisData,
                axisLabel: {
                    rotate: 45,
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                }
            },
            yAxis: {
                type: 'value',
                name: yAxisLabel,
                nameTextStyle: {
                    fontSize: 12
                },
                axisLabel: {
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#f0f0f0',
                        type: 'dashed'
                    }
                }
            },
            series: [{
                name: '散点图',
                type: 'scatter',
                data: seriesData.map(item => [item[0], item[1]]),
                itemStyle: {
                    color: color,
                    opacity: 0.8
                },
                emphasis: {
                    itemStyle: {
                        color: color,
                        opacity: 1,
                        shadowBlur: 10,
                        shadowColor: 'rgba(0, 0, 0, 0.3)'
                    }
                },
                symbolSize: 8,
                symbol: 'circle'
            }],
            toolbox: {
                feature: {
                    dataZoom: {
                        yAxisIndex: 'none'
                    },
                    restore: {},
                    saveAsImage: {
                        pixelRatio: 2,
                        backgroundColor: '#fff'
                    }
                },
                right: 10,
                top: 10
            },
            dataZoom: [
                {
                    type: 'inside',
                    start: 0,
                    end: 100
                },
                {
                    start: 0,
                    end: 100
                }
            ]
        };
    }

    createTrendPlotOption(data, options = {}) {
        const { title = '趋势图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
        
        const seriesData = this.convertToTrendData(data);
        const xAxisData = seriesData.map(item => item.name);
        const yAxisData = seriesData.map(item => item.value);

        return {
            title: {
                text: title,
                left: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    return `
                        <div style="padding: 10px;">
                            <h6 style="margin: 0 0 5px 0; color: ${color};">趋势数据</h6>
                            <div style="line-height: 1.6;">
                                <p>转速: <strong>${params[0].name}</strong></p>
                                <p>不平衡量: <strong>${params[0].value.toFixed(2)}</strong></p>
                            </div>
                        </div>
                    `;
                },
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: color,
                borderWidth: 1,
                borderRadius: 5
            },
            legend: {
                data: ['趋势线'],
                bottom: 10,
                textStyle: {
                    fontSize: 12
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: xAxisData,
                axisLabel: {
                    rotate: 45,
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                }
            },
            yAxis: {
                type: 'value',
                name: yAxisLabel,
                nameTextStyle: {
                    fontSize: 12
                },
                axisLabel: {
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#f0f0f0',
                        type: 'dashed'
                    }
                }
            },
            series: [{
                name: '趋势线',
                type: 'line',
                data: yAxisData,
                smooth: true,
                symbol: 'circle',
                symbolSize: 8,
                lineStyle: {
                    color: color,
                    width: 3
                },
                itemStyle: {
                    color: color,
                    shadowBlur: 3,
                    shadowColor: 'rgba(0, 0, 0, 0.2)'
                },
                emphasis: {
                    itemStyle: {
                        symbolSize: 12,
                        shadowBlur: 6,
                        shadowColor: 'rgba(0, 0, 0, 0.3)'
                    }
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: color + '80' },
                        { offset: 1, color: color + '10' }
                    ])
                }
            }],
            toolbox: {
                feature: {
                    dataZoom: {
                        yAxisIndex: 'none'
                    },
                    restore: {},
                    saveAsImage: {
                        pixelRatio: 2,
                        backgroundColor: '#fff'
                    }
                },
                right: 10,
                top: 10
            },
            dataZoom: [
                {
                    type: 'inside',
                    start: 0,
                    end: 100
                },
                {
                    start: 0,
                    end: 100
                }
            ]
        };
    }

    createViolinPlotOption(data, options = {}) {
        const { title = '小提琴图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
        
        const seriesData = this.convertToViolinData(data);

        return {
            title: {
                text: title,
                left: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                trigger: 'item',
                axisPointer: {
                    type: 'shadow'
                },
                formatter: function(params) {
                    return `
                        <div style="padding: 10px;">
                            <h6 style="margin: 0 0 5px 0; color: ${color};">${params.name}</h6>
                            <div style="line-height: 1.6;">
                                <p>数据点数量: <strong>${params.data.length}</strong></p>
                                <p>最小值: <strong>${Math.min(...params.data).toFixed(2)}</strong></p>
                                <p>最大值: <strong>${Math.max(...params.data).toFixed(2)}</strong></p>
                                <p>平均值: <strong>${(params.data.reduce((a, b) => a + b, 0) / params.data.length).toFixed(2)}</strong></p>
                            </div>
                        </div>
                    `;
                },
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: color,
                borderWidth: 1,
                borderRadius: 5
            },
            legend: {
                data: ['小提琴图'],
                bottom: 10,
                textStyle: {
                    fontSize: 12
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: seriesData.map(item => item.name),
                axisLabel: {
                    rotate: 45,
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                }
            },
            yAxis: {
                type: 'value',
                name: yAxisLabel,
                nameTextStyle: {
                    fontSize: 12
                },
                axisLabel: {
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#f0f0f0',
                        type: 'dashed'
                    }
                }
            },
            series: [{
                name: '小提琴图',
                type: 'violin',
                data: seriesData.map(item => item.data),
                itemStyle: {
                    color: color,
                    borderWidth: 1
                },
                emphasis: {
                    itemStyle: {
                        color: color,
                        borderWidth: 2
                    }
                },
                markArea: {
                    itemStyle: {
                        color: 'rgba(255, 173, 177, 0.4)'
                    }
                },
                boxplot: {
                    visible: true,
                    itemStyle: {
                        color: '#333'
                    }
                }
            }],
            toolbox: {
                feature: {
                    dataZoom: {
                        yAxisIndex: 'none'
                    },
                    restore: {},
                    saveAsImage: {
                        pixelRatio: 2,
                        backgroundColor: '#fff'
                    }
                },
                right: 10,
                top: 10
            },
            dataZoom: [
                {
                    type: 'inside',
                    start: 0,
                    end: 100
                },
                {
                    start: 0,
                    end: 100
                }
            ]
        };
    }

    createHeatmapOption(data, options = {}) {
        const { title = '热力图', yAxisLabel = '数据点' } = options;
        
        const seriesData = this.convertToHeatmapData(data);
        const xAxisData = [...new Set(seriesData.map(item => item[0]))];
        const yAxisData = [...new Set(seriesData.map(item => item[1]))];
        const heatmapData = seriesData.map(item => [xAxisData.indexOf(item[0]), yAxisData.indexOf(item[1]), item[2]]);
        
        const min = Math.min(...seriesData.map(item => item[2]));
        const max = Math.max(...seriesData.map(item => item[2]));

        return {
            title: {
                text: title,
                left: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                position: 'top',
                formatter: function(params) {
                    return `
                        <div style="padding: 10px;">
                            <h6 style="margin: 0 0 5px 0;">热力图数据</h6>
                            <div style="line-height: 1.6;">
                                <p>转速: <strong>${xAxisData[params.data[0]]}</strong></p>
                                <p>数据点: <strong>${yAxisData[params.data[1]]}</strong></p>
                                <p>不平衡量: <strong>${params.data[2].toFixed(2)}</strong></p>
                            </div>
                        </div>
                    `;
                },
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: '#1f77b4',
                borderWidth: 1,
                borderRadius: 5
            },
            grid: {
                height: '60%',
                top: '10%',
                left: '3%',
                right: '4%',
                bottom: '20%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: xAxisData,
                splitArea: {
                    show: true,
                    areaStyle: {
                        color: ['#fff', '#f5f5f5']
                    }
                },
                axisLabel: {
                    rotate: 45,
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                }
            },
            yAxis: {
                type: 'category',
                data: yAxisData,
                splitArea: {
                    show: true,
                    areaStyle: {
                        color: ['#fff', '#f5f5f5']
                    }
                },
                name: yAxisLabel,
                nameTextStyle: {
                    fontSize: 12
                },
                axisLabel: {
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                }
            },
            visualMap: {
                min: min,
                max: max,
                calculable: true,
                orient: 'horizontal',
                left: 'center',
                bottom: '10%',
                textStyle: {
                    fontSize: 11
                },
                inRange: {
                    color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
                },
                borderColor: '#ccc',
                borderWidth: 1
            },
            series: [{
                name: '热力图',
                type: 'heatmap',
                data: heatmapData,
                label: {
                    show: true,
                    fontSize: 9,
                    color: '#333'
                },
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    },
                    label: {
                        show: true,
                        fontSize: 11,
                        fontWeight: 'bold'
                    }
                },
                itemStyle: {
                    borderRadius: 2
                }
            }],
            toolbox: {
                feature: {
                    dataZoom: {
                        yAxisIndex: 'none'
                    },
                    restore: {},
                    saveAsImage: {
                        pixelRatio: 2,
                        backgroundColor: '#fff'
                    }
                },
                right: 10,
                top: 10
            },
            dataZoom: [
                {
                    type: 'inside',
                    start: 0,
                    end: 100
                },
                {
                    start: 0,
                    end: 100
                }
            ]
        };
    }

    createHistogramOption(data, options = {}) {
        const { title = '直方图', color = '#1f77b4', xAxisLabel = '不平衡量（单位：g·mm）' } = options;
        
        const seriesData = this.convertToHistogramData(data);

        return {
            title: {
                text: title,
                left: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    return `
                        <div style="padding: 10px;">
                            <h6 style="margin: 0 0 5px 0; color: ${color};">直方图数据</h6>
                            <div style="line-height: 1.6;">
                                <p>区间: <strong>${params[0].name}</strong></p>
                                <p>频次: <strong>${params[0].value}</strong></p>
                            </div>
                        </div>
                    `;
                },
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: color,
                borderWidth: 1,
                borderRadius: 5
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'value',
                name: xAxisLabel,
                nameTextStyle: {
                    fontSize: 12
                },
                axisLabel: {
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#f0f0f0',
                        type: 'dashed'
                    }
                }
            },
            yAxis: {
                type: 'value',
                name: '频次',
                nameTextStyle: {
                    fontSize: 12
                },
                axisLabel: {
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#f0f0f0',
                        type: 'dashed'
                    }
                }
            },
            series: [{
                name: '直方图',
                type: 'bar',
                data: seriesData,
                itemStyle: {
                    color: color,
                    borderRadius: [2, 2, 0, 0]
                },
                emphasis: {
                    itemStyle: {
                        color: color,
                        shadowBlur: 6,
                        shadowColor: 'rgba(0, 0, 0, 0.3)'
                    }
                },
                label: {
                    show: false,
                    position: 'top',
                    fontSize: 9
                }
            }],
            toolbox: {
                feature: {
                    dataZoom: {
                        yAxisIndex: 'none'
                    },
                    restore: {},
                    saveAsImage: {
                        pixelRatio: 2,
                        backgroundColor: '#fff'
                    }
                },
                right: 10,
                top: 10
            },
            dataZoom: [
                {
                    type: 'inside',
                    start: 0,
                    end: 100
                },
                {
                    start: 0,
                    end: 100
                }
            ]
        };
    }

    create3DScatterOption(data, options = {}) {
        const { title = '3D散点图' } = options;
        
        const seriesData = this.convertTo3DScatterData(data);

        return {
            title: {
                text: title,
                left: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                trigger: 'item',
                formatter: function(params) {
                    return `
                        <div style="padding: 10px;">
                            <h6 style="margin: 0 0 5px 0; color: #1f77b4;">3D散点数据</h6>
                            <div style="line-height: 1.6;">
                                <p>转速: <strong>${params.data[0]}</strong></p>
                                <p>数据点索引: <strong>${params.data[1]}</strong></p>
                                <p>不平衡量: <strong>${params.data[2].toFixed(2)}</strong></p>
                            </div>
                        </div>
                    `;
                },
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: '#1f77b4',
                borderWidth: 1,
                borderRadius: 5
            },
            xAxis3D: {
                type: 'category',
                name: '转速',
                nameTextStyle: {
                    fontSize: 12
                },
                axisLabel: {
                    fontSize: 10
                }
            },
            yAxis3D: {
                type: 'value',
                name: '数据点索引',
                nameTextStyle: {
                    fontSize: 12
                },
                axisLabel: {
                    fontSize: 10
                }
            },
            zAxis3D: {
                type: 'value',
                name: '不平衡量',
                nameTextStyle: {
                    fontSize: 12
                },
                axisLabel: {
                    fontSize: 10
                }
            },
            grid3D: {
                viewControl: {
                    projection: 'perspective',
                    autoRotate: true,
                    autoRotateSpeed: 5,
                    distance: 120,
                    minDistance: 80,
                    maxDistance: 200,
                    zoomSensitivity: 1
                },
                light: {
                    main: {
                        intensity: 1.2,
                        shadow: true
                    },
                    ambient: {
                        intensity: 0.6
                    }
                }
            },
            series: [{
                name: '3D散点图',
                type: 'scatter3D',
                data: seriesData,
                itemStyle: {
                    color: function(params) {
                        return new echarts.graphic.RadialGradient(0.4, 0.3, 1, [
                            { offset: 0, color: 'rgb(129, 227, 238)' },
                            { offset: 1, color: 'rgb(25, 183, 207)' }
                        ]);
                    }
                },
                symbolSize: 8,
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }],
            toolbox: {
                feature: {
                    restore: {},
                    saveAsImage: {
                        pixelRatio: 2,
                        backgroundColor: '#fff'
                    }
                },
                right: 10,
                top: 10
            }
        };
    }

    createParallelOption(data, options = {}) {
        const { title = '平行坐标图' } = options;
        
        const seriesData = this.convertToParallelData(data);
        const dimensions = this.extractParallelDimensions(data);

        return {
            title: {
                text: title,
                left: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                trigger: 'axis'
            },
            parallelAxis: dimensions.map((dim, index) => ({
                dim: index,
                name: dim,
                nameTextStyle: {
                    fontSize: 12
                },
                axisLabel: {
                    fontSize: 10
                }
            })),
            parallel: {
                left: '5%',
                right: '10%',
                bottom: '10%',
                top: '15%'
            },
            series: [{
                name: '平行坐标图',
                type: 'parallel',
                data: seriesData,
                lineStyle: {
                    width: 2,
                    color: function() {
                        return new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                            { offset: 0, color: '#1f77b4' },
                            { offset: 1, color: '#ff7f0e' }
                        ]);
                    },
                    opacity: 0.7
                },
                emphasis: {
                    lineStyle: {
                        width: 4,
                        opacity: 1
                    }
                }
            }],
            toolbox: {
                feature: {
                    restore: {},
                    saveAsImage: {
                        pixelRatio: 2,
                        backgroundColor: '#fff'
                    }
                },
                right: 10,
                top: 10
            }
        };
    }

    createBubbleOption(data, options = {}) {
        const { title = '气泡图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
        
        const seriesData = this.convertToBubbleData(data);

        return {
            title: {
                text: title,
                left: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                trigger: 'item',
                formatter: function(params) {
                    return `
                        <div style="padding: 10px;">
                            <h6 style="margin: 0 0 5px 0; color: ${color};">气泡数据</h6>
                            <div style="line-height: 1.6;">
                                <p>转速: <strong>${params.data[0]}</strong></p>
                                <p>不平衡量: <strong>${params.data[1].toFixed(2)}</strong></p>
                                <p>气泡大小: <strong>${params.data[2]}</strong></p>
                            </div>
                        </div>
                    `;
                },
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: color,
                borderWidth: 1,
                borderRadius: 5
            },
            xAxis: {
                type: 'category',
                data: [...new Set(seriesData.map(item => item[0]))],
                axisLabel: {
                    rotate: 45,
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                }
            },
            yAxis: {
                type: 'value',
                name: yAxisLabel,
                nameTextStyle: {
                    fontSize: 12
                },
                axisLabel: {
                    fontSize: 11
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#f0f0f0',
                        type: 'dashed'
                    }
                }
            },
            series: [{
                name: '气泡图',
                type: 'scatter',
                data: seriesData.map(item => [item[0], item[1], item[2]]),
                symbolSize: function(data) {
                    return Math.sqrt(data[2]) * 2;
                },
                itemStyle: {
                    color: color,
                    opacity: 0.8
                },
                emphasis: {
                    itemStyle: {
                        color: color,
                        opacity: 1,
                        shadowBlur: 10,
                        shadowColor: 'rgba(0, 0, 0, 0.3)'
                    }
                }
            }],
            toolbox: {
                feature: {
                    dataZoom: {
                        yAxisIndex: 'none'
                    },
                    restore: {},
                    saveAsImage: {
                        pixelRatio: 2,
                        backgroundColor: '#fff'
                    }
                },
                right: 10,
                top: 10
            },
            dataZoom: [
                {
                    type: 'inside',
                    start: 0,
                    end: 100
                },
                {
                    start: 0,
                    end: 100
                }
            ]
        };
    }

    convertToBoxPlotData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            return data.map((item, index) => {
                // 如果item是对象且有name属性，使用它作为名称（通常是转速）
                if (typeof item === 'object' && item !== null && 'name' in item) {
                    return {
                        name: item.name,
                        data: Array.isArray(item.data) ? item.data : [0, 0, 0, 0, 0]
                    };
                }
                // 否则使用默认格式
                return {
                    name: `数据${index + 1}`,
                    data: Array.isArray(item) ? item : [0, 0, 0, 0, 0]
                };
            });
        }

        return Object.keys(data).map(key => ({
            name: key,
            data: Array.isArray(data[key]) ? data[key] : [0, 0, 0, 0, 0]
        }));
    }

    convertToScatterData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            return data.map(item => Array.isArray(item) ? item : [0, 0]);
        }

        const result = [];
        Object.keys(data).forEach(key => {
            const values = data[key];
            if (Array.isArray(values)) {
                values.forEach((value, index) => {
                    result.push([key, value]);
                });
            }
        });
        return result;
    }

    convertToTrendData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            return data.map((item, index) => ({
                name: `数据${index + 1}`,
                value: typeof item === 'number' ? item : 0
            }));
        }

        return Object.keys(data).map(key => ({
            name: key,
            value: typeof data[key] === 'number' ? data[key] : 0
        }));
    }

    convertToViolinData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            return data.map((item, index) => ({
                name: `数据${index + 1}`,
                data: Array.isArray(item) ? item : []
            }));
        }

        return Object.keys(data).map(key => ({
            name: key,
            data: Array.isArray(data[key]) ? data[key] : []
        }));
    }

    convertToHeatmapData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        const result = [];
        if (Array.isArray(data)) {
            data.forEach((item, rowIndex) => {
                if (Array.isArray(item)) {
                    item.forEach((value, colIndex) => {
                        if (typeof value === 'number') {
                            result.push([`行${rowIndex + 1}`, `列${colIndex + 1}`, value]);
                        }
                    });
                }
            });
        } else {
            Object.keys(data).forEach(rowKey => {
                const rowData = data[rowKey];
                if (typeof rowData === 'object' && rowData !== null) {
                    Object.keys(rowData).forEach(colKey => {
                        const value = rowData[colKey];
                        if (typeof value === 'number') {
                            result.push([rowKey, colKey, value]);
                        }
                    });
                }
            });
        }
        return result;
    }

    convertToHistogramData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            return data.filter(item => typeof item === 'number');
        }

        const result = [];
        Object.values(data).forEach(value => {
            if (typeof value === 'number') {
                result.push(value);
            }
        });
        return result;
    }

    convertTo3DScatterData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        const result = [];
        if (Array.isArray(data)) {
            data.forEach((item, index) => {
                if (Array.isArray(item) && item.length >= 3) {
                    result.push([item[0], item[1], item[2]]);
                } else if (typeof item === 'number') {
                    result.push([index, 0, item]);
                }
            });
        } else {
            Object.keys(data).forEach(key => {
                const values = data[key];
                if (Array.isArray(values)) {
                    values.forEach((value, index) => {
                        if (typeof value === 'number') {
                            result.push([key, index, value]);
                        }
                    });
                } else if (typeof values === 'number') {
                    result.push([key, 0, values]);
                }
            });
        }
        return result;
    }

    convertToParallelData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            return data.map(item => Array.isArray(item) ? item : []);
        }

        const result = [];
        Object.values(data).forEach(value => {
            if (Array.isArray(value)) {
                result.push(value);
            }
        });
        return result;
    }

    convertToBubbleData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        const result = [];
        if (Array.isArray(data)) {
            data.forEach((item, index) => {
                if (Array.isArray(item) && item.length >= 2) {
                    result.push([`数据${index + 1}`, item[0], item[1]]);
                } else if (typeof item === 'number') {
                    result.push([`数据${index + 1}`, item, 1]);
                }
            });
        } else {
            Object.keys(data).forEach(key => {
                const value = data[key];
                if (typeof value === 'number') {
                    result.push([key, value, 1]);
                } else if (Array.isArray(value) && value.length >= 2) {
                    result.push([key, value[0], value[1]]);
                }
            });
        }
        return result;
    }

    extractParallelDimensions(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data) && data.length > 0) {
            const firstItem = data[0];
            if (Array.isArray(firstItem)) {
                return firstItem.map((_, index) => `维度${index + 1}`);
            }
        }

        return ['维度1', '维度2', '维度3'];
    }
}