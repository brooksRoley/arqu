"""
GitHub OAuth + developer profile ingestion.

Flow:
  1. GET /github/connect  -> return auth URL for frontend redirect
  2. GET /github/callback -> GitHub redirects back with ?code=&state=
                           -> exchange code for tokens
                           -> fetch user profile + repos + starred repos
                           -> encrypt tokens, store in oauth_tokens
                           -> store GitHub profile in vibe_vectors.github_data
                           -> redirect to frontend
"""

from __future__ import annotations

import json
import time
from collections import Counter
from urllib.parse import urlencode
from uuid import UUID

import secrets

from ..oracle.trigger import maybe_trigger_synthesis

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from ..auth.deps import get_current_user_id
from ..auth.service import decode_access_token
from ..config import get_settings
from ..db import get_conn
from ..llm.encryption import encrypt_api_key

router = APIRouter()

_GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_API_BASE = "https://api.github.com"
_SCOPES = "read:user repo"


# -- State helpers -------------------------------------------------------------

def _make_state(user_id: str) -> str:
    nonce = secrets.token_urlsafe(16)
    payload = {"sub": user_id, "nonce": nonce, "exp": int(time.time()) + 600}
    return jwt.encode(payload, get_settings().jwt_secret, algorithm="HS256")


async def _verify_state(state: str) -> str:
    """Decode, verify, and consume the state JWT (one-time use)."""
    try:
        payload = jwt.decode(state, get_settings().jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state") from exc

    nonce = payload.get("nonce")
    if not nonce:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state — missing nonce")

    # Consume the nonce — INSERT fails on replay due to UNIQUE constraint
    async with get_conn() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO _oauth_nonces (nonce, consumed_at)
                VALUES ($1, now())
                """,
                nonce,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth state already consumed — possible replay attack",
            )

    return payload["sub"]


# -- Routes --------------------------------------------------------------------

@router.get("/connect")
async def github_connect(token: str = Query(..., description="Frontend JWT")):
    """
    Return the GitHub authorization URL for the authenticated user.
    Accepts the JWT as a query param because browser redirects can't set headers.
    """
    settings = get_settings()
    if not settings.github_client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GitHub not configured")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": _SCOPES,
        "state": _make_state(payload["sub"]),
    }
    return {"auth_url": f"{_GITHUB_AUTH_URL}?{urlencode(params)}"}


@router.get("/callback")
async def github_callback(code: str, state: str):
    """
    GitHub redirects here (via frontend) after user authorizes.
    Exchanges code for tokens, fetches user profile + repos + stars, stores everything.
    """
    user_id = await _verify_state(state)
    settings = get_settings()

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Exchange authorization code for access token
        token_resp = await client.post(
            _GITHUB_TOKEN_URL,
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub token exchange failed: {token_resp.text}",
            )
        tokens = token_resp.json()

        access_token = tokens.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub token exchange failed: {tokens.get('error_description', 'no access_token')}",
            )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }

        # 2. Fetch user profile
        user_resp = await client.get(f"{_GITHUB_API_BASE}/user", headers=headers)
        user_data = {}
        if user_resp.status_code == 200:
            user_data = user_resp.json()

        # 3. Fetch repos (up to 100, sorted by recent push)
        repos_resp = await client.get(
            f"{_GITHUB_API_BASE}/user/repos",
            headers=headers,
            params={"per_page": 100, "sort": "pushed", "direction": "desc"},
        )
        repos_data = []
        if repos_resp.status_code == 200:
            repos_data = repos_resp.json()

        # 4. Fetch starred repos (up to 100)
        starred_resp = await client.get(
            f"{_GITHUB_API_BASE}/user/starred",
            headers=headers,
            params={"per_page": 100},
        )
        starred_data = []
        if starred_resp.status_code == 200:
            starred_data = starred_resp.json()

    # 5. Distill the developer profile
    github_profile = _distill_profile(user_data, repos_data, starred_data)

    # 6. Encrypt and store tokens (GitHub tokens don't expire by default)
    enc_access, access_nonce = encrypt_api_key(access_token)

    async with get_conn() as conn:
        # Store github_id on user
        github_id = str(user_data.get("id", ""))
        if github_id:
            await conn.execute(
                "UPDATE users SET github_id = $1, updated_at = now() WHERE id = $2",
                github_id, UUID(user_id),
            )

        await conn.execute(
            """
            INSERT INTO oauth_tokens
                (user_id, provider, encrypted_access_token, access_nonce,
                 encrypted_refresh_token, refresh_nonce, expires_at, scope)
            VALUES ($1, 'github', $2, $3, $4, $5, $6, $7)
            ON CONFLICT (user_id, provider) DO UPDATE SET
                encrypted_access_token  = EXCLUDED.encrypted_access_token,
                access_nonce            = EXCLUDED.access_nonce,
                encrypted_refresh_token = EXCLUDED.encrypted_refresh_token,
                refresh_nonce           = EXCLUDED.refresh_nonce,
                expires_at              = EXCLUDED.expires_at,
                scope                   = EXCLUDED.scope,
                updated_at              = now()
            """,
            UUID(user_id),
            enc_access, access_nonce,
            None, None,
            None, _SCOPES,
        )

        # 7. Store GitHub profile on vibe_vectors row (if intake already done)
        await conn.execute(
            """
            UPDATE vibe_vectors
            SET github_data = $2, updated_at = now()
            WHERE user_id = $1
            """,
            UUID(user_id), json.dumps(github_profile),
        )

    # Auto-trigger Oracle synthesis if enough providers connected
    await maybe_trigger_synthesis(UUID(user_id))

    # 8. Return success — frontend handles navigation
    return JSONResponse({"status": "connected", "username": github_profile.get("username", "")})


# ── Psychoanalysis ────────────────────────────────────────────────────────────

@router.get("/analyze")
async def github_analyze(user_id: UUID = Depends(get_current_user_id)):
    """Generate an LLM psychoanalysis of the user's GitHub developer profile."""
    settings = get_settings()

    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT github_data FROM vibe_vectors WHERE user_id = $1",
            user_id,
        )

    if not row or not row["github_data"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No GitHub data found")

    data = row["github_data"]
    profile = json.loads(data) if isinstance(data, str) else data

    if not settings.openai_embed_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM not configured")

    narrative = await _analyze_github_profile(settings.openai_embed_key, profile)
    return {"narrative": narrative}


async def _analyze_github_profile(api_key: str, profile: dict) -> str:
    username = profile.get("username", "")
    bio = profile.get("bio", "")
    company = profile.get("company", "")
    public_repos = profile.get("public_repos", 0)
    followers = profile.get("followers", 0)
    following = profile.get("following", 0)
    top_langs = ", ".join(profile.get("top_languages", []))
    stars_given = profile.get("stars_given", 0)
    repos_owned = profile.get("repos_owned", 0)
    repos_forked = profile.get("repos_forked", 0)
    owned_to_forked = profile.get("owned_to_forked_ratio", 0)
    age = profile.get("account_age_years")
    topics = ", ".join(profile.get("topics", [])[:20])
    descriptions = profile.get("repo_descriptions", [])
    desc_text = "\n".join(f'- "{d}"' for d in descriptions[:10]) if descriptions else "(unavailable)"

    prompt = f"""You are a perceptive behavioral psychologist analyzing a person's GitHub profile as a window into their builder identity and creative patterns.
Your task: write a sharp, warm, 2-3 paragraph psychoanalysis of this user's developer psychology and what their code reveals about their thought patterns.
Do not be clinical. Be insightful, specific, and draw connections between data points.

SIGNAL DATA:
- Username: {username}
- Bio: "{bio}"
- Company: "{company}"
- Public repos: {public_repos} | Followers: {followers} | Following: {following}
- Top languages: {top_langs}
- Stars given (curiosity signal): {stars_given}
- Repos owned: {repos_owned} | Repos forked: {repos_forked} | Owned/forked ratio: {owned_to_forked}
- Account age: {age} years
- Topics/interests: {topics}
- Repo descriptions:
{desc_text}

Write 2-3 paragraphs analyzing:
1. Builder identity — what language choices, repo descriptions, and topics reveal about how they think, what problems attract them, their aesthetic sensibility in code
2. Creative patterns — solo vs collaborative tendencies (owned vs forked ratio), curiosity breadth (stars given), and what their GitHub presence says about their relationship with making things
3. Social positioning in the developer world — followers, following, bio as identity performance, and what the gap between public repos and stars reveals about recognition needs

Be direct, specific, a little poetic. Avoid generic statements. Return only the narrative."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "max_tokens": 800,
        "messages": [{"role": "user", "content": prompt}],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="LLM call failed")
        return resp.json()["choices"][0]["message"]["content"]


# -- Profile endpoint ----------------------------------------------------------

@router.get("/profile")
async def get_github_profile(user_id: UUID = Depends(get_current_user_id)):
    """Return the stored GitHub profile for the current user, or null."""
    async with get_conn() as conn:
        row = await conn.fetchrow(
            "SELECT github_data FROM vibe_vectors WHERE user_id = $1",
            user_id,
        )
    if not row or not row["github_data"]:
        return None
    data = row["github_data"]
    return json.loads(data) if isinstance(data, str) else data


# -- Profile distillation ------------------------------------------------------

def _distill_profile(user: dict, repos: list[dict], starred: list[dict]) -> dict:
    """Reduce raw GitHub data to the developer essentials."""
    # Language aggregation
    lang_counts: Counter[str] = Counter()
    forked_count = 0
    owned_count = 0
    topics: list[str] = []
    descriptions: list[str] = []

    for r in repos:
        lang = r.get("language")
        if lang:
            lang_counts[lang] += 1
        if r.get("fork"):
            forked_count += 1
        else:
            owned_count += 1
        for t in r.get("topics", []):
            topics.append(t)
        desc = r.get("description")
        if desc:
            descriptions.append(desc)

    top_languages = [lang for lang, _ in lang_counts.most_common(10)]

    # Account age
    created_at = user.get("created_at", "")
    account_age_years = None
    if created_at:
        from datetime import datetime, timezone
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            delta = datetime.now(tz=timezone.utc) - created
            account_age_years = round(delta.days / 365.25, 1)
        except (ValueError, TypeError):
            pass

    return {
        "username": user.get("login", ""),
        "bio": user.get("bio", ""),
        "company": user.get("company", ""),
        "location": user.get("location", ""),
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "top_languages": top_languages,
        "stars_given": len(starred),
        "repos_owned": owned_count,
        "repos_forked": forked_count,
        "owned_to_forked_ratio": round(owned_count / max(forked_count, 1), 2),
        "account_age_years": account_age_years,
        "topics": list(set(topics))[:30],
        "repo_descriptions": descriptions[:20],
    }
