// 图表功能初始化
function initAllChartFeatures(formSelector) {
    // 图表类型选择变化事件
    const chartTypeCheckboxes = document.querySelectorAll('.chart-type-checkbox');
    chartTypeCheckboxes.forEach(checkbox => {
        // 统一使用change事件处理图表类型变化
        checkbox.addEventListener('change', function(e) {
            // 阻止表单默认提交行为
            e.preventDefault();
            // 延迟一小段时间确保复选框状态已更新
            setTimeout(() => {
                updateChartSettings(formSelector);
            }, 10);
        });
    });
    
    // 图表布局选择变化事件
    const layoutRadios = document.querySelectorAll('input[name="chartLayout"]');
    layoutRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            toggleChartLayout(this.value);
            // 延迟一小段时间确保单选按钮状态已更新
            setTimeout(() => {
                updateChartSettings(formSelector);
            }, 10);
        });
    });

    // 图表模态框事件处理
    const chartModal = document.getElementById('chartModal');
    if (chartModal) {
        chartModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const chartSrc = button.getAttribute('data-chart-src');
            const chartTitle = button.getAttribute('data-chart-title');
            
            const modalTitle = chartModal.querySelector('.modal-title');
            const chartFrame = document.getElementById('chartFrame');
            
            modalTitle.textContent = chartTitle;
            chartFrame.src = chartSrc;
        });

        chartModal.addEventListener('hide.bs.modal', function (event) {
            const chartFrame = document.getElementById('chartFrame');
            chartFrame.src = '';
        });
    }

    // 组合图表应用按钮事件
    const applyCombinedChartBtn = document.getElementById('applyCombinedChart');
    if (applyCombinedChartBtn) {
        applyCombinedChartBtn.addEventListener('click', function() {
            generateCombinedChart();
        });
    }

    // 组合图表类型选择变化事件
    const combinedChartTypes = document.querySelectorAll('.combined-chart-type');
    combinedChartTypes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // 检查是否至少选择了一种图表类型
            const checkedTypes = document.querySelectorAll('.combined-chart-type:checked');
            if (checkedTypes.length === 0) {
                alert('请至少选择一种图表类型');
                this.checked = true; // 强制选中
            }
            // 实时更新组合图表
            // 延迟一小段时间确保复选框状态已更新
            setTimeout(() => {
                generateCombinedChart();
            }, 10);
        });
    });

    // 初始化图表布局显示
    const activeLayout = document.querySelector('input[name="chartLayout"]:checked');
    if (activeLayout) {
        toggleChartLayout(activeLayout.value);
    }
    
    // 为图表图片绑定点击事件
    bindChartClickEvents();
}

// 切换图表布局显示
function toggleChartLayout(layout) {
    const stackedContainer = document.querySelector('.chart-stacked');
    const parallelContainer = document.querySelector('.chart-parallel');
    const combinedContainer = document.querySelector('.chart-combined');
    
    // 先全部隐藏
    if (stackedContainer) stackedContainer.classList.add('d-none');
    if (parallelContainer) parallelContainer.classList.add('d-none');
    if (combinedContainer) combinedContainer.classList.add('d-none');
    
    // 再显示选中的
    if (layout === 'parallel') {
        if (parallelContainer) parallelContainer.classList.remove('d-none');
    } else if (layout === 'combined') {
        if (combinedContainer) combinedContainer.classList.remove('d-none');
    } else {
        if (stackedContainer) stackedContainer.classList.remove('d-none');
    }
    
    // 重新绑定图表点击事件
    setTimeout(bindChartClickEvents, 100);
}

