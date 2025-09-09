<template>
  <div class="data-collection-container">
    <h2>数据采集</h2>
    
    <el-card>
      <div slot="header" class="clearfix">
        <span>采集配置</span>
      </div>
      
      <el-form :model="collectionForm" :rules="collectionRules" ref="collectionForm" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="数据源" prop="dataSource">
              <el-select v-model="collectionForm.dataSource" placeholder="请选择数据源">
                <el-option label="本地数据库" value="local_db" />
                <el-option label="外部API" value="external_api" />
                <el-option label="CSV文件" value="csv_file" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="股票代码" prop="stockCode">
              <el-input v-model="collectionForm.stockCode" placeholder="请输入股票代码，多个代码用逗号分隔" />
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="起始日期" prop="startDate">
              <el-date-picker
                v-model="collectionForm.startDate"
                type="date"
                placeholder="选择起始日期"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="结束日期" prop="endDate">
              <el-date-picker
                v-model="collectionForm.endDate"
                type="date"
                placeholder="选择结束日期"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="时间频率" prop="interval">
              <el-select v-model="collectionForm.interval" placeholder="请选择时间频率">
                <el-option label="日K" value="1d" />
                <el-option label="周K" value="1wk" />
                <el-option label="月K" value="1mo" />
                <el-option label="分钟线" value="1m" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="数据类型" prop="dataType">
              <el-select v-model="collectionForm.dataType" placeholder="请选择数据类型" multiple collapse-tags>
                <el-option label="基本行情" value="basic" />
                <el-option label="财务数据" value="financial" />
                <el-option label="公司信息" value="company" />
                <el-option label="行业数据" value="industry" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item>
          <div class="button-group">
            <el-button type="primary" @click="startCollection" :loading="collecting" :disabled="collecting">
              开始采集
            </el-button>
            <el-button @click="stopCollection" :disabled="!collecting">
              停止采集
            </el-button>
            <el-button @click="resetForm">
              重置
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="mt-4">
      <div slot="header" class="clearfix">
        <span>采集状态</span>
      </div>
      
      <div class="status-container">
        <div class="status-item">
          <span class="status-label">当前状态：</span>
          <span class="status-value" :class="collecting ? 'status-running' : 'status-idle'">
            {{ collecting ? '采集进行中' : '空闲' }}
          </span>
        </div>
        
        <div class="status-item" v-if="collecting">
          <span class="status-label">进度：</span>
          <el-progress :percentage="collectionProgress" :status="progressStatus" />
        </div>
        
        <div class="status-item" v-if="collectionResult">
          <span class="status-label">结果：</span>
          <span class="status-value" :class="collectionResult.success ? 'status-success' : 'status-error'">
            {{ collectionResult.message }}
          </span>
        </div>
        
        <div class="status-item" v-if="collectedStocks.length > 0">
          <span class="status-label">已采集股票：</span>
          <div class="stock-list">
            <el-tag v-for="stock in collectedStocks" :key="stock" type="success" size="small" close-transition>
              {{ stock }}
            </el-tag>
          </div>
        </div>
      </div>
      
      <div class="log-container mt-4" v-if="collectionLog.length > 0">
        <div class="log-header">
          <span>采集日志</span>
          <el-button type="text" @click="clearLog" size="small">清空日志</el-button>
        </div>
        <el-scrollbar class="log-content">
          <div v-for="(log, index) in collectionLog" :key="index" class="log-item">
            <span class="log-time">{{ formatLogTime(log.time) }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </el-scrollbar>
      </div>
    </el-card>
  </div>
</template>

<script>
import request from '@/utils/axios-config'

export default {
  name: 'DataCollection',
  data() {
    return {
      collectionForm: {
        dataSource: 'external_api',
        stockCode: '000001,600000,000002',
        startDate: '',
        endDate: '',
        interval: '1d',
        dataType: ['basic']
      },
      collectionRules: {
        dataSource: [
          { required: true, message: '请选择数据源', trigger: 'change' }
        ],
        stockCode: [
          { required: true, message: '请输入股票代码', trigger: 'blur' }
        ],
        startDate: [
          { required: true, message: '请选择起始日期', trigger: 'change' }
        ],
        endDate: [
          { required: true, message: '请选择结束日期', trigger: 'change' }
        ],
        interval: [
          { required: true, message: '请选择时间频率', trigger: 'change' }
        ],
        dataType: [
          { required: true, message: '请至少选择一种数据类型', trigger: 'change' }
        ]
      },
      collecting: false,
      collectionProgress: 0,
      progressStatus: 'success',
      collectionResult: null,
      collectedStocks: [],
      collectionLog: [],
      
      collectionTimer: null
    }
  },
  mounted() {
    // 设置默认日期范围（最近3个月）
    const endDate = new Date()
    const startDate = new Date()
    startDate.setMonth(startDate.getMonth() - 3)
    
    this.collectionForm.startDate = startDate
    this.collectionForm.endDate = endDate
  },
  methods: {
    async startCollection() {
      this.$refs.collectionForm.validate(async (valid) => {
        if (valid) {
          this.collecting = true
          this.collectionProgress = 0
          this.collectionResult = null
          this.collectedStocks = []
          this.collectionLog = []
          
          try {
            // 格式化日期
            const formatDate = (date) => {
              return date.toISOString().split('T')[0]
            }
            
            // 分割股票代码
            const stockCodes = this.collectionForm.stockCode.split(',').map(code => code.trim()).filter(code => code)
            
            this.log('开始采集数据，共' + stockCodes.length + '只股票')
            
            // 模拟采集进度
            this.simulateProgress(stockCodes.length)
            
            for (let i = 0; i < stockCodes.length; i++) {
              const stockCode = stockCodes[i]
              
              try {
                this.log('开始采集股票：' + stockCode)
                
                const response = await request.post('/api/data/collect', {
                  symbol: stockCode,
                  start_date: formatDate(this.collectionForm.startDate),
                  end_date: formatDate(this.collectionForm.endDate),
                  interval: this.collectionForm.interval,
                  data_source: this.collectionForm.dataSource,
                  data_types: this.collectionForm.dataType
                })
                
                if (response.data.success) {
                  this.collectedStocks.push(stockCode)
                  this.log('股票 ' + stockCode + ' 采集成功，共' + response.data.data.length + '条记录')
                } else {
                  this.log('股票 ' + stockCode + ' 采集失败：' + response.data.message, 'error')
                }
              } catch (error) {
                console.error('采集股票数据失败:', error)
                this.log('股票 ' + stockCode + ' 采集异常：' + error.message, 'error')
              }
            }
            
            this.collectionResult = {
              success: true,
              message: '数据采集完成，成功采集 ' + this.collectedStocks.length + '/' + stockCodes.length + ' 只股票'
            }
            
            this.$message({
              message: '数据采集完成',
              type: 'success'
            })
          } catch (error) {
            console.error('数据采集失败:', error)
            this.collectionResult = {
              success: false,
              message: '数据采集过程中发生错误：' + error.message
            }
            
            this.$message({
              message: '数据采集失败',
              type: 'error'
            })
          } finally {
            this.stopProgressSimulation()
            this.collecting = false
          }
        }
      })
    },
    
    stopCollection() {
      if (this.collecting) {
        this.$confirm('确定要停止数据采集吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.stopProgressSimulation()
          this.collecting = false
          this.collectionResult = {
            success: false,
            message: '数据采集已被用户中断'
          }
          
          this.$message({
            message: '数据采集已停止',
            type: 'info'
          })
        }).catch(() => {
          // 用户取消停止
        })
      }
    },
    
    resetForm() {
      this.$refs.collectionForm.resetFields()
      this.collectionResult = null
      this.collectedStocks = []
      this.collectionLog = []
    },
    
    log(message, type = 'info') {
      const logItem = {
        time: new Date(),
        message: message,
        type: type
      }
      
      this.collectionLog.push(logItem)
      
      // 自动滚动到最新日志
      this.$nextTick(() => {
        const scrollbar = this.$el.querySelector('.el-scrollbar__wrap')
        if (scrollbar) {
          scrollbar.scrollTop = scrollbar.scrollHeight
        }
      })
    },
    
    formatLogTime(time) {
      return new Date(time).toLocaleString('zh-CN')
    },
    
    clearLog() {
      this.collectionLog = []
    },
    
    simulateProgress(totalStocks) {
      let progress = 0
      this.stopProgressSimulation()
      
      this.collectionTimer = setInterval(() => {
        if (progress < 100) {
          // 根据已采集的股票数量计算进度
          const realProgress = (this.collectedStocks.length / totalStocks) * 100
          // 模拟进度接近实际进度，但不完全一致
          progress = Math.min(progress + Math.random() * 5, realProgress + 10, 100)
          this.collectionProgress = Math.floor(progress)
        }
      }, 500)
    },
    
    stopProgressSimulation() {
      if (this.collectionTimer) {
        clearInterval(this.collectionTimer)
        this.collectionTimer = null
      }
    }
  },
  beforeDestroy() {
    this.stopProgressSimulation()
  }
}
</script>

<style scoped>
.data-collection-container {
  padding: 20px;
}

.mt-4 {
  margin-top: 16px;
}

.button-group {
  display: flex;
  gap: 10px;
}

.status-container {
  padding: 10px 0;
}

.status-item {
  margin-bottom: 10px;
}

.status-label {
  display: inline-block;
  width: 80px;
  font-weight: 500;
  color: #606266;
}

.status-value {
  display: inline-block;
  color: #303133;
}

.status-running {
  color: #409EFF;
}

.status-idle {
  color: #909399;
}

.status-success {
  color: #67C23A;
}

.status-error {
  color: #F56C6C;
}

.stock-list {
  display: inline-block;
  margin-left: 10px;
}

.log-container {
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  padding: 10px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.log-content {
  height: 200px;
  background-color: #F5F7FA;
  padding: 10px;
  border-radius: 4px;
}

.log-item {
  padding: 5px 0;
  font-size: 14px;
}

.log-time {
  color: #909399;
  margin-right: 10px;
}

.log-message {
  color: #303133;
}
</style>