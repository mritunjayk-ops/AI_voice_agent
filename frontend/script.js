const micButton = document.getElementById("micButton");
const stopSpeakingButton = document.getElementById("stopSpeakingButton");
const statusText = document.getElementById("status");

let mediaRecorder;
let audioChunks = [];
let recordingMimeType = "";

let currentAudio = null;
let currentAudioUrl = null;


function resetAudioPlayback(statusMessage) {

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

    stopSpeakingButton.disabled = true;

    if (statusMessage) {

        statusText.innerText =
            statusMessage;
    }
}


async function startRecording() {

    try {

        resetAudioPlayback();

        const stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        audioChunks = [];

        recordingMimeType = MediaRecorder.isTypeSupported(
            "audio/webm"
        )
            ? "audio/webm"
            : "";

        mediaRecorder = new MediaRecorder(
            stream,
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

            try {

                statusText.innerText =
                    "Processing voice...";

                // IMPORTANT:
                // KEEP THIS SIMPLE

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

                statusText.innerText =
                    "AI is speaking...";

                currentAudio.onended = () => {

                    resetAudioPlayback(
                        "Hold button and speak"
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

                resetAudioPlayback(
                    "Error occurred"
                );
            }
        };

        mediaRecorder.start();

        statusText.innerText =
            "Listening...";

    } catch (error) {

        console.error(error);

        statusText.innerText =
            "Microphone access denied";
    }
}


function stopRecording() {

    if (
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
    ) {

        statusText.innerText =
            "Stopping recording...";

        mediaRecorder.stop();
    }
}


stopSpeakingButton.addEventListener(
    "click",
    () => {

        resetAudioPlayback(
            "Hold button and speak"
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
