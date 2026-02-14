// 应用入口文件

// 初始化应用
function initializeApp() {
  console.log('应用初始化完成');
  loadChartData();
  initRealtimeUpdateControls();
  initAnimations();
}

// 初始化动画
function initAnimations() {
  initScrollAnimations();
  initPageLoadAnimations();
  initButtonAnimations();
}

// 初始化滚动动画
function initScrollAnimations() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('active');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // 观察所有带有scroll-reveal类的元素
  document.querySelectorAll('.scroll-reveal').forEach(el => {
    observer.observe(el);
  });
}

// 初始化页面加载动画
function initPageLoadAnimations() {
  // 为主要元素添加动画类
  const mainElements = document.querySelectorAll('h1, .card, .upload-area, .chart-container');
  
  mainElements.forEach((el, index) => {
    setTimeout(() => {
      el.classList.add('animate-fade-in-up');
    }, index * 100);
  });
}

// 初始化按钮动画
function initButtonAnimations() {
  const buttons = document.querySelectorAll('button, .btn');
  
  buttons.forEach(button => {
    button.addEventListener('click', function(e) {
      // 创建点击效果
      const ripple = document.createElement('span');
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;
      
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = x + 'px';
      ripple.style.top = y + 'px';
      ripple.classList.add('ripple');
      
      this.appendChild(ripple);
      
      setTimeout(() => {
        ripple.remove();
      }, 600);
    });
  });
}

// 初始化实时更新控制
function initRealtimeUpdateControls() {
  // 初始化实时更新控制
  const updateButtons = document.querySelectorAll('[data-realtime-update]');
  updateButtons.forEach(button => {
    button.addEventListener('click', (e) => {
      const containerId = button.getAttribute('data-chart-container');
      const action = button.getAttribute('data-realtime-update');
      
      if (action === 'start') {
        startRealtimeUpdate(containerId);
        button.textContent = '停止实时更新';
        button.setAttribute('data-realtime-update', 'stop');
      } else if (action === 'stop') {
        stopRealtimeUpdate(containerId);
        button.textContent = '开始实时更新';
        button.setAttribute('data-realtime-update', 'start');
      }
    });
  });
}

// 启动实时更新
function startRealtimeUpdate(containerId) {
  // 启动实时更新
  if (window.plotlyManager) {
    window.plotlyManager.startRealtimeUpdate(containerId, 3000);
    console.log(`已启动图表 ${containerId} 的实时更新`);
  }
}

// 停止实时更新
function stopRealtimeUpdate(containerId) {
  // 停止实时更新
  if (window.plotlyManager) {
    window.plotlyManager.stopRealtimeUpdate(containerId);
    console.log(`已停止图表 ${containerId} 的实时更新`);
  }
}

// 加载图表数据
function loadChartData() {
  // 从DOM中获取图表数据
  const chartContainers = document.querySelectorAll('[data-chart-type]');
  chartContainers.forEach(container => {
    const chartType = container.getAttribute('data-chart-type');
    const chartData = container.getAttribute('data-chart-data');
    if (chartType && chartData) {
      try {
        const parsedData = JSON.parse(chartData);
        console.log(`加载图表数据: ${chartType}`, parsedData);
      } catch (error) {
        console.error(`解析图表数据失败: ${chartType}`, error);
      }
    }
  });
}

// 处理图表点击事件
function handleChartClick(event) {
  console.log('图表点击事件:', event);
}

// 处理图表双击事件
function handleChartDblClick(event) {
  console.log('图表双击事件:', event);
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}

// 导出全局函数
window.initializeApp = initializeApp;
window.initAnimations = initAnimations;