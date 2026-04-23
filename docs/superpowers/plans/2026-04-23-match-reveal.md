# Match Reveal + Fitting Ritual Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the match reveal surface — a scroll-narrative page that shows matched users exactly why the system paired them, with a pre-reveal "fitting ritual" that captures self and ideal-partner avatars.

**Architecture:** New migration adds `fitting_self`/`fitting_ideal` JSONB columns to `vibe_vectors`. Two new backend endpoints (`POST /api/intake/fitting` and `GET /api/match/reveal/:target_id`). Frontend: extract Fitting.vue's SVG logic into a reusable component, build a two-phase fitting ritual view, and build a five-section scroll-narrative reveal view. Modify GameView to redirect on mutual match and MessagesView to add "Signal Story" links.

**Tech Stack:** Vue 3 + TypeScript + Tailwind, FastAPI + asyncpg, existing Pinecone infrastructure

**Spec:** `docs/superpowers/specs/2026-04-23-match-reveal-design.md`

---

### Task 1: Database Migration — fitting columns

**Files:**
- Create: `server/migrations/016_fitting_data.sql`

- [ ] **Step 1: Write the migration**

```sql
-- 016_fitting_data.sql
-- Add avatar data columns for the fitting ritual (self-image + ideal-partner)

ALTER TABLE vibe_vectors
  ADD COLUMN IF NOT EXISTS fitting_self JSONB DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS fitting_ideal JSONB DEFAULT NULL;
```

- [ ] **Step 2: Run migration locally**

Run: `source server/venv/bin/activate && python -m server.app.migrate`

Expected: Migration 016 applied successfully.

- [ ] **Step 3: Commit**

```bash
git add server/migrations/016_fitting_data.sql
git commit -m "Add fitting_self and fitting_ideal columns to vibe_vectors"
```

---

### Task 2: Backend — POST /api/intake/fitting

**Files:**
- Modify: `server/app/intake/router.py` (append new endpoint)
- Modify: `server/app/intake/models.py` (add FittingRequest model)

- [ ] **Step 1: Add Pydantic model**

In `server/app/intake/models.py`, add:

```python
from typing import Literal, Optional


class FittingRequest(BaseModel):
    phase: Literal["self", "ideal"]
    data: dict  # FittingData JSON — validated client-side, stored as-is
```

- [ ] **Step 2: Add endpoint to router**

Append to `server/app/intake/router.py`:

```python
from .models import ConfessRequest, ConfessResponse, FittingRequest


@router.post("/fitting", status_code=204)
async def save_fitting(
    body: FittingRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Store self-avatar or ideal-partner avatar for the fitting ritual."""
    column = "fitting_self" if body.phase == "self" else "fitting_ideal"
    async with get_conn() as conn:
        await conn.execute(
            f"""
            UPDATE vibe_vectors
            SET {column} = $2::jsonb, updated_at = now()
            WHERE user_id = $1
            """,
            user_id, json.dumps(body.data),
        )
```

Also update the existing import line at the top of the file from:
```python
from .models import ConfessRequest, ConfessResponse
```
to:
```python
from .models import ConfessRequest, ConfessResponse, FittingRequest
```

- [ ] **Step 3: Verify the server starts**

Run: `cd server && python -c "from app.intake.router import router; print('OK')"`

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add server/app/intake/router.py server/app/intake/models.py
git commit -m "Add POST /api/intake/fitting endpoint"
```

---

### Task 3: Backend — GET /api/match/reveal/:target_id

**Files:**
- Modify: `server/app/match/router.py` (append new endpoint)

- [ ] **Step 1: Add reveal endpoint**

Append to `server/app/match/router.py`:

```python
import json


