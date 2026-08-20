function initDashboardCharts(onlyId) {
    var d = (typeof _dash !== 'undefined') ? _dash : null;
    if (!d || (!d.evaluation_dates.length && !d.speed_labels.length && !d.model_labels.length)) {
        showEmptyState();
        return;
    }

    var colors = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

    function wanted(id) {
        return !onlyId || id === onlyId;
    }

    var trendEl = document.getElementById('trendChart');
    var modelEl = document.getElementById('modelChart');
    var speedEl = document.getElementById('speedChart');

    if (trendEl && d.evaluation_dates.length && wanted('trendChart')) {
        Plotly.newPlot('trendChart', [{
            x: d.evaluation_dates,
            y: d.evaluation_counts,
            type: 'bar',
            marker: { color: '#2563eb', opacity: 0.85 },
            hovertemplate: '%{x}<br>评估次数: %{y}<extra></extra>'
        }], {
            margin: { t: 10, r: 20, b: 40, l: 50 },
            xaxis: { dtick: 1 },
            bargap: 0.3,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent'
        }, { responsive: true, displayModeBar: false });
    }

    if (modelEl && d.model_labels.length && wanted('modelChart')) {
        Plotly.newPlot('modelChart', [{
            labels: d.model_labels,
            values: d.model_counts,
            type: 'pie',
            hole: 0.55,
            marker: { colors: colors },
            textinfo: 'label+percent',
            textposition: 'outside',
            hovertemplate: '%{label}: %{value}次<extra></extra>'
        }], {
            margin: { t: 10, r: 20, b: 20, l: 20 },
            paper_bgcolor: 'transparent',
            showlegend: false
        }, { responsive: true, displayModeBar: false });
    }

    if (speedEl && d.speed_labels.length && wanted('speedChart')) {
        Plotly.newPlot('speedChart', [{
            x: d.speed_labels,
            y: d.speed_counts,
            type: 'bar',
            marker: { color: colors.slice(0, d.speed_labels.length) },
            hovertemplate: '%{x}: %{y}次<extra></extra>'
        }], {
            margin: { t: 10, r: 20, b: 40, l: 50 },
            bargap: 0.35,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent'
        }, { responsive: true, displayModeBar: false });
    }
}

function showEmptyState() {
    ['trendChart', 'modelChart', 'speedChart'].forEach(function(id) {
        var el = document.getElementById(id);
        if (el) el.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100"><p class="text-muted"><i class="bi bi-bar-chart me-2"></i>暂无数据</p></div>';
    });
}

function refreshCharts(targetId) {
    var fetchFn = typeof window.safeFetch === 'function' ? window.safeFetch : fetch;
    fetchFn('/api/dashboard/data')
        .then(function(res) { return res.ok ? res.json() : Promise.reject(res); })
        .then(function(json) {
            if (json.data) {
                _dash = {
                    evaluation_dates: json.data.evaluation_dates || [],
                    evaluation_counts: json.data.evaluation_counts || [],
                    speed_labels: json.data.speed_labels || [],
                    speed_counts: json.data.speed_counts || [],
                    model_labels: json.data.model_labels || [],
                    model_counts: json.data.model_counts || []
                };
                var ids = targetId ? [targetId] : ['trendChart', 'modelChart', 'speedChart'];
                ids.forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) Plotly.purge(el);
                });
                initDashboardCharts(targetId);
            }
        })
        .catch(function() {
            var ids = targetId ? [targetId] : ['trendChart', 'modelChart', 'speedChart'];
            ids.forEach(function(id) {
                var el = document.getElementById(id);
                if (el) Plotly.purge(el);
            });
            initDashboardCharts(targetId);
        });
}

var _chartButtons = {
    refreshTrendChart: 'trendChart',
    refreshModelChart: 'modelChart',
    refreshSpeedChart: 'speedChart'
};
Object.keys(_chartButtons).forEach(function(btnId) {
    var btn = document.getElementById(btnId);
    if (btn) btn.addEventListener('click', function() {
        var orig = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>刷新中...';
        refreshCharts(_chartButtons[btnId]).finally(function() {
            btn.disabled = false;
            btn.innerHTML = orig;
        });
    });
});
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboardCharts);
} else {
    initDashboardCharts();
}
