// 文件上传进度条功能
class UploadProgress {
    constructor() {
        this.init();
    }

    init() {
        // 为文件输入元素添加事件监听器
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.handleFileSelect(e);
            });
        });

        // 支持拖放上传
        const uploadAreas = document.querySelectorAll('.upload-area');
        uploadAreas.forEach(area => {
            area.addEventListener('dragover', (e) => {
                this.handleDragOver(e, area);
            });

            area.addEventListener('dragleave', (e) => {
                this.handleDragLeave(e, area);
            });

            area.addEventListener('drop', (e) => {
                this.handleDrop(e, area);
            });
        });
    }

    handleFileSelect(event) {
        const fileInput = event.target;
        const fileNameDisplay = this.getFileNameDisplayElement(fileInput);
        const file = fileInput.files[0];

        if (file) {
            fileNameDisplay.innerHTML = `<i class="bi bi-check-circle me-1"></i>已选择：${file.name}`;
            // 添加进度条容器
            this.createProgressBar(fileInput, file);
        }
    }

    handleDragOver(event, area) {
        event.preventDefault();
        area.style.borderColor = '#0d6efd';
        area.style.backgroundColor = '#e7f1ff';
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
            if (file.name.match(/\.(csv|xlsx|xls)$/i)) {
                let fileInput, fileNameDisplay;
                if (area.contains(document.getElementById('p1_file'))) {
                    fileInput = document.getElementById('p1_file');
                    fileNameDisplay = document.getElementById('p1_file_name');
                } else if (area.contains(document.getElementById('p2_file'))) {
                    fileInput = document.getElementById('p2_file');
                    fileNameDisplay = document.getElementById('p2_file_name');
                } else if (area.contains(document.getElementById('st_file'))) {
                    fileInput = document.getElementById('st_file');
                    fileNameDisplay = document.getElementById('st_file_name');
                }

                if (fileInput && fileNameDisplay) {
                    fileInput.files = files;
                    fileNameDisplay.innerHTML = `<i class="bi bi-check-circle me-1"></i>已选择：${file.name}`;
                    this.createProgressBar(fileInput, file);
                }
            } else {
                alert('请上传CSV、XLS或XLSX格式的文件');
            }
        }
    }

    getFileNameDisplayElement(fileInput) {
        if (fileInput.id === 'p1_file') {
            return document.getElementById('p1_file_name');
        } else if (fileInput.id === 'p2_file') {
            return document.getElementById('p2_file_name');
        } else if (fileInput.id === 'st_file') {
            return document.getElementById('st_file_name');
        }
        return null;
    }

    createProgressBar(fileInput, file) {
        // 移除现有的进度条
        const existingProgress = fileInput.parentNode.querySelector('.upload-progress');
        if (existingProgress) {
            existingProgress.remove();
        }

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
        
        // 注意：由于这是表单提交而非AJAX上传，我们无法获取真实的上传进度
        // 所以这里使用一个合理的固定时间动画来模拟上传过程
        this.animateProgress(fileInput, file.size);
    }

    animateProgress(fileInput, fileSize) {
        const progressBar = fileInput.parentNode.querySelector('.progress-bar');
        if (!progressBar) return;
        
        // 根据文件大小估算上传时间（假设网络速度为 1MB/s）
        const estimatedTime = Math.min(Math.max(fileSize / (1024 * 1024), 1), 10) * 1000; // 1-10秒
        
        // 计算每100毫秒应该增加的进度百分比
        const steps = estimatedTime / 100;
        const increment = 100 / steps;
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += increment;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
            }
            this.updateProgress(fileInput, progress);
        }, 100);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    updateProgress(fileInput, percentage) {
        const progressBar = fileInput.parentNode.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = percentage + '%';
            progressBar.setAttribute('aria-valuenow', percentage);
            progressBar.querySelector('span').textContent = Math.round(percentage) + '%';
        }
    }
}

// 表单提交前验证
document.querySelector('form').addEventListener('submit', function(e) {
    // 检查是否是图表更新操作（通过检查是否存在chart_types字段）
    const chartTypes = document.querySelector('input[name="chart_types"]');
    const chartUpdate = document.querySelector('input[name="chart_update"]');
    
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
});

// 初始化上传进度功能
document.addEventListener('DOMContentLoaded', function() {
    new UploadProgress();
});