
(function() {
    'use strict';

    // ============================================
    // 1. 工具函数
    // ============================================

    function getCsrfToken() {
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.content;
        }
        const inputToken = document.querySelector('input[name="csrf_token"]');
        if (inputToken) {
            return inputToken.value;
        }
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrf_token='))
            ?.split('=')[1];
        if (cookieValue) {
            return decodeURIComponent(cookieValue);
        }
        return '';
    }
    window.getCsrfToken = getCsrfToken;

    function debounce(func, wait) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }

    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // ============================================
    // 2. Toast 通知（带队列机制）
    // ============================================

    let _toastQueue = [];
    let _activeToastCount = 0;
    const _MAX_VISIBLE_TOASTS = 3;

    function processToastQueue() {
        if (_toastQueue.length === 0 || _activeToastCount >= _MAX_VISIBLE_TOASTS) return;
        let item = _toastQueue.shift();
        _activeToastCount++;
        let toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1090';
        let toastDiv = document.createElement('div');
        toastDiv.className = 'toast show align-items-center text-white bg-' + item.type;
        toastDiv.setAttribute('role', 'alert');
        let flexDiv = document.createElement('div');
        flexDiv.className = 'd-flex';
        let bodyDiv = document.createElement('div');
        bodyDiv.className = 'toast-body';
        bodyDiv.textContent = item.message;
        let closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'btn-close btn-close-white me-2 m-auto';
        closeBtn.setAttribute('data-bs-dismiss', 'toast');
        flexDiv.appendChild(bodyDiv);
        flexDiv.appendChild(closeBtn);
        toastDiv.appendChild(flexDiv);
        toastContainer.appendChild(toastDiv);
        document.body.appendChild(toastContainer);
        setTimeout(function() {
            if (toastContainer.parentNode) {
                toastContainer.remove();
            }
            _activeToastCount--;
            processToastQueue();
        }, 4000);
    }

    window.showToast = function(type, message) {
        let normalizedType = type;
        if (normalizedType === 'danger') normalizedType = 'danger';
        if (normalizedType === 'success') normalizedType = 'success';
        if (normalizedType === 'warning') normalizedType = 'warning';
        if (normalizedType === 'info') normalizedType = 'info';
        _toastQueue.push({ type: normalizedType, message: message });
        processToastQueue();
    };

    // ============================================
    // 3. JSON 验证
    // ============================================

    window.validateJSON = function() {
        const testDataInput = document.getElementById('testData');
        const jsonErrorContainer = document.getElementById('jsonErrorContainer');
        const jsonValidationStatus = document.getElementById('jsonValidationStatus');

        if (!testDataInput) {
            return { valid: true };
        }

        const value = testDataInput.value.trim();

        if (!value) {
            if (jsonValidationStatus) {
                jsonValidationStatus.textContent = '待验证';
                jsonValidationStatus.className = 'badge bg-secondary ms-2';
            }
            if (jsonErrorContainer) {
                jsonErrorContainer.innerHTML = '';
            }
            return { valid: false, error: '请输入数据' };
        }

        try {
            JSON.parse(value);
            if (jsonValidationStatus) {
                jsonValidationStatus.textContent = '✓ 格式正确';
                jsonValidationStatus.className = 'badge bg-success ms-2';
            }
            if (jsonErrorContainer) {
                jsonErrorContainer.innerHTML = '';
            }
            return { valid: true };
        } catch (error) {
            if (jsonValidationStatus) {
                jsonValidationStatus.textContent = '✗ 格式错误';
                jsonValidationStatus.className = 'badge bg-danger ms-2';
            }

            let errorMessage = 'JSON格式错误';
            if (error.message) {
                errorMessage += ': ' + error.message;
            }

            if (error.message.includes('position')) {
                const match = error.message.match(/position (\d+)/);
                if (match) {
                    const position = parseInt(match[1]);
                    const lines = value.substring(0, position).split('\n');
                    const lineNumber = lines.length;
                    const columnNumber = lines[lines.length - 1].length + 1;
                    errorMessage += ` (第${lineNumber}行，第${columnNumber}列)`;
                }
            }

            if (jsonErrorContainer) {
                jsonErrorContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show py-2 px-3" role="alert">
                        <i class="bi bi-x-circle me-1"></i><small>${errorMessage}</small>
                        <button type="button" class="btn-close py-1" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                `;
            }
            return { valid: false, error: errorMessage };
        }
    };

    // ============================================
    // 4. 错误显示
    // ============================================

    window.showErrorAlert = function(message, type) {
        if (type === undefined) type = 'danger';
        let container = document.getElementById('errorAlertContainer');

        if (!container) {
            window.showToast(type, message);
            return;
        }

        const iconClass = type === 'danger' ? 'x-circle' :
                        type === 'warning' ? 'exclamation-triangle' : 'info-circle';

        container.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="bi bi-${iconClass} me-2"></i>${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
    };

    window.clearErrorAlert = function() {
        const container = document.getElementById('errorAlertContainer');
        if (container) {
            container.innerHTML = '';
        }
    };

    // ============================================
    // 5. 评估结果缓存
    // ============================================

    let evaluationCache = {};
    let evaluationCacheOrder = [];
    const EVALUATION_CACHE_MAX_SIZE = 100;

    function evictOldestCacheEntry() {
        if (evaluationCacheOrder.length >= EVALUATION_CACHE_MAX_SIZE) {
            let oldestKey = evaluationCacheOrder.shift();
            delete evaluationCache[oldestKey];
        }
    }

    function generateCacheKey(data, filters) {
        return JSON.stringify({ data, filters });
    }

    // ============================================
    // 6. 图表管理
    // ============================================

    const chartInstances = {};

    function destroyChart(key) {
        if (chartInstances[key]) {
            chartInstances[key].destroy();
            delete chartInstances[key];
        }
    }

    function destroyAllCharts() {
        Object.keys(chartInstances).forEach(key => destroyChart(key));
    }

    function isChartAvailable() {
        return typeof Chart !== 'undefined';
    }

    // ============================================
    // 7. 图表生成
    // ============================================

    // 趋势分析图：展示各面线性回归斜率，tooltip 补充 R² / 截距 / 趋势方向
    function generateTrendChart(trendAnalysis) {
        if (!isChartAvailable()) return;
        const canvas = document.getElementById('trendChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        if (!trendAnalysis) return;

        const surfaces = [
            { key: 'p1_value', name: 'P1面', color: 'rgba(54, 162, 235, 0.6)', borderColor: 'rgb(54, 162, 235)' },
            { key: 'p2_value', name: 'P2面', color: 'rgba(255, 99, 132, 0.6)', borderColor: 'rgb(255, 99, 132)' },
            { key: 'st_value', name: 'ST面', color: 'rgba(75, 192, 192, 0.6)', borderColor: 'rgb(75, 192, 192)' }
        ];

        const labels = [];
        const slopeValues = [];
        const bgColors = [];
        const borderColors = [];
        const trendMeta = [];

        surfaces.forEach(surface => {
            const trend = trendAnalysis[surface.key];
            if (trend && typeof trend.slope === 'number' && isFinite(trend.slope)) {
                labels.push(surface.name);
                slopeValues.push(trend.slope);
                bgColors.push(surface.color);
                borderColors.push(surface.borderColor);
                trendMeta.push({
                    rSquared: trend.r_squared,
                    intercept: trend.intercept,
                    direction: trend.trend_direction || '未知'
                });
            }
        });

        if (!labels.length) return;

        chartInstances['trendChart'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '斜率',
                    data: slopeValues,
                    backgroundColor: bgColors,
                    borderColor: borderColors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '斜率值'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const meta = trendMeta[context.dataIndex];
                                if (!meta) return '';
                                const lines = [
                                    'R²: ' + (typeof meta.rSquared === 'number' ? meta.rSquared.toFixed(4) : 'N/A'),
                                    '截距: ' + (typeof meta.intercept === 'number' ? meta.intercept.toFixed(4) : 'N/A'),
                                    '方向: ' + meta.direction
                                ];
                                return lines.join('\n');
                            }
                        }
                    }
                }
            }
        });
    }

    // 数据分布（离散程度）分析：展示各面变异系数 CV%，替代原均值占比饼图。
    // 原饼图用 P1/P2/ST 三面均值做占比，量纲不同的均值做饼图无统计意义，属语义错误。
    function generateDistributionChart(basicStats) {
        if (!isChartAvailable()) return;
        const canvas = document.getElementById('distributionChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        if (!basicStats) return;

        const surfaces = [
            { key: 'p1_value', name: 'P1面', color: 'rgba(54, 162, 235, 0.6)', borderColor: 'rgb(54, 162, 235)' },
            { key: 'p2_value', name: 'P2面', color: 'rgba(255, 99, 132, 0.6)', borderColor: 'rgb(255, 99, 132)' },
            { key: 'st_value', name: 'ST面', color: 'rgba(75, 192, 192, 0.6)', borderColor: 'rgb(75, 192, 192)' }
        ];

        const labels = [];
        const cvValues = [];
        const bgColors = [];
        const borderColors = [];

        surfaces.forEach(surface => {
            const stats = basicStats[surface.key];
            if (stats && typeof stats.cv === 'number' && isFinite(stats.cv)) {
                labels.push(surface.name);
                cvValues.push(stats.cv);
                bgColors.push(surface.color);
                borderColors.push(surface.borderColor);
            }
        });

        if (!labels.length) return;

        chartInstances['distributionChart'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '变异系数 CV (%)',
                    data: cvValues,
                    backgroundColor: bgColors,
                    borderColor: borderColors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'CV (%)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    function generateComparisonChart(basicStats) {
        if (!isChartAvailable()) return;
        const canvas = document.getElementById('comparisonChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        if (!basicStats) return;

        const labels = ['均值', '中位数', '标准差'];
        const datasets = [];

        const surfaces = [
            { key: 'p1_value', name: 'P1面', color: 'rgba(54, 162, 235, 0.6)', borderColor: 'rgb(54, 162, 235)' },
            { key: 'p2_value', name: 'P2面', color: 'rgba(255, 99, 132, 0.6)', borderColor: 'rgb(255, 99, 132)' },
            { key: 'st_value', name: 'ST面', color: 'rgba(75, 192, 192, 0.6)', borderColor: 'rgb(75, 192, 192)' }
        ];

        surfaces.forEach(surface => {
            const stats = basicStats[surface.key];
            if (stats) {
                datasets.push({
                    label: surface.name,
                    data: [
                        stats.mean || 0,
                        stats.median || 0,
                        stats.std || 0
                    ],
                    backgroundColor: surface.color,
                    borderColor: surface.borderColor,
                    borderWidth: 1
                });
            }
        });

        chartInstances['comparisonChart'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    function generateChangeTrendChart(speedDetailedScores) {
        if (!isChartAvailable()) return;
        const canvas = document.getElementById('changeTrendChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        if (!speedDetailedScores) return;

        const speeds = Object.keys(speedDetailedScores);
        const scores = speeds.map(speed => speedDetailedScores[speed].total_score || 0);

        chartInstances['changeTrendChart'] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: speeds,
                datasets: [{
                    label: '综合得分',
                    data: scores,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgb(54, 162, 235)',
                    borderWidth: 2,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        title: {
                            display: true,
                            text: '得分'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '转速'
                        }
                    }
                }
            }
        });
    }

    function generateCharts(data) {
        if (!isChartAvailable()) {
            console.warn('Chart.js 库未加载，跳过图表生成');
            return;
        }
        destroyAllCharts();
        generateTrendChart(data.advanced_analysis?.trend_analysis);
        generateDistributionChart(data.advanced_analysis?.advanced_statistics?.basic_stats);
        generateComparisonChart(data.advanced_analysis?.advanced_statistics?.basic_stats);
        generateChangeTrendChart(data.optimal_speed_evaluation?.speed_detailed_scores);
    }

    // ============================================
    // 8. 结果显示函数
    // ============================================

    function updateDataQualityIndicator(quality) {
        const indicator = document.querySelector('.data-quality-indicator');
        if (!indicator) return;
        indicator.className = 'data-quality-indicator';
        if (quality === '优秀') {
            indicator.classList.add('quality-excellent');
        } else if (quality === '良好') {
            indicator.classList.add('quality-good');
        } else if (quality === '一般') {
            indicator.classList.add('quality-average');
        } else {
            indicator.classList.add('quality-poor');
        }
    }

    function displayBasicStats(basicStats) {
        const tableBody = document.getElementById('basicStatsTable');
        if (!tableBody) return;
        tableBody.innerHTML = '';

        if (!basicStats) {
            tableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">暂无数据</td></tr>';
            return;
        }

        const metrics = ['均值', '中位数', '标准差', '变异系数', '最小值', '最大值'];
        const metricKeys = ['mean', 'median', 'std', 'cv', 'min', 'max'];

        metricKeys.forEach((key, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${metrics[index]}</td>
                <td>${(val => Number.isFinite(val) ? val.toFixed(4) : '-')(basicStats.p1_value?.[key])}</td>
                <td>${(val => Number.isFinite(val) ? val.toFixed(4) : '-')(basicStats.p2_value?.[key])}</td>
                <td>${(val => Number.isFinite(val) ? val.toFixed(4) : '-')(basicStats.st_value?.[key])}</td>
            `;
            tableBody.appendChild(row);
        });
    }

    function displayTrendAnalysis(trendAnalysis) {
        const container = document.getElementById('trendAnalysisTable');
        if (!container) return;
        container.innerHTML = '';

        if (!trendAnalysis) {
            container.innerHTML = '<p class="text-center text-muted">暂无数据</p>';
            return;
        }

        const surfaces = [
            { key: 'p1_value', name: 'P1面' },
            { key: 'p2_value', name: 'P2面' },
            { key: 'st_value', name: 'ST面' }
        ];

        surfaces.forEach(surface => {
            const trend = trendAnalysis[surface.key];
            if (trend) {
                const div = document.createElement('div');
                div.className = 'mb-2';
                const trendClass = trend.trend_direction === '上升' ? 'trend-up' :
                                  trend.trend_direction === '下降' ? 'trend-down' : 'trend-stable';
                div.innerHTML = `
                    <strong>${surface.name}:</strong>
                    <span class="${trendClass}">${trend.trend_direction}</span>
                    (斜率: ${trend.slope?.toFixed(4) || '-'})
                `;
                container.appendChild(div);
            }
        });
    }

    function displayAnomalyDetection(anomalyDetection) {
        const container = document.getElementById('anomalyDetectionTable');
        if (!container) return;
        container.innerHTML = '';

        if (!anomalyDetection) {
            container.innerHTML = '<p class="text-center text-muted">暂无数据</p>';
            return;
        }

        const surfaces = [
            { key: 'p1_value', name: 'P1面' },
            { key: 'p2_value', name: 'P2面' },
            { key: 'st_value', name: 'ST面' }
        ];

        let hasAnomalies = false;

        surfaces.forEach(surface => {
            const anomaly = anomalyDetection[surface.key];
            if (anomaly && anomaly.anomaly_values && anomaly.anomaly_values.length > 0) {
                hasAnomalies = true;
                const div = document.createElement('div');
                div.className = 'mb-4 p-4 bg-warning bg-opacity-10 rounded-lg border border-warning';
                div.innerHTML = `
                    <h6 class="text-warning mb-2">${surface.name}</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <p class="mb-2"><strong>异常数量:</strong> <span class="badge bg-warning">${anomaly.anomaly_values.length}</span></p>
                            <p class="mb-0"><strong>异常值:</strong> ${anomaly.anomaly_values.join(', ') || '无'}</p>
                        </div>
                        <div class="col-md-6">
                            <p class="mb-2"><strong>异常比例:</strong> ${anomaly.anomaly_ratio ? (anomaly.anomaly_ratio * 100).toFixed(2) + '%' : '未知'}</p>
                            <p class="mb-0"><strong>检测方法:</strong> ${anomaly.detection_method || '统计方法'}</p>
                            ${anomaly.z_scores ? `<p class="mb-0"><strong>Z-scores:</strong> ${anomaly.z_scores.map(z => z.toFixed(2)).join(', ')}</p>` : ''}
                        </div>
                    </div>
                `;
                container.appendChild(div);
            }
        });

        if (!hasAnomalies) {
            container.innerHTML = '<p class="text-success"><i class="bi bi-check-circle me-2"></i>未检测到异常数据</p>';
        } else {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-warning alert-dismissible fade show mt-4';
            alertDiv.role = 'alert';
            alertDiv.innerHTML = `
                <i class="bi bi-exclamation-triangle me-2"></i>
                <strong>异常预警</strong> 检测到数据中存在异常值，可能影响分析结果的准确性，请检查数据采集过程。
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            container.insertBefore(alertDiv, container.firstChild);
        }
    }

    function displayRecommendations(data) {
        const container = document.getElementById('recommendationsList');
        if (!container) return;
        container.innerHTML = '';

        const comprehensiveEval = data.comprehensive_evaluation || {};
        const recommendations = [];

        if (comprehensiveEval.data_quality === '一般' || comprehensiveEval.data_quality === '不足') {
            recommendations.push({
                type: 'warning',
                text: '建议增加测量样本数量，提高数据质量'
            });
        }

        if (comprehensiveEval.process_stability === '不稳定') {
            recommendations.push({
                type: 'danger',
                text: '工艺稳定性较差，建议检查设备状态和操作流程'
            });
        }

        if (comprehensiveEval.anomaly_evaluation === '较多异常') {
            recommendations.push({
                type: 'danger',
                text: '存在较多异常值，建议检查测量过程和数据采集系统'
            });
        }

        if (comprehensiveEval.skill_score < 0.7) {
            recommendations.push({
                type: 'warning',
                text: '分析得分较低，建议加强操作培训和工艺优化'
            });
        }

        const trendAnalysis = data.advanced_analysis?.trend_analysis || {};
        const surfaces = ['p1_value', 'p2_value', 'st_value'];
        const surfaceNames = { p1_value: 'P1面', p2_value: 'P2面', st_value: 'ST面' };

        surfaces.forEach(key => {
            if (trendAnalysis[key]?.trend_direction === '上升') {
                recommendations.push({
                    type: 'warning',
                    text: `${surfaceNames[key]}呈现上升趋势，建议分析原因并采取措施`
                });
            }
        });

        if (recommendations.length === 0) {
            recommendations.push({
                type: 'success',
                text: '各项指标表现良好，继续保持当前的操作水平'
            });
        }

        recommendations.forEach(rec => {
            const div = document.createElement('div');
            div.className = `recommendation-item ${rec.type}`;
            div.innerHTML = '<i class="bi bi-' + (rec.type === 'success' ? 'check-circle' : rec.type === 'warning' ? 'exclamation-circle' : 'x-circle') + ' me-2"></i>';
            div.appendChild(document.createTextNode(rec.text));
            container.appendChild(div);
        });
    }

    function displayEvaluationResults(data) {
        const evaluateBtn = document.getElementById('evaluateBtn');

        const comprehensiveEval = data.comprehensive_evaluation || {};
        const analysisLevelBadge = document.getElementById('analysisLevelBadge');
        const analysisLevel = comprehensiveEval.overall_assessment || '需要提升';
        analysisLevelBadge.textContent = analysisLevel;
        analysisLevelBadge.className = 'analysis-level-badge d-inline-block';

        if (analysisLevel === '优秀') {
            analysisLevelBadge.classList.add('analysis-expert');
        } else if (analysisLevel === '良好') {
            analysisLevelBadge.classList.add('analysis-proficient');
        } else if (analysisLevel === '一般') {
            analysisLevelBadge.classList.add('analysis-basic');
        } else {
            analysisLevelBadge.classList.add('analysis-needs-improvement');
        }

        document.getElementById('skillScore').textContent =
            '分析得分: ' + ((comprehensiveEval.skill_score || 0)).toFixed(2);

        document.getElementById('dataQualityValue').textContent = comprehensiveEval.data_quality || '未知';
        updateDataQualityIndicator(comprehensiveEval.data_quality);

        document.getElementById('processStabilityValue').textContent = comprehensiveEval.process_stability || '未知';
        document.getElementById('anomalyCount').textContent = comprehensiveEval.anomaly_evaluation || '无异常';

        const optimalSpeed = data.optimal_speed_evaluation?.best_speeds?.[0];
        if (optimalSpeed && typeof optimalSpeed === 'object') {
            document.getElementById('optimalSpeedValue').textContent =
                optimalSpeed.id + ' (得分: ' + ((optimalSpeed.score || 0)).toFixed(4) + ')';
        } else {
            document.getElementById('optimalSpeedValue').textContent = optimalSpeed || '-';
        }

        displayBasicStats(data.advanced_analysis?.advanced_statistics?.basic_stats);
        displayTrendAnalysis(data.advanced_analysis?.trend_analysis);
        displayAnomalyDetection(data.advanced_analysis?.anomaly_detection);
        displayRecommendations(data);
        generateCharts(data);

        if (evaluateBtn) {
            evaluateBtn.disabled = false;
            evaluateBtn.innerHTML = '<i class="bi bi-play me-2"></i>开始分析';
        }
    }

    // ============================================
    // 9. 表单提交处理
    // ============================================

    function setupFormSubmit() {
        const form = document.getElementById('inDepthAnalysisForm');
        if (!form) return;

        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            const evaluateBtn = document.getElementById('evaluateBtn');
            const loadingSpinner = document.getElementById('loadingSpinner');
            const resultSection = document.getElementById('resultSection');

            // 声明提升到 handler 作用域：catch 块无法访问 try 块内的 let（块级作用域），
            // 否则 catch 路径会抛 ReferenceError（progressFill is not defined）
            let progressBar = null;
            let progressDiv = null;
            let progressFill = null;
            let progressInterval = null;
            let progressPercent = 0;
            let requestPhase = '';

            try {
                clearErrorAlert();

                const validation = validateJSON();
                if (!validation.valid) {
                    showErrorAlert(validation.error || 'JSON格式错误，请检查输入', 'danger');
                    return;
                }

                evaluateBtn.disabled = true;
                evaluateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 分析中...';
                loadingSpinner.classList.add('active');
                resultSection.classList.remove('active');

                progressBar = document.getElementById('analysisProgressBar');
                progressDiv = document.getElementById('analysisProgress');
                progressFill = null;
                progressInterval = null;
                progressPercent = 0;

                if (progressDiv) {
                    progressDiv.classList.remove('d-none');
                    progressFill = progressBar && progressBar.querySelector('.progress-bar');
                }

                if (progressFill) {
                    progressPercent = 0;
                    progressFill.style.width = '0%';
                    progressInterval = setInterval(function() {
                        if (progressPercent < 90) {
                            progressPercent += Math.random() * 10 + 2;
                            if (progressPercent > 90) progressPercent = 90;
                            progressFill.style.width = progressPercent + '%';
                            progressFill.setAttribute('aria-valuenow', Math.round(progressPercent));
                            let pt = document.getElementById('progressPercentText');
                            if (pt) pt.textContent = Math.round(progressPercent) + '%';
                        }
                    }, 300);
                }

                const fanModel = document.getElementById('fanModel').value;
                const testDataText = document.getElementById('testData').value;

                requestPhase = 'parse';
                const testData = JSON.parse(testDataText);

                const filters = {
                    speed_range: document.getElementById('speedRange').value,
                    data_surface: document.getElementById('dataSurface').value,
                    data_quality: document.getElementById('dataQuality').value,
                    anomaly_filter: document.getElementById('anomalyFilter').value
                };

                const cacheKey = generateCacheKey(testData, filters);

                if (evaluationCache[cacheKey]) {
                    displayEvaluationResults(evaluationCache[cacheKey]);
                    loadingSpinner.classList.remove('active');
                    resultSection.classList.add('active');
                    if (progressFill) { progressFill.style.width = '100%'; clearInterval(progressInterval); }
                    if (progressDiv) { setTimeout(function() { progressDiv.classList.add('d-none'); }, 500); }
                    saveAnalysisStateToSession(evaluationCache[cacheKey]);
                    setTimeout(function() { collapseInputSection(); }, 300);
                    showToast('success', '从缓存加载分析结果');
                    evaluateBtn.disabled = false;
                    evaluateBtn.innerHTML = '<i class="bi bi-play me-2"></i>开始分析';
                    return;
                }

                requestPhase = 'fetch';
                const response = await fetch('/api/in-depth-analysis/evaluate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        data: testData,
                        filters: filters
                    })
                });

                requestPhase = 'response';
                const result = await response.json();

                if (result.code === 200) {
                    evictOldestCacheEntry();
                    evaluationCache[cacheKey] = result.data;
                    evaluationCacheOrder.push(cacheKey);
                    displayEvaluationResults(result.data);
                    loadingSpinner.classList.remove('active');
                    resultSection.classList.add('active');
                    if (progressFill) { progressFill.style.width = '100%'; clearInterval(progressInterval); }
                    if (progressDiv) { setTimeout(function() { progressDiv.classList.add('d-none'); }, 500); }
                    saveAnalysisStateToSession(result.data);
                    setTimeout(function() { collapseInputSection(); }, 300);
                    showToast('success', '深入分析完成');
                    evaluateBtn.disabled = false;
                    evaluateBtn.innerHTML = '<i class="bi bi-play me-2"></i>开始分析';
                } else {
                    throw new Error(result.message || '评估失败');
                }
            } catch (error) {
                console.error('评估失败:', error);
                let errorMessage = '评估失败';
                if (error.message) {
                    errorMessage += ': ' + error.message;
                }
                if (error.name === 'SyntaxError') {
                    if (requestPhase === 'parse') {
                        errorMessage = 'JSON解析错误，请检查数据格式';
                    } else if (requestPhase === 'response') {
                        errorMessage = '服务器返回了非JSON响应，请检查服务器状态';
                    } else {
                        errorMessage = 'JSON解析错误，请检查数据格式';
                    }
                } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                    errorMessage = '网络连接失败，请检查服务器是否正常运行';
                }
                showErrorAlert(errorMessage, 'danger');
                loadingSpinner.classList.remove('active');
                if (progressFill) { progressFill.style.width = '0%'; clearInterval(progressInterval); }
                if (progressDiv) { progressDiv.classList.add('d-none'); }
                evaluateBtn.disabled = false;
                evaluateBtn.innerHTML = '<i class="bi bi-play me-2"></i>开始分析';
            }
        });
    }

    // ============================================
    // 10. 「从当前分析结果加载」按钮
    // ============================================

    function enhanceLoadButton() {
        const loadButtons = Array.from(document.querySelectorAll('button')).filter(btn =>
            btn.textContent.includes('从当前分析结果加载')
        );

        loadButtons.forEach(button => {
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);

            newButton.addEventListener('click', async function() {
                const btn = this;
                const originalHTML = btn.innerHTML;

                try {
                    btn.disabled = true;
                    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 加载中...';
                    clearErrorAlert();

                    const response = await fetch('/api/in-depth-analysis/get_session_data', {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }

                    const data = await response.json();

                    if (data.success && data.parsed_data) {
                        function replacer(key, value) {
                            if (typeof value === 'number' && isNaN(value)) {
                                return null;
                            }
                            return value;
                        }
                        document.getElementById('testData').value = JSON.stringify(data.parsed_data, replacer, 2);
                        if (data.fan_model) {
                            document.getElementById('fanModel').value = data.fan_model;
                        }

                        syncJsonEditorContent(document.getElementById('testData'));
                        validateJSON();

                        showToast('success', '成功从当前分析结果加载数据');
                    } else {
                        showErrorAlert(data.message || '暂无分析数据，请先进行数据分析', 'warning');
                    }
                } catch (error) {
                    console.error('加载数据失败:', error);
                    let errorMessage = '加载数据失败';
                    if (error.message) {
                        errorMessage += ': ' + error.message;
                    }
                    if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                        errorMessage = '网络连接失败，请检查服务器是否正常运行';
                    }
                    showErrorAlert(errorMessage, 'danger');
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = originalHTML;
                }
            });
        });
    }

    // ============================================
    // 11. 实时 JSON 验证
    // ============================================

    function syncJsonEditorScroll(textarea) {
        let highlightPre = document.querySelector('.json-editor-highlight');
        if (highlightPre) {
            highlightPre.scrollTop = textarea.scrollTop;
            highlightPre.scrollLeft = textarea.scrollLeft;
        }
    }

    function syncJsonEditorTextOnly(textarea) {
        let jsonHighlight = document.getElementById('jsonHighlight');
        if (jsonHighlight) {
            jsonHighlight.textContent = textarea.value;
        }
        syncJsonEditorScroll(textarea);
    }

    function syncJsonEditorContent(textarea) {
        let jsonHighlight = document.getElementById('jsonHighlight');
        if (jsonHighlight) {
            jsonHighlight.textContent = textarea.value;
            if (window.Prism) {
                Prism.highlightElement(jsonHighlight);
            }
        }
        syncJsonEditorScroll(textarea);
    }

    function addRealTimeValidation() {
        let testDataInput = document.getElementById('testData');

        if (testDataInput) {
            testDataInput.addEventListener('input', debounce(function() {
                syncJsonEditorContent(this);
                validateJSON();
            }, 150));

            testDataInput.addEventListener('scroll', function() {
                syncJsonEditorScroll(this);
            });

            setTimeout(function() {
                syncJsonEditorContent(testDataInput);
                validateJSON();
            }, 100);
        }
    }

    // ============================================
    // 12. 导出分析结果
    // ============================================

    function setupExportHandlers() {
        document.querySelectorAll('.dropdown-item[data-format]').forEach(item => {
            item.addEventListener('click', async function(e) {
                e.preventDefault();
                const format = this.getAttribute('data-format');

                if (this.disabled) return;
                this.disabled = true;
                const originalText = this.innerHTML;
                this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>导出中...';

                try {
                    const testDataText = document.getElementById('testData').value;
                    const testData = JSON.parse(testDataText);

                    const filters = {
                        speed_range: document.getElementById('speedRange').value,
                        data_surface: document.getElementById('dataSurface').value,
                        data_quality: document.getElementById('dataQuality').value,
                        anomaly_filter: document.getElementById('anomalyFilter').value
                    };

                    const cacheKey = generateCacheKey(testData, filters);
                    let evalData;

                    if (evaluationCache[cacheKey]) {
                        evalData = evaluationCache[cacheKey];
                    } else {
                        const evalResponse = await fetch('/api/in-depth-analysis/evaluate', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCsrfToken()
                            },
                            body: JSON.stringify({
                                data: testData,
                                filters: filters
                            })
                        });

                        const evalResult = await evalResponse.json();

                        if (evalResult.code !== 200) {
                            throw new Error(evalResult.message || '评估失败，无法导出');
                        }
                        evalData = evalResult.data;
                        evictOldestCacheEntry();
                        evaluationCache[cacheKey] = evalData;
                        evaluationCacheOrder.push(cacheKey);
                    }

                    const exportResponse = await fetch('/api/in-depth-analysis/export', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({
                            evaluation_results: evalData,
                            format: format
                        })
                    });

                    if (exportResponse.ok) {
                        const blob = await exportResponse.blob();
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;

                        const fileName = `in_depth_analysis_${new Date().toISOString().slice(0,10)}.${format === 'excel' ? 'xlsx' : format}`;
                        a.download = fileName;

                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);

                        showToast('success', `分析结果已导出为${format.toUpperCase()}格式`);
                    } else {
                        const errorData = await exportResponse.json();
                        throw new Error(errorData.message || '导出失败');
                    }
                } catch (error) {
                    console.error('导出分析结果失败:', error);
                    showToast('danger', '导出分析结果失败: ' + error.message);
                } finally {
                    this.disabled = false;
                    this.innerHTML = originalText;
                }
            });
        });
    }

    // ============================================
    // 13. 查看详细数据按钮
    // ============================================

    function setupViewDetailedButton() {
        const btn = document.getElementById('viewDetailedBtn');
        if (!btn) return;

        btn.addEventListener('click', function() {
            const testDataText = document.getElementById('testData').value;
            try {
                const testData = JSON.parse(testDataText);
                // 真正输出详细数据到控制台（原实现只弹 toast，无实际输出）
                console.log('[深入分析] 输入数据明细:');
                console.log(JSON.stringify(testData, null, 2));
                showToast('info', '详细数据已输出到控制台');
            } catch (error) {
                showToast('danger', '数据格式错误');
            }
        });
    }

    // ============================================
    // 14. 报告生成
    // ============================================

    async function generateReport(testDataText, template, format, include) {
        try {
            const testData = JSON.parse(testDataText);

            const filters = {
                speed_range: document.getElementById('speedRange').value,
                data_surface: document.getElementById('dataSurface').value,
                data_quality: document.getElementById('dataQuality').value,
                anomaly_filter: document.getElementById('anomalyFilter').value
            };

            const cacheKey = generateCacheKey(testData, filters);
            let evalData;

            if (evaluationCache[cacheKey]) {
                evalData = evaluationCache[cacheKey];
            } else {
                const evalResponse = await fetch('/api/in-depth-analysis/evaluate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        data: testData,
                        filters: filters
                    })
                });

                const evalResult = await evalResponse.json();

                if (evalResult.code !== 200) {
                    throw new Error(evalResult.message || '评估失败');
                }
                evalData = evalResult.data;
                evictOldestCacheEntry();
                evaluationCache[cacheKey] = evalData;
                evaluationCacheOrder.push(cacheKey);
            }

            const reportResponse = await fetch('/api/in-depth-analysis/generate-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    evaluation_results: evalData,
                    template: template,
                    format: format,
                    include: include
                })
            });

            if (reportResponse.ok) {
                const blob = await reportResponse.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;

                const fileName = `analysis_report_${new Date().toISOString().slice(0,10)}.${format === 'excel' ? 'xlsx' : format === 'word' ? 'docx' : format}`;
                a.download = fileName;

                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                showToast('success', `分析报告已生成为${format.toUpperCase()}格式`);
            } else {
                const errorData = await reportResponse.json();
                throw new Error(errorData.message || '生成报告失败');
            }
        } catch (error) {
            console.error('生成报告失败:', error);
            showToast('danger', '生成报告失败: ' + error.message);
        }
    }

    function setupReportButton() {
        const btn = document.getElementById('generateReportBtn');
        if (!btn) return;

        btn.addEventListener('click', async function() {
            if (btn.disabled) return;
            const testDataText = document.getElementById('testData').value;
            if (!testDataText) {
                showToast('danger', '请先输入测试数据');
                return;
            }

            const template = document.getElementById('reportTemplate').value;
            const format = document.getElementById('reportFormat').value;

            const include = {
                summary: document.getElementById('includeSummary').checked,
                basicStats: document.getElementById('includeBasicStats').checked,
                advancedStats: document.getElementById('includeAdvancedStats').checked,
                trendAnalysis: document.getElementById('includeTrendAnalysis').checked,
                anomalyDetection: document.getElementById('includeAnomalyDetection').checked,
                recommendations: document.getElementById('includeRecommendations').checked
            };

            const originalHtml = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>生成报告...';

            try {
                await generateReport(testDataText, template, format, include);
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        });
    }

    // ============================================
    // 15. sessionStorage 持久化与输入折叠
    // ============================================

    const SESSION_KEYS = {
        results: 'inDepthAnalysisResults',
        formData: 'inDepthAnalysisFormData',
        collapsed: 'inDepthAnalysisCollapsed'
    };

    function safeSessionSet(key, value) {
        try {
            sessionStorage.setItem(key, value);
        } catch (e) {
            if (e.name === 'QuotaExceededError' || e.code === 22 || e.code === 1014) {
                try {
                    Object.keys(SESSION_KEYS).forEach(function(k) {
                        sessionStorage.removeItem(SESSION_KEYS[k]);
                    });
                    sessionStorage.setItem(key, value);
                } catch (retryErr) {
                    console.warn('sessionStorage写入失败，存储空间不足:', retryErr);
                }
            } else {
                console.warn('sessionStorage写入失败:', e);
            }
        }
    }

    function collapseInputSection() {
        let collapseEl = document.getElementById('inputSectionCollapse');
        let icon = document.getElementById('inputCollapseIcon');
        if (collapseEl && collapseEl.classList.contains('show')) {
            let bsCollapse = bootstrap.Collapse.getInstance(collapseEl) || new bootstrap.Collapse(collapseEl, { toggle: false });
            bsCollapse.hide();
            if (icon) {
                icon.classList.remove('bi-chevron-up');
                icon.classList.add('bi-chevron-down');
            }
            safeSessionSet(SESSION_KEYS.collapsed, 'true');
        }
    }

    function expandInputSection() {
        let collapseEl = document.getElementById('inputSectionCollapse');
        let icon = document.getElementById('inputCollapseIcon');
        if (collapseEl && !collapseEl.classList.contains('show')) {
            let bsCollapse = bootstrap.Collapse.getInstance(collapseEl) || new bootstrap.Collapse(collapseEl, { toggle: false });
            bsCollapse.show();
            if (icon) {
                icon.classList.remove('bi-chevron-down');
                icon.classList.add('bi-chevron-up');
            }
            safeSessionSet(SESSION_KEYS.collapsed, 'false');
        }
    }

    function saveAnalysisStateToSession(data) {
        safeSessionSet(SESSION_KEYS.results, JSON.stringify(data));
        let formData = {
            fanModel: document.getElementById('fanModel') ? document.getElementById('fanModel').value : '',
            testData: document.getElementById('testData') ? document.getElementById('testData').value : '',
            speedRange: document.getElementById('speedRange') ? document.getElementById('speedRange').value : 'all',
            dataSurface: document.getElementById('dataSurface') ? document.getElementById('dataSurface').value : 'all',
            dataQuality: document.getElementById('dataQuality') ? document.getElementById('dataQuality').value : 'all',
            anomalyFilter: document.getElementById('anomalyFilter') ? document.getElementById('anomalyFilter').value : 'all'
        };
        safeSessionSet(SESSION_KEYS.formData, JSON.stringify(formData));
    }

    function restoreFromSession() {
        try {
            let savedResults = sessionStorage.getItem(SESSION_KEYS.results);
            let savedFormData = sessionStorage.getItem(SESSION_KEYS.formData);
            let wasCollapsed = sessionStorage.getItem(SESSION_KEYS.collapsed);

            if (savedFormData) {
                let formData = JSON.parse(savedFormData);
                if (formData.fanModel && document.getElementById('fanModel')) {
                    document.getElementById('fanModel').value = formData.fanModel;
                }
                if (formData.testData && document.getElementById('testData')) {
                    document.getElementById('testData').value = formData.testData;
                    syncJsonEditorContent(document.getElementById('testData'));
                }
                if (formData.speedRange && document.getElementById('speedRange')) {
                    document.getElementById('speedRange').value = formData.speedRange;
                }
                if (formData.dataSurface && document.getElementById('dataSurface')) {
                    document.getElementById('dataSurface').value = formData.dataSurface;
                }
                if (formData.dataQuality && document.getElementById('dataQuality')) {
                    document.getElementById('dataQuality').value = formData.dataQuality;
                }
                if (formData.anomalyFilter && document.getElementById('anomalyFilter')) {
                    document.getElementById('anomalyFilter').value = formData.anomalyFilter;
                }
            }

            if (savedResults) {
                let data = JSON.parse(savedResults);
                let resultSection = document.getElementById('resultSection');
                if (resultSection) {
                    resultSection.classList.add('active');
                }
                displayEvaluationResults(data);
            } else if (wasCollapsed === 'true') {
                expandInputSection();
            }

            if (wasCollapsed === 'true' && savedResults) {
                let collapseEl = document.getElementById('inputSectionCollapse');
                let icon = document.getElementById('inputCollapseIcon');
                let toggleBtn = document.getElementById('inputCollapseToggle');
                if (collapseEl) {
                    collapseEl.classList.remove('show');
                    if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'false');
                    if (icon) {
                        icon.classList.remove('bi-chevron-up');
                        icon.classList.add('bi-chevron-down');
                    }
                }
            }
        } catch (e) {}
    }

    function clearAnalysisState() {
        try {
            sessionStorage.removeItem(SESSION_KEYS.results);
            sessionStorage.removeItem(SESSION_KEYS.formData);
            sessionStorage.removeItem(SESSION_KEYS.collapsed);
        } catch (e) {}
    }

    function setupManualReset() {
        let resetBtn = document.getElementById('manualResetBtn');
        if (!resetBtn) return;

        resetBtn.addEventListener('click', function(e) {
            e.preventDefault();

            if (!confirm('确定要手动重置所有分析数据和表单输入吗？此操作将清除当前分析结果。')) {
                return;
            }

            clearAnalysisState();

            let resultSection = document.getElementById('resultSection');
            if (resultSection) {
                resultSection.classList.remove('active');
            }

            let form = document.getElementById('inDepthAnalysisForm');
            if (form) {
                form.reset();
            }

            let testDataInput = document.getElementById('testData');
            if (testDataInput) {
                testDataInput.value = '';
                syncJsonEditorContent(testDataInput);
            }

            expandInputSection();

            let evaluateBtn = document.getElementById('evaluateBtn');
            if (evaluateBtn) {
                evaluateBtn.disabled = false;
                evaluateBtn.innerHTML = '<i class="bi bi-play me-2"></i>开始分析';
            }

            showToast('info', '已手动重置所有数据');
        });
    }

    function setupCollapseEvents() {
        let collapseEl = document.getElementById('inputSectionCollapse');
        if (!collapseEl) return;

        collapseEl.addEventListener('show.bs.collapse', function() {
            let icon = document.getElementById('inputCollapseIcon');
            if (icon) {
                icon.classList.remove('bi-chevron-down');
                icon.classList.add('bi-chevron-up');
            }
            safeSessionSet(SESSION_KEYS.collapsed, 'false');
        });

        collapseEl.addEventListener('hide.bs.collapse', function() {
            let icon = document.getElementById('inputCollapseIcon');
            if (icon) {
                icon.classList.remove('bi-chevron-up');
                icon.classList.add('bi-chevron-down');
            }
            safeSessionSet(SESSION_KEYS.collapsed, 'true');
        });
    }

    // ============================================
    // 16. 初始化入口（唯一入口点）
    // ============================================

    document.addEventListener('DOMContentLoaded', function() {
        let testDataInput = document.getElementById('testData');
        if (testDataInput) {
            testDataInput.addEventListener('input', function() {
                syncJsonEditorTextOnly(this);
            });
        }

        if (typeof Prism !== 'undefined') {
            Prism.highlightAll();
        }

        setupFormSubmit();
        setupExportHandlers();
        setupViewDetailedButton();
        setupReportButton();
        enhanceLoadButton();
        addRealTimeValidation();
        setupManualReset();
        setupCollapseEvents();
        restoreFromSession();
    });

    window.addEventListener('beforeunload', function() {
        _toastQueue = [];
        let toasts = document.querySelectorAll('.toast-container');
        toasts.forEach(function(t) { if (t.parentNode) t.remove(); });
        _activeToastCount = 0;

        if (typeof evaluationCache !== 'undefined') {
            evaluationCache = {};
            evaluationCacheOrder = [];
        }
    });

    window.addEventListener('pagehide', function() {
        _toastQueue = [];
        let toasts = document.querySelectorAll('.toast-container');
        toasts.forEach(function(t) { if (t.parentNode) t.remove(); });
        _activeToastCount = 0;
    });
})();
