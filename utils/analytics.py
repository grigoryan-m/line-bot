"""
Analytics tracker.
Logs all key events to a local file and optionally sends to external services.

TODO: Wire up Google Analytics (Measurement Protocol) or your own backend.
"""

import logging
import json
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ANALYTICS_LOG = os.path.join(os.path.dirname(__file__), "../data/analytics.jsonl")

# Optional: Google Analytics 4 Measurement Protocol
GA4_MEASUREMENT_ID = os.getenv("GA4_MEASUREMENT_ID", "")
GA4_API_SECRET = os.getenv("GA4_API_SECRET", "")


def _write_event(event: dict):
    """Append event as JSON line to local log."""
    try:
        os.makedirs(os.path.dirname(ANALYTICS_LOG), exist_ok=True)
        with open(ANALYTICS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Analytics write error: {e}")


async def _send_to_ga4(client_id: str, event_name: str, params: dict):
    """Send event to Google Analytics 4 via Measurement Protocol."""
    if not GA4_MEASUREMENT_ID or not GA4_API_SECRET:
        return
    try:
        import httpx
        url = (
            f"https://www.google-analytics.com/mp/collect"
            f"?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"
        )
        payload = {
            "client_id": client_id,
            "events": [{"name": event_name, "params": params}],
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json=payload)
    except Exception as e:
        logger.warning(f"GA4 send error: {e}")


async def track(
    user_id: int,
    event: str,
    lang: str = "en",
    extra: Optional[dict] = None,
):
    """
    Track a user event.

    Events used in this bot:
      bot_started, language_selected, menu_opened,
      loyalty_started, loyalty_completed, loyalty_error,
      store_search_geo, store_search_region, store_map_click,
      manager_started, manager_transferred, manager_message_left,
      socials_opened, about_opened
    """
    payload = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "user_id": user_id,
        "event": event,
        "lang": lang,
        **(extra or {}),
    }
    _write_event(payload)

    # Send to GA4 asynchronously (fire-and-forget)
    await _send_to_ga4(
        client_id=str(user_id),
        event_name=event,
        params={"lang": lang, **(extra or {})},
    )

    logger.info(f"[analytics] {event} | user={user_id} | {extra or {}}")
