import { EChartsManager } from './EChartsManager';
import { ChartType, ChartData, ChartOptions, ChartUpdateResponse, ErrorResponse } from '../../types';

// 声明全局变量
declare const bootstrap: any;
declare const ModalManager: any;

/**
 * 错误处理工具类
 */
class ErrorHandler {
    /**
     * 处理错误
     * @param {Error} error - 错误对象
     * @param {string} context - 错误上下文
     * @returns {ErrorResponse} 错误响应
     */
    static handleError(error: Error, context: string): ErrorResponse {
        console.error(`${context} 错误:`, error);
        console.error(`${context} 错误详情:`, error.stack);
        
        return {
            success: false,
            message: `${context} 失败: ${error.message}`,
            error: error
        };
    }
    
    /**
     * 验证参数
     * @param {any} value - 要验证的值
     * @param {string} name - 参数名称
     * @param {Function} validator - 验证函数
     * @returns {boolean} 验证结果
     */
    static validateParam(value: any, name: string, validator: (val: any) => boolean): boolean {
        if (!validator(value)) {
            console.error(`参数验证失败: ${name}`);
            return false;
        }
        return true;
    }
}

/**
 * 图表初始化器
 * 负责图表功能的初始化和管理
 */
export class ChartInitializer {
    private echartsManager: EChartsManager | null = null;
    private chartModalManager: any = null;
    private currentChartRequest: AbortController | null = null;
    private chartDataCache: Map<string, ChartData> = new Map();


    constructor() {
        this.init();
    }

    /**
     * 初始化图表初始化器
     */
    private init(): void {
        // 初始化ECharts管理器
        if (typeof window !== 'undefined') {
            if (!window.echartsManager) {
                try {
                    window.echartsManager = new EChartsManager();
                    console.log('ECharts图表管理器已初始化');
                } catch (error) {
                    console.error('初始化ECharts图表管理器时出错:', error);
                    this.createFallbackEChartsManager();
                }
            }
            this.echartsManager = window.echartsManager;
        }
    }

    /**
     * 创建备用ECharts管理器
     */
    private createFallbackEChartsManager(): void {
        window.echartsManager = {
            initChart: function(containerId: string, chartType: ChartType, data: ChartData, options: ChartOptions) {
                console.warn('使用备用ECharts管理器');
                const container = document.getElementById(containerId);
                if (container) {
                    container.innerHTML = `
                        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                            <i class="bi bi-exclamation-triangle text-warning" style="font-size: 2rem; margin-bottom: 10px;"></i>
                            <p class="text-muted text-center">ECharts管理器未初始化</p>
                            <p class="text-muted text-center small">请检查echarts-manager.js是否正确引入</p>
                        </div>
                    `;
                }
            }
        };
    }

    /**
     * 初始化所有图表功能
     * @param {string} formSelector - 表单选择器
     */
    initAllChartFeatures(formSelector: string): void {
        console.log('开始初始化图表功能，表单选择器:', formSelector);
        
        // 确保formSelector是一个有效的字符串
        if (typeof formSelector === 'string' && formSelector.trim() !== '') {
            // 为指定的图表设置表单添加提交事件监听器
            const form = document.querySelector(formSelector);
            if (form) {
                // 先移除可能存在的旧事件监听器，避免重复绑定
                form.removeEventListener('submit', this.handleChartFormSubmit.bind(this));
                
                // 添加新的事件监听器
                form.addEventListener('submit', this.handleChartFormSubmit.bind(this));
                console.log('已为图表设置表单添加提交事件监听器');
            } else {
                console.log('表单', formSelector, '不存在，跳过表单相关初始化');
            }
        }

        // 初始化模态框管理器 - 使用模块化设计，实现高内聚低耦合
        if (typeof ModalManager !== 'undefined') {
            this.chartModalManager = new ModalManager('chartModal');
            console.log('模态框管理器已初始化');
        } else {
            console.error('未找到ModalManager类，请确保已正确引入modal-manager.js');
        }
        
        // 初始化拖放排序功能
        try {
            this.initDragAndDrop();
            console.log('拖放排序功能初始化完成');
        } catch (error) {
            console.error('初始化拖放排序功能时出错:', error);
        }

        // 初始化tooltip
        try {
            this.initTooltips();
        } catch (error) {
            console.error('初始化tooltip时出错:', error);
        }
        
        // 初始化图表布局显示
        try {
            this.initChartLayout();
        } catch (error) {
            console.error('初始化图表布局时出错:', error);
        }
        
        // 为图表图片绑定点击事件
        try {
            this.bindChartClickEvents();
            console.log('已绑定图表点击事件');
        } catch (error) {
            console.error('绑定图表点击事件时出错:', error);
        }
        
        // 初始化ECharts图表 - 使用延迟加载优化性能
        try {
            this.initEChartsChartsWithLazyLoad();
            console.log('ECharts图表已初始化（使用延迟加载）');
        } catch (error) {
            console.error('初始化ECharts图表时出错:', error);
        }
    }

    /**
     * 初始化tooltip
     */
    private initTooltips(): void {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        console.log('已初始化tooltip:', tooltipList.length, '个');
    }

    /**
     * 初始化图表布局
     */
    private initChartLayout(): void {
        const activeLayout = document.querySelector('input[name="chartLayout"]:checked');
        if (activeLayout) {
            this.toggleChartLayout((activeLayout as HTMLInputElement).value);
            console.log('已初始化图表布局:', (activeLayout as HTMLInputElement).value);
        } else {
            console.log('未找到选中的图表布局，跳过布局初始化');
        }
    }

    /**
     * 切换图表布局显示
     * @param {string} layout - 布局类型
     */
    toggleChartLayout(layout: string): void {
        // 先隐藏所有图表容器
        ['stacked', 'parallel'].forEach(type => {
            const container = document.querySelector(`.chart-${type}`);
            if (container) container.classList.add('d-none');
        });
        
        // 显示选中的图表容器
        const targetContainer = document.querySelector(
            layout === 'parallel' ? '.chart-parallel' : '.chart-stacked'
        );
        if (targetContainer) targetContainer.classList.remove('d-none');
        
        // 重新绑定图表点击事件
        this.bindChartClickEvents();
    }

    /**
     * 图表设置表单提交事件处理函数
     * @param {Event} e - 事件对象
     */
    handleChartFormSubmit(e: Event): void {
        e.preventDefault(); // 阻止表单默认提交行为
        const form = e.target as HTMLFormElement;
        const formSelector = '#' + form.id;
        this.updateChartSettings(formSelector); // 调用自定义的更新函数
        console.log('图表设置表单已提交，正在更新图表');
    }

