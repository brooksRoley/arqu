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

      <!-- Funnel with drop-off rates -->
      <section>
        <h2 class="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">Conversion Funnel</h2>
        <div class="flex flex-wrap items-center gap-2">
          <template v-for="(step, i) in funnel" :key="step.step">
            <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center min-w-[100px]">
              <div class="text-2xl font-bold text-white">{{ step.count }}</div>
              <div class="text-xs text-purple-400 font-semibold mt-0.5">{{ step.pct }}%</div>
              <div class="text-xs text-gray-500 mt-1 leading-tight">{{ funnelLabel(step.step) }}</div>
            </div>
            <div v-if="i < funnel.length - 1" class="text-center px-1">
              <div class="text-gray-600 text-sm">→</div>
              <div
                class="text-xs font-medium"
                :class="dropOff(i) > 50 ? 'text-red-400' : dropOff(i) > 25 ? 'text-yellow-400' : 'text-green-400'"
              >-{{ dropOff(i) }}%</div>
            </div>
          </template>
        </div>
      </section>

      <!-- Match Rate Trends -->
      <section v-if="matchTrends">
        <h2 class="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">Match Rate Trends</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div class="text-xs text-gray-500 mb-2">Last 7 Days</div>
            <div class="text-3xl font-bold text-white">{{ matchTrends.seven_day.rate_pct }}%</div>
            <div class="h-1.5 bg-gray-800 rounded-full mt-3 mb-2">
              <div class="h-1.5 bg-purple-500 rounded-full transition-all" :style="{ width: `${Math.min(matchTrends.seven_day.rate_pct, 100)}%` }"></div>
            </div>
            <div class="text-xs text-gray-500">{{ matchTrends.seven_day.matched }} matched / {{ matchTrends.seven_day.players }} played</div>
          </div>
          <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div class="text-xs text-gray-500 mb-2">Last 30 Days</div>
            <div class="text-3xl font-bold text-white">{{ matchTrends.thirty_day.rate_pct }}%</div>
            <div class="h-1.5 bg-gray-800 rounded-full mt-3 mb-2">
              <div class="h-1.5 bg-indigo-500 rounded-full transition-all" :style="{ width: `${Math.min(matchTrends.thirty_day.rate_pct, 100)}%` }"></div>
            </div>
            <div class="text-xs text-gray-500">{{ matchTrends.thirty_day.matched }} matched / {{ matchTrends.thirty_day.players }} played</div>
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

      <!-- Insights -->
      <section>
        <h2 class="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">Insights</h2>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">

          <!-- Archetype Distribution -->
          <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div class="text-xs text-gray-500 mb-3">Archetype Distribution</div>
            <div v-if="archetypes.length" class="space-y-2">
              <div v-for="a in archetypes" :key="a.archetype" class="flex items-center gap-2">
                <span class="text-xs text-purple-400 w-28 truncate font-medium">{{ a.archetype }}</span>
                <div class="flex-1 h-1.5 bg-gray-800 rounded-full">
                  <div
                    class="h-1.5 bg-purple-500 rounded-full"
                    :style="{ width: `${archetypesTotal ? (a.count / archetypesTotal * 100) : 0}%` }"
                  ></div>
                </div>
                <span class="text-xs text-gray-500 w-8 text-right">{{ a.count }}</span>
              </div>
            </div>
            <div v-else class="text-xs text-gray-600">No data yet</div>
          </div>

          <!-- Attachment Styles -->
          <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div class="text-xs text-gray-500 mb-3">Attachment Styles</div>
            <div v-if="attachmentStyles.length" class="flex flex-wrap gap-2">
              <div
                v-for="s in attachmentStyles"
                :key="s.style"
                class="px-3 py-1.5 rounded-full text-xs font-medium"
                :class="{
                  'bg-green-900/40 text-green-400': s.style === 'secure',
                  'bg-yellow-900/40 text-yellow-400': s.style === 'anxious-preoccupied',
                  'bg-blue-900/40 text-blue-400': s.style === 'dismissive-avoidant',
                  'bg-red-900/40 text-red-400': s.style === 'fearful-avoidant',
                }"
              >
                {{ s.style }} · {{ attachmentTotal ? Math.round(s.count / attachmentTotal * 100) : 0 }}%
              </div>
            </div>
            <div v-else class="text-xs text-gray-600">No data yet</div>
          </div>

          <!-- Connector Depth -->
          <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div class="text-xs text-gray-500 mb-3">Connector Depth</div>
            <div v-if="connectorDepth.length" class="space-y-2">
              <div v-for="b in connectorDepth" :key="b.connectors" class="flex items-center gap-2">
                <span class="text-xs text-gray-400 w-16">{{ b.connectors === 3 ? '3+' : b.connectors }} {{ b.connectors === 1 ? 'source' : 'sources' }}</span>
                <div class="flex-1 h-1.5 bg-gray-800 rounded-full">
                  <div
                    class="h-1.5 rounded-full"
                    :class="{
                      'bg-gray-600': b.connectors === 0,
                      'bg-yellow-500': b.connectors === 1,
                      'bg-green-500': b.connectors === 2,
                      'bg-purple-500': b.connectors === 3,
                    }"
                    :style="{ width: `${Math.max(5, b.count / Math.max(...connectorDepth.map(d => d.count)) * 100)}%` }"
                  ></div>
                </div>
                <span class="text-xs text-gray-500 w-8 text-right">{{ b.count }}</span>
              </div>
            </div>
            <div v-else class="text-xs text-gray-600">No data yet</div>
          </div>

        </div>
      </section>

      <!-- Spotify Profiles -->
      <section v-if="spotifyProfiles.length">
        <h2 class="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">
          Spotify Profiles
          <span class="ml-2 text-gray-600 normal-case text-xs font-normal">{{ spotifyTotal }} total</span>
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="sp in spotifyProfiles"
            :key="sp.user_id"
            class="bg-gray-900 border border-gray-800 rounded-xl p-5"
          >
            <div class="font-medium text-white text-sm mb-1">{{ sp.display_name || sp.email }}</div>
            <div class="flex flex-wrap gap-1 mb-3">
              <span
                v-for="a in sp.top_artists.slice(0, 3)"
                :key="a"
                class="text-xs px-2 py-0.5 bg-green-900/30 text-green-400 rounded-full"
              >{{ a }}</span>
            </div>
            <div class="flex flex-wrap gap-1 mb-3">
              <span
                v-for="g in sp.genres.slice(0, 4)"
                :key="g"
                class="text-xs px-2 py-0.5 bg-gray-800 text-gray-400 rounded-full"
              >{{ g }}</span>
            </div>
            <div class="space-y-1">
              <div v-for="(val, key) in sp.audio_avg" :key="key" class="flex items-center gap-2">
                <span class="text-xs text-gray-500 w-24 truncate capitalize">{{ key }}</span>
                <div class="flex-1 h-1.5 bg-gray-800 rounded-full">
                  <div
                    class="h-1.5 bg-green-500 rounded-full"
                    :style="{ width: `${Math.min(key === 'tempo' ? val / 200 * 100 : val * 100, 100)}%` }"
                  ></div>
                </div>
                <span class="text-xs text-gray-500 w-10 text-right">{{ typeof val === 'number' ? val.toFixed(2) : val }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-if="spotifyTotal > spotifyPerPage" class="flex justify-center gap-2 mt-4">
          <button
            :disabled="spotifyPage <= 1"
            @click="goSpotifyPage(spotifyPage - 1)"
            class="px-3 py-1.5 rounded-lg border border-gray-800 text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
          >Prev</button>
          <span class="px-3 py-1.5 text-sm text-gray-500">{{ spotifyPage }} / {{ Math.ceil(spotifyTotal / spotifyPerPage) }}</span>
          <button
            :disabled="spotifyPage >= Math.ceil(spotifyTotal / spotifyPerPage)"
            @click="goSpotifyPage(spotifyPage + 1)"
            class="px-3 py-1.5 rounded-lg border border-gray-800 text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
          >Next</button>
        </div>
      </section>

      <!-- Psychometric Profiles -->
      <section v-if="psychProfiles.length">
        <h2 class="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">
          Psychometrics
          <span class="ml-2 text-gray-600 normal-case text-xs font-normal">{{ psychTotal }} total</span>
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="pm in psychProfiles"
            :key="pm.user_id"
            class="bg-gray-900 border border-gray-800 rounded-xl p-5"
          >
            <div class="font-medium text-white text-sm mb-2">{{ pm.display_name || pm.email }}</div>
            <div class="flex flex-wrap gap-1 mb-3">
              <span v-if="pm.love_language" class="text-xs px-2 py-0.5 bg-pink-900/30 text-pink-400 rounded-full">{{ pm.love_language }}</span>
              <span v-if="pm.values_cluster" class="text-xs px-2 py-0.5 bg-blue-900/30 text-blue-400 rounded-full">{{ pm.values_cluster }}</span>
              <span v-if="pm.sociosexual_orientation" class="text-xs px-2 py-0.5 bg-purple-900/30 text-purple-400 rounded-full">{{ pm.sociosexual_orientation }}</span>
            </div>
            <div v-if="pm.ipip_neo_scores" class="space-y-1 mb-2">
              <div v-for="(val, trait) in pm.ipip_neo_scores" :key="trait" class="flex items-center gap-2">
                <span class="text-xs text-gray-500 w-24 truncate capitalize">{{ trait }}</span>
                <div class="flex-1 h-1.5 bg-gray-800 rounded-full">
                  <div
                    class="h-1.5 bg-purple-500 rounded-full"
                    :style="{ width: `${Math.min(Number(val) * 100, 100)}%` }"
                  ></div>
                </div>
                <span class="text-xs text-gray-500 w-10 text-right">{{ Number(val).toFixed(2) }}</span>
              </div>
            </div>
            <p v-if="pm.narrative" class="text-xs text-gray-500 leading-relaxed line-clamp-3">{{ pm.narrative }}</p>
          </div>
        </div>
        <div v-if="psychTotal > psychPerPage" class="flex justify-center gap-2 mt-4">
          <button
            :disabled="psychPage <= 1"
            @click="goPsychPage(psychPage - 1)"
            class="px-3 py-1.5 rounded-lg border border-gray-800 text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
          >Prev</button>
          <span class="px-3 py-1.5 text-sm text-gray-500">{{ psychPage }} / {{ Math.ceil(psychTotal / psychPerPage) }}</span>
          <button
            :disabled="psychPage >= Math.ceil(psychTotal / psychPerPage)"
            @click="goPsychPage(psychPage + 1)"
            class="px-3 py-1.5 rounded-lg border border-gray-800 text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
          >Next</button>
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
const { users, usersTotal, usersPage, funnel, connectors, matchTrends,
        spotifyProfiles, spotifyTotal, spotifyPage,
        psychProfiles, psychTotal, psychPage,
        archetypes, archetypesTotal, attachmentStyles, attachmentTotal, connectorDepth,
        loading, error,
        fetchUsers, fetchFunnel, fetchConnectors, fetchMatchTrends,
        fetchSpotifyProfiles, fetchPsychProfiles,
        fetchArchetypes, fetchAttachmentStyles, fetchConnectorDepth } = useAdminStore()

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
  await Promise.all([fetchFunnel(), fetchConnectors(), fetchMatchTrends(), fetchUsers(1, perPage), fetchSpotifyProfiles(1, 12), fetchPsychProfiles(1, 12), fetchArchetypes(), fetchAttachmentStyles(), fetchConnectorDepth()])
}

const spotifyPerPage = 12
const psychPerPage = 12

async function goSpotifyPage(page: number) { await fetchSpotifyProfiles(page, spotifyPerPage) }
async function goPsychPage(page: number) { await fetchPsychProfiles(page, psychPerPage) }

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

function dropOff(i: number): number {
  const curr = funnel.value[i]?.count || 0
  const next = funnel.value[i + 1]?.count || 0
  if (curr === 0) return 0
  return Math.round((1 - next / curr) * 100)
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
