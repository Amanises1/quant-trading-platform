<template>
  <div class="sidebar-container">
    <el-menu
      :default-active="activeMenu"
      class="sidebar-menu"
      :collapse="isCollapse"
      router
    >
      <div class="logo-container">
        <div class="logo-collapse-btn" @click="toggleCollapse">
          <i :class="isCollapse ? 'el-icon-s-unfold' : 'el-icon-s-fold'"/>
        </div>
      </div>
      
      <!-- 交易员菜单 -->
      <template v-if="userRole === 'trader'">
        <el-menu-item index="/dashboard">
          <i class="el-icon-s-home"/>
          <span slot="title">首页</span>
        </el-menu-item>
        <el-menu-item index="/visualization">
          <i class="el-icon-data-line"/>
          <span slot="title">多维特征可视化</span>
        </el-menu-item>
        <el-menu-item index="/trade-monitor">
          <i class="el-icon-monitor"/>
          <span slot="title">实时交易监控</span>
        </el-menu-item>
        <el-menu-item index="/strategy-backtest">
          <i class="el-icon-time"/>
          <span slot="title">交易策略回测</span>
        </el-menu-item>
        <el-menu-item index="/signal-generation">
          <i class="el-icon-bell"/>
          <span slot="title">智能交易信号生成</span>
        </el-menu-item>
      </template>
      
      <!-- 研究员菜单 -->
      <template v-if="userRole === 'researcher'">
        <el-menu-item index="/dashboard">
          <i class="el-icon-s-home"/>
          <span slot="title">首页</span>
        </el-menu-item>
        <el-menu-item index="/visualization">
          <i class="el-icon-data-line"/>
          <span slot="title">多维特征可视化</span>
        </el-menu-item>
        <el-menu-item index="/data-collection">
          <i class="el-icon-collection"/>
          <span slot="title">数据采集和清洗</span>
        </el-menu-item>
        <el-menu-item index="/model-management">
          <i class="el-icon-s-cooperation"/>
          <span slot="title">模型全生命周期管理</span>
        </el-menu-item>
        <el-menu-item index="/historical-data">
          <i class="el-icon-document"/>
          <span slot="title">加载历史数据</span>
        </el-menu-item>
        <el-menu-item index="/technical-indicators">
          <i class="el-icon-s-marketing"/>
          <span slot="title">计算技术指标</span>
        </el-menu-item>
        <el-menu-item index="/signal-generation">
          <i class="el-icon-bell"/>
          <span slot="title">智能交易信号生成</span>
        </el-menu-item>
        <el-menu-item index="/strategy-backtest">
          <i class="el-icon-time"/>
          <span slot="title">交易策略回测</span>
        </el-menu-item>
      </template>
      
      <!-- 系统管理员菜单 -->
      <template v-if="userRole === 'admin'">
        <el-menu-item index="/dashboard">
          <i class="el-icon-s-home"/>
          <span slot="title">首页</span>
        </el-menu-item>
        <el-menu-item index="/system-params">
          <i class="el-icon-setting"/>
          <span slot="title">系统参数管理</span>
        </el-menu-item>
        <el-menu-item index="/database-maintenance">
          <i class="el-icon-coin"/>
          <span slot="title">数据库维护</span>
        </el-menu-item>
        <el-menu-item index="/model-management">
          <i class="el-icon-s-cooperation"/>
          <span slot="title">模型全生命周期</span>
        </el-menu-item>
        <el-menu-item index="/platform-migration">
          <i class="el-icon-share"/>
          <span slot="title">跨平台迁移</span>
        </el-menu-item>
        <el-menu-item index="/user-management">
          <i class="el-icon-user"/>
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
      userRole: 'trader' // 默认为交易员角色，实际应从登录信息中获取
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
  background-color: #e7f3f8; /* 柔和的浅蓝白色 */
  transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1);
  width: auto;
  overflow: hidden;
}

.sidebar-menu {
  height: 100%;
  border-right: none;
  transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1);
  background-color: transparent !important; /* 强制透明背景 */
  white-space: nowrap;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 220px !important;
}

.sidebar-menu.el-menu--collapse {
  width: 60px !important; /* 强制设置收起时的宽度，确保不遮挡页面 */
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #d4e6f1; /* 与侧边栏协调的柔和颜色 */
  width: 100%;
  transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1);
}

.logo-collapse-btn {
  font-size: 20px;
  color: #2c3e50; /* 深色文字以适应浅色背景 */
  cursor: pointer;
  transition: transform 0.3s ease;
}

.logo-collapse-btn:hover {
  transform: scale(1.1);
}

.el-menu-item {
  height: 50px;
  line-height: 50px;
  color: #2c3e50 !important;
  transition: all 0.3s ease;
  padding: 0 20px !important;
}

.el-menu-item:hover {
  background-color: #d4e6f1 !important;
}

.el-menu-item i {
  margin-right: 5px;
  font-size: 18px;
  color: #2c3e50 !important; /* 深色图标以适应浅色背景 */
  transition: transform 0.3s ease;
}

.el-menu-item:hover i {
  transform: translateX(2px);
}

/* 确保文字颜色适应浅色背景 */
.sidebar-menu .el-menu-item {
  color: #2c3e50 !important;
}

.sidebar-menu .el-menu-item.is-active {
  color: #2980b9 !important;
  background-color: #d4e6f1 !important;
  transition: all 0.3s ease;
}

/* 菜单文字动画 */
.sidebar-menu .el-menu-item .el-menu-item__title {
  opacity: 1;
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.sidebar-menu.el-menu--collapse .el-menu-item .el-menu-item__title {
  opacity: 0;
  transform: translateX(-10px);
}
</style>