// 更新图表设置
function updateChartSettings(formSelector) {
    const form = document.querySelector(formSelector);
    if (!form) return;

    // 收集选中的图表类型
    const selectedTypes = [];
    document.querySelectorAll('.chart-type-checkbox:checked').forEach(checkbox => {
        selectedTypes.push(checkbox.value);
    });

    // 如果没有选择任何图表类型，则默认选择箱线图
    if (selectedTypes.length === 0) {
        selectedTypes.push('box');
        // 确保箱线图复选框被选中
        const boxCheckbox = document.querySelector('.chart-type-checkbox[value="box"]');
        if (boxCheckbox) {
            boxCheckbox.checked = true;
        }
    }

    // 获取当前布局设置
    const layoutElement = document.querySelector('input[name="chartLayout"]:checked');
    const layout = layoutElement ? layoutElement.value : 'stacked';

    // 准备发送的数据
    const formData = new FormData(form);
    formData.set('chart_types', selectedTypes.join(','));
    formData.set('chartLayout', layout);
    formData.set('chart_update', 'true');

    // 显示加载指示器
    showLoadingIndicator();

    // 发送AJAX请求更新图表
    fetch(window.location.href, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        // 检查响应状态
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        // 检查响应是否为JSON格式
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            // 如果不是JSON响应，可能是重定向或其他问题
            throw new Error('服务器返回非JSON响应');
        }
    })
    .then(data => {
        if (data.success) {
            // 更新图表区域内容而不是刷新整个页面
            updateChartArea(data);
            
            // 更新图表类型选择框的状态
            if (data.chart_types) {
                // 取消所有已选择的复选框
                document.querySelectorAll('.chart-type-checkbox').forEach(cb => {
                    cb.checked = false;
                });
                
                // 根据返回的数据选中相应的复选框
                data.chart_types.forEach(type => {
                    const checkbox = document.querySelector('.chart-type-checkbox[value="'+type+'"]');
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                });
            }
            
            // 更新布局选择
            if (data.chart_layout) {
                const layoutRadio = document.querySelector('input[name="chartLayout"][value="'+data.chart_layout+'"]');
                if (layoutRadio) {
                    layoutRadio.checked = true;
                    toggleChartLayout(data.chart_layout);
                }
            }
        } else {
            alert('图表更新失败: ' + data.message);
            hideLoadingIndicator(); // 确保隐藏加载指示器
        }
    })
    .catch(error => {
        console.error('Error:', error);
        let errorMessage = '更新图表时发生错误';
        if (error && error.message) {
            errorMessage += ': ' + error.message;
        } else if (error) {
            errorMessage += ': ' + error;
        }
        alert(errorMessage);
        hideLoadingIndicator(); // 确保隐藏加载指示器
    });
}

// 直接更新图表区域内容，避免二次请求
function updateChartAreaDirectly(data) {
    // 隐藏加载指示器
    hideLoadingIndicator();
    
    // 重新加载页面以确保数据一致性
    location.reload();
}

// 生成组合图表
function generateCombinedChart() {
    // 收集选中的图表类型
    const selectedTypes = [];
    document.querySelectorAll('.combined-chart-type:checked').forEach(checkbox => {
        selectedTypes.push(checkbox.value);
    });

    // 检查是否选择了至少一种图表类型
    if (selectedTypes.length === 0) {
        // 如果没有选择任何类型，默认选择趋势图
        selectedTypes.push('trend');
        // 确保对应的复选框被选中
        const trendCheckbox = document.getElementById('combinedTrendChart');
        if (trendCheckbox) {
            trendCheckbox.checked = true;
        }
    }

    // 获取其他设置
    const combineFaces = document.getElementById('combineAllFaces').checked;

    // 准备发送的数据
    const requestData = {
        chart_types: selectedTypes,
        combine_faces: combineFaces,
        enable_linkage: false // 暂时不启用联动
    };

    // 显示加载指示器
    showLoadingIndicator();

    // 发送AJAX请求生成组合图表
    fetch('/generate_combined_chart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        // 检查响应状态
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 更新组合图表区域，不刷新整个页面
            updateCombinedChartArea(data);
        } else {
            alert('生成组合图表失败: ' + data.message);
            hideLoadingIndicator(); // 确保隐藏加载指示器
        }
    })
    .catch(error => {
        console.error('Error:', error);
        let errorMessage = '生成组合图表时发生错误';
        if (error && error.message) {
            errorMessage += ': ' + error.message;
        } else if (error) {
            errorMessage += ': ' + error;
        }
        alert(errorMessage);
        hideLoadingIndicator(); // 确保隐藏加载指示器
    });
}

