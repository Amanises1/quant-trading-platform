<template>
  <div class="sidebar-container">
    <el-menu
      :default-active="activeMenu"
      class="sidebar-menu"
      :collapse="isCollapse"
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409EFF"
      router
    >
      <div class="logo-container">
        <div class="logo-collapse-btn" @click="toggleCollapse">
          <i :class="isCollapse ? 'el-icon-s-unfold' : 'el-icon-s-fold'"></i>
        </div>
      </div>
      
      <!-- 交易员菜单 -->
      <template v-if="userRole === 'trader'">
        <el-menu-item index="/dashboard">
          <i class="el-icon-s-home"></i>
          <span slot="title">首页</span>
        </el-menu-item>
        <el-menu-item index="/visualization">
          <i class="el-icon-data-line"></i>
          <span slot="title">多维特征可视化</span>
        </el-menu-item>
        <el-menu-item index="/risk-warning">
          <i class="el-icon-warning"></i>
          <span slot="title">风险预警与熔断</span>
        </el-menu-item>
        <el-menu-item index="/trade-monitor">
          <i class="el-icon-monitor"></i>
          <span slot="title">实时交易监控</span>
        </el-menu-item>
        <el-menu-item index="/strategy-backtest">
          <i class="el-icon-time"></i>
          <span slot="title">交易策略回测</span>
        </el-menu-item>
        <el-menu-item index="/signal-generation">
          <i class="el-icon-bell"></i>
          <span slot="title">智能交易信号生成</span>
        </el-menu-item>
      </template>
      
      <!-- 研究员菜单 -->
      <template v-if="userRole === 'researcher'">
        <el-menu-item index="/dashboard">
          <i class="el-icon-s-home"></i>
          <span slot="title">首页</span>
        </el-menu-item>
        <el-menu-item index="/visualization">
          <i class="el-icon-data-line"></i>
          <span slot="title">多维特征可视化</span>
        </el-menu-item>
        <el-menu-item index="/data-collection">
          <i class="el-icon-collection"></i>
          <span slot="title">数据采集和清洗</span>
        </el-menu-item>
        <el-menu-item index="/model-management">
          <i class="el-icon-s-cooperation"></i>
          <span slot="title">模型全生命周期管理</span>
        </el-menu-item>
        <el-menu-item index="/risk-warning">
          <i class="el-icon-warning"></i>
          <span slot="title">风险预警与熔断</span>
        </el-menu-item>
        <el-menu-item index="/historical-data">
          <i class="el-icon-document"></i>
          <span slot="title">加载历史数据</span>
        </el-menu-item>
        <el-menu-item index="/technical-indicators">
          <i class="el-icon-s-marketing"></i>
          <span slot="title">计算技术指标</span>
        </el-menu-item>
        <el-menu-item index="/signal-generation">
          <i class="el-icon-bell"></i>
          <span slot="title">智能交易信号生成</span>
        </el-menu-item>
        <el-menu-item index="/strategy-backtest">
          <i class="el-icon-time"></i>
          <span slot="title">交易策略回测</span>
        </el-menu-item>
      </template>
      
      <!-- 系统管理员菜单 -->
      <template v-if="userRole === 'admin'">
        <el-menu-item index="/dashboard">
          <i class="el-icon-s-home"></i>
          <span slot="title">首页</span>
        </el-menu-item>
        <el-menu-item index="/system-params">
          <i class="el-icon-setting"></i>
          <span slot="title">系统参数管理</span>
        </el-menu-item>
        <el-menu-item index="/database-maintenance">
          <i class="el-icon-coin"></i>
          <span slot="title">数据库维护</span>
        </el-menu-item>
        <el-menu-item index="/model-management">
          <i class="el-icon-s-cooperation"></i>
          <span slot="title">模型全生命周期</span>
        </el-menu-item>
        <el-menu-item index="/platform-migration">
          <i class="el-icon-share"></i>
          <span slot="title">跨平台迁移</span>
        </el-menu-item>
        <el-menu-item index="/user-management">
          <i class="el-icon-user"></i>
          <span slot="title">用户管理</span>
        </el-menu-item>
      </template>
    </el-menu>
  </div>
</template>

<script>
export default {
  name: 'Sidebar',
  data() {
    return {
      isCollapse: false,
      userRole: 'admin' // 默认为管理员角色，实际应从登录信息中获取
    }
  },
  computed: {
    activeMenu() {
      return this.$route.path;
    }
  },
  methods: {
    toggleCollapse() {
      this.isCollapse = !this.isCollapse;
      this.$emit('collapse-change', this.isCollapse);
    }
  },
  created() {
    // 从localStorage获取用户角色
    const userInfo = localStorage.getItem('userInfo');
    if (userInfo) {
      try {
        const parsedInfo = JSON.parse(userInfo);
        this.userRole = parsedInfo.role || 'admin';
      } catch (e) {
        console.error('解析用户信息失败', e);
      }
    }
  }
}
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  background-color: #304156;
}

.sidebar-menu {
  height: 100%;
  border-right: none;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 220px;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #263445;
}

.logo-collapse-btn {
  font-size: 20px;
  color: #bfcbd9;
  cursor: pointer;
}

.el-menu-item {
  height: 50px;
  line-height: 50px;
}

.el-menu-item i {
  margin-right: 5px;
  font-size: 18px;
}
</style>