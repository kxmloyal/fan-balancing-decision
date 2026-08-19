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
        this.eventsBound = false;
        this.boundHandlers = {};
        
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
        this.modalLabel = this.modal.querySelector('#chartModalLabel');
    }
    
    /**
     * 绑定事件监听器
     * @private
     */
    bindEventListeners() {
        if (this.eventsBound) return;
        this.eventsBound = true;
        
        this.boundHandlers.handleModalShow = (event) => this.handleModalShow(event);
        this.boundHandlers.handleModalShown = () => this.handleModalShown();
        this.boundHandlers.handleModalHide = () => this.handleModalHide();
        this.boundHandlers.handleWindowResize = () => this.handleWindowResize();
        this.boundHandlers.toggleFullscreen = () => this.toggleFullscreen();
        
        this.modal.addEventListener('show.bs.modal', this.boundHandlers.handleModalShow);
        this.modal.addEventListener('shown.bs.modal', this.boundHandlers.handleModalShown);
        this.modal.addEventListener('hide.bs.modal', this.boundHandlers.handleModalHide);
        
        if (this.fullscreenBtn) {
            this.fullscreenBtn.addEventListener('click', this.boundHandlers.toggleFullscreen);
        }
        
        window.addEventListener('resize', this.boundHandlers.handleWindowResize);
    }
    
    /**
     * 处理模态框显示事件
     * @private
     * @param {Event} event - 模态框显示事件对象
     */
    handleModalShow(event) {
        let button = event.relatedTarget;
        
        if (!button) {
            button = document.querySelector('.charts-container');
            if (!button) return;
        }
        
        const chartSrc = button.getAttribute('data-chart-src');
        const chartData = button.getAttribute('data-chart-data');
        const chartType = button.getAttribute('data-chart-type');
        
        if (!chartSrc && !chartData) return;
        
        const chartTitle = button.getAttribute('data-chart-title') || '图表详情';
        if (chartTitle) {
            this.modalLabel.textContent = chartTitle;
        }
        
        this.prepareChartContainer();
        
        if (chartData) {
            this.currentChartSrc = null;
            setTimeout(() => {
                this.renderPlotlyChart(chartData, chartType);
            }, 100);
        } else {
            this.currentChartSrc = chartSrc;
            setTimeout(() => {
                this.fetchAndRenderChart(this.currentChartSrc);
            }, 100);
        }
    }
    
    renderPlotlyChart(chartDataJson, chartType) {
        if (!this.chartContainer) return;
        
        try {
            var cleaned = chartDataJson
                .replace(/&#34;/g, '"')
                .replace(/&quot;/g, '"')
                .replace(/&amp;/g, '&');
            var data = JSON.parse(cleaned);
            
            var plotlyData, plotlyLayout;
            
            if (chartType && typeof plotlyManager !== 'undefined' && typeof plotlyManager.createPlotlyData === 'function') {
                plotlyData = plotlyManager.createPlotlyData(chartType, data, {});
                plotlyLayout = plotlyManager.createPlotlyLayout(chartType, { title: '', yAxisLabel: '不平衡量' });
            } else {
                plotlyData = data;
                plotlyLayout = {};
            }
            
            this.chartContainer.innerHTML = '';
            this.chartContainer.style.height = '';
            this.chartContainer.style.width = '';
            this.chartContainer.style.minHeight = '600px';
            this.chartContainer.style.display = 'flex';
            
            var innerDiv = document.createElement('div');
            innerDiv.id = 'modal-plotly-chart-' + Date.now();
            innerDiv.style.width = '100%';
            innerDiv.style.height = '100%';
            innerDiv.style.minHeight = '600px';
            this.chartContainer.appendChild(innerDiv);
            
            Plotly.newPlot(innerDiv, plotlyData, plotlyLayout, {
                responsive: true,
                scrollZoom: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['toImage', 'sendDataToCloud']
            });
            
            setTimeout(function() {
                try {
                    Plotly.Plots.resize(innerDiv);
                } catch (e) {}
            }, 300);

        } catch (error) {
            console.error('ModalManager: 渲染Plotly图表时出错:', error);
            this.chartContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--danger-color, #dc2626);">图表渲染失败：' + this._escapeHtml(error.message) + '</div>';
        }
    }
    
    /**
     * 处理模态框完全显示事件
     * @private
     */
    handleModalShown() {
        
        this.ensureContainerStyles();
        this.resizeChart();
    }
    
    /**
     * 处理模态框关闭事件
     * @private
     */
    handleModalHide() {
        this.resetFullscreen();
        document.body.style.overflow = '';
        this.cleanupChart();
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
            const plotElements = this.chartContainer.querySelectorAll('.js-plotly-plot, .plotly-graph-div, .plotly-chart');
            plotElements.forEach(el => {
                try {
                    if (typeof Plotly !== 'undefined' && el.id) {
                        Plotly.purge(el.id);
                    }
                } catch (e) {}
            });
            this.chartContainer.innerHTML = '';
        } catch (error) {
            console.error('销毁图表实例时出错:', error);
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
        
        this.chartContainer.innerHTML = '<div class="d-flex justify-content-center p-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
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
                this.chartContainer.innerHTML = `
                    <div style="padding: 20px; text-align: center; color: red;">
                        <h6 class="text-danger mb-2">图表加载失败</h6>
                        <p class="mb-3">错误信息：${this._escapeHtml(error.message)}</p>
                        <p class="text-muted" style="font-size: 0.9rem;">请求URL：${this._escapeHtml(chartUrl)}</p>
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
            
            // 移除 body 样式规则，防止污染页面
            const styleEl = this.chartContainer.querySelector('style');
            if (styleEl) {
                styleEl.textContent = styleEl.textContent.replace(/body\s*\{[^}]*\}/g, '');
            }
            
            // 查找所有脚本元素
            const scripts = this.chartContainer.querySelectorAll('script');
            
            // 重新执行所有脚本，确保图表能正确初始化
            scripts.forEach(script => {
                try {
                    // 跳过 Plotly 外部脚本（页面已加载）
                    if (script.src && script.src.includes('plotly')) {
                        script.remove();
                        return;
                    }
                    
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
            
            // 主动调用 renderChart：图表HTML使用 window.onload = renderChart，
            // 但HTML通过innerHTML插入modal时window已加载完毕，onload不会触发
            setTimeout(() => {
                var plotEls = this.chartContainer.querySelectorAll('.js-plotly-plot');
                if (plotEls.length === 0 && typeof renderChart === 'function') {
                    try {
                        renderChart();
                    } catch (e) {
                        console.error('ModalManager: renderChart执行失败:', e);
                    }
                }
            }, 80);
            
            setTimeout(() => {
                this.resizeChart();
            }, 300);
            
            setTimeout(() => {
                this.resizeChart();
            }, 800);
            
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
    resizePlotlyCharts() {
        this.resizeChart();
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
            const chartDivs = this.chartContainer.querySelectorAll('.chart-container, .plotly-container');
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
            this.ensureContainerStyles();
            
            if (typeof Plotly !== 'undefined') {
                const chartElements = this.chartContainer.querySelectorAll('.js-plotly-plot, .plotly-graph-div, .plotly-chart');
                chartElements.forEach(el => {
                    try {
                        Plotly.Plots.resize(el);
                    } catch (e1) {
                        try {
                            if (el.id) {
                                Plotly.relayout(el.id, {
                                    width: el.clientWidth,
                                    height: el.clientHeight
                                });
                            }
                        } catch (e2) {
                        }
                    }
                });
                if (chartElements.length === 0 && this.chartContainer) {
                    try {
                        Plotly.Plots.resize(this.chartContainer);
                    } catch (e3) {
                    }
                }
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
        
        document.body.style.overflow = this.isFullscreen ? 'hidden' : '';
        
        this.ensureContainerStyles();
        this.resizeChart();
        
        requestAnimationFrame(() => {
            this.ensureContainerStyles();
            this.resizeChart();
        });
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
        if (!this.modal) return;
        if (this._resizeDebounceTimer) {
            clearTimeout(this._resizeDebounceTimer);
        }
        this._resizeDebounceTimer = setTimeout(() => {
            if (!this.modal) return;
            this.ensureContainerStyles();
            this.resizeChart();
        }, 200);
    }
    
    /**
     * 销毁模态框，释放资源
     * @public
     */
    destroy() {
        if (this.eventsBound) {
            this.modal.removeEventListener('show.bs.modal', this.boundHandlers.handleModalShow);
            this.modal.removeEventListener('shown.bs.modal', this.boundHandlers.handleModalShown);
            this.modal.removeEventListener('hide.bs.modal', this.boundHandlers.handleModalHide);
            if (this.fullscreenBtn) {
                this.fullscreenBtn.removeEventListener('click', this.boundHandlers.toggleFullscreen);
            }
            window.removeEventListener('resize', this.boundHandlers.handleWindowResize);
            this.eventsBound = false;
        }
        
        this.cleanupChart();
        this.resetFullscreen();
        
        if (this._resizeDebounceTimer) {
            clearTimeout(this._resizeDebounceTimer);
            this._resizeDebounceTimer = null;
        }
        
        this.modal = null;
        this.chartContainer = null;
        this.fullscreenBtn = null;
        this.elements = {};
        this.boundHandlers = {};
    }

    _escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML;
    }
}

// 导出ModalManager类，以便其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModalManager;
} else if (typeof window !== 'undefined') {
    window.ModalManager = ModalManager;
}