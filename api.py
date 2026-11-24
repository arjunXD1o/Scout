"""
FastAPI Server & Web Portal for Scout Influencer Intelligence
Provides:
- GET /api/influencer/{username} -> JSON with full details
- GET / -> PulseTrack-style interactive dashboard portal
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import re
import os
import socket
import webbrowser
import threading

from app.scrapers.instagram import scrape_profile_no_login
from app.scrapers.enrichment import enrich_lead
from app.analytics import calculate_influencer_valuation

app = FastAPI(
    title="Scout Influencer Intelligence API",
    description="API for influencer scraping, contact enrichment, and demographic valuation"
)

# Enable CORS for external portals (React, Next.js, Vue, PHP, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PORTAL_DIR = os.path.dirname(os.path.abspath(__file__))


@app.get("/api/influencer/{username}")
def get_influencer_details(username: str):
    """Fetch complete influencer intelligence, contact info, valuation, and demographics."""
    clean_username = username.strip().lstrip('@')
    if not re.match(r'^[a-zA-Z0-9._]{1,30}$', clean_username):
        raise HTTPException(status_code=400, detail="Invalid username format")

    raw_profile = scrape_profile_no_login(clean_username)
    if not raw_profile:
        raise HTTPException(status_code=404, detail=f"Instagram profile @{clean_username} not found or inaccessible")

    # Contact enrichment (email, phone, agency)
    enriched = enrich_lead(raw_profile)

    # Demographics & valuation engine
    followers = enriched.get('follower_count', 0)
    valuation = calculate_influencer_valuation(
        clean_username,
        followers,
        platform="instagram",
        is_verified=enriched.get('is_verified', False),
        bio=enriched.get('bio', '')
    )
    enriched.update(valuation)

    return {
        "status": "success",
        "data": enriched
    }


@app.get("/", response_class=HTMLResponse)
def portal_dashboard():
    """Serve the PulseTrack-style dashboard portal."""
    portal_path = os.path.join(PORTAL_DIR, "portal.html")
    with open(portal_path, "r", encoding="utf-8") as f:
        return f.read()


def find_free_port(start_port=8080):
    """Find the first available port starting from start_port."""
    for p in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', p)) != 0:
                return p
    return start_port


if __name__ == '__main__':
    port = find_free_port(8080)
    url = f"http://127.0.0.1:{port}"
    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║   SCOUT — Influencer Intelligence Portal        ║")
    print(f"  ║   Dashboard:  {url:<33} ║")
    print(f"  ║   API Docs:   {url + '/docs':<33} ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print()

    def _open_browser():
        import time
        time.sleep(1.0)
        webbrowser.open(url)

    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=port)
