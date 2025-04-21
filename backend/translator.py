import httpx

OPENROUTER_API_KEY = "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"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4"

async def translate_text(content: str, source_lang: str, target_lang: str, model: str = DEFAULT_MODEL) -> str:
    prompt = (
        f"You are a professional translator. Translate the following content from {source_lang} to {target_lang}."
        f"\n\nContent: {content}"
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost",  # update this to your domain if using in prod, STH like "HTTP-Referer": "https://api.myconeapp.com"
        "X-Title": "ConeTranslation"
    }

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that translates text accurately. You should only respond with the translated content only!"},
            {"role": "user", "content": prompt}
        ]
    }

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(OPENROUTER_API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
