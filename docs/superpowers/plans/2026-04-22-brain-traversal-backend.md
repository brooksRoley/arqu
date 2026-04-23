# Brain Traversal — Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the brain image pipeline with vibe dimension extraction (GPT-4o-mini), UMAP 2D projection, a map endpoint, and a sequence compose endpoint that returns per-transition animation descriptors.

**Architecture:** Each uploaded image gets a 5-float vibe vector extracted from its GPT-4o description and stored as JSONB. After every upload, UMAP is re-run over all user image embeddings fetched from Pinecone to produce stable 2D coordinates. Two new endpoints serve the map state and compose transition descriptors for an ordered sequence.

**Tech Stack:** Python 3.14, FastAPI, asyncpg, Pinecone, umap-learn, numpy, httpx

---

## File Map

| Action | File |
|---|---|
| Create | `server/migrations/013_brain_vibe_dimensions.sql` |
| Modify | `server/requirements.txt` — add umap-learn |
| Modify | `server/app/brain/models.py` — add VibeDimensions, MapImage, ComposeRequest, TransitionDescriptor, ComposeResponse |
| Modify | `server/app/brain/service.py` — add extract_vibe_dimensions, recompute_umap_for_user |
| Modify | `server/app/brain/router.py` — update upload, add /map and /sequence/compose |

---

## Task 1: Migration — add vibe_dimensions, map_x, map_y columns

**Files:**
- Create: `server/migrations/013_brain_vibe_dimensions.sql`

- [ ] **Step 1: Write the migration**

```sql
-- 013_brain_vibe_dimensions.sql
ALTER TABLE brain_images
  ADD COLUMN IF NOT EXISTS vibe_dimensions JSONB,
  ADD COLUMN IF NOT EXISTS map_x FLOAT,
  ADD COLUMN IF NOT EXISTS map_y FLOAT;
```

- [ ] **Step 2: Run the migration locally**

```bash
cd /Users/brooks/Desktop/channelzero
source server/venv/bin/activate
python -m server.app.migrate
```

Expected: `Applied 013_brain_vibe_dimensions.sql` in output. No errors.

- [ ] **Step 3: Verify columns exist**

```bash
python -c "
import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv('server/.env')
async def check():
    conn = await asyncpg.connect(os.environ['DATABASE_URL_UNPOOLED'])
    rows = await conn.fetch(\"SELECT column_name FROM information_schema.columns WHERE table_name='brain_images'\")
    print([r['column_name'] for r in rows])
    await conn.close()
asyncio.run(check())
"
```

Expected: `['id', 'user_id', 'blob_url', 'filename', 'description', 'pinecone_id', 'width', 'height', 'created_at', 'vibe_dimensions', 'map_x', 'map_y']` (order may vary).

- [ ] **Step 4: Commit**

```bash
git add server/migrations/013_brain_vibe_dimensions.sql
git commit -m "Add vibe_dimensions, map_x, map_y columns to brain_images"
```

---

## Task 2: Add umap-learn to requirements

**Files:**
- Modify: `server/requirements.txt`

- [ ] **Step 1: Add dependency**

Add this line to `server/requirements.txt` after the `numpy` line:

```
umap-learn>=0.5,<1.0
```

- [ ] **Step 2: Install locally**

```bash
source server/venv/bin/activate
pip install umap-learn
```

Expected: installs umap-learn and its deps (numba, llvmlite). No errors.

- [ ] **Step 3: Verify import**

```bash
python -c "from umap import UMAP; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add server/requirements.txt
git commit -m "Add umap-learn dependency for image map projection"
```

---

## Task 3: Add new models

**Files:**
- Modify: `server/app/brain/models.py`

- [ ] **Step 1: Replace the file contents**

```python
"""Brain image library — request/response models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ImageRecord(BaseModel):
    id: UUID
    blob_url: str
    filename: str | None
    description: str | None
    width: int | None
    height: int | None
    created_at: datetime


class UploadResponse(BaseModel):
    image: ImageRecord
    embedded: bool


class TraverseBranch(BaseModel):
    id: UUID
    blob_url: str
    filename: str | None
    similarity: float


class TraverseResponse(BaseModel):
    branches: list[TraverseBranch]


class VibeDimensions(BaseModel):
    energy: float
    warmth: float
    density: float
    intimacy: float
    motion: float


class MapImage(BaseModel):
    id: str
    blob_url: str
    filename: str | None
    description: str | None
    vibe_dimensions: VibeDimensions | None
    map_x: float | None
    map_y: float | None


class ComposeRequest(BaseModel):
    image_ids: list[str]  # ordered DB UUIDs


class TransitionDescriptor(BaseModel):
    from_id: str
    to_id: str
    similarity: float
    color_shift: str   # "warm_to_cool" | "cool_to_warm" | "neutral"
    mood_shift: float  # 0-1, magnitude of energy delta
    subject_continuity: bool
    transition_type: str  # "dissolve" | "flash_cut" | "slow_zoom" | "hard_cut"
    duration: float    # seconds


class ComposeResponse(BaseModel):
    transitions: list[TransitionDescriptor]
    vibe_curve: dict[str, list[float]]  # { "energy": [...], "warmth": [...], ... }
```

