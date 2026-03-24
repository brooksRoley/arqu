from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os
import base64

# Assuming you have these functions defined elsewhere in your service.py
from .service import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

class OAuthCallbackRequest(BaseModel):
    code: str
    code_verifier: str | None = None  # Required for X (PKCE)

# -----------------------------------------------------------------------------
# GOOGLE OAUTH
# -----------------------------------------------------------------------------
@router.post("/google")
async def google_oauth_callback(req: OAuthCallbackRequest):
    token_url = "https://oauth2.googleapis.com/token"
    
    data = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "code": req.code,
        "grant_type": "authorization_code",
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
    }

    async with httpx.AsyncClient() as client:
        # 1. Exchange code for tokens
        token_res = await client.post(token_url, data=data)
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Google token exchange failed")
        
        token_data = token_res.json()
        access_token = token_data.get("access_token")

        # 2. Fetch User Profile
        user_info_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info = user_info_res.json()

    # 3. Upsert User & Generate Internal JWT
    user_data = {
        "google_id": user_info.get("id"),
        "email": user_info.get("email"),
        "display_name": user_info.get("name"),
        "avatar_url": user_info.get("picture")
    }
    
    user = await upsert_oauth_user(provider="google", profile=user_data)
    
    jwt_token = create_access_token(data={"sub": str(user["id"])})
    return {"access_token": jwt_token, "token_type": "bearer", "user": user}


# -----------------------------------------------------------------------------
# X (TWITTER) OAUTH 2.0 (PKCE)
# -----------------------------------------------------------------------------
@router.post("/x")
async def x_oauth_callback(req: OAuthCallbackRequest):
    if not req.code_verifier:
        raise HTTPException(status_code=400, detail="code_verifier is required for X OAuth")

    token_url = "https://api.twitter.com/2/oauth2/token"
    client_id = os.getenv("X_CLIENT_ID")
    client_secret = os.getenv("X_CLIENT_SECRET")
    
    # X requires Basic Auth for the token endpoint
    auth_str = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_str}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "code": req.code,
        "grant_type": "authorization_code",
        "client_id": client_id,
        "redirect_uri": os.getenv("X_REDIRECT_URI"),
        "code_verifier": req.code_verifier,
    }

    async with httpx.AsyncClient() as client:
        # 1. Exchange code for tokens
        token_res = await client.post(token_url, headers=headers, data=data)
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="X token exchange failed")
        
        access_token = token_res.json().get("access_token")

        # 2. Fetch User Profile
        # Note: Getting the email requires elevated permissions on the X Developer Portal
        user_info_res = await client.get(
            "https://api.twitter.com/2/users/me?user.fields=profile_image_url",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        x_data = user_info_res.json().get("data", {})

    # 3. Upsert User & Generate Internal JWT
    user_data = {
        "x_id": x_data.get("id"),
        "display_name": x_data.get("name"),
        "avatar_url": x_data.get("profile_image_url"),
        "email": None # Requires specific X app config to retrieve
    }

    user = await upsert_oauth_user(provider="x", profile=user_data)
    
    jwt_token = create_access_token(data={"sub": str(user["id"])})
    return {"access_token": jwt_token, "token_type": "bearer", "user": user}