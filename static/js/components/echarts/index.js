// ECharts组件封装规范 - 基础组件

/**
 * ECharts基础组件类
 * 提供统一的图表初始化、配置管理、主题应用等功能
 */
export class BaseEChartsComponent {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.options = {
            chartType: 'line',
            theme: 'default',
            renderer: 'canvas',
            responsive: true,
            animation: true,
            lazyLoad: false,
            ...options
        };
        this.chartInstance = null;
        this.loading = false;
        this.resizeObserver = null;
    }

    /**
     * 初始化图表
     * @param {Object} data - 图表数据
     * @param {Object} config - 额外配置
     * @returns {Promise} - 初始化结果
     */
    async init(data, config = {}) {
        try {
            if (!window.echarts) {
                throw new Error('ECharts library is not loaded');
            }

            const container = document.getElementById(this.containerId);
            if (!container) {
                throw new Error(`Container ${this.containerId} not found`);
            }

            // 应用主题
            const theme = this.getTheme(this.options.theme);

            // 初始化图表实例
            this.chartInstance = window.echarts.init(container, theme, {
                renderer: this.options.renderer,
                devicePixelRatio: window.devicePixelRatio || 1,
                lazyUpdate: this.options.lazyLoad,
                useDirtyRect: true
            });

            // 配置图表
            const chartOption = this.buildOption(data, config);
            this.chartInstance.setOption(chartOption);

            // 初始化响应式
            if (this.options.responsive) {
                this.initResponsive();
            }

            return this.chartInstance;
        } catch (error) {
            console.error('Failed to initialize chart:', error);
            throw error;
        }
    }

    /**
     * 构建图表配置项
     * @param {Object} data - 图表数据
     * @param {Object} config - 额外配置
     * @returns {Object} - ECharts配置项
     */
    buildOption(data, config) {
        return {
            title: this.buildTitle(config.title),
            tooltip: this.buildTooltip(config.tooltip),
            legend: this.buildLegend(config.legend),
            grid: this.buildGrid(config.grid),
            xAxis: this.buildXAxis(config.xAxis),
            yAxis: this.buildYAxis(config.yAxis),
            series: this.buildSeries(data, config.series),
            animation: this.options.animation,
            ...config
        };
    }

    /**
     * 构建标题配置
     * @param {Object} titleConfig - 标题配置
     * @returns {Object} - 标题配置项
     */
    buildTitle(titleConfig) {
        return {
            text: '',
            left: 'center',
            ...titleConfig
        };
    }

    /**
     * 构建tooltip配置
     * @param {Object} tooltipConfig - tooltip配置
     * @returns {Object} - tooltip配置项
     */
    buildTooltip(tooltipConfig) {
        return {
            trigger: 'axis',
            ...tooltipConfig
        };
    }

    /**
     * 构建图例配置
     * @param {Object} legendConfig - 图例配置
     * @returns {Object} - 图例配置项
     */
    buildLegend(legendConfig) {
        return {
            data: [],
            top: 30,
            ...legendConfig
        };
    }

    /**
     * 构建网格配置
     * @param {Object} gridConfig - 网格配置
     * @returns {Object} - 网格配置项
     */
    buildGrid(gridConfig) {
        return {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true,
            ...gridConfig
        };
    }

    /**
     * 构建X轴配置
     * @param {Object} xAxisConfig - X轴配置
     * @returns {Object} - X轴配置项
     */
    buildXAxis(xAxisConfig) {
        return {
            type: 'category',
            boundaryGap: false,
            data: [],
            ...xAxisConfig
        };
    }

    /**
     * 构建Y轴配置
     * @param {Object} yAxisConfig - Y轴配置
     * @returns {Object} - Y轴配置项
     */
    buildYAxis(yAxisConfig) {
        return {
            type: 'value',
            ...yAxisConfig
        };
    }

    /**
     * 构建系列配置
     * @param {Object} data - 图表数据
     * @param {Object} seriesConfig - 系列配置
     * @returns {Array} - 系列配置项
     */
    buildSeries(data, seriesConfig) {
        return [{
            name: 'Series',
            type: this.options.chartType,
            data: [],
            ...seriesConfig
        }];
    }

    /**
     * 获取主题配置
     * @param {string} themeName - 主题名称
     * @returns {Object} - 主题配置
     */
    getTheme(themeName) {
        const themes = {
            default: null,
            light: {
                backgroundColor: '#fff',
                textStyle: {
                    color: '#333'
                }
            },
            dark: {
                backgroundColor: '#1a1a1a',
                textStyle: {
                    color: '#ccc'
                }
            }
        };

        return themes[themeName] || themes.default;
    }

    /**
     * 初始化响应式
     */
    initResponsive() {
        if (window.ResizeObserver) {
            this.resizeObserver = new ResizeObserver(() => {
                this.resize();
            });

            const container = document.getElementById(this.containerId);
            if (container) {
                this.resizeObserver.observe(container);
            }
        }

        // 监听窗口大小变化
        window.addEventListener('resize', () => this.resize());
    }

    /**
     * 调整图表大小
     */
    resize() {
        if (this.chartInstance) {
            this.chartInstance.resize();
        }
    }

    /**
     * 更新图表数据
     * @param {Object} data - 新数据
     * @param {Object} config - 额外配置
     */
    update(data, config = {}) {
        if (!this.chartInstance) {
            throw new Error('Chart not initialized');
        }

        const option = this.buildOption(data, config);
        this.chartInstance.setOption(option, true);
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        if (this.chartInstance) {
            this.chartInstance.showLoading({
                text: 'Loading...',
                color: '#1f77b4',
                textColor: '#000',
                maskColor: 'rgba(255, 255, 255, 0.8)',
                zlevel: 0
            });
            this.loading = true;
        }
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        if (this.chartInstance) {
            this.chartInstance.hideLoading();
            this.loading = false;
        }
    }

    /**
     * 销毁图表
     */
    destroy() {
        if (this.chartInstance) {
            this.chartInstance.dispose();
            this.chartInstance = null;
        }

        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
            this.resizeObserver = null;
        }

        window.removeEventListener('resize', () => this.resize());
    }
}

