const micButton = document.getElementById("micButton");
const stopSpeakingButton = document.getElementById("stopSpeakingButton");
const statusText = document.getElementById("status");
const statusDot = document.getElementById("statusDot");
const chatMessages = document.getElementById("chatMessages");
const emptyConversation = document.getElementById("emptyConversation");

let mediaRecorder;
let mediaStream = null;
let audioChunks = [];
let recordingMimeType = "";

let currentAudio = null;
let currentAudioUrl = null;
let statusTimers = [];


function setStatus(message, state) {

    statusText.innerText =
        message;

    statusDot.className =
        `status-dot ${state}`;

    micButton.classList.toggle(
        "listening",
        state === "listening"
    );
}


function clearStatusTimers() {

    statusTimers.forEach((timerId) => {

        clearTimeout(timerId);
    });

    statusTimers = [];
}


function scheduleProcessingStatuses() {

    clearStatusTimers();

    setStatus(
        "Thinking",
        "thinking"
    );
}


function stopMediaStream() {

    if (!mediaStream) {

        return;
    }

    mediaStream.getTracks().forEach((track) => {

        track.stop();
    });

    mediaStream = null;
}


function scrollConversationToBottom() {

    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}


function addMessage(role, text) {

    if (!text) {

        return;
    }

    emptyConversation.hidden =
        true;

    const message = document.createElement("div");
    message.className =
        `message ${role}`;

    const label = document.createElement("div");
    label.className =
        "message-label";
    label.innerText =
        role === "user"
            ? "You"
            : "AI";

    const body = document.createElement("div");
    body.innerText =
        text;

    message.appendChild(label);
    message.appendChild(body);
    chatMessages.appendChild(message);

    scrollConversationToBottom();
}


function readResponseHeader(response, headerName) {

    const value = response.headers.get(
        headerName
    );

    if (!value) {

        return "";
    }

    try {

        return decodeURIComponent(
            value
        );

    } catch (error) {

        console.warn(error);

        return value;
    }
}


function resetAudioPlayback(statusMessage = "Ready") {

    if (currentAudio) {

        currentAudio.pause();

        currentAudio.onended = null;
        currentAudio.onerror = null;

        currentAudio.removeAttribute("src");
        currentAudio.load();

        currentAudio = null;
    }

    if (currentAudioUrl) {

        URL.revokeObjectURL(
            currentAudioUrl
        );

        currentAudioUrl = null;
    }

    stopSpeakingButton.disabled =
        true;

    setStatus(
        statusMessage,
        statusMessage === "Ready"
            ? "ready"
            : "error"
    );
}


async function startRecording() {

    try {

        clearStatusTimers();
        resetAudioPlayback();

        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        audioChunks = [];

        recordingMimeType = MediaRecorder.isTypeSupported(
            "audio/webm"
        )
            ? "audio/webm"
            : "";

        mediaRecorder = new MediaRecorder(
            mediaStream,
            recordingMimeType
                ? {
                    mimeType: recordingMimeType
                }
                : undefined
        );

        mediaRecorder.ondataavailable = (event) => {

            if (event.data.size > 0) {

                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {

            stopMediaStream();
            scheduleProcessingStatuses();

            try {

                const audioBlob = new Blob(
                    audioChunks,
                    recordingMimeType
                        ? {
                            type: recordingMimeType
                        }
                        : undefined
                );

                const formData = new FormData();

                formData.append(
                    "file",
                    audioBlob,
                    recordingMimeType === "audio/webm"
                        ? "recording.webm"
                        : "recording"
                );

                const response = await fetch(
                    "http://127.0.0.1:8000/voice-chat",
                    {
                        method: "POST",
                        body: formData
                    }
                );

                if (!response.ok) {

                    throw new Error(
                        "Backend request failed"
                    );
                }

                clearStatusTimers();

                const userText = readResponseHeader(
                    response,
                    "X-User-Transcript"
                );

                const aiText = readResponseHeader(
                    response,
                    "X-AI-Response"
                );

                addMessage(
                    "user",
                    userText || "Voice message"
                );

                addMessage(
                    "ai",
                    aiText || "AI response generated as speech."
                );

                const responseBlob =
                    await response.blob();

                const audioUrl =
                    URL.createObjectURL(
                        responseBlob
                    );

                currentAudioUrl =
                    audioUrl;

                currentAudio =
                    new Audio(audioUrl);

                stopSpeakingButton.disabled =
                    false;

                setStatus(
                    "Speaking",
                    "speaking"
                );

                currentAudio.onended = () => {

                    resetAudioPlayback(
                        "Ready"
                    );
                };

                currentAudio.onerror = () => {

                    resetAudioPlayback(
                        "Audio playback failed"
                    );
                };

                try {

                    await currentAudio.play();

                } catch (playError) {

                    if (playError.name === "AbortError") {

                        return;
                    }

                    throw playError;
                }

            } catch (error) {

                console.error(error);

                clearStatusTimers();

                resetAudioPlayback(
                    "Error occurred"
                );
            }
        };

        mediaRecorder.start();

        setStatus(
            "Listening",
            "listening"
        );

    } catch (error) {

        console.error(error);

        stopMediaStream();

        setStatus(
            "Microphone access denied",
            "error"
        );
    }
}


function stopRecording() {

    if (
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
    ) {

        mediaRecorder.stop();
    }
}


stopSpeakingButton.addEventListener(
    "click",
    () => {

        clearStatusTimers();

        resetAudioPlayback(
            "Ready"
        );
    }
);


micButton.addEventListener(
    "mousedown",
    startRecording
);

micButton.addEventListener(
    "mouseup",
    stopRecording
);

micButton.addEventListener(
    "mouseleave",
    stopRecording
);

micButton.addEventListener(
    "touchstart",
    (event) => {

        event.preventDefault();

        startRecording();
    }
);

micButton.addEventListener(
    "touchend",
    stopRecording
);
