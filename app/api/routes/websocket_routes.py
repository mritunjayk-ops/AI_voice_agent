import asyncio
import json
import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logger import logger
from app.core.config import GROQ_API_KEY, SARVAM_API_KEY
from app.services.session_service import resolve_session_id

router = APIRouter()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        from app.services.groq_service import generate_response
        while True:
            # RECEIVE MESSAGE
            user_message = await websocket.receive_text()
            logger.info(f"WebSocket message received: {user_message}")

            # GENERATE AI RESPONSE
            ai_response = await generate_response(
                "websocket_user",
                user_message
            )

            # SEND RESPONSE
            await websocket.send_text(ai_response)

    except WebSocketDisconnect:
        logger.warning("WebSocket disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket Error: {str(e)}")


async def receive_sarvam_transcripts(sarvam_ws, client_ws, transcript_state):
    """
    Background loop to receive real-time transcripts from Sarvam STT WebSocket
    and push them back to the client.
    """
    try:
        async for message in sarvam_ws:
            data = json.loads(message)
            transcript = data.get("transcript", "").strip()
            if transcript:
                transcript_state["text"] = transcript
                # Send live transcript update to client
                await client_ws.send_json({
                    "event": "transcript",
                    "text": transcript
                })
    except websockets.exceptions.ConnectionClosed:
        logger.info("Sarvam STT WebSocket connection closed normally")
    except asyncio.CancelledError:
        logger.info("Sarvam STT transcript listener task cancelled")
    except Exception as e:
        logger.error(f"Error in receive_sarvam_transcripts: {str(e)}")


async def call_tts_and_send(text: str, seq: int, client_ws: WebSocket):
    """
    Converts a sentence to speech via Sarvam HTTP TTS and sends it to the client.
    """
    try:
        from app.services.sarvam_service import text_to_speech
        logger.info(f"Generating TTS for sequence {seq}: '{text}'")

        tts_result = await text_to_speech(text)

        if tts_result.audios:
            base64_audio = tts_result.audios[0]
            await client_ws.send_json({
                "event": "audio",
                "audio": base64_audio,
                "seq": seq,
                "text": text
            })
        else:
            logger.error(f"Sarvam TTS returned no audio for sequence {seq}")

    except asyncio.CancelledError:
        logger.info(f"TTS task {seq} was cancelled")
    except Exception as e:
        logger.error(f"Error in call_tts_and_send for sequence {seq}: {str(e)}")


async def run_groq_and_tts(session_id: str, user_message: str, client_ws: WebSocket, active_tasks: list):
    """
    Streams tokens from Groq LLM, sends tokens to client, chunks sentences,
    triggers parallel TTS, and saves final transcript history.
    """
    try:
        from groq import AsyncGroq
        from app.services.memory_service import get_conversation_history, save_message

        memory = get_conversation_history(session_id, limit=20)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful voice assistant. "
                    "Keep your responses extremely short, conversational, and direct. "
                    "Use simple, brief sentences (under 10 words each). "
                    "Separate distinct ideas or clauses with periods or question marks immediately "
                    "so the speech generation begins instantly. "
                    "Keep the entire response under 2 sentences."
                )
            }
        ] + memory + [
            {
                "role": "user",
                "content": user_message
            }
        ]

        groq_client = AsyncGroq(api_key=GROQ_API_KEY)
        logger.info(f"Starting Groq stream for session: {session_id}")

        stream = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.7,
            max_tokens=60,
            stream=True
        )

        sentence_buffer = ""
        full_ai_response = ""
        seq = 0

        async for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            if not token:
                continue

            full_ai_response += token
            # Stream raw text token to client immediately
            await client_ws.send_json({
                "event": "text_stream",
                "text": token
            })

            sentence_buffer += token

            # Split on sentence boundary indicators
            if any(char in sentence_buffer for char in [".", "?", "!"]):
                last_ending_idx = -1
                for i, c in enumerate(sentence_buffer):
                    if c in [".", "?", "!"]:
                        last_ending_idx = i

                if last_ending_idx != -1:
                    sentence = sentence_buffer[:last_ending_idx + 1].strip()
                    sentence_buffer = sentence_buffer[last_ending_idx + 1:]

                    if len(sentence) > 2:
                        seq += 1
                        task = asyncio.create_task(
                            call_tts_and_send(sentence, seq, client_ws)
                        )
                        active_tasks.append(task)

        # Flush any remaining text in the buffer
        remaining = sentence_buffer.strip()
        if remaining:
            seq += 1
            task = asyncio.create_task(
                call_tts_and_send(remaining, seq, client_ws)
            )
            active_tasks.append(task)

        # Send total sequence count to browser
        await client_ws.send_json({
            "event": "generation_complete",
            "total_seq": seq
        })

        # Persist conversation
        save_message(session_id, "user", user_message)
        save_message(session_id, "assistant", full_ai_response)
        logger.info(f"Completed Groq stream for session: {session_id}")

    except asyncio.CancelledError:
        logger.info("Groq stream completion task cancelled")
    except Exception as e:
        logger.error(f"Error in run_groq_and_tts: {str(e)}")
        try:
            await client_ws.send_json({
                "event": "error",
                "message": "Failed to complete AI response generation"
            })
        except Exception:
            pass


