// 增强版Plotly管理器，与前端保持一致
class SimplePlotlyManager {
    constructor() {
        this.charts = {};
        this.eventListeners = {};
        this.resizeObserver = null;
        this.currentColorScheme = 'scheme1'; // 默认配色方案
        
        // 配色方案
        this.colorSchemes = {
            scheme1: {
                name: '专业科技蓝',
                primary: '#1f77b4',
                secondary: '#ff7f0e',
                accent: '#2ca02c',
                background: '#f8f9fa',
                text: '#333333',
                speedColors: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            },
            scheme2: {
                name: '现代商务灰',
                primary: '#2c3e50',
                secondary: '#95a5a6',
                accent: '#3498db',
                background: '#f5f5f5',
                text: '#333333',
                speedColors: ['#2c3e50', '#95a5a6', '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
            },
            scheme3: {
                name: '活力创新橙',
                primary: '#ff6b6b',
                secondary: '#4ecdc4',
                accent: '#45b7d1',
                background: '#f7f7f7',
                text: '#292f36',
                speedColors: ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeead', '#d9534f', '#5cb85c', '#f0ad4e', '#428bca', '#5bc0de']
            },
            scheme4: {
                name: '清新自然绿',
                primary: '#2ecc71',
                secondary: '#3498db',
                accent: '#9b59b6',
                background: '#ecf0f1',
                text: '#2c3e50',
                speedColors: ['#2ecc71', '#3498db', '#9b59b6', '#e74c3c', '#f1c40f', '#1abc9c', '#e67e22', '#34495e', '#95a5a6', '#27ae60']
            },
            scheme5: {
                name: '沉稳专业紫',
                primary: '#9b59b6',
                secondary: '#3498db',
                accent: '#e74c3c',
                background: '#f8f9fa',
                text: '#34495e',
                speedColors: ['#9b59b6', '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#1abc9c', '#e67e22', '#34495e', '#95a5a6', '#27ae60']
            }
        };
        
        // 多图表联动筛选相关
        this.selectionState = {}; // 存储当前选择状态
        this.linkedCharts = []; // 联动图表列表
        this.selectionMode = 'single'; // 选择模式：single, multiple, lasso
        
        // 动画相关配置
        this.animationConfig = {
            enabled: true, // 是否启用动画
            duration: 1000, // 动画持续时间（毫秒）
            easing: 'cubic-in-out', // 缓动函数
            transition: 'fade' // 过渡效果：fade, slide, zoom
        };
        
        // 主题相关配置
        this.themes = {
            default: {
                name: '默认主题',
                colors: {
                    primary: '#1f77b4',
                    secondary: '#ff7f0e',
                    accent: '#2ca02c',
                    background: '#f8f9fa',
                    text: '#333333',
                    speedColors: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
                },
                font: {
                    family: 'Arial, sans-serif',
                    size: 12,
                    weight: 'normal'
                },
                layout: {
                    margin: {
                        l: 60,
                        r: 40,
                        b: 80,
                        t: 60,
                        pad: 4
                    },
                    hoverlabel: {
                        bgcolor: 'rgba(255, 255, 255, 0.95)',
                        bordercolor: '#1f77b4',
                        borderwidth: 1,
                        font: {
                            color: '#333'
                        }
                    }
                }
            },
            dark: {
                name: '深色主题',
                colors: {
                    primary: '#4dabf7',
                    secondary: '#ff922b',
                    accent: '#51cf66',
                    background: '#1e1e1e',
                    text: '#e0e0e0',
                    speedColors: ['#4dabf7', '#ff922b', '#51cf66', '#ff6b6b', '#9775fa', '#fa5252', '#868e96', '#339af0', '#3bc9db', '#94d82d']
                },
                font: {
                    family: 'Arial, sans-serif',
                    size: 12,
                    weight: 'normal'
                },
                layout: {
                    margin: {
                        l: 60,
                        r: 40,
                        b: 80,
                        t: 60,
                        pad: 4
                    },
                    hoverlabel: {
                        bgcolor: 'rgba(40, 40, 40, 0.95)',
                        bordercolor: '#4dabf7',
                        borderwidth: 1,
                        font: {
                            color: '#e0e0e0'
                        }
                    }
                }
            },
            light: {
                name: '浅色主题',
                colors: {
                    primary: '#339af0',
                    secondary: '#ff7849',
                    accent: '#20c997',
                    background: '#ffffff',
                    text: '#212529',
                    speedColors: ['#339af0', '#ff7849', '#20c997', '#e64980', '#7950f2', '#fa5252', '#868e96', '#4c6ef5', '#0ca678', '#fab005']
                },
                font: {
                    family: 'Arial, sans-serif',
                    size: 12,
                    weight: 'normal'
                },
                layout: {
                    margin: {
                        l: 60,
                        r: 40,
                        b: 80,
                        t: 60,
                        pad: 4
                    },
                    hoverlabel: {
                        bgcolor: 'rgba(255, 255, 255, 0.95)',
                        bordercolor: '#339af0',
                        borderwidth: 1,
                        font: {
                            color: '#212529'
                        }
                    }
                }
            },
            professional: {
                name: '专业主题',
                colors: {
                    primary: '#2c3e50',
                    secondary: '#3498db',
                    accent: '#e74c3c',
                    background: '#f8f9fa',
                    text: '#34495e',
                    speedColors: ['#2c3e50', '#3498db', '#e74c3c', '#9b59b6', '#1abc9c', '#f1c40f', '#e67e22', '#34495e', '#95a5a6', '#27ae60']
                },
                font: {
                    family: 'Helvetica, Arial, sans-serif',
                    size: 12,
                    weight: 'normal'
                },
                layout: {
                    margin: {
                        l: 60,
                        r: 40,
                        b: 80,
                        t: 60,
                        pad: 4
                    },
                    hoverlabel: {
                        bgcolor: 'rgba(255, 255, 255, 0.95)',
                        bordercolor: '#2c3e50',
                        borderwidth: 1,
                        font: {
                            color: '#34495e'
                        }
                    }
                }
            },
            vibrant: {
                name: '活力主题',
                colors: {
                    primary: '#ff6b6b',
                    secondary: '#4ecdc4',
                    accent: '#45b7d1',
                    background: '#f7f7f7',
                    text: '#292f36',
                    speedColors: ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeead', '#d9534f', '#5cb85c', '#f0ad4e', '#428bca', '#5bc0de']
                },
                font: {
                    family: 'Arial, sans-serif',
                    size: 12,
                    weight: 'normal'
                },
                layout: {
                    margin: {
                        l: 60,
                        r: 40,
                        b: 80,
                        t: 60,
                        pad: 4
                    },
                    hoverlabel: {
                        bgcolor: 'rgba(255, 255, 255, 0.95)',
                        bordercolor: '#ff6b6b',
                        borderwidth: 1,
                        font: {
                            color: '#292f36'
                        }
                    }
                }
            },
            minimal: {
                name: '极简主题',
                colors: {
                    primary: '#6c757d',
                    secondary: '#adb5bd',
                    accent: '#ced4da',
                    background: '#ffffff',
                    text: '#212529',
                    speedColors: ['#6c757d', '#adb5bd', '#ced4da', '#dee2e6', '#e9ecef', '#f8f9fa', '#212529', '#495057', '#868e96', '#dee2e6']
                },
                font: {
                    family: 'Helvetica Neue, Arial, sans-serif',
                    size: 11,
                    weight: 'light'
                },
                layout: {
                    margin: {
                        l: 40,
                        r: 20,
                        b: 60,
                        t: 40,
                        pad: 2
                    },
                    hoverlabel: {
                        bgcolor: 'rgba(255, 255, 255, 0.9)',
                        bordercolor: '#6c757d',
                        borderwidth: 1,
                        font: {
                            color: '#212529'
                        }
                    }
                }
            },
            colorful: {
                name: '多彩主题',
                colors: {
                    primary: '#ff6384',
                    secondary: '#36a2eb',
                    accent: '#ffce56',
                    background: '#f9f9f9',
                    text: '#333333',
                    speedColors: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40', '#c9cbcf', '#ff6b6b', '#4ecdc4', '#45b7d1']
                },
                font: {
                    family: 'Comic Sans MS, Arial, sans-serif',
                    size: 12,
                    weight: 'normal'
                },
                layout: {
                    margin: {
                        l: 60,
                        r: 40,
                        b: 80,
                        t: 60,
                        pad: 4
                    },
                    hoverlabel: {
                        bgcolor: 'rgba(255, 255, 255, 0.95)',
                        bordercolor: '#ff6384',
                        borderwidth: 1,
                        font: {
                            color: '#333333'
                        }
                    }
                }
            }
        };
        
        this.currentTheme = 'default'; // 当前主题
        this.customThemes = {}; // 自定义主题
        
        // 加载状态相关配置
        this.loadingConfig = {
            enabled: true, // 是否启用加载状态
            showProgress: true, // 是否显示进度
            showError: true, // 是否显示错误
            animationDuration: 300, // 动画持续时间（毫秒）
            retryAttempts: 3 // 重试次数
        };
        
        // 加载状态管理
        this.loadingState = {}; // 存储每个图表的加载状态
        
        // 图表配置相关
        this.chartTemplates = {
            basic: {
                name: '基础图表',
                config: {
                    type: 'scatter',
                    options: {
                        title: '基础图表',
                        yAxisLabel: '值'
                    }
                }
            },
            trend: {
                name: '趋势图表',
                config: {
                    type: 'trend',
                    options: {
                        title: '趋势分析',
                        yAxisLabel: '数值'
                    }
                }
            },
            comparison: {
                name: '比较图表',
                config: {
                    type: 'box',
                    options: {
                        title: '数据比较',
                        yAxisLabel: '数值'
                    }
                }
            },
            distribution: {
                name: '分布图表',
                config: {
                    type: 'histogram',
                    options: {
                        title: '分布分析',
                        yAxisLabel: '频次'
                    }
                }
            },
            correlation: {
                name: '相关性图表',
                config: {
                    type: 'scatter',
                    options: {
                        title: '相关性分析',
                        yAxisLabel: '值'
                    }
                }
            }
        };
        
        this.savedConfigs = {}; // 保存的图表配置
        
        
        this.initResizeObserver();
        this.initResponsiveListeners();
        this.initResponsiveLayoutListeners();
        this.loadSavedColorScheme();
        this.loadCustomThemes();
        this.loadSavedTheme();
        this.loadSavedConfigs();
    }
    
    loadSavedColorScheme() {
        try {
            const savedScheme = localStorage.getItem('selectedColorScheme');
            if (savedScheme && this.colorSchemes[savedScheme]) {
                this.currentColorScheme = savedScheme;
            }
        } catch (error) {
            console.error('加载保存的配色方案失败:', error);
        }
    }

    loadCustomThemes() {
        try {
            const saved = localStorage.getItem('customThemes');
            if (saved) {
                this.customThemes = JSON.parse(saved);
            }
        } catch (error) {
            console.warn('加载自定义主题失败:', error.message);
        }
    }

    loadSavedTheme() {
        try {
            const saved = localStorage.getItem('savedTheme');
            if (saved && (this.themes[saved] || this.customThemes[saved])) {
                this.currentTheme = saved;
            }
        } catch (error) {
            console.warn('加载保存主题失败:', error.message);
        }
    }

    loadSavedConfigs() {
        try {
            const saved = localStorage.getItem('savedChartConfigs');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (parsed && typeof parsed === 'object') {
                    this.savedConfigs = parsed;
                }
            }
        } catch (error) {
            console.warn('加载保存配置失败:', error.message);
        }
    }
    
