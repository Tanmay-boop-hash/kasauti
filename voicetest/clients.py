import hashlib, json, os
from pathlib import Path
import requests
from dotenv import load_dotenv
from .cache import CACHE_DIR, key_for

load_dotenv()
BASE = "https://api.vachana.ai"


def _headers():
    return {"X-API-Key-ID": os.environ["GNANI_API_KEY"]}


def _check(r):
    """Raise with Gnani's own error text, not just 'HTTP 400'."""
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")


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
    _check(r)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(r.content)
    return path


def transcribe(wav_path, language_code="hi-IN", model="prisma-v2.5",
               fmt="transcribe", keyterms=None) -> dict:
    """Returns Gnani's whole JSON reply (transcript, model, timings...).

    We always send `model` and `format` explicitly instead of trusting defaults,
    and every setting that can change the answer is part of the cache key.
    """
    if keyterms and model != "prisma-v3.0":
        raise ValueError("keyterms only works with model='prisma-v3.0'")
    audio = Path(wav_path).read_bytes()
    key = key_for("stt", model, fmt, language_code, keyterms,
                  hashlib.sha256(audio).hexdigest())
    cached = CACHE_DIR / "stt" / f"{key}.json"
    if cached.exists():
        return json.loads(cached.read_text(encoding="utf-8"))
    data = {"language_code": language_code, "format": fmt, "model": model}
    if keyterms:
        data["keyterms"] = json.dumps(keyterms, ensure_ascii=False)
    r = requests.post(f"{BASE}/stt/v3", headers=_headers(),
                      files={"audio_file": ("audio.wav", audio)},
                      data=data, timeout=60)
    _check(r)
    body = r.json()
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    return body