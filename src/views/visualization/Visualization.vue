<template>
  <div class="visualization-container">
    <!-- 头部导航 -->
    <div class="header-section">
      <h1>股票量化交易平台 - 实时数据可视化</h1>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="实时数据展示" name="realtime" />
      </el-tabs>
    </div>

    <!-- 实时数据展示区域 -->
    <div class="realtime-content">
      <div class="toolbar">
        <el-select v-model="selectedStock" placeholder="选择股票" class="stock-select">
          <el-option v-for="option in stockOptions" :key="option.value" :label="option.label" :value="option.value"></el-option>
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          class="date-picker"
        ></el-date-picker>
        <el-select v-model="selectedChartType" placeholder="选择图表类型" class="chart-type-select">
          <el-option v-for="option in chartTypeOptions" :key="option.value" :label="option.label" :value="option.value"></el-option>
        </el-select>
        <el-button type="primary" @click="generateChart">生成图表</el-button>
        <el-button @click="downloadChart">下载图表</el-button>
      </div>
      
      <div class="chart-content">
        <!-- 图表容器 -->
        <div class="chart-container">
          <div v-if="!chartHtml && !chartUrl" class="chart-loading">
            <el-empty description="暂无图表数据，请点击生成图表"></el-empty>
          </div>
          <div v-else-if="chartHtml" v-html="chartHtml" class="chart-iframe"></div>
          <img v-else :src="chartUrl" class="chart-image" />
        </div>
        
        <!-- 图表参数配置面板 -->
        <div class="chart-config-panel">
          <h3>图表配置</h3>
          <el-form :model="chartConfig" label-width="120px">
            <el-form-item label="图表标题">
              <el-input v-model="chartConfig.title"></el-input>
            </el-form-item>
            <el-form-item label="是否显示网格线">
              <el-switch v-model="chartConfig.showGrid"></el-switch>
            </el-form-item>
            <el-form-item label="是否显示水印">
              <el-switch v-model="chartConfig.showWatermark"></el-switch>
            </el-form-item>
            <el-form-item label="主题选择" v-if="selectedChartType !== 'candlestick_chart'">
              <el-radio-group v-model="chartConfig.theme">
                <el-radio label="light">浅色主题</el-radio>
                <el-radio label="dark">深色主题</el-radio>
                <el-radio label="seaborn">Seaborn主题</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <!-- K线图特有配置 -->
            <el-divider v-if="selectedChartType === 'candlestick_chart'"></el-divider>
            <el-form-item label="显示成交量" v-if="selectedChartType === 'candlestick_chart'">
              <el-switch v-model="chartConfig.showVolume"></el-switch>
            </el-form-item>
            <el-form-item label="添加均线" v-if="selectedChartType === 'candlestick_chart'">
              <el-input-number v-model="chartConfig.maPeriod" :min="5" :max="250" :step="5"></el-input-number>
            </el-form-item>
            <el-form-item label="显示交易信号" v-if="selectedChartType === 'candlestick_chart'">
              <el-switch v-model="chartConfig.showSignals"></el-switch>
            </el-form-item>
            
            <!-- 投资组合特有配置 -->
            <el-divider v-if="selectedChartType === 'portfolio_performance'"></el-divider>
            <el-form-item label="显示基准对比" v-if="selectedChartType === 'portfolio_performance'">
              <el-switch v-model="chartConfig.showBenchmark"></el-switch>
            </el-form-item>
            <el-form-item label="显示回撤" v-if="selectedChartType === 'portfolio_performance'">
              <el-switch v-model="chartConfig.showDrawdown"></el-switch>
            </el-form-item>
          </el-form>
        </div>
      </div>
      
      <!-- 数据统计摘要 -->
      <div class="stats-summary" v-if="statsData">
        <h3>数据统计摘要</h3>
        <div class="stats-grid">
          <el-card v-for="stat in statsData" :key="stat.name" class="stat-card">
            <div slot="header" class="stat-card-header">
              <span>{{ stat.name }}</span>
            </div>
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-desc">{{ stat.description }}</div>
          </el-card>
        </div>
      </div>
    </div>


  </div>
</template>

<script>
import { axiosInstance } from '@/utils/axios-config';
import html2canvas from 'html2canvas';

