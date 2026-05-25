# AI Voice Agent

A browser-based conversational voice assistant built with FastAPI, Groq, and Sarvam AI speech APIs.

The project captures microphone input in the browser, sends the recorded audio to a FastAPI backend, transcribes speech with Sarvam, generates a short conversational response using Groq, converts the response back to speech with Sarvam, and plays the generated audio in the browser.

This is an evolving AI assistant system focused on practical voice interaction, modular backend services, and a clean frontend-to-backend voice pipeline.

## Problem Statement

Most assistant demos start with typed chat, but many real assistant workflows are voice-first. The engineering challenge is coordinating browser recording, speech-to-text, LLM response generation, text-to-speech, audio playback, interruption handling, and observability in one stable request-response pipeline.

This project focuses on that orchestration layer: making the system usable from the browser while keeping the backend modular enough to improve providers, latency, and interaction behavior over time.

## Why I Built This

I built this project to explore how a practical Voice AI assistant can be assembled from production-style components without overcomplicating the architecture. The goal was to demonstrate a working conversational loop, clear service boundaries, observable pipeline stages, and a minimal voice-first frontend suitable for iteration.

## Features

- **Dual Interaction Modes**: Push-to-Talk (HTTP/WAV) and Real-time Streaming (WebSockets).
- **LangChain-Powered Conversational Agent**: Equipped with tools to manage notes, todos, search conversation history, search the internet, and perform calculations.
- **Internet Search Tooling**: Uses Tavily search for current web information and a direct Bitcoin price lookup for price-specific queries.
- **WebSocket Streaming Mode**: Real-time continuous speech streaming from browser to backend.
- **Dynamic Waveform Visualization**: Live visual feedback on both audio input and output using HTML5 Canvas.
- **Real-Time Live Captions**: Transcribes incoming streaming speech in real-time on the UI.
- **Persistent SQLite Memory**: Uses a local SQLite database (`app.db`) to store session conversations, notes, and task lists.
- **Browser Audio Playback**: Plays generated speech audio responses with an interruption queue.
- **Stop Speaking Control**: Resets active audio playback and cancels server-side agent runs.
- **Observability & Logging**: Structured pipeline logs detailing STT, LLM, and TTS latency metrics.

## Demo Section

### Frontend UI

![Frontend UI](screenshots/frontend-ui.png)

### Pipeline Logs

![Pipeline Logs](screenshots/terminal-logs.png)

### Loom Demo

https://www.loom.com/share/aa14ca5466e84cf7a381dd44fb9e5695

## Architecture Flow

### Push-to-Talk Mode (HTTP)
```text
Browser microphone
    -> frontend/script.js
    -> POST /voice-chat
    -> FastAPI backend
    -> Sarvam Speech-to-Text
    -> Groq / LangChain Agent (with tools, internet search, and SQLite memory)
    -> Sarvam Text-to-Speech
    -> WAV audio response
    -> Browser playback
```

### Real-Time Streaming Mode (WebSockets)
```text
Browser microphone
    -> WebSocket /ws/stream-voice
    -> FastAPI backend (accumulates PCM chunk)
    -> Sarvam STT (on voice stop)
    -> Streams tokens from Groq
    -> Chunks sentences -> Sarvam TTS (parallel)
    -> Base64 WAV chunks -> Browser queue
    -> Sequential audio playback
```

## Workflow Comparison

| Area | Traditional Chat Workflow | This Voice-First AI System |
| --- | --- | --- |
| User input | Typed text message | Browser microphone recording |
| Input processing | Direct text payload | Audio upload followed by speech-to-text |
| Model interaction | LLM receives text | LLM receives transcribed speech |
| Output | Text response in chat UI | Generated speech audio played in browser |
| Interaction style | Keyboard-first | Voice-first with optional conversation visibility |
| Interruption | Usually not needed | Stop Speaking control resets active playback |
| Observability | Often request-level logs only | Stage-level logs for STT, LLM, TTS, and total latency |

## Observability & Metrics

The backend logs structured pipeline events through the project logger. Each `/voice-chat` request receives a `request_id`, making it easier to follow the orchestration flow across STT, Groq, TTS, and final response generation.

Example observed timings from `logs/app.log`:

