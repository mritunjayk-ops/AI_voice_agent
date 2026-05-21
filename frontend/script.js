const micButton = document.getElementById("micButton");
const stopSpeakingButton = document.getElementById("stopSpeakingButton");
const statusText = document.getElementById("status");
const statusDot = document.getElementById("statusDot");
const centerStatus = document.getElementById("centerStatus");
const chatMessages = document.getElementById("chatMessages");
const emptyConversation = document.getElementById("emptyConversation");

// Mode & Custom Element Bindings
const modeToggle = document.getElementById("modeToggle");
const labelPtt = document.getElementById("labelPtt");
const labelStream = document.getElementById("labelStream");
const waveformCanvas = document.getElementById("waveformCanvas");
const captionsContainer = document.getElementById("captionsContainer");
const liveCaptions = document.getElementById("liveCaptions");
const instructionsText = document.getElementById("instructionsText");

const SESSION_STORAGE_KEY = "ai_voice_agent_session_id";

// State for Push-to-Talk (PTT) Mode
let mediaRecorder;
let mediaStream = null;
let audioChunks = [];
let recordingMimeType = "";
let currentAudio = null;
let currentAudioUrl = null;
let statusTimers = [];

// State for Streaming Mode
let isStreamMode = false;
let isStreaming = false;
let websocket = null;
let streamAudioContext = null;
let streamSource = null;
let streamProcessor = null;
let streamAnalyser = null;
let visualizerAnimationId = null;

// State for Visualizer & Transcript Tracking
let isVisualizing = false;
let streamingUserTranscript = "";

// Playback Queue for Streaming
let receivedAudioBuffers = {};
let expectedSeq = 1;
let totalSeq = null;
let isPlayingAudio = false;
let currentSourceNode = null;
let playbackAudioContext = null;
let playbackGenerationId = 0;
let activeAiMessageBody = null;
let streamingUserMessageAdded = false;


// ==========================================================================
// SESSION MANAGEMENT
// ==========================================================================

function createBrowserSessionId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
        return window.crypto.randomUUID();
    }
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

function getSessionId() {
    try {
        let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
        if (!sessionId) {
            sessionId = createBrowserSessionId();
            localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
        }
        return sessionId;
    } catch (error) {
        console.warn(error);
        return createBrowserSessionId();
    }
}

function storeSessionId(sessionId) {
    if (!sessionId) return;
    try {
        localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
    } catch (error) {
        console.warn(error);
    }
}


// ==========================================================================
// STATE & STATUS HELPERS
// ==========================================================================

function setStatus(message, state) {
    statusText.innerText = message;
    statusDot.className = `status-dot ${state}`;
    micButton.classList.toggle("listening", state === "listening");
    if (centerStatus) {
        centerStatus.innerText = message;
        centerStatus.className = `center-status-text ${state}`;
    }
}

function clearStatusTimers() {
    statusTimers.forEach((timerId) => {
        clearTimeout(timerId);
    });
    statusTimers = [];
}

function scheduleProcessingStatuses() {
    clearStatusTimers();
    setStatus("Thinking", "thinking");
}

// mediaStream tracks cleanup is handled by stopStreamingAudioCapture

function scrollConversationToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}


// ==========================================================================
// CHAT UI DISPLAY
// ==========================================================================

function addMessage(role, text) {
    if (!text) return;
    emptyConversation.hidden = true;

    const message = document.createElement("div");
    message.className = `message ${role}`;

    const label = document.createElement("div");
    label.className = "message-label";
    label.innerText = role === "user" ? "You" : "AI";

    const body = document.createElement("div");
    body.innerText = text;

    message.appendChild(label);
    message.appendChild(body);
    chatMessages.appendChild(message);

    scrollConversationToBottom();
}

function appendAiToken(token) {
    if (!token) return;
    emptyConversation.hidden = true;

    if (!activeAiMessageBody) {
        const message = document.createElement("div");
        message.className = "message ai";

        const label = document.createElement("div");
        label.className = "message-label";
        label.innerText = "AI";

        const body = document.createElement("div");
        body.innerText = "";

        message.appendChild(label);
        message.appendChild(body);
        chatMessages.appendChild(message);

        activeAiMessageBody = body;
    }

    activeAiMessageBody.innerText += token;
    scrollConversationToBottom();
}

function readResponseHeader(response, headerName) {
    const value = response.headers.get(headerName);
    if (!value) return "";
    try {
        return decodeURIComponent(value);
    } catch (error) {
        console.warn(error);
        return value;
    }
}


