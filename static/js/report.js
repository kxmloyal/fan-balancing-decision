// 报告生成与导出功能
let _reportExporting = false;

function initReportPage() {
    const exportForm = document.getElementById('reportExportForm');
    if (exportForm) {
        exportForm.addEventListener('submit', handleExportSubmit);
    }

    const exportBtns = document.querySelectorAll('.export-btn');
    exportBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (_reportExporting) {
                e.preventDefault();
                e.stopPropagation();
                return;
            }
        });
    });
}

function handleExportSubmit(e) {
    if (_reportExporting) {
        e.preventDefault();
        return false;
    }

    _reportExporting = true;
    const btn = this.querySelector('button[type="submit"]') || document.querySelector('.export-btn');
    if (btn && btn.tagName === 'BUTTON') {
        btn.disabled = true;
        const originalHtml = btn.innerHTML;
        btn.dataset.originalHtml = originalHtml;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span>导出中...';
    }

    window.addEventListener('beforeunload', resetExportState);
    window.addEventListener('pagehide', resetExportState);

    setTimeout(function() {
        _reportExporting = false;
        const btn2 = document.querySelector('.export-btn[data-original-html]');
        if (btn2) {
            btn2.disabled = false;
            btn2.innerHTML = btn2.dataset.originalHtml;
            btn2.removeAttribute('data-original-html');
        }
    }, 5000);

    return true;
}

function resetExportState() {
    _reportExporting = false;
    const btn = document.querySelector('.export-btn[data-original-html]');
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalHtml;
        btn.removeAttribute('data-original-html');
    }
    window.removeEventListener('beforeunload', resetExportState);
    window.removeEventListener('pagehide', resetExportState);
}

window.addEventListener('beforeunload', function() {
    resetExportState();
});

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initReportPage);
} else {
    initReportPage();
}
