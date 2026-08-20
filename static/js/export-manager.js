// 导出管理器：js-export-link 统一走 POST 下载（GET 导出是写文件副作用操作，已下线）
(function () {
    'use strict';

    function getCsrfToken() {
        var el = document.querySelector('input[name="csrf_token"]');
        return el ? el.value : '';
    }

    function getFilenameFromHeader(header) {
        if (!header) {
            return 'export_report.html';
        }
        var m = header.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
        var name = m ? m[1] : 'export_report.html';
        try {
            name = decodeURIComponent(name);
        } catch (e) { /* 保持原名 */ }
        return name;
    }

    document.addEventListener('click', function (e) {
        var link = e.target.closest('.js-export-link');
        if (!link) {
            return;
        }
        var url = link.getAttribute('href');
        if (!url || url.indexOf('export_report') === -1) {
            return;
        }
        var token = getCsrfToken();
        if (!token) {
            alert('页面缺少安全令牌，请刷新页面后重试');
            return;
        }
        e.preventDefault();

        var originalText = link.innerHTML;
        link.classList.add('disabled');
        if (typeof link.setAttribute === 'function') {
            link.setAttribute('aria-disabled', 'true');
        }
        link.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>导出中…';

        fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': token }
        }).then(function (resp) {
            if (!resp.ok) {
                return resp.json().catch(function () { return {}; }).then(function (data) {
                    throw new Error((data && data.message) || ('导出失败，HTTP ' + resp.status));
                });
            }
            var filename = getFilenameFromHeader(resp.headers.get('Content-Disposition') || '');
            return resp.blob().then(function (blob) {
                var a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                setTimeout(function () {
                    URL.revokeObjectURL(a.href);
                    a.remove();
                }, 1000);
            });
        }).catch(function (err) {
            alert(err && err.message ? err.message : '导出失败，请重试');
        }).finally(function () {
            link.classList.remove('disabled');
            link.removeAttribute('aria-disabled');
            link.innerHTML = originalText;
        });
    });
})();
