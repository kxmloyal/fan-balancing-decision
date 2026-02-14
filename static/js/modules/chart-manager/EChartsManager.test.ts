import { EChartsManager } from './EChartsManager';
import { ChartType, ChartData, ChartOptions } from '../../types';

// 模拟echarts
const mockEcharts = {
    init: jest.fn(() => ({
        setOption: jest.fn(),
        getOption: jest.fn(() => ({})),
        resize: jest.fn(),
        dispose: jest.fn()
    })),
    graphic: {
        LinearGradient: jest.fn(() => 'mock-gradient'),
        RadialGradient: jest.fn(() => 'mock-radial-gradient')
    }
};

// 全局声明
declare global {
    var echarts: typeof mockEcharts;
}

global.echarts = mockEcharts;

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
        setAttribute: jest.fn()
    };
    return element as unknown as HTMLElement;
};

// 模拟document
const mockDocument = {
    getElementById: jest.fn((id: string) => {
        if (id === 'test-container') {
            return createMockElement(id);
        }
        return null;
    }),
    querySelector: jest.fn(),
    querySelectorAll: jest.fn(() => [])
};

Object.defineProperty(global, 'document', { value: mockDocument });

// 模拟window
Object.defineProperty(global, 'window', {
    value: {
        devicePixelRatio: 1,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        matchMedia: jest.fn(() => ({
            addEventListener: jest.fn()
        })),
        echarts: mockEcharts
    },
    writable: true
});

// 测试EChartsManager
class EChartsManagerTest {
    private manager: EChartsManager;

    constructor() {
        this.manager = new EChartsManager();
    }

    testInitChart() {
        console.log('测试 initChart 方法...');
        
        const container = createMockElement('test-container');
        mockDocument.getElementById = jest.fn(() => container);
        
        const data: ChartData = [1, 2, 3, 4, 5];
        const options: ChartOptions = {
            title: 'Test Chart',
            color: '#ff0000'
        };

        const result = this.manager.initChart('test-container', 'scatter', data, options);
        
        console.log('initChart 测试结果:', result ? '成功' : '失败');
        return result !== null;
    }

    testRenderChart() {
        console.log('测试 renderChart 方法...');
        
        const container = createMockElement('test-container');
        mockDocument.getElementById = jest.fn(() => container);
        
        const data: ChartData = [1, 2, 3, 4, 5];
        const options: ChartOptions = {
            title: 'Test Chart'
        };

        // 先初始化图表
        this.manager.initChart('test-container', 'scatter', data, options);
        
        // 测试渲染
        this.manager.renderChart('test-container', 'scatter', data, options);
        
        console.log('renderChart 测试完成');
        return true;
    }

    testResizeChart() {
        console.log('测试 resizeChart 方法...');
        
        const container = createMockElement('test-container');
        mockDocument.getElementById = jest.fn(() => container);
        
        const data: ChartData = [1, 2, 3, 4, 5];
        
        // 先初始化图表
        this.manager.initChart('test-container', 'scatter', data);
        
        // 测试调整大小
        this.manager.resizeChart('test-container');
        
        console.log('resizeChart 测试完成');
        return true;
    }

    testDestroyChart() {
        console.log('测试 destroyChart 方法...');
        
        const container = createMockElement('test-container');
        mockDocument.getElementById = jest.fn(() => container);
        
        const data: ChartData = [1, 2, 3, 4, 5];
        
        // 先初始化图表
        this.manager.initChart('test-container', 'scatter', data);
        
        // 测试销毁
        this.manager.destroyChart('test-container');
        
        console.log('destroyChart 测试完成');
        return true;
    }

    testBatchInitCharts() {
        console.log('测试 batchInitCharts 方法...');
        
        const container1 = createMockElement('container1');
        const container2 = createMockElement('container2');
        
        mockDocument.getElementById = jest.fn((id: string) => {
            if (id === 'container1') return container1;
            if (id === 'container2') return container2;
            return null;
        });
        
        const chartConfigs = [
            {
                containerId: 'container1',
                chartType: 'scatter' as ChartType,
                data: [1, 2, 3] as ChartData
            },
            {
                containerId: 'container2',
                chartType: 'box' as ChartType,
                data: { test: [1, 2, 3, 4, 5] } as ChartData
            }
        ];
        
        this.manager.batchInitCharts(chartConfigs);
        
        console.log('batchInitCharts 测试完成');
        return true;
    }

    testDataConversion() {
        console.log('测试数据转换方法...');
        
        // 测试数据
        const testData = {
            'A': [1, 2, 3, 4, 5],
            'B': [2, 3, 4, 5, 6]
        };
        
        // 测试各种图表类型的数据转换
        const manager = new EChartsManager();
        
        // 这里我们无法直接测试私有方法，但可以通过测试公共方法间接测试
        const container = createMockElement('test-container');
        mockDocument.getElementById = jest.fn(() => container);
        
        // 测试箱线图数据转换
        manager.initChart('test-container', 'box', testData);
        
        // 测试散点图数据转换
        manager.initChart('test-container', 'scatter', testData);
        
        // 测试趋势图数据转换
        manager.initChart('test-container', 'trend', testData);
        
        console.log('数据转换测试完成');
        return true;
    }

    testErrorHandling() {
        console.log('测试错误处理...');
        
        // 测试不存在的容器
        const result1 = this.manager.initChart('non-existent', 'scatter', [1, 2, 3]);
        console.log('不存在的容器测试:', result1 === null ? '成功' : '失败');
        
        // 测试无效的图表类型
        const container = createMockElement('test-container');
        mockDocument.getElementById = jest.fn(() => container);
        
        const result2 = this.manager.initChart('test-container', 'invalid-type' as ChartType, [1, 2, 3]);
        console.log('无效的图表类型测试:', result2 === null ? '成功' : '失败');
        
        // 测试空数据
        const result3 = this.manager.initChart('test-container', 'scatter', []);
        console.log('空数据测试:', result3 === null ? '成功' : '失败');
        
        console.log('错误处理测试完成');
        return true;
    }

    runAllTests() {
        console.log('开始测试 EChartsManager...');
        
        const tests = [
            this.testInitChart.bind(this),
            this.testRenderChart.bind(this),
            this.testResizeChart.bind(this),
            this.testDestroyChart.bind(this),
            this.testBatchInitCharts.bind(this),
            this.testDataConversion.bind(this),
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
    window.testEChartsManager = () => {
        const test = new EChartsManagerTest();
        return test.runAllTests();
    };
    
    // 页面加载完成后自动运行测试
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            console.log('页面加载完成，准备运行 EChartsManager 测试...');
            setTimeout(() => {
                const test = new EChartsManagerTest();
                test.runAllTests();
            }, 1000);
        });
    } else {
        // 页面已经加载完成
        setTimeout(() => {
            const test = new EChartsManagerTest();
            test.runAllTests();
        }, 1000);
    }
} else {
    // 在Node.js环境中运行
    const test = new EChartsManagerTest();
    test.runAllTests();
}

// 导出测试类
export { EChartsManagerTest };
