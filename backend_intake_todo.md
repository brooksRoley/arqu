## Fast API: The Intake Pipeline & Therapist Hook

- [ ] **1. Construct the `POST /api/intake/confess` Endpoint**
  - This endpoint receives the raw chat strings from `TheIntake.vue`.
  - It MUST NOT store the raw text in the public `users` table.
  - Route the raw text into a secure, encrypted side-table: `intake_shadow_logs`.

- [ ] **2. LLM NLP Extraction (The Subtext Parser)**
  - Pass the `intake_shadow_logs` to the Claude/Gemini API on the backend.
  - **Prompt Injection for the LLM:** *"You are a covert psychoanalyst. Read this user's venting session. Extract their attachment style (Secure, Anxious, Avoidant), their primary defense mechanism, and update their `vibeVector` in the Neon DB. Do not output text. Output only the updated JSON vector schema."*

- [ ] **3. The Calendar Sync Trigger (`GET /api/oauth/google/calendar`)**
  - When the user clicks "Protect My Time", initiate the Google OAuth flow.
  - Request scopes: `calendar.readonly`, `calendar.events`.
  - **CRITICAL:** Once the token is acquired, immediately fire a background task (`BackgroundTasks` in FastAPI) to scan the next 14 days. 
  - Identify gaps larger than 3 hours on Thursday-Saturday nights. Log these as `optimal_deployment_windows` in the Neon DB for the House Party routing engine.

- [ ] **4. The Silent Vector Update**
  - Merge the parsed psychological data (from the chat) with the logistical data (from the calendar).
  - Update the Pinia `channelZero` store via websocket: `vibeVector` is now fully armed. The user is ready for the nightly cronjob.