- [ ] **Step 2: Verify import**

```bash
python -c "from server.app.brain.models import ComposeResponse, MapImage; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add server/app/brain/models.py
git commit -m "Add MapImage, ComposeRequest, TransitionDescriptor models to brain"
```

---

## Task 4: Add vibe extraction to service

**Files:**
- Modify: `server/app/brain/service.py`

- [ ] **Step 1: Add `extract_vibe_dimensions` function**

Add after the `describe_image` function (after line 69):

```python
async def extract_vibe_dimensions(description: str) -> dict[str, float]:
    """Extract 5 normalized vibe floats from an image description via GPT-4o-mini."""
    key = get_settings().openai_embed_key
    if not key or not description:
        return {"energy": 0.5, "warmth": 0.5, "density": 0.5, "intimacy": 0.5, "motion": 0.5}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "max_tokens": 80,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Return ONLY valid JSON with exactly these five keys, "
                            "each a float between 0.0 and 1.0: "
                            "energy, warmth, density, intimacy, motion. No other text."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Rate these vibe dimensions for this image description:\n\n{description}",
                    },
                ],
            },
        )
        resp.raise_for_status()

    keys = ["energy", "warmth", "density", "intimacy", "motion"]
    try:
        raw = resp.json()["choices"][0]["message"]["content"]
        import json as _json
        data = _json.loads(raw)
        return {k: max(0.0, min(1.0, float(data.get(k, 0.5)))) for k in keys}
    except Exception:
        logger.exception("Vibe dimension extraction failed")
        return {k: 0.5 for k in keys}
```

- [ ] **Step 2: Add `recompute_umap_for_user` function**

Add after `extract_vibe_dimensions`:

```python
async def recompute_umap_for_user(user_id: str) -> None:
    """Re-run UMAP over all user image embeddings and write map_x/map_y to DB."""
    from uuid import UUID as _UUID
    from ..db import get_conn

    async with get_conn() as conn:
        rows = await conn.fetch(
            "SELECT id, pinecone_id FROM brain_images WHERE user_id = $1 AND pinecone_id IS NOT NULL",
            _UUID(user_id),
        )

    if len(rows) < 2:
        if len(rows) == 1:
            async with get_conn() as conn:
                await conn.execute(
                    "UPDATE brain_images SET map_x = 500.0, map_y = 500.0 WHERE id = $1",
                    rows[0]["id"],
                )
        return

    index = await asyncio.to_thread(_get_index_sync)
    if index is None:
        return

    pinecone_ids = [r["pinecone_id"] for r in rows]
    try:
        fetch_result = await asyncio.to_thread(
            index.fetch, ids=pinecone_ids, namespace=NAMESPACE_IMAGES,
        )
    except Exception:
        logger.exception("Pinecone fetch failed during UMAP recompute for user %s", user_id)
        return

    embeddings = []
    valid_rows = []
    for row in rows:
        vec = fetch_result.vectors.get(row["pinecone_id"])
        if vec:
            embeddings.append(vec.values)
            valid_rows.append(row)

    if len(embeddings) < 2:
        return

    import numpy as np
    from umap import UMAP

    arr = np.array(embeddings, dtype=np.float32)
    n_neighbors = min(15, len(embeddings) - 1)
    reducer = UMAP(n_components=2, n_neighbors=n_neighbors, random_state=42, verbose=False)
    try:
        coords = reducer.fit_transform(arr)
    except Exception:
        logger.exception("UMAP fit_transform failed for user %s", user_id)
        return

    x_min, x_max = float(coords[:, 0].min()), float(coords[:, 0].max())
    y_min, y_max = float(coords[:, 1].min()), float(coords[:, 1].max())
    x_range = max(x_max - x_min, 1e-6)
    y_range = max(y_max - y_min, 1e-6)

    async with get_conn() as conn:
        for i, row in enumerate(valid_rows):
            mx = float((coords[i, 0] - x_min) / x_range * 1000)
            my = float((coords[i, 1] - y_min) / y_range * 1000)
            await conn.execute(
                "UPDATE brain_images SET map_x = $1, map_y = $2 WHERE id = $3",
                mx, my, row["id"],
            )
    logger.info("UMAP recomputed for user %s over %d images", user_id, len(valid_rows))
```

- [ ] **Step 3: Verify imports are intact**

