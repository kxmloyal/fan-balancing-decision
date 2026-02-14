/**
 * 滚动触发动画管理器
 * 解决.scroll-reveal类元素在页面加载时无法正确显示的问题
 * 支持多种动画类型和配置选项
 */
class ScrollAnimationManager {
    constructor(options = {}) {
        this.defaultOptions = {
            // 动画触发阈值（元素可见比例）
            threshold: 0.1,
            // 根元素边距
            rootMargin: '0px 0px -50px 0px',
            // 默认动画类型
            defaultAnimation: 'fade-up',
            // 默认动画持续时间
            defaultDuration: 800,
            // 默认延迟时间
            defaultDelay: 0,
            // 是否在页面加载时自动初始化
            autoInit: true,
            // 是否在窗口大小改变时重新初始化
            watchResize: true,
            // 是否在内容加载后重新初始化
            watchContent: true
        };
        
        this.options = { ...this.defaultOptions, ...options };
        this.observer = null;
        this.elements = new Map();
        this.resizeTimeout = null;
        
        if (this.options.autoInit) {
            this.init();
        }
    }
    
    /**
     * 初始化滚动动画管理器
     */
    init() {
        // 确保DOM已经加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }
    
    /**
     * 实际初始化逻辑
     */
    initialize() {
        // 创建Intersection Observer实例
        this.createObserver();
        
        // 观察所有带有.scroll-reveal类的元素
        this.observeElements();
        
        // 监听窗口大小改变事件
        if (this.options.watchResize) {
            this.setupResizeListener();
        }
        
        // 监听内容加载事件
        if (this.options.watchContent) {
            this.setupContentListener();
        }
        
        console.log('ScrollAnimationManager 初始化完成');
    }
    
    /**
     * 创建Intersection Observer实例
     */
    createObserver() {
        const observerOptions = {
            root: null,
            rootMargin: this.options.rootMargin,
            threshold: this.options.threshold
        };
        
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.handleIntersection(entry.target);
                }
            });
        }, observerOptions);
    }
    
    /**
     * 观察所有带有.scroll-reveal类的元素
     */
    observeElements() {
        const elements = document.querySelectorAll('.scroll-reveal');
        
        elements.forEach(element => {
            // 跳过已经处理过的元素
            if (this.elements.has(element)) {
                return;
            }
            
            // 获取元素的动画配置
            const animationConfig = this.getElementConfig(element);
            this.elements.set(element, animationConfig);
            
            // 初始化元素状态
            this.initializeElement(element, animationConfig);
            
            // 开始观察元素
            this.observer.observe(element);
        });
        
        console.log(`已观察 ${elements.length} 个元素`);
    }
    
    /**
     * 获取元素的动画配置
     * @param {HTMLElement} element - DOM元素
     * @returns {Object} 动画配置
     */
    getElementConfig(element) {
        // 从data属性获取配置
        const animationType = element.dataset.animation || this.options.defaultAnimation;
        const duration = parseInt(element.dataset.duration || this.options.defaultDuration);
        const delay = parseInt(element.dataset.delay || this.options.defaultDelay);
        const once = element.dataset.once !== 'false'; // 默认只触发一次
        
        return {
            type: animationType,
            duration,
            delay,
            once
        };
    }
    
    /**
     * 初始化元素状态
     * @param {HTMLElement} element - DOM元素
     * @param {Object} config - 动画配置
     */
    initializeElement(element, config) {
        // 移除旧的active类
        element.classList.remove('active');
        
        // 根据动画类型设置初始状态
        switch (config.type) {
            case 'fade-up':
                element.style.opacity = '0';
                element.style.transform = 'translateY(30px)';
                break;
            case 'fade-in':
                element.style.opacity = '0';
                break;
            case 'slide-in-left':
                element.style.opacity = '0';
                element.style.transform = 'translateX(-30px)';
                break;
            case 'slide-in-right':
                element.style.opacity = '0';
                element.style.transform = 'translateX(30px)';
                break;
            case 'zoom-in':
                element.style.opacity = '0';
                element.style.transform = 'scale(0.9)';
                break;
            case 'zoom-out':
                element.style.opacity = '0';
                element.style.transform = 'scale(1.1)';
                break;
            default:
                element.style.opacity = '0';
                element.style.transform = 'translateY(30px)';
        }
        
        // 设置过渡效果
        element.style.transition = `all ${config.duration}ms ease ${config.delay}ms`;
    }
    
    /**
     * 处理元素交叉事件（进入视口）
     * @param {HTMLElement} element - DOM元素
     */
    handleIntersection(element) {
        const config = this.elements.get(element);
        if (!config) return;
        
        // 添加active类
        element.classList.add('active');
        
        // 触发动画
        this.triggerAnimation(element, config);
        
        // 如果只触发一次，则停止观察
        if (config.once) {
            this.observer.unobserve(element);
        }
    }
    
    /**
     * 触发元素动画
     * @param {HTMLElement} element - DOM元素
     * @param {Object} config - 动画配置
     */
    triggerAnimation(element, config) {
        // 根据动画类型设置最终状态
        switch (config.type) {
            case 'fade-up':
            case 'fade-in':
            case 'slide-in-left':
            case 'slide-in-right':
            case 'zoom-in':
            case 'zoom-out':
                element.style.opacity = '1';
                element.style.transform = 'translateY(0) translateX(0) scale(1)';
                break;
            default:
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
        }
        
        // 触发自定义事件
        element.dispatchEvent(new CustomEvent('scrollAnimation:triggered', {
            detail: { animationType: config.type, element }
        }));
    }
    
    /**
     * 设置窗口大小改变监听器
     */
    setupResizeListener() {
        window.addEventListener('resize', () => {
            // 防抖处理
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = setTimeout(() => {
                this.reinitialize();
            }, 200);
        });
    }
    
    /**
     * 设置内容加载监听器
     */
    setupContentListener() {
        // 监听DOM变化
        const observer = new MutationObserver(() => {
            this.reinitialize();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    /**
     * 重新初始化
     */
    reinitialize() {
        // 停止观察所有元素
        this.elements.forEach((_, element) => {
            this.observer.unobserve(element);
        });
        
        // 清空元素列表
        this.elements.clear();
        
        // 重新观察元素
        this.observeElements();
        
        console.log('ScrollAnimationManager 重新初始化完成');
    }
    
    /**
     * 添加单个元素
     * @param {HTMLElement} element - DOM元素
     * @param {Object} options - 可选配置
     */
    addElement(element, options = {}) {
        // 确保元素有scroll-reveal类
        if (!element.classList.contains('scroll-reveal')) {
            element.classList.add('scroll-reveal');
        }
        
        // 合并配置
        const config = { ...this.getElementConfig(element), ...options };
        this.elements.set(element, config);
        
        // 初始化元素
        this.initializeElement(element, config);
        
        // 开始观察
        this.observer.observe(element);
        
        return this;
    }
    
    /**
     * 移除单个元素
     * @param {HTMLElement} element - DOM元素
     */
    removeElement(element) {
        this.observer.unobserve(element);
        this.elements.delete(element);
        return this;
    }
    
    /**
     * 销毁管理器
     */
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
        
        clearTimeout(this.resizeTimeout);
        this.elements.clear();
        
        console.log('ScrollAnimationManager 已销毁');
    }
}

// 导出全局实例
if (typeof window !== 'undefined') {
    window.ScrollAnimationManager = ScrollAnimationManager;
    
    // 创建默认实例
    window.scrollAnimationManager = new ScrollAnimationManager({
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px',
        autoInit: true,
        watchResize: true,
        watchContent: true
    });
}

// 导出模块已通过全局变量实现
// window.ScrollAnimationManager = ScrollAnimationManager;