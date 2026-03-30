import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ── Auth ─────────────────────────────────────────────────────
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true }
    },

    // ── Hub ──────────────────────────────────────────────────────
    {
      path: '/',
      name: 'home',
      component: HomeView
    },

    // ── Experiences (existing) ───────────────────────────────────
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
      path: '/liquidglass',
      name: 'Song sandbox',
      component: () => import('@/views/LiquidGlassView.vue')
    },
    {
      path: '/audio',
      name: 'audio',
      component: () => import('@/views/AudioplayerView.vue')
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
    },
    {
      path: '/hypno',
      name: 'hypno',
      component: () => import('@/views/HypnoView.vue')
    },
    {
      path: '/poll',
      redirect: '/'
    },
    {
      path: '/webaudio',
      name: 'webaudio',
      component: () => import('@/views/WebAudioView.vue')
    },

    // ── Journal + Check-in (auth required) ──────────────────────
    {
      path: '/journal',
      name: 'journal',
      component: () => import('@/views/JournalView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/checkin',
      name: 'checkin',
      component: () => import('@/views/CheckInView.vue'),
      meta: { requiresAuth: true }
    },

    // ── OAuth callback routes ────────────────────────────────────
    {
      path: '/auth/google/callback',
      name: 'google-callback',
      component: () => import('@/views/GoogleCallback.vue')
    },
    {
      path: '/auth/x/callback',
      name: 'x-callback',
      component: () => import('@/views/XCallback.vue')
    },
    {
      path: '/auth/strava/callback',
      name: 'strava-callback',
      component: () => import('@/views/StravaCallback.vue')
    },

    // ── Vibe calibration (OAuth connections) ────────────────────
    {
      path: '/calibrate',
      name: 'calibrate',
      component: () => import('@/views/OauthView.vue'),
      meta: { requiresAuth: true }
    },

    // ── Peripheral data sync (auth required) ────────────────────
    {
      path: '/peripheral',
      name: 'peripheral',
      component: () => import('@/views/PeripheralSync.vue'),
      meta: { requiresAuth: true }
    },

    // ── Psychometrics / Psychoanalysis (auth required) ───────────
    {
      path: '/psychoanalysis',
      name: 'psychoanalysis',
      component: () => import('@/views/PsychoanalysisView.vue'),
      meta: { requiresAuth: true }
    },

    // ── Intake → Game pipeline (auth required) ──────────────────
    {
      path: '/intake',
      name: 'intake',
      component: () => import('@/views/IntakeView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/game',
      name: 'game',
      component: () => import('@/views/GameView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// ── Auth guard ──────────────────────────────────────────────────────
router.beforeEach((to) => {
  const token = localStorage.getItem('channelzero-jwt')

  // Redirect authenticated users away from guest-only pages
  if (to.meta.guest && token) {
    return { name: 'home' }
  }

  // Redirect unauthenticated users to login for protected pages
  if (to.meta.requiresAuth && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
})

export default router