    /**
     * 更新图表设置
     * @param {string} formSelector - 表单选择器
     */
    updateChartSettings(formSelector: string): void {
        const form = document.querySelector(formSelector);
        if (!form) return;

        // 收集选中的图表类型
        const selectedTypes = Array.from(document.querySelectorAll('.chart-type-checkbox:checked'))
            .map(checkbox => (checkbox as HTMLInputElement).value);

        // 如果没有选择任何图表类型,则默认选择箱线图
        if (selectedTypes.length === 0) {
            selectedTypes.push('box');
            const boxCheckbox = document.querySelector('.chart-type-checkbox[value="box"]');
            if (boxCheckbox) (boxCheckbox as HTMLInputElement).checked = true;
        }

        // 获取当前布局设置
        const layout = document.querySelector('input[name="chartLayout"]:checked') as HTMLInputElement;
        const layoutValue = layout ? layout.value : 'stacked';

        // 准备发送的数据
        const formData = new FormData(form);
        formData.set('chart_types', selectedTypes.join(','));
        formData.set('chartLayout', layoutValue);
        formData.set('chart_update', 'true');
        
        // 确保包含CSRF令牌 - 从当前表单中获取
        const csrfToken = form.querySelector('input[name="csrf_token"]') as HTMLInputElement;
        if (csrfToken) {
            formData.set('csrf_token', csrfToken.value);
        } else {
            // 如果当前表单中没有找到，则尝试从页面其他位置获取
            const pageCsrfToken = document.querySelector('input[name="csrf_token"]') as HTMLInputElement;
            if (pageCsrfToken) {
                formData.set('csrf_token', pageCsrfToken.value);
            }
        }

        // 显示加载指示器
        this.showLoadingIndicator();

        // 更新状态：开始发送数据
        setTimeout(() => {
            this.updateStatusIndicator('sending', '正在向服务器发送图表设置...', 30, '处理图表类型: ' + selectedTypes.join(', '));
        }, 300);

        // 取消当前正在进行的请求（如果有）
        if (this.currentChartRequest) {
            this.currentChartRequest.abort();
            this.currentChartRequest = null;
        }

        // 创建新的AbortController用于取消请求
        this.currentChartRequest = new AbortController();

        // 发送AJAX请求更新图表
        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            signal: this.currentChartRequest.signal
        })
        .then(response => {
            this.currentChartRequest = null;
            // 更新状态：数据已发送，等待处理
            this.updateStatusIndicator('processing', '服务器正在处理图表数据...', 60, '正在生成图表，请稍候...');
            return response.json();
        })
        .then((data: ChartUpdateResponse) => {
            if (data.success) {
                // 更新状态：图表已生成，正在更新显示
                this.updateStatusIndicator('updating', '正在更新页面图表显示...', 80, '图表数据已准备就绪，正在渲染到页面...');
                
                // 更新图表区域
                this.updateChartArea(data);
                
                // 更新图表类型选择框的状态
                if (data.chart_types) {
                    document.querySelectorAll('.chart-type-checkbox').forEach(cb => (cb as HTMLInputElement).checked = false);
                    data.chart_types.forEach(type => {
                        const checkbox = document.querySelector(`.chart-type-checkbox[value="${type}"]`);
                        if (checkbox) (checkbox as HTMLInputElement).checked = true;
                    });
                }
                
                // 更新布局选择
                if (data.chart_layout) {
                    const layoutRadio = document.querySelector(`input[name="chartLayout"][value="${data.chart_layout}"]`);
                    if (layoutRadio) {
                        (layoutRadio as HTMLInputElement).checked = true;
                        this.toggleChartLayout(data.chart_layout);
                    }
                }
                
                // 更新状态：完成
                this.updateStatusIndicator('completed', '图表更新完成！', 100, '所有图表已成功生成并显示在页面上。');
                
                // 2秒后自动隐藏状态指示器
                setTimeout(() => {
                    this.hideLoadingIndicator();
                }, 2000);
            } else {
                // 更新状态：错误
                this.updateStatusIndicator('error', '图表更新失败', 100, '错误信息: ' + (data.message || '未知错误'));
                alert('图表更新失败: ' + (data.message || '未知错误'));
            }
        })
        .catch(error => {
            this.currentChartRequest = null;
            // 忽略取消请求的错误
            if (error.name === 'AbortError') {
                console.log('图表更新请求已取消');
                return;
            }
            console.error('更新图表时发生错误:', error);
            this.updateStatusIndicator('error', '更新图表时发生网络错误', 100, '错误详情: ' + error.message);
            alert('更新图表时发生错误: ' + error.message);
        });
    }

    /**
     * 拖放排序功能实现
     */
    initDragAndDrop(): void {
        const sortableList = document.getElementById('sortableChartList');
        let draggedItem: HTMLElement | null = null;

        if (!sortableList) return;

        // 设置所有可拖拽项为可拖拽
        sortableList.querySelectorAll('.draggable-item').forEach(item => {
            (item as HTMLElement).setAttribute('draggable', 'true');
        });

        // 使用事件委托处理拖放事件
        sortableList.addEventListener('dragstart', (e: DragEvent) => {
            const target = e.target as HTMLElement;
            if (target.closest('.draggable-item')) {
                draggedItem = target.closest('.draggable-item') as HTMLElement;
                draggedItem.classList.add('dragging');
                if (e.dataTransfer) {
                    e.dataTransfer.effectAllowed = 'move';
                }
            }
        });

        sortableList.addEventListener('dragend', (e: DragEvent) => {
            const target = e.target as HTMLElement;
            if (target.closest('.draggable-item')) {
                const item = target.closest('.draggable-item') as HTMLElement;
                item.classList.remove('dragging');
                item.classList.remove('border-primary');
                draggedItem = null;
            }
            (e.currentTarget as HTMLElement).classList.remove('drag-over');
        });

        sortableList.addEventListener('dragenter', (e: DragEvent) => {
            const target = e.target as HTMLElement;
            if (target.closest('.draggable-item')) {
                const item = target.closest('.draggable-item') as HTMLElement;
                if (item !== draggedItem) {
                    item.classList.add('border-primary');
                }
            }
        });

        sortableList.addEventListener('dragleave', (e: DragEvent) => {
            const target = e.target as HTMLElement;
            if (target.closest('.draggable-item')) {
                const item = target.closest('.draggable-item') as HTMLElement;
                item.classList.remove('border-primary');
            }
        });

        sortableList.addEventListener('dragover', (e: DragEvent) => {
            e.preventDefault();
            if (e.dataTransfer) {
                e.dataTransfer.dropEffect = 'move';
            }
            
            const target = e.target as HTMLElement;
            if (target.closest('.draggable-item')) {
                const item = target.closest('.draggable-item') as HTMLElement;
                if (item !== draggedItem) {
                    item.classList.add('border-primary');
                }
            }
            (e.currentTarget as HTMLElement).classList.add('drag-over');
        });

        sortableList.addEventListener('drop', (e: DragEvent) => {
            e.preventDefault();
            (e.currentTarget as HTMLElement).classList.remove('drag-over');
            
            const target = e.target as HTMLElement;
            if (target.closest('.draggable-item') && draggedItem) {
                const targetItem = target.closest('.draggable-item') as HTMLElement;
                
                if (targetItem !== draggedItem) {
                    // 移除所有临时样式
                    targetItem.classList.remove('border-primary');
                    
                    const items = Array.from((e.currentTarget as HTMLElement).children);
                    const draggedIndex = items.indexOf(draggedItem);
                    const targetIndex = items.indexOf(targetItem);
                    
                    if (draggedIndex < targetIndex) {
                        (e.currentTarget as HTMLElement).insertBefore(draggedItem, targetItem.nextSibling);
                    } else {
                        (e.currentTarget as HTMLElement).insertBefore(draggedItem, targetItem);
                    }
                    
                    this.updateChartOrder();
                }
            }
        });

        // 点击拖拽手柄也能触发拖拽
        sortableList.addEventListener('mousedown', (e: MouseEvent) => {
            const target = e.target as HTMLElement;
            if (target.closest('.drag-handle')) {
                const draggableItem = target.closest('.draggable-item') as HTMLElement;
                if (draggableItem) {
                    draggableItem.setAttribute('draggable', 'true');
                    setTimeout(() => {
                        draggableItem.classList.add('dragging');
                        const dragEvent = new DragEvent('dragstart', {
                            bubbles: true,
                            cancelable: true,
                            dataTransfer: new DataTransfer()
                        });
                        draggableItem.dispatchEvent(dragEvent);
                    }, 0);
                }
            }
        });
    }

    /**
     * 更新图表顺序
     */
    updateChartOrder(): void {
        // 这里可以添加更新图表顺序的逻辑
        console.log('图表顺序已更新');
    }

    /**
     * 为图表图片绑定点击事件
     */
    bindChartClickEvents(): void {
        // 为所有图表图片设置Bootstrap模态框属性和错误处理
        document.querySelectorAll('.chart-img').forEach(img => {
            const image = img as HTMLImageElement;
            // 确保保留或设置所有必要的模态框属性
            // 这些属性应该已经由模板设置，但确保它们存在
            if (!image.hasAttribute('data-bs-toggle')) {
                image.setAttribute('data-bs-toggle', 'modal');
            }
            if (!image.hasAttribute('data-bs-target')) {
                image.setAttribute('data-bs-target', '#chartModal');
            }
            // 确保data-chart-title属性存在
            if (!image.hasAttribute('data-chart-title') && image.hasAttribute('alt')) {
                image.setAttribute('data-chart-title', image.getAttribute('alt') || '');
            }
            // 确保data-chart-src属性存在 - 从src属性推导（仅当缺少时）
            if (!image.hasAttribute('data-chart-src')) {
                // 从PNG URL推导HTML URL
                const pngUrl = image.getAttribute('src');
                if (pngUrl) {
                    // 将/view_chart/替换为/view_chart_html/，将.png替换为.html
                    let htmlUrl = pngUrl;
                    if (htmlUrl.includes('/view_chart/')) {
                        htmlUrl = htmlUrl.replace('/view_chart/', '/view_chart_html/');
                    }
                    if (htmlUrl.endsWith('.png')) {
                        htmlUrl = htmlUrl.replace('.png', '.html');
                    }
                    image.setAttribute('data-chart-src', htmlUrl);
                }
            }
            
            // 添加错误处理，当图片加载失败时显示友好信息
            image.addEventListener('error', (e: Event) => {
                const target = e.target as HTMLImageElement;
                console.error('图表图片加载失败:', target.src);
                // 替换为友好的错误信息
                const errorContainer = document.createElement('div');
                errorContainer.className = 'chart-img-error text-center p-5 bg-light border rounded';
                errorContainer.innerHTML = `
                    <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem;"></i>
                    <h6 class="mt-3 text-danger">图表加载失败</h6>
                    <p class="text-muted">无法加载图表图片，请尝试刷新页面或重新生成图表</p>
                    <p class="text-muted small">图片URL: ${target.src}</p>
                    <div class="d-flex gap-2 justify-content-center mt-3">
                        <button class="btn btn-sm btn-primary" onclick="location.reload()">
                            <i class="bi bi-arrow-clockwise me-1"></i>刷新页面
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="retryChartImageLoad(this, '${target.src}')">
                            <i class="bi bi-arrow-repeat me-1"></i>重试加载
                        </button>
                    </div>
                `;
                // 替换图片元素
                target.parentNode?.replaceChild(errorContainer, target);
            });
            
            // 添加加载指示器
            image.addEventListener('loadstart', function() {
                this.style.opacity = '0.5';
            });
            
            image.addEventListener('load', function() {
                this.style.opacity = '1';
            });
        });
    }

    /**
     * 使用Intersection Observer实现ECharts图表延迟加载
     */
    initEChartsChartsWithLazyLoad(): void {
        // 查找所有需要初始化的ECharts图表容器
        const chartContainers = document.querySelectorAll('.echarts-chart');
        console.log(`找到 ${chartContainers.length} 个ECharts图表容器，启用延迟加载`);
        
        if (chartContainers.length === 0) {
            console.log('未找到ECharts图表容器，可能图表尚未生成或已被隐藏');
            return;
        }
        
        // 创建Intersection Observer实例
        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const container = entry.target;
                    // 移除观察，避免重复初始化
                    observer.unobserve(container);
                    // 初始化图表
                    this.initSingleEChartsChart(container as HTMLElement);
                }
            });
        }, {
            rootMargin: '100px', // 提前100px开始加载
            threshold: 0.1       // 容器可见10%时开始加载
        });
        
        // 观察所有图表容器
        chartContainers.forEach(container => {
            observer.observe(container);
        });
        
        // 保存observer引用，以便后续清除
        if (typeof window !== 'undefined') {
            window.chartObserver = observer;
        }
    }

    /**
     * 解析图表数据
     * @param {string} chartDataAttr - 图表数据属性
     * @param {string} containerId - 容器ID
     * @param {ChartType} chartType - 图表类型
     * @returns {ChartData} 解析后的数据
     */
    private parseChartData(chartDataAttr: string, containerId: string, chartType: ChartType): ChartData {
        let data: ChartData = [];
        const cacheKey = `${containerId}_${chartType}`;
        
        // 检查缓存中是否已有解析好的数据
        if (this.chartDataCache.has(cacheKey)) {
            data = this.chartDataCache.get(cacheKey) as ChartData;
            console.log(`[图表 ${containerId}] 使用缓存的图表数据: ${cacheKey}`);
            return data;
        }
        
        // 尝试解析数据，因为后端返回的是JSON字符串
        let cleanedData = '';
        try {
            // 清理数据，移除可能存在的无效字符和HTML实体
            cleanedData = chartDataAttr.trim();
            
            console.log(`[图表 ${containerId}] 原始数据长度: ${cleanedData.length}`);
            console.log(`[图表 ${containerId}] 原始数据前200字符: ${cleanedData.substring(0, 200)}...`);
            console.log(`[图表 ${containerId}] 原始数据类型: ${typeof cleanedData}`);
            
            // 处理HTML实体
            cleanedData = cleanedData.replace(/&quot;/g, '"');
            cleanedData = cleanedData.replace(/&amp;/g, '&');
            cleanedData = cleanedData.replace(/&lt;/g, '<');
            cleanedData = cleanedData.replace(/&gt;/g, '>');
            
            // 只去除首尾空白，保留JSON内部的格式
            cleanedData = cleanedData.trim();
            
            console.log(`[图表 ${containerId}] 清理后数据长度: ${cleanedData.length}`);
            console.log(`[图表 ${containerId}] 清理后数据前200字符: ${cleanedData.substring(0, 200)}...`);
            
            // 检查是否是空字符串
            if (cleanedData === '') {
                console.warn(`[图表 ${containerId}] 清理后数据为空字符串，使用空数组`);
                data = [];
            } else {
                // 尝试解析JSON字符串
                try {
                    // 尝试解析一次
                    data = JSON.parse(cleanedData);
                    console.log(`[图表 ${containerId}] 解析图表数据成功，数据类型: ${typeof data}, 数据长度: ${Array.isArray(data) ? data.length : (typeof data === 'object' ? Object.keys(data).length : '非对象')}`);
                } catch (parseError) {
                    // 尝试修复可能的JSON格式问题
                    console.warn(`[图表 ${containerId}] 标准JSON解析失败，尝试修复格式: ${parseError.message}`);
                    
                    // 尝试1: 移除可能的多余逗号
                    let fixedData = cleanedData.replace(/,\s*}/g, '}');
                    fixedData = fixedData.replace(/,\s*\]/g, ']');
                    try {
                        data = JSON.parse(fixedData);
                        console.log(`[图表 ${containerId}] 修复后解析图表数据成功`);
                    } catch (secondParseError) {
                        console.warn(`[图表 ${containerId}] 修复后解析仍失败，尝试解析双重编码的JSON字符串: ${secondParseError.message}`);
                        
                        // 尝试2: 解析双重编码的JSON字符串
                        try {
                            data = JSON.parse(JSON.parse(cleanedData));
                            console.log(`[图表 ${containerId}] 解析双重编码的JSON字符串成功`);
                        } catch (doubleParseError) {
                            console.warn(`[图表 ${containerId}] 解析双重编码的JSON字符串也失败: ${doubleParseError.message}`);
                            
                            // 尝试3: 移除可能的HTML标签或其他无效字符
                            try {
                                fixedData = cleanedData.replace(/<[^>]*>/g, '');
                                
                                // 尝试3.1: 正常JSON解析
                                try {
                                    data = JSON.parse(fixedData);
                                    console.log(`[图表 ${containerId}] 移除HTML标签后解析成功`);
                                } catch (e) {
                                    // 尝试3.2: 处理可能被截断的JSON
                                    console.warn(`[图表 ${containerId}] 尝试处理可能被截断的JSON`);
                                    
                                    // 尝试添加缺失的闭合括号
                                    if (fixedData.startsWith('[{')) {
                                        let tempData = fixedData;
                                        // 尝试添加不同的闭合括号组合
                                        const closingOptions = ['}]', '}', ']'];
                                        let parseSuccess = false;
                                        
                                        for (const closing of closingOptions) {
                                            try {
                                                tempData = fixedData + closing;
                                                data = JSON.parse(tempData);
                                                console.log(`[图表 ${containerId}] 添加闭合括号 ${closing} 后解析成功`);
                                                parseSuccess = true;
                                                break;
                                            } catch (e) {
                                                // 继续尝试下一个选项
                                            }
                                        }
                                        
                                        if (!parseSuccess) {
                                            // 尝试3.3: 手动构建箱线图数据结构
                                            console.warn(`[图表 ${containerId}] 尝试手动构建箱线图数据结构`);
                                            try {
                                                // 从原始数据中提取转速和值
                                                const speedPattern = /"name":"([^"]+)"/g;
                                                const valuePattern = /"data":\[(.*?)\]/g;
                                                const speeds = [];
                                                const values = [];
                                                let match;
                                                
                                                while ((match = speedPattern.exec(fixedData)) !== null) {
                                                    speeds.push(match[1]);
                                                }
                                                
                                                while ((match = valuePattern.exec(fixedData)) !== null) {
                                                    try {
                                                        const valueArray = JSON.parse('[' + match[1] + ']');
                                                        values.push(valueArray);
                                                    } catch (e) {
                                                        // 忽略解析失败的情况
                                                    }
                                                }
                                                
                                                // 构建箱线图数据结构
                                                const boxData = [];
                                                for (let i = 0; i < speeds.length && i < values.length; i++) {
                                                    let boxValues = values[i];
                                                    // 确保data是长度为5的数组
                                                    if (!Array.isArray(boxValues)) {
                                                        boxValues = [0, 0, 0, 0, 0];
                                                    } else if (boxValues.length !== 5) {
                                                        // 如果数组长度不是5，填充或截断到5个元素
                                                        while (boxValues.length < 5) {
                                                            boxValues.push(0);
                                                        }
                                                        boxValues = boxValues.slice(0, 5);
                                                    }
                                                    boxData.push({
                                                        name: speeds[i],
                                                        data: boxValues
                                                    });
                                                }
                                                
                                                if (boxData.length > 0) {
                                                    data = boxData;
                                                    console.log(`[图表 ${containerId}] 手动构建箱线图数据结构成功，数据长度: ${boxData.length}`);
                                                } else {
                                                    // 尝试3.4: 基于图表类型构建默认数据结构
                                                    console.warn(`[图表 ${containerId}] 手动构建失败，尝试基于图表类型构建默认数据`);
                                                    data = this.buildDefaultChartData(chartType);
                                                    console.log(`[图表 ${containerId}] 构建默认图表数据成功`);
                                                }
                                            } catch (e) {
                                                // 尝试基于图表类型构建默认数据
                                                console.warn(`[图表 ${containerId}] 手动构建失败，尝试基于图表类型构建默认数据`);
                                                data = this.buildDefaultChartData(chartType);
                                                console.log(`[图表 ${containerId}] 构建默认图表数据成功`);
                                            }
                                        }
                                    } else if (fixedData.startsWith('{')) {
                                        // 处理对象类型的JSON
                                        let tempData = fixedData + '}';
                                        try {
                                            data = JSON.parse(tempData);
                                            console.log(`[图表 ${containerId}] 添加闭合括号 } 后解析成功`);
                                        } catch (e) {
                                            // 尝试基于图表类型构建默认数据
                                            console.warn(`[图表 ${containerId}] 对象JSON解析失败，尝试构建默认数据`);
                                            data = this.buildDefaultChartData(chartType);
                                            console.log(`[图表 ${containerId}] 构建默认图表数据成功`);
                                        }
                                    } else {
                                        // 尝试基于图表类型构建默认数据
                                        console.warn(`[图表 ${containerId}] 未知格式，尝试构建默认数据`);
                                        data = this.buildDefaultChartData(chartType);
                                        console.log(`[图表 ${containerId}] 构建默认图表数据成功`);
                                    }
                                }
                            } catch (htmlError) {
                                console.warn(`[图表 ${containerId}] 移除HTML标签后解析也失败: ${htmlError.message}`);
                                // 尝试基于图表类型构建默认数据
                                console.warn(`[图表 ${containerId}] 所有解析方法都失败，尝试构建默认数据`);
                                data = this.buildDefaultChartData(chartType);
                                console.log(`[图表 ${containerId}] 构建默认图表数据成功`);
                            }
                        }
                    }
                }
            }
            
            // 验证解析后的数据
            if (data === null || typeof data !== 'object') {
                console.warn(`[图表 ${containerId}] 解析后的数据类型无效: ${typeof data}`);
                data = [];
            }
            
            // 验证数据格式是否与图表类型匹配
            if (!this.validateChartData(data, chartType, containerId)) {
                console.warn(`[图表 ${containerId}] 数据格式与图表类型不匹配，使用空数组`);
                data = [];
            }
            
            // 将解析后的数据存入缓存
            this.chartDataCache.set(cacheKey, data);
            console.log(`[图表 ${containerId}] 数据已存入缓存，缓存键: ${cacheKey}`);
        } catch (parseError) {
            console.error(`[图表 ${containerId}] 图表数据解析失败: ${parseError.message}`);
            console.error(`[图表 ${containerId}] 清理后数据前200字符: ${cleanedData.substring(0, 200)}...`);
            console.error(`[图表 ${containerId}] 解析错误详情: ${parseError.stack}`);
            
            // 尝试使用更强大的解析方法
            try {
                // 尝试使用eval（仅作为最后的手段）
                if (cleanedData && cleanedData.length > 0) {
                    // 确保数据是有效的JavaScript表达式
                    let evalData = cleanedData;
                    if (!evalData.startsWith('{') && !evalData.startsWith('[')) {
                        evalData = '[' + evalData + ']';
                    }
                    data = eval(`(${evalData})`);
                    console.log(`[图表 ${containerId}] 使用eval解析成功: 数据类型: ${typeof data}`);
                    
                    // 验证eval解析后的数据
                    if (data === null || typeof data !== 'object') {
                        console.warn(`[图表 ${containerId}] eval解析后的数据类型无效: ${typeof data}`);
                        data = [];
                    } else if (!this.validateChartData(data, chartType, containerId)) {
                        console.warn(`[图表 ${containerId}] eval解析后的数据格式与图表类型不匹配，使用空数组`);
                        data = [];
                    } else {
                        this.chartDataCache.set(cacheKey, data);
                    }
                } else {
                    throw new Error('Empty data for eval');
                }
            } catch (evalError) {
                console.error(`[图表 ${containerId}] 使用eval解析也失败: ${evalError.message}`);
                console.error(`[图表 ${containerId}] eval错误详情: ${evalError.stack}`);
                // 如果所有解析方法都失败，使用空数据
                data = [];
                console.log(`[图表 ${containerId}] 使用空数组作为默认数据`);
            }
        }
        
        return data;
    }

    /**
     * 基于图表类型构建默认数据结构
     * @param {ChartType} chartType - 图表类型
     * @returns {ChartData} 默认数据结构
     */
    private buildDefaultChartData(chartType: ChartType): ChartData {
        switch (chartType) {
            case 'box':
                return [
                    { name: '3000rpm', data: [0, 0, 0, 0, 0] },
                    { name: '4000rpm', data: [0, 0, 0, 0, 0] },
                    { name: '5000rpm', data: [0, 0, 0, 0, 0] }
                ];
            case 'trend':
                return [
                    { name: '3000rpm', value: 0 },
                    { name: '4000rpm', value: 0 },
                    { name: '5000rpm', value: 0 }
                ];
            case 'scatter':
                return [
                    ['3000rpm', 0],
                    ['4000rpm', 0],
                    ['5000rpm', 0]
                ];
            case 'heatmap':
                return [
                    ['3000rpm', 0, 0],
                    ['4000rpm', 0, 0],
                    ['5000rpm', 0, 0]
                ];
            case 'histogram':
                return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
            case 'bubble':
                return [
                    { name: '3000rpm', value: ['3000rpm', 0, 1] },
                    { name: '4000rpm', value: ['4000rpm', 0, 1] },
                    { name: '5000rpm', value: ['5000rpm', 0, 1] }
                ];
            case 'violin':
                return [
                    { name: '3000rpm', data: [0] },
                    { name: '4000rpm', data: [0] },
                    { name: '5000rpm', data: [0] }
                ];
            case '3d':
                return [
                    ['3000rpm', 0, 0],
                    ['4000rpm', 0, 0],
                    ['5000rpm', 0, 0]
                ];
            case 'parallel':
                return [
                    ['3000rpm', 0, 0],
                    ['4000rpm', 0, 0],
                    ['5000rpm', 0, 0]
                ];
            default:
                return [];
        }
    }

    /**
     * 验证图表数据格式
     * @param {ChartData} data - 图表数据
     * @param {ChartType} chartType - 图表类型
     * @param {string} containerId - 容器ID
     * @returns {boolean} 验证结果
     */
    private validateChartData(data: ChartData, chartType: ChartType, containerId: string): boolean {
        try {
            switch (chartType) {
                case 'box':
                    return Array.isArray(data) && data.every(item => 
                        typeof item === 'object' && 
                        item !== null && 
                        'name' in item && 
                        'data' in item && 
                        Array.isArray(item.data) && 
                        item.data.length === 5
                    );
                case 'trend':
                    return Array.isArray(data) && data.every(item => 
                        typeof item === 'object' && 
                        item !== null && 
                        'name' in item && 
                        'value' in item && 
                        typeof item.value === 'number'
                    );
                case 'scatter':
                    return Array.isArray(data) && data.every(item => 
                        Array.isArray(item) && 
                        item.length === 2
                    );
                case 'heatmap':
                    return Array.isArray(data) && data.every(item => 
                        Array.isArray(item) && 
                        item.length === 3
                    );
                case 'histogram':
                    return Array.isArray(data) && data.every(item => 
                        typeof item === 'number'
                    );
                case 'bubble':
                    return Array.isArray(data) && data.every(item => 
                        typeof item === 'object' && 
                        item !== null && 
                        'name' in item && 
                        'value' in item && 
                        Array.isArray(item.value) && 
                        item.value.length === 3
                    );
                case 'violin':
                    return Array.isArray(data) && data.every(item => 
                        typeof item === 'object' && 
                        item !== null && 
                        'name' in item && 
                        'data' in item && 
                        Array.isArray(item.data)
                    );
                case '3d':
                    return Array.isArray(data) && data.every(item => 
                        Array.isArray(item) && 
                        item.length === 3
                    );
                case 'parallel':
                    return Array.isArray(data) && data.every(item => 
                        Array.isArray(item) && 
                        item.length >= 2
                    );
                default:
                    console.warn(`[图表 ${containerId}] 未知的图表类型: ${chartType}`);
                    return true;
            }
        } catch (error) {
            console.error(`[图表 ${containerId}] 验证数据格式时出错: ${error.message}`);
            return false;
        }
    }

    /**
     * 初始化单个ECharts图表
     * @param {HTMLElement} container - 图表容器
     */
    initSingleEChartsChart(container: HTMLElement): void {
        // 边界条件检查
        if (!container) {
            console.error('图表容器为空');
            return;
        }
        
        const containerId = container.id;
        if (!containerId) {
            console.error('图表容器缺少ID属性');
            this.showError('unknown', '图表容器缺少ID属性');
            return;
        }
        
        const chartType = container.getAttribute('data-chart-type') as ChartType;
        const chartDataAttr = container.getAttribute('data-chart-data');
        const chartTitle = container.getAttribute('data-chart-title');
        const chartColor = container.getAttribute('data-chart-color');
        
        console.log(`处理图表容器: ${containerId}, 类型: ${chartType}`);
        
        // 验证必要属性
        if (!chartType) {
            console.error(`图表容器 ${containerId} 缺少data-chart-type属性`);
            this.showError(containerId, '图表类型未定义');
            return;
        }
        
        if (!chartDataAttr) {
            console.error(`图表容器 ${containerId} 缺少data-chart-data属性`);
            this.showError(containerId, '图表数据未定义');
            return;
        }
        
        try {
            // 显示加载状态
            container.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <p class="mt-2 text-muted">图表加载中...</p>
                    <p class="text-muted small">正在处理数据，请稍候...</p>
                </div>
            `;
            
            // 解析图表数据
            const data = this.parseChartData(chartDataAttr, containerId, chartType);
            
            // 验证缓存中的数据
            const cacheKey = `${containerId}_${chartType}`;
            if (this.chartDataCache.has(cacheKey)) {
                const cachedData = this.chartDataCache.get(cacheKey);
                console.log(`[图表 ${containerId}] 缓存数据验证: 数据类型: ${typeof cachedData}, 数据长度: ${Array.isArray(cachedData) ? cachedData.length : (typeof cachedData === 'object' ? Object.keys(cachedData).length : '非对象')}`);
            }

            // 验证数据
            let isEmpty = false;
            let dataType = typeof data;
            let dataLength = 0;
            
            if (!data) {
                isEmpty = true;
                dataType = 'null/undefined';
            } else if (Array.isArray(data)) {
                dataLength = data.length;
                isEmpty = data.length === 0;
            } else if (typeof data === 'object') {
                dataLength = Object.keys(data).length;
                isEmpty = Object.keys(data).length === 0;
            } else if (chartType === 'histogram' && Array.isArray(data) && data.every(val => val === 0)) {
                isEmpty = true;
                dataLength = data.length;
            }
            
            // 增强的调试信息
            console.log(`图表数据验证: ${containerId}`);
            console.log(`数据类型: ${dataType}`);
            console.log(`数据长度: ${dataLength}`);
            console.log(`是否为空: ${isEmpty}`);
            
            if (isEmpty) {
                console.warn(`图表数据为空: ${containerId}, 数据类型: ${dataType}, 长度: ${dataLength}`);
                // 显示空数据提示
                container.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                        <i class="bi bi-info-circle text-info" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <p class="text-muted text-center">暂无数据</p>
                        <p class="text-muted text-center small">数据类型: ${dataType}</p>
                        <p class="text-muted text-center small">数据长度: ${dataLength}</p>
                        <p class="text-muted text-center small">图表类型: ${chartType}</p>
                    </div>
                `;
                return;
            }
            
            const options: ChartOptions = {
                title: chartTitle || `${chartType}图表`,
                color: chartColor || '#1f77b4'
            };
            
            // 使用ECharts管理器初始化图表
            if (this.echartsManager) {
                console.log(`调用echartsManager.initChart初始化图表: ${containerId}`);
                this.echartsManager.initChart(
                    containerId,
                    chartType,
                    data,
                    options
                );
            } else {
                console.error('ECharts管理器未初始化，尝试直接初始化图表');
                // 尝试直接初始化ECharts图表
                try {
                    if (typeof window !== 'undefined' && typeof window.echarts !== 'undefined') {
                        const chart = window.echarts.init(container);
                        console.log(`直接初始化ECharts图表成功: ${containerId}`);
                        // 简单的图表配置
                        const simpleOption = {
                            title: {
                                text: options.title,
                                left: 'center'
                            },
                            tooltip: {
                                trigger: 'axis'
                            },
                            xAxis: {
                                type: 'category',
                                data: ['数据1', '数据2', '数据3']
                            },
                            yAxis: {
                                type: 'value'
                            },
                            series: [{
                                data: [100, 200, 300],
                                type: 'bar',
                                color: options.color
                            }]
                        };
                        chart.setOption(simpleOption);
                    } else {
                        console.error('ECharts库未加载');
                        this.showError(containerId, 'ECharts库未加载');
                    }
                } catch (directInitError) {
                    console.error(`直接初始化图表失败: ${directInitError.message}`);
                    this.showError(containerId, '图表初始化失败');
                }
            }
        } catch (error) {
            ErrorHandler.handleError(error as Error, `初始化图表 ${containerId}`);
            // 显示友好的错误信息
            container.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                    <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem; margin-bottom: 10px;"></i>
                    <p class="text-danger text-center">图表初始化失败</p>
                    <p class="text-muted text-center small">${(error as Error).message}</p>
                    <button class="btn btn-sm btn-primary mt-3" onclick="retryChartInit('${containerId}')">
                        <i class="bi bi-arrow-repeat me-1"></i>重试
                    </button>
                </div>
            `;
        }
    }

    /**
     * 更新图表区域内容
     * @param {ChartUpdateResponse} data - 图表更新响应数据
     */
    updateChartArea(data: ChartUpdateResponse): void {
        console.log('开始更新图表区域内容');
        try {
            if (!data) {
                console.error('更新图表区域失败：响应数据为空');
                this.showChartAreaError('图表更新失败：响应数据为空');
                return;
            }

            if (!data.charts_html) {
                console.error('更新图表区域失败：charts_html字段为空');
                this.showChartAreaError('图表更新失败：图表HTML数据为空');
                return;
            }

            console.log(`图表HTML数据长度: ${data.charts_html.length}`);
            console.log(`图表HTML数据前200字符: ${data.charts_html.substring(0, 200)}...`);

            const parser = new DOMParser();
            let doc;
            try {
                doc = parser.parseFromString(data.charts_html, 'text/html');
                console.log('图表HTML解析成功');
            } catch (parseError) {
                console.error('解析图表HTML时出错:', parseError);
                this.showChartAreaError(`图表更新失败：HTML解析错误 - ${parseError.message}`);
                return;
            }
            
            // 更新所有图表容器的内容
            const containerTypes = ['stacked', 'parallel', 'combined'];
            let updatedContainers = 0;
            
            containerTypes.forEach(type => {
                const container = document.querySelector(`.chart-${type}`);
                const newContainer = doc.querySelector(`.chart-${type}`);
                if (container && newContainer) {
                    try {
                        container.innerHTML = newContainer.innerHTML;
                        updatedContainers++;
                        console.log(`成功更新图表容器: .chart-${type}`);
                    } catch (innerError) {
                        console.error(`更新图表容器 .chart-${type} 时出错:`, innerError);
                    }
                } else {
                    console.warn(`图表容器 .chart-${type} 未找到或新内容不存在`);
                }
            });
            
            console.log(`成功更新 ${updatedContainers} 个图表容器`);
            
            // 重新绑定图表点击事件
            try {
                this.bindChartClickEvents();
                console.log('图表点击事件重新绑定成功');
            } catch (bindError) {
                console.error('重新绑定图表点击事件时出错:', bindError);
            }
            
            // 重新初始化ECharts图表
            try {
                if (typeof window !== 'undefined' && typeof window.reinitEChartsCharts === 'function') {
                    console.log('使用window.reinitEChartsCharts重新初始化图表');
                    setTimeout(window.reinitEChartsCharts, 100);
                } else {
                    // 如果没有reinitEChartsCharts函数，手动重新初始化
                    console.log('手动重新初始化ECharts图表');
                    setTimeout(() => {
                        this.initEChartsChartsWithLazyLoad();
                    }, 100);
                }
                console.log('ECharts图表重新初始化计划已安排');
            } catch (initError) {
                console.error('重新初始化ECharts图表时出错:', initError);
            }
            
            console.log('图表区域更新完成');
        } catch (error) {
            console.error('更新图表内容时发生错误:', error);
            console.error('错误详情:', error.stack);
            this.showChartAreaError(`图表更新失败：${error.message}`);
        }
    }

    /**
     * 显示图表区域错误信息
     * @param {string} message - 错误信息
     */
    private showChartAreaError(message: string): void {
        console.error('显示图表区域错误:', message);
        
        // 显示友好的错误信息，而不是直接刷新页面
        const chartContainers = document.querySelectorAll('.chart-stacked, .chart-parallel, .chart-combined');
        if (chartContainers.length === 0) {
            console.warn('未找到图表容器，无法显示错误信息');
            return;
        }
        
        chartContainers.forEach(container => {
            container.innerHTML = `
                <div style="padding: 20px; text-align: center; color: red;">
                    <h5><i class="bi bi-exclamation-triangle me-2"></i>图表更新失败</h5>
                    <p>抱歉，更新图表内容时发生错误：</p>
                    <p class="text-muted">${message}</p>
                    <div class="mt-3 d-flex justify-content-center gap-2">
                        <button class="btn btn-primary" onclick="location.reload()">
                            <i class="bi bi-arrow-clockwise me-1"></i>重新加载页面
                        </button>
                        <button class="btn btn-outline-secondary" onclick="initAllChartFeatures('#chartSettingsForm')">
                            <i class="bi bi-chart-line me-1"></i>重新初始化图表
                        </button>
                    </div>
                </div>
            `;
        });
    }

    /**
     * 更新状态指示器
     * @param {string} phase - 阶段
     * @param {string} text - 文本
     * @param {number} progress - 进度
     * @param {string} details - 详情
     */
    updateStatusIndicator(phase: string, text: string, progress: number, details: string): void {
        const statusIndicator = document.querySelector('.chart-status-indicator');
        if (!statusIndicator) return;
        
        // 显示状态指示器
        statusIndicator.classList.remove('d-none');
        
        // 更新状态文本
        const statusText = document.getElementById('statusText');
        if (statusText) {
            statusText.textContent = text;
            statusText.className = 'text-primary';
        }
        
        // 更新进度条
        const statusProgress = document.getElementById('statusProgress');
        if (statusProgress) {
            statusProgress.style.width = `${progress}%`;
            statusProgress.setAttribute('aria-valuenow', progress.toString());
        }
        
        // 更新详细信息
        const statusDetails = document.getElementById('statusDetails');
        if (statusDetails) {
            statusDetails.innerHTML = details || '';
        }
        
        // 处理完成状态
        if (phase === 'completed') {
            const statusSpinner = document.getElementById('statusSpinner');
            if (statusSpinner) {
                statusSpinner.classList.remove('spinner-border', 'spinner-border-sm', 'text-primary');
                statusSpinner.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
            }
            if (statusText) {
                statusText.className = 'text-success';
            }
            if (statusProgress) {
                statusProgress.classList.remove('progress-bar-animated');
                statusProgress.classList.add('bg-success');
            }
        }
        
        // 处理错误状态
        if (phase === 'error') {
            const statusSpinner = document.getElementById('statusSpinner');
            if (statusSpinner) {
                statusSpinner.classList.remove('spinner-border', 'spinner-border-sm', 'text-primary');
                statusSpinner.innerHTML = '<i class="bi bi-x-circle-fill text-danger"></i>';
            }
            if (statusText) {
                statusText.className = 'text-danger';
            }
            if (statusProgress) {
                statusProgress.classList.remove('progress-bar-animated');
                statusProgress.classList.add('bg-danger');
            }
        }
    }

    /**
     * 显示加载指示器
     */
    showLoadingIndicator(): void {
        this.updateStatusIndicator('start', '准备更新图表设置...', 10, '正在收集当前设置...');
    }

    /**
     * 隐藏加载指示器
     */
    hideLoadingIndicator(): void {
        const statusIndicator = document.querySelector('.chart-status-indicator');
        if (statusIndicator) {
            // 延迟隐藏，让用户看到完成状态
            setTimeout(() => {
                statusIndicator.classList.add('d-none');
                
                // 重置状态指示器
                const statusSpinner = document.getElementById('statusSpinner');
                if (statusSpinner) {
                    statusSpinner.innerHTML = '';
                    statusSpinner.className = 'spinner-border spinner-border-sm text-primary me-2';
                    statusSpinner.setAttribute('role', 'status');
                }
                
                const statusProgress = document.getElementById('statusProgress');
                if (statusProgress) {
                    statusProgress.style.width = '0%';
                    statusProgress.classList.add('progress-bar-animated');
                    statusProgress.classList.remove('bg-success', 'bg-danger');
                }
            }, 2000);
        }
    }

    /**
     * 显示错误信息
     * @param {string} containerId - 容器ID
     * @param {string} message - 错误信息
     */
    showError(containerId: string, message: string): void {
        const container = document.getElementById(containerId);
        if (container) {
            container.classList.remove('loading');
            container.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                    <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem; margin-bottom: 10px;"></i>
                    <p class="text-danger text-center">${message}</p>
                </div>
            `;
        }
    }

    /**
     * 修复图表显示问题
     */
    fixChartDisplay(): void {
        // 此函数用于修复图表显示问题，保持与原页面调用的兼容性
        try {
            // 检查是否有需要修复的图表元素
            const chartElements = document.querySelectorAll('.chart-container, .chart-img');
            if (chartElements.length > 0) {
                // 可以在这里添加任何必要的图表显示修复逻辑
                console.log('图表显示修复函数已执行，检测到', chartElements.length, '个图表元素');
            }
            
            // 修复模态框显示问题
            const modal = document.getElementById('chartModal');
            const modalContent = modal ? modal.querySelector('.modal-content') : null;
            const modalBody = modal ? modal.querySelector('.modal-body') : null;
            const modalChartContainer = modal ? modal.querySelector('.modal-chart-container') : null;
            const chartContainer = modal ? modal.querySelector('#chartContainer') : null;
            
            console.log('模态框元素状态:', {
                modal: !!modal,
                modalContent: !!modalContent,
                modalBody: !!modalBody,
                modalChartContainer: !!modalChartContainer,
                chartContainer: !!chartContainer
            });
            
            // 确保模态框样式正确设置
            if (modal && modalContent && modalBody && modalChartContainer && chartContainer) {
                // 强制设置模态框相关元素的样式
                (modalContent as HTMLElement).style.display = 'flex';
                (modalContent as HTMLElement).style.flexDirection = 'column';
                (modalBody as HTMLElement).style.display = 'flex';
                (modalBody as HTMLElement).style.height = '100%';
                (modalBody as HTMLElement).style.overflow = 'hidden';
                (modalChartContainer as HTMLElement).style.display = 'flex';
                (modalChartContainer as HTMLElement).style.height = '100%';
                (modalChartContainer as HTMLElement).style.width = '100%';
                (modalChartContainer as HTMLElement).style.overflow = 'hidden';
                (chartContainer as HTMLElement).style.flex = '1';
                (chartContainer as HTMLElement).style.height = '100%';
                (chartContainer as HTMLElement).style.width = '100%';
                
                console.log('模态框样式已重置');
            }
        } catch (error) {
            console.error('执行图表显示修复时出错:', error);
        }
    }

    /**
     * 重试图表初始化
     * @param {string} containerId - 容器ID
     */
    retryChartInit(containerId: string): void {
        console.log(`开始重试初始化图表: ${containerId}`);
        
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`图表容器不存在: ${containerId}`);
            return;
        }
        
        // 显示加载状态
        container.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2 text-muted">图表加载中...</p>
                <p class="text-muted small">正在重试初始化，请稍候...</p>
            </div>
        `;
        
        // 延迟执行，确保加载状态显示
        setTimeout(() => {
            try {
                // 重新初始化图表
                this.initSingleEChartsChart(container);
                console.log(`重试初始化图表 ${containerId} 完成`);
            } catch (error) {
                console.error(`重试初始化图表 ${containerId} 失败:`, error);
                container.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                        <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <p class="text-danger text-center">图表初始化失败</p>
                        <p class="text-muted text-center small">${error.message}</p>
                        <button class="btn btn-sm btn-primary mt-2" onclick="retryChartInit('${containerId}')">
                            <i class="bi bi-arrow-repeat me-1"></i>重试
                        </button>
                    </div>
                `;
            }
        }, 500);
    }
}

