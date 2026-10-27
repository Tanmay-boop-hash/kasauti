import os, requests
from dotenv import load_dotenv

load_dotenv()
r = requests.post(
    "https://api.vachana.ai/stt/v3",
    headers={"X-API-Key-ID": os.environ["GNANI_API_KEY"]},
    files={"audio_file": open("hello.m4a", "rb")},
    data={"language_code": "hi-IN"},
)

print(r.status_code, r.json())