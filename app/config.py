from pathlib import Path

def _read_env() -> dict:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    result = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip()
    return result

_env = _read_env()

API_BASE = _env.get("API_BASE_URL", "http://localhost:8001")
WS_BASE  = API_BASE.replace("http://", "ws://").replace("https://", "wss://")