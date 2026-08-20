// 新手引导功能模块
class GuideManager {
    constructor() {
        this.currentStep = 0;
        this.steps = [];
        this.isActive = false;
        this.guideElement = null;
        this.backdropElement = null;
        this.progressElement = null;
        this.stepContentElement = null;
        this.navigationElement = null;
    }

    // 初始化引导
    init() {
        // 检查是否需要显示引导
        if (!this.shouldShowGuide()) {
            return;
        }

        // 定义引导步骤
        this.defineSteps();

        // 创建引导元素
        this.createGuideElements();

        // 显示引导
        this.startGuide();
    }

    // 检查是否应该显示引导
    shouldShowGuide() {
        // 检查localStorage中是否有引导完成记录
        const guideCompleted = localStorage.getItem('guideCompleted');
        return !guideCompleted;
    }

    // 定义引导步骤
    defineSteps() {
        this.steps = [
            {
                id: 'welcome',
                title: '欢迎使用扇叶平衡补土转速评估工具',
                content: '本工具可以帮助您分析扇叶在不同转速下的平衡状态，找到最优补土转速。',
                position: 'center',
                element: null
            },
            {
                id: 'fan-model',
                title: '扇叶型号',
                content: '请输入测试数据对应的扇叶型号，这将显示在生成的报告中作为副标题。',
                position: 'bottom',
                element: '#fan_model'
            },
            {
                id: 'upload-p1',
                title: 'P1面数据上传',
                content: '上传P1面的测试数据文件，支持CSV、XLSX、XLS格式。',
                position: 'right',
                element: '#p1_upload_area'
            },
            {
                id: 'upload-p2',
                title: 'P2面数据上传',
                content: '上传P2面的测试数据文件，支持CSV、XLSX、XLS格式。',
                position: 'right',
                element: '#p2_upload_area'
            },
            {
                id: 'upload-st',
                title: 'ST面数据上传（可选）',
                content: '可选上传ST面的测试数据文件，支持CSV、XLSX、XLS格式。',
                position: 'right',
                element: '#st_upload_area'
            },
            {
                id: 'start-analysis',
                title: '开始分析',
                content: '点击"开始分析"按钮，系统将处理上传的数据并生成分析结果。',
                position: 'top',
                element: 'button[type="submit"]'
            },
            {
                id: 'chart-settings',
                title: '图表设置',
                content: '分析完成后，您可以在这里选择不同的图表类型和布局方式。',
                position: 'top',
                element: '#chartSettingsForm'
            },
            {
                id: 'export-report',
                title: '导出报告',
                content: '分析完成后，您可以将结果导出为HTML、PDF、CSV等多种格式。',
                position: 'top',
                element: '.js-export-link'
            },
            {
                id: 'dashboard',
                title: '数据仪表盘',
                content: '点击导航栏中的"仪表盘"，查看系统的关键指标和分析趋势。',
                position: 'bottom',
                element: 'a[href*="dashboard"]'
            },
            {
                id: 'complete',
                title: '引导完成',
                content: '您已经了解了本工具的主要功能和使用流程。现在开始您的分析工作吧！',
                position: 'center',
                element: null
            }
        ];
    }

