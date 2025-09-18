<template>
  <div class="trade-monitor-container">
    <el-card>
      <div slot="header" class="clearfix">
        <span>实时交易监控</span>
        <el-button type="primary" size="small" @click="refreshData" class="refresh-btn">
          刷新数据
        </el-button>
      </div>

      <!-- 标签页组件 -->
      <el-tabs v-model="activeTab" type="border-card" @tab-click="handleTabClick">
        <!-- 交易监控标签页 -->
        <el-tab-pane label="交易监控" name="trade">
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
                    <span class="status-label">累计收益率</span>
                    <span class="status-value" :class="{ profit: cumulativeReturn > 0, loss: cumulativeReturn < 0 }">{{ cumulativeReturn.toFixed(2) }}%</span>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card class="status-card">
                  <div class="status-content">
                    <span class="status-label">年化波动率</span>
                    <span class="status-value">{{ annualVolatility.toFixed(2) }}%</span>
                  </div>
                </el-card>
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-top: 20px;">
              <el-col :span="6">
                <el-card class="status-card">
                  <div class="status-content">
                    <span class="status-label">夏普比率</span>
                    <span class="status-value">{{ sharpeRatio.toFixed(2) }}</span>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card class="status-card">
                  <div class="status-content">
                    <span class="status-label">最大回撤</span>
                    <span class="status-value loss">{{ maxDrawdown.toFixed(2) }}%</span>
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
              <el-col :span="6">
                <el-card class="status-card">
                  <div class="status-content">
                    <span class="status-label">风险状态</span>
                    <span class="status-value" :class="{ 'risk-low': riskStatus === '低风险', 'risk-medium': riskStatus === '中风险', 'risk-high': riskStatus === '高风险' }">{{ riskStatus }}</span>
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

          <!-- 买入操作 -->
          <div class="buy-section">
            <h3>买入股票</h3>
            <el-form :model="buyForm" ref="buyForm" :rules="{
              stockCode: [{ required: true, message: '请输入股票代码', trigger: 'blur' }],
              stockName: [{ required: true, message: '请输入股票名称', trigger: 'blur' }],
              price: [{ required: true, type: 'number', min: 0, message: '请输入有效的价格', trigger: 'blur' }],
              quantity: [{ required: true, type: 'number', min: 1, message: '请输入有效的数量', trigger: 'blur' }]
            }" label-width="120px">
              <el-row :gutter="20">
                <el-col :span="6">
                  <el-form-item label="股票代码" prop="stockCode">
                    <el-input v-model="buyForm.stockCode" placeholder="请输入股票代码"></el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="股票名称" prop="stockName">
                    <el-input v-model="buyForm.stockName" placeholder="请输入股票名称"></el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="买入价格" prop="price">
                    <el-input-number v-model="buyForm.price" :min="0" :step="0.01" style="width: 100%" placeholder="请输入买入价格"></el-input-number>
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="买入数量" prop="quantity">
                    <el-input-number v-model="buyForm.quantity" :min="1" :step="100" style="width: 100%" placeholder="请输入买入数量"></el-input-number>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item>
                <el-button type="primary" @click="buyStock('buyForm')">买入</el-button>
                <el-button @click="$refs.buyForm.resetFields()">重置</el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 卖出操作 -->
          <div class="buy-section">
            <h3>卖出股票</h3>
            <el-form :model="sellForm" ref="sellForm" :rules="{
              stockCode: [{ required: true, message: '请输入股票代码', trigger: 'blur' }],
              stockName: [{ required: true, message: '请输入股票名称', trigger: 'blur' }],
              price: [{ required: true, type: 'number', min: 0, message: '请输入有效的价格', trigger: 'blur' }],
              quantity: [{ required: true, type: 'number', min: 1, message: '请输入有效的数量', trigger: 'blur' }]
            }" label-width="120px">
              <el-row :gutter="20">
                <el-col :span="6">
                  <el-form-item label="股票代码" prop="stockCode">
                    <el-input v-model="sellForm.stockCode" placeholder="请输入股票代码"></el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="股票名称" prop="stockName">
                    <el-input v-model="sellForm.stockName" placeholder="请输入股票名称"></el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="卖出价格" prop="price">
                    <el-input-number v-model="sellForm.price" :min="0" :step="0.01" style="width: 100%" placeholder="请输入卖出价格"></el-input-number>
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="卖出数量" prop="quantity">
                    <el-input-number v-model="sellForm.quantity" :min="1" :step="100" style="width: 100%" placeholder="请输入卖出数量"></el-input-number>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item>
                <el-button type="primary" @click="sellPosition('sellForm')">卖出</el-button>
                <el-button @click="$refs.sellForm.resetFields()">重置</el-button>
              </el-form-item>
            </el-form>
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
                <el-tag :type="getStatusType(scope.row.status)">{{ getOrderStatusText(scope.row.status) }}</el-tag>
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
                <el-tag :type="getStatusType(scope.row.status)">{{ getOrderStatusText(scope.row.status) }}</el-tag>
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
        </el-tab-pane>

        <!-- 风险预警标签页 -->
        <el-tab-pane label="风险预警" name="risk">
          <div class="risk-warning-container">
            <!-- 风险状态概览 -->
            <div class="risk-status-overview">
              <el-row :gutter="20">
                <el-col :span="6">
                  <el-card class="status-card">
                    <div class="status-content">
                      <span class="status-label">系统风险等级</span>
                      <span class="status-value" :class="getRiskLevelClass(systemRiskLevel)">{{ systemRiskLevel }}</span>
                    </div>
                  </el-card>
                </el-col>
                <el-col :span="6">
                  <el-card class="status-card">
                    <div class="status-content">
                      <span class="status-label">当前预警数量</span>
                      <span class="status-value">{{ activeWarnings }}</span>
                    </div>
                  </el-card>
                </el-col>
                <el-col :span="6">
                  <el-card class="status-card">
                    <div class="status-content">
                      <span class="status-label">最大回撤</span>
                      <span class="status-value" :class="maxDrawdown < 0 ? 'loss' : ''">{{ formatPercentage(maxDrawdown) }}</span>
                    </div>
                  </el-card>
                </el-col>
                <el-col :span="6">
                  <el-card class="status-card">
                    <div class="status-content">
                      <span class="status-label">总盈亏比</span>
                      <span class="status-value" :class="profitLossRatio > 1 ? 'profit' : 'loss'">{{ profitLossRatio.toFixed(2) }}</span>
                    </div>
                  </el-card>
                </el-col>
              </el-row>
            </div>
            
            <!-- 账户风险状态详情 -->
            <div class="account-risk-section">
              <h3>账户风险状态详情</h3>
              <el-card class="risk-card animated fadeIn" :class="{
                'risk-high': accountRisk.status === '高风险',
                'risk-medium': accountRisk.status === '中风险',
                'risk-low': accountRisk.status === '低风险'
              }">
                <template slot="header">
                  <div class="card-header">
                    <span>账户风险状态</span>
                    <el-tag :type="getRiskLevelTagType(accountRisk.status)" size="medium" class="ml-2">
                      <i class="el-icon-warning-outline mr-1"></i>{{ accountRisk.status }}
                    </el-tag>
                  </div>
                </template>
                <div class="risk-grid">
                  <div class="risk-item animated fadeInUp" style="animation-delay: 0.1s">
                    <div class="risk-header">
                      <div class="risk-label">
                        <i class="el-icon-shield mr-2"></i>保证金比例
                      </div>
                      <div class="risk-value">{{ formatNumber(accountRisk.marginRatio, 2) }}%</div>
                    </div>
                    <div class="risk-desc">当前: {{ formatNumber(accountRisk.marginRatio, 2) }}% / 预警线: {{ riskThresholds.marginWarning }}% / 平仓线: {{ riskThresholds.marginLiquidation }}%</div>
                    <el-progress 
                      :percentage="Math.min(100, accountRisk.marginRatio / riskThresholds.marginWarning * 100)" 
                      :status="getMarginRatioStatus(accountRisk.marginRatio)"
                      class="mt-2"
                      stroke-width="6"
                      :text-inside="true"
                    />
                  </div>
                  <div class="risk-item animated fadeInUp" style="animation-delay: 0.2s">
                    <div class="risk-header">
                      <div class="risk-label">
                        <i class="el-icon-minus-circle mr-2"></i>最大回撤
                      </div>
                      <div class="risk-value loss">{{ formatNumber(accountRisk.maxDrawdown, 2) }}%</div>
                    </div>
                    <div class="risk-desc">历史最大亏损百分比</div>
                    <el-progress 
                      :percentage="Math.abs(accountRisk.maxDrawdown) / 20 * 100" 
                      status="exception"
                      class="mt-2"
                      stroke-width="6"
                      :text-inside="true"
                    />
                  </div>
                  <div class="risk-item animated fadeInUp" style="animation-delay: 0.3s">
                    <div class="risk-header">
                      <div class="risk-label">
                        <i class="el-icon-data-analysis mr-2"></i>Sharpe比率
                      </div>
                      <div class="risk-value" :class="accountRisk.sharpeRatio > 1.5 ? 'profit' : accountRisk.sharpeRatio < 0.5 ? 'loss' : ''">{{ formatNumber(accountRisk.sharpeRatio, 2) }}</div>
                    </div>
                    <div class="risk-desc">风险调整后收益指标</div>
                    <div class="mt-2 sharpe-info">
                      <span class="sharpe-range">&lt; 0.5: 低</span>
                      <span class="sharpe-range">0.5-1.5: 中</span>
                      <span class="sharpe-range">&gt; 1.5: 高</span>
                    </div>
                  </div>
                  <div class="risk-item animated fadeInUp" style="animation-delay: 0.4s">
                    <div class="risk-header">
                      <div class="risk-label">
                        <i class="el-icon-sort-up mr-2"></i>波动率
                      </div>
                      <div class="risk-value" :class="accountRisk.volatility > 25 ? 'loss' : accountRisk.volatility < 15 ? 'profit' : ''">{{ formatNumber(accountRisk.volatility, 2) }}%</div>
                    </div>
                    <div class="risk-desc">收益率波动性</div>
                    <el-progress 
                      :percentage="accountRisk.volatility / 30 * 100" 
                      :status="accountRisk.volatility > 25 ? 'exception' : accountRisk.volatility < 15 ? 'success' : 'warning'"
                      class="mt-2"
                      stroke-width="6"
                      :text-inside="true"
                    />
                  </div>
                  <div class="risk-item animated fadeInUp" style="animation-delay: 0.5s">
                    <div class="risk-header">
                      <div class="risk-label">
                        <i class="el-icon-s-operation mr-2"></i>总仓位
                      </div>
                      <div class="risk-value" :class="accountRisk.positionRatio > riskThresholds.positionLimit * 0.8 ? 'loss' : ''">{{ formatNumber(accountRisk.positionRatio, 2) }}%</div>
                    </div>
                    <div class="risk-desc">当前: {{ formatNumber(accountRisk.positionRatio, 2) }}% / 上限: {{ riskThresholds.positionLimit }}%</div>
                    <el-progress 
                      :percentage="accountRisk.positionRatio / riskThresholds.positionLimit * 100" 
                      :status="accountRisk.positionRatio > riskThresholds.positionLimit * 0.8 ? 'exception' : accountRisk.positionRatio > riskThresholds.positionLimit * 0.6 ? 'warning' : 'success'"
                      class="mt-2"
                      stroke-width="6"
                      :text-inside="true"
                    />
                  </div>
                  <div class="risk-item animated fadeInUp" style="animation-delay: 0.6s">
                    <div class="risk-header">
                      <div class="risk-label">
                        <i class="el-icon-trending-up mr-2"></i>单日盈亏
                      </div>
                      <div class="risk-value" :class="accountRisk.dailyProfit > 0 ? 'profit' : 'loss'">
                        {{ accountRisk.dailyProfit > 0 ? '+' : '' }}{{ formatNumber(accountRisk.dailyProfit, 2) }}%
                      </div>
                    </div>
                    <div class="risk-desc">今日收益率</div>
                    <el-progress 
                      :percentage="Math.abs(accountRisk.dailyProfit) / 5 * 100"
                      :status="accountRisk.dailyProfit > 0 ? 'success' : 'exception'"
                      class="mt-2"
                      stroke-width="6"
                      :text-inside="true"
                    />
                  </div>
                </div>
              </el-card>
            </div>
            
            <!-- 风控指标图表 -->
            <div class="risk-indicators-section">
              <h3>风控指标走势图</h3>
              <div id="riskChart" class="chart-container"></div>
            </div>

            <!-- 风险指标图表 -->
            <div class="risk-charts-section">
              <h3>风险趋势分析</h3>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-card>
                    <div slot="header" class="clearfix">
                      <span>系统风险趋势</span>
                    </div>
                    <div id="systemRiskTrendChart" class="chart-container"></div>
                  </el-card>
                </el-col>
                <el-col :span="12">
                  <el-card>
                    <div slot="header" class="clearfix">
                      <span>资产回撤分析</span>
                    </div>
                    <div id="drawdownChart" class="chart-container"></div>
                  </el-card>
                </el-col>
              </el-row>
            </div>

            <!-- 风险预警列表 -->
            <div class="warnings-section">
              <h3>风险预警记录</h3>
              <el-table :data="riskWarnings" style="width: 100%" stripe>
                <el-table-column prop="id" label="预警ID" width="100"></el-table-column>
                <el-table-column prop="timestamp" label="预警时间" width="180"></el-table-column>
                <el-table-column prop="type" label="预警类型" width="120"></el-table-column>
                <el-table-column prop="level" label="风险等级" width="100">
                  <template slot-scope="scope">
                    <el-tag :type="getRiskLevelTagType(scope.row.level)">{{ scope.row.level }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="message" label="预警信息" show-overflow-tooltip></el-table-column>
                <el-table-column prop="status" label="处理状态" width="100">
                  <template slot-scope="scope">
                    <el-tag :type="getStatusTagType(scope.row.status)">{{ getStatusText(scope.row.status) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                  <template slot-scope="scope">
                    <el-button type="text" @click="handleWarning(scope.row)" v-if="scope.row.status === 'unhandled'">处理</el-button>
                    <el-button type="text" @click="viewWarningDetail(scope.row)">详情</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <!-- 风险阈值设置 -->
            <div class="thresholds-section">
              <h3>风险阈值设置</h3>
              <el-form :model="thresholdForm" ref="thresholdForm" :rules="thresholdRules" label-width="150px">
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="最大回撤阈值" prop="maxDrawdownThreshold">
                      <el-input-number v-model="thresholdForm.maxDrawdownThreshold" :min="0" :max="1" :step="0.01" style="width: 100%"></el-input-number>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="滑点阈值" prop="slippageThreshold">
                      <el-input-number v-model="thresholdForm.slippageThreshold" :min="0" :max="0.1" :step="0.001" style="width: 100%"></el-input-number>
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="单笔最大亏损比例" prop="singleTradeLossThreshold">
                      <el-input-number v-model="thresholdForm.singleTradeLossThreshold" :min="0" :max="1" :step="0.01" style="width: 100%"></el-input-number>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="单日最大亏损比例" prop="dailyLossThreshold">
                      <el-input-number v-model="thresholdForm.dailyLossThreshold" :min="0" :max="1" :step="0.01" style="width: 100%"></el-input-number>
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-form-item>
                  <el-button type="primary" @click="saveThresholds">保存设置</el-button>
                </el-form-item>
              </el-form>
            </div>

            <!-- 风险详情对话框 -->
            <el-dialog title="风险预警详情" :visible.sync="detailDialogVisible" width="60%">
              <div v-if="selectedWarning">
                <el-form :model="selectedWarning" label-width="120px" :inline="false">
                  <el-form-item label="预警ID">
                    {{ selectedWarning.id }}
                  </el-form-item>
                  <el-form-item label="预警时间">
                    {{ selectedWarning.timestamp }}
                  </el-form-item>
                  <el-form-item label="预警类型">
                    {{ selectedWarning.type }}
                  </el-form-item>
                  <el-form-item label="风险等级">
                    <el-tag :type="getRiskLevelTagType(selectedWarning.level)">{{ selectedWarning.level }}</el-tag>
                  </el-form-item>
                  <el-form-item label="预警信息">
                    {{ selectedWarning.message }}
                  </el-form-item>
                  <el-form-item label="关联资产" v-if="selectedWarning.relatedAsset">
                    {{ selectedWarning.relatedAsset }}
                  </el-form-item>
                  <el-form-item label="详细数据" v-if="selectedWarning.data">
                    <pre>{{ JSON.stringify(selectedWarning.data, null, 2) }}</pre>
                  </el-form-item>
                </el-form>
              </div>
              <span slot="footer" class="dialog-footer">
                <el-button @click="detailDialogVisible = false">关闭</el-button>
              </span>
            </el-dialog>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import axios from '../../utils/axios-config.js'
import * as echarts from 'echarts'

export default {
  name: 'TradeMonitor',
  data() {
    return {
      // 当前激活的标签页
      activeTab: 'trade',
      
      // 交易状态数据
      totalPositionValue: 0,
      dailyProfit: 0,
      activeOrders: 0,
      todayTrades: 0,
      
      // 风险指标数据
      cumulativeReturn: 0,
      annualVolatility: 0,
      sharpeRatio: 0,
      maxDrawdown: 0,
      riskStatus: '低风险',
      
      // 资金数据
      accountBalance: 0,
      availableFunds: 0,
      
      // 持仓数据
      positions: [],
      
      // 交易历史数据
      tradeHistory: [],
      
      // 活跃订单数据
      activeOrdersList: [],
      
      // 风险预警相关数据
      systemRiskLevel: '低',
      activeWarnings: 0,
      profitLossRatio: 0,
      
      // 账户风控数据
      accountRisk: {
        status: '低风险',
        marginRatio: 180,
        maxDrawdown: -12.5,
        sharpeRatio: 1.8,
        volatility: 15.2,
        positionRatio: 65,
        dailyProfit: 2.3
      },
      
      // 风控阈值设置
      riskThresholds: {
        marginWarning: 130,
        marginLiquidation: 100,
        positionLimit: 90,
        maxDrawdownDaily: 5
      },
      
      // 风险预警列表
      riskWarnings: [],
      
      // 风险阈值设置表单
      thresholdForm: {
        maxDrawdownThreshold: 0.1,
        slippageThreshold: 0.005,
        singleTradeLossThreshold: 0.05,
        dailyLossThreshold: 0.03
      },
      
      // 风险阈值表单验证规则
      thresholdRules: {
        maxDrawdownThreshold: [
          { required: true, message: '请输入最大回撤阈值', trigger: 'blur' },
          { type: 'number', min: 0, max: 1, message: '最大回撤阈值应在0-1之间', trigger: 'blur' }
        ],
        slippageThreshold: [
          { required: true, message: '请输入滑点阈值', trigger: 'blur' },
          { type: 'number', min: 0, max: 0.1, message: '滑点阈值应在0-0.1之间', trigger: 'blur' }
        ],
        singleTradeLossThreshold: [
          { required: true, message: '请输入单笔最大亏损比例', trigger: 'blur' },
          { type: 'number', min: 0, max: 1, message: '单笔最大亏损比例应在0-1之间', trigger: 'blur' }
        ],
        dailyLossThreshold: [
          { required: true, message: '请输入单日最大亏损比例', trigger: 'blur' },
          { type: 'number', min: 0, max: 1, message: '单日最大亏损比例应在0-1之间', trigger: 'blur' }
        ]
      },
      
      // 图表实例
      systemRiskTrendChart: null,
      drawdownChart: null,
      riskChart: null,
      
      // 对话框控制
      detailDialogVisible: false,
      selectedWarning: null,
      
      // 买入表单数据
      buyForm: {
        stockCode: '',
        stockName: '',
        price: 0,
        quantity: 0
      },
      
      // 卖出表单数据
      sellForm: {
        stockCode: '',
        stockName: '',
        price: 0,
        quantity: 0
      }
    }
  },
  mounted() {
    // 组件挂载后加载数据
    this.loadAllData()
    
    // 监听窗口大小变化，调整图表大小
    window.addEventListener('resize', this.handleResize)
    
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
    
    // 移除窗口大小变化监听
    window.removeEventListener('resize', this.handleResize)
    
    // 销毁图表实例
    if (this.systemRiskTrendChart) {
      this.systemRiskTrendChart.dispose()
    }
    if (this.drawdownChart) {
      this.drawdownChart.dispose()
    }
    if (this.riskChart) {
      this.riskChart.dispose()
    }
  },
  methods: {
    // 标签页切换处理
    handleTabClick() {
      // 当切换到风险预警标签页时，确保图表已初始化
      if (this.activeTab === 'risk' && (!this.systemRiskTrendChart || !this.drawdownChart || !this.riskChart)) {
        this.initCharts()
      }
    },
    
    // 加载所有数据
    async loadAllData() {
      try {
        // 同时加载多个API的数据
        const [positionsResponse, tradeHistoryResponse, accountResponse, activeOrdersResponse, riskDataResponse, riskWarningsResponse, thresholdsResponse] = await Promise.all([
          axios.get('/api/positions'),
          axios.get('/api/trade/history', {
            params: {
              start_date: new Date().toISOString().split('T')[0],
              end_date: new Date().toISOString().split('T')[0]
            }
          }),
          axios.get('/api/account'),
          axios.get('/api/orders/active'),
          axios.get('/api/risk/data'),
          axios.get('/api/notifications'),
          axios.get('/api/risk/thresholds')
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
          // 从账户数据中获取风险指标
          if (accountResponse.maxDrawdown !== undefined) {
            this.maxDrawdown = accountResponse.maxDrawdown
          }
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
        
        // 处理风控数据
        if (riskDataResponse && riskDataResponse.riskData) {
          this.riskStatus = riskDataResponse.riskData.status || '低风险'
          this.annualVolatility = riskDataResponse.riskData.volatility || 0
          this.sharpeRatio = riskDataResponse.riskData.sharpeRatio || 0
          if (riskDataResponse.riskData.maxDrawdown !== undefined) {
            this.maxDrawdown = riskDataResponse.riskData.maxDrawdown
          }
        }
        
        // 处理风险预警列表数据
        if (riskWarningsResponse) {
          const data = riskWarningsResponse.data || riskWarningsResponse
          // 过滤出风险相关的通知
          this.riskWarnings = data.filter(notification => 
            notification.type === 'risk' || notification.type === 'warning'
          )
          // 确保即使API返回空数据，也有内容显示
          if (!this.riskWarnings || this.riskWarnings.length === 0) {
            this.generateMockRiskWarnings()
          }
          // 计算当前活跃预警数量
          this.activeWarnings = this.riskWarnings.filter(warning => warning.status === 'unhandled').length
        } else {
          this.generateMockRiskWarnings()
        }
        
        // 处理风险阈值设置
        if (thresholdsResponse) {
          const data = thresholdsResponse.data || thresholdsResponse
          this.thresholdForm = {
            maxDrawdownThreshold: data.maxDrawdownThreshold || 0.1,
            slippageThreshold: data.slippageThreshold || 0.005,
            singleTradeLossThreshold: data.singleTradeLossThreshold || 0.05,
            dailyLossThreshold: data.dailyLossThreshold || 0.03
          }
        }
        
        // 计算交易统计
        this.calculateTradeStats()
        // 计算累计收益率
        this.calculateCumulativeReturn()
        
        // 如果是风险标签页，确保图表数据已更新
        if (this.activeTab === 'risk') {
          this.updateCharts()
        }
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
        this.calculateCumulativeReturn()
        
        // 生成风险预警相关的模拟数据
        this.generateMockRiskData()
        this.generateMockRiskWarnings()
        
        // 设置默认风险指标
        this.annualVolatility = 15.0
        this.sharpeRatio = 1.8
        this.maxDrawdown = -8.5
        this.riskStatus = '低风险'
        
        this.$message.error('数据加载失败，使用模拟数据')
      }
    },
    
    // 刷新数据
    refreshData() {
      this.loadAllData()
      this.$message.success('数据已刷新')
    },
    
    // 初始化图表
    initCharts() {
      try {
        // 系统风险趋势图
        this.systemRiskTrendChart = echarts.init(document.getElementById('systemRiskTrendChart'))
        this.systemRiskTrendChart.setOption({
          title: {
            text: '',
          },
          tooltip: {
            trigger: 'axis',
            formatter: function(params) {
              return params[0].name + '<br/>' + params[0].seriesName + ': ' + params[0].value
            }
          },
          xAxis: {
            type: 'category',
            data: []
          },
          yAxis: {
            type: 'value',
            name: '风险等级',
            min: 0,
            max: 5,
            interval: 1,
            axisLabel: {
              formatter: function(value) {
                const levels = ['无', '低', '中', '高', '严重', '极高']
                return levels[value] || value
              }
            }
          },
          series: [
            {
              name: '系统风险等级',
              type: 'line',
              smooth: true,
              data: [],
              itemStyle: {
                color: '#e74c3c'
              },
              lineStyle: {
                width: 2
              },
              markLine: {
                silent: true,
                lineStyle: {
                  color: '#999'
                },
                data: [
                  {
                    yAxis: 3,
                    label: {
                      formatter: '风险警戒线',
                      position: 'insideEndTop'
                    }
                  }
                ]
              }
            }
          ]
        })
        
        // 资产回撤分析图
        this.drawdownChart = echarts.init(document.getElementById('drawdownChart'))
        this.drawdownChart.setOption({
          title: {
            text: '',
          },
          tooltip: {
            trigger: 'axis',
            formatter: function(params) {
              return params[0].name + '<br/>' + params[0].seriesName + ': ' + (params[0].value * 100).toFixed(2) + '%'
            }
          },
          xAxis: {
            type: 'category',
            data: []
          },
          yAxis: {
            type: 'value',
            name: '回撤比例',
            axisLabel: {
              formatter: '{value}%'
            }
          },
          series: [
            {
              name: '最大回撤',
              type: 'line',
              smooth: true,
              data: [],
              itemStyle: {
                color: '#3498db'
              },
              areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  {
                    offset: 0,
                    color: 'rgba(52, 152, 219, 0.3)'
                  },
                  {
                    offset: 1,
                    color: 'rgba(52, 152, 219, 0.1)'
                  }
                ])
              },
              lineStyle: {
                width: 2
              }
            }
          ]
        })
        
        // 风控指标走势图
        this.riskChart = echarts.init(document.getElementById('riskChart'))
        this.riskChart.setOption({
          title: {
            text: '',
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'cross'
            }
          },
          legend: {
            data: ['保证金比例', '持仓比例', '日收益']
          },
          xAxis: {
            type: 'category',
            data: []
          },
          yAxis: [
            {
              type: 'value',
              name: '比例(%)',
              position: 'left',
              axisLabel: {
                formatter: '{value}%'
              }
            },
            {
              type: 'value',
              name: '收益(%)',
              position: 'right',
              axisLabel: {
                formatter: '{value}%'
              }
            }
          ],
          series: [
            {
              name: '保证金比例',
              type: 'line',
              data: [],
              yAxisIndex: 0,
              itemStyle: {
                color: '#67c23a'
              },
              smooth: true
            },
            {
              name: '持仓比例',
              type: 'line',
              data: [],
              yAxisIndex: 0,
              itemStyle: {
                color: '#e6a23c'
              },
              smooth: true
            },
            {
              name: '日收益',
              type: 'line',
              data: [],
              yAxisIndex: 1,
              itemStyle: {
                color: '#f56c6c'
              },
              smooth: true
            }
          ]
        })
        
        // 更新图表数据
        this.updateCharts()
      } catch (error) {
        console.error('图表初始化失败:', error)
      }
    },
    
    // 更新图表数据
    updateCharts() {
      try {
        // 生成模拟趋势数据
        const mockTrendData = this.generateMockTrendData()
        
        // 更新系统风险趋势图
        if (this.systemRiskTrendChart) {
          this.systemRiskTrendChart.setOption({
            xAxis: {
              data: mockTrendData.timePoints || []
            },
            series: [
              {
                data: mockTrendData.riskLevels || []
              }
            ]
          })
        }
        
        // 更新回撤分析图
        if (this.drawdownChart) {
          this.drawdownChart.setOption({
            xAxis: {
              data: mockTrendData.timePoints || []
            },
            series: [
              {
                data: mockTrendData.drawdowns || []
              }
            ]
          })
        }
        
        // 更新风控指标走势图
        if (this.riskChart) {
          this.riskChart.setOption({
            xAxis: {
              data: mockTrendData.timePoints || []
            },
            series: [
              {
                data: mockTrendData.riskMetrics.marginRatios || []
              },
              {
                data: mockTrendData.riskMetrics.positionRatios || []
              },
              {
                data: mockTrendData.riskMetrics.dailyProfits || []
              }
            ]
          })
        }
      } catch (error) {
        console.warn('更新图表失败:', error)
      }
    },
    
    // 处理窗口大小变化
    handleResize() {
      if (this.systemRiskTrendChart) {
        this.systemRiskTrendChart.resize()
      }
      if (this.drawdownChart) {
        this.drawdownChart.resize()
      }
      if (this.riskChart) {
        this.riskChart.resize()
      }
    },
    
    // 计算持仓统计数据
    calculatePositionStats() {
      let totalValue = 0
      let totalProfit = 0
      
      this.positions.forEach(position => {
        const marketValue = position.quantity * position.current_price
        const profit = marketValue - (position.quantity * position.avg_price)
        const profitRate = profit / (position.quantity * position.avg_price)
        
        position.market_value = marketValue
        position.profit = profit
        position.profit_rate = profitRate
        
        totalValue += marketValue
        totalProfit += profit
      })
      
      this.totalPositionValue = totalValue
      this.dailyProfit = totalProfit
    },
    
    // 生成模拟风险数据
    generateMockRiskData() {
      this.systemRiskLevel = '低'
      this.activeWarnings = 3
      this.profitLossRatio = 1.8
      
      this.accountRisk = {
        status: '低风险',
        marginRatio: 180,
        maxDrawdown: -12.5,
        sharpeRatio: 1.8,
        volatility: 15.2,
        positionRatio: 65,
        dailyProfit: 2.3
      }
    },
    
    // 生成模拟风险预警数据
    generateMockRiskWarnings() {
      const now = new Date()
      const getDateStr = (daysOffset = 0) => {
        const date = new Date(now)
        date.setDate(date.getDate() - daysOffset)
        return date.toLocaleString('zh-CN')
      }
      
      this.riskWarnings = [
        {
          id: 'RW20240615001',
          timestamp: getDateStr(),
          type: 'position',
          level: '高风险',
          message: '股票600036持仓比例超过40%',
          relatedAsset: '600036',
          data: {
            symbol: '600036',
            name: '招商银行',
            positionRatio: 42.5,
            threshold: 40
          },
          status: 'unhandled'
        },
        {
          id: 'RW20240615002',
          timestamp: getDateStr(1),
          type: 'drawdown',
          level: '中风险',
          message: '当日回撤达到3.8%，接近预警阈值',
          data: {
            drawdown: 3.8,
            warningThreshold: 4,
            liquidationThreshold: 5
          },
          status: 'unhandled'
        },
        {
          id: 'RW20240614001',
          timestamp: getDateStr(2),
          type: 'volatility',
          level: '低风险',
          message: '组合波动率异常升高',
          data: {
            volatility: 22.5,
            normalLevel: 15
          },
          status: 'handled'
        },
        {
          id: 'RW20240613001',
          timestamp: getDateStr(3),
          type: 'market',
          level: '高风险',
          message: '市场大幅波动，建议减仓应对',
          data: {
            marketIndex: '上证指数',
            change: -2.8
          },
          status: 'handled'
        },
        {
          id: 'RW20240612001',
          timestamp: getDateStr(4),
          type: 'margin',
          level: '中风险',
          message: '保证金比例接近预警线',
          data: {
            marginRatio: 135,
            warningLine: 130
          },
          status: 'handled'
        }
      ]
      
      // 计算当前活跃预警数量
      this.activeWarnings = this.riskWarnings.filter(warning => warning.status === 'unhandled').length
    },
    
    // 生成模拟趋势数据
    generateMockTrendData() {
      const timePoints = []
      const riskLevels = []
      const drawdowns = []
      const marginRatios = []
      const positionRatios = []
      const dailyProfits = []
      
      // 生成过去30天的时间点
      const now = new Date()
      for (let i = 29; i >= 0; i--) {
        const date = new Date(now)
        date.setDate(date.getDate() - i)
        timePoints.push(date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }))
      }
      
      // 生成模拟的风险等级数据 (0-5)
      let baseRiskLevel = 2
      for (let i = 0; i < 30; i++) {
        // 添加一些随机波动
        const fluctuation = (Math.random() - 0.5) * 0.5
        baseRiskLevel = Math.max(0, Math.min(5, baseRiskLevel + fluctuation))
        
        // 在某些点添加一些异常值以模拟真实情况
        if (i === 10 || i === 20) {
          baseRiskLevel += (Math.random() * 2) // 增加风险
        } else if (i === 15 || i === 25) {
          baseRiskLevel -= (Math.random() * 2) // 降低风险
        }
        
        riskLevels.push(Math.round(baseRiskLevel))
      }
      
      // 生成模拟的最大回撤数据 (-0.05 到 -0.2)
      let baseDrawdown = -0.1
      for (let i = 0; i < 30; i++) {
        const fluctuation = (Math.random() - 0.5) * 0.02
        baseDrawdown = Math.max(-0.2, Math.min(-0.05, baseDrawdown + fluctuation))
        drawdowns.push(baseDrawdown)
      }
      
      // 生成模拟的保证金比例数据 (100-250%)
      let baseMarginRatio = 180
      for (let i = 0; i < 30; i++) {
        const fluctuation = (Math.random() - 0.5) * 10
        baseMarginRatio = Math.max(100, Math.min(250, baseMarginRatio + fluctuation))
        marginRatios.push(baseMarginRatio)
      }
      
      // 生成模拟的持仓比例数据 (30-90%)
      let basePositionRatio = 65
      for (let i = 0; i < 30; i++) {
        const fluctuation = (Math.random() - 0.5) * 5
        basePositionRatio = Math.max(30, Math.min(90, basePositionRatio + fluctuation))
        positionRatios.push(basePositionRatio)
      }
      
      // 生成模拟的日收益率数据 (-3% 到 3%)
      let baseDailyProfit = 0
      for (let i = 0; i < 30; i++) {
        const fluctuation = (Math.random() - 0.5) * 2
        baseDailyProfit = Math.max(-3, Math.min(3, baseDailyProfit + fluctuation))
        dailyProfits.push(baseDailyProfit)
      }
      
      return {
        timePoints,
        riskLevels,
        drawdowns,
        riskMetrics: {
          marginRatios,
          positionRatios,
          dailyProfits
        }
      }
    },
    
    // 格式化数字
    formatNumber(value, decimals = 2) {
      if (value === null || value === undefined || isNaN(value)) {
        return '0.00'
      }
      return Number(value).toFixed(decimals)
    },
    
    // 格式化百分比
    formatPercentage(value) {
      if (value === null || value === undefined || isNaN(value)) {
        return '0.00%'
      }
      return Number(value).toFixed(2) + '%'
    },
    
    // 获取风险等级的CSS类
    getRiskLevelClass(level) {
      switch(level) {
        case '高':
        case '高风险':
          return 'risk-high'
        case '中':
        case '中风险':
          return 'risk-medium'
        case '低':
        case '低风险':
          return 'risk-low'
        default:
          return ''
      }
    },
    
    // 获取风险等级标签类型
    getRiskLevelTagType(level) {
      switch(level) {
        case '高':
        case '高风险':
          return 'danger'
        case '中':
        case '中风险':
          return 'warning'
        case '低':
        case '低风险':
          return 'success'
        default:
          return 'info'
      }
    },
    
    // 获取状态标签类型
    getStatusTagType(status) {
      switch(status) {
        case 'unhandled':
          return 'danger'
        case 'handling':
          return 'warning'
        case 'handled':
          return 'success'
        default:
          return 'info'
      }
    },
    
    // 获取状态文本
    getStatusText(status) {
      switch(status) {
        case 'unhandled':
          return '未处理'
        case 'handling':
          return '处理中'
        case 'handled':
          return '已处理'
        default:
          return status
      }
    },
    
    // 处理风险预警
    handleWarning(warning) {
      this.$confirm('确定要标记此风险预警为已处理吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 找到对应的预警并更新状态
        const index = this.riskWarnings.findIndex(item => item.id === warning.id)
        if (index !== -1) {
          this.riskWarnings[index].status = 'handled'
          this.activeWarnings--
          this.$message({ type: 'success', message: '风险预警已标记为已处理' })
        }
      }).catch(() => {
        this.$message({ type: 'info', message: '已取消操作' })
      })
    },
    
    // 查看风险预警详情
    viewWarningDetail(warning) {
      this.selectedWarning = { ...warning }
      this.detailDialogVisible = true
    },
    
    // 获取保证金比例状态
    getMarginRatioStatus(marginRatio) {
      if (marginRatio < this.riskThresholds.marginLiquidation) {
        return 'exception'
      } else if (marginRatio < this.riskThresholds.marginWarning) {
        return 'warning'
      } else {
        return 'success'
      }
    },
    
    // 保存风险阈值设置
    saveThresholds() {
      this.$refs.thresholdForm.validate((valid) => {
        if (valid) {
          // 模拟API调用
          // axios.post('/api/risk/thresholds', this.thresholdForm)
          //   .then(() => {
          //     this.$message({ type: 'success', message: '风险阈值设置已保存' })
          //   })
          //   .catch(() => {
          //     this.$message({ type: 'error', message: '保存失败，请重试' })
          //   })
          
          // 模拟成功保存
          this.$message({ type: 'success', message: '风险阈值设置已保存' })
        } else {
          this.$message({ type: 'error', message: '请检查输入的阈值参数' })
          return false
        }
      })
    },
    
    // 计算交易统计数据
    calculateTradeStats() {
      this.todayTrades = this.tradeHistory.length
      this.activeOrders = this.activeOrdersList.length
    },
    
    // 计算累计收益率
    calculateCumulativeReturn() {
      // 根据持仓和账户资金计算累计收益率
      // 假设初始资金为账户余额和持仓市值之和减去当前盈亏
      const totalEquity = this.accountBalance + this.totalPositionValue
      const initialEquity = totalEquity - this.dailyProfit // 简化计算，实际应该基于历史数据
      
      if (initialEquity > 0) {
        this.cumulativeReturn = ((totalEquity - initialEquity) / initialEquity) * 100
      } else {
        this.cumulativeReturn = 0
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
    getOrderStatusText(status) {
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
    
    // 获取模拟交易历史数据（包含手续费）
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
          fee: 16.80,
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
          fee: 1.63,
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
          fee: 0.63,
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
          fee: 0.71,
          status: 'pending'
        }
      ]
    },
    
    // 卖出股票
    sellPosition(formName) {
      // 验证卖出表单
      const form = this.$refs[formName]
      if (!form) {
        this.$message({ type: 'error', message: '表单引用不存在' })
        return
      }
      
      form.validate((valid) => {
        if (!valid) {
          this.$message({ type: 'error', message: '请填写完整的卖出信息' })
          return false
        }
        
        // 检查是否持有该股票
        const position = this.positions.find(p => p.symbol === this.sellForm.stockCode)
        if (!position) {
          this.$message({ type: 'error', message: '您未持有该股票' })
          return false
        }
        
        // 检查卖出数量是否超过持有数量
        if (this.sellForm.quantity > position.quantity) {
          this.$message({ type: 'error', message: '卖出数量不能超过持有数量' })
          return false
        }
        
        // 显示确认对话框
        this.$confirm(`确定要卖出 ${this.sellForm.quantity} 股 ${this.sellForm.stockName} (${this.sellForm.stockCode}) 吗？价格: ${this.sellForm.price}`, '确认卖出', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 创建卖出交易记录
        const now = new Date().toISOString()
        const tradeRecord = {
          timestamp: now,
          symbol: this.sellForm.stockCode,
          name: this.sellForm.stockName,
          side: 'sell',
          quantity: this.sellForm.quantity,
          price: this.sellForm.price,
          amount: this.sellForm.quantity * this.sellForm.price,
          fee: (this.sellForm.quantity * this.sellForm.price) * 0.001, // 模拟手续费
          status: 'filled'
        }

        // 更新交易历史
        this.tradeHistory.unshift(tradeRecord)

        // 更新持仓
        const index = this.positions.findIndex(p => p.symbol === this.sellForm.stockCode)
        if (index !== -1) {
          if (this.sellForm.quantity === this.positions[index].quantity) {
            // 全部卖出，移除持仓
            this.positions.splice(index, 1)
          } else {
            // 部分卖出，更新持仓数量
            this.positions[index].quantity -= this.sellForm.quantity
            this.positions[index].cost_basis = (this.positions[index].cost_basis * this.positions[index].quantity) / this.positions[index].quantity
            this.positions[index].profit = this.positions[index].quantity * (this.positions[index].current_price - this.positions[index].cost_basis)
            this.positions[index].profit_rate = (this.positions[index].current_price - this.positions[index].cost_basis) / this.positions[index].cost_basis
          }
        }

        // 更新账户资金（现金增加）
        this.accountBalance += tradeRecord.amount - tradeRecord.fee
        this.availableFunds += tradeRecord.amount - tradeRecord.fee
        
        // 重置表单
        form.resetFields()

        // 重新计算统计数据
        this.calculatePositionStats()
        this.calculateTradeStats()
        this.calculateCumulativeReturn()

        // 模拟生成风险预警（如果触发阈值）
        this.checkRiskWarnings()

        this.$message({ type: 'success', message: '卖出成功' })
      }).catch(() => {
        this.$message({ type: 'info', message: '已取消卖出操作' })
      })
      })
    },

    // 买入股票
    buyStock(formName) {
        // 验证买入表单
        const form = this.$refs[formName]
        if (!form) {
          this.$message({ type: 'error', message: '表单引用不存在' })
          return
        }
        
        form.validate((valid) => {
          if (!valid) {
            this.$message({ type: 'error', message: '请填写完整的买入信息' })
            return false
          }
          
          // 验证资金是否充足
          const totalAmount = this.buyForm.quantity * this.buyForm.price
          const fee = totalAmount * 0.001
          if (totalAmount + fee > this.availableFunds) {
            this.$message({ type: 'error', message: '可用资金不足' })
            return false
          }
          
          // 显示确认对话框
          this.$confirm(`确定要买入 ${this.buyForm.quantity} 股 ${this.buyForm.stockName} (${this.buyForm.stockCode}) 吗？价格: ${this.buyForm.price}`, '确认买入', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'success'
          }).then(() => {
            // 创建买入交易记录
            const now = new Date().toISOString()
            const tradeRecord = {
              timestamp: now,
              symbol: this.buyForm.symbol,
              name: this.buyForm.name || this.buyForm.symbol,
              side: 'buy',
              quantity: this.buyForm.quantity,
              price: this.buyForm.price,
              amount: totalAmount,
              fee: fee,
              status: 'filled'
            }
            
            // 更新交易历史
            this.tradeHistory.unshift(tradeRecord)
            
            // 添加新持仓
            this.positions.push({
              symbol: this.buyForm.symbol,
              name: this.buyForm.name || this.buyForm.symbol,
              quantity: this.buyForm.quantity,
              avg_price: this.buyForm.price,
              current_price: this.buyForm.price, // 假设买入后价格不变
              market_value: totalAmount,
              profit: 0,
              profit_rate: 0
            })
            
            // 更新账户资金（现金减少）
            this.accountBalance -= totalAmount + fee
            this.availableFunds -= totalAmount + fee
            
            // 重新计算统计数据
            this.calculatePositionStats()
            this.calculateTradeStats()
            this.calculateCumulativeReturn()
            
            // 模拟生成风险预警（如果触发阈值）
            this.checkRiskWarnings()
            
            // 清空买入表单
            form.resetFields()
            
            this.$message({ type: 'success', message: '买入成功' })
          }).catch(() => {
            this.$message({ type: 'info', message: '已取消买入操作' })
          })
          
          return true
        })
      },

    // 检查风险预警
    checkRiskWarnings() {
      // 计算当前持仓比例
      const totalEquity = this.accountBalance + this.totalPositionValue
      const positionRatio = totalEquity > 0 ? (this.totalPositionValue / totalEquity) * 100 : 0
      
      // 检查单只股票持仓比例
      this.positions.forEach(position => {
        const stockRatio = this.totalPositionValue > 0 ? (position.market_value / this.totalPositionValue) * 100 : 0
        
        // 如果单只股票持仓比例超过40%，生成风险预警
        if (stockRatio > 40) {
          const now = new Date()
          const warning = {
            id: `RW${now.getTime()}`,
            timestamp: now.toLocaleString('zh-CN'),
            type: 'risk',
            level: '高风险',
            message: `股票${position.symbol}持仓比例超过40%`,
            relatedAsset: position.symbol,
            data: {
              symbol: position.symbol,
              name: position.name,
              positionRatio: stockRatio.toFixed(2),
              threshold: 40
            },
            status: 'unhandled'
          }
          
          // 添加新预警（避免重复）
          if (!this.riskWarnings.some(w => w.relatedAsset === position.symbol && w.status === 'unhandled')) {
            this.riskWarnings.unshift(warning)
            this.activeWarnings++
          }
        }
      })
      
      // 检查总持仓比例
      if (positionRatio > 90) {
        const now = new Date()
        const warning = {
          id: `RW${now.getTime()}`,
          timestamp: now.toLocaleString('zh-CN'),
          type: 'risk',
          level: '高风险',
          message: `总持仓比例超过90%`,
          data: {
            positionRatio: positionRatio.toFixed(2),
            threshold: 90
          },
          status: 'unhandled'
        }
        
        // 添加新预警（避免重复）
        if (!this.riskWarnings.some(w => w.type === 'risk' && w.message.includes('总持仓比例') && w.status === 'unhandled')) {
          this.riskWarnings.unshift(warning)
          this.activeWarnings++
        }
      }
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

.risk-low {
  color: #67c23a !important;
}

.risk-medium {
  color: #e6a23c !important;
}

.risk-high {
  color: #f56c6c !important;
}

/* 图表容器样式 */
.chart-container {
  width: 100%;
  height: 400px;
  margin: 10px 0;
}

/* 风险预警相关样式 */
.risk-warning-container {
  padding: 20px 0;
}

.risk-status-overview {
  margin-bottom: 30px;
}

.account-risk-section,
.risk-indicators-section,
.risk-charts-section,
.warnings-section,
.thresholds-section {
  margin-bottom: 30px;
}

/* 风险卡片动画效果 */
.risk-card {
  transition: all 0.3s ease;
}

.risk-card.risk-high {
  border-color: #f56c6c;
  box-shadow: 0 2px 8px rgba(245, 108, 108, 0.2);
}

.risk-card.risk-medium {
  border-color: #e6a23c;
  box-shadow: 0 2px 8px rgba(230, 162, 60, 0.2);
}

.risk-card.risk-low {
  border-color: #67c23a;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.2);
}

.risk-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.risk-item {
  padding: 15px;
  background-color: #fafafa;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.risk-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.risk-label {
  font-size: 14px;
  color: #606266;
}

.risk-value {
  font-size: 18px;
  font-weight: bold;
}

.risk-desc {
  font-size: 12px;
  color: #909399;
  margin-bottom: 10px;
}

/* Sharpe比率显示 */
.sharpe-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.sharpe-range {
  color: #909399;
}

/* 买入表单样式 */
.buy-section {
  margin-bottom: 30px;
  padding: 20px;
  background-color: #fafafa;
  border-radius: 4px;
}

/* 动画效果 */
.animated {
  animation-duration: 0.5s;
  animation-fill-mode: both;
}

.fadeIn {
  animation-name: fadeIn;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.fadeInUp {
  animation-name: fadeInUp;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translate3d(0, 10px, 0);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0);
  }
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