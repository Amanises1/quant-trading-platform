<template>
  <div class="visualization-container">
    <!-- 头部导航 -->
    <div class="header-section">
      <h1>股票量化交易平台 - 可视化中心</h1>
      <el-tabs v-model="activeTab" @tab-click="handleTabClick">
        <el-tab-pane label="实时数据展示" name="realtime" />
        <el-tab-pane label="风控数据展示" name="risk" />
        <el-tab-pane label="通知中心" name="notifications" />
      </el-tabs>
    </div>

    <!-- 实时数据展示区域 -->
    <div v-if="activeTab === 'realtime'" class="realtime-content">
      <div class="toolbar">
        <el-select v-model="selectedStock" placeholder="选择股票" class="stock-select">
          <el-option label="上证指数 (000001)" value="000001"></el-option>
          <el-option label="深证成指 (399001)" value="399001"></el-option>
          <el-option label="创业板指 (399006)" value="399006"></el-option>
          <el-option label="贵州茅台 (600519)" value="600519"></el-option>
          <el-option label="中国平安 (601318)" value="601318"></el-option>
          <el-option label="宁德时代 (300750)" value="300750"></el-option>
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
          <el-option label="价格走势图" value="price_chart"></el-option>
          <el-option label="K线图(基础图表)" value="candlestick_chart"></el-option>
          <el-option label="特征相关性矩阵" value="correlation_matrix"></el-option>
          <el-option label="因子收益率贡献度" value="factor_contribution"></el-option>
          <el-option label="资金流向桑基图" value="sankey_diagram"></el-option>
          <el-option label="市场情绪变化热力图" value="sentiment_heatmap"></el-option>
          <el-option label="投资组合表现" value="portfolio_performance"></el-option>
          <el-option label="收益分布" value="returns_distribution"></el-option>
          <el-option label="月度收益热图" value="monthly_returns_heatmap"></el-option>
          <el-option label="交易分析" value="trade_analysis"></el-option>
        </el-select>
        <el-button type="primary" @click="generateChart">生成图表</el-button>
        <el-button @click="downloadChart">下载图表</el-button>
        <el-button @click="toggleRealtimeUpdate" :type="isRealtimeUpdating ? 'warning' : 'success'">
          {{ isRealtimeUpdating ? '停止实时更新' : '开启实时更新' }}
        </el-button>
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

    <!-- 风控数据展示区域 -->
    <div v-if="activeTab === 'risk'" class="risk-content">
      <div class="risk-header">
        <h2>风控数据监控</h2>
        <el-button type="primary" @click="refreshRiskData">刷新数据</el-button>
      </div>
      
      <div class="risk-overview">
        <el-card class="risk-card" :class="{ 'risk-high': accountRisk.status === '高风险' }">
          <template slot="header">
            <div class="card-header">
              <span>账户风险状态</span>
              <el-tag :type="getRiskTagType(accountRisk.status)">{{ accountRisk.status }}</el-tag>
            </div>
          </template>
          <div class="risk-grid">
            <div class="risk-item">
              <div class="risk-label">保证金比例</div>
              <div class="risk-value">{{ accountRisk.marginRatio }}%</div>
              <div class="risk-desc">当前: {{ accountRisk.marginRatio }}% / 预警线: {{ riskThresholds.marginWarning }}% / 平仓线: {{ riskThresholds.marginLiquidation }}%</div>
            </div>
            <div class="risk-item">
              <div class="risk-label">最大回撤</div>
              <div class="risk-value">{{ accountRisk.maxDrawdown }}%</div>
              <div class="risk-desc">历史最大亏损百分比</div>
            </div>
            <div class="risk-item">
              <div class="risk-label">Sharpe比率</div>
              <div class="risk-value">{{ accountRisk.sharpeRatio }}</div>
              <div class="risk-desc">风险调整后收益指标</div>
            </div>
            <div class="risk-item">
              <div class="risk-label">波动率</div>
              <div class="risk-value">{{ accountRisk.volatility }}%</div>
              <div class="risk-desc">收益率波动性</div>
            </div>
            <div class="risk-item">
              <div class="risk-label">总仓位</div>
              <div class="risk-value">{{ accountRisk.positionRatio }}%</div>
              <div class="risk-desc">当前: {{ accountRisk.positionRatio }}% / 上限: {{ riskThresholds.positionLimit }}%</div>
            </div>
            <div class="risk-item">
              <div class="risk-label">单日盈亏</div>
              <div class="risk-value" :class="accountRisk.dailyProfit > 0 ? 'profit' : 'loss'">
                {{ accountRisk.dailyProfit > 0 ? '+' : '' }}{{ accountRisk.dailyProfit }}%
              </div>
              <div class="risk-desc">今日收益率</div>
            </div>
          </div>
        </el-card>
      </div>

      <div class="risk-charts">
        <div class="risk-chart-item">
          <h3>风险指标走势图</h3>
          <div class="risk-chart-container" v-html="riskChartHtml"></div>
        </div>
        <div class="risk-thresholds">
          <h3>风险阈值设置</h3>
          <el-form :model="riskThresholds" label-width="150px">
            <el-form-item label="保证金预警线">
              <el-input-number v-model="riskThresholds.marginWarning" :min="10" :max="100" :step="1" />
              <span style="margin-left: 10px;">%</span>
            </el-form-item>
            <el-form-item label="保证金平仓线">
              <el-input-number v-model="riskThresholds.marginLiquidation" :min="5" :max="50" :step="1" />
              <span style="margin-left: 10px;">%</span>
            </el-form-item>
            <el-form-item label="总仓位上限">
              <el-input-number v-model="riskThresholds.positionLimit" :min="30" :max="100" :step="5" />
              <span style="margin-left: 10px;">%</span>
            </el-form-item>
            <el-form-item label="单日最大回撤限制">
              <el-input-number v-model="riskThresholds.maxDrawdownDaily" :min="1" :max="20" :step="1" />
              <span style="margin-left: 10px;">%</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveRiskThresholds">保存设置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>

    <!-- 通知展示区域 -->
    <div v-if="activeTab === 'notifications'" class="notifications-content">
      <div class="notifications-header">
        <h2>通知中心</h2>
        <el-button @click="clearAllNotifications">清空所有通知</el-button>
      </div>
      
      <div class="notifications-filters">
        <el-select v-model="notificationFilter" placeholder="过滤通知类型">
          <el-option label="全部通知" value="all"></el-option>
          <el-option label="交易完成" value="trade"></el-option>
          <el-option label="风控警报" value="risk"></el-option>
          <el-option label="账户余额" value="balance"></el-option>
          <el-option label="系统消息" value="system"></el-option>
        </el-select>
        <el-select v-model="notificationStatusFilter" placeholder="过滤通知状态">
          <el-option label="全部状态" value="all"></el-option>
          <el-option label="未读" value="unread"></el-option>
          <el-option label="已读" value="read"></el-option>
        </el-select>
      </div>
      
      <div class="notifications-list">
        <el-card 
          v-for="notification in filteredNotifications" 
          :key="notification.id"
          class="notification-card" 
          :class="{ 'unread': !notification.read }"
          @click="markAsRead(notification.id)"
        >
          <template slot="header">
            <div class="notification-header">
              <span>{{ notification.title }}</span>
              <el-tag :type="getNotificationTagType(notification.type)">{{ getNotificationTypeText(notification.type) }}</el-tag>
            </div>
          </template>
          <div class="notification-content">
            <p>{{ notification.message }}</p>
            <div class="notification-meta">
              <span class="notification-time">{{ formatNotificationTime(notification.timestamp) }}</span>
              <span v-if="!notification.read" class="notification-unread-dot">●</span>
            </div>
          </div>
        </el-card>
        
        <div v-if="filteredNotifications.length === 0" class="no-notifications">
          <el-empty description="暂无通知"></el-empty>
        </div>
      </div>
      
      <div class="notification-settings">
        <h3>通知设置</h3>
        <el-form :model="notificationSettings">
          <el-form-item label="交易完成通知">
            <el-switch v-model="notificationSettings.trade" />
          </el-form-item>
          <el-form-item label="风控警报通知">
            <el-switch v-model="notificationSettings.risk" />
          </el-form-item>
          <el-form-item label="账户余额警告">
            <el-switch v-model="notificationSettings.balance" />
          </el-form-item>
          <el-form-item label="系统消息通知">
            <el-switch v-model="notificationSettings.system" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveNotificationSettings">保存设置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 消息通知弹窗 -->
    <el-notification
      :title="notificationPopup.title"
      :message="notificationPopup.message"
      :type="notificationPopup.type"
      :show-close="true"
      :duration="5000"
      v-if="showNotificationPopup"
    />
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Visualization',
  data() {
    return {
      // 基础状态
      activeTab: 'realtime',
      selectedStock: '000001',
      selectedChartType: 'price_chart',
      dateRange: [new Date('2023-01-01'), new Date('2023-12-31')],
      chartUrl: '',
      chartHtml: '',
      statsData: null,
      isRealtimeUpdating: false,
      realtimeUpdateInterval: null,
      
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
      },
      
      // 风控数据
      accountRisk: {
        status: '低风险',
        marginRatio: 180,
        maxDrawdown: -12.5,
        sharpeRatio: 1.8,
        volatility: 15.2,
        positionRatio: 65,
        dailyProfit: 2.3
      },
      riskThresholds: {
        marginWarning: 130,
        marginLiquidation: 100,
        positionLimit: 90,
        maxDrawdownDaily: 5
      },
      riskChartHtml: '',
      
      // 通知数据
      notifications: [
        {
          id: 1,
          title: '交易执行成功',
          message: '买入贵州茅台(600519) 100股，价格1680.00元',
          type: 'trade',
          timestamp: new Date().getTime() - 300000, // 5分钟前
          read: false
        },
        {
          id: 2,
          title: '保证金预警',
          message: '您的保证金比例已降至135%，接近预警线，请及时补充保证金',
          type: 'risk',
          timestamp: new Date().getTime() - 900000, // 15分钟前
          read: false
        },
        {
          id: 3,
          title: '账户余额不足',
          message: '您的账户余额不足，部分委托可能无法执行',
          type: 'balance',
          timestamp: new Date().getTime() - 1800000, // 30分钟前
          read: true
        },
        {
          id: 4,
          title: '系统维护通知',
          message: '系统将于2023-12-31 22:00-24:00进行例行维护，请提前做好准备',
          type: 'system',
          timestamp: new Date().getTime() - 3600000, // 1小时前
          read: true
        }
      ],
      notificationFilter: 'all',
      notificationStatusFilter: 'all',
      notificationSettings: {
        trade: true,
        risk: true,
        balance: true,
        system: true
      },
      
      // 通知弹窗
      showNotificationPopup: false,
      notificationPopup: {
        title: '',
        message: '',
        type: 'info'
      }
    };
  },
  computed: {
    // 过滤后的通知列表
    filteredNotifications() {
      return this.notifications.filter(notification => {
        const typeMatch = this.notificationFilter === 'all' || notification.type === this.notificationFilter;
        const statusMatch = this.notificationStatusFilter === 'all' || 
          (this.notificationStatusFilter === 'unread' && !notification.read) ||
          (this.notificationStatusFilter === 'read' && notification.read);
        return typeMatch && statusMatch;
      }).sort((a, b) => b.timestamp - a.timestamp);
    }
  },
  mounted() {
    // 组件挂载后初始化
    this.initialize();
    // 启动通知轮询
    this.startNotificationPolling();
  },
  beforeDestroy() {
    // 清理定时器
    if (this.realtimeUpdateInterval) {
      clearInterval(this.realtimeUpdateInterval);
    }
    if (this.notificationPollingInterval) {
      clearInterval(this.notificationPollingInterval);
    }
  },
  methods: {
    // 初始化函数
    async initialize() {
      try {
        // 初始化风险图表
        await this.generateRiskChart();
      } catch (error) {
        console.error('初始化失败:', error);
      }
    },
    
    // 标签切换处理
    handleTabClick(tab) {
      if (tab.name === 'risk') {
        this.refreshRiskData();
      }
    },
    
    // 生成图表
    async generateChart() {
      try {
        // 显示加载中状态
        this.$message.loading('正在生成图表，请稍候...', 0);
        
        // 准备请求参数
        const params = {
          chart_type: this.selectedChartType,
          start_date: this.formatDate(this.dateRange[0]),
          end_date: this.formatDate(this.dateRange[1]),
          stock_symbol: this.selectedStock,
          config: this.chartConfig
        };
        
        // 调用后端API生成图表
        const response = await axios.post('/api/visualization/generate', params);
        
        // 处理响应数据
        if (response.data.success) {
          // 根据图表类型处理返回数据
          if (['candlestick_chart', 'portfolio_performance', 'factor_contribution', 'sankey_diagram', 'sentiment_heatmap'].includes(this.selectedChartType)) {
            this.chartHtml = response.data.chart_html;
            this.chartUrl = '';
          } else {
            this.chartUrl = response.data.chart_url;
            this.chartHtml = '';
          }
          
          // 更新统计数据
          this.statsData = response.data.stats || null;
          
          this.$message.success('图表生成成功');
        } else {
          this.$message.error(`图表生成失败: ${response.data.message}`);
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
        const params = {
          chart_type: this.selectedChartType,
          start_date: this.formatDate(this.dateRange[0]),
          end_date: this.formatDate(this.dateRange[1]),
          stock_symbol: this.selectedStock,
          config: this.chartConfig
        };
        
        // 创建下载链接
        const url = '/api/visualization/download';
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = url;
        form.style.display = 'none';
        
        // 添加表单数据
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'params';
        input.value = JSON.stringify(params);
        form.appendChild(input);
        
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
        
      } catch (error) {
        console.error('下载图表时出错:', error);
        this.$message.error('下载图表时出错，请稍后重试');
      }
    },
    
    // 切换实时更新
    toggleRealtimeUpdate() {
      if (this.isRealtimeUpdating) {
        // 停止实时更新
        clearInterval(this.realtimeUpdateInterval);
        this.realtimeUpdateInterval = null;
        this.isRealtimeUpdating = false;
        this.$message.success('已停止实时更新');
      } else {
        // 开启实时更新
        this.isRealtimeUpdating = true;
        this.$message.success('已开启实时更新');
        // 立即更新一次
        this.generateChart();
        // 设置定时器，每30秒更新一次
        this.realtimeUpdateInterval = setInterval(() => {
          this.generateChart();
        }, 30000);
      }
    },
    
    // 刷新风险数据
    async refreshRiskData() {
      try {
        // 显示加载中状态
        this.$message.loading('正在刷新风险数据，请稍候...', 0);
        
        // 调用后端API获取风险数据
        const response = await axios.get('/api/risk/get_data');
        
        if (response.data.success) {
          this.accountRisk = response.data.risk_data;
          this.riskThresholds = response.data.thresholds;
          await this.generateRiskChart();
          this.$message.success('风险数据刷新成功');
        } else {
          this.$message.error(`风险数据刷新失败: ${response.data.message}`);
        }
      } catch (error) {
        console.error('刷新风险数据时出错:', error);
        // 使用模拟数据
        this.$message.warning('使用模拟风险数据');
        this.generateMockRiskData();
        await this.generateRiskChart();
      } finally {
        // 关闭加载中状态
        this.$message.closeAll();
      }
    },
    
    // 生成风险图表
    async generateRiskChart() {
      try {
        const params = {
          start_date: this.formatDate(this.dateRange[0]),
          end_date: this.formatDate(this.dateRange[1])
        };
        
        const response = await axios.post('/api/risk/generate_chart', params);
        
        if (response.data.success) {
          this.riskChartHtml = response.data.chart_html;
        } else {
          console.error('生成风险图表失败:', response.data.message);
        }
      } catch (error) {
        console.error('生成风险图表时出错:', error);
        // 使用模拟图表
        this.riskChartHtml = '<div style="text-align: center; padding: 50px; color: #999;">模拟风险趋势图</div>';
      }
    },
    
    // 保存风险阈值设置
    async saveRiskThresholds() {
      try {
        const response = await axios.post('/api/risk/update_thresholds', {
          thresholds: this.riskThresholds
        });
        
        if (response.data.success) {
          this.$message.success('风险阈值设置保存成功');
          // 显示通知
          this.showNotification({
            title: '风险阈值设置已更新',
            message: '您的风险阈值设置已成功保存',
            type: 'success'
          });
        } else {
          this.$message.error(`保存失败: ${response.data.message}`);
        }
      } catch (error) {
        console.error('保存风险阈值设置时出错:', error);
        this.$message.error('保存失败，请稍后重试');
      }
    },
    
    // 生成模拟风险数据
    generateMockRiskData() {
      // 随机波动当前风险数据
      const volatilityFactor = 0.05; // 5%的波动
      
      this.accountRisk = {
        ...this.accountRisk,
        marginRatio: Math.max(100, this.accountRisk.marginRatio * (1 + (Math.random() - 0.5) * 2 * volatilityFactor)).toFixed(2),
        maxDrawdown: (this.accountRisk.maxDrawdown * (1 + (Math.random() - 0.5) * 2 * volatilityFactor)).toFixed(2),
        sharpeRatio: (this.accountRisk.sharpeRatio * (1 + (Math.random() - 0.5) * 2 * volatilityFactor)).toFixed(2),
        volatility: (this.accountRisk.volatility * (1 + (Math.random() - 0.5) * 2 * volatilityFactor)).toFixed(2),
        positionRatio: Math.min(100, Math.max(0, this.accountRisk.positionRatio * (1 + (Math.random() - 0.5) * 2 * volatilityFactor))).toFixed(2),
        dailyProfit: (this.accountRisk.dailyProfit * (1 + (Math.random() - 0.5) * 2 * 0.2)).toFixed(2) // 20%的波动
      };
      
      // 更新风险状态
      if (this.accountRisk.marginRatio < this.riskThresholds.marginLiquidation) {
        this.accountRisk.status = '高风险';
      } else if (this.accountRisk.marginRatio < this.riskThresholds.marginWarning) {
        this.accountRisk.status = '中风险';
      } else {
        this.accountRisk.status = '低风险';
      }
    },
    
    // 获取风险标签类型
    getRiskTagType(status) {
      switch(status) {
        case '高风险':
          return 'danger';
        case '中风险':
          return 'warning';
        case '低风险':
          return 'success';
        default:
          return 'info';
      }
    },
    
    // 标记通知为已读
    markAsRead(notificationId) {
      const notification = this.notifications.find(n => n.id === notificationId);
      if (notification && !notification.read) {
        notification.read = true;
      }
    },
    
    // 清空所有通知
    clearAllNotifications() {
      this.$confirm('确定要清空所有通知吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.notifications = [];
        this.$message.success('所有通知已清空');
      }).catch(() => {
        // 用户取消操作
      });
    },
    
    // 获取通知类型文本
    getNotificationTypeText(type) {
      switch(type) {
        case 'trade':
          return '交易完成';
        case 'risk':
          return '风控警报';
        case 'balance':
          return '账户余额';
        case 'system':
          return '系统消息';
        default:
          return '未知类型';
      }
    },
    
    // 获取通知标签类型
    getNotificationTagType(type) {
      switch(type) {
        case 'trade':
          return 'success';
        case 'risk':
          return 'danger';
        case 'balance':
          return 'warning';
        case 'system':
          return 'info';
        default:
          return 'default';
      }
    },
    
    // 格式化通知时间
    formatNotificationTime(timestamp) {
      const now = new Date().getTime();
      const diff = now - timestamp;
      
      if (diff < 60000) {
        return '刚刚';
      } else if (diff < 3600000) {
        return `${Math.floor(diff / 60000)}分钟前`;
      } else if (diff < 86400000) {
        return `${Math.floor(diff / 3600000)}小时前`;
      } else {
        return `${Math.floor(diff / 86400000)}天前`;
      }
    },
    
    // 保存通知设置
    saveNotificationSettings() {
      // 在实际应用中，这里会调用API保存设置到后端
      this.$message.success('通知设置已保存');
      // 显示通知
      this.showNotification({
        title: '通知设置已更新',
        message: '您的通知设置已成功保存',
        type: 'success'
      });
    },
    
    // 显示通知弹窗
    showNotification(notification) {
      this.notificationPopup = {
        title: notification.title,
        message: notification.message,
        type: notification.type || 'info'
      };
      this.showNotificationPopup = true;
      
      // 5秒后自动关闭
      setTimeout(() => {
        this.showNotificationPopup = false;
      }, 5000);
    },
    
    // 启动通知轮询
    startNotificationPolling() {
      // 每1分钟检查一次新通知
      this.notificationPollingInterval = setInterval(() => {
        this.checkForNewNotifications();
      }, 60000);
    },
    
    // 检查新通知
    async checkForNewNotifications() {
      try {
        const response = await axios.get('/api/notifications/get_latest');
        
        if (response.data.success && response.data.new_notifications && response.data.new_notifications.length > 0) {
          // 添加新通知到列表
          response.data.new_notifications.forEach(notification => {
            // 检查是否已存在相同ID的通知
            if (!this.notifications.find(n => n.id === notification.id)) {
              this.notifications.unshift(notification);
              // 显示通知弹窗
              this.showNotification({
                title: notification.title,
                message: notification.message,
                type: this.getNotificationTypeForPopup(notification.type)
              });
            }
          });
        }
      } catch (error) {
        console.error('检查新通知时出错:', error);
        // 静默失败，不影响用户体验
      }
    },
    
    // 获取通知弹窗类型
    getNotificationTypeForPopup(type) {
      switch(type) {
        case 'risk':
          return 'error';
        case 'balance':
          return 'warning';
        case 'trade':
          return 'success';
        default:
          return 'info';
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