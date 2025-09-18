<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h2>量化交易选股系统</h2>
        <p>专业的量化交易平台，助力投资决策</p>
      </div>
      <el-form :model="loginForm" :rules="loginRules" ref="loginForm" class="login-form">
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username" 
            prefix-icon="el-icon-user" 
            placeholder="用户名">
          </el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input 
            v-model="loginForm.password" 
            prefix-icon="el-icon-lock" 
            type="password" 
            placeholder="密码" 
            @keyup.enter.native="handleLogin">
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
          <el-button type="text" class="forget-pwd" @click="forgetPassword">忘记密码?</el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">登录</el-button>
        </el-form-item>
        <div class="register-link">
          <span>还没有账号?</span>
          <el-button type="text" @click="goToRegister">立即注册</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Login',
  data() {
    return {
      loginForm: {
        username: '',
        password: '',
        remember: false
      },
      loginRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, max: 20, message: '长度在 6 到 20 个字符', trigger: 'blur' }
        ]
      },
      loading: false
    }
  },
  methods: {
    handleLogin() {
      this.$refs.loginForm.validate(valid => {
        if (valid) {
          this.loading = true;
          // 调用登录API
          this.$axios.post('/api/user/login', this.loginForm)
            .then(result => {
              if (result.success) {
                // 保存登录信息
                const userInfo = result.userInfo;
                localStorage.setItem('token', userInfo.token);
                localStorage.setItem('userInfo', JSON.stringify(userInfo));
                
                this.$message({
                  message: result.message || '登录成功',
                  type: 'success'
                });
                
                // 跳转到首页
                this.$router.push('/');
              } else {
                this.$message.error(result.message || '登录失败，请稍后重试');
              }
              this.loading = false;
            })
            .catch(error => {
              console.error('登录失败:', error);
              this.$message.error('登录失败，请稍后重试');
              this.loading = false;
            });
        } else {
          return false;
        }
      });
    },
    forgetPassword() {
      this.$message({
        message: '请联系系统管理员重置密码',
        type: 'info'
      });
    },
    goToRegister() {
      this.$router.push('/register');
    }
  },
  created() {
    // 如果已登录，直接跳转到首页
    const token = localStorage.getItem('token');
    if (token) {
      this.$router.push('/');
    }
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  width: 100%;
  background: linear-gradient(to right, #3494e6, #ec6ead);
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-box {
  width: 400px;
  padding: 30px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 10px;
}

.login-header p {
  font-size: 14px;
  color: #909399;
}

.login-form {
  margin-top: 20px;
}

.login-btn {
  width: 100%;
}

.forget-pwd {
  float: right;
}

.register-link {
  text-align: center;
  margin-top: 15px;
  font-size: 14px;
  color: #606266;
}
</style>