/**
 * 模态框管理类 - 采用模块化设计模式，实现高内聚低耦合
 * @class ModalManager
 * @param {string} modalId - 模态框的ID
 */
class ModalManager {
    constructor(modalId) {
        this.modalId = modalId;
        this.modal = null;
        this.isFullscreen = false;
        this.currentChartSrc = null;
        
        // DOM元素缓存
        this.elements = {};
        
        // 初始化模态框
        this.init();
    }
    
    /**
     * 初始化模态框
     * @private
     */
    init() {
        this.modal = document.getElementById(this.modalId);
        if (!this.modal) {
            console.error(`未找到ID为${this.modalId}的模态框元素`);
            return;
        }
        
        // 缓存DOM元素
        this.cacheElements();
        
        // 绑定事件监听器
        this.bindEventListeners();
        
        // 初始化全屏按钮状态
        this.updateFullscreenButton();
    }
    
    /**
     * 缓存DOM元素，减少重复查询
     * @private
     */
    cacheElements() {
        this.elements = {
            fullscreenBtn: this.modal.querySelector('#fullscreenBtn'),
            chartContainer: this.modal.querySelector('#chartContainer'),
            modalDialog: this.modal.querySelector('.modal-dialog'),
            modalContent: this.modal.querySelector('.modal-content'),
            modalHeader: this.modal.querySelector('.modal-header'),
            modalBody: this.modal.querySelector('.modal-body'),
            modalFooter: this.modal.querySelector('.modal-footer'),
            modalChartContainer: this.modal.querySelector('.modal-chart-container')
        };
        
        // 提取常用元素到实例属性
        this.fullscreenBtn = this.elements.fullscreenBtn;
        this.chartContainer = this.elements.chartContainer;
    }
    
    /**
     * 绑定事件监听器
     * @private
     */
    bindEventListeners() {
        // 模态框显示前事件
        this.modal.addEventListener('show.bs.modal', (event) => this.handleModalShow(event));
        
        // 模态框完全显示后事件
        this.modal.addEventListener('shown.bs.modal', () => this.handleModalShown());
        
        // 模态框关闭时事件
        this.modal.addEventListener('hide.bs.modal', () => this.handleModalHide());
        
        // 全屏按钮点击事件
        if (this.fullscreenBtn) {
            this.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        }
        
        // 窗口大小变化事件
        window.addEventListener('resize', () => this.handleWindowResize());
    }
    
    /**
     * 处理模态框显示事件
     * @private
     * @param {Event} event - 模态框显示事件对象
     */
    handleModalShow(event) {
        const button = event.relatedTarget;
        if (!button) return;
        
        // 更新模态框标题
        const modalTitle = this.modal.querySelector('.modal-title');
        if (modalTitle) {
            modalTitle.textContent = button.getAttribute('data-chart-title') || '图表详情';
        }
        
        // 准备图表容器
        this.prepareChartContainer();
        
        // 获取图表HTML URL
        this.currentChartSrc = button.getAttribute('data-chart-src');
        if (!this.currentChartSrc) {
            console.error('未找到图表源URL');
            return;
        }
        
        // 延迟获取并渲染图表，确保模态框已经开始显示
        setTimeout(() => {
            this.fetchAndRenderChart(this.currentChartSrc);
        }, 100);
    }
    
    /**
     * 处理模态框完全显示事件
     * @private
     */
    handleModalShown() {
        console.log('模态框完全显示');
        
        // 确保图表容器样式正确
        this.ensureContainerStyles();
        
        // 调整图表大小
        this.resizeChart();
    }
    
    /**
     * 处理模态框关闭事件
     * @private
     */
    handleModalHide() {
        // 重置全屏状态
        this.resetFullscreen();
        
        // 释放资源，清理图表
        this.cleanupChart();
        
        // 重置当前图表源
        this.currentChartSrc = null;
    }
    
    /**
     * 准备图表容器
     * @private
     */
    prepareChartContainer() {
        if (!this.chartContainer) return;
        
        // 清理旧图表实例
        this.cleanupChart();
        
        // 清空容器，准备渲染新图表
        this.chartContainer.innerHTML = '';
    }
    
    /**
     * 清理图表资源
     * @private
     */
    cleanupChart() {
        if (!this.chartContainer) return;
        
        try {
            // 清空图表容器
            this.chartContainer.innerHTML = '';
        } catch (error) {
            console.error('销毁图表实例时出错:', error);
            // 确保容器被清空
            this.chartContainer.innerHTML = '';
        }
    }
    
