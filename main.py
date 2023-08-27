import os

import speech_recognition as sr
from pydub import AudioSegment
import httpx
from io import BytesIO
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Set up CORS to allow requests from all origins
origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])

# Initialize the recognizer
recognizer = sr.Recognizer()


async def download_record(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            audio_file = BytesIO(response.content)
            return audio_file
        else:
            print("Failed to download M4A audio file. Status code:", response.status_code)
            return None


async def convert_to_text(url):
    m4a_audio_file = await download_record(url)
    if m4a_audio_file:
        audio = AudioSegment.from_file(m4a_audio_file, format="m4a")

        # Export the audio as WAV (SpeechRecognition supports WAV format)
        wav_audio_path = "temp_audio.wav"
        audio.export(wav_audio_path, format="wav")

        with sr.AudioFile(wav_audio_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                os.remove(wav_audio_path)
                return text
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
        return None
    return None


@app.post("/convert")
async def convert(request: dict):
    url = request.get("url")
    if url:
        text = await convert_to_text(url)
        print("Converted Text:")
        print(text)
        if text:
            return {"text": text}
        else:
            return {"error": "Text conversion failed"}
    else:
        return {"error": "URL parameter missing"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8005)