    saveColorScheme(schemeName) {
        try {
            localStorage.setItem('selectedColorScheme', schemeName);
        } catch (error) {
            console.error('保存配色方案失败:', error);
        }
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
        // 监听窗口大小变化
        const resizeHandler = this.debounce(() => {
            Object.keys(this.charts).forEach(containerId => {
                this.resizeChart(containerId);
            });
        }, 100);
        
        window.addEventListener('resize', resizeHandler);
        
        // 监听设备方向变化
        if (window.matchMedia) {
            const orientationHandler = this.debounce(() => {
                Object.keys(this.charts).forEach(containerId => {
                    this.resizeChart(containerId);
                });
            }, 100);
            
            window.matchMedia('(orientation: portrait)').addEventListener('change', orientationHandler);
        }
    }
    
    initResponsiveLayoutListeners() {
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
    }
    
    responsiveResize(containerId) {
        const container = document.getElementById(containerId);
        const chart = this.charts[containerId];
        
        if (!container || !chart) return;
        
        if (!container.clientWidth) return;
        
        // 检测设备类型
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        const width = container.clientWidth;
        const chartType = container.getAttribute('data-chart-type');
        
        // 根据图表类型和屏幕大小调整图表高度
        if (chartType === '3d') {
            // 3D图表使用接近正方形的比例
            if (width < 480) {
                container.style.height = isMobile ? '250px' : '300px';
            } else if (width < 768) {
                container.style.height = isMobile ? '300px' : '350px';
            } else if (width < 1200) {
                container.style.height = '450px';
            } else {
                container.style.height = '600px';
            }
        } else {
            // 其他图表使用原有高度设置
            if (width < 480) {
                container.style.height = isMobile ? '200px' : '250px';
            } else if (width < 768) {
                container.style.height = isMobile ? '250px' : '300px';
            } else if (width < 1200) {
                container.style.height = '400px';
            } else {
                container.style.height = '500px';
            }
        }
        
        // 为移动设备添加触摸操作支持
        if (isMobile) {
            container.style.touchAction = 'manipulation';
        }
        
        // 调整图表大小
        this.resizeChart(containerId);
    }
    
