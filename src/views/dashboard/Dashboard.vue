<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="welcome-card">
          <h2>欢迎使用量化交易选股系统</h2>
          <p>基于机器学习技术实现智能决策，实现从数据采集到风险控制的全流程覆盖</p>
        </div>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon">
            <i class="el-icon-data-line"></i>
          </div>
          <div class="stat-info">
            <div class="stat-title">今日交易信号</div>
            <div class="stat-value">12</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon warning">
            <i class="el-icon-warning"></i>
          </div>
          <div class="stat-info">
            <div class="stat-title">风险预警</div>
            <div class="stat-value">3</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon success">
            <i class="el-icon-s-data"></i>
          </div>
          <div class="stat-info">
            <div class="stat-title">模型数量</div>
            <div class="stat-value">8</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon info">
            <i class="el-icon-user"></i>
          </div>
          <div class="stat-info">
            <div class="stat-title">在线用户</div>
            <div class="stat-value">5</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card class="chart-card">
          <div slot="header" class="clearfix">
            <span>市场概览</span>
            <el-select v-model="chartType" size="small" class="chart-type-select">
              <el-option label="上证指数" value="sse"></el-option>
              <el-option label="深证成指" value="szse"></el-option>
              <el-option label="创业板指" value="gem"></el-option>
            </el-select>
          </div>
          <div ref="chartContainer" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="recent-card">
          <div slot="header" class="clearfix">
            <span>最近交易信号</span>
            <el-button type="text" size="small" class="refresh-btn" @click="refreshSignals">
              <i class="el-icon-refresh"></i> 刷新
            </el-button>
          </div>
          <div class="signal-list">
            <div v-for="(signal, index) in recentSignals" :key="index" class="signal-item">
              <div class="signal-header">
                <div class="signal-time">{{ signal.time }}</div>
                <span :class="['signal-type', signal.type === '买入' ? 'buy' : 'sell']">{{ signal.type }}</span>
              </div>
              <div class="signal-stock">{{ signal.stock }}</div>
              <div class="signal-footer">
                <div class="signal-confidence">置信度: {{ signal.confidence }}</div>
                <div class="signal-arrow" :class="signal.type === '买入' ? 'up' : 'down'">
                  <i :class="signal.type === '买入' ? 'el-icon-caret-top' : 'el-icon-caret-bottom'"></i>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
