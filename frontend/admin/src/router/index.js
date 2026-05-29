import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'login', component: () => import('@/views/LoginPage.vue') },
  { path: '/sign-up', name: 'sign-up', component: () => import('@/views/SignUpPage.vue') },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    children: [
      { path: '', name: 'dashboard', component: () => import('@/views/DashboardPage.vue') },
      { path: 'users', name: 'users', component: () => import('@/views/user/UserListPage.vue') },
      { path: 'users/create', name: 'user-create', component: () => import('@/views/user/UserCreatePage.vue') },
      { path: 'users/:id', name: 'user-detail', component: () => import('@/views/user/UserDetailPage.vue') },
      { path: 'rooms', name: 'rooms', component: () => import('@/views/room/RoomListPage.vue') },
      { path: 'rooms/:code', name: 'room-detail', component: () => import('@/views/room/RoomDetailPage.vue') },
      { path: 'qr', name: 'qr', component: () => import('@/views/QRStatusPage.vue') },
      { path: 'board/notify', name: 'board-notify', component: () => import('@/views/board/BoardNotifyPage.vue') },
      { path: 'board/inquiry', name: 'board-inquiry', component: () => import('@/views/board/BoardInquiryPage.vue') },
      { path: 'admins', name: 'admins', component: () => import('@/views/admin/AdminListPage.vue') },
      { path: 'admins/create', name: 'admin-create', component: () => import('@/views/admin/AdminCreatePage.vue') },
      { path: 'admins/pin', name: 'admin-pin', component: () => import('@/views/admin/AdminPinPage.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('admin_token')
  if (to.name !== 'login' && to.name !== 'sign-up' && !token) {
    next({ name: 'login' })
  } else {
    next()
  }
})

export default router
