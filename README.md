# Channel Zero

Psychoanalytic profiling engine disguised as a meditation app. Vue 3 + FastAPI + Neon Postgres.

## The Pipeline

```
Login → Poll (profiling) → Journal → Intake (confessional) → Game (deployment)
```

- **Poll** — Dissociation/fantasy quiz derives attachment archetype + theme palette
- **Journal** — Write, draw, record audio. Local-first with backend sync
- **Check-In** — Daily dashboard: mood arc, streak, synthesis, intention setting
- **Intake** — Psychoanalytic chat. Confessions encrypted at rest (AES-256-GCM), NLP extracts attachment style + defense mechanism → vibe vector
- **Game** — Matching engine scans vibe vectors, deploys to optimal windows

## Experiences

Binaural entrainment, visual sync, and trance induction modules:

- **Star Tunnel** (`/webaudio`) — Starfield with binaural beat layers
- **Zeromind** (`/zeromind`) — Generative visuals + streaming text
- **Spiral** (`/spiral`) — Hypnotic spiral with trance words
- **Tone Engine** (`/trance`) — Raw binaural tone laboratory (theta/delta descent)

## Setup

```sh
cp .env.example .env   # fill in Neon DB URL + secrets
npm install
npm run dev
```

### Backend

```sh
cd server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m app.migrate
uvicorn app.main:app --reload
```

## Deploy

- **Frontend** — Vercel (auto-deploys from main)
- **Backend** — Render (blueprint in `render.yaml`, auto-migrates on build)
