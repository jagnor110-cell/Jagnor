#!/usr/bin/env python3
"""
full_circle_company.py — Autonomous 6-Agent App Factory & Live 9:16 Video Publisher
====================================================================================
Fixes & Upgrades Applied for jagnor110-cell/Jagnor:
  1. Fixes truncated Whop URL ("https://whop.com" -> "https://api.whop.com/api/v1/checkout_configurations"
     and "/api/v1/products") so a real Whop product & checkout link are created.
  2. Auto-corrects PUBLIC_VIDEO_BASE_URL to "https://jagnor110-cell.github.io/Jagnor".
  3. Replaces the static 1-image screenshot with a REAL 14-second moving 9:16 video
     walkthrough recorded via Playwright (`record_video_dir`), showing a glowing touch
     cursor moving sliders, clicking buttons, and scrolling the live web app.
  4. Pushes the newly built app and MP4 to GitHub before calling Instagram so Instagram
     Reels always grabs the brand-new moving video immediately.
  5. Includes the Live Web App link and Direct Pro Zip link in the Gmail CEO report.
"""

import json
import os
import shutil
import smtplib
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from email.message import EmailMessage
from pathlib import Path

# =====================================================================
# 0. ENVIRONMENT CONFIGURATION & CREDENTIALS
# =====================================================================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL = "gemini-4-hydrogen"

WHOP_API_KEY = os.environ.get("WHOP_API_KEY", "").strip()
WHOP_COMPANY_ID = os.environ.get("WHOP_COMPANY_ID", "").strip()

YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID", "").strip()
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET", "").strip()
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN", "").strip()
YT_PRIVACY_STATUS = os.environ.get("YT_PRIVACY_STATUS", "public").strip() or "public"

IG_USER_ID = os.environ.get("IG_USER_ID", "").strip()
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()

# Auto-repair PUBLIC_VIDEO_BASE_URL if it was set to bare https://github.io
_raw_base = os.environ.get("PUBLIC_VIDEO_BASE_URL", "").strip().rstrip("/")
if not _raw_base or "jagnor110-cell.github.io/Jagnor" not in _raw_base:
    PUBLIC_VIDEO_BASE_URL = "https://jagnor110-cell.github.io/Jagnor"
else:
    PUBLIC_VIDEO_BASE_URL = _raw_base

RAW_GITHUB_BASE_URL = "https://raw.githubusercontent.com/jagnor110-cell/Jagnor/main/public"

GMAIL_USER = os.environ.get("COMPANY_GMAIL", "").strip()
GMAIL_APP_PASS = os.environ.get("GMAIL_APP_PASSWORD", "").strip()

PUBLIC_DIR = Path("public")
DIST_DIR = Path("dist")
RAW_VIDEO_DIR = DIST_DIR / "raw_video"
PUBLIC_DIR.mkdir(exist_ok=True)
DIST_DIR.mkdir(exist_ok=True)
RAW_VIDEO_DIR.mkdir(exist_ok=True)


