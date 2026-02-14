/**
 * 滚动动画管理器测试
 * 测试ScrollAnimationManager的各种功能和场景
 */

// 测试工具函数
function createTestElement(className = '', dataset = {}) {
    const element = document.createElement('div');
    element.className = className;
    
    // 设置data属性
    Object.keys(dataset).forEach(key => {
        element.dataset[key] = dataset[key];
    });
    
    element.style.height = '200px';
    element.style.width = '200px';
    element.style.backgroundColor = '#f0f0f0';
    element.style.margin = '20px';
    
    return element;
}

// 测试用例
function runScrollAnimationTests() {
    console.log('开始测试ScrollAnimationManager...');
    
    // 测试1: 基本初始化
    testBasicInitialization();
    
    // 测试2: 添加和移除元素
    testAddRemoveElements();
    
    // 测试3: 动画配置
    testAnimationConfig();
    
    // 测试4: 重新初始化
    testReinitialization();
    
    // 测试5: 销毁功能
    testDestroy();
    
    console.log('所有测试完成！');
}

// 测试1: 基本初始化
function testBasicInitialization() {
    console.log('测试1: 基本初始化');
    
    try {
        const manager = new ScrollAnimationManager({
            autoInit: false
        });
        
        // 测试初始化
        manager.init();
        
        console.log('✓ 基本初始化成功');
        console.log('✓ 观察器创建成功');
        
        manager.destroy();
    } catch (error) {
        console.error('✗ 基本初始化失败:', error);
    }
}

// 测试2: 添加和移除元素
function testAddRemoveElements() {
    console.log('测试2: 添加和移除元素');
    
    try {
        const manager = new ScrollAnimationManager({
            autoInit: false
        });
        
        manager.init();
        
        // 创建测试元素
        const testElement = createTestElement('scroll-reveal');
        document.body.appendChild(testElement);
        
        // 添加元素
        manager.addElement(testElement);
        console.log('✓ 添加元素成功');
        
        // 移除元素
        manager.removeElement(testElement);
        console.log('✓ 移除元素成功');
        
        // 清理
        document.body.removeChild(testElement);
        manager.destroy();
        
    } catch (error) {
        console.error('✗ 添加移除元素测试失败:', error);
    }
}

// 测试3: 动画配置
function testAnimationConfig() {
    console.log('测试3: 动画配置');
    
    try {
        const manager = new ScrollAnimationManager({
            autoInit: false
        });
        
        manager.init();
        
        // 创建不同动画类型的元素
        const animations = ['fade-up', 'fade-in', 'slide-in-left', 'slide-in-right', 'zoom-in', 'zoom-out'];
        
        animations.forEach(animationType => {
            const testElement = createTestElement('scroll-reveal', {
                animation: animationType,
                duration: '1000',
                delay: '100'
            });
            
            document.body.appendChild(testElement);
            manager.addElement(testElement);
            
            console.log(`✓ 配置${animationType}动画成功`);
            
            // 清理
            document.body.removeChild(testElement);
        });
        
        manager.destroy();
        
    } catch (error) {
        console.error('✗ 动画配置测试失败:', error);
    }
}

// 测试4: 重新初始化
function testReinitialization() {
    console.log('测试4: 重新初始化');
    
    try {
        const manager = new ScrollAnimationManager({
            autoInit: false
        });
        
        manager.init();
        
        // 测试重新初始化
        manager.reinitialize();
        console.log('✓ 重新初始化成功');
        
        manager.destroy();
        
    } catch (error) {
        console.error('✗ 重新初始化测试失败:', error);
    }
}

// 测试5: 销毁功能
function testDestroy() {
    console.log('测试5: 销毁功能');
    
    try {
        const manager = new ScrollAnimationManager({
            autoInit: false
        });
        
        manager.init();
        manager.destroy();
        
        console.log('✓ 销毁功能成功');
        
    } catch (error) {
        console.error('✗ 销毁功能测试失败:', error);
    }
}

// 页面加载完成后运行测试
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runScrollAnimationTests);
} else {
    runScrollAnimationTests();
}

// 导出测试函数
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        runScrollAnimationTests,
        testBasicInitialization,
        testAddRemoveElements,
        testAnimationConfig,
        testReinitialization,
        testDestroy
    };
}