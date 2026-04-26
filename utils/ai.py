import logging
import httpx
import os

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """You are a helpful customer support assistant for a retail loyalty program bot.

You can help with:
- FAQ about the loyalty program (how to earn points, redeem rewards, etc.)
- Navigation help (how to find stores, register, etc.)
- General info about the company and stores

You MUST NOT:
- Give medical advice
- Answer legally sensitive questions
- Make up information you don't know

If a question is complex, medical, legal, or the user asks to speak with a human,
respond with exactly: [TRANSFER_TO_HUMAN]

Always respond in the same language the user writes in.
Keep answers concise and friendly."""


async def ask_ai(user_message: str, lang: str = "en") -> str:
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set, skipping AI")
        return "[TRANSFER_TO_HUMAN]"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 500,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_message}],
                }
            )
            data = response.json()
            if response.status_code == 200:
                return data["content"][0]["text"]
            else:
                logger.error(f"AI API error: {data}")
                return "[TRANSFER_TO_HUMAN]"
    except Exception as e:
        logger.error(f"AI request failed: {e}")
        return "[TRANSFER_TO_HUMAN]"
