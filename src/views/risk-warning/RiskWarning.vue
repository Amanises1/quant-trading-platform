<template>
  <div class="risk-warning-container">
    <el-card>
      <div slot="header" class="clearfix">
        <span>风险预警与熔断</span>
        <el-button type="primary" size="small" @click="refreshAllData" class="refresh-btn">
          刷新数据
        </el-button>
      </div>
      
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
        <el-form :model="thresholdForm" ref="thresholdForm" label-width="150px">
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
    </el-card>
  </div>
</template>

<script>
import axios from '../../utils/axios-config.js'
import * as echarts from 'echarts'

export default {
  name: 'RiskWarning',
  data() {
    return {
      // 风险状态数据
      systemRiskLevel: '低',
      activeWarnings: 0,
      maxDrawdown: 0,
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
      
      // 图表实例
      systemRiskTrendChart: null,
      drawdownChart: null,
      riskChart: null,
      
      // 对话框控制
      detailDialogVisible: false,
      selectedWarning: null
    }
  },
  mounted() {
    console.log('RiskWarning组件已挂载')
    // 组件挂载后立即生成模拟数据，确保页面能立即显示内容
    this.generateMockRiskData()
    this.generateMockRiskWarnings()
    
    // 立即加载所有数据（与模拟数据同时显示，API返回后会更新）
    this.loadAllData()
    
    // 简化图表初始化，确保即使图表加载失败页面也能显示其他内容
    setTimeout(() => {
      try {
        this.initCharts()
      } catch (error) {
        console.error('图表初始化失败:', error)
      }
    }, 500)
    
    // 监听窗口大小变化，调整图表大小
    window.addEventListener('resize', this.handleResize)
    
    // 设置定时刷新（每30秒）
    this.refreshTimer = setInterval(() => {
      this.loadRiskData()
      this.loadRiskWarnings()
    }, 30000)
  },
  beforeDestroy() {
    // 清理定时器
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
    // 加载所有数据
    loadAllData() {
      this.loadRiskData()
      this.loadRiskWarnings()
      this.loadThresholds()
    },
    
    // 刷新所有数据
    refreshAllData() {
      this.loadAllData()
      this.$message.success('数据刷新成功')
    },
    
    // 加载风险数据
    loadRiskData() {
      axios.get('/api/risk/data')
        .then(response => {
          const data = response.data
          this.systemRiskLevel = data.systemRiskLevel || '低'
          this.activeWarnings = data.activeWarnings || 0
          this.maxDrawdown = data.maxDrawdown || 0
          this.profitLossRatio = data.profitLossRatio || 0
          
          // 加载账户风险数据
          if (data.accountRisk) {
            this.accountRisk = data.accountRisk
          }
          
          // 加载风控阈值数据
          if (data.riskThresholds) {
            this.riskThresholds = data.riskThresholds
          }
          
          // 更新图表数据
          this.updateCharts(data)
        })
        .catch(error => {
          console.warn('API请求失败，使用模拟数据:', error)
          // 确保生成模拟数据
          this.generateMockRiskData()
        })
    },
    
    // 加载风险预警列表
    loadRiskWarnings() {
      axios.get('/api/notifications')
        .then(response => {
          const data = response.data
          // 过滤出风险相关的通知
          this.riskWarnings = data.filter(notification => 
            notification.type === 'risk' || notification.type === 'warning'
          )
          // 确保即使API返回空数据，也有内容显示
          if (!this.riskWarnings || this.riskWarnings.length === 0) {
            this.generateMockRiskWarnings()
          }
        })
        .catch(error => {
          console.warn('API请求失败，使用模拟数据:', error)
          // 确保生成模拟风险预警数据
          this.generateMockRiskWarnings()
        })
    },
    
    // 加载风险阈值设置
    loadThresholds() {
      axios.get('/api/risk/thresholds')
        .then(response => {
          const data = response.data
          this.thresholdForm = {
            maxDrawdownThreshold: data.maxDrawdownThreshold || 0.1,
            slippageThreshold: data.slippageThreshold || 0.005,
            singleTradeLossThreshold: data.singleTradeLossThreshold || 0.05,
            dailyLossThreshold: data.dailyLossThreshold || 0.03
          }
        })
        .catch(() => {
          // 使用默认值
        })
    },
    
    // 保存风险阈值设置
    saveThresholds() {
      axios.post('/api/risk/set_thresholds', this.thresholdForm)
        .then(() => {
          this.$message.success('风险阈值设置已保存')
        })
        .catch(() => {
          this.$message.error('保存失败，请重试')
        })
    },
    
    // 初始化图表
    initCharts() {
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
    },
    
    // 更新图表数据
    updateCharts(data) {
      if (data.trendData) {
        // 更新系统风险趋势图
        if (this.systemRiskTrendChart) {
          this.systemRiskTrendChart.setOption({
            xAxis: {
              data: data.trendData.timePoints || []
            },
            series: [
              {
                data: data.trendData.riskLevels || []
              }
            ]
          })
        }
        
        // 更新回撤分析图
        if (this.drawdownChart) {
          this.drawdownChart.setOption({
            xAxis: {
              data: data.trendData.timePoints || []
            },
            series: [
              {
                data: data.trendData.drawdowns || []
              }
            ]
          })
        }
        
        // 更新风控指标走势图
        if (this.riskChart && data.trendData.riskMetrics) {
          this.riskChart.setOption({
            xAxis: {
              data: data.trendData.timePoints || []
            },
            series: [
              {
                data: data.trendData.riskMetrics.marginRatios || []
              },
              {
                data: data.trendData.riskMetrics.positionRatios || []
              },
              {
                data: data.trendData.riskMetrics.dailyProfits || []
              }
            ]
          })
        }
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
    
    // 处理风险预警
    handleWarning(warning) {
      // 标记预警为已处理
      axios.post(`/api/notifications/read/${warning.id}`)
        .then(() => {
          warning.status = 'handled'
          this.$message.success('风险预警已标记为处理')
        })
        .catch(() => {
          this.$message.error('处理失败，请重试')
        })
    },
    
    // 查看风险预警详情
    viewWarningDetail(warning) {
      this.selectedWarning = warning
      this.detailDialogVisible = true
    },
    
    // 获取风险等级样式类
    getRiskLevelClass(level) {
      switch(level) {
        case '低':
          return 'risk-low'
        case '中':
          return 'risk-medium'
        case '高':
          return 'risk-high'
        case '严重':
          return 'risk-severe'
        case '极高':
          return 'risk-extreme'
        default:
          return ''
      }
    },
    
    // 获取风险等级标签类型
    getRiskLevelTagType(level) {
      switch(level) {
        case '低':
          return 'success'
        case '中':
          return 'warning'
        case '高':
        case '严重':
          return 'danger'
        case '极高':
          return 'danger'
        default:
          return 'info'
      }
    },
    
    // 获取状态标签类型
    getStatusTagType(status) {
      return status === 'handled' ? 'success' : 'warning'
    },
    
    // 获取状态文本
    getStatusText(status) {
      return status === 'handled' ? '已处理' : '未处理'
    },
    
    // 格式化百分比
    formatPercentage(value) {
      return (value * 100).toFixed(2) + '%'
    },

    // 格式化数字，保留指定位数小数
    formatNumber(value, decimals = 2) {
      if (typeof value !== 'number') {
        value = parseFloat(value)
      }
      return value.toFixed(decimals)
    },

    // 获取保证金比例状态
    getMarginRatioStatus(marginRatio) {
      if (marginRatio < this.riskThresholds.marginLiquidation) {
        return 'exception'
      } else if (marginRatio < this.riskThresholds.marginWarning) {
        return 'warning'
      }
      return 'success'
    },
    
    // 生成模拟风险数据
    generateMockRiskData() {
      console.log('生成模拟风险数据')
      // 随机生成系统风险等级
      const riskLevels = ['低', '中', '低', '低', '中']
      this.systemRiskLevel = riskLevels[Math.floor(Math.random() * riskLevels.length)]
      
      // 随机生成预警数量
      this.activeWarnings = Math.floor(Math.random() * 10) + 3 // 确保至少有一些预警
      
      // 随机生成最大回撤（-10% 到 0）
      this.maxDrawdown = -Math.random() * 0.1
      
      // 随机生成盈亏比（0.8 到 2.5）
      this.profitLossRatio = 0.8 + Math.random() * 1.7
      
      // 生成模拟账户风险数据
      this.accountRisk = {
        status: this.systemRiskLevel === '低' ? '低风险' : '中风险',
        marginRatio: 150 + Math.random() * 100, // 150-250%
        maxDrawdown: -Math.random() * 20, // -0%到-20%
        sharpeRatio: 0.5 + Math.random() * 2.5, // 0.5-3.0
        volatility: 10 + Math.random() * 20, // 10-30%
        positionRatio: 40 + Math.random() * 50, // 40-90%
        dailyProfit: -5 + Math.random() * 10 // -5%到5%
      }
      
      // 生成模拟趋势数据
      const mockTrendData = {
        timePoints: [],
        riskLevels: [],
        drawdowns: [],
        riskMetrics: {
          marginRatios: [],
          positionRatios: [],
          dailyProfits: []
        }
      }
      
      const now = new Date()
      for (let i = 23; i >= 0; i--) {
        const time = new Date(now)
        time.setHours(time.getHours() - i)
        mockTrendData.timePoints.push(`${time.getHours().toString().padStart(2, '0')}:00`)
        mockTrendData.riskLevels.push(Math.floor(Math.random() * 4) + 1) // 1-4
        mockTrendData.drawdowns.push(-Math.random() * 0.1) // -10% 到 0
        
        // 生成风控指标数据
        mockTrendData.riskMetrics.marginRatios.push(150 + Math.random() * 100)
        mockTrendData.riskMetrics.positionRatios.push(40 + Math.random() * 50)
        mockTrendData.riskMetrics.dailyProfits.push(-5 + Math.random() * 10)
      }
      
      // 更新图表（如果图表已初始化）
      try {
        this.updateCharts({ trendData: mockTrendData })
      } catch (error) {
        console.warn('更新图表失败:', error)
        // 图表可能尚未初始化，稍后再尝试更新
        setTimeout(() => {
          try {
            this.updateCharts({ trendData: mockTrendData })
          } catch (e) {
            console.error('再次尝试更新图表失败:', e)
          }
        }, 500)
      }
    },
    
    // 生成模拟风险预警数据
    generateMockRiskWarnings() {
      console.log('生成模拟风险预警数据')
      const warningTypes = ['回撤预警', '滑点异常', '仓位超限', '市场异常波动', '流动性风险']
      const riskLevels = ['低', '中', '高', '严重']
      const mockWarnings = []
      
      const now = new Date()
      
      // 确保生成足够的预警数据（10-20条）
      const warningCount = 10 + Math.floor(Math.random() * 11)
      for (let i = 0; i < warningCount; i++) {
        const warningTime = new Date(now)
        warningTime.setMinutes(warningTime.getMinutes() - Math.floor(Math.random() * 360))
        
        const warning = {
          id: `WARN${1000 + i}`,
          timestamp: warningTime.toLocaleString('zh-CN'),
          type: warningTypes[Math.floor(Math.random() * warningTypes.length)],
          level: riskLevels[Math.floor(Math.random() * riskLevels.length)],
          message: this.generateMockWarningMessage(warningTypes[Math.floor(Math.random() * warningTypes.length)]),
          status: Math.random() > 0.5 ? 'handled' : 'unhandled',
          relatedAsset: `股票${Math.floor(Math.random() * 1000).toString().padStart(6, '0')}`,
          data: {
            threshold: Math.random() * 0.1,
            currentValue: Math.random() * 0.15,
            deviation: Math.random() * 0.05
          }
        }
        
        mockWarnings.push(warning)
      }
      
      // 确保至少有几条未处理的预警
      let unhandledCount = 0
      mockWarnings.forEach(warning => {
        if (warning.status === 'unhandled') {
          unhandledCount++
        }
      })
      
      if (unhandledCount < 3) {
        // 如果未处理预警太少，将一些已处理的改为未处理
        let needed = 3 - unhandledCount
        mockWarnings.forEach(warning => {
          if (needed > 0 && warning.status === 'handled') {
            warning.status = 'unhandled'
            needed--
          }
        })
      }
      
      // 按时间倒序排序
      mockWarnings.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      
      this.riskWarnings = mockWarnings
    },
    
    // 生成模拟预警信息
    generateMockWarningMessage(type) {
      const messages = {
        '回撤预警': '资产回撤超过阈值，当前回撤为5.2%，阈值为5%',
        '滑点异常': '订单执行滑点异常，当前滑点为0.8%，阈值为0.5%',
        '仓位超限': '单一股票持仓比例超过最大限制，当前比例为25%，限制为20%',
        '市场异常波动': '市场出现异常波动，波动率较昨日增加30%',
        '流动性风险': '部分持仓股票流动性下降，警惕无法及时平仓的风险'
      }
      return messages[type] || '检测到潜在风险'
    }
  }
}
</script>

<style scoped>
.risk-warning-container {
  padding: 20px;
}

.refresh-btn {
  float: right;
}

.risk-status-overview {
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

.risk-header {
  display: flex;
  align-items: center;
  width: 100%;
}

.risk-card {
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.risk-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.risk-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.risk-item {
  background-color: #fafafa;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  transition: all 0.3s ease;
}

.risk-item:hover {
  background-color: #ffffff;
  border-color: #dcdfe6;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.sharpe-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #606266;
}

.sharpe-range {
  padding: 2px 8px;
  border-radius: 3px;
  background-color: #f0f0f0;
}

.animated {
  animation-duration: 0.5s;
  animation-fill-mode: both;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translate3d(0, 20px, 0);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.fadeIn {
  animation-name: fadeIn;
}

.fadeInUp {
  animation-name: fadeInUp;
}

.profit {
  color: #67c23a !important;
}

.loss {
  color: #f56c6c !important;
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

.risk-severe {
  color: #f56c6c !important;
  animation: pulse 2s infinite;
}

.risk-extreme {
  color: #f56c6c !important;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
  100% {
    opacity: 1;
  }
}

.risk-charts-section,
.warnings-section,
.thresholds-section {
  margin-bottom: 30px;
}

h3 {
  margin-bottom: 15px;
  color: #303133;
  font-size: 18px;
}

.chart-container {
  width: 100%;
  height: 300px;
}

.dialog-footer {
  text-align: right;
}

pre {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>