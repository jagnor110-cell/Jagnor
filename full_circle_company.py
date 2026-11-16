
#!/usr/bin/env python3
"""
full_circle_company.py — Autonomous 6-Agent App Factory & Short-Form Video Publisher
====================================================================================
End-to-end pipeline designed to run in GitHub Actions (Ubuntu) or locally:
  1. Scout Agent: Picks a daily micro-app product idea via Gemini API.
  2. Builder Agent: Generates a mobile-ready HTML5/JS web app + Pro .zip bundle.
  3. Critic Agent: Verifies code integrity before release.
  4. Whop Store Agent: Creates a paid plan and live checkout link via Whop API.
  5. Promoter & Video Agent:
     - Writes a 20-second vertical video voiceover script + social caption.
     - Captures a 1080x1920 (9:16) screenshot of the live app via Playwright
       (with an automatic Pillow promo-card fallback on Android/lightweight setups).
     - Generates neural speech (MP3) + subtitles (SRT) via edge-tts.
     - Renders a 1080x1920 H.264 MP4 video (`dist/promo_short_9x16.mp4`) via FFmpeg.
     - Uploads the MP4 to YouTube Shorts (YouTube Data API v3) and Instagram Reels
       (Instagram Graph API 2-step container flow).
  6. Gmail Operations Agent: Emails the daily launch report via Gmail SMTP.

GitHub Actions Setup Commands (inside .github/workflows/heartbeat.yml):
-----------------------------------------------------------------------
  sudo apt-get update && sudo apt-get install -y ffmpeg
  pip install playwright edge-tts pillow
  playwright install --with-deps chromium
  python3 full_circle_company.py

Official Documentation References:
  - Gemini API: https://aistudio.google.com/docs/get-started
  - Whop API: https://docs.whop.com/developer/quickstart
  - Playwright Screenshots: https://playwright.dev/python/docs/screenshots
  - edge-tts Neural Voices: https://pypi.org/project/edge-tts/
  - FFmpeg 9:16 Vertical Video: https://varg.ai/how-to/crop-a-video-to-vertical-with-ffmpeg
  - YouTube Data API v3 Uploads: https://developers.google.com/youtube/data/guides/uploading_a_video
  - Instagram Graph API Reels: https://developers.facebook.com/documentation/instagram-platform/content-publishing
  - Gmail App Passwords: https://myaccount.google.com/apppasswords
"""

import json
import os
import shutil
import smtplib
import subprocess
import time
import urllib.parse
import urllib.request
import zipfile
from email.message import EmailMessage
from pathlib import Path

# =====================================================================
# 0. ENVIRONMENT CONFIGURATION & CREDENTIALS
# =====================================================================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "PASTE_GEMINI_KEY")
MODEL = "gemini-4-hydrogen"

# Whop Store Credentials (https://docs.whop.com/developer/quickstart)
WHOP_API_KEY = os.environ.get("WHOP_API_KEY", "")          # Starts with apik_
WHOP_COMPANY_ID = os.environ.get("WHOP_COMPANY_ID", "")    # Starts with biz_

# YouTube Data API v3 OAuth Credentials
YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID", "")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET", "")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN", "")
YT_PRIVACY_STATUS = os.environ.get("YT_PRIVACY_STATUS", "private")  # "private" or "public"

# Instagram Graph API Credentials (requires Creator/Business IG account)
IG_USER_ID = os.environ.get("IG_USER_ID", "")              # Numeric Instagram Business ID
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")    # Long-lived Graph API token
# Public base URL where GitHub Pages or release assets host the rendered MP4 for IG Graph API
PUBLIC_VIDEO_BASE_URL = os.environ.get("PUBLIC_VIDEO_BASE_URL", "")

# Dedicated Company Gmail Credentials
GMAIL_USER = os.environ.get("COMPANY_GMAIL", "")
GMAIL_APP_PASS = os.environ.get("GMAIL_APP_PASSWORD", "")  # 16-char Google App Password

PUBLIC_DIR = Path("public")
DIST_DIR = Path("dist")
PUBLIC_DIR.mkdir(exist_ok=True)
DIST_DIR.mkdir(exist_ok=True)


# =====================================================================
# HELPER: CALL GEMINI AGENT
# =====================================================================
def ask_agent(role_prompt: str, task_prompt: str) -> str:
    """Sends a structured role + task prompt to the Gemini API."""
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
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]


