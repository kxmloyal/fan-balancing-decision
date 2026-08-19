// 前端分析数据收集脚本

class FrontendAnalytics {
    constructor() {
        this.analyticsData = {
            performance: {},
            userInteractions: [],
            errors: [],
            browser: {},
            timestamp: new Date().toISOString()
        };
        this.init();
    }

    init() {
        this.collectBrowserInfo();
        this.collectPerformanceData();
        this.setupErrorListeners();
        this.setupUserInteractionListeners();
        this.setupPageUnloadListener();
    }

    // 收集浏览器信息
    collectBrowserInfo() {
        this.analyticsData.browser = {
            userAgent: navigator.userAgent,
            browserName: this.getBrowserName(),
            browserVersion: this.getBrowserVersion(),
            platform: navigator.platform,
            language: navigator.language,
            screenWidth: screen.width,
            screenHeight: screen.height,
            isMobile: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
        };
    }

    // 获取浏览器名称
    getBrowserName() {
        const userAgent = navigator.userAgent;
        if (userAgent.includes('Firefox')) return 'Firefox';
        if (userAgent.includes('Chrome')) return 'Chrome';
        if (userAgent.includes('Safari')) return 'Safari';
        if (userAgent.includes('Edge')) return 'Edge';
        if (userAgent.includes('MSIE') || userAgent.includes('Trident/')) return 'Internet Explorer';
        return 'Other';
    }

    // 获取浏览器版本
    getBrowserVersion() {
        const userAgent = navigator.userAgent;
        let version = 'Unknown';
        
        // 匹配常见浏览器版本
        const matches = userAgent.match(/(Firefox|Chrome|Safari|Edge|MSIE|Trident\/).*?([\d.]+)/);
        if (matches && matches[2]) {
            version = matches[2];
        }
        
        return version;
    }

    // 收集性能数据
    collectPerformanceData() {
        if (performance && performance.getEntriesByType) {
            // 收集页面加载性能指标
            const navigation = performance.getEntriesByType('navigation')[0];
            if (navigation) {
                this.analyticsData.performance = {
                    navigation: {
                        redirectCount: navigation.redirectCount,
                        type: navigation.type,
                        loadEventEnd: navigation.loadEventEnd,
                        loadEventStart: navigation.loadEventStart,
                        domContentLoadedEventEnd: navigation.domContentLoadedEventEnd,
                        domContentLoadedEventStart: navigation.domContentLoadedEventStart,
                        responseEnd: navigation.responseEnd,
                        responseStart: navigation.responseStart,
                        requestStart: navigation.requestStart,
                        connectEnd: navigation.connectEnd,
                        connectStart: navigation.connectStart,
                        domainLookupEnd: navigation.domainLookupEnd,
                        domainLookupStart: navigation.domainLookupStart,
                        fetchStart: navigation.fetchStart,
                        unloadEventEnd: navigation.unloadEventEnd,
                        unloadEventStart: navigation.unloadEventStart,
                        duration: navigation.duration
                    }
                };
            }

            // 收集资源加载性能指标
            const resources = performance.getEntriesByType('resource');
            if (resources.length > 0) {
                this.analyticsData.performance.resources = resources.map(resource => ({
                    name: resource.name,
                    initiatorType: resource.initiatorType,
                    duration: resource.duration,
                    transferSize: resource.transferSize,
                    encodedBodySize: resource.encodedBodySize,
                    decodedBodySize: resource.decodedBodySize,
                    startTime: resource.startTime,
                    responseEnd: resource.responseEnd
                }));
            }
        }
    }

    // 设置错误监听器
    setupErrorListeners() {
        // 监听JavaScript错误
        window.addEventListener('error', (event) => {
            this.analyticsData.errors.push({
                type: 'JavaScript Error',
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error ? event.error.stack : null,
                timestamp: new Date().toISOString()
            });
        });

        // 监听未捕获的Promise错误
        window.addEventListener('unhandledrejection', (event) => {
            this.analyticsData.errors.push({
                type: 'Promise Rejection',
                message: event.reason ? event.reason.message : 'Unhandled promise rejection',
                reason: event.reason,
                timestamp: new Date().toISOString()
            });
        });
    }

    // 设置用户交互监听器
    setupUserInteractionListeners() {
        // 监听点击事件
        document.addEventListener('click', (event) => {
            this.analyticsData.userInteractions.push({
                type: 'click',
                target: event.target.tagName,
                id: event.target.id || 'no-id',
                className: event.target.className || 'no-class',
                timestamp: new Date().toISOString(),
                x: event.clientX,
                y: event.clientY
            });
        });

        // 监听表单提交事件
        document.addEventListener('submit', (event) => {
            this.analyticsData.userInteractions.push({
                type: 'form_submit',
                formId: event.target.id || 'no-id',
                timestamp: new Date().toISOString()
            });
        });

        // 监听文件上传事件
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', (event) => {
                this.analyticsData.userInteractions.push({
                    type: 'file_upload',
                    inputId: event.target.id || 'no-id',
                    fileCount: event.target.files ? event.target.files.length : 0,
                    timestamp: new Date().toISOString()
                });
            });
        });
    }

    // 设置页面卸载监听器，将数据发送到服务器
    setupPageUnloadListener() {
        window.addEventListener('beforeunload', () => {
            this.sendAnalyticsData();
        });
    }

    // 发送分析数据到服务器
    sendAnalyticsData() {
        if (Object.keys(this.analyticsData.performance).length > 0 || 
            this.analyticsData.userInteractions.length > 0 || 
            this.analyticsData.errors.length > 0) {

            const payload = JSON.stringify(this.analyticsData);

            // beforeunload时fetch会被浏览器取消，用sendBeacon替代
            if (navigator.sendBeacon) {
                const blob = new Blob([payload], { type: 'application/json' });
                navigator.sendBeacon('/frontend-analytics', blob);
            } else {
                fetch('/frontend-analytics', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: payload,
                    keepalive: true
                }).catch(error => {
                    console.error('Failed to send analytics data:', error);
                });
            }
        }
    }

    // 获取分析数据
    getAnalyticsData() {
        return this.analyticsData;
    }

    // 将分析数据保存到localStorage
    saveToLocalStorage() {
        try {
            localStorage.setItem('frontendAnalyticsData', JSON.stringify(this.analyticsData));
        } catch (error) {
            console.error('Failed to save analytics data to localStorage:', error);
        }
    }

    // 从localStorage加载分析数据
    loadFromLocalStorage() {
        try {
            const savedData = localStorage.getItem('frontendAnalyticsData');
            if (savedData) {
                this.analyticsData = JSON.parse(savedData);
            }
        } catch (error) {
            console.error('Failed to load analytics data from localStorage:', error);
        }
    }
}

// 初始化前端分析
let frontendAnalytics;

document.addEventListener('DOMContentLoaded', () => {
    frontendAnalytics = new FrontendAnalytics();
});

// 暴露给全局作用域
window.FrontendAnalytics = FrontendAnalytics;
window.frontendAnalytics = frontendAnalytics;
