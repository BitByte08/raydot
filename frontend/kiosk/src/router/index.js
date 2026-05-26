import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'splash', component: () => import('@/views/SplashScreen.vue') },
  { path: '/login', name: 'login', component: () => import('@/views/LoginScreen.vue') },
  { path: '/wifi', name: 'wifi', component: () => import('@/views/WifiSettingsScreen.vue') },
  { path: '/password/initial', name: 'password-initial', component: () => import('@/views/auth/PasswordInitialScreen.vue') },
  { path: '/password/find', name: 'password-find', component: () => import('@/views/auth/PasswordFindScreen.vue') },
  { path: '/desk', name: 'desk', component: () => import('@/views/DeskScreen.vue') },
  { path: '/check-in', name: 'check-in', component: () => import('@/views/CheckInScreen.vue') },
  { path: '/check-out', name: 'check-out', component: () => import('@/views/CheckOutScreen.vue') },
  { path: '/move', name: 'move', component: () => import('@/views/MoveScreen.vue') },
  { path: '/qr', name: 'qr', component: () => import('@/views/QRDisplayScreen.vue') },
  { path: '/user/info', name: 'user-info', component: () => import('@/views/user/UserInfoScreen.vue') },
  { path: '/user/log', name: 'user-log', component: () => import('@/views/user/UserLogScreen.vue') },
  { path: '/user/password/reset', name: 'password-reset', component: () => import('@/views/user/PasswordResetScreen.vue') },
  { path: '/board/notify', name: 'board-notify', component: () => import('@/views/board/BoardNotifyScreen.vue') },
  { path: '/board/inquiry', name: 'board-inquiry', component: () => import('@/views/board/BoardInquiryScreen.vue') },
  { path: '/board/inquiry/new', name: 'board-inquiry-new', component: () => import('@/views/board/BoardInquiryNewScreen.vue') },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
