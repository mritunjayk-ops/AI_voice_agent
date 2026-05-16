import base64
import os
import uuid

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.services.sarvam_service import text_to_speech


router = APIRouter()


OUTPUT_DIR = "generated_audio"

os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.post("/speak")
async def speak(text: str):

    response = await text_to_speech(text)

    audio_base64 = response.audios[0]

    audio_bytes = base64.b64decode(audio_base64)

    file_name = f"{uuid.uuid4()}.wav"

    file_path = os.path.join(OUTPUT_DIR, file_name)

    with open(file_path, "wb") as audio_file:
        audio_file.write(audio_bytes)

    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=file_name
    )