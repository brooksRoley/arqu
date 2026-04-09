<template>
  <div class="min-h-screen bg-gray-950 text-gray-100 p-6">
    <div class="max-w-7xl mx-auto space-y-8">

      <!-- Header -->
      <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold tracking-tight">Analytics</h1>
        <button @click="refresh" class="text-sm text-gray-400 hover:text-white transition-colors">
          Refresh
        </button>
      </div>

      <div v-if="error" class="bg-red-900/30 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
        {{ error }}
      </div>

      <!-- Funnel -->
      <section>
        <h2 class="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">Conversion Funnel</h2>
        <div class="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-3">
          <div
            v-for="step in funnel"
            :key="step.step"
            class="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center"
          >
            <div class="text-2xl font-bold text-white">{{ step.count }}</div>
            <div class="text-xs text-purple-400 font-semibold mt-0.5">{{ step.pct }}%</div>
            <div class="text-xs text-gray-500 mt-1 leading-tight">{{ funnelLabel(step.step) }}</div>
          </div>
        </div>
      </section>

      <!-- Connector Stats -->
      <section>
        <h2 class="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">Connectors</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div
            v-for="c in connectors"
            :key="c.provider"
            class="bg-gray-900 border border-gray-800 rounded-xl p-5"
          >
            <div class="flex items-center justify-between mb-3">
              <span class="font-semibold capitalize">{{ c.provider }}</span>
              <span class="text-xs text-gray-500">{{ c.connection_rate_pct }}% connected</span>
            </div>

            <!-- Connection bar -->
            <div class="h-1.5 bg-gray-800 rounded-full mb-3">
              <div
                class="h-1.5 bg-purple-500 rounded-full transition-all"
                :style="{ width: `${Math.min(c.connection_rate_pct, 100)}%` }"
              ></div>
            </div>

            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-400">{{ c.connected_count }} users</span>
              <span v-if="c.avg_rating !== null" class="flex items-center gap-1 text-yellow-400">
                <span class="text-xs">★</span>
                {{ c.avg_rating.toFixed(1) }}
                <span class="text-gray-600 text-xs">({{ c.feedback_count }})</span>
              </span>
              <span v-else class="text-gray-600 text-xs">No ratings yet</span>
            </div>

            <div v-if="c.top_tags?.length" class="flex flex-wrap gap-1 mt-3">
              <span
                v-for="tag in c.top_tags.slice(0, 3)"
                :key="tag"
                class="text-xs px-2 py-0.5 bg-gray-800 rounded-full text-gray-400"
              >{{ tag.replace(/_/g, ' ') }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Users Table -->
      <section>
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xs font-semibold uppercase tracking-widest text-gray-500">
            Users
            <span class="ml-2 text-gray-600 normal-case text-xs font-normal">{{ usersTotal }} total</span>
          </h2>
          <div class="flex items-center gap-3">
            <input
              v-model="search"
              placeholder="Filter by email or name..."
              class="bg-gray-900 border border-gray-800 rounded-lg px-3 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-purple-500 w-56"
            />
          </div>
        </div>

        <div v-if="loading" class="text-center py-12 text-gray-600">Loading...</div>

        <div v-else class="overflow-x-auto rounded-xl border border-gray-800">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
                <th class="text-left px-4 py-3">User</th>
                <th class="text-left px-4 py-3">Joined</th>
                <th class="text-left px-4 py-3">Archetype</th>
                <th class="text-left px-4 py-3">Attachment</th>
                <th class="text-center px-4 py-3">Connectors</th>
                <th class="text-center px-4 py-3">Karma</th>
                <th class="text-center px-4 py-3">Accepts</th>
                <th class="text-center px-4 py-3">Journal</th>
                <th class="text-center px-4 py-3">Msgs</th>
                <th class="text-left px-4 py-3">Providers</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-800/50">
              <tr
                v-for="u in filteredUsers"
                :key="u.id"
                class="hover:bg-gray-900/50 transition-colors"
              >
                <td class="px-4 py-3">
                  <div class="font-medium text-white">{{ u.display_name || '—' }}</div>
                  <div class="text-gray-500 text-xs">{{ u.email }}</div>
                </td>
                <td class="px-4 py-3 text-gray-400 whitespace-nowrap">
                  {{ formatDate(u.created_at) }}
                </td>
                <td class="px-4 py-3">
                  <span v-if="u.archetype" class="text-purple-400 text-xs font-medium">{{ u.archetype }}</span>
                  <span v-else class="text-gray-700">—</span>
                </td>
                <td class="px-4 py-3">
                  <span v-if="u.attachment_style" class="text-blue-400 text-xs">{{ u.attachment_style }}</span>
                  <span v-else class="text-gray-700">—</span>
                </td>
                <td class="px-4 py-3 text-center">
                  <span
                    class="inline-block w-6 h-6 rounded-full text-xs font-bold leading-6 text-center"
                    :class="connectorColor(u.connector_count)"
                  >{{ u.connector_count }}</span>
                </td>
                <td class="px-4 py-3 text-center text-gray-300">{{ u.karma_total }}</td>
                <td class="px-4 py-3 text-center">
                  <span class="text-green-400">{{ u.matches_accepted }}</span>
                  <span class="text-gray-600">/</span>
                  <span class="text-red-400">{{ u.matches_rejected }}</span>
                </td>
                <td class="px-4 py-3 text-center text-gray-400">{{ u.journal_entry_count }}</td>
                <td class="px-4 py-3 text-center text-gray-400">{{ u.messages_sent }}</td>
                <td class="px-4 py-3">
                  <div class="flex gap-1 flex-wrap">
                    <span
                      v-for="p in (u.connected_providers || [])"
                      :key="p"
                      class="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400"
                    >{{ p }}</span>
                  </div>
                </td>
              </tr>
              <tr v-if="filteredUsers.length === 0">
                <td colspan="10" class="text-center py-8 text-gray-600">No users found</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="usersTotal > perPage" class="flex justify-center gap-2 mt-4">
          <button
            :disabled="usersPage <= 1"
            @click="goPage(usersPage - 1)"
            class="px-3 py-1.5 rounded-lg border border-gray-800 text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
          >Prev</button>
          <span class="px-3 py-1.5 text-sm text-gray-500">
            {{ usersPage }} / {{ Math.ceil(usersTotal / perPage) }}
          </span>
          <button
            :disabled="usersPage >= Math.ceil(usersTotal / perPage)"
            @click="goPage(usersPage + 1)"
            class="px-3 py-1.5 rounded-lg border border-gray-800 text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
          >Next</button>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/composables/useAuthStore'
import { useAdminStore } from '@/composables/useAdminStore'

const router = useRouter()
const { user } = useAuthStore()
const { users, usersTotal, usersPage, funnel, connectors, loading, error,
        fetchUsers, fetchFunnel, fetchConnectors } = useAdminStore()

const search = ref('')
const perPage = 50

// Guard — redirect non-admins
onMounted(async () => {
  if (!user.value?.is_admin) {
    router.replace('/')
    return
  }
  await refresh()
})

async function refresh() {
  await Promise.all([fetchFunnel(), fetchConnectors(), fetchUsers(1, perPage)])
}

async function goPage(page: number) {
  await fetchUsers(page, perPage)
}

const filteredUsers = computed(() => {
  const q = search.value.toLowerCase()
  if (!q) return users.value
  return users.value.filter(
    u => u.email.toLowerCase().includes(q) || (u.display_name || '').toLowerCase().includes(q)
  )
})

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function connectorColor(count: number) {
  if (count === 0) return 'bg-gray-800 text-gray-600'
  if (count === 1) return 'bg-yellow-900/50 text-yellow-400'
  if (count >= 2) return 'bg-green-900/50 text-green-400'
  return 'bg-gray-800 text-gray-500'
}

function funnelLabel(step: string) {
  const labels: Record<string, string> = {
    registered:              'Registered',
    completed_poll:          'Completed Poll',
    connected_any:           'Connected 1+',
    connected_2plus:         'Connected 2+',
    has_vibe_vector:         'Synthesized',
    completed_psychometrics: 'Psychometrics',
    played_game:             'Played Game',
    got_mutual_match:        'Matched',
    sent_message:            'Messaged',
  }
  return labels[step] ?? step
}
</script>
