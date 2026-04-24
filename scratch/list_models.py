import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
URL = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"

async def list_models():
    async with httpx.AsyncClient() as client:
        resp = await client.get(URL)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            for m in models:
                name = m.get('name', 'N/A')
                display_name = m.get('displayName', 'N/A')
                # Try both snake_case and camelCase
                methods = m.get('supportedGenerationMethods') or m.get('supported_generation_methods') or []
                if 'generateContent' in methods:
                    print(f"Model: {name} (DisplayName: {display_name}) supports generateContent")
        else:
            print(f"Error {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(list_models())
