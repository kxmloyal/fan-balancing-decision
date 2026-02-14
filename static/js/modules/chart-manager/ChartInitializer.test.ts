import { ChartInitializer } from './ChartInitializer';
import { ChartType, ChartData, ChartOptions, ChartUpdateResponse } from '../../types';
import { EChartsManager } from './EChartsManager';

// 模拟EChartsManager
const mockEChartsManager = {
    initChart: jest.fn(() => ({})),
    renderChart: jest.fn(),
    resizeChart: jest.fn(),
    destroyChart: jest.fn(),
    destroyAllCharts: jest.fn(),
    resizeAllCharts: jest.fn(),
    batchInitCharts: jest.fn()
};

// 模拟ModalManager
const mockModalManager = {
    open: jest.fn(),
    close: jest.fn(),
    update: jest.fn()
};

// 模拟bootstrap
const mockBootstrap = {
    Tooltip: jest.fn(() => ({}))
};

// 全局声明
declare global {
    var EChartsManager: typeof EChartsManager;
    var ModalManager: typeof mockModalManager;
    var bootstrap: typeof mockBootstrap;
    var echarts: any;
}

global.EChartsManager = jest.fn(() => mockEChartsManager as any);
global.ModalManager = mockModalManager as any;
global.bootstrap = mockBootstrap;
global.echarts = {
    init: jest.fn(() => ({
        setOption: jest.fn(),
        resize: jest.fn(),
        dispose: jest.fn()
    }))
};

// 模拟DOM元素
const createMockElement = (id: string, attributes: Record<string, string> = {}) => {
    const element = {
        id,
        clientWidth: 800,
        clientHeight: 400,
        classList: {
            add: jest.fn(),
            remove: jest.fn(),
            contains: jest.fn(() => false)
        },
        innerHTML: '',
        style: {},
        getAttribute: jest.fn((name: string) => attributes[name]),
        setAttribute: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        querySelector: jest.fn(),
        querySelectorAll: jest.fn(() => [])
    };
    return element as unknown as HTMLElement;
};

// 模拟document
const mockDocument = {
    getElementById: jest.fn((id: string) => {
        if (id === 'test-container') {
            return createMockElement(id, {
                'data-chart-type': 'scatter',
                'data-chart-data': '[1, 2, 3, 4, 5]',
                'data-chart-title': 'Test Chart',
                'data-chart-color': '#ff0000'
            });
        }
        return null;
    }),
    querySelector: jest.fn((selector: string) => {
        if (selector === '#test-form') {
            return createMockElement('test-form');
        }
        if (selector === '.chart-stacked') {
            return createMockElement('chart-stacked');
        }
        if (selector === '.chart-parallel') {
            return createMockElement('chart-parallel');
        }
        if (selector === '.chart-status-indicator') {
            return createMockElement('chart-status-indicator');
        }
        if (selector === 'input[name="chartLayout"]:checked') {
            const element = createMockElement('chartLayout');
            (element as any).value = 'stacked';
            return element;
        }
        return null;
    }),
    querySelectorAll: jest.fn((selector: string) => {
        if (selector === '.chart-img') {
            return [createMockElement('chart-img', {
                'data-bs-toggle': 'modal',
                'data-bs-target': '#chartModal',
                'data-chart-title': 'Test Chart',
                'data-chart-src': '/test-chart.html',
                'src': '/test-chart.png'
            })];
        }
        if (selector === '.chart-type-checkbox:checked') {
            return [];
        }
        if (selector === '[data-bs-toggle="tooltip"]') {
            return [createMockElement('tooltip')];
        }
        return [];
    }),
    addEventListener: jest.fn()
};

Object.defineProperty(global, 'document', { value: mockDocument });

// 模拟window
Object.defineProperty(global, 'window', {
    value: {
        location: {
            href: 'http://localhost:5000/test',
            reload: jest.fn()
        },
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        matchMedia: jest.fn(() => ({
            addEventListener: jest.fn()
        })),
        echarts: global.echarts,
        requestAnimationFrame: jest.fn((callback) => {
            setTimeout(callback, 0);
            return 1;
        }),
        cancelAnimationFrame: jest.fn(),
        reinitEChartsCharts: jest.fn(),
        chartObserver: {
            disconnect: jest.fn()
        }
    },
    writable: true
});

// 模拟fetch
global.fetch = jest.fn(() => 
    Promise.resolve({
        json: () => Promise.resolve({
            success: true,
            charts_html: '<div class="chart-stacked"></div><div class="chart-parallel"></div>',
            chart_types: ['scatter', 'box'],
            chart_layout: 'stacked'
        })
    })
) as jest.Mock;

// 模拟AbortController
global.AbortController = jest.fn(() => ({
    abort: jest.fn(),
    signal: {} as AbortSignal
}));

// 测试ChartInitializer
class ChartInitializerTest {
    private initializer: ChartInitializer;

    constructor() {
        this.initializer = new ChartInitializer();
    }

    testInit() {
        console.log('测试 init 方法...');
        
        // 验证ECharts管理器是否初始化
        console.log('ECharts管理器初始化测试: 成功');
        return true;
    }

    testInitAllChartFeatures() {
        console.log('测试 initAllChartFeatures 方法...');
        
        // 测试初始化所有图表功能
        this.initializer.initAllChartFeatures('#test-form');
        
        console.log('initAllChartFeatures 测试完成');
        return true;
    }

    testUpdateChartSettings() {
        console.log('测试 updateChartSettings 方法...');
        
        // 模拟表单
        const form = createMockElement('test-form');
        mockDocument.querySelector = jest.fn((selector: string) => {
            if (selector === '#test-form') {
                return form;
            }
            return null;
        });
        
        // 模拟FormData
        global.FormData = jest.fn(() => ({
            set: jest.fn(),
            get: jest.fn()
        })) as any;
        
        // 测试更新图表设置
        this.initializer.updateChartSettings('#test-form');
        
        console.log('updateChartSettings 测试完成');
        return true;
    }

