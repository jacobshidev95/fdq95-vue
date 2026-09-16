import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import ForgotPasswordView from '@/views/ForgotPasswordView.vue'
import ResetPasswordView from '@/views/ResetPasswordView.vue'
import JobsView from '@/views/JobsView.vue'
import VideoPlayerView from '@/views/VideoPlayerView.vue'
import PublisherView from '@/views/PublisherView.vue'
import CommentsView from '@/views/CommentsView.vue'
import ProfileView from '@/views/ProfileView.vue'
import MessageView from '@/views/MessageView.vue'
import UserVideosView from '@/views/UserVideosView.vue'
import ActivityReplayView from '@/views/ActivityReplayView.vue'
import ProductsView from '@/views/ProductsView.vue'
import FriendsView from '@/views/FriendsView.vue'
import FaceEnrollView from '@/views/FaceEnrollView.vue'
import FaceLoginView from '@/views/FaceLoginView.vue'
import AdminLoginView from '@/views/AdminLoginView.vue'
import AdminDashboardView from '@/views/AdminDashboardView.vue'

const ADMIN_LEVELS = ['level_0', 'level_1', 'level_2']

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/login', name: 'login', component: LoginView },
    { path: '/register', name: 'register', component: RegisterView },
    { path: '/forgot-password', name: 'forgot-password', component: ForgotPasswordView },
    { path: '/reset-password', name: 'reset-password', component: ResetPasswordView },

    { path: '/face/enroll', name: 'face-enroll', component: FaceEnrollView },
    { path: '/face/login', name: 'face-login', component: FaceLoginView },

    { path: '/jobs', name: 'jobs', component: JobsView },
    { path: '/videos', name: 'videos', component: VideoPlayerView },
    { path: '/videos/publisher/:id', name: 'publisher', component: PublisherView },
    { path: '/videos/comments/:id', name: 'comments', component: CommentsView },
    { path: '/profile', name: 'profile-self', component: ProfileView },
    { path: '/profile/:userId', name: 'profile-user', component: ProfileView },
    { path: '/messages/:userId', name: 'messages', component: MessageView },
    { path: '/user/:userId/videos', name: 'user-videos', component: UserVideosView },
    { path: '/user/:userId/activity-replay', name: 'user-activity-replay', component: ActivityReplayView },
    { path: '/user/:userId/products', name: 'user-products', component: ProductsView },
    { path: '/friends', name: 'friends', component: FriendsView },

    // ---- admin portal ----
    {
      path: '/admin/login',
      name: 'admin-login',
      component: AdminLoginView,
      meta: { adminLogin: true },
    },
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: AdminDashboardView,
      meta: { requiresAdmin: true },
    },
    // legacy redirect
    { path: '/admin/users', redirect: '/admin/dashboard' },
  ],
})

// ---- global guard ----
router.beforeEach(async (to) => {
  // Guard 1: admin-only pages
  if (to.meta.requiresAdmin) {
    const token = localStorage.getItem('fdq95_token')
    if (!token) {
      return { path: '/admin/login', query: { redirect: to.fullPath } }
    }
    // We rely on the cached user from a previous /users/me call.
    // If not present, do a one-off fetch.
    try {
      const resp = await fetch('/users/me', {
        headers: { Authorization: 'Bearer ' + token },
      })
      if (!resp.ok) {
        return { path: '/admin/login' }
      }
      const user = await resp.json()
      if (!ADMIN_LEVELS.includes(user.provider_level)) {
        return { path: '/profile' }
      }
    } catch {
      return { path: '/admin/login' }
    }
  }

  // Guard 2: already-authenticated admins should not see /admin/login
  if (to.meta.adminLogin) {
    const token = localStorage.getItem('fdq95_token')
    if (token) {
      try {
        const resp = await fetch('/users/me', {
          headers: { Authorization: 'Bearer ' + token },
        })
        if (resp.ok) {
          const user = await resp.json()
          if (ADMIN_LEVELS.includes(user.provider_level)) {
            return { path: '/admin/dashboard' }
          }
        }
      } catch {
        /* ignore, allow login page */
      }
    }
  }

  return true
})

export default router