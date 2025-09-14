<template>
  <div class="strategy-backtest-container">
    <div class="page-header">
      <h2>策略回测系统</h2>
      <p>选择交易策略、设置参数并进行历史回测分析</p>
    </div>

    <el-row :gutter="20">
      <!-- 左侧参数配置面板 -->
      <el-col :span="6" class="parameter-panel">
        <el-card shadow="hover" class="config-card">
          <div slot="header" class="card-header">
            <span>回测参数配置</span>
          </div>
          
          <!-- 策略选择 -->
          <div class="form-section">
            <el-form-item label="策略类型" label-width="100px">
              <el-select v-model="selectedStrategy" placeholder="请选择策略">
                <el-option label="移动平均线交叉策略" value="sma"></el-option>
                <el-option label="MACD策略" value="macd"></el-option>
                <el-option label="RSI策略" value="rsi"></el-option>
                <el-option label="均值回归策略" value="mean_reversion"></el-option>
              </el-select>
            </el-form-item>

            <!-- SMA策略参数 -->
            <div v-if="selectedStrategy === 'sma'" class="strategy-params">
              <el-form-item label="短期均线" label-width="100px">
                <el-input-number v-model="smaParams.shortPeriod" :min="1" :max="100" :step="1"></el-input-number>
              </el-form-item>
              <el-form-item label="长期均线" label-width="100px">
                <el-input-number v-model="smaParams.longPeriod" :min="1" :max="200" :step="1"></el-input-number>
              </el-form-item>
            </div>

            <!-- MACD策略参数 -->
            <div v-if="selectedStrategy === 'macd'" class="strategy-params">
              <el-form-item label="快线周期" label-width="100px">
                <el-input-number v-model="macdParams.fastPeriod" :min="1" :max="50" :step="1"></el-input-number>
              </el-form-item>
              <el-form-item label="慢线周期" label-width="100px">
                <el-input-number v-model="macdParams.slowPeriod" :min="1" :max="100" :step="1"></el-input-number>
              </el-form-item>
              <el-form-item label="信号线周期" label-width="100px">
                <el-input-number v-model="macdParams.signalPeriod" :min="1" :max="50" :step="1"></el-input-number>
              </el-form-item>
            </div>

            <!-- 回测基本参数 -->
            <div class="basic-params">
              <el-form-item label="初始资金" label-width="100px">
                <el-input-number v-model="backtestParams.initialCapital" :min="1000" :max="1000000" :step="1000"></el-input-number>
              </el-form-item>
              <el-form-item label="交易费用(%)" label-width="100px">
                <el-input-number v-model="backtestParams.transactionFee" :min="0" :max="1" :step="0.01" :precision="2"></el-input-number>
              </el-form-item>
              <el-form-item label="回测周期" label-width="100px">
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  format="yyyy-MM-dd"
                  value-format="yyyy-MM-dd"
                ></el-date-picker>
              </el-form-item>
              <el-form-item label="股票代码" label-width="100px">
                <el-input v-model="backtestParams.symbol" placeholder="如: 600000.SH"></el-input>
              </el-form-item>
            </div>

            <!-- 运行按钮 -->
            <div class="action-buttons">
              <el-button type="primary" @click="runBacktest" :loading="isRunning">
                <i class="el-icon-play" v-if="!isRunning"></i>
                <i class="el-icon-loading" v-if="isRunning"></i>
                运行回测
              </el-button>
              <el-button @click="resetParams">重置参数</el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧结果展示面板 -->
      <el-col :span="18" class="results-panel">
        <!-- 绩效指标卡片 -->
        <el-card shadow="hover" class="performance-card">
          <div slot="header" class="card-header">
            <span>绩效指标</span>
          </div>
          <div class="performance-metrics">
            <div class="metric-item">
              <div class="metric-label">总收益率</div>
              <div class="metric-value">{{ performanceMetrics.totalReturn.toFixed(2) }}%</div>
            </div>
            <div class="metric-item">
              <div class="metric-label">最大回撤</div>
              <div class="metric-value">{{ performanceMetrics.maxDrawdown.toFixed(2) }}%</div>
            </div>
            <div class="metric-item">
              <div class="metric-label">夏普比率</div>
              <div class="metric-value">{{ performanceMetrics.sharpeRatio.toFixed(2) }}</div>
            </div>
            <div class="metric-item">
              <div class="metric-label">胜率</div>
              <div class="metric-value">{{ performanceMetrics.winRate.toFixed(2) }}%</div>
            </div>
            <div class="metric-item">
              <div class="metric-label">交易次数</div>
              <div class="metric-value">{{ performanceMetrics.tradeCount }}</div>
            </div>
            <div class="metric-item">
              <div class="metric-label">最终资产</div>
              <div class="metric-value">¥{{ performanceMetrics.finalEquity.toFixed(2) }}</div>
            </div>
          </div>
        </el-card>

        <!-- 图表展示区域 -->
        <div class="charts-container">
          <!-- 价格和策略信号图 -->
          <el-card shadow="hover" class="chart-card">
            <div slot="header" class="card-header">
              <span>价格与交易信号</span>
            </div>
            <div id="priceChart" class="chart"></div>
          </el-card>

          <!-- 资产净值曲线 -->
          <el-card shadow="hover" class="chart-card">
            <div slot="header" class="card-header">
              <span>资产净值曲线</span>
            </div>
            <div id="equityChart" class="chart"></div>
          </el-card>
        </div>

        <!-- 交易记录表格 -->
        <el-card shadow="hover" class="trades-card">
          <div slot="header" class="card-header">
            <span>交易记录</span>
          </div>
          <el-table :data="tradeRecords" style="width: 100%">
            <el-table-column prop="date" label="交易日期" width="180"></el-table-column>
            <el-table-column prop="action" label="操作" width="100"></el-table-column>
            <el-table-column prop="price" label="价格" width="100"></el-table-column>
            <el-table-column prop="quantity" label="数量" width="100"></el-table-column>
            <el-table-column prop="amount" label="金额" width="120"></el-table-column>
            <el-table-column prop="equity" label="资产净值" width="120"></el-table-column>
            <el-table-column prop="pnl" label="盈亏" width="100"></el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import * as echarts from 'echarts';

