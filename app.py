import os
import json
import datetime
import aiohttp
from aiohttp import web

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
OAUTH2_REDIRECT_URI = os.getenv("OAUTH2_REDIRECT_URI")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


async def oauth_callback(request: web.Request) -> web.Response:
    code = request.rel_url.query.get("code")
    state = request.rel_url.query.get("state")

    if not code or not state:
        return web.Response(text="Missing code or state.", status=400)

    parts = state.split(":")
    if len(parts) != 2:
        return web.Response(text="Invalid state.", status=400)

    guild_id, user_id = parts

    # Exchange code for access token
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": OAUTH2_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                return web.Response(text=f"Token exchange failed: {text}", status=400)
            token_data = await resp.json()

    access_token = token_data.get("access_token")
    if not access_token:
        return web.Response(text="No access token returned.", status=400)

    # Save to Supabase
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{SUPABASE_URL}/rest/v1/verified_members",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates",
            },
            json={
                "guild_id": guild_id,
                "user_id": user_id,
                "access_token": access_token,
                "verified_at": datetime.datetime.utcnow().isoformat(),
            },
        ) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                return web.Response(text=f"Database save failed: {text}", status=500)

    html = """
    <html>
    <body style="font-family:sans-serif;text-align:center;padding:60px;background:#2b2d31;color:#fff;">
      <h1>&#10003; Verified!</h1>
      <p>You can now close this tab and return to Discord.</p>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")


async def index(request):
    return web.Response(text="OAuth2 callback server is running.")


app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/oauth/callback", oauth_callback)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    web.run_app(app, host="0.0.0.0", port=port)
