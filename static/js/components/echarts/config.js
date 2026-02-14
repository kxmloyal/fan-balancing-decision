// ECharts统一配置管理

/**
 * 图表主题配置
 */
export const CHART_THEMES = {
    default: {
        backgroundColor: '#ffffff',
        textStyle: {
            color: '#333333'
        },
        title: {
            textStyle: {
                color: '#333333',
                fontSize: 16,
                fontWeight: 'bold'
            }
        },
        legend: {
            textStyle: {
                color: '#666666'
            }
        },
        tooltip: {
            backgroundColor: 'rgba(50, 50, 50, 0.8)',
            textStyle: {
                color: '#ffffff'
            },
            borderColor: '#cccccc',
            borderWidth: 1
        },
        axisLine: {
            lineStyle: {
                color: '#999999'
            }
        },
        splitLine: {
            lineStyle: {
                color: '#f0f0f0',
                type: 'dashed'
            }
        }
    },
    dark: {
        backgroundColor: '#1a1a1a',
        textStyle: {
            color: '#cccccc'
        },
        title: {
            textStyle: {
                color: '#ffffff',
                fontSize: 16,
                fontWeight: 'bold'
            }
        },
        legend: {
            textStyle: {
                color: '#cccccc'
            }
        },
        tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            textStyle: {
                color: '#333333'
            },
            borderColor: '#666666',
            borderWidth: 1
        },
        axisLine: {
            lineStyle: {
                color: '#666666'
            }
        },
        splitLine: {
            lineStyle: {
                color: '#333333',
                type: 'dashed'
            }
        }
    },
    light: {
        backgroundColor: '#f8f9fa',
        textStyle: {
            color: '#333333'
        },
        title: {
            textStyle: {
                color: '#333333',
                fontSize: 14,
                fontWeight: 'normal'
            }
        },
        legend: {
            textStyle: {
                color: '#666666'
            }
        },
        tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            textStyle: {
                color: '#333333'
            },
            borderColor: '#e0e0e0',
            borderWidth: 1,
            shadowColor: 'rgba(0, 0, 0, 0.1)',
            shadowBlur: 10
        },
        axisLine: {
            lineStyle: {
                color: '#e0e0e0'
            }
        },
        splitLine: {
            lineStyle: {
                color: '#f0f0f0',
                type: 'dashed'
            }
        }
    }
};

/**
 * 图表类型默认配置
 */
export const CHART_TYPE_CONFIGS = {
    box: {
        series: {
            type: 'boxplot',
            itemStyle: {
                color: '#1f77b4',
                borderColor: '#1f77b4'
            },
            emphasis: {
                itemStyle: {
                    color: '#ff7f0e'
                }
            }
        },
        tooltip: {
            formatter: function(params) {
                const data = params[0].data;
                return [
                    `${params[0].name}<br/>`,
                    `最小值: ${data[0].toFixed(2)}<br/>`,
                    `下四分位: ${data[1].toFixed(2)}<br/>`,
                    `中位数: ${data[2].toFixed(2)}<br/>`,
                    `上四分位: ${data[3].toFixed(2)}<br/>`,
                    `最大值: ${data[4].toFixed(2)}`
                ].join('');
            }
        }
    },
    trend: {
        series: {
            type: 'line',
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
            areaStyle: {
                color: {
                    type: 'linear',
                    x: 0,
                    y: 0,
                    x2: 0,
                    y2: 1,
                    colorStops: [{
                        offset: 0, color: 'rgba(31, 119, 180, 0.3)'
                    }, {
                        offset: 1, color: 'rgba(31, 119, 180, 0.05)'
                    }]
                }
            }
        },
        tooltip: {
            formatter: function(params) {
                return `${params[0].name}: ${params[0].value.toFixed(2)}`;
            }
        }
    },
    scatter: {
        series: {
            type: 'scatter',
            symbolSize: 8,
            itemStyle: {
                color: '#1f77b4',
                opacity: 0.7
            }
        },
        tooltip: {
            formatter: function(params) {
                return `${params[0].name}: ${params[0].value[1].toFixed(2)}`;
            }
        }
    },
    heatmap: {
        series: {
            type: 'heatmap',
            label: {
                show: true,
                fontSize: 10
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            }
        },
        visualMap: {
            min: 0,
            max: 100,
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: '10%',
            inRange: {
                color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
            }
        }
    },
    histogram: {
        series: {
            type: 'bar',
            itemStyle: {
                color: '#1f77b4'
            },
            emphasis: {
                itemStyle: {
                    color: '#ff7f0e'
                }
            }
        },
        tooltip: {
            formatter: function(params) {
                return `${params[0].name}: ${params[0].value}`;
            }
        }
    },
    bubble: {
        series: {
            type: 'scatter',
            symbolSize: function(val) {
                return Math.sqrt(val[2]) * 5;
            },
            itemStyle: {
                color: '#1f77b4',
                opacity: 0.6
            }
        },
        tooltip: {
            formatter: function(params) {
                const data = params[0].value;
                return [
                    `${params[0].name}<br/>`,
                    `值: ${data[1].toFixed(2)}<br/>`,
                    `大小: ${data[2]}`
                ].join('');
            }
        }
    },
    '3d': {
        xAxis3D: {
            type: 'value',
            name: 'Speed',
            nameTextStyle: {
                fontSize: 12
            }
        },
        yAxis3D: {
            type: 'value',
            name: 'Index',
            nameTextStyle: {
                fontSize: 12
            }
        },
        zAxis3D: {
            type: 'value',
            name: 'Value',
            nameTextStyle: {
                fontSize: 12
            }
        },
        grid3D: {
            viewControl: {
                projection: 'perspective',
                autoRotate: true,
                autoRotateSpeed: 10,
                distance: 100
            }
        },
        series: {
            type: 'scatter3D',
            symbolSize: 5,
            itemStyle: {
                color: '#1f77b4'
            }
        }
    },
    parallel: {
        parallelAxis: [
            { name: 'Speed', type: 'value' },
            { name: 'Median', type: 'value' },
            { name: 'Mean', type: 'value' }
        ],
        series: {
            type: 'parallel',
            lineStyle: {
                width: 2,
                color: '#1f77b4'
            }
        }
    }
};

