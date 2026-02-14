// 重置功能管理器
class ResetManager {
    constructor() {
        this.init();
    }

    init() {
        // 初始化所有重置按钮
        this.initResetButtons();
    }

    /**
     * 初始化所有重置按钮
     */
    initResetButtons() {
        document.querySelectorAll('[data-reset="true"], .reset-button, #resetButton, #resetConnectionBtn').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleResetClick(button);
            });
        });
    }

    /**
     * 处理重置按钮点击事件
     * @param {HTMLElement} button - 点击的重置按钮
     */
    handleResetClick(button) {
        // 确定要重置的表单或区域
        const target = button.getAttribute('data-reset-target') || 'all';
        
        // 检查是否需要确认
        if (this.needsConfirmation(target)) {
            if (confirm('确定要重置所有输入内容吗？此操作不可撤销。')) {
                this.performReset(target, button);
            }
        } else {
            this.performReset(target, button);
        }
    }

    /**
     * 检查是否需要确认重置
     * @param {string} target - 重置目标
     * @returns {boolean} - 是否需要确认
     */
    needsConfirmation(target) {
        let hasSignificantInput = false;
        let inputCount = 0;
        
        const elements = target === 'all' ? 
            document.querySelectorAll('input, select, textarea') : 
            document.querySelectorAll(target + ' input, ' + target + ' select, ' + target + ' textarea');
        
        elements.forEach(element => {
            // 跳过禁用的元素
            if (element.disabled) return;
            
            // 检查是否有输入内容
            if (this.hasUserInput(element)) {
                inputCount++;
                // 如果有超过3个非空输入，认为是大量内容
                if (inputCount > 3) {
                    hasSignificantInput = true;
                    return false; // 跳出循环
                }
            }
        });
        
        return hasSignificantInput;
    }

    /**
     * 检查元素是否有用户输入
     * @param {HTMLElement} element - 表单元素
     * @returns {boolean} - 是否有用户输入
     */
    hasUserInput(element) {
        switch (element.type) {
            case 'text':
            case 'password':
            case 'email':
            case 'tel':
            case 'url':
            case 'number':
            case 'textarea':
                return element.value.trim() !== '';
            
            case 'checkbox':
            case 'radio':
                return element.checked;
            
            case 'select-one':
            case 'select-multiple':
                return element.value !== '' && element.value !== element.defaultValue;
            
            case 'file':
                return element.files.length > 0;
            
            default:
                return false;
        }
    }

    /**
     * 执行重置操作
     * @param {string} target - 重置目标
     * @param {HTMLElement} button - 点击的重置按钮
     */
    performReset(target, button) {
        // 添加视觉反馈
        this.addVisualFeedback(button);
        
        // 重置表单元素
        this.resetFormElements(target);
        
        // 重置验证状态
        this.resetValidationStates(target);
        
        // 重置文件输入
        this.resetFileInputs(target);
        
        // 重置上传区域
        this.resetUploadAreas(target);
        
        // 触发自定义重置事件
        this.triggerResetEvent(target);
    }

    /**
     * 添加视觉反馈
     * @param {HTMLElement} button - 点击的重置按钮
     */
    addVisualFeedback(button) {
        // 添加按钮动画效果
        button.classList.add('reset-button-active');
        
        // 添加表单高亮效果
        const form = button.closest('form') || document.querySelector('form');
        if (form) {
            form.classList.add('form-resetting');
        }
        
        // 1秒后移除动画类
        setTimeout(() => {
            button.classList.remove('reset-button-active');
            if (form) {
                form.classList.remove('form-resetting');
            }
        }, 1000);
    }

    /**
     * 重置表单元素
     * @param {string} target - 重置目标
     */
    resetFormElements(target) {
        if (target === 'all') {
            // 重置所有表单
            document.querySelectorAll('form').forEach(form => {
                // 跳过图表设置表单
                if (form.id !== 'chartSettingsForm') {
                    form.reset();
                }
            });
        } else {
            // 重置指定目标内的表单
            const form = document.querySelector(target) || document.querySelector(target + ' form');
            if (form) {
                form.reset();
            }
        }
    }

    /**
     * 重置验证状态
     * @param {string} target - 重置目标
     */
    resetValidationStates(target) {
        const selector = target === 'all' ? 
            '.error-message, .alert-danger, .invalid-feedback, .is-invalid' : 
            target + ' .error-message, ' + target + ' .alert-danger, ' + target + ' .invalid-feedback, ' + target + ' .is-invalid';
        
        // 移除错误消息
        document.querySelectorAll(selector).forEach(element => {
            if (element.classList.contains('is-invalid')) {
                element.classList.remove('is-invalid');
                element.classList.add('is-valid');
                setTimeout(() => {
                    element.classList.remove('is-valid');
                }, 1000);
            } else {
                element.remove();
            }
        });
    }

    /**
     * 重置文件输入
     * @param {string} target - 重置目标
     */
    resetFileInputs(target) {
        const selector = target === 'all' ? 'input[type="file"]' : target + ' input[type="file"]';
        
        document.querySelectorAll(selector).forEach(input => {
            input.value = '';
        });
    }

    /**
     * 重置上传区域
     * @param {string} target - 重置目标
     */
    resetUploadAreas(target) {
        // 清除文件名显示
        const selector = target === 'all' ? '.file-name-display' : target + ' .file-name-display';
        
        document.querySelectorAll(selector).forEach(display => {
            display.innerHTML = '';
        });
        
        // 清除进度条
        const progressSelector = target === 'all' ? '.upload-progress' : target + ' .upload-progress';
        
        document.querySelectorAll(progressSelector).forEach(bar => {
            bar.remove();
        });
        
        // 重置上传区域样式
        const areaSelector = target === 'all' ? '.upload-area' : target + ' .upload-area';
        
        document.querySelectorAll(areaSelector).forEach(area => {
            area.style.borderColor = '#ced4da';
            area.style.backgroundColor = '#ffffff';
        });
    }

    /**
     * 触发自定义重置事件
     * @param {string} target - 重置目标
     */
    triggerResetEvent(target) {
        const resetEvent = new CustomEvent('formReset', {
            detail: {
                target: target
            },
            bubbles: true,
            cancelable: true
        });
        
        document.dispatchEvent(resetEvent);
    }

    /**
     * 手动重置指定表单或区域
     * @param {string} target - 重置目标
     */
    reset(target = 'all') {
        this.performReset(target);
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ResetManager;
} else if (typeof window !== 'undefined') {
    window.ResetManager = ResetManager;
}