    /**
     * 获取并渲染图表
     * @private
     * @param {string} chartUrl - 图表HTML的URL
     */
    fetchAndRenderChart(chartUrl) {
        if (!this.chartContainer) return;
        
        // 添加加载状态
        this.chartContainer.innerHTML = `
            <div style="padding: 20px; text-align: center;">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <br>正在加载图表...
            </div>
        `;
        
        // 发送GET请求获取图表HTML内容
        fetch(chartUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok: ${response.status} ${response.statusText}`);
                }
                return response.text();
            })
            .then(htmlContent => {
                // 渲染图表
                this.renderChart(htmlContent);
            })
            .catch(error => {
                console.error('获取图表数据时出错:', error);
                // 显示详细的错误信息
                this.chartContainer.innerHTML = `
                    <div style="padding: 20px; text-align: center; color: red;">
                        <h6 class="text-danger mb-2">图表加载失败</h6>
                        <p class="mb-3">错误信息：${error.message}</p>
                        <p class="text-muted" style="font-size: 0.9rem;">请求URL：${chartUrl}</p>
                        <button class="btn btn-sm btn-primary mt-2" onclick="location.reload()">
                            <i class="bi bi-arrow-clockwise me-1"></i>刷新页面重试
                        </button>
                    </div>
                `;
            });
    }
    
    /**
     * 渲染图表
     * @private
     * @param {string} htmlContent - 图表的HTML内容
     */
    renderChart(htmlContent) {
        if (!this.chartContainer) return;
        
        try {
            // 清空容器
            this.chartContainer.innerHTML = '';
            
            // 直接将HTML内容插入容器，确保所有脚本和样式都能正确加载
            this.chartContainer.innerHTML = htmlContent;
            
            // 确保容器样式正确
            this.ensureContainerStyles();
            
            // 查找所有脚本元素
            const scripts = this.chartContainer.querySelectorAll('script');
            
            // 重新执行所有脚本，确保图表能正确初始化
            scripts.forEach(script => {
                try {
                    // 创建新的脚本元素
                    const newScript = document.createElement('script');
                    
                    // 复制脚本的src或内容
                    if (script.src) {
                        newScript.src = script.src;
                    } else {
                        newScript.textContent = script.textContent;
                    }
                    
                    // 替换原脚本元素
                    script.parentNode.replaceChild(newScript, script);
                } catch (scriptError) {
                    console.warn('重新执行脚本时出错:', scriptError);
                }
            });
            
            // 延迟调整图表大小，确保图表已渲染完成
            setTimeout(() => {
                this.initialResizeChart();
            }, 500);
            
            console.log('图表已渲染');
        } catch (error) {
            console.error('处理图表HTML时出错:', error);
            // 显示友好的错误信息
            this.chartContainer.innerHTML = `
                <div style="padding: 20px; text-align: center; color: red;">
                    处理图表HTML失败：${error.message}
                </div>
            `;
        }
    }
    
    /**
     * 图表首次加载时调整大小
     * @private
     */
    initialResizeChart() {
        if (!this.chartContainer) return;
        
        try {
            // 首先确保所有容器样式正确
            this.ensureContainerStyles();
            

        } catch (e) {
            console.error('首次调整图表大小时出错:', e);
        }
    }
    
    /**
     * 确保容器样式正确
     * @private
     */
    ensureContainerStyles() {
        // 确保模态框dialog有正确的尺寸
        if (this.elements.modalDialog) {
            this.elements.modalDialog.style.height = this.isFullscreen ? '100vh' : '90vh';
            this.elements.modalDialog.style.width = this.isFullscreen ? '100vw' : '100vw';
            this.elements.modalDialog.style.maxWidth = this.isFullscreen ? 'none' : '100vw';
            this.elements.modalDialog.style.margin = this.isFullscreen ? '0' : '0 auto';
            this.elements.modalDialog.style.display = 'flex';
            this.elements.modalDialog.style.alignItems = 'stretch';
        }
        
        // 确保模态框内容区域使用flex布局
        if (this.elements.modalContent) {
            this.elements.modalContent.style.display = 'flex';
            this.elements.modalContent.style.flexDirection = 'column';
            this.elements.modalContent.style.flex = '1';
            this.elements.modalContent.style.maxHeight = '100%';
            this.elements.modalContent.style.minHeight = this.isFullscreen ? '100vh' : '80vh';
        }
        
        // 确保模态框header有正确的样式
        if (this.elements.modalHeader) {
            this.elements.modalHeader.style.flexShrink = '0';
        }
        
        // 确保模态框footer有正确的样式
        if (this.elements.modalFooter) {
            this.elements.modalFooter.style.flexShrink = '0';
        }
        
        // 确保模态框内容区域使用flex布局
        if (this.elements.modalBody) {
            this.elements.modalBody.style.overflow = 'hidden';
            this.elements.modalBody.style.display = 'flex';
            this.elements.modalBody.style.height = '100%';
            this.elements.modalBody.style.width = '100%';
            this.elements.modalBody.style.padding = '0';
            this.elements.modalBody.style.margin = '0';
            this.elements.modalBody.style.flex = '1';
        }
        
        if (this.elements.modalChartContainer) {
            this.elements.modalChartContainer.style.overflow = 'hidden';
            this.elements.modalChartContainer.style.display = 'flex';
            this.elements.modalChartContainer.style.height = '100%';
            this.elements.modalChartContainer.style.width = '100%';
            this.elements.modalChartContainer.style.padding = '0';
            this.elements.modalChartContainer.style.margin = '0';
            this.elements.modalChartContainer.style.flex = '1';
        }
        
        if (this.chartContainer) {
            // 确保图表容器样式正确
            this.chartContainer.style.height = '100%';
            this.chartContainer.style.width = '100%';
            this.chartContainer.style.flex = '1';
            this.chartContainer.style.display = 'flex';
            this.chartContainer.style.flexDirection = 'column';
            this.chartContainer.style.minHeight = '600px';
            
            // 确保内部的图表div也能正确显示
            const chartDivs = this.chartContainer.querySelectorAll('.chart-container, .plotly-container, .echarts-container');
            chartDivs.forEach(div => {
                div.style.height = '100%';
                div.style.width = '100%';
                div.style.minHeight = '600px';
            });
        }
    }
    
    /**
     * 调整图表大小（用户交互期间调用，不重置缩放状态）
     * @private
     */
    resizeChart() {
        if (!this.chartContainer) return;
        
        try {
            // 首先确保所有容器样式正确
            this.ensureContainerStyles();
            
            // 查找所有图表元素并调整大小
            try {
                if (typeof Plotly !== 'undefined') {
                    // 调整所有Plotly图表大小
                    const chartElements = this.chartContainer.querySelectorAll('[id]');
                    chartElements.forEach(element => {
                        try {
                            Plotly.relayout(element.id, {
                                width: element.clientWidth,
                                height: element.clientHeight
                            });
                        } catch (e) {
                            // 忽略不是Plotly图表的元素
                        }
                    });
                    console.log('图表大小已调整');
                }
            } catch (error) {
                console.warn('调整图表大小时出错:', error.message);
            }
        } catch (e) {
            console.error('调整图表大小时出错:', e);
        }
    }
    
    /**
     * 切换全屏状态
     * @public
     */
    toggleFullscreen() {
        this.isFullscreen = !this.isFullscreen;
        this.updateFullscreenClass();
        this.updateFullscreenButton();
        
        // 确保容器样式正确
        this.ensureContainerStyles();
        
        // 调整图表大小以适应新的全屏状态
        this.resizeChart();
        
        // 延迟一小段时间后，再次调整图表大小以确保正确显示
        // 这是因为模态框的CSS类变化可能需要时间才能完全应用
        setTimeout(() => {
            this.ensureContainerStyles();
            this.resizeChart();
        }, 100);
        
        // 再延迟更长时间，确保所有样式都已应用
        setTimeout(() => {
            this.ensureContainerStyles();
            this.resizeChart();
        }, 300);
    }
    
    /**
     * 更新全屏类
     * @private
     */
    updateFullscreenClass() {
        if (this.isFullscreen) {
            this.modal.classList.add('modal-fullscreen');
        } else {
            this.modal.classList.remove('modal-fullscreen');
        }
    }
    
    /**
     * 更新全屏按钮样式和文本
     * @private
     */
    updateFullscreenButton() {
        if (!this.fullscreenBtn) return;
        
        const icon = this.fullscreenBtn.querySelector('i');
        if (!icon) return;
        
        // 更新图标
        if (this.isFullscreen) {
            icon.classList.remove('bi-arrows-fullscreen');
            icon.classList.add('bi-arrows-minimize');
            this.fullscreenBtn.setAttribute('title', '退出全屏');
        } else {
            icon.classList.remove('bi-arrows-minimize');
            icon.classList.add('bi-arrows-fullscreen');
            this.fullscreenBtn.setAttribute('title', '全屏放大');
        }
    }
    
    /**
     * 重置全屏状态
     * @private
     */
    resetFullscreen() {
        if (this.isFullscreen) {
            this.isFullscreen = false;
            this.updateFullscreenClass();
            this.updateFullscreenButton();
        }
    }
    
    /**
     * 处理窗口大小变化
     * @private
     */
    handleWindowResize() {
        // 确保图表容器样式正确
        this.ensureContainerStyles();
        
        // 调整图表大小
        this.resizeChart();
    }
    
    /**
     * 销毁模态框，释放资源
     * @public
     */
    destroy() {
        // 移除事件监听器
        window.removeEventListener('resize', () => this.handleWindowResize());
        
        // 清理图表资源
        this.cleanupChart();
        
        // 重置所有属性
        this.modal = null;
        this.chartContainer = null;
        this.fullscreenBtn = null;
        this.elements = {};
    }
}

// 导出ModalManager类，以便其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModalManager;
} else if (typeof window !== 'undefined') {
    window.ModalManager = ModalManager;
}