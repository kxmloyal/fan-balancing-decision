// 图表类型定义
export type ChartType = 'box' | 'scatter' | 'trend' | 'violin' | 'heatmap' | 'histogram' | '3d' | 'parallel' | 'bubble';

// 图表数据接口
export interface ChartData {
  [key: string]: any;
}

// 箱线图数据接口
export interface BoxPlotData {
  name: string;
  data: number[];
}

// 散点图数据接口
export interface ScatterData {
  [0]: number | string; // x轴值
  [1]: number; // y轴值
}

// 趋势图数据接口
export interface TrendData {
  name: string | number;
  value: number;
}

// 小提琴图数据接口
export interface ViolinData {
  name: string;
  data: number[];
}

// 热力图数据接口
export interface HeatmapData {
  [0]: string | number; // x轴值
  [1]: string | number; // y轴值
  [2]: number; // 热力值
}

// 直方图数据接口
export interface HistogramData {
  name: string;
  value: number;
}

// 3D散点图数据接口
export interface Scatter3DData {
  [0]: number | string; // x轴值
  [1]: number | string; // y轴值
  [2]: number; // z轴值
}

// 图表配置选项接口
export interface ChartOptions {
  title?: string;
  color?: string;
  yAxisLabel?: string;
  xAxisLabel?: string;
  [key: string]: any;
}

// 图表容器配置接口
export interface ChartContainer {
  id: string;
  type: ChartType;
  data: ChartData;
  options?: ChartOptions;
}

// 响应式配置接口
export interface ResponsiveConfig {
  title?: {
    textStyle?: {
      fontSize?: number;
    };
  };
  legend?: {
    show?: boolean;
    textStyle?: {
      fontSize?: number;
    };
  };
  tooltip?: {
    position?: string;
  };
  xAxis?: {
    axisLabel?: {
      fontSize?: number;
      rotate?: number;
    };
  };
  yAxis?: {
    axisLabel?: {
      fontSize?: number;
    };
  };
}

// 错误处理接口
export interface ErrorResponse {
  success: boolean;
  message: string;
  error?: any;
}

// 图表更新响应接口
export interface ChartUpdateResponse {
  success: boolean;
  message?: string;
  charts_html?: string;
  chart_types?: string[];
  chart_layout?: string;
  error?: string;
}

// 事件处理接口
export interface EventHandler {
  handleEvent: (event: Event) => void;
  cleanup?: () => void;
}

// 数据处理接口
export interface DataProcessor {
  process: (data: any) => any;
  validate: (data: any) => boolean;
}

// 缓存接口
export interface Cache {
  get: (key: string) => any;
  set: (key: string, value: any) => void;
  has: (key: string) => boolean;
  delete: (key: string) => void;
  clear: () => void;
}

// 响应式尺寸接口
export interface ResponsiveSize {
  width: number;
  height: number;
  breakpoint: 'small' | 'medium' | 'large';
}

// 图表管理器接口
export interface ChartManager {
  initChart: (containerId: string, chartType: ChartType, data: ChartData, options?: ChartOptions) => any;
  renderChart: (containerId: string, chartType: ChartType, data: ChartData, options?: ChartOptions) => void;
  resizeChart: (containerId: string) => void;
  destroyChart: (containerId: string) => void;
  destroyAllCharts: () => void;
  resizeAllCharts: () => void;
}

// 模态框接口
export interface ModalManager {
  open: (options: any) => void;
  close: () => void;
  update: (content: string) => void;
}

// 加载状态接口
export interface LoadingState {
  show: (containerId: string, message?: string) => void;
  hide: (containerId: string) => void;
  isLoading: (containerId: string) => boolean;
}

// 图表点击事件接口
export interface ChartClickEvent {
  chartId: string;
  chartType: ChartType;
  data: any;
  position: { x: number; y: number };
}

// 拖拽事件接口
export interface DragEvent {
  source: HTMLElement;
  target: HTMLElement;
  position: { x: number; y: number };
}

// 配置接口
export interface AppConfig {
  debug: boolean;
  defaultChartType: ChartType;
  defaultLayout: 'stacked' | 'parallel';
  animation: boolean;
  performance: {
    enableCaching: boolean;
    enableLazyLoading: boolean;
    batchSize: number;
    throttleDelay: number;
    debounceDelay: number;
  };
}