/**
 * 箱线图组件
 */
export class BoxChartComponent extends BaseEChartsComponent {
    constructor(containerId, options = {}) {
        super(containerId, {
            chartType: 'boxplot',
            ...options
        });
    }

    buildSeries(data, seriesConfig) {
        return [{
            name: 'Box Plot',
            type: 'boxplot',
            data: data || [],
            itemStyle: {
                color: '#1f77b4',
                borderColor: '#1f77b4'
            },
            emphasis: {
                itemStyle: {
                    color: '#ff7f0e'
                }
            },
            ...seriesConfig
        }];
    }
}

/**
 * 趋势图组件
 */
export class TrendChartComponent extends BaseEChartsComponent {
    constructor(containerId, options = {}) {
        super(containerId, {
            chartType: 'line',
            ...options
        });
    }

    buildSeries(data, seriesConfig) {
        return [{
            name: 'Trend',
            type: 'line',
            data: data || [],
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: {
                width: 3,
                color: '#1f77b4'
            },
            itemStyle: {
                color: '#1f77b4'
            },
            ...seriesConfig
        }];
    }
}

/**
 * 散点图组件
 */
export class ScatterChartComponent extends BaseEChartsComponent {
    constructor(containerId, options = {}) {
        super(containerId, {
            chartType: 'scatter',
            ...options
        });
    }

    buildSeries(data, seriesConfig) {
        return [{
            name: 'Scatter',
            type: 'scatter',
            data: data || [],
            symbolSize: 8,
            itemStyle: {
                color: '#1f77b4',
                opacity: 0.7
            },
            ...seriesConfig
        }];
    }
}

/**
 * 热力图组件
 */
export class HeatmapChartComponent extends BaseEChartsComponent {
    constructor(containerId, options = {}) {
        super(containerId, {
            chartType: 'heatmap',
            ...options
        });
    }

    buildSeries(data, seriesConfig) {
        return [{
            name: 'Heatmap',
            type: 'heatmap',
            data: data || [],
            label: {
                show: true
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            },
            ...seriesConfig
        }];
    }
}

