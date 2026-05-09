import asyncio
import httpx
from app.main import app
import secrets
import jwt
import time
from app.config import get_settings

async def main():
    settings = get_settings()
    payload = {"sub": "00000000-0000-0000-0000-000000000000", "nonce": secrets.token_urlsafe(16), "exp": int(time.time()) + 600}
    state = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/youtube/callback?code=testcode&state={state}")
        print("Status code:", response.status_code)
        print("Response:", response.text)

if __name__ == "__main__":
    asyncio.run(main())