# =====================================================================
# STEP 1:CAPTURE 1080x1920 (9:16) SCREENSHOT OF THE GENERATED APP
# =====================================================================
def capture_9x16_app_screenshot(html_path: Path, output_png: Path, title: str, subtitle: str) -> Path:
    """
    Captures a native 1080x1920 (9:16 vertical) screenshot of the generated HTML app
    using Playwright Chromium. Falls back to generating a clean 1080x1920 promo card
    with Pillow if Playwright is not installed.
    """
    try:
        from playwright.sync_api import sync_playwright

        print("   -> Capturing 1080x1920 (9:16) live app screenshot via Playwright...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 540, "height": 960},
                device_scale_factor=2,  # Renders crisp 1080x1920 output
            )
            page = context.new_page()
            page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            page.wait_for_timeout(800)
            page.screenshot(path=str(output_png), full_page=False)
            browser.close()
        return output_png
    except Exception as e:
        print(f"   -> Playwright unavailable ({e}); building 1080x1920 promo card via Pillow...")
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (1080, 1920), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)
        # Draw decorative card frame
        draw.rounded_rectangle(
            [(70, 260), (1010, 1660)],
            radius=48,
            fill=(30, 41, 59),
            outline=(56, 189, 248),
            width=6,
        )
        font = ImageFont.load_default()
        draw.text((140, 420), "NEW AI MICRO-APP RELEASE", fill=(56, 189, 248), font=font)
        draw.text((140, 540), title[:42], fill=(255, 255, 255), font=font)
        draw.text((140, 660), subtitle[:70], fill=(148, 163, 184), font=font)
        draw.text((140, 1500), "Link in Bio / Description -> Try It Now", fill=(56, 189, 248), font=font)
        img.save(output_png)
        return output_png


# =====================================================================
# STEP 2: GENERATE NEURAL VOICEOVER (MP3) + RENDER 9:16 MP4 VIA FFMPEG
# =====================================================================
def render_9x16_promo_video(
    screenshot_png: Path,
    voiceover_text: str,
    output_mp4: Path,
) -> Path:
    """
    1. Converts `voiceover_text` into natural speech (`dist/voiceover.mp3`) and
       word-synced subtitles (`dist/subtitles.srt`) using `edge-tts`.
    2. Uses FFmpeg to combine the 1080x1920 screenshot and audio into a
       YouTube-Shorts & Instagram-Reels compliant 9:16 MP4 (H.264 + AAC).
    """
    audio_mp3 = DIST_DIR / "voiceover.mp3"
    subs_srt = DIST_DIR / "subtitles.srt"

    # 1. Generate Neural TTS Audio via edge-tts CLI
    if shutil.which("edge-tts"):
        print("   -> Generating neural voiceover MP3 + SRT subtitles via edge-tts...")
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
        )
    else:
        raise RuntimeError(
            "edge-tts is required for neural voiceover generation. "
            "Install it with: pip install edge-tts"
        )

    # 2. Render 1080x1920 (9:16) MP4 with subtle zoompan motion + AAC audio via FFmpeg
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg is required to render MP4 video. Install with: apt install ffmpeg")

    print("   -> Rendering 1080x1920 (9:16) H.264 MP4 video via FFmpeg...")
    vf_filter = (
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=#0f172a,"
        "format=yuv420p"
    )
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-framerate",
        "30",
        "-i",
        str(screenshot_png),
        "-i",
        str(audio_mp3),
        "-vf",
        vf_filter,
        "-c:v",
        "libx264",
        "-tune",
        "stillimage",
        "-preset",
        "medium",
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
    print(f"   -> Saved 9:16 vertical video to: {output_mp4}")
    return output_mp4


