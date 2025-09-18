import Vue from 'vue'
import VueRouter from 'vue-router'
import Layout from '../views/layout/Layout.vue'

Vue.use(VueRouter)

// 路由配置
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/login/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/register/Register.vue'),
    meta: { title: '注册', requiresAuth: false }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/dashboard/Dashboard.vue'),
        meta: { title: '首页', requiresAuth: true }
      },
      // 交易员路由
      {
        path: 'visualization',
        name: 'Visualization',
        component: () => import('../views/visualization/Visualization.vue'),
        meta: { title: '多维特征可视化', requiresAuth: true, roles: ['user'] }
      },
      {
        path: 'risk-warning',
        name: 'RiskWarning',
        component: () => import('../views/risk-warning/RiskWarning.vue'),
        meta: { title: '风险预警与熔断', requiresAuth: true, roles: ['user'] }
      },
      {
        path: 'trade-monitor',
        name: 'TradeMonitor',
        component: () => import('../views/trade-monitor/TradeMonitor.vue'),
        meta: { title: '实时交易监控', requiresAuth: true, roles: ['user'] }
      },
      {
        path: 'strategy-backtest',
        name: 'StrategyBacktest',
        component: () => import('../views/strategy-backtest/StrategyBacktest.vue'),
        meta: { title: '交易策略回测', requiresAuth: true, roles: ['user'] }
      },
      {
        path: 'signal-generation',
        name: 'SignalGeneration',
        component: () => import('../views/signal-generation/SignalGeneration.vue'),
        meta: { title: '智能交易信号生成', requiresAuth: true, roles: ['user'] }
      },
      // 研究员路由
      {
        path: 'data-collection',
        name: 'DataCollection',
        component: () => import('../views/data-collection/DataCollection.vue'),
        meta: { title: '数据采集和清洗', requiresAuth: true, roles: ['user'] }
      },
      {
        path: 'model-management',
        name: 'ModelManagement',
        component: () => import('../views/model-management/ModelManagement.vue'),
        meta: { title: '模型全生命周期管理', requiresAuth: true, roles: ['user', 'admin'] }
      },
      {
        path: 'historical-data',
        name: 'HistoricalData',
        component: () => import('../views/historical-data/HistoricalData.vue'),
        meta: { title: '加载历史数据', requiresAuth: true, roles: ['user'] }
      },
      {
        path: 'technical-indicators',
        name: 'TechnicalIndicators',
        component: () => import('../views/technical-indicators/TechnicalIndicators.vue'),
        meta: { title: '计算技术指标', requiresAuth: true, roles: ['user'] }
      },
      // 系统管理员路由
      {
        path: 'system-params',
        name: 'SystemParams',
        component: () => import('../views/system-params/SystemParams.vue'),
        meta: { title: '系统参数管理', requiresAuth: true, roles: ['admin'] }
      },
      { path: 'database-maintenance', name: 'DatabaseMaintenance', component: () => import('../views/database-maintenance/DatabaseMaintenance.vue'), meta: { title: '数据库维护', requiresAuth: true, roles: ['admin'] } }, { path: 'notifications', name: 'Notifications', component: () => import('../views/notification/NotificationCenterPage.vue'), meta: { title: '通知中心', requiresAuth: true } },
      {
        path: 'platform-migration',
        name: 'PlatformMigration',
        component: () => import('../views/platform-migration/PlatformMigration.vue'),
        meta: { title: '跨平台迁移', requiresAuth: true, roles: ['admin'] }
      },
      { path: 'user-management', name: 'UserManagement', component: () => import('../views/user-management/UserManagement.vue'), meta: { title: '用户管理', requiresAuth: true, roles: ['admin'] } },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/profile/Profile.vue'),
        meta: { title: '个人信息', requiresAuth: true }
      }
    ]
  },
  // 404页面
  {
    path: '*',
    component: () => import('../views/error/404.vue'),
    meta: { title: '404', requiresAuth: false }
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

// 全局前置守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title || '量化交易选股系统'

  // 判断该路由是否需要登录权限
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('token')
    if (token) {
      // 判断用户角色权限
      if (to.meta.roles) {
        const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
        const userRole = userInfo.role || ''
        if (to.meta.roles.includes(userRole)) {
          next()
        } else {
          next('/dashboard') // 无权限，跳转到首页
        }
      } else {
        next()
      }
    } else {
      next({
        path: '/login',
        query: { redirect: to.fullPath } // 将跳转的路由path作为参数，登录成功后跳转到该路由
      })
    }
  } else {
    next()
  }
})

export default router