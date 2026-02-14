// 图表管理器 - 重构版本
class ChartManager {
    constructor() {
        this.charts = {};
        this.chartData = {};
        this.loadingStates = {};
        this.resizeObserver = null;
        this.supportedTypes = ['box', 'scatter', 'trend', 'violin', 'heatmap', 'histogram', '3d', 'parallel', 'bubble'];
        this.eventListeners = {};
        this.batchProcessing = false;
        this.batchQueue = [];
        this.initialized = false;
        this.echartsLoaded = false;
        this.echartsGLLoaded = false;

        this.initEChartsLibraryCheck();
        this.initResizeObserver();
        this.initResponsiveListeners();
        this.initialized = true;
        console.log('ChartManager 初始化完成');
    }

    initEChartsLibraryCheck() {
        if (typeof echarts !== 'undefined') {
            this.echartsLoaded = true;
            console.log('ECharts库已加载');
            // 检查ECharts GL是否加载
            this.checkEChartsGLLibrary();
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
                // 检查ECharts GL是否加载
                this.checkEChartsGLLibrary();
            }
            return true;
        } else {
            this.echartsLoaded = false;
            console.warn('ECharts库未加载');
            return false;
        }
    }

    checkEChartsGLLibrary() {
        if (typeof echarts !== 'undefined' && typeof echarts.gl !== 'undefined') {
            this.echartsGLLoaded = true;
            console.log('ECharts GL库已加载');
            return true;
        } else {
            this.echartsGLLoaded = false;
            console.warn('ECharts GL库未加载，3D功能将不可用');
            return false;
        }
    }

    isInitialized() {
        return this.initialized && this.echartsLoaded;
    }

    is3DSupported() {
        return this.echartsGLLoaded;
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
                console.error('ChartManager未初始化');
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

            // 确保容器有正确的大小
            this.ensureChartContainerSize(container, containerId);

            this.showLoading(containerId);

            if (this.charts[containerId]) {
                this.destroyChart(containerId);
            }

            if (!data) {
                console.warn('图表数据为空:', containerId);
                // 提供默认数据，避免显示错误
                data = this.getDefaultChartData(chartType);
            }

            if (Array.isArray(data) && data.length === 0) {
                console.warn('图表数据为空数组:', containerId);
                // 提供默认数据，避免显示错误
                data = this.getDefaultChartData(chartType);
            }

            if (!chartType || !this.supportedTypes.includes(chartType)) {
                console.error(`不支持的图表类型: ${chartType}`);
                this.hideLoading(containerId);
                this.showError(containerId, `不支持的图表类型: ${chartType}`);
                return null;
            }

            // 检查3D图表是否支持
            if (chartType === '3d' && !this.is3DSupported()) {
                console.error('3D图表功能不可用，ECharts GL库未加载');
                this.hideLoading(containerId);
                this.showError(containerId, '3D图表功能不可用，ECharts GL库未加载');
                return null;
            }

            if (typeof data !== 'object') {
                console.error('图表数据类型错误，期望对象或数组:', typeof data);
                this.hideLoading(containerId);
                this.showError(containerId, '图表数据格式错误');
                return null;
            }

            try {
                console.log(`开始创建ECharts实例: ${containerId}`);
                console.log(`图表类型: ${chartType}`);
                console.log(`图表数据长度: ${Array.isArray(data) ? data.length : '对象'}`);
                
                // 智能选择渲染器
                const renderer = this.selectRenderer(containerId, chartType, data);
                console.log(`选择的渲染器: ${renderer}`);
                
                // 优化ECharts实例配置
                const chart = echarts.init(container, null, {
                    renderer: renderer,
                    devicePixelRatio: window.devicePixelRatio || 1,
                    lazyUpdate: true,
                    useDirtyRect: true,
                    useCoarsePointer: this.shouldUseCoarsePointer(),
                    useWeakMap: true
                });
                
                console.log(`ECharts实例创建成功: ${containerId}`);
                this.charts[containerId] = chart;
                this.chartData[containerId] = data;
                
                // 添加交互事件监听器
                this.addChartEventListeners(chart, containerId, chartType);
                
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

    // 确保图表容器有正确的大小
    ensureChartContainerSize(container, containerId) {
        if (!container) return;
        
        // 强制设置容器样式，确保 canvas 正确显示
        container.style.position = 'relative';
        container.style.display = 'block';
        container.style.width = '100%';
        container.style.height = '400px';
        container.style.minWidth = '300px';
        container.style.minHeight = '300px';
        container.style.boxSizing = 'border-box';
        container.style.overflow = 'hidden';
        container.style.padding = '0';
        container.style.margin = '0';
        
        // 强制计算容器大小
        const containerWidth = container.offsetWidth || 600;
        const containerHeight = container.offsetHeight || 400;
        
        console.log(`图表容器大小: ${containerWidth}px x ${containerHeight}px (${containerId})`);
        
        // 确保容器大小至少为最小尺寸
        if (containerWidth < 300 || containerHeight < 300) {
            container.style.width = '600px';
            container.style.height = '400px';
            console.log(`已重置容器最小大小: 600px x 400px (${containerId})`);
        }
    }

    // 获取默认图表数据
    getDefaultChartData(chartType) {
        switch (chartType) {
            case 'box':
                return [{name: '默认转速', data: [0, 1, 2, 3, 4]}];
            case 'trend':
                return [{name: '3000rpm', value: 1}, {name: '4000rpm', value: 2}, {name: '5000rpm', value: 1.5}];
            case 'scatter':
                return [['3000rpm', 1], ['4000rpm', 2], ['5000rpm', 1.5], ['6000rpm', 2.5]];
            case 'heatmap':
                return [['3000rpm', 0, 1], ['4000rpm', 1, 2], ['5000rpm', 2, 1.5]];
            case 'histogram':
                return [1, 2, 3, 4, 3, 2, 1];
            case 'bubble':
                return [{name: '3000rpm', value: ['3000rpm', 1, 5]}];
            case 'violin':
                return [{name: '3000rpm', data: [0.5, 1, 1.5, 2, 2.5]}];
            case '3d':
                return [['3000rpm', 0, 1], ['4000rpm', 1, 2], ['5000rpm', 2, 1.5]];
            case 'parallel':
                return [['3000rpm', 1, 1.5], ['4000rpm', 2, 2.5]];
            default:
                return [];
        }
    }

    // 添加图表事件监听器
    addChartEventListeners(chart, containerId, chartType) {
        if (!chart) return;
        
        // 点击事件
        chart.on('click', (params) => {
            console.log(`图表点击事件: ${containerId}`, params);
            // 可以在这里添加自定义的点击事件处理逻辑
        });
        
        // 鼠标悬停事件
        chart.on('mouseover', (params) => {
            console.log(`图表悬停事件: ${containerId}`, params);
            // 可以在这里添加自定义的悬停事件处理逻辑
        });
        
        // 鼠标离开事件
        chart.on('mouseout', (params) => {
            console.log(`图表鼠标离开事件: ${containerId}`, params);
            // 可以在这里添加自定义的鼠标离开事件处理逻辑
        });
        
        // 数据区域缩放事件
        chart.on('dataZoom', (params) => {
            console.log(`图表数据区域缩放事件: ${containerId}`, params);
            // 可以在这里添加自定义的数据区域缩放事件处理逻辑
        });
        
        console.log(`已为图表 ${containerId} 添加事件监听器`);
    }

    // 智能选择渲染器
    selectRenderer(containerId, chartType, data) {
        const dataSize = this.calculateDataSize(data);
        const devicePerformance = this.detectDevicePerformance();
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        console.log(`渲染器选择参数: 数据大小=${dataSize}, 设备性能=${devicePerformance}, 移动设备=${isMobile}`);
        
        // 强制使用Canvas渲染器，确保图表正确显示
        // Canvas渲染器在处理各种图表类型时更稳定
        return 'canvas';
    }

    // 计算数据大小
    calculateDataSize(data) {
        if (!data) return 0;
        
        if (Array.isArray(data)) {
            return data.reduce((total, item) => {
                if (Array.isArray(item)) {
                    return total + item.length;
                } else if (typeof item === 'object' && item !== null) {
                    if (Array.isArray(item.data)) {
                        return total + item.data.length;
                    }
                }
                return total + 1;
            }, 0);
        } else if (typeof data === 'object') {
            return Object.keys(data).length;
        }
        
        return 1;
    }

    // 检测是否应该使用粗略指针（提高性能）
    shouldUseCoarsePointer() {
        const devicePerformance = this.detectDevicePerformance();
        return devicePerformance === 'low';
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
            
            // 验证并预处理数据
            const validatedData = this.validateAndPreprocessData(data, chartType, containerId);
            if (!validatedData) {
                console.warn(`图表数据验证失败: ${containerId}`);
                this.showError(containerId, '图表数据格式错误');
                return;
            }
            
            const dataSize = Array.isArray(validatedData) ? validatedData.length : Object.keys(validatedData).length;
            const isLargeData = dataSize > 1000;
            
            if (isLargeData) {
                console.log(`检测到大数据集: ${dataSize} 数据点，启用性能优化`);
                options = { ...options, largeData: true };
            }

            switch (chartType) {
                case 'box':
                    option = this.createBoxPlotOption(validatedData, options);
                    break;
                case 'scatter':
                    option = this.createScatterPlotOption(validatedData, options);
                    break;
                case 'trend':
                    option = this.createTrendPlotOption(validatedData, options);
                    break;
                case 'violin':
                    option = this.createViolinPlotOption(validatedData, options);
                    break;
                case 'heatmap':
                    option = this.createHeatmapOption(validatedData, options);
                    break;
                case 'histogram':
                    option = this.createHistogramOption(validatedData, options);
                    break;
                case '3d':
                    option = this.create3DScatterOption(validatedData, options);
                    break;
                case 'parallel':
                    option = this.createParallelOption(validatedData, options);
                    break;
                case 'bubble':
                    option = this.createBubbleOption(validatedData, options);
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

            // 使用requestAnimationFrame优化渲染
            requestAnimationFrame(() => {
                try {
                    // 确保图表实例存在且可用
                    if (!chart || typeof chart.setOption !== 'function') {
                        console.error('图表实例无效:', containerId);
                        this.showError(containerId, '图表实例无效');
                        return;
                    }
                    
                    // 确保容器仍然存在
                    const container = document.getElementById(containerId);
                    if (!container) {
                        console.error('图表容器已不存在:', containerId);
                        this.showError(containerId, '图表容器已不存在');
                        return;
                    }
                    
                    // 再次检查容器大小
                    const containerWidth = container.offsetWidth;
                    const containerHeight = container.offsetHeight;
                    
                    if (containerWidth === 0 || containerHeight === 0) {
                        console.error('图表容器大小为零:', containerId);
                        // 强制设置容器大小
                        container.style.width = '600px';
                        container.style.height = '400px';
                        console.log('已强制设置容器大小:', containerId);
                    }
                    
                    // 渲染图表
                    console.log(`开始设置图表选项: ${containerId}, 配置大小: ${JSON.stringify(option).length} 字符`);
                    chart.setOption(option, true);
                    console.log(`ECharts图表渲染成功: ${containerId} (${chartType})`);
                    
                    // 强制调整图表大小
                    setTimeout(() => {
                        if (chart && typeof chart.resize === 'function') {
                            chart.resize();
                            console.log(`已调整图表大小: ${containerId}`);
                        }
                    }, 100);
                    
                } catch (renderError) {
                    console.error('设置图表选项时出错:', renderError);
                    console.error('错误详情:', renderError.stack);
                    this.showError(containerId, `图表渲染失败: ${renderError.message}`);
                }
            });
        } catch (error) {
            console.error('渲染ECharts图表时出错:', error);
            console.error('错误详情:', error.stack);
            this.showError(containerId, `图表渲染失败: ${error.message}`);
        }
    }

    validateAndPreprocessData(data, chartType, containerId) {
        console.log(`[图表 ${containerId}] 开始验证和预处理数据，图表类型: ${chartType}`);
        
        try {
            if (!data || typeof data !== 'object') {
                console.warn(`[图表 ${containerId}] 图表数据类型错误: ${typeof data}`);
                return null;
            }
            
            switch (chartType) {
                case 'box':
                    return this.validateBoxPlotData(data, containerId);
                case 'scatter':
                    return this.validateScatterData(data, containerId);
                case 'trend':
                    return this.validateTrendData(data, containerId);
                case 'violin':
                    return this.validateViolinData(data, containerId);
                case 'heatmap':
                    return this.validateHeatmapData(data, containerId);
                case 'histogram':
                    return this.validateHistogramData(data, containerId);
                case '3d':
                    return this.validate3DScatterData(data, containerId);
                case 'parallel':
                    return this.validateParallelData(data, containerId);
                case 'bubble':
                    return this.validateBubbleData(data, containerId);
                default:
                    console.warn(`[图表 ${containerId}] 未知的图表类型: ${chartType}`);
                    return data;
            }
        } catch (error) {
            console.error(`[图表 ${containerId}] 验证和预处理数据时出错: ${error.message}`);
            return null;
        }
    }

    validateBoxPlotData(data, containerId) {
        if (Array.isArray(data)) {
            const validData = data.map((item, index) => {
                if (typeof item === 'object' && item !== null) {
                    return {
                        name: item.name || `转速${index + 1}`,
                        data: Array.isArray(item.data) && item.data.length === 5 ? item.data : [0, 0, 0, 0, 0]
                    };
                }
                return {
                    name: `转速${index + 1}`,
                    data: [0, 0, 0, 0, 0]
                };
            });
            return validData.length > 0 ? validData : [{ name: '默认转速', data: [0, 0, 0, 0, 0] }];
        }
        return [{ name: '默认转速', data: [0, 0, 0, 0, 0] }];
    }

    validateScatterData(data, containerId) {
        if (Array.isArray(data)) {
            return data.map(item => Array.isArray(item) && item.length >= 2 ? item : ['默认转速', 0]);
        }
        return [];
    }

    validateTrendData(data, containerId) {
        if (Array.isArray(data)) {
            return data.map((item, index) => ({
                name: item.name || `转速${index + 1}`,
                value: typeof item.value === 'number' ? item.value : 0
            }));
        }
        return [];
    }

    validateViolinData(data, containerId) {
        if (Array.isArray(data)) {
            return data.map((item, index) => ({
                name: item.name || `转速${index + 1}`,
                data: Array.isArray(item.data) ? item.data : []
            }));
        }
        return [];
    }

    validateHeatmapData(data, containerId) {
        if (Array.isArray(data)) {
            return data.map(item => Array.isArray(item) && item.length >= 3 ? item : ['默认转速', 0, 0]);
        }
        return [];
    }

    validateHistogramData(data, containerId) {
        if (Array.isArray(data)) {
            return data.filter(item => typeof item === 'number');
        }
        return [];
    }

    validate3DScatterData(data, containerId) {
        if (Array.isArray(data)) {
            return data.map(item => Array.isArray(item) && item.length >= 3 ? item : ['默认转速', 0, 0]);
        }
        return [];
    }

    validateParallelData(data, containerId) {
        if (Array.isArray(data)) {
            return data.map(item => Array.isArray(item) ? item : ['默认转速', 0, 0]);
        }
        return [];
    }

    validateBubbleData(data, containerId) {
        if (Array.isArray(data)) {
            return data.map((item, index) => {
                if (typeof item === 'object' && item !== null) {
                    return {
                        name: item.name || `转速${index + 1}`,
                        value: Array.isArray(item.value) && item.value.length >= 3 ? item.value : ['转速', 0, 1]
                    };
                }
                return {
                    name: `转速${index + 1}`,
                    value: ['转速', 0, 1]
                };
            });
        }
        return [];
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
                trigger: 'item',
                axisPointer: {
                    type: 'shadow',
                    shadowStyle: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                formatter: function(params) {
                    const boxData = params.data;
                    return `
                        <div style="padding: 10px; border-radius: 4px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);">
                            <h6 style="margin: 0 0 5px 0; color: ${color}; font-weight: bold;">${params.name}</h6>
                            <div style="line-height: 1.6;">
                                <p>最小值: <strong>${boxData[0].toFixed(2)}</strong></p>
                                <p>第一四分位数: <strong>${boxData[1].toFixed(2)}</strong></p>
                                <p>中位数: <strong>${boxData[2].toFixed(2)}</strong></p>
                                <p>第三四分位数: <strong>${boxData[3].toFixed(2)}</strong></p>
                                <p>最大值: <strong>${boxData[4].toFixed(2)}</strong></p>
                            </div>
                        </div>
                    `;
                },
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: color,
                borderWidth: 1,
                borderRadius: 5,
                padding: 10,
                textStyle: {
                    fontSize: 12
                }
            },
            legend: {
                data: ['箱线图', '中位线'],
                bottom: 10,
                textStyle: {
                    fontSize: 12
                },
                selectedMode: 'multiple'
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
                    fontSize: 11,
                    interval: 0,
                    overflow: 'truncate'
                },
                axisLine: {
                    lineStyle: {
                        color: '#ccc'
                    }
                },
                axisTick: {
                    alignWithLabel: true
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
                        borderWidth: 2,
                        shadowBlur: 10,
                        shadowColor: 'rgba(0, 0, 0, 0.3)'
                    }
                },
                label: {
                    show: false,
                    position: 'top'
                }
            }, {
                name: '中位线',
                type: 'line',
                data: medianData,
                smooth: true,
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: {
                    color: '#ff7f0e',
                    width: 2,
                    type: 'solid'
                },
                itemStyle: {
                    color: '#ff7f0e',
                    borderColor: '#fff',
                    borderWidth: 1
                },
                emphasis: {
                    itemStyle: {
                        symbolSize: 8,
                        shadowBlur: 10,
                        shadowColor: 'rgba(0, 0, 0, 0.3)'
                    }
                },
                tooltip: {
                    formatter: function(params) {
                        return `
                            <div style="padding: 10px; border-radius: 4px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);">
                                <h6 style="margin: 0 0 5px 0; color: #ff7f0e; font-weight: bold;">${params.name}</h6>
                                <div style="line-height: 1.6;">
                                    <p>转速: <strong>${params.name}</strong></p>
                                    <p>中位数: <strong>${params.value.toFixed(2)}</strong></p>
                                </div>
                            </div>
                        `;
                    }
                }
            }],
            toolbox: {
                feature: {
                    dataZoom: {
                        yAxisIndex: 'none'
                    },
                    restore: {
                        title: '重置'
                    },
                    saveAsImage: {
                        pixelRatio: 2,
                        backgroundColor: '#fff',
                        title: '保存图片'
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
                    xAxisIndex: [0],
                    zoomLock: false
                },
                {
                    start: 0,
                    end: 100,
                    xAxisIndex: [0],
                    height: 20,
                    bottom: 30,
                    handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
                    handleSize: '80%',
                    handleStyle: {
                        color: '#1f77b4',
                        shadowBlur: 3,
                        shadowColor: 'rgba(0, 0, 0, 0.6)',
                        shadowOffsetX: 2,
                        shadowOffsetY: 2
                    },
                    textStyle: {
                        color: '#333'
                    }
                }
            ],
            animation: true,
            animationDuration: 1000,
            animationEasing: 'cubicOut',
            animationThreshold: 1000
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
            return [{ name: '默认数据', data: [0, 0, 0, 0, 0] }];
        }

        if (Array.isArray(data)) {
            return data.map((item, index) => ({
                name: item.name || `数据${index + 1}`,
                data: Array.isArray(item.data) ? item.data : [0, 0, 0, 0, 0]
            }));
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
                name: item.name || `数据${index + 1}`,
                value: typeof item.value === 'number' ? item.value : 0
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
                name: item.name || `数据${index + 1}`,
                data: Array.isArray(item.data) ? item.data : []
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

//