// ==========================================================================
// AUDIO PLAYBACK & QUEUE MANAGEMENT
// ==========================================================================

function resetStreamingAudioPlayback() {
    playbackGenerationId += 1;
    micButton.classList.remove("speaking");
    if (currentSourceNode) {
        try {
            currentSourceNode.stop();
        } catch (e) {}
        currentSourceNode = null;
    }

    if (playbackAudioContext) {
        try {
            playbackAudioContext.close().catch(() => {});
        } catch (e) {}
        playbackAudioContext = null;
    }

    receivedAudioBuffers = {};
    expectedSeq = 1;
    totalSeq = null;
    isPlayingAudio = false;
    stopSpeakingButton.disabled = true;
    activeAiMessageBody = null; // Reset AI message body so the next response starts a new bubble
}

function resetAudioPlayback(statusMessage = "Ready") {
    micButton.classList.remove("speaking");
    // 1. Stop PTT audio
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.onended = null;
        currentAudio.onerror = null;
        currentAudio.removeAttribute("src");
        currentAudio.load();
        currentAudio = null;
    }

    if (currentAudioUrl) {
        URL.revokeObjectURL(currentAudioUrl);
        currentAudioUrl = null;
    }

    // 2. Stop streaming audio
    resetStreamingAudioPlayback();

    setStatus(
        statusMessage,
        statusMessage === "Ready" ? "ready" : "error"
    );
}

function base64ToArrayBuffer(base64) {
    var binaryString = window.atob(base64);
    var len = binaryString.length;
    var bytes = new Uint8Array(len);
    for (var i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
}

async function queueAudioFrame(base64Audio, seq, text) {
    const generationId = playbackGenerationId;

    try {
        if (!playbackAudioContext || playbackAudioContext.state === "closed") {
            playbackAudioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        const arrayBuffer = base64ToArrayBuffer(base64Audio);
        const audioBuffer = await playbackAudioContext.decodeAudioData(arrayBuffer);

        if (generationId !== playbackGenerationId) {
            return;
        }

        receivedAudioBuffers[seq] = { buffer: audioBuffer, text: text };
        playStreamingQueue();
    } catch (e) {
        console.error(`Error decoding audio sequence ${seq}:`, e);
    }
}

function playStreamingQueue() {
    if (isPlayingAudio) return;

    const nextChunk = receivedAudioBuffers[expectedSeq];
    if (!nextChunk) return; // Out of sequence or not yet received

    isPlayingAudio = true;
    setStatus("Speaking", "speaking");
    micButton.classList.add("speaking");
    stopSpeakingButton.disabled = false;

    const { buffer, text } = nextChunk;
    const ctx = playbackAudioContext;
    if (!ctx || ctx.state === "closed") {
        isPlayingAudio = false;
        return;
    }

    if (text) {
        appendAiToken(text + " ");
    }

    const sourceNode = ctx.createBufferSource();
    sourceNode.buffer = buffer;
    sourceNode.connect(ctx.destination);

    currentSourceNode = sourceNode;

    sourceNode.onended = () => {
        if (!isPlayingAudio) return; // Interrupted

        isPlayingAudio = false;
        currentSourceNode = null;

        delete receivedAudioBuffers[expectedSeq];
        expectedSeq++;

        checkStreamingQueueFinished();
        playStreamingQueue();
    };

    sourceNode.start(0);
}

function checkStreamingQueueFinished() {
    if (totalSeq !== null && expectedSeq > totalSeq && !isPlayingAudio) {
        console.log("Audio streaming queue completely empty.");
        resetStreamingAudioPlayback();
        setStatus("Ready", "ready");
        setTimeout(() => {
            if (!isStreaming && !isPlayingAudio) {
                captionsContainer.classList.add("hidden");
            }
        }, 4000);
    }
}


// ==========================================================================
// DOWNSAMPLING HELPERS (Float32 to Int16 PCM)
// ==========================================================================

function downsampleAndConvert(buffer, inputSampleRate, outputSampleRate) {
    if (outputSampleRate === inputSampleRate) {
        return convertFloat32ToInt16(buffer);
    }
    var sampleRateRatio = inputSampleRate / outputSampleRate;
    var newLength = Math.round(buffer.length / sampleRateRatio);
    var result = new Float32Array(newLength);
    var offsetResult = 0;
    var offsetBuffer = 0;
    while (offsetResult < result.length) {
        var nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
        var accum = 0, count = 0;
        for (var i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
            accum += buffer[i];
            count++;
        }
        result[offsetResult] = count > 0 ? accum / count : 0;
        offsetResult++;
        offsetBuffer = nextOffsetBuffer;
    }
    return convertFloat32ToInt16(result);
}

function convertFloat32ToInt16(buffer) {
    var l = buffer.length;
    var buf = new Int16Array(l);
    while (l--) {
        buf[l] = Math.min(1, Math.max(-1, buffer[l])) * 0x7FFF;
    }
    return buf.buffer;
}


// ==========================================================================
// VISUALIZER DRAW LOOP
// ==========================================================================

function startVisualizerAnimation() {
    const canvasContext = waveformCanvas.getContext("2d");
    const bufferLength = streamAnalyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
        if (!isVisualizing || !streamAnalyser) return;

        visualizerAnimationId = requestAnimationFrame(draw);
        streamAnalyser.getByteTimeDomainData(dataArray);

        canvasContext.fillStyle = "rgba(7, 21, 47, 0.4)";
        canvasContext.fillRect(0, 0, waveformCanvas.width, waveformCanvas.height);

        canvasContext.lineWidth = 3;
        const gradient = canvasContext.createLinearGradient(0, 0, waveformCanvas.width, 0);
        gradient.addColorStop(0, "#1e88e5");
        gradient.addColorStop(0.5, "#4fc3f7");
        gradient.addColorStop(1, "#22c55e");
        canvasContext.strokeStyle = gradient;

        canvasContext.beginPath();
        const sliceWidth = waveformCanvas.width * 1.0 / bufferLength;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i] / 128.0;
            const y = (v * waveformCanvas.height) / 2;

            if (i === 0) {
                canvasContext.moveTo(x, y);
            } else {
                canvasContext.lineTo(x, y);
            }
            x += sliceWidth;
        }

        canvasContext.lineTo(waveformCanvas.width, waveformCanvas.height / 2);
        canvasContext.stroke();
    }

    draw();
}