@router.websocket("/ws/stream-voice")
async def websocket_stream_voice(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to /ws/stream-voice WebSocket")

    session_id = None
    groq_task = None
    active_tts_tasks = []
    audio_buffer = bytearray()

    try:
        while True:
            # Handle incoming WebSocket frame (either JSON text or binary audio PCM)
            message = await websocket.receive()

            if message.get("text") is not None:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    logger.warning("Ignoring malformed stream voice WebSocket JSON message")
                    await websocket.send_json({
                        "event": "error",
                        "message": "Invalid WebSocket message"
                    })
                    continue

                event = data.get("event")

                if event == "start":
                    session_id = resolve_session_id(data.get("session_id"))
                    logger.info(f"Initialized stream voice session: {session_id}")

                    # Cancel any existing tasks
                    if groq_task and not groq_task.done():
                        groq_task.cancel()
                    for t in active_tts_tasks:
                        if not t.done():
                            t.cancel()
                    active_tts_tasks.clear()

                    audio_buffer.clear()

                elif event == "stop":
                    logger.info("Received stop event from client. Finalizing STT.")

                    if not audio_buffer:
                        logger.warning("Empty audio buffer received in stop event")
                        await websocket.send_json({
                            "event": "error",
                            "message": "No speech detected"
                        })
                        continue

                    # Prepend WAV header to the accumulated 16kHz PCM audio
                    from app.services.sarvam_service import speech_to_text
                    import io
                    import wave

                    wav_io = io.BytesIO()
                    with wave.open(wav_io, 'wb') as wav_file:
                        wav_file.setnchannels(1)
                        wav_file.setsampwidth(2)      # 16-bit
                        wav_file.setframerate(16000)  # 16kHz
                        wav_file.writeframes(bytes(audio_buffer))

                    wav_bytes = wav_io.getvalue()
                    audio_buffer.clear()

                    # Inform client we are transcribing
                    await websocket.send_json({
                        "event": "transcript",
                        "text": "Transcribing..."
                    })

                    try:
                        stt_result = await speech_to_text(
                            wav_bytes,
                            "recording.wav",
                            "audio/wav"
                        )
                        user_text = stt_result.transcript.strip()
                    except Exception as stt_err:
                        logger.error(f"STT error: {str(stt_err)}")
                        await websocket.send_json({
                            "event": "error",
                            "message": "Speech transcription failed"
                        })
                        continue

                    logger.info(f"Speech transcription complete: '{user_text}'")

                    if not user_text:
                        await websocket.send_json({
                            "event": "error",
                            "message": "No speech detected"
                        })
                        continue

                    # Send the finalized transcript to client
                    await websocket.send_json({
                        "event": "transcript",
                        "text": user_text
                    })

                    # Cancel old generation tasks if any
                    if groq_task and not groq_task.done():
                        groq_task.cancel()
                    for t in active_tts_tasks:
                        if not t.done():
                            t.cancel()
                    active_tts_tasks.clear()

                    # Run LLM + TTS pipeline in background task
                    groq_task = asyncio.create_task(
                        run_groq_and_tts(session_id, user_text, websocket, active_tts_tasks)
                    )

                elif event == "interrupt":
                    logger.info("Received interrupt event from client. Stopping speech and generation.")

                    if groq_task and not groq_task.done():
                        groq_task.cancel()
                    for t in active_tts_tasks:
                        if not t.done():
                            t.cancel()
                    active_tts_tasks.clear()
                    audio_buffer.clear()

                    await websocket.send_json({"event": "interrupted"})

                else:
                    logger.warning(f"Ignoring unknown stream voice event: {event}")
                    await websocket.send_json({
                        "event": "error",
                        "message": "Unknown WebSocket event"
                    })

            elif message.get("bytes") is not None:
                # Binary frame representing microphone PCM audio chunk
                pcm_chunk = message["bytes"]
                audio_buffer.extend(pcm_chunk)

    except WebSocketDisconnect:
        logger.info("Client disconnected from /ws/stream-voice WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error in stream handler: {str(e)}")
    finally:
        # Final cleanup on socket close
        if groq_task and not groq_task.done():
            groq_task.cancel()
        for t in active_tts_tasks:
            if not t.done():
                t.cancel()