export default {
  name: 'Visualization',
  data() {
      return {
        // 基础状态
        activeTab: 'realtime',
        selectedStock: '',
        selectedChartType: '',
        dateRange: [new Date('2023-01-01'), new Date('2023-12-31')],
        chartUrl: '',
        chartHtml: '',
        statsData: null,
        
        // 动态选项数据
        stockOptions: [],
        chartTypeOptions: [],
        
        // 图表配置
        chartConfig: {
          title: '股票数据分析',
          showGrid: true,
          showWatermark: true,
          theme: 'light',
          showVolume: true,
          maPeriod: 30,
          showBenchmark: true,
          showDrawdown: true,
          showSignals: true
        }
      };
    },
    
  mounted() {
    // 组件挂载后初始化
    this.initialize();
    
    // 初始化时获取股票列表和图表类型
    this.fetchStockOptions();
    this.fetchChartTypeOptions();
  },
  beforeDestroy() {
    // 清理资源
  },
  methods: {
      // 初始化函数
      initialize() {
        // 实时数据可视化模块初始化
      },
      
      // 获取股票列表
      async fetchStockOptions() {
        try {
          // 首先检查本地存储中是否已有股票列表数据
          const storedStocks = localStorage.getItem('visualization_stock_options');
          if (storedStocks) {
            console.log('从本地存储获取股票列表...');
            this.stockOptions = JSON.parse(storedStocks);
            // 默认选择第一个股票
            if (!this.selectedStock && this.stockOptions.length > 0) {
              this.selectedStock = this.stockOptions[0].value;
            }
            console.log('成功从本地存储加载股票列表，数量:', this.stockOptions.length);
            return;
          }
          
          // 如果本地存储中没有数据，则从API获取
          console.log('开始从API获取股票列表...');
          // 添加超时配置
          const config = { timeout: 60000 }; // 增加到60秒超时
          const response = await axiosInstance.get('/api/visualization/stocks', config);
          console.log('获取股票列表响应:', response);
          
          if (response && response.stocks && response.stocks.length > 0) {
            this.stockOptions = response.stocks;
            // 将数据保存到本地存储
            localStorage.setItem('visualization_stock_options', JSON.stringify(this.stockOptions));
            // 默认选择第一个股票
            if (!this.selectedStock && this.stockOptions.length > 0) {
              this.selectedStock = this.stockOptions[0].value;
            }
            console.log('成功加载股票列表并保存到本地，数量:', this.stockOptions.length);
          } else {
            console.warn('股票列表为空或响应格式不正确:', response);
            this.$message.warning('未获取到股票数据');
          }
        } catch (error) {
          console.error('获取股票列表失败:', error);
          this.$message.error('获取股票列表失败，请稍后再试');
        }
      },
      
      // 获取图表类型
      async fetchChartTypeOptions() {
        try {
            console.log('开始获取图表类型...');
            // 添加超时配置
            const config = { timeout: 60000 }; // 增加到60秒超时
            const response = await axiosInstance.get('/api/visualization/chart-types', config);
            console.log('获取图表类型响应:', response);
          if (response && response.chart_types && response.chart_types.length > 0) {
              this.chartTypeOptions = response.chart_types;
              // 默认选择第一个图表类型
              if (!this.selectedChartType && this.chartTypeOptions.length > 0) {
                this.selectedChartType = this.chartTypeOptions[0].value;
              }
              console.log('成功加载图表类型，数量:', this.chartTypeOptions.length);
            } else {
              console.warn('图表类型为空或响应格式不正确:', response);
              this.$message.warning('未获取到图表类型数据');
            }
        } catch (error) {
          console.error('获取图表类型失败:', error);
          this.$message.error('获取图表类型失败，请稍后再试');
        }
      },
      
      // 生成图表
      async generateChart() {
      try {
        // 显示加载中状态
        this.$message({message: '正在生成图表，请稍候...', type: 'info', duration: 0});
        
        // 准备请求参数
        const params = {
          chart_type: this.selectedChartType,
          start_date: this.formatDate(this.dateRange[0]),
          end_date: this.formatDate(this.dateRange[1]),
          stock_symbol: this.selectedStock,
          config: this.chartConfig
        };
        
        // 调用后端API生成图表
        const response = await axiosInstance.post('/api/visualization/generate', params);
        
        // 处理响应数据
        if (response && response.success) {
          // 根据图表类型处理返回数据
          if (['candlestick_chart', 'portfolio_performance'].includes(this.selectedChartType)) {
            this.chartHtml = response.chart_html;
            this.chartUrl = '';
          } else {
            this.chartUrl = response.chart_url;
            this.chartHtml = '';
          }
          
          // 更新统计数据
          this.statsData = response.stats || null;
          
          this.$message.success('图表生成成功');
        } else {
            this.$message.error(`图表生成失败: ${response && response.message ? response.message : '未知错误'}`);
          }
      } catch (error) {
        console.error('生成图表时出错:', error);
        this.$message.error('生成图表时出错，请稍后重试');
      } finally {
        // 关闭加载中状态
        this.$message.closeAll();
      }
    },
    
    // 下载图表
    async downloadChart() {
      try {
        // 显示加载中状态
        this.$message({message: '正在准备下载图表，请稍候...', type: 'info', duration: 0});
        
        // 首先检查是否有前端已生成的图表数据
        if (this.chartHtml) {
          // 处理HTML类型的图表
          console.log('使用本地HTML图表数据进行下载...');
          
          // 创建一个临时iframe来加载HTML内容
          const iframe = document.createElement('iframe');
          iframe.style.display = 'none';
          document.body.appendChild(iframe);
          
          // 将HTML内容加载到iframe
          iframe.contentDocument.write(this.chartHtml);
          iframe.contentDocument.close();
          
          // 等待iframe内容加载完成后再下载
          setTimeout(() => {
            try {
              // 将HTML转换为图片并下载
              html2canvas(iframe.contentDocument.body).then(canvas => {
                // 转换为图片URL
                const imgUrl = canvas.toDataURL('image/png');
                
                // 创建下载链接
                const link = document.createElement('a');
                link.href = imgUrl;
                link.download = `chart_${this.selectedChartType}_${new Date().toISOString().slice(0,10)}.png`;
                
                // 触发下载
                document.body.appendChild(link);
                link.click();
                
                // 清理
                document.body.removeChild(link);
                document.body.removeChild(iframe);
                
                this.$message.success('图表下载成功');
              }).catch(err => {
                console.error('HTML转图片失败:', err);
                this.$message.error('图表下载失败，请稍后重试');
                document.body.removeChild(iframe);
              });
            } catch (error) {
              console.error('下载HTML图表时出错:', error);
              this.$message.error('图表下载失败，请稍后重试');
              document.body.removeChild(iframe);
            } finally {
              // 关闭加载中状态
              this.$message.closeAll();
            }
          }, 1000);
          
          return;
        } else if (this.chartUrl) {
          // 处理图片类型的图表
          console.log('使用本地图片URL进行下载...');
          
          // 创建下载链接
          const link = document.createElement('a');
          link.href = this.chartUrl;
          link.download = `chart_${this.selectedChartType}_${new Date().toISOString().slice(0,10)}.png`;
          
          // 触发下载
          document.body.appendChild(link);
          link.click();
          
          // 清理
          document.body.removeChild(link);
          
          this.$message.success('图表下载成功');
        } else {
          // 没有本地图表数据，提示用户先生成图表
          this.$message.warning('请先生成图表再进行下载');
        }
        
      } catch (error) {
        console.error('下载图表时出错:', error);
        this.$message.error('图表下载时出错，请稍后重试');
      } finally {
        // 关闭加载中状态
        if (!this.chartHtml) { // HTML图表的清理在setTimeout回调中处理
          this.$message.closeAll();
        }
      }
    },
    

    
    // 格式化日期
    formatDate(date) {
      if (!date) return '';
      const d = new Date(date);
      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    }
  }
};
</script>