@router.get("/reveal/{target_id}")
async def get_reveal(
    target_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Return the full signal story for a mutual match pair.
    Both users must have accepted each other.
    """
    async with get_conn() as conn:
        # Verify mutual match exists
        mutual = await conn.fetchrow(
            """
            SELECT 1 FROM match_interactions a
            JOIN match_interactions b
                ON a.actor_id = b.target_id AND a.target_id = b.actor_id
            WHERE a.action = 'accept' AND b.action = 'accept'
              AND a.actor_id = $1 AND a.target_id = $2
            """,
            user_id, target_id,
        )
        if not mutual:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No mutual match found with this user",
            )

        # Fetch both vibe vectors
        my_vibe = await conn.fetchrow(
            """
            SELECT user_id, spotify_data, twitter_data, strava_data, steam_data,
                   oracle_coordinate, attachment_style, defense_mechanism,
                   fitting_self, fitting_ideal,
                   (spotify_data IS NOT NULL) AS has_spotify,
                   (twitter_data IS NOT NULL) AS has_twitter,
                   (strava_data IS NOT NULL) AS has_strava,
                   (steam_data IS NOT NULL) AS has_steam,
                   (oracle_coordinate IS NOT NULL) AS has_oracle
            FROM vibe_vectors WHERE user_id = $1
            """,
            user_id,
        )
        their_vibe = await conn.fetchrow(
            """
            SELECT user_id, spotify_data, twitter_data, strava_data, steam_data,
                   oracle_coordinate, attachment_style, defense_mechanism,
                   fitting_self, fitting_ideal,
                   (spotify_data IS NOT NULL) AS has_spotify,
                   (twitter_data IS NOT NULL) AS has_twitter,
                   (strava_data IS NOT NULL) AS has_strava,
                   (steam_data IS NOT NULL) AS has_steam,
                   (oracle_coordinate IS NOT NULL) AS has_oracle
            FROM vibe_vectors WHERE user_id = $1
            """,
            target_id,
        )

        # Fetch display names
        my_user = await conn.fetchrow(
            "SELECT display_name FROM users WHERE id = $1", user_id
        )
        their_user = await conn.fetchrow(
            "SELECT display_name FROM users WHERE id = $1", target_id
        )

        # Fetch psychometrics for both
        my_psych = await conn.fetchrow(
            "SELECT ipip_neo_scores, ecr_r_scores, love_language, "
            "sociosexual_orientation, values_cluster FROM user_psychometrics WHERE user_id = $1",
            user_id,
        )
        their_psych = await conn.fetchrow(
            "SELECT ipip_neo_scores, ecr_r_scores, love_language, "
            "sociosexual_orientation, values_cluster FROM user_psychometrics WHERE user_id = $1",
            target_id,
        )

    def parse_json(val):
        if val is None:
            return None
        return json.loads(val) if isinstance(val, str) else val

    def build_user_data(vibe, user_row):
        if not vibe:
            return None
        return {
            "display_name": user_row["display_name"] if user_row else None,
            "fitting_self": parse_json(vibe["fitting_self"]),
            "fitting_ideal": parse_json(vibe["fitting_ideal"]),
            "spotify_data": parse_json(vibe["spotify_data"]),
            "twitter_data": parse_json(vibe["twitter_data"]),
            "strava_data": parse_json(vibe["strava_data"]),
            "steam_data": parse_json(vibe["steam_data"]),
            "oracle_coordinate": parse_json(vibe["oracle_coordinate"]),
            "attachment_style": vibe["attachment_style"],
            "defense_mechanism": vibe["defense_mechanism"],
            "has_spotify": vibe["has_spotify"],
            "has_twitter": vibe["has_twitter"],
            "has_strava": vibe["has_strava"],
            "has_steam": vibe["has_steam"],
            "has_oracle": vibe["has_oracle"],
        }

    def build_psych(row):
        if not row:
            return None
        return {
            "ipip_neo_scores": parse_json(row["ipip_neo_scores"]),
            "ecr_r_scores": parse_json(row["ecr_r_scores"]),
            "love_language": row["love_language"],
            "sociosexual_orientation": row["sociosexual_orientation"],
            "values_cluster": row["values_cluster"],
        }

    # Build match reason from vibe data
    from ..intake.router import _build_match_reason, _extract_spotify_overlap

    match_stub = {
        "score": 0,  # will be overwritten if Pinecone available
        "attachment_style": their_vibe["attachment_style"] if their_vibe else None,
        "defense_mechanism": their_vibe["defense_mechanism"] if their_vibe else None,
    }

    # Try to get similarity from Pinecone
    similarity = 0.0
    try:
        from ..vector.service import find_nearest_users
        nearest = await find_nearest_users(str(user_id), top_k=10)
        for n in nearest:
            if n["user_id"] == str(target_id):
                similarity = n["score"]
                break
    except Exception:
        pass

    match_stub["score"] = similarity
    reason = _build_match_reason(match_stub, my_vibe, their_vibe)

    return {
        "similarity": similarity,
        "match_reason": reason,
        "self": build_user_data(my_vibe, my_user),
        "match": build_user_data(their_vibe, their_user),
        "psychometrics": {
            "self": build_psych(my_psych),
            "match": build_psych(their_psych),
        },
    }
```

- [ ] **Step 2: Verify import**

Run: `cd server && python -c "from app.match.router import router; print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add server/app/match/router.py
git commit -m "Add GET /api/match/reveal/:target_id endpoint"
```

---

### Task 4: Extract FittingAvatar component from Fitting.vue

**Files:**
- Create: `src/components/FittingAvatar.vue`

This extracts the SVG body rendering logic from `Fitting.vue` into a reusable component. The component accepts `FittingData` as a prop and renders the body SVG. No controls — just the visual.

- [ ] **Step 1: Create FittingAvatar.vue**

Create `src/components/FittingAvatar.vue` with the SVG rendering logic extracted from `Fitting.vue`. The component accepts a single prop `data` of type `FittingData` and renders the body figure as a read-only SVG.

```typescript
// Props interface (goes in <script setup>)
interface FittingData {
  body_type: 'female' | 'male'
  height: number
  build: number
  chest: number
  waist: number
  hips: number
  shoulders: number
  skin_color: string
  skin_shadow: string
  hair_color: string
  hair_length: 'short' | 'medium' | 'long'
  suit_color: string
  suit_color_dark: string
  top_style?: string
  rise?: string
  coverage?: string
  top?: string
  bottom?: string
  wetsuit?: string
}

const props = defineProps<{ data: FittingData }>()
```

Copy the following computed properties from `Fitting.vue` (lines 91–545), changing all refs to read from `props.data`:
- Replace `bodyType.value` → `props.data.body_type`
- Replace `body.height` → `props.data.height`, `body.build` → `props.data.build`, etc.
- Replace `skinColor` → `props.data.skin_color`, `skinShadow` → `props.data.skin_shadow`
- Replace `hairColor` → `props.data.hair_color`, `hairLength.value` → `props.data.hair_length`
- Replace `suitColor` → `props.data.suit_color`, `suitColorDark` → `props.data.suit_color_dark`
- Replace `femaleSuit.topStyle` → `props.data.top_style`, `femaleSuit.rise` → `props.data.rise`, `femaleSuit.coverage` → `props.data.coverage`
- Replace `maleSuit.top` → `props.data.top`, `maleSuit.bottom` → `props.data.bottom`, `maleSuit.wetsuit` → `props.data.wetsuit`

Copy the SVG template from `Fitting.vue` lines 581–722 (the `<svg>` element only, not the controls panel). Remove the interactive click handlers (`@click.stop`, `selectZone`, `clearZone`) and zone highlight elements — this is a read-only renderer.

Remove the `suit-zone` hover/active styles. Keep only the `body-figure` class with `filter: drop-shadow(...)`.

- [ ] **Step 2: Verify it compiles**

Run: `npx vue-tsc --noEmit 2>&1 | head -20`

Expected: No errors related to FittingAvatar.vue

- [ ] **Step 3: Commit**

```bash
git add src/components/FittingAvatar.vue
git commit -m "Extract FittingAvatar SVG renderer from Fitting.vue"
```

---

### Task 5: Shared types — FittingData

**Files:**
- Modify: `src/composables/useVibeStore.ts` (add FittingData type export and reveal types)

- [ ] **Step 1: Add types to useVibeStore.ts**

After the existing `InteractResult` interface (around line 96), add:

```typescript
export interface FittingData {
  body_type: 'female' | 'male'
  height: number
  build: number
  chest: number
  waist: number
  hips: number
  shoulders: number
  skin_color: string
  skin_shadow: string
  hair_color: string
  hair_length: 'short' | 'medium' | 'long'
  suit_color: string
  suit_color_dark: string
  top_style?: string
  rise?: string
  coverage?: string
  top?: string
  bottom?: string
  wetsuit?: string
}

export interface RevealUserData {
  display_name: string | null
  fitting_self: FittingData | null
  fitting_ideal: FittingData | null
  spotify_data: Record<string, unknown> | null
  twitter_data: Record<string, unknown> | null
  strava_data: Record<string, unknown> | null
  steam_data: Record<string, unknown> | null
  oracle_coordinate: Record<string, unknown> | null
  attachment_style: string | null
  defense_mechanism: string | null
  has_spotify: boolean
  has_twitter: boolean
  has_strava: boolean
  has_steam: boolean
  has_oracle: boolean
}

export interface RevealPsychometrics {
  ipip_neo_scores: Record<string, number> | null
  ecr_r_scores: Record<string, number> | null
  love_language: string | null
  sociosexual_orientation: string | null
  values_cluster: string | null
}

export interface RevealData {
  similarity: number
  match_reason: string
  self: RevealUserData | null
  match: RevealUserData | null
  psychometrics: {
    self: RevealPsychometrics | null
    match: RevealPsychometrics | null
  }
}
```

- [ ] **Step 2: Verify compilation**

Run: `npx vue-tsc --noEmit 2>&1 | head -20`

Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add src/composables/useVibeStore.ts
git commit -m "Add FittingData and RevealData types to useVibeStore"
```

---

### Task 6: useRevealStore composable

**Files:**
- Create: `src/composables/useRevealStore.ts`

- [ ] **Step 1: Create the composable**

```typescript
import { ref, readonly } from 'vue'
import { useAuthStore } from './useAuthStore'
import type { RevealData, FittingData } from './useVibeStore'

const revealData = ref<RevealData | null>(null)
const revealLoading = ref(false)
const revealError = ref<string | null>(null)

async function fetchReveal(matchId: string) {
  const { apiFetch } = useAuthStore()
  revealLoading.value = true
  revealError.value = null
  try {
    revealData.value = await apiFetch<RevealData>(`/api/match/reveal/${matchId}`)
  } catch (e: any) {
    revealError.value = e.message
  } finally {
    revealLoading.value = false
  }
}

async function saveFitting(phase: 'self' | 'ideal', data: FittingData) {
  const { apiFetch } = useAuthStore()
  await apiFetch('/api/intake/fitting', {
    method: 'POST',
    body: JSON.stringify({ phase, data }),
  })
}

function hasFittingData(): { self: boolean; ideal: boolean } {
  return {
    self: revealData.value?.self?.fitting_self != null,
    ideal: revealData.value?.self?.fitting_ideal != null,
  }
}

export function useRevealStore() {
  return {
    revealData: readonly(revealData),
    revealLoading: readonly(revealLoading),
    revealError: readonly(revealError),
    fetchReveal,
    saveFitting,
    hasFittingData,
  }
}
```

- [ ] **Step 2: Verify compilation**

Run: `npx vue-tsc --noEmit 2>&1 | head -20`

Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add src/composables/useRevealStore.ts
git commit -m "Add useRevealStore composable for reveal + fitting API"
```

---

### Task 7: PairedBar component

**Files:**
- Create: `src/components/PairedBar.vue`

- [ ] **Step 1: Create PairedBar.vue**

A reusable horizontal bar showing two values on a 0–1 scale.

```vue
<script setup lang="ts">
defineProps<{
  label: string
  selfValue: number
  matchValue: number
  selfColor?: string
  matchColor?: string
}>()
</script>

<template>
  <div class="flex items-center gap-2">
    <span class="text-xs text-gray-500 w-28 truncate">{{ label }}</span>
    <div class="flex-1 h-2.5 bg-gray-800 rounded-full relative overflow-hidden">
      <div
        class="absolute inset-y-0 left-0 rounded-full opacity-70"
        :style="{
          width: `${Math.min(selfValue * 100, 100)}%`,
          background: selfColor || '#8B5CF6',
        }"
      />
      <div
        class="absolute inset-y-0 left-0 rounded-full opacity-50 border-r-2 border-white/30"
        :style="{
          width: `${Math.min(matchValue * 100, 100)}%`,
          background: matchColor || '#EC4899',
        }"
      />
    </div>
    <span class="text-xs text-gray-500 w-16 text-right tabular-nums">
      {{ selfValue.toFixed(2) }} / {{ matchValue.toFixed(2) }}
    </span>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add src/components/PairedBar.vue
git commit -m "Add PairedBar component for paired value comparison"
```

---

### Task 8: AuraField component

**Files:**
- Create: `src/components/AuraField.vue`

- [ ] **Step 1: Create AuraField.vue**

SVG aura-field silhouette that renders a body shape with colored signal rings.

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { FittingData } from '@/composables/useVibeStore'

const props = defineProps<{
  fitting: FittingData | null
  hasSpotify: boolean
  hasOracle: boolean
  hasPsychometric: boolean
  hasActivity: boolean
  hasAttachment: boolean
}>()

// Derive silhouette proportions from fitting data or use defaults
const heightScale = computed(() => {
  const h = props.fitting?.height ?? 68
  return 0.82 + (h - 56) / 26 * 0.36
})
const buildScale = computed(() => {
  const b = props.fitting?.build ?? 5
  return 0.78 + (b - 1) / 9 * 0.56
})
const isMale = computed(() => props.fitting?.body_type === 'male')

const silhouetteHeight = computed(() => Math.round(400 * heightScale.value))
const silhouetteWidth = computed(() => Math.round(120 * buildScale.value * (isMale.value ? 1.1 : 1)))

// Signal layers: innermost to outermost
const layers = computed(() => {
  const result: { color: string; opacity: number; offset: number }[] = []
  if (props.hasPsychometric)
    result.push({ color: '#8B5CF6', opacity: 0.35, offset: 10 })
  if (props.hasOracle)
    result.push({ color: '#EC4899', opacity: 0.25, offset: 25 })
  if (props.hasSpotify)
    result.push({ color: '#22C55E', opacity: 0.18, offset: 40 })
  if (props.hasAttachment)
    result.push({ color: '#F59E0B', opacity: 0.14, offset: 55 })
  if (props.hasActivity)
    result.push({ color: '#3B82F6', opacity: 0.10, offset: 70 })
  return result
})
</script>

<template>
  <div class="relative flex items-center justify-center" :style="{ minHeight: `${silhouetteHeight + 160}px` }">
    <!-- Aura rings -->
    <div
      v-for="(layer, i) in layers"
      :key="i"
      class="absolute rounded-[50%] transition-all duration-700"
      :style="{
        width: `${silhouetteWidth + layer.offset * 2}px`,
        height: `${silhouetteHeight + layer.offset * 2}px`,
        background: `radial-gradient(ellipse at center, ${layer.color}${Math.round(layer.opacity * 255).toString(16).padStart(2, '0')} 0%, transparent 70%)`,
        filter: `blur(${8 + i * 4}px)`,
      }"
    />
    <!-- Core silhouette -->
    <div
      class="relative rounded-[40%_40%_35%_35%/25%_25%_40%_40%] border border-white/10"
      :style="{
        width: `${silhouetteWidth}px`,
        height: `${silhouetteHeight}px`,
        background: 'rgba(255,255,255,0.04)',
      }"
    />
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add src/components/AuraField.vue
git commit -m "Add AuraField signal silhouette component"
```

---

### Task 9: FittingRitualView — two-phase avatar builder

**Files:**
- Create: `src/views/FittingRitualView.vue`

- [ ] **Step 1: Create the view**

This view wraps the existing Fitting.vue configurator logic in a two-phase flow. It checks if the user already has fitting data via the reveal endpoint and skips completed phases.

```vue
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useRevealStore } from '@/composables/useRevealStore'
import type { FittingData } from '@/composables/useVibeStore'

const router = useRouter()
const route = useRoute()
const matchId = route.params.matchId as string
const { fetchReveal, saveFitting, revealData } = useRevealStore()

const phase = ref<'loading' | 'self' | 'ideal' | 'done'>('loading')
const saving = ref(false)

// ── Configurator state (mirrors Fitting.vue) ─────────────────────
type BodyType = 'female' | 'male'
const bodyType = ref<BodyType>('female')
const body = reactive({
  height: 68, build: 5, chest: 40, waist: 34, hips: 40, shoulders: 18,
})
const skinColor = ref('#C68642')
const skinShadow = ref('#A0522D')
const hairColor = ref('#3B1F0A')
const hairLength = ref<'short' | 'medium' | 'long'>('medium')
const suitColor = ref('#2E86AB')
const suitColorDark = ref('#1A5276')

// Suit-specific
const femaleSuit = reactive({
  topStyle: 'underwire' as string,
  rise: 'mid' as string,
  coverage: 'full' as string,
})
const maleSuit = reactive({
  top: 'none' as string,
  bottom: 'board-knee' as string,
  wetsuit: 'none' as string,
})

const skinTones = [
  { color: '#FDDBB4', shadow: '#E8B88A' },
  { color: '#EDB98A', shadow: '#C88B5A' },
  { color: '#C68642', shadow: '#A0522D' },
  { color: '#8D5524', shadow: '#6B3A0F' },
  { color: '#4A2912', shadow: '#2E1508' },
  { color: '#FEE0C0', shadow: '#ECBF98' },
]
const hairColors = ['#3B1F0A', '#6B3A0F', '#C49A3C', '#E8D5A3', '#1A1A1A', '#8B0000', '#6B478B', '#4A90D9']
const suitOptions = [
  { color: '#2E86AB', dark: '#1A5276' },
  { color: '#C0458A', dark: '#8B1A5E' },
  { color: '#E8453C', dark: '#B03030' },
  { color: '#27AE60', dark: '#1A7A42' },
  { color: '#F39C12', dark: '#B07A0A' },
  { color: '#1A1A2E', dark: '#0D0D1A' },
  { color: '#FFFFFF', dark: '#C8C8C8' },
  { color: '#E8C3E8', dark: '#C090C0' },
]

function resetToDefaults() {
  bodyType.value = 'female'
  body.height = 68; body.build = 5; body.chest = 40
  body.waist = 34; body.hips = 40; body.shoulders = 18
  skinColor.value = '#C68642'; skinShadow.value = '#A0522D'
  hairColor.value = '#3B1F0A'; hairLength.value = 'medium'
  suitColor.value = '#2E86AB'; suitColorDark.value = '#1A5276'
  femaleSuit.topStyle = 'underwire'; femaleSuit.rise = 'mid'; femaleSuit.coverage = 'full'
  maleSuit.top = 'none'; maleSuit.bottom = 'board-knee'; maleSuit.wetsuit = 'none'
}

function collectFittingData(): FittingData {
  return {
    body_type: bodyType.value,
    height: body.height,
    build: body.build,
    chest: body.chest,
    waist: body.waist,
    hips: body.hips,
    shoulders: body.shoulders,
    skin_color: skinColor.value,
    skin_shadow: skinShadow.value,
    hair_color: hairColor.value,
    hair_length: hairLength.value,
    suit_color: suitColor.value,
    suit_color_dark: suitColorDark.value,
    ...(bodyType.value === 'female'
      ? { top_style: femaleSuit.topStyle, rise: femaleSuit.rise, coverage: femaleSuit.coverage }
      : { top: maleSuit.top, bottom: maleSuit.bottom, wetsuit: maleSuit.wetsuit }
    ),
  }
}

async function submitPhase() {
  saving.value = true
  try {
    const currentPhase = phase.value as 'self' | 'ideal'
    await saveFitting(currentPhase, collectFittingData())
    if (currentPhase === 'self') {
      resetToDefaults()
      phase.value = 'ideal'
    } else {
      router.push(`/reveal/${matchId}`)
    }
  } finally {
    saving.value = false
  }
}

function setBodyType(type: BodyType) {
  bodyType.value = type
  if (type === 'male') {
    body.chest = 42; body.waist = 36; body.hips = 38; body.shoulders = 20
  } else {
    body.chest = 38; body.waist = 32; body.hips = 42; body.shoulders = 16
  }
}

onMounted(async () => {
  await fetchReveal(matchId)
  const hasSelf = revealData.value?.self?.fitting_self != null
  const hasIdeal = revealData.value?.self?.fitting_ideal != null
  if (hasSelf && hasIdeal) {
    router.replace(`/reveal/${matchId}`)
  } else if (hasSelf) {
    phase.value = 'ideal'
  } else {
    phase.value = 'self'
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <!-- Loading -->
    <div v-if="phase === 'loading'" class="flex items-center justify-center h-screen">
      <div class="text-gray-500">Loading...</div>
    </div>

    <!-- Ritual phases -->
    <div v-else class="flex flex-col lg:flex-row h-screen">
      <!-- Header / prompt -->
      <div class="lg:hidden px-6 pt-6 pb-2">
        <h1 class="text-lg font-semibold">
          {{ phase === 'self' ? 'Show us you' : 'Show us what you see' }}
        </h1>
        <p class="text-sm text-gray-500 mt-1">
          {{ phase === 'self'
            ? 'Build your avatar — this is how you see yourself.'
            : 'Now build the person you imagine. Before we show you your match.' }}
        </p>
      </div>

      <!-- SVG figure panel (placeholder — uses Fitting.vue's SVG inline) -->
      <div class="flex-shrink-0 lg:w-[380px] flex items-start justify-center p-6 bg-gray-900/50 overflow-y-auto">
        <div class="text-center">
          <div class="hidden lg:block mb-8">
            <h1 class="text-lg font-semibold">
              {{ phase === 'self' ? 'Show us you' : 'Show us what you see' }}
            </h1>
            <p class="text-sm text-gray-500 mt-1 max-w-[280px] mx-auto">
              {{ phase === 'self'
                ? 'Build your avatar — this is how you see yourself.'
                : 'Now build the person you imagine. Before we show you your match.' }}
            </p>
          </div>
          <!-- Avatar SVG will be rendered here using FittingAvatar component -->
          <div class="text-gray-600 text-sm">[Avatar SVG renders here — Task 4's FittingAvatar component]</div>
        </div>
      </div>

      <!-- Controls -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Body type toggle -->
        <section class="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 class="text-xs uppercase tracking-widest text-gray-500 mb-3">Body Type</h3>
          <div class="flex rounded-lg overflow-hidden border border-gray-700">
            <button
              class="flex-1 py-2 text-sm transition-colors"
              :class="bodyType === 'female' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
              @click="setBodyType('female')"
            >Female</button>
            <button
              class="flex-1 py-2 text-sm transition-colors"
              :class="bodyType === 'male' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
              @click="setBodyType('male')"
            >Male</button>
          </div>
        </section>

        <!-- Measurements -->
        <section class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
          <h3 class="text-xs uppercase tracking-widest text-gray-500 mb-1">Body</h3>
          <div v-for="[key, label, min, max] in ([
            ['height', 'Height', 56, 82],
            ['build', 'Build', 1, 10],
            ['shoulders', 'Shoulders', 14, 24],
            ['chest', bodyType === 'male' ? 'Chest' : 'Bust', 26, 58],
            ['waist', 'Waist', 22, 58],
            ['hips', 'Hips', 28, 64],
          ] as const)" :key="key">
            <div class="flex justify-between text-sm text-gray-400">
              <span>{{ label }}</span>
              <span class="text-amber-300 tabular-nums">{{ (body as any)[key] }}</span>
            </div>
            <input type="range" v-model.number="(body as any)[key]" :min="min" :max="max" class="w-full accent-purple-500" />
          </div>
        </section>

        <!-- Appearance -->
        <section class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
          <h3 class="text-xs uppercase tracking-widest text-gray-500 mb-1">Appearance</h3>
          <div>
            <div class="text-sm text-gray-400 mb-2">Skin Tone</div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="tone in skinTones" :key="tone.color"
                class="w-7 h-7 rounded-full border-2 transition-transform"
                :class="skinColor === tone.color ? 'border-white scale-110' : 'border-transparent'"
                :style="{ background: tone.color }"
                @click="skinColor = tone.color; skinShadow = tone.shadow"
              />
            </div>
          </div>
          <div>
            <div class="text-sm text-gray-400 mb-2">Hair Color</div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="h in hairColors" :key="h"
                class="w-7 h-7 rounded-full border-2 transition-transform"
                :class="hairColor === h ? 'border-white scale-110' : 'border-transparent'"
                :style="{ background: h }"
                @click="hairColor = h"
              />
            </div>
          </div>
          <div>
            <div class="text-sm text-gray-400 mb-2">Hair Length</div>
            <div class="flex gap-2">
              <button
                v-for="len in (['short', 'medium', 'long'] as const)" :key="len"
                class="px-3 py-1.5 rounded-lg text-xs border transition-colors"
                :class="hairLength === len ? 'bg-purple-600 border-purple-600 text-white' : 'bg-gray-800 border-gray-700 text-gray-400'"
                @click="hairLength = len"
              >{{ len }}</button>
            </div>
          </div>
        </section>

        <!-- Suit color -->
        <section class="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
          <h3 class="text-xs uppercase tracking-widest text-gray-500 mb-1">Swimwear Color</h3>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="s in suitOptions" :key="s.color"
              class="w-7 h-7 rounded-full border-2 transition-transform"
              :class="suitColor === s.color ? 'border-white scale-110' : 'border-transparent'"
              :style="{ background: s.color }"
              @click="suitColor = s.color; suitColorDark = s.dark"
            />
          </div>
        </section>

        <!-- Submit -->
        <button
          @click="submitPhase"
          :disabled="saving"
          class="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium transition-colors disabled:opacity-50"
        >
          {{ saving ? 'Saving...' : phase === 'self' ? 'Continue →' : 'Reveal my match →' }}
        </button>
      </div>
    </div>
  </div>
</template>
```

Note: The SVG figure panel has a placeholder comment. Once Task 4's `FittingAvatar` component is built, import it and render it with `collectFittingData()` passed as the `:data` prop. For now, the controls work and the data flow is correct.

- [ ] **Step 2: Verify compilation**

Run: `npx vue-tsc --noEmit 2>&1 | head -20`

Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add src/views/FittingRitualView.vue
git commit -m "Add FittingRitualView — two-phase avatar builder"
```

---

### Task 10: RevealView — scroll narrative

**Files:**
- Create: `src/views/RevealView.vue`

- [ ] **Step 1: Create the reveal view**

This is the five-section scroll-narrative page. Each section uses Intersection Observer for fade-in.

```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useRevealStore } from '@/composables/useRevealStore'
import AuraField from '@/components/AuraField.vue'
import PairedBar from '@/components/PairedBar.vue'

const router = useRouter()
const route = useRoute()
const matchId = route.params.matchId as string
const { fetchReveal, revealData, revealLoading, revealError } = useRevealStore()

// Intersection observer for scroll animations
const visibleSections = ref<Set<string>>(new Set())
let observer: IntersectionObserver | null = null

function setupObserver() {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const id = (entry.target as HTMLElement).dataset.section
        if (!id) return
        if (entry.isIntersecting) visibleSections.value.add(id)
      })
    },
    { threshold: 0.15 },
  )
  document.querySelectorAll('[data-section]').forEach((el) => observer!.observe(el))
}

onMounted(async () => {
  await fetchReveal(matchId)
  if (revealError.value) return

  // Check if fitting is complete — redirect if not
  if (revealData.value && !revealData.value.self?.fitting_self) {
    router.replace(`/fitting/${matchId}`)
    return
  }

  // Setup observer after data loads
  setTimeout(setupObserver, 100)
})

onUnmounted(() => observer?.disconnect())

// ── Desire overlap helpers ──────────────────────────────────
function proximity(a: number, b: number, range: number): number {
  return Math.round((1 - Math.abs(a - b) / range) * 100)
}

function skinDistance(a: string, b: string): string {
  // Simple hex distance bucketing
  const hexToRgb = (hex: string) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return [r, g, b]
  }
  const [r1, g1, b1] = hexToRgb(a)
  const [r2, g2, b2] = hexToRgb(b)
  const dist = Math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
  if (dist < 80) return 'close'
  if (dist < 160) return 'moderate'
  return 'different'
}

const bigFiveLabels: Record<string, string> = {
  O: 'Openness', C: 'Conscientiousness', E: 'Extraversion',
  A: 'Agreeableness', N: 'Neuroticism',
}
</script>

<template>
  <div class="min-h-screen bg-gray-950 text-gray-100">
    <!-- Loading -->
    <div v-if="revealLoading" class="flex items-center justify-center h-screen">
      <div class="text-gray-500">Loading signal story...</div>
    </div>

    <!-- Error -->
    <div v-else-if="revealError" class="flex flex-col items-center justify-center h-screen gap-4">
      <div class="text-red-400">{{ revealError }}</div>
      <button @click="router.push('/game')" class="text-sm text-gray-500 hover:text-white">Back to matches</button>
    </div>

    <!-- Reveal scroll -->
    <div v-else-if="revealData" class="max-w-4xl mx-auto px-6 py-16 space-y-32">

      <!-- Section 1: Signal Silhouettes -->
      <section
        data-section="silhouettes"
        class="min-h-[70vh] flex flex-col items-center justify-center transition-all duration-700"
        :class="visibleSections.has('silhouettes') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
      >
        <h2 class="text-xs uppercase tracking-widest text-gray-500 mb-12">Signal Silhouettes</h2>
        <div class="flex items-center gap-12 lg:gap-24">
          <div class="text-center">
            <AuraField
              :fitting="revealData.self?.fitting_self ?? null"
              :has-spotify="revealData.self?.has_spotify ?? false"
              :has-oracle="revealData.self?.has_oracle ?? false"
              :has-psychometric="!!revealData.psychometrics?.self"
              :has-activity="(revealData.self?.has_strava ?? false) || (revealData.self?.has_steam ?? false)"
              :has-attachment="!!revealData.self?.attachment_style"
            />
            <div class="text-sm text-gray-400 mt-4">You</div>
          </div>
          <div class="text-center">
            <AuraField
              :fitting="revealData.match?.fitting_self ?? null"
              :has-spotify="revealData.match?.has_spotify ?? false"
              :has-oracle="revealData.match?.has_oracle ?? false"
              :has-psychometric="!!revealData.psychometrics?.match"
              :has-activity="(revealData.match?.has_strava ?? false) || (revealData.match?.has_steam ?? false)"
              :has-attachment="!!revealData.match?.attachment_style"
            />
            <div class="text-sm text-gray-400 mt-4">{{ revealData.match?.display_name || 'Your match' }}</div>
          </div>
        </div>
      </section>

      <!-- Section 2: Desire Overlap -->
      <section
        v-if="revealData.self?.fitting_ideal && revealData.match?.fitting_self"
        data-section="desire"
        class="transition-all duration-700"
        :class="visibleSections.has('desire') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
      >
        <h2 class="text-xs uppercase tracking-widest text-gray-500 mb-8 text-center">Desire Overlap</h2>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- What you imagined vs Who they are -->
          <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 class="text-sm text-gray-400 mb-4">What you imagined → Who they are</h3>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-500">Body type</span>
                <span :class="revealData.self.fitting_ideal.body_type === revealData.match.fitting_self.body_type ? 'text-green-400' : 'text-gray-600'">
                  {{ revealData.self.fitting_ideal.body_type === revealData.match.fitting_self.body_type ? '✓ Match' : '✗ Different' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Build proximity</span>
                <span class="text-purple-400">{{ proximity(revealData.self.fitting_ideal.build, revealData.match.fitting_self.build, 9) }}%</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Height proximity</span>
                <span class="text-purple-400">{{ proximity(revealData.self.fitting_ideal.height, revealData.match.fitting_self.height, 26) }}%</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Coloring</span>
                <span class="text-purple-400">{{ skinDistance(revealData.self.fitting_ideal.skin_color, revealData.match.fitting_self.skin_color) }}</span>
              </div>
            </div>
          </div>
          <!-- What they imagined vs Who you are -->
          <div v-if="revealData.match?.fitting_ideal && revealData.self?.fitting_self" class="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 class="text-sm text-gray-400 mb-4">What they imagined → Who you are</h3>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-500">Body type</span>
                <span :class="revealData.match.fitting_ideal.body_type === revealData.self.fitting_self.body_type ? 'text-green-400' : 'text-gray-600'">
                  {{ revealData.match.fitting_ideal.body_type === revealData.self.fitting_self.body_type ? '✓ Match' : '✗ Different' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Build proximity</span>
                <span class="text-pink-400">{{ proximity(revealData.match.fitting_ideal.build, revealData.self.fitting_self.build, 9) }}%</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Height proximity</span>
                <span class="text-pink-400">{{ proximity(revealData.match.fitting_ideal.height, revealData.self.fitting_self.height, 26) }}%</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Coloring</span>
                <span class="text-pink-400">{{ skinDistance(revealData.match.fitting_ideal.skin_color, revealData.self.fitting_self.skin_color) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Section 3: Signal Layers -->
      <section
        data-section="signals"
        class="transition-all duration-700"
        :class="visibleSections.has('signals') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
      >
        <h2 class="text-xs uppercase tracking-widest text-gray-500 mb-8 text-center">Signal Layers</h2>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

          <!-- Spotify -->
          <div v-if="revealData.self?.has_spotify && revealData.match?.has_spotify" class="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 class="text-sm font-medium text-green-400 mb-4">♫ Spotify</h3>
            <div v-if="revealData.self.spotify_data && revealData.match.spotify_data">
              <div class="flex flex-wrap gap-1 mb-3">
                <span
                  v-for="g in (revealData.self.spotify_data as any).genres?.filter((g: string) => (revealData.match!.spotify_data as any)?.genres?.includes(g))?.slice(0, 5) ?? []"
                  :key="g"
                  class="text-xs px-2 py-0.5 bg-green-900/30 text-green-400 rounded-full"
                >{{ g }}</span>
                <span v-if="!(revealData.self.spotify_data as any).genres?.some((g: string) => (revealData.match!.spotify_data as any)?.genres?.includes(g))" class="text-xs text-gray-600">No shared genres</span>
              </div>
              <div class="space-y-1.5">
                <PairedBar
                  label="Valence"
                  :self-value="(revealData.self.spotify_data as any)?.audio_avg?.valence ?? 0"
                  :match-value="(revealData.match.spotify_data as any)?.audio_avg?.valence ?? 0"
                  self-color="#22C55E"
                  match-color="#86EFAC"
                />
                <PairedBar
                  label="Energy"
                  :self-value="(revealData.self.spotify_data as any)?.audio_avg?.energy ?? 0"
                  :match-value="(revealData.match.spotify_data as any)?.audio_avg?.energy ?? 0"
                  self-color="#EF4444"
                  match-color="#FCA5A5"
                />
                <PairedBar
                  label="Danceability"
                  :self-value="(revealData.self.spotify_data as any)?.audio_avg?.danceability ?? 0"
                  :match-value="(revealData.match.spotify_data as any)?.audio_avg?.danceability ?? 0"
                  self-color="#22C55E"
                  match-color="#86EFAC"
                />
              </div>
            </div>
          </div>

          <!-- Oracle -->
          <div v-if="revealData.self?.has_oracle && revealData.match?.has_oracle" class="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 class="text-sm font-medium text-pink-400 mb-4">☿ Oracle</h3>
            <div class="space-y-1.5 mb-4">
              <PairedBar
                v-for="key in ['empathy_index', 'isolation_metric', 'fatalism_score', 'masochism_curve']"
                :key="key"
                :label="key.replace(/_/g, ' ')"
                :self-value="(revealData.self?.oracle_coordinate as any)?.[key] ?? 0"
                :match-value="(revealData.match?.oracle_coordinate as any)?.[key] ?? 0"
                self-color="#EC4899"
                match-color="#F9A8D4"
              />
            </div>
            <p v-if="(revealData.match?.oracle_coordinate as any)?.oracle_rationale" class="text-xs text-gray-500 leading-relaxed italic">
              "{{ (revealData.match.oracle_coordinate as any).oracle_rationale }}"
            </p>
          </div>

          <!-- Strava -->
          <div v-if="revealData.self?.has_strava && revealData.match?.has_strava" class="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 class="text-sm font-medium text-blue-400 mb-4">⚡ Strava</h3>
            <div class="flex flex-wrap gap-1">
              <span
                v-for="a in (revealData.self?.strava_data as any)?.activity_types?.filter((t: string) => (revealData.match?.strava_data as any)?.activity_types?.includes(t)) ?? []"
                :key="a"
                class="text-xs px-2 py-0.5 bg-blue-900/30 text-blue-400 rounded-full"
              >{{ a }}</span>
              <span class="text-xs text-gray-600 ml-1">shared activities</span>
            </div>
          </div>

          <!-- No shared signals fallback -->
          <div
            v-if="!revealData.self?.has_spotify && !revealData.self?.has_oracle && !revealData.self?.has_strava"
            class="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center col-span-full"
          >
            <p class="text-sm text-gray-500">Connect more signals to enrich your match story</p>
            <router-link to="/calibrate" class="text-xs text-purple-400 hover:text-purple-300 mt-2 inline-block">Go to calibrate →</router-link>
          </div>
        </div>
      </section>

      <!-- Section 4: Psychometric Alignment -->
      <section
        v-if="revealData.psychometrics?.self && revealData.psychometrics?.match"
        data-section="psychometrics"
        class="transition-all duration-700"
        :class="visibleSections.has('psychometrics') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
      >
        <h2 class="text-xs uppercase tracking-widest text-gray-500 mb-8 text-center">Psychometric Alignment</h2>
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
          <!-- Big Five -->
          <div v-if="revealData.psychometrics.self.ipip_neo_scores && revealData.psychometrics.match.ipip_neo_scores">
            <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-3">Big Five</h3>
            <div class="space-y-2">
              <PairedBar
                v-for="(label, key) in bigFiveLabels"
                :key="key"
                :label="label"
                :self-value="revealData.psychometrics.self.ipip_neo_scores[key] ?? 0"
                :match-value="revealData.psychometrics.match.ipip_neo_scores[key] ?? 0"
              />
            </div>
          </div>

          <!-- ECR-R -->
          <div v-if="revealData.psychometrics.self.ecr_r_scores && revealData.psychometrics.match.ecr_r_scores">
            <h3 class="text-xs text-gray-500 uppercase tracking-wider mb-3 mt-6">Attachment Dimensions</h3>
            <div class="space-y-2">
              <PairedBar
                label="Anxiety"
                :self-value="revealData.psychometrics.self.ecr_r_scores.anxiety ?? 0"
                :match-value="revealData.psychometrics.match.ecr_r_scores.anxiety ?? 0"
              />
              <PairedBar
                label="Avoidance"
                :self-value="revealData.psychometrics.self.ecr_r_scores.avoidance ?? 0"
                :match-value="revealData.psychometrics.match.ecr_r_scores.avoidance ?? 0"
              />
            </div>
          </div>

          <!-- Pill badges -->
          <div class="flex flex-wrap gap-2 mt-4">
            <template v-for="field in ['love_language', 'values_cluster', 'sociosexual_orientation'] as const" :key="field">
              <div v-if="revealData.psychometrics.self[field] || revealData.psychometrics.match[field]" class="flex gap-1">
                <span
                  v-if="revealData.psychometrics.self[field]"
                  class="text-xs px-2 py-0.5 rounded-full"
                  :class="revealData.psychometrics.self[field] === revealData.psychometrics.match[field]
                    ? 'bg-purple-900/40 text-purple-300 ring-1 ring-purple-500/50'
                    : 'bg-gray-800 text-gray-400'"
                >{{ revealData.psychometrics.self[field] }}</span>
                <span
                  v-if="revealData.psychometrics.match[field] && revealData.psychometrics.match[field] !== revealData.psychometrics.self[field]"
                  class="text-xs px-2 py-0.5 bg-gray-800 text-gray-400 rounded-full"
                >{{ revealData.psychometrics.match[field] }}</span>
              </div>
            </template>
          </div>
        </div>

        <!-- Missing psychometrics -->
        <div v-if="!revealData.psychometrics?.self" class="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center">
          <p class="text-sm text-gray-500">Complete your psychometric assessment to unlock this layer</p>
          <router-link to="/psychoanalysis" class="text-xs text-purple-400 hover:text-purple-300 mt-2 inline-block">Take assessment →</router-link>
        </div>
      </section>

      <!-- Section 5: Connect -->
      <section
        data-section="connect"
        class="min-h-[50vh] flex flex-col items-center justify-center transition-all duration-700"
        :class="visibleSections.has('connect') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
      >
        <div class="text-7xl font-bold text-white mb-4">
          {{ Math.round(revealData.similarity * 100) }}<span class="text-3xl text-gray-500">%</span>
        </div>
        <p class="text-sm text-gray-400 max-w-md text-center mb-8">{{ revealData.match_reason }}</p>
        <button
          @click="router.push(`/messages/${matchId}`)"
          class="px-8 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium transition-colors"
        >Send a message</button>
        <router-link to="/game" class="text-xs text-gray-500 hover:text-gray-400 mt-4">Back to matches</router-link>
      </section>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Verify compilation**

Run: `npx vue-tsc --noEmit 2>&1 | head -20`

Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add src/views/RevealView.vue
git commit -m "Add RevealView — five-section scroll narrative"
```

---

### Task 11: Router — add new routes

**Files:**
- Modify: `src/router/index.ts`

- [ ] **Step 1: Add routes**

In `src/router/index.ts`, add these two routes before the admin route (around line 222):

```typescript
    // ── Fitting ritual + Match reveal ─────────────────────────────────────
    {
      path: '/fitting/:matchId',
      name: 'fitting-ritual',
      component: () => import('@/views/FittingRitualView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/reveal/:matchId',
      name: 'reveal',
      component: () => import('@/views/RevealView.vue'),
      meta: { requiresAuth: true }
    },
```

- [ ] **Step 2: Verify compilation**

Run: `npx vue-tsc --noEmit 2>&1 | head -20`

Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add src/router/index.ts
git commit -m "Add /fitting/:matchId and /reveal/:matchId routes"
```

---

### Task 12: GameView — redirect on mutual match

**Files:**
- Modify: `src/views/GameView.vue`

- [ ] **Step 1: Change mutual match handler**

In `GameView.vue`, find the `acceptMatch` function (around line 150). Change the mutual match branch from:

```typescript
    if (result.mutual_match) {
      phase.value = 'mutual'
    } else {
```

to:

```typescript
    if (result.mutual_match) {
      router.push(`/fitting/${currentMatch.value.user_id}`)
      return
    } else {
```

- [ ] **Step 2: Verify compilation**

Run: `npx vue-tsc --noEmit 2>&1 | head -20`

Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add src/views/GameView.vue
git commit -m "Redirect to fitting ritual on mutual match"
```

---

### Task 13: MessagesView — add Signal Story link

**Files:**
- Modify: `src/views/MessagesView.vue`

- [ ] **Step 1: Add Signal Story link to each thread**

In `MessagesView.vue`, inside the thread row `<router-link>` (around line 61-80), add a "Signal Story" link after the thread info div. Find:

```html
        <div class="thread-info">
```

After the closing `</div>` of `thread-info` (and still inside the `<router-link>`), the link needs to be outside the router-link to avoid nested links. Instead, modify the thread row to be a `<div>` wrapper with both links.

Replace the thread list block. Find the existing `<router-link v-for="t in threads"...>` and replace it with:

```html
      <div
        v-for="t in threads"
        :key="t.other_user_id"
        class="thread-row"
        :class="{ 'thread-row--unread': t.unread_count > 0 }"
      >
        <router-link :to="`/messages/${t.other_user_id}`" class="thread-link">
          <div class="thread-avatar">
            {{ (t.other_user_name || '?')[0].toUpperCase() }}
          </div>
          <div class="thread-info">
            <div class="thread-top">
              <span class="thread-name">{{ t.other_user_name }}</span>
              <span class="thread-time">{{ formatTime(t.last_message_at) }}</span>
            </div>
            <div class="thread-preview">
              <span class="preview-text">{{ t.last_message }}</span>
              <span v-if="t.unread_count > 0" class="unread-badge">{{ t.unread_count }}</span>
            </div>
          </div>
        </router-link>
        <router-link
          :to="`/reveal/${t.other_user_id}`"
          class="signal-story-link"
          @click.stop
        >Signal Story</router-link>
      </div>
```

Then add these styles inside the `<style scoped>` block:

```css
.thread-link {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  text-decoration: none;
  color: inherit;
}

.signal-story-link {
  font-size: 11px;
  color: #a78bfa;
  text-decoration: none;
  padding: 4px 10px;
  border-radius: 6px;
  white-space: nowrap;
  transition: background 0.15s, color 0.15s;
}

.signal-story-link:hover {
  background: rgba(139, 92, 246, 0.1);
  color: #c4b5fd;
}
```

Note: You will also need to remove the existing styling that treats `.thread-row` as `display: flex` with gap if it applies to the `<router-link>` wrapper — check the existing styles and ensure the `.thread-row` keeps its flex layout and `.thread-link` inherits the inner flex from the original `router-link`.

- [ ] **Step 2: Verify compilation**

Run: `npx vue-tsc --noEmit 2>&1 | head -20`

Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add src/views/MessagesView.vue
git commit -m "Add Signal Story links to messages thread list"
```

---

### Task 14: Update CLAUDE.md route map

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add new routes to the route map table**

In the Route Map section of `CLAUDE.md`, add these rows:

```
| `/fitting/:matchId` | yes | Pre-reveal avatar ritual (self + ideal) |
| `/reveal/:matchId` | yes | Match reveal scroll narrative |
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "Add fitting and reveal routes to CLAUDE.md route map"
```

---

### Task 15: Build verification

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
