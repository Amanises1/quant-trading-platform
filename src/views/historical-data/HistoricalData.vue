<template>
  <div class="historical-data-container">
    <h2>历史数据管理</h2>
    <el-card>
      <div slot="header" class="clearfix">
        <span>数据查询</span>
      </div>
      
      <el-form :model="queryForm" :rules="queryRules" ref="queryForm" label-width="80px">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="股票代码" prop="stockCode">
              <el-input v-model="queryForm.stockCode" placeholder="请输入股票代码" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="起始日期" prop="startDate">
              <el-date-picker
                v-model="queryForm.startDate"
                type="date"
                placeholder="选择起始日期"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="结束日期" prop="endDate">
              <el-date-picker
                v-model="queryForm.endDate"
                type="date"
                placeholder="选择结束日期"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="2">
            <el-form-item>
              <el-button type="primary" @click="handleQuery" :loading="loading">查询</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>
    
    <el-card class="mt-4" v-if="stockData.length > 0">
      <div slot="header" class="clearfix">
        <span>{{ queryForm.stockCode }} 历史数据</span>
        <el-button type="text" @click="exportToExcel" class="float-right">导出Excel</el-button>
      </div>
      
      <el-table :data="stockData" style="width: 100%">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="open" label="开盘价" width="100" />
        <el-table-column prop="high" label="最高价" width="100" />
        <el-table-column prop="low" label="最低价" width="100" />
        <el-table-column prop="close" label="收盘价" width="100" />
        <el-table-column prop="volume" label="成交量" width="120" />
      </el-table>
      
      <div class="mt-4">
        <el-pagination
          v-model="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalCount"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <el-empty v-else-if="!loading" description="暂无数据" class="mt-8" />
    <el-loading v-if="loading" fullscreen text="数据加载中..." />
  </div>
</template>

<script>
import request from '@/utils/axios-config'

export default {
  name: 'HistoricalData',
  data() {
    return {
      queryForm: {
        stockCode: '000001',
        startDate: '',
        endDate: ''
      },
      queryRules: {
        stockCode: [
          { required: true, message: '请输入股票代码', trigger: 'blur' }
        ],
        startDate: [
          { required: true, message: '请选择起始日期', trigger: 'change' }
        ],
        endDate: [
          { required: true, message: '请选择结束日期', trigger: 'change' }
        ]
      },
      stockData: [],
      totalCount: 0,
      currentPage: 1,
      pageSize: 20,
      loading: false,
      
    }
  },
  mounted() {
    // 设置默认日期范围（最近30天）
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - 30)
    
    this.queryForm.startDate = startDate
    this.queryForm.endDate = endDate
    
    // 组件挂载后自动加载数据
    this.handleQuery()
  },
  methods: {
    async handleQuery() {
      this.$refs.queryForm.validate(async (valid) => {
        if (valid) {
          this.loading = true
          try {
            // 格式化日期
            const formatDate = (date) => {
              return date.toISOString().split('T')[0]
            }
            
            const response = await request.post('/api/data/collect', {
              symbol: this.queryForm.stockCode,
              start_date: formatDate(this.queryForm.startDate),
              end_date: formatDate(this.queryForm.endDate),
              interval: '1d'
            })
            
            if (response.data.success) {
              this.stockData = response.data.data
              this.totalCount = response.data.data.length
              this.currentPage = 1
              
              this.$message({
                message: '数据加载成功',
                type: 'success'
              })
            } else {
              this.$message({
                message: response.data.message || '数据加载失败',
                type: 'error'
              })
            }
          } catch (error) {
            console.error('API调用失败:', error)
            this.$message({
              message: 'API调用失败，请检查服务是否正常运行',
              type: 'error'
            })
          } finally {
            this.loading = false
          }
        }
      })
    },
    
    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1
      // 实际项目中可能需要重新加载数据
    },
    
    handleCurrentChange(val) {
      this.currentPage = val
      // 实际项目中可能需要加载对应页码的数据
    },
    
    exportToExcel() {
      // 这里可以实现导出Excel功能
      this.$message({
        message: '导出功能开发中',
        type: 'info'
      })
    }
  },
  computed: {
    // 分页后的数据
    paginatedData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return this.stockData.slice(start, end)
    }
  }
}
</script>

<style scoped>
.historical-data-container {
  padding: 20px;
}

.mt-4 {
  margin-top: 16px;
}

.mt-8 {
  margin-top: 32px;
}

.float-right {
  float: right;
}
</style>