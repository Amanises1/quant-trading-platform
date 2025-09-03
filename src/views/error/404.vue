<template>
  <div class="error-container">
    <div class="error-content">
      <h1>404</h1>
      <h2>页面不存在</h2>
      <p>抱歉，您访问的页面不存在或已被移除</p>
      <el-button type="primary" @click="goHome">返回首页</el-button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NotFound',
  methods: {
    goHome() {
      this.$router.push('/')
    }
  }
}
</script>

<style scoped>
.error-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}

.error-content {
  text-align: center;
  padding: 40px;
}

.error-content h1 {
  font-size: 120px;
  margin: 0;
  color: #409EFF;
  line-height: 1;
}

.error-content h2 {
  font-size: 30px;
  margin: 20px 0;
  color: #303133;
}

.error-content p {
  font-size: 16px;
  color: #606266;
  margin-bottom: 30px;
}
</style>