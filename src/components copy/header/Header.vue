<template>
  <div class="header">
    <div class="logo-container">
      <h1 class="title">量化交易选股系统</h1>
    </div>
    <div class="header-right">
      <el-dropdown trigger="click" @command="handleCommand">
        <span class="user-info">
          <i class="el-icon-user"></i>
          {{ username }}
          <i class="el-icon-arrow-down el-icon--right"></i>
        </span>
        <el-dropdown-menu slot="dropdown">
          <el-dropdown-item command="profile">个人信息</el-dropdown-item>
          <el-dropdown-item command="settings">系统设置</el-dropdown-item>
          <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Header',
  data() {
    return {
      username: '管理员',
      logo: false // 暂时没有logo图片
    }
  },
  methods: {
    handleCommand(command) {
      if (command === 'logout') {
        this.$confirm('确认退出系统吗?', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          // 清除登录信息
          localStorage.removeItem('token');
          localStorage.removeItem('userInfo');
          // 跳转到登录页
          this.$router.push('/login');
          this.$message({
            type: 'success',
            message: '退出成功!'
          });
        }).catch(() => {
          // 取消退出
        });
      } else if (command === 'profile') {
        this.$router.push('/profile');
      } else if (command === 'settings') {
        this.$router.push('/settings');
      }
    }
  }
}
</script>

<style scoped>
.header {
  height: 60px;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: relative;
  z-index: 10;
}

.logo-container {
  display: flex;
  align-items: center;
}

.logo {
  height: 40px;
  margin-right: 10px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: var(--primary-color, #409EFF);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

.user-info i {
  margin-right: 5px;
}

.el-icon--right {
  margin-left: 5px;
}
</style>