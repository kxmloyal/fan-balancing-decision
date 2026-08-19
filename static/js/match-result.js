// 页面加载完成后初始化图表功能
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有图表功能
    if (typeof initAllChartFeatures === 'function') {
        initAllChartFeatures();
    } else {
        console.error('initAllChartFeatures 函数未定义');
    }
});