// ==========================================================================
// PUSH-TO-TALK (PTT) ENGINE
// ==========================================================================

async function startRecording() {
    if (isStreamMode) return; // Handled by Click listeners

    try {
        clearStatusTimers();
        resetAudioPlayback();

        captionsContainer.classList.remove("hidden");
        liveCaptions.innerHTML = "<span class='captions-status'>🎙️ Listening...</span> Keep holding the button and speak.";

        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });
        streamSource = mediaStream;

        // Initialize Audio Context for live waveform visualizer in PTT mode
        try {
            streamAudioContext = new (window.AudioContext || window.webkitAudioContext)();
            const sourceNode = streamAudioContext.createMediaStreamSource(mediaStream);
            streamAnalyser = streamAudioContext.createAnalyser();
            streamAnalyser.fftSize = 256;
            sourceNode.connect(streamAnalyser);
            isVisualizing = true;
            startVisualizerAnimation();
        } catch (visError) {
            console.warn("Visualizer initialization failed:", visError);
        }

        audioChunks = [];
        recordingMimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "";

        mediaRecorder = new MediaRecorder(
            mediaStream,
            recordingMimeType ? { mimeType: recordingMimeType } : undefined
        );

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            isVisualizing = false;
            stopStreamingAudioCapture();
            scheduleProcessingStatuses();
            liveCaptions.innerHTML = "<span class='captions-status thinking'>🤔 Thinking...</span> Processing speech and preparing reply.";

            try {
                const audioBlob = new Blob(
                    audioChunks,
                    recordingMimeType ? { type: recordingMimeType } : undefined
                );

                const formData = new FormData();
                formData.append(
                    "file",
                    audioBlob,
                    recordingMimeType === "audio/webm" ? "recording.webm" : "recording"
                );

                formData.append("session_id", getSessionId());

                const response = await fetch("http://127.0.0.1:8000/voice-chat", {
                    method: "POST",
                    body: formData
                });

                if (!response.ok) {
                    throw new Error("Backend request failed");
                }

                clearStatusTimers();

                const userText = readResponseHeader(response, "X-User-Transcript");
                const aiText = readResponseHeader(response, "X-AI-Response");

                storeSessionId(readResponseHeader(response, "X-Session-ID"));

                addMessage("user", userText || "Voice message");
                addMessage("ai", aiText || "AI response generated as speech.");

                // Show transcript in captions container
                liveCaptions.innerHTML = `<strong>You:</strong> "${userText || 'Voice message'}"<br><br><strong>AI:</strong> ${aiText || 'AI response'}`;

                const responseBlob = await response.blob();
                const audioUrl = URL.createObjectURL(responseBlob);

                currentAudioUrl = audioUrl;
                currentAudio = new Audio(audioUrl);

                stopSpeakingButton.disabled = false;
                setStatus("Speaking", "speaking");
                micButton.classList.add("speaking"); // Pulse mic button purple

                currentAudio.onended = () => {
                    resetAudioPlayback("Ready");
                };

                currentAudio.onerror = () => {
                    resetAudioPlayback("Audio playback failed");
                };

                try {
                    await currentAudio.play();
                } catch (playError) {
                    if (playError.name === "AbortError") return;
                    throw playError;
                }

            } catch (error) {
                console.error(error);
                clearStatusTimers();
                resetAudioPlayback("Error occurred");
                liveCaptions.innerHTML = `<span class='captions-status error'>❌ Error</span> ${error.message}`;
            }
        };

        mediaRecorder.start();
        setStatus("Listening", "listening");

    } catch (error) {
        console.error(error);
        isVisualizing = false;
        stopStreamingAudioCapture();
        setStatus("Microphone access denied", "error");
        liveCaptions.innerHTML = "<span class='captions-status error'>❌ Error</span> Microphone access denied.";
    }
}

