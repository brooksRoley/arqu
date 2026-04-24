# Post-Trance Microdose Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a post-trance reflection overlay in ZeromindView that surfaces connector data (Spotify/Strava) and delivers psychometric questions one at a time after each trance session.

**Architecture:** New `psychometric_responses` table stores individual item answers. Question pool lives in Python module with connector affinity tags. Backend serves next-item and accepts micro-dose answers, auto-computing instrument scores when enough items accumulate. Frontend `PostTranceOverlay.vue` component mounts in ZeromindView after wake phase, fetching connector profile + next question in parallel.

**Tech Stack:** Vue 3 + TypeScript + Tailwind, FastAPI + asyncpg, existing psychometrics scoring infrastructure

**Spec:** `docs/superpowers/specs/2026-04-24-post-trance-microdose-design.md`

---

### Task 1: Database Migration — psychometric_responses table

**Files:**
- Create: `server/migrations/017_psychometric_responses.sql`

- [ ] **Step 1: Write the migration**

```sql
-- 017_psychometric_responses.sql
-- Individual psychometric item responses for the microdose system

CREATE TABLE IF NOT EXISTS psychometric_responses (
    user_id UUID NOT NULL REFERENCES users(id),
    item_id TEXT NOT NULL,
    value INT NOT NULL,
    connector_context TEXT,
    trance_coherence FLOAT,
    session_duration_ms INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, item_id)
);
```

- [ ] **Step 2: Run migration locally**

Run: `source server/venv/bin/activate && python -m server.app.migrate`

Expected: Migration 017 applied successfully.

- [ ] **Step 3: Commit**

```bash
git add server/migrations/017_psychometric_responses.sql
git commit -m "Add psychometric_responses table for microdose system"
```

---

### Task 2: Question Pool Module

**Files:**
- Create: `server/app/psychometrics/question_pool.py`

- [ ] **Step 1: Create the question pool**