```bash
python -c "from server.app.brain.service import extract_vibe_dimensions, recompute_umap_for_user; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add server/app/brain/service.py
git commit -m "Add vibe dimension extraction and UMAP projection to brain service"
```

---

## Task 5: Update upload endpoint + add /map and /sequence/compose

**Files:**
- Modify: `server/app/brain/router.py`

- [ ] **Step 1: Add imports at the top of router.py**

After the existing imports, add:

```python
import asyncio
import json as _json
```

(Note: `asyncio` is already imported in the delete handler as a local import — move it to the top level.)

- [ ] **Step 2: Update the upload handler to call vibe extraction and schedule UMAP**

Replace the upload handler body from the `# 1. Describe with GPT-4o vision` comment through the `return UploadResponse(...)` with:

```python
    # 1. Describe with GPT-4o vision
    description = await describe_image(image_bytes, mime_type)

    # 2. Extract vibe dimensions from description
    vibe_dims = await extract_vibe_dimensions(description) if description else None

    # 3. Store image as base64 data URL
    import base64
    blob_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"

    # 4. Embed description and upsert to Pinecone
    embedded = False
    if description:
        embedded = await embed_and_upsert_image(
            pinecone_id=pinecone_id,
            user_id=str(user_id),
            description=description,
            blob_url=f"/api/brain/image/{pinecone_id}",
            filename=file.filename,
        )

    # 5. Store in DB with vibe dimensions
    async with get_tx() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO brain_images (user_id, blob_url, filename, description, pinecone_id, vibe_dimensions)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, blob_url, filename, description, width, height, created_at
            """,
            user_id, blob_url, file.filename, description, pinecone_id,
            _json.dumps(vibe_dims) if vibe_dims else None,
        )

    # 6. Trigger UMAP recompute in background (non-blocking)
    asyncio.create_task(recompute_umap_for_user(str(user_id)))

    return UploadResponse(
        image=ImageRecord(**dict(row)),
        embedded=embedded,
    )
```

- [ ] **Step 3: Add the /map endpoint**

Add after the existing `list_images` endpoint:

```python
@router.get("/map", response_model=list[MapImage])
async def get_map(user_id: UUID = Depends(get_current_user_id)):
    """Return all user images with UMAP coordinates and vibe dimensions."""
    async with get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT id, blob_url, filename, description, vibe_dimensions, map_x, map_y
            FROM brain_images
            WHERE user_id = $1
            ORDER BY created_at DESC
            """,
            user_id,
        )
    result = []
    for r in rows:
        vd = r["vibe_dimensions"]
        result.append(MapImage(
            id=str(r["id"]),
            blob_url=r["blob_url"],
            filename=r["filename"],
            description=r["description"],
            vibe_dimensions=VibeDimensions(**vd) if vd else None,
            map_x=r["map_x"],
            map_y=r["map_y"],
        ))
    return result
```

- [ ] **Step 4: Add the /sequence/compose endpoint**

Add after the `/map` endpoint:

