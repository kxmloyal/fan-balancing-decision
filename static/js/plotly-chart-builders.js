// 图表构建器 — 扩展 SimplePlotlyManager 的原型方法
// 此文件必须在 simple-plotly-manager.js 之前加载


SimplePlotlyManager.prototype.convertToBoxPlotData = function(data) {
        if (!data || typeof data !== 'object') {
            console.warn('无效的箱线图数据，使用默认数据');
            // 返回默认数据
            return [
                { name: '2500rpm', data: [1, 2, 3, 4, 5] },
                { name: '3000rpm', data: [2, 3, 4, 5, 6] },
                { name: '3500rpm', data: [3, 4, 5, 6, 7] },
                { name: '4000rpm', data: [4, 5, 6, 7, 8] },
                { name: '4500rpm', data: [5, 6, 7, 8, 9] }
            ];
        }

        if (Array.isArray(data)) {
            const result = data.map((item, index) => {
                if (typeof item === 'object' && item !== null && 'name' in item) {
                    const dataArray = Array.isArray(item.data) ? item.data : [0, 0, 0, 0, 0];
                    // 确保数据数组包含有效的数值
                    const validData = dataArray.filter(value => typeof value === 'number' && !isNaN(value));
                    if (validData.length === 0) {
                        console.warn(`数据系列 ${item.name} 没有有效数据`);
                        return null;
                    }
                    return {
                        name: item.name,
                        data: validData
                    };
                }
                const dataArray = Array.isArray(item) ? item : [0, 0, 0, 0, 0];
                // 确保数据数组包含有效的数值
                const validData = dataArray.filter(value => typeof value === 'number' && !isNaN(value));
                if (validData.length === 0) {
                    console.warn(`数据系列 ${index + 1} 没有有效数据`);
                    return null;
                }
                return {
                    name: `数据${index + 1}`,
                    data: validData
                };
            }).filter(Boolean);
            
            // 如果结果为空，返回默认数据
            if (result.length === 0) {
                console.warn('转换后的数组数据为空，使用默认数据');
                return [
                    { name: '2500rpm', data: [1, 2, 3, 4, 5] },
                    { name: '3000rpm', data: [2, 3, 4, 5, 6] },
                    { name: '3500rpm', data: [3, 4, 5, 6, 7] },
                    { name: '4000rpm', data: [4, 5, 6, 7, 8] },
                    { name: '4500rpm', data: [5, 6, 7, 8, 9] }
                ];
            }
            
            return result;
        }

        const result = Object.entries(data).map(([key, value]) => {
            const dataArray = Array.isArray(value) ? value : [0, 0, 0, 0, 0];
            // 确保数据数组包含有效的数值
            const validData = dataArray.filter(value => typeof value === 'number' && !isNaN(value));
            if (validData.length === 0) {
                console.warn(`数据系列 ${key} 没有有效数据`);
                return null;
            }
            return {
                name: key,
                data: validData
            };
        }).filter(Boolean);
        
        // 如果结果为空，返回默认数据
        if (result.length === 0) {
            console.warn('转换后的对象数据为空，使用默认数据');
            return [
                { name: '2500rpm', data: [1, 2, 3, 4, 5] },
                { name: '3000rpm', data: [2, 3, 4, 5, 6] },
                { name: '3500rpm', data: [3, 4, 5, 6, 7] },
                { name: '4000rpm', data: [4, 5, 6, 7, 8] },
                { name: '4500rpm', data: [5, 6, 7, 8, 9] }
            ];
        }
        
        return result;
    }
    // 图表数据创建方法