function stopRecording() {
    if (isStreamMode) return;
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }
}


// ==========================================================================
// REAL-TIME WEBSOCKET STREAMING ENGINE
// ==========================================================================

async function startStreamingSession() {
    try {
        resetAudioPlayback();

        captionsContainer.classList.remove("hidden");
        liveCaptions.innerHTML = "<span class='captions-status'>🎙️ Listening...</span> Speak now.";
        activeAiMessageBody = null;
        streamingUserTranscript = "";
        streamingUserMessageAdded = false;

        websocket = new WebSocket("ws://127.0.0.1:8000/ws/stream-voice");

        websocket.onopen = async () => {
            console.log("Streaming WebSocket connected.");
            websocket.send(JSON.stringify({
                event: "start",
                session_id: getSessionId()
            }));

            await startStreamingAudioCapture();
        };

        websocket.onmessage = async (event) => {
            let data;
            try {
                data = JSON.parse(event.data);
            } catch (parseError) {
                console.warn("Ignoring malformed WebSocket message:", parseError);
                return;
            }

            if (data.event === "transcript") {
                streamingUserTranscript = (data.text || "").trim();
                if (
                    streamingUserTranscript &&
                    streamingUserTranscript !== "Transcribing..." &&
                    !streamingUserMessageAdded
                ) {
                    addMessage("user", streamingUserTranscript);
                    streamingUserMessageAdded = true;
                }
                liveCaptions.innerHTML = `<strong>You:</strong> "${streamingUserTranscript}"`;
            } else if (data.event === "text_stream") {
                // Ignore raw token streaming in the chat history panel to print sentence-by-sentence as it speaks
                if (activeAiMessageBody) {
                    const userPart = streamingUserTranscript ? `<strong>You:</strong> "${streamingUserTranscript}"<br><br>` : "";
                    liveCaptions.innerHTML = `${userPart}<strong>AI:</strong> ${activeAiMessageBody.innerText}`;
                }
            } else if (data.event === "audio") {
                await queueAudioFrame(data.audio, data.seq, data.text);
            } else if (data.event === "generation_complete") {
                totalSeq = data.total_seq;
                checkStreamingQueueFinished();
            } else if (data.event === "error") {
                console.error("Server error:", data.message);
                setStatus(data.message, "error");
                liveCaptions.innerHTML = `<span class='captions-status error'>❌ Error</span> ${data.message}`;
                stopStreamingSession(true);
            } else if (data.event === "interrupted") {
                console.log("Server confirms stream interrupted.");
            }
        };

        websocket.onclose = () => {
            console.log("Streaming WebSocket closed.");
            isStreaming = false;
            stopStreamingAudioCapture();
            micButton.classList.remove("listening");
        };

        websocket.onerror = (err) => {
            console.error("Streaming WebSocket error:", err);
            setStatus("Connection error", "error");
            liveCaptions.innerHTML = "<span class='captions-status error'>❌ Error</span> Connection error.";
        };

        isStreaming = true;
        setStatus("Listening", "listening");

    } catch (e) {
        console.error("Failed to start stream session:", e);
        setStatus("Connection failed", "error");
        liveCaptions.innerHTML = "<span class='captions-status error'>❌ Error</span> Connection failed.";
    }
}

