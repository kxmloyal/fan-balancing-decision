// 文件上传进度条功能
class UploadProgress {
    constructor() {
        this.fileNameMap = {
            'p1_file': 'p1_file_name',
            'p2_file': 'p2_file_name',
            'st_file': 'st_file_name'
        };
        this.init();
    }

    init() {
        // 为文件输入元素添加事件监听器
        document.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', (e) => this.handleFileSelect(e));
        });

        // 支持拖放上传
        document.querySelectorAll('.upload-area').forEach(area => {
            area.addEventListener('dragover', (e) => this.handleDragOver(e, area));
            area.addEventListener('dragleave', (e) => this.handleDragLeave(e, area));
            area.addEventListener('drop', (e) => this.handleDrop(e, area));
        });
    }

    /**
     * 公共文件处理函数
     * @param {HTMLInputElement} fileInput - 文件输入元素
     * @param {File} file - 文件对象
     */
    handleFile(fileInput, file) {
        const fileNameDisplay = document.getElementById(this.fileNameMap[fileInput.id]);

        if (file) {
            const ALLOWED_TYPES = [
                'text/csv',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ];
            const MAX_FILE_SIZE = 16 * 1024 * 1024;

            if (!ALLOWED_TYPES.includes(file.type) && !/\.(csv|xlsx|xls)$/i.test(file.name)) {
                const errorEl = document.getElementById(fileInput.id + '-error') ||
                    fileInput.parentElement.querySelector('.upload-error');
                if (errorEl) {
                    errorEl.textContent = '\u4e0d\u652f\u6301\u7684\u6587\u4ef6\u7c7b\u578b\uff0c\u4ec5\u652f\u6301 .csv/.xlsx/.xls \u6587\u4ef6';
                    errorEl.style.display = 'block';
                    setTimeout(function () { errorEl.style.display = 'none'; }, 5000);
                }
                fileInput.value = '';
                return;
            }

            if (file.size > MAX_FILE_SIZE) {
                const errorEl = document.getElementById(fileInput.id + '-error') ||
                    fileInput.parentElement.querySelector('.upload-error');
                if (errorEl) {
                    errorEl.textContent = '\u6587\u4ef6\u5927\u5c0f\u8d85\u8fc7 16MB \u4e0a\u9650';
                    errorEl.style.display = 'block';
                    setTimeout(function () { errorEl.style.display = 'none'; }, 5000);
                }
                fileInput.value = '';
                return;
            }

            fileNameDisplay.textContent = '\u2714 \u5df2\u9009\u62e9\uff1a' + file.name;
            this.createProgressBar(fileInput, file);
        }
    }

    handleFileSelect(event) {
        const fileInput = event.target;
        const file = fileInput.files[0];

        if (file) {
            this.handleFile(fileInput, file);
        }
    }

    handleDragOver(event, area) {
        event.preventDefault();
        area.style.borderColor = 'var(--primary-color)';
        area.style.backgroundColor = 'rgba(var(--primary-rgb), 0.06)';
    }

    handleDragLeave(event, area) {
        area.style.borderColor = '#ced4da';
        area.style.backgroundColor = '#ffffff';
    }

    handleDrop(event, area) {
        event.preventDefault();
        area.style.borderColor = '#ced4da';
        area.style.backgroundColor = '#ffffff';

        const files = event.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            const ALLOWED_TYPES = [
                'text/csv',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ];
            const MAX_FILE_SIZE = 16 * 1024 * 1024;

            const typeValid = ALLOWED_TYPES.includes(file.type) || /\.(csv|xlsx|xls)$/i.test(file.name);
            const sizeValid = file.size <= MAX_FILE_SIZE;

            if (typeValid && sizeValid) {
                const fileInput = area.querySelector('input[type="file"]');
                if (fileInput && this.fileNameMap[fileInput.id]) {
                    fileInput.files = files;
                    this.handleFile(fileInput, file);
                }
            } else {
                if (!typeValid) {
                    const errorEl = area.querySelector('.upload-error');
                    if (errorEl) {
                        errorEl.textContent = '\u4e0d\u652f\u6301\u7684\u6587\u4ef6\u7c7b\u578b\uff0c\u4ec5\u652f\u6301 .csv/.xlsx/.xls \u6587\u4ef6';
                        errorEl.style.display = 'block';
                        setTimeout(function () { errorEl.style.display = 'none'; }, 5000);
                    } else {
                        area.style.color = '#ef4444';
                        setTimeout(function () { area.style.color = ''; }, 2000);
                    }
                } else {
                    const errorEl = area.querySelector('.upload-error');
                    if (errorEl) {
                        errorEl.textContent = '\u6587\u4ef6\u5927\u5c0f\u8d85\u8fc7 16MB \u4e0a\u9650';
                        errorEl.style.display = 'block';
                        setTimeout(function () { errorEl.style.display = 'none'; }, 5000);
                    } else {
                        area.style.color = '#ef4444';
                        setTimeout(function () { area.style.color = ''; }, 2000);
                    }
                }
            }
        }
    }

    createProgressBar(fileInput, file) {
        // 移除现有的进度条
        const existingProgress = fileInput.parentNode.querySelector('.upload-progress');
        if (existingProgress) existingProgress.remove();

        // 创建新的进度条
        const progressContainer = document.createElement('div');
        progressContainer.className = 'upload-progress mt-2 show';
        progressContainer.innerHTML = `
            <div class="progress" style="height: 20px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 0%;" aria-valuenow="0" 
                     aria-valuemin="0" aria-valuemax="100">
                     <span class="small fw-bold">0%</span>
                </div>
            </div>
            <div class="text-muted small mt-1">
                <span class="file-size">${this.formatFileSize(file.size)}</span>
            </div>
        `;

        fileInput.parentNode.appendChild(progressContainer);
        
        // 使用固定时间动画模拟上传过程
        this.animateProgress(fileInput);
    }

    animateProgress(fileInput) {
        const progressBar = fileInput.parentNode.querySelector('.progress-bar');
        if (!progressBar) return;
        
        // 简化动画：3秒内完成从0到100%的进度
        const duration = 3000; // 3秒
        const startTime = performance.now();
        
        const updateProgress = () => {
            const elapsed = performance.now() - startTime;
            const progress = Math.min((elapsed / duration) * 100, 100);
            
            progressBar.style.width = progress + '%';
            progressBar.setAttribute('aria-valuenow', progress);
            progressBar.querySelector('span').textContent = Math.round(progress) + '%';
            
            if (progress < 100) {
                requestAnimationFrame(updateProgress);
            }
        };
        
        requestAnimationFrame(updateProgress);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// 表单提交前验证，为所有表单添加事件监听器
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            // 检查是否是图表设置表单
            if (this.id === 'chartSettingsForm') {
                // 图表设置表单由charts.js处理，此处不阻止默认行为
                return true;
            }
            
            // 检查是否是文件上传表单
            if (this.id === 'uploadForm') {
                // 检查是否是图表更新操作
                const chartTypes = this.querySelector('input[name="chart_types"]');
                const chartUpdate = this.querySelector('input[name="chart_update"]');
                
                if (chartTypes || chartUpdate) {
                    // 这是图表更新操作，不需要检查文件
                    return true;
                }
                
                // 这是文件上传操作，需要检查文件
                const p1File = document.getElementById('p1_file').files.length > 0;
                const p2File = document.getElementById('p2_file').files.length > 0;
                const stFile = document.getElementById('st_file').files.length > 0;

                if (!p1File && !p2File && !stFile) {
                    e.preventDefault();
                    alert('请至少上传一个面的数据文件');
                    return false;
                }
                
                // 显示上传进度条
                const uploadCardBody = document.getElementById('uploadCardBody');
                const uploadProgressFooter = document.getElementById('uploadProgressFooter');
                const uploadStatusFooter = document.getElementById('uploadStatusFooter');
                
                if (uploadCardBody && uploadProgressFooter) {
                    // 隐藏上传区域
                    uploadCardBody.classList.remove('show');
                    uploadCardBody.classList.add('collapse');
                    
                    // 隐藏上传状态提示
                    if (uploadStatusFooter) {
                        uploadStatusFooter.classList.add('d-none');
                    }
                    
                    // 显示上传进度条
                    uploadProgressFooter.classList.remove('d-none');
                }
            }
        });
    });
    
});

