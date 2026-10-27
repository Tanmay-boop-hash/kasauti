import hashlib, json, os
from pathlib import Path
import requests
from dotenv import load_dotenv
from .cache import CACHE_DIR, key_for

load_dotenv()
BASE = "https://api.vachana.ai"

def _headers():
    return {"X-API-Key-ID": os.environ["GNANI_API_KEY"]}

def synthesize(text, voice="Shivani", language="hi-IN",
               model="timbre-v3.0", speed=1.0, sample_rate=16000) -> Path:
    payload = {
        "text": text, "voice": voice, "model": model,
        "language": language, "speed": speed,
        "audio_config": {"sample_rate": sample_rate, "num_channels": 1,
                         "sample_width": 2, "encoding": "linear_pcm",
                         "container": "wav"},
    }
    path = CACHE_DIR / "tts" / f"{key_for(payload)}.wav"
    if path.exists():                      # cache hit: no network, no credits
        return path
    r = requests.post(f"{BASE}/api/v1/tts/inference",
                      headers=_headers(), json=payload, timeout=60)
    r.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(r.content)
    return path

def transcribe(wav_path, language_code="hi-IN") -> str:
    audio = Path(wav_path).read_bytes()
    key = key_for("stt", language_code, hashlib.sha256(audio).hexdigest())
    cached = CACHE_DIR / "stt" / f"{key}.json"
    if cached.exists():
        return json.loads(cached.read_text(encoding="utf-8"))["transcript"]
    r = requests.post(f"{BASE}/stt/v3", headers=_headers(),
                      files={"audio_file": ("audio.wav", audio)},
                      data={"language_code": language_code}, timeout=60)
    r.raise_for_status()
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(r.json(), ensure_ascii=False), encoding="utf-8")
    return r.json()["transcript"]