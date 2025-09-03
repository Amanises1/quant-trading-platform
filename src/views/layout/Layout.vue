<template>
  <div class="app-container">
    <Sidebar class="sidebar" @collapse-change="handleSidebarCollapse" />
    <div class="main-container" :class="{'is-collapsed': isCollapsed}">
      <Header class="header" />
      <div class="content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script>
import Header from '@/components/header/Header.vue'
import Sidebar from '@/components/siderbar/Sidebar.vue'

export default {
  name: 'Layout',
  components: {
    Header,
    Sidebar
  },
  data() {
    return {
      isCollapsed: false
    }
  },
  methods: {
    handleSidebarCollapse(isCollapsed) {
      this.isCollapsed = isCollapsed
    }
  }
}
</script>

<style scoped>
.app-container {
  height: 100vh;
  width: 100%;
  display: flex;
}

.sidebar {
  width: 220px;
  height: 100%;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 1001;
  transition: width 0.3s;
  overflow-y: auto;
}

.main-container {
  flex: 1;
  margin-left: 220px;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.3s;
}

.main-container.is-collapsed {
  margin-left: 64px;
}

.header {
  width: 100%;
}

.content {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
  background-color: #f5f7fa;
}
</style>