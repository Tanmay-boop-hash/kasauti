import hashlib, json
from pathlib import Path

CACHE_DIR = Path(".cache")

def key_for(*parts) -> str:
    """Same input -> same key. This is what makes re-runs free."""
    blob = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]