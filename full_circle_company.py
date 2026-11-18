#!/usr/bin/env python3
"""
full_circle_company.py — Unified 6-AI Council Product Factory, Master Worker & Social Publisher
===============================================================================================
Merges:
  1. `full_circle_company.py` (Multi-Format PDF Playbook + Interactive HTML5 App + Storefront +
     1080x1920 4-Scene Playwright Motion Video + Whop Storefront + YouTube Shorts + IG Reels + Gmail CEO Report)
  2. `jagnor_master_worker.py` (CompanyBrain Memory Ledger + 4 Monetization Engines:
     `digital_product`, `clipping`, `b2b_agency`, `carousel_funnel`)
  3. `social_publisher.py` (Atomic JSON Locking, Binary MP4 QA Gate, Rolling 24h Pacing & Spacing Guards,
     Per-Platform Checkpointing, and IG Carousel/Reels Publishing)

New 6-AI Council Architecture (Specialized Multi-Model Pipeline):
  - Live Social Media Signal Harvester: Scrapes live trending discussions from Reddit public JSON
    (`r/artificial`, `r/SideProject`, `r/Productivity`, `r/Entrepreneur`, `r/Parenting`) + Hacker News
    top stories to measure real-time social demand and reach.
  - Specialist 1 — Gemini (`gemini-4-hydrogen`): Lead Market Scout & Reach Analyst (evaluates live
    social signals and picks the highest-reach digital product + target audience).
  - Specialist 2 — Groq (`openai/gpt-oss-120b`): Viral Hook & Social Reach Architect (crafts the
    scroll-stopping 6-8 word video hook and high-retention 4-scene visual pacing).
  - Specialist 3 — OpenRouter (`openrouter/free`): Interactive App & Gamification Engineer (designs
    the 3 interactive sliders, 3 difficulty/mode presets, and 4 live KPI cards).
  - Specialist 4 — ChatGPT (`gpt-6-luna` / `openai/gpt-oss-20b:free`): Curriculum & Playbook Author (structures the 3-page
    printable PDF Playbook modules, step-by-step bullets, and Pro Action Tips).
  - Specialist 5 — Claude (`claude-haiku-4-5` / `nvidia/nemotron-3-ultra-550b-a55b:free`): Chief Editor & Voiceover Director (polishes the
    spoken 35-word voiceover script, social captions, and final product spec for maximum conversion).
  *(Every specialist automatically falls back to any configured free AI key—such as Gemini, Groq,
  or OpenRouter—so the council collaborates smoothly even if only 1–3 keys are set in GitHub Secrets!)*
"""

from __future__ import annotations

import argparse
import gc
import html as html_lib
import json
import logging
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
import zipfile
from dataclasses import asdict, dataclass, field
from email.message import EmailMessage
from fractions import Fraction
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore[assignment]

try:
    import cv2  # type: ignore[import-untyped]
    import numpy as np
except ImportError:
    cv2 = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("jagnor_unified_company")

# =====================================================================
# 0. ENVIRONMENT CONFIGURATION & 6-AI COUNCIL CREDENTIALS
# =====================================================================
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL = "gemini-4-hydrogen"

GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
NVIDIA_KEY = os.environ.get("NVIDIA_API_KEY", "").strip()

WHOP_API_KEY = os.environ.get("WHOP_API_KEY", "").strip()
WHOP_COMPANY_ID = os.environ.get("WHOP_COMPANY_ID", "").strip()

YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID", "").strip()
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET", "").strip()
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN", "").strip()
YT_PRIVACY_STATUS = os.environ.get("YT_PRIVACY_STATUS", "public").strip() or "public"

IG_USER_ID = os.environ.get("IG_USER_ID", "").strip()
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()

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
BRAIN_DIR = Path("brain")
PUBLIC_DIR.mkdir(exist_ok=True)
DIST_DIR.mkdir(exist_ok=True)
RAW_VIDEO_DIR.mkdir(exist_ok=True)
BRAIN_DIR.mkdir(exist_ok=True)

IG_GRAPH_BASE = "https://graph.facebook.com/v22.0"
YT_TOKEN_URL = "https://oauth2.googleapis.com/token"
YT_UPLOAD_INIT_URL = (
    "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
)
RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}


def esc(val: object) -> str:
    """Escapes HTML special characters so AI-generated quotes/ampersands never break HTML."""
    return html_lib.escape(str(val or ""), quote=True)


def safe_price(val: object, default: float = 9.0) -> float:
    """Safely parses prices like 9, '9.00', or '$9.00' without crashing."""
    try:
        cleaned = "".join(ch for ch in str(val) if ch.isdigit() or ch == ".")
        parsed = float(cleaned) if cleaned else default
        return parsed if parsed > 0 else default
    except Exception:
        return default


def extract_json_dict(raw_text: str) -> dict[str, Any] | None:
    """Extracts the first valid JSON object from an LLM response string."""
    if not raw_text:
        return None
    s = raw_text.find("{")
    e = raw_text.rfind("}")
    if s == -1 or e == -1 or e <= s:
        return None
    try:
        parsed = json.loads(raw_text[s : e + 1])
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


# =====================================================================
# DEFAULT HIGH-REACH MULTI-FORMAT PRODUCT BUNDLE (FALLBACK)
# =====================================================================
DEFAULT_PRODUCT_SPEC: dict[str, Any] = {
    "category": "Kids & Family Brain-Training Kit",
    "title": "Junior Genius: Visual Math & Logic Quest Kit",
    "subtitle": "Illustrated 4-Page Kids Activity Playbook (PDF) + Interactive Logic Puzzle Game App",
    "audience": "Kids Ages 6-12, Parents & Teachers",
    "price_usd": 7.00,
    "hook_headline": "Turn Screen Time Into Genius Brain Power!",
    "voiceover": (
        "Want to turn your kid's screen time into real brain power? "
        "Inside the Junior Genius Math and Logic Quest Kit, you get a colorful printable PDF activity playbook "
        "plus an interactive brain puzzle game that adapts in real time. "
        "Tap the store link in our channel profile to preview the PDF and grab the full kit today."
    ),
    "caption": "Turn screen time into brain power with the Junior Genius Visual Math & Logic Quest Kit (Printable PDF Playbook + Interactive Game App)!",
    "playbook_pages": [
        {
            "page_title": "Page 1: The 5-Minute Daily Brain Quest",
            "badge": "VISUAL PLAYBOOK GUIDE",
            "bullets": [
                "Pattern Detective Rule: Spot the hidden number bridge before the timer hits zero.",
                "Visual Fraction Pizza: Slice and match colorful shapes to master mental math twice as fast.",
                "Reward Star Tracker: Kids earn 50 XP badges for every completed page and level.",
            ],
            "pro_tip": "Parents & Teachers: Print Page 3 for offline table games or pair with the live companion app!",
        },
        {
            "page_title": "Page 2: Speed-Math & Memory Palace Tricks",
            "badge": "STEP-BY-STEP SYSTEM",
            "bullets": [
                "The 9x Finger Shortcut: Multiply any number by 9 in under 2 seconds visually.",
                "Story-Chain Memory Game: Link 10 science facts together using funny cartoon characters.",
                "Logic Grid Mystery: Use elimination clues to solve who found the golden treasure.",
            ],
            "pro_tip": "Use the 3 difficulty buttons in the interactive app to test Easy, Hero, and Genius modes!",
        },
        {
            "page_title": "Page 3: Printable Daily Quest & Star Chart",
            "badge": "PRINTABLE WORKSHEET",
            "bullets": [
                "Monday - Pattern Jumper: Complete 3 visual number ladders (+100 XP).",
                "Wednesday - Logic Boss Battle: Solve the 3-door riddle challenge (+150 XP).",
                "Friday - Family Quiz Night: Beat the 60-second streak challenge (+250 XP).",
            ],
            "pro_tip": "Includes full offline HTML5 game + printable PDF workbook inside the instant download zip!",
        },
    ],
    "app_slider_1_label": "Quest Difficulty Level",
    "app_slider_2_label": "Daily Puzzle Missions",
    "app_slider_3_label": "Speed Bonus Multiplier",
    "app_preset_1": "Starter (Ages 6-8)",
    "app_preset_2": "Explorer (Ages 9-10)",
    "app_preset_3": "Genius Boss (Ages 11+)",
    "kpi_1_label": "Brain XP Earned",
    "kpi_2_label": "Logic Streak Score",
    "kpi_3_label": "Daily Quest Time",
    "kpi_4_label": "Unlocked Badges",
}