// 初始化重置管理器
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.ResetManager !== 'undefined') {
        window.resetManager = new ResetManager();
    }
});

// 添加重置按钮样式
const style = document.createElement('style');
style.textContent = `
    /* 重置按钮动画效果 */
    .reset-button-active {
        animation: resetPulse 1s ease-in-out;
    }
    
    /* 表单重置动画效果 */
    .form-resetting {
        animation: formHighlight 1s ease-in-out;
    }
    
    /* 重置按钮悬停效果 */
    [data-reset="true"], .reset-button {
        transition: all 0.3s ease;
    }
    
    [data-reset="true"]:hover, .reset-button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* 重置动画 */
    @keyframes resetPulse {
        0% {
            transform: scale(1);
            box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.7);
        }
        50% {
            transform: scale(1.05);
            box-shadow: 0 0 0 10px rgba(0, 123, 255, 0);
        }
        100% {
            transform: scale(1);
            box-shadow: 0 0 0 0 rgba(0, 123, 255, 0);
        }
    }
    
    /* 表单高亮动画 */
    @keyframes formHighlight {
        0% {
            background-color: transparent;
        }
        50% {
            background-color: rgba(0, 123, 255, 0.05);
        }
        100% {
            background-color: transparent;
        }
    }
`;
document.head.appendChild(style);