```python
"""
Psychometric question pool for the post-trance microdose system.

Each item has:
- item_id: unique identifier
- instrument: which psychometric instrument it belongs to
- text: the question text shown to the user
- scale: "likert_5", "likert_7", or "categorical"
- options: list of options for categorical items (None for Likert)
- connector_affinity: "spotify", "strava", or "general"
- trait: scoring key (e.g. "O" for openness, "anxiety" for ECR-R)
- direction: +1 for positively keyed, -1 for reverse-scored (Likert only)
"""

from __future__ import annotations

from typing import TypedDict


class PoolItem(TypedDict):
    item_id: str
    instrument: str
    text: str
    scale: str
    options: list[str] | None
    connector_affinity: str
    trait: str
    direction: int


# ── Core Pool (17 items) ─────────────────────────────────────────────────────

CORE_POOL: list[PoolItem] = [
    # IPIP-NEO Big Five (10 items, Likert 1-5)
    {
        "item_id": "ipip_neo_0", "instrument": "ipip_neo",
        "text": "I have a rich imagination and love exploring abstract ideas.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "spotify", "trait": "O", "direction": 1,
    },
    {
        "item_id": "ipip_neo_1", "instrument": "ipip_neo",
        "text": "I am always prepared and like to plan things in advance.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "strava", "trait": "C", "direction": 1,
    },
    {
        "item_id": "ipip_neo_2", "instrument": "ipip_neo",
        "text": "I love being around people and am the life of the party.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "spotify", "trait": "E", "direction": 1,
    },
    {
        "item_id": "ipip_neo_3", "instrument": "ipip_neo",
        "text": "I feel empathy for others and make people feel at ease.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "general", "trait": "A", "direction": 1,
    },
    {
        "item_id": "ipip_neo_4", "instrument": "ipip_neo",
        "text": "I am easily stressed and often feel anxious or unsettled.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "general", "trait": "N", "direction": 1,
    },
    {
        "item_id": "ipip_neo_5", "instrument": "ipip_neo",
        "text": "I am quick to understand new concepts and enjoy intellectual challenges.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "spotify", "trait": "O", "direction": 1,
    },
    {
        "item_id": "ipip_neo_6", "instrument": "ipip_neo",
        "text": "I pay attention to detail and follow through on commitments.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "strava", "trait": "C", "direction": 1,
    },
    {
        "item_id": "ipip_neo_7", "instrument": "ipip_neo",
        "text": "I feel energized after spending time in social settings.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "general", "trait": "E", "direction": 1,
    },
    {
        "item_id": "ipip_neo_8", "instrument": "ipip_neo",
        "text": "I try to understand others' perspectives before forming opinions.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "general", "trait": "A", "direction": 1,
    },
    {
        "item_id": "ipip_neo_9", "instrument": "ipip_neo",
        "text": "My mood fluctuates frequently and I can be easily upset.",
        "scale": "likert_5", "options": None,
        "connector_affinity": "general", "trait": "N", "direction": 1,
    },
    # ECR-R Attachment (4 items, Likert 1-7)
    {
        "item_id": "ecr_r_0", "instrument": "ecr_r",
        "text": "I worry about being abandoned by the people I am close to.",
        "scale": "likert_7", "options": None,
        "connector_affinity": "general", "trait": "anxiety", "direction": 1,
    },
    {
        "item_id": "ecr_r_1", "instrument": "ecr_r",
        "text": "I need a lot of reassurance that I am loved.",
        "scale": "likert_7", "options": None,
        "connector_affinity": "general", "trait": "anxiety", "direction": 1,
    },
    {
        "item_id": "ecr_r_2", "instrument": "ecr_r",
        "text": "I prefer not to share my feelings or problems with partners.",
        "scale": "likert_7", "options": None,
        "connector_affinity": "strava", "trait": "avoidance", "direction": 1,
    },
    {
        "item_id": "ecr_r_3", "instrument": "ecr_r",
        "text": "I feel comfortable depending on others for emotional support.",
        "scale": "likert_7", "options": None,
        "connector_affinity": "general", "trait": "avoidance", "direction": -1,
    },
    # Identity (3 items, categorical)
    {
        "item_id": "identity_love_language", "instrument": "identity",
        "text": "What makes you feel most valued?",
        "scale": "categorical",
        "options": ["Words of Affirmation", "Quality Time", "Gifts", "Acts of Service", "Physical Touch"],
        "connector_affinity": "general", "trait": "love_language", "direction": 0,
    },
    {
        "item_id": "identity_values", "instrument": "identity",
        "text": "What drives you most?",
        "scale": "categorical",
        "options": ["Traditional", "Career-driven", "Creative", "Progressive", "Adventure", "Spiritual"],
        "connector_affinity": "strava", "trait": "values_cluster", "direction": 0,
    },
    {
        "item_id": "identity_sociosexual", "instrument": "identity",
        "text": "How do you approach intimacy?",
        "scale": "categorical",
        "options": ["Restricted", "Moderate", "Unrestricted"],
        "connector_affinity": "general", "trait": "sociosexual_orientation", "direction": 0,
    },
]


def get_pool() -> list[PoolItem]:
    """Return the full question pool (core for now, extended later)."""
    return CORE_POOL


def get_next_item(
    answered_ids: set[str],
    connector: str | None = None,
) -> PoolItem | None:
    """
    Return the next unanswered item, preferring items with matching connector_affinity.
    Falls back to 'general' affinity if no connector-specific items remain.
    Returns None when everything is answered.
    """
    pool = get_pool()
    unanswered = [item for item in pool if item["item_id"] not in answered_ids]
    if not unanswered:
        return None

    if connector:
        # Try connector-specific first
        matched = [item for item in unanswered if item["connector_affinity"] == connector]
        if matched:
            return matched[0]

    # Fall back to general or any remaining
    general = [item for item in unanswered if item["connector_affinity"] == "general"]
    if general:
        return general[0]

    return unanswered[0]
```

