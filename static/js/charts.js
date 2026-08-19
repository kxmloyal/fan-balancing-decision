// 图表初始化和管理
// 使用Plotly作为唯一图表库

// 初始化所有图表功能
function initAllChartFeatures() {
    
    try {
        // 初始化Plotly图表（延迟加载）
        initPlotlyWithLazyLoad();
        
        // 初始化响应式布局
        initResponsiveLayout();
        
    } catch (error) {
        console.error('初始化图表功能时出错:', error);
        console.error('错误详情:', error.stack);
    }
}

function initPlotlyWithLazyLoad() {
    try {
        const chartContainers = document.querySelectorAll('.plotly-chart');

        if (typeof plotlyManager === 'undefined') {
            console.error('plotlyManager 未定义，无法初始化图表');
            return;
        }

        chartContainers.forEach(container => {
            const chartId = container.getAttribute('id');
            if (chartId && typeof plotlyManager !== 'undefined') {
                const chartType = container.getAttribute('data-chart-type');
                const chartTitle = container.getAttribute('data-chart-title');
                const chartColor = container.getAttribute('data-chart-color');
                const chartData = container.getAttribute('data-chart-data');

                try {
                    const unescapedChartData = chartData.replace(/&#34;/g, '"').replace(/&quot;/g, '"').replace(/&amp;/g, '&');
                    const data = JSON.parse(unescapedChartData);
                    plotlyManager.initChart(chartId, chartType, data, {
                        title: chartTitle,
                        color: chartColor
                    });
                } catch (error) {
                    console.error(`初始化图表失败: ${chartId}`, error);
                }
            }
        });
    } catch (error) {
        console.error('初始化图表时出错:', error);
    }
}

// 初始化响应式布局
function initResponsiveLayout() {
    
    try {
        // 监听窗口大小变化
        const resizeHandler = debounce(() => {
            if (typeof plotlyManager !== 'undefined') {
                const chartContainers = document.querySelectorAll('.plotly-chart');
                chartContainers.forEach(container => {
                    const chartId = container.getAttribute('id');
                    if (chartId && container.isConnected) {
                        plotlyManager.resizeChart(chartId);
                    }
                });
            }
        }, 200);
        
        window.addEventListener('resize', resizeHandler);
        
        // 监听设备方向变化
        if (window.matchMedia) {
            const orientationHandler = debounce(() => {
                if (typeof plotlyManager !== 'undefined') {
                    const chartContainers = document.querySelectorAll('.plotly-chart');
                    chartContainers.forEach(container => {
                        const chartId = container.getAttribute('id');
                        if (chartId && container.isConnected) {
                            plotlyManager.resizeChart(chartId);
                        }
                    });
                }
            }, 200);
            
            window.matchMedia('(orientation: portrait)').addEventListener('change', orientationHandler);
        }
        
    } catch (error) {
        console.error('初始化响应式布局时出错:', error);
        console.error('错误详情:', error.stack);
    }
}

// 防抖函数
function debounce(func, wait) {
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

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 重新加载所有图表
async function reloadAllCharts() {
    
    try {
        // 重新初始化
        initPlotlyWithLazyLoad();
        
    } catch (error) {
        console.error('重新加载图表时出错:', error);
        console.error('错误详情:', error.stack);
    }
}

// 导出函数
window.initAllChartFeatures = initAllChartFeatures;
window.reloadAllCharts = reloadAllCharts;

// 页面加载完成后初始化图表功能
document.addEventListener('DOMContentLoaded', function() {
    initAllChartFeatures();
});

// 页面可见性变化时的处理
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        // 页面重新变为可见时，可以检查图表状态并进行必要的更新
        if (typeof plotlyManager !== 'undefined') {
            const chartContainers = document.querySelectorAll('.plotly-chart');
            chartContainers.forEach(container => {
                const chartId = container.getAttribute('id');
                if (chartId) {
                    plotlyManager.resizeChart(chartId);
                }
            });
        }
    }
});

// 页面卸载时清理图表资源
var _chartsCleanupResizeHandler = null;
var _skipChartCleanup = false;

document.addEventListener('click', function(e) {
    var exportLink = e.target.closest('.js-export-link');
    if (exportLink) {
        _skipChartCleanup = true;
        setTimeout(function() { _skipChartCleanup = false; }, 3000);
    }
});

window.addEventListener('beforeunload', function() {
    if (_skipChartCleanup) return;
    if (typeof plotlyManager !== 'undefined') {
        try {
            var containers = document.querySelectorAll('.plotly-chart');
            containers.forEach(function(c) {
                var id = c.getAttribute('id');
                if (id) plotlyManager.destroyChart(id);
            });
        } catch (e) {}
    }
});

window.addEventListener('pagehide', function() {
    if (_skipChartCleanup) return;
    if (typeof plotlyManager !== 'undefined') {
        try {
            var containers = document.querySelectorAll('.plotly-chart');
            containers.forEach(function(c) {
                var id = c.getAttribute('id');
                if (id) plotlyManager.destroyChart(id);
            });
        } catch (e) {}
    }
});

// 错误处理
window.addEventListener('error', function(event) {
    console.error('全局错误:', event.error);
    console.error('错误详情:', event.error.stack);
});

