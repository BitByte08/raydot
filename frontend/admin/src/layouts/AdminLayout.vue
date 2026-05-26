<template>
  <div class="admin-layout">
    <nav class="sidebar">
      <div class="sidebar-header">
        <h2>Raydot</h2>
      </div>
      <ul class="nav-menu">
        <li><router-link to="/">대시보드</router-link></li>
        <li><router-link to="/users">사용자</router-link></li>
        <li><router-link to="/rooms">정독실</router-link></li>
        <li><router-link to="/qr">QR</router-link></li>
        <li><router-link to="/board/notify">공지사항</router-link></li>
        <li><router-link to="/board/inquiry">문의사항</router-link></li>
      </ul>
      <div class="sidebar-footer">
        <button @click="handleLogout" class="logout-btn">로그아웃</button>
      </div>
    </nav>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function handleLogout() {
  localStorage.removeItem('admin_token')
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}
.sidebar {
  width: 220px;
  background: #1a1a2e;
  color: #fff;
  display: flex;
  flex-direction: column;
  padding: 20px 0;
}
.sidebar-header {
  padding: 0 20px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.sidebar-header h2 {
  font-size: 20px;
}
.nav-menu {
  list-style: none;
  flex: 1;
  padding: 10px 0;
}
.nav-menu li a {
  display: block;
  padding: 12px 20px;
  color: rgba(255,255,255,0.7);
  text-decoration: none;
  transition: all 0.2s;
}
.nav-menu li a:hover,
.nav-menu li a.router-link-active {
  background: rgba(255,255,255,0.1);
  color: #fff;
}
.sidebar-footer {
  padding: 0 20px;
}
.logout-btn {
  width: 100%;
  padding: 10px;
  background: rgba(255,255,255,0.1);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.logout-btn:hover {
  background: rgba(255,255,255,0.2);
}
.content {
  flex: 1;
  padding: 24px;
  background: #f0f0f5;
  overflow-y: auto;
}
</style>