export default {
  name: 'StrategyBacktest',
  data() {
    return {
      // 策略选择
      selectedStrategy: 'sma',
      
      // SMA策略参数
      smaParams: {
        shortPeriod: 5,
        longPeriod: 20
      },
      
      // MACD策略参数
      macdParams: {
        fastPeriod: 12,
        slowPeriod: 26,
        signalPeriod: 9
      },
      
      // 回测基本参数
      backtestParams: {
        initialCapital: 100000,
        transactionFee: 0.1,
        symbol: '600000.SH'
      },
      
      // 日期范围
      dateRange: [],
      
      // 回测状态
      isRunning: false,
      
      // 回测结果
      performanceMetrics: {
        totalReturn: 0,
        maxDrawdown: 0,
        sharpeRatio: 0,
        winRate: 0,
        tradeCount: 0,
        finalEquity: 0
      },
      
      // 交易记录
      tradeRecords: [],
      
      // 图表实例
      priceChart: null,
      equityChart: null,
      
      // 回测数据（用于图表展示）
      backtestData: {
        dates: [],
        prices: [],
        signals: [],
        equity: []
      }
    };
  },
  
  mounted() {
    // 初始化日期范围（默认最近一年）
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(startDate.getFullYear() - 1);
    this.dateRange = [startDate, endDate];
    
    // 初始化图表
    this.$nextTick(() => {
      this.initCharts();
      this.updateCharts();
    });
  },
  
  beforeDestroy() {
    // 销毁图表实例
    if (this.priceChart) {
      this.priceChart.dispose();
    }
    if (this.equityChart) {
      this.equityChart.dispose();
    }
  },
  
  methods: {
    // 初始化图表
    initCharts() {
      // 价格与交易信号图
      this.priceChart = echarts.init(document.getElementById('priceChart'));
      
      // 资产净值曲线图
      this.equityChart = echarts.init(document.getElementById('equityChart'));
      
      // 窗口大小变化时重新调整图表大小
      window.addEventListener('resize', () => {
        if (this.priceChart) this.priceChart.resize();
        if (this.equityChart) this.equityChart.resize();
      });
    },
    
    // 更新图表显示
    updateCharts() {
      // 价格与交易信号图配置
      const priceOption = {
        title: {
          text: `${this.backtestParams.symbol} 价格走势与交易信号`,
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          }
        },
        legend: {
          data: ['价格', '买入信号', '卖出信号'],
          bottom: 10
        },
        xAxis: {
          type: 'category',
          data: this.backtestData.dates,
          axisLabel: {
            interval: Math.floor(this.backtestData.dates.length / 20), // 控制显示的标签数量
            rotate: 45
          }
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '价格',
            type: 'line',
            data: this.backtestData.prices,
            smooth: true,
            lineStyle: {
              color: '#3366CC'
            }
          },
          {
            name: '买入信号',
            type: 'scatter',
            data: this.backtestData.dates.map((date, index) => {
              return this.backtestData.signals[index] === 1 ? [index, this.backtestData.prices[index]] : null;
            }).filter(item => item !== null),
            symbolSize: 10,
            itemStyle: {
              color: '#2ECC71'
            }
          },
          {
            name: '卖出信号',
            type: 'scatter',
            data: this.backtestData.dates.map((date, index) => {
              return this.backtestData.signals[index] === -1 ? [index, this.backtestData.prices[index]] : null;
            }).filter(item => item !== null),
            symbolSize: 10,
            itemStyle: {
              color: '#E74C3C'
            }
          }
        ]
      };
      
      // 资产净值曲线图配置
      const equityOption = {
        title: {
          text: '资产净值走势',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['资产净值'],
          bottom: 10
        },
        xAxis: {
          type: 'category',
          data: this.backtestData.dates,
          axisLabel: {
            interval: Math.floor(this.backtestData.dates.length / 20), // 控制显示的标签数量
            rotate: 45
          }
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            formatter: '¥{value}'
          }
        },
        series: [
          {
            name: '资产净值',
            type: 'line',
            data: this.backtestData.equity,
            smooth: true,
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(51, 102, 204, 0.3)' },
                { offset: 1, color: 'rgba(51, 102, 204, 0.05)' }
              ])
            },
            lineStyle: {
              color: '#3366CC'
            }
          }
        ]
      };
      
      // 应用图表配置
      this.priceChart.setOption(priceOption);
      this.equityChart.setOption(equityOption);
    },
    
    // 运行回测
    async runBacktest() {
      // 验证参数
      if (!this.selectedStrategy || !this.dateRange || this.dateRange.length === 0) {
        this.$message.error('请完善回测参数');
        return;
      }
      
      this.isRunning = true;
      
      try {
        // 构建回测请求参数
        const requestParams = {
          strategy_type: this.selectedStrategy,
          symbol: this.backtestParams.symbol,
          start_date: this.dateRange[0],
          end_date: this.dateRange[1],
          initial_capital: this.backtestParams.initialCapital,
          transaction_fee: this.backtestParams.transactionFee,
          strategy_params: {}
        };
        
        // 添加策略特定参数
        if (this.selectedStrategy === 'sma') {
          requestParams.strategy_params = this.smaParams;
        } else if (this.selectedStrategy === 'macd') {
          requestParams.strategy_params = this.macdParams;
        }
        
        // 模拟回测请求（实际项目中应替换为真实API调用）
        // const response = await axios.post('/api/backtest/run', requestParams);
        // const result = response.data;
        
        // 模拟回测结果
        const result = this.generateMockBacktestResult();
        
        // 更新回测结果
        this.updateBacktestResults(result);
        
        this.$message.success('回测完成');
      } catch (error) {
        console.error('回测失败:', error);
        this.$message.error('回测失败，请检查参数或网络连接');
      } finally {
        this.isRunning = false;
      }
    },
    
    // 重置参数
    resetParams() {
      // 重置策略选择
      this.selectedStrategy = 'sma';
      
      // 重置策略参数
      this.smaParams = {
        shortPeriod: 5,
        longPeriod: 20
      };
      
      this.macdParams = {
        fastPeriod: 12,
        slowPeriod: 26,
        signalPeriod: 9
      };
      
      // 重置回测基本参数
      this.backtestParams = {
        initialCapital: 100000,
        transactionFee: 0.1,
        symbol: '600000.SH'
      };
      
      // 重置日期范围
      const endDate = new Date();
      const startDate = new Date();
      startDate.setFullYear(startDate.getFullYear() - 1);
      this.dateRange = [startDate, endDate];
      
      // 重置回测结果
      this.resetBacktestResults();
      
      this.$message.success('参数已重置');
    },
    
    // 更新回测结果
    updateBacktestResults(result) {
      // 更新绩效指标
      this.performanceMetrics = result.performance;
      
      // 更新交易记录
      this.tradeRecords = result.trades;
      
      // 更新图表数据
      this.backtestData = result.chartData;
      
      // 更新图表显示
      this.updateCharts();
    },
    
    // 重置回测结果
    resetBacktestResults() {
      // 重置绩效指标
      this.performanceMetrics = {
        totalReturn: 0,
        maxDrawdown: 0,
        sharpeRatio: 0,
        winRate: 0,
        tradeCount: 0,
        finalEquity: 0
      };
      
      // 重置交易记录
      this.tradeRecords = [];
      
      // 重置图表数据
      this.backtestData = {
        dates: [],
        prices: [],
        signals: [],
        equity: []
      };
      
      // 更新图表显示
      this.updateCharts();
    },
    
    // 生成模拟回测结果（实际项目中应替换为真实API返回数据）
    generateMockBacktestResult() {
      const days = 252; // 一年交易日
      const dates = [];
      const prices = [];
      const signals = [];
      const equity = [];
      const trades = [];
      
      // 生成模拟日期和价格数据
      let currentDate = new Date(this.dateRange[0]);
      let price = 100;
      let currentEquity = this.backtestParams.initialCapital;
      let shares = 0;
      let lastBuyPrice = 0;
      
      for (let i = 0; i < days; i++) {
        // 生成日期
        dates.push(currentDate.toISOString().split('T')[0]);
        
        // 生成价格（随机游走）
        const change = (Math.random() - 0.49) * 2; // -1 到 1 之间的随机数
        price = Math.max(price * (1 + change / 100), 50);
        prices.push(price.toFixed(2));
        
        // 生成交易信号
        let signal = 0;
        if (i > 0 && i % 30 === 0) {
          if (Math.random() > 0.5 && shares === 0) {
            signal = 1; // 买入
            const buyAmount = currentEquity * 0.3;
            shares = Math.floor(buyAmount / price);
            currentEquity -= shares * price * (1 + this.backtestParams.transactionFee / 100);
            lastBuyPrice = price;
            
            trades.push({
              date: dates[i],
              action: '买入',
              price: price.toFixed(2),
              quantity: shares,
              amount: (shares * price).toFixed(2),
              equity: currentEquity.toFixed(2),
              pnl: '0.00'
            });
          } else if (shares > 0) {
            signal = -1; // 卖出
            const sellAmount = shares * price;
            currentEquity += sellAmount * (1 - this.backtestParams.transactionFee / 100);
            const pnl = (sellAmount * (1 - this.backtestParams.transactionFee / 100) - shares * lastBuyPrice * (1 + this.backtestParams.transactionFee / 100)).toFixed(2);
            
            trades.push({
              date: dates[i],
              action: '卖出',
              price: price.toFixed(2),
              quantity: shares,
              amount: sellAmount.toFixed(2),
              equity: currentEquity.toFixed(2),
              pnl: pnl
            });
            
            shares = 0;
          }
        }
        signals.push(signal);
        
        // 更新资产净值
        if (shares > 0) {
          const totalEquity = currentEquity + shares * price;
          equity.push(totalEquity.toFixed(2));
        } else {
          equity.push(currentEquity.toFixed(2));
        }
        
        // 增加一天
        currentDate.setDate(currentDate.getDate() + 1);
        // 跳过周末
        if (currentDate.getDay() === 0 || currentDate.getDay() === 6) {
          currentDate.setDate(currentDate.getDate() + (currentDate.getDay() === 0 ? 1 : 2));
        }
      }
      
      // 计算绩效指标
      const totalReturn = ((parseFloat(equity[equity.length - 1]) / this.backtestParams.initialCapital) - 1) * 100;
      
      // 计算最大回撤
      let maxDrawdown = 0;
      let peakEquity = parseFloat(equity[0]);
      for (let i = 1; i < equity.length; i++) {
        const current = parseFloat(equity[i]);
        if (current > peakEquity) {
          peakEquity = current;
        } else {
          const drawdown = ((peakEquity - current) / peakEquity) * 100;
          if (drawdown > maxDrawdown) {
            maxDrawdown = drawdown;
          }
        }
      }
      
      // 计算胜率
      let winCount = 0;
      let loseCount = 0;
      for (const trade of trades) {
        if (parseFloat(trade.pnl) > 0) {
          winCount++;
        } else if (parseFloat(trade.pnl) < 0) {
          loseCount++;
        }
      }
      const winRate = trades.length > 0 ? (winCount / (winCount + loseCount)) * 100 : 0;
      
      // 计算夏普比率（简化计算）
      const dailyReturns = [];
      for (let i = 1; i < equity.length; i++) {
        const dailyReturn = ((parseFloat(equity[i]) / parseFloat(equity[i - 1])) - 1);
        dailyReturns.push(dailyReturn);
      }
      const avgReturn = dailyReturns.reduce((sum, ret) => sum + ret, 0) / dailyReturns.length;
      const stdDev = Math.sqrt(dailyReturns.reduce((sum, ret) => sum + Math.pow(ret - avgReturn, 2), 0) / dailyReturns.length);
      const sharpeRatio = stdDev > 0 ? (avgReturn / stdDev) * Math.sqrt(252) : 0;
      
      return {
        performance: {
          totalReturn: totalReturn,
          maxDrawdown: maxDrawdown,
          sharpeRatio: sharpeRatio,
          winRate: winRate,
          tradeCount: trades.length,
          finalEquity: parseFloat(equity[equity.length - 1])
        },
        trades: trades,
        chartData: {
          dates: dates,
          prices: prices,
          signals: signals,
          equity: equity
        }
      };
    }
  }
};
</script>

<style scoped>
.strategy-backtest-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  color: #303133;
  margin-bottom: 10px;
}

.page-header p {
  color: #606266;
  font-size: 14px;
}

.parameter-panel {
  background-color: #fafafa;
  padding: 10px;
  border-radius: 4px;
}

.results-panel {
  background-color: #fafafa;
  padding: 10px;
  border-radius: 4px;
}

.config-card,
.performance-card,
.chart-card,
.trades-card {
  margin-bottom: 20px;
  background-color: #ffffff;
}

.card-header {
  font-weight: bold;
  color: #303133;
}

.form-section {
  padding: 10px 0;
}

.strategy-params,
.basic-params {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e4e7ed;
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.performance-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  padding: 10px 0;
}

.metric-item {
  text-align: center;
  min-width: 100px;
}

.metric-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 5px;
}

.metric-value {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.charts-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart {
  width: 100%;
  height: 400px;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .parameter-panel {
    margin-bottom: 20px;
  }
}
</style>