- [ ] **Step 2: Verify import**

Run: `cd server && python -c "from app.psychometrics.question_pool import get_next_item, CORE_POOL; print(f'{len(CORE_POOL)} items'); print(get_next_item(set(), 'spotify'))"`

Expected: `17 items` followed by the first spotify-affinity item dict.

- [ ] **Step 3: Commit**

```bash
git add server/app/psychometrics/question_pool.py
git commit -m "Add question pool module for psychometric microdose"
```

---

### Task 3: Backend — Microdose & Next-Item Endpoints

**Files:**
- Modify: `server/app/psychometrics/router.py` (append two new endpoints)

- [ ] **Step 1: Add microdose and next-item endpoints**

Append to `server/app/psychometrics/router.py`:

```python
from .question_pool import get_next_item, CORE_POOL


class MicrodosePayload(BaseModel):
    item_id: str
    value: int
    connector_context: str | None = None
    trance_coherence: float | None = None
    session_duration_ms: int | None = None


@router.post("/microdose", status_code=204)
async def submit_microdose(
    payload: MicrodosePayload,
    user_id: UUID = Depends(get_current_user_id),
):
    """Store a single psychometric item response and recompute scores if instrument is complete."""
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO psychometric_responses (user_id, item_id, value, connector_context, trance_coherence, session_duration_ms)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id, item_id) DO UPDATE SET
                value = EXCLUDED.value,
                connector_context = EXCLUDED.connector_context,
                trance_coherence = EXCLUDED.trance_coherence,
                session_duration_ms = EXCLUDED.session_duration_ms,
                created_at = now()
            """,
            str(user_id), payload.item_id, payload.value,
            payload.connector_context, payload.trance_coherence, payload.session_duration_ms,
        )

        # Check if we can auto-compute scores
        rows = await conn.fetch(
            "SELECT item_id, value FROM psychometric_responses WHERE user_id = $1",
            str(user_id),
        )
        answered = {r["item_id"]: r["value"] for r in rows}

        # Try to build IPIP-NEO scores (need all 10 core items)
        ipip_ids = [f"ipip_neo_{i}" for i in range(10)]
        ipip_values = [answered[iid] for iid in ipip_ids if iid in answered]

        # Try to build ECR-R scores (need all 4 core items)
        ecr_ids = [f"ecr_r_{i}" for i in range(4)]
        ecr_values = [answered[iid] for iid in ecr_ids if iid in answered]

        # Extract identity items
        love_language = None
        values_cluster = None
        sociosexual = None

        # For categorical items, value is the index into the options list
        from .question_pool import CORE_POOL
        pool_map = {item["item_id"]: item for item in CORE_POOL}

        if "identity_love_language" in answered:
            item = pool_map["identity_love_language"]
            idx = answered["identity_love_language"]
            love_language = item["options"][idx] if item["options"] and 0 <= idx < len(item["options"]) else None

        if "identity_values" in answered:
            item = pool_map["identity_values"]
            idx = answered["identity_values"]
            values_cluster = item["options"][idx] if item["options"] and 0 <= idx < len(item["options"]) else None

        if "identity_sociosexual" in answered:
            item = pool_map["identity_sociosexual"]
            idx = answered["identity_sociosexual"]
            sociosexual = item["options"][idx] if item["options"] and 0 <= idx < len(item["options"]) else None

        # Compute available scores
        ipip_scores = None
        if len(ipip_values) >= 10:
            from .scoring import _score_ocean_items
            ipip_scores = _score_ocean_items(ipip_values)

        ecr_scores = None
        if len(ecr_values) >= 4:
            from .scoring import _score_ecr_r_items
            ecr_scores = _score_ecr_r_items(ecr_values)

        # Upsert into user_psychometrics if we have anything to store
        if ipip_scores or ecr_scores or love_language or values_cluster or sociosexual:
            await conn.execute(
                """
                INSERT INTO user_psychometrics
                    (user_id, ipip_neo_scores, ecr_r_scores, love_language, sociosexual_orientation, values_cluster, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, now())
                ON CONFLICT (user_id) DO UPDATE SET
                    ipip_neo_scores = COALESCE(EXCLUDED.ipip_neo_scores, user_psychometrics.ipip_neo_scores),
                    ecr_r_scores = COALESCE(EXCLUDED.ecr_r_scores, user_psychometrics.ecr_r_scores),
                    love_language = COALESCE(EXCLUDED.love_language, user_psychometrics.love_language),
                    sociosexual_orientation = COALESCE(EXCLUDED.sociosexual_orientation, user_psychometrics.sociosexual_orientation),
                    values_cluster = COALESCE(EXCLUDED.values_cluster, user_psychometrics.values_cluster),
                    updated_at = now()
                """,
                str(user_id),
                json.dumps(ipip_scores) if ipip_scores else None,
                json.dumps(ecr_scores) if ecr_scores else None,
                love_language,
                sociosexual,
                values_cluster,
            )


@router.get("/next-item")
async def get_next_psychometric_item(
    connector: str | None = None,
    user_id: UUID = Depends(get_current_user_id),
):
    """Return the next unanswered psychometric item for this user."""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT item_id FROM psychometric_responses WHERE user_id = $1",
            str(user_id),
        )
    answered_ids = {r["item_id"] for r in rows}
    item = get_next_item(answered_ids, connector)
    if not item:
        return None

    return {
        "item_id": item["item_id"],
        "instrument": item["instrument"],
        "text": item["text"],
        "scale": item["scale"],
        "options": item["options"],
        "connector_affinity": item["connector_affinity"],
        "progress": {
            "answered": len(answered_ids),
            "core_total": len(CORE_POOL),
        },
    }
```