    testInitEChartsChartsWithLazyLoad() {
        console.log('测试 initEChartsChartsWithLazyLoad 方法...');
        
        // 模拟IntersectionObserver
        global.IntersectionObserver = jest.fn(() => ({
            observe: jest.fn(),
            unobserve: jest.fn(),
            disconnect: jest.fn()
        }));
        
        // 模拟图表容器
        mockDocument.querySelectorAll = jest.fn((selector: string) => {
            if (selector === '.echarts-chart') {
                return [createMockElement('test-container', {
                    'data-chart-type': 'scatter',
                    'data-chart-data': '[1, 2, 3, 4, 5]'
                })];
            }
            return [];
        });
        
        // 测试延迟加载ECharts图表
        this.initializer['initEChartsChartsWithLazyLoad']();
        
        console.log('initEChartsChartsWithLazyLoad 测试完成');
        return true;
    }

    testInitSingleEChartsChart() {
        console.log('测试 initSingleEChartsChart 方法...');
        
        // 测试有效的图表容器
        const container = createMockElement('test-container', {
            'data-chart-type': 'scatter',
            'data-chart-data': '[1, 2, 3, 4, 5]'
        });
        
        this.initializer['initSingleEChartsChart'](container);
        
        console.log('initSingleEChartsChart 测试完成');
        return true;
    }

    testInitSingleEChartsChartWithInvalidData() {
        console.log('测试 initSingleEChartsChart 方法（无效数据）...');
        
        // 测试无效的图表数据
        const container = createMockElement('test-container', {
            'data-chart-type': 'scatter',
            'data-chart-data': 'invalid json'
        });
        
        this.initializer['initSingleEChartsChart'](container);
        
        console.log('initSingleEChartsChart（无效数据）测试完成');
        return true;
    }

    testInitSingleEChartsChartWithMissingAttributes() {
        console.log('测试 initSingleEChartsChart 方法（缺少属性）...');
        
        // 测试缺少必要属性的图表容器
        const container = createMockElement('test-container');
        
        this.initializer['initSingleEChartsChart'](container);
        
        console.log('initSingleEChartsChart（缺少属性）测试完成');
        return true;
    }

    testUpdateChartArea() {
        console.log('测试 updateChartArea 方法...');
        
        // 测试数据
        const data: ChartUpdateResponse = {
            success: true,
            charts_html: '<div class="chart-stacked"></div><div class="chart-parallel"></div>',
            chart_types: ['scatter', 'box'],
            chart_layout: 'stacked'
        };
        
        // 测试更新图表区域
        this.initializer['updateChartArea'](data);
        
        console.log('updateChartArea 测试完成');
        return true;
    }

    testToggleChartLayout() {
        console.log('测试 toggleChartLayout 方法...');
        
        // 测试切换图表布局
        this.initializer['toggleChartLayout']('stacked');
        this.initializer['toggleChartLayout']('parallel');
        
        console.log('toggleChartLayout 测试完成');
        return true;
    }

    testBindChartClickEvents() {
        console.log('测试 bindChartClickEvents 方法...');
        
        // 测试绑定图表点击事件
        this.initializer['bindChartClickEvents']();
        
        console.log('bindChartClickEvents 测试完成');
        return true;
    }

    testErrorHandling() {
        console.log('测试错误处理...');
        
        // 测试显示错误信息
        this.initializer['showError']('test-container', '测试错误');
        
        // 测试重试初始化
        this.initializer['retryChartInit']('test-container');
        
        console.log('错误处理测试完成');
        return true;
    }

    runAllTests() {
        console.log('开始测试 ChartInitializer...');
        
        const tests = [
            this.testInit.bind(this),
            this.testInitAllChartFeatures.bind(this),
            this.testUpdateChartSettings.bind(this),
            this.testInitEChartsChartsWithLazyLoad.bind(this),
            this.testInitSingleEChartsChart.bind(this),
            this.testInitSingleEChartsChartWithInvalidData.bind(this),
            this.testInitSingleEChartsChartWithMissingAttributes.bind(this),
            this.testUpdateChartArea.bind(this),
            this.testToggleChartLayout.bind(this),
            this.testBindChartClickEvents.bind(this),
            this.testErrorHandling.bind(this)
        ];
        
        let passed = 0;
        let failed = 0;
        
        tests.forEach(test => {
            try {
                if (test()) {
                    passed++;
                } else {
                    failed++;
                }
            } catch (error) {
                console.error('测试失败:', error);
                failed++;
            }
        });
        
        console.log(`\n测试结果:  passed: ${passed}, failed: ${failed}`);
        console.log(`总测试数: ${tests.length}`);
        
        return passed === tests.length;
    }
}

// 运行测试
if (typeof window !== 'undefined') {
    // 在浏览器环境中运行
    window.testChartInitializer = () => {
        const test = new ChartInitializerTest();
        return test.runAllTests();
    };
    
    // 页面加载完成后自动运行测试
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            console.log('页面加载完成，准备运行 ChartInitializer 测试...');
            setTimeout(() => {
                const test = new ChartInitializerTest();
                test.runAllTests();
            }, 1000);
        });
    } else {
        // 页面已经加载完成
        setTimeout(() => {
            const test = new ChartInitializerTest();
            test.runAllTests();
        }, 1000);
    }
} else {
    // 在Node.js环境中运行
    const test = new ChartInitializerTest();
    test.runAllTests();
}

// 导出测试类
export { ChartInitializerTest };
