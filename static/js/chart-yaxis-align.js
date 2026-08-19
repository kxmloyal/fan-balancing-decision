var YAxisAligner = (function () {
    var _aligned = false;
    var _originalRanges = {};
    var _unifiedRange = null;

    function _calculateNiceDtick(range) {
        var span = range[1] - range[0];
        if (span <= 0) return null;
        var rawTick = span / 5;
        var magnitude = Math.pow(10, Math.floor(Math.log10(rawTick)));
        var residual = rawTick / magnitude;
        var niceTick;
        if (residual <= 1.5) niceTick = magnitude;
        else if (residual <= 3.5) niceTick = 2 * magnitude;
        else if (residual <= 7.5) niceTick = 5 * magnitude;
        else niceTick = 10 * magnitude;
        return niceTick;
    }

    function _getVisibleChartIds() {
        var allCharts = document.querySelectorAll('.plotly-chart');
        var visibleIds = [];
        for (var i = 0; i < allCharts.length; i++) {
            var el = allCharts[i];
            if (el.offsetParent === null) continue;
            if (el.closest && el.closest('.d-none')) continue;
            var id = el.getAttribute('id');
            if (id && document.getElementById(id) && document.getElementById(id)._fullData) {
                visibleIds.push(id);
            }
        }
        return visibleIds;
    }

    function _extractYValues(gd) {
        var values = [];
        if (!gd || !gd._fullData) return values;
        var traces = gd._fullData;
        for (var i = 0; i < traces.length; i++) {
            var trace = traces[i];
            var yData = trace.y;
            if (yData !== undefined && yData !== null) {
                if (Array.isArray(yData)) {
                    for (var j = 0; j < yData.length; j++) {
                        var v = yData[j];
                        if (typeof v === 'number' && isFinite(v)) {
                            values.push(v);
                        }
                    }
                } else if (typeof yData === 'number') {
                    if (isFinite(yData)) values.push(yData);
                }
            }
            if (trace.boxpoints !== undefined || trace.type === 'box') {
                var boxData = trace.y || trace.x;
                if (Array.isArray(boxData)) {
                    for (var k = 0; k < boxData.length; k++) {
                        var bv = boxData[k];
                        if (typeof bv === 'number' && isFinite(bv)) values.push(bv);
                        if (Array.isArray(bv)) {
                            for (var m = 0; m < bv.length; m++) {
                                if (typeof bv[m] === 'number' && isFinite(bv[m])) values.push(bv[m]);
                            }
                        }
                    }
                }
            }
        }
        return values;
    }

    function align() {
        var visibleIds = _getVisibleChartIds();
        if (visibleIds.length < 2) return false;

        var allValues = [];
        _originalRanges = {};

        for (var i = 0; i < visibleIds.length; i++) {
            var id = visibleIds[i];
            var gd = document.getElementById(id);
            if (gd && gd._fullLayout && gd._fullLayout.yaxis) {
                var currentRange = gd._fullLayout.yaxis.range;
                if (currentRange && currentRange.length === 2) {
                    _originalRanges[id] = [currentRange[0], currentRange[1]];
                }
            }
            var yValues = _extractYValues(gd);
            for (var j = 0; j < yValues.length; j++) {
                allValues.push(yValues[j]);
            }
        }

        if (allValues.length === 0) return false;

        var globalMin = allValues[0];
        var globalMax = allValues[0];
        for (var k = 1; k < allValues.length; k++) {
            if (allValues[k] < globalMin) globalMin = allValues[k];
            if (allValues[k] > globalMax) globalMax = allValues[k];
        }

        var span = globalMax - globalMin;
        var padding = span !== 0 ? span * 0.05 : 1.0;
        _unifiedRange = [globalMin - padding, globalMax + padding];

        var niceDtick = _calculateNiceDtick(_unifiedRange);
        var updateObj = { 'yaxis.range': _unifiedRange };
        if (niceDtick !== null) {
            updateObj['yaxis.dtick'] = niceDtick;
        }

        for (var l = 0; l < visibleIds.length; l++) {
            Plotly.relayout(visibleIds[l], updateObj);
        }

        _aligned = true;
        return true;
    }

    function reset() {
        if (!_aligned) return false;
        var visibleIds = _getVisibleChartIds();
        for (var i = 0; i < visibleIds.length; i++) {
            var id = visibleIds[i];
            var range = _originalRanges[id];
            if (range) {
                Plotly.relayout(id, {
                    'yaxis.range': range,
                    'yaxis.dtick': null,
                    'yaxis.autorange': true
                });
            } else {
                Plotly.relayout(id, {
                    'yaxis.autorange': true
                });
            }
        }
        _aligned = false;
        _originalRanges = {};
        _unifiedRange = null;
        return true;
    }

    function toggle() {
        if (_aligned) {
            var ok = reset();
            if (ok) updateButtonState(false);
        } else {
            var ok = align();
            if (ok) updateButtonState(true);
        }
    }

    function updateButtonState(isAligned) {
        var btn = document.getElementById('btnAlignYAxis');
        if (!btn) return;
        var icon = btn.querySelector('i');
        var text = btn.querySelector('.btn-text');
        if (isAligned) {
            btn.classList.add('active');
            btn.classList.remove('btn-outline-info');
            btn.classList.add('btn-info');
            if (icon) {
                icon.className = 'bi bi-lock-fill me-1';
            }
            if (text) text.textContent = 'Y轴已对齐';
            btn.title = '点击取消Y轴对齐，恢复各自量程';
        } else {
            btn.classList.remove('active');
            btn.classList.add('btn-outline-info');
            btn.classList.remove('btn-info');
            if (icon) {
                icon.className = 'bi bi-arrows-expand-vertical me-1';
            }
            if (text) text.textContent = '对齐Y轴';
            btn.title = '一键对齐所有图表Y轴量程、刻度';
        }
    }

    function isAligned() {
        return _aligned;
    }

    return {
        align: align,
        reset: reset,
        toggle: toggle,
        isAligned: isAligned,
        updateButtonState: updateButtonState
    };
})();