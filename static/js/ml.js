(function () {
    'use strict';

    /* ===== 历史数据导入 ===== */
    var _activeTab = 'tab-trend';
    var _modelDataCache = null;
    var _panelFilled = false;

    /** 加载型号列表并填充下拉框 */
    function loadModels() {
        var select = el('ml-model-select');
        var spinner = el('ml-ds-spinner');
        if (!select) return;
        select.disabled = true;
        spinner.style.display = 'inline-block';

        window.safeFetch('/api/ml/models', { method: 'GET' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                spinner.style.display = 'none';
                if (data.success) {
                    select.innerHTML = '<option value="">-- 选择历史型号 --</option>';
                    (data.models || []).forEach(function (m) {
                        select.innerHTML += '<option value="' + escapeHtml(m.fan_model) + '">' +
                            escapeHtml(m.fan_model) + ' (' + m.record_count + ', ' + m.last_analysis + ')</option>';
                    });
                    if (data.models.length === 0) {
                        select.innerHTML += '<option disabled>暂无历史数据</option>';
                    }
                    select.disabled = false;
                } else {
                    showError(data.error || '加载型号列表失败');
                    select.disabled = false;
                }
            })
            .catch(function (err) {
                spinner.style.display = 'none';
                select.disabled = false;
                showError('加载型号列表失败: ' + (err.message || '网络错误'));
            });
    }

    /** 根据当前激活面板，用系统数据填充 textarea */
    function fillPanelWithModelData(rawData, faceOverride) {
        var face = faceOverride || el('ml-face-select').value || 'P1';
        var tab = _activeTab;
        var formatted;

        if (tab === 'tab-trend' || tab === 'tab-anomaly') {
            formatted = toTrendFormat(rawData, face);
        } else if (tab === 'tab-metrics') {
            formatted = toMetricsFormat(rawData);
        } else if (tab === 'tab-multi') {
            formatted = toMultiFormat(rawData);
        } else {
            return;
        }

        var inputId;
        if (tab === 'tab-trend') inputId = 'trend-input';
        else if (tab === 'tab-metrics') inputId = 'metrics-input';
        else if (tab === 'tab-multi') inputId = 'multi-input';
        else if (tab === 'tab-anomaly') inputId = 'anomaly-input';
        else return;

        var textarea = el(inputId);
        if (textarea) {
            textarea.value = JSON.stringify(formatted, null, 2);
            _panelFilled = true;
        }

        // 多维度面板：自动填入 dimensions 和 metrics
        if (tab === 'tab-multi' && formatted.length > 0) {
            var firstRow = formatted[0];
            var cols = Object.keys(firstRow);
            var dimsInput = el('multi-dimensions');
            var metricsInput = el('multi-metrics');
            if (dimsInput && !dimsInput.value.trim()) {
                // 维度：speed 列
                if (cols.indexOf('speed') !== -1) dimsInput.value = 'speed';
                else dimsInput.value = cols[0] || '';
            }
            if (metricsInput && !metricsInput.value.trim()) {
                // 指标：排除 speed 后的所有数值列
                var metricCols = cols.filter(function (c) { return c !== 'speed'; });
                metricsInput.value = metricCols.join(', ');
            }
        }

        updateDataSourceSummary(rawData);
    }

    /** 前端格式转换函数（与 Python ml_data_adapter.py 保持逻辑一致，基于行式数据） */
    function toTrendFormat(rawData, face) {
        var rows = rawData.rows || [];
        var faceLower = face.toLowerCase();
        var valueKey = faceLower + '_mean';
        return rows.map(function (r) {
            return { date: r.speed, value: r[valueKey] || 0 };
        });
    }

    function toMetricsFormat(rawData) {
        var rows = rawData.rows || [];
        return rows.map(function (r) {
            var row = { date: r.speed };
            ['p1', 'p2', 'st'].forEach(function (fn) {
                ['mean', 'cv', 'std', 'max'].forEach(function (stat) {
                    var key = fn + '_' + stat;
                    if (r[key] !== undefined) row[key] = r[key];
                });
            });
            row.total = Math.round(Math.sqrt((row.p1_mean || 0) * (row.p1_mean || 0) + (row.p2_mean || 0) * (row.p2_mean || 0)) * 1e6) / 1e6;
            return row;
        });
    }

    function toMultiFormat(rawData) {
        var rows = rawData.rows || [];
        return rows.map(function (r) {
            var row = { speed: r.speed };
            ['p1', 'p2', 'st'].forEach(function (fn) {
                if (r[fn + '_mean'] !== undefined) row[fn + '_amplitude'] = r[fn + '_mean'];
                if (r[fn + '_std'] !== undefined) row[fn + '_std'] = r[fn + '_std'];
            });
            var p1a = row.p1_amplitude || 0;
            var p2a = row.p2_amplitude || 0;
            row.p1_p2_ratio = p2a !== 0 ? Math.round((p1a / p2a) * 10000) / 10000 : 0;
            return row;
        });
    }

    /** 更新数据源摘要行 */
    function updateDataSourceSummary(rawData) {
        var summary = el('ml-ds-summary');
        if (!summary) return;
        var stats = rawData.stats || {};
        var faces = (stats.faces_available || []).map(function (f) {
            return f + ' ' + stats.total_speeds + '';
        }).join(' | ');
        summary.textContent = stats.record_count + ' 条记录 | ' + faces + ' 个转速';
        summary.style.display = '';
    }

    /** 更新端面选择器可见性 */
    function updateFaceSelectVisibility() {
        var group = el('ml-face-select-group');
        if (!group) return;
        var show = _activeTab === 'tab-trend' || _activeTab === 'tab-anomaly';
        group.style.display = show ? '' : 'none';
    }

    /** 初始化数据源栏 */
    function initDataSource() {
        loadModels();

        var modelSelect = el('ml-model-select');
        if (modelSelect) {
            modelSelect.addEventListener('change', function () {
                var fanModel = this.value;
                if (!fanModel) {
                    _modelDataCache = null;
                    _panelFilled = false;
                    var summaryEl = el('ml-ds-summary');
                    if (summaryEl) summaryEl.style.display = 'none';
                    return;
                }

                var spinner = el('ml-ds-spinner');
                spinner.style.display = 'inline-block';

                window.safeFetch('/api/ml/model_data/' + encodeURIComponent(fanModel), { method: 'GET' })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        spinner.style.display = 'none';
                        if (data.success) {
                            _modelDataCache = data;
                            fillPanelWithModelData(data);
                        } else {
                            showError(data.error || '获取型号数据失败');
                            _modelDataCache = null;
                        }
                    })
                    .catch(function (err) {
                        spinner.style.display = 'none';
                        showError('获取型号数据失败: ' + (err.message || '网络错误'));
                    });
            });
        }

        var faceSelect = el('ml-face-select');
        if (faceSelect) {
            faceSelect.addEventListener('change', function () {
                if (_modelDataCache) {
                    fillPanelWithModelData(_modelDataCache, this.value);
                }
            });
        }

        var refreshBtn = el('ml-refresh-models');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', function () {
                loadModels();
            });
        }

        var fileInput = el('ml-file-input');
        if (fileInput) {
            fileInput.addEventListener('change', function (e) {
                var file = e.target.files[0];
                if (!file) return;
                if (file.size > 1024 * 1024) {
                    showError('文件大小不能超过 1MB');
                    this.value = '';
                    return;
                }
                var reader = new FileReader();
                reader.onload = function (ev) {
                    try {
                        var content = ev.target.result;
                        var parsed;
                        if (file.name.endsWith('.csv')) {
                            parsed = parseCSVToJSON(content);
                        } else {
                            parsed = JSON.parse(content);
                        }
                        var currentPanel = _activeTab.replace('tab-', '');
                        var inputId = currentPanel + '-input';
                        var textarea = el(inputId);
                        if (textarea) {
                            textarea.value = JSON.stringify(parsed, null, 2);
                        }
                    } catch (err) {
                        showError('文件解析失败: ' + err.message);
                    }
                };
                reader.readAsText(file);
                this.value = '';
            });
        }
    }

    /** 简易 CSV JSON 解析器 */
    function parseCSVToJSON(csvText) {
        var lines = csvText.trim().split(/\r?\n/);
        if (lines.length < 2) throw new Error('CSV ');
        var headers = lines[0].split(',').map(function (h) { return h.trim().replace(/^"|"$/g, ''); });
        var result = [];
        for (var i = 1; i < lines.length; i++) {
            var vals = lines[i].split(',').map(function (v) { return v.trim().replace(/^"|"$/g, ''); });
            var row = {};
            headers.forEach(function (h, idx) {
                var v = vals[idx] || '';
                var num = parseFloat(v);
                row[h] = isNaN(num) ? v : num;
            });
            result.push(row);
        }
        return result;
    }

    const SAMPLE_DATA = {
        trend: [
            { "date": "2025-01-01", "value": 10 }, { "date": "2025-01-02", "value": 12 },
            { "date": "2025-01-03", "value": 14 }, { "date": "2025-01-04", "value": 15 },
            { "date": "2025-01-05", "value": 18 }, { "date": "2025-01-06", "value": 20 },
            { "date": "2025-01-07", "value": 22 }, { "date": "2025-01-08", "value": 23 },
            { "date": "2025-01-09", "value": 25 }, { "date": "2025-01-10", "value": 27 },
            { "date": "2025-01-11", "value": 28 }, { "date": "2025-01-12", "value": 30 },
            { "date": "2025-01-13", "value": 32 }, { "date": "2025-01-14", "value": 33 },
            { "date": "2025-01-15", "value": 35 }, { "date": "2025-01-16", "value": 36 },
            { "date": "2025-01-17", "value": 38 }, { "date": "2025-01-18", "value": 40 },
            { "date": "2025-01-19", "value": 41 }, { "date": "2025-01-20", "value": 43 }
        ],
        metrics: [
            { "date": "2025-01-01", "metric_a": 100, "metric_b": 50, "metric_c": 200 },
            { "date": "2025-01-02", "metric_a": 105, "metric_b": 52, "metric_c": 210 },
            { "date": "2025-01-03", "metric_a": 110, "metric_b": 55, "metric_c": 215 },
            { "date": "2025-01-04", "metric_a": 115, "metric_b": 58, "metric_c": 225 },
            { "date": "2025-01-05", "metric_a": 120, "metric_b": 60, "metric_c": 230 },
            { "date": "2025-01-06", "metric_a": 125, "metric_b": 63, "metric_c": 240 },
            { "date": "2025-01-07", "metric_a": 130, "metric_b": 65, "metric_c": 245 },
            { "date": "2025-01-08", "metric_a": 135, "metric_b": 68, "metric_c": 255 },
            { "date": "2025-01-09", "metric_a": 140, "metric_b": 70, "metric_c": 260 },
            { "date": "2025-01-10", "metric_a": 145, "metric_b": 72, "metric_c": 270 }
        ],
        multi: [
            { "speed": "800rpm", "vibration": 0.5, "temp": 30, "noise": 65 },
            { "speed": "1000rpm", "vibration": 0.8, "temp": 32, "noise": 70 },
            { "speed": "1200rpm", "vibration": 1.0, "temp": 34, "noise": 73 },
            { "speed": "1500rpm", "vibration": 1.2, "temp": 36, "noise": 78 },
            { "speed": "1800rpm", "vibration": 1.5, "temp": 39, "noise": 82 },
            { "speed": "2000rpm", "vibration": 1.8, "temp": 42, "noise": 85 },
            { "speed": "800rpm", "vibration": 0.6, "temp": 31, "noise": 66 },
            { "speed": "1200rpm", "vibration": 1.1, "temp": 35, "noise": 74 },
            { "speed": "1800rpm", "vibration": 1.6, "temp": 40, "noise": 83 }
        ],
        anomaly: [
            { "date": "2025-01-01", "value": 10 }, { "date": "2025-01-02", "value": 12 },
            { "date": "2025-01-03", "value": 11 }, { "date": "2025-01-04", "value": 13 },
            { "date": "2025-01-05", "value": 12 }, { "date": "2025-01-06", "value": 14 },
            { "date": "2025-01-07", "value": 11 }, { "date": "2025-01-08", "value": 13 },
            { "date": "2025-01-09", "value": 50 }, { "date": "2025-01-10", "value": 12 },
            { "date": "2025-01-11", "value": 14 }, { "date": "2025-01-12", "value": 13 },
            { "date": "2025-01-13", "value": 15 }, { "date": "2025-01-14", "value": 8 },
            { "date": "2025-01-15", "value": 14 }, { "date": "2025-01-16", "value": 13 },
            { "date": "2025-01-17", "value": 12 }, { "date": "2025-01-18", "value": 15 },
            { "date": "2025-01-19", "value": 13 }, { "date": "2025-01-20", "value": 14 },
            { "date": "2025-01-21", "value": 2 }, { "date": "2025-01-22", "value": 14 },
            { "date": "2025-01-23", "value": 13 }, { "date": "2025-01-24", "value": 15 },
            { "date": "2025-01-25", "value": 12 }, { "date": "2025-01-26", "value": 14 },
            { "date": "2025-01-27", "value": 55 }, { "date": "2025-01-28", "value": 13 },
            { "date": "2025-01-29", "value": 15 }, { "date": "2025-01-30", "value": 14 }
        ]
    };

    function el(id) { return document.getElementById(id); }

    var escapeHtml = window.escapeHtml || function (text) {
        if (text == null) return '';
        return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    };

    function showError(msg) {
        let banner = el('ml-error');
        banner.textContent = msg;
        banner.classList.add('show');
        setTimeout(function () { banner.classList.remove('show'); }, 6000);
    }

    function hideError() { el('ml-error').classList.remove('show'); }

    function setLoading(panel, show) {
        let loader = el(panel + '-loading');
        if (loader) { loader.classList.toggle('show', show); }
    }

    function showResult(panel) {
        let r = el(panel + '-result');
        if (r) r.classList.add('show');
    }

    function hideResult(panel) {
        let r = el(panel + '-result');
        if (r) r.classList.remove('show');
    }

    function renderStatCards(panel, entries) {
        let container = el(panel + '-stats');
        if (!container) return;
        container.innerHTML = entries.map(function (e) {
            let cls = e.badgeClass ? ' <span class="ml-badge ' + e.badgeClass + '">' + escapeHtml(e.badge) + '</span>' : '';
            return '<div class="ml-stat-card"><div class="ml-stat-value">' + escapeHtml(e.value) + cls + '</div><div class="ml-stat-label">' + escapeHtml(e.label) + '</div></div>';
        }).join('');
    }

    function buildCsrfHeaders() {
        let tokenInput = document.querySelector('input[name="csrf_token"]');
        let token = tokenInput ? tokenInput.value : '';
        return { 'Content-Type': 'application/json', 'X-CSRFToken': token };
    }

    function safeApiCall(url, body, onSuccess, panelName) {
        hideError();
        setLoading(panelName, true);
        hideResult(panelName);

        window.safeFetch(url, {
            method: 'POST',
            headers: buildCsrfHeaders(),
            body: JSON.stringify(body)
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                setLoading(panelName, false);
                if (data.success) {
                    onSuccess(data.result);
                    showResult(panelName);
                } else {
                    showError(data.error || '请求失败');
                }
            })
            .catch(function (err) {
                setLoading(panelName, false);
                showError(err.message || '网络错误，请稍后重试');
            });
    }

    /* ===== Tab Switching ===== */
    function switchTab(tabName) {
        document.querySelectorAll('.ml-toolbar .nav-link').forEach(function (btn) {
            btn.classList.toggle('active', btn.getAttribute('data-ml-tab') === tabName);
        });
        document.querySelectorAll('.ml-tab-panel').forEach(function (panel) {
            panel.style.display = panel.id === tabName ? '' : 'none';
        });
        _activeTab = tabName;
        updateFaceSelectVisibility();
        if (_modelDataCache && !_panelFilled) {
            fillPanelWithModelData(_modelDataCache);
        }
        setTimeout(function() {
            var visiblePanel = document.querySelector('.ml-panel.active .ml-result.show .ml-chart-container');
            if (visiblePanel && visiblePanel.id) {
                try { Plotly.Plots.resize(visiblePanel); } catch(e) {}
            }
        }, 100);
    }

    document.querySelector('.ml-toolbar').addEventListener('click', function (e) {
        let tabBtn = e.target.closest('[data-ml-tab]');
        if (tabBtn) {
            let tabName = tabBtn.getAttribute('data-ml-tab');
            switchTab(tabName);
            history.replaceState(null, '', '#' + tabName);
        }
    });

    /* ===== Sample & Action Buttons ===== */
    document.addEventListener('click', function (e) {
        let sampleBtn = e.target.closest('[data-sample]');
        let runBtn = e.target.closest('[data-run]');
        let clearBtn = e.target.closest('[data-clear]');

        if (sampleBtn) {
            let key = sampleBtn.getAttribute('data-sample');
            if (SAMPLE_DATA[key]) {
                let textarea = el(key + '-input') || el(key.replace('metrics', 'metrics').replace('multi', 'multi').replace('anomaly', 'anomaly') + '-input');
                let targetEl = el(key + '-input');
                if (targetEl) {
                    targetEl.value = JSON.stringify(SAMPLE_DATA[key], null, 2);
                }
            }
        }

        if (runBtn) {
            let panel = runBtn.getAttribute('data-run');
            if (panel === 'trend') runTrend();
            else if (panel === 'metrics') runMetrics();
            else if (panel === 'multi') runMulti();
            else if (panel === 'anomaly') runAnomaly();
        }

        if (clearBtn) {
            let clearKey = clearBtn.getAttribute('data-clear');
            let inputEl = el(clearKey + '-input');
            if (inputEl) inputEl.value = '';
            hideResult(clearKey);
            _modelDataCache = null;
            _panelFilled = false;
            var dsSummary = el('ml-ds-summary');
            if (dsSummary) dsSummary.style.display = 'none';
        }
    });

    /* ===== Trend Prediction ===== */
    function runTrend() {
        let raw = el('trend-input').value.trim();
        if (!raw) { showError('请输入历史数据 JSON'); return; }
        let historicalData;
        try { historicalData = JSON.parse(raw); } catch (e) { showError('JSON 格式错误: ' + e.message); return; }
        if (!Array.isArray(historicalData)) { showError('数据应为数组格式'); return; }

        let days = parseInt(el('trend-days').value) || 7;
        let model = el('trend-model').value || 'random_forest';

        safeApiCall('/api/predict_trend', {
            historical_data: historicalData,
            prediction_days: Math.max(1, Math.min(365, days)),
            model_type: model
        }, function (result) {
            renderTrendResult(result);
        }, 'trend');
    }

    function renderTrendResult(result) {
        let hist = result.historical_data || [];
        let pred = result.prediction_data || [];
        let metrics = result.model_metrics || {};
        let confidence = result.confidence || {};

        let badgeClass = confidence.confidence_level === 'high' ? 'ml-badge-high' :
            confidence.confidence_level === 'medium' ? 'ml-badge-medium' : 'ml-badge-low';
        renderStatCards('trend', [
            { value: (confidence.r2_score != null && Number.isFinite(confidence.r2_score) ? confidence.r2_score.toFixed(4) : '-'), label: 'R² Score', badge: confidence.confidence_level || '-', badgeClass: badgeClass },
            { value: (confidence.rmse != null && Number.isFinite(confidence.rmse) ? confidence.rmse.toFixed(4) : '-'), label: 'RMSE' },
            { value: confidence.n_samples || '-', label: '样本数' },
            { value: result.model_type || '-', label: '模型' }
        ]);

        let histDates = hist.map(function (d) { return d.date; });
        let histValues = hist.map(function (d) { return d.value; });
        let predDates = pred.map(function (d) { return d.date; });
        let predValues = pred.map(function (d) { return d.value; });

        let traceHist = { x: histDates, y: histValues, type: 'scatter', mode: 'lines+markers', name: '历史数据', line: { color: '#2563eb', width: 2 } };

        let boundaryX = histDates.length > 0 ? [histDates[histDates.length - 1], predDates[0]] : [];
        let boundaryY = histValues.length > 0 && predValues.length > 0 ? [histValues[histValues.length - 1], predValues[0]] : [];

        let traces = [traceHist];
        if (boundaryX.length === 2 && predDates.length > 0) {
            traces.push({ x: boundaryX, y: boundaryY, type: 'scatter', mode: 'lines', name: '预测边界', line: { color: '#94a3b8', dash: 'dash', width: 2 } });
            traces.push({ x: predDates, y: predValues, type: 'scatter', mode: 'lines+markers', name: '预测值', line: { color: '#ef4444', width: 2 }, marker: { color: '#ef4444', size: 6 } });
        }

        Plotly.newPlot('trend-chart', traces, {
            title: '趋势预测 (' + (result.prediction_days || '?') + '天)',
            xaxis: { title: '日期', gridcolor: '#f1f5f9' },
            yaxis: { title: '预测值', gridcolor: '#f1f5f9' },
            legend: { orientation: 'h', y: 1.15 },
            margin: { l: 50, r: 20, t: 50, b: 50 }
        }, { responsive: true, displayModeBar: false });

        setTimeout(function() {
            try { Plotly.Plots.resize('trend-chart'); } catch(e) {}
        }, 200);
    }

    /* ===== Key Metrics Prediction ===== */
    function runMetrics() {
        let raw = el('metrics-input').value.trim();
        if (!raw) { showError('请输入历史指标数据 JSON'); return; }
        let historicalMetrics;
        try { historicalMetrics = JSON.parse(raw); } catch (e) { showError('JSON 格式错误: ' + e.message); return; }
        if (!Array.isArray(historicalMetrics)) { showError('数据应为数组格式'); return; }

        let periods = parseInt(el('metrics-periods').value) || 6;
        let model = el('metrics-model').value || 'gradient_boosting';

        safeApiCall('/api/predict_key_metrics', {
            historical_metrics: historicalMetrics,
            prediction_periods: Math.max(1, Math.min(120, periods)),
            model_type: model
        }, function (result) {
            renderMetricsResult(result);
        }, 'metrics');
    }

    function renderMetricsResult(result) {
        let confidence = result.confidence || {};
        let predictions = result.predictions || {};
        let metricsResults = result.metrics_results || {};
        let metricNames = Object.keys(predictions);

        let stats = [];
        metricNames.forEach(function (m) {
            let ci = confidence[m] || {};
            stats.push({ value: ci.r2_score != null && Number.isFinite(ci.r2_score) ? ci.r2_score.toFixed(4) : '-', label: m + ' R²' });
        });
        stats.push({ value: result.prediction_periods || '-', label: '预测周期' });
        stats.push({ value: result.model_type || '-', label: '模型' });
        renderStatCards('metrics', stats);

        let traces = [];
        let histData = result.historical_data || [];
        let histLen = histData.length;
        metricNames.forEach(function (m) {
            let histVals = histData.map(function (d) { return d[m]; });
            let predVals = predictions[m] || [];
            let xs = [];
            for (let i = 0; i < histLen + predVals.length; i++) {
                xs.push(i < histLen ? 'H' + (i + 1) : 'P' + (i - histLen + 1));
            }
            traces.push({ x: xs.slice(0, histLen), y: histVals, type: 'scatter', mode: 'lines+markers', name: m + ' (历史)', line: { width: 2 } });
            if (predVals.length > 0) {
                let allVals = histVals.concat(predVals);
                traces.push({ x: xs, y: allVals, type: 'scatter', mode: 'lines+markers', name: m + ' (预测)', line: { dash: 'dash', width: 2 }, marker: { symbol: 'diamond' } });
            }
        });

        Plotly.newPlot('metrics-chart', traces, {
            title: '关键指标多步预测',
            xaxis: { title: '时间步', gridcolor: '#f1f5f9' },
            yaxis: { title: '指标值', gridcolor: '#f1f5f9' },
            legend: { orientation: 'h', y: 1.15 },
            margin: { l: 50, r: 20, t: 50, b: 50 }
        }, { responsive: true, displayModeBar: false });

        setTimeout(function() {
            try { Plotly.Plots.resize('metrics-chart'); } catch(e) {}
        }, 200);
    }

    /* ===== Multi-Dimensional Analysis ===== */
    function runMulti() {
        let raw = el('multi-input').value.trim();
        if (!raw) { showError('请输入分析数据 JSON'); return; }
        let analysisData;
        try { analysisData = JSON.parse(raw); } catch (e) { showError('JSON 格式错误: ' + e.message); return; }
        if (!Array.isArray(analysisData)) { showError('数据应为数组格式'); return; }

        let dimensions = el('multi-dimensions').value.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
        let metrics = el('multi-metrics').value.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
        if (dimensions.length === 0) { showError('请至少输入一个维度'); return; }
        if (metrics.length === 0) { showError('请至少输入一个指标'); return; }

        safeApiCall('/api/multi_dimensional_analysis', {
            data: analysisData,
            dimensions: dimensions,
            metrics: metrics
        }, function (result) {
            renderMultiResult(result);
        }, 'multi');
    }

    function renderMultiResult(result) {
        let confidence = result.confidence || {};
        let badgeClass = confidence.confidence_level === 'high' ? 'ml-badge-high' :
            confidence.confidence_level === 'medium' ? 'ml-badge-medium' : 'ml-badge-low';
        renderStatCards('multi', [
            { value: confidence.n_samples || '-', label: '样本数' },
            { value: confidence.n_dimensions || '-', label: '维度数' },
            { value: confidence.n_metrics || '-', label: '指标数' },
            { value: confidence.n_groups || '-', label: '分组数', badge: confidence.confidence_level || '', badgeClass: badgeClass }
        ]);

        let detailed = result.detailed || [];
        if (detailed.length === 0) { el('multi-table').innerHTML = '<tr><td class="text-center text-muted py-3">无分组数据</td></tr>'; return; }

        let keys = Object.keys(detailed[0]);
        let thead = '<thead><tr>' + keys.map(function (k) { return '<th>' + escapeHtml(k) + '</th>'; }).join('') + '</tr></thead>';
        let tbody = '<tbody>' + detailed.map(function (row) {
            return '<tr>' + keys.map(function (k) {
                let v = row[k];
                if (typeof v === 'number') return '<td>' + (Number.isFinite(v) ? (Number.isInteger(v) ? v : v.toFixed(4)) : '-') + '</td>';
                return '<td>' + escapeHtml(v != null ? v : '-') + '</td>';
            }).join('') + '</tr>';
        }).join('') + '</tbody>';
        el('multi-table').innerHTML = thead + tbody;
    }

    /* ===== Anomaly Detection ===== */
    function runAnomaly() {
        let raw = el('anomaly-input').value.trim();
        if (!raw) { showError('请输入时间序列数据 JSON'); return; }
        let timeSeriesData;
        try { timeSeriesData = JSON.parse(raw); } catch (e) { showError('JSON 格式错误: ' + e.message); return; }
        if (!Array.isArray(timeSeriesData)) { showError('数据应为数组格式'); return; }

        let windowSize = parseInt(el('anomaly-window').value) || 7;
        let threshold = parseFloat(el('anomaly-threshold').value) || 2.0;

        safeApiCall('/api/detect_anomaly_patterns', {
            time_series_data: timeSeriesData,
            window_size: Math.max(2, Math.min(100, windowSize)),
            threshold: Math.max(0.5, Math.min(5.0, threshold))
        }, function (result) {
            renderAnomalyResult(result, timeSeriesData);
        }, 'anomaly');
    }

    function renderAnomalyResult(result, rawData) {
        let anomalies = result.anomalies || [];
        let confidence = result.confidence || {};
        let diagnostic = result.diagnostic || {};

        let badgeClass = diagnostic.status === 'ok' && confidence.confidence_level === 'high' ? 'ml-badge-high' :
            diagnostic.status === 'ok' ? 'ml-badge-medium' : 'ml-badge-low';
        renderStatCards('anomaly', [
            { value: confidence.anomaly_count || 0, label: '异常点数', badge: diagnostic.status === 'ok' ? (confidence.anomaly_count > 0 ? '有异常' : '无异常') : '-', badgeClass: badgeClass },
            { value: (confidence.anomaly_rate_percent != null && Number.isFinite(confidence.anomaly_rate_percent) ? confidence.anomaly_rate_percent.toFixed(1) + '%' : '-'), label: '异常率' },
            { value: confidence.n_samples || '-', label: '样本数' },
            { value: confidence.window_size || '-', label: '窗口大小' }
        ]);

        let dates = rawData.map(function (d) { return d.date; });
        let values = rawData.map(function (d) { return d.value; });
        let anomalyIndices = {};
        anomalies.forEach(function (a) { anomalyIndices[a.date] = a; });

        let normalX = [], normalY = [], anomalyX = [], anomalyY = [];
        rawData.forEach(function (d) {
            if (anomalyIndices[d.date]) { anomalyX.push(d.date); anomalyY.push(d.value); }
            else { normalX.push(d.date); normalY.push(d.value); }
        });

        let traces = [
            { x: normalX, y: normalY, type: 'scatter', mode: 'lines+markers', name: '正常值', line: { color: '#2563eb', width: 1.5 }, marker: { size: 4 } }
        ];
        if (anomalyX.length > 0) {
            traces.push({ x: anomalyX, y: anomalyY, type: 'scatter', mode: 'markers', name: '异常点', marker: { color: '#ef4444', size: 10, symbol: 'x' } });
        }

        Plotly.newPlot('anomaly-chart', traces, {
            title: '异常模式检测 (窗口=' + (confidence.window_size || '?') + ', 阈值=' + (confidence.threshold || '?') + ')',
            xaxis: { title: '日期', gridcolor: '#f1f5f9' },
            yaxis: { title: '值', gridcolor: '#f1f5f9' },
            legend: { orientation: 'h', y: 1.15 },
            margin: { l: 50, r: 20, t: 50, b: 50 }
        }, { responsive: true, displayModeBar: false });

        setTimeout(function() {
            try { Plotly.Plots.resize('anomaly-chart'); } catch(e) {}
        }, 200);

        let anomalyTable = el('anomaly-table');
        if (anomalies.length === 0) {
            anomalyTable.innerHTML = '<tr><td class="text-center text-muted py-3">' + escapeHtml(diagnostic.message || '未检测到异常点') + '</td></tr>';
        } else {
            const headerKeys = ['date', 'value', 'z_score', 'anomaly_type'];
            anomalyTable.innerHTML = '<thead><tr>' + headerKeys.map(function (k) { return '<th>' + k + '</th>'; }).join('') + '</tr></thead><tbody>' +
                anomalies.map(function (a) {
                    return '<tr>' + headerKeys.map(function (k) {
                        let v = a[k];
                        if (k === 'z_score' && typeof v === 'number') return '<td>' + (Number.isFinite(v) ? v.toFixed(4) : '-') + '</td>';
                        if (k === 'anomaly_type') return '<td><span class="ml-badge ' + (v === 'high' ? 'ml-badge-low' : 'ml-badge-medium') + '">' + (v === 'high' ? '偏高' : '偏低') + '</span></td>';
                        return '<td>' + escapeHtml(v != null ? v : '-') + '</td>';
                    }).join('') + '</tr>';
                }).join('') + '</tbody>';
        }
    }

    (function initFromHash() {
        let hash = window.location.hash.replace('#', '');
        const validTabs = ['trend', 'metrics', 'multi', 'anomaly'];
        if (hash && validTabs.indexOf(hash) >= 0) {
            switchTab(hash);
        }
    })();

    (function initDataSourceOnLoad() {
        window.safeFetch('/api/ml/models', { method: 'GET' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success || data.error) {
                    var dsBar = el('ml-datasource');
                    if (dsBar) dsBar.style.display = '';
                }
            })
            .catch(function () {
                // API unreachable — DB not connected — keep hidden
            });
        initDataSource();
    })();

})();