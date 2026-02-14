// 主图表入口文件
import { initAllChartFeatures, fixChartDisplay, retryChartInit, retryChartImageLoad } from './modules/chart-manager';
import { EChartsManager } from './modules/chart-manager';

// 导出全局函数
declare global {
    interface Window {
        initAllChartFeatures: typeof initAllChartFeatures;
        fixChartDisplay: typeof fixChartDisplay;
        retryChartInit: typeof retryChartInit;
        retryChartImageLoad: typeof retryChartImageLoad;
        EChartsManager: typeof EChartsManager;
        echartsManager: InstanceType<typeof EChartsManager>;
        chartObserver: IntersectionObserver;
        reinitEChartsCharts: () => void;
    }
}

// 将函数挂载到全局对象上
if (typeof window !== 'undefined') {
    window.initAllChartFeatures = initAllChartFeatures;
    window.fixChartDisplay = fixChartDisplay;
    window.retryChartInit = retryChartInit;
    window.retryChartImageLoad = retryChartImageLoad;
    window.EChartsManager = EChartsManager;
}

// 重新初始化ECharts图表的全局函数
if (typeof window !== 'undefined') {
    window.reinitEChartsCharts = function() {
        console.log('开始重新初始化ECharts图表');
        try {
            // 查找所有需要初始化的ECharts图表容器
            const chartContainers = document.querySelectorAll('.echarts-chart');
            console.log(`找到 ${chartContainers.length} 个ECharts图表容器`);
            
            // 为每个容器重新初始化图表
            chartContainers.forEach(container => {
                const containerId = container.id;
                const chartType = container.getAttribute('data-chart-type');
                const chartDataAttr = container.getAttribute('data-chart-data');
                const chartTitle = container.getAttribute('data-chart-title');
                const chartColor = container.getAttribute('data-chart-color');
                
                if (chartType && chartDataAttr) {
                    try {
                        // 解析数据
                        let data = [];
                        try {
                            data = JSON.parse(chartDataAttr);
                        } catch (error) {
                            console.error('解析图表数据失败:', error);
                        }
                        
                        const options = {
                            title: chartTitle || `${chartType}图表`,
                            color: chartColor || '#1f77b4'
                        };
                        
                        // 使用ECharts管理器初始化图表
                        if (window.echartsManager) {
                            window.echartsManager.initChart(
                                containerId,
                                chartType as any,
                                data,
                                options
                            );
                        }
                    } catch (error) {
                        console.error(`重新初始化图表 ${containerId} 时出错:`, error);
                    }
                }
            });
            console.log('ECharts图表重新初始化完成');
        } catch (error) {
            console.error('执行重新初始化ECharts图表时出错:', error);
        }
    };
}

export {
    initAllChartFeatures,
    fixChartDisplay,
    retryChartInit,
    retryChartImageLoad,
    EChartsManager
};

export default {
    initAllChartFeatures,
    fixChartDisplay,
    retryChartInit,
    retryChartImageLoad,
    EChartsManager
};