/**
 * 直方图组件
 */
export class HistogramChartComponent extends BaseEChartsComponent {
    constructor(containerId, options = {}) {
        super(containerId, {
            chartType: 'bar',
            ...options
        });
    }

    buildSeries(data, seriesConfig) {
        return [{
            name: 'Histogram',
            type: 'bar',
            data: data || [],
            itemStyle: {
                color: '#1f77b4'
            },
            ...seriesConfig
        }];
    }
}

/**
 * 气泡图组件
 */
export class BubbleChartComponent extends BaseEChartsComponent {
    constructor(containerId, options = {}) {
        super(containerId, {
            chartType: 'scatter',
            ...options
        });
    }

    buildSeries(data, seriesConfig) {
        return [{
            name: 'Bubble',
            type: 'scatter',
            data: data || [],
            symbolSize: function (val) {
                return Math.sqrt(val[2]) * 5;
            },
            itemStyle: {
                color: '#1f77b4',
                opacity: 0.6
            },
            ...seriesConfig
        }];
    }
}

/**
 * 3D散点图组件
 */
export class Scatter3DChartComponent extends BaseEChartsComponent {
    constructor(containerId, options = {}) {
        super(containerId, {
            chartType: 'scatter3D',
            ...options
        });
    }

    buildSeries(data, seriesConfig) {
        return [{
            name: '3D Scatter',
            type: 'scatter3D',
            data: data || [],
            symbolSize: 5,
            itemStyle: {
                color: '#1f77b4'
            },
            ...seriesConfig
        }];
    }

    buildOption(data, config = {}) {
        return {
            title: this.buildTitle(config.title),
            tooltip: this.buildTooltip(config.tooltip),
            xAxis3D: {
                type: 'value'
            },
            yAxis3D: {
                type: 'value'
            },
            zAxis3D: {
                type: 'value'
            },
            grid3D: {
                viewControl: {
                    projection: 'perspective',
                    autoRotate: true
                }
            },
            series: this.buildSeries(data, config.series),
            animation: this.options.animation,
            ...config
        };
    }
}

/**
 * 平行坐标图组件
 */
export class ParallelChartComponent extends BaseEChartsComponent {
    constructor(containerId, options = {}) {
        super(containerId, {
            chartType: 'parallel',
            ...options
        });
    }

    buildOption(data, config = {}) {
        return {
            title: this.buildTitle(config.title),
            tooltip: this.buildTooltip(config.tooltip),
            parallelAxis: [
                { name: 'Speed', type: 'value' },
                { name: 'Median', type: 'value' },
                { name: 'Mean', type: 'value' }
            ],
            series: [{
                name: 'Parallel',
                type: 'parallel',
                data: data || [],
                lineStyle: {
                    width: 2,
                    color: '#1f77b4'
                },
                ...config.series
            }],
            animation: this.options.animation,
            ...config
        };
    }
}

/**
 * 图表工厂类
 */
export class ChartComponentFactory {
    /**
     * 创建图表组件
     * @param {string} containerId - 容器ID
     * @param {string} chartType - 图表类型
     * @param {Object} options - 配置选项
     * @returns {BaseEChartsComponent} - 图表组件实例
     */
    static create(containerId, chartType, options = {}) {
        const chartTypes = {
            box: BoxChartComponent,
            trend: TrendChartComponent,
            scatter: ScatterChartComponent,
            heatmap: HeatmapChartComponent,
            histogram: HistogramChartComponent,
            bubble: BubbleChartComponent,
            '3d': Scatter3DChartComponent,
            parallel: ParallelChartComponent
        };

        const ChartClass = chartTypes[chartType] || BaseEChartsComponent;
        return new ChartClass(containerId, options);
    }
}

// 导出默认对象
export default {
    BaseEChartsComponent,
    BoxChartComponent,
    TrendChartComponent,
    ScatterChartComponent,
    HeatmapChartComponent,
    HistogramChartComponent,
    BubbleChartComponent,
    Scatter3DChartComponent,
    ParallelChartComponent,
    ChartComponentFactory
};