<template>
  <div class="app-container">
    <Sidebar class="sidebar" @collapse-change="handleSidebarCollapse" />
    <div class="main-container">
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
  overflow: hidden;
}

.sidebar {
  height: 100%;
  flex-shrink: 0;
  overflow-y: auto;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1);
  overflow: hidden;
}

.header {
  width: 100%;
}

.content {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
  background-color: #f5f7fa;
  transition: all 0.6s cubic-bezier(0.19, 1, 0.22, 1);
}
</style>