- [ ] **Step 2: Verify import**

Run: `cd server && python -c "from app.psychometrics.router import router; print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add server/app/psychometrics/router.py
git commit -m "Add microdose and next-item psychometric endpoints"
```

---

### Task 4: Backend — Strava Profile Endpoint

**Files:**
- Modify: `server/app/strava/router.py` (append new endpoint)

- [ ] **Step 1: Add the profile endpoint**

Add the import for `get_current_user_id` and `Depends` at the top of `server/app/strava/router.py` (alongside existing imports):

```python
from ..auth.deps import get_current_user_id
from fastapi import APIRouter, Depends, HTTPException, Query, status
```

Then append this endpoint:

```python
@router.get("/profile")
async def get_strava_profile(user_id: UUID = Depends(get_current_user_id)):
    """Return the stored Strava profile for the current user, or null."""
    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT strava_data FROM vibe_vectors WHERE user_id = $1",
            user_id,
        )
    if not row or not row["strava_data"]:
        return None
    data = row["strava_data"]
    return json.loads(data) if isinstance(data, str) else data
```

- [ ] **Step 2: Verify import**

Run: `cd server && python -c "from app.strava.router import router; print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add server/app/strava/router.py
git commit -m "Add GET /api/strava/profile endpoint"
```

---

### Task 5: Frontend — PostTranceOverlay Component

**Files:**
- Create: `src/components/PostTranceOverlay.vue`

- [ ] **Step 1: Create the overlay component**

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/composables/useAuthStore'

const props = defineProps<{
  coherence: number
  syncCount: number
  sessionDuration: number
  dominantPhase: string
}>()

const emit = defineEmits<{ close: [] }>()

const { apiFetch } = useAuthStore()

const visible = ref(false)
const submitting = ref(false)
const submitted = ref(false)
const selectedValue = ref<number | null>(null)

interface NextItem {
  item_id: string
  instrument: string
  text: string
  scale: string
  options: string[] | null
  connector_affinity: string
  progress: { answered: number; core_total: number }
}

const nextItem = ref<NextItem | null>(null)
const connectorData = ref<Record<string, unknown> | null>(null)
const pickedConnector = ref<string>('spotify')

