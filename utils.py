import os, json, time, hashlib, re
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

def get_env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)

def sha1(text: str) -> str:
    return hashlib.sha1(text.encode('utf-8')).hexdigest()

def now_ms() -> int:
    return int(time.time() * 1000)

def clean_markdown(md: str) -> str:
    # Minimal cleanup to avoid duplicated whitespace
    return re.sub(r'\n{3,}', '\n\n', md).strip()

class SimpleCache:
    def __init__(self, base_dir: str = None):
        base_dir = base_dir or os.environ.get("PRO_LLM_CACHE_DIR", ".cache")
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def path_for(self, key: str) -> str:
        digest = sha1(key)
        return os.path.join(self.base_dir, f"{digest}.json")

    def get(self, key: str):
        path = self.path_for(key)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def set(self, key: str, value):
        path = self.path_for(key)
        try:
            with open(path, "w") as f:
                json.dump(value, f)
        except Exception:
            pass