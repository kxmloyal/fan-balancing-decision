// 页面初始化脚本

// 图表懒加载功能
function initChartLazyLoading() {
    // 定义图表容器选择器
    const chartContainers = document.querySelectorAll('.plotly-chart');
    
    // 直接初始化所有图表，不使用Intersection Observer
    chartContainers.forEach(container => {
        const chartId = container.getAttribute('id');
        if (chartId && typeof plotlyManager !== 'undefined') {
            try {
                const chartType = container.getAttribute('data-chart-type');
                const chartTitle = container.getAttribute('data-chart-title');
                const chartColor = container.getAttribute('data-chart-color');
                const chartDataRaw = container.getAttribute('data-chart-data');
                
                
                // 处理HTML实体编码
                const chartDataUnescaped = chartDataRaw.replace(/&quot;/g, '"').replace(/&amp;/g, '&');
                const chartData = JSON.parse(chartDataUnescaped);
                
                
                plotlyManager.initChart(chartId, chartType, chartData, {
                    title: chartTitle,
                    color: chartColor
                });
            } catch (error) {
                console.error('初始化图表失败:', error);
                console.error('图表数据:', container.getAttribute('data-chart-data'));
            }
        }
    });
}

// 初始化配色方案切换功能
function initColorSchemeSwitcher() {
    const colorSchemeRadios = document.querySelectorAll('input[name="colorScheme"]');
    
    // 从localStorage加载保存的配色方案
    try {
        const savedScheme = localStorage.getItem('selectedColorScheme');
        if (savedScheme) {
            const savedRadio = document.querySelector(`input[name="colorScheme"][value="${savedScheme}"]`);
            if (savedRadio) {
                savedRadio.checked = true;
            }
        }
    } catch (error) {
        console.error('加载保存的配色方案失败:', error);
    }
    
    colorSchemeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.checked && typeof plotlyManager !== 'undefined') {
                const schemeName = this.value;
                plotlyManager.setColorScheme(schemeName);
                
            }
        });
    });
}

// 初始化转速颜色选择组件
function initSpeedColorSelector() {
    // 检查是否存在转速颜色选择组件
    const speedColorContainer = document.getElementById('speedColorContainer');
    if (!speedColorContainer) {
        return;
    }
    
    // 获取当前配色方案的转速颜色
    if (typeof plotlyManager !== 'undefined') {
        const speedColors = plotlyManager.getSpeedColors();
        
        // 清空容器
        speedColorContainer.innerHTML = '';
        
        // 创建颜色选择器
        speedColors.forEach((color, index) => {
            const colorItem = document.createElement('div');
            colorItem.className = 'speed-color-item';
            colorItem.innerHTML = `
                <div class="color-preview" style="background-color: ${color}; width: 30px; height: 30px; border-radius: 50%; display: inline-block; margin-right: 10px;"></div>
                <input type="color" class="speed-color-input" value="${color}" data-index="${index}">
                <span class="color-label">转速 ${index + 1}</span>
            `;
            speedColorContainer.appendChild(colorItem);
        });
        
        // 添加颜色变更事件监听器
        const colorInputs = speedColorContainer.querySelectorAll('.speed-color-input');
        colorInputs.forEach(input => {
            input.addEventListener('change', function() {
                const index = parseInt(this.getAttribute('data-index'));
                const newColor = this.value;
                
                // 更新转速颜色
                if (typeof plotlyManager !== 'undefined') {
                    const currentScheme = plotlyManager.getCurrentColorScheme();
                    const colors = plotlyManager.getColorSchemeColors(currentScheme);
                    colors.speedColors[index] = newColor;
                    
                    // 重新渲染图表
                    plotlyManager.rerenderAllCharts();
                    
                }
            });
        });
    }
}

// 初始化页面时应用保存的配色方案
function applySavedColorScheme() {
    if (typeof plotlyManager !== 'undefined') {
        const currentScheme = plotlyManager.getCurrentColorScheme();
        plotlyManager.setColorScheme(currentScheme);
    }
}

