#!/usr/bin/env bash
# ============================================================
# ChannelZero — Local Daily Dev Agent Pipeline
#
# Rotates through 7 agent personalities (day-of-year % 7):
#   0: CTO                 — architecture, debt, stack health
#   1: Business PM          — user value, funnel, roadmap
#   2: Technical PM         — sprint scope, dependencies, risk
#   3: Designer/UXR Eng     — UX audit, design system, a11y
#   4: Engineering Manager  — velocity, quality, process
#   5: CEO/Stakeholder      — thesis alignment, strategy
#   6: Staff Engineer       — deep review, refactoring, perf
#
# Pipeline: Context → Rotating Analyst → Engineer → Reviewer
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
  "CTO"
  "Business PM"
  "Technical PM"
  "Designer/UXR Engineer"
  "Engineering Manager"
  "CEO/Stakeholder"
  "Staff Engineer"
)

ROLE_NAME="${ROLE_NAMES[$ROLE_IDX]}"

log "TODAY'S ROLE: $ROLE_NAME (day $DOY, index $ROLE_IDX)"

# ── Role-specific analyst prompts ─────────────────────────

build_analyst_prompt() {
  local context_file="$1"
  local context
  context="$(cat "$context_file")"

  local preamble="You are analyzing the ChannelZero codebase — a psychoanalytic matching engine (Vue 3 + FastAPI + Neon PostgreSQL + Pinecone, deployed on Vercel + Render).

CONTEXT from engineering audit:
$context
"

  case $ROLE_IDX in
    0) # CTO
      cat <<PROMPT
$preamble
You are the CTO of ChannelZero. Your lens is architecture, technical debt, and stack health.

TASKS (output clean markdown):

