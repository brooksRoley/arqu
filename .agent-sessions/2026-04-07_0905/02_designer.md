---

# ChannelZero — UX Audit Report

---

## 1. Component Audit

### Views — Flow Status

| View | Flow Complete? | Stubs/Placeholders | Missing States |
|------|---------------|-------------------|----------------|
| `HomeView.vue` | Mostly complete — poll → theme recommendation loop works | Poll results link to experiences but don't persist across sessions | No empty state if user skips poll |
| `LoginView.vue` | Complete — register/login toggle, validation, redirect | None | Error message clears on mode switch (disorienting); no "forgot password" |
| `OauthView.vue` (Calibrate) | Partially complete — Spotify real; Twitter, GCal locked | Twitter + GCal show as "CONNECT X / GOOGLE CALENDAR" but are non-functional placeholders | No feedback if Spotify fails mid-auth; no progress indicator through calibration steps |
| `PeripheralSync.vue` | Mostly complete | Co-Star uses `window.prompt()` for credential capture (non-standard, jarring) | No "why this data?" explainer; no last-sync age indicator |
| `PsychoanalysisView.vue` | Complete | None | No save-in-progress; browser back loses all answers |
| `IntakeView.vue` | Complete — multi-turn chat | Oracle responses are LLM-dependent; loading state exists | Silent fail if LLM key is missing or invalid; no retry |
| `GameView.vue` | Partially complete | Scan animation + match card are real; "Deploy" acceptance flow is thin | No state if no matches found; match card has no dismiss/pass mechanic; Oracle debrief has no exit path that doesn't feel abrupt |
| `JournalView.vue` | Complete | None | No empty state for history sidebar (first-use experience absent); no confirmation on delete |
| `CheckInView.vue` | Complete | Streak counter present | Streak shows "0" with no encouragement on first visit |
| `ReaderView.vue` | Complete | None | No error if story text is empty/missing |
| `GlassView.vue` | Complete | Export "progress" shows percentage but no estimated time | Cancel during export has no confirmation |
| `ZeromindView.vue` | Complete | Tone.js loaded from CDN (fragile) | No error if CDN load fails |
| `TranceView.vue` | Complete wrapper | None | — |
| `HypnoView.vue` | Complete | None | — |
| `LiquidGlassView.vue` | Complete | `/liquid-glass.html` loaded via iframe (opaque) | iframe load error is invisible to user |
| `PollView.vue` | Complete | None | No back-button handling from theme result page |
| `GoogleCallback.vue` | Complete | None | Redirect loop if token exchange fails |
| `XCallback.vue` | Complete | None | PKCE verifier loss from localStorage not handled gracefully |
| `Fitting.vue` | Appears to be a standalone/exploratory stub | SVG body measurement UI with no connection to rest of app | Entirely disconnected — no route from any nav item |

**Key broken/incomplete flows:**
- `Fitting.vue` — orphaned, not wired to any feature
- `OauthView.vue` — two of three primary OAuth buttons are dead; users may complete "calibration" thinking they're done when only Spotify is actually connected
- `GameView.vue` — no empty/no-match state; pass/reject mechanic missing (users can only accept)
- `IntakeView.vue` — silent failure on missing LLM key is a full blocker with no recovery path shown

---

## 2. Design System Check

### Inconsistencies Found

**Spacing**
- Cards use `p-8` in some views (`OauthView`) and `p-6` / `px-6 py-4` in others (`JournalView`, `CheckInView`) with no apparent semantic distinction.
- Connect buttons across OAuth views use different height conventions: some are `py-4`, some `py-3`, some implicitly sized by `h-12`.
- `GlassView` and `AudioplayerView` have nearly identical tool-panel layouts built independently with slightly different gap sizes (`gap-3` vs `gap-4`).