<style scoped>
.visualization-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

/* 头部样式 */
.header-section h1 {
  font-size: 24px;
  font-weight: bold;
  color: #1f2937;
  margin-bottom: 20px;
}

/* 实时数据展示样式 */
.realtime-content .toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stock-select, .chart-type-select {
  width: 200px;
}

.date-picker {
  width: 280px;
}

.chart-content {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.chart-container {
  flex: 1;
  min-height: 500px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-loading {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-iframe {
  width: 100%;
  height: 100%;
}

.chart-image {
  max-width: 100%;
  max-height: 100%;
}

.chart-config-panel {
  width: 350px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  padding: 20px;
}

.stats-summary {
  margin-top: 30px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  padding: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.stat-card {
  height: 100%;
}

.stat-card-header {
  padding: 0 10px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #1890ff;
  margin: 10px 0;
}

.stat-desc {
  color: #606266;
  font-size: 12px;
}

/* 风控数据展示样式 */
.risk-content {
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  padding: 20px;
}

.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.risk-header h2 {
  font-size: 20px;
  font-weight: bold;
  color: #1f2937;
}

.risk-overview {
  margin-bottom: 30px;
}

.risk-card {
  border-left: 4px solid #1890ff;
}

.risk-card.risk-high {
  border-left-color: #f56c6c;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.risk-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.risk-item {
  text-align: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.risk-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
}

.risk-value {
  font-size: 24px;
  font-weight: bold;
  color: #1890ff;
  margin-bottom: 5px;
}

.risk-value.profit {
  color: #67c23a;
}

.risk-value.loss {
  color: #f56c6c;
}

.risk-desc {
  font-size: 12px;
  color: #909399;
}

.risk-charts {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.risk-chart-item {
  flex: 1;
}

.risk-chart-item h3 {
  font-size: 16px;
  font-weight: bold;
  color: #1f2937;
  margin-bottom: 15px;
}

.risk-chart-container {
  height: 300px;
  background: #f5f7fa;
  border-radius: 4px;
  padding: 15px;
}

.risk-thresholds {
  width: 350px;
  background: #f5f7fa;
  border-radius: 4px;
  padding: 20px;
}

.risk-thresholds h3 {
  font-size: 16px;
  font-weight: bold;
  color: #1f2937;
  margin-bottom: 15px;
}

/* 通知展示样式 */
.notifications-content {
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  padding: 20px;
}

.notifications-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.notifications-header h2 {
  font-size: 20px;
  font-weight: bold;
  color: #1f2937;
}

.notifications-filters {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.notifications-filters .el-select {
  width: 150px;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 30px;
}

.notification-card {
  border-left: 4px solid #1890ff;
  cursor: pointer;
  transition: all 0.3s;
}

.notification-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.notification-card.unread {
  border-left-color: #67c23a;
  background-color: #f0f9ff;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notification-content {
  padding: 10px 0;
}

.notification-content p {
  margin: 0 0 10px 0;
  color: #606266;
}

.notification-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notification-time {
  font-size: 12px;
  color: #909399;
}

.notification-unread-dot {
  font-size: 12px;
  color: #67c23a;
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 50%, 100% {
    opacity: 1;
  }
  25%, 75% {
    opacity: 0.3;
  }
}

.no-notifications {
  text-align: center;
  padding: 50px;
  color: #909399;
}

/* 通知设置样式 */
.notification-settings {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 20px;
}

.notification-settings h3 {
  font-size: 16px;
  font-weight: bold;
  color: #1f2937;
  margin-bottom: 15px;
}

/* 通知类型设置卡片 */
.notification-type-card {
  background: white;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.notification-type-card h4 {
  font-size: 14px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 15px;
}

/* 通知类型设置项 */
.notification-type-settings {
  padding: 10px 0;
}

.notification-type-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.notification-type-item:last-child {
  border-bottom: none;
}

.notification-type-label {
  font-size: 14px;
  color: #606266;
}

/* 通知渠道设置卡片 */
.notification-channel-card {
  background: white;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.notification-channel-card h4 {
  font-size: 14px;
  font-weight: bold;
  color: #67c23a;
  margin-bottom: 15px;
}

/* 渠道设置样式 */
.channel-settings {
  margin-bottom: 25px;
}

.channel-settings h4 {
  font-size: 14px;
  font-weight: bold;
  color: #67c23a;
  margin-bottom: 15px;
}

/* 渠道开关项 */
.channel-toggle-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.channel-toggle-label {
  font-size: 14px;
  color: #606266;
}

/* 渠道配置项 */
.channel-config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.channel-config-item:last-child {
  border-bottom: none;
}

.channel-config-label {
  font-size: 14px;
  color: #606266;
  width: 120px;
}

/* 收件人管理 */
.recipients-container {
  padding: 10px 0;
}

.recipient-input-group {
  margin-bottom: 10px;
}

/* 收件人部分特殊样式 */
.recipients-section {
  flex-direction: column;
  align-items: flex-start;
}

.recipients-section .recipients-container {
  width: 100%;
}

.recipients-list {
  display: flex;
  flex-wrap: wrap;
  margin-top: 10px;
}

.recipients-list .el-tag {
  margin: 5px 5px 5px 0;
  background-color: #f4f4f5;
  color: #606266;
}

.recipients-list .el-tag .el-tag__close {
  color: #909399;
}

.recipients-list .el-tag .el-tag__close:hover {
  color: #606266;
}

/* 收件人列表样式 */
.recipients-list {
  max-height: 150px;
  overflow-y: auto;
  margin-bottom: 15px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
}

.recipient-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 5px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.recipient-item .recipient-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recipient-item .remove-btn {
  color: #f56c6c;
  cursor: pointer;
}

/* 测试通知区域 */
.test-notification-section {
  margin-top: 30px;
  padding: 20px;
  background-color: #fafafa;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.test-notification-section h4 {
  font-size: 14px;
  font-weight: bold;
  color: #606266;
  margin-bottom: 15px;
}

/* 测试按钮区域 */
.test-buttons {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

/* 保存按钮区域 */
.save-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .risk-charts {
    flex-direction: column;
  }
  
  .risk-thresholds {
    width: 100%;
  }
}

@media (max-width: 1024px) {
  .chart-content {
    flex-direction: column;
  }
  
  .chart-config-panel {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .visualization-container {
    padding: 10px;
  }
  
  .realtime-content .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .stock-select, .chart-type-select, .date-picker {
    width: 100%;
  }
  
  .risk-grid {
    grid-template-columns: 1fr;
  }
  
  .notifications-filters {
    flex-direction: column;
  }
  
  .notifications-filters .el-select {
    width: 100%;
  }
}
</style>