async function startStreamingAudioCapture() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamSource = stream;

        streamAudioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const sourceNode = streamAudioContext.createMediaStreamSource(stream);

        // Analyser node for rendering waveform on canvas
        streamAnalyser = streamAudioContext.createAnalyser();
        streamAnalyser.fftSize = 256;
        sourceNode.connect(streamAnalyser);

        // Script Processor for downsampling and streaming PCM chunks
        streamProcessor = streamAudioContext.createScriptProcessor(4096, 1, 1);
        const inputSampleRate = streamAudioContext.sampleRate;

        streamProcessor.onaudioprocess = (e) => {
            if (!isStreaming || !websocket || websocket.readyState !== WebSocket.OPEN) return;

            const inputData = e.inputBuffer.getChannelData(0);
            const pcmBuffer = downsampleAndConvert(inputData, inputSampleRate, 16000);
            websocket.send(pcmBuffer);
        };

        sourceNode.connect(streamProcessor);
        streamProcessor.connect(streamAudioContext.destination);

        isVisualizing = true;
        startVisualizerAnimation();

    } catch (err) {
        console.error("Failed to start mic capture:", err);
        setStatus("Microphone access denied", "error");
        stopStreamingSession(true);
    }
}

function stopStreamingAudioCapture() {
    isVisualizing = false;
    if (visualizerAnimationId) {
        cancelAnimationFrame(visualizerAnimationId);
        visualizerAnimationId = null;
    }

    const canvasContext = waveformCanvas.getContext("2d");
    canvasContext.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);

    if (streamProcessor) {
        streamProcessor.disconnect();
        streamProcessor = null;
    }

    if (streamSource) {
        streamSource.getTracks().forEach(track => track.stop());
        streamSource = null;
    }

    if (streamAudioContext) {
        try {
            streamAudioContext.close().catch(() => {});
        } catch (e) {}
        streamAudioContext = null;
    }

    streamAnalyser = null;
}

function stopStreamingSession(force = false) {
    if (!isStreaming) return;

    isStreaming = false;
    stopStreamingAudioCapture();
    micButton.classList.remove("listening");

    if (websocket && websocket.readyState === WebSocket.OPEN) {
        if (!force) {
            websocket.send(JSON.stringify({ event: "stop" }));
            setStatus("Thinking", "thinking");
        } else {
            websocket.close();
        }
    }
}

function interruptStreamingSession() {
    resetStreamingAudioPlayback();

    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ event: "interrupt" }));
    }

    setStatus("Ready", "ready");
    liveCaptions.innerHTML = "<span class='captions-status thinking'>⏹️ Interrupted</span> Session was stopped.";
}


// ==========================================================================
// EVENT LISTENERS & INITIALIZATION
// ==========================================================================

// Mode toggle switch
modeToggle.addEventListener("change", () => {
    isStreamMode = modeToggle.checked;

    // Toggle active classes on labels
    labelPtt.classList.toggle("active", !isStreamMode);
    labelStream.classList.toggle("active", isStreamMode);

    // Update instructions
    if (isStreamMode) {
        instructionsText.innerHTML = "Tap the mic button to start speaking.<br>Tap it again to stop.";
    } else {
        instructionsText.innerHTML = "Hold the mic button while speaking.<br>Release it when finished.";
    }

    // Cleanup any active connections/streams
    if (isStreaming) {
        stopStreamingSession(true);
    }
    resetAudioPlayback();
    captionsContainer.classList.add("hidden");
});

// Mic Button Actions
micButton.addEventListener("click", () => {
    if (!isStreamMode) return;

    if (isStreaming) {
        // User finished speaking, stop streaming to get response
        stopStreamingSession();
    } else {
        // User started speaking. If AI is talking, interrupt it first.
        if (isPlayingAudio || currentAudio) {
            interruptStreamingSession();
        }
        startStreamingSession();
    }
});

// PTT mouse/touch events
micButton.addEventListener("mousedown", startRecording);
micButton.addEventListener("mouseup", stopRecording);
micButton.addEventListener("mouseleave", stopRecording);

micButton.addEventListener("touchstart", (event) => {
    event.preventDefault();
    startRecording();
});
micButton.addEventListener("touchend", stopRecording);

// Stop Speaking Button
stopSpeakingButton.addEventListener("click", () => {
    clearStatusTimers();
    if (isStreamMode) {
        interruptStreamingSession();
    } else {
        resetAudioPlayback();
        liveCaptions.innerHTML = "<span class='captions-status thinking'>⏹️ Stopped</span> Playback stopped.";
    }
});
