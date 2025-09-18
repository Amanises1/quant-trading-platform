<template>
  <div class="profile-container">
    <div class="profile-header">
      <h2>个人信息</h2>
    </div>
    <el-card class="profile-card">
      <el-form :model="userInfoForm" :rules="userInfoRules" ref="userInfoForm" label-width="120px" class="user-info-form">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userInfoForm.username" placeholder="请输入用户名"></el-input>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userInfoForm.email" placeholder="请输入邮箱"></el-input>
        </el-form-item>
        <el-form-item label="手机号码" prop="phone">
          <el-input v-model="userInfoForm.phone" placeholder="请输入手机号码"></el-input>
        </el-form-item>
        <el-form-item label="用户角色" prop="role">
          <el-input :value="userInfoForm.role === 'admin' ? '管理员' : '普通用户'" disabled></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleUpdate">保存修改</el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card class="password-card">
      <div class="card-title">修改密码</div>
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordForm" label-width="120px" class="password-form">
        <el-form-item label="当前密码" prop="currentPassword">
          <el-input type="password" v-model="passwordForm.currentPassword" placeholder="请输入当前密码"></el-input>
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input type="password" v-model="passwordForm.newPassword" placeholder="请输入新密码"></el-input>
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input type="password" v-model="passwordForm.confirmPassword" placeholder="请再次输入新密码"></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="passwordLoading" @click="handlePasswordUpdate">修改密码</el-button>
          <el-button @click="resetPasswordForm">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'Profile',
  data() {
    // 自定义验证规则
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
    
    const validateNewPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请输入新密码'));
      } else if (value.length < 6 || value.length > 20) {
        callback(new Error('密码长度应在 6 到 20 个字符之间'));
      } else {
        callback();
      }
    };
    
    const validateConfirmPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入新密码'));
      } else if (value !== this.passwordForm.newPassword) {
        callback(new Error('两次输入的密码不一致'));
      } else {
        callback();
      }
    };
    
    return {
      userInfoForm: {
        id: '',
        username: '',
        email: '',
        phone: '',
        role: ''
      },
      userInfoRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符之间', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
        ],
        phone: [
          { required: true, message: '请输入手机号码', trigger: 'blur' },
          { validator: validatePhone, trigger: 'blur' }
        ]
      },
      passwordForm: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      passwordRules: {
        currentPassword: [
          { required: true, message: '请输入当前密码', trigger: 'blur' }
        ],
        newPassword: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { validator: validateNewPassword, trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请再次输入新密码', trigger: 'blur' },
          { validator: validateConfirmPassword, trigger: 'blur' }
        ]
      },
      loading: false,
      passwordLoading: false
    }
  },
  mounted() {
    this.loadUserInfo();
  },
  methods: {
    loadUserInfo() {
      // 从localStorage获取用户ID
      const userInfoStr = localStorage.getItem('userInfo');
      const userId = userInfoStr ? JSON.parse(userInfoStr).id || '1' : '1';
      
      // 调用后端API获取用户信息
      this.$axios.get('/api/user/profile', {
        params: { user_id: userId }
      })
        .then(response => {
          if (response.data.success) {
            this.userInfoForm = response.data.userInfo;
          } else {
            this.$message.error('获取用户信息失败: ' + response.data.message);
            // 失败时使用模拟数据
            this.setMockUserInfo(userId);
          }
        })
        .catch(error => {
          console.error('获取用户信息失败:', error);
          this.$message.error('获取用户信息失败，请稍后重试');
          // 异常时使用模拟数据
          this.setMockUserInfo(userId);
        });
    },
    
    setMockUserInfo(userId) {
      // 模拟补充完整的用户信息
      this.userInfoForm = {
        id: userId,
        username: 'user' + userId,
        email: 'user' + userId + '@example.com',
        phone: '1380013800' + userId,
        role: userId === '1' ? 'admin' : 'user'
      };
    },
    
    handleUpdate() {
      this.$refs.userInfoForm.validate(valid => {
        if (valid) {
          this.loading = true;
          
          // 调用后端API保存个人信息
          this.$axios.put('/api/user/profile', this.userInfoForm)
            .then(response => {
              if (response.data.success) {
                // 更新localStorage中的用户信息
                const currentUserInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
                const updatedUserInfo = {
                  ...currentUserInfo,
                  username: this.userInfoForm.username,
                  email: this.userInfoForm.email,
                  phone: this.userInfoForm.phone,
                  updated_at: new Date().toLocaleString()
                };
                localStorage.setItem('userInfo', JSON.stringify(updatedUserInfo));
                
                this.$message({
                  message: '个人信息更新成功',
                  type: 'success'
                });
              } else {
                this.$message.error('保存失败: ' + response.data.message);
              }
              this.loading = false;
            })
            .catch(error => {
              console.error('保存个人信息失败:', error);
              this.$message.error('保存失败，请稍后重试');
              this.loading = false;
            });
        } else {
          return false;
        }
      });
    },
    
    handleCancel() {
      this.loadUserInfo();
    },
    
    handlePasswordUpdate() {
      this.$refs.passwordForm.validate(valid => {
        if (valid) {
          this.passwordLoading = true;
          
          // 获取用户ID
          const userInfoStr = localStorage.getItem('userInfo');
          const userId = userInfoStr ? JSON.parse(userInfoStr).id || '1' : '1';
          
          // 调用后端API修改密码
          this.$axios.post('/api/user/change-password', {
            user_id: userId,
            current_password: this.passwordForm.currentPassword,
            new_password: this.passwordForm.newPassword,
            confirm_password: this.passwordForm.confirmPassword
          })
            .then(result => {
              this.passwordLoading = false;
              if (result.success) {
                this.$message({
                  message: result.message || '密码修改成功，请重新登录',
                  type: 'success'
                });
                
                // 清除登录信息并跳转到登录页
                localStorage.removeItem('token');
                localStorage.removeItem('userInfo');
                this.$router.push('/login');
              } else {
                this.$message.error('修改失败: ' + result.message);
              }
            })
            .catch(error => {
              console.error('修改密码失败:', error);
              this.$message.error('修改失败，请稍后重试');
              this.passwordLoading = false;
            });
        } else {
          return false;
        }
      });
    },
    
    resetPasswordForm() {
      this.$refs.passwordForm.resetFields();
    }
  }
}
</script>

<style scoped>
.profile-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 120px);
}

.profile-header {
  margin-bottom: 20px;
}

.profile-header h2 {
  font-size: 20px;
  color: #303133;
  margin: 0;
}

.profile-card,
.password-card {
  margin-bottom: 20px;
}

.user-info-form,
.password-form {
  margin-top: 20px;
}

.card-title {
  font-size: 16px;
  color: #303133;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.el-form-item {
  margin-bottom: 20px;
}

.el-button {
  margin-right: 10px;
}
</style>