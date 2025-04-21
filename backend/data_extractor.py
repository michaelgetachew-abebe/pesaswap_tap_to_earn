import httpx

OPENROUTER_API_KEY = "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"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = ""

async def extract_unread(input_html: str, model: str = DEFAULT_MODEL) -> str:
    prompt = (
        f"You are a JSON-only extractor. Given the raw HTML of WhatsApp Web message containers, find every message and output a single JSON object that strcicly follows this schema:"
        f"""
            {"message": 
                [
                    {"sender": string, // the name in the span[@title]
                     "timestamp": string, // the timestamp/day of the week/time of the day/time describing word,
                     "text": string // the message content
                    }
                ]
            }
        """
        f"Rules:\n 1. Return only valid JSON-no explanations, no extra keys.\n 2. If any field is missing, use null for its value. \n 3. Process all messages present in the HTML"
        f"\n\nINPUT HTML: {input_html}"
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost",  # update this to your domain if using in prod, STH like "HTTP-Referer": "https://api.myconeapp.com"
        "X-Title": "ConeTranslation"
    }

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that extracts useful JSON from a WhatsApp web page source accurately. You should only respond with JSON-only!"},
            {"role": "user", "content": prompt}
        ]
    }

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(OPENROUTER_API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