# =====================================================================
# HELPER: CALL GEMINI AGENT WITH RETRY
# =====================================================================
def ask_agent(role_prompt: str, task_prompt: str) -> str:
    """Sends a structured role + task prompt to the Gemini API with auto-retry."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODEL}:generateContent?key={GEMINI_KEY}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"System Role: {role_prompt}\n\nTask:\n{task_prompt}"}
                ]
            }
        ]
    }
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][-1]["text"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                print(f"   -> Gemini server busy (HTTP {e.code}), retrying in 15s (attempt {attempt}/3)...")
                time.sleep(15)
            else:
                raise
    raise RuntimeError("Gemini API failed after 3 attempts.")


# =====================================================================
# STEP 1: RECORD LIVE MOVING 9:16 SCREEN VIDEO OF THE WEB APP
# =====================================================================
def record_live_9x16_app_demo(html_path: Path, title: str, subtitle: str) -> Path:
    """
    Records a real 14-second 1080x1920 (9:16) moving screen recording of the generated
    HTML5 web app using Playwright's `record_video_dir`, showing a glowing touch cursor
    moving sliders, clicking buttons, and scrolling through the live app.
    """
    from playwright.sync_api import sync_playwright

    for old_file in RAW_VIDEO_DIR.glob("*"):
        old_file.unlink(missing_ok=True)

    print("   -> Recording live moving 9:16 app walkthrough via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 540, "height": 960},
            device_scale_factor=2,
            record_video_dir=str(RAW_VIDEO_DIR),
            record_video_size={"width": 1080, "height": 1920},
        )
        page = context.new_page()
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Inject top banner and glowing touch dot
        page.evaluate(
            """({title}) => {
                const banner = document.createElement('div');
                banner.innerHTML = `
                  <div style="position:fixed;top:0;left:0;right:0;z-index:99999;
                              background:linear-gradient(90deg,#0284c7,#2563eb);
                              color:#fff;padding:12px 16px;text-align:center;
                              font-family:sans-serif;box-shadow:0 4px 20px rgba(0,0,0,0.4);">
                    <div style="font-size:11px;letter-spacing:1.5px;text-transform:uppercase;opacity:0.9;">
                      LIVE AI WEB APP DEMO
                    </div>
                    <div style="font-size:16px;font-weight:700;margin-top:2px;">${title}</div>
                  </div>
                `;
                document.body.prepend(banner);
                document.body.style.paddingTop = '68px';

                const dot = document.createElement('div');
                dot.id = 'ai-touch-dot';
                dot.style.cssText = `
                  position:fixed;width:36px;height:36px;border-radius:50%;
                  background:rgba(56,189,248,0.6);border:3px solid #fff;
                  box-shadow:0 0 20px #38bdf8;pointer-events:none;z-index:100000;
                  transition:all 0.45s ease;left:270px;top:420px;transform:translate(-50%,-50%);
                `;
                document.body.appendChild(dot);
            }""",
            {"title": title[:40]},
        )
        page.wait_for_timeout(1000)

        # Animate sliders, inputs, buttons, and scrolling so the product visibly works
        page.evaluate(
            """async () => {
                const sleep = ms => new Promise(r => setTimeout(r, ms));
                const dot = document.getElementById('ai-touch-dot');
                const moveDot = (el) => {
                    if (!el || !dot) return;
                    const rect = el.getBoundingClientRect();
                    dot.style.left = (rect.left + rect.width / 2) + 'px';
                    dot.style.top = (rect.top + rect.height / 2) + 'px';
                    dot.style.transform = 'translate(-50%,-50%) scale(0.75)';
                    setTimeout(() => { dot.style.transform = 'translate(-50%,-50%) scale(1.15)'; }, 220);
                };

                const ranges = Array.from(document.querySelectorAll('input[type="range"]'));
                for (const r of ranges.slice(0, 3)) {
                    r.scrollIntoView({behavior: 'smooth', block: 'center'});
                    moveDot(r);
                    await sleep(600);
                    const min = parseFloat(r.min || 0);
                    const max = parseFloat(r.max || 100);
                    for (const pct of [0.35, 0.8, 0.6]) {
                        r.value = min + (max - min) * pct;
                        r.dispatchEvent(new Event('input', {bubbles: true}));
                        r.dispatchEvent(new Event('change', {bubbles: true}));
                        await sleep(450);
                    }
                }

                const buttons = Array.from(document.querySelectorAll('button'));
                for (const btn of buttons.slice(0, 3)) {
                    btn.scrollIntoView({behavior: 'smooth', block: 'center'});
                    moveDot(btn);
                    await sleep(500);
                    btn.click();
                    await sleep(900);
                }

                window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
                await sleep(1400);
                window.scrollTo({top: 0, behavior: 'smooth'});
                await sleep(1200);
            }"""
        )

        # Show closing Call-to-Action overlay card
        page.evaluate(
            """({title}) => {
                const cta = document.createElement('div');
                cta.style.cssText = `
                  position:fixed;bottom:32px;left:20px;right:20px;z-index:100001;
                  background:rgba(15,23,42,0.95);border:2px solid #38bdf8;
                  border-radius:20px;padding:18px;text-align:center;color:#fff;
                  font-family:sans-serif;box-shadow:0 12px 32px rgba(0,0,0,0.6);
                `;
                cta.innerHTML = `
                  <div style="color:#38bdf8;font-size:13px;font-weight:700;letter-spacing:1px;">
                    TRY THIS APP LIVE NOW
                  </div>
                  <div style="font-size:17px;font-weight:700;margin:6px 0;">${title}</div>
                  <div style="font-size:13px;color:#cbd5e1;">
                    Live App &amp; Pro Bundle Link in Description / Bio
                  </div>
                `;
                document.body.appendChild(cta);
            }""",
            {"title": title[:40]},
        )
        page.wait_for_timeout(2500)

        video_path_str = page.video.path()
        context.close()
        browser.close()

    return Path(video_path_str)


# =====================================================================
# STEP 2: GENERATE VOICEOVER & MERGE WITH LIVE SCREEN RECORDING
# =====================================================================
def render_9x16_promo_video(
    recorded_webm: Path,
    voiceover_text: str,
    output_mp4: Path,
) -> Path:
    """Combines the moving Playwright `.webm` video with neural `edge-tts` audio."""
    audio_mp3 = DIST_DIR / "voiceover.mp3"
    subs_srt = DIST_DIR / "subtitles.srt"

    tts_ok = False
    if shutil.which("edge-tts"):
        print("   -> Generating neural voiceover MP3 via edge-tts...")
        try:
            subprocess.run(
                [
                    "edge-tts",
                    "--voice",
                    "en-US-ChristopherNeural",
                    "--text",
                    voiceover_text,
                    "--write-media",
                    str(audio_mp3),
                    "--write-subtitles",
                    str(subs_srt),
                ],
                check=True,
                timeout=45,
            )
            tts_ok = audio_mp3.exists() and audio_mp3.stat().st_size > 500
        except Exception as e:
            print(f"   -> edge-tts notice ({e}); using 15s backup audio...")

    if not tts_ok:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=44100:cl=stereo",
                "-t",
                "15",
                "-q:a",
                "9",
                "-acodec",
                "libmp3lame",
                str(audio_mp3),
            ],
            check=True,
        )

    print("   -> Merging live moving 9:16 screen recording + voiceover via FFmpeg...")
    vf_filter = (
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=#0f172a,"
        "format=yuv420p"
    )
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-stream_loop",
        "-1",
        "-i",
        str(recorded_webm),
        "-i",
        str(audio_mp3),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-vf",
        vf_filter,
        "-r",
        "30",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output_mp4),
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    print(f"   -> Saved moving 9:16 video to: {output_mp4}")
    return output_mp4


# =====================================================================
# STEP 3: CREATE WHOP PRODUCT & LIVE CHECKOUT LINK
# =====================================================================
def create_whop_product_and_checkout(
    app_title: str,
    app_desc: str,
    price_usd: float,
    pro_bundle_url: str,
    live_demo_url: str,
) -> tuple[str, str]:
    """
    Calls the real Whop API (`https://api.whop.com/api/v1/checkout_configurations`
    and `/api/v1/products`) to create a visible product and a live checkout URL
    that redirects buyers straight to `pro_bundle_url`.
    """
    if not (WHOP_API_KEY and WHOP_COMPANY_ID):
        return live_demo_url, "Skipped (WHOP_API_KEY or WHOP_COMPANY_ID missing)"

    print("4. Whop Agent: Creating product & checkout link on api.whop.com...")
    # 1. Create visible product in Whop Dashboard so it appears in your store
    created_prod_id = ""
    try:
        prod_req = urllib.request.Request(
            "https://api.whop.com/api/v1/products",
            data=json.dumps(
                {
                    "account_id": WHOP_COMPANY_ID,
                    "title": app_title[:50],
                    "description": app_desc[:250],
                    "visibility": "visible",
                    "redirect_purchase_url": pro_bundle_url,
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {WHOP_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(prod_req, timeout=30) as p_resp:
            p_data = json.loads(p_resp.read().decode("utf-8"))
            created_prod_id = p_data.get("id", "")
            print(f"   -> Created visible Whop Product: {created_prod_id}")
    except urllib.error.HTTPError as e:
        print(f"   -> Whop /v1/products notice (HTTP {e.code}): {e.read().decode('utf-8', errors='replace')[:200]}")
    except Exception as e:
        print(f"   -> Whop /v1/products notice: {e}")

    # 2. Create live checkout link (`purchase_url`) via `/api/v1/checkout_configurations`
    plan_obj = {
        "company_id": WHOP_COMPANY_ID,
        "initial_price": price_usd,
        "plan_type": "one_time",
        "title": app_title[:30],
        "description": app_desc[:200],
    }
    if created_prod_id:
        plan_obj["product_id"] = created_prod_id
    else:
        plan_obj["product"] = {
            "title": app_title[:50],
            "description": app_desc[:250],
            "redirect_purchase_url": pro_bundle_url,
        }

    checkout_payload = {
        "plan": plan_obj,
        "mode": "payment",
        "redirect_url": pro_bundle_url,
    }
    try:
        req = urllib.request.Request(
            "https://api.whop.com/api/v1/checkout_configurations",
            data=json.dumps(checkout_payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {WHOP_API_KEY}",
                "Content-Type": "application/json",
                "Api-Version-Date": "2025-01-01",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            w_data = json.loads(resp.read().decode("utf-8"))
            purchase_url = w_data.get("purchase_url") or w_data.get("direct_link")
            if purchase_url:
                print(f"   -> Created live Whop Checkout URL: {purchase_url}")
                return purchase_url, f"Live Whop Checkout created ({w_data.get('id', 'ok')})"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"   -> Whop checkout HTTP {e.code}: {err_body[:300]}")
        return live_demo_url, f"Product {created_prod_id or 'none'} | Checkout HTTP {e.code}: {err_body[:160]}"
    except Exception as e:
        print(f"   -> Whop checkout error: {e}")
        return live_demo_url, f"Error: {e}"

    return live_demo_url, "Fallback to live demo URL"


# =====================================================================
# STEP 4: UPLOAD TO YOUTUBE SHORTS & INSTAGRAM REELS
# =====================================================================
def get_youtube_access_token() -> str:
    token_url = "https://oauth2.googleapis.com/token"
    payload = urllib.parse.urlencode(
        {
            "client_id": YT_CLIENT_ID,
            "client_secret": YT_CLIENT_SECRET,
            "refresh_token": YT_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        token_url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["access_token"]


def upload_to_youtube_shorts(mp4_path: Path, title: str, description: str) -> str:
    if not (YT_CLIENT_ID and YT_CLIENT_SECRET and YT_REFRESH_TOKEN):
        return "Skipped (YouTube secrets missing)"

    print("   -> Uploading moving 9:16 MP4 to YouTube Shorts...")
    access_token = get_youtube_access_token()
    metadata = {
        "snippet": {
            "title": f"{title[:82]} #Shorts",
            "description": f"{description}\n\n#Shorts #AI #Productivity #WebApp",
            "categoryId": "28",
        },
        "status": {
            "privacyStatus": YT_PRIVACY_STATUS,
            "selfDeclaredMadeForKids": False,
        },
    }
    init_url = (
        "https://www.googleapis.com/upload/youtube/v3/videos"
        "?uploadType=resumable&part=snippet,status"
    )
    video_bytes = mp4_path.read_bytes()
    init_req = urllib.request.Request(
        init_url,
        data=json.dumps(metadata).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(len(video_bytes)),
            "X-Upload-Content-Type": "video/mp4",
        },
        method="POST",
    )
    with urllib.request.urlopen(init_req, timeout=30) as init_resp:
        upload_location = init_resp.headers.get("Location")

    upload_req = urllib.request.Request(
        upload_location,
        data=video_bytes,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Length": str(len(video_bytes)),
            "Content-Type": "video/mp4",
        },
        method="PUT",
    )
    with urllib.request.urlopen(upload_req, timeout=180) as up_resp:
        yt_data = json.loads(up_resp.read().decode("utf-8"))
        video_id = yt_data.get("id", "")
        yt_url = f"https://youtube.com/shorts/{video_id}"

# =====================================================================
# MAIN 6-AGENT ORCHESTRATOR LOOP
# =====================================================================
def main() -> None:
    live_demo_url = f"{PUBLIC_VIDEO_BASE_URL}/"
    pro_bundle_url = f"{RAW_GITHUB_BASE_URL}/pro_app_bundle.zip"
    run_ts = int(time.time())
    # Use raw.githubusercontent.com so Instagram gets the newly pushed video immediately!
    public_mp4_url = f"{RAW_GITHUB_BASE_URL}/promo_short_9x16.mp4?v={run_ts}"

    # --- AGENT 1: SCOUT & ARCHITECT ---
    print("1. Scout Agent: Selecting today's micro-app product...")
    spec_raw = ask_agent(
        "You are a Product Architect Agent. Return valid JSON only with keys: "
        "'title', 'subtitle', 'price_usd'. No markdown fences.",
        "Pick ONE practical, visually interactive single-page HTML5/JS calculator, "
        "study planner, fitness tracker, or creator utility micro-app idea.",
    )
    clean_spec = spec_raw.replace("```json", "").replace("```", "").strip()
    try:
        spec = json.loads(clean_spec)
    except json.JSONDecodeError:
        spec = {
            "title": "Smart Study & Focus Sprint Calculator",
            "subtitle": "Interactive Pomodoro & retention planner with live progress bars.",
            "price_usd": 9.00,
        }

    app_title = spec.get("title", "Smart Study & Focus Sprint Calculator")
    app_desc = spec.get("subtitle", "Interactive browser toolkit and offline template.")
    price_usd = float(spec.get("price_usd", 9.00))

    # --- AGENT 2: APP & ZIP BUILDER ---
    print(f"2. Builder Agent: Coding interactive app '{app_title}'...")
    raw_html = ask_agent(
        "You are a Senior Frontend Engineer. Output ONLY raw, valid single-file HTML5 code "
        "(including <style> and <script>) optimized for a 9:16 mobile screen. No markdown fences.",
        f"Build a complete, visually striking interactive mobile web app for '{app_title}' ({app_desc}). "
        "Include 3 interactive <input type='range'> sliders that dynamically update big KPI cards "
        "and colored progress bars/charts in real time, plus 3 preset <button> elements.",
    )
    clean_html = raw_html.replace("```html", "").replace("```", "").strip()

    html_file = PUBLIC_DIR / "index.html"
    html_file.write_text(clean_html, encoding="utf-8")

    for z_target in (DIST_DIR / "pro_app_bundle.zip", PUBLIC_DIR / "pro_app_bundle.zip"):
        with zipfile.ZipFile(z_target, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("app_pro_offline.html", clean_html)
            zf.writestr(
                "README_GUIDE.txt",
                f"{app_title}\n{app_desc}\n\nLive Web App: {live_demo_url}\n",
            )

    # --- AGENT 3: QA CRITIC GATE ---
    print("3. Critic Agent: Auditing HTML build & bundle...")
    if "<html" not in clean_html.lower() or len(clean_html) < 200:
        raise RuntimeError("Critic Agent blocked release: HTML output failed validation.")

    # --- AGENT 4: WHOP STORE MANAGER ---
    checkout_url, whop_status = create_whop_product_and_checkout(
        app_title, app_desc, price_usd, pro_bundle_url, live_demo_url
    )

    # --- AGENT 5: PROMOTER & LIVE 9:16 VIDEO WALKTHROUGH ---
    print("5. Promoter Agent: Recording live 9:16 app walkthrough & rendering MP4...")
    promo_json_raw = ask_agent(
        "You are a Short-Form Video Marketer. Return valid JSON only with two keys: "
        "'voiceover' (a punchy 32-word spoken script with no emojis or hashtags) and "
        "'caption' (social post description). No fences.",
        f"Promote our new interactive web app '{app_title}' ({app_desc}).",
    )
    clean_promo = promo_json_raw.replace("```json", "").replace("```", "").strip()
    try:
        promo_data = json.loads(clean_promo)
    except json.JSONDecodeError:
        promo_data = {
            "voiceover": (
                f"Watch how fast {app_title} works on your phone. "
                f"Move the sliders to calculate your exact numbers in real time. "
                f"Try the live app or grab the pro toolkit from the link in the description."
            ),
            "caption": f"New AI Micro-App: {app_title} ({app_desc})",
        }

    voiceover_script = promo_data.get("voiceover", "")
    social_caption = (
        f"{promo_data.get('caption', app_title)}\n\n"
        f"🚀 Use Live Web App: {live_demo_url}\n"
        f"📦 Get Pro Bundle: {checkout_url}\n"
        f"#Shorts #Reels #AI #WebApp"
    )

    mp4_path = PUBLIC_DIR / "promo_short_9x16.mp4"
    recorded_webm = record_live_9x16_app_demo(html_file, app_title, app_desc)
    render_9x16_promo_video(recorded_webm, voiceover_script, mp4_path)

    # Push newly built app + moving MP4 to GitHub right now so Instagram fetches the new video!
    print("   -> Pushing new app & moving MP4 to GitHub before social uploads...")
    subprocess.run(["git", "config", "user.name", "AI-Company-Bot"], check=False)
    subprocess.run(["git", "config", "user.email", "bot@users.noreply.github.com"], check=False)
    subprocess.run(["git", "add", "public/", "dist/"], check=False)
    subprocess.run(["git", "commit", "-m", f"Auto-build: {app_title}"], check=False)
    subprocess.run(["git", "push"], check=False)
    time.sleep(3)

    yt_result = upload_to_youtube_shorts(mp4_path, app_title, social_caption)
    ig_result = upload_to_instagram_reels(public_mp4_url, social_caption)

    # --- AGENT 6: GMAIL CEO REPORT ---
    if GMAIL_USER and GMAIL_APP_PASS:
        print("6. Gmail Agent: Sending daily CEO report...")
        msg = EmailMessage()
        msg["Subject"] = f"[AI Company Daily Launch] {app_title}"
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_USER
        msg.set_content(
            f"Daily Autonomous Cycle Complete!\n\n"
            f"1. Product Built: {app_title}\n"
            f"   Subtitle: {app_desc}\n\n"
            f"2. OPEN LIVE WEB APP (Tap to use your product):\n"
            f"   {live_demo_url}\n\n"
            f"3. DOWNLOAD PRO ZIP BUNDLE:\n"
            f"   {pro_bundle_url}\n\n"
            f"4. WHOP STORE & CHECKOUT:\n"
            f"   Checkout URL: {checkout_url}\n"
            f"   Whop API Status: {whop_status}\n\n"
            f"5. SOCIAL VIDEOS PUBLISHED:\n"
            f"   YouTube Shorts: {yt_result}\n"
            f"   Instagram Reels: {ig_result}\n\n"
            f"Voiceover Script:\n{voiceover_script}\n"
        )
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_APP_PASS)
            smtp.send_message(msg)

    print("Full-circle app build, moving 9:16 MP4 render, and social upload finished!")


if __name__ == "__main__":
    main()
