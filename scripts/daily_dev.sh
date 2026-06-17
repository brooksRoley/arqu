#!/usr/bin/env bash
# ============================================================
# ChannelZero — Local Daily Dev Agent Pipeline
#
# Rotates through 7 creative-studio lenses (day-of-year % 7):
#   0: Creative Director       — art direction, aesthetic coherence
#   1: Experience Designer     — self-expression surfaces (journal, studio, reader)
#   2: Entrainment Engineer    — hypnosis / binaural / trance audio stack
#   3: Motion Engineer         — dynamic animation builds (Matter.js, Canvas, Tone.js)
#   4: Game & Ritual Designer  — embedded gaming + routine/ritual building
#   5: Depth Psychologist      — psychoanalysis insights from OAuth connections
#   6: Reliability Engineer    — keep it running on free/installed packages
#
# Pipeline: Context → Rotating Lens → Engineer → Reviewer
#
# Usage:   ./scripts/daily_dev.sh
# Cron:    0 9 * * 1-5 cd /path/to/channelzero && ./scripts/daily_dev.sh >> .agent-sessions/cron.log 2>&1
# ============================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE=/opt/homebrew/bin/claude
SESSION_DIR="$REPO_ROOT/.agent-sessions/$(date +%Y-%m-%d_%H%M)"
LOG="$SESSION_DIR/pipeline.log"

mkdir -p "$SESSION_DIR"
cd "$REPO_ROOT"

# ── GitHub auth via PAT from .env ──────────────────────────
if [ -f "$REPO_ROOT/.env" ]; then
  GITHUB_PAT="$(grep '^GITHUB_PAT=' "$REPO_ROOT/.env" | cut -d= -f2- | tr -d '[:space:]')"
  if [ -n "$GITHUB_PAT" ]; then
    export GH_TOKEN="$GITHUB_PAT"
  fi
fi

# Validate gh CLI auth before starting
if ! gh auth status &>/dev/null; then
  echo "ERROR: gh CLI not authenticated. Check GITHUB_PAT in .env or run: gh auth login"
  exit 1
fi

