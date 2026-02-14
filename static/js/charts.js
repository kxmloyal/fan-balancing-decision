// 图表初始化和管理
// 使用Plotly替代ECharts

// 初始化所有图表功能
function initAllChartFeatures() {
    console.log('开始初始化图表功能');
    
    try {
        // 初始化Plotly图表（延迟加载）
        initPlotlyChartsWithLazyLoad();
        
        // 初始化响应式布局
        initResponsiveLayout();
        
        console.log('图表功能初始化完成');
    } catch (error) {
        console.error('初始化图表功能时出错:', error);
        console.error('错误详情:', error.stack);
    }
}

// 延迟加载Plotly图表
function initPlotlyChartsWithLazyLoad() {
    console.log('开始延迟加载Plotly图表');
    
    try {
        // 检查是否支持IntersectionObserver
        if ('IntersectionObserver' in window) {
            const chartContainers = document.querySelectorAll('.plotly-chart');
            console.log(`找到 ${chartContainers.length} 个图表容器`);
            
            const observer = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        // 图表容器进入视口，初始化图表
                        const chartId = entry.target.getAttribute('id');
                        if (chartId && typeof plotlyManager !== 'undefined') {
                            const chartType = entry.target.getAttribute('data-chart-type');
                            const chartTitle = entry.target.getAttribute('data-chart-title');
                            const chartColor = entry.target.getAttribute('data-chart-color');
                            const chartData = entry.target.getAttribute('data-chart-data');
                            
                            try {
                                // Unescape HTML entities before parsing JSON
                                const unescapedChartData = chartData.replace(/&quot;/g, '"');
                                const data = JSON.parse(unescapedChartData);
                                plotlyManager.initChart(chartId, chartType, data, {
                                    title: chartTitle,
                                    color: chartColor
                                });
                            } catch (error) {
                                console.error(`解析图表数据失败: ${chartId}`, error);
                                console.error(`原始数据: ${chartData}`);
                            }
                        }
                        // 停止观察该容器
                        observer.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '200px 0px' // 提前200px开始加载
            });
            
            // 观察所有图表容器
            chartContainers.forEach(container => {
                observer.observe(container);
                console.log(`开始观察图表容器: ${container.id}`);
            });
        } else {
            // 不支持IntersectionObserver时，直接初始化所有图表
            console.warn('浏览器不支持IntersectionObserver，直接初始化所有图表');
            document.querySelectorAll('.plotly-chart').forEach(container => {
                const chartId = container.getAttribute('id');
                if (chartId && typeof plotlyManager !== 'undefined') {
                    const chartType = container.getAttribute('data-chart-type');
                    const chartTitle = container.getAttribute('data-chart-title');
                    const chartColor = container.getAttribute('data-chart-color');
                    const chartData = container.getAttribute('data-chart-data');
                    
                    try {
                        // Unescape HTML entities before parsing JSON
                        const unescapedChartData = chartData.replace(/&quot;/g, '"');
                        const data = JSON.parse(unescapedChartData);
                        plotlyManager.initChart(chartId, chartType, data, {
                            title: chartTitle,
                            color: chartColor
                        });
                    } catch (error) {
                        console.error(`解析图表数据失败: ${chartId}`, error);
                        console.error(`原始数据: ${chartData}`);
                    }
                }
            });
        }
    } catch (error) {
        console.error('延迟加载Plotly图表时出错:', error);
        console.error('错误详情:', error.stack);
    }
}

// 初始化响应式布局
function initResponsiveLayout() {
    console.log('开始初始化响应式布局');
    
    try {
        // 监听窗口大小变化
        const resizeHandler = debounce(() => {
            console.log('窗口大小变化，调整图表布局');
            // 调整所有图表大小
            if (typeof plotlyManager !== 'undefined') {
                // 触发plotlyManager的resize功能
                const chartContainers = document.querySelectorAll('.plotly-chart');
                chartContainers.forEach(container => {
                    const chartId = container.getAttribute('id');
                    if (chartId) {
                        plotlyManager.resizeChart(chartId);
                    }
                });
            }
        }, 200);
        
        window.addEventListener('resize', resizeHandler);
        
        // 监听设备方向变化
        if (window.matchMedia) {
            const orientationHandler = debounce(() => {
                console.log('设备方向变化，调整图表布局');
                // 调整所有图表大小
                if (typeof plotlyManager !== 'undefined') {
                    const chartContainers = document.querySelectorAll('.plotly-chart');
                    chartContainers.forEach(container => {
                        const chartId = container.getAttribute('id');
                        if (chartId) {
                            plotlyManager.resizeChart(chartId);
                        }
                    });
                }
            }, 200);
            
            window.matchMedia('(orientation: portrait)').addEventListener('change', orientationHandler);
        }
        
        console.log('响应式布局初始化完成');
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
    console.log('开始重新加载所有图表');
    
    try {
        // 重新初始化
        initPlotlyChartsWithLazyLoad();
        
        console.log('图表重新加载完成');
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
    console.log('DOM加载完成，初始化图表功能');
    initAllChartFeatures();
});

// 页面可见性变化时的处理
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        console.log('页面变为可见，检查图表状态');
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

// 错误处理
window.addEventListener('error', function(event) {
    console.error('全局错误:', event.error);
    console.error('错误详情:', event.error.stack);
});

console.log('charts.js 加载完成');
