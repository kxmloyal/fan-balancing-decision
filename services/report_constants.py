#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""报告渲染共享常量（从 report_html_builder.py 迁出，消除死代码文件的存活依赖）

PLOTLY_CDN_URL / PLOTLY_DUAL_TRACK_SCRIPT 由 ReportRenderer（主）与
ReportExporter（兼容路径）共用，避免双份脚本维护。
"""

PLOTLY_CDN_URL = "https://cdn.plot.ly/plotly-2.35.2.min.js"

PLOTLY_DUAL_TRACK_SCRIPT = r"""
<script>
/* 双轨图表渲染：交互可用则替换静态图，否则保留静态图兜底 */
(function () {
    function buildTraces(type, data) {
        if (!Array.isArray(data)) return [];
        switch (type) {
            case 'box':
                var traces = data.map(function (i) {
                    return { y: i.data || [], name: i.name, type: 'box', boxpoints: 'all', jitter: 0.3, pointpos: -1.8, opacity: 0.7 };
                });
                if (data.length > 1) {
                    var medians = data.map(function (i) {
                        var arr = (i.data || []).slice().sort(function (a, b) { return a - b; });
                        if (!arr.length) return 0;
                        var mid = Math.floor(arr.length / 2);
                        return arr.length % 2 ? arr[mid] : (arr[mid - 1] + arr[mid]) / 2;
                    });
                    traces.push({
                        x: data.map(function (i) { return i.name; }),
                        y: medians,
                        type: 'scatter', mode: 'lines+markers',
                        name: '中位线',
                        line: { color: '#64748b', width: 2, dash: 'dash' },
                        marker: { color: '#64748b', size: 6, symbol: 'circle' }
                    });
                }
                return traces;
            case 'violin':
                return data.map(function (i) {
                    return { y: i.data || [], name: i.name, type: 'violin' };
                });
            case 'trend':
                return [{
                    x: data.map(function (i) { return i.name; }),
                    y: data.map(function (i) { return i.value; }),
                    type: 'scatter', mode: 'lines+markers'
                }];
            case 'scatter':
                return [{
                    x: data.map(function (d) { return d[0]; }),
                    y: data.map(function (d) { return d[1]; }),
                    type: 'scatter', mode: 'markers'
                }];
            case 'bubble':
                return [{
                    x: data.map(function (i) { return i.value[0]; }),
                    y: data.map(function (i) { return i.value[1]; }),
                    type: 'scatter', mode: 'markers',
                    marker: { size: data.map(function (i) { return Math.max(6, i.value[2] || 6); }), sizemode: 'diameter' }
                }];
            case 'heatmap':
                return [{
                    x: data.map(function (d) { return d[0]; }),
                    y: data.map(function (d) { return d[1]; }),
                    z: [data.map(function (d) { return d[2]; })],
                    type: 'heatmap'
                }];
            case 'histogram':
                return [{ y: data, type: 'bar', name: '频数' }];
            case '3d':
                return [{
                    x: data.map(function (d) { return d[0]; }),
                    y: data.map(function (d) { return d[1]; }),
                    z: data.map(function (d) { return d[2]; }),
                    type: 'scatter3d', mode: 'markers'
                }];
            case 'parallel':
                return [{
                    type: 'parcoords',
                    dimensions: [
                        { label: '转速', values: data.map(function (d) { return d[0]; }) },
                        { label: '中位数', values: data.map(function (d) { return d[1]; }) },
                        { label: '均值', values: data.map(function (d) { return d[2]; }) }
                    ]
                }];
            default:
                return [];
        }
    }
    var ALIGNABLE_TYPES = ['box', 'violin', 'trend', 'scatter', 'bubble', 'histogram'];
    function niceDtick(range) {
        var span = range[1] - range[0];
        if (span <= 0) return null;
        var rawTick = span / 5;
        var magnitude = Math.pow(10, Math.floor(Math.log10(rawTick)));
        var residual = rawTick / magnitude;
        if (residual <= 1.5) return magnitude;
        if (residual <= 3.5) return 2 * magnitude;
        if (residual <= 7.5) return 5 * magnitude;
        return 10 * magnitude;
    }
    function collectAlignableY(type, raw) {
        var values = [];
        if (!Array.isArray(raw)) return values;
        function push(v) { if (typeof v === 'number' && isFinite(v)) values.push(v); }
        switch (type) {
            case 'box':
            case 'violin':
                raw.forEach(function (i) { if (i.data && Array.isArray(i.data)) i.data.forEach(push); });
                break;
            case 'trend':
                raw.forEach(function (i) { push(i.value); });
                break;
            case 'scatter':
                raw.forEach(function (d) { if (Array.isArray(d)) push(d[1]); });
                break;
            case 'bubble':
                raw.forEach(function (i) { if (i.value) push(i.value[1]); });
                break;
            case 'histogram':
                raw.forEach(push);
                break;
        }
        return values;
    }
    function renderAll() {
        if (typeof Plotly === 'undefined') return; /* 离线 → 保留静态图 */
        var containers = document.querySelectorAll('.chart-plotly-container');
        /* 第一遍：收集全部可对齐 Y 值，统一量程（默认对齐，与静态图 y_range 一致） */
        var allY = [];
        var alignCats = {};
        for (var c = 0; c < containers.length; c++) {
            var jsonEl0 = containers[c].querySelector('script[type="application/json"]');
            if (!jsonEl0) continue;
            var raw0;
            try { raw0 = JSON.parse(jsonEl0.textContent); } catch (e) { continue; }
            var type0 = containers[c].getAttribute('data-chart-type') || 'box';
            if (ALIGNABLE_TYPES.indexOf(type0) === -1) continue;
            allY = allY.concat(collectAlignableY(type0, raw0));
            if (type0 === 'box' || type0 === 'violin') {
                var cs = [];
                raw0.forEach(function (i) { if (i.name && cs.indexOf(i.name) === -1) cs.push(i.name); });
                alignCats[c] = cs;
            }
        }
        var unifiedRange = null, unifiedDtick = null;
        if (allY.length) {
            var gMin = allY[0], gMax = allY[0];
            for (var v = 1; v < allY.length; v++) {
                if (allY[v] < gMin) gMin = allY[v];
                if (allY[v] > gMax) gMax = allY[v];
            }
            var pad = gMax !== gMin ? (gMax - gMin) * 0.05 : 1.0;
            unifiedRange = [gMin - pad, gMax + pad];
            unifiedDtick = niceDtick(unifiedRange);
        }
        for (var k = 0; k < containers.length; k++) {
            (function (container) {
                try {
                    var jsonEl = container.querySelector('script[type="application/json"]');
                    if (!jsonEl) return;
                    var raw = JSON.parse(jsonEl.textContent);
                    var type = container.getAttribute('data-chart-type') || 'box';
                    var title = container.getAttribute('data-chart-title') || '';
                    var traces = buildTraces(type, raw);
                    if (!traces.length) return;
                    var layout = {
                        title: { text: title, x: 0.5, font: { size: 15 } },
                        margin: { l: 60, r: 30, b: 60, t: 50, pad: 4 },
                        showlegend: false, hovermode: 'closest'
                    };
                    // Y轴标题统一标注单位（与前端/静态PNG一致）
                    layout.yaxis = { title: { text: type === 'histogram' ? '频次' : '不平衡量 (g·mm)' } };
                    if (ALIGNABLE_TYPES.indexOf(type) !== -1 && unifiedRange) {
                        layout.yaxis.range = unifiedRange;
                        if (unifiedDtick !== null) layout.yaxis.dtick = unifiedDtick;
                    }
                    if (type === 'box' || type === 'violin') {
                        var cs = alignCats[k] || [];
                        if (cs.length) {
                            layout.xaxis = { type: 'category', range: [-0.5, cs.length - 0.5] };
                            layout.margin.r = 10;
                        }
                    }
                    // 渲染前确保容器可见并采用实际宽度：容器初始 display:none 时
                    // clientWidth=0，Plotly 会退回默认 700px 渲染，SVG 超出容器宽度
                    // 产生横向滚动条与右侧空白，必须先显示并按实际宽度显式设置
                    container.style.display = 'block';
                    var _cw = container.clientWidth || 0;
                    if (_cw > 0) layout.width = _cw;
                    Plotly.newPlot(container, traces, layout, { responsive: true, displaylogo: false });
                    if (_cw > 0) {
                        Plotly.relayout(container, { width: _cw });
                    }
                    var imgBox = container.previousElementSibling;
                    if (imgBox && imgBox.className.indexOf('chart-img-container') !== -1) {
                        imgBox.style.display = 'none';
                    }
                } catch (e) {
                    container.style.display = 'none'; /* 渲染失败 → 保留静态图 */
                }
            })(containers[k]);
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', renderAll);
    } else {
        renderAll();
    }
})();
</script>
"""