# ── Helpers ────────────────────────────────────────────────
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
hr()  { echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG"; }

run_agent() {
  local name="$1"
  local out="$SESSION_DIR/${name}.md"
  local prompt="$2"
  local tools="${3:-Bash,Read,Glob,Grep}"

  log "▶  Starting agent: $name"
  "$CLAUDE" -p "$prompt" \
    --allowedTools "$tools" \
    --output-format text \
    2>>"$LOG" \
    | tee "$out"
  log "✓  Agent $name complete → $out"
  echo "$out"
}

# ── Role rotation (day-of-year % 7) ───────────────────────
DOY=$(date +%j)
# Strip leading zeros so bash doesn't interpret as octal
DOY=$((10#$DOY))
ROLE_IDX=$(( DOY % 7 ))

declare -a ROLE_NAMES=(
  "Creative Director"
  "Experience Designer"
  "Entrainment Engineer"
  "Motion Engineer"
  "Game and Ritual Designer"
  "Depth Psychologist"
  "Reliability Engineer"
)

ROLE_NAME="${ROLE_NAMES[$ROLE_IDX]}"

log "TODAY'S LENS: $ROLE_NAME (day $DOY, index $ROLE_IDX)"

# ── Role-specific analyst prompts ─────────────────────────

build_analyst_prompt() {
  local context_file="$1"
  local context
  context="$(cat "$context_file")"

  local preamble="You are working on ChannelZero — a suite of immersive self-expression and hypnosis experiences: binaural/trance entrainment, generative visuals, a hypnotic spiral, a starfield breath-coherence journey, a journal (text/drawing/audio), a glass video studio, and a speed reader. Layered underneath is a psychoanalysis layer that reads insight from the user's OWN OAuth connections (Spotify, GitHub, YouTube, Reddit, Steam, Letterboxd, Strava, GCal, Co-Star).

Stack: Vue 3 + Vite + TypeScript + Tailwind (frontend); FastAPI + Neon PostgreSQL (backend); Tone.js + Matter.js + Web Audio + Canvas power the experiences.

CREATIVE DIRECTION — this overrides any older 'matching engine' framing:
- The product is SELF-EXPRESSION, HYPNOSIS/ENTRAINMENT, ROUTINE-BUILDING, and EMBEDDED GAMING. It is NOT a dating/swipe app.
- The Pinecone vibe-vector MATCHING NETWORK is shelved/aspirational. Do NOT propose embedding work, ANN matching, 'three shadows', mutual-match swiping, or karma-ledger features. The paid OpenAI embed key is intentionally unfunded — assume it stays that way.
- Psychoanalysis INSIGHTS come from per-connector LLM narratives over the user's own stored data (e.g. Spotify sonic profile → a psyche reading; GitHub → a maker's-mind reading). These run on user-supplied keys and need NO embeddings and NO Pinecone.
- Strongly prefer work that runs entirely on already-installed packages (Tone.js, Matter.js, Web Audio, Canvas). Avoid anything that requires a paid API to function.

CONTEXT from the session audit:
$context
"

  case $ROLE_IDX in
    0) # Creative Director
      cat <<PROMPT
$preamble
You are the Creative Director of ChannelZero. Your lens is art direction and aesthetic coherence across every immersive surface.

TASKS (output clean markdown):

1. **Aesthetic audit** — open the visual views (src/views/SpiralView.vue, TranceView.vue, WebAudioView.vue, ZeromindView.vue, HypnoView.vue, StudioView.vue). Describe the current visual language: palette, motion vocabulary, typography. Where does it feel coherent and where does it feel like different hands?

2. **Mood & intention** — for each experience, name the felt-state it is trying to induce (e.g. dissolution, focus, awe, surrender). Flag any view whose visuals fight its intended state.

3. **One signature move** — propose a single recurring visual/motion motif that could tie the whole suite together (a shared color ramp, a shared easing curve, a shared grain/bloom). Make it concrete enough to implement.

4. **Highest-impact art direction fix** — pick one view and write a tight brief: current look → target look, exact file, specific Canvas/CSS/Tone changes, and why it deepens the experience.

5. **Quick wins** — up to 5 small aesthetic fixes (<30 min each): file, what to change, the feeling it buys.

Output: structured markdown, opinionated, specific file paths. Think like an artist with taste, not a startup.
PROMPT
      ;;
    1) # Experience Designer
      cat <<PROMPT
$preamble
You are the Experience Designer for ChannelZero. Your lens is the self-expression surfaces: where the user MAKES something.

TASKS (output clean markdown):

1. **Expression inventory** — trace the surfaces where a user creates/expresses: src/views/JournalView.vue, StudioView.vue (glass studio), ReaderView.vue, CheckinView.vue. For each: is the creative act smooth or friction-filled? What stops someone mid-flow?

2. **The empty-canvas problem** — for each surface, what greets a first-time user? Is there a prompt, a seed, an invitation — or a blank void? Propose concrete first-touch invitations.

3. **Capture & keep** — does anything the user makes persist beautifully? Audit how journal entries / studio exports / drawings are saved and revisited. Where does expression get lost?

4. **Top expression upgrade** — pick the single surface where a focused change most increases the joy of making. Write the flow (current vs proposed), exact files, and microcopy.

5. **Quick wins** — up to 5 small expressive affordances (<30 min each): a send button, a mood color, an autosave toast. File + change + why.

Output: structured markdown. Frame everything around how it FEELS to make something here.
PROMPT
      ;;
    2) # Entrainment Engineer
      cat <<PROMPT
$preamble
You are the Entrainment Engineer for ChannelZero. Your lens is the hypnosis / binaural / trance audio engine.

TASKS (output clean markdown):

1. **Audio architecture map** — read src/composables/useTranceEngine.ts, useAudioMixer.ts, useMeditation.ts, useSignalSynth.ts, and public/trance-tone-engine.html. Diagram how Tone.js, raw Web Audio, and HTMLAudioElement coexist. Flag duplication or drift between the parallel systems.

2. **Entrainment integrity** — verify the binaural math: carrier/beat frequencies, stereo separation, and the phase progression in the WebAudio guided session (induction → coherence → entrainment → warmth → wake). Is the science sound? Any silent failure if headphones/stereo are absent?

