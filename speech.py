"""
speech.py - Speech-to-text backend support.
Optional cloud integrations (Google Cloud, OpenAI Whisper, etc.)
"""

import os
from typing import Optional, Tuple
import json


def transcribe_audio_google(audio_file_path: str) -> Optional[str]:
    """
    Transcribe audio using Google Cloud Speech-to-Text.
    
    Requires:
        1. Google Cloud project with Speech-to-Text API enabled
        2. Service account JSON credentials
        3. Set GOOGLE_APPLICATION_CREDENTIALS env var
    
    Install: pip install google-cloud-speech
    """
    try:
        from google.cloud import speech_v1
        
        client = speech_v1.SpeechClient()
        
        with open(audio_file_path, "rb") as audio_file:
            content = audio_file.read()
        
        audio = speech_v1.RecognitionAudio(content=content)
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )
        
        response = client.recognize(config=config, audio=audio)
        
        transcripts = []
        for result in response.results:
            for alternative in result.alternatives:
                transcripts.append(alternative.transcript)
        
        return " ".join(transcripts) if transcripts else None
    
    except ImportError:
        raise RuntimeError("Install: pip install google-cloud-speech")
    except Exception as e:
        print(f"[Speech] Google Cloud error: {e}")
        return None


def transcribe_audio_openai(audio_file_path: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Transcribe audio using OpenAI Whisper API.
    
    Requires:
        1. OpenAI API key
        2. Set OPENAI_API_KEY env var or pass api_key
    
    Install: pip install openai
    Cost: $0.02 per minute
    """
    try:
        from openai import OpenAI
        
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        client = OpenAI(api_key=api_key)
        
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        
        return transcript.text
    
    except ImportError:
        raise RuntimeError("Install: pip install openai")
    except Exception as e:
        print(f"[Speech] OpenAI Whisper error: {e}")
        return None


def get_transcription_service_status() -> dict:
    """Check which speech-to-text services are available."""
    services = {
        "web_speech_api": {"available": True, "note": "Browser-native, free, JavaScript"},
        "google_cloud": {"available": False, "note": "Requires setup"},
        "openai_whisper": {"available": False, "note": "Requires API key"},
        "assemblyai": {"available": False, "note": "Requires API key"},
    }
    
    # Check Google Cloud
    try:
        from google.cloud import speech_v1
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            services["google_cloud"]["available"] = True
    except ImportError:
        pass
    
    # Check OpenAI
    if os.getenv("OPENAI_API_KEY"):
        services["openai_whisper"]["available"] = True
    
    return services


# Recommended: Use Web Speech API on frontend first
# Only use cloud services for advanced needs or lower-noise environment
DEFAULT_SERVICE = "web_speech_api"