```python
@router.post("/sequence/compose", response_model=ComposeResponse)
async def compose_sequence(
    req: ComposeRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Given an ordered list of image IDs, return transition descriptors + vibe curve."""
    if len(req.image_ids) < 2:
        return ComposeResponse(transitions=[], vibe_curve={})

    ids = [UUID(i) for i in req.image_ids]
    async with get_conn() as conn:
        rows = await conn.fetch(
            """
            SELECT id, pinecone_id, vibe_dimensions
            FROM brain_images
            WHERE id = ANY($1::uuid[]) AND user_id = $2
            """,
            ids, user_id,
        )

    row_map = {str(r["id"]): r for r in rows}
    ordered = [row_map[i] for i in req.image_ids if i in row_map]

    # Build vibe curve — one value per image per dimension
    dim_keys = ["energy", "warmth", "density", "intimacy", "motion"]
    vibe_curve: dict[str, list[float]] = {k: [] for k in dim_keys}
    for row in ordered:
        dims = row["vibe_dimensions"] or {}
        for k in dim_keys:
            vibe_curve[k].append(float(dims.get(k, 0.5)))

    # Fetch vectors from Pinecone to compute pairwise cosine similarity
    index = await asyncio.to_thread(_get_index_sync)
    all_pinecone_ids = [r["pinecone_id"] for r in ordered if r["pinecone_id"]]
    vector_map: dict[str, list[float]] = {}
    if index and all_pinecone_ids:
        try:
            import numpy as np
            fetch = await asyncio.to_thread(
                index.fetch, ids=all_pinecone_ids, namespace=NAMESPACE_IMAGES,
            )
            vector_map = {pid: fetch.vectors[pid].values for pid in all_pinecone_ids if pid in fetch.vectors}
        except Exception:
            logger.exception("Pinecone fetch failed during compose for user %s", user_id)

    import numpy as np

    transitions = []
    for i in range(len(ordered) - 1):
        a, b = ordered[i], ordered[i + 1]
        dims_a = a["vibe_dimensions"] or {}
        dims_b = b["vibe_dimensions"] or {}

        # Cosine similarity from stored vectors
        similarity = 0.5
        va = vector_map.get(a["pinecone_id"] or "")
        vb = vector_map.get(b["pinecone_id"] or "")
        if va and vb:
            arr_a = np.array(va, dtype=np.float32)
            arr_b = np.array(vb, dtype=np.float32)
            norm_a = np.linalg.norm(arr_a)
            norm_b = np.linalg.norm(arr_b)
            if norm_a > 0 and norm_b > 0:
                similarity = float(np.dot(arr_a, arr_b) / (norm_a * norm_b))

        # Color shift from warmth delta
        warmth_delta = float(dims_b.get("warmth", 0.5)) - float(dims_a.get("warmth", 0.5))
        if warmth_delta < -0.2:
            color_shift = "warm_to_cool"
        elif warmth_delta > 0.2:
            color_shift = "cool_to_warm"
        else:
            color_shift = "neutral"

        # Mood shift from energy delta magnitude
        mood_shift = abs(float(dims_b.get("energy", 0.5)) - float(dims_a.get("energy", 0.5)))

        # Subject continuity: high similarity + low intimacy delta
        intimacy_delta = abs(float(dims_b.get("intimacy", 0.5)) - float(dims_a.get("intimacy", 0.5)))
        subject_continuity = similarity >= 0.65 and intimacy_delta < 0.3

        # Transition type matrix
        if similarity >= 0.7 and mood_shift < 0.4:
            t_type, duration = "dissolve", 0.8
        elif similarity >= 0.7 and mood_shift >= 0.4:
            t_type, duration = "flash_cut", 0.3
        elif similarity < 0.7 and mood_shift < 0.4:
            t_type, duration = "slow_zoom", 1.5
        else:
            t_type, duration = "hard_cut", 0.2

        transitions.append(TransitionDescriptor(
            from_id=str(a["id"]),
            to_id=str(b["id"]),
            similarity=round(similarity, 3),
            color_shift=color_shift,
            mood_shift=round(mood_shift, 3),
            subject_continuity=subject_continuity,
            transition_type=t_type,
            duration=duration,
        ))

    return ComposeResponse(transitions=transitions, vibe_curve=vibe_curve)
```

- [ ] **Step 5: Add missing imports to router.py**

At the top of router.py, ensure these imports are present:

```python
import asyncio
import json as _json
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from .models import (
    ComposeRequest, ComposeResponse, ImageRecord, MapImage,
    TraverseBranch, TraverseResponse, TransitionDescriptor,
    UploadResponse, VibeDimensions,
)
from .service import (
    describe_image, embed_and_upsert_image, extract_vibe_dimensions,
    find_similar_images, recompute_umap_for_user, NAMESPACE_IMAGES,
)
from ..auth.deps import get_current_user_id
from ..db import get_conn, get_tx
```

- [ ] **Step 6: Smoke test the endpoints**

```bash
source server/venv/bin/activate
uvicorn server.app.main:app --reload --port 8000 &
sleep 3
# Health check
curl -s http://localhost:8000/health | python -m json.tool
# The /map and /sequence/compose routes should appear in the OpenAPI docs
curl -s http://localhost:8000/openapi.json | python -c "import sys,json; doc=json.load(sys.stdin); print([p for p in doc['paths'] if 'brain' in p])"
```

Expected: `['/api/brain/upload', '/api/brain/library', '/api/brain/traverse', '/api/brain/map', '/api/brain/sequence/compose', '/api/brain/{image_id}']`

- [ ] **Step 7: Commit**

```bash
git add server/app/brain/router.py server/app/brain/service.py server/app/brain/models.py
git commit -m "Add vibe extraction, UMAP projection, /map and /sequence/compose endpoints"
```

---

## Task 6: Push and verify Render deploy

- [ ] **Step 1: Push to main**

```bash
git push origin main
```

- [ ] **Step 2: Run migration on Render**

In Render dashboard, trigger a manual run of:
```
python -m server.app.migrate
```
Or add to the build command temporarily. Verify `013_brain_vibe_dimensions.sql` is applied in logs.

- [ ] **Step 3: Verify the /map endpoint returns 200 on prod**

```bash
# Replace <token> with a valid JWT from localStorage
curl -s -H "Authorization: Bearer <token>" https://channelzero-api.onrender.com/api/brain/map | python -m json.tool
```

Expected: `[]` or a JSON array of image objects. No 500 errors.
