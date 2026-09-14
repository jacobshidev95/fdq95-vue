import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import JobsView from '@/views/JobsView.vue'
import VideoPlayerView from '@/views/VideoPlayerView.vue'
import PublisherView from '@/views/PublisherView.vue'
import CommentsView from '@/views/CommentsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/login', name: 'login', component: LoginView },
    { path: '/register', name: 'register', component: RegisterView },
    { path: '/jobs', name: 'jobs', component: JobsView },
    { path: '/videos', name: 'videos', component: VideoPlayerView },
    {
      path: '/videos/publisher/:id',
      name: 'publisher',
      component: PublisherView,
    },
    {
      path: '/videos/comments/:id',
      name: 'comments',
      component: CommentsView,
    },
  ],
})

export default router