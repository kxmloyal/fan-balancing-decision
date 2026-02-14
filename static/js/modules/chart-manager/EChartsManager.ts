import { ChartType, ChartData, ChartOptions, ChartManager as ChartManagerInterface, ResponsiveConfig, BoxPlotData, ScatterData, TrendData, ViolinData, HeatmapData, HistogramData, Scatter3DData, Cache } from '../../types';

// 声明全局echarts变量
declare const echarts: any;
// 声明全局echartsStat变量
declare const echartsStat: any;

/**
 * 内存缓存实现
 */
class MemoryCache implements Cache {
    private cache: Map<string, { value: any; timestamp: number }> = new Map();
    private maxSize: number = 100;
    private ttl: number = 3600000; // 1小时

    get(key: string): any {
        const item = this.cache.get(key);
        if (!item) return null;

        // 检查是否过期
        if (Date.now() - item.timestamp > this.ttl) {
            this.cache.delete(key);
            return null;
        }

        return item.value;
    }

    set(key: string, value: any): void {
        // 如果缓存已满，删除最旧的项目
        if (this.cache.size >= this.maxSize) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }

        this.cache.set(key, {
            value,
            timestamp: Date.now()
        });
    }

    has(key: string): boolean {
        return this.cache.has(key);
    }

    delete(key: string): void {
        this.cache.delete(key);
    }

    clear(): void {
        this.cache.clear();
    }
}

/**
 * ECharts图表管理器
 * 负责ECharts图表的初始化、渲染和交互管理
 */
export class EChartsManager implements ChartManagerInterface {
    private charts: Record<string, any> = {};
    private chartData: Record<string, ChartData> = {};
    private loadingStates: Record<string, boolean> = {};
    private resizeObserver: ResizeObserver | null = null;
    private supportedTypes: ChartType[] = ['box', 'scatter', 'trend', 'violin', 'heatmap', 'histogram', '3d', 'parallel', 'bubble', 'regression'];
    private eventListeners: Record<string, EventListener[]> = {};
    private dataCache: Cache = new MemoryCache();
    private configCache: Cache = new MemoryCache();
    private batchProcessing: boolean = false;
    private batchQueue: Array<{ containerId: string; chartType: ChartType; data: ChartData; options: ChartOptions }> = [];
    private initialized: boolean = false;
    private echartsLoaded: boolean = false;

    constructor() {
        this.initEChartsLibraryCheck();
        this.initResizeObserver();
        this.initResponsiveListeners();
        this.initResponsiveLayoutListeners();
        this.initialized = true;
        console.log('EChartsManager 初始化完成');
    }

    private echartsStatLoaded: boolean = false;

    /**
     * 检查ECharts库是否加载
     */
    private initEChartsLibraryCheck(): void {
        if (typeof echarts !== 'undefined') {
            this.echartsLoaded = true;
            console.log('ECharts库已加载');
        } else {
            this.echartsLoaded = false;
            console.warn('ECharts库未加载，将在需要时尝试重新检查');
        }
        
        if (typeof echartsStat !== 'undefined') {
            this.echartsStatLoaded = true;
            console.log('ECharts-Stat库已加载');
        } else {
            this.echartsStatLoaded = false;
            console.warn('ECharts-Stat库未加载，将在需要时尝试重新检查');
        }
        
        // 添加延迟检查，确保ECharts库有足够时间加载
        setTimeout(() => {
            this.checkEChartsLibrary();
        }, 1000);
    }

    /**
     * 检查ECharts库是否加载
     * @returns {boolean} ECharts库是否加载
     */
    public checkEChartsLibrary(): boolean {
        if (typeof echarts !== 'undefined') {
            if (!this.echartsLoaded) {
                this.echartsLoaded = true;
                console.log('ECharts库加载成功');
            }
        } else {
            this.echartsLoaded = false;
            console.warn('ECharts库未加载');
            return false;
        }
        
        if (typeof echartsStat !== 'undefined') {
            if (!this.echartsStatLoaded) {
                this.echartsStatLoaded = true;
                console.log('ECharts-Stat库加载成功');
            }
        } else {
            this.echartsStatLoaded = false;
            console.warn('ECharts-Stat库未加载');
        }
        
        return this.echartsLoaded;
    }

    /**
     * 检查EChartsManager是否初始化完成
     * @returns {boolean} 是否初始化完成
     */
    public isInitialized(): boolean {
        return this.initialized && this.echartsLoaded;
    }

    /**
     * 检查ECharts-Stat库是否加载
     * @returns {boolean} ECharts-Stat库是否加载
     */
    public isEChartsStatLoaded(): boolean {
        return this.echartsStatLoaded;
    }

