import axios from 'axios'

// 创建axios实例
const service = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:5000',
  timeout: 30000 // 请求超时时间
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 这里可以添加token等认证信息
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers['Authorization'] = `Bearer ${token}`
    // }
    
    // 添加请求时间戳，避免缓存
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      }
    }
    
    console.log('API请求配置:', config)
    return config
  },
  error => {
    console.error('请求配置错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data
    
    // 根据后端返回格式判断请求是否成功
    if (res.code !== undefined) {
      // 如果有code字段，使用code判断
      if (res.code !== 200) {
        // 处理业务错误
        handleError(res.code, res.message || '请求失败')
        return Promise.reject(new Error(res.message || '请求失败'))
      } else {
        return res
      }
    } else if (res.success !== undefined) {
      // 如果有success字段，使用success判断
      if (!res.success) {
        handleError(400, res.message || '请求失败')
        return Promise.reject(new Error(res.message || '请求失败'))
      } else {
        return res
      }
    } else {
      // 没有明确的成功标识，默认返回整个响应数据
      return res
    }
  },
  error => {
    console.error('响应错误:', error)
    
    // 处理网络错误、超时等
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      handleError(408, '请求超时，请稍后重试')
    } else if (error.response) {
        // 服务器返回错误状态码
        const status = error.response.status
        const message = error.response.data && error.response.data.message ? error.response.data.message : '服务器错误'
        handleError(status, message)
    } else if (error.request) {
      // 请求已发送但没有收到响应
      handleError(503, '网络连接失败，请检查网络设置')
    } else {
      // 请求配置出错
      handleError(400, error.message || '请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

// 错误处理函数
function handleError(code, message) {
  console.error(`API错误 ${code}:`, message)
  
  // 根据错误码进行不同处理
  switch (code) {
    case 401:
      // 未授权，跳转到登录页
      // router.replace('/login')
      showErrorMessage('登录已过期，请重新登录')
      break
    case 403:
      showErrorMessage('没有权限执行此操作')
      break
    case 404:
      showErrorMessage('请求的资源不存在')
      break
    case 500:
      showErrorMessage('服务器内部错误')
      break
    default:
      showErrorMessage(message)
  }
}

// 显示错误消息
function showErrorMessage(message) {
  // 尝试使用Element UI的Message组件显示错误消息
  if (window.Vue && window.Vue.prototype.$message) {
    window.Vue.prototype.$message.error(message)
  } else {
    // 如果Element UI不可用，使用alert
    console.warn('Element UI Message组件不可用，使用alert显示错误消息')
    // alert(message)
  }
}

// 导出常用的请求方法
export default {
  get(url, params = {}) {
    return service.get(url, { params })
  },
  
  post(url, data = {}, params = {}) {
    return service.post(url, data, { params })
  },
  
  put(url, data = {}, params = {}) {
    return service.put(url, data, { params })
  },
  
  delete(url, params = {}) {
    return service.delete(url, { params })
  },
  
  // 上传文件
  upload(url, file, onUploadProgress) {
    const formData = new FormData()
    formData.append('file', file)
    
    return service.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress
    })
  },
  
  // 下载文件
  download(url, params = {}) {
    return service.get(url, {
      params,
      responseType: 'blob'
    })
  },
  
  // 获取axios实例，用于自定义配置
  getInstance() {
    return service
  }
}

// 导出原始axios实例，方便一些特殊场景使用
export const axiosInstance = service