**Color — Accent Fragmentation**
- "Success/connected" state is represented by three different colors depending on which component: `emerald-500` (Spotify, Letterboxd), `orange-400` (Strava), `blue-400` (GCal/Steam). This is intentional per-service branding, but the **connected checkmark badge** itself changes color per service with no semantic meaning — it reads as inconsistency, not intent.
- Error states use `red-400`, `red-500`, and `rose-500` interchangeably.
- Disabled states use `opacity-20`, `opacity-40`, and `opacity-50` — no single standard.

**Typography**
- Uppercase tracking labels use `tracking-wider` in most places, `tracking-widest` in a few (`PsychoanalysisView`, `TranceCanvas`). No clear rule for when each applies.
- Body text inside cards alternates between `text-sm text-slate-400` and `text-sm text-gray-400` — these are effectively identical but the inconsistency suggests no shared token.
- `font-mono` is used both for time/code displays (appropriate) and for general UI labels in `PsychoanalysisView` (lime terminal aesthetic) — creates a tone mismatch when users flow from one section to another.

**Button States**
- Primary CTA buttons: most use `active:scale-95` but several in `GlassView` and `AudioplayerView` do not, making those buttons feel unresponsive.
- Hover states: `hover:bg-white/10` is the most common pattern, but some buttons use `hover:opacity-80` instead — both serve the same function, applied inconsistently.

**Z-Index Stack**
- Multiple layers at `z-50`: AudioDashboardControls, NavBar, export overlay, modal backdrops. No documented stacking order — adding a new overlay is a guess.

---

## 3. Design Brief — #1 ROI Feature: The Match Flow (GameView)

This is the core product. Everything else (intake, OAuth, psychoanalysis, journal) is funnel into this moment. It's currently the weakest UX in the app.

### User Flow (Step by Step)

```
1. User lands on /game
   → See: animated "scanning" state with status messages
   → Duration: ~3–5s
   → CTA: none (automatic)

2. Match found
   → See: profile card slides in — codename, compatibility %, venue, time window
   → CTA: "ACCEPT DEPLOYMENT" (only option)
   → Missing: pass/skip option, "why this match?" explanation

3. Accept → Oracle debrief chat
   → See: Oracle provides reasoning + prompts for prep
   → CTA: user types response, Oracle replies
   → Missing: clear exit, no "what happens next?" confirmation

4. [Gap] → No handoff to actual coordination (calendar, contact)
```

### Redesigned Flow

```
1. Scan Loading Screen
   Tone: ritual, not mechanical. "Reading your signal..." not "Scanning..."
   Visual: keep the animation, add a subtle progress arc
   Duration: show 3–4 rotating status phrases, then fade to result

2. Match Card (full-screen, centered)
   Above fold:
     - Codename (large, prominent)
     - Compatibility score (ring visualization, not just a %)
     - One-line Oracle excerpt: "You both surface when the city quiets."
   Below fold (revealed on scroll/swipe):
     - Venue recommendation + why
     - Overlap metrics (3 data points max, iconified)
     - Time window

   CTAs (two options):
     [ ACCEPT — I'm in ]     [ NOT NOW — skip ]
   "Not now" queues the match for 24hrs, doesn't discard it.

3. Accept → Coordinate
   Show proposed calendar slot (from GCal integration)
   CTA: "Block this window" → auto-creates calendar event
   Secondary: "Let me pick a time" → opens time picker

4. Oracle Debrief (optional, collapsible)
   Default collapsed with teaser: "Oracle has a read on this."
   Expands to chat with a clear "Close" button
   End state: "Match confirmed. The window is set." with checkmark
```

### Key UI Components Needed

| Component | Description |
|-----------|-------------|
| `MatchCard.vue` | Full-screen card with score ring, codename, venue, 2 CTAs |
| `CompatibilityRing.vue` | SVG ring at `0–100%`, animated fill on mount |
| `MatchActionBar.vue` | "Accept / Not Now" button pair with haptic-weight styling |
| `OracleCollapsible.vue` | Collapsed teaser → expand to full chat, with exit |
| `CalendarSlotPicker.vue` | Lightweight time picker that hooks into GCal integration |
| `ScanLoader.vue` | Extract from GameView — rotating phrases + progress arc |
| `EmptyMatchState.vue` | "No signal yet" — next check-in time, what improves chances |

