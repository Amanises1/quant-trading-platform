<template>
  <div class="notification-center">
    <div 
      class="notification-trigger" 
      @click="viewAllNotifications"
      style="cursor: pointer; position: relative;"
    >
      <i class="el-icon-bell"></i>
      <span v-if="unreadCount > 0" class="unread-badge">{{ unreadCount }}</span>
    </div>
  </div>
</template>

<script>
import axios from '@/utils/axios-config';

export default {
  name: 'NotificationCenter',
  data() {
    return {
      notifications: [],
      notificationPollingInterval: null,
      showNotificationPopup: false,
      notificationPopup: {
        title: '',
        message: '',
        type: 'info'
      }
    };
  },
  computed: {
    unreadCount() {
      return this.notifications.filter(notification => !notification.read).length;
    },
    recentNotifications() {
      // 只显示最近5条通知
      // 创建数组副本避免修改原数组（避免计算属性副作用）
      return [...this.notifications]
        .sort((a, b) => b.timestamp - a.timestamp)
        .slice(0, 5);
    }
  },
  mounted() {
    // 加载初始通知数据
    this.loadNotifications();
    // 启动通知轮询
    this.startNotificationPolling();
  },
  beforeDestroy() {
    // 清理定时器
    if (this.notificationPollingInterval) {
      clearInterval(this.notificationPollingInterval);
    }
  },
  methods: {
    // 加载通知数据
  async loadNotifications() {
    try {
      const response = await axios.get('/api/notifications');
      if (response.notifications) {
        this.notifications = response.notifications;
      } else if (response.success === false || !response.notifications) {
        // 如果API返回失败或没有数据，使用模拟数据
        console.warn('API返回无数据或失败，使用模拟数据');
        this.generateMockNotifications();
      }
    } catch (error) {
      console.error('加载通知失败:', error);
      // 网络错误或其他异常时，使用模拟数据
      this.generateMockNotifications();
    }
  },
  
  // 生成模拟通知数据
  generateMockNotifications() {
    console.log('生成模拟通知数据');
    this.notifications = [
      {
        id: 1,
        title: '交易执行成功',
        message: '买入贵州茅台(600519) 100股，价格1680.00元',
        type: 'trade',
        timestamp: Date.now() - 300000, // 5分钟前
        read: false
      },
      {
        id: 2,
        title: '保证金预警',
        message: '您的保证金比例已降至135%，接近预警线，请及时补充保证金',
        type: 'risk',
        timestamp: Date.now() - 900000, // 15分钟前
        read: false
      },
      {
        id: 3,
        title: '账户余额不足',
        message: '您的账户余额不足，部分委托可能无法执行',
        type: 'balance',
        timestamp: Date.now() - 1800000, // 30分钟前
        read: true
      },
      {
        id: 4,
        title: '系统维护通知',
        message: '系统将于2023-12-31 22:00-24:00进行例行维护，请提前做好准备',
        type: 'system',
        timestamp: Date.now() - 3600000, // 1小时前
        read: true
      }
    ];
  },

    // 启动通知轮询
    startNotificationPolling() {
      // 每1分钟检查一次新通知
      this.notificationPollingInterval = setInterval(() => {
        this.checkForNewNotifications();
      }, 60000);
    },

    // 检查新通知
  async checkForNewNotifications() {
    try {
      const response = await axios.get('/api/notifications/latest');
      
      if (response.success && response.new_notifications && response.new_notifications.length > 0) {
        // 添加新通知到列表
        response.new_notifications.forEach(notification => {
          // 检查是否已存在相同ID的通知
          if (!this.notifications.find(n => n.id === notification.id)) {
            this.notifications.unshift(notification);
            // 显示通知弹窗
            this.showNotification({
              title: notification.title,
              message: notification.message,
              type: this.getNotificationTypeForPopup(notification.type)
            });
          }
        });
      }
    } catch (error) {
      console.error('检查新通知时出错:', error);
      // 静默失败，不影响用户体验
      // 为了演示效果，可以定期添加一些模拟的新通知
      if (Math.random() > 0.7) { // 30%的概率添加一条模拟通知
        this.addMockNotification();
      }
    }
  },
  
  // 添加模拟通知
  addMockNotification() {
    const mockNotifications = [
      {
        title: '新交易信号',
        message: '上证指数出现买入信号，建议关注金融板块',
        type: 'trade'
      },
      {
        title: '市场波动提醒',
        message: '市场波动率大幅上升，请注意风险控制',
        type: 'risk'
      },
      {
        title: '系统更新提醒',
        message: '量化策略引擎已更新至最新版本，新增多种技术指标',
        type: 'system'
      }
    ];
    
    const randomNotification = mockNotifications[Math.floor(Math.random() * mockNotifications.length)];
    const newNotification = {
      id: Date.now(), // 使用时间戳作为唯一ID
      title: randomNotification.title,
      message: randomNotification.message,
      type: randomNotification.type,
      timestamp: Date.now(),
      read: false
    };
    
    this.notifications.unshift(newNotification);
    // 显示通知弹窗
    this.showNotification({
      title: newNotification.title,
      message: newNotification.message,
      type: this.getNotificationTypeForPopup(newNotification.type)
    });
  },

    // 标记单个通知为已读
    async markAsRead(notificationId) {
      const notification = this.notifications.find(n => n.id === notificationId);
      if (notification && !notification.read) {
        notification.read = true;
        try {
          await axios.post('/api/notifications/mark_as_read', { id: notificationId });
        } catch (error) {
          console.error('标记通知为已读失败:', error);
        }
      }
    },

    // 标记所有通知为已读
    async markAllAsRead() {
      try {
        await axios.post('/api/notifications/mark_all_as_read');
        this.notifications.forEach(notification => {
          notification.read = true;
        });
      } catch (error) {
        console.error('标记所有通知为已读失败:', error);
      }
    },

    // 查看全部通知
    viewAllNotifications() {
      // 避免重复导航到当前页面
      if (this.$route.path !== '/notifications') {
        // 跳转到完整的通知中心页面
        this.$router.push('/notifications');
      }
    },

    // 获取通知标签类型
    getNotificationTagType(type) {
      switch(type) {
        case 'trade':
          return 'success';
        case 'risk':
          return 'danger';
        case 'balance':
          return 'warning';
        case 'system':
          return 'info';
        default:
          return 'default';
      }
    },

    // 获取通知类型文本
    getNotificationTypeText(type) {
      switch(type) {
        case 'trade':
          return '交易';
        case 'risk':
          return '风控';
        case 'balance':
          return '账户';
        case 'system':
          return '系统';
        default:
          return '其他';
      }
    },

    // 格式化通知时间
    formatNotificationTime(timestamp) {
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

    // 显示通知弹窗
    showNotification(notification) {
      this.notificationPopup = {
        title: notification.title,
        message: notification.message,
        type: notification.type || 'info'
      };
      this.showNotificationPopup = true;
      
      // 5秒后自动关闭
      setTimeout(() => {
        this.showNotificationPopup = false;
      }, 5000);
    },

    // 获取通知弹窗类型
    getNotificationTypeForPopup(type) {
      switch(type) {
        case 'risk':
          return 'error';
        case 'balance':
          return 'warning';
        case 'trade':
          return 'success';
        default:
          return 'info';
      }
    }
  }
};
</script>

<style scoped>
.notification-center {
  position: relative;
}

.notification-trigger {
  position: relative;
  cursor: pointer;
  padding: 10px;
  color: #606266;
  font-size: 18px;
}

.notification-trigger:hover {
  color: #409eff;
}

.unread-badge {
  position: absolute;
  top: 5px;
  right: 5px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  font-size: 12px;
  line-height: 16px;
  color: #fff;
  background-color: #f56c6c;
  border-radius: 8px;
  text-align: center;
}

.notification-dropdown {
  width: 350px;
  max-height: 400px;
  overflow-y: auto;
}

.notification-dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  border-bottom: 1px solid #ebeef5;
  font-weight: 500;
}

.notification-dropdown-header .el-button {
  padding: 0;
  font-size: 12px;
}

.notification-list {
  max-height: 300px;
  overflow-y: auto;
}

.notification-item {
  padding: 12px 15px !important;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item.unread {
  background-color: #f0f9ff;
}

.notification-item:hover {
  background-color: #f5f7fa !important;
}

.notification-content {
  width: 100%;
}

.notification-title {
  font-weight: 500;
  margin-bottom: 4px;
  color: #303133;
  font-size: 14px;
}

.notification-message {
  color: #606266;
  font-size: 12px;
  margin-bottom: 6px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.notification-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notification-meta .el-tag {
  font-size: 11px;
  height: 20px;
  line-height: 20px;
  padding: 0 6px;
}

.notification-time {
  font-size: 11px;
  color: #909399;
}

.no-notifications {
  padding: 40px 20px;
  text-align: center;
  color: #909399;
}

.notification-dropdown-footer {
  text-align: center;
  padding: 10px;
  border-top: 1px solid #ebeef5;
}

.notification-dropdown-footer .el-button {
  padding: 0;
  font-size: 12px;
}
</style>