// 初始化图表设置表单处理
function initChartSettingsForm() {
    const chartSettingsForm = document.getElementById('chartSettingsForm');
    const statusIndicator = document.querySelector('.chart-status-indicator');
    const statusText = document.getElementById('statusText');
    const statusProgress = document.getElementById('statusProgress');
    const statusDetails = document.getElementById('statusDetails');
    // 找到图表区域的容器，确保只更新图表区域
    let chartContainer = null;
    const chartStacked = document.querySelector('.chart-stacked');
    const chartParallel = document.querySelector('.chart-parallel');
    if (chartStacked) {
        chartContainer = chartStacked;
    } else if (chartParallel) {
        chartContainer = chartParallel;
    }
    
    // 从localStorage加载保存的图表类型选择
    function loadSavedChartSettings() {
        try {
            const savedTypes = localStorage.getItem('selectedChartTypes');
            const savedLayout = localStorage.getItem('selectedChartLayout');
            
            if (savedTypes) {
                const selectedTypes = JSON.parse(savedTypes);
                // 应用保存的图表类型选择
                const checkboxes = document.querySelectorAll('.chart-type-checkbox');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = selectedTypes.includes(checkbox.value);
                });
            }
            
            if (savedLayout) {
                // 应用保存的图表布局选择
                const layoutRadios = document.querySelectorAll('input[name="chartLayout"]');
                layoutRadios.forEach(radio => {
                    radio.checked = (radio.value === savedLayout);
                });
            }
        } catch (error) {
            console.error('加载保存的图表设置失败:', error);
        }
    }
    
    if (chartSettingsForm) {
        // 初始化默认设置，确保只有箱线图被勾选且图表布局选择堆叠显示
        const checkboxes = document.querySelectorAll('.chart-type-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = (checkbox.value === 'box');
        });
        
        const layoutRadios = document.querySelectorAll('input[name="chartLayout"]');
        layoutRadios.forEach(radio => {
            radio.checked = (radio.value === 'stacked');
        });
        
        // 保存默认设置到localStorage
        localStorage.setItem('selectedChartTypes', JSON.stringify(['box']));
        localStorage.setItem('selectedChartLayout', 'stacked');
        
        chartSettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 显示状态指示器
            if (statusIndicator) {
                statusIndicator.classList.remove('d-none');
            }
            
            // 更新状态文本
            if (statusText) {
                statusText.textContent = '正在处理图表设置...';
                statusText.className = 'text-primary';
            }
            
            // 更新进度条
            if (statusProgress) {
                statusProgress.style.width = '20%';
            }
            
            // 获取表单数据
            const selectedChartTypes = [];
            const chartTypeCheckboxes = document.querySelectorAll('.chart-type-checkbox:checked');
            
            chartTypeCheckboxes.forEach(checkbox => {
                selectedChartTypes.push(checkbox.value);
            });
            
            // 验证至少选择一个图表类型
            if (selectedChartTypes.length === 0) {
                if (statusText) {
                    statusText.textContent = '请至少选择一种图表类型';
                    statusText.className = 'text-danger';
                }
                if (statusProgress) {
                    statusProgress.style.width = '0%';
                }
                
                // 3秒后隐藏状态指示器
                setTimeout(() => {
                    if (statusIndicator) {
                        statusIndicator.classList.add('d-none');
                    }
                    if (statusText) {
                        statusText.className = 'text-primary';
                    }
                }, 3000);
                
                return;
            }
            
            // 构建AJAX请求数据
            const requestData = new FormData();
            requestData.append('csrf_token', document.querySelector('input[name="csrf_token"]').value);
            requestData.append('chart_update', 'true');
            requestData.append('chart_types', selectedChartTypes.join(','));
            
            // 获取并设置选中的图表布局
            const chartLayoutRadio = document.querySelector('input[name="chartLayout"]:checked');
            const selectedLayout = chartLayoutRadio ? chartLayoutRadio.value : 'stacked';
            requestData.append('chartLayout', selectedLayout);
            
            // 保存用户的图表类型选择到localStorage，确保刷新后保持选择状态
            localStorage.setItem('selectedChartTypes', JSON.stringify(selectedChartTypes));
            localStorage.setItem('selectedChartLayout', selectedLayout);
            
            
            // 模拟处理过程
            setTimeout(() => {
                if (statusProgress) {
                    statusProgress.style.width = '60%';
                }
                if (statusText) {
                    statusText.textContent = '正在更新图表...';
                }
                if (statusDetails) {
                    statusDetails.textContent = `正在处理 ${selectedChartTypes.length} 种图表类型...`;
                }
            }, 500);
            
            // 发送AJAX请求
            fetch(window.location.href, {
                method: 'POST',
                body: requestData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 更新进度条
                    if (statusProgress) {
                        statusProgress.style.width = '100%';
                    }
                    if (statusText) {
                        statusText.textContent = '图表设置更新成功！';
                        statusText.className = 'text-success';
                    }
                    if (statusDetails) {
                        statusDetails.textContent = '所有图表已按照新设置更新完成';
                    }
                    
                    // 更新图表区域
                    if (data.charts_html) {
                        // 保存当前滚动位置
                        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                        
                        // 找到分析结果区域的容器
                        const analysisResultSection = document.querySelector('.mt-5');
                        if (analysisResultSection) {
                            // 创建一个临时容器来解析HTML
                            const tempContainer = document.createElement('div');
                            tempContainer.innerHTML = data.charts_html;
                            
                            // 找到临时容器中的两个图表区域
                            const tempStackedArea = tempContainer.querySelector('.chart-stacked');
                            const tempParallelArea = tempContainer.querySelector('.chart-parallel');
                            
                            // 找到当前页面中的两个图表区域
                            const currentStackedArea = analysisResultSection.querySelector('.chart-stacked');
                            const currentParallelArea = analysisResultSection.querySelector('.chart-parallel');
                            
                            // 替换堆叠显示区域
                            if (tempStackedArea) {
                                if (currentStackedArea) {
                                    currentStackedArea.parentNode.replaceChild(tempStackedArea, currentStackedArea);
                                } else {
                                    // 如果当前页面中没有堆叠显示区域，则添加它
                                    analysisResultSection.appendChild(tempStackedArea);
                                }
                            }
                            
                            // 替换并列显示区域
                            if (tempParallelArea) {
                                if (currentParallelArea) {
                                    currentParallelArea.parentNode.replaceChild(tempParallelArea, currentParallelArea);
                                } else {
                                    // 如果当前页面中没有并列显示区域，则添加它
                                    analysisResultSection.appendChild(tempParallelArea);
                                }
                            }
                            
                            // 恢复滚动位置
                            window.scrollTo(0, scrollTop);
                            
                            // 重新初始化图表
                            if (typeof reinitPlotlyCharts === 'function') {
                                reinitPlotlyCharts();
                            }
                        } else {
                            console.error('未找到分析结果区域');
                        }
                    }
                    
                    // 3秒后隐藏状态指示器
                    setTimeout(() => {
                        if (statusIndicator) {
                            statusIndicator.classList.add('d-none');
                        }
                        if (statusText) {
                            statusText.className = 'text-primary';
                        }
                    }, 1500);
                } else {
                    // 处理错误
                    if (statusText) {
                        statusText.textContent = data.message || '图表更新失败';
                        statusText.className = 'text-danger';
                    }
                    if (statusProgress) {
                        statusProgress.style.width = '0%';
                    }
                    
                    // 3秒后隐藏状态指示器
                    setTimeout(() => {
                        if (statusIndicator) {
                            statusIndicator.classList.add('d-none');
                        }
                        if (statusText) {
                            statusText.className = 'text-primary';
                        }
                    }, 3000);
                }
            })
            .catch(error => {
                console.error('AJAX请求失败:', error);
                if (statusText) {
                    statusText.textContent = '网络错误，图表更新失败';
                    statusText.className = 'text-danger';
                }
                if (statusProgress) {
                    statusProgress.style.width = '0%';
                }
                
                // 3秒后隐藏状态指示器
                setTimeout(() => {
                    if (statusIndicator) {
                        statusIndicator.classList.add('d-none');
                    }
                    if (statusText) {
                        statusText.className = 'text-primary';
                    }
                }, 3000);
            });
        });
    }
}

