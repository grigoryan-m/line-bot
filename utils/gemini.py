"""
Gemini AI helper for the Help section of the LINE bot.
Uses gemini-2.5-flash-preview-05-20 with instructions loaded from gemini_instructions.txt.
"""
import logging
import httpx
import os
from pathlib import Path

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBRR_WRhDRlVLKhgeA8Wfe-EjdQlO1MU5s")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
MAX_OUTPUT_TOKENS = 900

# Path to the instructions file (same directory as this file's parent)
INSTRUCTIONS_FILE = Path(__file__).parent.parent / "gemini_instructions.txt"


def load_instructions() -> str:
    """Load system instructions from gemini_instructions.txt, ignoring comment lines."""
    try:
        lines = INSTRUCTIONS_FILE.read_text(encoding="utf-8").splitlines()
        instructions = "\n".join(
            line for line in lines
            if line.strip() and not line.strip().startswith("#")
        )
        return instructions
    except FileNotFoundError:
        logger.warning(f"gemini_instructions.txt not found at {INSTRUCTIONS_FILE}, using defaults.")
        return (
            "You are a helpful customer support assistant. "
            "Respond in the same language as the user. "
            "Do not give medical, legal, or financial advice."
        )
    except Exception as e:
        logger.error(f"Failed to load Gemini instructions: {e}")
        return "You are a helpful assistant."


async def ask_gemini(user_message: str, conversation_history: list[dict] | None = None) -> str:
    """
    Send a message to Gemini and return its reply.

    Args:
        user_message: The user's text input.
        conversation_history: Optional list of previous turns in format
                              [{"role": "user"/"model", "text": "..."}]

    Returns:
        Gemini's response as a string, or an error fallback message.
    """
    system_instruction = load_instructions()

    # Build conversation contents
    contents = []

    # Add history if provided
    if conversation_history:
        for turn in conversation_history:
            contents.append({
                "role": turn["role"],  # "user" or "model"
                "parts": [{"text": turn["text"]}]
            })

    # Add current user message
    contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
            "temperature": 0.7,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                GEMINI_API_URL,
                params={"key": GEMINI_API_KEY},
                json=payload,
            )
            data = response.json()

            if response.status_code == 200:
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                logger.error(f"Gemini empty response: {data}")
                return _fallback_message()
            else:
                logger.error(f"Gemini API error {response.status_code}: {data}")
                return _fallback_message()

    except Exception as e:
        logger.error(f"Gemini request failed: {e}")
        return _fallback_message()


def _fallback_message() -> str:
    return "⚠️ AI assistant is temporarily unavailable. Please try again later."
