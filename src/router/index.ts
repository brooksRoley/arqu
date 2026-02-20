import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/reader',
      name: 'reader',
      component: () => import('@/views/ReaderView.vue')
    },
    {
      path: '/zeromind',
      name: 'zeromind',
      component: () => import('@/views/ZeromindView.vue')
    },
    {
      path: '/glass',
      name: 'glass',
      component: () => import('@/views/GlassView.vue')
    },
    {
      path: '/audio',
      name: 'audio',
      component: () => import('@/views/AudioplayerView.vue')
    },
    {
      path: '/resume',
      name: 'resume',
      component: () => import('@/views/ResumeView.vue')
    },
    {
      path: '/spiral',
      name: 'spiral',
      component: () => import('@/views/SpiralView.vue')
    },
    {
      path: '/trance',
      name: 'trance',
      component: () => import('@/views/TranceView.vue')
    }
  ]
})

export default router