// ── Connector round-robin ────────────────────────────────────────
const CONNECTOR_KEY = 'cz-last-reflect-connector'
const CONNECTORS = ['spotify', 'strava']

function pickConnector(): string {
  const last = localStorage.getItem(CONNECTOR_KEY)
  const idx = last ? (CONNECTORS.indexOf(last) + 1) % CONNECTORS.length : 0
  const pick = CONNECTORS[idx]
  localStorage.setItem(CONNECTOR_KEY, pick)
  return pick
}

// ── Trance summary line ─────────────────────────────────────────
const tranceLine = computed(() => {
  const mins = Math.floor(props.sessionDuration / 60000)
  const secs = Math.floor((props.sessionDuration % 60000) / 1000)
  const time = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
  return `coherence ${Math.round(props.coherence)} · ${time} · ${props.dominantPhase}`
})

// ── Spotify data cards ──────────────────────────────────────────
const spotifyStats = computed(() => {
  if (!connectorData.value || pickedConnector.value !== 'spotify') return []
  const d = connectorData.value as any
  const stats: { label: string; value: string }[] = []

  if (d.genres?.length >= 2) {
    stats.push({ label: 'genres', value: `${d.genres[0]} · ${d.genres[1]}` })
  } else if (d.genres?.length === 1) {
    stats.push({ label: 'genre', value: d.genres[0] })
  }

  if (d.audio_avg?.valence != null) {
    const v = d.audio_avg.valence
    const mood = v < 0.3 ? 'melancholic' : v < 0.6 ? 'bittersweet' : 'luminous'
    stats.push({ label: 'valence', value: `${(v * 100).toFixed(0)}% — ${mood}` })
  }

  if (d.top_artists?.length) {
    stats.push({ label: 'top artist', value: d.top_artists[0] })
  }

  return stats.slice(0, 3)
})

// ── Strava data cards ───────────────────────────────────────────
const stravaStats = computed(() => {
  if (!connectorData.value || pickedConnector.value !== 'strava') return []
  const d = connectorData.value as any
  const stats: { label: string; value: string }[] = []

  if (d.activity_types) {
    const entries = Object.entries(d.activity_types) as [string, number][]
    if (entries.length) {
      const [type, count] = entries.sort((a, b) => (b[1] as number) - (a[1] as number))[0]
      stats.push({ label: 'dominant', value: `${count} ${type.toLowerCase()}s` })
    }
  }

  if (d.total_distance_km) {
    stats.push({ label: 'distance', value: `${Math.round(d.total_distance_km)} km` })
  }

  if (d.avg_heartrate) {
    stats.push({
      label: 'heartrate',
      value: `HR ${Math.round(d.avg_heartrate)} bpm · coherence ${Math.round(props.coherence)}`,
    })
  }

  return stats.slice(0, 3)
})

const connectorStats = computed(() =>
  pickedConnector.value === 'spotify' ? spotifyStats.value : stravaStats.value
)

const connectorLabel = computed(() =>
  pickedConnector.value === 'spotify' ? '♫ Spotify' : '⚡ Strava'
)

// ── Likert helpers ──────────────────────────────────────────────
const likertMax = computed(() => {
  if (!nextItem.value) return 5
  return nextItem.value.scale === 'likert_7' ? 7 : 5
})

// ── Fetch & init ────────────────────────────────────────────────
onMounted(async () => {
  pickedConnector.value = pickConnector()

  const [itemRes, profileRes] = await Promise.allSettled([
    apiFetch<NextItem | null>(`/api/psychometrics/next-item?connector=${pickedConnector.value}`),
    apiFetch<Record<string, unknown> | null>(`/api/${pickedConnector.value}/profile`),
  ])

  if (itemRes.status === 'fulfilled') nextItem.value = itemRes.value
  if (profileRes.status === 'fulfilled') connectorData.value = profileRes.value

  // If we have no data and no question, don't show
  if (!nextItem.value && !connectorData.value) {
    emit('close')
    return
  }

  // Fade in
  setTimeout(() => { visible.value = true }, 100)
})

