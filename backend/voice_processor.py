import os
import requests
from requests.auth import HTTPBasicAuth
import uuid
import asyncio
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

from dotenv import dotenv_values

class VoiceProcessor:
    def __init__(self):
        pass

    def _download_twilio_media_sync(self, media_url: str, output_path: str):
        env = dotenv_values(".env")
        twilio_sid = env.get("TWILIO_ACCOUNT_SID")
        twilio_auth = env.get("TWILIO_AUTH_TOKEN")
        
        if not twilio_sid or not twilio_auth:
            raise ValueError("Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN")
            
        response = requests.get(
            media_url, 
            auth=HTTPBasicAuth(twilio_sid, twilio_auth),
            stream=True
        )
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            raise Exception(f"Failed to download Twilio media: {response.status_code} {response.text}")

    async def transcribe_audio(self, media_url: str) -> str:
        """Downloads audio from Twilio and returns the transcription text using Groq Whisper."""
        temp_filename = f"/tmp/twilio_audio_{uuid.uuid4().hex}.ogg"
        try:
            # Step 1: Download Media (executed in thread pool since requests is synchronous)
            await asyncio.to_thread(self._download_twilio_media_sync, media_url, temp_filename)
            
            # Step 2: Transcribe using Whisper
            env = dotenv_values(".env")
            groq_key = env.get("GROQ_API_KEY")
            if not groq_key:
                raise ValueError("Missing GROQ_API_KEY in .env")
                
            groq_client = AsyncGroq(api_key=groq_key)
            with open(temp_filename, "rb") as audio_file:
                transcription = await groq_client.audio.transcriptions.create(
                    file=("audio.ogg", audio_file.read()),
                    model="whisper-large-v3",
                )
            
            return transcription.text
        except Exception as e:
            print(f"VoiceProcessor Error: {e}")
            raise e
        finally:
            # Step 3: Cleanup temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

voice_processor = VoiceProcessor()