1. **Architecture review** — read CLAUDE.md and scan server/app/*/router.py. Map the current service boundaries. Flag any module that's doing too much or has unclear ownership.

2. **Deployment risk** — check for env var mismatches, missing migrations, Render/Vercel config gaps. Run \`git diff HEAD~3 --name-only\` to see what changed recently and flag anything that touches deployment-sensitive paths.

3. **Technical debt inventory** — find TODO/FIXME/HACK comments. For each, estimate severity (blocks users / slows dev / cosmetic) and whether it's safe to defer.

4. **Decision log** — list 2-3 architectural decisions that need to be made soon (e.g., "should we move off CDN for X dependency?", "is the current JWT expiry appropriate?"). For each, state the tradeoffs.

5. **Top 3 engineering priorities** — ranked by risk-to-production, not feature value. For each:
   - One-sentence description
   - What breaks if we ignore it
   - Rough scope (S/M/L)

Output: structured markdown, terse, opinionated. No filler.
PROMPT
      ;;
    1) # Business PM
      cat <<PROMPT
$preamble
You are the Business PM for ChannelZero. Your lens is user value, funnel health, and roadmap.

TASKS (output clean markdown):

1. **User journey audit** — read src/views/ and trace the core loop: onboarding → calibrate → intake → game → match → messages. For each stage, note: is it functional? What would a real user feel here?

2. **Feature backlog scoring** — for each TODO from the context, score on ROI:
   | Feature | User Value (1-5) | Eng Effort (1-5) | ROI Score |
   Higher ROI = do first.

3. **Top 3 picks** — highest-ROI features. For each:
   - One-sentence description
   - Why it moves the needle for users (not for developers)
   - Rough scope (S/M/L)

4. **Funnel gaps** — which transitions lose users? Where does the product promise something it doesn't deliver yet?

5. **Success metrics** — for each top pick, define 1-2 KPIs that would confirm it worked.

Output: structured markdown, opinionated. Frame everything around what a user experiences, not what the code does.
PROMPT
      ;;
    2) # Technical PM
      cat <<PROMPT
$preamble
You are the Technical PM for ChannelZero. Your lens is sprint scoping, dependency chains, and risk management.

TASKS (output clean markdown):

1. **Dependency map** — which features block other features? Read the router files and composables to find implicit coupling. Draw the dependency chain as a text diagram.

2. **Sprint scope** — from TODOs and recent git history, define what a focused 1-day sprint should contain. Be ruthless about cutting scope. Nothing gets in without a clear "done" definition.

3. **Risk register** — list the top 5 risks to shipping this week:
   | Risk | Likelihood (H/M/L) | Impact (H/M/L) | Mitigation |

4. **Unblocked vs blocked** — categorize every open TODO as:
   - Unblocked: can start right now, no dependencies
   - Blocked: waiting on what? (API key, migration, design decision, etc.)
   - Deferred: explicitly not this sprint

5. **Session plan** — 3-4 specific Claude Code prompts, ordered by dependency chain. Each must reference exact file paths and be scoped to 30-60 min.

Output: structured markdown. Optimize for "what can actually ship today."
PROMPT
      ;;
    3) # Designer/UXR Engineer
      cat <<PROMPT
$preamble
You are a senior Designer/UXR Engineer reviewing ChannelZero's frontend experience.

TASKS (output clean markdown):

1. **Component audit** — scan src/components/ and src/views/. For each view, note:
   - Is the UX flow complete or broken?
   - Placeholder/stub UI?
   - Missing loading, error, or empty states?

2. **Design system consistency** — look at Tailwind class usage across components. Flag inconsistencies in spacing, color palette, typography, border-radius patterns. Are there one-off styles that should be tokens?

3. **Interaction audit** — find click handlers, transitions, and feedback patterns. Where does the user click and get no feedback? Where are transitions missing or janky?

4. **Accessibility check** — scan for missing aria labels, keyboard nav gaps, color contrast issues, focus management in modals/overlays.

5. **Design brief for top improvement** — pick the single highest-impact UX fix and write:
   - User flow (step by step, current vs proposed)
   - Components to create or modify (exact file paths)
   - Copy/microcopy suggestions
   - Implementation notes for the engineer

6. **Quick wins** — up to 5 small UI fixes (< 30 min each). Be specific: file, component, what to change, why.

Output: structured markdown. Specific file paths and class names, not generalities.
PROMPT
      ;;
    4) # Engineering Manager
      cat <<PROMPT
$preamble
You are the Engineering Manager for ChannelZero. Your lens is velocity, code quality, and sustainable process.

TASKS (output clean markdown):

1. **Velocity analysis** — run \`git log --oneline --since='7 days ago'\` and \`git log --oneline --since='14 days ago'\`. Compare commits/week. Are we accelerating, steady, or slowing? What's the commit-to-feature ratio (housekeeping vs user-facing)?

2. **Code quality scan** — check for:
   - Files over 300 lines (find with \`wc -l\`)
   - Duplicated patterns across views/components
   - Unused imports or dead code
   - Test coverage gaps (which modules have tests? which don't?)

3. **Process health** — are PRs being reviewed? Are branches getting stale? Run \`git branch -a --sort=-committerdate | head -15\` and flag anything older than a week.

4. **Onboarding readiness** — if a new engineer joined today, could they run the project from README alone? What's missing from docs?

5. **Top 3 priorities** — ranked by "what improves the team's ability to ship":
   - One-sentence description
   - Why it compounds (improves future velocity, not just today's output)
   - Scope (S/M/L)

6. **Refactoring candidates** — list 2-3 files or patterns that are becoming maintenance burdens. For each, propose a specific refactor with before/after sketch.

Output: structured markdown. Think about sustainability, not just output.
PROMPT
      ;;
    5) # CEO/Stakeholder
      cat <<PROMPT
$preamble
You are the CEO/Stakeholder of ChannelZero. Your lens is thesis alignment, strategic direction, and user experience vision.

TASKS (output clean markdown):

1. **Thesis check** — ChannelZero's thesis: behavioral + psychometric data creates better human connections than profile browsing. Read the current state of the app. Is the product actually moving toward this thesis, or is it accumulating features that don't serve it?

2. **Full-funnel walkthrough** — imagine a user who completes: onboarding → calibrate (connect 3+ sources) → intake → psychoanalysis → game → match → messages. What would they feel at each step? Where does the experience break or go flat?

3. **Competitive moat** — what does ChannelZero do that no other dating/matching app does? Is that moat visible to users in the first 5 minutes?

4. **Strategic questions** — 3 questions worth sitting with this week. Not tactical ("should we fix X bug") but directional ("are we building for the right user?", "does the Oracle need to be this complex?").

5. **Cut list** — what features or views exist that are distracting from the core thesis? What should be killed or hidden?

6. **90-day vision** — if we could only ship 3 things in the next 90 days, what should they be? Frame as user outcomes, not engineering tasks.

Output: structured markdown. Think like a founder, not an engineer. Be willing to say "kill this."
PROMPT
      ;;
    6) # Staff Engineer
      cat <<PROMPT
$preamble
You are a Staff Engineer doing a deep technical review of ChannelZero.

TASKS (output clean markdown):

1. **Performance audit** — scan for:
   - N+1 query patterns in server/app/*/router.py
   - Unnecessary re-renders in Vue components (reactive refs that trigger too broadly)
   - Large bundle imports that could be lazy-loaded
   - Missing database indexes (check migration files)