3. **Deepening opportunities** — propose 2-3 ways to make an induction land harder using ONLY installed packages: isochronic pulsing, breath-locked amplitude, phrase-synced suggestion timing, dynamic detune.

4. **Top entrainment build** — pick the single highest-impact audio improvement. Exact files, the Tone.js/Web Audio changes, and the subjective effect it should produce.

5. **Quick wins** — up to 5 small audio fixes (<30 min each): a missing fade, a click on start, a volume ramp. File + change + why.

Output: structured markdown. Be specific about frequencies, nodes, and files.
PROMPT
      ;;
    3) # Motion Engineer
      cat <<PROMPT
$preamble
You are the Motion Engineer for ChannelZero. Your lens is dynamic animation built on the packages we ALREADY have (Matter.js, Canvas 2D, Tone.js-driven motion, CSS).

TASKS (output clean markdown):

1. **Animation inventory** — scan src/composables/useCosmicPhysics.ts, useSpotifyPhysics.ts and the canvas views. Catalog the live animation systems: what's physics-driven, what's hand-rolled rAF, what's CSS. Note frame-rate risks and any jank.

2. **Idle vs alive** — find screens that are visually static and would come alive with motion (loading states, empty states, transitions between views). List them.

3. **New animation concepts** — propose 3 NEW dynamic animations buildable today with Matter.js / Canvas / audio-reactive motion. For each: the visual idea, which package drives it, and where it would live. Bias toward things that are mesmerizing and on-theme (orbital, fluid, particulate, breathing).

4. **Top animation build** — pick the single most striking one and write an implementation sketch: file to create/modify, the core loop, how it hooks into existing canvas/overlay patterns, perf budget.

5. **Quick wins** — up to 5 small motion polish items (<30 min each): an easing fix, a parallax layer, a hover ripple. File + change + why.

Output: structured markdown. Specific about the render loop and the package doing the work.
PROMPT
      ;;
    4) # Game and Ritual Designer
      cat <<PROMPT
$preamble
You are the Game & Ritual Designer for ChannelZero. Your lens is embedded gaming AND routine/ritual building — turning use into a practice the user wants to return to.

TASKS (output clean markdown):

1. **Loop audit** — read src/views/GameView.vue, CheckinView.vue, and the poll/onboarding flow. What are the current game/ritual loops? Where is there a satisfying beat (anticipation → action → feedback) and where does it fall flat?

2. **Routine spine** — design (or improve) a daily routine the user can build: a check-in, a chosen entrainment session, a journal beat, an insight reveal. What's the minimal satisfying daily loop, and what state must persist between days?

3. **Embedded game ideas** — propose 2-3 small games/rituals that fit the hypnotic, introspective tone and run on installed packages (e.g. a breath-timing minigame on the WebAudio ring, a tarot-like insight draw, a focus-streak ritual). NO matching/swipe mechanics.

4. **Top build** — pick the single ritual/game beat with the best return-on-effort. Exact files, the loop, the persistence (localStorage or a small DB table — migration as SQL only, do not run it), and the feedback moment.

5. **Quick wins** — up to 5 small engagement touches (<30 min each): a streak counter, a completion flourish, a 'come back tomorrow' beat. File + change + why.

Output: structured markdown. Think in loops, beats, and reasons to return — not funnels.
PROMPT
      ;;
    5) # Depth Psychologist
      cat <<PROMPT
$preamble
You are the Depth Psychologist for ChannelZero. Your lens is the psychoanalysis INSIGHTS generated from the user's own OAuth connections — WITHOUT embeddings or matching.

TASKS (output clean markdown):

1. **Insight inventory** — read server/app/llm/psychoanalysis.py and the per-connector analyzers (e.g. spotify/router.py _analyze_spotify_profile, plus github/, youtube/, reddit/, steam/, letterboxd/, strava/, gcal/, costar/ routers). For each connector, note: does it produce a human-readable psychological narrative today? Where is that surfaced in the UI?

2. **Coverage gaps** — which connectors store data but generate NO insight narrative yet? Rank them by how rich the raw signal is (e.g. listening history, commit patterns, watch history, activity rhythms).