    initChart(containerId, chartType, data, options = {}) {
        
        // 检查Plotly库
        if (!window.Plotly) {
            console.error('Plotly库未加载');
            return null;
        }
        
        // 检查容器
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('图表容器不存在: ' + containerId);
            return null;
        }
        
        // 保存容器引用，供后续使用
        const chartContainer = container;
        
        // 确保容器有正确的样式
        container.style.width = '100%';
        container.style.height = '500px';
        container.style.minHeight = '450px';
        container.style.maxHeight = '600px';
        container.style.position = 'relative';
        container.style.overflow = 'visible';
        container.style.backgroundColor = '#ffffff';
        container.style.border = '1px solid #eee';
        container.style.borderRadius = '5px';
        container.style.display = 'block';
        container.style.boxSizing = 'border-box';
        container.style.zIndex = '1';
        container.style.opacity = '1';
        container.style.visibility = 'visible';
        
        // 强制重排
        container.offsetHeight;
        
        // 检查容器尺寸
        let containerWidth = container.clientWidth;
        let containerHeight = container.clientHeight;
        
        // 如果容器尺寸为0，尝试获取父容器尺寸
        if (containerWidth === 0 || containerHeight === 0) {
            const parent = container.parentElement;
            if (parent) {
                containerWidth = parent.clientWidth || 800;
                containerHeight = 420;
            } else {
                // 如果没有父容器，使用默认尺寸
                containerWidth = 800;
                containerHeight = 400;
            }
            
            // 设置容器尺寸
            container.style.width = containerWidth + 'px';
            container.style.height = containerHeight + 'px';
            // 强制重排
            container.offsetHeight;
        }
        