// 监听图表类型选择变化，实时保存到localStorage
function initChartTypeSelectionListener() {
    // 等待DOM完全渲染
    setTimeout(() => {
        const checkboxes = document.querySelectorAll('.chart-type-checkbox');
        const layoutRadios = document.querySelectorAll('input[name="chartLayout"]');
        
        // 监听复选框变化
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const selectedChartTypes = [];
                checkboxes.forEach(cb => {
                    if (cb.checked) {
                        selectedChartTypes.push(cb.value);
                    }
                });
                localStorage.setItem('selectedChartTypes', JSON.stringify(selectedChartTypes));
            });
        });
        
        // 监听布局选择变化
        layoutRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.checked) {
                    localStorage.setItem('selectedChartLayout', this.value);
                }
            });
        });
    }, 200);
}

// 独立的loadSavedChartSettings函数，确保在任何情况下都会执行
function loadSavedChartSettings() {
    try {
        const savedTypes = localStorage.getItem('selectedChartTypes');
        const savedLayout = localStorage.getItem('selectedChartLayout');
        
        if (savedTypes) {
            const selectedTypes = JSON.parse(savedTypes);
            // 应用保存的图表类型选择
            const checkboxes = document.querySelectorAll('.chart-type-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectedTypes.includes(checkbox.value);
            });
        }
        
        if (savedLayout) {
            // 应用保存的图表布局选择
            const layoutRadios = document.querySelectorAll('input[name="chartLayout"]');
            layoutRadios.forEach(radio => {
                radio.checked = (radio.value === savedLayout);
            });
        }
    } catch (error) {
        console.error('加载保存的图表设置失败:', error);
    }
}