# =====================================================================
# STEP 3: UPLOAD 9:16 MP4 TO YOUTUBE SHORTS (YOUTUBE DATA API V3)
# =====================================================================
def get_youtube_access_token() -> str:
    """Exchanges the stored OAuth2 Refresh Token for a fresh YouTube access token."""
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
    """
    Uploads the rendered 9:16 MP4 to YouTube Shorts using the YouTube Data API v3
    resumable upload protocol (https://developers.google.com/youtube/data/guides/uploading_a_video).
    """
    if not (YT_CLIENT_ID and YT_CLIENT_SECRET and YT_REFRESH_TOKEN):
        print("   -> [Skipped YouTube Upload] Set YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.")
        return "Not uploaded (YouTube OAuth secrets not configured)"

    print("   -> Uploading 9:16 MP4 to YouTube Shorts via YouTube Data API v3...")
    access_token = get_youtube_access_token()

    short_title = f"{title[:85]} #Shorts"
    metadata = {
        "snippet": {
            "title": short_title,
            "description": f"{description}\n\n#Shorts #AI #Productivity #WebApp",
            "categoryId": "28",  # Science & Technology
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
        print(f"   -> Published YouTube Short: {yt_url}")
        return yt_url


# =====================================================================
# STEP 4: UPLOAD 9:16 MP4 TO INSTAGRAM REELS (INSTAGRAM GRAPH API)
# =====================================================================
def upload_to_instagram_reels(public_mp4_url: str, caption: str) -> str:
    """
    Publishes a 9:16 MP4 to Instagram Reels using Meta's two-step Content Publishing API:
      1. POST /{ig-user-id}/media (media_type=REELS, video_url=public_mp4_url)
      2. Poll container status_code until FINISHED
      3. POST /{ig-user-id}/media_publish
    Docs: https://developers.facebook.com/documentation/instagram-platform/content-publishing
    """
    if not (IG_USER_ID and IG_ACCESS_TOKEN and public_mp4_url):
        print("   -> [Skipped Instagram Upload] Set IG_USER_ID, IG_ACCESS_TOKEN, PUBLIC_VIDEO_BASE_URL.")
        return "Not uploaded (Instagram Graph API secrets not configured)"

    print("   -> Creating Instagram Reels media container via Graph API...")
    create_url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media"
    create_params = urllib.parse.urlencode(
        {
            "media_type": "REELS",
            "video_url": public_mp4_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": IG_ACCESS_TOKEN,
        }
    ).encode("utf-8")

    req = urllib.request.Request(create_url, data=create_params, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        creation_id = json.loads(resp.read().decode("utf-8"))["id"]

    # Poll container readiness (up to 10 checks, 10 seconds apart)
    status_url = (
        f"https://graph.facebook.com/v21.0/{creation_id}"
        f"?fields=status_code&access_token={IG_ACCESS_TOKEN}"
    )
    for attempt in range(1, 11):
        time.sleep(10)
        with urllib.request.urlopen(status_url, timeout=20) as s_resp:
            status_code = json.loads(s_resp.read().decode("utf-8")).get("status_code", "")
            print(f"   -> Instagram container status (attempt {attempt}/10): {status_code}")
            if status_code == "FINISHED":
                break
            if status_code == "ERROR":
                raise RuntimeError("Instagram Graph API reported media container ERROR.")

    # Publish the finished Reels container
    publish_url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish"
    pub_params = urllib.parse.urlencode(
        {
            "creation_id": creation_id,
            "access_token": IG_ACCESS_TOKEN,
        }
    ).encode("utf-8")
    pub_req = urllib.request.Request(publish_url, data=pub_params, method="POST")
    with urllib.request.urlopen(pub_req, timeout=30) as p_resp:
        media_id = json.loads(p_resp.read().decode("utf-8")).get("id", "")
        print(f"   -> Published Instagram Reel Media ID: {media_id}")
        return f"Instagram Reel ID: {media_id}"


# =====================================================================
# MAIN 6-AGENT ORCHESTRATOR LOOP
# =====================================================================
def main() -> None:
    # --- AGENT 1: SCOUT & ARCHITECT ---
    print("1. Scout Agent: Selecting today's micro-app product...")
    spec_raw = ask_agent(
        "You are a Product Architect Agent. Return valid JSON only with keys: "
        "'title', 'subtitle', 'price_usd'. No markdown fences.",
        "Pick ONE practical single-page interactive HTML5/JS calculator, study planner, "
        "or productivity micro-app idea.",
    )
    clean_spec = spec_raw.replace("```json", "").replace("```", "").strip()
    try:
        spec = json.loads(clean_spec)
    except json.JSONDecodeError:
        spec = {
            "title": "Smart Study & Focus Sprint Calculator",
            "subtitle": "Interactive Pomodoro & retention planner with offline storage.",
            "price_usd": 9.00,
        }

    app_title = spec.get("title", "Smart Study & Focus Sprint Calculator")
    app_desc = spec.get("subtitle", "Interactive browser toolkit and offline template.")
    price_usd = float(spec.get("price_usd", 9.00))

    # --- AGENT 2: APP & ZIP BUILDER ---
    print(f"2. Builder Agent: Coding '{app_title}'...")
    raw_html = ask_agent(
        "You are a Senior Frontend Engineer. Output ONLY raw, valid single-file HTML5 code "
        "(including <style> and <script>) optimized for a 9:16 mobile screen. No markdown fences.",
        f"Build a complete, interactive mobile web app for '{app_title}' ({app_desc}). "
        "Include interactive sliders/inputs, live calculated metrics, and a polished dark UI.",
    )
    clean_html = raw_html.replace("```html", "").replace("```", "").strip()

    html_file = PUBLIC_DIR / "index.html"
    html_file.write_text(clean_html, encoding="utf-8")

    zip_path = DIST_DIR / "pro_app_bundle.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("app_pro_offline.html", clean_html)
        zf.writestr("README_GUIDE.txt", f"{app_title}\n\n{app_desc}\n")

    # --- AGENT 3: QA CRITIC GATE ---
    print("3. Critic Agent: Auditing HTML build & bundle...")
    if "<html" not in clean_html.lower() or len(clean_html) < 200:
        raise RuntimeError("Critic Agent blocked release: HTML output failed validation.")

    # --- AGENT 4: WHOP STORE MANAGER ---
    checkout_url = "https://whop.com/your-store-link"
    if WHOP_API_KEY and WHOP_COMPANY_ID:
        print("4. Whop Agent: Creating checkout link via Whop API...")
        whop_req = urllib.request.Request(
            "https://api.whop.com/api/v2/plans",
            data=json.dumps(
                {
                    "company_id": WHOP_COMPANY_ID,
                    "plan_type": "one_time",
                    "initial_price": price_usd,
                    "currency": "usd",
                    "title": app_title[:50],
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {WHOP_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(whop_req, timeout=30) as w_resp:
                w_data = json.loads(w_resp.read().decode("utf-8"))
                checkout_url = w_data.get("direct_link", checkout_url)
        except Exception as e:
            print(f"   -> Whop API notice: {e}")

    # --- AGENT 5: PROMOTER, 9:16 MP4 RENDERER & SOCIAL UPLOADER ---
    print("5. Promoter Agent: Creating 9:16 Short/Reel script, screenshot, and MP4...")
    promo_json_raw = ask_agent(
        "You are a Short-Form Video Marketer. Return valid JSON only with two keys: "
        "'voiceover' (a punchy 35-word spoken script with no emojis or hashtags) and "
        "'caption' (social post description with the checkout link and hashtags). No fences.",
        f"Promote the new web app '{app_title}' ({app_desc}). "
        f"Direct viewers to grab it at: {checkout_url}",
 )
    clean_promo = promo_json_raw.replace("```json", "").replace("```", "").strip()
    try:
        promo_data = json.loads(clean_promo)
    except json.JSONDecodeError:
        promo_data = {
            "voiceover": (
                f"Stop guessing your daily workflow. We just built {app_title}. "
                f"Adjust your inputs, track live results right on your phone, "
                f"and grab the full offline toolkit from the link in the description."
            ),
            "caption": f"Try {app_title}! Grab the full app pack here: {checkout_url} #Shorts #Reels #AI",
        }

    voiceover_script = promo_data.get("voiceover", "")
    social_caption = promo_data.get("caption", f"{app_title} -> {checkout_url}")

    screenshot_path = DIST_DIR / "app_9x16.png"
    mp4_path = PUBLIC_DIR / "promo_short_9x16.mp4"

    capture_9x16_app_screenshot(html_file, screenshot_path, app_title, app_desc)
    render_9x16_promo_video(screenshot_path, voiceover_script, mp4_path)

    yt_result = upload_to_youtube_shorts(mp4_path, app_title, social_caption)
    public_mp4_url = (
        f"{PUBLIC_VIDEO_BASE_URL.rstrip('/')}/promo_short_9x16.mp4"
        if PUBLIC_VIDEO_BASE_URL
        else ""
    )
    ig_result = upload_to_instagram_reels(public_mp4_url, social_caption)

    # --- AGENT 6: GMAIL CEO REPORT & SUPPORT BOT ---
    if GMAIL_USER and GMAIL_APP_PASS:
        print("6. Gmail Agent: Sending daily CEO report...")
        msg = EmailMessage()
        msg["Subject"] = f"[AI Company Daily Launch] {app_title}"
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_USER
        msg.set_content(
            f"Daily Autonomous Cycle Complete!\n\n"
            f"Product: {app_title}\n"
            f"Whop Checkout URL: {checkout_url}\n"
            f"YouTube Shorts Status: {yt_result}\n"
            f"Instagram Reels Status: {ig_result}\n\n"
            f"Voiceover Script:\n{voiceover_script}\n\n"
            f"Social Caption:\n{social_caption}\n"
        )
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_APP_PASS)
            smtp.send_message(msg)

    print("Full-circle app build, 9:16 MP4 render, and social upload pipeline finished!")


if __name__ == "__main__":
    main()