        try {
            // 验证数据格式
            const validatedData = this.validateChartData(data, chartType);
            
            // 首先尝试使用传入的数据
            let plotlyData = this.createPlotlyData(chartType, validatedData, options);
            let plotlyLayout = this.createPlotlyLayout(chartType, options);
            const plotlyConfig = this.createPlotlyConfig();
            
            // 确保数据有效
            if (plotlyData.length === 0) {
                console.warn('图表数据为空，使用默认数据');
                plotlyData = this.createDefaultData(chartType);
            }
            
            // 箱线/小提琴类图表收紧类别轴：Plotly 默认会在末类后 autoexpand，
            // 与左侧 Y 轴刻度相比右侧显得过空，这里显式限定 range 并收小右 margin
            if (chartType === 'box' || chartType === 'violin') {
                var catSet = [];
                plotlyData.forEach(function (t) {
                    if (Array.isArray(t.x)) {
                        t.x.forEach(function (x) {
                            if (x !== null && x !== undefined && catSet.indexOf(x) === -1) catSet.push(x);
                        });
                    }
                });
                if (catSet.length) {
                    plotlyLayout.xaxis = plotlyLayout.xaxis || {};
                    plotlyLayout.xaxis.type = 'category';
                    plotlyLayout.xaxis.range = [-0.5, catSet.length - 0.5];
                    plotlyLayout.margin = plotlyLayout.margin || {};
                    plotlyLayout.margin.r = 10;
                }
            }
            // 设置布局尺寸
            plotlyLayout.width = container.clientWidth;
            plotlyLayout.height = container.clientHeight;
            
            
            // 清除容器内容
            container.innerHTML = '';
            
            // 创建图表
            return Plotly.newPlot(containerId, plotlyData, plotlyLayout, plotlyConfig).then((chart) => {
                this.charts[containerId] = chart;
                
                // 为图表添加点击事件监听器
                chart.on('plotly_click', function() {
                    const chartSrc = chartContainer.getAttribute('data-chart-src');
                    const chartData = chartContainer.getAttribute('data-chart-data');
                    const chartTitle = chartContainer.getAttribute('data-chart-title');
                    if (chartSrc || chartData) {
                        
                        try {
                            const modalElement = document.getElementById('chartModal');
                            if (modalElement) {
                                const modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
                                modal.show(chartContainer);
                            } else {
                                console.error('PlotlyManager: 未找到模态框元素');
                            }
                        } catch (error) {
                            console.error('PlotlyManager: 显示模态框时出错:', error);
                        }
                    }
                });
                
                // 确保图表大小与容器匹配
                setTimeout(() => {
                    const currentWidth = container.clientWidth;
                    const currentHeight = container.clientHeight;
                    if (currentWidth > 0 && currentHeight > 0) {
                        Plotly.relayout(containerId, {
                            width: currentWidth,
                            height: currentHeight
                        });
                    }
                }, 100);
                
                // 再次调整图表大小，确保图表能够正确显示
                setTimeout(() => {
                    const currentWidth = container.clientWidth;
                    const currentHeight = container.clientHeight;
                    if (currentWidth > 0 && currentHeight > 0) {
                        Plotly.relayout(containerId, {
                            width: currentWidth,
                            height: currentHeight
                        });
                    }
                }, 500);
                
                // 强制重绘图表
                setTimeout(() => {
                    const currentWidth = container.clientWidth;
                    const currentHeight = container.clientHeight;
                    if (currentWidth > 0 && currentHeight > 0) {
                        Plotly.redraw(containerId);
                    }
                }, 1000);
                
                return chart;
            }).catch((error) => {
                console.error('初始化图表时出错:', error);
                console.error('错误详情:', error.stack);
                
                // 出错时使用默认数据
                console.warn('初始化图表出错，使用默认数据');
                const defaultData = this.createDefaultData(chartType);
                const defaultLayout = this.createPlotlyLayout(chartType, options);
                defaultLayout.width = container.clientWidth;
                defaultLayout.height = container.clientHeight;
                
                return Plotly.newPlot(containerId, defaultData, defaultLayout, plotlyConfig).then((chart) => {
                    this.charts[containerId] = chart;
                    
                    // 确保图表大小与容器匹配
                    setTimeout(() => {
                        const currentWidth = container.clientWidth;
                        const currentHeight = container.clientHeight;
                        if (currentWidth > 0 && currentHeight > 0) {
                            Plotly.relayout(containerId, {
                                width: currentWidth,
                                height: currentHeight
                            });
                        }
                    }, 100);
                    
                    // 再次调整图表大小，确保图表能够正确显示
                    setTimeout(() => {
                        const currentWidth = container.clientWidth;
                        const currentHeight = container.clientHeight;
                        if (currentWidth > 0 && currentHeight > 0) {
                            Plotly.relayout(containerId, {
                                width: currentWidth,
                                height: currentHeight
                            });
                        }
                    }, 500);
                    
                    // 强制重绘图表
                    setTimeout(() => {
                        const currentWidth = container.clientWidth;
                        const currentHeight = container.clientHeight;
                        if (currentWidth > 0 && currentHeight > 0) {
                            Plotly.redraw(containerId);
                        }
                    }, 1000);
                    
                    return chart;
                }).catch((error) => {
                    console.error('使用默认数据初始化图表时也出错:', error);
                    return null;
                });
            });
        } catch (error) {
            console.error('初始化图表时出错:', error);
            console.error('错误详情:', error.stack);
            
            // 出错时使用默认数据
            try {
                console.warn('初始化图表出错，使用默认数据');
                const defaultData = this.createDefaultData(chartType);
                const defaultLayout = this.createPlotlyLayout(chartType, options);
                defaultLayout.width = container.clientWidth;
                defaultLayout.height = container.clientHeight;
                const plotlyConfig = this.createPlotlyConfig();
                
                container.innerHTML = '';
                return Plotly.newPlot(containerId, defaultData, defaultLayout, plotlyConfig).then((chart) => {
                    this.charts[containerId] = chart;
                    return chart;
                }).catch((error) => {
                    console.error('使用默认数据初始化图表时也出错:', error);
                    return null;
                });
            } catch (innerError) {
                console.error('使用默认数据初始化图表时也出错:', innerError);
                return null;
            }
        }
    }
    
    // 创建默认数据
    createDefaultData(chartType) {
        switch (chartType) {
            case 'scatter':
                return [{
                    type: 'scatter',
                    x: ['2500rpm', '3000rpm', '3500rpm', '4000rpm', '4500rpm'],
                    y: [3, 4, 5, 6, 7],
                    mode: 'markers',
                    marker: {
                        color: ['#17becf', '#8c564b', '#1f77b4', '#e377c2', '#ff7f0e'],
                        size: 8
                    }
                }];
            case 'trend':
                return [{
                    type: 'scatter',
                    x: ['2500rpm', '3000rpm', '3500rpm', '4000rpm', '4500rpm'],
                    y: [3, 4, 5, 6, 7],
                    mode: 'lines+markers',
                    line: {
                        color: '#1f77b4',
                        width: 2
                    },
                    marker: {
                        color: ['#17becf', '#8c564b', '#1f77b4', '#e377c2', '#ff7f0e'],
                        size: 6
                    }
                }];
            case 'box':
            default:
                return [
                    {
                        type: 'box',
                        name: '2500rpm',
                        y: [1, 2, 3, 4, 5],
                        marker: {
                            color: '#17becf'
                        },
                        line: {
                            color: '#17becf'
                        }
                    },
                    {
                        type: 'box',
                        name: '3000rpm',
                        y: [2, 3, 4, 5, 6],
                        marker: {
                            color: '#8c564b'
                        },
                        line: {
                            color: '#8c564b'
                        }
                    },
                    {
                        type: 'box',
                        name: '3500rpm',
                        y: [3, 4, 5, 6, 7],
                        marker: {
                            color: '#1f77b4'
                        },
                        line: {
                            color: '#1f77b4'
                        }
                    },
                    {
                        type: 'box',
                        name: '4000rpm',
                        y: [4, 5, 6, 7, 8],
                        marker: {
                            color: '#e377c2'
                        },
                        line: {
                            color: '#e377c2'
                        }
                    },
                    {
                        type: 'box',
                        name: '4500rpm',
                        y: [5, 6, 7, 8, 9],
                        marker: {
                            color: '#ff7f0e'
                        },
                        line: {
                            color: '#ff7f0e'
                        }
                    },
                    {
                        type: 'scatter',
                        x: ['2500rpm', '3000rpm', '3500rpm', '4000rpm', '4500rpm'],
                        y: [3, 4, 5, 6, 7],
                        mode: 'lines',
                        name: '中位线',
                        line: {
                            color: '#ff7f0e',
                            width: 2,
                            dash: 'dash'
                        },
                        marker: {
                            color: '#ff7f0e',
                            size: 6
                        }
                    }
                ];
        }
    }
    
    ensureChartContainerSize(container) {
        if (!container) return;
        
        container.style.position = 'relative';
        container.style.display = 'block';
        container.style.width = '100%';
        container.style.minWidth = '250px';
        container.style.minHeight = '250px';
        container.style.boxSizing = 'border-box';
        container.style.overflow = 'visible';
        container.style.padding = '0';
        container.style.margin = '0';
        container.style.zIndex = '1';
        
        // 检测设备类型
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        // 根据图表类型和屏幕大小调整图表高度
        const width = container.clientWidth || window.innerWidth;
        const chartType = container.getAttribute('data-chart-type');
        
        if (chartType === '3d') {
            // 3D图表使用接近正方形的比例
            if (width < 480) {
                container.style.height = isMobile ? '280px' : '320px';
            } else if (width < 768) {
                container.style.height = isMobile ? '320px' : '380px';
            } else if (width < 1200) {
                container.style.height = '480px';
            } else {
                container.style.height = '620px';
            }
        } else {
            // 其他图表使用原有高度设置
            if (width < 480) {
                container.style.height = isMobile ? '230px' : '280px';
            } else if (width < 768) {
                container.style.height = isMobile ? '280px' : '330px';
            } else if (width < 1200) {
                container.style.height = '420px';
            } else {
                container.style.height = '520px';
            }
        }
        
        // 为移动设备添加触摸操作支持
        if (isMobile) {
            container.style.touchAction = 'manipulation';
        }
    }
    
    createPlotlyData(chartType, data, options) {
        try {
            
            switch (chartType) {
                case 'box':
                    return this.createBoxPlotData(data, options);
                case 'trend':
                    return this.createTrendPlotData(data, options);
                case 'scatter':
                    return this.createScatterPlotData(data, options);
                case 'violin':
                    return this.createViolinPlotData(data, options);
                case 'heatmap':
                    return this.createHeatmapData(data, options);
                case 'histogram':
                    return this.createHistogramData(data, options);
                case '3d':
                    return this.create3DScatterData(data, options);
                case 'parallel':
                    return this.createParallelData(data, options);
                case 'bubble':
                    return this.createBubbleData(data, options);
                case 'regression':
                    return this.createRegressionData(data, options);
                default:
                    console.warn(`未支持的图表类型: ${chartType}，使用默认散点图`);
                    // 返回默认散点图数据
                    return [{
                        type: 'scatter',
                        x: ['2500rpm', '3000rpm', '3500rpm', '4000rpm', '4500rpm'],
                        y: [3, 4, 5, 6, 7],
                        mode: 'markers',
                        marker: {
                            color: ['#17becf', '#8c564b', '#1f77b4', '#e377c2', '#ff7f0e'],
                            size: 8
                        }
                    }];
            }
        } catch (error) {
            console.error('创建图表数据时出错:', error);
            console.error('错误详情:', error.stack);
            // 返回默认散点图数据
            return [{
                type: 'scatter',
                x: ['2500rpm', '3000rpm', '3500rpm', '4000rpm', '4500rpm'],
                y: [3, 4, 5, 6, 7],
                mode: 'markers',
                marker: {
                    color: ['#17becf', '#8c564b', '#1f77b4', '#e377c2', '#ff7f0e'],
                    size: 8
                }
            }];
        }
    }
    
    createPlotlyLayout(chartType, options) {
        const { title = '图表', yAxisLabel = '值' } = options;
        const layout = {
            title: {
                text: title,
                x: 0.5,
                font: {
                    size: 16,
                    weight: 'bold'
                }
            },
            margin: {
                l: 50,
                r: 50,
                b: 80,
                t: 50,
                pad: 4
            },
            hovermode: 'closest',
            hoverlabel: {
                bgcolor: 'rgba(255, 255, 255, 0.95)',
                bordercolor: '#1f77b4',
                borderwidth: 1,
                font: {
                    color: '#333'
                }
            },
            showlegend: false
        };
        
        
        switch (chartType) {
            case 'box':
            case 'trend':
            case 'scatter':
            case 'violin':
            case 'histogram':
            case 'bubble':
            case 'regression':
                layout.xaxis = {
                    title: {
                        text: '类别'
                    },
                    tickangle: 0,
                    tickfont: {
                        size: 11
                    },
                    automargin: true,
                    tickmode: 'auto',
                    nticks: 'auto',
                    tickformat: '',
                    tickposition: 'outside',
                    ticklen: 5,
                    tickwidth: 1,
                    showgrid: false,
                    range: 'auto'
                };
                layout.yaxis = {
                    title: {
                        text: yAxisLabel
                    },
                    tickfont: {
                        size: 11
                    },
                    automargin: true,
                    range: 'auto'
                };
                break;
            case 'heatmap':
                layout.xaxis = {
                    tickangle: 45,
                    tickfont: {
                        size: 11
                    },
                    automargin: true
                };
                layout.yaxis = {
                    tickfont: {
                        size: 11
                    },
                    automargin: true
                };
                layout.coloraxis = {
                    colorscale: 'Viridis',
                    colorbar: {
                        title: yAxisLabel
                    }
                };
                break;
            case '3d':
                layout.scene = {
                    xaxis: {
                        title: 'X',
                        showgrid: true,
                        gridwidth: 1,
                        gridcolor: '#e0e0e0'
                    },
                    yaxis: {
                        title: 'Y',
                        showgrid: true,
                        gridwidth: 1,
                        gridcolor: '#e0e0e0'
                    },
                    zaxis: {
                        title: yAxisLabel,
                        showgrid: true,
                        gridwidth: 1,
                        gridcolor: '#e0e0e0'
                    },
                    camera: {
                        autorotate: true,
                        autorotateSpeed: 5,
                        eye: {
                            x: 1.2,
                            y: 1.2,
                            z: 1.2
                        }
                    },
                    aspectmode: 'data',
                    aspectratio: {
                        x: 1,
                        y: 1,
                        z: 1
                    }
                };
                layout.margin = {
                    l: 10,
                    r: 10,
                    b: 10,
                    t: 50,
                    pad: 4
                };
                break;
            case 'parallel':
                layout.parallelCoordinates = {
                    dimensions: []
                };
                break;
        }
        
        return layout;
    }
    
    createPlotlyConfig() {
        return {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['sendDataToCloud'],
            scrollZoom: true,
            toImageButtonOptions: {
                format: 'png',
                filename: 'chart',
                height: 500,
                width: 700,
                scale: 2
            },
            // 允许点击事件穿透到容器
            staticPlot: false
        };
    }
    
    // 数据转换方法
    
    // 检查并修复数据格式
    validateChartData(data, chartType) {
        if (!data) {
            console.warn('数据为空，使用默认数据');
            return this.createDefaultData(chartType);
        }
        
        if (typeof data === 'string') {
            try {
                data = JSON.parse(data);
            } catch (error) {
                console.error('数据解析失败，使用默认数据:', error);
                return this.createDefaultData(chartType);
            }
        }
        
        if (!Array.isArray(data) && typeof data !== 'object') {
            console.warn('数据格式无效，使用默认数据');
            return this.createDefaultData(chartType);
        }
        
        return data;
    }
    
    convertToScatterData(data) {
        if (!data || typeof data !== 'object') {
            // 返回默认数据
            return [['2500rpm', 3], ['3000rpm', 4], ['3500rpm', 5], ['4000rpm', 6], ['4500rpm', 7]];
        }

        if (Array.isArray(data)) {
            // 处理后端返回的格式：[[转速, 不平衡量], [转速, 不平衡量], ...]
            const result = data.map(item => {
                if (Array.isArray(item) && item.length >= 2) {
                    return [item[0], typeof item[1] === 'number' ? item[1] : 0];
                }
                return ['', 0];
            }).filter(item => item[0] !== '');
            
            // 如果结果为空，返回默认数据
            if (result.length === 0) {
                return [['2500rpm', 3], ['3000rpm', 4], ['3500rpm', 5], ['4000rpm', 6], ['4500rpm', 7]];
            }
            return result;
        }

        const result = Object.entries(data).map(([key, value]) => [key, typeof value === 'number' ? value : 0]);
        
        // 如果结果为空，返回默认数据
        if (result.length === 0) {
            return [['2500rpm', 3], ['3000rpm', 4], ['3500rpm', 5], ['4000rpm', 6], ['4500rpm', 7]];
        }
        return result;
    }
    
    convertToTrendData(data) {
        if (!data || typeof data !== 'object') {
            // 返回默认数据
            return [
                { name: '2500rpm', value: 3 },
                { name: '3000rpm', value: 4 },
                { name: '3500rpm', value: 5 },
                { name: '4000rpm', value: 6 },
                { name: '4500rpm', value: 7 }
            ];
        }

        if (Array.isArray(data)) {
            // 处理后端返回的格式：[{"name": "转速", "value": 中位数}]
            const result = data.map(item => {
                if (typeof item === 'object' && item !== null && 'name' in item && 'value' in item) {
                    return {
                        name: item.name,
                        value: typeof item.value === 'number' ? item.value : 0
                    };
                }
                return {
                    name: '',
                    value: 0
                };
            }).filter(item => item.name !== '');
            
            // 如果结果为空，返回默认数据
            if (result.length === 0) {
                return [
                    { name: '2500rpm', value: 3 },
                    { name: '3000rpm', value: 4 },
                    { name: '3500rpm', value: 5 },
                    { name: '4000rpm', value: 6 },
                    { name: '4500rpm', value: 7 }
                ];
            }
            return result;
        }

        const result = Object.entries(data).map(([key, value]) => ({
            name: key,
            value: typeof value === 'number' ? value : 0
        }));
        
        // 如果结果为空，返回默认数据
        if (result.length === 0) {
            return [
                { name: '2500rpm', value: 3 },
                { name: '3000rpm', value: 4 },
                { name: '3500rpm', value: 5 },
                { name: '4000rpm', value: 6 },
                { name: '4500rpm', value: 7 }
            ];
        }
        return result;
    }
    
    convertToViolinData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            // 处理后端返回的格式：[{"name": "转速", "data": [值1, 值2, ...]}]
            return data.map(item => {
                if (typeof item === 'object' && item !== null && 'name' in item && 'data' in item) {
                    return {
                        name: item.name,
                        data: Array.isArray(item.data) ? item.data : [0]
                    };
                }
                return {
                    name: '',
                    data: [0]
                };
            });
        }

        return Object.entries(data).map(([key, value]) => ({
            name: key,
            data: Array.isArray(value) ? value : [0]
        }));
    }
    
    convertToHeatmapData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        const result = [];
        if (Array.isArray(data)) {
            // 处理后端返回的格式：[["转速", 索引, 值], ["转速", 索引, 值], ...]
            data.forEach(item => {
                if (Array.isArray(item) && item.length >= 3) {
                    result.push([item[0], item[1], typeof item[2] === 'number' ? item[2] : 0]);
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
    
    convertToHistogramData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            // 处理后端返回的格式：[频次1, 频次2, 频次3, ...]
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
    
    convertTo3DScatterData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        const result = [];
        if (Array.isArray(data)) {
            // 处理后端返回的格式：[["转速", 索引, 值], ["转速", 索引, 值], ...]
            data.forEach(item => {
                if (Array.isArray(item) && item.length >= 3) {
                    result.push([item[0], item[1], typeof item[2] === 'number' ? item[2] : 0]);
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
    
    convertToParallelData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            // 处理后端返回的格式：[["转速", 中位数, 均值], ["转速", 中位数, 均值], ...]
            return data.map(item => Array.isArray(item) ? item : []);
        }

        return Object.values(data).map(value => Array.isArray(value) ? value : []);
    }
    
    convertToBubbleData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            // 处理后端返回的格式：[{"name": "转速", "value": ["转速", 中位数, 数据点数量]}]
            return data.map(item => {
                if (typeof item === 'object' && item !== null && 'name' in item && 'value' in item) {
                    return {
                        name: item.name,
                        value: Array.isArray(item.value) ? item.value : [0, 0, 0]
                    };
                }
                return {
                    name: '',
                    value: [0, 0, 0]
                };
            });
        }

        return Object.entries(data).map(([key, value]) => ({
            name: key,
            value: Array.isArray(value) ? value : [0, 0, 0]
        }));
    }
    
    convertToRegressionData(data) {
        if (!data || typeof data !== 'object') {
            return [];
        }

        if (Array.isArray(data)) {
            return data.map((item, index) => [index, typeof item === 'number' ? item : 0]);
        }

        return Object.entries(data).map(([key, value]) => [key, typeof value === 'number' ? value : 0]);
    }
    
    
    create3DScatterData(data, options) {
        const seriesData = this.convertTo3DScatterData(data);
        const x = seriesData.map(item => item[0]);
        const y = seriesData.map(item => item[1]);
        const z = seriesData.map(item => item[2]);
        
        // 为每个数据点使用不同的颜色
        const markers = {
            color: seriesData.map(item => this.getSpeedColor(item[0])),
            size: 8,
            opacity: 0.6
        };
        
        // 为每个数据点添加自定义悬停信息
        const text = seriesData.map(item => `转速: ${item[0]}<br>索引: ${item[1]}<br>值: ${item[2].toFixed(2)}`);
        
        return [{
            type: 'scatter3d',
            x: x,
            y: y,
            z: z,
            mode: 'markers',
            marker: markers,
            hoverinfo: 'text',
            text: text
        }];
    }
    
    
    resizeChart(containerId) {
        const chart = this.charts[containerId];
        const container = document.getElementById(containerId);
        if (chart && container) {
            try {
                const width = container.clientWidth;
                const height = container.clientHeight;
                
                if (width > 0 && height > 0) {
                    Plotly.relayout(containerId, {
                        width: width,
                        height: height
                    });
                }
            } catch (error) {
                console.warn('调整图表大小时出错:', error.message);
            }
        }
    }
    
    destroyChart(containerId) {
        const chart = this.charts[containerId];
        if (chart) {
            try {
                Plotly.purge(containerId);
            } catch (error) {
                console.warn('销毁图表实例时出错:', error.message);
            }
        }
        delete this.charts[containerId];

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
    
    setColorScheme(schemeName) {
        // 配色方案切换功能
        
        if (!this.colorSchemes[schemeName]) {
            console.error(`未知的配色方案: ${schemeName}`);
            return;
        }
        
        // 更新当前配色方案
        this.currentColorScheme = schemeName;
        
        // 保存到localStorage
        this.saveColorScheme(schemeName);
        
        // 应用配色方案到页面元素
        this.applyColorSchemeToPage();
        
        // 重新渲染所有图表
        this.rerenderAllCharts();
        
        // 更新转速颜色选择组件
        if (typeof initSpeedColorSelector === 'function') {
            initSpeedColorSelector();
        }
    }
    
    
    
    
    
    // 转速颜色映射表
    speedColorMap = {
        '2500rpm': '#1f77b4',  // 蓝色
        '3000rpm': '#ff7f0e',  // 橙色
        '3500rpm': '#2ca02c',  // 绿色
        '4000rpm': '#d62728',  // 红色
        '4500rpm': '#9467bd',  // 紫色
        '5000rpm': '#8c564b',  // 棕色
        '5500rpm': '#e377c2',  // 粉色
        '6000rpm': '#7f7f7f',  // 灰色
        '6500rpm': '#bcbd22',  // 黄绿色
        '7000rpm': '#17becf'   // 青色
    };


    // 获取转速颜色映射表
    
    
    /**
     * 根据图表类型自动推荐配色方案
     * @param {string} chartType - 图表类型
     * @returns {string} 推荐的配色方案名称
     */
    
    /**
     * 应用推荐的配色方案到指定图表
     * @param {string} containerId - 图表容器ID
     * @param {string} chartType - 图表类型
     */
    
    /**
     * 添加图表到联动列表
     * @param {string} containerId - 图表容器ID
     */
    addToLinkedCharts(containerId) {
        if (!this.linkedCharts.includes(containerId)) {
            this.linkedCharts.push(containerId);
            this.setupSelectionEvents(containerId);
        }
    }
    
    /**
     * 从联动列表中移除图表
     * @param {string} containerId - 图表容器ID
     */
    removeFromLinkedCharts(containerId) {
        const index = this.linkedCharts.indexOf(containerId);
        if (index > -1) {
            this.linkedCharts.splice(index, 1);
        }
    }
    
    /**
     * 设置图表选择事件
     * @param {string} containerId - 图表容器ID
     */
    
    /**
     * 高亮联动图表中相关的数据点
     * @param {string} containerId - 图表容器ID
     * @param {Set} selectedValues - 选择的值集合
     */
    highlightLinkedChartData(containerId, selectedValues) {
        const chart = this.charts[containerId];
        if (!chart) return;
        
        try {
            const data = chart.data;
            const updatedData = data.map(trace => {
                // 为每个数据点创建颜色数组
                const colors = [];
                const sizes = [];
                
                // 检查数据格式并处理
                if (trace.x && Array.isArray(trace.x)) {
                    for (let i = 0; i < trace.x.length; i++) {
                        const xValue = trace.x[i].toString();
                        const yValue = trace.y ? trace.y[i].toString() : '';
                        const nameValue = trace.name ? trace.name : '';
                        
                        // 检查是否匹配选择的值
                        const isSelected = selectedValues.has(xValue) || 
                                         selectedValues.has(yValue) || 
                                         selectedValues.has(nameValue);
                        
                        // 设置颜色和大小
                        colors.push(isSelected ? '#ff0000' : trace.marker?.color || '#1f77b4');
                        sizes.push(isSelected ? 10 : trace.marker?.size || 6);
                    }
                }
                
                return {
                    ...trace,
                    marker: {
                        ...trace.marker,
                        color: colors.length > 0 ? colors : trace.marker?.color,
                        size: sizes.length > 0 ? sizes : trace.marker?.size
                    }
                };
            });
            
            // 更新图表数据
            Plotly.restyle(containerId, updatedData);
        } catch (error) {
            console.error('更新联动图表时出错:', error);
        }
    }
    
    /**
     * 清除所有图表的选择状态
     */
    clearAllSelections() {
        this.selectionState = {};
        
        // 重置所有联动图表的样式
        this.linkedCharts.forEach(containerId => {
            const chart = this.charts[containerId];
            if (chart) {
                try {
                    const data = chart.data;
                    const resetData = data.map(trace => {
                        return {
                            ...trace,
                            marker: {
                                ...trace.marker,
                                color: trace.marker?.color && Array.isArray(trace.marker.color) ? 
                                    trace.marker.color.map(() => trace.marker?.color[0] || '#1f77b4') : 
                                    trace.marker?.color,
                                size: trace.marker?.size && Array.isArray(trace.marker.size) ? 
                                    trace.marker.size.map(() => trace.marker?.size[0] || 6) : 
                                    trace.marker?.size
                            }
                        };
                    });
                    
                    Plotly.restyle(containerId, resetData);
                } catch (error) {
                    console.error('重置图表选择状态时出错:', error);
                }
            }
        });
        
    }
    
    /**
     * 设置选择模式
     * @param {string} mode - 选择模式：single, multiple, lasso
     */
    setSelectionMode(mode) {
        if (['single', 'multiple', 'lasso'].includes(mode)) {
            this.selectionMode = mode;
        } else {
            console.error('无效的选择模式:', mode);
        }
    }
    
    /**
     * 获取当前选择状态
     * @returns {object} 选择状态
     */
    getSelectionState() {
        return this.selectionState;
    }
    
    /**
     * 获取联动图表列表
     * @returns {array} 联动图表列表
     */
    getLinkedCharts() {
        return this.linkedCharts;
    }
    
    /**
     * 设置动画配置
     * @param {object} config - 动画配置对象
     */
    setAnimationConfig(config) {
        this.animationConfig = {
            ...this.animationConfig,
            ...config
        };
    }
    
    /**
     * 启用或禁用动画
     * @param {boolean} enabled - 是否启用动画
     */
    setAnimationEnabled(enabled) {
        this.animationConfig.enabled = enabled;
    }
    
    /**
     * 设置动画持续时间
     * @param {number} duration - 动画持续时间（毫秒）
     */
    setAnimationDuration(duration) {
        this.animationConfig.duration = duration;
    }
    
    /**
     * 设置动画缓动函数
     * @param {string} easing - 缓动函数
     */
    setAnimationEasing(easing) {
        const validEasings = ['linear', 'cubic-in', 'cubic-out', 'cubic-in-out', 'quad-in', 'quad-out', 'quad-in-out', 'sin-in', 'sin-out', 'sin-in-out', 'exp-in', 'exp-out', 'exp-in-out', 'circle-in', 'circle-out', 'circle-in-out', 'back-in', 'back-out', 'back-in-out', 'elastic-in', 'elastic-out', 'elastic-in-out', 'bounce-in', 'bounce-out', 'bounce-in-out'];
        
        if (validEasings.includes(easing)) {
            this.animationConfig.easing = easing;
        } else {
            console.error('无效的缓动函数:', easing);
        }
    }
    
    /**
     * 设置动画过渡效果
     * @param {string} transition - 过渡效果：fade, slide, zoom
     */
    setAnimationTransition(transition) {
        const validTransitions = ['fade', 'slide', 'zoom'];
        
        if (validTransitions.includes(transition)) {
            this.animationConfig.transition = transition;
        } else {
            console.error('无效的过渡效果:', transition);
        }
    }
    
    /**
     * 获取当前动画配置
     * @returns {object} 动画配置
     */
    getAnimationConfig() {
        return this.animationConfig;
    }
    
    /**
     * 应用动画配置到图表布局
     * @param {object} layout - 图表布局对象
     * @returns {object} 应用了动画配置的布局对象
     */
    
    
    /**
     * 获取所有可用主题
     * @returns {array} 主题列表
     */
    getAvailableThemes() {
        const themes = Object.keys(this.themes).map(key => ({
            name: key,
            displayName: this.themes[key].name,
            isDefault: true
        }));
        
        const customThemes = Object.keys(this.customThemes).map(key => ({
            name: key,
            displayName: this.customThemes[key].name,
            isDefault: false
        }));
        
        return [...themes, ...customThemes];
    }
    
    /**
     * 获取主题配置
     * @param {string} themeName - 主题名称
     * @returns {object} 主题配置
     */
    getThemeConfig(themeName = this.currentTheme) {
        return this.themes[themeName] || this.customThemes[themeName] || this.themes.default;
    }
    
    /**
     * 应用主题到页面
     */
    
    
    
    /**
     * 设置加载配置
     * @param {object} config - 加载配置对象
     */
    setLoadingConfig(config) {
        this.loadingConfig = {
            ...this.loadingConfig,
            ...config
        };
    }
    
    /**
     * 重试加载
     * @param {string} containerId - 图表容器ID
     * @param {function} loadFunction - 加载函数
     */
    async retryLoading(containerId, loadFunction) {
        let attempts = 0;
        
        const attemptLoad = async () => {
            attempts++;
            
            try {
                this.showLoading(containerId, `加载中... (${attempts}/${this.loadingConfig.retryAttempts})`);
                await loadFunction();
                this.hideLoading(containerId);
                return true;
            } catch (error) {
                console.error(`加载失败 (尝试 ${attempts}/${this.loadingConfig.retryAttempts}):`, error);
                
                if (attempts < this.loadingConfig.retryAttempts) {
                    // 延迟后重试
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    return attemptLoad();
                } else {
                    // 达到最大重试次数
                    this.showError(containerId, `加载失败，请稍后重试。错误: ${error.message}`, () => {
                        this.retryLoading(containerId, loadFunction);
                    });
                    return false;
                }
            }
        };
        
        return attemptLoad();
    }
    
    /**
     * 获取加载状态
     * @param {string} containerId - 图表容器ID
     * @returns {object} 加载状态
     */
    getLoadingState(containerId) {
        return this.loadingState[containerId] || {};
    }
    
    /**
     * 优化图表加载性能
     * @param {string} containerId - 图表容器ID
     * @param {function} loadFunction - 加载函数
     */
    async optimizedLoad(containerId, loadFunction) {
        try {
            this.showLoading(containerId);
            
            // 测量加载时间
            const startTime = performance.now();
            await loadFunction();
            const endTime = performance.now();
            
            
            // 延迟隐藏加载状态，确保动画效果可见
            setTimeout(() => {
                this.hideLoading(containerId);
            }, 300);
        } catch (error) {
            console.error('图表加载失败:', error);
            this.showError(containerId, `加载失败: ${error.message}`, () => {
                this.optimizedLoad(containerId, loadFunction);
            });
        }
    }
    
    /**
     * 批量渲染图表，优化性能
     * @param {array} chartConfigs - 图表配置数组
     */
    async batchRenderCharts(chartConfigs) {
        // 分组处理，避免同时渲染过多图表
        const batchSize = 3;
        for (let i = 0; i < chartConfigs.length; i += batchSize) {
            const batch = chartConfigs.slice(i, i + batchSize);
            await Promise.all(batch.map(config => {
                return new Promise((resolve) => {
                    setTimeout(() => {
                        this.initChart(config.containerId, config.type, config.data, config.options);
                        resolve();
                    }, 50); // 小延迟避免阻塞
                });
            }));
        }
    }
    
    /**
     * 优化大数据集处理
     * @param {array} data - 原始数据
     * @param {number} maxPoints - 最大数据点数量
     * @returns {array} 优化后的数据
     */
    optimizeLargeDataSet(data, maxPoints = 1000) {
        if (!Array.isArray(data) || data.length <= maxPoints) {
            return data;
        }
        
        // 数据降采样
        const step = Math.ceil(data.length / maxPoints);
        const optimizedData = [];
        
        for (let i = 0; i < data.length; i += step) {
            optimizedData.push(data[i]);
        }
        
        return optimizedData;
    }
    
    /**
     * 清理所有图表实例和资源
     */
    cleanup() {
        // 销毁所有图表实例
        Object.keys(this.charts).forEach(containerId => {
            this.destroyChart(containerId);
        });
        
        // 清理事件监听器
        this.eventListeners = {};
        
        // 清理选择状态
        this.selectionState = {};
        
        // 清理联动图表列表
        this.linkedCharts = [];
        
        // 清理加载状态
        this.loadingState = {};
        
        // 清理ResizeObserver
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
            this.resizeObserver = null;
        }
        
    }
    
    
    /**
     * 启用自动清理机制
     * @param {number} interval - 清理间隔（毫秒）
     */
    enableAutoCleanup(interval = 60000) {
        if (this.autoCleanupInterval) {
            clearInterval(this.autoCleanupInterval);
        }
        
        this.autoCleanupInterval = setInterval(() => {
            // 清理未使用的图表
            const activeContainers = [];
            document.querySelectorAll('.plotly-chart').forEach(container => {
                activeContainers.push(container.id);
            });
            
            Object.keys(this.charts).forEach(containerId => {
                if (!activeContainers.includes(containerId)) {
                    this.destroyChart(containerId);
                }
            });
        }, interval);
        
    }
    
    /**
     * 禁用自动清理机制
     */
    disableAutoCleanup() {
        if (this.autoCleanupInterval) {
            clearInterval(this.autoCleanupInterval);
            this.autoCleanupInterval = null;
        }
    }
    
    
    /**
     * 保存配置
     */
    saveConfigs() {
        try {
            localStorage.setItem('chartConfigs', JSON.stringify(this.savedConfigs));
        } catch (error) {
            console.error('保存配置失败:', error);
        }
    }
    
    /**
     * 获取所有图表模板
     * @returns {object} 图表模板对象
     */
    getChartTemplates() {
        return this.chartTemplates;
    }
    
    /**
     * 获取指定模板
     * @param {string} templateName - 模板名称
     * @returns {object} 模板配置
     */
    getChartTemplate(templateName) {
        return this.chartTemplates[templateName] || null;
    }
    
    /**
     * 应用图表模板
     * @param {string} containerId - 图表容器ID
     * @param {string} templateName - 模板名称
     * @param {object} data - 图表数据
     * @returns {object} 应用模板后的图表实例
     */
    
    /**
     * 保存图表配置
     * @param {string} configName - 配置名称
     * @param {object} config - 图表配置
     */
    saveChartConfig(configName, config) {
        this.savedConfigs[configName] = config;
        this.saveConfigs();
    }
    
    /**
     * 加载图表配置
     * @param {string} configName - 配置名称
     * @returns {object} 图表配置
     */
    
    /**
     * 删除图表配置
     * @param {string} configName - 配置名称
     */
    deleteChartConfig(configName) {
        if (this.savedConfigs[configName]) {
            delete this.savedConfigs[configName];
            this.saveConfigs();
        }
    }
    
    /**
     * 获取所有保存的配置
     * @returns {object} 保存的配置对象
     */
    getSavedConfigs() {
        return this.savedConfigs;
    }
}

// 创建全局plotlyManager实例
const plotlyManager = new SimplePlotlyManager();
