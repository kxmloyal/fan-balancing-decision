// 加载状态管理器
class LoadingManager {
    constructor() {
        this.loadingElements = {};
        this.activeLoadings = new Set();
        this.defaultOptions = {
            text: '加载中...',
            type: 'spinner', // spinner, dots, bar
            color: 'primary',
            size: 'medium', // small, medium, large
            overlay: false,
            duration: 0, // 自动隐藏时间（毫秒），0表示不自动隐藏
            onStart: null,
            onComplete: null
        };
    }

    // 显示加载状态
    show(id, options = {}) {
        const mergedOptions = { ...this.defaultOptions, ...options };
        this.activeLoadings.add(id);

        // 如果已经存在该ID的加载元素，先移除
        if (this.loadingElements[id]) {
            this.hide(id);
        }

        // 创建加载元素
        const loadingElement = this.createLoadingElement(id, mergedOptions);
        this.loadingElements[id] = loadingElement;

        // 添加到页面
        if (mergedOptions.overlay) {
            document.body.appendChild(loadingElement);
        } else {
            const target = mergedOptions.target;
            if (target && target.nodeType === Node.ELEMENT_NODE) {
                target.appendChild(loadingElement);
            } else {
                document.body.appendChild(loadingElement);
            }
        }

        // 触发开始回调
        if (typeof mergedOptions.onStart === 'function') {
            mergedOptions.onStart();
        }

        // 设置自动隐藏
        if (mergedOptions.duration > 0) {
            setTimeout(() => {
                this.hide(id);
            }, mergedOptions.duration);
        }

        return loadingElement;
    }

    // 隐藏加载状态
    hide(id) {
        if (this.loadingElements[id]) {
            const loadingElement = this.loadingElements[id];
            
            // 添加淡出动画
            loadingElement.style.opacity = '0';
            loadingElement.style.transition = 'opacity 0.3s ease';

            // 动画结束后移除
            setTimeout(() => {
                if (loadingElement.parentNode) {
                    loadingElement.parentNode.removeChild(loadingElement);
                }
                delete this.loadingElements[id];
                this.activeLoadings.delete(id);
            }, 300);

            // 触发完成回调
            const options = loadingElement._options;
            if (options && typeof options.onComplete === 'function') {
                options.onComplete();
            }
        }
    }

    // 隐藏所有加载状态
    hideAll() {
        const ids = [...this.activeLoadings];
        ids.forEach(id => this.hide(id));
    }

    // 创建加载元素
    createLoadingElement(id, options) {
        const container = document.createElement('div');
        container.id = `loading-${id}`;
        container.className = 'loading-container';
        container._options = options;

        // 基础样式
        const baseStyles = {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: options.overlay ? 'fixed' : 'relative',
            zIndex: options.overlay ? 9999 : 1000,
            opacity: '1',
            transition: 'opacity 0.3s ease'
        };

        // 叠加层样式
        if (options.overlay) {
            Object.assign(baseStyles, {
                top: '0',
                left: '0',
                width: '100%',
                height: '100%',
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(2px)'
            });
        } else {
            Object.assign(baseStyles, {
                padding: '20px',
                borderRadius: '8px',
                backgroundColor: options.overlay ? 'rgba(255, 255, 255, 0.9)' : 'transparent'
            });
        }

        // 应用样式
        Object.assign(container.style, baseStyles);

        // 创建加载内容
        const content = document.createElement('div');
        content.className = 'loading-content';
        content.style.display = 'flex';
        content.style.alignItems = 'center';
        content.style.gap = '12px';

        // 创建加载动画
        const loader = this.createLoader(options.type, options.color, options.size);
        content.appendChild(loader);

        // 创建加载文本
        if (options.text) {
            const textElement = document.createElement('span');
            textElement.className = 'loading-text';
            textElement.textContent = options.text;
            textElement.style.fontSize = this.getSizeForText(options.size);
            textElement.style.color = this.getColorValue(options.color);
            textElement.style.fontWeight = '500';
            content.appendChild(textElement);
        }

        container.appendChild(content);
        return container;
    }

    // 创建加载动画
    createLoader(type, color, size) {
        const loader = document.createElement('div');
        loader.className = `loading-loader loading-${type}`;

        switch (type) {
            case 'spinner':
                this.createSpinnerLoader(loader, color, size);
                break;
            case 'dots':
                this.createDotsLoader(loader, color, size);
                break;
            case 'bar':
                this.createBarLoader(loader, color, size);
                break;
            default:
                this.createSpinnerLoader(loader, color, size);
        }

        return loader;
    }

    // 创建 spinner 加载动画
    createSpinnerLoader(loader, color, size) {
        const sizeValue = this.getSizeValue(size);
        const colorValue = this.getColorValue(color);

        loader.style.cssText = `
            width: ${sizeValue}px;
            height: ${sizeValue}px;
            border: 3px solid rgba(0, 0, 0, 0.1);
            border-radius: 50%;
            border-top-color: ${colorValue};
            animation: loadingSpin 1s ease-in-out infinite;
        `;
    }

