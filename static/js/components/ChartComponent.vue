<template>
  <div class="chart-container">
    <v-chart 
      ref="chartRef"
      class="chart"
      :option="chartOption"
      :loading="loading"
      :init-options="initOptions"
      @click="handleChartClick"
      @dblclick="handleChartDblClick"
      @mouseover="handleChartMouseOver"
      @mouseout="handleChartMouseOut"
    />
    <div v-if="error" class="chart-error">
      <i class="bi bi-exclamation-triangle text-danger"></i>
      <span>{{ error }}</span>
    </div>
  </div>
</template>

<script>
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { 
  BarChart, 
  LineChart, 
  ScatterChart, 
  BoxplotChart, 
  HeatmapChart,
  ParallelChart
} from 'echarts/charts';
import { 
  TitleComponent, 
  TooltipComponent, 
  LegendComponent, 
  GridComponent, 
  DatasetComponent, 
  TransformComponent,
  ToolboxComponent,
  DataZoomComponent,
  VisualMapComponent
} from 'echarts/components';
import VChart from 'vue-echarts';

// 注册必要的组件
use([
  CanvasRenderer,
  BarChart,
  LineChart,
  ScatterChart,
  BoxplotChart,
  HeatmapChart,
  ParallelChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  ToolboxComponent,
  DataZoomComponent,
  VisualMapComponent
]);