// 页面加载完成后初始化功能
document.addEventListener('DOMContentLoaded', function() {
    // 首先加载保存的图表设置
    setTimeout(loadSavedChartSettings, 100);
    
    // 滚动动画管理器会自动处理scroll-reveal元素的初始化
    
    // 配色方案切换功能
    initColorSchemeSwitcher();
    
    // 图表设置表单处理
    initChartSettingsForm();
    
    // 图表类型选择监听器
    initChartTypeSelectionListener();
    
    // 最优转速评估加载处理
    const collapseElement = document.getElementById('optimalSpeedEvaluation');
    if (collapseElement) {
        // 监听折叠事件
        collapseElement.addEventListener('show.bs.collapse', function () {
            // 这里可以添加加载状态处理
        });
    }
    
    // ====================== 上传模块自动折叠功能 ======================
    // 获取上传模块相关元素
    const uploadCardHeader = document.getElementById('uploadCardHeader');
    const uploadCardBody = document.getElementById('uploadCardBody');
    const uploadCollapseIcon = document.getElementById('uploadCollapseIcon');
    const uploadStatusFooter = document.getElementById('uploadStatusFooter');
    const reopenUploadBtn = document.getElementById('reopenUploadBtn');
    
    // 检查是否有分析结果
    const uploadFormElement = document.getElementById('uploadForm');
    const hasAnalysisResults = uploadFormElement && uploadFormElement.dataset.hasResults === 'true';
    
    // 从sessionStorage获取折叠状态，默认展开
    const isCollapsed = sessionStorage.getItem('uploadModuleCollapsed') === 'true';
    
    // 初始化上传模块状态
    if (hasAnalysisResults) {
        // 有分析结果时，检查是否需要自动折叠
        if (!isCollapsed) {
            // 如果还没有折叠状态记录，1秒后自动折叠
            setTimeout(() => {
                // 检查上传卡片是否可见
                if (uploadCardBody && uploadCardBody.classList.contains('show')) {
                    // 触发折叠
                    const collapse = new bootstrap.Collapse(uploadCardBody, { toggle: false });
                    collapse.hide();
                    // 更新图标
                    uploadCollapseIcon.classList.remove('bi-chevron-up');
                    uploadCollapseIcon.classList.add('bi-chevron-down');
                    // 保存状态到sessionStorage
                    sessionStorage.setItem('uploadModuleCollapsed', 'true');
                }
            }, 1000);
        } else {
            // 如果已经有折叠状态记录，保持折叠
            const collapse = new bootstrap.Collapse(uploadCardBody, { toggle: false });
            collapse.hide();
            // 更新图标
            uploadCollapseIcon.classList.remove('bi-chevron-up');
            uploadCollapseIcon.classList.add('bi-chevron-down');
        }
    }
    
    // 监听折叠事件，更新图标和状态
    uploadCardBody.addEventListener('hidden.bs.collapse', function () {
        uploadCollapseIcon.classList.remove('bi-chevron-up');
        uploadCollapseIcon.classList.add('bi-chevron-down');
        // 保存状态到sessionStorage
        sessionStorage.setItem('uploadModuleCollapsed', 'true');
    });
    
    uploadCardBody.addEventListener('shown.bs.collapse', function () {
        uploadCollapseIcon.classList.remove('bi-chevron-down');
        uploadCollapseIcon.classList.add('bi-chevron-up');
        // 保存状态到sessionStorage
        sessionStorage.setItem('uploadModuleCollapsed', 'false');
    });
    
    // 重新上传按钮点击事件
    if (reopenUploadBtn) {
        reopenUploadBtn.addEventListener('click', function () {
            const collapse = new bootstrap.Collapse(uploadCardBody, { toggle: true });
            collapse.show();
        });
    }
    
    // 重置按钮点击事件
    const resetButton = document.getElementById('resetButton');
    if (resetButton) {
        resetButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 检查是否需要确认
            if (confirm('确定要重置所有分析数据和表单输入吗？此操作将清除所有当前分析结果。')) {
                // 显示加载状态
                this.disabled = true;
                this.innerHTML = '<i class="bi bi-spinner bi-spin me-1"></i>重置中...';
                
                // 调用后端重置API
                fetch('/reset', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                    }
                })
                .then(response => response.ok ? response : Promise.reject(response))
                .then(() => {
                    // 重置成功后刷新页面
                    window.location.reload();
                })
                .catch(error => {
                    console.error('重置API调用失败:', error);
                    // 重置失败后恢复按钮状态
                    resetButton.disabled = false;
                    resetButton.innerHTML = '<i class="bi bi-arrow-counterclockwise me-1"></i>重置';
                    alert('重置失败，请稍后重试。');
                });
            }
        });
    } else {
        console.warn('未找到重置按钮');
    }
    
    // 初始化加载管理器
    setTimeout(() => {
        if (typeof window.loadingManager !== 'undefined') {
        }
    }, 500);
    
    // 为表单提交添加加载状态
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            if (typeof window.loadingManager !== 'undefined') {
                window.loadingManager.showPageLoading({
                    text: '分析数据中，请稍候...',
                    type: 'dots',
                    color: 'primary'
                });
            }
        });
    }
    
    // 应用保存的配色方案
    applySavedColorScheme();
    
    // 初始化转速颜色选择组件
    initSpeedColorSelector();
});