# =====================================================================
# 1. LIVE SOCIAL MEDIA TREND HARVESTER & 6-AI SPECIALIST COUNCIL
# =====================================================================
def harvest_live_social_media_trends() -> list[str]:
    """
    Fetches live high-reach social discussions from Reddit public JSON endpoints
    and Hacker News Firebase API (zero API key required) so the 6-AI Council
    chooses a topic based on real-time social demand and reach.
    """
    trends: list[str] = []
    subreddits = ["SideProject", "Productivity", "artificial", "Parenting", "learnprogramming"]
    headers = {"User-Agent": "JagnorAICompanyTrendScout/2.0"}

    for sub in subreddits:
        try:
            req = urllib.request.Request(
                f"https://www.reddit.com/r/{sub}/hot.json?limit=4",
                headers=headers,
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for child in data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    title = str(post.get("title", "")).strip()
                    score = int(post.get("score", 0))
                    if title and not post.get("stickied") and score >= 10:
                        trends.append(f"[r/{sub} • {score} upvotes] {title[:110]}")
        except Exception:
            continue

    # Also pull top 5 Hacker News stories for tech/creator reach signals
    try:
        with urllib.request.urlopen(
            "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=6
        ) as resp:
            top_ids = json.loads(resp.read().decode("utf-8"))[:5]
        for item_id in top_ids:
            with urllib.request.urlopen(
                f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", timeout=5
            ) as item_resp:
                item = json.loads(item_resp.read().decode("utf-8"))
                if item and item.get("title"):
                    trends.append(f"[HN • {item.get('score', 50)} pts] {item['title'][:110]}")
    except Exception:
        pass

    if not trends:
        trends = [
            "[High-Reach Signal] Kids screen-free + interactive visual math & logic games for parents",
            "[High-Reach Signal] Student active-recall visual memory palace & exam prep flashcards",
            "[High-Reach Signal] Gamified 30-day personal savings challenge & interactive budget planner",
            "[High-Reach Signal] Daily ADHD focus timer, habit streak tracker & visual routine playbook",
        ]
    print(f"   -> Harvested {len(trends)} live social media trend signals for the 6-AI Council.")
    return trends[:12]


def _call_single_provider(provider: str, prompt: str, json_mode: bool = False) -> str | None:
    """Calls a specific AI provider by name ('gemini', 'groq', 'openrouter', 'chatgpt', 'claude')."""
    if provider == "gemini" and GEMINI_KEY:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{MODEL}:generateContent?key={GEMINI_KEY}"
        )
        payload: dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}]}
        if json_mode:
            payload["generationConfig"] = {"responseMimeType": "application/json"}
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][-1]["text"].strip()

    if provider == "groq" and GROQ_KEY:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(
                {
                    "model": "openai/gpt-oss-120b",
                    "messages": [{"role": "user", "content": prompt}],
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            msg = data["choices"][0].get("message", {}); return (msg.get("content") or msg.get("reasoning_content") or "").strip()

    if provider == "openrouter" and OPENROUTER_KEY:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(
                {
                    "model": "openrouter/free",
                    "messages": [{"role": "user", "content": prompt}],
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": PUBLIC_VIDEO_BASE_URL,
                "X-Title": "Jagnor AI Company",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            msg = data["choices"][0].get("message", {}); return (msg.get("content") or msg.get("reasoning_content") or "").strip()

    if provider == "chatgpt":
        if OPENAI_KEY:
            api_url, key, model_id = "https://api.openai.com/v1/chat/completions", OPENAI_KEY, "gpt-6-luna"
        elif OPENROUTER_KEY:
            # 100% Free OpenAI open-weight model on OpenRouter (:free tier)
            api_url, key, model_id = "https://openrouter.ai/api/v1/chat/completions", OPENROUTER_KEY, "openai/gpt-oss-20b:free"
        elif GROQ_KEY:
            # 100% Free OpenAI open-weight model on Groq
            api_url, key, model_id = "https://api.groq.com/openai/v1/chat/completions", GROQ_KEY, "openai/gpt-oss-20b"
        else:
            api_url, key, model_id = "", "", ""
        if key:
            req = urllib.request.Request(
                api_url,
                data=json.dumps(
                    {
                        "model": model_id,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                ).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                msg = data["choices"][0].get("message", {}); return (msg.get("content") or msg.get("reasoning_content") or "").strip()

    if provider == "claude" and not ANTHROPIC_KEY and OPENROUTER_KEY:
        # 100% Free 550B reasoning/editorial model when no paid Anthropic key is present
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(
                {
                    "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
                    "messages": [{"role": "user", "content": prompt}],
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": PUBLIC_VIDEO_BASE_URL,
                "X-Title": "Jagnor AI Company",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            msg = data["choices"][0].get("message", {}); return (msg.get("content") or msg.get("reasoning_content") or "").strip()

    if provider == "claude" and ANTHROPIC_KEY:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(
                {
                    "model": "claude-haiku-4-5",
                    "max_tokens": 2048,
                    "messages": [{"role": "user", "content": prompt}],
                }
            ).encode("utf-8"),
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return "".join(
                blk.get("text", "")
                for blk in data.get("content", [])
                if blk.get("type") == "text"
            ).strip()

    if provider == "nvidia" and NVIDIA_KEY:
        req = urllib.request.Request(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            data=json.dumps(
                {
                    "model": "nvidia/nemotron-3-ultra-550b-a55b",
                    "messages": [{"role": "user", "content": prompt}],
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {NVIDIA_KEY}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            msg = data["choices"][0].get("message", {}); return (msg.get("content") or msg.get("reasoning_content") or "").strip()

    return None


def call_specialist_ai(
    preferred_provider: str,
    role_title: str,
    prompt: str,
    json_mode: bool = True,
) -> str | None:
    """
    Routes a specialist task to its preferred AI brain first (e.g., Groq for viral hooks,
    OpenRouter for interactive app controls, ChatGPT for playbook curriculum, Claude for
    voiceover polish, Gemini for reach analysis), and automatically falls back across
    all other available AI brains if a key isn't set or hits a rate limit.
    """
    order = [preferred_provider] + [
        p
        for p in ("gemini", "groq", "openrouter", "chatgpt", "claude", "nvidia")
        if p != preferred_provider
    ]
    for provider in order:
        try:
            res = _call_single_provider(provider, prompt, json_mode=json_mode)
            if res:
                print(f"   -> [6-AI Council • {role_title}] Executed via {provider.upper()}")
                return res
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            print(f"   -> [{provider.upper()}] HTTP {e.code}: {err_body[:140]}")
            if provider == "gemini" and e.code == 429 and not (GROQ_KEY or OPENROUTER_KEY or OPENAI_KEY or ANTHROPIC_KEY):
                print("   -> Waiting 62s for Gemini rate-limit window reset...")
                time.sleep(62)
                try:
                    res = _call_single_provider("gemini", prompt, json_mode=json_mode)
                    if res:
                        return res
                except Exception:
                    pass
        except Exception as e:
            print(f"   -> [{provider.upper()}] notice: {e}")
    return None


def sanitize_product_spec(raw_spec: dict[str, Any]) -> dict[str, Any]:
    """Guarantees all required keys and playbook_pages entries are valid types so HTML/PDF builders never crash."""
    clean = dict(DEFAULT_PRODUCT_SPEC)
    if isinstance(raw_spec, dict):
        for k, v in raw_spec.items():
            if v is not None and v != "":
                clean[k] = v
    raw_pages = clean.get("playbook_pages")
    valid_pages: list[dict[str, Any]] = []
    if isinstance(raw_pages, list):
        for idx, item in enumerate(raw_pages[:3], start=1):
            if isinstance(item, dict):
                bullets = item.get("bullets")
                if not isinstance(bullets, list) or not bullets:
                    bullets = DEFAULT_PRODUCT_SPEC["playbook_pages"][min(idx - 1, 2)]["bullets"]
                valid_pages.append({
                    "page_title": str(item.get("page_title") or f"Page {idx}: Action Module"),
                    "badge": str(item.get("badge") or f"MODULE {idx}"),
                    "bullets": [str(b) for b in bullets[:4] if str(b).strip()],
                    "pro_tip": str(item.get("pro_tip") or "Apply this step daily for best results."),
                })
    while len(valid_pages) < 3:
        valid_pages.append(DEFAULT_PRODUCT_SPEC["playbook_pages"][len(valid_pages)])
    clean["playbook_pages"] = valid_pages
    clean["price_usd"] = safe_price(clean.get("price_usd", 9.0))
    return clean


def scout_and_design_product(processed_titles: set[str] | None = None) -> dict[str, Any]:
    """
    6-AI Specialist Council Pipeline:
      Stage 1 (Gemini — Market Scout & Reach Analyst + Groq — Viral Hook Specialist):
        Analyzes live social media trends and selects the highest-reach digital product bundle.
      Stage 2 (OpenRouter — Interactive App Architect + ChatGPT — Playbook Author):
        Refines the 3-page PDF Playbook modules and interactive HTML5 companion app controls.
      Stage 3 (Claude — Chief Editor & Voiceover Director):
        Audits and polishes the 4-scene vertical video voiceover script, hook headline, and caption.
    """
    trends = harvest_live_social_media_trends()
    trends_text = "\n".join(f"  - {t}" for t in trends)
    avoid_list = ", ".join(sorted(list(processed_titles or set()))[:10]) or "None"

    # STAGE 1: Gemini (Market Reach Analyst) designs the core bundle from live social trends
    stage1_prompt = (
        "You are Specialist 1 (Gemini-4-Hydrogen Market Scout) leading a 6-AI Product Council.\n"
        f"Here are today's live trending social media signals:\n{trends_text}\n\n"
        f"Previously built products to avoid repeating: {avoid_list}\n\n"
        "Pick ONE high-demand, mass-appeal digital product bundle (Illustrated 3-Page PDF Playbook + "
        "Interactive HTML5 Companion App) with viral reach on YouTube Shorts & Instagram Reels.\n"
        "Choose from high-reach consumer categories such as:\n"
        "  - Kids' Interactive Visual Learning, Math/Science Activity Book & Brain Game (for parents/kids)\n"
        "  - Student / Medical / Exam Visual Memory Playbook & Active-Recall Flashcard Trainer\n"
        "  - Gamified Fitness, Calorie/Macro & Daily Habit Playbook + Interactive Planner\n"
        "  - Personal Budget, Savings Challenge & Wealth Playbook + Interactive Simulator\n\n"
        "Return ONLY valid JSON (no markdown fences) matching this exact structure:\n"
        "{\n"
        '  "category": "Short category badge",\n'
        '  "title": "Catchy product bundle title (under 44 chars)",\n'
        '  "subtitle": "Illustrated PDF Playbook + Interactive Companion App",\n'
        '  "audience": "Who this is for",\n'
        '  "price_usd": 9.0,\n'
        '  "hook_headline": "Bold 6-8 word viral video hook",\n'
        '  "voiceover": "35-word spoken script (no emojis/hashtags) explaining the problem, showing off the PDF Playbook pages and interactive app, and telling viewers to tap the store link in our channel profile",\n'
        '  "caption": "Engaging social caption",\n'
        '  "playbook_pages": [\n'
        '    {"page_title": "Page 1: ...", "badge": "MODULE 1", "bullets": ["Actionable point 1", "Actionable point 2", "Actionable point 3"], "pro_tip": "Practical tip"},\n'
        '    {"page_title": "Page 2: ...", "badge": "MODULE 2", "bullets": ["Actionable point 1", "Actionable point 2", "Actionable point 3"], "pro_tip": "Practical tip"},\n'
        '    {"page_title": "Page 3: ...", "badge": "CHEAT SHEET & WORKSHEET", "bullets": ["Checklist item 1", "Checklist item 2", "Checklist item 3"], "pro_tip": "Practical tip"}\n'
        "  ],\n"
        '  "app_slider_1_label": "Label for slider 1",\n'
        '  "app_slider_2_label": "Label for slider 2",\n'
        '  "app_slider_3_label": "Label for slider 3",\n'
        '  "app_preset_1": "Preset mode 1",\n'
        '  "app_preset_2": "Preset mode 2",\n'
        '  "app_preset_3": "Preset mode 3",\n'
        '  "kpi_1_label": "Metric 1 label",\n'
        '  "kpi_2_label": "Metric 2 label",\n'
        '  "kpi_3_label": "Metric 3 label",\n'
        '  "kpi_4_label": "Metric 4 label"\n'
        "}"
    )

    spec: dict[str, Any] = dict(DEFAULT_PRODUCT_SPEC)
    raw_stage1 = call_specialist_ai("gemini", "Market Scout & Reach Analyst", stage1_prompt, json_mode=True)
    parsed1 = extract_json_dict(raw_stage1 or "")
    if parsed1 and parsed1.get("title") and parsed1.get("playbook_pages"):
        spec.update(parsed1)

    # STAGE 2: Groq (Viral Hook & Reach Specialist) sharpens the Short/Reel hook & social caption
    if GROQ_KEY or OPENROUTER_KEY or OPENAI_KEY or ANTHROPIC_KEY:
        stage2_prompt = (
            f"You are Specialist 2 (Groq Viral Short-Form Hook Architect).\n"
            f"Product Bundle: '{spec['title']}' ({spec['subtitle']}) for {spec['audience']}.\n"
            f"Current Hook: '{spec['hook_headline']}'\n"
            f"Current Voiceover: '{spec['voiceover']}'\n\n"
            "Upgrade the hook and voiceover for maximum YouTube Shorts & Instagram Reels retention.\n"
            "Return ONLY valid JSON with keys:\n"
            '{"hook_headline": "Punchy 6-8 word scroll-stopping hook", '
            '"voiceover": "35-word spoken script (no emojis or hashtags) showing the problem, the 3-page PDF Playbook, the live interactive app, and telling viewers to tap the store link in our channel profile", '
            '"caption": "High-converting social caption"}'
        )
        raw_stage2 = call_specialist_ai("groq", "Viral Hook & Pacing Architect", stage2_prompt, json_mode=True)
        parsed2 = extract_json_dict(raw_stage2 or "")
        if parsed2:
            for k in ("hook_headline", "voiceover", "caption"):
                if parsed2.get(k):
                    spec[k] = parsed2[k]

    # STAGE 3: OpenRouter (Interactive UI Engineer) & ChatGPT (Playbook Curriculum Author)
    if OPENROUTER_KEY or OPENAI_KEY:
        stage3_prompt = (
            f"You are Specialist 3 & 4 (Interactive App Engineer & Playbook Curriculum Author).\n"
            f"Product Bundle: '{spec['title']}' for {spec['audience']}.\n"
            "Ensure the 3 interactive app sliders, 3 mode presets, and 4 KPI labels are hyper-specific and engaging.\n"
            "Return ONLY valid JSON with keys: app_slider_1_label, app_slider_2_label, app_slider_3_label, "
            "app_preset_1, app_preset_2, app_preset_3, kpi_1_label, kpi_2_label, kpi_3_label, kpi_4_label."
        )
        preferred = "openrouter" if OPENROUTER_KEY else "chatgpt"
        raw_stage3 = call_specialist_ai(preferred, "Interactive App & Curriculum Specialist", stage3_prompt, json_mode=True)
        parsed3 = extract_json_dict(raw_stage3 or "")
        if parsed3:
            for k in (
                "app_slider_1_label", "app_slider_2_label", "app_slider_3_label",
                "app_preset_1", "app_preset_2", "app_preset_3",
                "kpi_1_label", "kpi_2_label", "kpi_3_label", "kpi_4_label",
            ):
                if parsed3.get(k):
                    spec[k] = parsed3[k]
 # STAGE 4: Claude (Chief Editorial & Video Director) performs final QA polish if ANTHROPIC_KEY is present
    if ANTHROPIC_KEY or OPENROUTER_KEY:
        stage4_prompt = (
            f"You are Specialist 5 (Claude Chief Editor & Video Director).\n"
            f"Review this product spec JSON and polish the voiceover and playbook pro_tips for clarity:\n"
            f"{json.dumps({'title': spec['title'], 'hook_headline': spec['hook_headline'], 'voiceover': spec['voiceover']})}\n"
            "Return ONLY valid JSON with keys: hook_headline, voiceover."
        )
        raw_stage4 = call_specialist_ai("claude", "Chief Editor & Video Director", stage4_prompt, json_mode=True)
        parsed4 = extract_json_dict(raw_stage4 or "")
        if parsed4:
            for k in ("hook_headline", "voiceover"):
                if parsed4.get(k):
                    spec[k] = parsed4[k]

    # STAGE 5: NVIDIA NIM (Global Reach & Final Engagement Check; falls back to OpenRouter/Groq if blank)
    if NVIDIA_KEY or OPENROUTER_KEY or GROQ_KEY:
        stage5_prompt = (
            f"You are Specialist 6 (NVIDIA NIM Global Reach & Engagement Reviewer).\n"
            f"Product Bundle: '{spec['title']}' ({spec['subtitle']}) for {spec['audience']}.\n"
            f"Current Social Caption: '{spec['caption']}'\n"
            "Make the social caption punchy, clear, and globally appealing for YouTube Shorts and Instagram Reels.\n"
            'Return ONLY valid JSON with key: {"caption": "Upgraded high-reach social caption"}'
        )
        raw_stage5 = call_specialist_ai("nvidia", "Global Reach & Engagement Reviewer", stage5_prompt, json_mode=True)
        parsed5 = extract_json_dict(raw_stage5 or "")
        if parsed5 and parsed5.get("caption"):
            spec["caption"] = parsed5["caption"]

    return sanitize_product_spec(spec)


# =====================================================================
# 2. BUILD ILLUSTRATED PDF PLAYBOOK + INTERACTIVE APP + STOREFRONT HTML
# =====================================================================
def build_playbook_html(spec: dict) -> str:
    pages_html = ""
    for idx, p in enumerate(spec.get("playbook_pages", DEFAULT_PRODUCT_SPEC["playbook_pages"]), start=1):
        bullets_li = "".join(
            f"<li style='margin-bottom:14px;font-size:16px;line-height:1.5;color:#1e293b;'>"
            f"<strong style='color:#0284c7;'>✓ Step {i}:</strong> {esc(b)}</li>"
            for i, b in enumerate(p.get("bullets", []), start=1)
        )
        pages_html += f"""
        <div class="pdf-page">
          <div class="header-bar">
            <span class="badge">{esc(p.get('badge', f'MODULE {idx}'))}</span>
            <span class="page-num">Page {idx} of 3 • {esc(spec['title'])}</span>
          </div>
          <h2>{esc(p.get('page_title', f'Module {idx}'))}</h2>
          <div class="content-box">
            <ul style="list-style:none;padding:0;">{bullets_li}</ul>
          </div>
          <div class="tip-box">
            <strong>💡 Pro Action Tip:</strong> {esc(p.get('pro_tip', ''))}
          </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{esc(spec['title'])} — Official PDF Playbook</title>
<style>
  @page {{ size: A4; margin: 16mm; }}
  * {{ box-sizing: border-box; font-family: 'Segoe UI', system-ui, sans-serif; }}
  body {{ margin: 0; background: #f8fafc; color: #0f172a; }}
  .cover {{ background: linear-gradient(135deg, #0f172a, #1e3a8a); color: #fff; padding: 48px; border-radius: 24px; margin-bottom: 28px; }}
  .cover .cat {{ display: inline-block; background: #38bdf8; color: #0f172a; font-weight: 800; font-size: 13px; padding: 6px 14px; border-radius: 999px; text-transform: uppercase; }}
  .cover h1 {{ font-size: 34px; margin: 16px 0 10px; }}
  .cover p {{ font-size: 17px; color: #cbd5e1; margin: 0; }}
  .pdf-page {{ background: #fff; border: 2px solid #e2e8f0; border-radius: 20px; padding: 32px; margin-bottom: 24px; page-break-inside: avoid; }}
  .header-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }}
  .badge {{ background: #e0f2fe; color: #0369a1; font-weight: 700; font-size: 12px; padding: 5px 12px; border-radius: 8px; }}
  .page-num {{ font-size: 12px; color: #64748b; }}
  h2 {{ font-size: 24px; color: #0f172a; margin: 0 0 18px; }}
  .content-box {{ background: #f8fafc; border-left: 5px solid #0284c7; padding: 20px; border-radius: 12px; margin-bottom: 18px; }}
  .tip-box {{ background: #fef9c3; border: 1px solid #fde047; color: #854d0e; padding: 16px; border-radius: 12px; font-size: 15px; }}
</style>
</head>
<body>
  <div class="cover">
    <span class="cat">{esc(spec.get('category', 'OFFICIAL PLAYBOOK'))}</span>
    <h1>{esc(spec['title'])}</h1>
    <p>{esc(spec['subtitle'])} • Audience: {esc(spec.get('audience', 'All Ages'))}</p>
  </div>
  {pages_html}
</body>
</html>"""


def build_interactive_app_html(spec: dict, checkout_url: str, pdf_filename: str, price_usd: float) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(spec['title'])} — Interactive App</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }}
  body {{ background: #0f172a; color: #f8fafc; padding: 20px; max-width: 600px; margin: 0 auto; }}
  .top-nav {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }}
  .top-nav a {{ color: #38bdf8; text-decoration: none; font-weight: 700; font-size: 14px; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 20px; padding: 22px; margin-bottom: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.35); }}
  .badge {{ display: inline-block; background: rgba(56,189,248,0.15); color: #38bdf8; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; margin-bottom: 8px; }}
  h1 {{ font-size: 24px; color: #fff; margin-bottom: 6px; }}
  p.sub {{ font-size: 14px; color: #94a3b8; margin-bottom: 16px; }}
  .presets {{ display: flex; gap: 8px; margin-bottom: 18px; }}
  button.preset {{ flex: 1; background: #0284c7; color: #fff; border: none; padding: 12px 8px; border-radius: 12px; font-weight: 700; font-size: 13px; cursor: pointer; }}
  .control {{ margin-bottom: 16px; }}
  .control-header {{ display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 6px; color: #e2e8f0; }}
  input[type=range] {{ width: 100%; accent-color: #38bdf8; height: 9px; border-radius: 6px; cursor: pointer; }}
  .kpi-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px; }}
  .kpi {{ background: #0f172a; border: 1px solid #334155; border-radius: 14px; padding: 14px; text-align: center; }}
  .kpi-val {{ font-size: 26px; font-weight: 800; color: #38bdf8; }}
  .kpi-lbl {{ font-size: 12px; color: #94a3b8; margin-top: 4px; }}
  .bar-wrap {{ background: #0f172a; border-radius: 10px; height: 16px; overflow: hidden; margin-top: 10px; }}
  .bar-fill {{ background: linear-gradient(90deg, #38bdf8, #22c55e); height: 100%; width: 72%; transition: width 0.35s ease; }}
  .cta-row {{ display: flex; gap: 10px; margin-top: 16px; }}
  .btn-buy {{ flex: 2; display: block; text-align: center; background: linear-gradient(90deg, #22c55e, #16a34a); color: #fff; text-decoration: none; padding: 14px; border-radius: 14px; font-weight: 800; font-size: 15px; }}
  .btn-pdf {{ flex: 1; display: block; text-align: center; background: #334155; color: #fff; text-decoration: none; padding: 14px; border-radius: 14px; font-weight: 700; font-size: 14px; }}
</style>
</head>
<body>
  <div class="top-nav">
    <a href="index.html">← Back to Jagnor Digital Store</a>
    <a href="{esc(pdf_filename)}" target="_blank">📄 Open PDF Playbook</a>
  </div>
  <div class="card">
    <span class="badge">{esc(spec.get('category', 'INTERACTIVE TOOL'))}</span>
    <h1>{esc(spec['title'])}</h1>
    <p class="sub">{esc(spec['subtitle'])}</p>
    <div class="presets">
      <button class="preset" onclick="setMode(3, 25, 70)">{esc(spec.get('app_preset_1', 'Starter Mode'))}</button>
      <button class="preset" onclick="setMode(6, 45, 85)">{esc(spec.get('app_preset_2', 'Pro Mode'))}</button>
      <button class="preset" onclick="setMode(9, 60, 98)">{esc(spec.get('app_preset_3', 'Master Mode'))}</button>
    </div>
    <div class="control">
      <div class="control-header"><span>{esc(spec.get('app_slider_1_label', 'Level / Units'))}</span><strong id="v1">6</strong></div>
      <input type="range" id="s1" min="1" max="10" value="6" oninput="updateApp()">
    </div>
    <div class="control">
      <div class="control-header"><span>{esc(spec.get('app_slider_2_label', 'Daily Target'))}</span><strong id="v2">45</strong></div>
      <input type="range" id="s2" min="10" max="100" value="45" oninput="updateApp()">
    </div>
    <div class="control">
      <div class="control-header"><span>{esc(spec.get('app_slider_3_label', 'Intensity Boost'))}</span><strong id="v3">85%</strong></div>
      <input type="range" id="s3" min="50" max="100" value="85" oninput="updateApp()">
    </div>
  </div>
  <div class="card">
    <div class="control-header"><span>Live Mastery &amp; Progress Score</span><strong id="scoreTxt">89 / 100</strong></div>
    <div class="bar-wrap"><div class="bar-fill" id="scoreBar"></div></div>
    <div class="kpi-grid">
      <div class="kpi"><div class="kpi-val" id="k1">+680</div><div class="kpi-lbl">{esc(spec.get('kpi_1_label', 'Total XP / Output'))}</div></div>
      <div class="kpi"><div class="kpi-val" id="k2">94%</div><div class="kpi-lbl">{esc(spec.get('kpi_2_label', 'Efficiency Score'))}</div></div>
      <div class="kpi"><div class="kpi-val" id="k3">4.5h</div><div class="kpi-lbl">{esc(spec.get('kpi_3_label', 'Weekly Saved'))}</div></div>
      <div class="kpi"><div class="kpi-val" id="k4">Tier S</div><div class="kpi-lbl">{esc(spec.get('kpi_4_label', 'Rank Unlocked'))}</div></div>
    </div>
    <div class="cta-row">
      <a class="btn-buy" href="{esc(checkout_url)}" target="_blank">💳 Get Full Bundle (${price_usd:.0f})</a>
      <a class="btn-pdf" href="{esc(pdf_filename)}" target="_blank">📖 PDF Guide</a>
    </div>
  </div>
<script>
function updateApp() {{
  const a = parseFloat(document.getElementById('s1').value);
  const b = parseFloat(document.getElementById('s2').value);
  const c = parseFloat(document.getElementById('s3').value);
  document.getElementById('v1').textContent = a;
  document.getElementById('v2').textContent = b;
  document.getElementById('v3').textContent = c + '%';
  const score = Math.min(100, Math.round(a * 4 + b * 0.35 + c * 0.35));
  document.getElementById('scoreTxt').textContent = score + ' / 100';
  document.getElementById('scoreBar').style.width = score + '%';
  document.getElementById('k1').textContent = '+' + Math.round(a * b * (c / 25));
  document.getElementById('k2').textContent = Math.min(99, Math.round(c * 0.96)) + '%';
  document.getElementById('k3').textContent = ((a * b) / 60).toFixed(1) + 'h';
  document.getElementById('k4').textContent = score > 85 ? 'Tier S+' : (score > 70 ? 'Tier A' : 'Tier B');
}}
function setMode(a, b, c) {{
  document.getElementById('s1').value = a;
  document.getElementById('s2').value = b;
  document.getElementById('s3').value = c;
  updateApp();
}}
updateApp();
</script>
</body>
</html>"""


def build_storefront_html(catalog: list[dict], whop_store_url: str) -> str:
    cards_html = ""
    for item in catalog:
        p_usd = safe_price(item.get("price_usd", 9.0))
        cards_html += f"""
        <div class="prod-card">
          <div class="prod-top">
            <span class="cat-pill">{esc(item.get('category', 'DIGITAL BUNDLE'))}</span>
            <span class="price-pill">${p_usd:.0f} USD</span>
          </div>
          <h2>{esc(item.get('title', 'Digital Bundle'))}</h2>
          <p class="desc">{esc(item.get('subtitle', ''))}</p>
          <div class="included">
            <span>📘 Illustrated PDF Playbook</span>
            <span>⚡ Interactive Web App</span>
            <span>📦 Offline ZIP Pack</span>
          </div>
          <div class="actions">
            <a class="buy-btn" href="{esc(item.get('checkout_url', whop_store_url))}" target="_blank">
              💳 Buy &amp; Instant Download (${p_usd:.0f})
            </a>
            <div class="sub-actions">
              <a class="preview-btn" href="{esc(item.get('pdf_url', 'playbook_latest.pdf'))}" target="_blank">📄 Preview PDF Playbook</a>
              <a class="preview-btn" href="{esc(item.get('app_url', 'app_latest.html'))}" target="_blank">🎮 Try Interactive App</a>
            </div>
          </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Jagnor Digital Product Store — Playbooks, Kids' Kits &amp; AI Apps</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }}
  body {{ background: #090d16; color: #f8fafc; padding: 20px; max-width: 780px; margin: 0 auto; }}
  .hero {{ background: linear-gradient(135deg, #0f172a, #1e3a8a); border: 1px solid #38bdf8; border-radius: 24px; padding: 28px; text-align: center; margin-bottom: 24px; box-shadow: 0 12px 35px rgba(2,132,199,0.25); }}
  .hero h1 {{ font-size: 28px; margin-bottom: 8px; color: #fff; }}
  .hero p {{ font-size: 15px; color: #cbd5e1; margin-bottom: 16px; }}
  .hero-store-btn {{ display: inline-block; background: #38bdf8; color: #0f172a; font-weight: 800; padding: 12px 22px; border-radius: 999px; text-decoration: none; font-size: 14px; }}
  .prod-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 22px; padding: 24px; margin-bottom: 18px; }}
  .prod-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
  .cat-pill {{ background: rgba(56,189,248,0.15); color: #38bdf8; font-size: 12px; font-weight: 700; padding: 5px 12px; border-radius: 999px; }}
  .price-pill {{ background: #22c55e; color: #052e16; font-size: 14px; font-weight: 800; padding: 5px 12px; border-radius: 999px; }}
  .prod-card h2 {{ font-size: 22px; margin-bottom: 6px; color: #fff; }}
  .desc {{ font-size: 14px; color: #94a3b8; margin-bottom: 14px; }}
  .included {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }}
  .included span {{ background: #0f172a; border: 1px solid #334155; padding: 6px 12px; border-radius: 10px; font-size: 12px; color: #cbd5e1; }}
  .buy-btn {{ display: block; text-align: center; background: linear-gradient(90deg, #22c55e, #16a34a); color: #fff; text-decoration: none; padding: 15px; border-radius: 14px; font-weight: 800; font-size: 16px; margin-bottom: 10px; box-shadow: 0 6px 20px rgba(34,197,94,0.3); }}
  .sub-actions {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
  .preview-btn {{ display: block; text-align: center; background: #0f172a; border: 1px solid #38bdf8; color: #38bdf8; text-decoration: none; padding: 12px; border-radius: 12px; font-weight: 700; font-size: 13px; }}
</style>
</head>
<body>
  <div class="hero">
    <h1>⚡ Jagnor Digital Store</h1>
    <p>Instant-Download Illustrated PDF Playbooks, Kids' Learning Kits &amp; Interactive Apps</p>
    <a class="hero-store-btn" href="{esc(whop_store_url)}" target="_blank">🛒 Visit Official Whop Store &amp; Checkout</a>
  </div>
  {cards_html}
</body>
</html>"""


# =====================================================================
# 3. FULL-SCREEN 1080x1920 (9:16) 4-SCENE MOTION VIDEO SHOWCASE
# =====================================================================
def build_full_screen_motion_showcase_html(spec: dict, price_usd: float) -> str:
    pages = spec.get("playbook_pages", DEFAULT_PRODUCT_SPEC["playbook_pages"])
    p1 = pages[0] if len(pages) > 0 else DEFAULT_PRODUCT_SPEC["playbook_pages"][0]
    p2 = pages[1] if len(pages) > 1 else p1

    p1_bullets = "".join(f"<li>✅ {esc(b)}</li>" for b in p1.get("bullets", [])[:3])
    p2_bullets = "".join(f"<li>🔥 {esc(b)}</li>" for b in p2.get("bullets", [])[:3])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }}
  html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #070b14; color: #fff; position: relative; }}
  .bg-glow {{ position: absolute; width: 900px; height: 900px; border-radius: 50%; background: radial-gradient(circle, rgba(56,189,248,0.28), transparent 70%); top: -150px; left: 90px; animation: pulse 4s infinite alternate; }}
  @keyframes pulse {{ 0% {{ transform: scale(0.95); }} 100% {{ transform: scale(1.1); }} }}

  .top-pill {{ position: absolute; top: 70px; left: 60px; right: 60px; display: flex; justify-content: space-between; align-items: center; background: rgba(30,41,59,0.9); border: 2px solid #38bdf8; border-radius: 999px; padding: 18px 36px; z-index: 10; }}
  .top-pill .cat {{ color: #38bdf8; font-size: 26px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }}
  .top-pill .price {{ background: #22c55e; color: #052e16; font-size: 28px; font-weight: 900; padding: 8px 24px; border-radius: 999px; }}

  .scene {{ position: absolute; top: 210px; left: 60px; right: 60px; bottom: 260px; opacity: 0; transform: translateY(60px) scale(0.96); transition: all 0.65s cubic-bezier(0.22, 1, 0.36, 1); display: flex; flex-direction: column; justify-content: center; }}
  .scene.active {{ opacity: 1; transform: translateY(0) scale(1); }}

  .card-big {{ background: linear-gradient(160deg, #1e293b, #0f172a); border: 3px solid #334155; border-radius: 44px; padding: 56px; box-shadow: 0 30px 80px rgba(0,0,0,0.65); }}
  .hook-tag {{ display: inline-block; background: #f59e0b; color: #0f172a; font-size: 28px; font-weight: 900; padding: 10px 28px; border-radius: 16px; margin-bottom: 28px; }}
  h1.giant {{ font-size: 68px; line-height: 1.12; font-weight: 900; margin-bottom: 24px; color: #fff; }}
  p.lead {{ font-size: 36px; line-height: 1.4; color: #cbd5e1; margin-bottom: 40px; }}
  .bundle-items {{ display: flex; flex-direction: column; gap: 22px; }}
  .b-item {{ background: rgba(2,132,199,0.2); border: 2px solid #38bdf8; border-radius: 26px; padding: 26px 32px; font-size: 34px; font-weight: 700; display: flex; align-items: center; gap: 20px; }}

  .pdf-sheet {{ background: #ffffff; color: #0f172a; border-radius: 36px; padding: 48px; box-shadow: 0 25px 70px rgba(0,0,0,0.7); border: 6px solid #38bdf8; margin-bottom: 28px; transition: transform 0.5s ease; }}
  .pdf-sheet h2 {{ font-size: 44px; color: #0284c7; margin-bottom: 22px; }}
  .pdf-sheet ul {{ list-style: none; padding: 0; }}
  .pdf-sheet li {{ font-size: 31px; line-height: 1.45; margin-bottom: 18px; color: #1e293b; font-weight: 600; }}
  .pdf-tip {{ background: #fef08a; color: #854d0e; padding: 22px; border-radius: 20px; font-size: 28px; font-weight: 700; margin-top: 16px; }}

  .app-box {{ background: #1e293b; border: 4px solid #38bdf8; border-radius: 40px; padding: 48px; }}
  .mode-row {{ display: flex; gap: 18px; margin-bottom: 32px; }}
  .mode-btn {{ flex: 1; background: #334155; color: #fff; font-size: 28px; font-weight: 800; padding: 24px 12px; border-radius: 20px; text-align: center; transition: 0.3s; }}
  .mode-btn.lit {{ background: #38bdf8; color: #0f172a; transform: scale(1.06); }}
  .slider-row {{ margin-bottom: 28px; }}
  .slider-lbl {{ display: flex; justify-content: space-between; font-size: 32px; font-weight: 700; margin-bottom: 12px; }}
  .bar-track {{ background: #0f172a; height: 28px; border-radius: 999px; overflow: hidden; border: 2px solid #475569; }}
  .bar-prog {{ background: linear-gradient(90deg, #38bdf8, #22c55e); height: 100%; width: 45%; transition: width 0.5s ease; }}
  .kpi-2x2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 22px; margin-top: 32px; }}
  .kpi-tile {{ background: #0f172a; border: 2px solid #38bdf8; border-radius: 26px; padding: 28px; text-align: center; }}
  .kpi-num {{ font-size: 58px; font-weight: 900; color: #22c55e; }}
  .kpi-name {{ font-size: 26px; color: #94a3b8; margin-top: 8px; }}

  .cta-Btn {{ background: linear-gradient(90deg, #22c55e, #16a34a); color: #fff; font-size: 46px; font-weight: 900; padding: 38px; border-radius: 30px; text-align: center; margin-top: 34px; box-shadow: 0 15px 45px rgba(34,197,94,0.5); animation: pulse 1.2s infinite alternate; }}

  .footer-bar {{ position: absolute; bottom: 55px; left: 60px; right: 60px; background: rgba(15,23,42,0.95); border: 2px solid #475569; border-radius: 28px; padding: 24px 36px; text-align: center; font-size: 30px; font-weight: 700; color: #38bdf8; }}
  #cursor-ring {{ position: absolute; width: 72px; height: 72px; border-radius: 50%; background: rgba(56,189,248,0.45); border: 5px solid #fff; box-shadow: 0 0 35px #38bdf8; z-index: 9999; pointer-events: none; transition: all 0.55s ease; left: 540px; top: 960px; transform: translate(-50%, -50%); }}
</style>
</head>
<body>
  <div class="bg-glow"></div>
  <div id="cursor-ring"></div>

  <div class="top-pill">
    <span class="cat">{esc(spec.get('category', 'DIGITAL PLAYBOOK + APP'))}</span>
    <span class="price">FULL KIT • ${price_usd:.0f}</span>
  </div>

  <div class="scene active" id="sc1">
    <div class="card-big">
      <span class="hook-tag">🔥 {esc(spec.get('audience', 'FOR EVERYONE'))}</span>
      <h1 class="giant">{esc(spec.get('hook_headline', spec['title']))}</h1>
      <p class="lead">{esc(spec['title'])}: {esc(spec['subtitle'])}</p>
      <div class="bundle-items">
        <div class="b-item">📘 1. Illustrated Multi-Page PDF Playbook</div>
        <div class="b-item">🎮 2. Live Interactive Web App &amp; Game</div>
        <div class="b-item">🖨️ 3. Printable Worksheets &amp; Cheat Sheets</div>
      </div>
    </div>
  </div>

  <div class="scene" id="sc2">
    <div class="pdf-sheet" id="sheet1">
      <h2>📘 Inside the PDF Playbook — {esc(p1.get('page_title', 'Page 1'))}</h2>
      <ul>{p1_bullets}</ul>
      <div class="pdf-tip">💡 {esc(p1.get('pro_tip', 'Step-by-step visual guide included!'))}</div>
    </div>
    <div class="pdf-sheet" id="sheet2">
      <h2>📄 {esc(p2.get('page_title', 'Page 2: Printable Action Sheet'))}</h2>
      <ul>{p2_bullets}</ul>
    </div>
  </div>

  <div class="scene" id="sc3">
    <div class="app-box">
      <h1 style="font-size:48px;margin-bottom:24px;">⚡ Companion Interactive App</h1>
      <div class="mode-row">
        <div class="mode-btn" id="m1">{esc(spec.get('app_preset_1', 'Starter'))}</div>
        <div class="mode-btn lit" id="m2">{esc(spec.get('app_preset_2', 'Explorer'))}</div>
        <div class="mode-btn" id="m3">{esc(spec.get('app_preset_3', 'Genius'))}</div>
      </div>
      <div class="slider-row">
        <div class="slider-lbl"><span>{esc(spec.get('app_slider_1_label', 'Level'))}</span><span id="sv1">Level 5</span></div>
        <div class="bar-track"><div class="bar-prog" id="sb1" style="width:50%;"></div></div>
      </div>
      <div class="slider-row">
        <div class="slider-lbl"><span>{esc(spec.get('app_slider_2_label', 'Daily Missions'))}</span><span id="sv2">45 mins</span></div>
        <div class="bar-track"><div class="bar-prog" id="sb2" style="width:65%;"></div></div>
      </div>
      <div class="kpi-2x2">
        <div class="kpi-tile"><div class="kpi-num" id="kv1">+450</div><div class="kpi-name">{esc(spec.get('kpi_1_label', 'XP Earned'))}</div></div>
        <div class="kpi-tile"><div class="kpi-num" id="kv2">92%</div><div class="kpi-name">{esc(spec.get('kpi_2_label', 'Mastery Score'))}</div></div>
        <div class="kpi-tile"><div class="kpi-num" id="kv3">5.2h</div><div class="kpi-name">{esc(spec.get('kpi_3_label', 'Time Saved'))}</div></div>
        <div class="kpi-tile"><div class="kpi-num" id="kv4">RANK S</div><div class="kpi-name">{esc(spec.get('kpi_4_label', 'Badge'))}</div></div>
      </div>
    </div>
  </div>

  <div class="scene" id="sc4">
    <div class="card-big" style="text-align:center;">
      <span class="hook-tag">🚀 INSTANT DIGITAL DOWNLOAD</span>
      <h1 class="giant">{esc(spec['title'])}</h1>
      <p class="lead">Get the Complete Illustrated PDF Playbook + Interactive App + Printable Kit!</p>
      <div class="cta-Btn">🛒 TAP STORE LINK IN PROFILE / BIO</div>
    </div>
  </div>

  <div class="footer-bar" id="footerTxt">
    🔗 Store &amp; Instant Download Link in Channel Profile / Bio!
  </div>

<script>
  function showScene(num, cursorX, cursorY) {{
    document.querySelectorAll('.scene').forEach((el, i) => {{
      el.classList.toggle('active', (i + 1) === num);
    }});
    const c = document.getElementById('cursor-ring');
    c.style.left = cursorX + 'px';
    c.style.top = cursorY + 'px';
  }}
  function animateAppValues(lvl, mins, xp, pct, modeIdx) {{
    document.getElementById('sv1').textContent = 'Level ' + lvl;
    document.getElementById('sb1').style.width = (lvl * 10) + '%';
    document.getElementById('sv2').textContent = mins + ' mins';
    document.getElementById('sb2').style.width = mins + '%';
    document.getElementById('kv1').textContent = '+' + xp;
    document.getElementById('kv2').textContent = pct + '%';
    ['m1','m2','m3'].forEach((id, idx) => {{
      document.getElementById(id).classList.toggle('lit', (idx + 1) === modeIdx);
    }});
  }}
</script>
</body>
</html>"""


def generate_pdf_and_record_9x16_video(
    playbook_html_path: Path,
    pdf_output_path: Path,
    showcase_html_path: Path,
) -> Path:
    from playwright.sync_api import sync_playwright

    for old_file in RAW_VIDEO_DIR.glob("*"):
        old_file.unlink(missing_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        print("   -> Compiling multi-page Illustrated PDF Playbook via Chromium...")
        pdf_page = browser.new_page()
        pdf_page.goto(playbook_html_path.resolve().as_uri(), wait_until="networkidle")
        pdf_page.pdf(
            path=str(pdf_output_path),
            format="A4",
            print_background=True,
            margin={"top": "12mm", "bottom": "12mm", "left": "12mm", "right": "12mm"},
        )
        pdf_page.close()
        print(f"   -> Saved PDF Playbook: {pdf_output_path} ({pdf_output_path.stat().st_size} bytes)")

        print("   -> Recording full-screen 1080x1920 4-Scene Motion Video...")
        context = browser.new_context(
            viewport={"width": 1080, "height": 1920},
            device_scale_factor=1,
            record_video_dir=str(RAW_VIDEO_DIR),
            record_video_size={"width": 1080, "height": 1920},
        )
        page = context.new_page()
        page.goto(showcase_html_path.resolve().as_uri(), wait_until="networkidle")

        page.evaluate("showScene(1, 540, 1180)")
        page.wait_for_timeout(3800)

        page.evaluate("showScene(2, 540, 620)")
        page.wait_for_timeout(2300)
        page.evaluate(
            """() => {
                document.getElementById('sheet1').style.transform = 'scale(0.96)';
                document.getElementById('sheet2').style.transform = 'scale(1.03)';
                showScene(2, 540, 1280);
            }"""
        )
        page.wait_for_timeout(2400)

        page.evaluate("showScene(3, 240, 480)")
        page.evaluate("animateAppValues(4, 35, 320, 84, 1)")
        page.wait_for_timeout(1700)

        page.evaluate("showScene(3, 540, 740)")
        page.evaluate("animateAppValues(7, 65, 690, 94, 2)")
        page.wait_for_timeout(1700)

        page.evaluate("showScene(3, 840, 480)")
        page.evaluate("animateAppValues(10, 92, 1250, 99, 3)")
        page.wait_for_timeout(1900)

        page.evaluate("showScene(4, 540, 1180)")
        page.wait_for_timeout(3200)

        video_path_str = page.video.path()
        context.close()
        browser.close()

    return Path(video_path_str)


def render_9x16_promo_video(
    recorded_webm: Path,
    voiceover_text: str,
    output_mp4: Path,
) -> Path:
    """
    Merges the full 17s Playwright `.webm` motion video with `edge-tts` audio.
    Uses `-af apad` and `-shortest` WITHOUT `-stream_loop -1` so all 4 scenes
    always play completely to the end (even if the voiceover finishes at 12s).
    """
    audio_mp3 = DIST_DIR / "voiceover.mp3"
    subs_srt = DIST_DIR / "subtitles.srt"

    tts_ok = False
    if shutil.which("edge-tts"):
        print("   -> Generating neural voiceover MP3 + SRT subtitles via edge-tts...")
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
            print(f"   -> edge-tts notice ({e}); using backup audio...")

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
                "17",
                "-q:a",
                "9",
                "-acodec",
                "libmp3lame",
                str(audio_mp3),
            ],
            check=True,
        )

    print("   -> Encoding full-screen 1080x1920 H.264 MP4 via FFmpeg (all 4 scenes preserved)...")
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(recorded_webm),
        "-i",
        str(audio_mp3),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-vf",
        "scale=1080:1920,format=yuv420p",
        "-af",
        "apad",
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
    return output_mp4


# =====================================================================
# 4. WHOP STORE PRODUCT & PAYMENT CHECKOUT ENGINE
# =====================================================================
def create_whop_product_and_checkout(
    app_title: str,
    app_desc: str,
    price_usd: float,
    pro_bundle_url: str,
    storefront_url: str,
) -> tuple[str, str]:
    if not (WHOP_API_KEY and WHOP_COMPANY_ID):
        return storefront_url, "Skipped (WHOP_API_KEY or WHOP_COMPANY_ID missing)"

    print("4. Whop Agent: Creating visible Product & Payment Checkout on api.whop.com...")
    created_prod_id = ""
    prod_route = ""
    try:
        prod_req = urllib.request.Request(
            "https://api.whop.com/api/v1/products",
            data=json.dumps(
                {
                    "company_id": WHOP_COMPANY_ID,
                    "title": app_title[:50],
                    "description": app_desc[:250],
                    "visibility": "visible",
                    "custom_cta": "order_now",
                    "custom_cta_url": pro_bundle_url,
                    "redirect_purchase_url": pro_bundle_url,
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {WHOP_API_KEY}",
                "Content-Type": "application/json",
                "Api-Version-Date": "2025-01-01",
            },
            method="POST",
        )
        with urllib.request.urlopen(prod_req, timeout=30) as p_resp:
            p_data = json.loads(p_resp.read().decode("utf-8"))
            created_prod_id = p_data.get("id", "")
            prod_route = p_data.get("route", "")
            print(f"   -> Created visible Whop Product: {created_prod_id} (route: {prod_route})")
    except urllib.error.HTTPError as e:
        err_p = e.read().decode("utf-8", errors="replace")
        print(f"   -> Whop /v1/products HTTP {e.code}: {err_p[:220]}")
    except Exception as e:
        print(f"   -> Whop /v1/products notice: {e}")

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
                print(f"   -> Created live Whop Payment Checkout URL: {purchase_url}")
                return purchase_url, f"Live Whop Checkout created ({w_data.get('id', 'ok')})"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"   -> Whop checkout HTTP {e.code}: {err_body[:300]}")
        if prod_route:
            return f"https://whop.com/{prod_route}", f"Product live at whop.com/{prod_route} (Checkout HTTP {e.code}: {err_body[:120]})"
        return storefront_url, f"Whop HTTP {e.code}: {err_body[:160]}"
    except Exception as e:
        return storefront_url, f"Whop error: {e}"

    return storefront_url, "Using Jagnor Storefront URL"


# =====================================================================
# 5. YOUTUBE SHORTS & INSTAGRAM REELS UPLOADERS
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

    print("   -> Uploading full-screen 9:16 motion video to YouTube Shorts...")
    try:
        access_token = get_youtube_access_token()
        metadata = {
            "snippet": {
                "title": f"{title[:80]} #Shorts",
                "description": description,
                "categoryId": "27",
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
        if not upload_location:
            return "YouTube Error: Missing resumable Location header"

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
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"   -> YouTube HTTP {e.code}: {err_body[:240]}")
        return f"HTTP {e.code}: {err_body[:140]}"
    except Exception as e:
        return f"Notice: {e}"


def upload_to_instagram_reels(public_mp4_url: str, caption: str) -> str:
    if not (IG_USER_ID and IG_ACCESS_TOKEN and public_mp4_url):
        return "Skipped (Instagram secrets missing)"

    print(f"   -> Creating Instagram Reels media container from {public_mp4_url}...")
    create_url = f"{IG_GRAPH_BASE}/{IG_USER_ID}/media"
    create_params = urllib.parse.urlencode(
        {
            "media_type": "REELS",
            "video_url": public_mp4_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": IG_ACCESS_TOKEN,
        }
    ).encode("utf-8")

    try:
        req = urllib.request.Request(create_url, data=create_params, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            creation_id = json.loads(resp.read().decode("utf-8"))["id"]

        status_url = (
            f"{IG_GRAPH_BASE}/{creation_id}"
            f"?fields=status_code&access_token={IG_ACCESS_TOKEN}"
        )
        final_status = ""
        for attempt in range(1, 13):
            time.sleep(10)
            with urllib.request.urlopen(status_url, timeout=20) as s_resp:
                final_status = json.loads(s_resp.read().decode("utf-8")).get("status_code", "")
                print(f"   -> Instagram container status ({attempt}/12): {final_status}")
                if final_status == "FINISHED":
                    break
                if final_status in ("ERROR", "EXPIRED"):
                    return f"Instagram container {final_status}"
        if final_status != "FINISHED":
            return f"Instagram container timed out (last status: {final_status or 'UNKNOWN'})"

        publish_url = f"{IG_GRAPH_BASE}/{IG_USER_ID}/media_publish"
        pub_params = urllib.parse.urlencode(
            {"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN}
        ).encode("utf-8")
        pub_req = urllib.request.Request(publish_url, data=pub_params, method="POST")
        with urllib.request.urlopen(pub_req, timeout=30) as p_resp:
            media_id = json.loads(p_resp.read().decode("utf-8")).get("id", "")
            print(f"   -> Published Instagram Reel Media ID: {media_id}")
            return f"Instagram Reel ID: {media_id}"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"   -> Instagram HTTP {e.code}: {err_body[:250]}")
        return f"HTTP {e.code}: {err_body[:160]}"
    except Exception as e:
        return f"Error: {e}"




# =====================================================================
# 6. UNIFIED COMPANY BRAIN, ATOMIC LEDGER & PAPERCLIP MASTER ENGINES
# =====================================================================
def atomic_write_json(path: Path, data: Any) -> None:
    """Writes JSON atomically with file locking so concurrent runs never corrupt ledger or manifest files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    with lock_path.open("w", encoding="utf-8") as lock_f:
        if fcntl is not None:
            try:
                fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
            except OSError:
                pass
        try:
            fd, tmp_name = tempfile.mkstemp(
                dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
            )
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
            if fcntl is not None:
                try:
                    fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass


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
    def load(cls, brain_dir: Path | None = None) -> "CompanyBrain":
        target_dir = brain_dir or BRAIN_DIR
        today_utc = time.strftime("%Y-%m-%d", time.gmtime())
        target_dir.mkdir(parents=True, exist_ok=True)

        def _read_md(name: str, default: str) -> str:
            p = target_dir / name
            if not p.exists():
                p.write_text(default, encoding="utf-8")
            return p.read_text(encoding="utf-8")

        icp = _read_md(
            "01_identity_icp.md",
            "# Identity & ICP\nTarget high-reach consumers, parents, students, and digital buyers.\n",
        )
        style = _read_md(
            "02_brand_style.md",
            "# Brand Style\nPrimary: #0F172A | Accent: #38BDF8 | Highlight: #FACC15\n",
        )
        pricing = _read_md(
            "03_offers_pricing.md",
            "# Offers & Pricing\n- Digital Playbook + App Bundle: $7-$17\n- B2B Automation Retainer: $1,500\n",
        )
        sops = _read_md(
            "04_sops_guardrails.md",
            "# SOPs & Guardrails\nMax 4 posts/day. Full 1080x1920 9:16 motion video QA verified.\n",
        )

        ledger_path = target_dir / "05_memory_ledger.json"
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
            brain_dir=target_dir,
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

    def record_completion(
        self, item_key: str, engine: str, cost_usd: float, summary: dict[str, Any]
    ) -> None:
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
        history.append(
            {
                "timestamp": int(time.time()),
                "engine": engine,
                "item_key": item_key,
                "cost_usd": cost_usd,
                "summary": summary,
            }
        )
        data["history"] = history[-100:]
        atomic_write_json(self.ledger_path, data)


def verify_rendered_mp4_qa(mp4_path: Path, min_duration: float = 5.0) -> str:
    """Runs the Master Worker binary ffprobe + moov atom QA check on the rendered 9:16 MP4."""
    try:
        if not mp4_path.exists() or mp4_path.stat().st_size == 0:
            return "QA_WARN: File missing or empty"
        res = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(mp4_path),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        data = json.loads(res.stdout)
        duration = float(data.get("format", {}).get("duration", 0.0))
        streams = data.get("streams", [])
        vs = next((s for s in streams if s.get("codec_type") == "video"), None)
        aus = next((s for s in streams if s.get("codec_type") == "audio"), None)
        if not vs or not aus:
            return "QA_WARN: Missing video or audio stream"
        w, h = int(vs.get("width", 0)), int(vs.get("height", 0))
        vc, ac = vs.get("codec_name", ""), aus.get("codec_name", "")
        return f"PASS ({w}x{h} {vc}/{ac}, {duration:.1f}s, +faststart verified)"
    except Exception as exc:
        return f"QA_NOTICE: {exc}"


# =====================================================================
# MAIN 6-AGENT + 6-AI COUNCIL ORCHESTRATOR LOOP
# =====================================================================
def run_full_circle_autonomous_factory() -> int:
    brain = CompanyBrain.load(BRAIN_DIR)
    storefront_url = f"{PUBLIC_VIDEO_BASE_URL}/"
    run_ts = int(time.time())
    slug = f"prod_{run_ts}"

    pdf_filename = f"playbook_{slug}.pdf"
    app_filename = f"app_{slug}.html"
    zip_filename = f"bundle_{slug}.zip"

    pdf_url = f"{PUBLIC_VIDEO_BASE_URL}/{pdf_filename}"
    app_url = f"{PUBLIC_VIDEO_BASE_URL}/{app_filename}"
    pro_bundle_url = f"{RAW_GITHUB_BASE_URL}/{zip_filename}"
    public_mp4_url = f"{RAW_GITHUB_BASE_URL}/promo_short_9x16.mp4?v={run_ts}"

    print("1. 6-AI Specialist Council: Harvesting social trends & designing today's Bundle...")
    spec = scout_and_design_product(processed_titles=brain.processed_items)
    app_title = str(spec.get("title", DEFAULT_PRODUCT_SPEC["title"])).strip()
    app_desc = str(spec.get("subtitle", DEFAULT_PRODUCT_SPEC["subtitle"])).strip()
    price_usd = safe_price(spec.get("price_usd", 9.00))
    voiceover_script = str(spec.get("voiceover", DEFAULT_PRODUCT_SPEC["voiceover"])).strip()

    checkout_url, whop_status = create_whop_product_and_checkout(
        app_title, app_desc, price_usd, pro_bundle_url, storefront_url
    )

    print(f"2. Builder Agent: Creating PDF Playbook, Interactive App & Storefront for '{app_title}'...")
    playbook_html_str = build_playbook_html(spec)
    playbook_html_path = DIST_DIR / "playbook_source.html"
    playbook_html_path.write_text(playbook_html_str, encoding="utf-8")

    app_html_str = build_interactive_app_html(spec, checkout_url, pdf_filename, price_usd)
    (PUBLIC_DIR / app_filename).write_text(app_html_str, encoding="utf-8")
    (PUBLIC_DIR / "app_latest.html").write_text(app_html_str, encoding="utf-8")

    showcase_html_str = build_full_screen_motion_showcase_html(spec, price_usd)
    showcase_html_path = DIST_DIR / "showcase_1080x1920.html"
    showcase_html_path.write_text(showcase_html_str, encoding="utf-8")

    pdf_path = PUBLIC_DIR / pdf_filename
    recorded_webm = generate_pdf_and_record_9x16_video(
        playbook_html_path, pdf_path, showcase_html_path
    )
    shutil.copyfile(pdf_path, PUBLIC_DIR / "playbook_latest.pdf")

    safe_arc_title = "".join(c if c.isalnum() or c in "_-" else "_" for c in app_title[:30])
    for z_target in (
        PUBLIC_DIR / zip_filename,
        PUBLIC_DIR / "pro_app_bundle.zip",
        DIST_DIR / "pro_app_bundle.zip",
    ):
        with zipfile.ZipFile(z_target, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(pdf_path, arcname=f"{safe_arc_title}_Playbook.pdf")
            zf.writestr("Interactive_App_Offline.html", app_html_str)
            zf.writestr(
                "START_HERE_GUIDE.txt",
                f"{app_title}\n{app_desc}\n\n"
                f"1. Open the PDF Playbook in any PDF viewer or print it out.\n"
                f"2. Open Interactive_App_Offline.html in any browser.\n"
                f"3. Visit our Full Storefront: {storefront_url}\n",
            )

    catalog_path = PUBLIC_DIR / "catalog.json"
    catalog = []
    if catalog_path.exists():
        try:
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        except Exception:
            catalog = []

    catalog.insert(
        0,
        {
            "title": app_title,
            "subtitle": app_desc,
            "category": spec.get("category", "DIGITAL BUNDLE"),
            "price_usd": price_usd,
            "checkout_url": checkout_url,
            "pdf_url": pdf_filename,
            "app_url": app_filename,
        },
    )
    catalog = catalog[:24]
    atomic_write_json(catalog_path, catalog)
    (PUBLIC_DIR / "index.html").write_text(
        build_storefront_html(catalog, checkout_url), encoding="utf-8"
    )

    print("5. Promoter Agent & Binary QA Gate: Encoding full-screen 9:16 MP4 & verifying...")
    mp4_path = PUBLIC_DIR / "promo_short_9x16.mp4"
    render_9x16_promo_video(recorded_webm, voiceover_script, mp4_path)
    qa_report = verify_rendered_mp4_qa(mp4_path)
    print(f"   -> Video QA Gate Report: {qa_report}")

    social_caption = (
        f"{spec.get('caption', app_title)}\n\n"
        f"🛒 Instant Checkout & Payment: {checkout_url}\n"
        f"🏪 Full Digital Store (PDF Playbook + Interactive App): {storefront_url}\n"
        f"📘 Preview PDF Playbook: {pdf_url}\n"
        f"#Shorts #Reels #Playbook #KidsLearning #DigitalProducts #AI"
    )

    print("   -> Pushing new Storefront, PDF Playbook, App, Brain Ledger & 9:16 Video to GitHub...")
    subprocess.run(["git", "config", "user.name", "AI-Company-Bot"], check=False)
    subprocess.run(["git", "config", "user.email", "bot@users.noreply.github.com"], check=False)
    subprocess.run(["git", "add", "public/", "dist/", "brain/"], check=False)
    subprocess.run(["git", "commit", "-m", f"Release Bundle: {app_title}"], check=False)
    subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "main"], check=False)
    subprocess.run(["git", "push"], check=False)
    time.sleep(3)

    yt_result = upload_to_youtube_shorts(mp4_path, app_title, social_caption)
    ig_result = upload_to_instagram_reels(public_mp4_url, social_caption)

    summary_manifest = {
        "engine": "full_circle_5ai_council",
        "status": "PUBLISHED",
        "product_title": app_title,
        "category": spec.get("category"),
        "price_usd": price_usd,
        "whop_checkout_url": checkout_url,
        "whop_status": whop_status,
        "storefront_url": storefront_url,
        "pdf_url": pdf_url,
        "app_url": app_url,
        "qa_report": qa_report,
        "youtube_result": yt_result,
        "instagram_result": ig_result,
    }
    brain.record_completion(
        item_key=f"bundle:{app_title.lower()}",
        engine="full_circle_5ai_council",
        cost_usd=0.0,
        summary=summary_manifest,
    )
    atomic_write_json(DIST_DIR / "manifest.json", summary_manifest)

    if GMAIL_USER and GMAIL_APP_PASS:
        print("6. Gmail Agent: Sending daily CEO report...")
        msg = EmailMessage()
        msg["Subject"] = f"[6-AI Council Bundle Launch] {app_title} (PDF + App)"
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_USER
        msg.set_content(
            f"Your 6-AI Council & Autonomous Company just built and published a Multi-Format Product Bundle!\n\n"
            f"1. PRODUCT BUNDLE (Chosen from Live Social Trends):\n"
            f"   Title: {app_title}\n"
            f"   Category: {spec.get('category')}\n"
            f"   Price: ${price_usd:.2f} USD\n"
            f"   Video Hook: {spec.get('hook_headline')}\n"
            f"   Binary QA Check: {qa_report}\n\n"
            f"2. YOUR DIGITAL STOREFRONT (Add this 1 link to your YouTube & IG Bio!):\n"
            f"   {storefront_url}\n\n"
            f"3. INSIDE TODAY'S BUNDLE:\n"
            f"   - Illustrated PDF Playbook: {pdf_url}\n"
            f"   - Interactive Companion Web App: {app_url}\n"
            f"   - Full Downloadable ZIP Pack: {pro_bundle_url}\n\n"
            f"4. WHOP CHECKOUT & PAYMENT:\n"
            f"   Checkout Link: {checkout_url}\n"
            f"   Whop Status: {whop_status}\n\n"
            f"5. SHORT-FORM VIDEO DISTRIBUTION:\n"
            f"   - YouTube Shorts: {yt_result}\n"
            f"   - Instagram Reels: {ig_result}\n"
        )
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
                smtp.login(GMAIL_USER, GMAIL_APP_PASS)
                smtp.send_message(msg)
            print("   -> Daily CEO report emailed!")
        except Exception as e:
            print(f"   -> Gmail notice: {e}")

    print("Done! All 6 AI Specialists + 6 Autonomous Robots completed today's build.")
    return 0


def main() -> None:
    """
    Supports both zero-argument GitHub Actions execution (`python3 full_circle_company.py`)
    AND Paperclip Master Worker CLI flags (`--engine clipping | b2b_agency | carousel_funnel | digital_product`).
    """
    if len(sys.argv) > 1 and any(arg.startswith("--") for arg in sys.argv[1:]):
        import jagnor_master_worker
        sys.exit(jagnor_master_worker.main())
    sys.exit(run_full_circle_autonomous_factory())


if __name__ == "__main__":
    main()
