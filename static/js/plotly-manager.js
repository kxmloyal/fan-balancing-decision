// Plotly图表管理器 - 替代ECharts实现
class PlotlyManager {
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
        this.plotlyLoaded = false;
        this.realtimeUpdates = {};
        this.updateIntervals = {};

        this.initPlotlyLibraryCheck();
        this.initResizeObserver();
        this.initResponsiveListeners();
        this.initialized = true;
        console.log('PlotlyManager 初始化完成');
    }

    initPlotlyLibraryCheck() {
        if (typeof Plotly !== 'undefined') {
            this.plotlyLoaded = true;
            console.log('Plotly库已加载');
        } else {
            this.plotlyLoaded = false;
            console.warn('Plotly库未加载，将在需要时尝试重新检查');
            setTimeout(() => {
                this.checkPlotlyLibrary();
            }, 1000);
        }
    }

    checkPlotlyLibrary() {
        if (typeof Plotly !== 'undefined') {
            if (!this.plotlyLoaded) {
                this.plotlyLoaded = true;
                console.log('Plotly库加载成功');
            }
            return true;
        } else {
            this.plotlyLoaded = false;
            console.warn('Plotly库未加载');
            return false;
        }
    }

    isInitialized() {
        return this.initialized && this.plotlyLoaded;
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

    initResponsiveListeners() {
        window.addEventListener('resize', () => {
            if (this.batchProcessing) {
                this.batchQueue.push('resize');
                return;
            }
            
            Object.keys(this.charts).forEach((containerId) => {
                this.resizeChart(containerId);
            });
        });
    }

    ensureChartContainerSize(container, containerId) {
        if (!container) return;
        
        // 强制设置容器样式，确保canvas正确显示
        container.style.position = 'relative';
        container.style.display = 'block';
        container.style.width = '100%';
        container.style.height = '500px';
        container.style.minWidth = '300px';
        container.style.minHeight = '400px';
        container.style.boxSizing = 'border-box';
        container.style.overflow = 'hidden';
        container.style.padding = '0';
        container.style.margin = '0';
        
        // 强制计算容器大小
        const containerWidth = container.offsetWidth || 600;
        const containerHeight = container.offsetHeight || 500;
        
        console.log(`图表容器大小: ${containerWidth}px x ${containerHeight}px (${containerId})`);
        
        // 确保容器大小至少为最小尺寸
        if (containerWidth < 300 || containerHeight < 400) {
            container.style.width = '600px';
            container.style.height = '500px';
            console.log(`已重置容器最小大小: 600px x 500px (${containerId})`);
        }
    }

    showLoading(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; font-size: 14px; color: #666;">加载中...</div>';
            this.loadingStates[containerId] = true;
        }
    }

    hideLoading(containerId) {
        this.loadingStates[containerId] = false;
    }

    showError(containerId, message) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `<div style="display: flex; align-items: center; justify-content: center; height: 100%; font-size: 14px; color: #f44336;">${message}</div>`;
        }
    }

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
                return [[0, 1, 2, 3], [1, 2, 3, 4], [2, 3, 4, 5]];
            default:
                return [];
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
            console.log('原始箱线图数据:', data);
            const validData = data.map((item, index) => {
                if (typeof item === 'object' && item !== null) {
                    console.log('处理数据项:', item);
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
            console.log('验证后的箱线图数据:', validData);
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
                data: Array.isArray(item.data) ? item.data : [0, 0, 0, 0, 0]
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
            return data.map(item => typeof item === 'number' ? item : 0);
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
            return data.map(item => Array.isArray(item) ? item : [0, 0, 0, 0]);
        }
        return [];
    }

    validateBubbleData(data, containerId) {
        if (Array.isArray(data)) {
            return data.map((item, index) => ({
                name: item.name || `转速${index + 1}`,
                value: Array.isArray(item.value) && item.value.length >= 3 ? item.value : ['默认转速', 0, 0]
            }));
        }
        return [];
    }

    initChart(containerId, chartType, data, options = {}) {
        console.log(`开始初始化图表: ${containerId}, 类型: ${chartType}`);
        
        try {
            if (!this.initialized) {
                console.error('PlotlyManager未初始化');
                this.showError(containerId, '图表管理器未初始化');
                return null;
            }

            if (!this.checkPlotlyLibrary()) {
                console.error('Plotly库未加载');
                this.showError(containerId, 'Plotly库未加载');
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

            try {
                console.log(`开始创建Plotly实例: ${containerId}`);
                console.log(`图表类型: ${chartType}`);
                console.log(`图表数据长度: ${Array.isArray(data) ? data.length : '对象'}`);
                
                this.hideLoading(containerId);
                
                // 验证并预处理数据
                const validatedData = this.validateAndPreprocessData(data, chartType, containerId);
                if (!validatedData) {
                    console.warn(`图表数据验证失败: ${containerId}`);
                    this.showError(containerId, '图表数据格式错误');
                    return null;
                }
                
                // 渲染图表
                this.renderChart(containerId, chartType, validatedData, options);
                
                console.log(`Plotly图表初始化成功: ${containerId}`);
                return this.charts[containerId];
            } catch (initError) {
                console.error('创建Plotly实例时出错:', initError);
                console.error('错误详情:', initError.stack);
                this.hideLoading(containerId);
                this.showError(containerId, '图表实例创建失败');
                return null;
            }
        } catch (error) {
            console.error('初始化Plotly图表时出错:', error);
            console.error('错误详情:', error.stack);
            this.hideLoading(containerId);
            this.showError(containerId, `图表初始化失败: ${error.message}`);
            return null;
        }
    }

    renderChart(containerId, chartType, data, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`图表容器不存在: ${containerId}`);
            return [[], {}];
        }

        try {
            console.log(`开始渲染图表: ${containerId}, 类型: ${chartType}`);
            
            let plotlyData = [];
            let layout = {};
            let config = {};
            
            // 计算数据大小，用于性能优化
            const dataSize = this.calculateDataSize(data);
            const isLargeData = dataSize > 1000;
            console.log(`数据大小: ${dataSize}, 大数据集: ${isLargeData}`);
            
            switch (chartType) {
                case 'box':
                    [plotlyData, layout] = this.createBoxPlotConfig(data, options);
                    break;
                case 'scatter':
                    [plotlyData, layout] = this.createScatterPlotConfig(data, options);
                    break;
                case 'trend':
                    [plotlyData, layout] = this.createTrendPlotConfig(data, options);
                    break;
                case 'violin':
                    [plotlyData, layout] = this.createViolinPlotConfig(data, options);
                    break;
                case 'heatmap':
                    [plotlyData, layout] = this.createHeatmapConfig(data, options);
                    break;
                case 'histogram':
                    [plotlyData, layout] = this.createHistogramConfig(data, options);
                    break;
                case '3d':
                    [plotlyData, layout] = this.create3DScatterConfig(data, options);
                    break;
                case 'parallel':
                    [plotlyData, layout] = this.createParallelConfig(data, options);
                    break;
                case 'bubble':
                    [plotlyData, layout] = this.createBubbleConfig(data, options);
                    break;
                default:
                    console.warn(`未支持的图表类型: ${chartType}`);
                    this.showError(containerId, `不支持的图表类型: ${chartType}`);
                    return [[], {}];
            }

            // 设置默认配置
            config = {
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                scrollZoom: true,
                modeBarButtonsToAdd: ['resetScale2d'],
                toImageButtonOptions: {
                    format: 'png',
                    filename: `chart-${containerId}`,
                    height: 500,
                    width: 800,
                    scale: 2
                }
            };

            // 大数据集性能优化
            if (isLargeData) {
                config = {
                    ...config,
                    animation: false,
                    transition: {
                        duration: 0
                    },
                    modeBarButtonsToRemove: ['toggleSpikelines'],
                    staticPlot: false
                };
                
                // 优化布局
                layout = {
                    ...layout,
                    hovermode: 'closest',
                    hoverlabel: {
                        bgcolor: 'rgba(255, 255, 255, 0.9)',
                        bordercolor: '#ddd',
                        font: {
                            size: 12
                        }
                    }
                };
            }

            // 合并自定义配置
            if (options.config) {
                config = { ...config, ...options.config };
            }

            // 渲染图表
            console.log(`开始渲染Plotly图表: ${containerId}`);
            Plotly.newPlot(container, plotlyData, layout, config).then((chart) => {
                this.charts[containerId] = chart;
                this.chartData[containerId] = data;
                console.log(`Plotly图表渲染成功: ${containerId}`);
                
                // 添加事件监听器
                this.addChartEventListeners(chart, containerId, chartType);
                
                // 强制调整图表大小
                setTimeout(() => {
                    this.resizeChart(containerId);
                }, 100);
            }).catch((error) => {
                console.error('渲染Plotly图表时出错:', error);
                this.showError(containerId, `图表渲染失败: ${error.message}`);
            });

            return [plotlyData, layout];
        } catch (error) {
            console.error('渲染Plotly图表时出错:', error);
            console.error('错误详情:', error.stack);
            this.showError(containerId, `图表渲染失败: ${error.message}`);
            return [[], {}];
        }
    }

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

    createBoxPlotConfig(data, options) {
        // 数据验证和处理
        if (!data || data.length === 0) {
            return [[], {
                title: options.title || '箱线图',
                xaxis: { title: options.xAxisLabel || '转速' },
                yaxis: { title: options.yAxisLabel || '数值' },
                margin: { l: 50, r: 50, b: 100, t: 50, pad: 4 },
                showlegend: true
            }];
        }

        // 处理箱线图数据
        console.log('进入createBoxPlotConfig函数，数据:', data);
        const categories = data.map((item, index) => item.name);
        console.log('生成的categories:', categories);
        
        // 为每个箱线图创建单独的轨迹
        const plotlyData = [];
        const medianValues = []; // 存储箱线图的中位数，供中位线使用
        
        data.forEach((item, index) => {
            // 直接使用后端预计算的统计值
            const min = item.data[0];
            const q1 = item.data[1];
            const median = item.data[2];
            const q3 = item.data[3];
            const max = item.data[4];
            
            // 存储中位数，供中位线使用
            medianValues.push(median);
            
            // 验证中位数
            console.log(`转速: ${item.name}, 中位数值: ${median}`);
            
            // 创建箱线图轨迹 - 直接使用后端提供的统计值
            // 使用Plotly的自定义统计值功能，确保箱线图显示的中位数与后端一致
            // 为每个转速分配唯一的x轴位置，避免箱体叠加
            plotlyData.push({
                x: [item.name],  // 使用转速名称作为x轴值
                name: item.name,
                type: 'box',
                q1: [q1],
                median: [median],
                q3: [q3],
                lowerfence: [min],
                upperfence: [max],
                boxpoints: false,  // 不显示散点
                marker: {
                    color: this.getColorForIndex(index)
                },
                fillcolor: this.getColorForIndex(index, 0.4), // 设置箱体填充颜色
                line: {
                    width: 1.5,
                    color: this.getColorForIndex(index, 0.9) // 设置箱体边框颜色
                },
                opacity: 0.8
            });
        });
        
        console.log('生成的plotlyData:', plotlyData);

        // 添加中位线连线，直接使用箱线图的中位数
        if (data.length > 1) {
            console.log('添加中位线，使用的x坐标:', categories);
            console.log('添加中位线，使用的y坐标:', medianValues);
            
            const medianTrace = {
                x: categories,
                y: medianValues,
                mode: 'lines+markers',
                type: 'scatter',
                name: '中位数趋势',
                showlegend: true,
                line: {
                    color: this.getColor('accent'),
                    width: 3,
                    dash: 'solid'
                },
                marker: {
                    color: this.getColor('accent'),
                    size: 8,
                    symbol: 'circle',
                    line: {
                        color: 'white',
                        width: 1.5
                    }
                },
                hoverinfo: 'x+y',
                // 确保中位线在箱体上方
                z: 100
            };
            
            plotlyData.push(medianTrace);
            console.log('添加中位线后的plotlyData:', plotlyData);
        }

        const layout = {
            title: {
                text: options.title || '箱线图',
                font: {
                    size: 18,
                    weight: 'bold'
                }
            },
            xaxis: {
                title: {
                    text: options.xAxisLabel || '转速',
                    font: {
                        size: 14
                    }
                },
                tickangle: -45,
                gridcolor: '#f0f0f0',
                gridwidth: 1,
                // 显式设置类别顺序，确保使用实际名称
                categoryarray: categories,
                categoryorder: 'array'
            },
            yaxis: {
                title: {
                    text: options.yAxisLabel || '数值',
                    font: {
                        size: 14
                    }
                },
                gridcolor: '#f0f0f0',
                gridwidth: 1
            },
            margin: {
                l: 60,
                r: 40,
                b: 120,
                t: 60,
                pad: 4
            },
            showlegend: true,
            legend: {
                font: {
                    size: 12
                },
                orientation: 'v',
                x: 1.02,
                y: 1
            },
            hovermode: 'closest'
        };

        return [plotlyData, layout];
    }

    createScatterPlotConfig(data, options) {
        // 数据验证和处理
        if (!data || data.length === 0) {
            return [[], {
                title: options.title || '散点图',
                xaxis: { title: options.xAxisLabel || '转速' },
                yaxis: { title: options.yAxisLabel || '数值' },
                margin: { l: 50, r: 50, b: 100, t: 50, pad: 4 },
                showlegend: true
            }];
        }

        // 提取数据
        const x = data.map(item => item[0]);
        const y = data.map(item => item[1]);

        const plotlyData = [{
            x: x,
            y: y,
            mode: 'markers',
            type: 'scatter',
            name: options.seriesName || '数据',
            marker: {
                size: 8,
                opacity: 0.7,
                color: options.color || '#1f77b4',
                line: {
                    color: 'white',
                    width: 1
                }
            },
            hoverinfo: 'x+y',
            hovertemplate: `${options.xAxisLabel || 'X'}: %{x}<br>${options.yAxisLabel || 'Y'}: %{y}<extra></extra>`
        }];

        const layout = {
            title: {
                text: options.title || '散点图',
                font: {
                    size: 18,
                    weight: 'bold'
                }
            },
            xaxis: {
                title: {
                    text: options.xAxisLabel || '转速',
                    font: {
                        size: 14
                    }
                },
                tickangle: -45,
                gridcolor: '#f0f0f0',
                gridwidth: 1
            },
            yaxis: {
                title: {
                    text: options.yAxisLabel || '数值',
                    font: {
                        size: 14
                    }
                },
                gridcolor: '#f0f0f0',
                gridwidth: 1
            },
            margin: {
                l: 60,
                r: 40,
                b: 120,
                t: 60,
                pad: 4
            },
            showlegend: true,
            legend: {
                font: {
                    size: 12
                },
                orientation: 'v',
                x: 1.02,
                y: 1
            },
            hovermode: 'closest'
        };

        return [plotlyData, layout];
    }

    createTrendPlotConfig(data, options) {
        // 数据验证和处理
        if (!data || data.length === 0) {
            return [[], {
                title: options.title || '趋势图',
                xaxis: { title: options.xAxisLabel || '转速' },
                yaxis: { title: options.yAxisLabel || '数值' },
                margin: { l: 50, r: 50, b: 100, t: 50, pad: 4 },
                showlegend: true
            }];
        }

        // 提取数据
        const x = data.map(item => item.name);
        const y = data.map(item => item.value);

        const plotlyData = [{
            x: x,
            y: y,
            mode: 'lines+markers',
            type: 'scatter',
            name: options.seriesName || '趋势数据',
            line: {
                width: 2.5,
                color: options.color || '#4caf50',
                shape: 'linear'
            },
            marker: {
                size: 6,
                color: options.color || '#4caf50',
                line: {
                    color: 'white',
                    width: 1
                }
            },
            hoverinfo: 'x+y',
            hovertemplate: `${options.xAxisLabel || 'X'}: %{x}<br>${options.yAxisLabel || 'Y'}: %{y}<extra></extra>`
        }];

        const layout = {
            title: {
                text: options.title || '趋势图',
                font: {
                    size: 18,
                    weight: 'bold'
                }
            },
            xaxis: {
                title: {
                    text: options.xAxisLabel || '转速',
                    font: {
                        size: 14
                    }
                },
                tickangle: -45,
                gridcolor: '#f0f0f0',
                gridwidth: 1
            },
            yaxis: {
                title: {
                    text: options.yAxisLabel || '数值',
                    font: {
                        size: 14
                    }
                },
                gridcolor: '#f0f0f0',
                gridwidth: 1
            },
            margin: {
                l: 60,
                r: 40,
                b: 120,
                t: 60,
                pad: 4
            },
            showlegend: true,
            legend: {
                font: {
                    size: 12
                },
                orientation: 'v',
                x: 1.02,
                y: 1
            },
            hovermode: 'closest',
            // 添加趋势线辅助功能
            shapes: options.showTrendline ? [{
                type: 'line',
                x0: 0,
                y0: y[0],
                x1: x.length - 1,
                y1: y[y.length - 1],
                line: {
                    color: 'rgba(255, 165, 0, 0.6)',
                    width: 2,
                    dash: 'dash'
                }
            }] : []
        };

        return [plotlyData, layout];
    }

    createViolinPlotConfig(data, options) {
        // 数据验证和处理
        if (!data || data.length === 0) {
            return [[], {
                title: options.title || '小提琴图',
                xaxis: { title: options.xAxisLabel || '转速' },
                yaxis: { title: options.yAxisLabel || '数值' },
                margin: { l: 50, r: 50, b: 100, t: 50, pad: 4 },
                showlegend: true
            }];
        }

        const plotlyData = data.map((item, index) => ({
            y: item.data,
            name: item.name,
            type: 'violin',
            box: {
                visible: true,
                line: {
                    color: '#444'
                },
                fillcolor: 'white'
            },
            points: 'all',
            pointpos: -1.5,
            jitter: 0.1,
            marker: {
                size: 4,
                opacity: 0.6
            },
            line: {
                color: `hsl(${index * 60 % 360}, 70%, 50%)`
            },
            fillcolor: `hsla(${index * 60 % 360}, 70%, 50%, 0.2)`
        }));

        const layout = {
            title: {
                text: options.title || '小提琴图',
                font: {
                    size: 18,
                    weight: 'bold'
                }
            },
            xaxis: {
                title: {
                    text: options.xAxisLabel || '转速',
                    font: {
                        size: 14
                    }
                },
                tickangle: -45,
                gridcolor: '#f0f0f0',
                gridwidth: 1
            },
            yaxis: {
                title: {
                    text: options.yAxisLabel || '数值',
                    font: {
                        size: 14
                    }
                },
                gridcolor: '#f0f0f0',
                gridwidth: 1
            },
            margin: {
                l: 60,
                r: 40,
                b: 120,
                t: 60,
                pad: 4
            },
            showlegend: true,
            legend: {
                font: {
                    size: 12
                },
                orientation: 'v',
                x: 1.02,
                y: 1
            },
            hovermode: 'closest'
        };

        return [plotlyData, layout];
    }

    createHeatmapConfig(data, options) {
        // 数据验证和处理
        if (!data || data.length === 0) {
            return [[], {
                title: options.title || '热力图',
                xaxis: { title: options.xAxisLabel || 'X轴' },
                yaxis: { title: options.yAxisLabel || '转速' },
                margin: { l: 50, r: 50, b: 50, t: 50, pad: 4 }
            }];
        }

        // 处理热力图数据
        const xValues = [...new Set(data.map(item => item[1]))];
        const yValues = [...new Set(data.map(item => item[0]))];
        const zValues = [];

        // 构建z矩阵
        yValues.forEach(y => {
            const row = [];
            xValues.forEach(x => {
                const item = data.find(d => d[0] === y && d[1] === x);
                row.push(item ? item[2] : 0);
            });
            zValues.push(row);
        });

        const plotlyData = [{
            z: zValues,
            x: xValues,
            y: yValues,
            type: 'heatmap',
            colorscale: options.colorscale || 'YlOrRd',
            colorbar: {
                title: {
                    text: options.colorBarLabel || '数值',
                    font: {
                        size: 12
                    }
                },
                tickfont: {
                    size: 10
                }
            },
            hoverinfo: 'x+y+z',
            hovertemplate: `${options.xAxisLabel || 'X'}: %{x}<br>${options.yAxisLabel || 'Y'}: %{y}<br>值: %{z}<extra></extra>`,
            showscale: true
        }];

        const layout = {
            title: {
                text: options.title || '热力图',
                font: {
                    size: 18,
                    weight: 'bold'
                }
            },
            xaxis: {
                title: {
                    text: options.xAxisLabel || 'X轴',
                    font: {
                        size: 14
                    }
                },
                tickangle: -45,
                gridcolor: '#f0f0f0',
                gridwidth: 1
            },
            yaxis: {
                title: {
                    text: options.yAxisLabel || '转速',
                    font: {
                        size: 14
                    }
                },
                gridcolor: '#f0f0f0',
                gridwidth: 1
            },
            margin: {
                l: 60,
                r: 80,
                b: 100,
                t: 60,
                pad: 4
            },
            hovermode: 'closest'
        };

        return [plotlyData, layout];
    }

    createHistogramConfig(data, options) {
        // 数据验证和处理
        if (!data || data.length === 0) {
            return [[], {
                title: options.title || '直方图',
                xaxis: { title: options.xAxisLabel || '数值' },
                yaxis: { title: options.yAxisLabel || '频率' },
                margin: { l: 50, r: 50, b: 50, t: 50, pad: 4 }
            }];
        }

        // 计算合适的 bins 数量
        const binSize = options.binSize || Math.ceil(Math.sqrt(data.length));

        const plotlyData = [{
            x: data,
            type: 'histogram',
            nbinsx: binSize,
            marker: {
                color: options.color || '#636EFA',
                opacity: 0.7,
                line: {
                    color: 'white',
                    width: 1
                }
            },
            hoverinfo: 'x+y',
            hovertemplate: `${options.xAxisLabel || '数值'}: %{x}<br>${options.yAxisLabel || '频率'}: %{y}<extra></extra>`
        }];

        const layout = {
            title: {
                text: options.title || '直方图',
                font: {
                    size: 18,
                    weight: 'bold'
                }
            },
            xaxis: {
                title: {
                    text: options.xAxisLabel || '数值',
                    font: {
                        size: 14
                    }
                },
                gridcolor: '#f0f0f0',
                gridwidth: 1
            },
            yaxis: {
                title: {
                    text: options.yAxisLabel || '频率',
                    font: {
                        size: 14
                    }
                },
                gridcolor: '#f0f0f0',
                gridwidth: 1
            },
            margin: {
                l: 60,
                r: 40,
                b: 60,
                t: 60,
                pad: 4
            },
            hovermode: 'closest'
        };

        return [plotlyData, layout];
    }

    create3DScatterConfig(data, options) {
        // 数据验证和处理
        if (!data || data.length === 0) {
            return [[], {
                title: options.title || '3D散点图',
                scene: {
                    xaxis: { title: options.xAxisLabel || '转速' },
                    yaxis: { title: options.yAxisLabel || 'Y轴' },
                    zaxis: { title: options.zAxisLabel || 'Z轴' }
                },
                margin: {
                    l: 0,
                    r: 0,
                    b: 0,
                    t: 50,
                    pad: 4
                }
            }];
        }

        const x = data.map(item => item[0]);
        const y = data.map(item => item[1]);
        const z = data.map(item => item[2]);

        const plotlyData = [{
            x: x,
            y: y,
            z: z,
            mode: 'markers',
            type: 'scatter3d',
            name: options.seriesName || '3D数据',
            marker: {
                size: options.markerSize || 5,
                opacity: 0.8,
                color: options.color || '#1f77b4',
                line: {
                    color: 'white',
                    width: 1
                }
            },
            hoverinfo: 'x+y+z',
            hovertemplate: `${options.xAxisLabel || 'X'}: %{x}<br>${options.yAxisLabel || 'Y'}: %{y}<br>${options.zAxisLabel || 'Z'}: %{z}<extra></extra>`
        }];

        const layout = {
            title: {
                text: options.title || '3D散点图',
                font: {
                    size: 18,
                    weight: 'bold'
                }
            },
            scene: {
                xaxis: {
                    title: {
                        text: options.xAxisLabel || '转速',
                        font: {
                            size: 12
                        }
                    },
                    backgroundcolor: '#f9f9f9',
                    gridcolor: '#e0e0e0',
                    showbackground: true
                },
                yaxis: {
                    title: {
                        text: options.yAxisLabel || 'Y轴',
                        font: {
                            size: 12
                        }
                    },
                    backgroundcolor: '#f9f9f9',
                    gridcolor: '#e0e0e0',
                    showbackground: true
                },
                zaxis: {
                    title: {
                        text: options.zAxisLabel || 'Z轴',
                        font: {
                            size: 12
                        }
                    },
                    backgroundcolor: '#f9f9f9',
                    gridcolor: '#e0e0e0',
                    showbackground: true
                },
                camera: {
                    eye: {
                        x: 1.25,
                        y: 1.25,
                        z: 1.25
                    }
                }
            },
            margin: {
                l: 0,
                r: 0,
                b: 0,
                t: 60,
                pad: 4
            },
            showlegend: true,
            legend: {
                font: {
                    size: 12
                }
            }
        };

        return [plotlyData, layout];
    }

    createParallelConfig(data, options) {
        // 数据验证和处理
        if (!data || data.length === 0) {
            return [[], {
                title: options.title || '平行坐标图',
                margin: {
                    l: 50,
                    r: 50,
                    b: 50,
                    t: 50,
                    pad: 4
                }
            }];
        }

        // 计算维度数量
        const dimensionCount = data[0].length;
        const dimensions = options.dimensions || Array.from({ length: dimensionCount }, (_, i) => ({
            label: `维度${i + 1}`,
            values: data.map(row => row[i])
        }));

        const plotlyData = [{
            type: 'parcoords',
            line: {
                color: data.map((_, i) => i),
                colorscale: options.colorscale || 'Viridis',
                width: 1.5
            },
            dimensions: dimensions,
            hoverinfo: 'none'
        }];

        const layout = {
            title: {
                text: options.title || '平行坐标图',
                font: {
                    size: 18,
                    weight: 'bold'
                }
            },
            margin: {
                l: 50,
                r: 50,
                b: 50,
                t: 60,
                pad: 4
            },
            showlegend: true
        };

        return [plotlyData, layout];
    }

    createBubbleConfig(data, options) {
        // 数据验证和处理
        if (!data || data.length === 0) {
            return [[], {
                title: options.title || '气泡图',
                xaxis: { title: options.xAxisLabel || '转速' },
                yaxis: { title: options.yAxisLabel || '数值' },
                margin: { l: 50, r: 50, b: 100, t: 50, pad: 4 },
                showlegend: true
            }];
        }

        const x = data.map(item => item.value[0]);
        const y = data.map(item => item.value[1]);
        const z = data.map(item => item.value[2]);

        const plotlyData = [{
            x: x,
            y: y,
            marker: {
                size: z.map(val => Math.max(5, val * 10)), // 确保最小气泡大小
                sizemode: 'area',
                color: z,
                colorscale: options.colorscale || 'Viridis',
                colorbar: {
                    title: {
                        text: options.zAxisLabel || '大小',
                        font: {
                            size: 12
                        }
                    }
                },
                line: {
                    color: 'white',
                    width: 1
                }
            },
            text: data.map(item => item.name),
            mode: 'markers',
            type: 'scatter',
            name: options.seriesName || '气泡数据',
            hoverinfo: 'x+y+text',
            hovertemplate: `${options.xAxisLabel || 'X'}: %{x}<br>${options.yAxisLabel || 'Y'}: %{y}<br>大小: %{marker.size}<br>名称: %{text}<extra></extra>`
        }];

        const layout = {
            title: {
                text: options.title || '气泡图',
                font: {
                    size: 18,
                    weight: 'bold'
                }
            },
            xaxis: {
                title: {
                    text: options.xAxisLabel || '转速',
                    font: {
                        size: 14
                    }
                },
                tickangle: -45,
                gridcolor: '#f0f0f0',
                gridwidth: 1
            },
            yaxis: {
                title: {
                    text: options.yAxisLabel || '数值',
                    font: {
                        size: 14
                    }
                },
                gridcolor: '#f0f0f0',
                gridwidth: 1
            },
            margin: {
                l: 60,
                r: 80,
                b: 120,
                t: 60,
                pad: 4
            },
            showlegend: true,
            legend: {
                font: {
                    size: 12
                },
                orientation: 'v',
                x: 1.02,
                y: 1
            },
            hovermode: 'closest'
        };

        return [plotlyData, layout];
    }

    addChartEventListeners(chart, containerId, chartType) {
        if (!chart) return;

        // 点击事件
        chart.on('plotly_click', (data) => {
            console.log(`图表点击事件: ${containerId}`, data);
            // 可以在这里添加自定义的点击事件处理
        });

        // 悬停事件
        chart.on('plotly_hover', (data) => {
            console.log(`图表悬停事件: ${containerId}`, data);
            // 可以在这里添加自定义的悬停事件处理
        });

        // 缩放事件
        chart.on('plotly_relayout', (data) => {
            console.log(`图表缩放事件: ${containerId}`, data);
            // 可以在这里添加自定义的缩放事件处理
        });

        console.log(`已为图表 ${containerId} 添加事件监听器`);
    }

    resizeChart(containerId) {
        const chart = this.charts[containerId];
        if (chart && typeof chart.resize === 'function') {
            try {
                chart.resize();
                console.log(`已调整图表大小: ${containerId}`);
            } catch (error) {
                console.warn('调整图表大小时出错:', error.message);
            }
        }
    }

    destroyChart(containerId) {
        const chart = this.charts[containerId];
        if (chart && typeof chart.purge === 'function') {
            try {
                chart.purge();
                console.log(`已销毁图表: ${containerId}`);
            } catch (error) {
                console.warn('销毁图表时出错:', error.message);
            }
        }
        delete this.charts[containerId];
        delete this.chartData[containerId];
        if (this.eventListeners[containerId]) {
            this.eventListeners[containerId].forEach((listener) => {
                window.removeEventListener('resize', listener);
            });
            delete this.eventListeners[containerId];
        }
    }

    updateChart(containerId, data, options = {}) {
        const chart = this.charts[containerId];
        if (!chart) {
            console.warn(`图表实例不存在: ${containerId}`);
            return;
        }

        try {
            console.log(`开始更新图表: ${containerId}`);
            
            // 重新渲染图表
            const chartType = options.chartType || this.getChartType(containerId);
            if (chartType) {
                this.renderChart(containerId, chartType, data, options);
            }
        } catch (error) {
            console.error('更新图表时出错:', error);
            this.showError(containerId, `图表更新失败: ${error.message}`);
        }
    }

    getChartType(containerId) {
        // 简单实现，实际应用中可能需要更复杂的逻辑
        return 'scatter';
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

    // 实时更新相关方法
    startRealtimeUpdate(containerId, updateInterval = 5000, dataSource = null) {
        /**
         * 启动图表的实时更新
         * @param {string} containerId - 图表容器ID
         * @param {number} updateInterval - 更新间隔（毫秒）
         * @param {function} dataSource - 数据源函数，返回新数据
         */
        if (!this.charts[containerId]) {
            console.warn(`图表不存在: ${containerId}`);
            return false;
        }

        // 停止之前的更新
        this.stopRealtimeUpdate(containerId);

        this.realtimeUpdates[containerId] = {
            active: true,
            interval: updateInterval,
            dataSource: dataSource
        };

        // 开始更新循环
        this.updateIntervals[containerId] = setInterval(() => {
            this.updateChartData(containerId);
        }, updateInterval);

        console.log(`已启动图表 ${containerId} 的实时更新，间隔: ${updateInterval}ms`);
        return true;
    }

    stopRealtimeUpdate(containerId) {
        /**
         * 停止图表的实时更新
         * @param {string} containerId - 图表容器ID
         */
        if (this.updateIntervals[containerId]) {
            clearInterval(this.updateIntervals[containerId]);
            delete this.updateIntervals[containerId];
        }

        if (this.realtimeUpdates[containerId]) {
            this.realtimeUpdates[containerId].active = false;
        }

        console.log(`已停止图表 ${containerId} 的实时更新`);
    }

    updateChartData(containerId) {
        /**
         * 更新图表数据
         * @param {string} containerId - 图表容器ID
         */
        const updateConfig = this.realtimeUpdates[containerId];
        if (!updateConfig || !updateConfig.active) {
            return;
        }

        try {
            // 获取新数据
            let newData = null;
            if (updateConfig.dataSource && typeof updateConfig.dataSource === 'function') {
                newData = updateConfig.dataSource();
            } else {
                // 模拟数据更新
                newData = this.generateMockData(containerId);
            }

            if (newData) {
                // 更新图表
                const chart = this.charts[containerId];
                if (chart) {
                    // 根据图表类型更新数据
                    const chartType = this.getChartType(containerId);
                    const validatedData = this.validateAndPreprocessData(newData, chartType, containerId);
                    
                    if (validatedData) {
                        const [plotlyData] = this.renderChart(containerId, chartType, validatedData);
                        if (plotlyData && plotlyData.length > 0) {
                            Plotly.update(containerId, plotlyData);
                            console.log(`已更新图表 ${containerId} 的数据`);
                        }
                    }
                }
            }
        } catch (error) {
            console.error(`更新图表数据时出错: ${error.message}`);
        }
    }

    generateMockData(containerId) {
        /**
         * 生成模拟数据用于测试
         * @param {string} containerId - 图表容器ID
         * @returns {Array} 模拟数据
         */
        const chartType = this.getChartType(containerId);
        const baseData = this.getDefaultChartData(chartType);

        // 根据图表类型生成动态数据
        switch (chartType) {
            case 'box':
                return baseData.map(item => ({
                    name: item.name,
                    data: item.data.map(value => value + (Math.random() - 0.5) * 0.5)
                }));
            case 'scatter':
                return baseData.map(item => [
                    item[0],
                    item[1] + (Math.random() - 0.5) * 0.5
                ]);
            case 'trend':
                return baseData.map(item => ({
                    name: item.name,
                    value: item.value + (Math.random() - 0.5) * 0.5
                }));
            default:
                return baseData;
        }
    }

    isRealtimeUpdateActive(containerId) {
        /**
         * 检查图表的实时更新是否激活
         * @param {string} containerId - 图表容器ID
         * @returns {boolean} 是否激活
         */
        return this.realtimeUpdates[containerId] && this.realtimeUpdates[containerId].active;
    }

    // 配色方案管理
    colorSchemes = {
        // 方案1：专业科技蓝
        scheme1: {
            name: "专业科技蓝",
            primary: { rgb: "52, 152, 219", hex: "#3498db", hsl: "207, 70%, 52%" },
            secondary: {
                blue: { rgb: "41, 128, 185", hex: "#2980b9", hsl: "205, 64%, 44%" },
                teal: { rgb: "26, 188, 156", hex: "#1abc9c", hsl: "160, 66%, 41%" },
                purple: { rgb: "155, 89, 182", hex: "#9b59b6", hsl: "283, 40%, 52%" }
            },
            accent: {
                orange: { rgb: "241, 196, 15", hex: "#f1c40f", hsl: "48, 89%, 50%" },
                red: { rgb: "231, 76, 60", hex: "#e74c3c", hsl: "6, 76%, 57%" }
            },
            neutral: {
                white: { rgb: "255, 255, 255", hex: "#ffffff", hsl: "0, 0%, 100%" },
                light: { rgb: "245, 246, 250", hex: "#f5f6fa", hsl: "220, 13%, 95%" },
                gray: { rgb: "149, 165, 166", hex: "#95a5a6", hsl: "184, 14%, 62%" },
                dark: { rgb: "52, 73, 94", hex: "#34495e", hsl: "209, 24%, 28%" }
            },
            dataColors: [
                "rgba(52, 152, 219, %alpha%)",   // 主蓝色
                "rgba(155, 89, 182, %alpha%)",   // 紫色
                "rgba(26, 188, 156, %alpha%)",   // 青色
                "rgba(241, 196, 15, %alpha%)",   // 黄色
                "rgba(231, 76, 60, %alpha%)",    // 红色
                "rgba(46, 204, 113, %alpha%)",   // 绿色
                "rgba(155, 89, 182, %alpha%)",   // 深紫色
                "rgba(52, 73, 94, %alpha%)",     // 深蓝色
                "rgba(243, 156, 18, %alpha%)",   // 橙色
                "rgba(142, 68, 173, %alpha%)"    // 紫罗兰色
            ]
        },
        // 方案2：现代商务灰
        scheme2: {
            name: "现代商务灰",
            primary: { rgb: "52, 73, 94", hex: "#34495e", hsl: "209, 24%, 28%" },
            secondary: {
                slate: { rgb: "108, 122, 137", hex: "#6c7a89", hsl: "208, 13%, 47%" },
                olive: { rgb: "149, 165, 166", hex: "#95a5a6", hsl: "184, 14%, 62%" },
                amber: { rgb: "241, 196, 15", hex: "#f1c40f", hsl: "48, 89%, 50%" }
            },
            accent: {
                blue: { rgb: "52, 152, 219", hex: "#3498db", hsl: "207, 70%, 52%" },
                green: { rgb: "46, 204, 113", hex: "#2ecc71", hsl: "146, 63%, 49%" }
            },
            neutral: {
                white: { rgb: "255, 255, 255", hex: "#ffffff", hsl: "0, 0%, 100%" },
                light: { rgb: "245, 246, 250", hex: "#f5f6fa", hsl: "220, 13%, 95%" },
                gray: { rgb: "176, 190, 197", hex: "#b0bec5", hsl: "200, 14%, 72%" },
                dark: { rgb: "44, 62, 80", hex: "#2c3e50", hsl: "209, 29%, 24%" }
            },
            dataColors: [
                "rgba(52, 73, 94, %alpha%)",     // 主灰色
                "rgba(52, 152, 219, %alpha%)",   // 蓝色
                "rgba(46, 204, 113, %alpha%)",   // 绿色
                "rgba(241, 196, 15, %alpha%)",   // 黄色
                "rgba(230, 126, 34, %alpha%)",   // 橙色
                "rgba(155, 89, 182, %alpha%)",   // 紫色
                "rgba(231, 76, 60, %alpha%)",    // 红色
                "rgba(26, 188, 156, %alpha%)",   // 青色
                "rgba(142, 68, 173, %alpha%)",   // 紫罗兰色
                "rgba(52, 152, 219, %alpha%)"    // 亮蓝色
            ]
        },
        // 方案3：活力创新橙
        scheme3: {
            name: "活力创新橙",
            primary: { rgb: "243, 156, 18", hex: "#f39c12", hsl: "38, 87%, 50%" },
            secondary: {
                blue: { rgb: "52, 152, 219", hex: "#3498db", hsl: "207, 70%, 52%" },
                green: { rgb: "46, 204, 113", hex: "#2ecc71", hsl: "146, 63%, 49%" },
                purple: { rgb: "155, 89, 182", hex: "#9b59b6", hsl: "283, 40%, 52%" }
            },
            accent: {
                red: { rgb: "231, 76, 60", hex: "#e74c3c", hsl: "6, 76%, 57%" },
                teal: { rgb: "26, 188, 156", hex: "#1abc9c", hsl: "160, 66%, 41%" }
            },
            neutral: {
                white: { rgb: "255, 255, 255", hex: "#ffffff", hsl: "0, 0%, 100%" },
                light: { rgb: "249, 249, 249", hex: "#f9f9f9", hsl: "0, 0%, 98%" },
                gray: { rgb: "170, 170, 170", hex: "#aaaaaa", hsl: "0, 0%, 67%" },
                dark: { rgb: "51, 51, 51", hex: "#333333", hsl: "0, 0%, 20%" }
            },
            dataColors: [
                "rgba(243, 156, 18, %alpha%)",   // 主橙色
                "rgba(52, 152, 219, %alpha%)",   // 蓝色
                "rgba(46, 204, 113, %alpha%)",   // 绿色
                "rgba(155, 89, 182, %alpha%)",   // 紫色
                "rgba(231, 76, 60, %alpha%)",    // 红色
                "rgba(26, 188, 156, %alpha%)",   // 青色
                "rgba(241, 196, 15, %alpha%)",   // 黄色
                "rgba(142, 68, 173, %alpha%)",   // 紫罗兰色
                "rgba(52, 73, 94, %alpha%)",     // 深蓝色
                "rgba(230, 126, 34, %alpha%)"    // 深橙色
            ]
        }
    };

    // 当前使用的配色方案
    currentScheme = "scheme1";

    // 获取指定索引的颜色，用于区分不同转速的箱线图
    getColorForIndex(index, alpha = 0.7) {
        const scheme = this.colorSchemes[this.currentScheme];
        if (!scheme || !scheme.dataColors || scheme.dataColors.length === 0) {
            return `rgba(0, 0, 0, ${alpha})`;
        }
        const colorTemplate = scheme.dataColors[index % scheme.dataColors.length];
        return colorTemplate.replace("%alpha%", alpha);
    }

    // 获取指定颜色类型
    getColor(type, alpha = 1) {
        const scheme = this.colorSchemes[this.currentScheme];
        if (!scheme) {
            return `rgba(0, 0, 0, ${alpha})`;
        }
        if (type === "primary") {
            return `rgba(${scheme.primary.rgb}, ${alpha})`;
        } else if (type === "accent") {
            return `rgba(${scheme.accent.orange ? scheme.accent.orange.rgb : scheme.primary.rgb}, ${alpha})`;
        } else if (type === "neutral") {
            return `rgba(${scheme.neutral.gray.rgb}, ${alpha})`;
        }
        return `rgba(0, 0, 0, ${alpha})`;
    }

    // 切换配色方案
    setColorScheme(schemeName) {
        if (this.colorSchemes[schemeName]) {
            this.currentScheme = schemeName;
            console.log(`已切换到配色方案: ${this.colorSchemes[schemeName].name}`);
            return true;
        }
        console.warn(`配色方案 ${schemeName} 不存在`);
        return false;
    }

    // 获取当前配色方案信息
    getCurrentSchemeInfo() {
        return this.colorSchemes[this.currentScheme];
    }

    // 获取所有配色方案
    getAllSchemes() {
        return this.colorSchemes;
    }
}

// 全局实例
window.PlotlyManager = PlotlyManager;
window.plotlyManager = new PlotlyManager();