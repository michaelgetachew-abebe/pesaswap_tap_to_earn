import httpx
import json
from fastapi import HTTPException
import os

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"

async def extract_unread(input_html: str, token: str, model: str = DEFAULT_MODEL) -> str:
    prompt = (
        "You are a JSON-only extractor. Given the raw HTML of a single WhatsApp Web chat list item, output a JSON object that strictly follows the following schema:\n"
        "{\n"
        '    "message": [\n'
        "        {\n"
        '            "sender": "string",  // the contact name\n'
        '            "timestamp": "string",  // the time of the last message\n'
        '            "text": "string",  // the preview of the last message\n'
        '            "unread_message": "int"  // the number of unread messages, or null if not present\n'
        "        }\n"
        "    ]\n"
        "}\n"
        "Rules:\n"
        "1. Return only valid JSONno explanations, no extra keys.\n"
        "2. If any field is missing, use null for its value.\n"
        "3. The sender, timestamp, and text should be strings extracted as text content, and unread_message should be an integer if present, otherwise null.\n"
        "Extraction Instructions:\n"
        "- Sender: Look for a `span` element with a `title` attribute that contains the contact's name. This is typically the first prominent text in the chat item.\n"
        "- Timestamp: Identify a text element that appears to be a time or date, often located near the sender's name or at the end of the chat item. It might be contained within a `div` or `span`.\n"
        "- Text (Message Preview): Look for a `span` with a `title` attribute that contains the preview of the last message. This is usually located below or next to the sender's name and timestamp.\n"
        "- Unread Message Count: Search for a `span` with an `aria-label` attribute that includes the phrase 'unread message' or similar. The text content of this span should be a number indicating the unread count, converted to an integer. If no such span exists, use null.\n\n"
        f"Now, extract the information from the following HTML:\n{input_html}"
    )

    if not token.startswith("Bearer "):
        token = f"Bearer {token}"

    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("HTTP_REFERER", "https://api.srv768692.hstgr.cloud"),
        "X-Title": os.getenv("X_TITLE", "ConeTranslation")
    }

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that extracts useful JSON from a WhatsApp web page source accurately. You should only respond with JSON-only!"},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        async with httpx.AsyncClient(verify=False) as client:  # SSL verification enabled by default
            response = await client.post(OPENROUTER_API_URL, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"]
            json.loads(result)
            return result
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"OpenRouter API error: {e.response.text}")
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=502, detail=f"Unexpected API response format: {str(e)}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"Invalid JSON response from OpenRouter: {str(e)}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Network error while contacting OpenRouter API: {str(e)}")