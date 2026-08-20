function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

window.showToast = function(type, message) {
    type = type || 'danger';
    message = message || '';
    var container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = 'position:fixed;top:70px;right:16px;z-index:9999;display:flex;flex-direction:column;gap:8px;';
        document.body.appendChild(container);
    }
    var icons = { success: 'bi-check-circle', danger: 'bi-exclamation-triangle', warning: 'bi-exclamation-circle', info: 'bi-info-circle' };
    var bgColors = { success: '#10b981', danger: '#ef4444', warning: '#f59e0b', info: '#3b82f6' };
    var toast = document.createElement('div');
    toast.className = 'toast-toast';
    toast.style.cssText = 'background:#fff;color:#1e293b;padding:12px 20px;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,0.12);font-size:0.875rem;display:flex;align-items:center;gap:10px;min-width:280px;max-width:420px;border-left:4px solid ' + (bgColors[type] || bgColors.danger) + ';animation:toastSlideIn 0.3s ease;';
    toast.innerHTML = '<i class="bi ' + (icons[type] || icons.danger) + '" style="color:' + (bgColors[type] || bgColors.danger) + ';font-size:1.1rem;flex-shrink:0;"></i><span style="flex:1;">' + escapeHtml(message) + '</span><button style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:1.1rem;padding:0;line-height:1;" onclick="this.parentElement.remove()">&times;</button>';
    container.appendChild(toast);
    setTimeout(function() {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(function() { if (toast.parentElement) toast.remove(); }, 300);
    }, 4000);
};