// 更新图表区域内容
function updateChartArea(data) {
    // 通过AJAX获取更新后的图表内容
    fetch(window.location.href, {
        method: 'GET'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.text();
    })
    .then(html => {
        // 创建临时DOM元素来解析返回的HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // 获取当前显示的图表容器类型
        const stackedContainer = document.querySelector('.chart-stacked');
        const parallelContainer = document.querySelector('.chart-parallel');
        const combinedContainer = document.querySelector('.chart-combined');
        
        // 根据当前布局更新相应的内容
        if (stackedContainer && !stackedContainer.classList.contains('d-none')) {
            const newStackedContainer = doc.querySelector('.chart-stacked');
            if (newStackedContainer) {
                stackedContainer.innerHTML = newStackedContainer.innerHTML;
            }
        } else if (parallelContainer && !parallelContainer.classList.contains('d-none')) {
            const newParallelContainer = doc.querySelector('.chart-parallel');
            if (newParallelContainer) {
                parallelContainer.innerHTML = newParallelContainer.innerHTML;
            }
        } else if (combinedContainer && !combinedContainer.classList.contains('d-none')) {
            const newCombinedContainer = doc.querySelector('.chart-combined');
            if (newCombinedContainer) {
                combinedContainer.innerHTML = newCombinedContainer.innerHTML;
            }
        }
        
        // 重新绑定图表点击事件
        bindChartClickEvents();
        // 隐藏加载指示器
        hideLoadingIndicator();
    })
    .catch(error => {
        console.error('Error fetching updated content:', error);
        hideLoadingIndicator(); // 确保隐藏加载指示器
        location.reload(); // 出错时刷新页面
    });
}

// 更新组合图表区域
function updateCombinedChartArea(data) {
    // 通过AJAX获取更新后的组合图表内容
    fetch('/get_combined_chart', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.text();
    })
    .then(html => {
        // 创建临时DOM元素来解析返回的HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // 获取新的组合图表区域
        const newCombinedChartContainer = doc.querySelector('.combined-chart-container');
        if (newCombinedChartContainer) {
            // 替换当前的组合图表容器内容
            const currentCombinedChartContainer = document.querySelector('.chart-combined .combined-chart-container');
            if (currentCombinedChartContainer) {
                currentCombinedChartContainer.innerHTML = newCombinedChartContainer.innerHTML;
                // 重新绑定图表点击事件
                bindChartClickEvents();
            }
        }
        // 隐藏加载指示器
        hideLoadingIndicator();
    })
    .catch(error => {
        console.error('Error fetching updated combined chart content:', error);
        hideLoadingIndicator(); // 确保隐藏加载指示器
        location.reload(); // 出错时刷新页面
    });
}

// 显示加载指示器
function showLoadingIndicator() {
    const loadingIndicator = document.querySelector('.chart-loading');
    if (loadingIndicator) {
        loadingIndicator.classList.add('show');
    }
}

// 隐藏加载指示器
function hideLoadingIndicator() {
    const loadingIndicator = document.querySelector('.chart-loading');
    if (loadingIndicator) {
        loadingIndicator.classList.remove('show');
    }
}

// 为图表图片绑定点击事件
function bindChartClickEvents() {
    const chartImages = document.querySelectorAll('.chart-img');
    chartImages.forEach(img => {
        // 确保图片有必要的属性
        if (!img.hasAttribute('data-bs-toggle')) {
            img.setAttribute('data-bs-toggle', 'modal');
            img.setAttribute('data-bs-target', '#chartModal');
        }
        
        // 确保图片有点击事件监听器
        if (!img.hasAttribute('data-listener-added')) {
            img.addEventListener('click', function() {
                const chartSrc = this.getAttribute('data-chart-src');
                const chartTitle = this.getAttribute('data-chart-title');
                
                if (chartSrc && chartTitle) {
                    const chartModal = document.getElementById('chartModal');
                    if (chartModal) {
                        const modalTitle = chartModal.querySelector('.modal-title');
                        const chartFrame = document.getElementById('chartFrame');
                        
                        if (modalTitle && chartFrame) {
                            modalTitle.textContent = chartTitle;
                            chartFrame.src = chartSrc;
                        }
                    }
                }
            });
            
            // 标记已添加监听器，防止重复添加
            img.setAttribute('data-listener-added', 'true');
        }
    });
}