### Copy / Microcopy

| Moment | Current | Suggested |
|--------|---------|-----------|
| Scan start | "Scanning..." | "Reading your signal..." |
| Scan status | generic status strings | "Cross-referencing 48 resonance points" / "Filtering for temporal alignment" / "Isolating compatible dissonance" |
| Match found header | (none) | "A signal resolved." |
| CTA accept | "ACCEPT DEPLOYMENT" | "I'm in — lock the window" |
| CTA skip | (missing) | "Not yet — hold this match" |
| Oracle debrief teaser | (not present) | "Oracle has a read on this pairing." |
| No match state | (missing) | "The signal is still forming. Come back tonight." |
| Match confirmed | (missing) | "The window is set. Trust the timing." |

### Accessibility Considerations

- `CompatibilityRing` SVG: add `role="img" aria-label="Compatibility score: 87%"`
- Both CTA buttons need `aria-label` with full context, not just the visual label
- Oracle chat input needs `aria-live="polite"` on the response container so screen readers announce new messages
- "Not Now" must be keyboard-focusable and visually distinct from Accept (not just color — use shape or weight difference)
- Scan loading screen: add `aria-busy="true"` on the container, `role="status"` on status text
- Color contrast: compatibility score ring must meet 4.5:1 against dark background — emerald-400 on near-black passes; verify the specific shade used

---

## 4. Quick Wins

### #1 — Kill `window.prompt()` in Co-Star connect
**File:** `src/components/CoStarConnect.vue`  
**What:** The app uses the browser's native `prompt()` dialog to collect a username. This looks like a browser bug or phishing attempt to most users, and blocks on iOS.  
**Fix:** Replace with the existing modal pattern already in `CoStarConnect.vue` (the component already has a modal UI built — the `prompt()` call is a remnant). Wire the modal's input fields to replace the `prompt()` call. ~20 min.

---

### #2 — Add a "not yet connected" state to OauthView's locked buttons
**File:** `src/views/OauthView.vue`  
**What:** Twitter and GCal buttons appear clickable but do nothing (or redirect to the same page). Users who click them get no feedback.  
**Fix:** Add `cursor-not-allowed opacity-50` + a tooltip `"Coming soon"` to the locked connect buttons, and a small badge `COMING SOON` inline. One Tailwind class change + 2 lines of template per button. ~15 min.

---

### #3 — Empty state for Journal history sidebar (first-use)
**File:** `src/views/JournalView.vue`  
**What:** On first use, the history sidebar is a blank panel with no prompt. Users don't know what to do.  
**Fix:** Add a `v-if="entries.length === 0"` block with copy: *"Your entries will appear here. Start writing above."* and a subtle icon. ~15 min.

---

### #4 — Standardize error color token
**Files:** `src/components/*.vue`, `src/views/LoginView.vue`  
**What:** Error text uses `text-red-400`, `text-red-500`, and `text-rose-500` interchangeably. Pick one — `text-red-400` is already the most-used — and do a global find-replace.  
**Fix:** `sed` or IDE find-replace `text-red-500` → `text-red-400` and `text-rose-500` → `text-red-400` across `src/`. 10 min. (Verify `rose-500` isn't used for a separate semantic purpose first.)

---

### #5 — Add `active:scale-95` to Glass and Audioplayer CTA buttons
**Files:** `src/views/GlassView.vue`, `src/views/AudioplayerView.vue`  
**What:** Preset and transport buttons in these views lack the press-feedback that all other buttons in the app have. They feel broken/unresponsive by comparison.  
**Fix:** Add `active:scale-95 transition-transform` to the button class strings in both views. ~10 min across both files.
