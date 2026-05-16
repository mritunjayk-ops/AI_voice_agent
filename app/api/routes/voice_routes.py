import base64
import os
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.services.groq_service import (
    generate_response
)

from app.services.sarvam_service import (
    speech_to_text,
    text_to_speech
)


router = APIRouter()


OUTPUT_DIR = "generated_audio"

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


async def _audio_file_response(
    text: str
):

    tts_result = await text_to_speech(
        text
    )

    if not tts_result.audios:

        raise HTTPException(
            status_code=502,
            detail="Sarvam TTS returned no audio"
        )

    audio_base64 = (
        tts_result.audios[0]
    )

    audio_bytes = base64.b64decode(
        audio_base64
    )

    output_file_name = (
        f"{uuid.uuid4()}.wav"
    )

    output_file_path = os.path.join(
        OUTPUT_DIR,
        output_file_name
    )

    with open(
        output_file_path,
        "wb"
    ) as audio_file:

        audio_file.write(
            audio_bytes
        )

    return FileResponse(
        path=output_file_path,
        media_type="audio/wav",
        filename=output_file_name
    )


@router.post("/voice-chat")
async def voice_chat(
    file: UploadFile = File(...)
):

    audio_bytes = await file.read()

    if not audio_bytes:

        raise HTTPException(
            status_code=400,
            detail="No audio received"
        )

    stt_result = await speech_to_text(
        audio_bytes,
        file.filename or "recording.webm",
        file.content_type or "audio/webm"
    )

    user_text = stt_result.transcript.strip()

    if not user_text:

        raise HTTPException(
            status_code=400,
            detail="No speech detected"
        )

    ai_response = await generate_response(
        "default_user",
        user_text
    )

    return await _audio_file_response(
        ai_response
    )


@router.get("/voice-test")
async def voice_test():

    user_text = (
        "Recommend me some good ice cream."
    )

    ai_response = await generate_response(
        "default_user",
        user_text
    )

    return await _audio_file_response(
        ai_response
    )