export default {
  name: 'Dashboard',
  data() {
    return {
      chartType: 'sse',
      recentSignals: [
        { time: '2023-07-20 14:30', stock: '600000 浦发银行', type: '买入', confidence: '85%' },
        { time: '2023-07-20 13:45', stock: '000001 平安银行', type: '卖出', confidence: '78%' },
        { time: '2023-07-20 11:20', stock: '601318 中国平安', type: '买入', confidence: '92%' },
        { time: '2023-07-20 10:15', stock: '600519 贵州茅台', type: '买入', confidence: '95%' },
        { time: '2023-07-20 09:30', stock: '000858 五粮液', type: '卖出', confidence: '82%' }
      ]
    }
  },
  mounted() {
    this.initChart();
  },
  watch: {
    chartType() {
      this.initChart();
    }
  },
  methods: {
    initChart() {
      // 由于没有实际引入ECharts，这里使用模拟数据创建简单的可视化
      const chartContainer = this.$refs.chartContainer;
      if (!chartContainer) return;
      
      // 清空容器
      chartContainer.innerHTML = '';
      
      // 创建简单的模拟图表
      const canvas = document.createElement('canvas');
      canvas.width = chartContainer.offsetWidth;
      canvas.height = 300;
      chartContainer.appendChild(canvas);
      
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      
      // 获取模拟数据
      const chartData = this.getChartData();
      
      // 绘制图表
      this.drawChart(ctx, canvas.width, canvas.height, chartData);
    },
    
    getChartData() {
      // 根据选择的图表类型返回不同的模拟数据
      const baseData = [];
      const dates = [];
      const baseValue = this.chartType === 'sse' ? 3200 : this.chartType === 'szse' ? 2100 : 2500;
      
      // 生成最近30天的数据
      for (let i = 29; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        dates.push(`${date.getMonth() + 1}/${date.getDate()}`);
        
        // 生成随机波动
        const fluctuation = (Math.random() - 0.48) * 50;
        baseData.push(baseValue + fluctuation);
      }
      
      return { dates, values: baseData };
    },
    
    drawChart(ctx, width, height, data) {
      const { dates, values } = data;
      const padding = { top: 20, right: 20, bottom: 40, left: 40 };
      const chartWidth = width - padding.left - padding.right;
      const chartHeight = height - padding.top - padding.bottom;
      
      // 找出最大值和最小值
      const maxValue = Math.max(...values);
      const minValue = Math.min(...values);
      const valueRange = maxValue - minValue;
      
      // 绘制背景
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, width, height);
      
      // 绘制网格线
      ctx.strokeStyle = '#f0f0f0';
      ctx.lineWidth = 1;
      
      // 水平网格线
      for (let i = 0; i <= 5; i++) {
        const y = padding.top + (chartHeight * i) / 5;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();
      }
      
      // 垂直网格线
      for (let i = 0; i <= 5; i++) {
        const x = padding.left + (chartWidth * i) / 5;
        ctx.beginPath();
        ctx.moveTo(x, padding.top);
        ctx.lineTo(x, height - padding.bottom);
        ctx.stroke();
      }
      
      // 绘制数据线
      ctx.strokeStyle = '#3494e6';
      ctx.lineWidth = 2;
      ctx.beginPath();
      
      for (let i = 0; i < values.length; i++) {
        const x = padding.left + (chartWidth * i) / (values.length - 1);
        const y = padding.top + chartHeight - ((values[i] - minValue) / valueRange) * chartHeight;
        
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      
      ctx.stroke();
      
      // 绘制数据点
      ctx.fillStyle = '#3494e6';
      for (let i = 0; i < values.length; i += 5) {
        const x = padding.left + (chartWidth * i) / (values.length - 1);
        const y = padding.top + chartHeight - ((values[i] - minValue) / valueRange) * chartHeight;
        
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fill();
      }
      
      // 绘制坐标轴标签
      ctx.fillStyle = '#909399';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      
      // X轴标签
      for (let i = 0; i <= 5; i++) {
        const x = padding.left + (chartWidth * i) / 5;
        const dateIndex = Math.floor((values.length - 1) * i / 5);
        ctx.fillText(dates[dateIndex], x, height - padding.bottom + 20);
      }
      
      // Y轴标签
      ctx.textAlign = 'right';
      for (let i = 0; i <= 5; i++) {
        const y = padding.top + (chartHeight * i) / 5;
        const value = maxValue - (valueRange * i) / 5;
        ctx.fillText(value.toFixed(0), padding.left - 10, y + 5);
      }
      
      // 绘制标题
      ctx.fillStyle = '#303133';
      ctx.font = 'bold 14px sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(
        this.chartType === 'sse' ? '上证指数走势' : this.chartType === 'szse' ? '深证成指走势' : '创业板指走势',
        padding.left, 
        padding.top - 5
      );
    },
    
    refreshSignals() {
      // 模拟刷新交易信号
      this.$message({ message: '交易信号已刷新', type: 'success' });
      // 实际应用中这里应该调用API获取最新数据
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  background-color: var(--background-color);
}

.welcome-card {
  background: linear-gradient(135deg, var(--primary-color), #ec6ead);
  color: white;
  padding: 30px 20px;
  border-radius: 8px;
  margin-bottom: 24px;
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
}

.welcome-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px 0 rgba(0, 0, 0, 0.15);
}

.welcome-card h2 {
  margin: 0 0 10px 0;
  font-size: 28px;
  font-weight: 600;
}

.welcome-card p {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
  line-height: 1.5;
}

.stat-row {
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  height: 120px;
  border-radius: 8px;
  transition: all 0.3s ease;
  overflow: hidden;
  position: relative;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px 0 rgba(0, 0, 0, 0.15);
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background-color: var(--primary-color);
  }

  .stat-card:nth-child(2)::before {
    background-color: var(--warning-color);
  }

  .stat-card:nth-child(3)::before {
    background-color: var(--success-color);
  }

  .stat-card:nth-child(4)::before {
    background-color: var(--info-color);
  }

.stat-icon {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background-color: var(--primary-color);
    color: white;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 32px;
    margin: 0 20px;
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  }

  .stat-icon.warning {
    background-color: var(--warning-color);
    box-shadow: 0 4px 12px rgba(230, 162, 60, 0.3);
  }

  .stat-icon.success {
    background-color: var(--success-color);
    box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
  }

  .stat-icon.info {
    background-color: var(--info-color);
    box-shadow: 0 4px 12px rgba(144, 147, 153, 0.3);
  }

.stat-info {
  flex: 1;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 30px;
  font-weight: bold;
  color: #303133;
  transition: all 0.3s ease;
}

.stat-card:hover .stat-value {
  transform: scale(1.05);
}

.chart-card, .recent-card {
  margin-bottom: 24px;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.chart-card:hover, .recent-card:hover {
  box-shadow: 0 8px 24px 0 rgba(0, 0, 0, 0.12);
}

.chart-container {
  height: 350px;
  width: 100%;
  background-color: #ffffff;
}

.chart-type-select {
  float: right;
  width: auto;
}

.signal-list {
  max-height: 350px;
  overflow-y: auto;
  padding-right: 4px;
}

/* 自定义滚动条样式 */
.signal-list::-webkit-scrollbar {
  width: 6px;
}

.signal-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.signal-list::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

.signal-list::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

.signal-item {
  padding: 12px 16px;
  border-bottom: 1px solid #EBEEF5;
  transition: all 0.2s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.signal-item:hover {
  background-color: #f5f7fa;
  padding-left: 20px;
}

.signal-item:last-child {
  border-bottom: none;
}

.signal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.signal-time {
  font-size: 12px;
  color: #909399;
}

.signal-content {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.signal-stock {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
  margin-bottom: 6px;
}

.signal-type {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.signal-type.buy {
    background-color: #f0f9eb;
    color: var(--success-color);
    border: 1px solid #e1f3d8;
  }

  .signal-type.sell {
    background-color: #fef0f0;
    color: var(--danger-color);
    border: 1px solid #fbc4c4;
  }

.signal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.signal-confidence {
  font-size: 12px;
  color: #606266;
}

.signal-arrow {
  font-size: 16px;
  transition: all 0.2s ease;
}

.signal-arrow.up {
    color: var(--success-color);
  }

  .signal-arrow.down {
    color: var(--danger-color);
  }

.signal-item:hover .signal-arrow {
  transform: scale(1.2);
}

.refresh-btn {
    float: right;
    color: var(--primary-color);
    transition: all 0.2s ease;
  }

  .refresh-btn:hover {
    color: #66b1ff;
    transform: rotate(180deg);
  }

/* 响应式调整 */
@media screen and (max-width: 768px) {
  .welcome-card {
    padding: 20px 16px;
  }
  
  .welcome-card h2 {
    font-size: 24px;
  }
  
  .stat-card {
    height: 100px;
  }
  
  .stat-icon {
    width: 50px;
    height: 50px;
    font-size: 24px;
    margin: 0 12px;
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .chart-container {
    height: 300px;
  }
}
</style>