// 自动折叠上传区域功能
class AutoCollapseUpload {
    constructor() {
        this.init();
    }

    init() {
        // 监听文件选择事件
        this.bindFileEvents();
        
        // 监听折叠事件
        this.bindCollapseEvents();
        
        // 监听重新上传按钮事件
        this.bindReopenEvent();
        
        // 检查是否有已上传的文件
        this.checkExistingFiles();
        
        // 检查是否有分析结果，如果有，隐藏上传进度条
        this.checkAnalysisResults();
    }
    
    checkAnalysisResults() {
        // 检查是否有分析结果
        const hasAnalysisResults = document.querySelector('.mt-5');
        const uploadProgressFooter = document.getElementById('uploadProgressFooter');
        const uploadStatusFooter = document.getElementById('uploadStatusFooter');
        
        if (hasAnalysisResults && uploadProgressFooter) {
            // 隐藏上传进度条
            uploadProgressFooter.classList.add('d-none');
            
            // 显示上传状态提示
            if (uploadStatusFooter) {
                uploadStatusFooter.classList.remove('d-none');
            }
        }
    }

    bindFileEvents() {
        // 监听文件选择事件
        document.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', (e) => this.handleFileChange(e));
        });
    }

    bindCollapseEvents() {
        // 监听折叠状态变化事件
        const uploadCardBody = document.getElementById('uploadCardBody');
        const uploadCollapseIcon = document.getElementById('uploadCollapseIcon');
        const uploadCardHeader = document.getElementById('uploadCardHeader');
        
        if (uploadCardBody && uploadCollapseIcon) {
            uploadCardBody.addEventListener('show.bs.collapse', () => {
                uploadCollapseIcon.classList.remove('bi-chevron-down');
                uploadCollapseIcon.classList.add('bi-chevron-up');
            });
            
            uploadCardBody.addEventListener('hide.bs.collapse', () => {
                uploadCollapseIcon.classList.remove('bi-chevron-up');
                uploadCollapseIcon.classList.add('bi-chevron-down');
            });
        }
    }

    bindReopenEvent() {
        // 监听重新上传按钮事件
        const reopenUploadBtn = document.getElementById('reopenUploadBtn');
        if (reopenUploadBtn) {
            reopenUploadBtn.addEventListener('click', () => this.reopenUploadArea());
        }
    }

    handleFileChange(e) {
        // 文件选择后，检查是否所有文件都已选择
        setTimeout(() => {
            this.checkUploadComplete();
        }, 500);
    }

    checkUploadComplete() {
        // 检查是否有文件被选择
        const p1File = document.getElementById('p1_file').files.length > 0;
        const p2File = document.getElementById('p2_file').files.length > 0;
        const stFile = document.getElementById('st_file').files.length > 0;
        
        // 检查是否有至少一个文件被选择
        const hasFiles = p1File || p2File || stFile;
        
        // 如果有文件被选择，检查上传进度
        if (hasFiles) {
            // 检查所有上传进度是否已完成
            const progressBars = document.querySelectorAll('.upload-progress');
            const completeProgressBars = Array.from(progressBars).filter(bar => {
                const progressBar = bar.querySelector('.progress-bar');
                return progressBar && progressBar.style.width === '100%';
            });
            
            // 如果所有进度条都已完成，自动折叠上传区域
            if (completeProgressBars.length === progressBars.length) {
                this.collapseUploadArea();
            }
        }
    }

    checkExistingFiles() {
        // 检查页面加载时是否有已上传的文件（通过文件名显示）
        const fileNameDisplays = document.querySelectorAll('.file-name-display');
        const hasUploadedFiles = Array.from(fileNameDisplays).some(display => {
            return display.textContent.includes('已选择：');
        });
        
        // 如果有已上传的文件，自动折叠上传区域
        if (hasUploadedFiles) {
            this.collapseUploadArea();
        }
    }

    collapseUploadArea() {
        // 折叠上传区域
        const uploadCardBody = document.getElementById('uploadCardBody');
        const uploadStatusFooter = document.getElementById('uploadStatusFooter');
        const collapseButton = document.querySelector('[data-bs-target="#uploadCardBody"]');
        
        if (uploadCardBody && collapseButton) {
            // 触发折叠
            const bsCollapse = new bootstrap.Collapse(uploadCardBody, { toggle: false });
            bsCollapse.hide();
            
            // 显示上传状态提示
            if (uploadStatusFooter) {
                uploadStatusFooter.classList.remove('d-none');
            }
        }
    }

    reopenUploadArea() {
        // 重新展开上传区域
        const uploadCardBody = document.getElementById('uploadCardBody');
        const uploadStatusFooter = document.getElementById('uploadStatusFooter');
        
        if (uploadCardBody) {
            // 触发展开
            const bsCollapse = new bootstrap.Collapse(uploadCardBody, { toggle: false });
            bsCollapse.show();
            
            // 隐藏上传状态提示
            if (uploadStatusFooter) {
                uploadStatusFooter.classList.add('d-none');
            }
        }
    }
}

// AutoCollapseUpload初始化已合并到统一的DOMContentLoaded事件监听器中，此处不再重复初始化

// 重置功能集成
// 监听重置事件以更新上传区域
if (typeof window !== 'undefined' && window.addEventListener) {
    window.addEventListener('formReset', function(event) {
        // 当重置事件触发时，重新检查上传区域状态
        if (typeof autoCollapseUpload !== 'undefined') {
            autoCollapseUpload.checkExistingFiles();
        }
    });
}

// 统一的DOMContentLoaded事件监听器，确保所有功能都被正确初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化上传进度功能
    new UploadProgress();
    
    // 初始化自动折叠上传功能
    window.autoCollapseUpload = new AutoCollapseUpload();
    
});