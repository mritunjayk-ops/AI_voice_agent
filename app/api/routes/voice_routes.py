import base64
import os
import time
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.logger import logger

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
    text: str,
    request_id: str | None = None
):

    tts_start = time.perf_counter()

    logger.info(
        "event=tts_started request_id=%s text_chars=%s",
        request_id or "-",
        len(text)
    )

    tts_result = await text_to_speech(
        text
    )

    tts_latency_ms = (
        time.perf_counter() - tts_start
    ) * 1000

    if not tts_result.audios:

        raise HTTPException(
            status_code=502,
            detail="Sarvam TTS returned no audio"
        )

    logger.info(
        "event=tts_completed request_id=%s latency_ms=%.2f audio_count=%s",
        request_id or "-",
        tts_latency_ms,
        len(tts_result.audios)
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

    request_id = str(
        uuid.uuid4()
    )

    pipeline_start = time.perf_counter()

    audio_bytes = await file.read()

    logger.info(
        (
            "event=audio_received request_id=%s "
            "filename=%s content_type=%s size_bytes=%s"
        ),
        request_id,
        file.filename or "recording.webm",
        file.content_type or "audio/webm",
        len(audio_bytes)
    )

    if not audio_bytes:

        raise HTTPException(
            status_code=400,
            detail="No audio received"
        )

    stt_start = time.perf_counter()

    logger.info(
        "event=stt_started request_id=%s",
        request_id
    )

    stt_result = await speech_to_text(
        audio_bytes,
        file.filename or "recording.webm",
        file.content_type or "audio/webm"
    )

    stt_latency_ms = (
        time.perf_counter() - stt_start
    ) * 1000

    user_text = stt_result.transcript.strip()

    logger.info(
        "event=stt_completed request_id=%s latency_ms=%.2f transcript_chars=%s",
        request_id,
        stt_latency_ms,
        len(user_text)
    )

    if not user_text:

        raise HTTPException(
            status_code=400,
            detail="No speech detected"
        )

    llm_start = time.perf_counter()

    logger.info(
        "event=llm_started request_id=%s provider=groq",
        request_id
    )

    ai_response = await generate_response(
        "default_user",
        user_text
    )

    llm_latency_ms = (
        time.perf_counter() - llm_start
    ) * 1000

    logger.info(
        "event=llm_completed request_id=%s provider=groq latency_ms=%.2f response_chars=%s",
        request_id,
        llm_latency_ms,
        len(ai_response)
    )

    response = await _audio_file_response(
        ai_response,
        request_id
    )

    total_latency_ms = (
        time.perf_counter() - pipeline_start
    ) * 1000

    logger.info(
        "event=voice_pipeline_completed request_id=%s total_latency_ms=%.2f",
        request_id,
        total_latency_ms
    )

    return response


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
