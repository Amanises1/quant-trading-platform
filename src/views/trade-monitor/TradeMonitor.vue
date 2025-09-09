<template>
  <div class="trade-monitor-container">
    <el-card>
      <div slot="header" class="clearfix">
        <span>实时交易监控</span>
        <el-button type="primary" size="small" @click="refreshData" class="refresh-btn">
          刷新数据
        </el-button>
      </div>
      
      <!-- 交易状态概览 -->
      <div class="status-overview">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="status-card">
              <div class="status-content">
                <span class="status-label">总持仓市值</span>
                <span class="status-value">{{ formatCurrency(totalPositionValue) }}</span>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="status-card">
              <div class="status-content">
                <span class="status-label">当日盈亏</span>
                <span class="status-value" :class="{ profit: dailyProfit > 0, loss: dailyProfit < 0 }">{{ formatCurrency(dailyProfit) }}</span>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="status-card">
              <div class="status-content">
                <span class="status-label">活跃订单</span>
                <span class="status-value">{{ activeOrders }}</span>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="status-card">
              <div class="status-content">
                <span class="status-label">今日交易次数</span>
                <span class="status-value">{{ todayTrades }}</span>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 持仓列表 -->
      <div class="positions-section">
        <h3>当前持仓</h3>
        <el-table :data="positions" style="width: 100%" stripe>
          <el-table-column prop="symbol" label="股票代码" width="120"></el-table-column>
          <el-table-column prop="name" label="股票名称" width="150"></el-table-column>
          <el-table-column prop="quantity" label="持仓数量" width="120" align="right"></el-table-column>
          <el-table-column prop="avg_price" label="平均成本价" width="120" align="right" :formatter="formatCurrency"></el-table-column>
          <el-table-column prop="current_price" label="当前价格" width="120" align="right" :formatter="formatCurrency"></el-table-column>
          <el-table-column prop="market_value" label="市值" width="120" align="right" :formatter="formatCurrency"></el-table-column>
          <el-table-column prop="profit" label="浮动盈亏" width="120" align="right">
            <template slot-scope="scope">
              <span :class="{ profit: scope.row.profit > 0, loss: scope.row.profit < 0 }">{{ formatCurrency(scope.row.profit) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="profit_rate" label="盈亏比例" width="120" align="right">
            <template slot-scope="scope">
              <span :class="{ profit: scope.row.profit_rate > 0, loss: scope.row.profit_rate < 0 }">{{ (scope.row.profit_rate * 100).toFixed(2) }}%</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template slot-scope="scope">
              <el-button type="text" size="small" @click="sellPosition(scope.row)">卖出</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 交易历史 -->
      <div class="trade-history-section">
        <h3>今日交易历史</h3>
        <el-table :data="tradeHistory" style="width: 100%" stripe>
          <el-table-column prop="timestamp" label="交易时间" width="180" :formatter="formatTime"></el-table-column>
        <el-table-column prop="symbol" label="股票代码" width="120"></el-table-column>
        <el-table-column prop="name" label="股票名称" width="150"></el-table-column>
        <el-table-column prop="side" label="交易方向" width="100">
          <template slot-scope="scope">
            <el-tag :type="scope.row.side === 'buy' ? 'success' : 'danger'">
              {{ scope.row.side === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="100" align="right"></el-table-column>
        <el-table-column prop="price" label="价格" width="120" align="right" :formatter="formatCurrency"></el-table-column>
        <el-table-column prop="amount" label="成交额" width="120" align="right" :formatter="formatCurrency"></el-table-column>
        <el-table-column prop="fee" label="交易费用" width="120" align="right" :formatter="formatCurrency">
          <template slot-scope="scope">
            {{ formatCurrency(scope.row.fee || 0) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template slot-scope="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ getStatusText(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        </el-table>
    </div>

    <!-- 活跃订单 -->
    <div class="active-orders-section">
      <h3>活跃订单</h3>
      <el-table :data="activeOrdersList" style="width: 100%" stripe>
        <el-table-column prop="id" label="订单ID" width="180"></el-table-column>
        <el-table-column prop="timestamp" label="下单时间" width="180" :formatter="formatTime"></el-table-column>
        <el-table-column prop="symbol" label="股票代码" width="120"></el-table-column>
        <el-table-column prop="name" label="股票名称" width="150"></el-table-column>
        <el-table-column prop="side" label="交易方向" width="100">
          <template slot-scope="scope">
            <el-tag :type="scope.row.side === 'buy' ? 'success' : 'danger'">
              {{ scope.row.side === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="100" align="right"></el-table-column>
        <el-table-column prop="filled_quantity" label="已成交" width="100" align="right"></el-table-column>
        <el-table-column prop="price" label="价格" width="120" align="right" :formatter="formatCurrency"></el-table-column>
        <el-table-column prop="order_type" label="订单类型" width="100">
          <template slot-scope="scope">
            <el-tag type="info">{{ scope.row.order_type === 'limit' ? '限价单' : '市价单' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template slot-scope="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ getStatusText(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template slot-scope="scope">
            <el-button 
              type="text" 
              size="small" 
              @click="cancelOrder(scope.row.id)"
              :disabled="['filled', 'rejected', 'cancelled'].includes(scope.row.status)"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 账户资金 -->
    <div class="account-section">
      <h3>账户资金</h3>
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="status-card">
            <div class="status-content">
              <span class="status-label">账户总资产</span>
              <span class="status-value">{{ formatCurrency(accountBalance + totalPositionValue) }}</span>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="status-card">
            <div class="status-content">
              <span class="status-label">现金余额</span>
              <span class="status-value">{{ formatCurrency(accountBalance) }}</span>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="status-card">
            <div class="status-content">
              <span class="status-label">可用资金</span>
              <span class="status-value">{{ formatCurrency(availableFunds) }}</span>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="status-card">
            <div class="status-content">
              <span class="status-label">资金使用率</span>
              <span class="status-value">{{ ((totalPositionValue / (accountBalance + totalPositionValue)) * 100).toFixed(2) }}%</span>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 交易表单 -->
      <div class="trade-form-section">
        <h3>执行交易</h3>
        <el-form :model="tradeForm" ref="tradeForm" label-width="100px">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="股票代码" prop="symbol">
                <el-input v-model="tradeForm.symbol" placeholder="请输入股票代码"></el-input>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="交易方向" prop="side">
                <el-radio-group v-model="tradeForm.side">
                  <el-radio label="buy">买入</el-radio>
                  <el-radio label="sell">卖出</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="订单类型" prop="order_type">
                <el-select v-model="tradeForm.order_type" placeholder="请选择订单类型">
                  <el-option label="市价单" value="market"></el-option>
                  <el-option label="限价单" value="limit"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="交易数量" prop="quantity">
                <el-input v-model.number="tradeForm.quantity" placeholder="请输入交易数量"></el-input>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="交易价格" prop="price">
                <el-input v-model.number="tradeForm.price" placeholder="请输入交易价格" :disabled="tradeForm.order_type === 'market'"></el-input>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item>
                <el-button type="primary" @click="submitTrade">提交订单</el-button>
                <el-button @click="resetTradeForm">重置</el-button>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </div>
    </el-card>

    <!-- 卖出确认对话框 -->
    <el-dialog title="确认卖出" :visible.sync="sellDialogVisible" width="40%">
      <div v-if="selectedPosition">
        <p>股票代码: {{ selectedPosition.symbol }}</p>
        <p>股票名称: {{ selectedPosition.name }}</p>
        <p>当前持仓: {{ selectedPosition.quantity }}股</p>
        <p>当前价格: {{ formatCurrency(selectedPosition.current_price) }}</p>
        <el-form-item label="卖出数量" prop="sellQuantity">
          <el-input v-model.number="sellQuantity" placeholder="请输入卖出数量"></el-input>
        </el-form-item>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="sellDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmSell">确认卖出</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import axios from '../../utils/axios-config.js'

export default {
  name: 'TradeMonitor',
  data() {
    return {
      // 交易状态数据
      totalPositionValue: 0,
      dailyProfit: 0,
      activeOrders: 0,
      todayTrades: 0,
      
      // 资金数据
      accountBalance: 0,
      availableFunds: 0,
      
      // 持仓数据
      positions: [],
      
      // 交易历史数据
      tradeHistory: [],
      
      // 活跃订单数据
      activeOrdersList: [],
      
      // 交易表单数据
      tradeForm: {
        symbol: '',
        side: 'buy',
        order_type: 'market',
        quantity: '',
        price: ''
      },
      
      // 卖出对话框数据
      sellDialogVisible: false,
      selectedPosition: null,
      sellQuantity: 0
    }
  },
  mounted() {
    // 组件挂载后加载数据
    this.loadAllData()
    
    // 定时刷新数据（每30秒）
    this.refreshTimer = setInterval(() => {
      this.loadAllData()
    }, 30000)
  },
  beforeDestroy() {
    // 组件销毁前清除定时器
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer)
    }
  },
  methods: {
    // 加载所有数据
    async loadAllData() {
      try {
        // 同时加载多个API的数据
        const [positionsResponse, tradeHistoryResponse, accountResponse, activeOrdersResponse] = await Promise.all([
          axios.get('/api/positions'),
          axios.get('/api/trade/history', {
            params: {
              start_date: new Date().toISOString().split('T')[0],
              end_date: new Date().toISOString().split('T')[0]
            }
          }),
          axios.get('/api/account'),
          axios.get('/api/orders/active')
        ])
        
        // 处理持仓数据
        if (positionsResponse && positionsResponse.positions) {
          this.positions = positionsResponse.positions
          this.calculatePositionStats()
        } else {
          // 使用模拟数据
          this.positions = this.getMockPositions()
          this.calculatePositionStats()
        }
        
        // 处理交易历史数据
        if (tradeHistoryResponse && tradeHistoryResponse.trades) {
          this.tradeHistory = tradeHistoryResponse.trades
        } else {
          // 使用模拟数据
          this.tradeHistory = this.getMockTradeHistory()
        }
        
        // 处理账户资金数据
        if (accountResponse && accountResponse.balance && accountResponse.available_funds) {
          this.accountBalance = accountResponse.balance
          this.availableFunds = accountResponse.available_funds
        } else {
          // 使用模拟数据
          this.accountBalance = 500000.00
          this.availableFunds = 300000.00
        }
        
        // 处理活跃订单数据
        if (activeOrdersResponse && activeOrdersResponse.orders) {
          this.activeOrdersList = activeOrdersResponse.orders
        } else {
          // 使用模拟数据
          this.activeOrdersList = this.getMockActiveOrders()
        }
        
        // 计算交易统计
        this.calculateTradeStats()
      } catch (error) {
        console.error('加载数据失败:', error)
        // 使用模拟数据
        this.positions = this.getMockPositions()
        this.tradeHistory = this.getMockTradeHistory()
        this.accountBalance = 500000.00
        this.availableFunds = 300000.00
        this.activeOrdersList = this.getMockActiveOrders()
        this.calculatePositionStats()
        this.calculateTradeStats()
        this.$message.error('数据加载失败，使用模拟数据')
      }
    },
    
    // 刷新数据
    refreshData() {
      this.loadAllData()
      this.$message.success('数据已刷新')
    },
    
    // 计算持仓统计数据
    calculatePositionStats() {
      this.totalPositionValue = this.positions.reduce((sum, pos) => sum + (pos.market_value || 0), 0)
      this.dailyProfit = this.positions.reduce((sum, pos) => sum + (pos.profit || 0), 0)
    },
    
    // 计算交易统计数据
    calculateTradeStats() {
      this.todayTrades = this.tradeHistory.length
      this.activeOrders = this.activeOrdersList.length
    },
    
    // 取消订单
    async cancelOrder(orderId) {
      try {
        const response = await axios.post('/api/orders/cancel', {
          order_id: orderId
        })
        
        if (response && response.success) {
          this.$message.success('订单取消成功')
          // 重新加载数据
          this.loadAllData()
        }
      } catch (error) {
        console.error('取消订单失败:', error)
        this.$message.error('订单取消失败，请稍后重试')
      }
    },
    
    // 获取模拟活跃订单数据
    getMockActiveOrders() {
      const now = new Date()
      const formatTime = (minutes) => {
        const time = new Date(now)
        time.setMinutes(now.getMinutes() - minutes)
        return time.toISOString()
      }
      
      return [
        {
          id: 'ORD-20230415-0001',
          timestamp: formatTime(60),
          symbol: '600036',
          name: '招商银行',
          side: 'buy',
          quantity: 200,
          price: 35.60,
          status: 'pending',
          order_type: 'limit',
          filled_quantity: 0,
          fee: 0
        },
        {
          id: 'ORD-20230415-0002',
          timestamp: formatTime(90),
          symbol: '601318',
          name: '中国平安',
          side: 'sell',
          quantity: 500,
          price: 55.80,
          status: 'partially_filled',
          order_type: 'limit',
          filled_quantity: 200,
          fee: 11.16
        }
      ]
    },
    
    // 提交交易订单
    async submitTrade() {
      // 表单验证
      if (!this.tradeForm.symbol || !this.tradeForm.quantity || (this.tradeForm.order_type === 'limit' && !this.tradeForm.price)) {
        this.$message.error('请填写完整的交易信息')
        return
      }
      
      try {
        const response = await axios.post('/api/trade/exec', {
          account_id: 'default',
          symbol: this.tradeForm.symbol,
          side: this.tradeForm.side,
          quantity: this.tradeForm.quantity,
          price: this.tradeForm.price,
          order_type: this.tradeForm.order_type
        })
        
        if (response) {
          this.$message.success('订单提交成功')
          this.resetTradeForm()
          // 重新加载数据
          this.loadAllData()
        }
      } catch (error) {
        console.error('提交订单失败:', error)
        this.$message.error('订单提交失败，请稍后重试')
      }
    },
    
    // 重置交易表单
    resetTradeForm() {
      this.tradeForm = {
        symbol: '',
        side: 'buy',
        order_type: 'market',
        quantity: '',
        price: ''
      }
      if (this.$refs.tradeForm) {
        this.$refs.tradeForm.resetFields()
      }
    },
    
    // 打开卖出对话框
    sellPosition(position) {
      this.selectedPosition = position
      this.sellQuantity = position.quantity
      this.sellDialogVisible = true
    },
    
    // 确认卖出
    async confirmSell() {
      if (!this.sellQuantity || this.sellQuantity <= 0 || this.sellQuantity > this.selectedPosition.quantity) {
        this.$message.error('请输入有效的卖出数量')
        return
      }
      
      try {
        const response = await axios.post('/api/trade/exec', {
          account_id: 'default',
          symbol: this.selectedPosition.symbol,
          side: 'sell',
          quantity: this.sellQuantity,
          price: this.selectedPosition.current_price,
          order_type: 'market'
        })
        
        if (response) {
          this.$message.success('卖出订单提交成功')
          this.sellDialogVisible = false
          // 重新加载数据
          this.loadAllData()
        }
      } catch (error) {
        console.error('卖出订单提交失败:', error)
        this.$message.error('卖出订单提交失败，请稍后重试')
      }
    },
    
    // 格式化货币
    formatCurrency(value) {
      if (!value && value !== 0) return '¥0.00'
      return '¥' + Number(value).toFixed(2)
    },
    
    // 格式化时间
    formatTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN')
    },
    
    // 获取订单状态类型
    getStatusType(status) {
      const statusMap = {
        'filled': 'success',
        'pending': 'warning',
        'rejected': 'danger',
        'cancelled': 'info',
        'partially_filled': 'primary'
      }
      return statusMap[status] || 'default'
    },
    
    // 获取订单状态文本
    getStatusText(status) {
      const statusMap = {
        'filled': '已成交',
        'pending': '待成交',
        'rejected': '已拒绝',
        'cancelled': '已取消',
        'partially_filled': '部分成交'
      }
      return statusMap[status] || status
    },
    
    // 获取模拟持仓数据
    getMockPositions() {
      return [
        {
          symbol: '600519',
          name: '贵州茅台',
          quantity: 100,
          avg_price: 1680.00,
          current_price: 1720.50,
          market_value: 172050.00,
          profit: 4050.00,
          profit_rate: 0.0241
        },
        {
          symbol: '000858',
          name: '五粮液',
          quantity: 200,
          avg_price: 165.00,
          current_price: 160.20,
          market_value: 32040.00,
          profit: -960.00,
          profit_rate: -0.0291
        },
        {
          symbol: '000001',
          name: '平安银行',
          quantity: 500,
          avg_price: 12.50,
          current_price: 13.20,
          market_value: 6600.00,
          profit: 350.00,
          profit_rate: 0.056
        }
      ]
    },
    
    // 获取模拟交易历史数据
    getMockTradeHistory() {
      const now = new Date()
      const formatTime = (minutes) => {
        const time = new Date(now)
        time.setMinutes(now.getMinutes() - minutes)
        return time.toISOString()
      }
      
      return [
        {
          timestamp: formatTime(10),
          symbol: '600519',
          name: '贵州茅台',
          side: 'buy',
          quantity: 100,
          price: 1680.00,
          amount: 168000.00,
          status: 'filled'
        },
        {
          timestamp: formatTime(25),
          symbol: '000858',
          name: '五粮液',
          side: 'sell',
          quantity: 100,
          price: 162.50,
          amount: 16250.00,
          status: 'filled'
        },
        {
          timestamp: formatTime(45),
          symbol: '000001',
          name: '平安银行',
          side: 'buy',
          quantity: 500,
          price: 12.50,
          amount: 6250.00,
          status: 'filled'
        },
        {
          timestamp: formatTime(60),
          symbol: '600036',
          name: '招商银行',
          side: 'buy',
          quantity: 200,
          price: 35.60,
          amount: 7120.00,
          status: 'pending'
        }
      ]
    }
  }
}
</script>

<style scoped>
.trade-monitor-container {
  padding: 20px;
}

.refresh-btn {
  float: right;
}

.status-overview {
  margin-bottom: 30px;
}

.status-card {
  height: 100%;
}

.status-content {
  text-align: center;
  padding: 10px 0;
}

.status-label {
  display: block;
  color: #606266;
  font-size: 14px;
  margin-bottom: 10px;
}

.status-value {
  display: block;
  color: #303133;
  font-size: 24px;
  font-weight: bold;
}

.profit {
  color: #f56c6c !important;
}

.loss {
  color: #67c23a !important;
}

.positions-section,
    .active-orders-section,
    .account-section,
    .trade-history-section,
    .trade-form-section {
  margin-bottom: 30px;
}

h3 {
  margin-bottom: 15px;
  color: #303133;
  font-size: 18px;
}

.dialog-footer {
  text-align: right;
}
</style>