    // 创建引导元素
    createGuideElements() {
        // 创建背景遮罩
        this.backdropElement = document.createElement('div');
        this.backdropElement.className = 'guide-backdrop';
        this.backdropElement.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 99998;
        `;

        // 创建引导容器
        this.guideElement = document.createElement('div');
        this.guideElement.className = 'guide-container';
        this.guideElement.style.cssText = `
            position: fixed;
            z-index: 99999;
            max-width: 400px;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            padding: 24px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        `;

        // 创建引导内容
        const contentHTML = `
            <div class="guide-progress mb-4">
                <div class="progress" style="height: 6px; border-radius: 3px;">
                    <div class="progress-bar bg-primary" role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
                </div>
                <div class="text-right mt-1 text-sm text-muted">
                    <span class="guide-step-current">1</span>/<span class="guide-step-total">${this.steps.length}</span>
                </div>
            </div>
            <h3 class="guide-title mb-3" style="color: #3498db; font-weight: bold;"></h3>
            <div class="guide-content mb-4"></div>
            <div class="guide-navigation d-flex justify-content-between">
                <button class="btn btn-secondary btn-sm" id="guide-prev" disabled>
                    <i class="bi bi-arrow-left me-1"></i> 上一步
                </button>
                <div>
                    <button class="btn btn-outline-secondary btn-sm me-2" id="guide-skip">
                        <i class="bi bi-x me-1"></i> 跳过
                    </button>
                    <button class="btn btn-primary btn-sm" id="guide-next">
                        下一步 <i class="bi bi-arrow-right ms-1"></i>
                    </button>
                </div>
            </div>
        `;

        this.guideElement.innerHTML = contentHTML;

        // 获取元素引用
        this.progressElement = this.guideElement.querySelector('.progress-bar');
        this.stepContentElement = this.guideElement.querySelector('.guide-content');
        this.navigationElement = this.guideElement.querySelector('.guide-navigation');

        // 添加事件监听
        this.addEventListeners();

        // 添加到页面
        document.body.appendChild(this.backdropElement);
        document.body.appendChild(this.guideElement);
    }

    // 添加事件监听
    addEventListeners() {
        // 上一步按钮
        this.guideElement.querySelector('#guide-prev').addEventListener('click', () => {
            this.prevStep();
        });

        // 下一步按钮
        this.guideElement.querySelector('#guide-next').addEventListener('click', () => {
            this.nextStep();
        });

        // 跳过按钮
        this.guideElement.querySelector('#guide-skip').addEventListener('click', () => {
            this.completeGuide();
        });

        // 背景点击
        this.backdropElement.addEventListener('click', () => {
            // 可以添加点击背景关闭引导的功能
        });
    }

    // 开始引导
    startGuide() {
        this.isActive = true;
        this.currentStep = 0;
        this.updateStep();
    }

    // 更新当前步骤
    updateStep() {
        const currentStep = this.steps[this.currentStep];

        // 更新进度条
        const progress = ((this.currentStep + 1) / this.steps.length) * 100;
        this.progressElement.style.width = `${progress}%`;
        this.progressElement.setAttribute('aria-valuenow', progress);

        // 更新步骤计数
        this.guideElement.querySelector('.guide-step-current').textContent = this.currentStep + 1;

        // 更新标题和内容
        this.guideElement.querySelector('.guide-title').textContent = currentStep.title;
        this.stepContentElement.textContent = currentStep.content;

        // 更新按钮状态
        const prevButton = this.guideElement.querySelector('#guide-prev');
        const nextButton = this.guideElement.querySelector('#guide-next');
        const skipButton = this.guideElement.querySelector('#guide-skip');

        prevButton.disabled = this.currentStep === 0;
        nextButton.textContent = this.currentStep === this.steps.length - 1 ? '完成' : '下一步 <i class="bi bi-arrow-right ms-1"></i>';
        nextButton.innerHTML = this.currentStep === this.steps.length - 1 ? '完成' : '下一步 <i class="bi bi-arrow-right ms-1"></i>';
        skipButton.style.display = this.currentStep === this.steps.length - 1 ? 'none' : 'inline-block';

        // 定位引导元素
        this.positionGuide(currentStep);
    }

    // 定位引导元素
    positionGuide(step) {
        if (step.element) {
            const targetElement = document.querySelector(step.element);
            if (targetElement) {
                // 高亮目标元素
                this.highlightElement(targetElement);

                // 计算位置
                const rect = targetElement.getBoundingClientRect();
                const guideRect = this.guideElement.getBoundingClientRect();

                let left, top;

                switch (step.position) {
                    case 'top':
                        left = rect.left + (rect.width - guideRect.width) / 2;
                        top = rect.top - guideRect.height - 20;
                        break;
                    case 'bottom':
                        left = rect.left + (rect.width - guideRect.width) / 2;
                        top = rect.bottom + 20;
                        break;
                    case 'left':
                        left = rect.left - guideRect.width - 20;
                        top = rect.top + (rect.height - guideRect.height) / 2;
                        break;
                    case 'right':
                        left = rect.right + 20;
                        top = rect.top + (rect.height - guideRect.height) / 2;
                        break;
                    default:
                        left = (window.innerWidth - guideRect.width) / 2;
                        top = (window.innerHeight - guideRect.height) / 2;
                }

                // 调整位置，确保不超出视口
                left = Math.max(20, Math.min(left, window.innerWidth - guideRect.width - 20));
                top = Math.max(20, Math.min(top, window.innerHeight - guideRect.height - 20));

                this.guideElement.style.left = `${left}px`;
                this.guideElement.style.top = `${top}px`;
                this.guideElement.style.transform = 'none';
            } else {
                // 如果目标元素不存在，居中显示
                this.centerGuide();
            }
        } else {
            // 居中显示
            this.centerGuide();
        }
    }

    // 居中显示引导
    centerGuide() {
        this.guideElement.style.left = '50%';
        this.guideElement.style.top = '50%';
        this.guideElement.style.transform = 'translate(-50%, -50%)';
    }

    // 高亮目标元素
    highlightElement(element) {
        // 移除之前的高亮
        const previousHighlight = document.querySelector('.guide-highlight');
        if (previousHighlight) {
            previousHighlight.classList.remove('guide-highlight');
        }

        // 添加新的高亮
        element.classList.add('guide-highlight');
    }

    // 上一步
    prevStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.updateStep();
        }
    }

    // 下一步
    nextStep() {
        if (this.currentStep < this.steps.length - 1) {
            this.currentStep++;
            this.updateStep();
        } else {
            // 完成引导
            this.completeGuide();
        }
    }

    // 完成引导
    completeGuide() {
        // 移除高亮
        const highlightElement = document.querySelector('.guide-highlight');
        if (highlightElement) {
            highlightElement.classList.remove('guide-highlight');
        }

        // 移除引导元素
        if (this.guideElement) {
            this.guideElement.remove();
        }
        if (this.backdropElement) {
            this.backdropElement.remove();
        }

        // 标记引导完成
        localStorage.setItem('guideCompleted', 'true');

        this.isActive = false;
    }

    // 重置引导
    resetGuide() {
        localStorage.removeItem('guideCompleted');
    }
}

// 初始化引导管理器
const guideManager = new GuideManager();

// 页面加载完成后初始化引导
document.addEventListener('DOMContentLoaded', function() {
    // 延迟初始化，确保页面元素都已加载
    setTimeout(() => {
        guideManager.init();
    }, 1000);
});

// 导出引导管理器
window.guideManager = guideManager;