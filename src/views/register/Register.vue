<template>
  <div class="register-container">
    <div class="register-box">
      <div class="register-header">
        <h2>用户注册</h2>
        <p>欢迎加入量化交易选股系统</p>
      </div>
      <el-form :model="registerForm" :rules="registerRules" ref="registerForm" class="register-form" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username" placeholder="请输入用户名"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input type="password" v-model="registerForm.password" placeholder="请输入密码"></el-input>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input type="password" v-model="registerForm.confirmPassword" placeholder="请再次输入密码"></el-input>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="registerForm.email" placeholder="请输入邮箱"></el-input>
        </el-form-item>
        <el-form-item label="手机号码" prop="phone">
          <el-input v-model="registerForm.phone" placeholder="请输入手机号码"></el-input>
        </el-form-item>
        <el-form-item label="用户角色" prop="role">
          <el-select v-model="registerForm.role" placeholder="请选择用户角色">
            <el-option label="普通用户" value="trader"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRegister">注册</el-button>
          <el-button @click="goToLogin">返回登录</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Register',
  data() {
    // 自定义验证规则
    const validatePass = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请输入密码'));
      } else {
        if (this.registerForm.confirmPassword !== '') {
          this.$refs.registerForm.validateField('confirmPassword');
        }
        callback();
      }
    };
    const validatePass2 = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'));
      } else if (value !== this.registerForm.password) {
        callback(new Error('两次输入密码不一致!'));
      } else {
        callback();
      }
    };
    const validatePhone = (rule, value, callback) => {
      const reg = /^1[3-9]\d{9}$/;
      if (value === '') {
        callback(new Error('请输入手机号码'));
      } else if (!reg.test(value)) {
        callback(new Error('请输入有效的手机号码'));
      } else {
        callback();
      }
    };
    
    return {
      registerForm: {
        username: '',
        password: '',
        confirmPassword: '',
        email: '',
        phone: '',
        role: ''
      },
      registerRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, max: 20, message: '长度在 6 到 20 个字符', trigger: 'blur' },
          { validator: validatePass, trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请再次输入密码', trigger: 'blur' },
          { validator: validatePass2, trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
        ],
        phone: [
          { required: true, message: '请输入手机号码', trigger: 'blur' },
          { validator: validatePhone, trigger: 'blur' }
        ],
        role: [
          { required: true, message: '请选择用户角色', trigger: 'change' }
        ]
      },
      loading: false
    }
  },
  methods: {
    handleRegister() {
      this.$refs.registerForm.validate(valid => {
        if (valid) {
          this.loading = true;
          // 调用注册API
          this.$axios.post('/api/user/register', this.registerForm)
            .then(response => {
              if (response.data.success) {
                this.$message({
                  message: response.data.message || '注册成功，请登录',
                  type: 'success'
                });
                this.loading = false;
                this.$router.push('/login');
              } else {
                this.$message.error(response.data.message || '注册失败，请稍后重试');
                this.loading = false;
              }
            })
            .catch(error => {
              console.error('注册失败:', error);
              this.$message.error('注册失败，请稍后重试');
              this.loading = false;
            });
        } else {
          return false;
        }
      });
    },
    goToLogin() {
      this.$router.push('/login');
    }
  }
}
</script>

<style scoped>
.register-container {
  height: 100vh;
  width: 100%;
  background: linear-gradient(to right, #3494e6, #ec6ead);
  display: flex;
  justify-content: center;
  align-items: center;
}

.register-box {
  width: 500px;
  padding: 30px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-header h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 10px;
}

.register-header p {
  font-size: 14px;
  color: #909399;
}

.register-form {
  margin-top: 20px;
}

.el-form-item:last-child {
  margin-bottom: 0;
  text-align: center;
}

.el-button {
  width: 120px;
  margin: 0 10px;
}
</style>