export default {
  name: 'ChartComponent',
  components: {
    VChart
  },
  props: {
    chartType: {
      type: String,
      required: true,
      validator: (value) => {
        return ['box', 'scatter', 'trend', 'violin', 'heatmap', 'histogram', '3d', 'parallel', 'bubble'].includes(value);
      }
    },
    chartData: {
      type: [Array, Object],
      default: () => []
    },
    options: {
      type: Object,
      default: () => ({})
    },
    height: {
      type: String,
      default: '400px'
    },
    width: {
      type: String,
      default: '100%'
    }
  },
  data() {
    return {
      loading: false,
      error: null,
      chartOption: {},
      initOptions: {
        renderer: 'canvas',
        devicePixelRatio: window.devicePixelRatio || 1,
        lazyUpdate: true,
        useDirtyRect: true
      }
    };
  },
  computed: {
    chartStyle() {
      return {
        height: this.height,
        width: this.width
      };
    }
  },
  watch: {
    chartType: {
      handler() {
        this.updateChart();
      },
      immediate: true
    },
    chartData: {
      handler() {
        this.updateChart();
      },
      deep: true,
      immediate: true
    },
    options: {
      handler() {
        this.updateChart();
      },
      deep: true
    }
  },
  mounted() {
    this.updateChart();
    window.addEventListener('resize', this.handleResize);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
  },
  methods: {
    updateChart() {
      this.loading = true;
      this.error = null;
      
      try {
        const validatedData = this.validateAndPreprocessData(this.chartData, this.chartType);
        this.chartOption = this.createChartOption(validatedData, this.chartType, this.options);
        this.loading = false;
      } catch (error) {
        console.error('更新图表时出错:', error);
        this.error = `图表更新失败: ${error.message}`;
        this.loading = false;
      }
    },
    validateAndPreprocessData(data, chartType) {
      if (!data || typeof data !== 'object') {
        return [];
      }
      
      switch (chartType) {
        case 'box':
          return this.validateBoxPlotData(data);
        case 'scatter':
          return this.validateScatterData(data);
        case 'trend':
          return this.validateTrendData(data);
        case 'violin':
          return this.validateViolinData(data);
        case 'heatmap':
          return this.validateHeatmapData(data);
        case 'histogram':
          return this.validateHistogramData(data);
        case '3d':
          return this.validate3DScatterData(data);
        case 'parallel':
          return this.validateParallelData(data);
        case 'bubble':
          return this.validateBubbleData(data);
        default:
          return data;
      }
    },
    validateBoxPlotData(data) {
      if (Array.isArray(data)) {
        return data.map((item, index) => ({
          name: item.name || `数据${index + 1}`,
          data: Array.isArray(item.data) && item.data.length === 5 ? item.data : [0, 0, 0, 0, 0]
        }));
      }
      return [{ name: '默认数据', data: [0, 0, 0, 0, 0] }];
    },
    validateScatterData(data) {
      if (Array.isArray(data)) {
        return data.map(item => Array.isArray(item) && item.length >= 2 ? item : [0, 0]);
      }
      return [];
    },
    validateTrendData(data) {
      if (Array.isArray(data)) {
        return data.map((item, index) => ({
          name: item.name || `数据${index + 1}`,
          value: typeof item.value === 'number' ? item.value : 0
        }));
      }
      return [];
    },
    validateViolinData(data) {
      if (Array.isArray(data)) {
        return data.map((item, index) => ({
          name: item.name || `数据${index + 1}`,
          data: Array.isArray(item.data) ? item.data : []
        }));
      }
      return [];
    },
    validateHeatmapData(data) {
      if (Array.isArray(data)) {
        return data.map(item => Array.isArray(item) && item.length >= 3 ? item : [0, 0, 0]);
      }
      return [];
    },
    validateHistogramData(data) {
      if (Array.isArray(data)) {
        return data.filter(item => typeof item === 'number');
      }
      return [];
    },
    validate3DScatterData(data) {
      if (Array.isArray(data)) {
        return data.map(item => Array.isArray(item) && item.length >= 3 ? item : [0, 0, 0]);
      }
      return [];
    },
    validateParallelData(data) {
      if (Array.isArray(data)) {
        return data.map(item => Array.isArray(item) ? item : []);
      }
      return [];
    },
    validateBubbleData(data) {
      if (Array.isArray(data)) {
        return data.map((item, index) => ({
          name: item.name || `数据${index + 1}`,
          value: Array.isArray(item.value) && item.value.length >= 3 ? item.value : [0, 0, 1]
        }));
      }
      return [];
    },
    createChartOption(data, chartType, options = {}) {
      switch (chartType) {
        case 'box':
          return this.createBoxPlotOption(data, options);
        case 'scatter':
          return this.createScatterPlotOption(data, options);
        case 'trend':
          return this.createTrendPlotOption(data, options);
        case 'violin':
          return this.createViolinPlotOption(data, options);
        case 'heatmap':
          return this.createHeatmapOption(data, options);
        case 'histogram':
          return this.createHistogramOption(data, options);
        case '3d':
          return this.create3DScatterOption(data, options);
        case 'parallel':
          return this.createParallelOption(data, options);
        case 'bubble':
          return this.createBubbleOption(data, options);
        default:
          return {};
      }
    },
    createBoxPlotOption(data, options = {}) {
      const { title = '箱线图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
      
      const seriesData = data;
      const xAxisData = seriesData.map(item => item.name);
      const boxData = seriesData.map(item => item.data);
      const medianData = seriesData.map(item => item.data[2]);

      return {
        title: {
          text: title,
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
                <h6 style="margin: 0 0 5px 0; color: ${color};">${params.name}</h6>
                <div style="line-height: 1.6;">
                  <p>最小值: <strong>${boxData[0].toFixed(2)}</strong></p>
                  <p>第一四分位数: <strong>${boxData[1].toFixed(2)}</strong></p>
                  <p>中位数: <strong>${boxData[2].toFixed(2)}</strong></p>
                  <p>第三四分位数: <strong>${boxData[3].toFixed(2)}</strong></p>
                  <p>最大值: <strong>${boxData[4].toFixed(2)}</strong></p>
                </div>
              </div>
            `;
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: color,
          borderWidth: 1,
          borderRadius: 5
        },
        legend: {
          data: ['箱线图', '中位线'],
          bottom: 10,
          textStyle: {
            fontSize: 12
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: xAxisData,
          axisLabel: {
            rotate: 45,
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          }
        },
        yAxis: {
          type: 'value',
          name: yAxisLabel,
          nameTextStyle: {
            fontSize: 12
          },
          axisLabel: {
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0',
              type: 'dashed'
            }
          }
        },
        series: [{
          name: '箱线图',
          type: 'boxplot',
          data: boxData,
          itemStyle: {
            color: color,
            borderWidth: 1
          },
          emphasis: {
            itemStyle: {
              color: color,
              borderWidth: 2
            }
          }
        }, {
          name: '中位线',
          type: 'line',
          data: medianData,
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            color: '#ff7f0e',
            width: 2,
            type: 'solid'
          },
          itemStyle: {
            color: '#ff7f0e',
            borderColor: '#fff',
            borderWidth: 1
          }
        }],
        toolbox: {
          feature: {
            dataZoom: {
              yAxisIndex: 'none'
            },
            restore: {},
            saveAsImage: {
              pixelRatio: 2,
              backgroundColor: '#fff'
            }
          },
          right: 10,
          top: 10
        },
        dataZoom: [
          {
            type: 'inside',
            start: 0,
            end: 100,
            xAxisIndex: [0]
          },
          {
            start: 0,
            end: 100,
            xAxisIndex: [0]
          }
        ]
      };
    },
    createScatterPlotOption(data, options = {}) {
      const { title = '散点图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
      
      const seriesData = data;

      return {
        title: {
          text: title,
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
                <h6 style="margin: 0 0 5px 0; color: ${color};">散点数据</h6>
                <div style="line-height: 1.6;">
                  <p>X: <strong>${params.data[0]}</strong></p>
                  <p>Y: <strong>${params.data[1].toFixed(2)}</strong></p>
                </div>
              </div>
            `;
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: color,
          borderWidth: 1,
          borderRadius: 5
        },
        legend: {
          data: ['散点图'],
          bottom: 10,
          textStyle: {
            fontSize: 12
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          axisLabel: {
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0',
              type: 'dashed'
            }
          }
        },
        yAxis: {
          type: 'value',
          name: yAxisLabel,
          nameTextStyle: {
            fontSize: 12
          },
          axisLabel: {
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0',
              type: 'dashed'
            }
          }
        },
        series: [{
          name: '散点图',
          type: 'scatter',
          data: seriesData,
          itemStyle: {
            color: color,
            opacity: 0.8
          },
          emphasis: {
            itemStyle: {
              color: color,
              opacity: 1,
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.3)'
            }
          },
          symbolSize: 8
        }],
        toolbox: {
          feature: {
            dataZoom: {
              yAxisIndex: 'none'
            },
            restore: {},
            saveAsImage: {
              pixelRatio: 2,
              backgroundColor: '#fff'
            }
          },
          right: 10,
          top: 10
        },
        dataZoom: [
          {
            type: 'inside',
            start: 0,
            end: 100
          },
          {
            start: 0,
            end: 100
          }
        ]
      };
    },
    createTrendPlotOption(data, options = {}) {
      const { title = '趋势图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
      
      const seriesData = data;
      const xAxisData = seriesData.map(item => item.name);
      const yAxisData = seriesData.map(item => item.value);

      return {
        title: {
          text: title,
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
                <h6 style="margin: 0 0 5px 0; color: ${color};">趋势数据</h6>
                <div style="line-height: 1.6;">
                  <p>X: <strong>${params[0].name}</strong></p>
                  <p>Y: <strong>${params[0].value.toFixed(2)}</strong></p>
                </div>
              </div>
            `;
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: color,
          borderWidth: 1,
          borderRadius: 5
        },
        legend: {
          data: ['趋势线'],
          bottom: 10,
          textStyle: {
            fontSize: 12
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: xAxisData,
          axisLabel: {
            rotate: 45,
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          }
        },
        yAxis: {
          type: 'value',
          name: yAxisLabel,
          nameTextStyle: {
            fontSize: 12
          },
          axisLabel: {
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0',
              type: 'dashed'
            }
          }
        },
        series: [{
          name: '趋势线',
          type: 'line',
          data: yAxisData,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            color: color,
            width: 3
          },
          itemStyle: {
            color: color,
            shadowBlur: 3,
            shadowColor: 'rgba(0, 0, 0, 0.2)'
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [{
                offset: 0, color: color + '80'
              }, {
                offset: 1, color: color + '10'
              }]
            }
          }
        }],
        toolbox: {
          feature: {
            dataZoom: {
              yAxisIndex: 'none'
            },
            restore: {},
            saveAsImage: {
              pixelRatio: 2,
              backgroundColor: '#fff'
            }
          },
          right: 10,
          top: 10
        },
        dataZoom: [
          {
            type: 'inside',
            start: 0,
            end: 100
          },
          {
            start: 0,
            end: 100
          }
        ]
      };
    },
    createViolinPlotOption(data, options = {}) {
      const { title = '小提琴图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
      
      const seriesData = data;

      return {
        title: {
          text: title,
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
            return `
              <div style="padding: 10px;">
                <h6 style="margin: 0 0 5px 0; color: ${color};">${params.name}</h6>
                <div style="line-height: 1.6;">
                  <p>数据点数量: <strong>${params.data.length}</strong></p>
                  <p>最小值: <strong>${Math.min(...params.data).toFixed(2)}</strong></p>
                  <p>最大值: <strong>${Math.max(...params.data).toFixed(2)}</strong></p>
                </div>
              </div>
            `;
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: color,
          borderWidth: 1,
          borderRadius: 5
        },
        legend: {
          data: ['小提琴图'],
          bottom: 10,
          textStyle: {
            fontSize: 12
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: seriesData.map(item => item.name),
          axisLabel: {
            rotate: 45,
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          }
        },
        yAxis: {
          type: 'value',
          name: yAxisLabel,
          nameTextStyle: {
            fontSize: 12
          },
          axisLabel: {
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0',
              type: 'dashed'
            }
          }
        },
        series: [{
          name: '小提琴图',
          type: 'violin',
          data: seriesData.map(item => item.data),
          itemStyle: {
            color: color,
            borderWidth: 1
          },
          emphasis: {
            itemStyle: {
              color: color,
              borderWidth: 2
            }
          },
          boxplot: {
            visible: true,
            itemStyle: {
              color: '#333'
            }
          }
        }],
        toolbox: {
          feature: {
            dataZoom: {
              yAxisIndex: 'none'
            },
            restore: {},
            saveAsImage: {
              pixelRatio: 2,
              backgroundColor: '#fff'
            }
          },
          right: 10,
          top: 10
        },
        dataZoom: [
          {
            type: 'inside',
            start: 0,
            end: 100
          },
          {
            start: 0,
            end: 100
          }
        ]
      };
    },
    createHeatmapOption(data, options = {}) {
      const { title = '热力图', yAxisLabel = '数据点' } = options;
      
      const seriesData = data;
      const xAxisData = [...new Set(seriesData.map(item => item[0]))];
      const yAxisData = [...new Set(seriesData.map(item => item[1]))];
      const heatmapData = seriesData.map(item => [xAxisData.indexOf(item[0]), yAxisData.indexOf(item[1]), item[2]]);
      
      const min = Math.min(...seriesData.map(item => item[2]));
      const max = Math.max(...seriesData.map(item => item[2]));

      return {
        title: {
          text: title,
          left: 'center',
          textStyle: {
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        tooltip: {
          position: 'top',
          formatter: function(params) {
            return `
              <div style="padding: 10px;">
                <h6 style="margin: 0 0 5px 0;">热力图数据</h6>
                <div style="line-height: 1.6;">
                  <p>X: <strong>${xAxisData[params.data[0]]}</strong></p>
                  <p>Y: <strong>${yAxisData[params.data[1]]}</strong></p>
                  <p>值: <strong>${params.data[2].toFixed(2)}</strong></p>
                </div>
              </div>
            `;
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#1f77b4',
          borderWidth: 1,
          borderRadius: 5
        },
        grid: {
          height: '60%',
          top: '10%',
          left: '3%',
          right: '4%',
          bottom: '20%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: xAxisData,
          splitArea: {
            show: true,
            areaStyle: {
              color: ['#fff', '#f5f5f5']
            }
          },
          axisLabel: {
            rotate: 45,
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          }
        },
        yAxis: {
          type: 'category',
          data: yAxisData,
          splitArea: {
            show: true,
            areaStyle: {
              color: ['#fff', '#f5f5f5']
            }
          },
          name: yAxisLabel,
          nameTextStyle: {
            fontSize: 12
          },
          axisLabel: {
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          }
        },
        visualMap: {
          min: min,
          max: max,
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: '10%',
          textStyle: {
            fontSize: 11
          },
          inRange: {
            color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
          }
        },
        series: [{
          name: '热力图',
          type: 'heatmap',
          data: heatmapData,
          label: {
            show: true,
            fontSize: 9,
            color: '#333'
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            },
            label: {
              show: true,
              fontSize: 11,
              fontWeight: 'bold'
            }
          },
          itemStyle: {
            borderRadius: 2
          }
        }],
        toolbox: {
          feature: {
            dataZoom: {
              yAxisIndex: 'none'
            },
            restore: {},
            saveAsImage: {
              pixelRatio: 2,
              backgroundColor: '#fff'
            }
          },
          right: 10,
          top: 10
        },
        dataZoom: [
          {
            type: 'inside',
            start: 0,
            end: 100
          },
          {
            start: 0,
            end: 100
          }
        ]
      };
    },
    createHistogramOption(data, options = {}) {
      const { title = '直方图', color = '#1f77b4', xAxisLabel = '不平衡量（单位：g·mm）' } = options;
      
      const seriesData = data;

      return {
        title: {
          text: title,
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
                <h6 style="margin: 0 0 5px 0; color: ${color};">直方图数据</h6>
                <div style="line-height: 1.6;">
                  <p>区间: <strong>${params[0].name}</strong></p>
                  <p>频次: <strong>${params[0].value}</strong></p>
                </div>
              </div>
            `;
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: color,
          borderWidth: 1,
          borderRadius: 5
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          name: xAxisLabel,
          nameTextStyle: {
            fontSize: 12
          },
          axisLabel: {
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0',
              type: 'dashed'
            }
          }
        },
        yAxis: {
          type: 'value',
          name: '频次',
          nameTextStyle: {
            fontSize: 12
          },
          axisLabel: {
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0',
              type: 'dashed'
            }
          }
        },
        series: [{
          name: '直方图',
          type: 'bar',
          data: seriesData,
          itemStyle: {
            color: color,
            borderRadius: [2, 2, 0, 0]
          },
          emphasis: {
            itemStyle: {
              color: color,
              shadowBlur: 6,
              shadowColor: 'rgba(0, 0, 0, 0.3)'
            }
          }
        }],
        toolbox: {
          feature: {
            dataZoom: {
              yAxisIndex: 'none'
            },
            restore: {},
            saveAsImage: {
              pixelRatio: 2,
              backgroundColor: '#fff'
            }
          },
          right: 10,
          top: 10
        },
        dataZoom: [
          {
            type: 'inside',
            start: 0,
            end: 100
          },
          {
            start: 0,
            end: 100
          }
        ]
      };
    },
    create3DScatterOption(data, options = {}) {
      const { title = '3D散点图' } = options;
      
      const seriesData = data;

      return {
        title: {
          text: title,
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
                <h6 style="margin: 0 0 5px 0; color: #1f77b4;">3D散点数据</h6>
                <div style="line-height: 1.6;">
                  <p>X: <strong>${params.data[0]}</strong></p>
                  <p>Y: <strong>${params.data[1]}</strong></p>
                  <p>Z: <strong>${params.data[2].toFixed(2)}</strong></p>
                </div>
              </div>
            `;
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#1f77b4',
          borderWidth: 1,
          borderRadius: 5
        },
        xAxis3D: {
          type: 'value',
          name: 'X轴',
          nameTextStyle: {
            fontSize: 12
          },
          axisLabel: {
            fontSize: 10
          }
        },
        yAxis3D: {
          type: 'value',
          name: 'Y轴',
          nameTextStyle: {
            fontSize: 12
          },
          axisLabel: {
            fontSize: 10
          }
        },
        zAxis3D: {
          type: 'value',
          name: 'Z轴',
          nameTextStyle: {
            fontSize: 12
          },
          axisLabel: {
            fontSize: 10
          }
        },
        grid3D: {
          viewControl: {
            projection: 'perspective',
            autoRotate: true,
            autoRotateSpeed: 5,
            distance: 120
          },
          light: {
            main: {
              intensity: 1.2,
              shadow: true
            },
            ambient: {
              intensity: 0.6
            }
          }
        },
        series: [{
          name: '3D散点图',
          type: 'scatter3D',
          data: seriesData,
          itemStyle: {
            color: function(params) {
              return {
                type: 'radial',
                x: 0.4,
                y: 0.3,
                r: 1,
                colorStops: [{
                  offset: 0, color: 'rgb(129, 227, 238)'
                }, {
                  offset: 1, color: 'rgb(25, 183, 207)'
                }]
              };
            }
          },
          symbolSize: 8
        }],
        toolbox: {
          feature: {
            restore: {},
            saveAsImage: {
              pixelRatio: 2,
              backgroundColor: '#fff'
            }
          },
          right: 10,
          top: 10
        }
      };
    },
    createParallelOption(data, options = {}) {
      const { title = '平行坐标图' } = options;
      
      const seriesData = data;

      return {
        title: {
          text: title,
          left: 'center',
          textStyle: {
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        tooltip: {
          trigger: 'axis'
        },
        parallelAxis: seriesData[0].map((_, index) => ({
          dim: index,
          name: `维度${index + 1}`,
          nameTextStyle: {
            fontSize: 12
          },
          axisLabel: {
            fontSize: 10
          }
        })),
        parallel: {
          left: '5%',
          right: '10%',
          bottom: '10%',
          top: '15%'
        },
        series: [{
          name: '平行坐标图',
          type: 'parallel',
          data: seriesData,
          lineStyle: {
            width: 2,
            color: function() {
              return {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 1,
                y2: 0,
                colorStops: [{
                  offset: 0, color: '#1f77b4'
                }, {
                  offset: 1, color: '#ff7f0e'
                }]
              };
            },
            opacity: 0.7
          },
          emphasis: {
            lineStyle: {
              width: 4,
              opacity: 1
            }
          }
        }],
        toolbox: {
          feature: {
            restore: {},
            saveAsImage: {
              pixelRatio: 2,
              backgroundColor: '#fff'
            }
          },
          right: 10,
          top: 10
        }
      };
    },
    createBubbleOption(data, options = {}) {
      const { title = '气泡图', color = '#1f77b4', yAxisLabel = '不平衡量（单位：g·mm）' } = options;
      
      const seriesData = data.map(item => item.value || item);

      return {
        title: {
          text: title,
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
                <h6 style="margin: 0 0 5px 0; color: ${color};">气泡数据</h6>
                <div style="line-height: 1.6;">
                  <p>X: <strong>${params.data[0]}</strong></p>
                  <p>Y: <strong>${params.data[1].toFixed(2)}</strong></p>
                  <p>大小: <strong>${params.data[2]}</strong></p>
                </div>
              </div>
            `;
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: color,
          borderWidth: 1,
          borderRadius: 5
        },
        xAxis: {
          type: 'value',
          axisLabel: {
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0',
              type: 'dashed'
            }
          }
        },
        yAxis: {
          type: 'value',
          name: yAxisLabel,
          nameTextStyle: {
            fontSize: 12
          },
          axisLabel: {
            fontSize: 11
          },
          axisLine: {
            lineStyle: {
              color: '#ccc'
            }
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0',
              type: 'dashed'
            }
          }
        },
        series: [{
          name: '气泡图',
          type: 'scatter',
          data: seriesData,
          symbolSize: function(data) {
            return Math.sqrt(data[2]) * 2;
          },
          itemStyle: {
            color: color,
            opacity: 0.8
          },
          emphasis: {
            itemStyle: {
              color: color,
              opacity: 1,
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.3)'
            }
          }
        }],
        toolbox: {
          feature: {
            dataZoom: {
              yAxisIndex: 'none'
            },
            restore: {},
            saveAsImage: {
              pixelRatio: 2,
              backgroundColor: '#fff'
            }
          },
          right: 10,
          top: 10
        },
        dataZoom: [
          {
            type: 'inside',
            start: 0,
            end: 100
          },
          {
            start: 0,
            end: 100
          }
        ]
      };
    },
    handleChartClick(event) {
      this.$emit('chart-click', event);
    },
    handleChartDblClick(event) {
      this.$emit('chart-dblclick', event);
    },
    handleChartMouseOver(event) {
      this.$emit('chart-mouseover', event);
    },
    handleChartMouseOut(event) {
      this.$emit('chart-mouseout', event);
    },
    handleResize() {
      if (this.$refs.chartRef) {
        this.$refs.chartRef.resize();
      }
    }
  }
};
</script>

<style scoped>
.chart-container {
  position: relative;
  width: 100%;
}

.chart {
  width: 100%;
  height: 100%;
}

.chart-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #dc3545;
  padding: 20px;
  background-color: rgba(255, 255, 255, 0.9);
  border: 1px solid #dc3545;
  border-radius: 5px;
}

.chart-error i {
  font-size: 2rem;
  margin-bottom: 10px;
  display: block;
}
</style>