const micButton = document.getElementById("micButton");
const statusText = document.getElementById("status");

let mediaRecorder;
let audioChunks = [];
let recordingMimeType = "";

let currentAudio = null;


async function startRecording() {

    try {

        // STOP CURRENT AI SPEECH

        if (currentAudio) {

            currentAudio.pause();

            currentAudio.currentTime = 0;
        }

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

                currentAudio =
                    new Audio(audioUrl);

                statusText.innerText =
                    "AI is speaking...";

                await currentAudio.play();

                currentAudio.onended = () => {

                    statusText.innerText =
                        "Hold button and speak";
                };

            } catch (error) {

                console.error(error);

                statusText.innerText =
                    "Error occurred";
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


micButton.addEventListener(
    "mousedown",
    startRecording
);

micButton.addEventListener(
    "mouseup",
    stopRecording
);
