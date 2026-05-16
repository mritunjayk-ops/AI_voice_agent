import httpx

from pydantic import BaseModel

from app.core.config import SARVAM_API_KEY


SARVAM_TTS_URL = (
    "https://api.sarvam.ai/text-to-speech"
)

SARVAM_STT_URL = (
    "https://api.sarvam.ai/speech-to-text"
)


class SpeechToTextResponse(BaseModel):

    transcript: str


class TextToSpeechResponse(BaseModel):

    audios: list[str]


async def speech_to_text(
    audio_bytes: bytes,
    filename: str,
    content_type: str
):

    headers = {
        "api-subscription-key": SARVAM_API_KEY
    }

    files = {
        "file": (
            filename,
            audio_bytes,
            content_type
        )
    }

    data = {
        "model": "saaras:v3",
        "language_code": "unknown"
    }

    async with httpx.AsyncClient(
        timeout=120.0
    ) as client:

        response = await client.post(
            SARVAM_STT_URL,
            headers=headers,
            files=files,
            data=data
        )

    response.raise_for_status()

    response_json = response.json()

    return SpeechToTextResponse(
        transcript=response_json.get(
            "transcript",
            ""
        )
    )


async def text_to_speech(
    text: str
):

    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {

        "text": text,

        "target_language_code": "en-IN",

        "speaker": "shubh",

        "pace": 1.0,

        "speech_sample_rate": 22050,

        "model": "bulbul:v3"
    }

    async with httpx.AsyncClient(
        timeout=120.0
    ) as client:

        response = await client.post(
            SARVAM_TTS_URL,
            headers=headers,
            json=payload
        )

    response.raise_for_status()

    response_json = response.json()

    return TextToSpeechResponse(
        audios=response_json.get(
            "audios",
            []
        )
    )
