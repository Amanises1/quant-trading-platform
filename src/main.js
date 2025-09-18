import Vue from 'vue'
import App from './App.vue'
import router from './router'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import './assets/styles/global.css'
// 导入axios配置
import { axiosInstance } from './utils/axios-config'

Vue.use(ElementUI)
Vue.prototype.$axios = axiosInstance // 全局注册axios，使组件可以通过this.$axios访问
Vue.config.productionTip = false

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')