/**
 * 全局图表配置
 */
export const GLOBAL_CONFIG = {
    // 响应式配置
    responsive: {
        enabled: true,
        resizeDelay: 200,
        maxWidth: 1200,
        maxHeight: 600
    },
    
    // 动画配置
    animation: {
        enabled: true,
        duration: 1000,
        easing: 'cubicOut'
    },
    
    // 性能配置
    performance: {
        lazyLoad: true,
        useDirtyRect: true,
        useCoarsePointer: false,
        useWeakMap: true,
        cache: {
            enabled: true,
            maxSize: 100,
            ttl: 3600000 // 1小时
        }
    },
    
    // 渲染配置
    renderer: {
        preferred: 'canvas', // canvas 或 svg
        fallback: 'canvas'
    },
    
    // 数据处理配置
    dataProcessing: {
        maxPoints: 1000,
        sampling: true,
        samplingThreshold: 500
    },
    
    // 错误处理配置
    errorHandling: {
        showError: true,
        errorMessage: '图表加载失败',
        showEmptyData: true,
        emptyDataMessage: '暂无数据'
    }
};

/**
 * 图表工具函数
 */
export const ChartUtils = {
    /**
     * 获取图表主题
     * @param {string} themeName - 主题名称
     * @returns {Object} - 主题配置
     */
    getTheme(themeName) {
        return CHART_THEMES[themeName] || CHART_THEMES.default;
    },
    
    /**
     * 获取图表类型默认配置
     * @param {string} chartType - 图表类型
     * @returns {Object} - 图表类型配置
     */
    getChartTypeConfig(chartType) {
        return CHART_TYPE_CONFIGS[chartType] || {};
    },
    
    /**
     * 合并配置
     * @param {Object} base - 基础配置
     * @param {Object} override - 覆盖配置
     * @returns {Object} - 合并后的配置
     */
    mergeConfig(base, override) {
        if (!override) return base;
        
        const result = { ...base };
        for (const key in override) {
            if (override.hasOwnProperty(key)) {
                if (typeof override[key] === 'object' && override[key] !== null && !Array.isArray(override[key])) {
                    result[key] = this.mergeConfig(result[key] || {}, override[key]);
                } else {
                    result[key] = override[key];
                }
            }
        }
        return result;
    },
    
    /**
     * 生成图表配置
     * @param {string} chartType - 图表类型
     * @param {Object} data - 图表数据
     * @param {Object} options - 额外配置
     * @param {string} theme - 主题名称
     * @returns {Object} - 完整的图表配置
     */
    generateChartConfig(chartType, data, options = {}, theme = 'default') {
        const themeConfig = this.getTheme(theme);
        const typeConfig = this.getChartTypeConfig(chartType);
        
        // 基础配置
        const baseConfig = {
            ...themeConfig,
            ...typeConfig,
            series: typeConfig.series ? {
                ...typeConfig.series,
                data: data
            } : {
                data: data
            },
            animation: GLOBAL_CONFIG.animation.enabled,
            animationDuration: GLOBAL_CONFIG.animation.duration,
            animationEasing: GLOBAL_CONFIG.animation.easing
        };
        
        // 合并用户配置
        return this.mergeConfig(baseConfig, options);
    },
    
    /**
     * 优化大数据集
     * @param {Array} data - 原始数据
     * @param {number} maxPoints - 最大点数
     * @returns {Array} - 优化后的数据
     */
    optimizeLargeDataSet(data, maxPoints = GLOBAL_CONFIG.dataProcessing.maxPoints) {
        if (!Array.isArray(data) || data.length <= maxPoints) {
            return data;
        }
        
        const step = Math.ceil(data.length / maxPoints);
        const optimizedData = [];
        
        for (let i = 0; i < data.length; i += step) {
            optimizedData.push(data[i]);
        }
        
        return optimizedData;
    },
    
    /**
     * 计算数据范围
     * @param {Array} data - 数据数组
     * @returns {Object} - 数据范围 {min, max}
     */
    calculateDataRange(data) {
        if (!Array.isArray(data) || data.length === 0) {
            return { min: 0, max: 100 };
        }
        
        let min = Infinity;
        let max = -Infinity;
        
        data.forEach(item => {
            if (Array.isArray(item)) {
                item.forEach(val => {
                    if (typeof val === 'number') {
                        min = Math.min(min, val);
                        max = Math.max(max, val);
                    }
                });
            } else if (typeof item === 'number') {
                min = Math.min(min, item);
                max = Math.max(max, item);
            } else if (typeof item === 'object' && item !== null) {
                for (const key in item) {
                    if (typeof item[key] === 'number') {
                        min = Math.min(min, item[key]);
                        max = Math.max(max, item[key]);
                    }
                }
            }
        });
        
        return { min, max };
    },
    
    /**
     * 生成颜色数组
     * @param {number} count - 颜色数量
     * @returns {Array} - 颜色数组
     */
    generateColorPalette(count) {
        const baseColors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ];
        
        if (count <= baseColors.length) {
            return baseColors.slice(0, count);
        }
        
        // 如果需要更多颜色，生成额外的颜色
        const colors = [...baseColors];
        for (let i = baseColors.length; i < count; i++) {
            const hue = (i * 360 / count) % 360;
            colors.push(`hsl(${hue}, 70%, 50%)`);
        }
        
        return colors;
    }
};