    /**
     * 初始化响应式调整观察器
     */
    private initResizeObserver(): void {
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

    /**
     * 初始化ECharts图表
     * @param {string} containerId - 图表容器ID
     * @param {ChartType} chartType - 图表类型
     * @param {ChartData} data - 图表数据
     * @param {ChartOptions} options - 额外配置选项
     */
    initChart(containerId: string, chartType: ChartType, data: ChartData, options: ChartOptions = {}): any {
        console.log(`开始初始化图表: ${containerId}, 类型: ${chartType}`);
        
        try {
            // 检查EChartsManager是否初始化
            if (!this.initialized) {
                console.error('EChartsManager未初始化');
                this.showError(containerId, '图表管理器未初始化');
                return null;
            }

            // 检查ECharts库是否加载
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

            // 生成缓存键
            const cacheKey = `${containerId}_${chartType}_${JSON.stringify(options)}`;
            const dataCacheKey = `${cacheKey}_data`;
            
            // 检查是否有缓存的图表配置
            const cachedConfig = this.configCache.get(cacheKey);
            const cachedData = this.dataCache.get(dataCacheKey);
            
            if (cachedConfig && cachedData) {
                console.log(`使用缓存的图表配置和数据: ${containerId}`);
                // 销毁已存在的图表实例
                if (this.charts[containerId]) {
                    this.destroyChart(containerId);
                }
                
                // 显示加载状态
                this.showLoading(containerId);
                
                try {
                    // 创建图表实例
                    const renderer = window.devicePixelRatio > 1 ? 'canvas' : 'svg';
                    const chart = echarts.init(container, null, {
                        renderer: renderer,
                        devicePixelRatio: window.devicePixelRatio || 1,
                        lazyUpdate: true // 启用懒更新
                    });
                    
                    this.charts[containerId] = chart;
                    this.chartData[containerId] = cachedData;
                    
                    // 应用缓存的配置
                    chart.setOption(cachedConfig);
                    
                    // 监听窗口大小变化
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
                    
                    // 添加到ResizeObserver
                    if (this.resizeObserver) {
                        this.resizeObserver.observe(container);
                    }
                    
                    // 隐藏加载状态
                    this.hideLoading(containerId);
                    console.log(`使用缓存初始化图表成功: ${containerId}`);
                    return chart;
                } catch (cacheError) {
                    console.error('使用缓存初始化图表时出错:', cacheError);
                    console.error('错误详情:', cacheError.stack);
                    this.showError(containerId, '图表初始化失败');
                    return null;
                }
            }

            // 显示加载状态
            this.showLoading(containerId);

            // 销毁已存在的图表实例
            if (this.charts[containerId]) {
                this.destroyChart(containerId);
            }

            // 验证数据
            if (!data) {
                console.warn('图表数据为空:', containerId);
                this.showError(containerId, '暂无数据');
                return null;
            }

            // 验证数据格式
            if (Array.isArray(data) && data.length === 0) {
                console.warn('图表数据为空数组:', containerId);
                this.showError(containerId, '暂无数据');
                return null;
            }

            // 验证图表类型
            if (!chartType || !this.supportedTypes.includes(chartType)) {
                console.error(`不支持的图表类型: ${chartType}`);
                this.showError(containerId, `不支持的图表类型: ${chartType}`);
                return null;
            }

            // 验证数据类型
            if (typeof data !== 'object') {
                console.error('图表数据类型错误，期望对象或数组:', typeof data);
                this.showError(containerId, '图表数据格式错误');
                return null;
            }

            // 验证数据格式是否与图表类型匹配
            if (!this.validateChartData(data, chartType, containerId)) {
                console.warn(`数据格式与图表类型不匹配: ${containerId}, 类型: ${chartType}`);
                this.showError(containerId, '图表数据格式错误');
                return null;
            }

            // 创建新的图表实例，启用渲染优化
            try {
                console.log(`开始创建ECharts实例: ${containerId}`);
                console.log(`图表类型: ${chartType}`);
                console.log(`图表数据长度: ${Array.isArray(data) ? data.length : '对象'}`);
                
                // 根据设备像素比选择渲染器
                const renderer = window.devicePixelRatio > 1 ? 'canvas' : 'svg';
                console.log(`选择的渲染器: ${renderer}`);
                
                // 简化配置，移除可能不支持的选项
                const chart = echarts.init(container, null, {
                    renderer: renderer,
                    devicePixelRatio: window.devicePixelRatio || 1,
                    lazyUpdate: true, // 启用懒更新
                    useDirtyRect: true // 启用脏矩形渲染
                });
                
                console.log(`ECharts实例创建成功: ${containerId}`);
                this.charts[containerId] = chart;
                this.chartData[containerId] = data;
                
                // 监听窗口大小变化，使用防抖优化
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
                
                // 添加到ResizeObserver（如果支持）
                if (this.resizeObserver) {
                    this.resizeObserver.observe(container);
                    console.log(`已添加到ResizeObserver: ${containerId}`);
                }
                console.log(`ECharts实例配置完成: ${containerId}`);
            } catch (initError) {
                console.error('创建ECharts实例时出错:', initError);
                console.error('错误详情:', initError.stack);
                this.showError(containerId, '图表实例创建失败');
                return null;
            }

            // 渲染图表
            try {
                this.renderChart(containerId, chartType, data, options);
                
                // 缓存数据和配置
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
                this.showError(containerId, '图表渲染失败');
                return null;
            }

            // 隐藏加载状态
            this.hideLoading(containerId);
            console.log(`ECharts图表初始化成功: ${containerId}`);
            return this.charts[containerId];
        } catch (error) {
            console.error('初始化ECharts图表时出错:', error);
            console.error('错误详情:', error.stack);
            this.showError(containerId, `图表初始化失败: ${error.message}`);
            return null;
        }
    }

    /**
     * 验证图表数据格式
     * @param {ChartData} data - 图表数据
     * @param {ChartType} chartType - 图表类型
     * @param {string} containerId - 容器ID
     * @returns {boolean} 验证结果
     */
    private validateChartData(data: ChartData, chartType: ChartType, containerId: string): boolean {
        try {
            console.log(`[图表 ${containerId}] 开始验证数据格式，图表类型: ${chartType}`);
            console.log(`[图表 ${containerId}] 原始数据: ${JSON.stringify(data)}`);
            console.log(`[图表 ${containerId}] 数据类型: ${typeof data}, 是否为数组: ${Array.isArray(data)}, 长度: ${Array.isArray(data) ? data.length : (typeof data === 'object' ? Object.keys(data).length : '非对象')}`);
            
            if (!data) {
                console.warn(`[图表 ${containerId}] 数据为空`);
                return false;
            }
            
            if (!Array.isArray(data)) {
                console.warn(`[图表 ${containerId}] 数据不是数组，图表类型: ${chartType}`);
                return false;
            }
            
            if (data.length === 0) {
                console.warn(`[图表 ${containerId}] 数据数组为空，图表类型: ${chartType}`);
                return false;
            }
            
            switch (chartType) {
                case 'box':
                    const validBoxData = data.every((item, index) => {
                        const isValid = typeof item === 'object' && 
                            item !== null && 
                            'name' in item && 
                            'data' in item && 
                            Array.isArray(item.data) && 
                            item.data.length === 5;
                        if (!isValid) {
                            console.warn(`[图表 ${containerId}] 箱线图数据格式错误，索引: ${index}, 数据: ${JSON.stringify(item)}`);
                        }
                        return isValid;
                    });
                    console.log(`[图表 ${containerId}] 箱线图数据验证结果: ${validBoxData}`);
                    return validBoxData;
                case 'trend':
                    const validTrendData = data.every((item, index) => {
                        const isValid = typeof item === 'object' && 
                            item !== null && 
                            'name' in item && 
                            'value' in item && 
                            typeof item.value === 'number';
                        if (!isValid) {
                            console.warn(`[图表 ${containerId}] 趋势图数据格式错误，索引: ${index}, 数据: ${JSON.stringify(item)}`);
                        }
                        return isValid;
                    });
                    console.log(`[图表 ${containerId}] 趋势图数据验证结果: ${validTrendData}`);
                    return validTrendData;
                case 'scatter':
                    const validScatterData = data.every((item, index) => {
                        const isValid = Array.isArray(item) && 
                            item.length === 2;
                        if (!isValid) {
                            console.warn(`[图表 ${containerId}] 散点图数据格式错误，索引: ${index}, 数据: ${JSON.stringify(item)}`);
                        }
                        return isValid;
                    });
                    console.log(`[图表 ${containerId}] 散点图数据验证结果: ${validScatterData}`);
                    return validScatterData;
                case 'heatmap':
                    const validHeatmapData = data.every((item, index) => {
                        const isValid = Array.isArray(item) && 
                            item.length === 3;
                        if (!isValid) {
                            console.warn(`[图表 ${containerId}] 热力图数据格式错误，索引: ${index}, 数据: ${JSON.stringify(item)}`);
                        }
                        return isValid;
                    });
                    console.log(`[图表 ${containerId}] 热力图数据验证结果: ${validHeatmapData}`);
                    return validHeatmapData;
                case 'histogram':
                    const validHistogramData = data.every((item, index) => {
                        const isValid = typeof item === 'number';
                        if (!isValid) {
                            console.warn(`[图表 ${containerId}] 直方图数据格式错误，索引: ${index}, 数据: ${JSON.stringify(item)}`);
                        }
                        return isValid;
                    });
                    console.log(`[图表 ${containerId}] 直方图数据验证结果: ${validHistogramData}`);
                    return validHistogramData;
                case 'bubble':
                    const validBubbleData = data.every((item, index) => {
                        const isValid = typeof item === 'object' && 
                            item !== null && 
                            'name' in item && 
                            'value' in item && 
                            Array.isArray(item.value) && 
                            item.value.length === 3;
                        if (!isValid) {
                            console.warn(`[图表 ${containerId}] 气泡图数据格式错误，索引: ${index}, 数据: ${JSON.stringify(item)}`);
                        }
                        return isValid;
                    });
                    console.log(`[图表 ${containerId}] 气泡图数据验证结果: ${validBubbleData}`);
                    return validBubbleData;
                case 'violin':
                    const validViolinData = data.every((item, index) => {
                        const isValid = typeof item === 'object' && 
                            item !== null && 
                            'name' in item && 
                            'data' in item && 
                            Array.isArray(item.data);
                        if (!isValid) {
                            console.warn(`[图表 ${containerId}] 小提琴图数据格式错误，索引: ${index}, 数据: ${JSON.stringify(item)}`);
                        }
                        return isValid;
                    });
                    console.log(`[图表 ${containerId}] 小提琴图数据验证结果: ${validViolinData}`);
                    return validViolinData;
                case '3d':
                    const valid3DData = data.every((item, index) => {
                        const isValid = Array.isArray(item) && 
                            item.length === 3;
                        if (!isValid) {
                            console.warn(`[图表 ${containerId}] 3D散点图数据格式错误，索引: ${index}, 数据: ${JSON.stringify(item)}`);
                        }
                        return isValid;
                    });
                    console.log(`[图表 ${containerId}] 3D散点图数据验证结果: ${valid3DData}`);
                    return valid3DData;
                case 'parallel':
                    const validParallelData = data.every((item, index) => {
                        const isValid = Array.isArray(item) && 
                            item.length >= 2;
                        if (!isValid) {
                            console.warn(`[图表 ${containerId}] 平行坐标图数据格式错误，索引: ${index}, 数据: ${JSON.stringify(item)}`);
                        }
                        return isValid;
                    });
                    console.log(`[图表 ${containerId}] 平行坐标图数据验证结果: ${validParallelData}`);
                    return validParallelData;
                default:
                    console.warn(`[图表 ${containerId}] 未知的图表类型: ${chartType}`);
                    return false;
            }
        } catch (error) {
            console.error(`[图表 ${containerId}] 验证数据格式时出错: ${error.message}`);
            console.error(`[图表 ${containerId}] 错误详情: ${error.stack}`);
            return false;
        }
    }

    /**
     * 渲染图表
     * @param {string} containerId - 图表容器ID
     * @param {ChartType} chartType - 图表类型
     * @param {ChartData} data - 图表数据
     * @param {ChartOptions} options - 额外配置选项
     */
    renderChart(containerId: string, chartType: ChartType, data: ChartData, options: ChartOptions = {}): void {
        const chart = this.charts[containerId];
        if (!chart) {
            console.warn(`图表实例不存在: ${containerId}`);
            return;
        }

        try {
            let option: any = {};

            // 验证图表类型
            if (!this.supportedTypes.includes(chartType)) {
                console.warn(`未支持的图表类型: ${chartType}`);
                this.showError(containerId, `不支持的图表类型: ${chartType}`);
                return;
            }

            // 验证数据
            if (!data || (Array.isArray(data) && data.length === 0)) {
                console.warn(`图表数据为空: ${containerId}`);
                this.showError(containerId, '图表数据为空');
                return;
            }

            console.log(`开始渲染图表: ${containerId}, 类型: ${chartType}`);
            
            // 检查数据大小，对于大数据集进行优化
            const dataSize = Array.isArray(data) ? data.length : Object.keys(data).length;
            const isLargeData = dataSize > 1000;
            
            if (isLargeData) {
                console.log(`检测到大数据集: ${dataSize} 数据点，启用性能优化`);
                // 对于大数据集，禁用动画和部分交互功能
                options = { ...options, largeData: true };
            }

            // 根据图表类型生成配置
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
                case 'regression':
                    option = this.createRegressionOption(data, options);
                    break;
                default:
                    console.warn(`未支持的图表类型: ${chartType}`);
                    this.showError(containerId, `不支持的图表类型: ${chartType}`);
                    return;
            }

            // 验证生成的配置
            if (!option || typeof option !== 'object') {
                console.error('图表配置生成失败');
                this.showError(containerId, '图表配置生成失败');
                return;
            }

            // 应用响应式配置
            const responsiveConfig = this.getResponsiveConfig(containerId);
            option = this.mergeOptions(option, responsiveConfig);

            // 对于大数据集，添加性能优化配置
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
                    series: option.series?.map((series: any) => ({
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

            // 应用图表配置
            chart.setOption(option, true); // 启用懒更新
            console.log(`ECharts图表渲染成功: ${containerId} (${chartType})`);
        } catch (error) {
            console.error('渲染ECharts图表时出错:', error);
            console.error('错误详情:', error.stack);
            this.showError(containerId, `图表渲染失败: ${error.message}`);
        }
    }

    /**
     * 调整图表大小
     * @param {string} containerId - 图表容器ID
     */
    resizeChart(containerId: string): void {
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

    /**
     * 销毁图表实例
     * @param {string} containerId - 图表容器ID
     */
    destroyChart(containerId: string): void {
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

        // 清理事件监听器
        if (this.eventListeners[containerId]) {
            this.eventListeners[containerId].forEach(listener => {
                window.removeEventListener('resize', listener);
            });
            delete this.eventListeners[containerId];
        }

        // 从ResizeObserver中移除
        const container = document.getElementById(containerId);
        if (container && this.resizeObserver) {
            this.resizeObserver.unobserve(container);
        }
    }

    /**
     * 销毁所有图表实例
     */
    destroyAllCharts(): void {
        Object.keys(this.charts).forEach(containerId => {
            this.destroyChart(containerId);
        });
        this.charts = {};
        this.chartData = {};
        this.loadingStates = {};
        this.eventListeners = {};
        
        // 清理ResizeObserver
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        
        console.log('所有图表实例已销毁');
    }

    /**
     * 强制所有图表重绘
     */
    resizeAllCharts(): void {
        const resizeHandler = this.throttle(() => {
            Object.keys(this.charts).forEach(containerId => {
                this.resizeChart(containerId);
            });
        }, 100);
        
        resizeHandler();
    }

    /**
     * 初始化响应式监听
     */
    private initResponsiveListeners(): void {
        // 监听窗口大小变化
        const resizeHandler = this.throttle(() => {
            this.resizeAllCharts();
        }, 100);
        
        window.addEventListener('resize', resizeHandler);
        
        // 监听设备方向变化
        if (window.matchMedia) {
            const orientationHandler = this.throttle(() => {
                this.resizeAllCharts();
            }, 100);
            
            window.matchMedia('(orientation: portrait)').addEventListener('change', orientationHandler);
        }
        
        console.log('响应式监听已初始化');
    }

    /**
     * 获取响应式配置
     * @param {string} containerId - 图表容器ID
     */
    private getResponsiveConfig(containerId: string): ResponsiveConfig {
        const container = document.getElementById(containerId);
        if (!container) return {};
        
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        // 检测设备类型
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        const isTablet = window.innerWidth >= 768 && window.innerWidth < 1024;
        
        console.log(`响应式配置检测: 宽度=${width}, 高度=${height}, 移动设备=${isMobile}, 平板=${isTablet}`);
        
        // 根据容器大小和设备类型调整配置
        if (width < 480 || isMobile) {
            // 移动设备配置
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
            // 平板设备配置
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
            // 小屏幕桌面配置
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
            // 中等屏幕桌面配置
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
            // 大屏幕桌面配置
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
    
    /**
     * 响应式调整图表大小
     * @param {string} containerId - 图表容器ID
     */
    private responsiveResize(containerId: string): void {
        const container = document.getElementById(containerId);
        const chart = this.charts[containerId];
        
        if (!container || !chart) return;
        
        const width = container.clientWidth;
        
        // 根据屏幕大小调整图表高度
        if (width < 480) {
            container.style.height = '250px';
        } else if (width < 768) {
            container.style.height = '300px';
        } else if (width < 1200) {
            container.style.height = '400px';
        } else {
            container.style.height = '500px';
        }
        
        // 调整图表大小
        this.resizeChart(containerId);
    }
    
    /**
     * 初始化响应式布局监听器
     */
    private initResponsiveLayoutListeners(): void {
        // 监听窗口大小变化
        const resizeHandler = this.debounce(() => {
            Object.keys(this.charts).forEach(containerId => {
                this.responsiveResize(containerId);
            });
        }, 150);
        
        window.addEventListener('resize', resizeHandler);
        
        // 监听设备方向变化
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

    /**
     * 显示加载状态
     * @param {string} containerId - 图表容器ID
     */
    private showLoading(containerId: string): void {
        const container = document.getElementById(containerId);
        if (container) {
            container.classList.add('loading');
            this.loadingStates[containerId] = true;
            // 显示加载动画
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

    /**
     * 隐藏加载状态
     * @param {string} containerId - 图表容器ID
     */
    private hideLoading(containerId: string): void {
        const container = document.getElementById(containerId);
        if (container) {
            container.classList.remove('loading');
            this.loadingStates[containerId] = false;
        }
    }

    /**
     * 显示错误信息
     * @param {string} containerId - 图表容器ID
     * @param {string} message - 错误信息
     */
    private showError(containerId: string, message: string): void {
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

    /**
     * 防抖函数
     * @param {Function} func - 要执行的函数
     * @param {number} wait - 等待时间（毫秒）
     * @returns {Function} 防抖后的函数
     */
    private debounce(func: Function, wait: number): Function {
        let timeout: NodeJS.Timeout;
        return function executedFunction(...args: any[]) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * 节流函数
     * @param {Function} func - 要执行的函数
     * @param {number} limit - 时间限制（毫秒）
     * @returns {Function} 节流后的函数
     */
    private throttle(func: Function, limit: number): Function {
        let inThrottle: boolean;
        return function(...args: any[]) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * 合并配置选项
     * @param {Object} target - 目标配置
     * @param {Object} source - 源配置
     * @returns {Object} 合并后的配置
     */
    private mergeOptions(target: any, source: any): any {
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

    /**
     * 批量初始化图表
     * @param {Array} chartConfigs - 图表配置数组
     */
    batchInitCharts(chartConfigs: Array<{
        containerId: string;
        chartType: ChartType;
        data: ChartData;
        options?: ChartOptions;
    }>): void {
        if (!Array.isArray(chartConfigs)) return;
        
        // 启用批量处理模式
        this.batchProcessing = true;
        this.batchQueue = chartConfigs;
        
        console.log(`开始批量初始化图表，共 ${chartConfigs.length} 个图表`);
        
        // 优化批处理大小，根据设备性能调整
        const devicePerformance = this.detectDevicePerformance();
        const batchSize = devicePerformance === 'high' ? 5 : devicePerformance === 'medium' ? 3 : 2;
        
        console.log(`根据设备性能调整批处理大小: ${batchSize}`);
        
        // 分批处理，避免一次性创建过多实例
        const batches: Array<Array<{
            containerId: string;
            chartType: ChartType;
            data: ChartData;
            options?: ChartOptions;
        }>> = [];
        
        for (let i = 0; i < chartConfigs.length; i += batchSize) {
            batches.push(chartConfigs.slice(i, i + batchSize));
        }
        
        // 依次处理每个批次
        batches.forEach((batch, index) => {
            setTimeout(() => {
                console.log(`处理第 ${index + 1} 批次，共 ${batch.length} 个图表`);
                
                // 使用requestAnimationFrame优化渲染
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
            }, index * 150); // 每个批次间隔150ms，比之前更快
        });
        
        // 批量处理完成后清理
        setTimeout(() => {
            this.batchProcessing = false;
            this.batchQueue = [];
            console.log('批量初始化图表完成');
        }, batches.length * 150 + 1000);
    }
    
    /**
     * 检测设备性能
     * @returns {string} 设备性能等级
     */
    private detectDevicePerformance(): string {
        if (typeof navigator === 'undefined') return 'medium';
        
        // 检测设备内存
        const deviceMemory = (navigator as any).deviceMemory || 4;
        // 检测CPU核心数
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

    /**
     * 创建箱线图配置
     * @param {ChartData} data - 图表数据
     * @param {ChartOptions} options - 额外配置选项
     */
    private createBoxPlotOption(data: ChartData, options: ChartOptions = {}): any {
        const { title = '箱线图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
        
        // 转换数据格式为ECharts箱线图所需格式
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
                formatter: function(params: any) {
                    let result = '';
                    params.forEach((param: any) => {
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

    /**
     * 创建散点图配置
     * @param {ChartData} data - 图表数据
     * @param {ChartOptions} options - 额外配置选项
     */
    private createScatterPlotOption(data: ChartData, options: ChartOptions = {}): any {
        const { title = '散点图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
        
        // 转换数据格式为ECharts散点图所需格式
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
                formatter: function(params: any) {
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

    /**
     * 创建趋势图配置
     * @param {ChartData} data - 图表数据
     * @param {ChartOptions} options - 额外配置选项
     */
    private createTrendPlotOption(data: ChartData, options: ChartOptions = {}): any {
        const { title = '趋势图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
        
        // 转换数据格式为ECharts折线图所需格式
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
                formatter: function(params: any) {
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

    /**
     * 创建小提琴图配置
     * @param {ChartData} data - 图表数据
     * @param {ChartOptions} options - 额外配置选项
     */
    private createViolinPlotOption(data: ChartData, options: ChartOptions = {}): any {
        const { title = '小提琴图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
        
        // 转换数据格式为ECharts小提琴图所需格式
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
                formatter: function(params: any) {
                    return `
                        <div style="padding: 10px;">
                            <h6 style="margin: 0 0 5px 0; color: ${color};">${params.name}</h6>
                            <div style="line-height: 1.6;">
                                <p>数据点数量: <strong>${params.data.length}</strong></p>
                                <p>最小值: <strong>${Math.min(...params.data).toFixed(2)}</strong></p>
                                <p>最大值: <strong>${Math.max(...params.data).toFixed(2)}</strong></p>
                                <p>平均值: <strong>${(params.data.reduce((a: number, b: number) => a + b, 0) / params.data.length).toFixed(2)}</strong></p>
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
                // 显示箱线图内部的统计信息
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

    /**
     * 创建热力图配置
     * @param {ChartData} data - 图表数据
     * @param {ChartOptions} options - 额外配置选项
     */
    private createHeatmapOption(data: ChartData, options: ChartOptions = {}): any {
        const { title = '热力图', yAxisLabel = '数据点' } = options;
        
        // 转换数据格式为ECharts热力图所需格式
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
                formatter: function(params: any) {
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

    /**
     * 创建直方图配置
     * @param {ChartData} data - 图表数据
     * @param {ChartOptions} options - 额外配置选项
     */
    private createHistogramOption(data: ChartData, options: ChartOptions = {}): any {
        const { title = '直方图', color = '#1f77b4', xAxisLabel = '不平衡量（单位：g·mm）' } = options;
        
        // 转换数据格式为ECharts直方图所需格式
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
                formatter: function(params: any) {
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

    /**
     * 创建3D散点图配置
     * @param {ChartData} data - 图表数据
     * @param {ChartOptions} options - 额外配置选项
     */
    private create3DScatterOption(data: ChartData, options: ChartOptions = {}): any {
        const { title = '3D散点图' } = options;
        
        // 转换数据格式为ECharts 3D散点图所需格式
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
                formatter: function(params: any) {
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
                    color: function(params: any) {
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

    /**
     * 创建平行坐标图配置
     * @param {ChartData} data - 图表数据
     * @param {ChartOptions} options - 额外配置选项
     */
    private createParallelOption(data: ChartData, options: ChartOptions = {}): any {
        const { title = '平行坐标图' } = options;
        
        // 转换数据格式为ECharts平行坐标图所需格式
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

    /**
     * 创建气泡图配置
     * @param {ChartData} data - 图表数据
     * @param {ChartOptions} options - 额外配置选项
     */
    private createBubbleOption(data: ChartData, options: ChartOptions = {}): any {
        const { title = '气泡图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
        
        // 转换数据格式为ECharts气泡图所需格式
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
                formatter: function(params: any) {
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
                symbolSize: function(data: any) {
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

    /**
     * 转换数据为箱线图格式
     * @param {ChartData} data - 原始数据
     * @returns {BoxPlotData[]} 转换后的数据
     */
    private convertToBoxPlotData(data: ChartData): BoxPlotData[] {
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

        return Object.entries(data).map(([key, value]) => ({
            name: key,
            data: Array.isArray(value) ? value : [0, 0, 0, 0, 0]
        }));
    }

    /**
     * 转换数据为散点图格式
     * @param {ChartData} data - 原始数据
     * @returns {ScatterData[]} 转换后的数据
     */
    private convertToScatterData(data: ChartData): ScatterData[] {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            return data.map((item, index) => [index, typeof item === 'number' ? item : 0]);
        }

        return Object.entries(data).map(([key, value]) => [key, typeof value === 'number' ? value : 0]);
    }

    /**
     * 转换数据为趋势图格式
     * @param {ChartData} data - 原始数据
     * @returns {TrendData[]} 转换后的数据
     */
    private convertToTrendData(data: ChartData): TrendData[] {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            return data.map((item, index) => ({
                name: index,
                value: typeof item === 'number' ? item : 0
            }));
        }

        return Object.entries(data).map(([key, value]) => ({
            name: key,
            value: typeof value === 'number' ? value : 0
        }));
    }

    /**
     * 转换数据为小提琴图格式
     * @param {ChartData} data - 原始数据
     * @returns {ViolinData[]} 转换后的数据
     */
    private convertToViolinData(data: ChartData): ViolinData[] {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            return data.map((item, index) => ({
                name: `数据${index + 1}`,
                data: Array.isArray(item) ? item : [0]
            }));
        }

        return Object.entries(data).map(([key, value]) => ({
            name: key,
            data: Array.isArray(value) ? value : [0]
        }));
    }

    /**
     * 转换数据为热力图格式
     * @param {ChartData} data - 原始数据
     * @returns {HeatmapData[]} 转换后的数据
     */
    private convertToHeatmapData(data: ChartData): HeatmapData[] {
        if (!data || typeof data !== 'object') {
            return [];
        }

        const result: HeatmapData[] = [];
        if (Array.isArray(data)) {
            data.forEach((item, i) => {
                if (Array.isArray(item)) {
                    item.forEach((value, j) => {
                        result.push([i, j, typeof value === 'number' ? value : 0]);
                    });
                }
            });
        } else {
            Object.entries(data).forEach(([key, value]) => {
                if (Array.isArray(value)) {
                    value.forEach((item, index) => {
                        result.push([key, index, typeof item === 'number' ? item : 0]);
                    });
                }
            });
        }
        return result;
    }

    /**
     * 转换数据为直方图格式
     * @param {ChartData} data - 原始数据
     * @returns {HistogramData[]} 转换后的数据
     */
    private convertToHistogramData(data: ChartData): HistogramData[] {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            return data.map((item, index) => ({
                name: `区间${index + 1}`,
                value: typeof item === 'number' ? item : 0
            }));
        }

        return Object.entries(data).map(([key, value]) => ({
            name: key,
            value: typeof value === 'number' ? value : 0
        }));
    }

    /**
     * 转换数据为3D散点图格式
     * @param {ChartData} data - 原始数据
     * @returns {Scatter3DData[]} 转换后的数据
     */
    private convertTo3DScatterData(data: ChartData): Scatter3DData[] {
        if (!data || typeof data !== 'object') {
            return [];
        }

        const result: Scatter3DData[] = [];
        if (Array.isArray(data)) {
            data.forEach((item, i) => {
                if (Array.isArray(item)) {
                    item.forEach((value, j) => {
                        result.push([i, j, typeof value === 'number' ? value : 0]);
                    });
                }
            });
        } else {
            Object.entries(data).forEach(([key, value]) => {
                if (Array.isArray(value)) {
                    value.forEach((item, index) => {
                        result.push([key, index, typeof item === 'number' ? item : 0]);
                    });
                }
            });
        }
        return result;
    }

    /**
     * 转换数据为平行坐标图格式
     * @param {ChartData} data - 原始数据
     * @returns {any[]} 转换后的数据
     */
    private convertToParallelData(data: ChartData): any[] {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            return data.map(item => Array.isArray(item) ? item : []);
        }

        return Object.values(data).map(value => Array.isArray(value) ? value : []);
    }

    /**
     * 提取平行坐标图维度
     * @param {ChartData} data - 原始数据
     * @returns {string[]} 维度数组
     */
    private extractParallelDimensions(data: ChartData): string[] {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data) && data.length > 0) {
            const firstItem = data[0];
            if (Array.isArray(firstItem)) {
                return firstItem.map((_, index) => `维度${index + 1}`);
            }
        } else if (typeof data === 'object') {
            const firstValue = Object.values(data)[0];
            if (Array.isArray(firstValue)) {
                return firstValue.map((_, index) => `维度${index + 1}`);
            }
        }

        return [];
    }

    /**
     * 转换数据为气泡图格式
     * @param {ChartData} data - 原始数据
     * @returns {any[]} 转换后的数据
     */
    private convertToBubbleData(data: ChartData): any[] {
        if (!data || typeof data !== 'object') {
            return [];
        }

        const result: any[] = [];
        if (Array.isArray(data)) {
            data.forEach((item, index) => {
                if (typeof item === 'number') {
                    result.push([index, item, item]);
                } else if (Array.isArray(item) && item.length >= 2) {
                    result.push([index, item[0], item[1]]);
                }
            });
        } else {
            Object.entries(data).forEach(([key, value]) => {
                if (typeof value === 'number') {
                    result.push([key, value, value]);
                } else if (Array.isArray(value) && value.length >= 2) {
                    result.push([key, value[0], value[1]]);
                }
            });
        }
        return result;
    }

    /**
     * 创建回归分析图表配置
     * @param {ChartData} data - 图表数据
     * @param {ChartOptions} options - 额外配置选项
     */
    private createRegressionOption(data: ChartData, options: ChartOptions = {}): any {
        const { title = '回归分析图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）', regressionType = 'linear' } = options;
        
        // 转换数据格式为ECharts散点图所需格式
        const seriesData = this.convertToScatterData(data);
        
        // 提取X和Y数据用于回归分析
        const xData = seriesData.map(item => parseFloat(item[0]) || 0);
        const yData = seriesData.map(item => item[1]);
        
        // 准备回归分析数据
        const regressionData = [];
        for (let i = 0; i < xData.length; i++) {
            regressionData.push([xData[i], yData[i]]);
        }
        
        // 使用echarts-stat进行回归分析
        let regressionResult = [];
        let equation = '';
        
        if (this.echartsStatLoaded && echartsStat) {
            try {
                if (regressionType === 'linear') {
                    // 线性回归
                    const linearResult = echartsStat.linearRegression(regressionData);
                    regressionResult = linearResult.points;
                    equation = `y = ${linearResult.a.toFixed(4)}x + ${linearResult.b.toFixed(4)}`;
                } else if (regressionType === 'exponential') {
                    // 指数回归
                    const expResult = echartsStat.exponentialRegression(regressionData);
                    regressionResult = expResult.points;
                    equation = `y = ${expResult.a.toFixed(4)}e^(${expResult.b.toFixed(4)}x)`;
                } else if (regressionType === 'logarithmic') {
                    // 对数回归
                    const logResult = echartsStat.logarithmicRegression(regressionData);
                    regressionResult = logResult.points;
                    equation = `y = ${logResult.a.toFixed(4)}ln(x) + ${logResult.b.toFixed(4)}`;
                } else if (regressionType === 'polynomial') {
                    // 多项式回归（二次）
                    const polyResult = echartsStat.polynomialRegression(regressionData, 2);
                    regressionResult = polyResult.points;
                    equation = `y = ${polyResult.a[2].toFixed(4)}x² + ${polyResult.a[1].toFixed(4)}x + ${polyResult.a[0].toFixed(4)}`;
                }
            } catch (error) {
                console.error('回归分析计算失败:', error);
                // 使用默认线性回归
                if (echartsStat.linearRegression) {
                    const linearResult = echartsStat.linearRegression(regressionData);
                    regressionResult = linearResult.points;
                    equation = `y = ${linearResult.a.toFixed(4)}x + ${linearResult.b.toFixed(4)}`;
                }
            }
        }

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
                formatter: function(params: any) {
                    if (params.seriesName === '原始数据') {
                        return `
                            <div style="padding: 10px;">
                                <h6 style="margin: 0 0 5px 0; color: ${color};">原始数据</h6>
                                <div style="line-height: 1.6;">
                                    <p>X值: <strong>${params.data[0]}</strong></p>
                                    <p>Y值: <strong>${params.data[1].toFixed(2)}</strong></p>
                                </div>
                            </div>
                        `;
                    } else {
                        return `
                            <div style="padding: 10px;">
                                <h6 style="margin: 0 0 5px 0; color: ${color};">回归曲线</h6>
                                <div style="line-height: 1.6;">
                                    <p>X值: <strong>${params.data[0]}</strong></p>
                                    <p>预测Y值: <strong>${params.data[1].toFixed(2)}</strong></p>
                                    <p>回归方程: <strong>${equation}</strong></p>
                                </div>
                            </div>
                        `;
                    }
                },
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: color,
                borderWidth: 1,
                borderRadius: 5
            },
            legend: {
                data: ['原始数据', '回归曲线'],
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
                type: 'value',
                name: '转速',
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
            series: [
                {
                    name: '原始数据',
                    type: 'scatter',
                    data: seriesData.map(item => [parseFloat(item[0]) || 0, item[1]]),
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
                },
                {
                    name: '回归曲线',
                    type: 'line',
                    data: regressionResult,
                    smooth: true,
                    symbol: 'none',
                    lineStyle: {
                        color: '#ff7f0e',
                        width: 3,
                        type: 'solid'
                    },
                    itemStyle: {
                        color: '#ff7f0e'
                    }
                }
            ],
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
}