| Metric | Observed latency |
| --- | ---: |
| STT latency | 2518.09 ms |
| LLM latency | 350.86 ms |
| TTS latency | 2351.95 ms |
| Total pipeline latency | 5228.98 ms |

The logs are intended to support demo review, performance evaluation, and future optimization work without requiring a separate observability stack.

## Tech Stack

### Backend

- Python
- FastAPI
- Uvicorn
- HTTPX
- Pydantic
- python-dotenv
- LangChain / langchain-groq (Agent Framework)
- SQLite3 (Persistent database)

### AI Services

- Groq LLM API (Llama models)
- Sarvam AI Speech-to-Text
- Sarvam AI Text-to-Speech
- Tavily Search API
- CoinGecko price API for Bitcoin price lookups

### Frontend

- HTML
- CSS
- JavaScript
- Browser MediaRecorder API
- Browser Audio API & WebSockets
- HTML5 Canvas API (Waveform visualizer)

## Folder Structure

```text
ai_voice_agent/
|-- app/
|   |-- agents/
|   |   `-- voice_agent.py          # LangChain voice assistant definition
|   |-- api/
|   |   `-- routes/
|   |       |-- chat_routes.py      # Plain chat route with memory
|   |       |-- tts_routes.py       # Direct text-to-speech route (unmounted)
|   |       |-- voice_routes.py     # Push-to-Talk audio route
|   |       `-- websocket_routes.py # WebSocket real-time audio & streaming route
|   |-- core/
|   |   |-- config.py               # Env configuration loader
|   |   `-- logger.py               # Application-wide structured logging
|   |-- models/
|   |   `-- chat_models.py          # Pydantic schemas
|   |-- services/
|   |   |-- agent_service.py        # LangChain agent wrapper & execution
|   |   |-- cache_service.py        # Simple cache management
|   |   |-- groq_service.py         # Direct Groq completions & fallback routing
|   |   |-- memory_service.py       # SQLite database initialization & message saving
|   |   |-- sarvam_service.py       # Sarvam STT & TTS HTTP clients
|   |   |-- session_service.py      # Session ID generators and validation
|   |   `-- tool_storage_service.py # SQLite interfaces for agent tools
|   |-- tools/
|   |   |-- conversation_tools.py   # Search conversation history tool
|   |   |-- notes_tools.py          # Save, list, and search notes tools
|   |   |-- search_tools.py         # Internet search and price lookup tools
|   |   |-- todo_tools.py           # Add, list, and complete todo tools
|   |   `-- utility_tools.py        # Calculator & clock utility tools
|   `-- utils/
|-- frontend/
|   |-- index.html                  # Responsive UI layout
|   |-- script.js                   # Handles mic, WebSockets, Canvas, PTT, and audio player
|   `-- style.css                   # Custom modern styles
|-- generated_audio/                # Local cache directory for generated TTS audio files
|-- logs/                           # Local app logs
|-- scratch/                        # Diagnostic and test scripts
|   |-- check_db.py                 # SQLite verification script
|   |-- test_sarvam_ws.py           # Sarvam WebSocket client test
|   `-- test_voice_ws_end_to_end.py # Voice WebSocket test script
|-- temp_audio/                     # Temporary upload directory
|-- app.db                          # SQLite database containing app state & memory
|-- main.py                         # FastAPI server initialization and routing
|-- requirements.txt                # Python dependencies
`-- README.md                       # Documentation
```

Note: `chat_routes.py`, `voice_routes.py`, and `websocket_routes.py` are mounted in `main.py`. `tts_routes.py` is present for direct TTS testing but is not currently mounted.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/mritunjayk-ops/AI_voice_agent.git
cd AI_voice_agent
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
TAVILY_API_KEY=your_tavily_api_key
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

### 1. Start the Backend & Frontend
* Make sure your backend and frontend servers are running (see Setup instructions).
* Open the application in your browser (typically `http://localhost:5500`).

### 2. Push-to-Talk (PTT) Mode
1. Ensure the mode toggle is set to **Push-to-Talk**.
2. Click and **hold** the microphone button while speaking.
3. **Release** the button when you are done.
4. The system transcribes your audio, triggers the LangChain agent or deterministic search route (fetching database notes/todos, executing tools, or searching the internet when requested), generates TTS audio, and streams it back.
5. The browser plays the generated audio response.
6. Click **Stop Speaking** to interrupt current audio playback at any point.

