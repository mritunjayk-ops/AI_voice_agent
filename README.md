# AI Voice Agent

A browser-based conversational voice assistant built with FastAPI, Groq, and Sarvam AI speech APIs.

The project captures microphone input in the browser, sends the recorded audio to a FastAPI backend, transcribes speech with Sarvam, generates a short conversational response using Groq, converts the response back to speech with Sarvam, and plays the generated audio in the browser.

This is an evolving AI assistant system focused on practical voice interaction, modular backend services, and a clean frontend-to-backend voice pipeline.

## Features

- Browser microphone input using the MediaRecorder API
- Speech-to-text transcription through Sarvam AI
- Groq-powered conversational responses
- Short-term conversational memory per session
- Text-to-speech voice replies through Sarvam AI
- Browser audio playback for generated responses
- FastAPI backend with modular route and service layers
- Simple HTML, CSS, and JavaScript frontend

## Architecture Flow

```text
Browser microphone
    -> frontend/script.js
    -> POST /voice-chat
    -> FastAPI backend
    -> Sarvam Speech-to-Text
    -> Groq LLM
    -> Sarvam Text-to-Speech
    -> WAV audio response
    -> Browser playback
```

## Tech Stack

### Backend

- Python
- FastAPI
- Uvicorn
- HTTPX
- Pydantic
- python-dotenv

### AI Services

- Groq LLM API
- Sarvam AI Speech-to-Text
- Sarvam AI Text-to-Speech

### Frontend

- HTML
- CSS
- JavaScript
- Browser MediaRecorder API
- Browser Audio API

## Folder Structure

```text
ai_voice_agent/
|-- app/
|   |-- api/
|   |   `-- routes/
|   |       |-- chat_routes.py
|   |       |-- tts_routes.py
|   |       |-- voice_routes.py
|   |       `-- websocket_routes.py
|   |-- core/
|   |   |-- config.py
|   |   `-- logger.py
|   |-- models/
|   |   `-- chat_models.py
|   |-- services/
|   |   |-- cache_service.py
|   |   |-- groq_service.py
|   |   `-- sarvam_service.py
|   `-- utils/
|-- frontend/
|   |-- index.html
|   |-- script.js
|   `-- style.css
|-- generated_audio/
|-- logs/
|-- temp_audio/
|-- main.py
|-- requirements.txt
`-- README.md
```

Note: `chat_routes.py` and `voice_routes.py` are currently mounted in `main.py`. Other route files are present for earlier or future experiments but are not currently mounted.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd ai_voice_agent
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
SARVAM_API_KEY=your_sarvam_api_key
```

## Running the Application

### Run the Backend

From the project root:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Backend health check:

```text
http://127.0.0.1:8000/health
```

Interactive API docs:

```text
http://127.0.0.1:8000/docs
```

### Run the Frontend

Serve the `frontend/` directory on port `5500`, because CORS is configured for:

```text
http://localhost:5500
http://127.0.0.1:5500
```

One simple option is to use Python's static file server:

```bash
cd frontend
python -m http.server 5500
```

Then open:

```text
http://127.0.0.1:5500
```

You can also use a local development server such as VS Code Live Server, as long as it serves the frontend from port `5500`.

## Usage

1. Start the FastAPI backend.
2. Start the frontend server.
3. Open the frontend in a browser.
4. Hold the microphone button and speak.
5. Release the button to send the recording to the backend.
6. The backend transcribes the audio, generates a Groq response, converts it to speech, and returns a WAV file.
7. The browser plays the generated voice response.

## API Endpoints

### `GET /health`

Returns a basic health check response.

### `POST /chat`

Accepts a text message and returns a Groq-generated response with session memory.

### `POST /voice-chat`

Accepts an uploaded audio file from the browser and returns generated speech audio.

Pipeline:

```text
audio file -> Sarvam STT -> Groq -> Sarvam TTS -> audio/wav
```

### `GET /voice-test`

Runs a hardcoded voice test prompt through Groq and Sarvam TTS, then returns a generated WAV file.

## Current Limitations

- Voice interaction is request-response based, not realtime streaming.
- Interruption handling is basic: the frontend stops current playback when a new recording starts.
- Conversational memory is in-memory only and resets when the backend restarts.
- Generated audio files are stored locally in `generated_audio/`.
- The frontend is intentionally minimal and currently optimized for desktop browser use.
- WebSocket route files exist in the repository, but websocket routes are not mounted in the active FastAPI app.

## Future Roadmap

- Realtime streaming speech-to-text and text-to-speech
- More natural interruption handling while the assistant is speaking
- Long-term memory backed by a persistent database or vector store
- Multi-agent architecture for task planning and tool use
- Stronger frontend states for recording, processing, speaking, and errors
- Authentication and user-specific memory
- Deployment-ready configuration for cloud hosting
- Observability for latency, API failures, and conversation quality

## Author

**Mritunjay Kumar**

AI builder focused on voice agents, applied LLM systems, and practical assistant workflows.
