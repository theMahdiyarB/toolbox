#!/usr/bin/env python3
"""
Piper TTS API Server
Runs on localhost:5050, proxied by Caddy at /api/tts
Install: /var/www/toolbox/venv/bin/pip install piper-tts fastapi uvicorn
Run:     /var/www/toolbox/venv/bin/python tts_server.py
"""

import io
import logging
import wave
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from piper import PiperVoice
from piper.config import SynthesisConfig

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_PATH = Path(__file__).parent / "static/lib/fa_IR-ganji-medium.onnx"
HOST       = "127.0.0.1"
PORT       = 5050
MAX_CHARS  = 2000

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("tts")

# ── Load model once at startup ────────────────────────────────────────────────
log.info(f"Loading Piper model: {MODEL_PATH}")
voice = PiperVoice.load(str(MODEL_PATH))   # config_path auto-detected as MODEL_PATH + ".json"
log.info(f"✅ Piper model loaded — sample_rate={voice.config.sample_rate}")

# ── FastAPI ───────────────────────────────────────────────────────────────────
app = FastAPI(title="TTS API", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["POST", "GET"], allow_headers=["Content-Type"])

class TTSRequest(BaseModel):
    text:  str
    speed: float = 1.0   # 0.5 – 2.0  (higher = faster)

@app.post("/api/tts")
async def synthesize(req: TTSRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(400, "متن خالی است")
    if len(text) > MAX_CHARS:
        raise HTTPException(400, f"متن طولانی‌تر از {MAX_CHARS} کاراکتر است")

    speed = max(0.5, min(2.0, req.speed))
    # length_scale: 1.0 = normal, < 1.0 = faster, > 1.0 = slower
    syn_config = SynthesisConfig(length_scale=1.0 / speed)

    try:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            # synthesize_wav sets WAV params automatically from the first chunk
            voice.synthesize_wav(text, wf, syn_config=syn_config)
        buf.seek(0)
        size = buf.getbuffer().nbytes
        log.info(f"Synthesized {len(text)} chars at speed={speed} → {size} bytes")
        return StreamingResponse(buf, media_type="audio/wav", headers={"Cache-Control": "no-store"})
    except Exception as e:
        log.error(f"Synthesis error: {e}", exc_info=True)
        raise HTTPException(500, f"خطا در تولید صدا: {e}")

@app.get("/api/tts/health")
async def health():
    return {"status": "ok", "model": MODEL_PATH.name, "sample_rate": voice.config.sample_rate}

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")