// 导出全局函数
export function initAllChartFeatures(formSelector: string): void {
    const chartInitializer = new ChartInitializer();
    chartInitializer.initAllChartFeatures(formSelector);
}

export function fixChartDisplay(): void {
    const chartInitializer = new ChartInitializer();
    chartInitializer.fixChartDisplay();
}

export function retryChartInit(containerId: string): void {
    const chartInitializer = new ChartInitializer();
    chartInitializer.retryChartInit(containerId);
}

export function retryChartImageLoad(button: HTMLElement, imgUrl: string): void {
    // 显示加载状态
    button.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>加载中...';
    button.disabled = true;
    
    // 创建新的img元素
    const newImg = document.createElement('img');
    newImg.className = 'chart-img img-fluid';
    newImg.src = imgUrl;
    
    // 复制原始图片的所有data属性
    const errorContainer = button.closest('.chart-img-error');
    if (errorContainer) {
        const originalImg = errorContainer.previousElementSibling as HTMLImageElement;
        if (originalImg) {
            // 复制所有data-*属性
            const dataAttrs = originalImg.attributes;
            for (let i = 0; i < dataAttrs.length; i++) {
                const attr = dataAttrs[i];
                if (attr.name.startsWith('data-')) {
                    newImg.setAttribute(attr.name, attr.value);
                }
            }
        }
    }
    
    // 添加事件监听器
    newImg.addEventListener('load', function() {
        // 替换错误容器
        const errorContainer = button.closest('.chart-img-error');
        if (errorContainer) {
            errorContainer.parentNode?.replaceChild(this, errorContainer);
            // 重新绑定点击事件
            const chartInitializer = new ChartInitializer();
            chartInitializer.bindChartClickEvents();
        }
    });
    
    newImg.addEventListener('error', function() {
        // 恢复按钮状态
        button.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i>重试加载';
        button.disabled = false;
        // 显示更详细的错误信息
        const errorMsg = button.parentNode?.querySelector('.text-danger');
        if (errorMsg) {
            (errorMsg as HTMLElement).textContent = '重试加载失败，请检查网络连接或刷新页面';
        }
    });
    
    // 开始加载图片
    // 当设置src属性时，图片会自动开始加载
    console.log('开始重新加载图表图片:', imgUrl);
}
