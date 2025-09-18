<template>
  <div class="user-management-container">
    <h2>用户管理</h2>
    <p>此页面用于用户账户的管理和权限控制，包括查看、新增、编辑、删除用户和重置密码。</p>
    
    <!-- 操作按钮区域 -->
    <div class="action-buttons">
      <button class="el-button el-button--primary" @click="showAddUserModal">
        <i class="el-icon-plus"></i> 新增用户
      </button>
      <button class="el-button el-button--success" @click="refreshUserList">
        <i class="el-icon-refresh"></i> 刷新列表
      </button>
    </div>
    
    <!-- 用户表格 -->
    <div class="user-table-container">
      <el-table 
        v-loading="loading" 
        :data="users" 
        style="width: 100%" 
        border
        fit
      >
        <el-table-column prop="id" label="用户ID" width="80" align="center"></el-table-column>
        <el-table-column prop="username" label="用户名" width="180"></el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="200"></el-table-column>
        <el-table-column prop="phone" label="手机号" width="150"></el-table-column>
        <el-table-column prop="role" label="角色" width="100" align="center">
          <template slot-scope="scope">
            <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'success'">
              {{ scope.row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" align="center">
          <template slot-scope="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180" align="center">
          <template slot-scope="scope">
            {{ formatDate(scope.row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template slot-scope="scope">
            <div style="display: flex; gap: 8px;">
              <el-button type="primary" size="small" @click="showEditUserModal(scope.row)">
                编辑
              </el-button>
              <el-button type="warning" size="small" @click="showResetPasswordModal(scope.row)">
                重置密码
              </el-button>
              <el-button type="danger" size="small" @click="confirmDeleteUser(scope.row.id)" 
                        :disabled="scope.row.id === 1">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-if="total > 0"
          background
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          @current-change="handleCurrentChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>
    
    <!-- 新增用户弹窗 -->
    <el-dialog title="新增用户" :visible.sync="addUserVisible" width="500px">
      <el-form :model="addUserForm" :rules="userRules" ref="addUserForm" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="addUserForm.username" placeholder="请输入用户名"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input 
            :type="addUserPasswordVisible ? 'text' : 'password'" 
            v-model="addUserForm.password" 
            placeholder="请输入密码"
            suffix-icon="el-icon-view"
            @click.native="addUserPasswordVisible = !addUserPasswordVisible"
          ></el-input>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="addUserForm.email" placeholder="请输入邮箱"></el-input>
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="addUserForm.phone" placeholder="请输入手机号"></el-input>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="addUserForm.role" placeholder="请选择角色">
            <el-option label="普通用户" value="user"></el-option>
            <el-option label="管理员" value="admin"></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="addUserVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAddUser">确定</el-button>
      </div>
    </el-dialog>
    
    <!-- 编辑用户弹窗 -->
    <el-dialog title="编辑用户" :visible.sync="editUserVisible" width="500px">
      <el-form :model="editUserForm" :rules="userRulesWithoutPassword" ref="editUserForm" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="editUserForm.username" placeholder="请输入用户名"></el-input>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editUserForm.email" placeholder="请输入邮箱"></el-input>
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="editUserForm.phone" placeholder="请输入手机号"></el-input>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="editUserForm.role" placeholder="请选择角色">
            <el-option label="普通用户" value="user"></el-option>
            <el-option label="管理员" value="admin"></el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="editUserVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEditUser">确定</el-button>
      </div>
    </el-dialog>
    
    <!-- 重置密码弹窗 -->
    <el-dialog title="重置密码" :visible.sync="resetPasswordVisible" width="400px">
      <el-form :model="resetPasswordForm" :rules="resetPasswordRules" ref="resetPasswordForm" label-width="80px">
        <el-form-item label="新密码" prop="new_password">
          <el-input 
            :type="resetPasswordVisible1 ? 'text' : 'password'" 
            v-model="resetPasswordForm.new_password" 
            placeholder="请输入新密码"
            suffix-icon="el-icon-view"
            @click.native="resetPasswordVisible1 = !resetPasswordVisible1"
          ></el-input>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input 
            :type="resetPasswordVisible2 ? 'text' : 'password'" 
            v-model="resetPasswordForm.confirm_password" 
            placeholder="请再次输入新密码"
            suffix-icon="el-icon-view"
            @click.native="resetPasswordVisible2 = !resetPasswordVisible2"
          ></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="resetPasswordVisible = false">取消</el-button>
        <el-button type="primary" @click="submitResetPassword">确定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'UserManagement',
  data() {
    return {
      users: [], // 用户列表数据
      loading: false, // 加载状态
      total: 0, // 总条数
      currentPage: 1, // 当前页码
      pageSize: 10, // 每页条数
      
      // 新增用户相关
      addUserVisible: false,
      addUserForm: {
        username: '',
        password: '',
        email: '',
        phone: '',
        role: 'user'
      },
      
      // 编辑用户相关
      editUserVisible: false,
      editUserForm: {
        id: '',
        username: '',
        email: '',
        phone: '',
        role: 'user'
      },
      
      // 重置密码相关
      resetPasswordVisible: false,
      resetPasswordForm: {
        new_password: '',
        confirm_password: ''
      },
      currentUserId: '', // 当前操作的用户ID
      
      // 密码可见性控制
      addUserPasswordVisible: false,
      resetPasswordVisible1: false,
      resetPasswordVisible2: false,
      
      // 表单验证规则
      userRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
        ],
        phone: [
          { required: true, message: '请输入手机号', trigger: 'blur' },
          { pattern: /^1[3456789]\d{9}$/, message: '请输入正确的手机号格式', trigger: 'blur' }
        ],
        role: [
          { required: true, message: '请选择角色', trigger: 'change' }
        ]
      },
      
      // 不含密码的用户验证规则（用于编辑）
      userRulesWithoutPassword: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
        ],
        phone: [
          { required: true, message: '请输入手机号', trigger: 'blur' },
          { pattern: /^1[3456789]\d{9}$/, message: '请输入正确的手机号格式', trigger: 'blur' }
        ],
        role: [
          { required: true, message: '请选择角色', trigger: 'change' }
        ]
      },
      
      // 重置密码验证规则
      resetPasswordRules: {
        new_password: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
        ],
        confirm_password: [
          { required: true, message: '请再次输入新密码', trigger: 'blur' },
          { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' },
          {
            validator: (rule, value, callback) => {
              if (value !== this.resetPasswordForm.new_password) {
                callback(new Error('两次输入的密码不一致'))
              } else {
                callback()
              }
            },
            trigger: 'blur'
          }
        ]
      }
    }
  },
  mounted() {
    this.loadUserList()
  },
  methods: {
    // 加载用户列表
    loadUserList() {
      this.loading = true
      this.$axios.get('/api/users')
        .then(result => {
          if (result.success) {
            this.users = result.users
            this.total = result.users.length
          } else {
            this.$message.error(result.message || '获取用户列表失败')
          }
        })
        .catch(error => {
          console.error('获取用户列表失败:', error)
          this.$message.error('获取用户列表失败，请稍后重试')
        })
        .finally(() => {
          this.loading = false
        })
    },
    
    // 刷新用户列表
    refreshUserList() {
      this.currentPage = 1
      this.loadUserList()
    },
    
    // 显示新增用户弹窗
    showAddUserModal() {
      // 重置表单
      this.$refs.addUserForm && this.$refs.addUserForm.resetFields()
      this.addUserForm = {
        username: '',
        password: '',
        email: '',
        phone: '',
        role: 'user'
      }
      this.addUserVisible = true
    },
    
    // 提交新增用户
    submitAddUser() {
      this.$refs.addUserForm.validate(valid => {
        if (valid) {
          this.$axios.post('/api/users/create', this.addUserForm)
            .then(result => {
              if (result.success) {
                this.$message.success('用户创建成功')
                this.addUserVisible = false
                this.loadUserList()
              } else {
                this.$message.error(result.message || '用户创建失败')
              }
            })
            .catch(error => {
              console.error('创建用户失败:', error)
              this.$message.error('用户创建失败，请稍后重试')
            })
        }
      })
    },
    
    // 显示编辑用户弹窗
    showEditUserModal(user) {
      // 复制用户数据到编辑表单
      this.editUserForm = {
        id: user.id,
        username: user.username,
        email: user.email,
        phone: user.phone,
        role: user.role
      }
      this.editUserVisible = true
    },
    
    // 提交编辑用户
    submitEditUser() {
      this.$refs.editUserForm.validate(valid => {
        if (valid) {
          const userId = this.editUserForm.id
          // 移除id字段，因为API路径中包含了id
          const userData = { ...this.editUserForm }
          delete userData.id
          
          this.$axios.put(`/api/users/${userId}/update`, userData)
            .then(result => {
              if (result.success) {
                this.$message.success('用户信息更新成功')
                this.editUserVisible = false
                this.loadUserList()
              } else {
                this.$message.error(result.message || '用户信息更新失败')
              }
            })
            .catch(error => {
              console.error('更新用户信息失败:', error)
              this.$message.error('用户信息更新失败，请稍后重试')
            })
        }
      })
    },
    
    // 显示重置密码弹窗
    showResetPasswordModal(user) {
      this.currentUserId = user.id
      this.resetPasswordForm = {
        new_password: '',
        confirm_password: ''
      }
      this.$refs.resetPasswordForm && this.$refs.resetPasswordForm.resetFields()
      this.resetPasswordVisible = true
    },
    
    // 提交重置密码
    submitResetPassword() {
      this.$refs.resetPasswordForm.validate(valid => {
        if (valid) {
          const resetData = {
            new_password: this.resetPasswordForm.new_password
          }
          
          this.$axios.post(`/api/users/${this.currentUserId}/reset-password`, resetData)
            .then(result => {
              if (result.success) {
                this.$message.success('密码重置成功')
                this.resetPasswordVisible = false
                this.loadUserList()
              } else {
                this.$message.error(result.message || '密码重置失败')
              }
            })
            .catch(error => {
              console.error('重置密码失败:', error)
              this.$message.error('密码重置失败，请稍后重试')
            })
        }
      })
    },
    
    // 确认删除用户
    confirmDeleteUser(userId) {
      if (userId === 1) {
        this.$message.warning('不允许删除管理员用户')
        return
      }
      
      this.$confirm('确定要删除该用户吗？此操作不可撤销。', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.deleteUser(userId)
      }).catch(() => {
        this.$message.info('已取消删除')
      })
    },
    
    // 删除用户
    deleteUser(userId) {
      this.$axios.delete(`/api/users/${userId}/delete`)
        .then(result => {
          if (result.success) {
            this.$message.success('用户删除成功')
            this.loadUserList()
          } else {
            this.$message.error(result.message || '用户删除失败')
          }
        })
        .catch(error => {
          console.error('删除用户失败:', error)
          this.$message.error('用户删除失败，请稍后重试')
        })
    },
    
    // 格式化日期
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      const seconds = String(date.getSeconds()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
    },
    
    // 分页相关方法
    handleCurrentChange(current) {
      this.currentPage = current
    },
    
    handleSizeChange(size) {
      this.pageSize = size
      this.currentPage = 1
    }
  }
}
</script>

<style scoped>
.user-management-container {
  padding: 20px;
}

h2 {
  margin-bottom: 20px;
  color: #303133;
}

p {
  color: #606266;
  margin-bottom: 20px;
}

.action-buttons {
  margin-bottom: 20px;
}

.user-table-container {
  background-color: #fff;
  padding: 20px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.el-button + .el-button {
  margin-left: 10px;
}
</style>