SimplePlotlyManager.prototype.createBoxPlotData = function(data, options) {
        const seriesData = this.convertToBoxPlotData(data);
        const colors = this.getColorSchemeColors();
        
        // 确保数据有效，如果没有数据，使用默认数据
        if (seriesData.length === 0) {
            console.warn('箱线图数据为空，使用默认数据');
            // 创建默认数据
            const defaultData = [
                { name: '2500rpm', data: [1, 2, 3, 4, 5] },
                { name: '3000rpm', data: [2, 3, 4, 5, 6] },
                { name: '3500rpm', data: [3, 4, 5, 6, 7] },
                { name: '4000rpm', data: [4, 5, 6, 7, 8] },
                { name: '4500rpm', data: [5, 6, 7, 8, 9] }
            ];
            seriesData.push(...defaultData);
        }
        
        const boxPlots = seriesData.map((item, index) => {
            // 确保数据数组有效
            const validData = item.data.filter(value => typeof value === 'number' && !isNaN(value));
            if (validData.length === 0) {
                console.warn(`数据系列 ${item.name} 没有有效数据，使用默认数据`);
                // 使用默认数据
                validData.push(1, 2, 3, 4, 5);
            }
            
            
            return {
                type: 'box',
                name: item.name,
                y: validData,
                marker: {
                    color: this.getSpeedColor(item.name)
                },
                line: {
                    color: this.getSpeedColor(item.name)
                },
                hoverinfo: 'name+y+text',
                text: validData.map((value, i) => `数据点 ${i+1}: ${value.toFixed(2)}`),
                // 确保箱线图的基本属性
                boxpoints: 'all',
                jitter: 0.3,
                pointpos: -1.8,
                // 添加更多箱线图配置
                fillcolor: `${this.getSpeedColor(item.name)}33`,
                opacity: 0.7
            };
        });
        
        
        // 添加中位线连线
        if (boxPlots.length > 1) {
            const medians = boxPlots.map(item => {
                // 计算中位数
                const sortedData = [...item.y].sort((a, b) => a - b);
                const mid = Math.floor(sortedData.length / 2);
                const median = sortedData.length % 2 !== 0 ? sortedData[mid] : (sortedData[mid - 1] + sortedData[mid]) / 2;
                return median;
            });
            
            const medianLine = {
                type: 'scatter',
                x: boxPlots.map(item => item.name),
                y: medians,
                mode: 'lines+markers',
                name: '中位线',
                line: {
                    color: colors.secondary,
                    width: 2,
                    dash: 'dash'
                },
                marker: {
                    color: colors.secondary,
                    size: 6,
                    symbol: 'circle'
                },
                hoverinfo: 'name+x+y'
            };
            
            boxPlots.push(medianLine);
        }
        
        return boxPlots;
    }
    
SimplePlotlyManager.prototype.createScatterPlotData = function(data, options) {
        const seriesData = this.convertToScatterData(data);
        
        const x = seriesData.map(item => item[0]);
        const y = seriesData.map(item => item[1]);
        
        // 为每个数据点使用不同的颜色
        const markers = {
            color: seriesData.map(item => this.getSpeedColor(item[0])),
            size: 6,
            opacity: 0.6
        };
        
        // 为每个数据点添加自定义悬停信息
        const text = seriesData.map((item, i) => `转速: ${item[0]}<br>不平衡量: ${item[1].toFixed(2)}`);
        
        const scatterData = [{
            type: 'scatter',
            x: x,
            y: y,
            mode: 'markers',
            marker: markers,
            hoverinfo: 'text',
            text: text
        }];
        
        return scatterData;
    }
    
SimplePlotlyManager.prototype.createTrendPlotData = function(data, options) {
        const seriesData = this.convertToTrendData(data);
        
        const x = seriesData.map(item => item.name);
        const y = seriesData.map(item => item.value);
        const colors = this.getColorSchemeColors();
        
        // 为每个数据点使用不同的颜色
        const markers = {
            color: seriesData.map(item => this.getSpeedColor(item.name)),
            size: 6
        };
        
        // 为每个数据点添加自定义悬停信息
        const text = seriesData.map(item => `转速: ${item.name}<br>中位数: ${item.value.toFixed(2)}`);
        
        const trendData = [{
            type: 'scatter',
            x: x,
            y: y,
            mode: 'lines+markers',
            line: {
                color: colors.primary,
                width: 2,
                shape: 'spline'
            },
            marker: markers,
            fill: 'tozeroy',
            fillcolor: `${colors.primary}33`,
            hoverinfo: 'text',
            text: text
        }];
        
        return trendData;
    }
    
SimplePlotlyManager.prototype.createViolinPlotData = function(data, options) {
        const seriesData = this.convertToViolinData(data);
        
        const violinData = seriesData.map(item => ({
            type: 'violin',
            name: item.name,
            y: item.data,
            marker: {
                color: this.getSpeedColor(item.name)
            },
            line: {
                color: this.getSpeedColor(item.name)
            },
            hoverinfo: 'name+y+text',
            text: item.data.map((value, i) => `数据点 ${i+1}: ${value.toFixed(2)}`),
            box: {
                visible: true
            },
            points: 'all',
            jitter: 0.3,
            pointpos: -1.8
        }));
        
        return violinData;
    }
    
