#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Plotly HTML 图表渲染器（chart_generation_optimized 拆分模块）

负责将图表数据渲染为包含 Plotly 图表的完整 HTML 文档。
"""

import json

from app.services.chart_utils import _prepare_chart_config


def _generate_plotly_html(chart_data_json_str, chart_type, surface_name, color, y_range=None):
    """生成包含Plotly图表的完整HTML文档

    Args:
        chart_data_json_str: 图表数据的JSON字符串
        chart_type: 图表类型字符串
        surface_name: 面名称
        color: 图表颜色
        y_range: Y轴范围元组(min, max)，用于跨面对齐刻度

    Returns:
        str: 完整的HTML文档字符串
    """
    chart_config = _prepare_chart_config(chart_type, surface_name, color)
    chart_title = chart_config["title"]
    chart_color = chart_config["color"]

    try:
        from chart_style_config import CHART_FONT_CONFIG, CHART_LAYOUT_CONFIG, GRID_STYLE

        common_layout = CHART_LAYOUT_CONFIG["common"]
        font_config_json = json.dumps(CHART_FONT_CONFIG)
        hoverlabel_json = json.dumps(common_layout["hoverlabel"])
        margin_json = json.dumps(common_layout["margin"])
        grid_style_json = json.dumps(GRID_STYLE)
    except (ImportError, KeyError):
        font_config_json = json.dumps({"family": "sans-serif", "size": 12, "color": "#333333"})
        hoverlabel_json = json.dumps(
            {
                "bgcolor": "rgba(255,255,255,0.95)",
                "bordercolor": "#2563eb",
                "borderwidth": 1,
                "font": {"color": "#333"},
            }
        )
        margin_json = json.dumps({"l": 50, "r": 50, "b": 80, "t": 50, "pad": 4})
        grid_style_json = json.dumps({"color": "#e0e0e0", "width": 1, "dash": "solid"})

    y_range_js = ""
    if y_range and len(y_range) == 2:
        y_range_js = f"range: [{y_range[0]}, {y_range[1]}], "

    html = (
        """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>图表详情</title>
    <script src="/static/libs/plotly/plotly.min.js"></script>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
        }
        #chart-container {
            width: 100%;
            height: 100%;
        }
    </style>