/**
 * 图表配置管理器
 */
export class ChartConfigManager {
    constructor() {
        this.configs = new Map();
        this.defaultTheme = 'default';
    }
    
    /**
     * 注册图表配置
     * @param {string} key - 配置键
     * @param {Object} config - 配置对象
     */
    registerConfig(key, config) {
        this.configs.set(key, config);
    }
    
    /**
     * 获取图表配置
     * @param {string} key - 配置键
     * @returns {Object} - 配置对象
     */
    getConfig(key) {
        return this.configs.get(key);
    }
    
    /**
     * 删除图表配置
     * @param {string} key - 配置键
     */
    removeConfig(key) {
        this.configs.delete(key);
    }
    
    /**
     * 清空所有配置
     */
    clearConfigs() {
        this.configs.clear();
    }
    
    /**
     * 设置默认主题
     * @param {string} theme - 主题名称
     */
    setDefaultTheme(theme) {
        if (CHART_THEMES[theme]) {
            this.defaultTheme = theme;
        }
    }
    
    /**
     * 获取默认主题
     * @returns {string} - 默认主题名称
     */
    getDefaultTheme() {
        return this.defaultTheme;
    }
}

// 导出默认配置
export default {
    CHART_THEMES,
    CHART_TYPE_CONFIGS,
    GLOBAL_CONFIG,
    ChartUtils,
    ChartConfigManager
};