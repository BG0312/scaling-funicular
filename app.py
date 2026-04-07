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


async def index(request: web.Request) -> web.Response:
    """Custom verification landing page with browser fingerprinting"""
    guild_id = request.rel_url.query.get("guild_id", "")
    user_id = request.rel_url.query.get("user_id", "")

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": OAUTH2_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds.join",
        "state": f"{guild_id}:{user_id}",
    }
    from urllib.parse import urlencode
    oauth_url = f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Verify — ServiceBot</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #1a1b1e;
    color: #fff;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .card {{
    background: #2b2d31;
    border: 1px solid #3f4147;
    border-radius: 16px;
    padding: 40px;
    max-width: 420px;
    width: 90%;
    text-align: center;
  }}
  .logo {{ font-size: 48px; margin-bottom: 16px; }}
  h1 {{ font-size: 24px; font-weight: 700; margin-bottom: 8px; }}
  p {{ color: #b5bac1; font-size: 15px; margin-bottom: 28px; line-height: 1.6; }}
  .btn {{
    display: inline-block;
    background: #5865f2;
    color: #fff;
    font-size: 16px;
    font-weight: 600;
    padding: 14px 32px;
    border-radius: 10px;
    text-decoration: none;
    border: none;
    cursor: pointer;
    transition: background 0.2s;
    width: 100%;
  }}
  .btn:hover {{ background: #4752c4; }}
  .btn:disabled {{ background: #3f4147; cursor: not-allowed; }}
  .status {{ margin-top: 16px; font-size: 13px; color: #b5bac1; min-height: 20px; }}
  .warning {{ color: #faa61a; font-size: 13px; margin-top: 12px; }}
</style>
</head>
<body>
<div class="card">
  <div class="logo">🛡️</div>
  <h1>Verify Your Account</h1>
  <p>Click the button below to securely verify your Discord account and gain access to the server.</p>
  <button class="btn" id="verifyBtn" onclick="startVerify()">Verify with Discord</button>
  <div class="status" id="status"></div>
  <div class="warning" id="warning"></div>
</div>

<script>
async function getFingerprint() {{
  const components = [];

  // Basic browser info
  components.push(navigator.userAgent);
  components.push(navigator.language);
  components.push(screen.width + 'x' + screen.height);
  components.push(screen.colorDepth);
  components.push(new Date().getTimezoneOffset());
  components.push(navigator.hardwareConcurrency || 0);
  components.push(navigator.deviceMemory || 0);
  components.push(navigator.platform || '');

  // Canvas fingerprint
  try {{
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = '#069';
    ctx.fillText('ServiceBot fingerprint 🛡️', 2, 15);
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('ServiceBot fingerprint 🛡️', 4, 17);
    components.push(canvas.toDataURL());
  }} catch(e) {{ components.push('canvas-error'); }}

  // WebGL fingerprint
  try {{
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (gl) {{
      components.push(gl.getParameter(gl.VENDOR));
      components.push(gl.getParameter(gl.RENDERER));
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      if (ext) {{
        components.push(gl.getParameter(ext.UNMASKED_VENDOR_WEBGL));
        components.push(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL));
      }}
    }}
  }} catch(e) {{ components.push('webgl-error'); }}

  // Audio fingerprint
  try {{
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = ctx.createOscillator();
    const analyser = ctx.createAnalyser();
    const gain = ctx.createGain();
    gain.gain.value = 0;
    oscillator.connect(analyser);
    analyser.connect(gain);
    gain.connect(ctx.destination);
    oscillator.start(0);
    const data = new Float32Array(analyser.frequencyBinCount);
    analyser.getFloatFrequencyData(data);
    oscillator.stop();
    ctx.close();
    components.push(data.slice(0, 10).join(','));
  }} catch(e) {{ components.push('audio-error'); }}

  // Installed plugins
  try {{
    const plugins = Array.from(navigator.plugins).map(p => p.name).join(',');
    components.push(plugins);
  }} catch(e) {{ components.push(''); }}

  // Hash everything into a fingerprint
  const raw = components.join('|||');
  const msgBuffer = new TextEncoder().encode(raw);
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}}

async function startVerify() {{
  const btn = document.getElementById('verifyBtn');
  const status = document.getElementById('status');
  btn.disabled = true;
  status.textContent = 'Collecting verification data...';

  try {{
    const fingerprint = await getFingerprint();

    // Send fingerprint to server before redirecting
    const resp = await fetch('/store-fingerprint', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        guild_id: '{guild_id}',
        user_id: '{user_id}',
        fingerprint: fingerprint,
        screen: screen.width + 'x' + screen.height,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        platform: navigator.platform || 'unknown',
      }})
    }});

    if (resp.ok) {{
      status.textContent = 'Redirecting to Discord...';
      window.location.href = '{oauth_url}';
    }} else {{
      status.textContent = 'Error storing fingerprint, redirecting anyway...';
      setTimeout(() => {{ window.location.href = '{oauth_url}'; }}, 1500);
    }}
  }} catch(e) {{
    status.textContent = 'Redirecting to Discord...';
    window.location.href = '{oauth_url}';
  }}
}}
</script>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")


async def store_fingerprint(request: web.Request) -> web.Response:
    """Store fingerprint before OAuth2 redirect"""
    try:
        data = await request.json()
        guild_id = data.get("guild_id")
        user_id = data.get("user_id")
        fingerprint = data.get("fingerprint")
        screen = data.get("screen", "unknown")
        timezone = data.get("timezone", "unknown")
        platform = data.get("platform", "unknown")
        ip = request.headers.get("X-Forwarded-For", "unknown").split(",")[0].strip()

        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        }
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{SUPABASE_URL}/rest/v1/pending_fingerprints",
                headers=headers,
                json={
                    "guild_id": guild_id,
                    "user_id": user_id,
                    "fingerprint": fingerprint,
                    "ip": ip,
                    "screen": screen,
                    "timezone": timezone,
                    "platform": platform,
                    "created_at": datetime.datetime.utcnow().isoformat(),
                }
            )
        return web.Response(text="ok")
    except Exception as e:
        print(f"Fingerprint store error: {e}")
        return web.Response(text="error", status=500)


async def oauth_callback(request: web.Request) -> web.Response:
    code = request.rel_url.query.get("code")
    state = request.rel_url.query.get("state")
    ip = request.headers.get("X-Forwarded-For", "unknown").split(",")[0].strip()

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

    # Get Discord user info
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://discord.com/api/v10/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        ) as resp:
            user_data = await resp.json() if resp.status == 200 else {}

    username = user_data.get("username", "Unknown")
    account_created_at = None
    account_age_days = None
    if user_id:
        # Calculate account age from Discord snowflake ID
        snowflake = int(user_id)
        timestamp_ms = (snowflake >> 22) + 1420070400000
        created_dt = datetime.datetime.utcfromtimestamp(timestamp_ms / 1000)
        account_created_at = created_dt.isoformat()
        account_age_days = (datetime.datetime.utcnow() - created_dt).days

    # Get stored fingerprint
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }
    fingerprint = None
    screen = "unknown"
    timezone = "unknown"
    platform = "unknown"

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{SUPABASE_URL}/rest/v1/pending_fingerprints?guild_id=eq.{guild_id}&user_id=eq.{user_id}&order=created_at.desc&limit=1",
            headers=headers
        ) as resp:
            if resp.status == 200:
                rows = await resp.json()
                if rows:
                    fingerprint = rows[0].get("fingerprint")
                    screen = rows[0].get("screen", "unknown")
                    timezone = rows[0].get("timezone", "unknown")
                    platform = rows[0].get("platform", "unknown")
                    ip = rows[0].get("ip", ip)

    # Check for existing fingerprint match (alt detection)
    is_alt = False
    alt_of_user_id = None
    if fingerprint:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{SUPABASE_URL}/rest/v1/verified_members?fingerprint=eq.{fingerprint}&guild_id=eq.{guild_id}&user_id=neq.{user_id}",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    matches = await resp.json()
                    if matches:
                        is_alt = True
                        alt_of_user_id = matches[0].get("user_id")

    # Save verified member
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"{SUPABASE_URL}/rest/v1/verified_members",
            headers=headers,
            json={
                "guild_id": guild_id,
                "user_id": user_id,
                "access_token": access_token,
                "username": username,
                "fingerprint": fingerprint,
                "ip": ip,
                "screen": screen,
                "timezone": timezone,
                "platform": platform,
                "account_created_at": account_created_at,
                "account_age_days": account_age_days,
                "is_alt": is_alt,
                "alt_of": alt_of_user_id,
                "verified_at": datetime.datetime.utcnow().isoformat(),
            }
        )

    # Notify bot via Supabase verification_events table
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"{SUPABASE_URL}/rest/v1/verification_events",
            headers=headers,
            json={
                "guild_id": guild_id,
                "user_id": user_id,
                "username": username,
                "ip": ip,
                "screen": screen,
                "timezone": timezone,
                "platform": platform,
                "account_age_days": account_age_days,
                "is_alt": is_alt,
                "alt_of": alt_of_user_id,
                "fingerprint": fingerprint,
                "processed": False,
                "created_at": datetime.datetime.utcnow().isoformat(),
            }
        )

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Verified — ServiceBot</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #1a1b1e;
    color: #fff;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .card {
    background: #2b2d31;
    border: 1px solid #3f4147;
    border-radius: 16px;
    padding: 40px;
    max-width: 420px;
    width: 90%;
    text-align: center;
  }
  .check { font-size: 56px; margin-bottom: 16px; }
  h1 { font-size: 24px; font-weight: 700; margin-bottom: 8px; color: #57f287; }
  p { color: #b5bac1; font-size: 15px; line-height: 1.6; }
</style>
</head>
<body>
<div class="card">
  <div class="check">✅</div>
  <h1>Verified!</h1>
  <p>You can now close this tab and return to Discord.</p>
</div>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")


app = web.Application()
app.router.add_get("/", index)
app.router.add_post("/store-fingerprint", store_fingerprint)
app.router.add_get("/oauth/callback", oauth_callback)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    web.run_app(app, host="0.0.0.0", port=port)
