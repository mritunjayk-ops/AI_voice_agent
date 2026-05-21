import asyncio
import os
import sys
import time
import httpx
from dotenv import load_dotenv

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(parent_dir, ".env")
load_dotenv(env_path)

api_key = os.getenv("SARVAM_API_KEY")

async def test_tts_latency(sample_rate):
    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": "Hello, testing TTS generation speed. This is a short sentence.",
        "target_language_code": "en-IN",
        "speaker": "shubh",
        "speech_sample_rate": sample_rate,
        "model": "bulbul:v3"
    }
    url = "https://api.sarvam.ai/text-to-speech"
    async with httpx.AsyncClient() as client:
        start_time = time.perf_counter()
        try:
            r = await client.post(url, headers=headers, json=payload, timeout=10.0)
            latency = (time.perf_counter() - start_time) * 1000
            print(f"Sample Rate: {sample_rate}Hz -> Status: {r.status_code}, Latency: {latency:.2f}ms, Audio len (chars): {len(r.json().get('audios', [''])[0]) if r.status_code == 200 else 0}")
            return latency
        except Exception as e:
            print(f"Sample Rate: {sample_rate}Hz -> Failed: {e}")
            return None

async def main():
    print("Testing Sarvam TTS latency at different sample rates...")
    for sr in [22050, 16000, 8000]:
        await test_tts_latency(sr)
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
