'use strict';

(function () {
    let csrfToken = '';

    function getCsrfToken() {
        if (!csrfToken) {
            let el = document.querySelector('input[name="csrf_token"]');
            csrfToken = el ? el.value : '';
        }
        return csrfToken;
    }

    function showToast(type, message) {
        let stack = document.getElementById('settingsToastStack');
        if (!stack) return;
        const bgMap = { success: 'bg-success', danger: 'bg-danger', warning: 'bg-warning', info: 'bg-info' };
        const iconMap = { success: 'bi-check-circle', danger: 'bi-x-circle', warning: 'bi-exclamation-triangle', info: 'bi-info-circle' };
        let toast = document.createElement('div');
        toast.className = 'toast show auto-toast text-white ' + (bgMap[type] || 'bg-secondary');
        toast.setAttribute('role', 'alert');
        toast.innerHTML = '<div class="d-flex"><div class="toast-body"><i class="bi ' + (iconMap[type] || 'bi-bell') + ' me-2"></i>' + escapeHtml(message) + '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
        stack.appendChild(toast);
        setTimeout(function () { if (toast.parentNode) toast.remove(); }, 5000);
    }

    function escapeHtml(str) {
        let div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    function fetchApi(url, options) {
        let opts = options || {};
        opts.headers = opts.headers || {};
        opts.headers['X-CSRFToken'] = getCsrfToken();
        return fetch(url, opts).then(function (resp) {
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            return resp.json();
        });
    }

    let connectionHealthCache = {};

    function refreshDbStatus() {
        fetchApi('/api/db_status')
            .then(function (data) {
                if (!data.success || !data.data) return;
                renderMainDbStatus(data.data.main_db);
                renderConnectionList(data.data.saved_connections);
                renderPoolStatus(data.data.pool_status);
            })
            .catch(function (err) {
                console.error('数据库状态刷新失败:', err);
                let dot = document.getElementById('heroStatusDot');
                if (dot) {
                    dot.style.backgroundColor = 'var(--danger-color, #dc3545)';
                    dot.style.boxShadow = '0 0 6px var(--danger-color, #dc3545)';
                }
                let mainEl = document.getElementById('mainDbStatus');
                if (mainEl) {
                    mainEl.className = 'db-status-indicator disconnected';
                    mainEl.innerHTML = '<i class="bi bi-database-exclamation"></i>';
                }
                let infoEl = document.getElementById('mainDbInfo');
                if (infoEl) {
                    let badge = infoEl.querySelector('.db-status-badge');
                    if (badge) {
                        badge.textContent = '● 错误';
                        badge.className = 'db-status-badge inactive';
                    }
                    let detail = infoEl.querySelector('.db-detail');
                    if (detail) detail.textContent = '状态刷新失败，请检查网络';
                }
            });
    }

    function renderMainDbStatus(status) {
        let el = document.getElementById('mainDbStatus');
        if (!el) return;
        let connected = status && status.connected && status.responsive;
        let iconClass = connected ? 'connected' : 'disconnected';
        let icon = connected ? 'bi-database-check' : 'bi-database-exclamation';
        let dbType = status && status.db_type ? status.db_type : '';
        let label = dbType ? dbType + ' · ' + (connected ? '已连接' : '未连接') : (connected ? '已连接' : '未连接');
        // 优先显示响应性错误，其次显示连接错误，最后显示默认文本
        let detail;
        if (status && status.connected && !status.responsive) {
            detail = status.error || '数据库连接异常（无响应）';
        } else if (status && status.connected) {
            detail = 'SQLAlchemy 响应正常';
        } else {
            detail = (status && status.error) ? status.error : '数据库未初始化';
        }

        el.className = 'db-status-indicator ' + iconClass;
        el.innerHTML = '<i class="bi ' + icon + '"></i>';

        let infoEl = document.getElementById('mainDbInfo');
        if (infoEl) {
            infoEl.querySelector('strong').textContent = '主数据库';
            infoEl.querySelector('.db-type-label').textContent = label;
            infoEl.querySelector('.db-detail').textContent = detail;
            let badge = infoEl.querySelector('.db-status-badge');
            if (badge) {
                badge.textContent = connected ? '● 在线' : '● 离线';
                badge.className = 'db-status-badge ' + (connected ? 'active' : 'inactive');
            }
        }
    }

    function renderConnectionList(connections) {
        let listEl = document.getElementById('connectionsListBody');
        if (!listEl) return;
        listEl.innerHTML = '';
        if (!connections || !connections.length || connections.error) {
            listEl.innerHTML = '<div class="text-center py-3 text-muted small"><i class="bi bi-inbox d-block mb-2 opacity-50"></i>暂无已保存的连接</div>';
            return;
        }
        connections.forEach(function (conn) {
            let statusClass = conn.status === 'active' ? 'active' : 'inactive';
            let statusText = conn.status === 'active' ? '● 活跃' : '● 休眠';
            let iconLetter = conn.type.charAt(0).toUpperCase();
            let item = document.createElement('div');
            item.className = 'connection-list-item';
            item.setAttribute('data-id', conn.id);
            item.innerHTML =
                '<div class="conn-info">' +
                    '<div class="conn-icon ' + escapeHtml(conn.type) + '">' + iconLetter + '</div>' +
                    '<div>' +
                        '<strong class="d-block">' + escapeHtml(conn.name) + '</strong>' +
                        '<small class="text-muted">' + escapeHtml(conn.type.toUpperCase()) + ' · ' + escapeHtml(conn.host || '—') + '</small>' +
                    '</div>' +
                '</div>' +
                '<div class="conn-actions">' +
                    '<span class="db-status-badge ' + statusClass + '">' + statusText + '</span>' +
                    '<button class="btn btn-sm btn-outline-primary health-check-btn" data-id="' + conn.id + '">' +
                        '<span class="health-check-spinner"></span> 检测' +
                    '</button>' +
                '</div>';
            item.addEventListener('click', function (e) {
                if (e.target.closest('.health-check-btn')) return;
                loadConnectionForEdit(conn.id);
            });
            listEl.appendChild(item);
        });
        bindHealthCheckButtons();
    }

    function bindHealthCheckButtons() {
        document.querySelectorAll('.health-check-btn').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                let id = this.getAttribute('data-id');
                let spinner = this.querySelector('.health-check-spinner');
                spinner.style.display = 'inline-block';
                this.textContent = '';
                this.appendChild(spinner);
                this.disabled = true;

                let formData = new FormData();
                formData.append('connection_id', id);

                fetch('/api/connection_health', {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-CSRFToken': getCsrfToken() }
                })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.success) {
                        connectionHealthCache[id] = { status: 'active', time: new Date().toLocaleTimeString() };
                        showToast('success', '连接正常 — ' + (data.message || 'OK'));
                    } else {
                        connectionHealthCache[id] = { status: 'error', time: new Date().toLocaleTimeString() };
                        showToast('danger', '连接失败 — ' + (data.message || 'Error'));
                    }
                    refreshDbStatus();
                })
                .catch(function () {
                    showToast('danger', '健康检查请求失败');
                })
                .finally(function () {
                    btn.disabled = false;
                    btn.innerHTML = '<span class="health-check-spinner"></span> 检测';
                });
            });
        });
    }

    function loadConnectionForEdit(id) {
        fetch('/get_connection?id=' + id)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.success || !data.connection) return;
                let conn = data.connection;
                document.getElementById('connection_id').value = conn.id;
                document.getElementById('connection_name').value = conn.name;
                document.getElementById('connection_type').value = conn.type;
                document.getElementById('connection_type').dispatchEvent(new Event('change'));
                setTimeout(function () {
                    let hostEl = document.getElementById('host');
                    let portEl = document.getElementById('port');
                    let dbEl = document.getElementById('database');
                    let userEl = document.getElementById('username');
                    if (hostEl) hostEl.value = conn.host || '';
                    if (portEl) portEl.value = conn.port || '';
                    if (dbEl) dbEl.value = conn.database || '';
                    if (userEl) userEl.value = conn.username || '';
                    document.getElementById('password').value = '';
                }, 50);
                document.getElementById('deleteConnectionBtn').style.display = 'inline-block';
                document.getElementById('connectionFormCard').scrollIntoView({ behavior: 'smooth' });
            })
            .catch(function () { showToast('danger', '加载连接详情失败'); });
    }

    function renderPoolStatus(status) {
        let el = document.getElementById('dbPoolInfo');
        if (!el) return;
        let total = status && status.total_connections !== undefined ? status.total_connections : 0;
        let cached = status && status.cached_connections !== undefined ? status.cached_connections : 0;
        el.innerHTML =
            '<strong>连接池</strong>' +
            '<span class="db-type-label">' + total + ' 条配置 · ' + cached + ' 个缓存</span>' +
            '<span class="db-detail">' + (status && status.available ? '可用' : '不可用') + '</span>' +
            '<span class="db-status-badge ' + (status && status.available ? 'active' : 'inactive') + '">' +
                (status && status.available ? '● 就绪' : '● 异常') + '</span>';
    }

    function updateWeightsUI() {
        let w1 = parseFloat(document.getElementById('weight_p1').value);
        let w2 = parseFloat(document.getElementById('weight_p2').value);
        let w3 = parseFloat(document.getElementById('weight_st').value);

        document.getElementById('weight_p1_val').textContent = w1.toFixed(2);
        document.getElementById('weight_p2_val').textContent = w2.toFixed(2);
        document.getElementById('weight_st_val').textContent = w3.toFixed(2);

        let detail = '';
        if (Math.abs(w1 - w2) < 0.01 && w1 > w3) {
            detail = 'P1/P2权重相等（' + w1.toFixed(2) + '），前后端面同等重要；ST面权重' + w3.toFixed(2) + '作为辅助参考。';
        } else if (w1 > w2 && w1 > w3) {
            detail = 'P1端面权重最高（' + w1.toFixed(2) + '），系统将优先选择P1端面数据更稳定的转速。';
        } else if (w2 > w1 && w2 > w3) {
            detail = 'P2端面权重最高（' + w2.toFixed(2) + '），系统将优先选择P2端面数据更稳定的转速。';
        } else if (w3 > w1 && w3 > w2) {
            detail = 'ST端面权重最高（' + w3.toFixed(2) + '），系统将优先选择ST端面数据更稳定的转速。';
        } else {
            detail = '三个端面权重大致均衡。';
        }

        let sum = w1 + w2 + w3;
        if (sum < 0.01) {
            detail += ' ⚠️ 所有权重均为0，无法进行有效评分！';
        } else if (Math.abs(sum - 0.5) < 0.01 && sum < 0.99) {
            detail += ' ℹ️ 权重之和为' + sum.toFixed(2) + '，实际运算中会自动归一化处理。';
        }
        document.getElementById('explanation_detail').textContent = detail;
    }

    function showWeightsFeedback(success, message) {
        let fb = document.getElementById('weightsFeedback');
        if (!fb) return;
        fb.classList.remove('d-none');
        fb.className = 'mt-3 alert ' + (success ? 'alert-success' : 'alert-danger');
        fb.innerHTML = message;
        fb.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        setTimeout(function () { fb.classList.add('d-none'); }, 4000);
    }

    function refreshModelTable(highlightId) {
        fetchApi('/api/balancer_models')
            .then(function (resp) {
                if (!resp.success || !resp.data) return;
                let tbody = document.querySelector('#balancerModelsTable tbody');
                if (!tbody) return;
                tbody.innerHTML = '';
                if (resp.data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="text-center empty-row"><i class="bi bi-inbox fs-3 d-block mb-2 opacity-50"></i>暂无平衡机型号，点击"新增型号"添加</td></tr>';
                    return;
                }
                resp.data.forEach(function (m) {
                    let statusBadge = m.is_active ? '<span class="badge bg-success">启用</span>' : '<span class="badge bg-secondary">停用</span>';
                    let highlightClass = (highlightId === m.id) ? ' class="table-primary"' : '';
                    let row = '<tr data-id="' + m.id + '"' + highlightClass + '>' +
                        '<td><strong>' + escapeHtml(m.model_name) + '</strong></td>' +
                        '<td>' + escapeHtml(m.manufacturer || '-') + '</td>' +
                        '<td>' + escapeHtml(m.max_speed || '-') + '</td>' +
                        '<td>' + escapeHtml(m.max_radius || '-') + '</td>' +
                        '<td>' + statusBadge + '</td>' +
                        '<td class="text-muted small">' + escapeHtml(m.updated_at) + '</td>' +
                        '<td class="text-end">' +
                            '<button class="btn btn-sm btn-outline-primary me-1 btnEditModel" data-id="' + m.id + '" title="编辑"><i class="bi bi-pencil"></i></button>' +
                            '<button class="btn btn-sm btn-outline-danger btnDeleteModel" data-id="' + m.id + '" data-name="' + escapeHtml(m.model_name) + '" title="删除"><i class="bi bi-trash"></i></button>' +
                        '</td></tr>';
                    tbody.insertAdjacentHTML('beforeend', row);
                });
                if (highlightId) {
                    setTimeout(function () {
                        let row = document.querySelector('#balancerModelsTable tr[data-id="' + highlightId + '"]');
                        if (row) row.classList.remove('table-primary');
                    }, 2500);
                }
            })
            .catch(function () { showToast('danger', '刷新型号列表失败'); });
    }

    function openModelModal(id) {
        document.getElementById('editModelId').value = '';
        document.getElementById('modelName').value = '';
        document.getElementById('modelManufacturer').value = '';
        document.getElementById('modelMaxSpeed').value = '';
        document.getElementById('modelMaxRadius').value = '';
        document.getElementById('modelDescription').value = '';
        document.getElementById('modelIsActive').checked = true;
        document.getElementById('modelModalTitle').textContent = '新增平衡机型号';

        if (id) {
            let row = document.querySelector('#balancerModelsTable tr[data-id="' + id + '"]');
            if (row) {
                document.getElementById('modelModalTitle').textContent = '编辑平衡机型号';
                document.getElementById('editModelId').value = id;
                document.getElementById('modelName').value = (row.querySelector('td:first-child strong') || {}).textContent || '';
                let td1 = row.querySelector('td:nth-child(2)');
                let td2 = row.querySelector('td:nth-child(3)');
                let td3 = row.querySelector('td:nth-child(4)');
                document.getElementById('modelManufacturer').value = (td1 && td1.textContent.trim() !== '-' ? td1.textContent.trim() : '');
                document.getElementById('modelMaxSpeed').value = (td2 && td2.textContent.trim() !== '-' ? td2.textContent.trim() : '');
                document.getElementById('modelMaxRadius').value = (td3 && td3.textContent.trim() !== '-' ? td3.textContent.trim() : '');
                document.getElementById('modelIsActive').checked = row.querySelector('.badge.bg-success') !== null;
            }
        }
        let modal = new bootstrap.Modal(document.getElementById('modelModal'));
        modal.show();
    }

    document.addEventListener('DOMContentLoaded', function () {

        refreshDbStatus();

        let autoRefresh;

        document.addEventListener('visibilitychange', function () {
            if (document.hidden) {
                clearInterval(autoRefresh);
                autoRefresh = null;
            } else if (!autoRefresh) {
                autoRefresh = setInterval(refreshDbStatus, 30000);
            }
        });

        autoRefresh = setInterval(refreshDbStatus, 30000);

        document.querySelectorAll('#weight_p1, #weight_p2, #weight_st').forEach(function (el) {
            el.addEventListener('input', updateWeightsUI);
        });

        document.getElementById('save-weights-btn').addEventListener('click', function () {
            let btn = this;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>保存中...';
            let weights = {
                P1: parseFloat(document.getElementById('weight_p1').value),
                P2: parseFloat(document.getElementById('weight_p2').value),
                ST: parseFloat(document.getElementById('weight_st').value)
            };
            fetch('/save_face_weights', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                body: JSON.stringify(weights)
            })
            .then(function (r) { return r.json(); })
            .then(function (resp) {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-save"></i> 保存权重配置';
                showWeightsFeedback(resp.success, resp.success ? '✅ 权重配置已保存' : '❌ ' + (resp.message || '保存失败'));
            })
            .catch(function () {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-save"></i> 保存权重配置';
                showWeightsFeedback(false, '❌ 网络错误');
            });
        });

        document.getElementById('reset-weights-btn').addEventListener('click', function () {
            if (!window.confirm('确定要重置算法权重为默认值吗？')) return;
            let btn = this;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>恢复中...';
            fetch('/reset_face_weights')
                .then(function (r) { return r.json(); })
                .then(function (resp) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="bi bi-arrow-counterclockwise"></i> 恢复默认经验值';
                    if (resp.success && resp.weights) {
                        document.getElementById('weight_p1').value = resp.weights.P1;
                        document.getElementById('weight_p2').value = resp.weights.P2;
                        document.getElementById('weight_st').value = resp.weights.ST;
                        updateWeightsUI();
                        showWeightsFeedback(true, '✅ 权重已恢复为默认经验值');
                    } else {
                        showWeightsFeedback(false, '❌ ' + (resp.message || '恢复失败'));
                    }
                })
                .catch(function () {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="bi bi-arrow-counterclockwise"></i> 恢复默认经验值';
                    showWeightsFeedback(false, '❌ 网络错误');
                });
        });

        updateWeightsUI();

        document.getElementById('test-connection-btn').addEventListener('click', function () {
            let btn = this;
            let originalText = btn.innerHTML;
            btn.innerHTML = '<i class="bi bi-hourglass-split"></i> 测试中... <span class="spinner-border spinner-border-sm"></span>';
            btn.disabled = true;
            let formData = new FormData(document.getElementById('db-config-form'));
            fetch('/test_db_connection', { method: 'POST', body: formData, headers: { 'X-CSRFToken': getCsrfToken() } })
                .then(function (r) { return r.json(); })
                .then(function (resp) {
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                    if (resp.success) {
                        showToast('success', '连接测试通过');
                        refreshDbStatus();
                    } else {
                        showToast('danger', '连接测试失败：' + (resp.message || '未知错误'));
                    }
                })
                .catch(function () {
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                    showToast('danger', '连接测试请求失败');
                });
        });

        document.getElementById('db-config-form').addEventListener('submit', function (e) {
            e.preventDefault();
            let submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>保存中...';
            }
            let formData = new FormData(this);
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': getCsrfToken() }
            })
            .then(function (r) {
                if (r.redirected) {
                    refreshDbStatus();
                    refreshModelTable();
                    document.getElementById('connection_id').value = '';
                    document.getElementById('deleteConnectionBtn').style.display = 'none';
                    showToast('success', '数据库连接配置保存成功');
                }
                return r.text();
            })
            .then(function (html) {
                let parser = new DOMParser();
                let doc = parser.parseFromString(html, 'text/html');
                let alerts = doc.querySelectorAll('.alert');
                alerts.forEach(function (alert) {
                    let isSuccess = alert.classList.contains('alert-success');
                    if (isSuccess) {
                        showToast('success', alert.textContent.trim());
                    } else if (alert.classList.contains('alert-danger') || alert.classList.contains('alert-error')) {
                        showToast('danger', alert.textContent.trim());
                    } else {
                        showToast('warning', alert.textContent.trim());
                    }
                });
                if (!alerts.length && !r.redirected) {
                    showToast('danger', '保存失败，请检查表单');
                }
            })
            .catch(function () {
                showToast('danger', '保存请求失败，请检查网络');
            })
            .finally(function () {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="bi bi-save me-1"></i>保存连接配置';
                }
            });
        });

        document.getElementById('clearCacheBtn').addEventListener('click', function () {
            fetch('/api/clear_connection_cache', { method: 'POST', headers: { 'X-CSRFToken': getCsrfToken() } })
                .then(function (r) { return r.json(); })
                .then(function (resp) {
                    if (resp.success) {
                        showToast('info', '连接缓存已清除');
                        refreshDbStatus();
                    } else {
                        showToast('danger', resp.message || '清除失败');
                    }
                })
                .catch(function () { showToast('danger', '请求失败'); });
        });

        document.getElementById('deleteConnectionBtn').addEventListener('click', function () {
            let connId = document.getElementById('connection_id').value;
            if (!connId) { showToast('danger', '请先在右侧列表中选择一个连接'); return; }
            let connName = document.getElementById('connection_name').value || connId;
            if (!confirm('确认删除连接 "' + connName + '"？\n此操作不可恢复。')) return;
            let formData = new FormData();
            formData.append('action', 'delete');
            formData.append('connection_id', connId);
            fetch('/database_connections', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': getCsrfToken() }
            })
            .then(function () {
                showToast('success', '连接已删除');
                document.getElementById('connection_id').value = '';
                document.getElementById('connection_name').value = '';
                document.getElementById('deleteConnectionBtn').style.display = 'none';
                refreshDbStatus();
            })
            .catch(function () { showToast('danger', '删除请求失败'); });
        });

        document.getElementById('btnAddModel').addEventListener('click', function () { openModelModal(null); });

        document.getElementById('balancerModelsTable').addEventListener('click', function (e) {
            let editBtn = e.target.closest('.btnEditModel');
            let deleteBtn = e.target.closest('.btnDeleteModel');
            if (editBtn) { openModelModal(parseInt(editBtn.getAttribute('data-id'))); }
            if (deleteBtn) {
                let id = deleteBtn.getAttribute('data-id');
                let name = deleteBtn.getAttribute('data-name');
                if (!confirm('确认删除型号 "' + name + '"？\n此操作不可恢复。')) return;
                fetch('/api/balancer_models/' + id, {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': getCsrfToken() }
                })
                .then(function (r) { return r.json(); })
                .then(function (resp) {
                    if (resp.success) { showToast('success', '型号已删除'); refreshModelTable(); }
                    else { showToast('danger', resp.message || '删除失败'); }
                })
                .catch(function () { showToast('danger', '删除请求失败'); });
            }
        });

        let modelSearchTimer = null;
        let modelSearchInput = document.getElementById('modelSearchInput');
        if (modelSearchInput) {
            modelSearchInput.addEventListener('input', function () {
                clearTimeout(modelSearchTimer);
                modelSearchTimer = setTimeout(function () {
                    let query = modelSearchInput.value.trim().toLowerCase();
                    let rows = document.querySelectorAll('#balancerModelsTable tbody tr');
                    rows.forEach(function (row) {
                        let nameCell = row.querySelector('td:first-child strong');
                        let name = nameCell ? nameCell.textContent.toLowerCase() : '';
                        row.style.display = (!query || name.indexOf(query) >= 0) ? '' : 'none';
                    });
                }, 300);
            });
        }

        document.getElementById('btnSaveModel').addEventListener('click', function () {
            let editId = document.getElementById('editModelId').value;
            let modelName = document.getElementById('modelName').value.trim();
            if (!modelName) { showToast('danger', '型号名称不能为空'); return; }
            let payload = {
                model_name: modelName,
                manufacturer: document.getElementById('modelManufacturer').value.trim(),
                max_speed: document.getElementById('modelMaxSpeed').value.trim(),
                max_radius: document.getElementById('modelMaxRadius').value.trim(),
                description: document.getElementById('modelDescription').value.trim(),
                is_active: document.getElementById('modelIsActive').checked
            };
            let btn = this;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>保存中...';
            let method = editId ? 'PUT' : 'POST';
            let url = editId ? '/api/balancer_models/' + editId : '/api/balancer_models';
            fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                body: JSON.stringify(payload)
            })
            .then(function (r) { return r.json(); })
            .then(function (resp) {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-check-lg me-1"></i>保存';
                if (resp.success) {
                    bootstrap.Modal.getInstance(document.getElementById('modelModal')).hide();
                    showToast('success', resp.message);
                    refreshModelTable(resp.id || parseInt(editId));
                } else {
                    showToast('danger', resp.message || '操作失败');
                }
            })
            .catch(function () {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-check-lg me-1"></i>保存';
                showToast('danger', '请求失败');
            });
        });

        let connTypeSelect = document.getElementById('connection_type');
        if (connTypeSelect) {
            connTypeSelect.addEventListener('change', function () {
                let type = this.value;
                let paramsEl = document.getElementById('connection_params');
                if (!paramsEl) return;
                if (type === 'sqlite') {
                    paramsEl.innerHTML = '<div class="mb-3"><label for="database" class="form-label fw-semibold">数据库文件路径</label><input type="text" class="form-control" id="database" name="database" placeholder="例如: ./data.db"></div>';
                } else {
                    paramsEl.innerHTML =
                        '<div class="mb-3"><label for="host" class="form-label fw-semibold">主机地址</label><input type="text" class="form-control" id="host" name="host" placeholder="例如: localhost 或 IP地址"></div>' +
                        '<div class="mb-3"><label for="port" class="form-label fw-semibold">端口号</label><input type="number" class="form-control" id="port" name="port" placeholder="例如: 3306 (MySQL默认端口)"></div>' +
                        '<div class="mb-3"><label for="database" class="form-label fw-semibold">数据库名称</label><input type="text" class="form-control" id="database" name="database" placeholder="请输入数据库名称"></div>' +
                        '<div class="mb-3"><label for="username" class="form-label fw-semibold">用户名</label><input type="text" class="form-control" id="username" name="username" placeholder="请输入数据库用户名"></div>' +
                        '<div class="mb-3"><label for="password" class="form-label fw-semibold">密码</label><input type="password" class="form-control" id="password" name="password" placeholder="请输入数据库密码"><div class="form-text small">密码将加密后存储到本地配置文件</div></div>';
                }
            });
            connTypeSelect.dispatchEvent(new Event('change'));
        }
    });

    // ═══ 侧边导航滚动高亮联动 ═══
    (function initSideNav() {
        let sidenav = document.getElementById('settingsSidenav');
        if (!sidenav) return;

        let links = sidenav.querySelectorAll('.sidenav-link');
        let sections = [];
        links.forEach(function(link) {
            let id = link.getAttribute('data-section');
            let el = document.getElementById(id);
            if (el) sections.push({ id: id, el: el, link: link });
        });
        if (!sections.length) return;

        let ticking = false;
        function updateActiveLink() {
            let scrollPos = window.scrollY + 120;
            let activeId = sections[0].id;

            for (let i = sections.length - 1; i >= 0; i--) {
                if (sections[i].el.offsetTop <= scrollPos) {
                    activeId = sections[i].id;
                    break;
                }
            }

            links.forEach(function(link) {
                link.classList.toggle('active', link.getAttribute('data-section') === activeId);
            });
            ticking = false;
        }

        window.addEventListener('scroll', function() {
            if (!ticking) {
                window.requestAnimationFrame(updateActiveLink);
                ticking = true;
            }
        }, { passive: true });

        // 点击平滑滚动
        links.forEach(function(link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                let target = document.getElementById(this.getAttribute('data-section'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    history.replaceState(null, '', '#' + this.getAttribute('data-section'));
                }
            });
        });

        // 初始高亮
        updateActiveLink();
    })();
})();
