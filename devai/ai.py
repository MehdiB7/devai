import urllib.request
import urllib.error
import json


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3"


def ask_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str | None:
    """Envoie un prompt à Ollama et retourne la réponse complète."""
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except urllib.error.URLError:
        return None
    except json.JSONDecodeError:
        return None
