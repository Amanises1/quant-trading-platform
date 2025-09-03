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
          </div>
          <div class="chart-placeholder">
            <div class="placeholder-text">这里将显示市场概览图表</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="recent-card">
          <div slot="header" class="clearfix">
            <span>最近交易信号</span>
          </div>
          <div class="signal-list">
            <div v-for="(signal, index) in recentSignals" :key="index" class="signal-item">
              <div class="signal-time">{{ signal.time }}</div>
              <div class="signal-content">
                <span class="signal-stock">{{ signal.stock }}</span>
                <span :class="['signal-type', signal.type === '买入' ? 'buy' : 'sell']">{{ signal.type }}</span>
              </div>
              <div class="signal-confidence">置信度: {{ signal.confidence }}</div>
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
      recentSignals: [
        { time: '2023-07-20 14:30', stock: '600000 浦发银行', type: '买入', confidence: '85%' },
        { time: '2023-07-20 13:45', stock: '000001 平安银行', type: '卖出', confidence: '78%' },
        { time: '2023-07-20 11:20', stock: '601318 中国平安', type: '买入', confidence: '92%' },
        { time: '2023-07-20 10:15', stock: '600519 贵州茅台', type: '买入', confidence: '95%' },
        { time: '2023-07-20 09:30', stock: '000858 五粮液', type: '卖出', confidence: '82%' }
      ]
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.welcome-card {
  background: linear-gradient(to right, #3494e6, #ec6ead);
  color: white;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.welcome-card h2 {
  margin: 0 0 10px 0;
  font-size: 24px;
}

.welcome-card p {
  margin: 0;
  font-size: 14px;
  opacity: 0.8;
}

.stat-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  height: 100px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: #409EFF;
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 30px;
  margin-right: 15px;
}

.stat-icon.warning {
  background-color: #E6A23C;
}

.stat-icon.success {
  background-color: #67C23A;
}

.stat-icon.info {
  background-color: #909399;
}

.stat-info {
  flex: 1;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.chart-card, .recent-card {
  margin-bottom: 20px;
}

.chart-placeholder {
  height: 300px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.placeholder-text {
  color: #909399;
  font-size: 14px;
}

.signal-list {
  max-height: 300px;
  overflow-y: auto;
}

.signal-item {
  padding: 10px 0;
  border-bottom: 1px solid #EBEEF5;
}

.signal-item:last-child {
  border-bottom: none;
}

.signal-time {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.signal-content {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.signal-stock {
  font-weight: bold;
  color: #303133;
}

.signal-type {
  padding: 2px 6px;
  border-radius: 2px;
  font-size: 12px;
}

.signal-type.buy {
  background-color: #f0f9eb;
  color: #67C23A;
}

.signal-type.sell {
  background-color: #fef0f0;
  color: #F56C6C;
}

.signal-confidence {
  font-size: 12px;
  color: #606266;
}
</style>