    // 创建 dots 加载动画
    createDotsLoader(loader, color, size) {
        const sizeValue = this.getSizeValue(size);
        const dotSize = sizeValue * 0.3;
        const colorValue = this.getColorValue(color);

        loader.style.cssText = `
            display: flex;
            gap: ${dotSize * 0.5}px;
        `;

        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.style.cssText = `
                width: ${dotSize}px;
                height: ${dotSize}px;
                border-radius: 50%;
                background-color: ${colorValue};
                animation: loadingBounce 1.4s ease-in-out infinite both;
                animation-delay: ${i * 0.2}s;
            `;
            loader.appendChild(dot);
        }
    }

    // 创建 bar 加载动画
    createBarLoader(loader, color, size) {
        const sizeValue = this.getSizeValue(size);
        const barHeight = sizeValue * 0.2;
        const colorValue = this.getColorValue(color);

        loader.style.cssText = `
            width: ${sizeValue * 2}px;
            height: ${barHeight}px;
            background-color: rgba(0, 0, 0, 0.1);
            border-radius: ${barHeight / 2}px;
            overflow: hidden;
        `;

        const bar = document.createElement('div');
        bar.style.cssText = `
            width: 30%;
            height: 100%;
            background-color: ${colorValue};
            border-radius: ${barHeight / 2}px;
            animation: loadingBar 1.5s ease-in-out infinite;
        `;
        loader.appendChild(bar);
    }

    // 获取尺寸值
    getSizeValue(size) {
        switch (size) {
            case 'small':
                return 20;
            case 'large':
                return 40;
            case 'medium':
            default:
                return 30;
        }
    }

    // 获取文本尺寸
    getSizeForText(size) {
        switch (size) {
            case 'small':
                return '0.875rem';
            case 'large':
                return '1.125rem';
            case 'medium':
            default:
                return '1rem';
        }
    }

    // 获取颜色值
    getColorValue(color) {
        const colorMap = {
            primary: '#3498db',
            success: '#2ecc71',
            warning: '#f39c12',
            danger: '#e74c3c',
            info: '#1abc9c',
            dark: '#34495e',
            light: '#ecf0f1'
        };

        return colorMap[color] || color;
    }

    // 检查是否有加载状态活跃
    isLoading(id) {
        return this.activeLoadings.has(id);
    }

    // 获取活跃的加载状态数量
    getActiveCount() {
        return this.activeLoadings.size;
    }

    // 创建并显示页面级加载
    showPageLoading(options = {}) {
        return this.show('page', {
            overlay: true,
            size: 'large',
            text: '处理中，请稍候...',
            ...options
        });
    }

    // 隐藏页面级加载
    hidePageLoading() {
        this.hide('page');
    }

    // 创建并显示上传加载
    showUploadLoading(options = {}) {
        return this.show('upload', {
            text: '上传中...',
            type: 'bar',
            ...options
        });
    }

    // 隐藏上传加载
    hideUploadLoading() {
        this.hide('upload');
    }

    // 创建并显示图表加载
    showChartLoading(options = {}) {
        return this.show('chart', {
            text: '图表生成中...',
            ...options
        });
    }

    // 隐藏图表加载
    hideChartLoading() {
        this.hide('chart');
    }

    // 创建并显示数据加载
    showDataLoading(options = {}) {
        return this.show('data', {
            text: '数据处理中...',
            ...options
        });
    }

    // 隐藏数据加载
    hideDataLoading() {
        this.hide('data');
    }
}

// 初始化加载管理器
const loadingManager = new LoadingManager();

// 添加加载动画样式
const loadingStyles = `
    /* 加载动画样式 */
    @keyframes loadingSpin {
        to { transform: rotate(360deg); }
    }

    @keyframes loadingBounce {
        0%, 80%, 100% {
            transform: scale(0);
        } 40% {
            transform: scale(1);
        }
    }

    @keyframes loadingBar {
        0% {
            transform: translateX(-100%);
        }
        100% {
            transform: translateX(333.333%);
        }
    }

    .loading-container {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .loading-content {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .loading-spinner {
        animation: loadingSpin 1s ease-in-out infinite;
    }

    .loading-dots > div {
        animation: loadingBounce 1.4s ease-in-out infinite both;
    }

    .loading-dots > div:nth-child(1) {
        animation-delay: -0.32s;
    }

    .loading-dots > div:nth-child(2) {
        animation-delay: -0.16s;
    }

    .loading-bar > div {
        animation: loadingBar 1.5s ease-in-out infinite;
    }

    /* 响应式调整 */
    @media (max-width: 768px) {
        .loading-content {
            flex-direction: column;
            text-align: center;
            gap: 8px;
        }
    }
`;

// 添加样式到页面
const styleElement = document.createElement('style');
styleElement.textContent = loadingStyles;
document.head.appendChild(styleElement);

// 导出加载管理器
window.loadingManager = loadingManager;