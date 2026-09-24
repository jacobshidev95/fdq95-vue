import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import ForgotPasswordView from '@/views/ForgotPasswordView.vue'
import ResetPasswordView from '@/views/ResetPasswordView.vue'
import VerifyEmailView from '@/views/VerifyEmailView.vue'
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

// ★ 新增：4 个视频播放相关页面
import SearchView from '@/views/SearchView.vue'
import SettingsView from '@/views/SettingsView.vue'
import VideoShareView from '@/views/VideoShareView.vue'
import VideoCommentsView from '@/views/VideoCommentsView.vue'
import SettingsListPlaceholder from '@/views/SettingsListPlaceholder.vue'
import ChannelProfileView from '@/views/ChannelProfileView.vue'
import CreatorCenterView from '@/views/CreatorCenterView.vue'
import ArticlePlayerView from '@/views/ArticlePlayerView.vue'
import UserArticlesView from '@/views/UserArticlesView.vue'
import SettingsPublishArticleView from '@/views/SettingsPublishArticleView.vue'
import LiveHallView from '@/views/LiveHallView.vue'
import StartLiveView from '@/views/StartLiveView.vue'

const ADMIN_LEVELS = ['level_0', 'level_1', 'level_2']

import VideoRecorderView from '@/views/VideoRecorderView.vue'
import AIVideoStudioView from '@/views/AIVideoStudioView.vue'
import SettingsPublishVideoView from '@/views/SettingsPublishVideoView.vue'

