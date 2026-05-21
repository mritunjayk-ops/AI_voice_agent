import asyncio
import json
import os
import wave
import struct
import websockets

async def test_end_to_end():
    url = "ws://127.0.0.1:8000/ws/stream-voice"
    audio_dir = "generated_audio"
    
    # Find a valid wav file in generated_audio
    files = [f for f in os.listdir(audio_dir) if f.endswith(".wav") and os.path.getsize(os.path.join(audio_dir, f)) > 10000]
    if not files:
        print("No suitable audio file found for testing.")
        return
    
    audio_path = os.path.join(audio_dir, files[0])
    print(f"Using audio file for test: {audio_path}")
    
    # Read the audio and convert to 16kHz raw PCM if necessary
    with wave.open(audio_path, 'rb') as wav:
        params = wav.getparams()
        print(f"Audio params: {params}")
        raw_frames = wav.readframes(params.nframes)
        
        sample_width = params.sampwidth
        channels = params.nchannels
        frame_rate = params.framerate
        
        if sample_width != 2:
            print("Unsupported sample width (only 16-bit supported)")
            return
            
        # Unpack raw 16-bit signed PCM frames
        num_frames = len(raw_frames) // (sample_width * channels)
        
        # Unpack samples (might be multi-channel)
        format_str = f"<{num_frames * channels}h"
        all_samples = struct.unpack(format_str, raw_frames)
        
        # Convert to mono by taking the first channel
        if channels > 1:
            samples = [all_samples[i * channels] for i in range(num_frames)]
        else:
            samples = list(all_samples)
            
        # Resample to 16000Hz using linear interpolation in pure Python
        new_num_samples = int(num_frames * 16000 / frame_rate)
        print(f"Resampling from {num_frames} samples ({frame_rate}Hz) to {new_num_samples} samples (16000Hz)...")
        
        resampled_samples = []
        for i in range(new_num_samples):
            pos = i * frame_rate / 16000
            idx = int(pos)
            frac = pos - idx
            if idx + 1 < len(samples):
                val = int(samples[idx] * (1.0 - frac) + samples[idx + 1] * frac)
            else:
                val = samples[idx]
            resampled_samples.append(val)
            
        # Pack resampled samples back to bytes
        pcm_bytes = struct.pack(f"<{len(resampled_samples)}h", *resampled_samples)

    print(f"Connecting to {url}...")
    async with websockets.connect(url) as ws:
        print("Connected to WebSocket. Sending start event...")
        await ws.send(json.dumps({
            "event": "start",
            "session_id": "test_integration_session"
        }))
        
        # Stream the raw 16kHz PCM chunks
        chunk_size = 4096  # bytes
        print("Streaming PCM bytes...")
        for i in range(0, len(pcm_bytes), chunk_size):
            chunk = pcm_bytes[i:i+chunk_size]
            await ws.send(chunk)
            await asyncio.sleep(0.02) # simulate real-time streaming delay (20ms chunks)
            
        print("Streaming finished. Sending stop event...")
        await ws.send(json.dumps({
            "event": "stop"
        }))
        
        # Listen for events
        print("\n--- Listening for incoming events ---")
        try:
            while True:
                # Wait for up to 15 seconds for a response
                msg = await asyncio.wait_for(ws.recv(), timeout=15.0)
                if isinstance(msg, str):
                    data = json.loads(msg)
                    event_type = data.get("event")
                    if event_type == "transcript":
                        print(f"\n[Event: transcript] Text: {data.get('text')}")
                    elif event_type == "text_stream":
                        print(f"{data.get('text')}", end="", flush=True)
                    elif event_type == "generation_complete":
                        print(f"\n[Event: generation_complete] Total Sequences: {data.get('total_seq')}")
                    elif event_type == "error":
                        print(f"\n[Event: error] Error: {data.get('message')}")
                        break
                else:
                    # Binary audio data
                    print(f"\n[Event: audio] Binary Audio Frame, Size: {len(msg)}")
        except asyncio.TimeoutError:
            print("\nTimeout waiting for response. Ending test.")
        except websockets.exceptions.ConnectionClosed:
            print("\nWebSocket connection closed.")

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
