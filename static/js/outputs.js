(function() {
    'use strict';

    let _selectedFiles = new Set();
    let _activeFilter = 'all';
    let _viewMode = 'grouped';
    let _activeModel = null;

    function getCsrfToken() {
        return document.querySelector('input[name="csrf_token"]')?.value || '';
    }

    function fetchFn(url, options) {
        if (!options) options = {};
        if (!options.headers) options.headers = {};
        options.headers['X-CSRFToken'] = getCsrfToken();
        return window.safeFetch(url, options);
    }

    function formatSize(bytes) {
        if (!bytes) return '--';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }

    function parseDateStr(dateStr) {
        if (!dateStr) return null;
        // 兼容 Safari：不支持 "YYYY-MM-DD HH:MM:SS" 空格分隔格式，需替换为 T
        let d = new Date(String(dateStr).replace(' ', 'T'));
        return isNaN(d.getTime()) ? null : d;
    }

    function formatDate(dateStr) {
        if (!dateStr) return '--';
        let d = parseDateStr(dateStr);
        if (!d) return '--';
        let now = new Date();
        let diff = now - d;
        if (diff < 3600000) return Math.floor(diff / 60000) + ' 分钟前';
        if (diff < 86400000) return Math.floor(diff / 3600000) + ' 小时前';
        if (diff < 604800000) return Math.floor(diff / 86400000) + ' 天前';
        return d.getFullYear() + '-' +
            String(d.getMonth() + 1).padStart(2, '0') + '-' +
            String(d.getDate()).padStart(2, '0');
    }

    function formatDateShort(dateStr) {
        if (!dateStr) return '--';
        let d = parseDateStr(dateStr);
        if (!d) return '--';
        return String(d.getMonth() + 1).padStart(2, '0') + '-' +
            String(d.getDate()).padStart(2, '0');
    }

    function healthLabel(h) {
        const map = { fresh: '24小时内', recent: '7天内', stale: '30天内', old: '超过30天' };
        return map[h] || '未知';
    }

    function renderTypeTags(breakdown) {
        if (!breakdown) return '';
        const colors = { html: '#e34c26', png: '#0891b2', pdf: '#dc2626', xlsx: '#16a34a', jpg: '#0891b2', jpeg: '#0891b2', svg: '#9333ea', webp: '#9333ea', csv: '#16a34a', json: '#d97706', txt: '#6b7280' };
        let tags = '';
        Object.keys(breakdown).forEach(function(t) {
            let c = colors[t] || '#6b7280';
            tags += '<span class="rm-type-tag" style="background:' + c + '1a;color:' + c + ';border:1px solid ' + c + '40">' + escapeHtml(t.toUpperCase()) + '×' + breakdown[t] + '</span>';
        });
        return tags;
    }

    let _dataCache = null;

    function getFileIconType(filename) {
        let ext = (filename || '').split('.').pop().toLowerCase();
        const iconMap = { html: 'html', htm: 'html', pdf: 'pdf', csv: 'csv',
            json: 'json', txt: 'txt', log: 'txt', md: 'txt',
            png: 'png', jpg: 'png', jpeg: 'png', svg: 'png',
            xlsx: 'xlsx', xls: 'xlsx' };
        return iconMap[ext] || 'txt';
    }

    function getFileIconClass(filename) {
        return 'bi ' + ({
            html: 'bi-filetype-html', pdf: 'bi-filetype-pdf',
            csv: 'bi-filetype-csv', json: 'bi-filetype-json',
            txt: 'bi-filetype-txt', png: 'bi-file-image',
            xlsx: 'bi-filetype-xlsx'
        })[getFileIconType(filename)] || 'bi-file-earmark';
    }

    function loadReportData() {
        _selectedFiles.clear();
        updateBatchBar();
        let search = document.getElementById('searchInput').value.trim();
        let container = document.getElementById('modelGroupsContainer');

        if (_dataCache && _activeFilter === 'all' && !search) {
            let groups = applyModelFilter(_dataCache.groups);
            if (_viewMode === 'flat') renderFlatFiles(groups, _dataCache.resp);
            else renderModelGroups(groups, _dataCache.resp);
            return;
        }

        if (_dataCache && !search) {
            let filtered = applyModelFilter(filterCachedGroups(_activeFilter));
            if (_viewMode === 'flat') renderFlatFiles(filtered, _dataCache.resp);
            else renderModelGroups(filtered, _dataCache.resp);
            return;
        }

        if (_dataCache && search) {
            let base = _activeFilter === 'all' ? JSON.parse(JSON.stringify(_dataCache.groups)) : filterCachedGroups(_activeFilter);
            let searched = applyModelFilter(filterCachedBySearch(base, search));
            if (_viewMode === 'flat') renderFlatFiles(searched, _dataCache.resp);
            else renderModelGroups(searched, _dataCache.resp);
            return;
        }

        let params = '?per_page=500';
        if (search) params += '&search=' + encodeURIComponent(search);
        if (_activeFilter !== 'all') params += '&file_type=' + encodeURIComponent(_activeFilter);
        if (!params.includes('=')) params = '?per_page=500';

        container.innerHTML = '<div class="rm-empty"><div class="spinner-border text-primary mb-3"></div><p>正在加载报告数据...</p></div>';

        fetchFn('/api/outputs/by_model' + params)
            .then(function(r) { return r.json(); })
            .then(function(resp) {
                if (!resp.success) throw new Error(resp.error || '加载失败');
                if (!search && _activeFilter === 'all') _dataCache = { groups: resp.data || [], resp: resp };
                let groups = applyModelFilter(resp.data || []);
                if (_viewMode === 'flat') renderFlatFiles(groups, resp);
                else renderModelGroups(groups, resp);
            })
            .catch(function(err) {
                container.innerHTML = '<div class="rm-empty"><div class="rm-empty-icon"><i class="bi bi-exclamation-triangle"></i></div><p>加载失败: ' + escapeHtml(err.message) + '</p><button class="btn btn-outline-primary btn-sm mt-2" onclick="location.reload()"><i class="bi bi-arrow-clockwise me-1"></i>重试</button></div>';
                console.error('加载报告数据失败:', err);
            });
    }

    function renderModelGroups(groups, resp) {
        let container = document.getElementById('modelGroupsContainer');
        _selectedFiles.clear();
        updateBatchBar();

        if (groups.length === 0) {
            container.innerHTML = '<div class="rm-empty"><div class="rm-empty-icon"><i class="bi bi-inbox"></i></div><p>暂无报告数据</p><p class="small text-muted">请先上传数据并生成分析报告</p></div>';
            updateStats(0, 0, '--', '--');
            document.getElementById('resultCount').textContent = '';
            return;
        }

        let totalFiles = resp.total_items || groups.reduce(function(s, g) { return s + g.files.length; }, 0);
        let totalModels = groups.length;
        let latestDate = '--';
        if (groups.length > 0) {
            let maxDate = null;
            groups.forEach(function(g) {
                // 后端返回的是 g.summary.latest_report（分组级最新文件时间），
                // 原实现读 g.created_at（后端未返回该字段）导致统计卡恒为 "--"
                if (g.summary && g.summary.latest_report) {
                    let d = parseDateStr(g.summary.latest_report);
                    if (d && (!maxDate || d > maxDate)) maxDate = d;
                }
            });
            if (maxDate) latestDate = formatDate(maxDate.toISOString());
        }
        let typeSet = new Set();
        groups.forEach(function(g) { g.files.forEach(function(f) { typeSet.add(f.file_type); }); });

        updateStats(totalFiles, totalModels, latestDate, typeSet.size);

        let html = '';
        groups.forEach(function(group, idx) {
            let files = group.files || [];
            let summary = group.summary || {};
            html += '<div class="rm-model-group' + (idx === 0 ? '' : ' collapsed') + '" data-model-name="' + escapeHtml(group.model) + '">';
            html += '  <div class="rm-model-header" data-model="' + escapeHtml(group.model) + '">';
            html += '    <input type="checkbox" class="rm-model-checkbox" data-model="' + escapeHtml(group.model) + '" title="全选/取消该型号">';
            html += '    <div class="rm-model-icon"><i class="bi bi-folder2"></i></div>';
            html += '    <div class="rm-model-info">';
            html += '      <div class="rm-model-name" title="' + escapeHtml(group.model) + '">';
            html += '        <span class="rm-model-health ' + (summary.health || 'old') + '" title="' + healthLabel(summary.health) + '"></span>';
            html += escapeHtml(group.model);
            let completeness = checkModelCompleteness(summary.orig_type_breakdown || summary.type_breakdown, (group.files || []).length);
            if (completeness) {
                html += '        <span class="rm-model-incomplete" title="' + completeness.join('；') + '"><i class="bi bi-exclamation-triangle-fill"></i>' + completeness.join('；') + '</span>';
            }
            html += '      </div>';
            html += '      <div class="rm-model-meta">' + files.length + ' 份报告';
            if (summary.test_count) html += ' &middot; ' + summary.test_count + ' 次测试';
            if (summary.total_size) html += ' &middot; ' + formatSize(summary.total_size);
            if (summary.first_report && summary.latest_report) {
                html += ' &middot; ' + formatDateShort(summary.first_report) + ' ~ ' + formatDateShort(summary.latest_report);
            } else if (summary.latest_report) {
                html += ' &middot; ' + formatDateShort(summary.latest_report);
            }
            html += '      </div>';
            html += '      <div class="rm-model-tags">' + renderTypeTags(summary.type_breakdown) + '</div>';
            html += '    </div>';
            html += '    <div class="rm-model-actions">';
            html += '      <button class="btn btn-sm btn-outline-primary rm-model-dl-btn" data-model="' + escapeHtml(group.model) + '" title="下载该型号全部报告"><i class="bi bi-download"></i></button>';
            html += '    </div>';
            html += '    <i class="bi bi-chevron-down rm-model-chevron"></i>';
            html += '  </div>';
            html += '  <div class="rm-model-body">';

            // 按测试批次分组渲染：同一次测试的报告+图表归为一组，带批次标题
            let batchMap = {};
            files.forEach(function(file) {
                let key = file.test_no || 0;
                if (!batchMap[key]) batchMap[key] = [];
                batchMap[key].push(file);
            });
            let batchKeys = Object.keys(batchMap).map(Number).sort(function(a, b) { return a - b; });
            batchKeys.forEach(function(key) {
                let batchFiles = batchMap[key];
                // 批次标题：未分类型号（无型号归属）才显示"未归类文件"；
                // 有型号但未导出报告（无报告锚点）的分析同样算一次测试
                let batchTitle = key > 0 ? '第 ' + key + ' 次测试'
                    : (group.model === '未分类' ? '未归类文件' : '第 1 次测试');
                let batchTime = '';
                let timeAnchor = batchFiles.find(function(f) { return f.filename.indexOf('动平衡分析报告') >= 0; });
                if (!timeAnchor) timeAnchor = batchFiles[0]; // 无报告时用批次内最早文件时间
                if (timeAnchor && timeAnchor.created_at) batchTime = ' · ' + formatDateShort(timeAnchor.created_at);
                html += '<div class="rm-test-batch" data-test-no="' + key + '">';
                html += '  <div class="rm-test-batch-title"><i class="bi bi-flask me-1"></i>' + escapeHtml(batchTitle) + batchTime + '<span class="rm-test-batch-count">' + batchFiles.length + ' 个文件</span></div>';
                html += '  <div class="rm-file-grid">';
                batchFiles.forEach(function(file) {
                    html += renderFileCard(file, group.model);
                });
                html += '  </div>';
                html += '</div>';
            });

            html += '  </div>';
            html += '</div>';
        });

        container.innerHTML = html;

        bindModelHeaders();
        bindFileCardEvents();
        bindModelCheckboxes();

        document.getElementById('resultCount').textContent = '共 ' + totalModels + ' 个型号 · ' + totalFiles + ' 份报告';

        renderModelNav(groups);
    }

    function renderModelNav(groups) {
        let navBar = document.getElementById('modelNavBar');
        let chipsContainer = document.getElementById('modelNavChips');
        if (!navBar || !chipsContainer) return;
        let allGroups = (_dataCache && _dataCache.groups) || groups;
        if (allGroups.length <= 1) { navBar.style.display = 'none'; return; }
        navBar.style.display = 'flex';
        let html = '';
        allGroups.forEach(function(g) {
            let count = (g.files || []).length;
            html += '<span class="rm-model-nav-chip" data-nav-model="' + escapeHtml(g.model) + '">'
                + escapeHtml(g.model) + ' <span class="rm-nav-badge">' + count + '</span></span>';
        });
        chipsContainer.innerHTML = html;
        chipsContainer.querySelectorAll('.rm-model-nav-chip').forEach(function(chip) {
            chip.addEventListener('click', function() {
                let modelName = chip.dataset.navModel;
                if (_activeModel === modelName) {
                    _activeModel = null;
                } else {
                    _activeModel = modelName;
                }
                loadReportData();
            });
        });
        updateModelNavActive();
    }

    function updateModelNavActive() {
        let chips = document.querySelectorAll('.rm-model-nav-chip');
        chips.forEach(function(chip) {
            if (chip.dataset.navModel === _activeModel) {
                chip.classList.add('active');
            } else {
                chip.classList.remove('active');
            }
        });
    }

    function filterCachedGroups(filterType) {
        return (_dataCache.groups || []).map(function(g) {
            let filteredFiles = g.files.filter(function(f) { return f.file_type === filterType; });
            if (filteredFiles.length === 0) return null;
            let clone = JSON.parse(JSON.stringify(g));
            clone.files = filteredFiles;
            if (clone.summary) {
                // 保留原始类型分布，供型号完整性判定使用（过滤视图下 type_breakdown 已被改写）
                clone.summary.orig_type_breakdown = g.summary.type_breakdown;
                let tb = {};
                tb[filterType] = filteredFiles.length;
                clone.summary.type_breakdown = tb;
                clone.summary.file_count = filteredFiles.length;
            }
            return clone;
        }).filter(Boolean);
    }

    function renderFlatFiles(groups, resp) {
        let container = document.getElementById('modelGroupsContainer');
        _selectedFiles.clear();
        updateBatchBar();
        document.getElementById('modelNavBar').style.display = 'none';

        if (!groups || groups.length === 0) {
            container.innerHTML = '<div class="rm-empty"><div class="rm-empty-icon"><i class="bi bi-inbox"></i></div><p>暂无报告数据</p><p class="small text-muted">请先上传数据并生成分析报告</p></div>';
            updateStats(0, 0, '--', '--');
            document.getElementById('resultCount').textContent = '';
            return;
        }

        let allFiles = [];
        groups.forEach(function(g) {
            g.files.forEach(function(f) {
                allFiles.push({ file: f, model: g.model });
            });
        });

        let totalModels = groups.length;
        let totalFiles = allFiles.length;
        let maxDate = null;
        groups.forEach(function(g) {
            if (g.summary && g.summary.latest_report) {
                let d = new Date(g.summary.latest_report);
                if (!maxDate || d > maxDate) maxDate = d;
            }
        });
        let latestDate = maxDate ? formatDate(maxDate.toISOString()) : '--';
        let typeSet = new Set();
        allFiles.forEach(function(entry) { typeSet.add(entry.file.file_type); });

        updateStats(totalFiles, totalModels, latestDate, typeSet.size);

        let html = '<div class="rm-flat-grid">';
        allFiles.forEach(function(entry) {
            html += renderFileCard(entry.file, entry.model);
        });
        html += '</div>';

        container.innerHTML = html;
        bindFileCardEvents();
        document.getElementById('resultCount').textContent = '共 ' + totalModels + ' 个型号 · ' + totalFiles + ' 份报告（平铺视图）';
    }

    function updateViewToggleUI() {
        let btn = document.getElementById('viewToggleBtn');
        if (!btn) return;
        let icon = btn.querySelector('i');
        let label = btn.querySelector('.rm-view-toggle-label');
        if (_viewMode === 'flat') {
            btn.classList.add('flat-mode');
            if (icon) { icon.className = 'bi bi-list-ul'; }
            if (label) label.textContent = '平铺';
        } else {
            btn.classList.remove('flat-mode');
            if (icon) { icon.className = 'bi bi-grid-3x3-gap'; }
            if (label) label.textContent = '分组';
        }
    }

    function filterCachedBySearch(groups, searchTerm) {
        let q = searchTerm.toLowerCase();
        return groups.map(function(g) {
            let modelMatch = g.model.toLowerCase().indexOf(q) >= 0;
            let matchedFiles = g.files.filter(function(f) {
                return modelMatch || f.filename.toLowerCase().indexOf(q) >= 0;
            });
            if (matchedFiles.length === 0) return null;
            let clone = JSON.parse(JSON.stringify(g));
            clone.files = matchedFiles;
            return clone;
        }).filter(Boolean);
    }

    function applyModelFilter(groups) {
        if (!_activeModel) return groups;
        return groups.filter(function(g) { return g.model === _activeModel; });
    }

    function checkModelCompleteness(breakdown, fileCount) {
        if (!breakdown || fileCount <= 1) return null;
        let types = Object.keys(breakdown);
        if (types.length < 2) return null;
        let hasHtml = types.indexOf('html') >= 0 || types.indexOf('htm') >= 0;
        let hasImage = types.some(function(t) { return ['png', 'jpg', 'jpeg', 'svg', 'webp'].indexOf(t) >= 0; });
        let missing = [];
        if (!hasHtml) missing.push('缺HTML报告');
        if (hasHtml && !hasImage && fileCount >= 2) missing.push('缺图表');
        return missing.length > 0 ? missing : null;
    }

    function renderFileCard(file, model) {
        let iconType = getFileIconType(file.filename);
        let iconClass = getFileIconClass(file.filename);
        let downloadUrl = '/api/outputs/download/' + encodeURIComponent(file.filename);
        if (model && model !== '未分类') {
            downloadUrl = '/api/outputs/download/' + encodeURIComponent(model + '/' + file.filename);
        }
        // 测试批次标签：报告/图表文件都带 test_no（1=第1次测试），无批次不显示
        let testBadge = '';
        if (file.test_no) {
            testBadge = '<span class="rm-test-badge" title="第 ' + file.test_no + ' 次测试">第' + file.test_no + '次</span>';
        }
        return '<div class="rm-file-card" data-file-id="' + escapeHtml(file.id) + '" data-file-name="' + escapeHtml(file.filename) + '" data-file-type="' + escapeHtml(iconType) + '" data-model="' + escapeHtml(model) + '" data-download-url="' + escapeHtml(downloadUrl) + '">' +
            '<input type="checkbox" class="rm-file-checkbox form-check-input me-2" data-file-id="' + escapeHtml(file.id) + '">' +
            '<div class="rm-file-icon ' + iconType + '"><i class="' + iconClass + '"></i></div>' +
            '<div class="rm-file-info">' +
                '<div class="rm-file-name" title="' + escapeHtml(file.filename) + '">' + escapeHtml(file.filename) + testBadge + '</div>' +
                '<div class="rm-file-meta">' +
                    '<span>' + formatSize(file.file_size) + '</span>' +
                    '<span>' + formatDate(file.created_at) + '</span>' +
                '</div>' +
            '</div>' +
            '<div class="rm-file-actions">' +
                '<button class="btn-icon preview-btn" title="预览" data-file-id="' + escapeHtml(file.id) + '" data-file-name="' + escapeHtml(file.filename) + '" data-file-type="' + escapeHtml(iconType) + '" data-download-url="' + escapeHtml(downloadUrl) + '"><i class="bi bi-eye"></i></button>' +
                '<a class="btn-icon download-btn" title="下载" href="' + escapeHtml(downloadUrl) + '" download><i class="bi bi-download"></i></a>' +
                '<button class="btn-icon danger delete-btn" title="删除" data-file-id="' + escapeHtml(file.id) + '"><i class="bi bi-trash"></i></button>' +
            '</div>' +
        '</div>';
    }

    function escapeHtml(str) {
        let div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function updateStats(total, models, latest, types) {
        document.getElementById('statTotal').textContent = total;
        document.getElementById('statModels').textContent = models;
        document.getElementById('statLatest').textContent = latest;
        document.getElementById('statTypes').textContent = types;
    }

    function bindModelHeaders() {
        document.querySelectorAll('.rm-model-header').forEach(function(header) {
            header.addEventListener('click', function(e) {
                if (e.target.closest('.rm-model-checkbox')) return;
                if (e.target.closest('.rm-model-dl-btn')) return;
                let group = header.closest('.rm-model-group');
                if (group) group.classList.toggle('collapsed');
            });
        });

        document.querySelectorAll('.rm-model-dl-btn').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                let model = btn.dataset.model;
                window.location.href = '/api/outputs/batch_download?fan_model=' + encodeURIComponent(model);
            });
        });
    }

    function bindModelCheckboxes() {
        document.querySelectorAll('.rm-model-checkbox').forEach(function(cb) {
            cb.addEventListener('click', function(e) {
                e.stopPropagation();
                let model = cb.dataset.model;
                let body = cb.closest('.rm-model-header').nextElementSibling;
                if (!body) return;
                let cards = body.querySelectorAll('.rm-file-card');
                cards.forEach(function(card) {
                    let fileCheckbox = card.querySelector('.rm-file-checkbox');
                    let fileId = card.dataset.fileId;
                    if (cb.checked) {
                        fileCheckbox.checked = true;
                        _selectedFiles.add(fileId);
                        card.classList.add('selected');
                    } else {
                        fileCheckbox.checked = false;
                        _selectedFiles.delete(fileId);
                        card.classList.remove('selected');
                    }
                });
                updateBatchBar();
            });
        });
    }

    function bindFileCardEvents() {
        document.querySelectorAll('.rm-file-card').forEach(function(card) {
            card.addEventListener('click', function(e) {
                if (e.target.closest('.btn-icon') || e.target.closest('.rm-file-checkbox')) return;

                if (e.ctrlKey || e.metaKey) {
                    toggleFileCheckbox(card);
                } else {
                    let fileId = card.dataset.fileId;
                    let filename = card.dataset.fileName;
                    let fileType = card.dataset.fileType;
                    openPreview(fileId, filename, fileType, card.dataset.downloadUrl);
                }
            });
        });

        document.querySelectorAll('.rm-file-checkbox').forEach(function(cb) {
            cb.addEventListener('click', function(e) {
                e.stopPropagation();
                let card = cb.closest('.rm-file-card');
                if (!card) return;
                if (cb.checked) {
                    _selectedFiles.add(card.dataset.fileId);
                    card.classList.add('selected');
                } else {
                    _selectedFiles.delete(card.dataset.fileId);
                    card.classList.remove('selected');
                }
                updateBatchBar();
            });
        });

        document.querySelectorAll('.preview-btn').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();
                let fileId = btn.dataset.fileId;
                openPreview(fileId, btn.dataset.fileName, btn.dataset.fileType, btn.dataset.downloadUrl);
            });
        });

        document.querySelectorAll('.delete-btn').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();
                let fileId = btn.dataset.fileId;
                let card = btn.closest('.rm-file-card');
                let filename = card ? card.dataset.fileName : fileId;
                confirmSingleDelete(fileId, filename);
            });
        });
    }

    function toggleFileCheckbox(card) {
        let cb = card.querySelector('.rm-file-checkbox');
        let fileId = card.dataset.fileId;
        if (_selectedFiles.has(fileId)) {
            _selectedFiles.delete(fileId);
            cb.checked = false;
            card.classList.remove('selected');
        } else {
            _selectedFiles.add(fileId);
            cb.checked = true;
            card.classList.add('selected');
        }
        updateBatchBar();
    }

    function updateBatchBar() {
        let bar = document.getElementById('batchBar');
        let count = _selectedFiles.size;
        document.getElementById('batchCount').textContent = count;
        if (count > 0) {
            bar.classList.add('show');
        } else {
            bar.classList.remove('show');
        }

        document.querySelectorAll('.rm-model-group').forEach(function(group) {
            let modelCb = group.querySelector('.rm-model-checkbox');
            if (!modelCb) return;
            let cards = group.querySelectorAll('.rm-file-card');
            let totalCards = cards.length;
            let selectedCards = group.querySelectorAll('.rm-file-card .rm-file-checkbox:checked').length;
            modelCb.checked = totalCards > 0 && selectedCards === totalCards;
            modelCb.indeterminate = selectedCards > 0 && selectedCards < totalCards;
        });
    }

    function openPreview(fileId, filename, fileType, downloadUrl) {
        let modal = new bootstrap.Modal(document.getElementById('previewModal'));
        let modalTitle = document.getElementById('previewTitle');
        let modalBody = document.getElementById('previewBody');
        let downloadBtn = document.getElementById('previewDownloadBtn');

        modalTitle.innerHTML = '<i class="bi bi-eye me-2"></i>' + escapeHtml(filename);
        modalBody.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div><p class="mt-2 text-muted">正在加载预览...</p></div>';

        downloadBtn.href = '#';

        fetchFn('/api/outputs/preview_info/' + fileId)
            .then(function(r) { return r.json(); })
            .then(function(infoResp) {
                let info = (infoResp.success && infoResp.data) ? infoResp.data : {};
                let previewType = info.preview_type || fileType;
                let viewUrl = info.view_url || '';
                let dlUrl = info.download_url || '';

                // 使用后端返回的相对路径下载链接；原实现用绝对路径 file_path，
                // 会被后端 /api/outputs/download 以"路径不合法"拒绝
                if (dlUrl) downloadBtn.href = dlUrl;

                if (previewType === 'html') {
                    if (viewUrl) {
                        previewAsIframe(viewUrl, modalBody);
                    } else {
                        modalBody.innerHTML = '<div class="rm-preview-content text-center py-5"><p class="text-muted">无法获取文件预览路径</p></div>';
                    }
                } else if (previewType === 'image') {
                    if (viewUrl) {
                        previewAsImage(viewUrl, modalBody);
                    } else {
                        modalBody.innerHTML = '<div class="rm-preview-content text-center py-5"><p class="text-muted">无法获取文件预览路径</p></div>';
                    }
                } else if (previewType === 'pdf') {
                    if (viewUrl) {
                        previewAsPdf(viewUrl, modalBody);
                    } else {
                        modalBody.innerHTML = '<div class="rm-preview-content text-center py-5"><p class="text-muted">无法获取PDF文件路径</p></div>';
                    }
                } else if (['csv', 'json', 'txt', 'log', 'md'].indexOf(previewType) >= 0) {
                    previewAsText(fileId, previewType, modalBody);
                } else {
                    let dlLink = downloadBtn.href || '#';
                    modalBody.innerHTML = '<div class="rm-preview-content text-center py-5"><i class="bi bi-file-earmark" style="font-size:3rem;color:#94a3b8;"></i><p class="text-muted mt-2">此文件类型不支持在线预览</p><p class="small"><a href="' + dlLink + '" class="btn btn-outline-primary btn-sm"><i class="bi bi-download me-1"></i>下载查看</a></p></div>';
                }
            })
            .catch(function() {
                // 后端 preview_info 不可用时降级：从卡片相对下载链接提取路径
                let relPath = downloadUrl || encodeURIComponent(filename);
                if (relPath.indexOf('/api/outputs/download/') === 0) {
                    relPath = relPath.substring('/api/outputs/download/'.length);
                }

                if (fileType === 'html') {
                    previewAsIframe('/view_chart_html/' + relPath, modalBody);
                } else if (['png', 'jpg', 'jpeg', 'svg', 'webp'].indexOf(fileType) >= 0) {
                    previewAsImage('/view_chart/' + relPath, modalBody);
                } else if (fileType === 'pdf') {
                    previewAsPdf('/view_pdf/' + relPath, modalBody);
                } else if (['csv', 'json', 'txt', 'log', 'md'].indexOf(fileType) >= 0) {
                    previewAsText(fileId, fileType, modalBody);
                } else {
                    let dlLink = downloadBtn.href || '#';
                    modalBody.innerHTML = '<div class="rm-preview-content text-center py-5"><i class="bi bi-file-earmark" style="font-size:3rem;color:#94a3b8;"></i><p class="text-muted mt-2">此文件类型不支持在线预览</p><p class="small"><a href="' + dlLink + '" class="btn btn-outline-primary btn-sm"><i class="bi bi-download me-1"></i>下载查看</a></p></div>';
                }
            });

        modal.show();
    }

    function previewAsIframe(url, body) {
        body.innerHTML = '<iframe class="rm-preview-frame" src="' + url + '" sandbox="allow-scripts allow-same-origin"></iframe>';
    }

    function previewAsImage(url, body) {
        body.innerHTML = '<div class="rm-preview-img"><img src="' + url + '" alt="图表预览"></div>';
    }

    function previewAsPdf(url, body) {
        body.innerHTML = '<iframe class="rm-preview-frame" src="' + url + '" sandbox="allow-scripts allow-same-origin"></iframe><div class="text-center p-2"><small class="text-muted">PDF预览 — 如无法显示请<a href="' + url + '" target="_blank">下载查看</a></small></div>';
    }

    function previewAsText(fileId, fileType, body) {
        fetchFn('/api/outputs/preview/' + fileId)
            .then(function(r) { return r.json(); })
            .then(function(resp) {
                if (!resp.success) throw new Error(resp.error);
                let content = resp.data || '';
                let langMap = { csv: 'csv', json: 'json', txt: '', log: '', md: 'markdown' };
                body.innerHTML = '<div class="rm-preview-content"><pre><code class="language-' + (langMap[fileType] || '') + '">' + escapeHtml(content) + '</code></pre></div>';
            })
            .catch(function(err) {
                body.innerHTML = '<div class="rm-preview-content text-center py-5 text-danger">预览失败: ' + escapeHtml(err.message) + '</div>';
            });
    }

    function confirmSingleDelete(fileId, filename) {
        if (!window.confirm('确定要删除文件 "' + filename + '" 吗？此操作不可撤销。')) return;
        performBatchDelete([fileId]);
    }

    function setBatchLoading(show) {
        let bar = document.getElementById('batchBar');
        if (!bar) return;
        let btns = bar.querySelectorAll('button');
        btns.forEach(function(btn) { btn.disabled = show; });
        let loadingEl = bar.querySelector('.rm-batch-loading');
        if (show) {
            if (!loadingEl) {
                loadingEl = document.createElement('span');
                loadingEl.className = 'rm-batch-loading ms-2';
                loadingEl.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span>处理中...';
                bar.querySelector('span').appendChild(loadingEl);
            }
        } else {
            if (loadingEl) loadingEl.remove();
        }
    }

    function performBatchDelete(fileIds) {
        setBatchLoading(true);
        fetchFn('/api/outputs/batch_delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids: fileIds })
        })
        .then(function(r) { return r.json(); })
        .then(function(resp) {
            setBatchLoading(false);
            if (resp.success) {
                _selectedFiles.clear();
                updateBatchBar();
                // 删除后必须清空数据缓存：loadReportData 在 _dataCache 命中时直接渲染缓存，
                // 不清空会导致已删除文件仍显示在列表中
                _dataCache = null;
                window.showToast('success', '已成功删除 ' + fileIds.length + ' 个文件');
                loadReportData();
            } else {
                window.showToast('danger', '删除失败: ' + (resp.message || '未知错误'));
            }
        })
        .catch(function(err) {
            setBatchLoading(false);
            console.error('删除失败:', err);
            window.showToast('danger', '删除失败: ' + err.message);
        });
    }

    function performBatchDownload() {
        if (_selectedFiles.size === 0) return;
        setBatchLoading(true);
        fetchFn('/api/outputs/batch_download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids: Array.from(_selectedFiles) })
        })
        .then(function(r) {
            if (!r.ok) throw new Error('下载失败');
            let disposition = r.headers.get('Content-Disposition');
            let filename = 'reports_batch.zip';
            if (disposition) {
                let match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (match && match[1]) filename = match[1].replace(/['"]/g, '');
            }
            return r.blob();
        })
        .then(function(blob) {
            setBatchLoading(false);
            let url = window.URL.createObjectURL(blob);
            let a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            try { window.URL.revokeObjectURL(url); } catch(e) {}
        })
        .catch(function(err) {
            setBatchLoading(false);
            console.error('批量下载失败:', err);
            window.showToast('danger', '批量下载失败: ' + err.message);
        });
    }

    function selectAllVisible() {
        document.querySelectorAll('.rm-file-card').forEach(function(card) {
            let cb = card.querySelector('.rm-file-checkbox');
            if (cb) {
                cb.checked = true;
                _selectedFiles.add(card.dataset.fileId);
                card.classList.add('selected');
            }
        });
        document.querySelectorAll('.rm-model-checkbox').forEach(function(cb) { cb.checked = true; });
        updateBatchBar();
    }

    function deselectAll() {
        _selectedFiles.clear();
        document.querySelectorAll('.rm-file-card.selected').forEach(function(c) { c.classList.remove('selected'); });
        document.querySelectorAll('.rm-file-checkbox').forEach(function(cb) { cb.checked = false; });
        document.querySelectorAll('.rm-model-checkbox').forEach(function(cb) { cb.checked = false; });
        updateBatchBar();
    }

    function invertSelection() {
        let currentSelected = new Set(_selectedFiles);
        _selectedFiles.clear();
        document.querySelectorAll('.rm-file-card').forEach(function(card) {
            let cb = card.querySelector('.rm-file-checkbox');
            let fileId = card.dataset.fileId;
            if (currentSelected.has(fileId)) {
                cb.checked = false;
                card.classList.remove('selected');
            } else {
                cb.checked = true;
                _selectedFiles.add(fileId);
                card.classList.add('selected');
            }
        });
        updateBatchBar();
    }

    function init() {
        loadReportData();

        document.getElementById('searchInput').addEventListener('input', debounce(function() {
            loadReportData();
        }, 300));

        document.querySelectorAll('.rm-filter-chip').forEach(function(chip) {
            chip.addEventListener('click', function() {
                document.querySelectorAll('.rm-filter-chip').forEach(function(c) { c.classList.remove('active'); });
                chip.classList.add('active');
                _activeFilter = chip.dataset.filter;
                _activeModel = null;
                loadReportData();
            });
        });

        document.getElementById('btnCollapseAll').addEventListener('click', function() {
            document.querySelectorAll('.rm-model-group').forEach(function(g) { g.classList.add('collapsed'); });
        });

        document.getElementById('btnExpandAll').addEventListener('click', function() {
            document.querySelectorAll('.rm-model-group').forEach(function(g) { g.classList.remove('collapsed'); });
        });

        document.getElementById('batchClearBtn').addEventListener('click', function() {
            deselectAll();
        });

        document.getElementById('batchDeleteConfirmBtn').addEventListener('click', function() {
            if (_selectedFiles.size === 0) return;
            if (!window.confirm('确定要删除选中的 ' + _selectedFiles.size + ' 个文件吗？此操作不可撤销。')) return;
            performBatchDelete(Array.from(_selectedFiles));
        });

        let batchDownloadBtn = document.getElementById('batchDownloadBtn');
        if (batchDownloadBtn) {
            batchDownloadBtn.addEventListener('click', function() {
                if (_selectedFiles.size === 0) return;
                performBatchDownload();
            });
        }
        let batchDownloadBtn2 = document.getElementById('batchDownloadBtn2');
        if (batchDownloadBtn2) {
            batchDownloadBtn2.addEventListener('click', function() {
                if (_selectedFiles.size === 0) return;
                performBatchDownload();
            });
        }

        let selectAllBtn = document.getElementById('btnSelectAll');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', selectAllVisible);
        }
        let deselectAllBtn = document.getElementById('btnDeselectAll');
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', deselectAll);
        }
        let invertBtn = document.getElementById('btnInvertSelect');
        if (invertBtn) {
            invertBtn.addEventListener('click', invertSelection);
        }

        let viewToggleBtn = document.getElementById('viewToggleBtn');
        if (viewToggleBtn) {
            viewToggleBtn.addEventListener('click', function() {
                _viewMode = _viewMode === 'grouped' ? 'flat' : 'grouped';
                updateViewToggleUI();
                loadReportData();
            });
        }

        document.addEventListener('keydown', function(e) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
            if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
                e.preventDefault();
                selectAllVisible();
            } else if (e.key === 'Escape') {
                deselectAll();
            } else if (e.key === 'Delete' && _selectedFiles.size > 0) {
                e.preventDefault();
                if (window.confirm('确定要删除选中的 ' + _selectedFiles.size + ' 个文件吗？此操作不可撤销。')) {
                    performBatchDelete(Array.from(_selectedFiles));
                }
            }
        });
    }

    function debounce(fn, delay) {
        let timer = null;
        return function() {
            let context = this;
            let args = arguments;
            clearTimeout(timer);
            timer = setTimeout(function() { fn.apply(context, args); }, delay);
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();