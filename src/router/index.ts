import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue')
    },
    {
      path: '/koming',
      name: 'koming',
      component: () => import('../views/Koming.vue')
    },
    {
      path: '/multi',
      name: 'multi',
      component: () => import('../components/MultiStepForm.vue')
    },
    {
      path: '/Supplicant',
      name: 'Supplicant',
      component: () => import('../views/Supplicant.vue')
    },
    {
      path: '/descent',
      name: 'Descent',
      component: () => import('../views/Descent.vue')
    },
    {
      path: '/elora',
      name: 'elora',
      component: () => import('../views/Elora.vue')
    },
    {
      path: '/nature',
      name: 'nature',
      component: () => import('../views/NatureNurture.vue')
    },
    {
      path: '/therapy',
      name: 'therapy',
      component: () => import('../views/CouplesTherapy.vue')
    }
  ]
})

export default router
