(function() {
    'use strict';

    var _items = [];
    var _filter = 'all';
    var _data = null;

    function getCsrfToken() {
        return document.querySelector('input[name="csrf_token"]')?.value || '';
    }

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.textContent = str == null ? '' : String(str);
        return div.innerHTML;
    }

    // 属性值转义：escapeHtml 不转义引号，直接拼进 data-* 属性会被拆穿
    function escapeAttr(str) {
        return escapeHtml(str).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function statusText(s) {
        return { fresh: '24小时内', recent: '7天内', stale: '超7天', old: '超30天' }[s] || '未知';
    }

    function fmtTime(t) {
        if (!t) return '--';
        return t.replace('T', ' ').substring(0, 16);
    }

    function loadData() {
        var grid = document.getElementById('mmCardGrid');
        grid.innerHTML = '<div class="mm-loading"><div class="spinner-border text-primary mb-3"></div><p class="text-muted">正在加载机型监控数据...</p></div>';

        var opts = {
            method: 'GET',
            headers: { 'X-CSRFToken': getCsrfToken() }
        };
        // refresh=1 让后端强制失效 60s 缓存，否则点刷新在缓存期内看不到变化
        fetch('/api/outputs/model_monitor?refresh=1', opts)
            .then(function(r) { return r.json(); })
            .then(function(resp) {
                if (!resp.success) throw new Error(resp.error || '加载失败');
                _data = resp;
                _items = resp.items || [];
                renderStats(resp);
                renderAlertBar(resp);
                renderGrid();
            })
            .catch(function(err) {
                grid.innerHTML = '<div class="mm-loading"><p class="text-danger">加载失败: ' + escapeHtml(err.message) + '</p><button class="btn btn-outline-primary btn-sm mt-2" onclick="location.reload()"><i class="bi bi-arrow-clockwise me-1"></i>重试</button></div>';
            });
    }

    function renderStats(resp) {
        document.getElementById('mmStatModels').textContent = (resp.items || []).length;
        document.getElementById('mmStatAlerts').textContent = resp.alert_count || 0;
        document.getElementById('mmStatCritical').textContent = resp.critical_count || 0;
        var latest = '--';
        var items = resp.items || [];
        items.forEach(function(i) {
            if (i.latest_time && (!latest || latest === '--' || i.latest_time > latest)) latest = i.latest_time;
        });
        document.getElementById('mmStatLatest').textContent = fmtTime(latest);
    }

    function renderAlertBar(resp) {
        var bar = document.getElementById('mmAlertBar');
        var items = resp.items || [];
        var critical = items.filter(function(i) { return i.status === 'old'; });
        var stale = items.filter(function(i) { return i.status === 'stale'; });
        var parts = [];
        if (critical.length) parts.push(critical.length + ' 个机型超30天未分析');
        if (stale.length) parts.push(stale.length + ' 个机型超7天未分析');
        items.forEach(function(i) {
            if (i.speed_changed) parts.push('「' + i.model + '」推荐转速有变化');
            if (i.missing) parts.push('「' + i.model + '」' + i.missing);
        });
        if (!parts.length) {
            bar.style.display = 'none';
            return;
        }
        bar.style.display = 'block';
        bar.className = 'mm-alert-bar ' + (critical.length ? 'critical' : 'warn');
        bar.innerHTML = '<i class="bi bi-bell-fill me-2"></i>' + parts.slice(0, 4).join('；') + (parts.length > 4 ? '；等' + parts.length + ' 项' : '');
    }

    function renderGrid() {
        var grid = document.getElementById('mmCardGrid');
        var items = _items.filter(function(i) {
            if (_filter === 'all') return true;
            if (_filter === 'alert') return i.status === 'stale' || i.status === 'old' || i.speed_changed || i.missing;
            if (_filter === 'stale') return i.status === 'stale' || i.status === 'old';
            if (_filter === 'speed') return i.speed_changed;
            if (_filter === 'missing') return !!i.missing;
            return true;
        });

        document.getElementById('mmResultCount').textContent = '共 ' + items.length + ' 个机型';

        if (!items.length) {
            grid.innerHTML = '<div class="mm-loading"><div class="bi bi-inbox" style="font-size:3rem;color:#94a3b8;"></div><p class="text-muted mt-2">暂无监控数据</p></div>';
            return;
        }

        var html = '';
        items.forEach(function(i) {
            var badges = '';
            if (i.status === 'old') badges += '<span class="mm-badge crit">超30天</span>';
            else if (i.status === 'stale') badges += '<span class="mm-badge warn">超7天</span>';
            if (i.speed_changed) badges += '<span class="mm-badge warn">转速变化</span>';
            if (i.missing) badges += '<span class="mm-badge warn">' + escapeHtml(i.missing) + '</span>';

            var speed = i.best_speed ? '<span class="mm-speed-value">' + escapeHtml(i.best_speed) + '</span><span class="mm-speed-label">推荐转速</span>'
                : '<span class="mm-speed-label">暂无推荐转速记录</span>';
            var device = i.device
                ? '<div class="mm-device-row"><i class="bi bi-gear-wide-connected"></i>使用设备：' + escapeHtml(i.device) + '</div>'
                : '<div class="mm-device-row"><i class="bi bi-gear-wide-connected"></i>使用设备：未记录</div>';

            html += '<div class="mm-card status-' + i.status + '" data-model="' + escapeAttr(i.model) + '">' +
                '<div class="mm-card-head" data-model="' + escapeAttr(i.model) + '" title="点击查看转速历史">' +
                    '<span class="mm-status-dot ' + i.status + '"></span>' +
                    '<span class="mm-card-model">' + escapeHtml(i.model) + '</span>' +
                    badges +
                '</div>' +
                '<div class="mm-card-body">' +
                    '<div class="mm-speed-row">' + speed + '</div>' +
                    device +
                    '<div class="mm-meta-row">' +
                        '<span><i class="bi bi-clock me-1"></i>' + fmtTime(i.latest_time) + '（' + statusText(i.status) + '）</span>' +
                        '<span><i class="bi bi-file-earmark me-1"></i>报告 ' + (i.report_count || 0) + '</span>' +
                        '<span><i class="bi bi-list-ul me-1"></i>历史 ' + (i.history_count || 0) + ' 次</span>' +
                    '</div>' +
                '</div>' +
                '<div class="mm-card-foot">' +
                    '<button class="btn btn-outline-primary btn-sm mm-hist-btn" data-model="' + escapeAttr(i.model) + '"><i class="bi bi-clock-history me-1"></i>转速历史</button>' +
                    '<a class="btn btn-outline-secondary btn-sm" href="/outputs"><i class="bi bi-folder2-open me-1"></i>报告管理</a>' +
                    '<a class="btn btn-outline-success btn-sm" href="/api/outputs/batch_download?fan_model=' + encodeURIComponent(i.model) + '"><i class="bi bi-download me-1"></i>打包</a>' +
                '</div>' +
            '</div>';
        });
        grid.innerHTML = html;
        bindEvents();
    }

    function bindEvents() {
        document.querySelectorAll('.mm-card-head').forEach(function(head) {
            head.addEventListener('click', function() {
                var model = head.dataset.model;
                openHistory(model);
            });
        });
        document.querySelectorAll('.mm-hist-btn').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                openHistory(btn.dataset.model);
            });
        });
    }

    function openHistory(model) {
        var item = _items.find(function(i) { return i.model === model; });
        if (!item) return;
        document.getElementById('mmHistoryTitle').innerHTML = '<i class="bi bi-clock-history me-2"></i>' + escapeHtml(model) + ' — 推荐转速历史';
        var body = document.getElementById('mmHistoryBody');
        var hist = item.history || [];
        if (!hist.length) {
            body.innerHTML = '<div class="text-center py-4 text-muted">暂无转速记录</div>';
        } else {
            var html = '<ul class="mm-history-list">';
            hist.slice().reverse().forEach(function(h) {
                var sp = (h.best_speeds || []).join('、') || '--';
                html += '<li>' +
                    '<span><span class="mm-history-speed">' + escapeHtml(sp) + '</span> <span class="mm-history-muted">' + escapeHtml(h.device || '设备未记录') + '</span></span>' +
                    '<span class="mm-history-muted">' + fmtTime(h.time) + '</span>' +
                '</li>';
            });
            html += '</ul>';
            body.innerHTML = html;
        }
        new bootstrap.Modal(document.getElementById('mmHistoryModal')).show();
    }

    function init() {
        loadData();
        document.getElementById('mmRefreshBtn').addEventListener('click', loadData);
        document.querySelectorAll('.mm-filter-chip').forEach(function(chip) {
            chip.addEventListener('click', function() {
                document.querySelectorAll('.mm-filter-chip').forEach(function(c) { c.classList.remove('active'); });
                chip.classList.add('active');
                _filter = chip.dataset.filter;
                renderGrid();
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