// ★ 新增：视频直播页
import LiveStreamView from '@/views/LiveStreamView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/login', name: 'login', component: LoginView },
    { path: '/register', name: 'register', component: RegisterView },
    { path: '/forgot-password', name: 'forgot-password', component: ForgotPasswordView },
    { path: '/reset-password', name: 'reset-password', component: ResetPasswordView },

    // ★ 邮件验证页面：使用 /verify-email，避开 nginx 的 /auth/ 前缀
    { path: '/verify-email', name: 'verify-email', component: VerifyEmailView },

    // ★ 新增：视频播放页的辅助页面
    { path: '/search', name: 'search', component: SearchView },
    { path: '/settings', name: 'settings', component: SettingsView },

    { path: '/face/enroll', name: 'face-enroll', component: FaceEnrollView },
    { path: '/face/login', name: 'face-login', component: FaceLoginView },

    { path: '/jobs', name: 'jobs', component: JobsView },

    // ── 视频相关 ──
    { path: '/videos', name: 'videos', component: VideoPlayerView },
    { path: '/videos/publisher/:id', name: 'publisher', component: PublisherView },
    // 原有的评论页（旧版）
    { path: '/videos/comments/:id', name: 'comments', component: CommentsView },
    // ★ 新增：从视频播放页进入的评论 / 分享页
    { path: '/videos/:videoId/comments', name: 'video-comments', component: VideoCommentsView },
    { path: '/videos/:videoId/share', name: 'video-share', component: VideoShareView },
    // ★ 新增：视频录制页
    { path: '/record-video', name: 'record-video', component: VideoRecorderView },
    // ── 文章浏览页 ──
    { path: '/articles', name: 'articles', component: ArticlePlayerView },

    // ── 用户相关 ──
    { path: '/profile', name: 'profile-self', component: ProfileView },
    { path: '/profile/:userId', name: 'profile-user', component: ProfileView },
    { path: '/messages/:userId', name: 'messages', component: MessageView },
    { path: '/user/:userId/videos', name: 'user-videos', component: UserVideosView },
    { path: '/user/:userId/activity-replay', name: 'user-activity-replay', component: ActivityReplayView },
    { path: '/user/:userId/products', name: 'user-products', component: ProductsView },
    { path: '/friends', name: 'friends', component: FriendsView },
    { path: '/user/:userId/articles', name: 'user-articles', component: UserArticlesView },

    // ── AI 视频工作室 ──
    { path: '/ai-video-studio', name: 'ai-video-studio', component: AIVideoStudioView },

    // ★ 新增：视频直播页

    { path: '/live',              name: 'live-hall', component: LiveHallView,    meta: { hideChrome: true } },
    { path: '/live/:roomId',      name: 'live-room', component: LiveStreamView,  meta: { hideChrome: true } },
    { path: '/live/:roomId/host', name: 'live-host', component: LiveStreamView,  meta: { hideChrome: true, host: true } },

    // ── 设置页及其子页 ──
    {
      path: '/settings/likes',
      name: 'settings-likes',
      component: SettingsListPlaceholder,
      meta: { title: '点赞', apiPath: '/api/profile/likes' },
    },
    {
      path: '/settings/follows',
      name: 'settings-follows',
      component: SettingsListPlaceholder,
      meta: { title: '关注', apiPath: '/api/social/following/list' },
    },
    {
      path: '/settings/messages',
      name: 'settings-messages',
      component: SettingsListPlaceholder,
      meta: { title: '消息', apiPath: '/api/messages/inbox' },
    },
    {
      path: '/settings/dms',
      name: 'settings-dms',
      component: SettingsListPlaceholder,
      meta: { title: '私信', apiPath: '/api/messages/direct' },
    },
    {
      path: '/settings/channel',
      name: 'settings-channel',
      component: ChannelProfileView,
    },
    {
      path: '/settings/channel/notifications',
      name: 'settings-channel-notifs',
      component: SettingsListPlaceholder,
      meta: { title: '视频号消息', apiPath: '/api/profile/channel-notifications' },
    },
    {
      path: '/settings/channel/dms',
      name: 'settings-channel-dms',
      component: SettingsListPlaceholder,
      meta: { title: '视频号私信', apiPath: '/api/messages/channel-dms' },
    },
    // ★ 新增：创作中心
    {
      path: '/settings/creator-center',
      name: 'settings-creator-center',
      component: CreatorCenterView,
    },
    {
      path: '/settings/creator/verifications',
      name: 'settings-creator-verifications',
      component: SettingsListPlaceholder,
      meta: { title: '账号认证', apiPath: '/api/creator/verifications' },
    },
    {
      path: '/settings/creator/stats',
      name: 'settings-creator-stats',
      component: SettingsListPlaceholder,
      meta: { title: '浏览数据统计', apiPath: '/api/creator/stats' },
    },
    {
      path: '/settings/creator/audience',
      name: 'settings-creator-audience',
      component: SettingsListPlaceholder,
      meta: { title: '观众分析', apiPath: '/api/creator/audience' },
    },
    {
      path: '/settings/creator/revenue',
      name: 'settings-creator-revenue',
      component: SettingsListPlaceholder,
      meta: { title: '收入详情', apiPath: '/api/creator/revenue' },
    },
    {
      path: '/settings/creator/tools',
      name: 'settings-creator-tools',
      component: SettingsListPlaceholder,
      meta: { title: '服务工具', apiPath: '/api/creator/tools' },
    },

    // ── 发布相关 ──
    {
      path: '/settings/publish-video',
      name: 'settings-publish-video',
      component: SettingsPublishVideoView,
    },
    {
      path: '/settings/publish-article',
      name: 'settings-publish-article',
      component: SettingsPublishArticleView,
    },

    // ★ 修改：发起直播 → 跳转到新的 /live 页面
    {
      path: '/settings/go-live',
      name: 'settings-go-live',
      component: StartLiveView,
    },
    {
      path: '/settings/launch-activity',
      name: 'settings-launch-activity',
      component: SettingsListPlaceholder,
      meta: { title: '发起活动', apiPath: '' },
    },

    // ── admin portal ──
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
    { path: '/admin/users', redirect: '/admin/dashboard' },
  ],
})

// ── global guard（未做任何改动） ──
router.beforeEach(async (to) => {
  if (to.meta.requiresAdmin) {
    const token = localStorage.getItem('fdq95_token')
    if (!token) {
      return { path: '/admin/login', query: { redirect: to.fullPath } }
    }
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
        /* ignore */
      }
    }
  }

  return true
})

export default router