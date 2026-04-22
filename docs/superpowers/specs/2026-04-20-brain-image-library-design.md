# Brain Image Library — Design Spec

## Overview
A visual similarity engine that lets users upload images, embeds them as vectors in Pinecone, and enables branching traversal through vector space — rendered as interactive orbs in the existing Matter.js cosmic physics engine.

## Architecture

### Data Pipeline
1. User uploads images via `/api/brain/upload`
2. GPT-4o vision generates a rich visual description of each image
3. `text-embedding-3-small` embeds that description → 1,536-dim vector
4. Vector upserted to Pinecone `"images"` namespace with metadata
5. Image file stored in Vercel Blob (MVP: base64 in DB)
6. PostgreSQL `brain_images` table stores the catalog record

### Similarity Traversal
- Given a current image, query Pinecone for top-3 nearest neighbors (cosine)
- Exclude visited images to prevent loops
- Minimum similarity threshold: 0.4
- Dead-end handling: jump to most distant unvisited image

### Physics Visualization
- Extends `useCosmicPhysics` — images become circular-clipped orbs
- 1 center orb (current) + 3 branch orbs (neighbors)
- Spring stiffness scales with similarity score
- Click a branch → animates to center, fetches new branches
- History breadcrumb trail for back-navigation

## Files Created

### Backend
- `server/app/brain/__init__.py`
- `server/app/brain/models.py` — Pydantic schemas
- `server/app/brain/service.py` — GPT-4o vision, embedding, Pinecone ops
- `server/app/brain/router.py` — upload, library, traverse, delete endpoints
- `server/migrations/012_brain_images.sql` — brain_images table

### Modified
- `server/app/main.py` — registered brain router
- `server/requirements.txt` — added python-multipart

## API Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/brain/upload` | yes | Upload image → describe → embed → store |
| GET | `/api/brain/library` | yes | List user's images (paginated) |
| GET | `/api/brain/traverse` | yes | Get 3 nearest unvisited branches |
| DELETE | `/api/brain/{id}` | yes | Remove from DB + Pinecone |

## Test Results (2026-04-20)

Pipeline smoke test passed:
- Pinecone upsert to `"images"` namespace: **OK**
- Vector fetch/verify (1,536 dims): **OK**
- Similarity query with metadata filter: **OK**
- Cleanup/delete: **OK**

## Blocker: OpenAI API Key Permissions

**Status:** The current `OPENAI_EMBED_KEY` (project `proj_8pERhmljbOUkRzurStcMGtZ5`) returns 403 for both embeddings and chat completions.

**To unblock:**
1. Go to https://platform.openai.com/settings/organization/projects
2. Find project `proj_8pERhmljbOUkRzurStcMGtZ5`
3. Enable model access for:
   - `text-embedding-3-small` (required — embeddings)
   - `gpt-4o` (required — vision descriptions)
4. Or generate a new key with access to both models and update `OPENAI_EMBED_KEY` in `.env` and Render

**Note:** This also blocks the existing intake/journal embedding pipeline — `text-embedding-3-small` is 403 on the current key, so vibe vectors and journal RAG are also non-functional.

## Scope Not Yet Built
- Frontend: `BrainView.vue`, `useImageBrainPhysics.ts`, `useBrainStore.ts`
- Vercel Blob storage (currently base64 in DB)
- ChatGPT conversation scraping (Phase D)
- TTS narration during traversal
- Audio/glass tones integration
- Cross-modal similarity (image ↔ user vibe vectors)
