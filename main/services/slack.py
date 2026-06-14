from __future__ import annotations

import os
from typing import Optional, Tuple

import requests


def send_slack_message(
    message: str,
    webhook_url: Optional[str] = None,
    channel: Optional[str] = None,
    username: Optional[str] = None,
    icon_emoji: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Send an operational alert through a Slack incoming webhook."""
    webhook_url = (webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")).strip()
    if not webhook_url:
        return False, "SLACK_WEBHOOK_URL is not configured"

    payload = {"text": message}

    channel = (channel or os.getenv("SLACK_CHANNEL", "")).strip()
    if channel:
        payload["channel"] = channel

    username = (username or os.getenv("SLACK_USERNAME", "")).strip()
    if username:
        payload["username"] = username

    icon_emoji = (icon_emoji or os.getenv("SLACK_ICON_EMOJI", "")).strip()
    if icon_emoji:
        payload["icon_emoji"] = icon_emoji

    try:
        response = requests.post(webhook_url, json=payload, timeout=15)
        if 200 <= response.status_code < 300:
            return True, None
        return False, f"Slack HTTP {response.status_code}: {response.text[:500]}"
    except Exception as exc:
        return False, str(exc)
