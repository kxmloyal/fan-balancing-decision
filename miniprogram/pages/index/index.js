// index.js
import * as echarts from '../../components/ec-canvas/echarts.min.js';

let chartBox = null;
let chartScatter = null;
let chartTrend = null;

Page({
  data: {
    ecBox: {
      onInit: initChartBox
    },
    ecScatter: {
      onInit: initChartScatter
    },
    ecTrend: {
      onInit: initChartTrend
    }
  },

  onLoad: function () {
    console.log('页面加载完成');
  },

  onShow: function () {
    console.log('页面显示');
    // 页面显示时可以刷新图表数据
    this.refreshCharts();
  },

  onReady: function () {
    console.log('页面初次渲染完成');
  },

  onHide: function () {
    console.log('页面隐藏');
  },

  onUnload: function () {
    console.log('页面卸载');
    // 页面卸载时销毁图表实例
    this.destroyCharts();
  },

  onPullDownRefresh: function () {
    console.log('下拉刷新');
    this.refreshCharts();
    wx.stopPullDownRefresh();
  },

  refreshCharts: function () {
    console.log('刷新图表数据');
    // 这里可以从服务器获取最新数据，然后更新图表
    if (chartBox) {
      chartBox.setOption(getBoxOption());
    }
    if (chartScatter) {
      chartScatter.setOption(getScatterOption());
    }
    if (chartTrend) {
      chartTrend.setOption(getTrendOption());
    }
  },

  destroyCharts: function () {
    console.log('销毁图表实例');
    if (chartBox) {
      chartBox.dispose();
      chartBox = null;
    }
    if (chartScatter) {
      chartScatter.dispose();
      chartScatter = null;
    }
    if (chartTrend) {
      chartTrend.dispose();
      chartTrend = null;
    }
  }
});

function initChartBox(canvas, width, height) {
  chartBox = echarts.init(canvas, null, {
    width: width,
    height: height
  });
  canvas.setChart(chartBox);
  chartBox.setOption(getBoxOption());
  return chartBox;
}

function initChartScatter(canvas, width, height) {
  chartScatter = echarts.init(canvas, null, {
    width: width,
    height: height
  });
  canvas.setChart(chartScatter);
  chartScatter.setOption(getScatterOption());
  return chartScatter;
}

function initChartTrend(canvas, width, height) {
  chartTrend = echarts.init(canvas, null, {
    width: width,
    height: height
  });
  canvas.setChart(chartTrend);
  chartTrend.setOption(getTrendOption());
  return chartTrend;
}

function getBoxOption() {
  return {
    title: {
      text: '箱线图',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      axisPointer: {
        type: 'shadow'
      },
      formatter: function(params) {
        const boxData = params.data;
        return `
          <div style="padding: 10px;">
            <h6 style="margin: 0 0 5px 0; color: #1f77b4;">${params.name}</h6>
            <div style="line-height: 1.6;">
              <p>最小值: <strong>${boxData[0].toFixed(2)}</strong></p>
              <p>第一四分位数: <strong>${boxData[1].toFixed(2)}</strong></p>
              <p>中位数: <strong>${boxData[2].toFixed(2)}</strong></p>
              <p>第三四分位数: <strong>${boxData[3].toFixed(2)}</strong></p>
              <p>最大值: <strong>${boxData[4].toFixed(2)}</strong></p>
            </div>
          </div>
        `;
      }
    },
    legend: {
      data: ['箱线图', '中位线'],
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['3000rpm', '4000rpm', '5000rpm', '6000rpm', '7000rpm'],
      axisLabel: {
        rotate: 45,
        fontSize: 11
      }
    },
    yAxis: {
      type: 'value',
      name: '不平衡量（单位：g·mm）',
      nameTextStyle: {
        fontSize: 12
      }
    },
    series: [{
      name: '箱线图',
      type: 'boxplot',
      data: [
        [1.2, 2.1, 3.5, 4.2, 5.1],
        [0.8, 1.9, 3.2, 4.5, 5.8],
        [1.5, 2.5, 3.8, 4.8, 6.0],
        [0.9, 2.0, 3.0, 4.0, 5.5],
        [1.1, 2.2, 3.3, 4.3, 5.2]
      ],
      itemStyle: {
        color: '#1f77b4'
      }
    }, {
      name: '中位线',
      type: 'line',
      data: [3.5, 3.2, 3.8, 3.0, 3.3],
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        color: '#ff7f0e',
        width: 2
      }
    }]
  };
}

function getScatterOption() {
  return {
    title: {
      text: '散点图',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        return `
          <div style="padding: 10px;">
            <h6 style="margin: 0 0 5px 0; color: #1f77b4;">散点数据</h6>
            <div style="line-height: 1.6;">
              <p>转速: <strong>${params.data[0]}</strong></p>
              <p>不平衡量: <strong>${params.data[1].toFixed(2)}</strong></p>
            </div>
          </div>
        `;
      }
    },
    legend: {
      data: ['散点图'],
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '转速（rpm）'
    },
    yAxis: {
      type: 'value',
      name: '不平衡量（单位：g·mm）'
    },
    series: [{
      name: '散点图',
      type: 'scatter',
      data: [
        [3000, 3.5],
        [3000, 3.2],
        [3000, 3.8],
        [4000, 3.0],
        [4000, 3.3],
        [4000, 3.6],
        [5000, 3.2],
        [5000, 3.5],
        [5000, 3.8],
        [6000, 3.0],
        [6000, 3.2],
        [6000, 3.4],
        [7000, 3.1],
        [7000, 3.3],
        [7000, 3.5]
      ],
      itemStyle: {
        color: '#1f77b4',
        opacity: 0.8
      },
      symbolSize: 8
    }]
  };
}

function getTrendOption() {
  return {
    title: {
      text: '趋势图',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        return `
          <div style="padding: 10px;">
            <h6 style="margin: 0 0 5px 0; color: #1f77b4;">趋势数据</h6>
            <div style="line-height: 1.6;">
              <p>转速: <strong>${params[0].name}</strong></p>
              <p>不平衡量: <strong>${params[0].value.toFixed(2)}</strong></p>
            </div>
          </div>
        `;
      }
    },
    legend: {
      data: ['趋势线'],
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['3000rpm', '4000rpm', '5000rpm', '6000rpm', '7000rpm'],
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '不平衡量（单位：g·mm）'
    },
    series: [{
      name: '趋势线',
      type: 'line',
      data: [3.5, 3.2, 3.8, 3.0, 3.3],
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: {
        color: '#1f77b4',
        width: 3
      },
      itemStyle: {
        color: '#1f77b4'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [{
            offset: 0, color: 'rgba(31, 119, 180, 0.3)'
          }, {
            offset: 1, color: 'rgba(31, 119, 180, 0.1)'
          }]
        }
      }
    }]
  };
}