Example search prompts:

```text
Search the internet for the latest AI news today.
What is the current Bitcoin price?
Give me polity questions from UPSC prelims 2026 paper.
```

### 3. Real-Time Streaming Mode
1. Toggle the switch to **Streaming**.
2. Click the microphone button once to connect to the `/ws/stream-voice` WebSocket and start streaming audio.
3. Speak into the microphone; you will see the **Waveform Visualizer** capture your voice, and live captions will display the incoming transcription in real-time.
4. Stop speaking or click the mic button again to finalize input. The agent will process your query, and streaming TTS chunks will play sequentially.
5. If the agent starts speaking and you wish to interrupt it, either speak again or click **Stop Speaking** to cancel background tasks and reset the state.

## API Endpoints

### `GET /health`

Returns a basic health check response.

### `POST /chat`

Accepts a text message and returns a Groq-generated response with session memory.

### `POST /voice-chat`

Accepts an uploaded audio file from the browser and returns generated speech audio.

Pipeline:
```text
audio file -> Sarvam STT -> Groq / Agent -> Sarvam TTS -> audio/wav
```
The response remains playable audio. The backend also exposes transcript and AI response text through response headers so the lightweight conversation panel can render the exchange without changing the core audio contract.

### `GET /voice-test`

Runs a hardcoded voice test prompt through Groq / Agent and Sarvam TTS, then returns a generated WAV file.

### `WebSocket /ws/chat`

A simple text-based WebSocket endpoint to exchange text messages with conversational memory.

### `WebSocket /ws/stream-voice`

An event-driven audio streaming WebSocket.
* **Input events**: `start` (sends `session_id`), `stop` (completes speech stream and triggers agent STT -> LLM -> TTS), `interrupt` (stops speaking and cancels active tasks).
* **Input bytes**: Raw PCM 16kHz audio chunks from mic.
* **Output events**: `transcript` (updates live transcription), `text_stream` (streams agent response tokens), `audio` (Base64 WAV chunks), `generation_complete`, `interrupted`, and `error`.

## AI-Native Development Workflow

The project includes a `.cursorrules` file to guide collaborative AI-assisted development. Its purpose is to keep future changes aligned with the current architecture and product direction:

- preserve route, service, frontend, and logging boundaries
- avoid unnecessary rewrites or speculative abstractions
- keep the frontend voice-first and minimal
- preserve the `/voice-chat` audio contract and interruption behavior
- maintain structured logging and latency metrics
- prevent hardcoded secrets or provider credentials

These rules are intended to make AI-native iteration safer by giving coding assistants explicit project constraints before they modify the codebase.

## Current Limitations

- **Interruption in HTTP Mode**: In Push-to-Talk (HTTP) mode, Stop Speaking only halts browser audio playback; any in-progress API calls on the backend will finish execution. (WebSocket Streaming Mode does support proper task cancellation).
- **Search Coverage Depends on External Results**: Internet search answers are grounded in Tavily or price API results. If exact source data is unavailable, the assistant should say so rather than inventing details.
- **Session-Scoped SQLite States**: The Notes, Todos, and Memory databases are session-scoped and stored inside `app.db`. Currently, there is no cross-session data merging or authentication.
- **Local Audio Storage**: Generated WAV files are saved locally in the `generated_audio/` folder, which accumulates files over time.
- **Desktop Focus**: The frontend is optimized primarily for desktop browsers (Chrome, Edge, Firefox) that support WebRTC / MediaRecorder APIs.

## Future Roadmap

- **Vector Store Database**: Back long-term agent memory with a vector database (e.g., Chroma, Qdrant) to support semantic search.
- **Authentication**: Add user logins, allowing multi-user isolation of conversations, notes, and tasks.
- **Cloud Deployment**: Configuration files for Docker/Kubernetes and cloud deployment guides (AWS, GCP, or Render).
- **Advanced Interruption Handling**: Enable wake-word detection or full-duplex conversations where the agent stops speaking immediately upon user voice activity detection (VAD).
- **Multi-Agent Systems**: Expand the LangChain agent into a multi-agent team capable of collaborative task execution.

## Author

**Mritunjay Kumar**

AI builder focused on voice agents, applied LLM systems, and practical assistant workflows.
