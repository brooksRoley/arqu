#!/usr/bin/env bash
# ============================================================
# ChannelZero — Local Daily Dev Agent Pipeline
# Runs a multistep agent team: Context → PM → Designer →
# Engineer → Finance, then commits feature branches ranked by ROI.
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

# ── Phase 0: Context & Test Run ────────────────────────────
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

# ── Phase 1: Product Manager ───────────────────────────────
hr
log "PHASE 1 — Product Manager (ROI Prioritization)"
hr

PM_FILE=$(run_agent "01_pm" "
You are a product manager for ChannelZero, a psychoanalytic matching engine (Vue 3 + FastAPI + Neon + Pinecone).

CONTEXT from engineering audit:
$(cat "$CONTEXT_FILE")

TASKS (output clean markdown):

1. **User journey gaps** — read src/views/ and list any views that are stubs, show 'coming soon', or lack real functionality.

2. **Feature backlog scoring** — for each TODO item from the context above, score it on a simple ROI matrix:
   | Feature | User Value (1-5) | Eng Effort (1-5) | ROI Score (Value/Effort) |
   Score honestly. Higher ROI = do first.

3. **Top 3 picks** — select the 3 highest-ROI features. For each, write:
   - One-sentence description
   - Why it moves the needle for users
   - Rough scope (S/M/L)

4. **Success metrics** — for each top pick, define 1-2 measurable KPIs that would confirm it worked (e.g., 'X% of users complete onboarding', 'match acceptance rate > Y%').

5. **Risk flags** — note any technical debt or blockers that would derail the top picks.

Output: structured markdown, no filler. Be opinionated.
" "Read,Glob,Grep")

# ── Phase 2: Designer ──────────────────────────────────────
hr
log "PHASE 2 — Designer (UX Audit + Brief)"
hr

DESIGN_FILE=$(run_agent "02_designer" "
You are a senior UX designer reviewing ChannelZero's frontend.

CONTEXT — PM priorities:
$(cat "$PM_FILE")

TASKS (output clean markdown):

1. **Component audit** — scan src/components/ and src/views/. For each view, note:
   - Is the UX flow complete or broken?
   - Any placeholder/stub UI?
   - Missing loading/error states?

2. **Design system check** — look at how Tailwind classes are used. Are there inconsistencies in spacing, color, or typography patterns across components?

3. **Design brief for top PM pick** — take the #1 ROI feature from the PM report and write a concrete design brief:
   - User flow (step by step)
   - Key UI components needed
   - Copy/microcopy suggestions
   - Any accessibility considerations

4. **Quick wins** — list up to 5 small UI fixes (< 30 min each) that would noticeably improve the feel of the app. Be specific: file, component, what to change.

Output: structured markdown. Focus on actionable specifics, not generalities.
" "Read,Glob,Grep")

# ── Phase 3: Engineer ──────────────────────────────────────
hr
log "PHASE 3 — Engineer (Implementation)"
hr

BRANCH_ID=$(cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | head -c 6)
BRANCH_DATE=$(date +%Y-%m-%d)
BRANCH_NAME="claude/daily-agent-${BRANCH_DATE}-${BRANCH_ID}"

ENG_FILE=$(run_agent "03_engineer" "
You are a senior full-stack engineer implementing the top-priority feature for ChannelZero.

CONTEXT — PM priorities:
$(cat "$PM_FILE")

CONTEXT — Design brief:
$(cat "$DESIGN_FILE")

CONSTRAINTS (non-negotiable):
- Follow Vue 3 \`<script setup lang=\"ts\">\` pattern for all components
- FastAPI routers with Pydantic models for backend
- Tailwind CSS only — no inline styles
- JWT auth middleware for protected routes
- DB migrations go in server/migrations/ as standalone SQL — do NOT execute them
- No .env modifications
- One focused change — do not scope-creep

TASKS:
1. Pick the single highest-ROI, lowest-risk improvement from the PM + design context that you can implement fully in this session. If scope is too large, pick a sub-task.

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

🤖 Generated by ChannelZero Daily Dev Agent
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

# ── Phase 4: Finance / KPI Analyst ────────────────────────
hr
log "PHASE 4 — Finance & KPI Report"
hr

FINANCE_FILE=$(run_agent "04_finance" "
You are a product analytics and finance analyst reviewing ChannelZero's development progress.

CONTEXT — Engineering audit:
$(cat "$CONTEXT_FILE")

CONTEXT — PM priorities and ROI scores:
$(cat "$PM_FILE")

CONTEXT — What was built today:
$(cat "$ENG_FILE")

TASKS (output clean markdown):

1. **Development velocity** — from git log, calculate:
   - Commits this week vs last week
   - Features shipped vs TODO list length (completion %)
   - Estimated sprints to MVP based on current pace

2. **Feature ROI ledger** — create a table of all features:
   | Feature | Status | ROI Score | Est. Revenue Impact | Priority |
   Mark each as: Shipped / In Progress / Backlog / Blocked

3. **Technical debt cost** — estimate dev-hours blocked by current debt items. Translate to opportunity cost.

4. **KPI dashboard (pre-launch proxies)**:
   - Onboarding completion rate (based on UI completeness): X%
   - Core loop completeness (quiz → match → connect): X%
   - Backend endpoint coverage: X of Y planned routes implemented
   - Test coverage estimate: X%

5. **Next session recommendation** — one paragraph: what the team should focus on next session and why, given velocity and ROI scores.

Output: clean markdown with tables. Use real data from the context where possible; estimate clearly where not.
" "Bash,Read,Glob,Grep")

# ── Summary ────────────────────────────────────────────────
hr
log "PIPELINE COMPLETE — Generating summary"
hr

SUMMARY="$SESSION_DIR/SUMMARY.md"
cat > "$SUMMARY" <<EOF
# ChannelZero Daily Dev Session — $(date +"%Y-%m-%d %H:%M")

## Session Artifacts
| Agent | Output |
|-------|--------|
| Context & Tests | [00_context.md](00_context.md) |
| Product Manager | [01_pm.md](01_pm.md) |
| Designer | [02_designer.md](02_designer.md) |
| Engineer | [03_engineer.md](03_engineer.md) |
| Finance / KPIs | [04_finance.md](04_finance.md) |

## Branch & PR
- Branch: \`$BRANCH_NAME\`
- PR: see \`03_engineer.md\` for the GitHub PR URL

## Quick Links
- Run \`gh pr list\` to see the open PR
- Run \`git diff main...$BRANCH_NAME --stat\` to review changes
- Read \`$SESSION_DIR/04_finance.md\` for KPIs and next-session rec

---
*Generated by scripts/daily_dev.sh*
EOF

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Session saved to: $SESSION_DIR"
log "Summary: $SUMMARY"
log "Branch:  $BRANCH_NAME"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Print finance report to terminal as the final highlight
echo ""
echo "════════════════════════════════════════════════"
echo "  KPI SNAPSHOT"
echo "════════════════════════════════════════════════"
cat "$FINANCE_FILE"