// ── Submit ──────────────────────────────────────────────────────
async function submit(value: number) {
  if (!nextItem.value || submitting.value) return
  submitting.value = true
  selectedValue.value = value
  try {
    await apiFetch('/api/psychometrics/microdose', {
      method: 'POST',
      body: JSON.stringify({
        item_id: nextItem.value.item_id,
        value,
        connector_context: pickedConnector.value,
        trance_coherence: props.coherence,
        session_duration_ms: props.sessionDuration,
      }),
    })
    submitted.value = true
    setTimeout(() => emit('close'), 1200)
  } catch {
    submitting.value = false
  }
}

function submitCategorical(index: number) {
  submit(index)
}

function handleBackdropClick(e: MouseEvent) {
  if ((e.target as HTMLElement).classList.contains('overlay-backdrop')) {
    emit('close')
  }
}
</script>

<template>
  <div
    class="overlay-backdrop fixed inset-0 z-50 flex items-center justify-center p-4"
    :class="visible ? 'opacity-100' : 'opacity-0'"
    style="transition: opacity 1.5s ease; background: rgba(0, 0, 0, 0.4)"
    @click="handleBackdropClick"
  >
    <div
      class="overlay-card relative w-full max-w-[400px] rounded-2xl border border-white/10 p-6 space-y-5"
      :class="submitted ? 'opacity-0 translate-y-2' : 'opacity-100 translate-y-0'"
      style="
        background: rgba(15, 10, 25, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        transition: opacity 1s ease, transform 1s ease;
      "
    >
      <!-- Close -->
      <button
        class="absolute top-3 right-3 text-gray-600 hover:text-gray-400 text-sm"
        @click="emit('close')"
      >✕</button>

      <!-- Connector data -->
      <div v-if="connectorStats.length" class="space-y-1.5">
        <div class="text-xs uppercase tracking-widest text-gray-500">{{ connectorLabel }}</div>
        <div v-for="stat in connectorStats" :key="stat.label" class="flex justify-between text-sm">
          <span class="text-gray-500">{{ stat.label }}</span>
          <span class="text-gray-300">{{ stat.value }}</span>
        </div>
      </div>

      <!-- Trance line -->
      <div class="text-xs text-gray-600 text-center">{{ tranceLine }}</div>

      <!-- Psychometric item -->
      <div v-if="nextItem" class="space-y-4">
        <p class="text-sm text-gray-200 leading-relaxed">{{ nextItem.text }}</p>

        <!-- Likert scale -->
        <div v-if="nextItem.scale !== 'categorical'" class="flex justify-center gap-1.5">
          <button
            v-for="n in likertMax"
            :key="n"
            class="w-9 h-9 rounded-lg text-sm font-medium transition-all"
            :class="
              selectedValue === n
                ? 'bg-purple-600 text-white scale-110'
                : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-gray-200'
            "
            :disabled="submitting"
            @click="submit(n)"
          >{{ n }}</button>
        </div>

        <!-- Categorical options -->
        <div v-else class="space-y-1.5">
          <button
            v-for="(opt, idx) in nextItem.options"
            :key="opt"
            class="w-full py-2 px-3 rounded-lg text-sm text-left transition-all"
            :class="
              selectedValue === idx
                ? 'bg-purple-600 text-white'
                : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-gray-200'
            "
            :disabled="submitting"
            @click="submitCategorical(idx)"
          >{{ opt }}</button>
        </div>

        <!-- Progress -->
        <div v-if="nextItem.progress" class="flex items-center gap-2">
          <div class="flex-1 h-0.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              class="h-full bg-purple-600/50 rounded-full transition-all duration-500"
              :style="{ width: `${(nextItem.progress.answered / nextItem.progress.core_total) * 100}%` }"
            />
          </div>
          <span class="text-xs text-gray-600 tabular-nums">
            {{ nextItem.progress.answered }} / {{ nextItem.progress.core_total }}
          </span>
        </div>
      </div>

      <!-- Data-only mode (no question) -->
      <div v-else-if="connectorStats.length" class="text-center">
        <p class="text-xs text-gray-600">reflect on your signal</p>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Verify compilation**

Run: `npx vue-tsc --noEmit 2>&1 | head -20`

Expected: No errors related to PostTranceOverlay.vue

- [ ] **Step 3: Commit**

```bash
git add src/components/PostTranceOverlay.vue
git commit -m "Add PostTranceOverlay component for post-trance microdose"
```

---

### Task 6: Frontend — Integrate Overlay into ZeromindView

**Files:**
- Modify: `src/views/ZeromindView.vue`
- Modify: `src/composables/useTranceEngine.ts`

- [ ] **Step 1: Expose session data from useTranceEngine**

In `src/composables/useTranceEngine.ts`, the composable's return statement needs to expose `coherenceScore`, `syncCount`, and `phase` if they aren't already. Find the return statement at the end of the `useTranceEngine` function and ensure these are included. Also add a `sessionDuration` computed ref and a `sessionComplete` ref.

Add these near the other refs at the top of the composable:

```typescript
const sessionComplete = ref(false)
```

In `completeSession()`, before the `stopSession()` call, add:

```typescript
  sessionComplete.value = true
```

Add a computed for duration (add `computed` to the vue import if needed):

```typescript
const sessionDurationMs = computed(() =>
  sessionStartTime ? Date.now() - sessionStartTime : 0
)
```

Add to the return object:

```typescript
  sessionComplete,
  sessionDurationMs,
  coherenceScore,
  syncCount,
```

- [ ] **Step 2: Add overlay to ZeromindView**

In `src/views/ZeromindView.vue`, add the import:

```typescript
import PostTranceOverlay from '@/components/PostTranceOverlay.vue'
```

Add a local ref for overlay visibility (the `sessionComplete` ref from the engine triggers it):

```typescript
const showOverlay = ref(false)
```

Watch for session completion to show the overlay:

```typescript
watch(sessionComplete, (val) => {
  if (val) showOverlay.value = true
})
```

Add the overlay to the template, at the end of the root element (after the existing canvas/UI elements):

```html
<PostTranceOverlay
  v-if="showOverlay"
  :coherence="coherenceScore"
  :sync-count="syncCount"
  :session-duration="sessionDurationMs"
  :dominant-phase="phase"
  @close="showOverlay = false"
/>
```

- [ ] **Step 3: Verify compilation**

Run: `npx vue-tsc --noEmit 2>&1 | head -20`

Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add src/composables/useTranceEngine.ts src/views/ZeromindView.vue
git commit -m "Wire PostTranceOverlay into ZeromindView after trance completion"
```

---

### Task 7: Build Verification

**Files:** None (verification only)

- [ ] **Step 1: TypeScript check**

Run: `npx vue-tsc --noEmit`

Expected: Exit 0, no errors

- [ ] **Step 2: Vite build**

Run: `npm run build`

Expected: Build succeeds with no errors

- [ ] **Step 3: Verify backend imports**

Run: `cd server && python -c "from app.main import app; print('OK')"`

Expected: `OK`

- [ ] **Step 4: Verify question pool**

Run: `cd server && python -c "from app.psychometrics.question_pool import get_next_item, CORE_POOL; print(f'Pool: {len(CORE_POOL)} items'); item = get_next_item(set(), 'spotify'); print(f'Next spotify item: {item[\"item_id\"]}'); item2 = get_next_item({'ipip_neo_0'}, 'spotify'); print(f'After answering 0: {item2[\"item_id\"]}')" `

Expected: Pool: 17 items, Next spotify item: ipip_neo_0, After answering 0: ipip_neo_2
