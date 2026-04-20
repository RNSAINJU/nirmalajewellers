from __future__ import annotations

import os
from typing import Optional, Tuple

import requests


def send_message(channel: str, to_phone: str, message: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Send message via configured provider endpoint.

    Returns: (success, provider_message_id, error_message)
    """
    if channel not in {"sms", "whatsapp"}:
        return False, None, f"Unsupported channel: {channel}"

    if channel == "sms":
        provider_url = os.getenv("SMS_PROVIDER_URL", "").strip()
        token = os.getenv("SMS_PROVIDER_TOKEN", "").strip()
        sender_id = os.getenv("SMS_SENDER_ID", "").strip()
    else:
        provider_url = os.getenv("WHATSAPP_PROVIDER_URL", "").strip()
        token = os.getenv("WHATSAPP_PROVIDER_TOKEN", "").strip()
        sender_id = os.getenv("WHATSAPP_SENDER_ID", "").strip()

    if not provider_url:
        return False, None, f"{channel} provider URL not configured"

    payload = {
        "to": to_phone,
        "message": message,
    }
    if sender_id:
        payload["sender_id"] = sender_id

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.post(provider_url, json=payload, headers=headers, timeout=15)
        if 200 <= response.status_code < 300:
            provider_message_id = None
            try:
                data = response.json()
                provider_message_id = str(data.get("message_id") or data.get("id") or "") or None
            except Exception:
                provider_message_id = None
            return True, provider_message_id, None
        return False, None, f"Provider HTTP {response.status_code}: {response.text[:500]}"
    except Exception as exc:
        return False, None, str(exc)