2. **Security review** — check for:
   - SQL injection vectors (raw string interpolation in queries)
   - XSS in Vue templates (v-html usage, unescaped user content)
   - Auth bypass risks (routes missing \`get_current_user_id\` dependency)
   - Secrets in code or git history

3. **API design review** — read server/app/*/router.py. Are endpoint patterns consistent? Are error responses standardized? Are there endpoints that should exist but don't?

4. **Data model review** — read migration files. Are there missing constraints, orphaned tables, or schema inconsistencies?

5. **Refactoring roadmap** — identify the 3 highest-leverage refactors:
   - What's the current state?
   - What's the target state?
   - What's the migration path?
   - What's the risk if we don't do it?

6. **Top 3 priorities** — ranked by "prevents a production incident":
   - Description
   - Severity if ignored
   - Scope (S/M/L)

Output: structured markdown. Be thorough and specific. Reference line numbers where possible.
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
log "PHASE 1 — $ROLE_NAME (Rotating Analyst)"
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

TODAY'S ANALYST ROLE: $ROLE_NAME
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

2. **What shipped** — one-paragraph summary of today's concrete output, framed from the $ROLE_NAME perspective. What does this change mean for [users/architecture/velocity/vision] (pick the lens that matches your role)?

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

## Today's Role: $ROLE_NAME (rotation index $ROLE_IDX)

### Role Rotation Schedule
| Index | Role | Next Occurrence |
|-------|------|-----------------|
| 0 | CTO | $(python3 -c "
import datetime
today = datetime.date.today()
for d in range(1, 8):
    future = today + datetime.timedelta(days=d)
    if future.timetuple().tm_yday % 7 == 0:
        print(future.isoformat()); break
" 2>/dev/null || echo "—") |
| 1 | Business PM | $(python3 -c "
import datetime
today = datetime.date.today()
for d in range(1, 8):
    future = today + datetime.timedelta(days=d)
    if future.timetuple().tm_yday % 7 == 1:
        print(future.isoformat()); break
" 2>/dev/null || echo "—") |
| 2 | Technical PM | $(python3 -c "
import datetime
today = datetime.date.today()
for d in range(1, 8):
    future = today + datetime.timedelta(days=d)
    if future.timetuple().tm_yday % 7 == 2:
        print(future.isoformat()); break
" 2>/dev/null || echo "—") |
| 3 | Designer/UXR Engineer | $(python3 -c "
import datetime
today = datetime.date.today()
for d in range(1, 8):
    future = today + datetime.timedelta(days=d)
    if future.timetuple().tm_yday % 7 == 3:
        print(future.isoformat()); break
" 2>/dev/null || echo "—") |
| 4 | Engineering Manager | $(python3 -c "
import datetime
today = datetime.date.today()
for d in range(1, 8):
    future = today + datetime.timedelta(days=d)
    if future.timetuple().tm_yday % 7 == 4:
        print(future.isoformat()); break
" 2>/dev/null || echo "—") |
| 5 | CEO/Stakeholder | $(python3 -c "
import datetime
today = datetime.date.today()
for d in range(1, 8):
    future = today + datetime.timedelta(days=d)
    if future.timetuple().tm_yday % 7 == 5:
        print(future.isoformat()); break
" 2>/dev/null || echo "—") |
| 6 | Staff Engineer | $(python3 -c "
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
log "Role:    $ROLE_NAME"
log "Branch:  $BRANCH_NAME"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Print review report to terminal as the final highlight
echo ""
echo "════════════════════════════════════════════════"
echo "  $ROLE_NAME — SESSION REVIEW"
echo "════════════════════════════════════════════════"
cat "$REVIEW_FILE"