</head>
<body>
    <div id="chart-container"></div>
    <script>
        var chartData = """
        + chart_data_json_str
        + ''';
        var chartType = """
        + json.dumps(chart_type)
        + """;
        var chartTitle = "'''
        + chart_title
        + '''";
        var chartColor = "'''
        + chart_color
        + """";
        var fontConfig = """
        + font_config_json
        + """;
        var hoverlabelConfig = """
        + hoverlabel_json
        + """;
        var marginConfig = """
        + margin_json
        + """;
        var gridStyle = """
        + grid_style_json
        + """;
        var baseLayout = {
            font: fontConfig,
            hoverlabel: hoverlabelConfig,
            margin: marginConfig,
            hovermode: "closest"
        };

        function renderChart() {
            var container = document.getElementById('chart-container');

            if (chartType === 'box') {
                var data = chartData.map(function(item) {
                    return {
                        y: item.data,
                        name: item.name,
                        type: 'box',
                        marker: {
                            color: chartColor
                        }
                    };
                });

                var layout = Object.assign({}, baseLayout, {
                    title: chartTitle,
                    yaxis: {
                        title: '不平衡量',
                        gridcolor: gridStyle.color,
                        gridwidth: gridStyle.width, """
        + y_range_js
        + """
                    },
                    xaxis: {
                        tickangle: -45,
                        automargin: true
                    }
                });

                Plotly.newPlot(container, data, layout, {responsive: true, scrollZoom: true});
            } else if (chartType === 'trend') {
                var x = chartData.map(function(item) { return item.name; });
                var y = chartData.map(function(item) { return item.value; });

                var data = [{
                    x: x,
                    y: y,
                    type: 'scatter',
                    mode: 'lines+markers',
                    marker: {
                        color: chartColor
                    },
                    line: {
                        color: chartColor
                    }
                }];

                var layout = Object.assign({}, baseLayout, {
                    title: chartTitle,
                    yaxis: {
                        title: '不平衡量',
                        gridcolor: gridStyle.color,
                        gridwidth: gridStyle.width, """
        + y_range_js
        + """
                    },
                    xaxis: {
                        tickangle: -45,
                        automargin: true
                    }
                });

                Plotly.newPlot(container, data, layout, {responsive: true, scrollZoom: true});
            } else if (chartType === 'scatter') {
                var x = chartData.map(function(item) { return item[0]; });
                var y = chartData.map(function(item) { return item[1]; });

                var data = [{
                    x: x,
                    y: y,
                    type: 'scatter',
                    mode: 'markers',
                    marker: {
                        color: chartColor,
                        opacity: 0.6
                    }
                }];

                var layout = Object.assign({}, baseLayout, {
                    title: chartTitle,
                    yaxis: {
                        title: '不平衡量',
                        gridcolor: gridStyle.color,
                        gridwidth: gridStyle.width, """
        + y_range_js
        + """
                    },
                    xaxis: {
                        tickangle: -45,
                        automargin: true
                    }
                });

                Plotly.newPlot(container, data, layout, {responsive: true, scrollZoom: true});
            } else if (chartType === 'violin') {
                var data = chartData.map(function(item) {
                    return {
                        y: item.data,
                        name: item.name,
                        type: 'violin',
                        box: {visible: true},
                        meanline: {visible: true},
                        marker: {color: chartColor}
                    };
                });

                var layout = Object.assign({}, baseLayout, {
                    title: chartTitle,
                    yaxis: {
                        title: '不平衡量',
                        gridcolor: gridStyle.color,
                        gridwidth: gridStyle.width, """
        + y_range_js
        + """
                    },
                    xaxis: {
                        tickangle: -45,
                        automargin: true
                    }
                });

                Plotly.newPlot(container, data, layout, {responsive: true, scrollZoom: true});
            } else if (chartType === 'heatmap') {
                var speeds = [];
                var heatRows = {};
                var maxRows = 0;
                chartData.forEach(function(item) {
                    var speed = item[0], idx = item[1], val = item[2];
                    if (!heatRows[speed]) { heatRows[speed] = []; speeds.push(speed); }
                    heatRows[speed].push(val);
                    maxRows = Math.max(maxRows, heatRows[speed].length);
                });

                var z = [];
                for (var r = 0; r < maxRows; r++) {
                    var row = [];
                    speeds.forEach(function(speed) {
                        var vals = heatRows[speed];
                        row.push(r < vals.length ? vals[r] : null);
                    });
                    z.push(row);
                }

                var data = [{z: z, x: speeds, type: 'heatmap', colorscale: 'YlOrRd'}];

                var layout = Object.assign({}, baseLayout, {
                    title: chartTitle,
                    yaxis: {title: '数据点索引'},
                    xaxis: {
                        title: '转速',
                        tickangle: -45,
                        automargin: true
                    }
                });

                Plotly.newPlot(container, data, layout, {responsive: true, scrollZoom: true});
            } else if (chartType === 'histogram') {
                var data = [{
                    x: chartData,
                    type: 'histogram',
                    marker: {color: chartColor, opacity: 0.7},
                    nbinsx: 30
                }];

                var layout = Object.assign({}, baseLayout, {
                    title: chartTitle,
                    yaxis: {
                        title: '频次',
                        gridcolor: gridStyle.color,
                        gridwidth: gridStyle.width
                    },
                    xaxis: {title: '不平衡量', """
        + y_range_js
        + """}
                });

                Plotly.newPlot(container, data, layout, {responsive: true, scrollZoom: true});
            } else if (chartType === 'bubble') {
                var bx = [], by = [], bsizes = [], bnames = [];
                chartData.forEach(function(item, i) {
                    if (item.value && Array.isArray(item.value) && item.value.length >= 3) {
                        bnames.push(item.name);
                        by.push(parseFloat(item.value[1]));
                        bsizes.push(Math.max(parseFloat(item.value[2]) * 2, 4));
                    }
                });

                var data = [{
                    x: bnames,
                    y: by,
                    mode: 'markers',
                    type: 'scatter',
                    marker: {
                        size: bsizes,
                        color: chartColor,
                        opacity: 0.6
                    }
                }];

                var layout = Object.assign({}, baseLayout, {
                    title: chartTitle,
                    yaxis: {
                        title: '不平衡量',
                        gridcolor: gridStyle.color,
                        gridwidth: gridStyle.width, """
        + y_range_js
        + """
                    },
                    xaxis: {
                        title: '转速',
                        tickangle: -45,
                        automargin: true
                    }
                });

                Plotly.newPlot(container, data, layout, {responsive: true, scrollZoom: true});
            } else if (chartType === '3d') {
                var x3 = [], y3 = [], z3 = [];
                var speedSet = [];
                chartData.forEach(function(item) {
                    if (Array.isArray(item) && item.length >= 3) {
                        var s = item[0];
                        if (speedSet.indexOf(s) === -1) speedSet.push(s);
                        y3.push(item[1]);
                        z3.push(parseFloat(item[2]));
                    }
                });
                chartData.forEach(function(item) {
                    if (Array.isArray(item) && item.length >= 3) {
                        x3.push(speedSet.indexOf(item[0]));
                    }
                });

                var data = [{
                    x: x3, y: y3, z: z3,
                    type: 'scatter3d',
                    mode: 'markers',
                    marker: {size: 4, color: z3, colorscale: 'Viridis', opacity: 0.7}
                }];

                var layout = Object.assign({}, baseLayout, {
                    title: chartTitle,
                    scene: {
                        xaxis: {title: '转速', tickvals: speedSet.map(function(s,i){return i;}), ticktext: speedSet},
                        yaxis: {title: '数据点索引'},
                        zaxis: {title: '不平衡量'}
                    }
                });

                Plotly.newPlot(container, data, layout, {responsive: true, scrollZoom: true});
            } else if (chartType === 'parallel') {
                var pnames = [], pmedians = [], pmeans = [];
                chartData.forEach(function(item) {
                    if (Array.isArray(item) && item.length >= 3) {
                        pnames.push(item[0]);
                        pmedians.push(parseFloat(item[1]));
                        pmeans.push(parseFloat(item[2]));
                    }
                });

                var data = [
                    {x: pnames, y: pmedians, type: 'scatter', mode: 'lines+markers', name: '中位数', marker: {color: chartColor}, line: {color: chartColor}},
                    {x: pnames, y: pmeans, type: 'scatter', mode: 'lines+markers', name: '均值', marker: {color: '#f59e0b'}, line: {color: '#f59e0b', dash: 'dash'}}
                ];

                var layout = Object.assign({}, baseLayout, {
                    title: chartTitle,
                    yaxis: {
                        title: '不平衡量',
                        gridcolor: gridStyle.color,
                        gridwidth: gridStyle.width, """
        + y_range_js
        + """
                    },
                    xaxis: {
                        title: '转速',
                        tickangle: -45,
                        automargin: true
                    }
                });

                Plotly.newPlot(container, data, layout, {responsive: true, scrollZoom: true});
            } else if (chartType === 'radar') {
                var rlabels = [], rvalues = [];
                chartData.forEach(function(item) {
                    rlabels.push(item['转速'] || '');
                    rvalues.push(parseFloat(item['不平衡量'] || 0));
                });

                var data = [{
                    r: rvalues.concat([rvalues[0]]),
                    theta: rlabels.concat([rlabels[0]]),
                    type: 'scatterpolar',
                    fill: 'toself',
                    marker: {color: chartColor},
                    fillcolor: chartColor.replace(')', ',0.25)').replace('rgb', 'rgba')
                }];

                var layout = Object.assign({}, baseLayout, {
                    title: chartTitle,
                    polar: {
                        radialaxis: {visible: true}
                    }
                });

                Plotly.newPlot(container, data, layout, {responsive: true, scrollZoom: true});
            } else {
                container.innerHTML = '<div style="padding: 20px; text-align: center;"><p>不支持导出该图表类型: ' + chartType + '</p></div>';
            }
        }

        window.onload = renderChart;
        if (document.readyState === 'complete') {
            renderChart();
        }

        window.onresize = function() {
            var container = document.getElementById('chart-container');
            Plotly.relayout(container, {
                width: container.clientWidth,
                height: container.clientHeight
            });
        };
    </script>
</body>
</html>"""
    )
    return html
