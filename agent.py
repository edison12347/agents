#!/usr/bin/env python3
"""
YouTube News Telegram Agent
────────────────────────────
Fetches recent videos from a YouTube channel via RSS, generates a daily
digest with Claude, and pushes the summary to a Telegram bot.

Required environment variables:
    ANTHROPIC_API_KEY      – Anthropic API key
    TELEGRAM_BOT_TOKEN     – Telegram bot token  (from @BotFather)
    TELEGRAM_CHAT_ID       – Target chat / group ID

Optional environment variables (defaults shown):
    YOUTUBE_CHANNEL        – @handle or channel URL   (@alphamediachannel)
    LOOKBACK_HOURS         – How many hours back to look  (24)
    SUMMARY_PROMPT         – Custom Claude prompt
"""

import os
import re
import sys
import logging
from datetime import datetime, timedelta, timezone

import feedparser
import anthropic
import httpx

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

DEFAULT_PROMPT = (
    "You are a news editor. Summarise the following YouTube videos from "
    "Alpha Media Channel into a concise daily digest. Highlight the key "
    "news stories, important events, and notable topics covered. Use clear "
    "bullet points, starting each with an emoji that fits the topic. "
    "End with a one-line overall takeaway."
)


def resolve_channel_id(channel_handle: str) -> str:
    """
    Convert a YouTube @handle / URL into a bare channel ID (UC…).
    If the input already looks like a channel ID it is returned unchanged.
    """
    # Strip tracking query params
    channel_handle = channel_handle.split("?")[0].rstrip("/")

    # Already a channel ID?
    if re.match(r"^UC[a-zA-Z0-9_-]{22}$", channel_handle):
        return channel_handle

    # Build the URL to scrape
    if channel_handle.startswith("http"):
        url = channel_handle
    elif channel_handle.startswith("@"):
        url = f"https://www.youtube.com/{channel_handle}"
    else:
        url = f"https://www.youtube.com/@{channel_handle}"

    logger.info("Resolving channel ID from %s …", url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }
    response = httpx.get(url, headers=headers, follow_redirects=True, timeout=30)
    response.raise_for_status()

    # Pattern 1 – JSON blob
    match = re.search(r'"channelId"\s*:\s*"(UC[a-zA-Z0-9_-]{22})"', response.text)
    if match:
        logger.info("Resolved channel ID: %s", match.group(1))
        return match.group(1)

    # Pattern 2 – URL path
    match = re.search(r"/channel/(UC[a-zA-Z0-9_-]{22})", response.text)
    if match:
        logger.info("Resolved channel ID: %s", match.group(1))
        return match.group(1)

    # Pattern 3 – externalId / browseId
    match = re.search(r'"(UC[a-zA-Z0-9_-]{22})"', response.text)
    if match:
        logger.info("Resolved channel ID (fallback): %s", match.group(1))
        return match.group(1)

    raise ValueError(f"Could not resolve a channel ID from: {url}")


def fetch_recent_videos(channel_id: str, hours: int = 24) -> list[dict]:
    """Return videos published in the last *hours* hours."""
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    logger.info("Fetching RSS feed: %s", rss_url)

    feed = feedparser.parse(rss_url)

    if feed.bozo and not feed.entries:
        raise ValueError(f"Failed to parse RSS feed: {feed.bozo_exception}")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent: list[dict] = []

    for entry in feed.entries:
        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        if published >= cutoff:
            recent.append(
                {
                    "title": entry.title,
                    "link": entry.link,
                    "published": published.strftime("%Y-%m-%d %H:%M UTC"),
                    "description": getattr(entry, "summary", "")[:600],
                }
            )

    logger.info("Found %d video(s) in the last %d hours.", len(recent), hours)
    return recent


def generate_summary(videos: list[dict], prompt: str) -> str:
    """Ask Claude to summarise the list of videos."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    videos_text = "\n\n".join(
        f"Title: {v['title']}\n"
        f"URL: {v['link']}\n"
        f"Published: {v['published']}\n"
        f"Description: {v['description']}"
        for v in videos
    )

    user_message = f"{prompt}\n\n---\n\n{videos_text}"

    logger.info("Generating summary with Claude …")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": user_message}],
    )

    return message.content[0].text


def send_telegram(text: str, bot_token: str, chat_id: str) -> None:
    """Send *text* to a Telegram chat, splitting if it exceeds the 4096-char limit."""
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    max_len = 4096

    # Split at paragraph boundaries to stay under the limit
    chunks: list[str] = []
    while len(text) > max_len:
        split_at = text.rfind("\n\n", 0, max_len)
        if split_at == -1:
            split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    if text:
        chunks.append(text)

    for i, chunk in enumerate(chunks, 1):
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        resp = httpx.post(api_url, json=payload, timeout=30)
        resp.raise_for_status()
        logger.info("Sent Telegram chunk %d / %d", i, len(chunks))


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    channel_handle = os.environ.get("YOUTUBE_CHANNEL", "@alphamediachannel")
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    prompt = os.environ.get("SUMMARY_PROMPT", DEFAULT_PROMPT)
    lookback_hours = int(os.environ.get("LOOKBACK_HOURS", "24"))

    logger.info("=== YouTube News Agent starting ===")
    logger.info("Channel : %s", channel_handle)
    logger.info("Lookback: %d hours", lookback_hours)

    try:
        channel_id = resolve_channel_id(channel_handle)
        videos = fetch_recent_videos(channel_id, lookback_hours)

        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

        if not videos:
            msg = (
                f"📺 *Alpha Media Channel — Daily Digest*\n"
                f"_{date_str}_\n\n"
                f"No new videos in the last {lookback_hours} hours."
            )
            send_telegram(msg, bot_token, chat_id)
            logger.info("No recent videos — sent empty-digest notification.")
            return

        summary = generate_summary(videos, prompt)

        video_links = "\n".join(
            f"• [{v['title']}]({v['link']})" for v in videos
        )
        header = (
            f"📺 *Alpha Media Channel — Daily Digest*\n"
            f"_{date_str}_\n\n"
        )
        footer = f"\n\n📎 *Videos today ({len(videos)})*\n{video_links}"

        send_telegram(header + summary + footer, bot_token, chat_id)
        logger.info("=== Daily digest sent successfully ===")

    except Exception as exc:
        logger.error("Agent failed: %s", exc, exc_info=True)
        # Best-effort error notification
        try:
            send_telegram(
                f"⚠️ *YouTube News Agent — Error*\n`{exc}`",
                bot_token,
                chat_id,
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
