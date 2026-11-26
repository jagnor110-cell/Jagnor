#!/usr/bin/env python3
"""
jagnor_master_worker.py — Unified Master Execution, 4-Brain Free AI Council, Trend Discovery & Publishing Engine
Orchestration Layer: Paperclip & GitHub Actions (`clipping_company.yml`)
All-in-One Standalone Script: Built-in Social Publisher (YouTube Shorts + Instagram Graph API v22.0) & Gmail SMTP Reporter (no separate py required)

4-Brain Free AI Council (`AICouncil` — 100% Free-Tier Stack):
1. Gemini (`GEMINI_API_KEY` / `gemini-2.5-flash`)                       — Transcript & Viral Script Strategist
2. Groq (`GROQ_API_KEY` / `llama-3.3-70b-versatile`)                    — Narrative Pacing, 3s Hook & IG Captioner
3. NVIDIA NIM (`NVIDIA_API_KEY` / `nvidia/nemotron-3-super-120b-a12b`)  — YouTube Shorts Title, SEO & Hashtag Polisher
4. OpenRouter (`OPENROUTER_API_KEY` / `openrouter/free`)                — Chief Consensus Judge & Universal Fallback Router

Free Visual Engines (`--engine ai_faceless` with selectable `--art-style` & `--theme`):
- Pollinations.ai (`POLLINATIONS_API_KEY`) -> OpenRouter/HF FLUX (`HF_TOKEN`) -> Pixabay HD Portrait Media (`PIXABAY_API_KEY`) -> Clean Branded Fallback
"""

from __future__ import annotations

import argparse
import base64
import fcntl
import gc
import hashlib
import html
import json
import logging
import math
import os
import random
import re
import shutil
import smtplib
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
import zlib
from dataclasses import asdict, dataclass, field
from email.message import EmailMessage
from fractions import Fraction
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("jagnor_master_worker")


# ============================================================================
# 0. BUILT-IN SOCIAL PUBLISHER, ATOMIC I/O, RATE LIMITS & GMAIL SMTP REPORTER
#    (Merged from py — YouTube Data API v3, IG Graph v22.0)
# ============================================================================

IG_GRAPH_BASE = "https://graph.facebook.com/v22.0"
YT_TOKEN_URL = "https://oauth2.googleapis.com/token"
YT_UPLOAD_INIT_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}


# ============================================================================
# 1. ATOMIC JSON I/O, HTTP RETRY & GMAIL SMTP REPORTING
# ============================================================================

def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    payload = json.dumps(data, indent=2, ensure_ascii=False)

    with lock_path.open("w", encoding="utf-8") as lock_f:
        fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
        try:
            fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
                    tmp_f.write(payload)
                    tmp_f.flush()
                    os.fsync(tmp_f.fileno())
                os.replace(tmp_name, path)
            except Exception:
                if os.path.exists(tmp_name):
                    os.unlink(tmp_name)
                raise
        finally:
            fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)


def urlopen_with_retry(
    req: urllib.request.Request,
    timeout: int = 60,
    max_attempts: int = 3,
    base_backoff: float = 2.0,
) -> tuple[bytes, dict[str, str]]:
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                headers = {k.lower(): v for k, v in resp.headers.items()}
                return resp.read(), headers
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace")
            if err.code in RETRYABLE_HTTP_CODES and attempt < max_attempts:
                sleep_s = base_backoff * (2 ** (attempt - 1))
                log.warning("HTTP %d (attempt %d/%d); retrying in %.1fs...", err.code, attempt, max_attempts, sleep_s)
                time.sleep(sleep_s)
                last_exc = RuntimeError(f"HTTP {err.code}: {err_body}")
                continue
            raise RuntimeError(f"HTTP {err.code}: {err_body}") from err
        except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
            if attempt < max_attempts:
                sleep_s = base_backoff * (2 ** (attempt - 1))
                log.warning("Network error %s (attempt %d/%d); retrying in %.1fs...", err, attempt, max_attempts, sleep_s)
                time.sleep(sleep_s)
                last_exc = err
                continue
            raise RuntimeError(f"Network error after {max_attempts} attempts: {err}") from err
    raise RuntimeError(f"Request failed: {last_exc}")


def format_manifest_report(
    manifest: dict[str, Any] | None,
    stage: str,
    error_msg: str | None = None,
) -> tuple[str, str]:
    """
    Builds a concise, high-signal email subject and plain-text body with status,
    4-Brain Free AI Council details, public preview links, and YouTube/Instagram receipts.
    """
    m = manifest or {}
    engine = m.get("source_mode") or m.get("engine", "unknown")
    status = "FAILED" if error_msg else m.get("status", "UNKNOWN")
    public_base = _get_public_base_url()

    subject = f"[Jagnor AI | {engine}] {status} (stage={stage})"
    rt = m.get("red_team_audit") if isinstance(m.get("red_team_audit"), dict) else {}
    rt_line = f"Red-Team Critic: {rt.get('verdict', 'N/A')} (issues={len(rt.get('issues_found') or [])}, fixes={len(rt.get('fixes_applied') or [])})" if rt else "Red-Team Critic: N/A"
    lines: list[str] = [
        f"Pipeline Stage: {stage}",
        f"Business Engine: {engine}",
        rt_line,
        f"Status: {status}",
        f"Timestamp (UTC): {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        "",
    ]

    if error_msg:
        lines.extend([
            "--- ERROR DETAILS ---",
            error_msg,
            "",
        ])

    if m.get("source_url"):
        lines.append(f"Source Video: {m['source_url']}")
    if m.get("product_title"):
        lines.append(f"Product Title: {m['product_title']} (${m.get('price_usd', 0):.2f})")
    if m.get("client_name"):
        lines.append(f"B2B Client: {m['client_name']} (Invoice {m.get('invoice_id', 'N/A')} - ${m.get('amount_due_usd', 0):.2f})")
    if m.get("script_source") and m.get("script_source") != "ai":
        lines.append(f"Script source: {m['script_source']} (AI council unavailable{' - NOT published' if m.get('script_source') == 'template' else ''})")
    if m.get("council_models_used"):
        lines.append(f"AI Council Models: {', '.join(m['council_models_used'])}")
    lines.append("")

    # Public Preview Links & Clip Details
    clips = m.get("clips", [])
    if clips:
        lines.append("--- RENDERED CLIPS ---")
        for c in clips:
            mp4_name = Path(c.get("mp4_path", "")).name
            preview_url = f"{public_base}/{mp4_name}" if (public_base and mp4_name) else c.get("mp4_path", "")
            lines.append(
                f"* {c.get('clip_id')} ({c.get('duration_sec')}s | {c.get('layout_mode')}): {c.get('yt_title')}"
            )
            lines.append(f"  Hook Banner: {c.get('hook_overlay', '')}")
            lines.append(f"  Preview URL: {preview_url}")
        lines.append("")

    if m.get("promo_mp4_path"):
        promo_name = Path(m["promo_mp4_path"]).name
        lines.append(f"Promo Video URL: {public_base}/{promo_name}" if public_base else f"Promo Video: {m['promo_mp4_path']}")
    if m.get("bundle_zip_path"):
        zip_name = Path(m["bundle_zip_path"]).name
        lines.append(f"Product Bundle ZIP: {public_base}/{zip_name}" if public_base else f"Product Bundle ZIP: {m['bundle_zip_path']}")
    if m.get("whop_checkout_url"):
        simulated = " (SIMULATED - add WHOP secrets)" if m.get("whop_simulated") else ""
        lines.append(f"Whop Checkout URL: {m['whop_checkout_url']}{simulated}")
    if m.get("slide_paths"):
        slide_urls = [f"{public_base}/{Path(p).name}" if public_base else str(p) for p in m["slide_paths"]]
        lines.append("Carousel Slides:")
        lines.extend(f"  - {u}" for u in slide_urls)
        lines.append("")
    if engine == "b2b_agency":
        lines.append(f"Client: {m.get('client_name', 'N/A')} | Invoice: {m.get('invoice_id', 'N/A')} | Deposit Due: ${m.get('amount_due_usd', 0):,.2f}")
        for label, key in [("Call Summary", "ops_summary_path"), ("Client Proposal", "proposal_path"), ("Invoice JSON", "invoice_path")]:
            if m.get(key):
                fname = Path(m[key]).name
                lines.append(f"  - {label}: {public_base}/{fname}" if public_base else f"  - {label}: {m[key]}")
        lines.append("")

    # Published Receipts
    receipts = m.get("published_receipts", [])
    if receipts:
        lines.append("--- PUBLISHED RECEIPTS ---")
        for r in receipts:
            yt_id = r.get("youtube") or r.get("youtube_video_id")
            ig_id = r.get("instagram") or r.get("instagram_media_id")
            ig_car = r.get("instagram_carousel_id")
            if yt_id:
                lines.append(f"YouTube Shorts: https://youtube.com/shorts/{yt_id}")
            if ig_car:
                lines.append(f"Instagram Carousel Media ID: {ig_car}")
            elif ig_id:
                label = "Instagram Carousel Media ID" if engine == "carousel_funnel" else "Instagram Reel Media ID"
                lines.append(f"{label}: {ig_id}")
            if r.get("release_status"):
                lines.append(f"B2B Release: {r['release_status']} ({r.get('proposal_path', '')})")
        lines.append("")

    return subject, "\n".join(lines).strip() + "\n"


def send_gmail_report(
    subject: str,
    body_text: str,
    to_email: str | None = None,
    dry_run: bool = False,
) -> bool:
    """
    Sends a plain-text status report via Gmail SMTP SSL (smtp.gmail.com:465)
    using `COMPANY_GMAIL` and `GMAIL_APP_PASSWORD`.
    """
    sender = os.environ.get("COMPANY_GMAIL", "").strip()
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
    recipient = (to_email or os.environ.get("REPORT_TO_EMAIL", "")).strip() or sender

    if dry_run:
        log.info("[DRY-RUN] Gmail report prepared -> To: %s | Subject: %s", recipient or "unset", subject)
        return True

    if not sender or not app_password:
        log.info("COMPANY_GMAIL / GMAIL_APP_PASSWORD not set; skipping Gmail report.")
        return False

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body_text)

    last_exc: Exception | None = None
    # Try STARTTLS on port 587 first (more reliable on GitHub Actions/Azure runners), then SSL on port 465
    import ssl
    ctx = ssl.create_default_context()
    for mode in ("starttls_587", "ssl_465", "starttls_587_retry"):
        try:
            if mode.startswith("starttls_587"):
                with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
                    smtp.ehlo()
                    smtp.starttls(context=ctx)
                    smtp.ehlo()
                    smtp.login(sender, app_password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30, context=ctx) as smtp:
                    smtp.ehlo()
                    smtp.login(sender, app_password)
                    smtp.send_message(msg)
            log.info("Gmail report sent to %s via %s (%s)", recipient, mode, subject)
            return True
        except Exception as exc:
            last_exc = exc
            log.debug("Gmail SMTP (%s) failed: %s", mode, exc)
            time.sleep(1.5)
    log.warning("Failed to send Gmail report: %s", last_exc)
    return False


# ============================================================================
# 2. RATE LIMITING & LEDGER AUDIT TRAIL (`05_memory_ledger.json`)
# ============================================================================

def load_ledger(brain_dir: Path) -> tuple[dict[str, Any], Path]:
    brain_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = brain_dir / "05_memory_ledger.json"
    today_utc = time.strftime("%Y-%m-%d", time.gmtime())

    if not ledger_path.exists():
        default_data: dict[str, Any] = {
            "spend_date_utc": today_utc,
            "processed_items": [],
            "allowlisted_channels": [],
            "daily_spend_usd": 0.0,
            "daily_budget_cap_usd": 5.0,
            "publish_log": [],
            "history": [],
        }
        atomic_write_json(ledger_path, default_data)
        return default_data, ledger_path

    try:
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
    except Exception:
        data = {}

    if data.get("spend_date_utc") != today_utc:
        data["spend_date_utc"] = today_utc
        data["daily_spend_usd"] = 0.0

    data.setdefault("publish_log", [])
    return data, ledger_path


def check_platform_pacing(
    ledger_data: dict[str, Any],
    platform: str,
    max_daily_posts: int = 4,
    min_gap_hours: float = 4.0,
    skip_spacing_check: bool = False,
) -> None:
    now = time.time()
    rolling_24h = [
        entry for entry in ledger_data.get("publish_log", [])
        if entry.get("platform") == platform and (now - float(entry.get("timestamp", 0))) < 86400
    ]

    if len(rolling_24h) >= max_daily_posts:
        raise RuntimeError(
            f"RATE_LIMIT_GUARD: {platform} has already published {len(rolling_24h)}/{max_daily_posts} posts in the last 24h."
        )

    if not skip_spacing_check and rolling_24h:
        last_ts = max(float(e["timestamp"]) for e in rolling_24h)
        elapsed_hours = (now - last_ts) / 3600.0
        if elapsed_hours < min_gap_hours:
            wait_min = max(1, int((min_gap_hours - elapsed_hours) * 60))
            raise RuntimeError(
                f"SPACING_GUARD: Last {platform} post was {elapsed_hours:.2f}h ago (min gap {min_gap_hours}h). Retry in ~{wait_min}m."
            )


def record_publish_event(
    ledger_data: dict[str, Any],
    ledger_path: Path,
    platform: str,
    post_id: str,
    title_or_caption: str,
) -> None:
    ledger_data.setdefault("publish_log", []).append({
        "timestamp": int(time.time()),
        "platform": platform,
        "post_id": post_id,
        "title": title_or_caption[:80],
    })
    ledger_data["publish_log"] = ledger_data["publish_log"][-200:]
    atomic_write_json(ledger_path, ledger_data)


# ============================================================================
# 3. YOUTUBE DATA API v3 (`videos.insert` RESUMABLE UPLOAD)
# ============================================================================

def get_youtube_access_token() -> str:
    client_id = os.environ.get("YT_CLIENT_ID", "").strip()
    client_secret = os.environ.get("YT_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("YT_REFRESH_TOKEN", "").strip()
    if not (client_id and client_secret and refresh_token):
        raise EnvironmentError("Missing YT_CLIENT_ID, YT_CLIENT_SECRET, or YT_REFRESH_TOKEN environment variables.")

    payload = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")

    req = urllib.request.Request(
        YT_TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    raw, _ = urlopen_with_retry(req, timeout=30)
    data = json.loads(raw.decode("utf-8"))
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"Failed to refresh YouTube OAuth token: {data}")
    return str(token)


def upload_youtube_short(
    mp4_path: Path,
    title: str,
    description: str,
    contains_synthetic_media: bool = False,
    privacy_status: str = "public",
    dry_run: bool = False,
    is_short: bool = True,
) -> str:
    if not mp4_path.exists() or mp4_path.stat().st_size == 0:
        raise FileNotFoundError(f"YouTube MP4 missing or empty: {mp4_path}")

    file_size = mp4_path.stat().st_size
    if file_size > 256 * 1024 * 1024:
        raise ValueError(f"MP4 file exceeds 256MB safety cap ({file_size} bytes)")

    clean_title = re.sub(r"[<>]+", "", (title or "")).strip() or "Jagnor AI Video"
    if is_short and "#shorts" not in clean_title.lower():
        clean_title = f"{clean_title[:90].strip()} #Shorts"
    elif not is_short:
        clean_title = re.sub(r"\s*#shorts\b", "", clean_title, flags=re.IGNORECASE).strip() or "Jagnor AI Video"
    clean_title = clean_title[:100]
    clean_desc = re.sub(r"[<>]+", "", (description or "")).strip()[:4900]

    if dry_run:
        fake_id = f"yt_dryrun_{int(time.time())}"
        log.info("[DRY-RUN] YouTube Short uploaded: %s (%s)", clean_title, fake_id)
        return fake_id

    access_token = get_youtube_access_token()

    body_meta = {
        "snippet": {
            "title": clean_title,
            "description": clean_desc,
            "categoryId": "28",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": bool(contains_synthetic_media),
        },
    }
    meta_bytes = json.dumps(body_meta).encode("utf-8")

    init_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Length": str(file_size),
        "X-Upload-Content-Type": "video/mp4",
    }
    init_req = urllib.request.Request(
        YT_UPLOAD_INIT_URL,
        data=meta_bytes,
        headers=init_headers,
        method="POST",
    )
    _, resp_headers = urlopen_with_retry(init_req, timeout=60)
    upload_url = resp_headers.get("location")
    if not upload_url:
        raise RuntimeError("YouTube resumable init did not return a Location header.")

    with mp4_path.open("rb") as f:
        video_bytes = f.read()

    put_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Length": str(file_size),
        "Content-Type": "video/mp4",
    }
    put_req = urllib.request.Request(upload_url, data=video_bytes, headers=put_headers, method="PUT")
    put_raw, _ = urlopen_with_retry(put_req, timeout=300)
    resp_data = json.loads(put_raw.decode("utf-8"))
    video_id = resp_data.get("id")
    if not video_id:
        raise RuntimeError(f"YouTube upload returned no video ID: {resp_data}")
    log.info("Published YouTube Short: https://youtube.com/shorts/%s", video_id)
    return str(video_id)


# ============================================================================
# 4. INSTAGRAM GRAPH API v22.0 (`REELS` & `CAROUSEL` CONTAINERS)
# ============================================================================

def _ig_api_call(url: str, method: str = "GET", params: dict[str, Any] | None = None) -> dict[str, Any]:
    if method == "GET" and params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
        data = None
    elif params:
        data = urllib.parse.urlencode(params).encode("utf-8")
    else:
        data = None

    req = urllib.request.Request(url, data=data, method=method)
    raw, _ = urlopen_with_retry(req, timeout=60)
    return json.loads(raw.decode("utf-8"))


def check_ig_publishing_quota(ig_user_id: str, access_token: str, max_api_quota: int = 20) -> int:
    res = _ig_api_call(
        f"{IG_GRAPH_BASE}/{ig_user_id}/content_publishing_limit",
        method="GET",
        params={"fields": "quota_usage,config", "access_token": access_token},
    )
    items = res.get("data", [])
    usage = int(items[0].get("quota_usage", 0)) if items else 0
    log.info("Instagram Graph API rolling 24h quota_usage: %d", usage)
    if usage >= max_api_quota:
        raise RuntimeError(f"IG_QUOTA_GUARD: quota_usage={usage} exceeds safe threshold ({max_api_quota}).")
    return usage


def poll_ig_container_until_finished(
    container_id: str,
    access_token: str,
    max_attempts: int = 20,
    base_sleep_sec: float = 6.0,
) -> None:
    for attempt in range(1, max_attempts + 1):
        res = _ig_api_call(
            f"{IG_GRAPH_BASE}/{container_id}",
            method="GET",
            params={"fields": "status_code,status", "access_token": access_token},
        )
        code = res.get("status_code", "")
        log.info("IG container %s poll %d/%d -> status_code=%s", container_id, attempt, max_attempts, code)
        if code == "FINISHED":
            return
        if code in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"IG container {container_id} failed with status_code={code}: {res}")
        time.sleep(min(base_sleep_sec * (1.25 ** (attempt - 1)), 30.0))
    raise TimeoutError(f"IG container {container_id} did not reach FINISHED after {max_attempts} polls.")


def publish_instagram_reel(
    mp4_path: Path,
    caption: str,
    dry_run: bool = False,
) -> str:
    if not mp4_path.exists() or mp4_path.stat().st_size == 0:
        raise FileNotFoundError(f"Instagram Reel MP4 missing or empty: {mp4_path}")

    if dry_run:
        fake_id = f"ig_reel_dryrun_{int(time.time())}"
        log.info("[DRY-RUN] Instagram Reel published: %s (%s)", mp4_path.name, fake_id)
        return fake_id

    ig_user_id = os.environ.get("IG_USER_ID", "").strip()
    access_token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    public_base = _get_public_base_url()
    if not (ig_user_id and access_token and public_base):
        raise EnvironmentError("Missing IG_USER_ID, IG_ACCESS_TOKEN, or PUBLIC_VIDEO_BASE_URL.")

    check_ig_publishing_quota(ig_user_id, access_token)
    video_url = f"{public_base}/{urllib.parse.quote(mp4_path.name)}"
    wait_until_public(video_url)

    create_res = _ig_api_call(
        f"{IG_GRAPH_BASE}/{ig_user_id}/media",
        method="POST",
        params={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": (caption or "").strip()[:2150],
            "share_to_feed": "true",
            "access_token": access_token,
        },
    )
    container_id = str(create_res["id"])
    poll_ig_container_until_finished(container_id, access_token)

    pub_res = _ig_api_call(
        f"{IG_GRAPH_BASE}/{ig_user_id}/media_publish",
        method="POST",
        params={"creation_id": container_id, "access_token": access_token},
    )
    media_id = str(pub_res["id"])
    log.info("Published Instagram Reel media_id=%s", media_id)
    return media_id


def publish_instagram_carousel(
    slide_paths: list[Path],
    caption: str,
    dry_run: bool = False,
) -> str:
    if len(slide_paths) < 2 or len(slide_paths) > 10:
        raise ValueError(f"Instagram Carousel requires 2..10 slides, got {len(slide_paths)}")
    for sp in slide_paths:
        if not sp.exists() or sp.stat().st_size == 0:
            raise FileNotFoundError(f"Carousel slide missing or empty: {sp}")

    if dry_run:
        fake_id = f"ig_carousel_dryrun_{int(time.time())}"
        log.info("[DRY-RUN] Instagram Carousel (%d slides) published: %s", len(slide_paths), fake_id)
        return fake_id

    ig_user_id = os.environ.get("IG_USER_ID", "").strip()
    access_token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    public_base = _get_public_base_url()
    if not (ig_user_id and access_token and public_base):
        raise EnvironmentError("Missing IG_USER_ID, IG_ACCESS_TOKEN, or PUBLIC_VIDEO_BASE_URL.")

    check_ig_publishing_quota(ig_user_id, access_token)

    child_ids: list[str] = []
    for sp in slide_paths:
        img_url = f"{public_base}/{urllib.parse.quote(sp.name)}"
        wait_until_public(img_url)
        child_res = _ig_api_call(
            f"{IG_GRAPH_BASE}/{ig_user_id}/media",
            method="POST",
            params={
                "image_url": img_url,
                "is_carousel_item": "true",
                "access_token": access_token,
            },
        )
        cid = str(child_res["id"])
        poll_ig_container_until_finished(cid, access_token)
        child_ids.append(cid)

    parent_res = _ig_api_call(
        f"{IG_GRAPH_BASE}/{ig_user_id}/media",
        method="POST",
        params={
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "caption": (caption or "").strip()[:2150],
            "access_token": access_token,
        },
    )
    parent_id = str(parent_res["id"])
    poll_ig_container_until_finished(parent_id, access_token)

    pub_res = _ig_api_call(
        f"{IG_GRAPH_BASE}/{ig_user_id}/media_publish",
        method="POST",
        params={"creation_id": parent_id, "access_token": access_token},
    )
    media_id = str(pub_res["id"])
    log.info("Published Instagram Carousel media_id=%s", media_id)
    return media_id


# ============================================================================
# 5. MANIFEST ROUTER WITH PER-PLATFORM CHECKPOINTING
# ============================================================================

def _resolve_media_path(raw_path: str, public_dir: Path | None = None) -> Path:
    """Resolve media file path, falling back to public/<filename> for two-stage CI runs."""
    p = Path(raw_path)
    if p.exists():
        return p
    if public_dir is not None:
        candidate = public_dir / p.name
        if candidate.exists():
            log.info("Resolved %s via public_dir fallback -> %s", p, candidate)
            return candidate
    default_pub = Path("public") / p.name
    if default_pub.exists():
        log.info("Resolved %s via ./public fallback -> %s", p, default_pub)
        return default_pub
    return p


def process_manifest(
    manifest_path: Path,
    brain_dir: Path,
    approve_manifest: bool = False,
    platforms: set[str] = frozenset({"youtube", "instagram"}),
    max_daily_posts: int = 4,
    min_gap_hours: float = 4.0,
    skip_spacing_check: bool = False,
    apply_jitter: bool = False,
    dry_run: bool = False,
    public_dir: Path | None = None,
) -> dict[str, Any]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    def _save() -> None:
        # Dry-run must be side-effect free: no fake receipts in the manifest, so a later LIVE publish still runs.
        if not dry_run:
            atomic_write_json(manifest_path, manifest)

    def _record(platform: str, post_id: str, title_or_caption: str) -> None:
        # ...and no fake posts in the ledger, so test runs never consume the 4/day or 3.5h anti-ban budget.
        if not dry_run:
            record_publish_event(ledger_data, ledger_path, platform, post_id, title_or_caption)

    if approve_manifest and manifest.get("status") == "APPROVAL_PENDING":
        manifest["status"] = "APPROVED"
        manifest["approved_at"] = int(time.time())
        _save()
        log.info("Paperclip Human-Approval Gate passed -> manifest marked APPROVED.")

    status = manifest.get("status")
    if status == "PUBLISHED":
        log.info("Manifest %s is already PUBLISHED; skipping.", manifest_path)
        return manifest
    if status != "APPROVED":
        raise PermissionError(
            f"GOVERNANCE_GATE_BLOCKED: Manifest status is '{status}' (must be 'APPROVED' before publishing)."
        )

    if (
        manifest.get("script_source") == "template"
        and not dry_run
        and os.environ.get("ALLOW_TEMPLATE_PUBLISH", "").strip() != "1"
    ):
        raise ValueError(
            "SCRIPT_TEMPLATE_BLOCKED: every AI council provider failed and no verified facts were available, so the "
            "script is a generic placeholder. It was built but NOT published. Re-run the build once the AI keys/quota work."
        )

    ledger_data, ledger_path = load_ledger(brain_dir)
    engine = manifest.get("engine", "clipping")
    published_receipts: list[dict[str, Any]] = []

    if apply_jitter and not dry_run:
        jitter_sec = random.randint(0, 10 * 60)
        log.info("Applying anti-ban random jitter sleep: %d seconds...", jitter_sec)
        time.sleep(jitter_sec)

    if engine == "digital_product":
        if not manifest.get("qa_verified", False):
            raise ValueError("QA_GATE_BLOCKED: digital_product promo MP4 is not qa_verified.")
        if manifest.get("whop_simulated") and not dry_run:
            raise ValueError(
                "WHOP_NOT_CONFIGURED: the checkout link is a simulated placeholder. Add WHOP_API_KEY and "
                "WHOP_COMPANY_ID secrets and rebuild before publishing (a fake link must never go public)."
            )
        mp4_path = _resolve_media_path(manifest["promo_mp4_path"], public_dir)
        yt_title = manifest.get("yt_title", f"{manifest['product_title']} #Shorts")
        ig_caption = manifest.get("ig_caption", manifest["product_title"])
        checkout_url = manifest.get("whop_checkout_url", "")
        done_platforms: dict[str, str] = manifest.setdefault("published_platforms", {})

        if "youtube" in platforms and "youtube" not in done_platforms:
            check_platform_pacing(ledger_data, "youtube", max_daily_posts, min_gap_hours, skip_spacing_check)
            yt_id = upload_youtube_short(
                mp4_path,
                title=yt_title,
                description=f"{ig_caption}\n\nGet it here: {checkout_url}",
                contains_synthetic_media=False,
                dry_run=dry_run,
            )
            _record("youtube", yt_id, yt_title)
            done_platforms["youtube"] = yt_id
            _save()

        if "instagram" in platforms and "instagram" not in done_platforms:
            check_platform_pacing(ledger_data, "instagram", max_daily_posts, min_gap_hours, skip_spacing_check)
            ig_id = publish_instagram_reel(mp4_path, caption=ig_caption, dry_run=dry_run)
            _record("instagram", ig_id, ig_caption)
            done_platforms["instagram"] = ig_id
            _save()

        published_receipts.append({"item": manifest["product_title"], **done_platforms})

    elif engine in {"clipping", "ai_faceless", "raw_video_drop", "motion_story"}:
        clips = manifest.get("clips", [])
        if not clips:
            raise ValueError("No clips found in clipping manifest.")

        for clip in clips:
            if clip.get("published"):
                continue
            if not clip.get("qa_verified", False):
                raise ValueError(f"QA_GATE_BLOCKED: Clip {clip.get('clip_id')} failed qa_verified check.")

            mp4_path = _resolve_media_path(clip["mp4_path"], public_dir)
            is_long_form = bool(manifest.get("is_long_form")) or float(clip.get("duration_sec") or 0.0) > 59.5
            yt_title = clip.get("yt_title") or f"Highlight {clip['clip_id']}" + ("" if is_long_form else " #Shorts")
            ig_caption = clip.get("ig_caption") or "Key takeaway from today's episode. Full breakdown in bio."
            synthetic = bool(clip.get("contains_synthetic_media", False))
            clip_done: dict[str, str] = clip.setdefault("published_platforms", {})
            target_platforms = (platforms - {"instagram"}) if is_long_form else platforms

            if "youtube" in target_platforms and "youtube" not in clip_done:
                check_platform_pacing(ledger_data, "youtube", max_daily_posts, min_gap_hours, skip_spacing_check)
                yt_id = upload_youtube_short(
                    mp4_path,
                    title=yt_title,
                    description=ig_caption,
                    contains_synthetic_media=synthetic,
                    dry_run=dry_run,
                    is_short=not is_long_form,
                )
                _record("youtube", yt_id, yt_title)
                clip_done["youtube"] = yt_id
                _save()

            if "instagram" in target_platforms and "instagram" not in clip_done:
                check_platform_pacing(ledger_data, "instagram", max_daily_posts, min_gap_hours, skip_spacing_check)
                ig_id = publish_instagram_reel(mp4_path, caption=ig_caption, dry_run=dry_run)
                _record("instagram", ig_id, ig_caption)
                clip_done["instagram"] = ig_id
                _save()

            if not target_platforms:
                log.warning("No compatible publishing platforms active for %s (long-form 16:9 skips Instagram; connect YouTube to auto-post).", clip.get("clip_id"))
            elif target_platforms.issubset(clip_done.keys()):
                clip["published"] = True
            receipt = {"clip_id": clip["clip_id"], **clip_done}
            clip["receipt"] = receipt
            published_receipts.append(receipt)
            break

    elif engine == "carousel_funnel":
        slide_paths = [_resolve_media_path(p, public_dir) for p in (manifest.get("slide_jpg_paths") or manifest.get("slide_paths", []))]
        ig_caption = manifest.get("ig_caption", manifest.get("topic", ""))
        done_platforms = manifest.setdefault("published_platforms", {})
        if "instagram" in platforms and "instagram" not in done_platforms:
            check_platform_pacing(ledger_data, "instagram", max_daily_posts, min_gap_hours, skip_spacing_check)
            ig_id = publish_instagram_carousel(slide_paths, caption=ig_caption, dry_run=dry_run)
            _record("instagram", ig_id, ig_caption)
            done_platforms["instagram"] = ig_id
            _save()
        receipt_obj: dict[str, Any] = {"topic": manifest.get("topic"), **done_platforms}
        if "instagram" not in done_platforms:
            receipt_obj["note"] = "Carousel slides saved in public/ (connect IG_USER_ID & IG_ACCESS_TOKEN to auto-post)"
        published_receipts.append(receipt_obj)

    elif engine == "b2b_agency":
        published_receipts.append({
            "client_name": manifest.get("client_name"),
            "invoice_id": manifest.get("invoice_id"),
            "proposal_path": manifest.get("proposal_path"),
            "release_status": "CLEARED_FOR_CLIENT_DELIVERY",
        })

    if engine in {"clipping", "ai_faceless", "raw_video_drop", "motion_story"}:
        all_done = all(c.get("published", False) for c in manifest.get("clips", []))
    elif engine == "digital_product":
        all_done = platforms.issubset(manifest.get("published_platforms", {}).keys())
    elif engine == "carousel_funnel":
        all_done = ("instagram" not in platforms) or ("instagram" in manifest.get("published_platforms", {}))
    else:
        all_done = True

    if all_done:
        manifest["status"] = "PUBLISHED"
        manifest["published_at"] = int(time.time())
    manifest["published_receipts"] = published_receipts
    _save()
    return manifest


# ============================================================================
# 1. UNIVERSAL DATA STRUCTURES & COMPANY BRAIN (`brain/`)
# ============================================================================

@dataclass
class WordToken:
    word: str
    start: float
    end: float
    speaker: str = "SPEAKER_00"


@dataclass
class IndexedSegment:
    segment_id: int
    speaker: str
    start: float
    end: float
    text: str
    words: list[WordToken]


@dataclass
class ClipSpec:
    clip_id: str
    start_segment_id: int
    end_segment_id: int
    start_sec: float
    end_sec: float
    duration_sec: float
    mp4_path: str
    layout_mode: str
    qa_verified: bool
    yt_title: str = ""
    ig_caption: str = ""
    hook_overlay: str = ""
    council_score: float = 0.0
    council_models_used: list[str] = field(default_factory=list)
    contains_synthetic_media: bool = False
    source_url: str = ""


@dataclass
class CompanyBrain:
    brain_dir: Path
    spend_date_utc: str = ""
    identity_icp: str = ""
    brand_style: str = ""
    offers_pricing: str = ""
    sops_guardrails: str = ""
    processed_items: set[str] = field(default_factory=set)
    allowlisted_channels: set[str] = field(default_factory=set)
    daily_spend_usd: float = 0.0
    daily_budget_cap_usd: float = 5.0
    ledger_path: Path | None = None

    @classmethod
    def load(cls, brain_dir: Path | None) -> "CompanyBrain":
        today_utc = time.strftime("%Y-%m-%d", time.gmtime())
        if brain_dir is None:
            return cls(brain_dir=Path("."), spend_date_utc=today_utc)
        brain_dir.mkdir(parents=True, exist_ok=True)

        def _read_md(name: str, default: str) -> str:
            p = brain_dir / name
            if not p.exists():
                p.write_text(default, encoding="utf-8")
            return p.read_text(encoding="utf-8")

        icp = _read_md("01_identity_icp.md", "# Identity & ICP\nTarget high-value digital buyers and AI/tech enthusiasts.\n")
        style = _read_md("02_brand_style.md", "# Brand Style\nPrimary: #0F172A | Accent: #38BDF8 | Highlight: #FACC15\n")
        pricing = _read_md("03_offers_pricing.md", "# Offers & Pricing\n- Pro Bundle: $17\n- B2B Automation Retainer: $1,500\n")
        sops = _read_md("04_sops_guardrails.md", "# SOPs & Guardrails\nMax 4 posts/day. Human approval required before publish.\n")

        ledger_path = brain_dir / "05_memory_ledger.json"
        if not ledger_path.exists():
            default_ledger = {
                "spend_date_utc": today_utc,
                "processed_items": [],
                "allowlisted_channels": [],
                "daily_spend_usd": 0.0,
                "daily_budget_cap_usd": 5.0,
                "publish_log": [],
                "history": [],
            }
            atomic_write_json(ledger_path, default_ledger)

        try:
            data = json.loads(ledger_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}

        if data.get("spend_date_utc") != today_utc:
            data["spend_date_utc"] = today_utc
            data["daily_spend_usd"] = 0.0
            atomic_write_json(ledger_path, data)

        items = set(data.get("processed_items", [])) | set(data.get("processed_urls", []))
        return cls(
            brain_dir=brain_dir,
            spend_date_utc=today_utc,
            identity_icp=icp,
            brand_style=style,
            offers_pricing=pricing,
            sops_guardrails=sops,
            processed_items=items,
            allowlisted_channels=set(data.get("allowlisted_channels", [])),
            daily_spend_usd=float(data.get("daily_spend_usd", 0.0)),
            daily_budget_cap_usd=float(data.get("daily_budget_cap_usd", 5.0)),
            ledger_path=ledger_path,
        )

    def check_pre_flight(self, item_key: str, estimated_cost_usd: float = 0.10) -> None:
        if item_key in self.processed_items:
            raise ValueError(f"DEAD_LETTER: Item already processed in Company Brain ledger: {item_key}")
        if (self.daily_spend_usd + estimated_cost_usd) > self.daily_budget_cap_usd:
            raise RuntimeError(
                f"DEAD_LETTER: Budget cap exceeded (${self.daily_spend_usd:.2f} + ${estimated_cost_usd:.2f} > ${self.daily_budget_cap_usd:.2f})"
            )

    def record_completion(self, item_key: str, engine: str, cost_usd: float, summary: dict[str, Any]) -> None:
        today_utc = time.strftime("%Y-%m-%d", time.gmtime())
        if self.spend_date_utc != today_utc:
            self.spend_date_utc = today_utc
            self.daily_spend_usd = 0.0

        self.processed_items.add(item_key)
        self.daily_spend_usd = round(self.daily_spend_usd + cost_usd, 4)
        if self.ledger_path is None:
            return
        try:
            data = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        data["spend_date_utc"] = self.spend_date_utc
        data["processed_items"] = sorted(self.processed_items)
        data["allowlisted_channels"] = sorted(self.allowlisted_channels)
        data["daily_spend_usd"] = self.daily_spend_usd
        data["daily_budget_cap_usd"] = self.daily_budget_cap_usd
        data.setdefault("publish_log", [])
        history = list(data.get("history", []))
        history.append({
            "timestamp": int(time.time()),
            "engine": engine,
            "item_key": item_key,
            "cost_usd": cost_usd,
            "summary": summary,
        })
        data["history"] = history[-100:]
        atomic_write_json(self.ledger_path, data)


# ============================================================================
# 2. THE 4-BRAIN FREE AI COUNCIL (GEMINI -> GROQ -> NVIDIA NIM -> OPENROUTER)
# ============================================================================

ART_STYLE_PROMPTS: dict[str, str] = {
    "original": "preserve exact original source visual look and color grading, no artificial stylization",
    "dark_cinematic": "dark moody cinematic photography, dramatic rim lighting, ultra detailed 8k, shallow depth of field, no text",
    "anime": "high-budget Japanese anime art style, vibrant cel shading, dynamic cinematic lighting, Makoto Shinkai aesthetic, no text",
    "cyberpunk": "futuristic cyberpunk neon noir aesthetic, glowing cyan and magenta reflections, rain-slicked sci-fi lighting, ultra detailed, no text",
    "3d_pixar": "stylized 3D animated film still, Pixar lighting quality, expressive cinematic render, global illumination, no text",
    "comic_book": "bold graphic novel comic book illustration, inked outlines, dramatic halftone shading, vibrant high-contrast colors, no text",
    "minimalist_sketch": "clean editorial minimalist ink and charcoal sketch illustration on dark slate paper, gold accent highlights, modern aesthetic, no text",
    "oil_painting": "dramatic classical oil painting, rich visible brushstrokes, chiaroscuro lighting, museum masterpiece aesthetic, no text",
    "editorial_mascot": "clean bright modern editorial illustration, crisp cinematic framing, warm natural lighting, minimal clutter, no text",
}

FFMPEG_ART_STYLE_FILTERS: dict[str, str] = {
    "original": "",
    "dark_cinematic": "eq=contrast=1.10:brightness=-0.04:saturation=0.95,colorbalance=rs=-0.04:gs=0.01:bs=0.06",
    "anime": "hqdn3d=4:3:6:4.5,eq=contrast=1.12:saturation=1.35,unsharp=5:5:1.1:5:5:0.0",
    "cyberpunk": "eq=contrast=1.15:saturation=1.40,colorbalance=rs=0.06:gs=-0.05:bs=0.14:rh=0.10:bh=0.12",
    "3d_pixar": "hqdn3d=3:2:5:3,eq=contrast=1.08:brightness=0.03:saturation=1.28",
    "comic_book": "hqdn3d=5:4:6:5,eq=contrast=1.22:saturation=1.35,unsharp=7:7:1.4:7:7:0.0",
    "minimalist_sketch": "hue=s=0.15,eq=contrast=1.35:brightness=0.02,unsharp=5:5:1.2:5:5:0.0",
    "oil_painting": "hqdn3d=6:5:8:6,eq=contrast=1.10:saturation=1.25",
    "editorial_mascot": "eq=contrast=1.06:brightness=0.03:saturation=1.12",
}

STYLE_THEMES: dict[str, dict[str, Any]] = {
    "original": {
        "bg_top": (12, 18, 36), "bg_mid": (24, 38, 68), "bg_bot": (10, 14, 28),
        "accent": (245, 196, 81), "secondary": (56, 189, 248), "card_bg": (18, 26, 44),
        "card_text": (245, 248, 255), "border_w": 4, "frame_style": "clean",
    },
    "dark_cinematic": {
        "bg_top": (8, 12, 22), "bg_mid": (20, 32, 52), "bg_bot": (6, 8, 16),
        "accent": (245, 196, 81), "secondary": (96, 165, 250), "card_bg": (14, 18, 28),
        "card_text": (242, 244, 248), "border_w": 3, "frame_style": "letterbox",
    },
    "anime": {
        "bg_top": (24, 52, 118), "bg_mid": (148, 86, 146), "bg_bot": (242, 154, 124),
        "accent": (255, 232, 102), "secondary": (255, 116, 178), "card_bg": (24, 20, 48),
        "card_text": (255, 250, 255), "border_w": 6, "frame_style": "speedlines",
    },
    "cyberpunk": {
        "bg_top": (10, 4, 28), "bg_mid": (38, 10, 66), "bg_bot": (8, 26, 46),
        "accent": (0, 245, 255), "secondary": (255, 42, 157), "card_bg": (12, 8, 28),
        "card_text": (215, 252, 255), "border_w": 5, "frame_style": "scanlines",
    },
    "3d_pixar": {
        "bg_top": (28, 44, 96), "bg_mid": (74, 112, 178), "bg_bot": (36, 56, 102),
        "accent": (255, 214, 102), "secondary": (126, 224, 255), "card_bg": (26, 38, 72),
        "card_text": (255, 252, 245), "border_w": 6, "frame_style": "soft_glow",
    },
    "comic_book": {
        "bg_top": (184, 34, 44), "bg_mid": (236, 148, 36), "bg_bot": (28, 36, 64),
        "accent": (255, 230, 0), "secondary": (0, 208, 255), "card_bg": (252, 246, 222),
        "card_text": (18, 18, 22), "border_w": 10, "frame_style": "comic_panel",
    },
    "minimalist_sketch": {
        "bg_top": (28, 30, 34), "bg_mid": (42, 45, 52), "bg_bot": (22, 24, 28),
        "accent": (235, 204, 128), "secondary": (210, 214, 222), "card_bg": (244, 240, 232),
        "card_text": (26, 26, 30), "border_w": 3, "frame_style": "editorial_grid",
    },
    "oil_painting": {
        "bg_top": (48, 18, 22), "bg_mid": (108, 56, 36), "bg_bot": (24, 16, 18),
        "accent": (238, 192, 106), "secondary": (186, 118, 72), "card_bg": (240, 226, 196),
        "card_text": (38, 26, 18), "border_w": 7, "frame_style": "ornate_frame",
    },
    "editorial_mascot": {
        "bg_top": (248, 244, 236), "bg_mid": (244, 239, 230), "bg_bot": (238, 232, 222),
        "accent": (226, 88, 34), "secondary": (30, 34, 42), "card_bg": (255, 255, 255),
        "card_text": (28, 30, 36), "border_w": 4, "frame_style": "editorial_mascot",
    },
}

STORY_ACTIONS: tuple[str, ...] = (
    "cinematic_zoom_in",
    "dramatic_pull_back",
    "pan_left_to_right",
    "pan_right_to_left",
    "kinetic_stat_slam",
    "timeline_reveal",
    "quote_card_styled",
    "spotlight_drift",
    "pulse_beat_zoom",
    "focus_callout",
)


_CAMERA_DIRECTION_RE = re.compile(
    r"\bcamera\b|\bpulls? back\b|\bpull(?:s|ing)? out\b|\bzoom(?:s|ed|ing)? (?:in|out|back)\b|\bpans? (?:left|right|across|over)\b|"
    r"\bwatch (?:the )?screen\b|\bon[- ]screen\b|\bfades? (?:in|out|to)\b|\bcuts? to\b|\bas we (?:see|watch)\b|"
    r"\bwe (?:now )?see\b|\bthe (?:shot|frame|scene) (?:shifts|changes|opens)\b|\bscene \d\b",
    re.IGNORECASE,
)
_VISUAL_TEXT_RE = re.compile(
    r"\b(?:(?:neon|street|shop|store|road|wall|billboard|game|movie|film|brand|company)\s+)?"
    r"(?:signs?|signage|logos?|billboards?|posters?|text|lettering|letters?|captions?|titles?|words?|typography|banners?|labels?|storefronts?|"
    r"watermarks?|slogans?|headlines?|screens? showing)\b",
    re.IGNORECASE,
)
_GENERIC_STEP_LABELS = ["START", "SHIFT", "NOW"]
_CINEMATIC_ACTIONS = ("cinematic_zoom_in", "dramatic_pull_back", "pan_left_to_right", "pan_right_to_left",
                      "spotlight_drift", "pulse_beat_zoom", "focus_callout")


def _strip_camera_directions(narration: str) -> str:
    """Narration is spoken aloud by TTS, so visual/camera directions must never reach it."""
    text = " ".join(str(narration or "").split())
    sentences = re.split(r"(?<=[.!?])\s+", text)
    kept = [x for x in sentences if x and not _CAMERA_DIRECTION_RE.search(x)]
    return " ".join(kept).strip() if kept else text


def _clean_visual_prompt(prompt: str) -> str:
    """Image models garble lettering ('gand talet VI'); drop every request for signs/logos/text."""
    cleaned = re.sub(
        r"\b(?:reading|saying|that says|which says|spelling|spelled|inscribed|labell?ed|written|displaying|titled|named)\b[^,.;]*",
        "", str(prompt or ""), flags=re.IGNORECASE,
    )
    cleaned = _VISUAL_TEXT_RE.sub("", cleaned)
    cleaned = re.sub(r"\b(?:glowing|lit|illuminated|large|giant|huge)\s+(?=(?:on|over|above|behind|in|at)\b|,|$)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;])", r"\1", cleaned)
    cleaned = re.sub(r"(?:,\s*){2,}", ", ", cleaned).strip(" ,;")
    return cleaned or "cinematic atmospheric scene"


def _digits_grounded(label: str, evidence: str) -> bool:
    nums = re.findall(r"\d[\d,.]*", label or "")
    return bool(nums) and all(n.strip(",.") in evidence for n in nums)


def _sanitize_motion_scenes(scenes: list[dict[str, Any]], fact_brief: str) -> list[dict[str, Any]]:
    """Deterministic anti-hallucination pass: spoken-only narration, text-free visuals, and no stat/year
    on screen unless its digits appear in the Verified Fact Brief (or, for evergreen topics, in the narration)."""
    used = {str(sc.get("action")) for sc in scenes}
    for sc in scenes:
        sc["narration"] = _strip_camera_directions(sc.get("narration", ""))
        sc["visual_prompt"] = _clean_visual_prompt(sc.get("visual_prompt", ""))
        evidence = fact_brief if fact_brief.strip() else sc["narration"]
        if sc.get("stat_text") and not _digits_grounded(sc["stat_text"], evidence):
            sc["stat_text"] = ""
        steps = sc.get("timeline_steps") or []
        if any(re.search(r"\d{4}", str(x)) for x in steps) and not all(
            _digits_grounded(str(x), evidence) for x in steps if re.search(r"\d", str(x))
        ):
            sc["timeline_steps"] = list(_GENERIC_STEP_LABELS)
        act = str(sc.get("action"))
        bad = (
            (act == "kinetic_stat_slam" and not sc.get("stat_text"))
            or (act == "quote_card_styled" and fact_brief.strip())
        )
        if bad:
            used.discard(act)
            repl = next((a for a in _CINEMATIC_ACTIONS if a not in used), _CINEMATIC_ACTIONS[0])
            sc["action"] = repl
            used.add(repl)
    return scenes


_WORLD_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("space", ("space", "voyager", "planet", "planets", "mars", "orbit", "galaxy", "galaxies", "nasa", "isro", "spacex", "moon", "universe", "rocket", "telescope", "asteroid", "comet", "astronaut", "cosmos", "black hole", "nebula", "satellite", "supernova", "exoplanet", "solar system")),
    ("ocean", ("ocean", "oceans", "sea", "mariana", "trench", "submarine", "whale", "whales", "shark", "coral", "deep sea", "titanic", "shipwreck", "marine", "dolphin", "reef")),
    ("tech_ai", ("ai", "artificial intelligence", "agent", "agents", "robot", "robots", "code", "coding", "algorithm", "software", "tech", "cyber", "computer", "chip", "chips", "gpu", "openai", "chatgpt", "llm", "app", "startup", "internet", "quantum", "iphone", "android", "gaming", "game", "gta", "console", "hacker", "data")),
    ("finance", ("money", "stock", "stocks", "billion", "wealth", "finance", "crypto", "bitcoin", "business", "economy", "economic", "gold", "market", "markets", "bank", "inflation", "invest", "investing", "trading", "tax", "salary", "rich", "millionaire")),
    ("history_myth", ("myth", "mythology", "ramayan", "ramayana", "mahabharat", "hanuman", "king", "queen", "empire", "roman", "pyramid", "pyramids", "war", "ancient", "history", "historical", "god", "gods", "legend", "medieval", "dynasty", "pharaoh", "viking", "samurai", "temple", "battle", "revolution")),
]


def _classify_visual_world(low_ctx: str) -> str:
    """Whole-word keyword scoring (no substring accidents like 'ai' in 'rain' or 'sun' in 'sunday')."""
    text = f" {re.sub(r'[^a-z0-9]+', ' ', (low_ctx or '').lower())} "
    best, best_score = "nature", 0
    for world, kws in _WORLD_KEYWORDS:
        score = sum(1 for k in kws if f" {k} " in text)
        if score > best_score:
            best, best_score = world, score
    return best


def _brief_sentences(fact_brief: str, max_n: int = 5) -> list[str]:
    """Real, relevant sentences from the Verified Fact Brief (Wikipedia / trend text) for no-LLM fallbacks."""
    out: list[str] = []
    for line in (fact_brief or "").splitlines():
        line = re.sub(r"^(Background:|Wikipedia \([^)]*\):)\s*", "", line.strip(), flags=re.I)
        if not line or "headline only" in line.lower() or line.lower().startswith("trending"):
            continue
        for sent in re.split(r"(?<=[.!?])\s+", line):
            sent = re.sub(r"\s*\([^)]{0,80}\)", "", sent).strip()
            n = len(sent.split())
            if 6 <= n <= 30 and sent not in out:
                out.append(sent)
            if len(out) >= max_n:
                return out
    return out


def _honest_template_narrations(topic: str) -> list[str]:
    """Claim-free generic script used only when no AI draft and no fact brief exist (never auto-published)."""
    return [
        f"Here is what makes {topic} worth a closer look.",
        f"Start with the basics: what {topic} actually is and why people talk about it.",
        "Then look at what changed, and why it matters right now.",
        f"Here is the part about {topic} that most people overlook at first.",
        f"What is your take on {topic}? Share it in the comments.",
    ]


class RedTeamCriticRobot:
    """
    Dedicated Red-Team Critic & Decision Evaluator Specialist Robot:
    Stress-tests every Council script and every Engine's final deliverable BEFORE rendering/publishing,
    flags concrete defects, and forces immediate auto-repairs (or Board rewrites) without straying from instructions.
    """

    @staticmethod
    def audit_and_fix_script(
        pkg: dict[str, Any],
        topic: str,
        engine: str,
        fact_brief: str = "",
        is_long_form: bool = False,
        council: Any = None,
    ) -> dict[str, Any]:
        issues: list[str] = []
        fixes: list[str] = []

        # 1. Title & Packaging Audit
        yt_title = re.sub(r"[<>]+", "", str(pkg.get("yt_title") or "")).strip()
        if not yt_title or len(yt_title) < 8:
            issues.append("Weak or missing yt_title")
            yt_title = f"{topic[:72].strip()}" + ("" if is_long_form else " #Shorts")
            fixes.append("Rebuilt yt_title from topic")
        if is_long_form and "#shorts" in yt_title.lower():
            issues.append("Long-form 16:9 title leaked #Shorts tag")
            yt_title = re.sub(r"\s*#shorts\b", "", yt_title, flags=re.IGNORECASE).strip()
            fixes.append("Stripped #Shorts from 16:9 title")
        elif not is_long_form and "#shorts" not in yt_title.lower():
            issues.append("Short-form title missing #Shorts tag")
            yt_title = f"{yt_title[:88].strip()} #Shorts"
            fixes.append("Appended #Shorts to Shorts title")
        pkg["yt_title"] = yt_title[:100]

        # 2. Hook & Caption Audit
        hook = str(pkg.get("hook_overlay") or "").strip()
        if not hook or hook.lower() in {"watch this", "video", "short", "untitled"}:
            issues.append("Generic or empty hook_overlay")
            pkg["hook_overlay"] = " ".join(topic.split()[:5]).upper()[:42] or "MUST WATCH"
            fixes.append("Replaced generic hook_overlay with topic hook")

        ig_cap = str(pkg.get("ig_caption") or "").strip()
        if len(ig_cap) < 20:
            issues.append("IG caption too short")
            pkg["ig_caption"] = f"{topic} — key breakdown. Follow for daily insights! #AI #Facts"
            fixes.append("Expanded ig_caption with topic + CTA")

        # 3. Scene-level Audit (for motion_story / ai_faceless)
        scenes = pkg.get("scenes")
        if isinstance(scenes, list) and scenes:
            seen_narrs: set[str] = set()
            for idx, sc in enumerate(scenes):
                if not isinstance(sc, dict):
                    continue
                nr = _strip_camera_directions(str(sc.get("narration") or "").strip())
                if re.search(r"\b(TBD|TODO|Lorem ipsum|\[insert)\b", nr, re.I):
                    issues.append(f"Scene {idx+1} contained placeholder text")
                    nr = f"Here is the key fact about {topic}."
                    fixes.append(f"Replaced placeholder in Scene {idx+1}")
                norm_nr = nr.lower()
                if norm_nr in seen_narrs and idx > 0:
                    issues.append(f"Scene {idx+1} duplicated earlier narration")
                    nr = f"And here is what most people miss about {topic}: {nr}"
                    fixes.append(f"Differentiated duplicate Scene {idx+1}")
                seen_narrs.add(norm_nr)
                sc["narration"] = nr
                vp = _clean_visual_prompt(str(sc.get("visual_prompt") or f"{topic} scene"))
                if not vp:
                    vp = f"cinematic view of {topic}"
                    fixes.append(f"Restored visual_prompt in Scene {idx+1}")
                sc["visual_prompt"] = vp

            # Optional 1-shot Board rewrite ONLY if script fell back to generic template & council has budget
            if pkg.get("script_source") == "template" and council is not None and getattr(council, "_budget_left", lambda *_: False)(True):
                issues.append("Script used generic template fallback")
                rewrite_raw = council.invoke_stage(
                    "groq",
                    "You are a Red-Team Critic rewriting a weak template script into 5 sharp, topic-accurate scenes. Output ONLY strict JSON.",
                    f"Topic: {topic}\nFact Brief: {fact_brief or 'Use undisputed general facts only'}\n"
                    'Output ONLY JSON: {"yt_title": str, "hook_overlay": str, "ig_caption": str, '
                    '"scenes": [{"narration": str, "visual_prompt": str, "stock_keywords": str}]}',
                    final_pass=True,
                )
                rewritten = council._extract_json_dict(rewrite_raw) if hasattr(council, "_extract_json_dict") else None
                if isinstance(rewritten, dict) and isinstance(rewritten.get("scenes"), list) and len(rewritten["scenes"]) >= 3:
                    for k, rsc in enumerate(rewritten["scenes"][:len(scenes)]):
                        if isinstance(rsc, dict) and str(rsc.get("narration") or "").strip():
                            scenes[k]["narration"] = _strip_camera_directions(str(rsc["narration"]).strip())
                            scenes[k]["visual_prompt"] = _clean_visual_prompt(str(rsc.get("visual_prompt") or scenes[k]["visual_prompt"]))
                            if rsc.get("stock_keywords"):
                                scenes[k]["stock_keywords"] = str(rsc["stock_keywords"])[:40].strip()
                    pkg["script_source"] = "red_team_rewritten"
                    fixes.append("Forced Board rewrite from template to topic-specific script")

        pkg["red_team_audit"] = {
            "stage": "pre_render_script",
            "engine": engine,
            "verdict": "FIXED" if fixes else "PASS",
            "issues_found": issues,
            "fixes_applied": fixes,
        }
        if fixes:
            log.info("Red-Team Critic [%s]: flagged %d issue(s) -> auto-fixed (%s)", engine, len(issues), "; ".join(fixes[:3]))
        else:
            log.info("Red-Team Critic [%s]: script audit PASS (0 defects).", engine)
        return pkg

    @staticmethod
    def audit_manifest(manifest: dict[str, Any], engine: str, public_dir: Path | None = None) -> dict[str, Any]:
        """Post-build Red-Team Critic check across all 7 engines before APPROVAL_PENDING."""
        issues: list[str] = []
        fixes: list[str] = []
        prior = manifest.get("red_team_audit") if isinstance(manifest.get("red_team_audit"), dict) else {}
        if prior:
            issues.extend(prior.get("issues_found") or [])
            fixes.extend(prior.get("fixes_applied") or [])

        if engine in {"motion_story", "ai_faceless", "clipping", "raw_video_drop"}:
            clips = manifest.get("clips") or []
            if not clips:
                raise ValueError(f"RED_TEAM_BLOCKED [{engine}]: 0 clips produced.")
            for c in clips:
                raw_mp = str(c.get("mp4_path") or "").strip()
                mp = _resolve_media_path(raw_mp, public_dir) if raw_mp else Path("__missing__")
                if not raw_mp or not mp.is_file() or mp.stat().st_size < 10000:
                    raise ValueError(f"RED_TEAM_BLOCKED [{engine}]: output MP4 missing/corrupt ({mp}).")
                if not c.get("qa_verified", False):
                    raise ValueError(f"RED_TEAM_BLOCKED [{engine}]: clip {c.get('clip_id')} failed QA verification.")
                if not str(c.get("yt_title") or "").strip():
                    c["yt_title"] = f"Jagnor {engine} Update #Shorts"
                    issues.append("Clip missing yt_title")
                    fixes.append("Auto-populated clip yt_title")
        elif engine == "carousel_funnel":
            slides = manifest.get("slide_jpg_paths") or manifest.get("slide_paths") or []
            if len(slides) < 2:
                raise ValueError(f"RED_TEAM_BLOCKED [carousel_funnel]: requires >=2 slides, got {len(slides)}.")
            for sp_raw in slides:
                sp_s = str(sp_raw or "").strip()
                sp = _resolve_media_path(sp_s, public_dir) if sp_s else Path("__missing__")
                if not sp_s or not sp.is_file() or sp.stat().st_size == 0:
                    raise ValueError(f"RED_TEAM_BLOCKED [carousel_funnel]: slide missing/empty ({sp}).")
        elif engine == "digital_product":
            raw_z = str(manifest.get("zip_path") or "").strip()
            raw_p = str(manifest.get("promo_mp4_path") or "").strip()
            zp = _resolve_media_path(raw_z, public_dir) if raw_z else Path("__missing__")
            pp = _resolve_media_path(raw_p, public_dir) if raw_p else Path("__missing__")
            if not raw_z or not raw_p or not zp.is_file() or not pp.is_file() or not manifest.get("qa_verified", False):
                raise ValueError("RED_TEAM_BLOCKED [digital_product]: product ZIP or QA-verified promo MP4 missing.")
        elif engine == "b2b_agency":
            for k in ("ops_summary_path", "proposal_path", "invoice_path"):
                raw_f = str(manifest.get(k) or "").strip()
                fp = _resolve_media_path(raw_f, public_dir) if raw_f else Path("__missing__")
                if not raw_f or not fp.is_file() or fp.stat().st_size == 0:
                    raise ValueError(f"RED_TEAM_BLOCKED [b2b_agency]: missing deliverable {k}.")

        manifest["red_team_audit"] = {
            "stage": "post_build_manifest",
            "engine": engine,
            "verdict": "FIXED" if fixes else "PASS",
            "issues_found": issues,
            "fixes_applied": fixes,
        }
        log.info("Red-Team Critic [%s]: post-build verdict=%s (issues=%d, fixes=%d)", engine, manifest["red_team_audit"]["verdict"], len(issues), len(fixes))
        return manifest


class AICouncil:
    """
    Executive Board of Directors (4 Free-Tier Specialist Directors + Adaptive Failover):
      Director 1 (Gemini)     : Chief Story & Fact Architect (grounded facts, visual-verbal sync)
      Director 2 (Groq)       : VP of Retention & Pacing (3-second hook, tension, dialogue rhythm)
      Director 3 (NVIDIA NIM) : Chief Growth & Packaging Officer (high-CTR titles, SEO, hashtags)
      Chair      (OpenRouter) : Board Chair & Quality Auditor (cross-examines all 3 directors, resolves conflicts)
    """

    def __init__(self) -> None:
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.groq_key = os.environ.get("GROQ_API_KEY", "").strip()
        self.nvidia_key = os.environ.get("NVIDIA_API_KEY", "").strip()
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        self.models_called: list[str] = []
        # Hard wall-clock budget for ALL LLM calls in one run so dead/slow free APIs can never
        # push the GitHub job past its 35-minute timeout (every caller has a deterministic fallback).
        self.time_budget_sec = float(os.environ.get("COUNCIL_TIME_BUDGET_SEC", "240"))
        self._started = time.monotonic()

    def _budget_left(self, final_pass: bool = False) -> bool:
        # The last-resort JSON pass gets a small extra reserve so one slow provider can never force the generic template.
        limit = self.time_budget_sec + (90.0 if final_pass else 0.0)
        return (time.monotonic() - self._started) < limit

    def _call_openai_compatible(
        self,
        url: str,
        api_key: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        extra_headers: dict[str, str] | None = None,
        timeout: int = 30,
        max_attempts: int = 2,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "curl/8.18.0",
            **(extra_headers or {}),
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.35,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        raw, _ = urlopen_with_retry(req, timeout=timeout, max_attempts=max_attempts)
        data = json.loads(raw.decode("utf-8"))
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError(f"Empty choices from {url} ({model}): {data}")
        raw_msg = str((choices[0].get("message") or {}).get("content") or "")
        cleaned_msg = re.sub(r"<think>.*?</think>", "", raw_msg, flags=re.S | re.IGNORECASE).strip()
        if not cleaned_msg:
            raise RuntimeError(f"Empty content from {url} ({model})")
        return cleaned_msg

    def _call_gemini_native(self, system_prompt: str, user_prompt: str) -> str:
        primary_model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
        queue_models = list(dict.fromkeys([primary_model, "gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite"]))
        tried: set[str] = set()
        last_err = ""
        while queue_models:
            model = queue_models.pop(0)
            if not model or model in tried:
                continue
            tried.add(model)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": user_prompt}]}],
                "generationConfig": {"temperature": 0.35},
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.gemini_key,
                    "User-Agent": "curl/8.18.0",
                },
                method="POST",
            )
            try:
                raw, _ = urlopen_with_retry(req, timeout=45, max_attempts=2)
                data = json.loads(raw.decode("utf-8"))
                candidates = data.get("candidates") or []
                if candidates:
                    parts = (candidates[0].get("content") or {}).get("parts") or []
                    text_parts = [str(p.get("text") or "") for p in parts if isinstance(p, dict) and p.get("text") and not p.get("thought")]
                    if not text_parts:
                        text_parts = [str(p.get("text") or "") for p in parts if isinstance(p, dict) and p.get("text")]
                    joined = "\n".join(text_parts).strip()
                    if joined:
                        return joined
                    last_err = f"{model}: empty/filtered candidate"
            except Exception as exc:
                err_s = str(exc)
                last_err = f"{model}: {err_s[:180]}"
                m_hint = re.search(r"use models/([a-zA-Z0-9._-]+)", err_s)
                if m_hint and m_hint.group(1) not in tried:
                    queue_models.insert(0, m_hint.group(1))
                log.debug("Gemini model %s attempt failed: %s", model, exc)
                continue
        raise RuntimeError(f"All native Gemini model endpoints failed ({last_err}).")

    def _call_groq_native(self, system_prompt: str, user_prompt: str) -> str:
        """Calls Groq's ultra-fast free-tier OpenAI-compatible endpoint (`GROQ_API_KEY`)."""
        primary_model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        last_err = ""
        for g_model in dict.fromkeys([primary_model, "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "openai/gpt-oss-20b"]):
            try:
                return self._call_openai_compatible(
                    "https://api.groq.com/openai/v1/chat/completions",
                    self.groq_key,
                    g_model,
                    system_prompt,
                    user_prompt,
                )
            except Exception as exc:
                last_err = f"{g_model}: {str(exc)[:180]}"
                log.debug("Groq model %s attempt failed: %s", g_model, exc)
                continue
        raise RuntimeError(f"All native Groq model endpoints failed ({last_err}).")

    def _call_nvidia_native(self, system_prompt: str, user_prompt: str) -> str:
        """Calls NVIDIA NIM OpenAI-compatible endpoint (`NVIDIA_API_KEY`)."""
        nv_url = os.environ.get("NVIDIA_API_URL", "https://integrate.api.nvidia.com/v1/chat/completions").strip()
        primary_model = os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")
        fallback_models = [
            primary_model,
            "meta/llama-3.3-70b-instruct",
            "meta/llama-3.1-70b-instruct",
            "qwen/qwen2.5-72b-instruct",
        ]
        for nv_model in list(dict.fromkeys(fallback_models))[:3]:
            try:
                return self._call_openai_compatible(
                    nv_url,
                    self.nvidia_key,
                    nv_model,
                    system_prompt,
                    user_prompt,
                    timeout=25,
                    max_attempts=1,
                )
            except Exception as exc:
                log.debug("NVIDIA NIM model %s attempt failed: %s", nv_model, exc)
                continue
        raise RuntimeError("All native NVIDIA NIM model endpoints failed.")

    def invoke_stage(self, provider: str, system_prompt: str, user_prompt: str, final_pass: bool = False) -> str | None:
        if not self._budget_left(final_pass):
            log.warning("AI Council time budget (%.0fs) exhausted; skipping [%s] stage and using deterministic fallback.", self.time_budget_sec, provider)
            return None
        openrouter_candidates = {
            "gemini": ["openrouter/free", "google/gemini-2.0-flash-exp:free"],
            "groq": ["meta-llama/llama-3.3-70b-instruct:free", "openrouter/free"],
            "nvidia": ["openrouter/free", "meta-llama/llama-3.3-70b-instruct:free"],
            "openrouter": [os.environ.get("OPENROUTER_JUDGE_MODEL", "openrouter/free"), "meta-llama/llama-3.3-70b-instruct:free"],
        }

        try:
            if provider == "gemini" and self.gemini_key:
                res = self._call_gemini_native(system_prompt, user_prompt)
                self.models_called.append("gemini-native")
                return res
            if provider == "groq" and self.groq_key:
                res = self._call_groq_native(system_prompt, user_prompt)
                self.models_called.append("groq-native")
                return res
            if provider == "nvidia" and self.nvidia_key:
                res = self._call_nvidia_native(system_prompt, user_prompt)
                self.models_called.append("nvidia-nim-native")
                return res
        except Exception as native_exc:
            log.warning("Native [%s] API failed (%s); falling back to OpenRouter if configured...", provider, native_exc)

        if self.openrouter_key and self._budget_left(final_pass):
            for or_model in dict.fromkeys(openrouter_candidates.get(provider, ["openrouter/free", "meta-llama/llama-3.3-70b-instruct:free"])):
                try:
                    res = self._call_openai_compatible(
                        "https://openrouter.ai/api/v1/chat/completions",
                        self.openrouter_key,
                        or_model,
                        system_prompt,
                        user_prompt,
                        extra_headers={
                            "HTTP-Referer": "https://github.com/jagnor110-cell",
                            "X-Title": "Jagnor Free AI Council",
                        },
                    )
                    self.models_called.append(f"openrouter:{or_model}")
                    return res
                except Exception as or_exc:
                    log.debug("OpenRouter model %s failed (%s); trying next...", or_model, or_exc)
                    continue

        # Adaptive human-like failover: if the assigned provider & OpenRouter both failed,
        # route to the next healthy free-tier provider so the council never stalls.
        for alt_prov, key_val, fn in (
            ("groq", self.groq_key, self._call_groq_native),
            ("gemini", self.gemini_key, self._call_gemini_native),
            ("nvidia", self.nvidia_key, self._call_nvidia_native),
        ):
            if alt_prov == provider or not key_val or not self._budget_left(final_pass):
                continue
            try:
                res = fn(system_prompt, user_prompt)
                self.models_called.append(f"{alt_prov}-failover")
                log.info("Council adaptive failover: [%s] -> [%s] succeeded.", provider, alt_prov)
                return res
            except Exception as alt_exc:
                log.debug("Failover provider %s failed (%s)", alt_prov, alt_exc)
                continue

        return None

    @staticmethod
    def _has_scenes(d: dict[str, Any] | None) -> bool:
        if not isinstance(d, dict) or not isinstance(d.get("scenes"), list):
            return False
        good = [x for x in d["scenes"] if isinstance(x, dict) and str(x.get("narration") or "").strip()]
        return len(good) >= 3

    @staticmethod
    def _board_audit_scenes(scenes: list[dict[str, Any]], topic: str, dialogue_mode: bool = False) -> list[dict[str, Any]]:
        """Board Chair post-check: ensures Scene 1 anchors the exact topic, every scene has clean spoken pacing, and specialist roles alternate."""
        if not scenes:
            return scenes
        topic_words = [w for w in re.findall(r"[A-Za-z0-9]{3,}", topic) if w.lower() not in {"the", "and", "for", "with", "that", "this", "how", "why"}]
        s0_narr = str(scenes[0].get("narration") or "").strip()
        if topic_words and not any(w.lower() in s0_narr.lower() for w in topic_words[:3]):
            if not re.search(r"[\u0D00-\u0D7F\u0900-\u097F]", s0_narr):  # preserve non-Latin scripts cleanly
                scenes[0]["narration"] = f"{topic}: {s0_narr}".strip()
        if dialogue_mode:
            # Ensure specialist roles (`host`=Anchor, `guest`=Skeptic, `bot`=Analyst) actually alternate & match specialist tone
            roles = ("host", "guest", "bot")
            all_same = len({str(s.get("speaker") or "").strip().lower() for s in scenes}) <= 1
            prev_sp = ""
            for idx, sc in enumerate(scenes):
                sp = str(sc.get("speaker") or "").strip().lower()
                if all_same or sp not in roles or sp == prev_sp:
                    sp = roles[idx % 3] if roles[idx % 3] != prev_sp else roles[(idx + 1) % 3]
                sc["speaker"] = sp
                prev_sp = sp
                if sp == "guest" and not sc.get("emotion"):
                    sc["emotion"] = "skeptical"
                elif sp == "bot" and not sc.get("emotion"):
                    sc["emotion"] = "explaining"
        return scenes

    def _resolve_script_json(self, outputs: list[str | None], judge_prompt: str) -> dict[str, Any]:
        """
        Pick the first council output that is real JSON WITH scenes (judge first, then drafts). If none, ask Groq then
        Gemini to convert the drafts into JSON. Metadata-only dicts never block a later draft that has the scenes.
        """
        dicts = [self._extract_json_dict(o) for o in outputs]
        for d in dicts:
            if self._has_scenes(d):
                return d  # type: ignore[return-value]
        for fb_provider in ("groq", "gemini"):
            fb_out = self.invoke_stage(
                fb_provider,
                "Convert the drafts into strict valid JSON ONLY. No markdown fences, no commentary.",
                judge_prompt,
                final_pass=True,
            )
            fb = self._extract_json_dict(fb_out)
            if self._has_scenes(fb):
                return fb  # type: ignore[return-value]
        return next((d for d in dicts if d), {})

    @staticmethod
    def _extract_json_dict(raw_text: str | None) -> dict[str, Any] | None:
        if not raw_text:
            return None
        no_think = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.S | re.IGNORECASE)
        cleaned = re.sub(r"```(?:json)?", "", no_think, flags=re.IGNORECASE).replace("```", "").strip()
        decoder = json.JSONDecoder()

        def _scan(text: str) -> tuple[list[dict[str, Any]], list[Any] | None]:
            found_dicts: list[dict[str, Any]] = []
            first_list: list[Any] | None = None
            idx = 0
            while idx < len(text):
                if text[idx] in {"{", "["}:
                    try:
                        obj, end = decoder.raw_decode(text[idx:])
                    except Exception:
                        idx += 1
                        continue
                    if isinstance(obj, dict):
                        found_dicts.append(obj)
                    elif isinstance(obj, list) and first_list is None and any(isinstance(x, dict) for x in obj):
                        first_list = obj
                    idx += max(end, 1)
                    continue
                idx += 1
            return found_dicts, first_list

        found_dicts, first_list = _scan(cleaned)
        if not found_dicts and first_list is None:
            no_trailing = re.sub(r",\s*([}\]])", r"\1", cleaned)
            if no_trailing != cleaned:
                found_dicts, first_list = _scan(no_trailing)

        if found_dicts:
            priority_keys = ("scenes", "clips", "points", "slides", "proposal_md")
            for d in found_dicts:
                if any(k in d for k in priority_keys):
                    return d
            return max(found_dicts, key=lambda d: len(d))
        if first_list is not None:
            if any(isinstance(x, dict) and "narration" in x for x in first_list):
                return {"scenes": first_list}
            return {"clips": first_list}
        return None

    @staticmethod
    def _clamp_window_to_valid_duration(
        s_id: int,
        e_id: int,
        seg_map: dict[int, IndexedSegment],
        min_dur: float = 12.0,
        max_dur: float = 58.0,
    ) -> tuple[int, int] | None:
        if not seg_map:
            return None
        all_ids = sorted(seg_map.keys())
        s_id = max(all_ids[0], min(s_id, all_ids[-1]))
        e_id = max(s_id, min(e_id, all_ids[-1]))
        if s_id not in seg_map:
            s_id = min(all_ids, key=lambda k: abs(k - s_id))
        if e_id not in seg_map:
            e_id = min(all_ids, key=lambda k: abs(k - e_id))
        if e_id < s_id:
            e_id = s_id

        while e_id > s_id and (seg_map[e_id].end - seg_map[s_id].start) > max_dur:
            e_id -= 1
            while e_id > s_id and e_id not in seg_map:
                e_id -= 1

        while e_id < all_ids[-1] and (seg_map[e_id].end - seg_map[s_id].start) < min_dur:
            next_id = e_id + 1
            while next_id <= all_ids[-1] and next_id not in seg_map:
                next_id += 1
            if next_id > all_ids[-1]:
                break
            if (seg_map[next_id].end - seg_map[s_id].start) > max_dur:
                break
            e_id = next_id

        return s_id, e_id

    def dispatch_department(
        self,
        brain: CompanyBrain,
        inbox_dir: Path,
        theme: str = "Universal Storytelling",
        url: str = "",
        explicit_title: str = "",
        notes: str = "",
    ) -> tuple[str, str]:
        """
        Executive Board Dispatcher (when `--engine auto`):
        1) Deterministic priority checks first (zero wasted LLM calls):
           - Explicit URL -> `clipping`
           - Unprocessed MP4/MOV in `inbox_videos/` -> `raw_video_drop`
           - Active mid-arc 3-day series -> continues `active_series["engine"]`
        2) Otherwise balances recent department history from ledger + 1 fast Director call
           to pick the highest-value department (`motion_story`, `ai_faceless`, `carousel_funnel`).
        """
        if (url or "").strip():
            return "clipping", "Explicit source URL provided"

        if inbox_dir.exists():
            unprocessed = [
                f for f in sorted(inbox_dir.iterdir())
                if f.is_file() and f.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"}
                and f"raw_drop:{f.name}" not in brain.processed_items
            ]
            if unprocessed:
                return "raw_video_drop", f"Found unprocessed inbox video: {unprocessed[0].name}"

        ledger_dir = brain.ledger_path.parent if brain.ledger_path else brain.brain_dir
        ledger_data, _ = load_ledger(ledger_dir)
        cur_series = ledger_data.get("active_series")
        if (
            isinstance(cur_series, dict)
            and cur_series.get("base_topic")
            and int(cur_series.get("day", 0)) < int(cur_series.get("max_days", 1))
            and cur_series.get("engine") in {"motion_story", "ai_faceless"}
        ):
            return str(cur_series["engine"]), f"Continuing active series ({cur_series.get('base_topic')})"

        recent_engines = [
            str(item.split(":", 1)[0])
            for item in list(brain.processed_items)[-6:]
            if ":" in str(item)
        ]
        # Deterministic rotation fallback so no department is starved
        rotation = ("motion_story", "ai_faceless", "carousel_funnel")
        last_eng = next((e for e in reversed(recent_engines) if e in rotation), "")
        fallback_eng = rotation[(rotation.index(last_eng) + 1) % len(rotation)] if last_eng in rotation else "motion_story"

        prompt = (
            f"Theme: {theme}\nTitle/Topic: {explicit_title or '(auto-trending)'}\nNotes: {notes or '(none)'}\n"
            f"Recent engines run: {recent_engines or ['none']}\n"
            "Pick the SINGLE best department engine for today's automated release from: "
            "[motion_story, ai_faceless, carousel_funnel]. "
            "Prefer `motion_story` for narrative/dialogue explainers, `ai_faceless` for visual stock-video hooks, "
            "and `carousel_funnel` if bullet-point notes are provided or to balance recent video runs. "
            'Output ONLY JSON: {"engine": str, "reason": str}'
        )
        raw = self.invoke_stage(
            "groq",
            "You are the Executive Board Dispatcher. Pick the best department engine as strict JSON only.",
            prompt,
        )
        parsed = self._extract_json_dict(raw) or {}
        chosen = str(parsed.get("engine") or "").strip().lower()
        if chosen in rotation:
            return chosen, str(parsed.get("reason") or "Board strategic selection")[:120]
        return fallback_eng, f"Deterministic department rotation (after {last_eng or 'none'})"

    def run_6_brain_clip_council(
        self,
        segments: list[IndexedSegment],
        brain: CompanyBrain,
        max_clips: int = 3,
    ) -> list[dict[str, Any]]:
        """Runs the 4-Brain Free AI Council (Gemini -> Groq -> NVIDIA NIM -> OpenRouter) for clipping."""
        deterministic_windows = select_candidate_windows(segments, max_clips=max_clips)
        if not deterministic_windows:
            return []

        seg_map = {s.segment_id: s for s in segments}
        transcript_digest = "\n".join(
            f"[{s.segment_id}] ({s.start:.1f}s..{s.end:.1f}s) {s.text}"
            for s in segments[:180]
        )

        # Stage 1: GEMINI — Hook Window Discovery
        gemini_out = self.invoke_stage(
            "gemini",
            "You are Stage 1 (Gemini Hook Analyst) in a 4-AI free video clipping council. Pick high-retention 30-55s segment ranges by integer segment_id.",
            f"Brand ICP:\n{brain.identity_icp}\n\nIndexed Transcript:\n{transcript_digest}\n\n"
            f"Propose up to {max_clips} clip windows as JSON: {{\"clips\": [{{\"start_segment_id\": int, \"end_segment_id\": int, \"reason\": str}}]}}",
        )

        # Stage 2: GROQ — Narrative Pacing, Viral 3-Second Hook & Instagram Caption
        groq_out = self.invoke_stage(
            "groq",
            "You are Stage 2 (Groq Viral Director). Refine the windows to start on a bold hook sentence and end cleanly (30-55s), adding a <=6-word ALL-CAPS `hook_overlay` and an engaging `ig_caption` (no raw URLs).",
            f"Brand Style:\n{brain.brand_style}\n\nTranscript:\n{transcript_digest}\n\nGemini Proposal:\n{gemini_out or json.dumps(deterministic_windows)}\n\n"
            "Return JSON with start_segment_id, end_segment_id, hook_overlay, and ig_caption.",
        )

        # Stage 3: NVIDIA NIM — YouTube Shorts High-CTR Title, SEO & Hashtags
        nvidia_out = self.invoke_stage(
            "nvidia",
            "You are Stage 3 (NVIDIA Nemotron Title & Retention Polisher). Add a high-CTR `yt_title` (<=60 chars including #Shorts), tighten `hook_overlay`, and add 3 niche hashtags to `ig_caption`.",
            f"Groq Draft:\n{groq_out or gemini_out or json.dumps(deterministic_windows)}\n\n"
            "Return JSON preserving start_segment_id and end_segment_id with polished hook_overlay, yt_title, and ig_caption.",
        )

        # Stage 4: OPENROUTER — Chief Consensus Judge & Final Schema Validator
        judge_out = self.invoke_stage(
            "openrouter",
            "You are Stage 4 (OpenRouter Chief Consensus Judge). Merge all 3 AI drafts into final strict JSON.",
            f"Gemini:\n{gemini_out}\nGroq:\n{groq_out}\nNVIDIA NIM:\n{nvidia_out}\n\n"
            "Output ONLY valid JSON: {\"clips\": [{\"start_segment_id\": int, \"end_segment_id\": int, "
            "\"hook_overlay\": str, \"yt_title\": str, \"ig_caption\": str, \"council_score\": float}]}",
        )

        _clip_dicts = [self._extract_json_dict(o) for o in (judge_out, nvidia_out, groq_out, gemini_out)]
        parsed = next((d for d in _clip_dicts if isinstance(d, dict) and isinstance(d.get("clips"), list) and d["clips"]), None)
        if parsed is None and any((judge_out, nvidia_out, groq_out, gemini_out)):
            for fb_prov in ("groq", "gemini"):
                repaired = self.invoke_stage(
                    fb_prov,
                    "Convert the clip drafts into strict valid JSON ONLY. No markdown fences.",
                    f'Drafts:\n{nvidia_out or groq_out or gemini_out}\nOutput ONLY JSON: {{"clips": [{{"start_segment_id": int, "end_segment_id": int, "hook_overlay": str, "yt_title": str, "ig_caption": str, "council_score": float}}]}}',
                    final_pass=True,
                )
                cand = self._extract_json_dict(repaired)
                if isinstance(cand, dict) and isinstance(cand.get("clips"), list) and cand["clips"]:
                    parsed = cand
                    break

        final_specs: list[dict[str, Any]] = []
        if parsed and isinstance(parsed.get("clips"), list):
            for item in parsed["clips"]:
                if not isinstance(item, dict):
                    continue
                try:
                    raw_s = int(item["start_segment_id"])
                    raw_e = int(item["end_segment_id"])
                except Exception:
                    continue
                clamped = self._clamp_window_to_valid_duration(raw_s, raw_e, seg_map)
                if clamped is None:
                    continue
                s_id, e_id = clamped
                final_specs.append({
                    "start_segment_id": s_id,
                    "end_segment_id": e_id,
                    "hook_overlay": str(item.get("hook_overlay") or "WATCH THIS BREAKDOWN")[:42].upper(),
                    "yt_title": str(item.get("yt_title") or f"{seg_map[s_id].text[:48]} #Shorts")[:100],
                    "ig_caption": str(item.get("ig_caption") or f"{seg_map[s_id].text[:90]} — full details in bio."),
                    "council_score": (lambda _v: float(re.search(r"\d+(?:\.\d+)?", str(_v)).group(0)) if re.search(r"\d+(?:\.\d+)?", str(_v or "")) else 9.5)(item.get("council_score")),
                })

        if not final_specs:
            for s_id, e_id in deterministic_windows:
                hook_text = seg_map[s_id].text[:48].strip() or "Must-See Moment"
                final_specs.append({
                    "start_segment_id": s_id,
                    "end_segment_id": e_id,
                    "hook_overlay": " ".join(hook_text.split()[:5]).upper(),
                    "yt_title": f"{hook_text} #Shorts",
                    "ig_caption": f"{hook_text} — full breakdown via link in bio.",
                    "council_score": 8.5,
                })

        log.info(
            "4-Brain Free AI Council completed (%d models active: %s) -> selected %d clips.",
            len(self.models_called),
            ", ".join(self.models_called) if self.models_called else "deterministic-fallback",
            len(final_specs[:max_clips]),
        )
        return final_specs[:max_clips]

    def run_6_brain_copy_council(
        self,
        title_or_topic: str,
        raw_notes: str,
        brain: CompanyBrain,
        default_points: list[str] | None = None,
    ) -> dict[str, Any]:
        s1 = self.invoke_stage(
            "gemini",
            "You are Stage 1 (Gemini Market Analyst). Extract the 3 highest-value takeaways for this topic/product.",
            f"ICP:\n{brain.identity_icp}\nTopic: {title_or_topic}\nNotes: {raw_notes}",
        )
        s2 = self.invoke_stage(
            "groq",
            "You are Stage 2 (Groq Viral Copywriter). Turn the 3 takeaways into crisp <=12-word bullets, add a 5-word hook badge, and write an engaging Instagram caption.",
            f"Gemini Draft:\n{s1 or raw_notes}",
        )
        s3 = self.invoke_stage(
            "nvidia",
            "You are Stage 3 (NVIDIA Nemotron SEO Polisher). Add a <=60-char YouTube Shorts title with #Shorts and 3 targeted hashtags to the Instagram caption.",
            f"Groq Copy:\n{s2 or raw_notes}",
        )
        s4 = self.invoke_stage(
            "openrouter",
            "You are Stage 4 (OpenRouter Chief Consensus Judge). Output strict JSON only.",
            f"Synthesize:\nGemini: {s1}\nGroq: {s2}\nNVIDIA NIM: {s3}\n"
            "Output ONLY JSON: {\"hook_badge\": str, \"points\": [str, str, str], \"yt_title\": str, \"ig_caption\": str}",
        )
        _copy_dicts = [self._extract_json_dict(o) for o in (s4, s3, s2, s1)]
        parsed = next((d for d in _copy_dicts if isinstance(d, dict) and isinstance(d.get("points"), list) and len(d["points"]) >= 3), None)
        if parsed is None and any((s4, s3, s2, s1)):
            for fb_prov in ("groq", "gemini"):
                repaired = self.invoke_stage(
                    fb_prov,
                    "Convert the copywriting drafts into strict valid JSON ONLY. No markdown fences.",
                    f'Drafts:\n{s3 or s2 or s1}\nOutput ONLY JSON: {{"hook_badge": str, "points": [str, str, str], "yt_title": str, "ig_caption": str}}',
                    final_pass=True,
                )
                cand = self._extract_json_dict(repaired)
                if isinstance(cand, dict) and isinstance(cand.get("points"), list) and len(cand["points"]) >= 3:
                    parsed = cand
                    break
        if parsed is None:
            parsed = next((d for d in _copy_dicts if isinstance(d, dict)), None) or {}
        fillers = default_points or [
            f"What {title_or_topic} is and why it matters.",
            f"The key idea behind {title_or_topic}.",
            f"How to apply {title_or_topic} today.",
        ]
        default_pts = [p.strip() for p in raw_notes.split(";") if p.strip()]
        default_pts += [f for f in fillers if f not in default_pts][: max(0, 3 - len(default_pts))]
        pts = parsed.get("points") if isinstance(parsed.get("points"), list) and len(parsed["points"]) >= 3 else default_pts
        return {
            "hook_badge": str(parsed.get("hook_badge") or "KEY TAKEAWAYS")[:36].upper(),
            "points": [str(p) for p in pts[:3]],
            "yt_title": str(parsed.get("yt_title") or f"{title_or_topic[:48]} #Shorts")[:100],
            "ig_caption": str(parsed.get("ig_caption") or f"{title_or_topic} — full breakdown via the link in bio."),
            "council_models_used": list(self.models_called),
        }

    def run_6_brain_faceless_script(
        self,
        topic: str,
        brain: CompanyBrain,
        art_style: str = "dark_cinematic",
        theme: str = "AI & Tech Automation",
        character_desc: str = "",
        language_hint: str = "English",
        fact_brief: str = "",
    ) -> dict[str, Any]:
        """
        Passes a topic, theme, and art_style through the 4-Brain Free AI Council to produce
        a cohesive 5-scene motion-animated faceless Short script.
        """
        style_desc = gen_style_prompt(art_style)

        fact_clause = f"Verified Fact Brief (stick strictly to these facts; NEVER invent stats or release years):\n{fact_brief}\n" if fact_brief.strip() else ""
        s1 = self.invoke_stage(
            "gemini",
            "You are Stage 1 (Gemini Viral Strategist). Outline a 5-scene 35-second faceless vertical video script. NEVER invent unverified numbers, sales figures, or release dates. NEVER include camera directions in narration (no 'the camera pulls back'). NEVER ask for logos, signs, or words in visual_prompt. Scene 1 MUST explicitly name the exact topic subject, and NEVER say 'trending on tech platforms' or 'viral online'.",
            f"Theme: {theme}\nArt Style: {art_style} ({style_desc})\nTopic: {topic}\nLanguage: {language_hint}\n"
            f"Character/Subject Lock: {character_desc or 'Topic-matched consistent visual subject'}\n"
            f"{fact_clause}"
            f"ICP:\n{brain.identity_icp}\n"
            "Give 5 short scenes with spoken narration (12-16 words each, zero camera directions, zero invented numbers), a vivid visual_prompt matching the Art Style (pure scenery/action, NO logos, NO text, NO signs), and a 2-3 word stock_keywords phrase for each scene.",
        )
        s2 = self.invoke_stage(
            "groq",
            "You are Stage 2 (Groq Viral Script Director). Tighten all 5 scenes so the first 3 seconds hook hard, every narration sentence flows cleanly, and add a <=6-word ALL-CAPS `hook_overlay` + engaging `ig_caption`.",
            f"Theme: {theme} | Art Style: {art_style}\nGemini Outline:\n{s1 or topic}",
        )
        s3 = self.invoke_stage(
            "nvidia",
            "You are Stage 3 (NVIDIA Nemotron SEO & Retention Polisher). Add a <=60-char `yt_title` with #Shorts, polish visual_prompt consistency for the chosen Art Style, and add 3 niche hashtags to `ig_caption`.",
            f"Art Style: {art_style} ({style_desc})\nGroq Draft:\n{s2 or topic}",
        )
        judge_prompt = (
            f"Merge all 3 drafts into final strict JSON:\nGemini:{s1}\nGroq:{s2}\nNVIDIA:{s3}\n"
            'Output ONLY valid JSON (no markdown, no explanation): {"hook_overlay": str, "yt_title": str, "ig_caption": str, '
            '"scenes": [{"narration": str, "visual_prompt": str, "stock_keywords": str}]} (exactly 5 scenes).'
        )
        s4 = self.invoke_stage(
            "openrouter",
            "You are Stage 4 (OpenRouter Chief Consensus Judge). Output ONLY strict JSON.",
            judge_prompt,
        )
        parsed = self._resolve_script_json([s4, s3, s2, s1], judge_prompt)
        raw_scenes = parsed.get("scenes")
        scenes: list[dict[str, str]] = []
        if isinstance(raw_scenes, list):
            for sc in raw_scenes[:5]:
                if isinstance(sc, dict) and sc.get("narration"):
                    scenes.append({
                        "narration": _strip_camera_directions(str(sc["narration"]).strip()),
                        "visual_prompt": _clean_visual_prompt(str(sc.get("visual_prompt") or f"{topic}, {theme}").strip()),
                        "stock_keywords": str(sc.get("stock_keywords") or f"{theme} {topic}")[:40].strip(),
                    })

        script_source = "ai"
        if len(scenes) < 3:
            sents = _brief_sentences(fact_brief, 5)
            if len(sents) >= 3:
                script_source = "fact_brief"
                narrs = sents[:4] + [f"What is your take on {topic}? Share it in the comments."]
            else:
                script_source = "template"
                narrs = _honest_template_narrations(topic)
            angles = ["opening wide shot", "key subject close-up", "moment of change", "detail view", "closing wide shot"]
            scenes = [
                {
                    "narration": nr,
                    "visual_prompt": f"{angles[k % 5]} of {topic}, {theme}",
                    "stock_keywords": " ".join(topic.split()[:4])[:40],
                }
                for k, nr in enumerate(narrs[:5])
            ]

        scenes = self._board_audit_scenes(scenes, topic, dialogue_mode=False)
        fl_pkg = {
            "hook_overlay": str(parsed.get("hook_overlay") or topic[:36]).upper()[:42],
            "yt_title": str(parsed.get("yt_title") or f"{topic[:48]} #Shorts")[:100],
            "ig_caption": str(parsed.get("ig_caption") or f"{topic} — what to know. Follow for more! #Shorts"),
            "script_source": script_source,
            "scenes": scenes,
            "art_style": art_style,
            "theme": theme,
            "council_models_used": list(self.models_called),
        }
        return RedTeamCriticRobot.audit_and_fix_script(fl_pkg, topic, "ai_faceless", fact_brief=fact_brief, is_long_form=False, council=self)



    def run_motion_story_council(
        self,
        topic: str,
        brain: CompanyBrain,
        art_style: str = "dark_cinematic",
        theme: str = "Universal Storytelling",
        character_desc: str = "",
        language_hint: str = "English",
        fact_brief: str = "",
        target_duration_sec: int = 45,
        dialogue_mode: bool = False,
    ) -> dict[str, Any]:
        """
        4-Brain Free AI Council for `--engine motion_story`:
        Dynamically picks DIFFERENT, topic-relevant camera & motion actions per scene
        from STORY_ACTIONS (never repeating the same 5 fixed templates!) and aligns
        every visual_prompt strictly to the topic, theme, character, and art_style.
        """
        style_desc = gen_style_prompt(art_style)
        char_hint = character_desc.strip() or f"Topic-accurate central subject for {topic}"
        actions_csv = ", ".join(STORY_ACTIONS)

        target_scene_count = max(5, min(28, round(int(target_duration_sec or 45) / 12)))
        is_long_story = int(target_duration_sec or 45) > 60
        fact_clause = f"Verified Fact Brief (ONLY cite numbers/dates from here or well-established history; NEVER invent stats or future sales figures):\n{fact_brief}\n" if fact_brief.strip() else ""
        s1 = self.invoke_stage(
            "gemini",
            f"You are Stage 1 (Gemini Story & Motion Director). Write a factually accurate, gripping {target_scene_count}-scene {target_duration_sec}-second story script where scenes vary visual actions. STRICT RULES: (1) NEVER invent unverified numbers, sales figures, or release years. (2) NEVER write camera directions in narration (never say 'the camera pulls back' or 'watch the screen'). (3) NEVER put logos, signs, or words in visual_prompt. (4) Scene 1 MUST explicitly name the exact topic subject (never vague phrases like 'a devastating disease'). (5) NEVER mention 'trending on platforms' or 'viral online' — tell the actual story.",
            f"Topic: {topic}\nTheme: {theme}\nArt Style: {art_style} ({style_desc})\nLanguage: {language_hint}\n"
            f"Subject/Character: {char_hint}\n{fact_clause}ICP:\n{brain.identity_icp}\n"
            f"For each of the {target_scene_count} scenes, pick a varied, context-appropriate `action` from [{actions_csv}]:\n"
            "- Only use `kinetic_stat_slam` if you have a 100% VERIFIED number from the Fact Brief or undisputed history; otherwise skip it.\n"
            "- Only use `quote_card_styled` if quoting a real verified source.\n"
            "- Only use `timeline_reveal` if the years/milestones are 100% verified.\n"
            "- Otherwise use pure cinematic motion (`cinematic_zoom_in`, `dramatic_pull_back`, `pan_left_to_right`, `pan_right_to_left`, `spotlight_drift`, `pulse_beat_zoom`, `focus_callout`).\n"
            + ("BOARD-DIRECTED SPECIALIST CAST (3 Experts in Sync): Write a sharp, natural back-and-forth between 3 specialists: `host` (Lead Strategist & Anchor who frames the big picture), `guest` (Field Skeptic & Audience Advocate who challenges assumptions and asks the tough question), and `bot` (Chief Data & Tech Analyst who drops the surprising mechanism, verified fact, or twist). Alternate speakers every scene and pick an `emotion` from [explaining, excited, shocked, skeptical, thinking, celebrating] matching their specialist reaction!\n" if dialogue_mode else "")
            + "For EVERY scene include: action, speaker (host/guest/bot), emotion, narration (12-18 words of natural spoken dialogue/voiceover, NO camera directions), top_label (<=4 words), "
            "visual_prompt (pure atmospheric scene/character/environment matching topic & art_style — STRICTLY NO logos, NO signs, NO letters, NO text), "
            "stock_keywords (2-4 concrete real-world nouns spoken in THIS scene), stat_text (verified short stat or ''), "
            "quote_title, quote_text, timeline_steps (3 verified short milestone labels), and callout_label.",
        )
        s2 = self.invoke_stage(
            "groq",
            f"You are Stage 2 (Groq Viral Director). Ensure all {target_scene_count} scenes use varied, topic-accurate actions, tighten the 3-second hook, end with a comment question, and add `hook_overlay` + `ig_caption`.",
            f"Topic: {topic} | Theme: {theme} | Art Style: {art_style} | Language: {language_hint}\nGemini Draft:\n{s1 or topic}",
        )
        s3 = self.invoke_stage(
            "nvidia",
            f"You are Stage 3 (NVIDIA Nemotron Polish & SEO). Add a <=60-char `yt_title`{'' if is_long_story else ' with #Shorts'}, verify every visual_prompt matches the Art Style & Topic, and add 3 niche hashtags to `ig_caption`.",
            f"Art Style: {art_style}\nGroq Draft:\n{s2 or topic}",
        )
        judge_prompt = (
            f"Merge all 3 drafts into strict valid JSON:\nGemini:{s1}\nGroq:{s2}\nNVIDIA:{s3}\n"
            'Output ONLY valid JSON (no markdown, no explanation): {"hook_overlay": str, "yt_title": str, "ig_caption": str, '
            '"visual_world": str, '
            '"character": {"name": str, "archetype": str, "primary_hex": str, "accent_hex": str, "skin_hex": str, "aura_hex": str}, '
            '"scenes": [{"action": str, "speaker": str, "emotion": str, "narration": str, "top_label": str, "visual_prompt": str, "stock_keywords": str, '
            '"stat_text": str, "quote_title": str, "quote_text": str, "timeline_steps": [str, str, str], "callout_label": str}]} '
            f"(exactly {target_scene_count} scenes with varied actions)."
        )
        s4 = self.invoke_stage(
            "openrouter",
            "You are Stage 4 (OpenRouter Chief Consensus Judge). Output ONLY strict valid JSON.",
            judge_prompt,
        )
        parsed = self._resolve_script_json([s4, s3, s2, s1], judge_prompt)

        def _safe_hex(val: Any, default: str) -> str:
            s = str(val or "").strip()
            return s if re.fullmatch(r"#[0-9a-fA-F]{6}", s) else default

        low_ctx = f"{topic} {theme} {character_desc}".lower()
        valid_worlds = {"space", "ocean", "tech_ai", "finance", "history_myth", "nature"}
        v_world = str(parsed.get("visual_world") or "").strip().lower()
        if v_world not in valid_worlds:
            v_world = _classify_visual_world(low_ctx)

        # Deterministic topic+style hash so different topics/styles pick genuinely different action orders even in fallback!
        seed_rng = random.Random(f"{topic.lower()}|{art_style.lower()}|{theme.lower()}")
        style_preferred = {
            "anime": ["pulse_beat_zoom", "pan_left_to_right", "cinematic_zoom_in", "dramatic_pull_back", "focus_callout"],
            "cyberpunk": ["spotlight_drift", "kinetic_stat_slam", "pan_right_to_left", "pulse_beat_zoom", "focus_callout"],
            "comic_book": ["pulse_beat_zoom", "kinetic_stat_slam", "pan_left_to_right", "quote_card_styled", "dramatic_pull_back"],
            "oil_painting": ["dramatic_pull_back", "pan_left_to_right", "quote_card_styled", "cinematic_zoom_in", "spotlight_drift"],
            "minimalist_sketch": ["timeline_reveal", "kinetic_stat_slam", "quote_card_styled", "pan_right_to_left", "focus_callout"],
            "3d_pixar": ["cinematic_zoom_in", "pan_left_to_right", "dramatic_pull_back", "pulse_beat_zoom", "focus_callout"],
        }
        fallback_actions = list(style_preferred.get(art_style, STORY_ACTIONS[:5]))
        seed_rng.shuffle(fallback_actions)

        raw_char = parsed.get("character") if isinstance(parsed.get("character"), dict) else {}
        _dc = _topic_character_colors(topic, v_world)
        character = {
            "name": str(raw_char.get("name") or topic[:24])[:32],
            "archetype": str(raw_char.get("archetype") or "hero").lower(),
            "primary_hex": _safe_hex(raw_char.get("primary_hex"), _dc["primary_hex"]),
            "accent_hex": _safe_hex(raw_char.get("accent_hex"), _dc["accent_hex"]),
            "skin_hex": _safe_hex(raw_char.get("skin_hex"), _dc["skin_hex"]),
            "aura_hex": _safe_hex(raw_char.get("aura_hex"), _dc["aura_hex"]),
            "visual_world": v_world,
        }

        raw_scenes = parsed.get("scenes")
        scenes: list[dict[str, Any]] = []
        used_actions: set[str] = set()
        max_scenes = max(5, min(32, round(target_duration_sec / 11)))
        if isinstance(raw_scenes, list):
            for idx, sc in enumerate(raw_scenes[:max_scenes]):
                if isinstance(sc, dict) and sc.get("narration"):
                    act = str(sc.get("action") or sc.get("scene_type") or "").strip().lower()
                    if len(used_actions) >= len(STORY_ACTIONS):
                        used_actions.clear()
                    if act not in set(STORY_ACTIONS) or act in used_actions:
                        act = next((a for a in fallback_actions if a not in used_actions), STORY_ACTIONS[idx % len(STORY_ACTIONS)])
                    used_actions.add(act)
                    t_steps = sc.get("timeline_steps")
                    if not isinstance(t_steps, list) or len(t_steps) < 3:
                        t_steps = ["START", "SHIFT", "NOW"]
                    _sp = str(sc.get("speaker") or ("host" if idx % 3 == 0 else ("guest" if idx % 3 == 1 else "bot"))).strip().lower()
                    if _sp not in {"host", "guest", "bot"}:
                        _sp = ("host", "guest", "bot")[idx % 3]
                    _emo = str(sc.get("emotion") or ("excited" if idx == 0 else ("skeptical" if _sp == "guest" else "explaining"))).strip().lower()
                    scenes.append({
                        "action": act,
                        "speaker": _sp,
                        "emotion": _emo,
                        "narration": str(sc["narration"]).strip(),
                        "top_label": _trim_words(str(sc.get("top_label") or topic), 28).upper(),
                        "visual_prompt": str(sc.get("visual_prompt") or f"{topic}, {theme}, {art_style}").strip(),
                        "stock_keywords": str(sc.get("stock_keywords") or f"{v_world.replace('_', ' ')} {topic}")[:42].strip(),
                        "stat_text": _trim_words(str(sc.get("stat_text") or ""), 16).upper(),
                        "quote_title": _trim_words(str(sc.get("quote_title") or theme), 32),
                        "quote_text": str(sc.get("quote_text") or sc["narration"]).strip()[:180],
                        "timeline_steps": [str(x)[:14].upper() for x in t_steps[:3]],
                        "callout_label": _trim_words(str(sc.get("callout_label") or ""), 20).upper(),
                    })

        script_source = "ai"
        if len(scenes) < 3:
            sents = _brief_sentences(fact_brief, 5)
            if len(sents) >= 3:
                script_source = "fact_brief"
                narrs = sents[:4] + [f"What is your take on {topic}? Share it in the comments."]
            else:
                script_source = "template"
                narrs = _honest_template_narrations(topic)
            labels = ["THE STORY", "THE BASICS", "WHAT CHANGED", "OVERLOOKED", "YOUR TAKE"]
            angles = ["dramatic opening visual", "clear establishing view", "dynamic moment of change", "detailed close-up", "wide closing shot"]
            scenes = [
                {
                    "action": fallback_actions[k % len(fallback_actions)],
                    "speaker": ("host", "guest", "bot", "host", "bot")[k % 5],
                    "emotion": ("excited", "skeptical", "shocked", "explaining", "celebrating")[k % 5],
                    "narration": nr,
                    "top_label": labels[k % 5],
                    "visual_prompt": f"{angles[k % 5]} of {topic}, {theme}",
                    "stock_keywords": f"{v_world.replace('_', ' ')} {' '.join(topic.split()[:3])}"[:42].strip(),
                    "stat_text": "",
                    "quote_title": theme.upper(),
                    "quote_text": nr if k in (2, 3) else "",
                    "timeline_steps": ["BEFORE", "SHIFT", "AFTER"],
                    "callout_label": "",
                }
                for k, nr in enumerate(narrs[:5])
            ]

        scenes = _sanitize_motion_scenes(scenes, fact_brief)
        scenes = self._board_audit_scenes(scenes, topic, dialogue_mode=dialogue_mode)

        ms_pkg = {
            "hook_overlay": _trim_words(str(parsed.get("hook_overlay") or topic), 36).upper(),
            "yt_title": str(parsed.get("yt_title") or f"{topic[:48]} #Shorts")[:100],
            "ig_caption": str(parsed.get("ig_caption") or f"{topic} — the story in 30 seconds. Tell us your thoughts! #Shorts"),
            "visual_world": v_world,
            "character": character,
            "script_source": script_source,
            "scenes": scenes,
            "art_style": art_style,
            "theme": theme,
            "council_models_used": list(self.models_called),
        }
        return RedTeamCriticRobot.audit_and_fix_script(ms_pkg, topic, "motion_story", fact_brief=fact_brief, is_long_form=is_long_story, council=self)


# ============================================================================
# 3. DEPARTMENT #1: INTELLIGENCE — YOUTUBE & INSTAGRAM TREND SCOUT
# ============================================================================

def get_ytdlp_cookie_args(job_dir: Path) -> list[str]:
    cookies_raw = os.environ.get("YT_COOKIES_TXT", "").strip()
    if not cookies_raw:
        return []
    # Normalize mobile/Windows line endings and ensure Netscape header is present
    normalized = cookies_raw.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff").strip()
    if not normalized.startswith("# Netscape HTTP Cookie File") and not normalized.startswith("# HTTP Cookie File"):
        normalized = "# Netscape HTTP Cookie File\n" + normalized
    job_dir.mkdir(parents=True, exist_ok=True)
    cookie_file = job_dir / ".yt_cookies.txt"
    cookie_file.write_text(normalized + "\n", encoding="utf-8")
    return ["--cookies", str(cookie_file)]


_YTDLP_CAPS: dict[str, bool] = {}


def _ytdlp_supports(flag: str) -> bool:
    if flag not in _YTDLP_CAPS:
        try:
            out = subprocess.run(["yt-dlp", "--help"], capture_output=True, text=True, timeout=60).stdout
            _YTDLP_CAPS[flag] = flag in out
        except Exception:
            _YTDLP_CAPS[flag] = False
    return _YTDLP_CAPS[flag]


def _ytdlp_ejs_args() -> list[str]:
    """
    YouTube n-challenge/PO-token support flags, only when the installed yt-dlp understands them.
    yt-dlp enables only `deno` by default; GitHub runners ship Node, so enable it explicitly.
    """
    args: list[str] = []
    if _ytdlp_supports("--js-runtimes") and not shutil.which("deno") and shutil.which("node"):
        args += ["--js-runtimes", "node"]
    if _ytdlp_supports("--remote-components"):
        args += ["--remote-components", "ejs:github"]
    return args


def discover_instagram_trending(
    niche_query: str,
    brain: CompanyBrain,
) -> list[dict[str, Any]]:
    ig_user_id = os.environ.get("IG_USER_ID", "").strip()
    access_token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    if not (ig_user_id and access_token):
        return []

    hashtag = re.sub(r"[^a-zA-Z0-9]", "", niche_query.split()[0] if niche_query.split() else "ai").lower() or "ai"

    try:
        search_res = _ig_api_call(
            f"{IG_GRAPH_BASE}/ig_hashtag_search",
            method="GET",
            params={"user_id": ig_user_id, "q": hashtag, "access_token": access_token},
        )
        tag_data = search_res.get("data", [])
        if not tag_data:
            return []
        hashtag_id = str(tag_data[0]["id"])

        top_res = _ig_api_call(
            f"{IG_GRAPH_BASE}/{hashtag_id}/top_media",
            method="GET",
            params={
                "user_id": ig_user_id,
                "fields": "id,media_type,media_url,permalink,caption,like_count,comments_count",
                "access_token": access_token,
            },
        )
        candidates: list[dict[str, Any]] = []
        for item in top_res.get("data", []):
            m_type = item.get("media_type", "")
            media_url = (item.get("media_url") or "").strip()
            permalink = (item.get("permalink") or "").strip()
            target_url = media_url if media_url.lower().split("?")[0].endswith(".mp4") else (permalink or media_url)
            if m_type not in {"VIDEO", "REELS"} or not target_url:
                continue
            if f"clip_url:{target_url}" in brain.processed_items:
                continue
            likes = int(item.get("like_count", 0))
            comments = int(item.get("comments_count", 0))
            score = float(likes * 25 + comments * 50 + 1000)
            candidates.append({
                "platform": "instagram",
                "url": target_url,
                "title": (item.get("caption") or f"Trending #{hashtag} Reel")[:80],
                "score": score,
                "license": "instagram_top_media",
            })
        return candidates
    except Exception as exc:
        log.warning("Instagram Graph API Hashtag Trend Scout skipped: %s", exc)
        return []


def discover_youtube_trending(
    niche_query: str,
    brain: CompanyBrain,
    require_cc: bool = True,
    max_results: int = 12,
    cookie_args: list[str] | None = None,
) -> list[dict[str, Any]]:
    cookie_args = cookie_args or []

    def _run_search(query_str: str, enforce_strict_cc_field: bool) -> list[dict[str, Any]]:
        cmd = [
            "yt-dlp",
            *cookie_args,
            *_ytdlp_ejs_args(),
            f"ytsearch{max_results}:{query_str}",
            "--dump-json",
            "--no-playlist",
            "--skip-download",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=240)
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            log.warning("yt-dlp trend search failed (%s).", exc)
            return []
        found: list[dict[str, Any]] = []
        for line in res.stdout.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                info = json.loads(line)
            except Exception:
                continue

            url = (info.get("webpage_url") or info.get("original_url") or "").strip()
            if not url or f"clip_url:{url}" in brain.processed_items:
                continue

            duration = float(info.get("duration") or 0.0)
            if duration < 25.0 or duration > 3600.0:
                continue

            channel_id = info.get("channel_id", "")
            license_str = (info.get("license") or "").lower()
            desc_str = (info.get("description") or "").lower()
            is_cc = ("creative commons" in license_str) or ("cc-by" in desc_str) or ("creative commons" in desc_str)
            is_allowlisted = channel_id in brain.allowlisted_channels
            if enforce_strict_cc_field and not (is_cc or is_allowlisted):
                continue

            views = int(info.get("view_count") or 0)
            likes = int(info.get("like_count") or 0)
            score = float(views + likes * 25)
            found.append({
                "platform": "youtube",
                "url": url,
                "title": info.get("title", "YouTube Trending Video"),
                "duration": duration,
                "views": views,
                "likes": likes,
                "score": score,
                "license": info.get("license") or "CC-Search",
            })
        return found

    search_q = f"{niche_query} creative commons" if require_cc else niche_query
    results = _run_search(search_q, enforce_strict_cc_field=require_cc)
    if not results and require_cc:
        results = _run_search(f"{niche_query} creative commons attribution", enforce_strict_cc_field=False)
    if not results:
        short_niche = " ".join(niche_query.split()[:2]).strip()
        if short_niche and short_niche.lower() != niche_query.lower():
            results = _run_search(
                f"{short_niche} creative commons" if require_cc else short_niche,
                enforce_strict_cc_field=False,
            )
    return results


def discover_trending_candidates(
    niche_query: str,
    brain: CompanyBrain,
    trend_platform: str = "auto",
    require_cc: bool = True,
    cookie_args: list[str] | None = None,
) -> list[str]:
    urls: list[str] = []
    queue_file = brain.brain_dir / "queue.txt"
    if queue_file.exists():
        for raw_line in queue_file.read_text(encoding="utf-8").splitlines():
            u = raw_line.strip()
            if u and not u.startswith("#") and f"clip_url:{u}" not in brain.processed_items:
                urls.append(u)

    candidates: list[dict[str, Any]] = []
    if trend_platform in {"auto", "instagram"}:
        candidates.extend(discover_instagram_trending(niche_query, brain))
    if trend_platform in {"auto", "youtube"}:
        candidates.extend(discover_youtube_trending(niche_query, brain, require_cc=require_cc, cookie_args=cookie_args))

    candidates.sort(key=lambda c: float(c.get("score", 0.0)), reverse=True)
    for c in candidates:
        u = str(c["url"])
        if u not in urls:
            urls.append(u)

    if not urls:
        raise RuntimeError(
            f"TREND_SCOUT_EMPTY: No un-clipped trending videos found for query='{niche_query}' (require_cc={require_cc})."
        )
    return urls[:5]




# ============================================================================
# 4. SHARED MEDIA, FFMPEG & PUBLIC HOSTING UTILITIES
# ============================================================================

def run_cmd(cmd: list[str], check: bool = True, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    log.debug("Executing: %s", " ".join(cmd))
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=check, timeout=timeout)
    except subprocess.CalledProcessError as err:
        tail = (err.stderr or err.stdout or "").strip()[-700:]
        raise RuntimeError(f"Command failed (exit {err.returncode}): {cmd[0]} ... | {tail}") from err
    except subprocess.TimeoutExpired as err:
        raise RuntimeError(f"Command timed out after {timeout}s: {cmd[0]} ...") from err


def resolve_device(requested: str) -> str:
    if requested in {"cuda", "cpu"}:
        return requested
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"



def _get_public_base_url(default: str = "") -> str:
    """Returns PUBLIC_VIDEO_BASE_URL normalized so GitHub Pages URLs always include `/public`."""
    raw = os.environ.get("PUBLIC_VIDEO_BASE_URL", "").strip().rstrip("/") or default.strip().rstrip("/")
    if not raw:
        return ""
    if "github.io/" in raw.lower() and not raw.lower().endswith("/public"):
        raw = f"{raw}/public"
    return raw


def _run_tag() -> str:
    """UTC minute stamp used to make published filenames unique (defeats GitHub Pages CDN caching
    and stops a later run from overwriting a file Instagram has not fetched yet)."""
    return time.strftime("%Y%m%d%H%M", time.gmtime())


def wait_until_public(url: str, timeout_sec: int = 480, interval_sec: int = 15) -> None:
    """Blocks until `url` answers HTTP 200 (GitHub Pages can take minutes to deploy a fresh push).
    Instagram's Graph API fails the whole container if it cannot fetch the media on first try."""
    deadline = time.monotonic() + timeout_sec
    last = "no response"
    while True:
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "JagnorPublisher/2.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                if resp.status == 200:
                    log.info("Public media is live: %s", url)
                    return
                last = f"HTTP {resp.status}"
        except urllib.error.HTTPError as err:
            last = f"HTTP {err.code}"
        except Exception as err:
            last = str(err)
        if time.monotonic() >= deadline:
            raise TimeoutError(f"PUBLIC_URL_NOT_READY: {url} not reachable after {timeout_sec}s ({last}). Re-run stage=publish later.")
        time.sleep(interval_sec)


def _safe_slug(text: str, prefix: str = "item", max_len: int = 28) -> str:
    """Produces a clean, unique ASCII filename slug even for non-ASCII titles."""
    ascii_part = re.sub(r"[^a-zA-Z0-9]+", "_", (text or "").lower()).strip("_")[:max_len]
    if ascii_part:
        return ascii_part
    digest = hashlib.md5((text or prefix).encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{digest}"


def export_to_public_dir(files: list[Path], public_dir: Path | None) -> None:
    if public_dir is None:
        return
    public_dir.mkdir(parents=True, exist_ok=True)
    for src in files:
        if src.exists():
            dst = public_dir / src.name
            if src.resolve() != dst.resolve():
                shutil.copy2(src, dst)
                log.info("Exported %s -> %s (for GitHub Pages / IG Graph API)", src.name, dst)


def cleanup_heavy_temp_files(job_dir: Path) -> None:
    for pattern in ("source.*", "audio_16k.wav", ".yt_cookies.txt"):
        for p in job_dir.glob(pattern):
            if p.name == "source.info.json":
                continue
            try:
                p.unlink()
            except Exception:
                pass


def parse_fps(rate_str: str) -> float:
    try:
        return float(Fraction(rate_str))
    except (ValueError, ZeroDivisionError):
        return 30.0


def ffprobe_metadata(video_path: Path, min_duration: float = 5.0) -> dict[str, Any]:
    if not video_path.exists() or video_path.stat().st_size == 0:
        raise ValueError(f"DEAD_LETTER: File missing or 0 bytes: {video_path}")

    res = run_cmd([
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ])
    data = json.loads(res.stdout)
    duration = float(data.get("format", {}).get("duration", 0.0))
    streams = data.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    if not video_streams:
        raise ValueError("DEAD_LETTER: No video stream found in media file.")
    if not audio_streams:
        raise ValueError("DEAD_LETTER: No audio stream found in media file.")
    if duration < min_duration:
        raise ValueError(f"DEAD_LETTER: Duration ({duration:.1f}s) is shorter than minimum {min_duration:.1f}s.")

    vs = video_streams[0]
    aus = audio_streams[0]
    return {
        "duration": duration,
        "width": int(vs["width"]),
        "height": int(vs["height"]),
        "vcodec": vs.get("codec_name", ""),
        "acodec": aus.get("codec_name", ""),
        "sample_rate": int(aus.get("sample_rate", 48000)),
        "fps": parse_fps(vs.get("r_frame_rate", "30/1")),
    }


def gen_style_prompt(art_style: str) -> str:
    """Prompt suffix for AI image generation. `original` only makes sense for clipped footage, so
    generated engines fall back to the dark_cinematic look instead of sending a nonsense phrase."""
    key = (art_style or "dark_cinematic").lower()
    if key == "original" or key not in ART_STYLE_PROMPTS:
        key = "dark_cinematic"
    return ART_STYLE_PROMPTS[key]


ASPECT_RATIOS: dict[str, tuple[int, int]] = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}


def verify_rendered_mp4(
    mp4_path: Path,
    min_duration: float = 5.0,
    expected_size: tuple[int, int] = (1080, 1920),
    max_duration: float = 59.5,
) -> bool:
    meta = ffprobe_metadata(mp4_path, min_duration=min_duration)
    exp_w, exp_h = expected_size
    if meta["width"] != exp_w or meta["height"] != exp_h:
        raise ValueError(f"QA_FAIL: Expected {exp_w}x{exp_h}, got {meta['width']}x{meta['height']}")
    if meta["vcodec"] != "h264" or meta["acodec"] != "aac":
        raise ValueError(f"QA_FAIL: Expected h264/aac, got {meta['vcodec']}/{meta['acodec']}")
    if meta["duration"] > max_duration:
        raise ValueError(f"QA_FAIL: Duration {meta['duration']:.2f}s exceeds {max_duration:.1f}s cap")

    try:
        meas = subprocess.run(
            ["ffmpeg", "-nostats", "-i", str(mp4_path), "-af", "ebur128=peak=none", "-vn", "-f", "null", "-"],
            capture_output=True, text=True, timeout=240, check=False,
        )
        hits = re.findall(r"I:\s*(-?\d+(?:\.\d+)?)\s*LUFS", meas.stderr)
        if hits:
            lufs = float(hits[-1])
            if abs(lufs - (-14.0)) > 3.0:
                log.warning("QA loudness %.1f LUFS is outside -14 +/- 3 LUFS for %s", lufs, mp4_path.name)
            else:
                log.info("QA loudness OK: %.1f LUFS (%s)", lufs, mp4_path.name)
    except Exception as exc:
        log.debug("Loudness measurement skipped: %s", exc)

    with mp4_path.open("rb") as f:
        head = f.read(65536)
    moov_pos = head.find(b"moov")
    mdat_pos = head.find(b"mdat")
    if moov_pos == -1 or (mdat_pos != -1 and mdat_pos < moov_pos):
        raise ValueError("QA_FAIL: MP4 `moov` atom is not at the front of the file (+faststart failed).")
    return True


def escape_ffmpeg_filter_path(path: Path) -> str:
    s = str(path.resolve()).replace("\\", "/")
    s = s.replace(":", r"\:").replace("'", r"\'").replace("[", r"\[").replace("]", r"\]").replace(",", r"\,")
    return s


# ============================================================================
# 5. ENGINE A: DIGITAL PRODUCT & MICRO-SAAS FACTORY (`--engine digital_product`)
# ============================================================================

def whop_is_configured() -> bool:
    return bool(os.environ.get("WHOP_API_KEY", "").strip() and os.environ.get("WHOP_COMPANY_ID", "").strip())


def create_whop_checkout_link(product_title: str, price_usd: float, redirect_url: str) -> str:
    api_key = os.environ.get("WHOP_API_KEY", "").strip()
    company_id = os.environ.get("WHOP_COMPANY_ID", "").strip()
    slug = re.sub(r"[^a-z0-9]+", "-", product_title.lower()).strip("-") or "bundle"
    if not api_key or not company_id:
        log.info("WHOP_API_KEY / WHOP_COMPANY_ID not set; returning simulated checkout URL for local dry run.")
        return f"https://whop.com/checkout/plan_{slug}_dryrun/"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Api-Version-Date": "2025-01-01",
    }
    payload = {
        "company_id": company_id,
        "plan": {
            "company_id": company_id,
            "initial_price": price_usd,
            "plan_type": "one_time",
            "currency": "usd",
        },
        "redirect_url": redirect_url,
        "metadata": {"product_title": product_title},
    }
    req = urllib.request.Request(
        "https://api.whop.com/api/v1/checkout_configurations",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        raw, _ = urlopen_with_retry(req, timeout=30)
        body = json.loads(raw.decode("utf-8"))
        url = body.get("purchase_url") or body.get("url")
        if url:
            return str(url)
    except Exception as exc:
        log.warning("Whop checkout_configurations failed (%s); attempting /api/v1/products fallback...", exc)

    fallback_req = urllib.request.Request(
        f"https://api.whop.com/api/v1/products?company_id={urllib.parse.quote(company_id)}",
        headers=headers,
        method="GET",
    )
    raw_fb, _ = urlopen_with_retry(fallback_req, timeout=30)
    fb_body = json.loads(raw_fb.decode("utf-8"))
    products = fb_body.get("data", [])
    if products and products[0].get("route"):
        return f"https://whop.com/{products[0]['route']}"
    raise RuntimeError("Whop checkout link creation failed on both primary and fallback endpoints.")


def run_digital_product_engine(
    product_title: str,
    price_usd: float,
    source_app_dir: Path | None,
    job_dir: Path,
    brain: CompanyBrain,
    public_dir: Path | None = None,
    voice: str = "deep_male",
    notes: str = "",
) -> dict[str, Any]:
    item_key = f"product:{product_title.lower().strip()}"
    brain.check_pre_flight(item_key, estimated_cost_usd=0.05)

    out_dir = job_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    council = AICouncil()
    context_text = notes.strip() or brain.offers_pricing
    copy_spec = council.run_6_brain_copy_council(product_title, context_text, brain)
    pillars = copy_spec.get("points") or [
        "Step-by-step quickstart framework",
        "Plug-and-play templates & prompts",
        "Automation checklist for immediate launch",
    ]
    slug = _safe_slug(product_title, prefix="product")

    bundle_zip = out_dir / f"product_{slug}.zip"
    with zipfile.ZipFile(bundle_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        if source_app_dir and source_app_dir.exists():
            for file_p in sorted(source_app_dir.rglob("*")):
                if file_p.is_file() and file_p.resolve() != bundle_zip.resolve():
                    zf.write(file_p, file_p.relative_to(source_app_dir))
        else:
            bullets_md = "\n".join(f"{i}. **{p}**" for i, p in enumerate(pillars, start=1))
            readme_content = (
                f"# {product_title}\n\n"
                f"**Price:** ${price_usd:,.2f} USD | **Publisher:** Jagnor AI\n\n"
                f"## Overview\n{copy_spec.get('ig_caption', context_text)}\n\n"
                f"## Core Modules Included\n{bullets_md}\n\n"
                f"## Quick-Start Checklist\n"
                f"- [ ] Open `index.html` in any browser to view the interactive guide.\n"
                f"- [ ] Customize the workflow parameters for your niche.\n"
                f"- [ ] Deploy and track results using your weekly KPI sheet.\n"
            )
            bullets_html = "".join(f"<li>{html.escape(str(p))}</li>" for p in pillars)
            safe_title = html.escape(product_title)
            safe_caption = html.escape(str(copy_spec.get("ig_caption", context_text)))
            guide_html = (
                "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
                f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>{safe_title}</title>"
                "<style>body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;max-width:760px;margin:40px auto;padding:24px;line-height:1.6}"
                "h1{color:#38bdf8}li{margin:10px 0}.card{background:#1e293b;border-radius:14px;padding:20px;margin-top:20px}</style></head>"
                f"<body><h1>{safe_title}</h1><p>{safe_caption}</p>"
                f"<div class='card'><h2>What's Inside</h2><ol>{bullets_html}</ol></div>"
                "<p style='margin-top:24px;color:#94a3b8'>Built by Jagnor AI Studio</p></body></html>"
            )
            zf.writestr("README.md", readme_content)
            zf.writestr("index.html", guide_html)

    promo_png = out_dir / f"promo_{slug}.png"
    _render_brand_slide_png(
        promo_png,
        width=1080,
        height=1920,
        badge=copy_spec["hook_badge"],
        headline=product_title.upper(),
        subline=f"Instant Download • ${price_usd:.0f} One-Time • Link in Bio",
        footer="JAGNOR AI VERIFIED BUILD",
    )
    promo_mp4 = out_dir / f"promo_{slug}.mp4"
    promo_audio = out_dir / f"promo_{slug}.wav"
    pitch_text = (
        f"Introducing {product_title}. "
        f"{pillars[0]}. {pillars[1] if len(pillars) > 1 else ''}. "
        f"Grab instant access today for just {int(round(price_usd))} dollars. Link in bio."
    )
    audio_dur = 12.0
    use_tts = False
    try:
        audio_dur = max(10.5, _synthesize_scene_voiceover(pitch_text, promo_audio, voice=voice))
        use_tts = promo_audio.exists() and promo_audio.stat().st_size > 1000
    except Exception as exc:
        log.info("Digital product promo TTS unavailable (%s); falling back to silent audio.", exc)

    if use_tts:
        target_dur = max(12.0, audio_dur + 1.0)
        run_cmd([
            "ffmpeg", "-y",
            "-loop", "1", "-t", f"{target_dur:.2f}", "-i", str(promo_png),
            "-i", str(promo_audio),
            "-vf", "scale=1080:1920,format=yuv420p",
            "-af", f"loudnorm=I=-14:TP=-1.5:LRA=11,apad=whole_dur={target_dur:.2f}",
            "-t", f"{target_dur:.2f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
            "-movflags", "+faststart",
            str(promo_mp4),
        ])
    else:
        run_cmd([
            "ffmpeg", "-y",
            "-loop", "1", "-t", "12", "-i", str(promo_png),
            "-f", "lavfi", "-t", "12", "-i", "anullsrc=channel_layout=mono:sample_rate=48000",
            "-vf", "scale=1080:1920,format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
            "-movflags", "+faststart",
            str(promo_mp4),
        ])
    qa_ok = verify_rendered_mp4(promo_mp4, min_duration=10.0)
    export_to_public_dir([bundle_zip, promo_mp4], public_dir)

    public_base = _get_public_base_url("https://jagnor110-cell.github.io/Jagnor/public")
    redirect_url = f"{public_base}/{bundle_zip.name}"
    checkout_url = create_whop_checkout_link(product_title, price_usd, redirect_url)

    result = {
        "engine": "digital_product",
        "status": "APPROVAL_PENDING",
        "product_title": product_title,
        "price_usd": price_usd,
        "bundle_zip_path": str(bundle_zip),
        "promo_mp4_path": str(promo_mp4),
        "qa_verified": qa_ok,
        "whop_checkout_url": checkout_url,
        "whop_simulated": not whop_is_configured(),
        "yt_title": copy_spec["yt_title"],
        "ig_caption": copy_spec["ig_caption"],
        "council_models_used": copy_spec["council_models_used"],
    }
    brain.record_completion(item_key, "digital_product", 0.05, result)
    return result


# ============================================================================
# 6. ENGINE B: AUTOMATED VIDEO CLIPPING (`--engine clipping`)
# ============================================================================

def _parse_timestamp_sec(raw: str) -> int | None:
    """Parse HH:MM:SS, MM:SS, or plain seconds into integer seconds (None if blank)."""
    s = (raw or "").strip()
    if not s:
        return None
    parts = s.split(":")
    try:
        if len(parts) == 1:
            return max(0, int(float(parts[0])))
        if len(parts) == 2:
            return max(0, int(parts[0]) * 60 + int(float(parts[1])))
        if len(parts) == 3:
            return max(0, int(parts[0]) * 3600 + int(parts[1]) * 60 + int(float(parts[2])))
    except ValueError as exc:
        raise ValueError(f"Invalid --slice-start timestamp '{raw}'. Use HH:MM:SS, MM:SS, or seconds.") from exc
    raise ValueError(f"Invalid --slice-start timestamp '{raw}'. Use HH:MM:SS, MM:SS, or seconds.")


def ingest_video(
    url: str,
    job_dir: Path,
    require_cc: bool = True,
    allowlisted_channels: set[str] | None = None,
    slice_start_sec: int | None = None,
) -> tuple[Path, Path]:
    url = re.sub(r"^(https?)://", lambda m: m.group(1).lower() + "://", (url or "").strip(), flags=re.IGNORECASE)
    job_dir.mkdir(parents=True, exist_ok=True)
    out_tpl = str(job_dir / "source.%(ext)s")
    cookie_args = get_ytdlp_cookie_args(job_dir)

    if url.lower().split("?")[0].endswith(".mp4"):
        video_path = job_dir / "source.mp4"
        info_path = job_dir / "source.info.json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        raw, _ = urlopen_with_retry(req, timeout=120)
        video_path.write_bytes(raw)
        info_path.write_text(json.dumps({"webpage_url": url, "license": "instagram_graph_media"}), encoding="utf-8")
        ffprobe_metadata(video_path, min_duration=15.0)
        return video_path, info_path

    # 3-tier resilient YouTube strategy: defeats SABR-only / web_creator PO-token / missing-JS-runtime errors
    ejs = _ytdlp_ejs_args()
    meta_attempts: list[list[str]] = [
        [*cookie_args, *ejs, "--extractor-args", "youtube:player_client=default,web_safari"],
        [*cookie_args, *ejs],
        [*ejs, "--extractor-args", "youtube:player_client=android_vr,web_embedded"],
    ]
    meta_res = None
    last_meta_err: Exception | None = None
    for attempt_idx, extra_args in enumerate(meta_attempts):
        try:
            meta_res = run_cmd(["yt-dlp", *extra_args, "--dump-single-json", "--no-playlist", url])
            # Download with the client strategy that just worked first, then the others.
            meta_attempts = meta_attempts[attempt_idx:] + meta_attempts[:attempt_idx]
            break
        except Exception as exc:
            last_meta_err = exc
            log.info("yt-dlp metadata attempt failed (%s); trying next client strategy...", str(exc)[:160])
    if meta_res is None:
        raise RuntimeError(f"yt-dlp metadata failed across all client strategies: {last_meta_err}")

    json_lines = [ln for ln in meta_res.stdout.splitlines() if ln.strip().startswith("{")]
    info = json.loads(json_lines[-1] if json_lines else meta_res.stdout)
    if info.get("is_live") or str(info.get("live_status") or "") in {"is_live", "is_upcoming"}:
        raise ValueError("DEAD_LETTER: This URL is an active live stream. Wait until it ends or provide a finished video URL.")
    channel_id = info.get("channel_id", "")
    extractor = (info.get("extractor") or "").lower()
    license_str = (info.get("license") or "").lower()
    desc_str = (info.get("description") or "").lower()

    is_cc = ("creative commons" in license_str) or ("cc-by" in desc_str) or ("creative commons" in desc_str)
    is_allowlisted = allowlisted_channels is not None and (channel_id in allowlisted_channels or url in allowlisted_channels)
    is_ig = "instagram" in extractor
    if require_cc and not (is_cc or is_allowlisted or is_ig):
        raise PermissionError(
            f"DEAD_LETTER: License '{info.get('license')}' is not Creative Commons and channel '{channel_id}' is not allowlisted."
        )

    # Never let leftovers from a previous source (video, captions, slice window) leak into this job.
    for stale in job_dir.glob("source.*"):
        try:
            stale.unlink()
        except OSError:
            pass

    duration_sec = float(info.get("duration") or 0.0)
    slice_args: list[str] = []
    fmt_selector = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
    slice_meta_path = job_dir / "source.slice.json"
    slice_meta_path.unlink(missing_ok=True)
    if duration_sec > 10800.0 and not _ytdlp_supports("--download-sections"):
        raise ValueError(
            f"DEAD_LETTER: Video is {duration_sec / 3600.0:.1f}h long and this yt-dlp cannot download a slice; refusing a full download."
        )
    if (slice_start_sec is not None or duration_sec > 1800.0) and _ytdlp_supports("--download-sections"):
        slice_start = slice_start_sec if slice_start_sec is not None else (300 if duration_sec > 2400.0 else 0)
        if duration_sec > 0 and slice_start >= int(duration_sec) - 20:
            raise ValueError(
                f"DEAD_LETTER: --slice-start ({slice_start}s) is past the end of the video ({int(duration_sec)}s)."
            )
        slice_end = min(int(duration_sec), slice_start + 900) if duration_sec > 0 else (slice_start + 900)
        slice_args = ["--download-sections", f"*{slice_start}-{slice_end}", "--force-keyframes-at-cuts"]
        if duration_sec > 1800.0 or slice_start_sec is not None:
            fmt_selector = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
        slice_meta_path.write_text(json.dumps({"start": slice_start, "end": slice_end}), encoding="utf-8")
        log.info(
            "Slicing video (%.1fh total) window %ds..%ds (15m max) at <=720p so it finishes quickly on the runner.",
            duration_sec / 3600.0, slice_start, slice_end,
        )

    dl_ok = False
    last_dl_err: Exception | None = None
    for extra_args in meta_attempts:
        try:
            run_cmd([
                "yt-dlp",
                *extra_args,
                *slice_args,
                "--geo-bypass",
                "--no-playlist",
                "--write-info-json",
                "--write-subs",
                "--write-auto-subs",
                "--sub-langs", "en.*,en",
                "--sub-format", "json3",
                "-f", fmt_selector,
                "--merge-output-format", "mp4",
                "--remux-video", "mp4",
                "-o", out_tpl,
                url,
            ])
            dl_ok = True
            break
        except Exception as exc:
            last_dl_err = exc
            # A subtitle-only failure (e.g. HTTP 429) makes yt-dlp exit non-zero even though the video finished.
            done = [
                p for p in job_dir.glob("source.*")
                if p.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov", ".m4v"} and p.stat().st_size > 100_000
            ]
            err_l = str(exc).lower()
            if done and ("429" in err_l or "subtitle" in err_l or "too many requests" in err_l):
                log.warning("yt-dlp reported an error but the video file exists (%s); continuing.", str(exc)[:120])
                dl_ok = True
                break
            log.warning("yt-dlp download strategy failed (%s); trying next client strategy...", str(exc)[:180])
    if not dl_ok:
        raise RuntimeError(f"yt-dlp download failed across all client strategies: {last_dl_err}")

    video_path = job_dir / "source.mp4"
    if not video_path.exists():
        candidates = [
            p for p in job_dir.glob("source.*")
            if p.suffix.lower() in {".mkv", ".webm", ".mov", ".m4v"}
        ]
        if candidates:
            run_cmd(["ffmpeg", "-y", "-i", str(candidates[0]), "-c", "copy", str(video_path)])

    info_path = job_dir / "source.info.json"
    ffprobe_metadata(video_path, min_duration=20.0)
    return video_path, info_path


def parse_yt_json3_subtitles(job_dir: Path) -> list[IndexedSegment]:
    json3_files = sorted(job_dir.glob("source.*.json3"))
    if not json3_files:
        return []
    try:
        raw = json.loads(json3_files[0].read_text(encoding="utf-8"))
        events = [ev for ev in raw.get("events", []) if ev.get("segs")]
    except Exception:
        return []

    slice_start_ms = 0.0
    slice_end_ms: float | None = None
    slice_meta = job_dir / "source.slice.json"
    if slice_meta.exists():
        try:
            sm = json.loads(slice_meta.read_text(encoding="utf-8"))
            slice_start_ms = float(sm.get("start", 0.0)) * 1000.0
            if sm.get("end"):
                slice_end_ms = float(sm["end"]) * 1000.0
        except Exception:
            pass

    if slice_end_ms is not None:
        events = [
            ev for ev in events
            if slice_start_ms <= float(ev.get("tStartMs", 0.0)) < slice_end_ms
        ]

    indexed: list[IndexedSegment] = []
    for ev_i, ev in enumerate(events):
        segs = ev.get("segs", [])
        t_start_ms = max(0.0, float(ev.get("tStartMs", 0.0)) - slice_start_ms)
        d_dur_ms = float(ev.get("dDurationMs", 2500.0))
        if ev_i + 1 < len(events):
            next_start_ms = max(0.0, float(events[ev_i + 1].get("tStartMs", 0.0)) - slice_start_ms)
            event_end_ms = min(t_start_ms + d_dur_ms, max(t_start_ms + 300.0, next_start_ms))
        else:
            event_end_ms = t_start_ms + d_dur_ms

        words: list[WordToken] = []
        for idx, s in enumerate(segs):
            txt = (s.get("utf8") or "").strip()
            if not txt or txt == "\n":
                continue
            offset_ms = float(s.get("tOffsetMs", idx * 220.0))
            w_start = min(event_end_ms - 100.0, t_start_ms + offset_ms) / 1000.0
            w_end = min(event_end_ms / 1000.0, w_start + 0.40)
            for sub_w in txt.split():
                words.append(
                    WordToken(
                        word=sub_w,
                        start=round(max(0.0, w_start), 3),
                        end=round(max(w_start + 0.12, w_end), 3),
                    )
                )

        if not words:
            continue
        contig_id = len(indexed)
        indexed.append(
            IndexedSegment(
                segment_id=contig_id,
                speaker="SPEAKER_00",
                start=words[0].start,
                end=words[-1].end,
                text=" ".join(w.word for w in words),
                words=words,
            )
        )
    return indexed


def transcribe_with_faster_whisper_cpu(audio_wav: Path, model_name: str = "base") -> tuple[list[IndexedSegment], str]:
    from faster_whisper import WhisperModel

    cpu_model = "base" if "large" in model_name else model_name
    log.info("Running faster-whisper CPU fallback (model=%s, int8, word_timestamps=True)...", cpu_model)
    fw = WhisperModel(cpu_model, device="cpu", compute_type="int8")
    segments_gen, info = fw.transcribe(str(audio_wav), word_timestamps=True)
    detected_lang = getattr(info, "language", "en") or "en"

    indexed: list[IndexedSegment] = []
    for seg in segments_gen:
        raw_words = getattr(seg, "words", None) or []
        words = [
            WordToken(word=w.word.strip(), start=round(float(w.start), 3), end=round(float(w.end), 3))
            for w in raw_words
            if w.word.strip()
        ]
        if not words:
            continue
        contig_id = len(indexed)
        indexed.append(
            IndexedSegment(
                segment_id=contig_id,
                speaker="SPEAKER_00",
                start=words[0].start,
                end=words[-1].end,
                text=" ".join(w.word for w in words),
                words=words,
            )
        )
    return indexed, detected_lang


def flush_gpu_memory() -> None:
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


def transcribe_with_whisperx(
    video_path: Path,
    job_dir: Path,
    device: str = "auto",
    model_name: str = "large-v3-turbo",
    compute_type: str = "float16",
    batch_size: int = 16,
    hf_token: str | None = None,
) -> tuple[list[IndexedSegment], str]:
    actual_device = resolve_device(device)
    try:
        import whisperx
        has_whisperx = True
    except ImportError:
        has_whisperx = False

    out_json = job_dir / "transcript_indexed.json"

    if actual_device == "cpu" or not has_whisperx:
        fast_segments = parse_yt_json3_subtitles(job_dir)
        if fast_segments:
            log.info("Using zero-GPU yt-dlp .json3 word-aligned subtitle fast path (%d segments).", len(fast_segments))
            out_json.write_text(
                json.dumps([asdict(s) for s in fast_segments], indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return fast_segments, "en"

    audio_wav = job_dir / "audio_16k.wav"
    run_cmd([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(audio_wav),
    ])

    if not has_whisperx:
        fw_segments, fw_lang = transcribe_with_faster_whisper_cpu(audio_wav, model_name=model_name)
        out_json.write_text(
            json.dumps([asdict(s) for s in fw_segments], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return fw_segments, fw_lang

    log.info("Stage 1/3: WhisperX (%s) ASR on %s...", model_name, actual_device)
    model = whisperx.load_model(model_name, actual_device, compute_type=compute_type)
    audio = whisperx.load_audio(str(audio_wav))
    result = model.transcribe(audio, batch_size=batch_size)
    detected_lang = result.get("language", "en")
    del model
    flush_gpu_memory()

    log.info("Stage 2/3: Word-level forced alignment...")
    align_model, metadata = whisperx.load_align_model(language_code=detected_lang, device=actual_device)
    aligned = whisperx.align(
        result["segments"], align_model, metadata, audio, actual_device, return_char_alignments=False
    )
    del align_model
    flush_gpu_memory()

    token = hf_token or os.environ.get("HF_TOKEN")
    if token:
        try:
            log.info("Stage 3/3: Running Pyannote speaker diarization...")
            from whisperx.diarize import DiarizationPipeline
            diarize_model = DiarizationPipeline(use_auth_token=token, device=actual_device)
            diarize_segments = diarize_model(audio)
            aligned = whisperx.assign_word_speakers(diarize_segments, aligned)
            del diarize_model
            flush_gpu_memory()
        except Exception as exc:
            log.warning("Speaker diarization skipped: %s", exc)

    indexed: list[IndexedSegment] = []
    for seg in aligned.get("segments", []):
        seg_speaker = seg.get("speaker", "SPEAKER_00")
        words = [
            WordToken(
                word=w["word"].strip(),
                start=float(w["start"]),
                end=float(w["end"]),
                speaker=w.get("speaker", seg_speaker),
            )
            for w in seg.get("words", [])
            if "start" in w and "end" in w and w.get("word", "").strip()
        ]
        if not words:
            continue

        chunk_start_idx = 0
        for w_idx, w_tok in enumerate(words):
            is_last = (w_idx == len(words) - 1)
            span = w_tok.end - words[chunk_start_idx].start
            if span >= 45.0 or is_last:
                sub_words = words[chunk_start_idx: w_idx + 1]
                contig_id = len(indexed)
                indexed.append(
                    IndexedSegment(
                        segment_id=contig_id,
                        speaker=seg_speaker,
                        start=float(sub_words[0].start),
                        end=float(sub_words[-1].end),
                        text=" ".join(sw.word for sw in sub_words),
                        words=sub_words,
                    )
                )
                chunk_start_idx = w_idx + 1

    out_json.write_text(
        json.dumps([asdict(s) for s in indexed], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return indexed, detected_lang


def select_candidate_windows(
    segments: list[IndexedSegment],
    min_sec: float = 30.0,
    max_sec: float = 55.0,
    max_clips: int = 3,
) -> list[tuple[int, int]]:
    if not segments:
        return []
    hook_re = re.compile(r"(\?|\b(?:why|how|secret|never|stop|mistake|truth|actually|first|million|billion|percent|%)\b|\d+)", re.I)
    scored_windows: list[tuple[float, int, int]] = []
    for i in range(len(segments)):
        start_t = segments[i].start
        j = i
        while j + 1 < len(segments) and (segments[j + 1].end - start_t) <= max_sec:
            j += 1
        dur = segments[j].end - start_t
        if min_sec <= dur <= max_sec:
            hook_hits = len(hook_re.findall(segments[i].text)) * 2.5
            body_text = " ".join(s.text for s in segments[i : j + 1])
            body_hits = len(hook_re.findall(body_text))
            pacing_bonus = 3.0 if 35.0 <= dur <= 50.0 else 1.0
            score = hook_hits + min(body_hits, 8) * 0.6 + pacing_bonus
            scored_windows.append((score, i, j))

    scored_windows.sort(key=lambda x: x[0], reverse=True)
    windows: list[tuple[int, int]] = []
    used_idx: set[int] = set()
    for _, i, j in scored_windows:
        if any(k in used_idx for k in range(i, j + 1)):
            continue
        windows.append((segments[i].segment_id, segments[j].segment_id))
        used_idx.update(range(i, j + 1))
        if len(windows) >= max_clips:
            break

    if not windows:
        for seg in segments:
            dur = seg.end - seg.start
            if 15.0 <= dur <= 58.0:
                windows.append((seg.segment_id, seg.segment_id))
                break
        if not windows:
            windows.append((segments[0].segment_id, segments[0].segment_id))
    return windows


def detect_faces_in_frame(rgb_frame: np.ndarray, mp_detector: Any = None, cv_cascade: Any = None) -> list[tuple[float, float]]:
    detections: list[tuple[float, float]] = []
    if mp_detector is not None:
        res = mp_detector.process(rgb_frame)
        if res and getattr(res, "detections", None):
            for d in res.detections:
                score = float(d.score[0]) if d.score else 0.6
                box = d.location_data.relative_bounding_box
                cx = float(np.clip(box.xmin + box.width / 2.0, 0.15, 0.85))
                detections.append((score, cx))
        return detections

    if cv_cascade is not None:
        gray = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2GRAY)
        _h, w = gray.shape[:2]
        faces = cv_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(48, 48))
        for (x, _y, fw, _fh) in faces:
            cx = float(np.clip((x + fw / 2.0) / max(w, 1), 0.15, 0.85))
            detections.append((0.7, cx))
    return detections


HAAR_FACE_XML = "haarcascade_frontalface_default.xml"
HAAR_FACE_URL = "https://raw.githubusercontent.com/opencv/opencv/4.x/data/haarcascades/" + HAAR_FACE_XML


def _load_face_cascade() -> Any | None:
    """Loads OpenCV's Haar face model robustly. Some pip builds (opencv-contrib / mixed opencv wheels)
    ship `cv2.data` without the XML, which makes detectMultiScale assert and kills the whole run."""
    candidates: list[Path] = []
    try:
        candidates.append(Path(cv2.data.haarcascades) / HAAR_FACE_XML)
    except Exception:
        pass
    candidates += [
        Path("/usr/share/opencv4/haarcascades") / HAAR_FACE_XML,
        Path("/usr/local/share/opencv4/haarcascades") / HAAR_FACE_XML,
        Path(tempfile.gettempdir()) / HAAR_FACE_XML,
    ]
    for cand in candidates:
        if cand.exists():
            cascade = cv2.CascadeClassifier(str(cand))
            if not cascade.empty():
                return cascade
    try:
        data, _ = urlopen_with_retry(urllib.request.Request(HAAR_FACE_URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=30, max_attempts=2)
        dst = Path(tempfile.gettempdir()) / HAAR_FACE_XML
        dst.write_bytes(data)
        cascade = cv2.CascadeClassifier(str(dst))
        if not cascade.empty():
            return cascade
    except Exception as exc:
        log.warning("Could not download Haar face model (%s).", exc)
    return None


def analyze_speaker_centers(
    video_path: Path,
    start_sec: float,
    end_sec: float,
    sample_fps: float = 2.0,
) -> tuple[list[tuple[float, float]], str]:
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, int(fps / sample_fps))

    centers: list[tuple[float, float]] = []
    wide_two_speaker_frames = 0
    total_sampled = 0

    mp_detector = None
    cv_cascade = None
    try:
        import mediapipe as mp
        if hasattr(mp, "solutions") and hasattr(mp.solutions, "face_detection"):
            mp_detector = mp.solutions.face_detection.FaceDetection(
                model_selection=1, min_detection_confidence=0.55
            )
    except Exception:
        mp_detector = None

    if mp_detector is None:
        cv_cascade = _load_face_cascade()

    if (mp_detector is None and cv_cascade is None) or not cap.isOpened():
        log.warning("No face detector available (or video unreadable); using centered crop.")
        cap.release()
        return [(0.0, 0.5)], "single_ema"

    try:
        frame_idx = int(start_sec * fps)
        end_idx = int(end_sec * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)

        while frame_idx <= end_idx:
            ok, frame = cap.read()
            if not ok:
                break
            if (frame_idx - int(start_sec * fps)) % step == 0:
                total_sampled += 1
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                try:
                    faces = detect_faces_in_frame(rgb, mp_detector=mp_detector, cv_cascade=cv_cascade)
                except Exception as exc:
                    log.debug("Face detection frame skipped (%s)", exc)
                    faces = []
                t_rel = (frame_idx / max(fps, 1.0)) - start_sec

                if faces:
                    faces_sorted = sorted(faces, key=lambda item: item[0], reverse=True)
                    if len(faces_sorted) >= 2 and abs(faces_sorted[0][1] - faces_sorted[1][1]) >= 0.20:
                        wide_two_speaker_frames += 1
                    centers.append((t_rel, faces_sorted[0][1]))
                else:
                    prev_cx = centers[-1][1] if centers else 0.5
                    centers.append((t_rel, prev_cx))
            frame_idx += 1
    finally:
        cap.release()
        if mp_detector is not None and hasattr(mp_detector, "close"):
            mp_detector.close()

    if total_sampled > 0 and (wide_two_speaker_frames / total_sampled) > 0.45:
        return centers, "split"
    return centers, "single_ema"


def smooth_crop_x(centers: list[tuple[float, float]], alpha: float = 0.15, dwell_sec: float = 1.5) -> float:
    if not centers:
        return 0.5
    ema = centers[0][1]
    locked_x = ema
    last_switch_t = centers[0][0]
    smoothed: list[float] = []

    for t_rel, cx in centers:
        ema = alpha * cx + (1.0 - alpha) * ema
        if abs(ema - locked_x) > 0.08 and (t_rel - last_switch_t) >= dwell_sec:
            locked_x = ema
            last_switch_t = t_rel
        smoothed.append(locked_x)
    return float(np.median(smoothed))


def format_ass_time(sec: float) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def sanitize_ass_text(raw: str) -> str:
    return re.sub(r"[{}\\\r\n]+", "", raw).strip()


def _ass_font_family(script_info: tuple[str, str] | None) -> str:
    """Real fontconfig family names for libass (e.g. there is no 'Noto Sans Korean')."""
    if not script_info:
        return "Noto Sans"
    lang, name = script_info
    return {
        "ja": "Noto Sans CJK JP", "ko": "Noto Sans CJK KR", "zh": "Noto Sans CJK SC",
        "ml": "Noto Sans Malayalam", "hi": "Noto Sans Devanagari", "bn": "Noto Sans Bengali",
        "pa": "Noto Sans Gurmukhi", "gu": "Noto Sans Gujarati", "ta": "Noto Sans Tamil",
        "te": "Noto Sans Telugu", "kn": "Noto Sans Kannada", "th": "Noto Sans Thai",
        "ar": "Noto Sans Arabic", "he": "Noto Sans Hebrew",
    }.get(lang, f"Noto Sans {name}")


def write_ass_captions(
    segments: list[IndexedSegment],
    start_seg_id: int,
    end_seg_id: int,
    clip_start: float,
    ass_path: Path,
    hook_overlay: str = "",
    target_size: tuple[int, int] = (1080, 1920),
    light_theme: bool = False,
    middle_band: bool = False,
) -> None:
    res_x, res_y = target_size
    if (light_theme or middle_band) and res_y >= res_x:
        cap_margin_v = int(res_y * 0.44)  # Sits cleanly in the middle band between top visual card & bottom mascot
    else:
        cap_margin_v = int(res_y * (0.18 if res_y >= res_x else 0.08))
    hook_margin_v = int(res_y * (0.12 if res_y >= res_x else 0.06))
    font_default = 70 if res_y >= 1350 else 44
    font_hook = 56 if res_y >= 1350 else 38
    in_clip = [sg.text for sg in segments if start_seg_id <= sg.segment_id <= end_seg_id] or [sg.text for sg in segments[:3]]
    sample_ass = f"{hook_overlay} " + " ".join(in_clip)
    script_info = _detect_script(sample_ass)
    ass_font = _ass_font_family(script_info)
    if light_theme:
        prim_c, hi_c, out_c, back_c, out_w = "&H00241E1C", "&H002258E2", "&H00F4EFE6", "&H00F4EFE6", 2
    else:
        prim_c, hi_c, out_c, back_c, out_w = "&H00FFFFFF", "&H0000D7FF", "&H00000000", "&H80000000", 4
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{ass_font},{font_default},{prim_c},{hi_c},{out_c},{back_c},-1,0,0,0,100,100,0,0,1,{out_w},0,2,70,70,{cap_margin_v},1
Style: HookBanner,{ass_font},{font_hook},{hi_c},{prim_c},{out_c},&H99000000,-1,0,0,0,100,100,0,0,3,3,0,8,80,80,{hook_margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    clean_hook = sanitize_ass_text(hook_overlay).upper()
    if clean_hook:
        lines.append(
            f"Dialogue: 1,{format_ass_time(0.0)},{format_ass_time(3.5)},HookBanner,,0,0,0,,{clean_hook}"
        )

    selected = [s for s in segments if start_seg_id <= s.segment_id <= end_seg_id]

    for seg in selected:
        words = seg.words
        for idx in range(0, len(words), 4):
            chunk = words[idx: idx + 4]
            for active_i, active_w in enumerate(chunk):
                t0 = max(0.0, active_w.start - clip_start)
                t1 = max(t0 + 0.12, active_w.end - clip_start)
                rendered_tokens: list[str] = []
                for j, w in enumerate(chunk):
                    clean = sanitize_ass_text(w.word).upper()
                    if not clean:
                        continue
                    if j == active_i:
                        rendered_tokens.append(r"{\c" + hi_c.replace("&H00", "&H") + "&}" + clean + r"{\c" + prim_c.replace("&H00", "&H") + "&}")
                    else:
                        rendered_tokens.append(clean)
                if rendered_tokens:
                    lines.append(
                        f"Dialogue: 0,{format_ass_time(t0)},{format_ass_time(t1)},Default,,0,0,0,,{' '.join(rendered_tokens)}"
                    )

    ass_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_vertical_short(
    video_path: Path,
    meta: dict[str, Any],
    start_sec: float,
    end_sec: float,
    ass_path: Path,
    out_mp4: Path,
    norm_cx: float,
    layout_mode: str,
    art_style: str = "original",
    aspect_ratio: str = "9:16",
) -> None:
    src_w, src_h = meta["width"], meta["height"]
    out_w, out_h = ASPECT_RATIOS.get(aspect_ratio, (1080, 1920))
    target_ratio = out_w / float(out_h)
    src_ratio = src_w / float(max(src_h, 1))
    duration_sec = min(58.5, max(1.0, end_sec - start_sec))
    is_matching_ratio = abs(src_ratio - target_ratio) < 0.05
    ass_escaped = escape_ffmpeg_filter_path(ass_path)
    style_vf = FFMPEG_ART_STYLE_FILTERS.get((art_style or "original").lower(), "")
    style_chain = f"{style_vf}," if style_vf else ""

    if is_matching_ratio:
        vf = (
            f"scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,"
            f"pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2,{style_chain}ass='{ass_escaped}'"
        )
        filter_args = ["-vf", vf]
    elif aspect_ratio == "9:16" and layout_mode == "split":
        fc = (
            f"[0:v]split=2[left][right];"
            f"[left]crop=trunc(iw/4)*2:trunc(ih/2)*2:0:0,"
            f"scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[top];"
            f"[right]crop=trunc(iw/4)*2:trunc(ih/2)*2:trunc(iw/4)*2:0,"
            f"scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[bot];"
            f"[top][bot]vstack=inputs=2,{style_chain}ass='{ass_escaped}'[vout]"
        )
        filter_args = ["-filter_complex", fc, "-map", "[vout]", "-map", "0:a:0"]
    elif src_ratio > target_ratio:
        crop_w = int((src_h * target_ratio) // 2 * 2)
        crop_w = min(crop_w, (src_w // 2) * 2)
        x_offset = int(np.clip(norm_cx * src_w - crop_w / 2, 0, src_w - crop_w))
        x_offset = (x_offset // 2) * 2
        vf = f"crop={crop_w}:{(src_h // 2) * 2}:{x_offset}:0,scale={out_w}:{out_h},{style_chain}ass='{ass_escaped}'"
        filter_args = ["-vf", vf]
    else:
        vf = (
            f"scale={out_w}:{out_h}:force_original_aspect_ratio=increase,"
            f"crop={out_w}:{out_h},{style_chain}ass='{ass_escaped}'"
        )
        filter_args = ["-vf", vf]

    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start_sec:.3f}",
        "-i", str(video_path),
        "-t", f"{duration_sec:.3f}",
        *filter_args,
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
        "-movflags", "+faststart",
        str(out_mp4),
    ]
    run_cmd(cmd)


def run_clipping_engine(
    url: str,
    job_dir: Path,
    brain: CompanyBrain,
    max_clips: int = 3,
    device: str = "auto",
    model_name: str = "large-v3-turbo",
    allow_all_licenses: bool = False,
    public_dir: Path | None = None,
    art_style: str = "original",
    aspect_ratio: str = "9:16",
    slice_start: str = "",
) -> dict[str, Any]:
    slice_start_sec = _parse_timestamp_sec(slice_start)
    item_key = f"clip_url:{url.strip()}" + (f"@s={slice_start_sec}" if slice_start_sec is not None else "")
    brain.check_pre_flight(item_key, estimated_cost_usd=0.25)

    out_dir = job_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    video_path, _ = ingest_video(
        url,
        job_dir,
        require_cc=not allow_all_licenses,
        allowlisted_channels=brain.allowlisted_channels,
        slice_start_sec=slice_start_sec,
    )
    meta = ffprobe_metadata(video_path, min_duration=15.0)
    actual_device = resolve_device(device)
    compute_type = "float16" if actual_device == "cuda" else "int8"
    segments, lang = transcribe_with_whisperx(
        video_path,
        job_dir,
        device=actual_device,
        model_name=model_name,
        compute_type=compute_type,
    )
    seg_map = {s.segment_id: s for s in segments}

    council = AICouncil()
    council_specs = council.run_6_brain_clip_council(segments, brain=brain, max_clips=max_clips)
    if not council_specs:
        raise ValueError("DEAD_LETTER: Transcript produced 0 usable speech windows.")

    rendered: list[ClipSpec] = []
    exported_mp4s: list[Path] = []
    for idx, c_spec in enumerate(council_specs, start=1):
        clip_id = f"clip_{idx:02d}"
        file_stem = f"clip_{_run_tag()}_{idx:02d}"
        s_id = int(c_spec["start_segment_id"])
        e_id = int(c_spec["end_segment_id"])
        start_sec = seg_map[s_id].start
        end_sec = min(float(meta["duration"]), start_sec + 58.0, max(start_sec + 12.0, seg_map[e_id].end))
        hook_overlay = str(c_spec.get("hook_overlay", ""))
        yt_title = str(c_spec.get("yt_title", f"Highlight {clip_id} #Shorts"))
        ig_caption = str(c_spec.get("ig_caption", "Full breakdown via link in bio."))
        council_score = float(c_spec.get("council_score", 9.0))

        centers, layout_mode = analyze_speaker_centers(video_path, start_sec, end_sec)
        norm_cx = smooth_crop_x(centers)

        ass_path = out_dir / f"{clip_id}.ass"
        mp4_path = out_dir / f"{file_stem}.mp4"
        target_sz = ASPECT_RATIOS.get(aspect_ratio, (1080, 1920))
        write_ass_captions(segments, s_id, e_id, start_sec, ass_path, hook_overlay=hook_overlay, target_size=target_sz)
        render_vertical_short(
            video_path, meta, start_sec, end_sec, ass_path, mp4_path, norm_cx, layout_mode,
            art_style=art_style, aspect_ratio=aspect_ratio,
        )
        qa_ok = verify_rendered_mp4(mp4_path, min_duration=10.0, expected_size=target_sz)
        exported_mp4s.append(mp4_path)

        rendered.append(
            ClipSpec(
                clip_id=clip_id,
                start_segment_id=s_id,
                end_segment_id=e_id,
                start_sec=start_sec,
                end_sec=end_sec,
                duration_sec=round(end_sec - start_sec, 2),
                mp4_path=str(mp4_path),
                layout_mode=layout_mode,
                qa_verified=qa_ok,
                yt_title=yt_title,
                ig_caption=ig_caption,
                hook_overlay=hook_overlay,
                council_score=council_score,
                council_models_used=list(council.models_called),
                contains_synthetic_media=False,
                source_url=url,
            )
        )

    export_to_public_dir(exported_mp4s, public_dir)
    cleanup_heavy_temp_files(job_dir)

    result = {
        "engine": "clipping",
        "status": "APPROVAL_PENDING",
        "source_url": url,
        "language": lang,
        "council_models_used": list(council.models_called),
        "clips": [asdict(c) for c in rendered],
    }
    brain.record_completion(
        item_key,
        "clipping",
        0.25,
        {"clip_count": len(rendered), "source_url": url, "council_models": list(council.models_called)},
    )
    return result


# ============================================================================
# 7. ENGINE C: B2B LEAD, PROPOSAL & INVOICE ENGINE (`--engine b2b_agency`)
# ============================================================================

def run_b2b_agency_engine(
    client_name: str,
    discovery_notes: str,
    price_usd: float,
    job_dir: Path,
    brain: CompanyBrain,
    public_dir: Path | None = None,
) -> dict[str, Any]:
    item_key = f"b2b_client:{client_name.lower().strip()}"
    brain.check_pre_flight(item_key, estimated_cost_usd=0.05)

    out_dir = job_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = _safe_slug(client_name, prefix="client")

    notes_clean = discovery_notes.strip() or "No discovery notes were supplied; scope to be confirmed with the client on a call."
    council = AICouncil()
    copy_spec = council.run_6_brain_copy_council(
        f"AI Automation Proposal for {client_name}",
        discovery_notes.strip(),
        brain,
        default_points=[
            "Automated workflow discovery & architecture setup",
            "Custom AI content and operations pipeline deployment",
            "Weekly reporting, QA checks, and team handoff",
        ],
    )
    deliverable_points = copy_spec.get("points") or [
        "Automated workflow discovery & architecture setup",
        "Custom AI content and operations pipeline deployment",
        "Weekly reporting, QA checks, and team handoff",
    ]
    deliverables_md = "\n".join(f"{i}. **{p}**" for i, p in enumerate(deliverable_points, start=1))

    ops_summary_path = out_dir / f"b2b_{slug}_summary.md"
    ops_md = (
        f"# Discovery Call Summary — {client_name}\n\n"
        f"## Captured Notes\n{notes_clean}\n\n"
        f"## Recommended Automation Pillars\n{deliverables_md}\n\n"
        f"## Action Items & Owners\n"
        f"- **Operations Agent:** Lock scope against `03_offers_pricing.md`.\n"
        f"- **Deals Agent:** Draft turnkey automation proposal at **${price_usd:,.2f}**.\n"
        f"- **Human Gate:** Review proposal and invoice before sending to {client_name}.\n"
    )
    ops_summary_path.write_text(ops_md, encoding="utf-8")

    proposal_path = out_dir / f"b2b_{slug}_proposal.md"
    proposal_md = (
        f"# AI Automation Proposal for {client_name}\n\n"
        f"## 1. Objective & Scope\n"
        f"Addressing key bottleneck identified in discovery: *{notes_clean}*\n\n"
        f"## 2. Proposed Solution & Deliverables\n"
        f"{deliverables_md}\n\n"
        f"## 3. Standard Offer & SLA Reference\n"
        f"{brain.offers_pricing}\n\n"
        f"## 4. Investment & Terms\n"
        f"- **Total Setup & Retainer:** ${price_usd:,.2f} USD\n"
        f"- **First Milestone (50% on sign-off):** ${price_usd / 2.0:,.2f} USD\n"
        f"- **Final Milestone (50% on delivery):** ${price_usd / 2.0:,.2f} USD\n"
    )
    proposal_path.write_text(proposal_md, encoding="utf-8")

    invoice_id = f"INV-{int(time.time())}"
    invoice_path = out_dir / f"b2b_{slug}_invoice.json"
    invoice_payload = {
        "invoice_id": invoice_id,
        "client_name": client_name,
        "amount_due_usd": round(price_usd / 2.0, 2),
        "total_contract_usd": round(price_usd, 2),
        "status": "APPROVAL_PENDING",
    }
    atomic_write_json(invoice_path, invoice_payload)
    export_to_public_dir([ops_summary_path, proposal_path, invoice_path], public_dir)

    result = {
        "engine": "b2b_agency",
        "status": "APPROVAL_PENDING",
        "client_name": client_name,
        "ops_summary_path": str(ops_summary_path),
        "proposal_path": str(proposal_path),
        "invoice_path": str(invoice_path),
        "invoice_id": invoice_id,
        "amount_due_usd": invoice_payload["amount_due_usd"],
        "council_models_used": copy_spec.get("council_models_used", []),
    }
    brain.record_completion(item_key, "b2b_agency", 0.05, result)
    return result


# ============================================================================
# 8. ENGINE D: BRANDED 5-SLIDE IG CAROUSEL & FUNNEL (`--engine carousel_funnel`)
# ============================================================================

def _load_ttf_font(size: int, bold: bool = False, text_sample: str = "") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return _load_font(size, bold=bold, text_sample=text_sample)


def _wrap_text_lines(text: str, max_chars_per_line: int = 24, max_lines: int = 5) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for w in words:
        if len(w) > max_chars_per_line:
            # Unspaced scripts (CJK/Thai) and long tokens: split into chunks instead of truncating the text away.
            if cur:
                lines.append(" ".join(cur))
                cur = []
            chunks = [w[i:i + max_chars_per_line] for i in range(0, len(w), max_chars_per_line)]
            lines.extend(chunks[:-1])
            cur = [chunks[-1]]
            continue
        cur.append(w)
        if len(" ".join(cur)) > max_chars_per_line:
            lines.append(" ".join(cur[:-1]) if len(cur) > 1 else cur[0])
            cur = [w] if len(cur) > 1 else []
    if cur:
        lines.append(" ".join(cur))
    return lines[:max_lines]


def _render_brand_slide_png(
    out_png: Path,
    width: int,
    height: int,
    badge: str,
    headline: str,
    subline: str,
    footer: str,
) -> None:
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(60, 80), (width - 60, 92)], fill=(56, 189, 248))
    draw.rounded_rectangle([(60, 130), (width - 60, height - 130)], radius=32, outline=(56, 189, 248), width=3)

    _sample = f"{badge} {headline} {subline} {footer}"
    font_lg = _load_ttf_font(52, bold=True, text_sample=_sample)
    font_md = _load_ttf_font(32, bold=False, text_sample=_sample)

    draw.text((110, 190), badge[:40], fill=(250, 204, 21), font=font_md)

    y = 310
    for line in _wrap_text_lines(headline, max_chars_per_line=22, max_lines=5):
        draw.text((110, y), line, fill=(255, 255, 255), font=font_lg)
        y += 76

    y += 40
    for s_line in _wrap_text_lines(subline, max_chars_per_line=38, max_lines=3):
        draw.text((110, y), s_line, fill=(148, 163, 184), font=font_md)
        y += 48

    draw.text((110, height - 220), footer[:48], fill=(56, 189, 248), font=font_md)
    img.save(out_png, format="PNG")


def run_carousel_funnel_engine(
    topic: str,
    points: list[str],
    job_dir: Path,
    brain: CompanyBrain,
    public_dir: Path | None = None,
) -> dict[str, Any]:
    item_key = f"carousel:{topic.lower().strip()}"
    brain.check_pre_flight(item_key, estimated_cost_usd=0.04)

    out_dir = job_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    council = AICouncil()
    clean_pts = [p.strip() for p in points if p and p.strip()]
    copy_spec = council.run_6_brain_copy_council(topic, "; ".join(clean_pts) or topic, brain)
    padded_points = [str(p).strip() for p in (copy_spec.get("points") or []) if str(p).strip()]
    fallback_pts = [
        f"Master the core strategy behind {topic}",
        "Automate the repetitive steps with repeatable workflows",
        "Measure results weekly and scale what converts",
    ]
    for fp in fallback_pts:
        if len(padded_points) >= 3:
            break
        padded_points.append(fp)
    slug = _safe_slug(topic, prefix="carousel")

    slides_spec = [
        (f"SLIDE 01 / {copy_spec['hook_badge'][:18]}", topic.upper(), "Swipe to see the exact 4-stage blueprint ->"),
        ("SLIDE 02 / STEP 1", padded_points[0], "Stage 1: Foundation"),
        ("SLIDE 03 / STEP 2", padded_points[1], "Stage 2: Execution"),
        ("SLIDE 04 / STEP 3", padded_points[2], "Stage 3: Governance Gate"),
        ("SLIDE 05 / ACTION", "GET THE FULL BLUEPRINT & TOOLS", "Check the link in bio to deploy this today."),
    ]

    slide_paths: list[str] = []
    slide_jpg_paths: list[str] = []
    slide_files: list[Path] = []
    for idx, (badge, headline, subline) in enumerate(slides_spec, start=1):
        p = out_dir / f"carousel_{slug}_{idx:02d}.png"
        _render_brand_slide_png(
            p,
            width=1080,
            height=1350,
            badge=badge,
            headline=headline,
            subline=subline,
            footer=f"JAGNOR AI • {idx}/5",
        )
        # Instagram's Graph API only accepts JPEG for image_url, so ship a JPEG twin of every PNG slide.
        jpg = p.with_suffix(".jpg")
        with Image.open(p) as _im:
            _im.convert("RGB").save(jpg, format="JPEG", quality=92, optimize=True)
        slide_paths.append(str(p))
        slide_jpg_paths.append(str(jpg))
        slide_files.extend([p, jpg])

    export_to_public_dir(slide_files, public_dir)

    result = {
        "engine": "carousel_funnel",
        "status": "APPROVAL_PENDING",
        "topic": topic,
        "slide_paths": slide_paths,
        "slide_jpg_paths": slide_jpg_paths,
        "ig_caption": copy_spec["ig_caption"],
        "council_models_used": copy_spec["council_models_used"],
    }
    brain.record_completion(item_key, "carousel_funnel", 0.04, result)
    return result


# ============================================================================
# 8B. ENGINE E: CANVA / FABBLER / DIGITAL MAKER / QWEN DROP (`--engine raw_video_drop`)
# ============================================================================

def run_raw_video_drop_engine(
    inbox_dir: Path,
    job_dir: Path,
    brain: CompanyBrain,
    device: str = "auto",
    model_name: str = "base",
    public_dir: Path | None = None,
    art_style: str = "original",
    aspect_ratio: str = "9:16",
) -> dict[str, Any]:
    """
    Scans `inbox_dir` (e.g. `inbox_videos/`) for the next unprocessed MP4/MOV exported from
    Canva (Fabbler.ai), Digital Maker AI, or Qwen/Wan, auto-transcribes (if audio has speech),
    runs the 4-Brain Free AI Council for hook/title/caption, formats to 1080x1920 9:16 with +faststart,
    marks `contains_synthetic_media=True`, and queues it for YouTube Shorts + Instagram Reels.
    """
    inbox_dir.mkdir(parents=True, exist_ok=True)
    video_files = sorted(
        f for f in inbox_dir.iterdir()
        if f.is_file() and f.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"}
    )
    target_file: Path | None = None
    for vf in video_files:
        if f"raw_drop:{vf.name}" not in brain.processed_items:
            target_file = vf
            break

    if target_file is None:
        raise FileNotFoundError(
            f"DEAD_LETTER: No unprocessed MP4/MOV files found in {inbox_dir}. Drop a Canva/Qwen export there first."
        )

    item_key = f"raw_drop:{target_file.name}"
    brain.check_pre_flight(item_key, estimated_cost_usd=0.10)

    out_dir = job_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    working_src = job_dir / "dropped_source.mp4"
    probe_raw = run_cmd([
        "ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(target_file)
    ])
    pdata = json.loads(probe_raw.stdout)
    has_audio = any(s.get("codec_type") == "audio" for s in pdata.get("streams", []))
    raw_dur = float(pdata.get("format", {}).get("duration", 15.0))

    if not has_audio:
        log.info("Dropped video %s has no audio track (e.g. Qwen/Wan); muxing silent 48kHz track...", target_file.name)
        v_codec = ["-c:v", "copy"] if target_file.suffix.lower() == ".mp4" else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        run_cmd([
            "ffmpeg", "-y",
            "-i", str(target_file),
            "-f", "lavfi", "-t", f"{raw_dur:.3f}", "-i", "anullsrc=channel_layout=mono:sample_rate=48000",
            *v_codec, "-c:a", "aac", "-ar", "48000", "-shortest",
            str(working_src),
        ])
    else:
        shutil.copy2(target_file, working_src)

    meta = ffprobe_metadata(working_src, min_duration=5.0)
    duration_sec = min(58.0, meta["duration"])
    clean_stem = re.sub(r"[_-]+", " ", target_file.stem).strip() or "AI Story Video"

    segments: list[IndexedSegment] = []
    lang = "en"
    if has_audio:
        try:
            actual_device = resolve_device(device)
            compute_type = "float16" if actual_device == "cuda" else "int8"
            segments, lang = transcribe_with_whisperx(
                working_src, job_dir, device=actual_device, model_name=model_name, compute_type=compute_type
            )
        except Exception as exc:
            log.info("Skipping speech transcription on dropped video (%s); using 4-Brain Free AI Council hook banner only.", exc)

    council = AICouncil()
    council_specs = council.run_6_brain_clip_council(segments, brain=brain, max_clips=1) if segments else []
    if council_specs:
        c_spec = council_specs[0]
        s_id = int(c_spec["start_segment_id"])
        e_id = int(c_spec["end_segment_id"])
        seg_map = {s.segment_id: s for s in segments}
        start_sec = seg_map[s_id].start
        end_sec = min(start_sec + 58.0, max(start_sec + 5.0, seg_map[e_id].end))
        hook_overlay = str(c_spec.get("hook_overlay") or clean_stem[:36]).upper()
        yt_title = str(c_spec.get("yt_title") or f"{clean_stem[:48]} #Shorts")
        ig_caption = str(c_spec.get("ig_caption") or f"{clean_stem} — created with AI. Full tools in bio.")
        council_score = float(c_spec.get("council_score") or 9.2)
    else:
        copy_spec = council.run_6_brain_copy_council(clean_stem, f"AI generated short video: {clean_stem}", brain)
        s_id, e_id = 0, 0
        start_sec, end_sec = 0.0, duration_sec
        hook_overlay = copy_spec["hook_badge"]
        yt_title = copy_spec["yt_title"]
        ig_caption = copy_spec["ig_caption"]
        council_score = 9.0

    centers, layout_mode = analyze_speaker_centers(working_src, start_sec, end_sec)
    norm_cx = smooth_crop_x(centers)

    ass_path = out_dir / "drop_01.ass"
    safe_slug = re.sub(r"[^a-zA-Z0-9]+", "_", target_file.stem)[:24].strip("_") or "01"
    mp4_path = out_dir / f"drop_{safe_slug}_{_run_tag()}.mp4"
    target_sz = ASPECT_RATIOS.get(aspect_ratio, (1080, 1920))
    write_ass_captions(segments, s_id, e_id, start_sec, ass_path, hook_overlay=hook_overlay, target_size=target_sz)
    render_vertical_short(working_src, meta, start_sec, end_sec, ass_path, mp4_path, norm_cx, layout_mode, art_style=art_style, aspect_ratio=aspect_ratio)
    qa_ok = verify_rendered_mp4(mp4_path, min_duration=5.0, expected_size=target_sz)

    export_to_public_dir([mp4_path], public_dir)
    if working_src.exists():
        working_src.unlink()
    cleanup_heavy_temp_files(job_dir)

    clip_obj = ClipSpec(
        clip_id="drop_01",
        start_segment_id=s_id,
        end_segment_id=e_id,
        start_sec=start_sec,
        end_sec=end_sec,
        duration_sec=round(end_sec - start_sec, 2),
        mp4_path=str(mp4_path),
        layout_mode=layout_mode,
        qa_verified=qa_ok,
        yt_title=yt_title,
        ig_caption=ig_caption,
        hook_overlay=hook_overlay,
        council_score=council_score,
        council_models_used=list(council.models_called),
        contains_synthetic_media=True,
        source_url=f"inbox:{target_file.name}",
    )

    result = {
        "engine": "clipping",
        "source_mode": "raw_video_drop",
        "status": "APPROVAL_PENDING",
        "source_url": f"inbox:{target_file.name}",
        "language": lang,
        "council_models_used": list(council.models_called),
        "clips": [asdict(clip_obj)],
    }
    brain.record_completion(item_key, "raw_video_drop", 0.10, {"file": target_file.name, "mp4_path": str(mp4_path)})
    return result


# ============================================================================
# 8C. ENGINE F: 100% HANDS-FREE AI FACELESS GENERATOR (`--engine ai_faceless`)
# ============================================================================

def _trim_words(text: str, max_chars: int = 58) -> str:
    """Trim text cleanly on a word boundary so fallback cards never slice mid-word."""
    clean = " ".join(text.split()).strip()
    if len(clean) <= max_chars:
        return clean
    cut = clean[:max_chars].rsplit(" ", 1)[0].rstrip(",;:- ")
    return (cut or clean[:max_chars]) + "..."


def _extract_narration_search_query(narration: str, explicit_query: str, topic: str) -> str:
    """
    Ensures every scene's visual search query stays tightly locked to the exact concrete
    subject spoken in that scene's narration (never generic random filler).
    """
    q = " ".join(re.sub(r"[^a-zA-Z0-9\s\-]+", " ", str(explicit_query or "")).split()).strip()
    if len(q.split()) >= 2:
        return q[:64]
    stopwords = {
        "the", "and", "for", "that", "this", "with", "from", "into", "your", "they", "them",
        "their", "what", "when", "where", "which", "about", "there", "these", "those", "most",
        "people", "never", "really", "just", "over", "under", "still", "every", "single",
        "would", "could", "should", "have", "been", "were", "will", "more", "than", "then",
    }
    words = [w for w in re.findall(r"[A-Za-z0-9\-]+", narration) if len(w) > 3 and w.lower() not in stopwords]
    base_topic = " ".join(topic.split()[:3])
    picked = " ".join(words[:3])
    return f"{base_topic} {picked}".strip()[:64] or topic[:64]


def _center_crop_9x16(im: Image.Image, out_img: Path) -> None:
    rgb = im.convert("RGB")
    w, h = rgb.size
    target_ratio = 9.0 / 16.0
    cur_ratio = w / float(max(h, 1))
    if cur_ratio > target_ratio:
        new_w = int(h * target_ratio)
        x0 = max(0, (w - new_w) // 2)
        rgb = rgb.crop((x0, 0, x0 + new_w, h))
    else:
        new_h = int(w / target_ratio)
        y0 = max(0, (h - new_h) // 2)
        rgb = rgb.crop((0, y0, w, y0 + new_h))
    rgb.resize((1080, 1920), Image.Resampling.LANCZOS).save(out_img, format="PNG")


def _apply_art_style_filter(im: Image.Image, art_style: str) -> Image.Image:
    """
    Transforms any fallback photo using OpenCV so it matches the user's chosen `art_style`
    (anime cel-shading, comic ink outlines, cyberpunk neon, oil painting, minimalist sketch,
    or dark cinematic film grading) — never raw unstyled photography.
    """
    try:
        bgr = cv2.cvtColor(np.asarray(im.convert("RGB")), cv2.COLOR_RGB2BGR)
        style = (art_style or "dark_cinematic").lower()
        if style == "original":
            return im.convert("RGB")

        if style in {"anime", "comic_book"}:
            # Bilateral smoothing + cel-shaded color quantization + crisp dark ink edges
            smooth = cv2.bilateralFilter(bgr, d=9, sigmaColor=85, sigmaSpace=85)
            smooth = cv2.bilateralFilter(smooth, d=9, sigmaColor=85, sigmaSpace=85)
            step = 32 if style == "comic_book" else 24
            quant = ((smooth // step) * step + step // 2).astype(np.uint8)
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            edges = cv2.adaptiveThreshold(
                cv2.medianBlur(gray, 5), 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 6
            )
            if style == "comic_book":
                # Slightly thicken comic ink lines for graphic-novel consistency
                edges = cv2.erode(edges, np.ones((2, 2), np.uint8), iterations=1)
            edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            out = cv2.bitwise_and(quant, edges_bgr)
            hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1.35 if style == "comic_book" else 1.28), 0, 255)
            out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        elif style == "cyberpunk":
            # Smooth neon noir + high-contrast cyan/magenta split-tone + dark shadow crush
            smooth = cv2.bilateralFilter(bgr, d=9, sigmaColor=65, sigmaSpace=65).astype(np.float32)
            smooth[:, :, 0] = np.clip(smooth[:, :, 0] * 1.38 + 22, 0, 255)  # Electric cyan/blue
            smooth[:, :, 1] = np.clip(smooth[:, :, 1] * 0.82, 0, 255)
            smooth[:, :, 2] = np.clip(smooth[:, :, 2] * 1.32 + 16, 0, 255)  # Neon magenta/red
            out = cv2.convertScaleAbs(smooth.astype(np.uint8), alpha=1.18, beta=-16)
        elif style == "oil_painting":
            # Rich classical painterly brushstroke texture + warm museum chiaroscuro contrast
            painted = cv2.stylization(bgr, sigma_s=75, sigma_r=0.40)
            painted = cv2.stylization(painted, sigma_s=45, sigma_r=0.55)
            f_p = painted.astype(np.float32)
            f_p[:, :, 0] = np.clip(f_p[:, :, 0] * 0.90, 0, 255)
            f_p[:, :, 1] = np.clip(f_p[:, :, 1] * 1.02, 0, 255)
            f_p[:, :, 2] = np.clip(f_p[:, :, 2] * 1.12 + 6, 0, 255)
            out = cv2.convertScaleAbs(f_p.astype(np.uint8), alpha=1.12, beta=-8)
        elif style == "minimalist_sketch":
            # High-contrast editorial ink & charcoal sketch on dark slate paper with warm gold highlights
            gray_sketch, _ = cv2.pencilSketch(bgr, sigma_s=55, sigma_r=0.06, shade_factor=0.035)
            inv = cv2.normalize(255 - gray_sketch, None, 0, 255, cv2.NORM_MINMAX).astype(np.float32)
            out = np.zeros_like(bgr)
            out[:, :, 0] = np.clip(20 + inv * 0.42, 0, 255).astype(np.uint8)
            out[:, :, 1] = np.clip(26 + inv * 0.74, 0, 255).astype(np.uint8)
            out[:, :, 2] = np.clip(34 + inv * 0.92, 0, 255).astype(np.uint8)
        elif style == "3d_pixar":
            # Soft global-illumination stylized 3D shading + vibrant warm highlights
            smooth = cv2.edgePreservingFilter(bgr, flags=1, sigma_s=65, sigma_r=0.48)
            smooth = cv2.bilateralFilter(smooth, d=7, sigmaColor=55, sigmaSpace=55)
            hsv = cv2.cvtColor(smooth, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.32, 0, 255)
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.08, 0, 255)
            out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        else:
            # dark_cinematic: moody teal/amber film grade + soft edge vignette
            h_im, w_im = bgr.shape[:2]
            kx = cv2.getGaussianKernel(w_im, w_im * 0.62)
            ky = cv2.getGaussianKernel(h_im, h_im * 0.62)
            mask = (ky @ kx.T)
            mask = (mask / max(float(mask.max()), 1e-6)) * 0.45 + 0.55
            out_f = bgr.astype(np.float32)
            out_f[:, :, 0] = np.clip(out_f[:, :, 0] * 1.12, 0, 255)
            out_f[:, :, 1] = np.clip(out_f[:, :, 1] * 0.95, 0, 255)
            out_f[:, :, 2] = np.clip(out_f[:, :, 2] * 1.08, 0, 255)
            out_f *= mask[:, :, None]
            out = cv2.convertScaleAbs(np.clip(out_f, 0, 255).astype(np.uint8), alpha=1.14, beta=-18)

        return Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))


    except Exception as exc:
        log.debug("Art style filter [%s] fallback (%s); returning RGB image.", art_style, exc)
        return im.convert("RGB")

def _fetch_openrouter_ai_image(full_prompt: str, out_img: Path, scene_num: int) -> bool:
    """
    Generates a true 9:16 AI-styled image via OpenRouter's Image API (`POST /api/v1/images`)
    using `OPENROUTER_API_KEY`, matching the exact topic, theme, character, and art_style.
    """
    or_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not or_key:
        return False
    models = [
        os.environ.get("OPENROUTER_IMAGE_MODEL", "").strip(),
        "bytedance-seed/seedream-4.5",
        "black-forest-labs/flux.2-klein-4b",
    ]
    for model in [m for m in dict.fromkeys(models) if m]:
        payload = {
            "model": model,
            "prompt": full_prompt[:900],
            "aspect_ratio": "9:16",
            "n": 1,
        }
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/images",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {or_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/jagnor110-cell",
                "X-Title": "Jagnor AI Studio",
            },
            method="POST",
        )
        try:
            raw, _ = urlopen_with_retry(req, timeout=60, max_attempts=1)
            data = json.loads(raw.decode("utf-8"))
            items = data.get("data") or []
            if not items:
                continue
            item = items[0]
            img_bytes: bytes | None = None
            if item.get("b64_json"):
                b64_str = str(item["b64_json"])
                if "," in b64_str and b64_str.startswith("data:"):
                    b64_str = b64_str.split(",", 1)[1]
                img_bytes = base64.b64decode(b64_str)
            elif item.get("url"):
                with urllib.request.urlopen(urllib.request.Request(str(item["url"]), headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as resp:
                    img_bytes = resp.read()
            if img_bytes and len(img_bytes) > 10000:
                tmp_f = out_img.with_suffix(".or.img")
                tmp_f.write_bytes(img_bytes)
                with Image.open(tmp_f) as im:
                    _center_crop_9x16(im, out_img)
                tmp_f.unlink(missing_ok=True)
                log.info("Scene %d custom AI art generated via OpenRouter (%s).", scene_num, model)
                return True
        except Exception as exc:
            err_s = str(exc)
            log.debug("Scene %d OpenRouter image (%s) skipped: %s", scene_num, model, err_s)
            if any(code in err_s for code in ("HTTP 401", "HTTP 402", "HTTP 403")):
                break
            continue
    return False


def _fetch_hf_ai_image(full_prompt: str, out_img: Path, scene_num: int) -> bool:
    """Generates a custom 9:16 AI image via Hugging Face Inference API (`HF_TOKEN`) if configured."""
    hf_key = os.environ.get("HF_TOKEN", "").strip()
    if not hf_key:
        return False
    req = urllib.request.Request(
        "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell",
        data=json.dumps({"inputs": full_prompt[:600]}).encode("utf-8"),
        headers={"Authorization": f"Bearer {hf_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        raw, _ = urlopen_with_retry(req, timeout=60, max_attempts=1)
        if len(raw) > 10000:
            tmp_f = out_img.with_suffix(".hf.img")
            tmp_f.write_bytes(raw)
            with Image.open(tmp_f) as im:
                _center_crop_9x16(im, out_img)
            tmp_f.unlink(missing_ok=True)
            log.info("Scene %d custom AI art generated via Hugging Face FLUX.", scene_num)
            return True
    except Exception as exc:
        log.debug("Scene %d HF FLUX image skipped: %s", scene_num, exc)
    return False


def _fetch_wikimedia_topic_image(query: str, out_img: Path, scene_num: int, used_urls: set[str] | None = None) -> bool:
    """
    Fetches real, topic-accurate public-domain / CC photographs matching the exact scene
    narration from Wikimedia Commons (100% free, zero API key, zero watermarks).
    """
    clean_q = " ".join(re.sub(r"[^a-zA-Z0-9\s\-]+", " ", query).split()).strip()
    if not clean_q:
        return False
    api_url = (
        "https://commons.wikimedia.org/w/api.php?"
        + urllib.parse.urlencode({
            "action": "query",
            "generator": "search",
            "gsrnamespace": "6",
            "gsrsearch": f"{clean_q} filetype:bitmap",
            "gsrlimit": "10",
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": "1200",
            "format": "json",
        })
    )
    try:
        req = urllib.request.Request(
            api_url,
            headers={"User-Agent": "JagnorAIStudio/2.0 (https://github.com/jagnor110-cell)"},
        )
        raw, _ = urlopen_with_retry(req, timeout=20, max_attempts=2)
        data = json.loads(raw.decode("utf-8"))
        pages = list((data.get("query") or {}).get("pages", {}).values())
        if not pages:
            return False

        candidates: list[tuple[int, str]] = []
        for p in pages:
            title_low = str(p.get("title") or "").lower()
            if any(bad in title_low for bad in (".svg", ".pdf", ".tif", "logo", "icon", "flag_of", "diagram_blank", "map_blank", "page_", "_page", "book_", "text_", "scan", "manuscript", "title_page", "frontispiece", "letter_", "document", "signature")):
                continue
            infos = p.get("imageinfo") or []
            if not infos:
                continue
            info = infos[0]
            mime = str(info.get("mime") or "")
            if mime not in {"image/jpeg", "image/png", "image/webp"}:
                continue
            w = int(info.get("width") or 0)
            h = int(info.get("height") or 0)
            if w < 500 or h < 500:
                continue
            img_url = str(info.get("thumburl") or info.get("url") or "")
            if not img_url:
                continue
            if used_urls is not None and img_url in used_urls:
                continue
            # Prefer portrait/square high-res photos over ultra-wide panoramas
            aspect_penalty = 0 if (h / float(max(w, 1))) >= 0.65 else -5000
            candidates.append((w * h + aspect_penalty, img_url))

        if not candidates:
            return False
        candidates.sort(key=lambda x: x[0], reverse=True)
        chosen_url = candidates[0][1]

        img_req = urllib.request.Request(
            chosen_url,
            headers={"User-Agent": "JagnorAIStudio/2.0 (https://github.com/jagnor110-cell)"},
        )
        with urllib.request.urlopen(img_req, timeout=25) as resp:
            img_bytes = resp.read()
        if len(img_bytes) < 12000:
            return False

        tmp_img = out_img.with_suffix(".wiki.img")
        tmp_img.write_bytes(img_bytes)
        with Image.open(tmp_img) as im:
            _center_crop_9x16(im, out_img)
        tmp_img.unlink(missing_ok=True)
        if used_urls is not None:
            used_urls.add(chosen_url)
        log.info("Scene %d real topic photo loaded from Wikimedia Commons (%s).", scene_num, clean_q[:36])
        return True
    except Exception as exc:
        log.info("Scene %d Wikimedia Commons lookup unavailable (%s).", scene_num, exc)
        return False


def _fetch_pixabay_portrait_image(
    keywords: str,
    out_img: Path,
    scene_num: int,
    art_style: str = "dark_cinematic",
    used_urls: set[str] | None = None,
) -> bool:
    """Fetches a free, watermark-free 9:16 portrait HD photo or illustration from Pixabay API (`PIXABAY_API_KEY`)."""
    pixabay_key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not pixabay_key:
        return False
    clean_q = re.sub(r"[^a-zA-Z0-9\s]+", " ", keywords).strip() or "futuristic dark technology"
    prefer_illustration = art_style in {"anime", "comic_book", "3d_pixar", "minimalist_sketch", "oil_painting", "cyberpunk"}
    search_types = ["illustration", "all"] if prefer_illustration else ["all"]
    try:
        hits = []
        for img_type in search_types:
            search_url = (
                "https://pixabay.com/api/?"
                + urllib.parse.urlencode({
                    "key": pixabay_key,
                    "q": clean_q[:95],
                    "image_type": img_type,
                    "orientation": "vertical",
                    "safesearch": "true",
                    "per_page": 10,
                })
            )
            req = urllib.request.Request(search_url, headers={"User-Agent": "JagnorAIStudio/2.0"})
            raw, _ = urlopen_with_retry(req, timeout=25, max_attempts=2)
            data = json.loads(raw.decode("utf-8"))
            hits = data.get("hits") or []
            if hits:
                break
        if not hits:
            return False
        candidates = [
            h for h in hits
            if (h.get("largeImageURL") or h.get("webformatURL"))
            and (used_urls is None or (h.get("largeImageURL") or h.get("webformatURL")) not in used_urls)
        ] or hits
        chosen = candidates[(scene_num - 1) % len(candidates)]
        img_url = chosen.get("largeImageURL") or chosen.get("webformatURL")
        if not img_url:
            return False
        img_req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(img_req, timeout=30) as resp:
            img_bytes = resp.read()
        if len(img_bytes) < 10000:
            return False
        tmp_jpg = out_img.with_suffix(".pixabay.jpg")
        tmp_jpg.write_bytes(img_bytes)
        with Image.open(tmp_jpg) as im:
            rgb = im.convert("RGB")
            w, h = rgb.size
            target_ratio = 9.0 / 16.0
            cur_ratio = w / float(max(h, 1))
            if cur_ratio > target_ratio:
                new_w = int(h * target_ratio)
                x0 = max(0, (w - new_w) // 2)
                rgb = rgb.crop((x0, 0, x0 + new_w, h))
            else:
                new_h = int(w / target_ratio)
                y0 = max(0, (h - new_h) // 2)
                rgb = rgb.crop((0, y0, w, y0 + new_h))
            rgb.resize((1080, 1920), Image.Resampling.LANCZOS).save(out_img, format="PNG")
        tmp_jpg.unlink(missing_ok=True)
        if used_urls is not None:
            used_urls.add(img_url)
        log.info("Scene %d visual loaded from Pixabay HD (%s).", scene_num, clean_q[:30])
        return True
    except Exception as exc:
        log.info("Scene %d Pixabay API unavailable (%s).", scene_num, exc)
        return False




def _fetch_pixabay_scene_video(
    keywords: str,
    out_mp4: Path,
    dur: float,
    wav_p: Path,
    scene_num: int,
    art_style: str = "dark_cinematic",
    used_urls: set[str] | None = None,
) -> bool:
    """
    Fetches a real moving HD stock MP4 clip from Pixabay's free Video API (`https://pixabay.com/api/videos/`)
    using the user's existing `PIXABAY_API_KEY`, crops/scales it to 1080x1920, applies the chosen art style,
    and muxes the scene's voiceover audio.
    """
    pixabay_key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not pixabay_key:
        return False
    clean_q = re.sub(r"[^a-zA-Z0-9\s]+", " ", keywords).strip() or "futuristic dark technology"
    try:
        search_url = (
            "https://pixabay.com/api/videos/?"
            + urllib.parse.urlencode({
                "key": pixabay_key,
                "q": clean_q[:95],
                "safesearch": "true",
                "per_page": 10,
            })
        )
        req = urllib.request.Request(search_url, headers={"User-Agent": "JagnorAIStudio/2.0"})
        raw, _ = urlopen_with_retry(req, timeout=25, max_attempts=2)
        data = json.loads(raw.decode("utf-8"))
        hits = data.get("hits") or []
        if not hits:
            return False

        def _pick_url(h: dict[str, Any]) -> str:
            vids = h.get("videos") or {}
            for tier in ("medium", "large", "small", "tiny"):
                u = str((vids.get(tier) or {}).get("url") or "").strip()
                if u:
                    return u
            return ""

        candidates = [
            (h, _pick_url(h)) for h in hits
            if _pick_url(h) and (used_urls is None or _pick_url(h) not in used_urls)
        ]
        if not candidates:
            candidates = [(h, _pick_url(h)) for h in hits if _pick_url(h)]
        if not candidates:
            return False

        _, vid_url = candidates[(scene_num - 1) % len(candidates)]
        vid_req = urllib.request.Request(vid_url, headers={"User-Agent": "Mozilla/5.0"})
        max_bytes = 45 * 1024 * 1024
        with urllib.request.urlopen(vid_req, timeout=45) as resp:
            cl = resp.headers.get("Content-Length") if hasattr(resp, "headers") and resp.headers else None
            if cl and cl.isdigit() and int(cl) > max_bytes:
                log.info("Scene %d Pixabay video too large (%s bytes); falling back.", scene_num, cl)
                return False
            vid_bytes = resp.read(max_bytes + 1)
        if len(vid_bytes) < 25000 or len(vid_bytes) > max_bytes:
            return False

        raw_mp4 = out_mp4.with_suffix(".pixabay_raw.mp4")
        try:
            raw_mp4.write_bytes(vid_bytes)
            style_vf = FFMPEG_ART_STYLE_FILTERS.get((art_style or "dark_cinematic").lower(), "")
            style_chain = f",{style_vf}" if style_vf else ""
            vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30{style_chain},format=yuv420p"
            run_cmd([
                "ffmpeg", "-y",
                "-stream_loop", "-1", "-i", str(raw_mp4),
                "-i", str(wav_p),
                "-t", f"{dur:.3f}",
                "-map", "0:v:0", "-map", "1:a:0",
                "-vf", vf,
                "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
                "-shortest",
                str(out_mp4),
            ])
        finally:
            raw_mp4.unlink(missing_ok=True)
        if not out_mp4.exists() or out_mp4.stat().st_size < 10000:
            return False
        if used_urls is not None:
            used_urls.add(vid_url)
        log.info("Scene %d real moving HD video loaded from Pixabay Video API (%s).", scene_num, clean_q[:30])
        return True
    except Exception as exc:
        log.info("Scene %d Pixabay Video API unavailable (%s); falling back to AI art/photo.", scene_num, exc)
        return False


def _fetch_free_ai_scene_image(
    visual_prompt: str,
    out_img: Path,
    fallback_headline: str,
    scene_num: int,
    art_style: str = "dark_cinematic",
    stock_keywords: str = "",
    used_urls: set[str] | None = None,
) -> Path:
    """
    3-Layer Free Visual Chain:
      1) Pollinations.ai (`POLLINATIONS_API_KEY` on gen.pollinations.ai, or 1-shot legacy check; stops immediately on HTTP 401/402)
      2) Pixabay HD Portrait Photos & Illustrations (`PIXABAY_API_KEY` — 100% free, zero watermarks)
      3) Cleanly word-wrapped branded editorial card
    """
    style_suffix = gen_style_prompt(art_style)
    full_prompt = f"{visual_prompt}, {style_suffix}, vertical 9:16 composition, strictly no text, no letters, no logos, no street signs, no watermarks"
    encoded = urllib.parse.quote(full_prompt)
    poll_key = os.environ.get("POLLINATIONS_API_KEY", "").strip()

    if scene_num > 1 and poll_key:
        time.sleep(3.0)

    max_attempts = 3 if poll_key else 1
    last_exc: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        seed = (scene_num * 137) + (attempt * 31)
        if poll_key:
            url = (
                f"https://gen.pollinations.ai/image/{encoded}"
                f"?width=1080&height=1920&model=flux&nologo=true&seed={seed}"
            )
            headers = {"Authorization": f"Bearer {poll_key}", "User-Agent": "Mozilla/5.0"}
        else:
            url = (
                f"https://image.pollinations.ai/prompt/{encoded}"
                f"?width=1080&height=1920&nologo=true&seed={seed}"
            )
            headers = {"User-Agent": "Mozilla/5.0"}

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read()
            if len(raw) > 10000:
                tmp_jpg = out_img.with_suffix(".jpg")
                tmp_jpg.write_bytes(raw)
                with Image.open(tmp_jpg) as im:
                    rgb = im.convert("RGB")
                    w, h = rgb.size
                    cropped = rgb.crop((0, 0, w, int(h * 0.94)))
                    cropped.resize((1080, 1920), Image.Resampling.LANCZOS).save(out_img, format="PNG")
                tmp_jpg.unlink(missing_ok=True)
                log.info("Scene %d visual generated via Pollinations (%s).", scene_num, art_style)
                return out_img
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code in {401, 402, 403}:
                log.info("Scene %d Pollinations returned HTTP %d; skipping retries and checking next visual fallback.", scene_num, exc.code)
                break
            if attempt < max_attempts:
                time.sleep(4.0 * attempt)
        except Exception as exc:
            last_exc = exc
            if "Temporary failure in name resolution" in str(exc) or "nodename nor servname" in str(exc):
                break
            if attempt < max_attempts:
                time.sleep(4.0 * attempt)

    if _fetch_openrouter_ai_image(full_prompt, out_img, scene_num):
        return out_img

    if _fetch_hf_ai_image(full_prompt, out_img, scene_num):
        return out_img

    if _fetch_pixabay_portrait_image(stock_keywords or visual_prompt, out_img, scene_num, art_style=art_style, used_urls=used_urls) or _fetch_wikimedia_topic_image(stock_keywords or fallback_headline, out_img, scene_num, used_urls=used_urls):
        with Image.open(out_img) as im:
            _apply_art_style_filter(im, art_style).save(out_img, format="PNG")
        return out_img

    log.info("Scene %d image APIs unavailable (%s); rendering branded fallback visual.", scene_num, last_exc)
    _render_brand_slide_png(
        out_img,
        width=1080,
        height=1920,
        badge=f"SCENE 0{scene_num} • {art_style.replace('_', ' ').upper()}",
        headline=_trim_words(fallback_headline, 58).upper(),
        subline="4-Brain Free AI Council • Motion Short",
        footer="JAGNOR AI STUDIO",
    )
    return out_img


VOICE_PRESETS: dict[str, tuple[str, str, str]] = {
    # preset_name: (edge_tts_voice, rate, pitch)
    "original": ("en-US-ChristopherNeural", "+0%", "+0Hz"),
    "deep_male": ("en-US-ChristopherNeural", "-6%", "-14Hz"),
    "serious_male": ("en-GB-RyanNeural", "-4%", "-6Hz"),
    "mysterious_male": ("en-US-SteffanNeural", "-12%", "-10Hz"),
    "happy_male": ("en-US-BrianNeural", "+8%", "+4Hz"),
    "indian_storyteller_male": ("en-IN-PrabhatNeural", "-3%", "-4Hz"),
    "deep_female": ("en-US-AriaNeural", "-6%", "-10Hz"),
    "serious_female": ("en-GB-SoniaNeural", "-4%", "-4Hz"),
    "mysterious_female": ("en-US-EmmaNeural", "-11%", "-8Hz"),
    "happy_female": ("en-US-JennyNeural", "+8%", "+6Hz"),
    "malayalam_mysterious_male": ("ml-IN-MidhunNeural", "-8%", "-6Hz"),
    "malayalam_female": ("ml-IN-SobhanaNeural", "-4%", "-2Hz"),
    "hindi_serious_male": ("hi-IN-MadhurNeural", "-5%", "-6Hz"),
}


def _resolve_voice_preset(voice_or_preset: str) -> tuple[str, str, str]:
    key = (voice_or_preset or "").strip()
    if key in VOICE_PRESETS:
        return VOICE_PRESETS[key]
    return (key or "en-US-ChristopherNeural", "+0%", "+0Hz")


def _synthesize_scene_voiceover(text: str, out_wav: Path, voice: str = "deep_male") -> float:
    """
    Uses free Microsoft `edge-tts` with mood presets (deep/serious/mysterious/happy
    male & female voices via --rate and --pitch) and 3-attempt retry + fallback voice.
    Falls back to a timed silent WAV only if offline or `edge-tts` is missing.
    """
    resolved_voice, rate, pitch = _resolve_voice_preset(voice)
    text = " ".join(str(text or "").split()).strip() or "Discover the hidden story behind this moment."
    mp3_tmp = out_wav.with_suffix(".mp3")
    est_dur = max(3.2, min(9.5, len(text.split()) / 2.6))
    locale = resolved_voice.split("-")[0:2]
    alt_by_locale = {
        "ml-IN": ["ml-IN-MidhunNeural", "ml-IN-SobhanaNeural"],
        "hi-IN": ["hi-IN-MadhurNeural", "hi-IN-SwaraNeural"],
    }
    alts = alt_by_locale.get("-".join(locale), ["en-US-ChristopherNeural", "en-US-GuyNeural", "en-US-AriaNeural"])
    voices_to_try = list(dict.fromkeys([resolved_voice, *alts]))
    if len(voices_to_try) < 3:
        voices_to_try.insert(0, resolved_voice)
    last_exc: Exception | None = None

    for attempt, active_voice in enumerate(voices_to_try, start=1):
        try:
            mp3_tmp.unlink(missing_ok=True)
            run_cmd(
                [
                    "edge-tts",
                    f"--voice={active_voice}",
                    f"--rate={rate}",
                    f"--pitch={pitch}",
                    f"--text={text}",
                    f"--write-media={mp3_tmp}",
                ],
                timeout=45,
            )
            if not mp3_tmp.exists() or mp3_tmp.stat().st_size < 1000:
                raise RuntimeError("edge-tts produced empty audio file")
            run_cmd([
                "ffmpeg", "-y", "-i", str(mp3_tmp),
                "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(out_wav),
            ], timeout=60)
            mp3_tmp.unlink(missing_ok=True)
            res = run_cmd([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(out_wav),
            ])
            dur = float(res.stdout.strip() or est_dur)
            return max(2.5, min(11.0, dur))
        except FileNotFoundError as exc:
            last_exc = exc
            break  # edge-tts binary not installed
        except Exception as exc:
            last_exc = exc
            if attempt < len(voices_to_try):
                sleep_s = 2.0 * attempt
                log.info("edge-tts attempt %d/%d failed (%s); retrying in %.0fs...", attempt, len(voices_to_try), str(exc).strip()[-160:], sleep_s)
                time.sleep(sleep_s)

    log.info("edge-tts unavailable (%s); generating %.1fs silent fallback audio.", str(last_exc).strip()[-160:], est_dur)
    run_cmd([
        "ffmpeg", "-y", "-f", "lavfi", "-t", f"{est_dur:.2f}",
        "-i", "anullsrc=channel_layout=mono:sample_rate=48000",
        "-c:a", "pcm_s16le", str(out_wav),
    ], timeout=30)
    return est_dur


def run_ai_faceless_engine(
    topic: str,
    job_dir: Path,
    brain: CompanyBrain,
    voice: str = "deep_male",
    public_dir: Path | None = None,
    art_style: str = "dark_cinematic",
    theme: str = "AI & Tech Automation",
    character_desc: str = "",
    fact_brief: str = "",
    prior_media_urls: set[str] | None = None,
) -> dict[str, Any]:
    """
    100% Hands-Free AI Faceless Short Generator:
    1) 4-Brain Free AI Council writes a 5-scene script & visual prompts.
    2) Free `edge-tts` voices each scene (with automatic fallback).
    3) Fetches 9:16 AI scene visuals (or branded fallback cards) and applies smooth Ken Burns zoompan.
    4) Burns 3.5s HookBanner + word-by-word gold karaoke `.ass` captions and verifies `moov` +faststart.
    """
    item_key = f"ai_faceless:{topic.lower().strip()}:{time.strftime('%Y%m%d', time.gmtime())}"
    brain.check_pre_flight(item_key, estimated_cost_usd=0.12)

    out_dir = job_dir / "out"
    scene_dir = job_dir / "scenes"
    out_dir.mkdir(parents=True, exist_ok=True)
    scene_dir.mkdir(parents=True, exist_ok=True)

    council = AICouncil()
    resolved_v = _resolve_voice_preset(voice)[0]
    lang_hint = "Malayalam" if resolved_v.startswith("ml-") else ("Hindi" if resolved_v.startswith("hi-") else "English")
    log.info(
        "Active Settings [ai_faceless]: topic='%s' | theme='%s' | art_style='%s' | voice='%s' (%s) | character='%s'",
        topic, theme, art_style, voice, lang_hint, character_desc or "auto",
    )
    script_pkg = council.run_6_brain_faceless_script(
        topic, brain, art_style=art_style, theme=theme, character_desc=character_desc, language_hint=lang_hint, fact_brief=fact_brief
    )
    scenes = script_pkg["scenes"]

    scene_mp4s: list[Path] = []
    indexed_segments: list[IndexedSegment] = []
    used_media_urls: set[str] = set(prior_media_urls or set())
    cursor_t = 0.0

    for idx, sc in enumerate(scenes, start=1):
        narration = sc["narration"]
        vis_prompt = f"{sc['visual_prompt']}, featuring {character_desc}" if character_desc.strip() else sc["visual_prompt"]
        img_p = scene_dir / f"scene_{idx:02d}.png"
        wav_p = scene_dir / f"scene_{idx:02d}.wav"
        clip_p = scene_dir / f"scene_{idx:02d}.mp4"

        stock_kw = sc.get("stock_keywords", f"{theme} {topic}")
        dur = _synthesize_scene_voiceover(narration, wav_p, voice=voice)
        used_real_video = _fetch_pixabay_scene_video(
            stock_kw, clip_p, dur, wav_p, scene_num=idx, art_style=art_style, used_urls=used_media_urls
        )
        if not used_real_video:
            _fetch_free_ai_scene_image(
                vis_prompt,
                img_p,
                fallback_headline=narration,
                scene_num=idx,
                art_style=art_style,
                stock_keywords=stock_kw,
                used_urls=used_media_urls,
            )
            frames = max(60, int(round(dur * 30)))

            # Alternating dynamic camera motion per scene (zoom-in, pan-right, zoom-out, pan-left, punch-in)
            motion_mode = (idx - 1) % 5
            if motion_mode == 0:
                zp_expr = f"zoompan=z='min(zoom+0.0016,1.18)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
            elif motion_mode == 1:
                zp_expr = f"zoompan=z='1.12':d={frames}:x='(iw-iw/zoom)*on/{frames}':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
            elif motion_mode == 2:
                zp_expr = f"zoompan=z='max(1.18-on*0.0012,1.0)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
            elif motion_mode == 3:
                zp_expr = f"zoompan=z='1.12':d={frames}:x='(iw-iw/zoom)*(1-on/{frames})':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
            else:
                zp_expr = f"zoompan=z='min(zoom+0.0018,1.20)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"

            run_cmd([
                "ffmpeg", "-y",
                "-loop", "1", "-t", f"{dur:.3f}", "-i", str(img_p),
                "-i", str(wav_p),
                "-vf", f"scale=1080:1920,{zp_expr},format=yuv420p",
                "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
                "-shortest",
                str(clip_p),
            ])
        scene_mp4s.append(clip_p)

        # Evenly distribute word timestamps across this scene's exact voiceover duration
        raw_words = [w for w in narration.split() if w.strip()]
        w_dur = dur / max(len(raw_words), 1)
        tokens: list[WordToken] = []
        for wi, w in enumerate(raw_words):
            ws = cursor_t + wi * w_dur
            we = cursor_t + (wi + 1) * w_dur
            tokens.append(WordToken(word=w, start=round(ws, 3), end=round(we, 3)))

        indexed_segments.append(
            IndexedSegment(
                segment_id=idx - 1,
                speaker="NARRATOR",
                start=round(cursor_t, 3),
                end=round(cursor_t + dur, 3),
                text=narration,
                words=tokens,
            )
        )
        cursor_t += dur

    # Concatenate all animated scenes
    concat_txt = scene_dir / "concat.txt"
    concat_txt.write_text("\n".join("file '" + str(p.resolve()).replace("'", "'\\''") + "'" for p in scene_mp4s) + "\n", encoding="utf-8")
    merged_mp4 = scene_dir / "merged_raw.mp4"
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c", "copy", str(merged_mp4),
    ])

    # Burn HookBanner + word-by-word gold karaoke ASS captions and enforce -14 LUFS + faststart
    ass_path = out_dir / "faceless_01.ass"
    safe_slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic)[:24].strip("_").lower() or f"short_{int(time.time()) % 100000}"
    final_mp4 = out_dir / f"faceless_{safe_slug}_{_run_tag()}.mp4"
    write_ass_captions(
        indexed_segments,
        0,
        len(indexed_segments) - 1,
        0.0,
        ass_path,
        hook_overlay=script_pkg["hook_overlay"],
    )
    ass_escaped = escape_ffmpeg_filter_path(ass_path)
    run_cmd([
        "ffmpeg", "-y",
        "-i", str(merged_mp4),
        "-t", f"{min(58.0, cursor_t):.3f}",
        "-vf", f"scale=1080:1920,ass='{ass_escaped}'",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
        "-movflags", "+faststart",
        str(final_mp4),
    ])

    qa_ok = verify_rendered_mp4(final_mp4, min_duration=10.0)
    export_to_public_dir([final_mp4], public_dir)
    shutil.rmtree(scene_dir, ignore_errors=True)

    clip_obj = ClipSpec(
        clip_id="faceless_01",
        start_segment_id=0,
        end_segment_id=len(indexed_segments) - 1,
        start_sec=0.0,
        end_sec=round(min(58.0, cursor_t), 2),
        duration_sec=round(min(58.0, cursor_t), 2),
        mp4_path=str(final_mp4),
        layout_mode="ai_faceless_9x16",
        qa_verified=qa_ok,
        yt_title=script_pkg["yt_title"],
        ig_caption=script_pkg["ig_caption"],
        hook_overlay=script_pkg["hook_overlay"],
        council_score=9.6,
        council_models_used=script_pkg["council_models_used"],
        contains_synthetic_media=True,
        source_url=f"ai_faceless:{topic}",
    )

    result = {
        "engine": "clipping",
        "source_mode": "ai_faceless",
        "status": "APPROVAL_PENDING",
        "source_url": f"ai_faceless:{topic}",
        "language": lang_hint,
        "settings_applied": {
            "topic": topic, "theme": theme, "art_style": art_style, "voice": voice, "character_desc": character_desc,
        },
        "council_models_used": script_pkg["council_models_used"],
        "script_source": script_pkg.get("script_source", "ai"),
        "episode_continuity": {
            "recap": " ".join(sc["narration"] for sc in scenes[:3])[:320],
            "ending_line": scenes[-1]["narration"] if scenes else "",
            "visual_prompts": [sc.get("visual_prompt", "")[:100] for sc in scenes],
            "used_media_urls": sorted(used_media_urls),
        },
        "clips": [asdict(clip_obj)],
    }
    brain.record_completion(item_key, "ai_faceless", 0.12, {"topic": topic, "mp4_path": str(final_mp4)})
    return result



# ============================================================================
# 8D. ENGINE G: UNIVERSAL 2D ANIMATED STORY & CHARACTER ENGINE (`--engine motion_story`)
# ============================================================================

def _hex_to_rgb(hex_str: str, default: tuple[int, int, int] = (217, 74, 56)) -> tuple[int, int, int]:
    s = hex_str.strip().lstrip("#")
    if len(s) == 6:
        try:
            return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
        except Exception:
            pass
    return default




_SCRIPT_RANGES: list[tuple[str, int, int, str]] = [
    ("ml", 0x0D00, 0x0D7F, "Malayalam"),
    ("hi", 0x0900, 0x097F, "Devanagari"),
    ("bn", 0x0980, 0x09FF, "Bengali"),
    ("pa", 0x0A00, 0x0A7F, "Gurmukhi"),
    ("gu", 0x0A80, 0x0AFF, "Gujarati"),
    ("ta", 0x0B80, 0x0BFF, "Tamil"),
    ("te", 0x0C00, 0x0C7F, "Telugu"),
    ("kn", 0x0C80, 0x0CFF, "Kannada"),
    ("th", 0x0E00, 0x0E7F, "Thai"),
    ("ar", 0x0600, 0x06FF, "Arabic"),
    ("he", 0x0590, 0x05FF, "Hebrew"),
    ("ja", 0x3040, 0x30FF, "CJK"),
    ("ko", 0xAC00, 0xD7AF, "Korean"),
    ("zh", 0x4E00, 0x9FFF, "CJK"),
]
_FONT_PATH_CACHE: dict[tuple[str, bool], str | None] = {}


def _detect_script(text: str) -> tuple[str, str] | None:
    for ch in text or "":
        o = ord(ch)
        for lang, lo, hi, name in _SCRIPT_RANGES:
            if lo <= o <= hi:
                return lang, name
    return None


def _script_font_path(lang: str, name: str, bold: bool) -> str | None:
    key = (lang, bold)
    if key in _FONT_PATH_CACHE:
        return _FONT_PATH_CACHE[key]
    found: str | None = None
    weight = "Bold" if bold else "Regular"
    static = [
        f"/usr/share/fonts/truetype/noto/NotoSans{name}-{weight}.ttf",
        f"/usr/share/fonts/truetype/noto/NotoSans{name}-Regular.ttf",
        f"/usr/share/fonts/opentype/noto/NotoSans{name}-{weight}.ttf",
        "/usr/share/fonts/truetype/lohit-malayalam/Lohit-Malayalam.ttf",
        "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
        "/usr/share/fonts/truetype/lohit-tamil/Lohit-Tamil.ttf",
        "/usr/share/fonts/truetype/lohit-telugu/Lohit-Telugu.ttf",
        "/usr/share/fonts/truetype/lohit-bengali/Lohit-Bengali.ttf",
    ]
    if name == "CJK" or lang in ("ko", "ja", "zh"):
        static = [f"/usr/share/fonts/opentype/noto/NotoSansCJK-{weight}.ttc"] + static
    for p in static:
        if os.path.exists(p):
            found = p
            break
    if found is None and shutil.which("fc-match"):
        try:
            out = subprocess.run(
                ["fc-match", "-f", "%{file}", f"sans:lang={lang}:{'bold' if bold else 'regular'}"],
                capture_output=True, text=True, timeout=10,
            ).stdout.strip()
            if out and os.path.exists(out):
                found = out
        except Exception:
            found = None
    _FONT_PATH_CACHE[key] = found
    return found


def _load_font(size: int, bold: bool = False, text_sample: str = "") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates: list[str] = []
    script = _detect_script(text_sample)
    if script:
        sp = _script_font_path(script[0], script[1], bold)
        if sp:
            candidates.append(sp)
    candidates.extend(
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        ]
    )
    for fp in candidates:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    start_size: int = 56,
    min_size: int = 24,
    bold: bool = True,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for sz in range(start_size, min_size - 1, -4):
        fnt = _load_font(sz, bold=bold, text_sample=text)
        bbox = draw.textbbox((0, 0), text, font=fnt)
        if (bbox[2] - bbox[0]) <= max_width:
            return fnt
    return _load_font(min_size, bold=bold, text_sample=text)


def _draw_topic_subject(
    draw: ImageDraw.ImageDraw,
    visual_world: str,
    cx: float,
    cy: float,
    scale: float,
    char: dict[str, str],
    phase: float,
    flying: bool = False,
) -> None:
    """
    Draws a clean, topic-accurate 2D vector centerpiece so every topic gets the right visual:
      - `space`        : Voyager-style golden parabolic spacecraft + antenna + glowing thrusters
      - `ocean`        : Deep-sea exploration submersible + glowing headlight beam + bubbles
      - `tech_ai`      : Glowing neural core + orbiting satellite nodes + circuit rings
      - `finance`      : Animated rising gold market bars + luminous upward trend arrow
      - `history_myth` / `nature` : Sleek Kurzgesagt-style illustrated protagonist silhouette (no boxy blocks)
    """
    primary = _hex_to_rgb(char.get("primary_hex", "#D94A38"), (217, 74, 56))
    accent = _hex_to_rgb(char.get("accent_hex", "#F5C451"), (245, 196, 81))
    skin = _hex_to_rgb(char.get("skin_hex", "#C68642"), (198, 134, 66))
    aura = _hex_to_rgb(char.get("aura_hex", "#38BDF8"), (56, 189, 248))
    s = max(0.35, scale)
    bob = math.sin(phase * 2.0 * math.pi) * (10.0 * s)
    y = cy + bob

    if visual_world == "space":
        # Voyager-style deep-space probe: high-gain dish, golden record disc, long booms
        draw.ellipse((cx - 115 * s, y - 220 * s, cx + 115 * s, y - 140 * s), fill=(228, 236, 248), outline=aura, width=max(2, int(4 * s)))
        draw.ellipse((cx - 38 * s, y - 196 * s, cx + 38 * s, y - 164 * s), fill=(52, 68, 96))
        # Central hexagonal bus
        bus = [(cx - 58 * s, y - 140 * s), (cx + 58 * s, y - 140 * s), (cx + 46 * s, y - 62 * s), (cx - 46 * s, y - 62 * s)]
        draw.polygon(bus, fill=(38, 48, 72), outline=(190, 210, 235))
        # Golden Record emblem on spacecraft side
        draw.ellipse((cx - 26 * s, y - 126 * s, cx + 26 * s, y - 74 * s), fill=accent, outline=(255, 246, 200), width=max(2, int(3 * s)))
        draw.ellipse((cx - 7 * s, y - 107 * s, cx + 7 * s, y - 93 * s), fill=(38, 48, 72))
        # Magnetometer & RTG booms
        draw.line((cx - 54 * s, y - 104 * s, cx - 195 * s, y - 65 * s), fill=(180, 200, 225), width=max(2, int(4 * s)))
        draw.line((cx + 54 * s, y - 104 * s, cx + 185 * s, y - 145 * s), fill=(180, 200, 225), width=max(2, int(4 * s)))
        draw.ellipse((cx - 205 * s, y - 75 * s, cx - 185 * s, y - 55 * s), fill=aura)
        # Subtle thruster glow
        glow = int(18 * s * (0.85 + 0.25 * math.sin(phase * 6.0 * math.pi)))
        draw.ellipse((cx - glow, y - 60 * s, cx + glow, y - 60 * s + glow * 2), fill=aura)

    elif visual_world == "ocean":
        # Sleek deep-sea submersible + searchlight cone + rising bubbles
        beam = [(cx + 85 * s, y - 135 * s), (cx + 340 * s, y - 220 * s), (cx + 340 * s, y - 50 * s)]
        draw.polygon(beam, fill=(48, 128, 178))
        draw.rounded_rectangle((cx - 125 * s, y - 185 * s, cx + 110 * s, y - 85 * s), radius=int(48 * s), fill=accent, outline=(250, 245, 225), width=max(2, int(4 * s)))
        draw.rounded_rectangle((cx - 42 * s, y - 225 * s, cx + 28 * s, y - 175 * s), radius=int(14 * s), fill=primary, outline=(250, 245, 225), width=max(2, int(3 * s)))
        # Glass viewport dome
        draw.ellipse((cx + 22 * s, y - 165 * s, cx + 82 * s, y - 105 * s), fill=(26, 62, 108), outline=(185, 232, 255), width=max(2, int(4 * s)))
        # Rising bubbles
        for bi in range(4):
            bx = cx - 135 * s - bi * 18 * s
            by = y - 120 * s - ((phase * 140 + bi * 35) % 140) * s
            br = max(3, int((8 - bi) * s))
            draw.ellipse((bx - br, by - br, bx + br, by + br), outline=(185, 232, 255), width=2)

    elif visual_world == "tech_ai":
        # Glowing AI neural core + orbiting nodes
        r_outer = int(118 * s)
        r_inner = int(58 * s)
        draw.ellipse((cx - r_outer, y - 160 * s - r_outer, cx + r_outer, y - 160 * s + r_outer), outline=aura, width=max(2, int(4 * s)))
        draw.ellipse((cx - r_inner, y - 160 * s - r_inner, cx + r_inner, y - 160 * s + r_inner), fill=(22, 42, 76), outline=accent, width=max(3, int(5 * s)))
        for ni in range(6):
            ang = phase * 2.0 * math.pi + ni * (math.pi / 3.0)
            nx = cx + math.cos(ang) * r_outer
            ny = (y - 160 * s) + math.sin(ang) * r_outer
            draw.line((cx, y - 160 * s, nx, ny), fill=aura, width=max(1, int(2 * s)))
            draw.ellipse((nx - 14 * s, ny - 14 * s, nx + 14 * s, ny + 14 * s), fill=accent, outline=(255, 255, 255), width=2)

    elif visual_world == "finance":
        # Animated rising gold bars + glowing upward arrow
        bar_heights = [90, 145, 200, 275]
        for bi, bh in enumerate(bar_heights):
            cur_h = bh * s * min(1.0, 0.35 + phase * 0.9)
            bx = cx - 130 * s + bi * 74 * s
            col = accent if bi == 3 else aura
            draw.rounded_rectangle((bx, y - cur_h, bx + 52 * s, y), radius=int(8 * s), fill=col, outline=(245, 248, 255), width=2)
        draw.line((cx - 130 * s, y - 110 * s, cx + 135 * s, y - 305 * s), fill=accent, width=max(3, int(6 * s)))

    elif (variant := _topic_seed(str(char.get("name", "")), visual_world) % 3) == 1 and visual_world in {"nature", "history_myth"}:
        if visual_world == "nature":
            # Lone majestic tree with glowing canopy
            draw.polygon([(cx - 26 * s, y), (cx - 12 * s, y - 230 * s), (cx + 12 * s, y - 230 * s), (cx + 26 * s, y)], fill=(86, 58, 34))
            for k, (dx, dy, r) in enumerate([(0, 300, 120), (-90, 250, 90), (90, 250, 90), (0, 370, 80)]):
                col = _mix_rgb(primary, (40, 150, 70), 0.55 + 0.1 * k)
                draw.ellipse((cx + (dx - r) * s, y - (dy + r) * s, cx + (dx + r) * s, y - (dy - r) * s), fill=col, outline=accent, width=max(2, int(3 * s)))
        else:
            # Temple of pillars under a pediment
            for k in range(4):
                px = cx - 135 * s + k * 90 * s
                draw.rectangle((px, y - 250 * s, px + 36 * s, y), fill=(236, 220, 188), outline=accent, width=max(2, int(3 * s)))
            draw.polygon([(cx - 175 * s, y - 250 * s), (cx, y - 350 * s), (cx + 175 * s, y - 250 * s)], fill=primary, outline=accent)
            draw.rectangle((cx - 175 * s, y, cx + 175 * s, y + 20 * s), fill=(210, 190, 150))
    elif variant == 2 and visual_world in {"nature", "history_myth"}:
        if visual_world == "nature":
            # Mountain peak with glowing summit
            draw.polygon([(cx - 230 * s, y), (cx - 20 * s, y - 330 * s), (cx + 240 * s, y)], fill=_mix_rgb(primary, (60, 80, 110), 0.6), outline=accent)
            draw.polygon([(cx - 60 * s, y - 250 * s), (cx - 20 * s, y - 330 * s), (cx + 40 * s, y - 232 * s), (cx - 10 * s, y - 262 * s)], fill=(245, 248, 255))
            draw.ellipse((cx - 50 * s, y - 380 * s, cx + 10 * s, y - 320 * s), fill=accent)
        else:
            # Crown over an obelisk
            draw.polygon([(cx - 40 * s, y), (cx - 22 * s, y - 300 * s), (cx + 22 * s, y - 300 * s), (cx + 40 * s, y)], fill=(222, 206, 170), outline=accent)
            draw.polygon([(cx - 22 * s, y - 300 * s), (cx, y - 360 * s), (cx + 22 * s, y - 300 * s)], fill=accent)
            draw.polygon([(cx - 90 * s, y - 380 * s), (cx - 60 * s, y - 440 * s), (cx - 30 * s, y - 395 * s), (cx, y - 450 * s), (cx + 30 * s, y - 395 * s), (cx + 60 * s, y - 440 * s), (cx + 90 * s, y - 380 * s)], fill=primary, outline=accent)
    else:
        # Sleek Kurzgesagt-style minimalist illustrated protagonist (clean proportions, no boxy stomach smiley)
        halo_r = int(120 * s * (1.0 + 0.04 * math.sin(phase * 4.0 * math.pi)))
        draw.ellipse((cx - halo_r, y - 240 * s - halo_r * 0.7, cx + halo_r, y - 240 * s + halo_r * 0.7), outline=aura, width=max(2, int(3 * s)))
        sway = math.sin(phase * 2.0 * math.pi) * (20 * s)
        # Flowing cloak silhouette
        cloak = [(cx - 52 * s, y - 275 * s), (cx + 52 * s, y - 275 * s), (cx + 88 * s + sway, y - 35 * s), (cx - 88 * s + sway, y - 35 * s)]
        draw.polygon(cloak, fill=tuple(max(0, c - 45) for c in primary), outline=accent)
        # Tapered torso & lower tunic
        torso = [(cx - 52 * s, y - 278 * s), (cx + 52 * s, y - 278 * s), (cx + 38 * s, y - 150 * s), (cx - 38 * s, y - 150 * s)]
        draw.polygon(torso, fill=primary, outline=(245, 240, 230))
        if not flying:
            draw.rounded_rectangle((cx - 34 * s, y - 155 * s, cx - 6 * s, y), radius=int(10 * s), fill=tuple(max(0, c - 25) for c in primary))
            draw.rounded_rectangle((cx + 6 * s, y - 155 * s, cx + 34 * s, y), radius=int(10 * s), fill=tuple(max(0, c - 25) for c in primary))
        # Diagonal sash / scarf accent
        draw.line((cx - 46 * s, y - 272 * s, cx + 36 * s, y - 158 * s), fill=accent, width=max(3, int(8 * s)))
        # Clean rounded head + minimal glowing eyes (no awkward mouth)
        hr = 42 * s
        hy = y - 328 * s
        draw.ellipse((cx - hr, hy - hr, cx + hr, hy + hr), fill=skin, outline=(245, 240, 230), width=max(2, int(3 * s)))
        draw.ellipse((cx - 18 * s, hy - 8 * s, cx - 8 * s, hy + 2 * s), fill=(255, 255, 255))
        draw.ellipse((cx + 8 * s, hy - 8 * s, cx + 18 * s, hy + 2 * s), fill=(255, 255, 255))
        draw.arc((cx - hr * 0.9, hy - hr * 0.9, cx + hr * 0.9, hy - hr * 0.15), start=195, end=345, fill=accent, width=max(2, int(6 * s)))


def _fetch_story_backdrop_if_available(
    scene: dict[str, Any],
    art_style: str,
    scene_num: int,
    tmp_dir: Path,
    topic: str = "",
    theme: str = "",
    character_desc: str = "",
    used_urls: set[str] | None = None,
) -> Image.Image | None:
    """
    Strictly follows ALL pre-workflow instructions (`art_style`, `theme`, `topic`, `character_desc`):
      1) Pollinations.ai (`POLLINATIONS_API_KEY`) — custom AI art
      2) OpenRouter Image API (`OPENROUTER_API_KEY`) — custom AI art
      3) Hugging Face FLUX (`HF_TOKEN`) — custom AI art
      4) Stylized topic media (Pixabay / Wikimedia transformed via `_apply_art_style_filter`
         so it NEVER looks like raw unstyled photography)
    """
    tmp_png = tmp_dir / f"story_bg_{scene_num:02d}.png"
    narration = str(scene.get("narration") or "")
    vp = str(scene.get("visual_prompt") or "")
    sk = _extract_narration_search_query(narration, str(scene.get("stock_keywords") or ""), topic or str(scene.get("top_label") or ""))

    style_suffix = gen_style_prompt(art_style)
    char_clause = f", featuring {character_desc}" if character_desc.strip() else ""
    theme_clause = f", theme: {theme}" if theme.strip() else ""
    full_prompt = f"{vp or sk}{char_clause}{theme_clause}, topic: {topic}, {style_suffix}, vertical 9:16 composition, strictly no text, no letters, no logos, no street signs, no watermarks"

    poll_key = os.environ.get("POLLINATIONS_API_KEY", "").strip()
    pixabay_key = os.environ.get("PIXABAY_API_KEY", "").strip()
    loaded_ai = False
    loaded_photo = False

    if poll_key:
        encoded = urllib.parse.quote(full_prompt)
        seed_val = zlib.crc32(f"{topic}|{art_style}|{scene_num}".encode("utf-8")) % 999999
        url = f"https://gen.pollinations.ai/image/{encoded}?width=1080&height=1920&model=flux&nologo=true&seed={seed_val}"
        try:
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {poll_key}", "User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=40) as resp:
                raw = resp.read()
            if len(raw) > 10000:
                tmp_jpg = tmp_png.with_suffix(".jpg")
                tmp_jpg.write_bytes(raw)
                with Image.open(tmp_jpg) as im:
                    rgb = im.convert("RGB")
                    w, h = rgb.size
                    rgb.crop((0, 0, w, int(h * 0.94))).resize((1080, 1920), Image.Resampling.LANCZOS).save(tmp_png, format="PNG")
                tmp_jpg.unlink(missing_ok=True)
                loaded_ai = True
        except Exception as exc:
            log.info("Story scene %d Pollinations AI art skipped (%s).", scene_num, exc)

    if not loaded_ai:
        loaded_ai = _fetch_openrouter_ai_image(full_prompt, tmp_png, scene_num)

    if not loaded_ai:
        loaded_ai = _fetch_hf_ai_image(full_prompt, tmp_png, scene_num)

    if not loaded_ai and pixabay_key:
        loaded_photo = _fetch_pixabay_portrait_image(sk, tmp_png, scene_num, art_style=art_style, used_urls=used_urls)

    if not loaded_ai and not loaded_photo:
        loaded_photo = _fetch_wikimedia_topic_image(sk, tmp_png, scene_num, used_urls=used_urls)

    if (loaded_ai or loaded_photo) and tmp_png.exists():
        with Image.open(tmp_png) as im:
            styled = _apply_art_style_filter(im, art_style) if loaded_photo else im.convert("RGB")
            arr = np.asarray(styled, dtype=np.float32) * 0.65
            return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return None


def _draw_style_frame_decor(
    draw: ImageDraw.ImageDraw,
    W: int,
    H: int,
    theme_cfg: dict[str, Any],
    t: float,
) -> None:
    """Applies unmistakable art-style framing (comic panels, cyber scanlines, anime speedlines, letterbox, ornate border)."""
    fstyle = theme_cfg["frame_style"]
    accent = theme_cfg["accent"]
    sec = theme_cfg["secondary"]

    if fstyle == "comic_panel":
        draw.rectangle((22, 22, W - 22, H - 22), outline=(12, 12, 16), width=16)
        draw.rectangle((34, 34, W - 34, H - 34), outline=accent, width=5)
    elif fstyle == "scanlines":
        for sy in range(0, H, 18):
            draw.line((0, sy, W, sy), fill=(18, 28, 48), width=1)
        # Neon corner brackets
        for x0, y0, dx, dy in [(36, 36, 90, 90), (W - 36, 36, -90, 90), (36, H - 36, 90, -90), (W - 36, H - 36, -90, -90)]:
            draw.line((x0, y0, x0 + dx, y0), fill=accent, width=6)
            draw.line((x0, y0, x0, y0 + dy), fill=sec, width=6)
    elif fstyle == "speedlines":
        # Dynamic anime radial accent lines near outer edges
        for ai in range(16):
            ang = (ai / 16.0) * 2.0 * math.pi + t * 0.4
            x1 = int(W / 2 + math.cos(ang) * 520)
            y1 = int(H / 2 + math.sin(ang) * 900)
            x2 = int(W / 2 + math.cos(ang) * 760)
            y2 = int(H / 2 + math.sin(ang) * 1200)
            draw.line((x1, y1, x2, y2), fill=accent if ai % 2 == 0 else sec, width=3)
    elif fstyle == "letterbox":
        draw.rectangle((0, 0, W, 72), fill=(6, 8, 12))
        draw.rectangle((0, H - 72, W, H), fill=(6, 8, 12))
    elif fstyle == "ornate_frame":
        draw.rectangle((28, 28, W - 28, H - 28), outline=accent, width=6)
        draw.rectangle((44, 44, W - 44, H - 44), outline=sec, width=2)
    elif fstyle == "editorial_grid":
        for gx in (90, W - 90):
            draw.line((gx, 60, gx, H - 60), fill=(72, 76, 86), width=2)


_WORLD_PALETTES: dict[str, tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]] = {
    "space": ((6, 8, 26), (20, 18, 58), (40, 22, 70)),
    "ocean": ((4, 40, 74), (6, 92, 128), (2, 22, 46)),
    "tech_ai": ((8, 12, 30), (14, 38, 70), (6, 70, 82)),
    "finance": ((10, 24, 22), (16, 54, 44), (8, 26, 28)),
    "history_myth": ((74, 38, 18), (150, 84, 36), (44, 22, 14)),
    "nature": ((20, 74, 96), (52, 120, 90), (22, 56, 42)),
}


def _mix_rgb(a: tuple[int, int, int], b: tuple[int, int, int], k: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(a[i] * (1 - k) + b[i] * k))) for i in range(3))  # type: ignore[return-value]


def _hue_shift(rgb: tuple[int, int, int], deg: float) -> tuple[int, int, int]:
    import colorsys
    h, l_, sat = colorsys.rgb_to_hls(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
    r, g, b = colorsys.hls_to_rgb((h + deg / 360.0) % 1.0, l_, sat)
    return int(r * 255), int(g * 255), int(b * 255)


def _topic_seed(*parts: str) -> int:
    return zlib.crc32("|".join(p.lower().strip() for p in parts).encode("utf-8", "ignore"))


def _topic_character_colors(topic: str, visual_world: str) -> dict[str, str]:
    """Deterministic per-topic colours so different topics never share one default look."""
    rng = random.Random(_topic_seed(topic, visual_world, "char"))
    base = rng.randint(0, 359)

    def hx(rgb: tuple[int, int, int]) -> str:
        return "#%02X%02X%02X" % rgb

    primary = _hue_shift((200, 70, 60), base)
    accent = _hue_shift((245, 196, 81), base + rng.choice([40, 90, 150, 200]))
    aura = _hue_shift((56, 189, 248), base + rng.choice([120, 180, 240]))
    skin = rng.choice([(198, 134, 66), (141, 85, 36), (224, 172, 105), (255, 219, 172), (110, 70, 40)])
    return {"primary_hex": hx(primary), "accent_hex": hx(accent), "skin_hex": hx(skin), "aura_hex": hx(aura)}


def _build_style_themed_backdrop(
    W: int,
    H: int,
    theme_cfg: dict[str, Any],
    scene_idx: int,
    visual_world: str = "",
    seed_key: str = "",
) -> Image.Image:
    """
    Topic-specific backdrop: world palette (space/ocean/tech/finance/history/nature) blended with the art style,
    hue-rotated per topic, plus world scenery drawn from a topic+scene seeded RNG.
    """
    c1, c2, c3 = theme_cfg["bg_top"], theme_cfg["bg_mid"], theme_cfg["bg_bot"]
    seed = _topic_seed(seed_key, visual_world, str(scene_idx // 2))
    rng = random.Random(seed ^ (scene_idx * 7919))
    if visual_world in _WORLD_PALETTES:
        w1, w2, w3 = _WORLD_PALETTES[visual_world]
        shift = (seed % 61) - 30 if seed_key else 0
        c1, c2, c3 = (_hue_shift(_mix_rgb(x, y, 0.72), shift) for x, y in ((c1, w1), (c2, w2), (c3, w3)))
    if scene_idx % 2 == 1:
        c1, c2 = c2, c1
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    split = int(H * 0.58)
    for y in range(H):
        if y < split:
            u = y / float(max(split, 1))
            arr[y, :] = [int(c1[i] + (c2[i] - c1[i]) * u) for i in range(3)]
        else:
            u = (y - split) / float(max(H - split, 1))
            arr[y, :] = [int(c2[i] + (c3[i] - c2[i]) * u) for i in range(3)]
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img, "RGBA")
    acc = tuple(theme_cfg["accent"])[:3]
    sec = tuple(theme_cfg["secondary"])[:3]
    fstyle = theme_cfg["frame_style"]
    light = _mix_rgb(c2, (255, 255, 255), 0.35)
    dark = _mix_rgb(c3, (0, 0, 0), 0.45)

    if visual_world == "space":
        for _ in range(rng.randint(40, 80)):
            sx, sy, sr = rng.randint(20, W - 20), rng.randint(60, int(H * 0.7)), rng.choice([1, 2, 2, 3, 4])
            draw.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=(255, 255, 255, rng.randint(110, 255)))
        px, py, pr = rng.randint(140, W - 140), rng.randint(300, 900), rng.randint(90, 230)
        pc = _hue_shift((190, 110, 80), rng.randint(0, 359))
        draw.ellipse((px - pr, py - pr, px + pr, py + pr), fill=pc + (255,))
        draw.ellipse((px - pr * 0.2, py - pr, px + pr, py + pr * 0.8), fill=_mix_rgb(pc, (0, 0, 0), 0.45) + (140,))
        if rng.random() < 0.6:
            draw.ellipse((px - pr * 1.7, py - pr * 0.22, px + pr * 1.7, py + pr * 0.22), outline=light + (200,), width=5)
    elif visual_world == "ocean":
        for _ in range(4):
            rx = rng.randint(-100, W)
            draw.polygon([(rx, 0), (rx + rng.randint(60, 160), 0), (rx + rng.randint(300, 560), int(H * 0.7)), (rx + 120, int(H * 0.7))], fill=light + (28,))
        for _ in range(rng.randint(18, 34)):
            bx, by, br = rng.randint(30, W - 30), rng.randint(200, H - 300), rng.randint(5, 22)
            draw.ellipse((bx - br, by - br, bx + br, by + br), outline=(220, 245, 255, 170), width=3)
        for k in range(7):
            bx = k * (W // 6) - 40
            draw.polygon([(bx, H), (bx + 90, H - rng.randint(120, 300)), (bx + 190, H)], fill=dark + (255,))
    elif visual_world == "tech_ai":
        for _ in range(rng.randint(10, 18)):
            x, y = rng.randint(0, W // 40) * 40, rng.randint(2, H // 40) * 40
            pts = [(x, y)]
            for _ in range(rng.randint(2, 4)):
                x += rng.choice([-1, 1]) * rng.randint(2, 6) * 40 if rng.random() < 0.5 else 0
                y += rng.randint(1, 5) * 40
                pts.append((x, y))
            draw.line(pts, fill=acc + (120,), width=3)
            ex, ey = pts[-1]
            draw.ellipse((ex - 9, ey - 9, ex + 9, ey + 9), fill=sec + (230,))
        for gy in range(0, H, 160):
            draw.line((0, gy, W, gy), fill=light + (14,), width=1)
    elif visual_world == "finance":
        for gy in range(200, int(H * 0.8), 150):
            draw.line((0, gy, W, gy), fill=light + (30,), width=2)
        x = 40
        val = rng.randint(900, 1200)
        while x < W - 40:
            o = val
            val = max(300, min(1500, val + rng.randint(-120, 150)))
            top, bot = min(o, val), max(o, val)
            col = (60, 200, 120, 150) if val >= o else (230, 80, 80, 150)
            draw.line((x + 17, top - 60, x + 17, bot + 60), fill=col, width=3)
            draw.rectangle((x, top, x + 34, bot), fill=col)
            x += 62
    elif visual_world == "history_myth":
        sx, sy = rng.randint(200, W - 200), rng.randint(260, 560)
        draw.ellipse((sx - 150, sy - 150, sx + 150, sy + 150), fill=_mix_rgb(c1, (255, 210, 120), 0.5) + (110,))
        draw.ellipse((sx - 90, sy - 90, sx + 90, sy + 90), fill=(255, 226, 150, 235))
        base_y = int(H * 0.66)
        for _ in range(rng.randint(2, 4)):
            cx = rng.randint(-100, W + 100)
            hw = rng.randint(180, 420)
            if rng.random() < 0.5:
                draw.polygon([(cx - hw, base_y), (cx, base_y - int(hw * 0.8)), (cx + hw, base_y)], fill=dark + (255,))
            else:
                for c in range(4):
                    draw.rectangle((cx - hw // 2 + c * hw // 4, base_y - 220, cx - hw // 2 + c * hw // 4 + 28, base_y), fill=dark + (255,))
                draw.polygon([(cx - hw // 2 - 20, base_y - 220), (cx, base_y - 300), (cx + hw // 2 + 20, base_y - 220)], fill=dark + (255,))
        draw.rectangle((0, base_y, W, H), fill=dark + (255,))
    else:  # nature / unknown: layered hills, sun, trees, clouds
        sx, sy = rng.randint(120, W - 120), rng.randint(220, 480)
        draw.ellipse((sx - 80, sy - 80, sx + 80, sy + 80), fill=(255, 236, 170, 235))
        for _ in range(rng.randint(2, 4)):
            cx, cy = rng.randint(0, W), rng.randint(140, 760)
            for k in range(3):
                draw.ellipse((cx + k * 70 - 90, cy - 36, cx + k * 70 + 90, cy + 36), fill=(255, 255, 255, 70))
        for layer in range(3):
            base = int(H * (0.52 + layer * 0.08))
            col = _mix_rgb(c3, (10, 40, 20), 0.2 + layer * 0.25) + (255,)
            pts = [(0, H)] + [(x, base + int(math.sin(x / (160.0 + 60 * layer) + rng.random() * 6) * (70 - 12 * layer))) for x in range(0, W + 60, 60)] + [(W, H)]
            draw.polygon(pts, fill=col)
        for _ in range(rng.randint(4, 9)):
            tx, ty = rng.randint(30, W - 30), rng.randint(int(H * 0.62), int(H * 0.8))
            th = rng.randint(70, 150)
            draw.rectangle((tx - 6, ty - th // 3, tx + 6, ty), fill=(60, 40, 24, 255))
            draw.polygon([(tx - th // 3, ty - th // 3), (tx, ty - th), (tx + th // 3, ty - th // 3)], fill=_mix_rgb(c3, (30, 120, 50), 0.6) + (255,))

    # Art-style overlay keeps style identity on top of the topic scenery
    if fstyle == "comic_panel":
        for gy in range(80, H - 80, 96):
            for gx in range(80, W - 80, 96):
                draw.ellipse((gx - 6, gy - 6, gx + 6, gy + 6), fill=_mix_rgb(c2, (255, 255, 255), 0.15) + (90,))
    elif fstyle == "scanlines":
        for gx in range(0, W + 120, 120):
            draw.line((W // 2, int(H * 0.65), gx, H), fill=sec + (160,), width=2)
    return img.convert("RGB")




def _draw_editorial_mascot(
    draw: ImageDraw.ImageDraw,
    cx: float,
    bottom_y: float,
    scale: float,
    t: float,
    accent: tuple[int, int, int] = (226, 88, 34),
) -> None:
    """
    Draws a crisp minimalist 2D illustrated presenter character (warm orange cap, sweater,
    expressive blinking eyes, animated talking mouth, pointing arm) on a light cream canvas.
    """
    ink = (30, 32, 38)
    skin = (252, 248, 242)
    sweater = (232, 228, 222)
    s = max(0.4, scale)
    bob = math.sin(t * 2.0 * math.pi) * (8.0 * s)
    y = bottom_y + bob
    lw = max(3, int(6 * s))

    # Torso / sweater
    draw.rounded_rectangle(
        (cx - 145 * s, y - 260 * s, cx + 145 * s, y + 30 * s),
        radius=int(75 * s), fill=sweater, outline=ink, width=lw,
    )
    # Subtle accent emblem on chest
    draw.ellipse((cx + 55 * s, y - 140 * s, cx + 82 * s, y - 113 * s), fill=accent)

    # Raised pointing arm (left or right alternating gently)
    arm_wave = math.sin(t * 4.0 * math.pi) * (16 * s)
    arm_x = cx + 140 * s
    draw.line((arm_x, y - 210 * s, arm_x + 42 * s, y - 355 * s + arm_wave), fill=ink, width=int(48 * s))
    draw.line((arm_x, y - 210 * s, arm_x + 42 * s, y - 355 * s + arm_wave), fill=sweater, width=int(36 * s))
    # Pointing hand
    hx, hy = arm_x + 44 * s, y - 380 * s + arm_wave
    draw.ellipse((hx - 24 * s, hy - 22 * s, hx + 24 * s, hy + 22 * s), fill=skin, outline=ink, width=lw)
    draw.rounded_rectangle((hx - 8 * s, hy - 58 * s, hx + 10 * s, hy - 8 * s), radius=int(7 * s), fill=skin, outline=ink, width=max(2, lw - 1))

    # Collar & neck
    draw.rectangle((cx - 26 * s, y - 300 * s, cx + 26 * s, y - 245 * s), fill=skin, outline=ink, width=lw)

    # Ears
    hy_c = y - 375 * s
    draw.ellipse((cx - 122 * s, hy_c - 18 * s, cx - 84 * s, hy_c + 24 * s), fill=skin, outline=ink, width=lw)
    draw.ellipse((cx + 84 * s, hy_c - 18 * s, cx + 122 * s, hy_c + 24 * s), fill=skin, outline=ink, width=lw)

    # Head
    draw.ellipse((cx - 102 * s, hy_c - 102 * s, cx + 102 * s, hy_c + 96 * s), fill=skin, outline=ink, width=lw)

    # Orange cap dome + brim
    draw.pieslice((cx - 106 * s, hy_c - 152 * s, cx + 106 * s, hy_c - 18 * s), start=180, end=360, fill=accent, outline=ink, width=lw)
    draw.rounded_rectangle((cx - 118 * s, hy_c - 86 * s, cx + 118 * s, hy_c - 54 * s), radius=int(16 * s), fill=accent, outline=ink, width=lw)
    draw.ellipse((cx - 12 * s, hy_c - 160 * s, cx + 12 * s, hy_c - 140 * s), fill=accent, outline=ink, width=max(2, lw - 1))

    # Eyes (periodic quick blink)
    blinking = (t * 3.0) % 1.0 > 0.92
    for ex in (cx - 38 * s, cx + 38 * s):
        if blinking:
            draw.line((ex - 12 * s, hy_c - 6 * s, ex + 12 * s, hy_c - 6 * s), fill=ink, width=lw)
        else:
            draw.ellipse((ex - 10 * s, hy_c - 16 * s, ex + 10 * s, hy_c + 6 * s), fill=ink)
        # Eyebrows
        draw.arc((ex - 18 * s, hy_c - 40 * s, ex + 18 * s, hy_c - 18 * s), start=200, end=340, fill=ink, width=max(2, lw - 1))

    # Small nose
    draw.arc((cx - 8 * s, hy_c + 2 * s, cx + 8 * s, hy_c + 24 * s), start=30, end=150, fill=ink, width=max(2, lw - 2))

    # Animated talking mouth
    mouth_open = abs(math.sin(t * 14.0 * math.pi))
    mh = (6 + 18 * mouth_open) * s
    draw.pieslice((cx - 28 * s, hy_c + 34 * s, cx + 28 * s, hy_c + 34 * s + mh * 2), start=0, end=180, fill=(255, 255, 255), outline=ink, width=max(2, lw - 1))




def _wav_amplitude_envelope(wav_path: Path, n_frames: int) -> list[float]:
    """Extracts normalized [0..1] per-frame speech loudness from a WAV file so character mouths sync to real speech."""
    import wave
    try:
        with wave.open(str(wav_path), "rb") as wf:
            n_ch = wf.getnchannels()
            sw = wf.getsampwidth()
            raw = wf.readframes(wf.getnframes())
        if sw != 2 or not raw:
            return []
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
        if n_ch > 1:
            samples = samples.reshape(-1, n_ch).mean(axis=1)
        if len(samples) < n_frames:
            return []
        chunks = np.array_split(np.abs(samples), n_frames)
        rms = np.array([float(np.sqrt(np.mean(c * c))) if len(c) else 0.0 for c in chunks], dtype=np.float32)
        peak = float(np.percentile(rms, 95)) if len(rms) else 1.0
        if peak < 150.0:
            return []  # Silent fallback track -> let renderer use gentle procedural mouth motion
        norm = np.clip(rms / max(peak, 1.0), 0.0, 1.0)
        if len(norm) >= 3:
            norm = np.convolve(norm, np.array([0.25, 0.50, 0.25], dtype=np.float32), mode="same")
        return [0.0 if float(x) < 0.08 else float(x) for x in norm]
    except Exception:
        return []


def _resolve_dialogue_voice(base_voice: str, speaker: str) -> str:
    """Maps each character in a multi-character conversation (host / guest / bot) to a distinct matching-language voice."""
    resolved = _resolve_voice_preset(base_voice)[0]
    sp = (speaker or "host").strip().lower()
    if resolved.startswith("ml-"):
        return {"host": "ml-IN-MidhunNeural", "guest": "ml-IN-SobhanaNeural", "bot": "ml-IN-MidhunNeural"}.get(sp, resolved)
    if resolved.startswith("hi-"):
        return {"host": "hi-IN-MadhurNeural", "guest": "hi-IN-SwaraNeural", "bot": "hi-IN-MadhurNeural"}.get(sp, resolved)
    if sp == "guest":
        return "happy_female" if "Male" in resolved or any(n in resolved for n in ("Christopher", "Ryan", "Steffan", "Brian", "Prabhat", "Andrew")) else "happy_male"
    if sp == "bot":
        return "happy_male"
    return base_voice


def _draw_dialogue_character(
    draw: ImageDraw.ImageDraw,
    role: str,
    cx: float,
    bottom_y: float,
    scale: float,
    t: float,
    is_speaking: bool,
    emotion: str,
    mouth_level: float,
    accent: tuple[int, int, int],
    sec: tuple[int, int, int],
    look_dir: float = 0.0,
) -> None:
    """
    Draws one of 3 distinct animated characters (host, guest, bot) with coordinated movements:
    active speaker bounces, gestures, and lip-syncs to audio; listeners blink, nod, and look toward the speaker.
    """
    ink = (26, 28, 36)
    s = max(0.38, scale)
    emo = (emotion or "explaining").lower()
    lw = max(2, int(5 * s))

    # Coordinated movement based on role + speaking state + emotion
    if is_speaking:
        if emo in ("excited", "celebrating"):
            bob = -abs(math.sin(t * 6.0 * math.pi)) * (22.0 * s)
        elif emo == "shocked":
            bob = -14.0 * s + math.sin(t * 10.0 * math.pi) * (5.0 * s)
        else:
            bob = math.sin(t * 4.0 * math.pi) * (10.0 * s)
        gesture_y = math.sin(t * 6.0 * math.pi) * (22.0 * s)
    else:
        # Subtle attentive listening nod
        bob = math.sin(t * 2.0 * math.pi + (1.4 if role == "guest" else 2.6)) * (4.0 * s)
        gesture_y = 0.0

    y = bottom_y + bob

    if role == "bot":
        # Cute 3D-shaded boxy AI bot mascot sized proportionally to host/guest eye-level
        body_col = accent if is_speaking else _mix_rgb(accent, (130, 120, 125), 0.35)
        bw, bh = 104 * s, 108 * s
        by = y - 178 * s
        # Feet + lower chassis
        draw.rounded_rectangle((cx - 58 * s, by + bh - 6 * s, cx - 20 * s, y + 20 * s), radius=int(10 * s), fill=_mix_rgb(body_col, (0, 0, 0), 0.22), outline=ink, width=lw)
        draw.rounded_rectangle((cx + 20 * s, by + bh - 6 * s, cx + 58 * s, y + 20 * s), radius=int(10 * s), fill=_mix_rgb(body_col, (0, 0, 0), 0.22), outline=ink, width=lw)
        # Arms (coordinated gesture when speaking, relaxed when listening)
        draw.rounded_rectangle((cx - bw - 22 * s, by - 16 * s - gesture_y * 0.6, cx - bw + 6 * s, by + 22 * s - gesture_y * 0.6), radius=int(12 * s), fill=body_col, outline=ink, width=lw)
        draw.rounded_rectangle((cx + bw - 6 * s, by - 16 * s + gesture_y * 0.6, cx + bw + 22 * s, by + 22 * s + gesture_y * 0.6), radius=int(12 * s), fill=body_col, outline=ink, width=lw)
        # Antenna (pulses brighter when speaking)
        draw.line((cx, by - bh, cx, by - bh - 40 * s), fill=ink, width=lw)
        ant_r = (14 if is_speaking else 11) * s
        draw.ellipse((cx - ant_r, by - bh - 40 * s - ant_r, cx + ant_r, by - bh - 40 * s + ant_r), fill=sec if is_speaking else (200, 210, 225), outline=ink, width=max(2, lw - 1))
        # Box body + specialist analyst screen faceplate + live telemetry LED bars
        draw.rounded_rectangle((cx - bw, by - bh, cx + bw, by + bh), radius=int(28 * s), fill=body_col, outline=ink, width=lw)
        draw.rounded_rectangle((cx - bw + 14 * s, by - bh + 18 * s, cx + bw - 14 * s, by + bh - 22 * s), radius=int(18 * s), fill=_mix_rgb(body_col, (255, 255, 255), 0.16))
        # Specialist Analyst chest telemetry bar (glows & animates with voice level when speaking)
        led_y = by + bh - 16 * s
        for bi in range(5):
            bx_led = cx - 44 * s + bi * 22 * s
            bar_h = (6 + 10 * abs(math.sin(t * 10.0 * math.pi + bi * 0.9)) * (1.0 if is_speaking else 0.25)) * s
            draw.rounded_rectangle((bx_led - 5 * s, led_y - bar_h, bx_led + 5 * s, led_y), radius=int(3 * s), fill=sec if is_speaking else (195, 205, 220))
        # Blush cheeks
        draw.ellipse((cx - 78 * s, by + 10 * s, cx - 48 * s, by + 30 * s), fill=(245, 130, 140))
        draw.ellipse((cx + 48 * s, by + 10 * s, cx + 78 * s, by + 30 * s), fill=(245, 130, 140))
        # Eyes
        eye_dx = look_dir * 8 * s
        blinking = (not is_speaking) and ((t * 2.7 + 0.4) % 1.0 > 0.93)
        for ex in (cx - 42 * s + eye_dx, cx + 42 * s + eye_dx):
            if emo == "celebrating" and is_speaking:
                draw.arc((ex - 14 * s, by - 28 * s, ex + 14 * s, by - 2 * s), start=190, end=350, fill=ink, width=lw)
            elif blinking:
                draw.line((ex - 12 * s, by - 14 * s, ex + 12 * s, by - 14 * s), fill=ink, width=lw)
            else:
                draw.rounded_rectangle((ex - 9 * s, by - 32 * s, ex + 9 * s, by + 2 * s), radius=int(6 * s), fill=ink)
        # Mouth
        if is_speaking:
            mh = (5 + 16 * mouth_level) * s
            draw.rounded_rectangle((cx - 24 * s, by + 22 * s, cx + 24 * s, by + 22 * s + mh), radius=int(8 * s), fill=(255, 255, 255), outline=ink, width=max(2, lw - 1))
        else:
            draw.line((cx - 18 * s, by + 28 * s, cx + 18 * s, by + 28 * s), fill=ink, width=lw)
        return

    # Human characters: `host` (orange cap + warm cream hoodie) vs `guest` (hair tuft + teal/olive sweater)
    is_host = role == "host"
    skin = (252, 232, 214) if is_host else (244, 216, 192)
    shirt = (232, 226, 218) if is_host else _mix_rgb(sec, (90, 145, 115), 0.55)
    if not is_speaking:
        shirt = _mix_rgb(shirt, (120, 120, 130), 0.25)

    # Torso
    draw.rounded_rectangle((cx - 110 * s, y - 205 * s, cx + 110 * s, y + 25 * s), radius=int(56 * s), fill=shirt, outline=ink, width=lw)

    # Animated speaking arm
    if is_speaking:
        side = 1 if is_host else -1
        ax = cx + side * 102 * s
        draw.line((ax, y - 165 * s, ax + side * 34 * s, y - 285 * s + gesture_y), fill=ink, width=int(36 * s))
        draw.line((ax, y - 165 * s, ax + side * 34 * s, y - 285 * s + gesture_y), fill=shirt, width=int(26 * s))
        hx, hy = ax + side * 36 * s, y - 305 * s + gesture_y
        draw.ellipse((hx - 20 * s, hy - 18 * s, hx + 20 * s, hy + 18 * s), fill=skin, outline=ink, width=lw)

    # Neck & head
    draw.rectangle((cx - 20 * s, y - 235 * s, cx + 20 * s, y - 195 * s), fill=skin, outline=ink, width=lw)
    hy_c = y - 295 * s
    draw.ellipse((cx - 82 * s, hy_c - 82 * s, cx + 82 * s, hy_c + 78 * s), fill=skin, outline=ink, width=lw)

    # Headgear / hair
    if is_host:
        draw.pieslice((cx - 86 * s, hy_c - 122 * s, cx + 86 * s, hy_c - 14 * s), start=180, end=360, fill=accent, outline=ink, width=lw)
        draw.rounded_rectangle((cx - 96 * s, hy_c - 68 * s, cx + 96 * s, hy_c - 44 * s), radius=int(12 * s), fill=accent, outline=ink, width=lw)
    else:
        draw.pieslice((cx - 86 * s, hy_c - 102 * s, cx + 86 * s, hy_c + 6 * s), start=190, end=350, fill=(46, 36, 32), outline=ink, width=lw)

    # Eyes + emotion eyebrows
    eye_dx = look_dir * 9 * s
    blinking = (not is_speaking) and ((t * 3.1 + (0.2 if is_host else 0.7)) % 1.0 > 0.92)
    for idx_e, ex in enumerate((cx - 30 * s + eye_dx, cx + 30 * s + eye_dx)):
        if blinking:
            draw.line((ex - 10 * s, hy_c - 4 * s, ex + 10 * s, hy_c - 4 * s), fill=ink, width=lw)
        else:
            er = 12 * s if emo == "shocked" else 9 * s
            draw.ellipse((ex - er, hy_c - 10 * s - er * 0.4, ex + er, hy_c - 10 * s + er * 1.2), fill=ink)
            draw.ellipse((ex - er * 0.4, hy_c - 12 * s, ex + er * 0.1, hy_c - 6 * s), fill=(255, 255, 255))
        # Eyebrow expression
        by_b = hy_c - 32 * s
        if emo == "skeptical" and idx_e == 1:
            draw.line((ex - 14 * s, by_b - 6 * s, ex + 14 * s, by_b + 4 * s), fill=ink, width=max(2, lw - 1))
        elif emo == "shocked":
            draw.arc((ex - 14 * s, by_b - 14 * s, ex + 14 * s, by_b + 6 * s), start=195, end=345, fill=ink, width=max(2, lw - 1))
        else:
            draw.arc((ex - 14 * s, by_b - 6 * s, ex + 14 * s, by_b + 10 * s), start=200, end=340, fill=ink, width=max(2, lw - 1))

    # Mouth (audio-synced when speaking, expressive when listening)
    if is_speaking:
        mh = (6 + 20 * mouth_level) * s
        if emo == "shocked":
            draw.ellipse((cx - 16 * s, hy_c + 24 * s, cx + 16 * s, hy_c + 24 * s + mh * 1.4), fill=(50, 24, 28), outline=ink, width=max(2, lw - 1))
        else:
            draw.pieslice((cx - 24 * s, hy_c + 24 * s, cx + 24 * s, hy_c + 24 * s + mh * 1.8), start=0, end=180, fill=(255, 255, 255), outline=ink, width=max(2, lw - 1))
    else:
        if emo == "shocked":
            draw.ellipse((cx - 10 * s, hy_c + 28 * s, cx + 10 * s, hy_c + 46 * s), fill=(50, 24, 28), outline=ink, width=max(2, lw - 1))
        elif emo == "skeptical":
            draw.line((cx - 16 * s, hy_c + 34 * s, cx + 16 * s, hy_c + 30 * s), fill=ink, width=max(2, lw - 1))
        else:
            draw.arc((cx - 18 * s, hy_c + 22 * s, cx + 18 * s, hy_c + 42 * s), start=15, end=165, fill=ink, width=max(2, lw - 1))


def _render_motion_story_scene(
    scene: dict[str, Any],
    character: dict[str, str],
    scene_idx: int,
    dur: float,
    wav_path: Path,
    out_mp4: Path,
    fps: int = 24,
    art_style: str = "dark_cinematic",
    tmp_dir: Path | None = None,
    topic: str = "",
    theme: str = "",
    character_desc: str = "",
    used_urls: set[str] | None = None,
    canvas_size: tuple[int, int] = (1080, 1920),
    dialogue_mode: bool = False,
) -> None:
    """
    Dynamic 10-Action Motion Director:
    Supports both 9:16 vertical Shorts and 16:9 widescreen long-form YouTube videos,
    plus the `editorial_mascot` cream card + animated 2D presenter layout.
    """
    W, H = canvas_size
    n_frames = max(48, int(round(dur * fps)))
    action = str(scene.get("action") or "cinematic_zoom_in").lower()
    visual_world = character.get("visual_world", "nature")
    top_label = str(scene.get("top_label") or "").upper()
    stat_text = str(scene.get("stat_text") or "").upper()
    quote_title = str(scene.get("quote_title") or "RECORD")
    quote_text = str(scene.get("quote_text") or scene.get("narration") or "")
    timeline_steps = scene.get("timeline_steps") or ["START", "SHIFT", "NOW"]
    callout_label = str(scene.get("callout_label") or "").upper()

    theme_cfg = STYLE_THEMES.get((art_style or "dark_cinematic").lower(), STYLE_THEMES["dark_cinematic"])
    accent_rgb = theme_cfg["accent"]
    sec_rgb = theme_cfg["secondary"]

    photo_bg = _fetch_story_backdrop_if_available(
        scene,
        art_style,
        scene_idx + 1,
        tmp_dir or out_mp4.parent,
        topic=topic,
        theme=theme,
        character_desc=character_desc,
        used_urls=used_urls,
    )
    has_photo_bg = photo_bg is not None
    if has_photo_bg and photo_bg.size != (W, H):
        # Center-crop/cover photo to target canvas (handles 16:9 widescreen cleanly)
        pw, ph = photo_bg.size
        tr = W / float(max(H, 1))
        cr = pw / float(max(ph, 1))
        if cr > tr:
            nw = int(ph * tr)
            photo_bg = photo_bg.crop(((pw - nw) // 2, 0, (pw - nw) // 2 + nw, ph))
        else:
            nh = int(pw / tr)
            photo_bg = photo_bg.crop((0, (ph - nh) // 2, pw, (ph - nh) // 2 + nh))
        photo_bg = photo_bg.resize((W, H), Image.Resampling.LANCZOS)
    bg_base = photo_bg if has_photo_bg else _build_style_themed_backdrop(W, H, theme_cfg, scene_idx, visual_world=visual_world, seed_key=topic)
    is_mascot_style = (art_style or "").lower() == "editorial_mascot"
    cream_canvas = Image.new("RGB", (W, H), color=(246, 241, 233)) if is_mascot_style else None
    speech_env = _wav_amplitude_envelope(wav_path, n_frames) if (dialogue_mode or is_mascot_style) else []
    active_speaker = str(scene.get("speaker") or "host").strip().lower()
    scene_emotion = str(scene.get("emotion") or "explaining").strip().lower()

    sample_all = f"{top_label} {stat_text} {quote_title} {quote_text} {callout_label}"
    font_med = _load_font(36, bold=True, text_sample=sample_all)
    font_body = _load_font(34, bold=False, text_sample=sample_all)

    cmd = [
        "ffmpeg", "-y",
        "-loglevel", "error", "-nostats",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
        "-i", str(wav_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
        "-shortest",
        str(out_mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin is not None

    try:
        for f_idx in range(n_frames):
            t = f_idx / float(max(n_frames - 1, 1))

            # 1. Distinct Camera Motion driven by this scene's exact `action`!
            if action == "dramatic_pull_back":
                z = 1.22 - 0.20 * t
                cw, ch = int(W / z), int(H / z)
                x0, y0 = (W - cw) // 2, (H - ch) // 2
                frame = bg_base.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.Resampling.BILINEAR)
            elif action == "pan_left_to_right":
                z = 1.18
                cw, ch = int(W / z), int(H / z)
                x0 = int((W - cw) * t)
                y0 = (H - ch) // 2
                frame = bg_base.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.Resampling.BILINEAR)
            elif action == "pan_right_to_left":
                z = 1.18
                cw, ch = int(W / z), int(H / z)
                x0 = int((W - cw) * (1.0 - t))
                y0 = (H - ch) // 2
                frame = bg_base.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.Resampling.BILINEAR)
            elif action == "pulse_beat_zoom":
                z = 1.04 + 0.14 * t + 0.03 * abs(math.sin(t * 4.0 * math.pi))
                cw, ch = int(W / z), int(H / z)
                x0, y0 = (W - cw) // 2, (H - ch) // 2
                frame = bg_base.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.Resampling.BILINEAR)
            elif action == "spotlight_drift":
                z = 1.14
                cw, ch = int(W / z), int(H / z)
                x0 = int((W - cw) * (0.5 + 0.35 * math.sin(t * 1.5 * math.pi)))
                y0 = int((H - ch) * (0.5 + 0.20 * math.cos(t * 1.5 * math.pi)))
                frame = bg_base.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.Resampling.BILINEAR)
            else:
                # cinematic_zoom_in / kinetic_stat_slam / timeline_reveal / quote_card_styled / focus_callout
                z = 1.0 + 0.15 * t
                cw, ch = int(W / z), int(H / z)
                x0, y0 = (W - cw) // 2, (H - ch) // 2
                frame = bg_base.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.Resampling.BILINEAR)

            mouth_lvl = speech_env[f_idx] if f_idx < len(speech_env) else abs(math.sin(t * 14.0 * math.pi))
            if dialogue_mode:
                # Multi-character coordinated stage: topic visual card above + 3 reacting characters below!
                visual_card = frame
                if is_mascot_style and cream_canvas is not None:
                    frame = cream_canvas.copy()
                else:
                    # Dimmed themed backdrop so characters + floating card pop cleanly
                    frame = Image.fromarray(np.clip(np.asarray(bg_base, dtype=np.float32) * 0.42, 0, 255).astype(np.uint8))
                draw = ImageDraw.Draw(frame)
                if H >= W:
                    cw_box, ch_box = W - 88, int(H * 0.34)
                    bx0, by0 = 44, 190
                    card_img = visual_card.resize((cw_box, ch_box), Image.Resampling.BILINEAR)
                    draw.rounded_rectangle((bx0 + 8, by0 + 12, bx0 + cw_box + 8, by0 + ch_box + 12), radius=28, fill=(20, 22, 30) if not is_mascot_style else (220, 214, 204))
                    frame.paste(card_img, (bx0, by0))
                    draw.rounded_rectangle((bx0, by0, bx0 + cw_box, by0 + ch_box), radius=26, outline=accent_rgb, width=5)
                    # Stage 3 characters side by side with guaranteed arm clearance
                    positions = [("host", W * 0.19, 0.86), ("bot", W * 0.50, 0.88), ("guest", W * 0.81, 0.86)]
                    ordered = sorted(positions, key=lambda item: 1 if item[0] == active_speaker else 0)
                    speaker_x = dict((r, px) for r, px, _ in positions).get(active_speaker, W * 0.5)
                    for role, px, base_sc in ordered:
                        speaking = (role == active_speaker)
                        sc_now = base_sc * (1.12 if speaking else 0.88)
                        look = 0.0 if speaking else (1.0 if speaker_x > px else -1.0)
                        _draw_dialogue_character(
                            draw, role, px, H - 55, sc_now, t, speaking, scene_emotion, mouth_lvl, accent_rgb, sec_rgb, look_dir=look
                        )
                else:
                    cw_box, ch_box = int(W * 0.50), int(H * 0.60)
                    bx0, by0 = 40, int(H * 0.14)
                    card_img = visual_card.resize((cw_box, ch_box), Image.Resampling.BILINEAR)
                    frame.paste(card_img, (bx0, by0))
                    draw.rounded_rectangle((bx0, by0, bx0 + cw_box, by0 + ch_box), radius=22, outline=accent_rgb, width=4)
                    positions = [("host", W * 0.64, 0.56), ("bot", W * 0.78, 0.58), ("guest", W * 0.92, 0.56)]
                    ordered = sorted(positions, key=lambda item: 1 if item[0] == active_speaker else 0)
                    speaker_x = dict((r, px) for r, px, _ in positions).get(active_speaker, W * 0.78)
                    for role, px, base_sc in ordered:
                        speaking = (role == active_speaker)
                        sc_now = base_sc * (1.12 if speaking else 0.88)
                        look = 0.0 if speaking else (1.0 if speaker_x > px else -1.0)
                        _draw_dialogue_character(
                            draw, role, px, H - 25, sc_now, t, speaking, scene_emotion, mouth_lvl, accent_rgb, sec_rgb, look_dir=look
                        )
            elif is_mascot_style and cream_canvas is not None:
                # Editorial Mascot layout: warm cream backdrop, rounded floating visual card, animated presenter
                visual_card = frame
                frame = cream_canvas.copy()
                draw = ImageDraw.Draw(frame)
                if H >= W:
                    # 9:16 vertical: rounded visual window at top, captions in middle, animated mascot at bottom
                    cw_box, ch_box = W - 88, int(H * 0.34)
                    bx0, by0 = 44, 195
                    card_img = visual_card.resize((cw_box, ch_box), Image.Resampling.BILINEAR)
                    draw.rounded_rectangle((bx0 + 8, by0 + 12, bx0 + cw_box + 8, by0 + ch_box + 12), radius=30, fill=(224, 218, 208))
                    frame.paste(card_img, (bx0, by0))
                    draw.rounded_rectangle((bx0, by0, bx0 + cw_box, by0 + ch_box), radius=26, outline=(36, 38, 44), width=5)
                    _draw_editorial_mascot(draw, W * 0.5, H - 55, scale=1.22, t=t, accent=accent_rgb)
                else:
                    # 16:9 widescreen: rounded visual window on left, animated mascot on right
                    cw_box, ch_box = int(W * 0.60), int(H * 0.66)
                    bx0, by0 = 56, int(H * 0.16)
                    card_img = visual_card.resize((cw_box, ch_box), Image.Resampling.BILINEAR)
                    draw.rounded_rectangle((bx0 + 8, by0 + 10, bx0 + cw_box + 8, by0 + ch_box + 10), radius=24, fill=(224, 218, 208))
                    frame.paste(card_img, (bx0, by0))
                    draw.rounded_rectangle((bx0, by0, bx0 + cw_box, by0 + ch_box), radius=22, outline=(36, 38, 44), width=4)
                    _draw_editorial_mascot(draw, W * 0.81, H - 25, scale=0.82, t=t, accent=accent_rgb)
            else:
                draw = ImageDraw.Draw(frame)

                # 2. Art-style frame decorations (comic borders, cyber scanlines, anime speedlines, letterbox, etc.)
                _draw_style_frame_decor(draw, W, H, theme_cfg, t)

                # 3. Topic-matched procedural centerpiece ONLY when no photo/AI art loaded
                if not has_photo_bg and action not in {"quote_card_styled", "timeline_reveal"}:
                    subj_x = W * (0.25 + 0.5 * t) if action in {"pan_left_to_right", "pan_right_to_left"} else W * 0.5
                    _draw_topic_subject(draw, visual_world, subj_x, int(H * 0.68), (0.92 if H >= W else 0.65) + 0.10 * t, character, phase=t)

            # 4. Action-specific graphic overlay (confined to card when dialogue/mascot layout is active)
            ov_x0, ov_y0, ov_w, ov_h = (bx0, by0, cw_box, ch_box) if (dialogue_mode or is_mascot_style) else (0, 0, W, H)
            if action == "kinetic_stat_slam" and stat_text:
                slam_scale = min(1.0, t * 4.0)
                f_stat = _fit_font(draw, stat_text, max_width=max(200, ov_w - 140), start_size=int(96 * max(0.5, slam_scale)), min_size=34, bold=True)
                sb = draw.textbbox((0, 0), stat_text, font=f_stat)
                sw, sh = sb[2] - sb[0], sb[3] - sb[1]
                sx, sy = ov_x0 + (ov_w - sw) // 2, ov_y0 + int(ov_h * 0.36)
                draw.rounded_rectangle((sx - 34, sy - 22, sx + sw + 34, sy + sh + 24), radius=20, fill=theme_cfg["card_bg"], outline=accent_rgb, width=theme_cfg["border_w"])
                draw.text((sx, sy), stat_text, font=f_stat, fill=accent_rgb)

            elif action == "timeline_reveal":
                bar_y = ov_y0 + int(ov_h * 0.52)
                x_start, x_end = ov_x0 + 100, ov_x0 + ov_w - 100
                cur_x = int(x_start + (x_end - x_start) * min(1.0, t * 1.35))
                draw.line((x_start, bar_y, x_end, bar_y), fill=(90, 100, 120), width=6)
                draw.line((x_start, bar_y, cur_x, bar_y), fill=accent_rgb, width=10)
                for si, lbl in enumerate(timeline_steps[:3]):
                    nx = int(x_start + (x_end - x_start) * (si / 2.0))
                    active = cur_x >= nx - 10
                    nr = 20 if active else 13
                    draw.ellipse((nx - nr, bar_y - nr, nx + nr, bar_y + nr), fill=accent_rgb if active else (70, 80, 100), outline=sec_rgb, width=4)
                    lb = draw.textbbox((0, 0), lbl, font=font_med)
                    lw_t = lb[2] - lb[0]
                    draw.text((max(ov_x0 + 30, min(ov_x0 + ov_w - 30 - lw_t, nx - lw_t // 2)), bar_y - 68), lbl, font=font_med, fill=accent_rgb if active else (180, 190, 210))

            elif action == "quote_card_styled":
                words = quote_text.split()
                q_lines: list[str] = []
                cur_l = ""
                for w in words:
                    test_l = (cur_l + " " + w).strip()
                    if len(test_l) > (28 if ov_w < 750 else 34) and cur_l:
                        q_lines.append(cur_l)
                        cur_l = w
                    else:
                        cur_l = test_l
                if cur_l:
                    q_lines.append(cur_l)
                q_lines = q_lines[:4 if (dialogue_mode or is_mascot_style) else 6]
                card_h = 150 + len(q_lines) * 48
                card_top = ov_y0 + max(24, (ov_h - card_h) // 2)
                cy_off = int((1.0 - min(1.0, t * 3.5)) * 40)
                box = (ov_x0 + 54, card_top + cy_off, ov_x0 + ov_w - 54, min(ov_y0 + ov_h - 20, card_top + card_h + cy_off))
                draw.rounded_rectangle(box, radius=20, fill=theme_cfg["card_bg"], outline=accent_rgb, width=theme_cfg["border_w"])
                qt_str = quote_title.upper()
                f_qt = _fit_font(draw, qt_str, max_width=max(180, ov_w - 180), start_size=34, min_size=20, bold=True)
                qb = draw.textbbox((0, 0), qt_str, font=f_qt)
                draw.text((ov_x0 + (ov_w - (qb[2] - qb[0])) // 2, card_top + 28 + cy_off), qt_str, font=f_qt, fill=accent_rgb)
                draw.line((ov_x0 + 90, card_top + 84 + cy_off, ov_x0 + ov_w - 90, card_top + 84 + cy_off), fill=sec_rgb, width=3)
                for li, ql in enumerate(q_lines):
                    draw.text((ov_x0 + 90, card_top + 108 + cy_off + li * 48), ql, font=font_body, fill=theme_cfg["card_text"])

            elif action == "focus_callout" and callout_label:
                slide = min(1.0, t * 3.0)
                f_co = _fit_font(draw, callout_label, max_width=max(180, ov_w - 160), start_size=42, min_size=24, bold=True)
                cb = draw.textbbox((0, 0), callout_label, font=f_co)
                cw_txt, ch_txt = cb[2] - cb[0], cb[3] - cb[1]
                bx = ov_x0 + int((-cw_txt + (cw_txt + (ov_w - cw_txt) // 2) * slide))
                by = ov_y0 + int(ov_h * 0.34)
                draw.rounded_rectangle((bx - 24, by - 16, bx + cw_txt + 24, by + ch_txt + 20), radius=14, fill=theme_cfg["card_bg"], outline=sec_rgb, width=theme_cfg["border_w"])
                draw.text((bx, by), callout_label, font=f_co, fill=accent_rgb)

            # 5. Clean style-matched top chapter header
            if top_label:
                f_top = _fit_font(draw, top_label, max_width=W - 140, start_size=48, min_size=26, bold=True)
                bbox = draw.textbbox((0, 0), top_label, font=f_top)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                tx = (W - tw) // 2
                draw.rounded_rectangle((tx - 26, 108, tx + tw + 26, 108 + th + 24), radius=14, fill=theme_cfg["card_bg"], outline=accent_rgb, width=max(2, theme_cfg["border_w"] // 2))
                draw.text((tx, 118), top_label, font=f_top, fill=accent_rgb)

            proc.stdin.write(frame.tobytes())
    finally:
        if proc.stdin:
            proc.stdin.close()
        stderr_out = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        ret = proc.wait(timeout=180)
        if ret != 0:
            raise RuntimeError(f"FFmpeg motion_story scene render failed (code {ret}): {stderr_out[-400:]}")




def _scaffold_remotion_project(studio_dir: Path) -> None:
    """Auto-creates a clean Remotion React/SVG studio motion-graphics project (zero manual files to copy)."""
    src_dir = studio_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    pkg = {
        "name": "jagnor-remotion-studio",
        "version": "1.0.0",
        "private": True,
        "dependencies": {
            "react": "^18.3.1",
            "react-dom": "^18.3.1",
            "remotion": "^4.0.220",
            "@remotion/cli": "^4.0.220",
        },
    }
    pkg_path = studio_dir / "package.json"
    if not pkg_path.exists():
        pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
    tsconfig_path = studio_dir / "tsconfig.json"
    if not tsconfig_path.exists():
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "ESNext",
                "moduleResolution": "bundler",
                "jsx": "react-jsx",
                "esModuleInterop": True,
                "skipLibCheck": True,
                "strict": False,
            },
            "include": ["src"],
        }
        tsconfig_path.write_text(json.dumps(tsconfig, indent=2) + "\n", encoding="utf-8")

    (src_dir / "index.ts").write_text(
        'import {registerRoot} from "remotion";\nimport {RemotionRoot} from "./Root";\nregisterRoot(RemotionRoot);\n',
        encoding="utf-8",
    )

    root_tsx = """import React from "react";
import {Composition} from "remotion";
import {StoryVideo, StoryProps, SceneItem} from "./StoryVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="JagnorStory"
      component={StoryVideo}
      durationInFrames={300}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{
        topic: "Jagnor AI Story",
        artStyle: "editorial_mascot",
        dialogueMode: true,
        width: 1080,
        height: 1920,
        fps: 30,
        scenes: [] as SceneItem[],
      }}
      calculateMetadata={({props}: {props: StoryProps}) => {
        const fps = props.fps || 30;
        const total = Math.max(90, (props.scenes || []).reduce((acc, s) => acc + Math.max(30, Math.round((s.durationSec || 5) * fps)), 0));
        return {durationInFrames: total, fps, width: props.width || 1080, height: props.height || 1920};
      }}
    />
  );
};
"""
    (src_dir / "Root.tsx").write_text(root_tsx, encoding="utf-8")

    story_tsx = """import React from "react";
import {AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from "remotion";

export interface SceneItem {
  narration: string;
  topLabel: string;
  speaker: string;
  emotion: string;
  durationSec: number;
  audioFile: string;
  bgFile?: string;
}

export type StoryProps = {
  topic: string;
  artStyle: string;
  dialogueMode: boolean;
  width: number;
  height: number;
  fps: number;
  scenes: SceneItem[];
};

const CharacterSVG: React.FC<{role: string; speaking: boolean; emotion: string; frame: number; accent: string; lookDir?: number}> = ({role, speaking, emotion, frame, accent, lookDir = 0}) => {
  const bounce = speaking ? -Math.abs(Math.sin(frame / 4.5)) * (emotion === "excited" || emotion === "celebrating" ? 18 : 9) : Math.sin(frame / 14) * 3;
  const mouthH = speaking ? 6 + Math.abs(Math.sin(frame / 2.2)) * 14 : 3;
  const scale = speaking ? 1.08 : 0.88;
  const opacity = speaking ? 1 : 0.8;
  const eyeDx = speaking ? 0 : lookDir * 6;
  const armRot = speaking ? Math.sin(frame / 3.5) * 14 : 0;
  return (
    <div style={{transform: `translateY(${bounce}px) scale(${scale})`, opacity}}>
      <svg width="210" height="235" viewBox="0 0 220 240">
        {role === "bot" ? (
          <>
            <line x1="110" y1="24" x2="110" y2="54" stroke="#1E2028" strokeWidth="6" />
            <circle cx="110" cy="18" r={speaking ? 11 : 9} fill={speaking ? "#38BDF8" : "#CBD5E1"} stroke="#1E2028" strokeWidth="4" />
            <rect x="44" y="192" width="34" height="32" rx="10" fill={accent} stroke="#1E2028" strokeWidth="5" />
            <rect x="142" y="192" width="34" height="32" rx="10" fill={accent} stroke="#1E2028" strokeWidth="5" />
            <rect x="30" y="54" width="160" height="142" rx="28" fill={accent} stroke="#1E2028" strokeWidth="6" />
            <circle cx="64" cy="140" r="11" fill="#F472B6" opacity="0.65" />
            <circle cx="156" cy="140" r="11" fill="#F472B6" opacity="0.65" />
            <rect x={74 + eyeDx} y="98" width="14" height="24" rx="6" fill="#1E2028" />
            <rect x={132 + eyeDx} y="98" width="14" height="24" rx="6" fill="#1E2028" />
            <rect x="90" y="140" width="40" height={mouthH} rx="6" fill="#FFFFFF" stroke="#1E2028" strokeWidth="4" />
            {[0, 1, 2, 3].map((bi) => {
              const bh = speaking ? 6 + Math.abs(Math.sin(frame / 2.4 + bi)) * 12 : 5;
              return <rect key={bi} x={72 + bi * 20} y={182 - bh} width="10" height={bh} rx="3" fill={speaking ? "#38BDF8" : "#CBD5E1"} />;
            })}
          </>
        ) : (
          <>
            <rect x="42" y="148" width="136" height="86" rx="40" fill={role === "host" ? "#E8E2D8" : "#5E8B7E"} stroke="#1E2028" strokeWidth="6" />
            {speaking ? (
              <g transform={`rotate(${armRot} 170 165)`}>
                <line x1="170" y1="168" x2="196" y2="112" stroke="#1E2028" strokeWidth="22" strokeLinecap="round" />
                <line x1="170" y1="168" x2="196" y2="112" stroke={role === "host" ? "#E8E2D8" : "#5E8B7E"} strokeWidth="14" strokeLinecap="round" />
                <circle cx="198" cy="106" r="12" fill={role === "host" ? "#FDE8D7" : "#F3D3B8"} stroke="#1E2028" strokeWidth="4" />
              </g>
            ) : null}
            <circle cx="110" cy="96" r="56" fill={role === "host" ? "#FDE8D7" : "#F3D3B8"} stroke="#1E2028" strokeWidth="6" />
            {role === "host" ? (
              <>
                <path d="M52 84 A58 58 0 0 1 168 84 Z" fill={accent} stroke="#1E2028" strokeWidth="6" />
                <rect x="44" y="76" width="132" height="16" rx="8" fill={accent} stroke="#1E2028" strokeWidth="5" />
              </>
            ) : (
              <path d="M54 88 A56 56 0 0 1 166 88 Z" fill="#2D2420" stroke="#1E2028" strokeWidth="6" />
            )}
            <circle cx={90 + eyeDx} cy="100" r={emotion === "shocked" ? 8 : 6} fill="#1E2028" />
            <circle cx={130 + eyeDx} cy="100" r={emotion === "shocked" ? 8 : 6} fill="#1E2028" />
            <ellipse cx="110" cy={124 + mouthH / 3} rx="14" ry={mouthH / 2 + 2} fill="#FFFFFF" stroke="#1E2028" strokeWidth="4" />
          </>
        )}
      </svg>
    </div>
  );
};

const SceneView: React.FC<{scene: SceneItem; artStyle: string; dialogueMode: boolean; isVertical: boolean; sceneFrames: number}> = ({scene, artStyle, dialogueMode, isVertical, sceneFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const safeFrames = Math.max(1, sceneFrames || Math.round((scene.durationSec || 5) * fps));
  const pop = spring({frame, fps, config: {damping: 14, stiffness: 160}});
  const zoom = interpolate(frame, [0, safeFrames], [1.0, 1.12], {extrapolateRight: "clamp"});
  const isLight = artStyle === "editorial_mascot";
  const bg = isLight ? "#F6F1E9" : "#0F172A";
  const fg = isLight ? "#1E2028" : "#F8FAFC";
  const accent = isLight ? "#E25822" : "#F5C451";
  const words = (scene.narration || "").split(/\s+/).filter(Boolean);
  const activeIdx = words.length > 0 ? Math.min(words.length - 1, Math.max(0, Math.floor((frame / safeFrames) * words.length))) : 0;
  const chunkStart = Math.floor(activeIdx / 5) * 5;
  const visibleWords = words.slice(chunkStart, chunkStart + 5);

  return (
    <AbsoluteFill style={{backgroundColor: bg, fontFamily: "Noto Sans, DejaVu Sans, sans-serif", padding: 44, justifyContent: "space-between"}}>
      {scene.audioFile ? <Audio src={staticFile(scene.audioFile)} /> : null}
      <div style={{display: "flex", justifyContent: "center", transform: `scale(${0.85 + 0.15 * pop})`}}>
        <div style={{background: isLight ? "#FFFFFF" : "#1E293B", color: accent, border: `4px solid ${accent}`, borderRadius: 18, padding: "12px 28px", fontSize: isVertical ? 36 : 26, fontWeight: 800, letterSpacing: 1}}>
          {(scene.topLabel || "STORY").toUpperCase()}
        </div>
      </div>

      <div style={{position: "relative", width: "100%", height: isVertical ? "38%" : "52%", borderRadius: 28, overflow: "hidden", border: `5px solid ${accent}`, boxShadow: "0 18px 40px rgba(0,0,0,0.22)", transform: `scale(${0.92 + 0.08 * pop})`}}>
        {scene.bgFile ? (
          <Img src={staticFile(scene.bgFile)} style={{width: "100%", height: "100%", objectFit: "cover", transform: `scale(${zoom})`}} />
        ) : (
          <div style={{width: "100%", height: "100%", background: isLight ? "linear-gradient(135deg,#FDE68A,#FCA5A5)" : "linear-gradient(135deg,#1E3A8A,#312E81)"}} />
        )}
      </div>

      <div style={{textAlign: "center", padding: "10px 18px", minHeight: isVertical ? 140 : 80}}>
        <div style={{fontSize: isVertical ? 54 : 38, fontWeight: 900, lineHeight: 1.25, color: fg}}>
          {visibleWords.map((w, i) => {
            const isNow = chunkStart + i === activeIdx;
            return <span key={i} style={{color: isNow ? accent : fg, marginRight: 14}}>{w.toUpperCase()}</span>;
          })}
        </div>
      </div>

      {(dialogueMode || isLight) ? (
        <div style={{display: "flex", justifyContent: "space-around", alignItems: "flex-end", paddingBottom: 16}}>
          {dialogueMode ? (
            <>
              <CharacterSVG role="host" speaking={scene.speaker === "host"} emotion={scene.emotion} frame={frame} accent={accent} lookDir={scene.speaker === "host" ? 0 : 1} />
              <CharacterSVG role="bot" speaking={scene.speaker === "bot"} emotion={scene.emotion} frame={frame} accent={accent} lookDir={scene.speaker === "host" ? -1 : (scene.speaker === "guest" ? 1 : 0)} />
              <CharacterSVG role="guest" speaking={scene.speaker === "guest"} emotion={scene.emotion} frame={frame} accent={accent} lookDir={scene.speaker === "guest" ? 0 : -1} />
            </>
          ) : (
            <CharacterSVG role="host" speaking={true} emotion={scene.emotion} frame={frame} accent={accent} />
          )}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

export const StoryVideo: React.FC<StoryProps> = ({scenes, artStyle, dialogueMode, width, height, fps}) => {
  let cursor = 0;
  const isVertical = height >= width;
  return (
    <AbsoluteFill>
      {(scenes || []).map((sc, idx) => {
        const durFrames = Math.max(30, Math.round((sc.durationSec || 5) * (fps || 30)));
        const from = cursor;
        cursor += durFrames;
        return (
          <Sequence key={idx} from={from} durationInFrames={durFrames}>
            <SceneView scene={sc} artStyle={artStyle} dialogueMode={dialogueMode} isVertical={isVertical} sceneFrames={durFrames} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
"""
    (src_dir / "StoryVideo.tsx").write_text(story_tsx, encoding="utf-8")


def _render_story_with_remotion(
    scenes: list[dict[str, Any]],
    wav_paths: list[Path],
    durs: list[float],
    bg_paths: list[Path | None],
    out_mp4: Path,
    topic: str,
    art_style: str,
    dialogue_mode: bool,
    target_size: tuple[int, int],
    studio_dir: Path,
    max_cap_sec: float = 58.0,
) -> bool:
    """Attempts studio-grade Remotion rendering; returns False gracefully if Node/Remotion is unavailable."""
    if not shutil.which("npx"):
        log.info("Remotion skipped: `npx` not found; using built-in Python motion renderer.")
        return False
    try:
        studio_dir = studio_dir.resolve()
        out_mp4 = out_mp4.resolve()
        _scaffold_remotion_project(studio_dir)
        pub_dir = studio_dir / "public"
        if pub_dir.exists():
            for old_f in pub_dir.iterdir():
                if old_f.is_file():
                    old_f.unlink(missing_ok=True)
        pub_dir.mkdir(parents=True, exist_ok=True)
        remotion_scenes: list[dict[str, Any]] = []
        for idx, (sc, wp, dur, bgp) in enumerate(zip(scenes, wav_paths, durs, bg_paths), start=1):
            aud_name = f"s_{idx:02d}.wav"
            shutil.copy2(wp, pub_dir / aud_name)
            bg_name = ""
            if bgp is not None and bgp.exists():
                ext = bgp.suffix.lower() if bgp.suffix else ".png"
                bg_name = f"bg_{idx:02d}{ext}"
                shutil.copy2(bgp, pub_dir / bg_name)
            remotion_scenes.append({
                "narration": sc["narration"],
                "topLabel": sc.get("top_label") or topic[:24],
                "speaker": sc.get("speaker") or "host",
                "emotion": sc.get("emotion") or "explaining",
                "durationSec": round(dur, 3),
                "audioFile": aud_name,
                "bgFile": bg_name,
            })
        props = {
            "topic": topic,
            "artStyle": art_style,
            "dialogueMode": dialogue_mode,
            "width": target_size[0],
            "height": target_size[1],
            "fps": 30 if target_size[1] >= target_size[0] else 24,
            "scenes": remotion_scenes,
        }
        props_path = (studio_dir / "props.json").resolve()
        props_path.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")

        if not (studio_dir / "node_modules" / "remotion").exists():
            log.info("Installing Remotion dependencies in %s...", studio_dir)
            subprocess.run(["npm", "install", "--no-audit", "--no-fund", "--legacy-peer-deps"], cwd=studio_dir, check=True, timeout=300)

        raw_out = (studio_dir / "remotion_raw.mp4").resolve()
        raw_out.unlink(missing_ok=True)
        render_cmd = [
            "npx", "remotion", "render", "src/index.ts", "JagnorStory",
            str(raw_out), f"--props={props_path}", "--codec=h264", "--concurrency=2",
        ]
        for chrome_cand in ("/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"):
            if Path(chrome_cand).exists():
                render_cmd.append(f"--browser-executable={chrome_cand}")
                break
        subprocess.run(render_cmd, cwd=studio_dir, check=True, timeout=600)
        if not raw_out.exists() or raw_out.stat().st_size < 10000:
            return False
        run_cmd([
            "ffmpeg", "-y", "-i", str(raw_out),
            "-t", f"{max_cap_sec:.3f}",
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
            "-movflags", "+faststart", str(out_mp4),
        ])
        if not verify_rendered_mp4(out_mp4, min_duration=5.0):
            return False
        log.info("Remotion studio render complete -> %s", out_mp4.name)
        return True
    except Exception as exc:
        log.warning("Remotion studio render unavailable (%s); falling back seamlessly to built-in Python renderer.", str(exc)[:180])
        return False


def run_motion_story_engine(
    topic: str,
    job_dir: Path,
    brain: CompanyBrain,
    voice: str = "en-IN-PrabhatNeural",
    public_dir: Path | None = None,
    art_style: str = "dark_cinematic",
    theme: str = "Universal Storytelling",
    character_desc: str = "",
    fact_brief: str = "",
    prior_media_urls: set[str] | None = None,
    target_duration_sec: int = 45,
    dialogue_mode: bool = False,
    render_engine: str = "python",
) -> dict[str, Any]:
    """
    All-Rounder 2D Animated Story & Universal Character Engine (`--engine motion_story`):
    1) 4-Brain Free AI Council designs a universal character sheet + 5 animated story scenes.
    2) Free `edge-tts` voices every scene (supports Indian English, US/UK English, Malayalam, Hindi).
    3) Streams real 24fps 2D vector animations (universal character motion, scale rulers,
       ticking counters, parchment quote cards, circular zoom callouts) directly to FFmpeg.
    4) Burns centered karaoke captions, enforces -14 LUFS + faststart, and exports to public/.
    """
    item_key = f"motion_story:{topic.lower().strip()}:{time.strftime('%Y%m%d', time.gmtime())}"
    brain.check_pre_flight(item_key, estimated_cost_usd=0.10)

    out_dir = job_dir / "out"
    scene_dir = job_dir / "story_scenes"
    out_dir.mkdir(parents=True, exist_ok=True)
    scene_dir.mkdir(parents=True, exist_ok=True)

    resolved_v = _resolve_voice_preset(voice)[0]
    lang_hint = "Malayalam" if resolved_v.startswith("ml-") else ("Hindi" if resolved_v.startswith("hi-") else "English")
    log.info(
        "Active Settings [motion_story]: topic='%s' | theme='%s' | art_style='%s' | voice='%s' (%s) | character='%s'",
        topic, theme, art_style, voice, lang_hint, character_desc or "auto",
    )
    council = AICouncil()
    is_long_form = int(target_duration_sec or 45) > 60
    target_sz = (1280, 720) if is_long_form else (1080, 1920)
    render_fps = 18 if is_long_form else 24
    story_pkg = council.run_motion_story_council(
        topic=topic,
        brain=brain,
        art_style=art_style,
        theme=theme,
        character_desc=character_desc,
        language_hint=lang_hint,
        fact_brief=fact_brief,
        target_duration_sec=int(target_duration_sec or 45),
        dialogue_mode=dialogue_mode,
    )
    character = story_pkg["character"]
    scenes = story_pkg["scenes"]

    scene_mp4s: list[Path] = []
    indexed_segments: list[IndexedSegment] = []
    used_media_urls: set[str] = set(prior_media_urls or set())
    cursor_t = 0.0
    remotion_wavs: list[Path] = []
    remotion_durs: list[float] = []
    remotion_bgs: list[Path | None] = []
    use_remotion = (render_engine or "python").strip().lower() == "remotion"

    for idx, sc in enumerate(scenes, start=1):
        narration = sc["narration"]
        wav_p = scene_dir / f"story_{idx:02d}.wav"
        clip_p = scene_dir / f"story_{idx:02d}.mp4"

        scene_voice = _resolve_dialogue_voice(voice, str(sc.get("speaker") or "host")) if dialogue_mode else voice
        dur = _synthesize_scene_voiceover(narration, wav_p, voice=scene_voice)
        remotion_wavs.append(wav_p)
        remotion_durs.append(dur)
        if use_remotion:
            bg_im = _fetch_story_backdrop_if_available(
                sc, art_style, idx, scene_dir, topic=topic, theme=theme, character_desc=character_desc, used_urls=used_media_urls
            )
            bg_p = scene_dir / f"remotion_bg_{idx:02d}.png"
            if bg_im is not None:
                bg_im.save(bg_p, format="PNG")
                remotion_bgs.append(bg_p)
            else:
                remotion_bgs.append(None)
        else:
            _render_motion_story_scene(
                sc,
                character,
                idx - 1,
                dur,
                wav_p,
                clip_p,
                fps=render_fps,
                art_style=art_style,
                tmp_dir=scene_dir,
                topic=topic,
                theme=theme,
                character_desc=character_desc,
                used_urls=used_media_urls,
                canvas_size=target_sz,
                dialogue_mode=dialogue_mode,
            )
            scene_mp4s.append(clip_p)

        raw_words = [w for w in narration.split() if w.strip()]
        w_dur = dur / max(len(raw_words), 1)
        tokens: list[WordToken] = []
        for wi, w in enumerate(raw_words):
            ws = cursor_t + wi * w_dur
            we = cursor_t + (wi + 1) * w_dur
            tokens.append(WordToken(word=w, start=round(ws, 3), end=round(we, 3)))

        indexed_segments.append(
            IndexedSegment(
                segment_id=idx - 1,
                speaker="NARRATOR",
                start=round(cursor_t, 3),
                end=round(cursor_t + dur, 3),
                text=narration,
                words=tokens,
            )
        )
        cursor_t += dur

    safe_slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic)[:24].strip("_").lower() or f"story_{int(time.time()) % 100000}"
    final_mp4 = out_dir / f"story_{safe_slug}_{_run_tag()}.mp4"
    max_cap_sec = max(58.0, float(target_duration_sec) * 1.35) if is_long_form else 58.0
    final_dur = min(max_cap_sec, cursor_t)

    remotion_ok = False
    if use_remotion:
        remotion_ok = _render_story_with_remotion(
            scenes, remotion_wavs, remotion_durs, remotion_bgs, final_mp4,
            topic=topic, art_style=art_style, dialogue_mode=dialogue_mode,
            target_size=target_sz, studio_dir=Path("remotion_studio"),
            max_cap_sec=final_dur,
        )
        if not remotion_ok:
            for idx, (sc, wp, dur) in enumerate(zip(scenes, remotion_wavs, remotion_durs), start=1):
                clip_p = scene_dir / f"story_{idx:02d}.mp4"
                _render_motion_story_scene(
                    sc, character, idx - 1, dur, wp, clip_p, fps=render_fps, art_style=art_style,
                    tmp_dir=scene_dir, topic=topic, theme=theme, character_desc=character_desc,
                    used_urls=used_media_urls, canvas_size=target_sz, dialogue_mode=dialogue_mode,
                )
                scene_mp4s.append(clip_p)

    if not remotion_ok:
        concat_txt = scene_dir / "concat.txt"
        concat_txt.write_text("\n".join("file '" + str(p.resolve()).replace("'", "'\\''") + "'" for p in scene_mp4s) + "\n", encoding="utf-8")
        merged_mp4 = scene_dir / "merged_story.mp4"
        run_cmd([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
            "-c", "copy", str(merged_mp4),
        ])

        ass_path = out_dir / "motion_story_01.ass"
        write_ass_captions(
            indexed_segments,
            0,
            len(indexed_segments) - 1,
            0.0,
            ass_path,
            hook_overlay="",
            target_size=target_sz,
            light_theme=(art_style or "").lower() == "editorial_mascot",
            middle_band=dialogue_mode,
        )
        ass_escaped = escape_ffmpeg_filter_path(ass_path)
        run_cmd([
            "ffmpeg", "-y",
            "-i", str(merged_mp4),
            "-t", f"{final_dur:.3f}",
            "-vf", f"scale={target_sz[0]}:{target_sz[1]},ass='{ass_escaped}'",
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
            "-movflags", "+faststart",
            str(final_mp4),
        ])

    qa_ok = verify_rendered_mp4(final_mp4, min_duration=10.0, expected_size=target_sz, max_duration=max_cap_sec + 5.0)
    export_to_public_dir([final_mp4], public_dir)
    shutil.rmtree(scene_dir, ignore_errors=True)

    clip_obj = ClipSpec(
        clip_id="story_01",
        start_segment_id=0,
        end_segment_id=len(indexed_segments) - 1,
        start_sec=0.0,
        end_sec=round(final_dur, 2),
        duration_sec=round(final_dur, 2),
        mp4_path=str(final_mp4),
        layout_mode="motion_story_16x9_long" if is_long_form else "motion_story_2d_9x16",
        qa_verified=qa_ok,
        yt_title=story_pkg["yt_title"],
        ig_caption=story_pkg["ig_caption"],
        hook_overlay=story_pkg["hook_overlay"],
        council_score=9.7,
        council_models_used=story_pkg["council_models_used"],
        contains_synthetic_media=True,
        source_url=f"motion_story:{topic}",
    )

    result = {
        "engine": "clipping",
        "source_mode": "motion_story",
        "is_long_form": is_long_form,
        "target_duration_sec": int(target_duration_sec or 45),
        "status": "APPROVAL_PENDING",
        "source_url": f"motion_story:{topic}",
        "language": lang_hint,
        "settings_applied": {
            "topic": topic, "theme": theme, "art_style": art_style, "voice": voice, "character_desc": character_desc,
        },
        "character": character,
        "council_models_used": story_pkg["council_models_used"],
        "script_source": story_pkg.get("script_source", "ai"),
        "episode_continuity": {
            "recap": " ".join(sc["narration"] for sc in scenes[:3])[:320],
            "ending_line": scenes[-1]["narration"] if scenes else "",
            "visual_prompts": [sc.get("visual_prompt", "")[:100] for sc in scenes],
            "used_media_urls": sorted(used_media_urls),
        },
        "clips": [asdict(clip_obj)],
    }
    brain.record_completion(
        item_key,
        "motion_story",
        0.10,
        {"topic": topic, "character": character["name"], "mp4_path": str(final_mp4)},
    )
    return result


# ============================================================================
# 9. UNIFIED CLI ENTRYPOINT (TREND SCOUT + 4-BRAIN FREE AI COUNCIL + SOCIAL PUBLISHER)
# ============================================================================

_SENSITIVE_TOPIC_RE = re.compile(
    r"\b(kill(?:ed|s|ing)?|dead|death|dies|died|dying|murder\w*|shoot(?:ing|er|ings)?|shot dead|stabb\w*|attack(?:s|ed)?|"
    r"bomb\w*|war|massacre|terror\w*|hostage\w*|rape\w*|abus\w*|suicide|trump|biden|harris|modi|putin|netanyahu|"
    r"election\w*|vote[sd]?|voting|senate|congress|parliament|bjp|democrat\w*|republican\w*|gop|lawsuit|sued|arrest\w*|"
    r"scandal|crash(?:es|ed)?|explosion|wildfire|flood\w*|hurricane|earthquake|tsunami|victims?|tragedy|funeral|"
    r"obituary|shutdown|strike|protest\w*|riot\w*|gaza|ukraine|israel|hamas|nude|leak(?:ed)?|vs\.?|odds|score|live updates?)\b",
    re.IGNORECASE,
)
_TOPIC_STOPWORDS = {"the", "and", "for", "with", "that", "this", "from", "into", "how", "why", "what", "when", "are", "was",
                    "has", "have", "its", "can", "your", "you", "will", "just", "about", "more", "than", "all", "new"}


def _is_safe_topic(text: str) -> bool:
    """Unattended auto-publishing must never post tragedies, politics or breaking-news claims."""
    return not _SENSITIVE_TOPIC_RE.search(text or "")


def _topic_tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(w) >= 3 and w not in _TOPIC_STOPWORDS}


def _is_similar_topic(cand: str, previous: list[str]) -> bool:
    ct = _topic_tokens(cand)
    if not ct:
        return False
    cl = cand.lower().strip()
    for prev in previous:
        pl = prev.lower().strip()
        if not pl:
            continue
        if cl == pl or cl in pl or pl in cl:
            return True
        pt = _topic_tokens(prev)
        if pt:
            inter = len(ct & pt)
            ratio = inter / max(1, len(ct | pt))
            if ratio >= 0.5 or (inter >= 3 and ratio >= 0.33):
                return True
    return False


def _previous_topics(ledger_data: dict[str, Any]) -> list[str]:
    """All topics ever produced by the two daily engines (ledger keys look like `engine:topic:YYYYMMDD`)."""
    topics: list[str] = []
    for key in ledger_data.get("processed_items", []):
        k = str(key)
        for eng in ("motion_story:", "ai_faceless:"):
            if k.startswith(eng):
                body = k[len(eng):]
                topics.append(body.rsplit(":", 1)[0] if body.count(":") else body)
    for st in ledger_data.get("completed_series_topics", []) or []:
        if st:
            topics.append(str(st))
    act = ledger_data.get("active_series")
    if isinstance(act, dict) and act.get("base_topic"):
        topics.append(str(act["base_topic"]))
    return topics


def _parse_rss_entries(xml_bytes: bytes, limit: int = 12) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    seen: set[str] = set()
    try:
        root = ET.fromstring(xml_bytes)
        for item in root.findall(".//item"):
            t_el = item.find("title")
            if t_el is not None and t_el.text:
                clean = " ".join(t_el.text.split()).strip()
                clean = re.sub(r"\s+[-|]\s+[^-|]{2,40}$", "", clean).strip()
                d_el = item.find("description")
                raw_desc = html.unescape(d_el.text or "") if d_el is not None else ""
                clean_desc = " ".join(re.sub(r"<[^>]+>", " ", raw_desc).split()).strip()[:220]
                if len(clean) >= 6 and clean not in seen:
                    seen.add(clean)
                    entries.append((clean, clean_desc))
            if len(entries) >= limit:
                break
    except Exception:
        pass
    return entries




def fetch_wikipedia_brief(topic: str, max_chars: int = 1400) -> str:
    """
    Free, keyless Verified Fact Brief for ANY topic (manual or auto): Wikipedia search + intro extract.
    Returns "" when nothing relevant is found (caller then uses the no-invented-numbers rule).
    """
    topic = (topic or "").strip()
    if not topic:
        return ""
    script = _detect_script(topic)
    langs = ([script[0]] if script and script[0] in ("ml", "hi", "bn", "pa", "gu", "ta", "te", "kn", "th", "ar", "he", "ja", "ko", "zh") else []) + ["en"]
    q_tokens = _topic_tokens(topic) or {w for w in re.findall(r"\w+", topic.lower()) if len(w) >= 2}
    hdr = {"User-Agent": "JagnorClippingBot/1.0 (https://github.com/jagnor110-cell/Jagnor)", "Accept": "application/json"}
    for lang in langs:
        try:
            base = f"https://{lang}.wikipedia.org/w/api.php"
            sq = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": topic, "srlimit": 3, "format": "json"})
            body, _ = urlopen_with_retry(urllib.request.Request(f"{base}?{sq}", headers=hdr), timeout=15, max_attempts=2, base_backoff=1.0)
            hits = (json.loads(body).get("query") or {}).get("search") or []
            for h in hits:
                title = str(h.get("title") or "")
                t_tokens = _topic_tokens(title) or {w for w in re.findall(r"\w+", title.lower()) if len(w) >= 2}
                if q_tokens and not (q_tokens & t_tokens) and lang == "en":
                    continue
                eq = urllib.parse.urlencode({"action": "query", "prop": "extracts|pageprops", "exintro": 1, "explaintext": 1,
                                             "redirects": 1, "titles": title, "format": "json"})
                body2, _ = urlopen_with_retry(urllib.request.Request(f"{base}?{eq}", headers=hdr), timeout=15, max_attempts=2, base_backoff=1.0)
                pages = (json.loads(body2).get("query") or {}).get("pages") or {}
                for pg in pages.values():
                    if "disambiguation" in (pg.get("pageprops") or {}):
                        continue
                    ext = re.sub(r"\s+", " ", str(pg.get("extract") or "")).strip()
                    if len(ext) < 80 or re.search(r"may (also )?refer to", ext[:200], re.I):
                        continue
                    cut = ext[:max_chars]
                    if len(ext) > max_chars and "." in cut:
                        cut = cut[: cut.rfind(".") + 1]
                    return f"Wikipedia ({title}): {cut}"
        except Exception as err:
            log.warning("Wikipedia brief (%s) unavailable: %s", lang, err)
    return ""


def enrich_fact_brief(topic: str, fact_brief: str) -> str:
    """Merge trending headline brief with Wikipedia & Google News RSS background so councils always have grounded facts."""
    has_real = bool(fact_brief.strip()) and "headline only" not in fact_brief.lower()
    wiki = fetch_wikipedia_brief(topic)
    if not wiki:
        short_kw = " ".join(re.findall(r"[A-Za-z0-9]{3,}", topic)[:4])
        if short_kw and short_kw.lower() != topic.lower():
            wiki = fetch_wikipedia_brief(short_kw)
    if not wiki and not has_real:
        try:
            q_enc = urllib.parse.quote_plus(topic[:80])
            rss_url = f"https://news.google.com/rss/search?q={q_enc}&hl=en-US&gl=US&ceid=US:en"
            req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
            raw, _ = urlopen_with_retry(req, timeout=15, max_attempts=1)
            entries = _parse_rss_entries(raw, limit=3)
            if entries:
                wiki = " | ".join(f"{t}. {d}".strip() for t, d in entries if t)[:700]
        except Exception:
            pass
    if not wiki:
        return fact_brief
    if has_real:
        return f"{fact_brief}\nBackground: {wiki}"
    base = fact_brief.strip()
    return f"{wiki}\n{base}" if base else wiki


def _fetch_live_trending_items(max_items: int = 18) -> list[tuple[str, str]]:
    """
    Fetches live daily trending topics + RSS summary snippets 100% free (zero API keys) from:
      1) Google Trends Daily RSS (US & India)
      2) Google News Top Stories RSS
      3) Hacker News Top Stories (Tech/AI/Science)
    Fails gracefully to [] when offline.
    """
    items: list[tuple[str, str]] = []
    seen: set[str] = set()
    rss_urls = [
        "https://trends.google.com/trending/rss?geo=US",
        "https://trends.google.com/trending/rss?geo=IN",
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    ]
    for u in rss_urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (JagnorTrendScout/2.0)"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                for title, desc in _parse_rss_entries(resp.read(), limit=8):
                    if title not in seen:
                        seen.add(title)
                        items.append((title, desc))
        except Exception as exc:
            log.debug("Trend RSS skipped (%s): %s", u, exc)

    try:
        req = urllib.request.Request(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers={"User-Agent": "JagnorTrendScout/2.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            ids = json.loads(resp.read().decode("utf-8"))[:6]
        for sid in ids:
            try:
                sreq = urllib.request.Request(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                    headers={"User-Agent": "JagnorTrendScout/2.0"},
                )
                with urllib.request.urlopen(sreq, timeout=8) as sresp:
                    item = json.loads(sresp.read().decode("utf-8"))
                t = " ".join(str(item.get("title") or "").split()).strip()
                if len(t) >= 8 and t not in seen:
                    seen.add(t)
                    items.append((t, ""))
            except Exception:
                continue
    except Exception as exc:
        log.debug("Hacker News trend fetch skipped: %s", exc)

    return items[:max_items]




def pick_fresh_auto_topic_with_context(theme: str, brain: CompanyBrain, engine: str) -> tuple[str, str]:
    """
    Live Trending Topic Selector returning `(topic_title, grounded_fact_brief)` so the
    script council uses real headline facts instead of inventing numbers or dates.
    """
    ledger_data, _ = load_ledger(brain.ledger_path.parent if brain.ledger_path else brain.brain_dir)
    all_previous = _previous_topics(ledger_data)
    recent_titles = all_previous[-12:]

    raw_items = [(t, d) for t, d in _fetch_live_trending_items(max_items=30) if _is_safe_topic(t)][:18]
    live_trends = [t for t, _ in raw_items]
    if live_trends:
        log.info("Live Trend Scout fetched %d real-time trending topics.", len(live_trends))

    def _match_fact_brief(chosen: str) -> str:
        ct = _topic_tokens(chosen)
        scored = []
        for t, d in raw_items:
            overlap = len(ct & _topic_tokens(f"{t} {d}"))
            if overlap >= max(2, (len(ct) * 2 + 4) // 5):  # >=2 shared words and ~40% of the title
                scored.append((overlap, f"{t}. {d}".strip()))
        scored.sort(key=lambda x: x[0], reverse=True)
        return " | ".join(s for _, s in scored[:2]) if scored else ""

    council = AICouncil()
    if live_trends:
        trend_bullets = "\n".join(f"- {t}" + (f" ({d[:110]})" if d else "") for t, d in raw_items)
        prompt = (
            f"Engine: {engine} | Theme: {theme}\n"
            f"Live Trending Headlines Right Now:\n{trend_bullets}\n\n"
            f"Pick the SINGLE most fascinating, curiosity-driving trending topic above (prefer science, tech, AI, space, money, world events, or viral breakthroughs; avoid sensitive tragedies or politics) "
            f"and rewrite it as ONE punchy YouTube Shorts title (5-10 words, no quotes, no numbering).\n"
            f"Avoid repeating recent titles: {recent_titles}"
        )
    else:
        prompt = (
            f"Engine: {engine} | Theme: {theme}. Give ONE fresh, high-curiosity YouTube Shorts topic "
            f"(5-10 words, no quotes, no numbering) that viewers haven't seen yet. "
            f"Avoid repeating recent titles: {recent_titles}"
        )

    for provider in ("groq", "gemini", "openrouter"):
        ai_raw = council.invoke_stage(
            provider,
            "Return ONLY one short, viral YouTube Shorts topic title (5-10 words, plain text, no quotes, no bullet or numbering).",
            prompt,
        )
        if ai_raw:
            lines = [ln for ln in ai_raw.strip().splitlines() if ln.strip()]
            first = lines[0] if lines else ""
            first = re.sub(r"^\s*(?:[-*\u2022]|\d{1,2}[.)])\s+", "", first).strip().strip('"').strip("'").strip("*").strip()
            cand = " ".join(first.split())[:72]
            looks_like_preface = cand.endswith(":") or cand.lower().startswith(("here", "sure", "title", "okay", "ok,", "topic"))
            if (
                len(cand) >= 10
                and not looks_like_preface
                and _is_safe_topic(cand)
                and not _is_similar_topic(cand, all_previous)
            ):
                log.info("Trending auto-topic selected via [%s]: %s", provider, cand)
                brief = _match_fact_brief(cand) or (
                    f"Trending headline only: {cand}. No other verified facts available - use no numbers, dates or sales figures."
                    if live_trends else ""
                )
                return cand, brief
            log.info("AI topic from [%s] rejected (preface/unsafe/duplicate): %r", provider, cand[:80])

    # Without the AI Council a raw headline would become a template script with no facts behind it,
    # so we deliberately fall through to the evergreen pool instead of auto-publishing a raw news title.
    if live_trends:
        log.info("AI Council unavailable for trend rewrite; using evergreen pool instead of a raw headline.")

    fallback_pool = [
        "How Deep The Mariana Trench Really Goes",
        "How Far Voyager 1 Has Traveled Into Deep Space",
        "Why The Roman Concrete Formula Lasted 2000 Years",
        "How Tall Olympus Mons Is Compared To Everest",
        "The Forgotten Library That Changed Ancient Science",
        "How Fast A Neutron Star Spins In Deep Space",
        "Why The Great Pyramid Aligns Almost Perfectly True North",
        "How Much Gold Is Still Hidden Inside Earth's Core",
        "The Smallest Creature That Can Survive Outer Space",
        "How One Algorithm Changed Modern Navigation Forever",
    ]
    for cand in fallback_pool:
        if not _is_similar_topic(cand, all_previous):
            log.info("Auto-topic selected from curated pool: %s", cand)
            return cand, ""
    return f"{theme} Untold Story {time.strftime('%Y%m%d%H%M', time.gmtime())}", ""


def pick_fresh_auto_topic(theme: str, brain: CompanyBrain, engine: str) -> str:
    return pick_fresh_auto_topic_with_context(theme, brain, engine)[0]

SERIES_ART_STYLES: tuple[str, ...] = (
    "anime",
    "comic_book",
    "dark_cinematic",
    "3d_pixar",
    "cyberpunk",
    "oil_painting",
)

SERIES_ANGLES: tuple[tuple[str, str], ...] = (
    ("Part 1", "Focus ONLY on the surprising origin, hook, and core discovery of this topic. End with a short cliffhanger teasing Part 2 tomorrow (e.g. 'Follow for Part 2 tomorrow')."),
    ("Part 2", "Continue the series with a COMPLETELY DIFFERENT angle from Part 1: focus on the hidden mechanics, wild scale, or surprising behind-the-scenes details. Do NOT repeat Part 1's intro, and end by teasing the Part 3 finale."),
    ("Part 3", "Deliver the finale with a COMPLETELY DIFFERENT angle from Parts 1 & 2: focus on the strangest consequence, unsolved mystery, or what happens next, ending with a strong comment question."),
)


def resolve_series_auto_topic(
    theme: str,
    brain: CompanyBrain,
    engine: str,
    series_days: int,
    default_art_style: str,
    explicit_title: str = "",
) -> tuple[str, str, str, dict[str, Any] | None]:
    """
    When `series_days > 1` (e.g. 3), keeps the SAME core topic and SAME art style across
    Part 1, Part 2, and Part 3 — continuing directly from where the previous part left off
    and banning any visual prompts or stock URLs already used in earlier parts.
    Supports both auto-picked topics and manual custom topics (`explicit_title`).
    """
    clean_explicit = (explicit_title or "").strip()
    if series_days <= 1:
        if clean_explicit:
            return clean_explicit, "", default_art_style, None
        topic, brief = pick_fresh_auto_topic_with_context(theme, brain, engine)
        return topic, brief, default_art_style, None

    ledger_dir = brain.ledger_path.parent if brain.ledger_path else brain.brain_dir
    ledger_data, _ = load_ledger(ledger_dir)
    cur = ledger_data.get("active_series")
    same_custom = (
        not clean_explicit
        or (isinstance(cur, dict) and clean_explicit.lower() == str(cur.get("base_topic") or "").lower())
    )
    if (
        isinstance(cur, dict)
        and cur.get("base_topic")
        and int(cur.get("day", 0)) < int(cur.get("max_days", series_days))
        and cur.get("engine") == engine
        and same_custom
    ):
        day = int(cur["day"]) + 1
        max_days = int(cur.get("max_days", series_days))
        base_topic = str(cur["base_topic"])
        base_brief = str(cur.get("fact_brief") or "")
        chosen_style = str(cur.get("art_style") or default_art_style)
        series_index = int(cur.get("series_index", 0))
        episodes = list(cur.get("episodes") or [])
        prior_visuals = list(cur.get("used_visual_prompts") or [])
        prior_urls = list(cur.get("used_media_urls") or [])
    else:
        day = 1
        max_days = series_days
        if clean_explicit:
            base_topic, base_brief = clean_explicit, ""
            chosen_style = default_art_style if default_art_style in ART_STYLE_PROMPTS else "anime"
            series_index = int(cur.get("series_index", 0)) if isinstance(cur, dict) else 0
        else:
            base_topic, base_brief = pick_fresh_auto_topic_with_context(theme, brain, engine)
            prev_style = str(cur.get("art_style") or "") if isinstance(cur, dict) else ""
            series_index = (int(cur.get("series_index", -1)) + 1) if isinstance(cur, dict) else 0
            chosen_style = SERIES_ART_STYLES[series_index % len(SERIES_ART_STYLES)]
            if chosen_style == prev_style:
                series_index += 1
                chosen_style = SERIES_ART_STYLES[series_index % len(SERIES_ART_STYLES)]
        episodes = []
        prior_visuals = []
        prior_urls = []

    part_tag, angle_note = SERIES_ANGLES[(day - 1) % len(SERIES_ANGLES)]
    part_label = f"{part_tag}/{max_days}"
    continuity_lines = [
        f"3-Day Series {part_label} on '{base_topic}'. {angle_note} Include '{part_label}' in the YouTube Shorts title.",
        "VISUAL ACCURACY RULE: Every scene's visual_prompt and stock_keywords MUST directly match the exact event spoken in THAT scene.",
    ]
    if episodes:
        last_ep = episodes[-1]
        recap_block = " | ".join(f"Part {e.get('part')}: {e.get('recap', '')[:140]}" for e in episodes[-2:])
        continuity_lines.append(
            f"DIRECT CONTINUATION: Pick up RIGHT where Part {last_ep.get('part')} left off (it ended on: \"{last_ep.get('ending_line', '')}\"). "
            f"Already covered (DO NOT REPEAT): {recap_block}."
        )
    if prior_visuals:
        continuity_lines.append(
            "DO NOT REPEAT ANY VISUALS FROM EARLIER PARTS. Already shown (create completely NEW scenes/angles/subjects): "
            + "; ".join(prior_visuals[-10:])
        )
    series_note = "\n".join(continuity_lines)
    combined_brief = f"{series_note}\n{base_brief}".strip()
    active_topic = f"{base_topic} ({part_label})"
    next_state = {
        "engine": engine,
        "base_topic": base_topic,
        "fact_brief": base_brief,
        "day": day,
        "max_days": max_days,
        "art_style": chosen_style,
        "series_index": series_index,
        "episodes": episodes,
        "used_visual_prompts": prior_visuals,
        "used_media_urls": prior_urls,
        "updated_utc": time.strftime("%Y-%m-%d", time.gmtime()),
    }
    log.info(
        "Series mode [%s]: base_topic='%s' | art_style='%s' | prior_parts=%d | blocked_prior_urls=%d",
        part_label, base_topic, chosen_style, len(episodes), len(prior_urls),
    )
    return active_topic, combined_brief, chosen_style, next_state


def save_series_state(
    brain: CompanyBrain,
    state: dict[str, Any] | None,
    manifest: dict[str, Any] | None = None,
) -> None:
    if state is None or brain.ledger_path is None:
        return
    if isinstance(manifest, dict) and isinstance(manifest.get("episode_continuity"), dict):
        ec = manifest["episode_continuity"]
        state.setdefault("episodes", []).append({
            "part": state.get("day", 1),
            "recap": str(ec.get("recap") or "")[:320],
            "ending_line": str(ec.get("ending_line") or "")[:200],
        })
        prior_vp = list(state.get("used_visual_prompts") or [])
        for vp in ec.get("visual_prompts") or []:
            if vp and vp not in prior_vp:
                prior_vp.append(vp)
        state["used_visual_prompts"] = prior_vp[-20:]
        prior_urls = set(state.get("used_media_urls") or []) | set(ec.get("used_media_urls") or [])
        state["used_media_urls"] = sorted(prior_urls)[-60:]
    try:
        data = json.loads(brain.ledger_path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if state.get("base_topic"):
        done_topics = list(data.get("completed_series_topics") or [])
        bt = str(state["base_topic"]).strip()
        if bt and bt.lower() not in {x.lower() for x in done_topics}:
            done_topics.append(bt)
        data["completed_series_topics"] = done_topics[-100:]
    data["active_series"] = state
    atomic_write_json(brain.ledger_path, data)



def main() -> int:
    parser = argparse.ArgumentParser(
        description="Jagnor AI Master Company Worker — 4-Brain Free AI Council, Trend Discovery & Social Publishing"
    )
    parser.add_argument(
        "--stage",
        default="build",
        choices=["build", "publish", "full"],
        help="`build` (discover/render & pause at APPROVAL_PENDING), `publish` (run built-in social publisher), or `full` (discover + build + publish)",
    )
    parser.add_argument(
        "--engine",
        default="auto",
        choices=["auto", "motion_story", "ai_faceless", "clipping", "raw_video_drop", "digital_product", "b2b_agency", "carousel_funnel"],
        help="Department engine to execute (`auto` = Executive AI Council chooses & pivots automatically)",
    )
    parser.add_argument("--job-dir", required=True, help="Working directory for this ticket/job")
    parser.add_argument("--brain-dir", default=None, help="Path to company `brain/` directory")
    parser.add_argument("--public-dir", default=None, help="Optional `public/` directory for GitHub Pages hosting")
    parser.add_argument("--inbox-dir", default="./inbox_videos", help="[raw_video_drop] Folder containing Canva/Fabbler/Digital Maker/Qwen MP4s")

    parser.add_argument("--url", default=None, help="[clipping] Explicit video URL (if omitted, Trend Scout auto-discovers)")
    parser.add_argument("--niche", default="AI agents automation tech podcast", help="[clipping] Niche query/hashtag for Trend Scout")
    parser.add_argument(
        "--trend-platform",
        default="auto",
        choices=["auto", "youtube", "instagram"],
        help="[clipping] Where Trend Scout searches when --url is omitted",
    )
    parser.add_argument("--max-clips", type=int, default=3, help="[clipping] Max clips to render")
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"], help="[clipping] Execution device")
    parser.add_argument("--model", default="large-v3-turbo", help="[clipping] WhisperX / faster-whisper model")
    parser.add_argument("--allow-all-licenses", action="store_true", help="[clipping] Disable CC-only filter")
    parser.add_argument("--slice-start", default="", help="[clipping] Optional start timestamp (HH:MM:SS, MM:SS, or seconds) for a 15-min slice of long videos")

    parser.add_argument("--title", default="", help="[ai_faceless / digital_product / carousel_funnel] Title or topic")
    parser.add_argument(
        "--art-style",
        default="dark_cinematic",
        choices=list(ART_STYLE_PROMPTS.keys()),
        help="[all video engines] Visual art style preset for scenes/clips",
    )
    parser.add_argument(
        "--aspect-ratio",
        default="9:16",
        choices=list(ASPECT_RATIOS.keys()),
        help="[clipping / raw_video_drop] Output video aspect ratio (9:16, 16:9, 1:1, 4:5)",
    )
    parser.add_argument(
        "--theme",
        default="Universal Storytelling",
        help="[motion_story / ai_faceless] Content niche/theme guiding script & visuals",
    )
    parser.add_argument(
        "--voice",
        default="deep_male",
        help="[motion_story / ai_faceless] Voice mood preset (deep_male, serious_male, mysterious_male, happy_male, deep_female, serious_female, mysterious_female, happy_female, etc.) or raw edge-tts voice",
    )
    parser.add_argument(
        "--character",
        default="",
        help="[motion_story] Optional character description (leave blank for universal auto-creation)",
    )
    parser.add_argument(
        "--auto-topic",
        action="store_true",
        help="[motion_story / ai_faceless] Auto-generate a fresh non-duplicate topic (used on scheduled runs)",
    )
    parser.add_argument(
        "--series-days",
        type=int,
        default=1,
        help="[motion_story / ai_faceless] Keep the same core topic for N consecutive auto-topic runs with a different angle & art style each day (e.g. 3)",
    )
    parser.add_argument(
        "--target-duration",
        type=int,
        default=45,
        help="[motion_story] Target video length in seconds (45=Short 9:16; 180=3m, 300=5m, 480=8m widescreen 16:9 YouTube video)",
    )
    parser.add_argument(
        "--dialogue-mode",
        action="store_true",
        help="[motion_story] Multi-character animated conversation (3 characters with distinct voices & coordinated movements)",
    )
    parser.add_argument(
        "--render-engine",
        default="python",
        choices=["python", "remotion"],
        help="[motion_story] Visual motion renderer: python (fast built-in 24fps) or remotion (30fps React/SVG studio motion graphics)",
    )
    parser.add_argument("--price", type=float, default=17.0, help="[digital_product / b2b_agency] Price in USD")
    parser.add_argument("--source-app-dir", default=None, help="[digital_product] Optional folder to bundle into zip")

    parser.add_argument("--client", default="Acme Corp", help="[b2b_agency] Client name")
    parser.add_argument("--notes", default="", help="[b2b_agency / carousel_funnel] Discovery notes or semicolon-separated points")

    parser.add_argument(
        "--approve-manifest",
        action="store_true",
        help="Pass Paperclip Human Approval Gate (transitions APPROVAL_PENDING -> APPROVED before publishing)",
    )
    parser.add_argument("--platforms", default="youtube,instagram", help="Comma-separated platforms (youtube,instagram)")
    parser.add_argument("--max-daily-posts", type=int, default=4, help="Max posts/platform per rolling 24h")
    parser.add_argument("--min-gap-hours", type=float, default=3.5, help="Min hours between posts on same platform")
    parser.add_argument("--skip-spacing-check", action="store_true", help="Bypass spacing check for immediate release")
    parser.add_argument("--apply-jitter", action="store_true", help="Sleep random 0..10m before calling social APIs")
    parser.add_argument("--dry-run-publish", action="store_true", help="Simulate YouTube/Instagram API calls locally")

    args = parser.parse_args()
    job_dir = Path(args.job_dir)
    job_dir.mkdir(parents=True, exist_ok=True)
    brain_dir = Path(args.brain_dir) if args.brain_dir else (job_dir / "brain")
    public_dir = Path(args.public_dir) if args.public_dir else None
    manifest_path = job_dir / "manifest.json"

    build_started = args.stage in {"build", "full"}
    build_finished = False
    try:
        if args.stage in {"build", "full"}:
            brain = CompanyBrain.load(brain_dir)
            auto_mode = (args.engine == "auto")
            active_engine = args.engine
            if auto_mode:
                exec_council = AICouncil()
                active_engine, dispatch_reason = exec_council.dispatch_department(
                    brain=brain,
                    inbox_dir=Path(args.inbox_dir),
                    theme=args.theme,
                    url=(args.url or ""),
                    explicit_title=(args.title or ""),
                    notes=(args.notes or ""),
                )
                log.info("Executive Board Dispatcher chose [%s] -> %s", active_engine, dispatch_reason)

            def _execute_department(eng_name: str, repair_feedback: str = "") -> dict[str, Any]:
                if eng_name == "clipping":
                    explicit_url = (args.url or "").strip()
                    if explicit_url:
                        candidate_urls = [explicit_url]
                    else:
                        cookie_args = get_ytdlp_cookie_args(job_dir)
                        log.info("Launching Department #1 Trend Scout (niche='%s', platform='%s')...", args.niche, args.trend_platform)
                        candidate_urls = discover_trending_candidates(
                            niche_query=args.niche,
                            brain=brain,
                            trend_platform=args.trend_platform,
                            require_cc=not args.allow_all_licenses,
                            cookie_args=cookie_args,
                        )

                    manifest = None
                    last_err: Exception | None = None
                    for cand_idx, cand_url in enumerate(candidate_urls, start=1):
                        try:
                            log.info("Attempting candidate %d/%d: %s", cand_idx, len(candidate_urls), cand_url)
                            manifest = run_clipping_engine(
                                url=cand_url,
                                job_dir=job_dir,
                                brain=brain,
                                max_clips=args.max_clips,
                                device=args.device,
                                model_name=args.model,
                                allow_all_licenses=args.allow_all_licenses,
                                public_dir=public_dir,
                                art_style=args.art_style,
                                aspect_ratio=args.aspect_ratio,
                                slice_start=args.slice_start,
                            )
                            break
                        except Exception as err:
                            log.warning("Candidate %d (%s) failed (%s); trying next candidate...", cand_idx, cand_url, err)
                            cleanup_heavy_temp_files(job_dir)
                            last_err = err
                    if manifest is None:
                        raise RuntimeError(f"All {len(candidate_urls)} trending candidates failed. Last error: {last_err}")

                elif eng_name == "motion_story":
                    series_state = None
                    active_style = args.art_style
                    if args.series_days > 1 or args.auto_topic or not (args.title or "").strip():
                        active_topic, fact_brief, active_style, series_state = resolve_series_auto_topic(
                            args.theme, brain, "motion_story", args.series_days, args.art_style,
                            explicit_title="" if args.auto_topic else (args.title or ""),
                        )
                    else:
                        active_topic, fact_brief = args.title.strip(), ""
                    if (args.notes or "").strip():
                        fact_brief = f"User Content Brief / Key Points: {args.notes.strip()}\n{fact_brief}".strip()
                    if repair_feedback:
                        fact_brief = f"RED-TEAM CRITIC REPAIR DIRECTIVE (FIX THIS): {repair_feedback}\n{fact_brief}".strip()
                    wiki_query = series_state["base_topic"] if series_state else active_topic
                    fact_brief = enrich_fact_brief(wiki_query, fact_brief)
                    prior_urls = set(series_state.get("used_media_urls") or []) if series_state else set()
                    eff_render = "python" if repair_feedback else args.render_engine
                    manifest = run_motion_story_engine(
                        topic=active_topic,
                        job_dir=job_dir,
                        brain=brain,
                        voice=args.voice,
                        public_dir=public_dir,
                        art_style=active_style,
                        theme=args.theme,
                        character_desc=args.character,
                        fact_brief=fact_brief,
                        prior_media_urls=prior_urls,
                        target_duration_sec=args.target_duration,
                        dialogue_mode=args.dialogue_mode,
                        render_engine=eff_render,
                    )
                    if series_state and manifest.get("clips"):
                        _pl = f"Part {series_state['day']}/{series_state['max_days']}"
                        _shorts_sfx = "" if int(args.target_duration or 45) > 60 else " #Shorts"
                        for _c in manifest["clips"]:
                            _yt = str(_c.get("yt_title") or "")
                            if _pl.lower() not in _yt.lower():
                                _base_yt = _yt.replace("#Shorts", "").replace("#shorts", "").strip()[:75]
                                _c["yt_title"] = f"{_base_yt} | {_pl}{_shorts_sfx}"[:100]
                    if series_state is not None:
                        _dur_map = {180: "long_3m", 300: "long_5m", 480: "long_8m"}
                        series_state["duration_preset"] = _dur_map.get(int(args.target_duration or 45), "short_45s")
                        series_state["dialogue_mode"] = bool(args.dialogue_mode)
                        series_state["render_engine"] = args.render_engine
                        series_state["voice"] = args.voice
                        series_state["theme"] = args.theme
                    save_series_state(brain, series_state, manifest)
                elif eng_name == "ai_faceless":
                    series_state = None
                    active_style = args.art_style
                    if args.series_days > 1 or args.auto_topic or not (args.title or "").strip():
                        active_topic, fact_brief, active_style, series_state = resolve_series_auto_topic(
                            args.theme, brain, "ai_faceless", args.series_days, args.art_style,
                            explicit_title="" if args.auto_topic else (args.title or ""),
                        )
                    else:
                        active_topic, fact_brief = args.title.strip(), ""
                    if (args.notes or "").strip():
                        fact_brief = f"User Content Brief / Key Points: {args.notes.strip()}\n{fact_brief}".strip()
                    if repair_feedback:
                        fact_brief = f"RED-TEAM CRITIC REPAIR DIRECTIVE (FIX THIS): {repair_feedback}\n{fact_brief}".strip()
                    wiki_query = series_state["base_topic"] if series_state else active_topic
                    fact_brief = enrich_fact_brief(wiki_query, fact_brief)
                    prior_urls = set(series_state.get("used_media_urls") or []) if series_state else set()
                    manifest = run_ai_faceless_engine(
                        topic=active_topic,
                        job_dir=job_dir,
                        brain=brain,
                        voice=args.voice,
                        public_dir=public_dir,
                        art_style=active_style,
                        theme=args.theme,
                        character_desc=args.character,
                        fact_brief=fact_brief,
                        prior_media_urls=prior_urls,
                    )
                    if series_state and manifest.get("clips"):
                        _pl = f"Part {series_state['day']}/{series_state['max_days']}"
                        for _c in manifest["clips"]:
                            _yt = str(_c.get("yt_title") or "")
                            if _pl.lower() not in _yt.lower():
                                _base_yt = _yt.replace("#Shorts", "").replace("#shorts", "").strip()[:75]
                                _c["yt_title"] = f"{_base_yt} | {_pl} #Shorts"[:100]
                    save_series_state(brain, series_state, manifest)
                elif eng_name == "raw_video_drop":
                    manifest = run_raw_video_drop_engine(
                        inbox_dir=Path(args.inbox_dir),
                        job_dir=job_dir,
                        brain=brain,
                        device=args.device,
                        model_name=args.model,
                        public_dir=public_dir,
                        art_style=args.art_style,
                        aspect_ratio=args.aspect_ratio,
                    )
                elif eng_name == "digital_product":
                    src_dir = Path(args.source_app_dir) if args.source_app_dir else None
                    safe_prod_title = (args.title or "").strip() or "Jagnor Pro Automation Suite"
                    manifest = run_digital_product_engine(
                        product_title=safe_prod_title,
                        price_usd=args.price,
                        source_app_dir=src_dir,
                        job_dir=job_dir,
                        brain=brain,
                        public_dir=public_dir,
                        voice=args.voice,
                        notes=(f"{args.notes} | RED-TEAM FIX: {repair_feedback}".strip(" |") if repair_feedback else args.notes),
                    )
                elif eng_name == "b2b_agency":
                    client_label = (args.client or "").strip()
                    if not client_label or client_label == "Acme Corp":
                        client_label = (args.title or "").strip() or "Client Company"
                    manifest = run_b2b_agency_engine(
                        client_name=client_label,
                        discovery_notes=(f"{args.notes} | RED-TEAM FIX: {repair_feedback}".strip(" |") if repair_feedback else args.notes),
                        price_usd=args.price,
                        job_dir=job_dir,
                        brain=brain,
                        public_dir=public_dir,
                    )
                elif eng_name == "carousel_funnel":
                    pts = [p.strip() for p in args.notes.split(";") if p.strip()]
                    safe_car_topic = (args.title or "").strip() or pick_fresh_auto_topic(args.theme, brain, "carousel_funnel")
                    manifest = run_carousel_funnel_engine(
                        topic=safe_car_topic,
                        points=pts,
                        job_dir=job_dir,
                        brain=brain,
                        public_dir=public_dir,
                    )
                else:
                    raise ValueError(f"Unsupported engine: {eng_name}")
                return manifest

            def _run_with_red_team_fix(eng_name: str) -> dict[str, Any]:
                prev_items = set(brain.processed_items)
                prev_spend = brain.daily_spend_usd
                prev_ledger_bytes = (
                    brain.ledger_path.read_bytes()
                    if (brain.ledger_path and brain.ledger_path.exists())
                    else None
                )
                cand_manifest = _execute_department(eng_name)
                try:
                    return RedTeamCriticRobot.audit_manifest(cand_manifest, eng_name, public_dir=public_dir)
                except ValueError as rt_exc:
                    if "RED_TEAM_BLOCKED" not in str(rt_exc):
                        raise
                    log.warning(
                        "Red-Team Critic flagged defect in [%s] (%s) -> redirecting back to [%s] for targeted repair (attempt 2/2)...",
                        eng_name, rt_exc, eng_name,
                    )
                    # Full rollback of failed attempt (processed_items, daily spend, & on-disk series ledger state)
                    brain.processed_items.clear()
                    brain.processed_items.update(prev_items)
                    brain.daily_spend_usd = prev_spend
                    if brain.ledger_path:
                        if prev_ledger_bytes is not None:
                            brain.ledger_path.write_bytes(prev_ledger_bytes)
                        else:
                            brain.ledger_path.unlink(missing_ok=True)
                    cleanup_heavy_temp_files(job_dir)
                    repaired_manifest = _execute_department(eng_name, repair_feedback=str(rt_exc))
                    repaired_manifest = RedTeamCriticRobot.audit_manifest(repaired_manifest, eng_name, public_dir=public_dir)
                    rt_block = repaired_manifest.setdefault("red_team_audit", {})
                    rt_block["verdict"] = "FIXED"
                    rt_block["repaired_by_engine"] = True
                    rt_block.setdefault("issues_found", []).append(str(rt_exc))
                    rt_block.setdefault("fixes_applied", []).append(f"Redirected to [{eng_name}] and repaired on attempt 2/2")
                    return repaired_manifest

            try:
                manifest = _run_with_red_team_fix(active_engine)
            except Exception as dept_exc:
                if auto_mode and active_engine != "motion_story":
                    log.warning("Auto-selected department [%s] failed (%s); Executive Board pivoting to [motion_story]...", active_engine, dept_exc)
                    cleanup_heavy_temp_files(job_dir)
                    active_engine = "motion_story"
                    manifest = _run_with_red_team_fix("motion_story")
                else:
                    raise
            atomic_write_json(manifest_path, manifest)
            build_finished = True
            log.info("Build stage [%s] complete -> %s (status=%s)", args.engine, manifest_path, manifest.get("status"))

        if args.stage in {"publish", "full"}:
            platforms = {p.strip().lower() for p in args.platforms.split(",") if p.strip()}
            updated = process_manifest(
                manifest_path=manifest_path,
                brain_dir=brain_dir,
                approve_manifest=args.approve_manifest,
                platforms=platforms,
                max_daily_posts=args.max_daily_posts,
                min_gap_hours=args.min_gap_hours,
                skip_spacing_check=args.skip_spacing_check,
                apply_jitter=args.apply_jitter,
                dry_run=args.dry_run_publish,
                public_dir=public_dir,
            )
            log.info(
                "Connected Social Publisher complete -> status=%s | receipts=%s",
                updated.get("status"),
                updated.get("published_receipts"),
            )
            manifest = updated

        if args.stage in {"publish", "full"}:
            final_manifest = manifest  # in dry-run the on-disk manifest is intentionally untouched
        else:
            final_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
        subj, body = format_manifest_report(final_manifest, stage=args.stage)
        send_gmail_report(subj, body, dry_run=args.dry_run_publish)
        return 0
    except Exception as exc:
        log.error("Master pipeline halted: %s", exc)
        if (build_started and not build_finished) or not manifest_path.exists():
            err_manifest = {"engine": locals().get("active_engine", args.engine)}  # a failed build must not echo the previous run's stale manifest
        else:
            err_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        subj, body = format_manifest_report(err_manifest, stage=args.stage, error_msg=str(exc))
        send_gmail_report(subj, body, dry_run=args.dry_run_publish)
        return 1


if __name__ == "__main__":
    sys.exit(main())
 
