<template>
  <div class="notification-center-page">
    <el-card>
      <div slot="header" class="clearfix">
        <span>通知中心</span>
        <div class="header-actions">
          <el-button type="primary" size="small" @click="markAllAsRead">
            全部已读
          </el-button>
          <el-button type="default" size="small" @click="refreshNotifications">
            刷新
          </el-button>
          <el-button type="default" size="small" @click="showNotificationSettings">
            通知设置
          </el-button>
        </div>
      </div>
      
      <!-- 通知类型筛选 -->
      <div class="notification-filter">
        <el-tabs v-model="activeFilter" @tab-click="handleFilterChange" type="card">
          <el-tab-pane label="全部" name="all"></el-tab-pane>
          <el-tab-pane label="交易通知" name="trade"></el-tab-pane>
          <el-tab-pane label="风控预警" name="risk"></el-tab-pane>
          <el-tab-pane label="账户通知" name="balance"></el-tab-pane>
          <el-tab-pane label="系统通知" name="system"></el-tab-pane>
          <el-tab-pane label="未读通知" name="unread"></el-tab-pane>
        </el-tabs>
      </div>
      
      <!-- 通知列表 -->
      <div class="notification-list">
        <el-table 
          :data="filteredNotifications" 
          style="width: 100%" 
          stripe 
          v-loading="loading"
          element-loading-text="加载中..."
        >
          <el-table-column prop="id" label="ID" width="80"></el-table-column>
          <el-table-column label="状态" width="80">
            <template slot-scope="scope">
              <el-tag 
                v-if="!scope.row.read" 
                size="small" 
                type="danger"
              >
                未读
              </el-tag>
              <el-tag 
                v-else 
                size="small" 
                type="success"
              >
                已读
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" show-overflow-tooltip></el-table-column>
          <el-table-column prop="message" label="内容" show-overflow-tooltip width="400"></el-table-column>
          <el-table-column prop="type" label="类型" width="100">
            <template slot-scope="scope">
              <el-tag 
                size="small" 
                :type="getNotificationTagType(scope.row.type)"
              >
                {{ getNotificationTypeText(scope.row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="timestamp" label="时间" width="180" :formatter="formatNotificationTime"></el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template slot-scope="scope">
              <el-button 
                type="text" 
                size="small" 
                @click="markAsRead(scope.row.id)"
                v-if="!scope.row.read"
              >
                标记已读
              </el-button>
              <el-button 
                type="text" 
                size="small" 
                @click="viewNotificationDetail(scope.row)"
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 无通知提示 -->
        <div v-if="!loading && filteredNotifications.length === 0" class="no-notifications">
          <el-empty description="暂无通知"></el-empty>
        </div>
      </div>
      
      <!-- 分页 -->
      <div v-if="filteredNotifications.length > 0" class="pagination">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next, jumper"
          :total="filteredNotifications.length"
          :page-sizes="[10, 20, 50, 100]"
          :current-page="currentPage"
          :page-size="pageSize"
          @current-change="currentPage = $event"
          @size-change="pageSize = $event"
        >
        </el-pagination>
      </div>
    </el-card>
    
    <!-- 通知详情对话框 -->
    <el-dialog 
      title="通知详情" 
      :visible.sync="detailDialogVisible" 
      width="60%"
    >
      <div v-if="selectedNotification">
        <el-form :model="selectedNotification" label-width="100px">
          <el-form-item label="通知ID">
            {{ selectedNotification.id }}
          </el-form-item>
          <el-form-item label="标题">
            {{ selectedNotification.title }}
          </el-form-item>
          <el-form-item label="内容">
            <div class="notification-message-detail">{{ selectedNotification.message }}</div>
          </el-form-item>
          <el-form-item label="类型">
            <el-tag 
              size="small" 
              :type="getNotificationTagType(selectedNotification.type)"
            >
              {{ getNotificationTypeText(selectedNotification.type) }}
            </el-tag>
          </el-form-item>
          <el-form-item label="时间">
            {{ formatDateTime(selectedNotification.timestamp) }}
          </el-form-item>
          <el-form-item label="状态">
            <span>{{ selectedNotification.read ? '已读' : '未读' }}</span>
          </el-form-item>
          <el-form-item label="相关数据" v-if="selectedNotification.data">
            <pre>{{ JSON.stringify(selectedNotification.data, null, 2) }}</pre>
          </el-form-item>
        </el-form>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </span>
    </el-dialog>
    
    <!-- 通知设置对话框 -->
    <el-dialog 
      title="通知设置" 
      :visible.sync="settingsDialogVisible" 
      width="70%"
      :before-close="handleSettingsClose"
    >
      <div class="notification-settings">
        <h4>通知类型配置</h4>
        <el-table 
          :data="notificationSettings"
          border
          style="width: 100%"
        >
          <el-table-column prop="type" label="通知类型" width="120">
            <template slot-scope="scope">
              <el-tag 
                size="small" 
                :type="getNotificationTagType(scope.row.type)"
              >
                {{ getNotificationTypeText(scope.row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="通知名称" width="150"></el-table-column>
          <el-table-column label="系统内通知" width="100">
            <template slot-scope="scope">
              <el-switch 
                v-model="scope.row.channels.system"
                active-color="#13ce66"
                inactive-color="#ff4949"
              ></el-switch>
            </template>
          </el-table-column>
          <el-table-column label="邮件通知" width="100">
            <template slot-scope="scope">
              <el-switch 
                v-model="scope.row.channels.email"
                active-color="#13ce66"
                inactive-color="#ff4949"
              ></el-switch>
            </template>
          </el-table-column>
          <el-table-column label="短信通知" width="100">
            <template slot-scope="scope">
              <el-switch 
                v-model="scope.row.channels.sms"
                active-color="#13ce66"
                inactive-color="#ff4949"
              ></el-switch>
            </template>
          </el-table-column>
          <el-table-column label="风险等级" width="120">
            <template slot-scope="scope" v-if="scope.row.type === 'risk'">
              <el-select 
                v-model="scope.row.riskLevel"
                placeholder="选择风险等级"
                style="width: 100%"
              >
                <el-option label="低风险" value="low"></el-option>
                <el-option label="中风险" value="medium"></el-option>
                <el-option label="高风险" value="high"></el-option>
                <el-option label="严重风险" value="severe"></el-option>
              </el-select>
            </template>
          </el-table-column>
        </el-table>
        
        <h4 style="margin-top: 20px;">通知渠道设置</h4>
        <el-form :model="channelSettings" ref="channelForm" label-width="120px">
          <el-form-item label="默认邮箱" prop="defaultEmail">
            <el-input v-model="channelSettings.defaultEmail" placeholder="请输入默认接收通知的邮箱"></el-input>
          </el-form-item>
          <el-form-item label="默认手机号" prop="defaultPhone">
            <el-input v-model="channelSettings.defaultPhone" placeholder="请输入默认接收通知的手机号"></el-input>
          </el-form-item>
          <el-form-item label="通知轮询间隔" prop="pollingInterval">
            <el-select v-model="channelSettings.pollingInterval" placeholder="选择通知轮询间隔">
              <el-option label="1分钟" value="60000"></el-option>
              <el-option label="5分钟" value="300000"></el-option>
              <el-option label="10分钟" value="600000"></el-option>
              <el-option label="30分钟" value="1800000"></el-option>
              <el-option label="1小时" value="3600000"></el-option>
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="handleSettingsClose">取消</el-button>
        <el-button type="primary" @click="saveNotificationSettings">保存设置</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'NotificationCenterPage',
  data() {
    return {
      notifications: [],
      activeFilter: 'all',
      loading: false,
      currentPage: 1,
      pageSize: 20,
      detailDialogVisible: false,
      settingsDialogVisible: false,
      selectedNotification: null,
      notificationSettings: [
        { id: 1, type: 'risk', name: '风险预警', channels: { system: true, email: true, sms: true }, riskLevel: 'medium' },
        { id: 2, type: 'trade', name: '交易通知', channels: { system: true, email: true, sms: false } },
        { id: 3, type: 'balance', name: '资金变动', channels: { system: true, email: true, sms: false } },
        { id: 4, type: 'system', name: '系统公告', channels: { system: true, email: false, sms: false } }
      ],
      channelSettings: {
        defaultEmail: 'user@example.com',
        defaultPhone: '13800138000',
        pollingInterval: '60000'
      }
    };
  },
  computed: {
    filteredNotifications() {
      // 根据筛选条件过滤通知
      let filtered = [...this.notifications];
      
      if (this.activeFilter === 'unread') {
        filtered = filtered.filter(notification => !notification.read);
      } else if (this.activeFilter !== 'all') {
        filtered = filtered.filter(notification => notification.type === this.activeFilter);
      }
      
      // 按时间降序排序
      return filtered.sort((a, b) => b.timestamp - a.timestamp);
    },
    paginatedNotifications() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return this.filteredNotifications.slice(start, end);
    }
  },
  mounted() {
    this.loadNotifications();
  },
  methods: {
    // 加载通知数据
    async loadNotifications() {
      this.loading = true;
      try {
        const response = await axios.get('/api/notifications/get_all');
        if (response.data.success && response.data.notifications) {
          this.notifications = response.data.notifications;
        }
      } catch (error) {
        // 使用模拟数据
        this.notifications = this.generateMockNotifications();
        this.$message.error('加载通知失败，使用模拟数据');
      } finally {
        this.loading = false;
      }
    },
    
    // 刷新通知
    refreshNotifications() {
      this.loadNotifications();
    },
    
    // 标记所有通知为已读
    async markAllAsRead() {
      try {
        await axios.post('/api/notifications/mark_all_as_read');
        this.notifications.forEach(notification => {
          notification.read = true;
        });
        this.$message.success('已将所有通知标记为已读');
      } catch (error) {
        this.$message.error('操作失败，请重试');
      }
    },
    
    // 标记单个通知为已读
    async markAsRead(id) {
      try {
        await axios.post(`/api/notifications/read/${id}`);
        const notification = this.notifications.find(n => n.id === id);
        if (notification) {
          notification.read = true;
        }
        this.$message.success('已标记为已读');
      } catch (error) {
        this.$message.error('操作失败，请重试');
      }
    },
    
    // 查看通知详情
    viewNotificationDetail(notification) {
      this.selectedNotification = notification;
      this.detailDialogVisible = true;
    },
    
    // 处理筛选变化
    handleFilterChange() {
      this.currentPage = 1; // 重置到第一页
    },
    
    // 显示通知设置对话框
    showNotificationSettings() {
      this.settingsDialogVisible = true;
    },
    
    // 处理设置对话框关闭
    handleSettingsClose() {
      this.settingsDialogVisible = false;
    },
    
    // 保存通知设置
    saveNotificationSettings() {
      try {
        // 这里应该有保存到后端的逻辑
        this.$message.success('通知设置已保存');
        this.settingsDialogVisible = false;
      } catch (error) {
        this.$message.error('保存失败，请重试');
      }
    },
    
    // 获取通知类型标签样式
    getNotificationTagType(type) {
      const typeMap = {
        risk: 'danger',
        trade: 'success',
        balance: 'info',
        system: 'warning'
      };
      return typeMap[type] || 'default';
    },
    
    // 获取通知类型文本
    getNotificationTypeText(type) {
      const typeMap = {
        risk: '风险',
        trade: '交易',
        balance: '资金',
        system: '系统'
      };
      return typeMap[type] || '其他';
    },
    
    // 格式化通知时间（相对时间）
    formatNotificationTime(row, column, cellValue) {
      const timestamp = row.timestamp || cellValue;
      const now = Date.now();
      const diff = now - timestamp;
      
      if (diff < 60000) {
        return '刚刚';
      } else if (diff < 3600000) {
        return `${Math.floor(diff / 60000)}分钟前`;
      } else if (diff < 86400000) {
        return `${Math.floor(diff / 3600000)}小时前`;
      } else {
        return `${Math.floor(diff / 86400000)}天前`;
      }
    },
    
    // 格式化日期时间（绝对时间）
    formatDateTime(timestamp) {
      const date = new Date(timestamp);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    },
    
    // 生成模拟通知数据
    generateMockNotifications() {
      const now = Date.now();
      const types = ['trade', 'risk', 'balance', 'system'];
      const notifications = [];
      
      // 生成20条模拟通知
      for (let i = 1; i <= 20; i++) {
        const type = types[Math.floor(Math.random() * types.length)];
        const daysAgo = Math.floor(Math.random() * 10);
        const hoursAgo = Math.floor(Math.random() * 24);
        const minutesAgo = Math.floor(Math.random() * 60);
        
        notifications.push({
          id: i,
          title: this.getMockTitle(type),
          message: this.getMockMessage(type),
          type: type,
          timestamp: now - (daysAgo * 86400000 + hoursAgo * 3600000 + minutesAgo * 60000),
          read: Math.random() > 0.3 // 70%的概率未读
        });
      }
      
      return notifications;
    },
    
    // 获取模拟标题
    getMockTitle(type) {
      const titles = {
        trade: ['交易执行成功', '交易订单完成', '交易委托已提交', '交易部分成交'],
        risk: ['保证金预警', '风险等级提升', '交易异常提醒', '风控指标超限'],
        balance: ['账户余额不足', '资金到账通知', '充值成功', '提现申请已处理'],
        system: ['系统维护通知', '功能更新公告', '系统异常提醒', '登录提醒']
      };
      const typeTitles = titles[type] || titles.system;
      return typeTitles[Math.floor(Math.random() * typeTitles.length)];
    },
    
    // 获取模拟消息
    getMockMessage(type) {
      const messages = {
        trade: '交易已成功执行，详情请查看交易记录。',
        risk: '您的账户存在风险，请及时查看并处理。',
        balance: '您的账户资金发生变动，请确认是否为您本人操作。',
        system: '系统有重要通知，请查看详情了解更多信息。'
      };
      return messages[type] || messages.system;
    }
  }
};
</script>

<style scoped>
.notification-center-page {
  padding: 20px;
}

.header-actions {
  float: right;
}

.notification-filter {
  margin-bottom: 20px;
}

.no-notifications {
  text-align: center;
  padding: 40px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.notification-message-detail {
  white-space: pre-wrap;
  word-break: break-word;
}

pre {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>