3. **Cross-connector reading** — propose how to author a single integrated 'portrait' that reads ACROSS connectors using a direct LLM call on the stored profiles (no Pinecone). What's the prompt shape? What data does it stitch together?

4. **Top insight build** — pick the single highest-signal connector lacking a narrative and design its analyzer: exact files, the distilled-profile → prompt → narrative path, mirroring the Spotify pattern. Must run on a user-supplied LLM key and degrade gracefully without one.

5. **Quick wins** — up to 5 small insight upgrades (<30 min each): a sharper prompt, a surfaced narrative, a 'why we think this' line. File + change + why.

Output: structured markdown. The reading should feel uncanny and earned, drawn from real behavior.
PROMPT
      ;;
    6) # Reliability Engineer
      cat <<PROMPT
$preamble
You are the Reliability Engineer for ChannelZero. Your lens is keeping everything running on free/installed packages with no paid-API dependence.

TASKS (output clean markdown):

1. **Free-stack audit** — scan for any code path that hard-depends on a paid API (OpenAI embeddings, paid LLM defaults). Confirm each degrades gracefully (logs + no crash) when the key is absent. Flag anything that silently breaks the UX.

2. **Package health** — run \`npm outdated 2>/dev/null | head -20\`. Confirm Tone.js and Matter.js are npm deps (not CDN). Flag any remaining CDN <script> single-points-of-failure in index.html or views.

3. **Offline & cold-start** — which experiences must work with no backend (the public trance/visual routes)? Verify they don't block on an API call. Note Render cold-start exposure on first authed action.

4. **Free model options** — research and list concrete options for running the psychoanalysis narratives WITHOUT a paid key: local/free inference, user-supplied keys (already the pattern), or a free-tier API. Recommend one path with tradeoffs. (Report only — do not wire up secrets.)

5. **Top reliability fix** — the single change that most reduces silent breakage for a user on the free stack. Exact files, the change, the failure it prevents.

Output: structured markdown. Optimize for 'works with zero paid dependencies'.
PROMPT
      ;;
  esac
}

# ── Phase 0: Context & Validation ────────────────────────
hr
log "PHASE 0 — Context & Validation"
hr

CONTEXT_FILE=$(run_agent "00_context" "
You are a senior engineering lead auditing the ChannelZero codebase at $REPO_ROOT.

TASKS (do them in order, output clean markdown):

1. **Git status** — run \`git log --oneline -15\` and \`git branch -a\`. Summarize what shipped recently and what branches are open.

2. **Frontend tests** — run \`npm run test -- --reporter=verbose --run 2>&1 | tail -40\` from $REPO_ROOT. Report pass/fail counts and any failing tests.

3. **Python sanity** — from $REPO_ROOT/server, run \`python test_config.py 2>&1\` and \`python test_pydantic.py 2>&1\`. Report results.

4. **Codebase snapshot** — count lines of code per major directory (src/, server/app/). List any TODO/FIXME comments found with \`grep -r 'TODO\|FIXME' src/ server/app/ --include='*.py' --include='*.ts' --include='*.vue' -l\`.

5. **Dependency health** — check for outdated npm packages with \`npm outdated 2>/dev/null | head -20\` and report anything critical.

6. **README TODOs** — read README.md and extract the current TODO/roadmap items as a numbered list.

Output format: clean markdown with headers for each section. Be factual and terse. No fluff.
" "Bash,Read,Glob,Grep")

# ── Phase 1: Rotating Analyst ─────────────────────────────
hr
log "PHASE 1 — $ROLE_NAME (Rotating Lens)"
hr

ANALYST_PROMPT="$(build_analyst_prompt "$CONTEXT_FILE")"
ANALYST_FILE=$(run_agent "01_analyst_$(echo "$ROLE_NAME" | tr ' /' '_' | tr '[:upper:]' '[:lower:]')" "$ANALYST_PROMPT" "Bash,Read,Glob,Grep")

# ── Phase 2: Engineer (Implementation) ────────────────────
hr
log "PHASE 2 — Engineer (Implementation, informed by $ROLE_NAME)"
hr

BRANCH_ID=$(cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | head -c 6)
BRANCH_DATE=$(date +%Y-%m-%d)
BRANCH_NAME="claude/daily-agent-${BRANCH_DATE}-${BRANCH_ID}"

ENG_FILE=$(run_agent "02_engineer" "
You are a senior full-stack engineer implementing the top-priority item for ChannelZero.

TODAY'S LENS: $ROLE_NAME
Their analysis and priorities:
$(cat "$ANALYST_FILE")

ORIGINAL CONTEXT:
$(cat "$CONTEXT_FILE")

CONSTRAINTS (non-negotiable):
- Follow Vue 3 \`<script setup lang=\"ts\">\` pattern for all components
- FastAPI routers with Pydantic models for backend
- Tailwind CSS only — no inline styles
- JWT auth middleware for protected routes
- DB migrations go in server/migrations/ as standalone SQL — do NOT execute them
- No .env modifications
- One focused change — do not scope-creep
- Do NOT add Pinecone / embedding / vibe-vector matching code — that network is shelved
- Do NOT introduce a dependency that requires a paid API key to function
- Prefer features that run on already-installed packages (Tone.js, Matter.js, Web Audio, Canvas)
- OAuth 'insights' = a direct LLM narrative over stored connector data, gated on a user-supplied key, degrading gracefully without one

TASKS:
1. Pick the single highest-priority, lowest-risk improvement from the $ROLE_NAME analysis that you can implement fully in this session. If scope is too large, pick a sub-task.

2. Write a one-paragraph implementation plan before touching any code.

3. Create a feature branch:
   \`\`\`
   git checkout -b $BRANCH_NAME
   \`\`\`

4. Implement the change. Add comments only where logic is non-obvious.

5. Stage and commit (use specific file paths, never \`git add .\`):
   \`\`\`
   git add src/path/to/changed/file.vue server/app/path/to/file.py
   git commit -m '<type>: <concise description>'
   \`\`\`

6. Push the branch to GitHub:
   \`\`\`
   git push -u origin $BRANCH_NAME
   \`\`\`

7. Open a PR against main:
   \`\`\`
   gh pr create \\
     --base main \\
     --head $BRANCH_NAME \\
     --title '<concise title under 60 chars>' \\
     --body \"\$(cat <<'PRBODY'
## What & Why
<rationale from step 1>

## Changes
<bullet list of files changed and what changed>

## How to Test
<step-by-step test instructions>

## Migrations
<None, or: See server/migrations/XXX.sql — run manually before deploying>

🤖 Generated by ChannelZero Daily Dev Agent ($ROLE_NAME lens)
PRBODY
   )\"
   \`\`\`

8. Output a final summary including:
   - PR URL (copy the URL gh prints)
   - What you built and why
   - Files changed (with line counts)
   - How to manually test it
   - Any migrations needed
   - What was left out of scope
" "Bash,Read,Write,Edit,Glob,Grep")

# ── Phase 3: Role-matched Reviewer ────────────────────────
hr
log "PHASE 3 — $ROLE_NAME Review & Session Report"
hr

REVIEW_FILE=$(run_agent "03_review" "
You are the $ROLE_NAME for ChannelZero, reviewing what was built today.

ANALYST REPORT (your earlier analysis):
$(cat "$ANALYST_FILE")

ENGINEERING OUTPUT:
$(cat "$ENG_FILE")

TASKS (output clean markdown):

1. **Implementation review** — does the engineer's work address the top priority from your analysis? Did they cut scope appropriately or miss something critical?

2. **What shipped** — one-paragraph summary of today's concrete output, framed from the $ROLE_NAME perspective. What does this change mean for the experience (pick the lens that matches your role)?

3. **Remaining gap** — what's the single most important thing that DIDN'T get done today? Why does it matter?

4. **Tomorrow's handoff** — write 2-3 specific Claude Code prompts for the next session, ordered by priority. Each must:
   - Reference exact file paths
   - Be scoped to 30-60 min
   - Include one sentence on why it's next

5. **Development velocity note** — from \`git log --oneline --since='7 days ago'\`, comment on pace. One sentence.

Output: structured markdown, terse. You're writing a handoff doc, not an essay.
" "Bash,Read,Glob,Grep")

# ── Summary ────────────────────────────────────────────────
hr
log "PIPELINE COMPLETE — Generating summary"
hr

SUMMARY="$SESSION_DIR/SUMMARY.md"
cat > "$SUMMARY" <<EOF
# ChannelZero Daily Dev Session — $(date +"%Y-%m-%d %H:%M")

## Today's Lens: $ROLE_NAME (rotation index $ROLE_IDX)

### Lens Rotation Schedule
| Index | Lens | Next Occurrence |
|-------|------|-----------------|
| 0 | Creative Director | $(python3 -c "
import datetime
today = datetime.date.today()
for d in range(1, 8):
    future = today + datetime.timedelta(days=d)
    if future.timetuple().tm_yday % 7 == 0:
        print(future.isoformat()); break
" 2>/dev/null || echo "—") |
| 1 | Experience Designer | $(python3 -c "
import datetime
today = datetime.date.today()
for d in range(1, 8):
    future = today + datetime.timedelta(days=d)
    if future.timetuple().tm_yday % 7 == 1:
        print(future.isoformat()); break
" 2>/dev/null || echo "—") |
| 2 | Entrainment Engineer | $(python3 -c "
import datetime
today = datetime.date.today()
for d in range(1, 8):
    future = today + datetime.timedelta(days=d)
    if future.timetuple().tm_yday % 7 == 2:
        print(future.isoformat()); break
" 2>/dev/null || echo "—") |
| 3 | Motion Engineer | $(python3 -c "
import datetime
today = datetime.date.today()
for d in range(1, 8):
    future = today + datetime.timedelta(days=d)
    if future.timetuple().tm_yday % 7 == 3:
        print(future.isoformat()); break
" 2>/dev/null || echo "—") |
| 4 | Game and Ritual Designer | $(python3 -c "
import datetime
today = datetime.date.today()
for d in range(1, 8):
    future = today + datetime.timedelta(days=d)
    if future.timetuple().tm_yday % 7 == 4:
        print(future.isoformat()); break
" 2>/dev/null || echo "—") |
| 5 | Depth Psychologist | $(python3 -c "
import datetime
today = datetime.date.today()
for d in range(1, 8):
    future = today + datetime.timedelta(days=d)
    if future.timetuple().tm_yday % 7 == 5:
        print(future.isoformat()); break
" 2>/dev/null || echo "—") |
| 6 | Reliability Engineer | $(python3 -c "
import datetime
today = datetime.date.today()
for d in range(1, 8):
    future = today + datetime.timedelta(days=d)
    if future.timetuple().tm_yday % 7 == 6:
        print(future.isoformat()); break
" 2>/dev/null || echo "—") |

## Session Artifacts
| Phase | Agent | Output |
|-------|-------|--------|
| 0 — Context | Engineering Lead | [00_context.md](00_context.md) |
| 1 — Analysis | $ROLE_NAME | [01_analyst.md](01_analyst_$(echo "$ROLE_NAME" | tr ' /' '_' | tr '[:upper:]' '[:lower:]').md) |
| 2 — Build | Engineer | [02_engineer.md](02_engineer.md) |
| 3 — Review | $ROLE_NAME | [03_review.md](03_review.md) |

## Branch & PR
- Branch: \`$BRANCH_NAME\`
- PR: see \`02_engineer.md\` for the GitHub PR URL

## Quick Links
- Run \`gh pr list\` to see the open PR
- Run \`git diff main...$BRANCH_NAME --stat\` to review changes
- Read \`$SESSION_DIR/03_review.md\` for tomorrow's handoff prompts

---
*Generated by scripts/daily_dev.sh — $ROLE_NAME rotation*
EOF

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Session saved to: $SESSION_DIR"
log "Summary: $SUMMARY"
log "Lens:    $ROLE_NAME"
log "Branch:  $BRANCH_NAME"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Print review report to terminal as the final highlight
echo ""
echo "════════════════════════════════════════════════"
echo "  $ROLE_NAME — SESSION REVIEW"
echo "════════════════════════════════════════════════"
cat "$REVIEW_FILE"
