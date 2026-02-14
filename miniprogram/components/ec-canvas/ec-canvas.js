// ec-canvas.js
import * as echarts from './echarts.min.js';

Component({
  properties: {
    canvasId: {
      type: String,
      value: 'ec-canvas'
    },
    ec: {
      type: Object
    },
    lazyLoad: {
      type: Boolean,
      value: false
    }
  },
  data: {
    isUseNewCanvas: true
  },
  ready: function () {
    if (!this.data.lazyLoad) {
      this.init();
    }
  },
  methods: {
    init: function (callback) {
      const version = wx.getSystemInfoSync().SDKVersion;
      const isValid = compareVersion(version, '2.7.1') >= 0;
      if (!isValid) {
        console.error('ec-canvas: 微信基础库版本过低，需大于等于 2.7.1');
        return;
      }

      const canvasId = this.data.canvasId;
      const ec = this.data.ec;
      if (!ec) {
        console.error('ec-canvas: 请传入正确的 ec 配置');
        return;
      }

      if (!ec.lazyUpdate) {
        this.ctx = wx.createCanvasContext(canvasId, this);
        this.canvas = new WxCanvas(this.ctx, canvasId);
        this.chart = echarts.init(this.canvas, ec.theme);
        this.canvas.setChart(this.chart);

        const query = wx.createSelectorQuery().in(this);
        query.select('#' + canvasId).boundingClientRect(res => {
          if (!res) {
            console.error('ec-canvas: 找不到 canvas 元素');
            return;
          }
          this.canvas.width = res.width;
          this.canvas.height = res.height;
          this.chart.resize();
        }).exec();

        if (ec.option) {
          this.chart.setOption(ec.option);
        }

        if (callback) {
          callback(this.chart);
        }
      } else {
        this.ctx = wx.createCanvasContext(canvasId, this);
        this.canvas = new WxCanvas(this.ctx, canvasId);
        this.chart = echarts.init(this.canvas, ec.theme);
        this.canvas.setChart(this.chart);

        const query = wx.createSelectorQuery().in(this);
        query.select('#' + canvasId).boundingClientRect(res => {
          if (!res) {
            console.error('ec-canvas: 找不到 canvas 元素');
            return;
          }
          this.canvas.width = res.width;
          this.canvas.height = res.height;
          this.chart.resize();

          if (ec.option) {
            this.chart.setOption(ec.option);
          }

          if (callback) {
            callback(this.chart);
          }
        }).exec();
      }

      this.triggerEvent('init', { canvas: this.canvas, chart: this.chart });
    },
    getChart: function () {
      return this.chart;
    },
    setOption: function (option, notMerge, lazyUpdate) {
      if (this.chart) {
        this.chart.setOption(option, notMerge, lazyUpdate);
      } else {
        console.error('ec-canvas: 图表尚未初始化');
      }
    },
    resize: function () {
      if (this.chart) {
        this.chart.resize();
      } else {
        console.error('ec-canvas: 图表尚未初始化');
      }
    },
    destroy: function () {
      if (this.chart) {
        this.chart.dispose();
        this.chart = null;
      }
    }
  }
});

function compareVersion(v1, v2) {
  v1 = v1.split('.');
  v2 = v2.split('.');
  const len = Math.max(v1.length, v2.length);

  while (v1.length < len) {
    v1.push('0');
  }
  while (v2.length < len) {
    v2.push('0');
  }

  for (let i = 0; i < len; i++) {
    const num1 = parseInt(v1[i]);
    const num2 = parseInt(v2[i]);

    if (num1 > num2) {
      return 1;
    } else if (num1 < num2) {
      return -1;
    }
  }

  return 0;
}

class WxCanvas {
  constructor(ctx, canvasId) {
    this.ctx = ctx;
    this.canvasId = canvasId;
    this.chart = null;
  }

  getContext(contextType) {
    return this.ctx;
  }

  setChart(chart) {
    this.chart = chart;
  }

  set width(w) {
    this._width = w;
  }

  get width() {
    return this._width;
  }

  set height(h) {
    this._height = h;
  }

  get height() {
    return this._height;
  }

  get canvasId() {
    return this.canvasId;
  }

  toDataURL(type, quality) {
    return new Promise((resolve, reject) => {
      wx.canvasToTempFilePath({
        canvasId: this.canvasId,
        success: res => {
          resolve(res.tempFilePath);
        },
        fail: reject
      });
    });
  }
}