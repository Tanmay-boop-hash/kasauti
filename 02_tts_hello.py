import requests, os
from dotenv import load_dotenv

load_dotenv()
r = requests.post(
    "https://api.vachana.ai/api/v1/tts/inference",
    headers={"X-API-Key-ID": os.environ["GNANI_API_KEY"]},
    json={
        "text": "Mera number nau aath saat chhah paanch hai.",
        "voice": "Shivani",
        "model": "timbre-v3.0",
        "language": "hi-IN",
        "speed": 1.0,
        "audio_config": {"sample_rate": 16000, "num_channels": 1,
                         "sample_width": 2, "encoding": "linear_pcm",
                         "container": "wav"},
    }
)

print(r.status_code)
open("hello_tts.wav", "wb").write(r.content)