SimplePlotlyManager.prototype.createHeatmapData = function(data, options) {
        const seriesData = this.convertToHeatmapData(data);
        const z = [];
        const x = [];
        const y = [];
        const text = [];
        
        // 整理数据为Plotly热力图格式
        const xValues = [...new Set(seriesData.map(item => item[0]))];
        const yValues = [...new Set(seriesData.map(item => item[1]))];
        
        xValues.forEach((xVal, i) => {
            const row = [];
            const textRow = [];
            yValues.forEach((yVal, j) => {
                const point = seriesData.find(p => p[0] === xVal && p[1] === yVal);
                const value = point ? point[2] : 0;
                row.push(value);
                textRow.push(`转速: ${xVal}<br>索引: ${yVal}<br>值: ${value.toFixed(2)}`);
            });
            z.push(row);
            text.push(textRow);
        });
        
        return [{
            type: 'heatmap',
            x: yValues,
            y: xValues,
            z: z,
            colorscale: 'Viridis',
            hoverinfo: 'text',
            text: text
        }];
    }
    
SimplePlotlyManager.prototype.createHistogramData = function(data, options) {
        const seriesData = this.convertToHistogramData(data);
        const x = seriesData.map(item => item.name);
        const y = seriesData.map(item => item.value);
        
        // 为每个数据点使用不同的颜色
        const markers = {
            color: seriesData.map(item => this.getSpeedColor(item.name))
        };
        
        // 为每个数据点添加自定义悬停信息
        const text = seriesData.map(item => `区间: ${item.name}<br>频次: ${item.value}`);
        
        return [{
            type: 'bar',
            x: x,
            y: y,
            marker: markers,
            hoverinfo: 'text',
            text: text
        }];
    }
SimplePlotlyManager.prototype.createParallelData = function(data, options) {
        const seriesData = this.convertToParallelData(data);
        const colors = this.getColorSchemeColors();
        return [{
            type: 'parcoords',
            line: {
                color: colors.primary,
                width: 2,
                opacity: 0.6
            },
            dimensions: seriesData[0].map((_, i) => ({
                label: `维度${i + 1}`,
                values: seriesData.map(row => row[i])
            }))
        }];
    }
    
SimplePlotlyManager.prototype.createBubbleData = function(data, options) {
        const seriesData = this.convertToBubbleData(data);
        const x = seriesData.map(item => item.value[0]);
        const y = seriesData.map(item => item.value[1]);
        const size = seriesData.map(item => item.value[2]);
        
        // 为每个数据点使用不同的颜色
        const markers = {
            color: seriesData.map(item => this.getSpeedColor(item.value[0])),
            size: size,
            opacity: 0.6
        };
        
        // 为每个数据点添加自定义悬停信息
        const text = seriesData.map(item => `转速: ${item.value[0]}<br>中位数: ${item.value[1].toFixed(2)}<br>数据点数量: ${item.value[2]}`);
        
        return [{
            type: 'scatter',
            x: x,
            y: y,
            mode: 'markers',
            marker: markers,
            hoverinfo: 'text',
            text: text
        }];
    }
    
SimplePlotlyManager.prototype.createRegressionData = function(data, options) {
        const seriesData = this.convertToRegressionData(data);
        const x = seriesData.map(item => item[0]);
        const y = seriesData.map(item => item[1]);
        const colors = this.getColorSchemeColors();
        
        // 简单线性回归计算
        const n = seriesData.length;
        let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
        
        seriesData.forEach(([xVal, yVal]) => {
            sumX += parseFloat(xVal);
            sumY += yVal;
            sumXY += parseFloat(xVal) * yVal;
            sumX2 += parseFloat(xVal) * parseFloat(xVal);
        });
        
        const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
        const intercept = (sumY - slope * sumX) / n;
        
        // 生成回归直线数据
        const regressionX = x;
        const regressionY = regressionX.map(xVal => slope * parseFloat(xVal) + intercept);
        
        // 为每个数据点使用不同的颜色
        const markers = {
            color: seriesData.map(item => this.getSpeedColor(item[0])),
            size: 6,
            opacity: 0.6
        };
        
        // 为每个数据点添加自定义悬停信息
        const text = seriesData.map(item => `X: ${item[0]}<br>Y: ${item[1].toFixed(2)}`);
        
        return [
            {
                type: 'scatter',
                x: x,
                y: y,
                mode: 'markers',
                name: '原始数据',
                marker: markers,
                hoverinfo: 'text',
                text: text
            },
            {
                type: 'scatter',
                x: regressionX,
                y: regressionY,
                mode: 'lines',
                name: '回归直线',
                line: {
                    color: colors.secondary,
                    width: 2,
                    dash: 'dash'
                },
                hoverinfo: 'name+x+y',
                text: regressionX.map((xVal, i) => `预测值: ${regressionY[i].toFixed(2)}`)
            }
        ];
    }
