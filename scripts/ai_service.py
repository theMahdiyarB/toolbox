#!/usr/bin/env python3
"""
Unified AI Service — TTS + OCR + STT
Runs on localhost:8084, proxied by Caddy

Endpoints:
  POST /api/tts          { text, speed }             → audio/wav
  GET  /api/tts/health
  POST /api/ocr          { image: base64, lang }      → { text }
  POST /api/stt          multipart: audio + lang      → { text, language, duration }
  GET  /api/ai/health

Install (into existing venv):
  /var/www/toolbox/venv/bin/pip install \
      piper-tts fastapi uvicorn \
      pytesseract pillow \
      faster-whisper

System deps:
  apt install tesseract-ocr tesseract-ocr-fas tesseract-ocr-ara ffmpeg -y
"""

import io, base64, logging, os, tempfile, wave
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent.parent          # /var/www/toolbox
TTS_MODEL_PATH = BASE_DIR / "static/lib/fa_IR-ganji-medium.onnx"
WHISPER_DIR    = BASE_DIR / "scripts/whisper-models"
HOST           = "127.0.0.1"
PORT           = 8084
MAX_TTS_CHARS  = 2000
MAX_AUDIO_MB   = 50 * 1024 * 1024

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("ai_service")

# ── Load TTS ──────────────────────────────────────────────────────────────────
log.info(f"Loading Piper TTS: {TTS_MODEL_PATH}")
from piper import PiperVoice
from piper.config import SynthesisConfig
tts_voice = PiperVoice.load(str(TTS_MODEL_PATH))
log.info(f"✅ Piper ready  sample_rate={tts_voice.config.sample_rate}")

# ── Load Whisper ──────────────────────────────────────────────────────────────
WHISPER_DIR.mkdir(parents=True, exist_ok=True)
log.info("Loading faster-whisper base...")
try:
    from faster_whisper import WhisperModel
    whisper_model = WhisperModel("/var/www/toolbox/scripts/whisper-models",
                                 device="cpu", compute_type="int8",
                                 download_root=str(WHISPER_DIR))
    log.info("✅ Whisper ready")
    WHISPER_OK = True
except Exception as e:
    log.error(f"Whisper load failed: {e}")
    whisper_model = None
    WHISPER_OK = False

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Toolbox AI", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["GET","POST"], allow_headers=["Content-Type"])

# ══ TTS ═══════════════════════════════════════════════════════════════════════
class TTSRequest(BaseModel):
    text:  str
    speed: float = 1.0

@app.post("/api/tts")
async def synthesize(req: TTSRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(400, "متن خالی است")
    if len(text) > MAX_TTS_CHARS:
        raise HTTPException(400, f"متن بیش از {MAX_TTS_CHARS} کاراکتر است")
    speed = max(0.5, min(2.0, req.speed))
    try:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            tts_voice.synthesize_wav(text, wf, syn_config=SynthesisConfig(length_scale=1.0/speed))
        buf.seek(0)
        log.info(f"TTS {len(text)} chars speed={speed} → {buf.getbuffer().nbytes}B")
        return StreamingResponse(buf, media_type="audio/wav", headers={"Cache-Control":"no-store"})
    except Exception as e:
        log.error(f"TTS error: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@app.get("/api/tts/health")
async def tts_health():
    return {"status":"ok","model":TTS_MODEL_PATH.name,"sample_rate":tts_voice.config.sample_rate}

# ══ OCR ═══════════════════════════════════════════════════════════════════════
_ALLOWED_LANGS = {"fas","eng","fas+eng","eng+fas","ara"}

class OCRRequest(BaseModel):
    image: str
    lang:  str = "fas+eng"

@app.post("/api/ocr")
async def ocr(req: OCRRequest):
    import pytesseract
    from PIL import Image
    lang = req.lang if req.lang in _ALLOWED_LANGS else "fas+eng"
    try:
        img = Image.open(io.BytesIO(base64.b64decode(req.image))).convert("RGB")
    except Exception as e:
        raise HTTPException(400, f"تصویر نامعتبر: {e}")
    try:
        text = pytesseract.image_to_string(img, lang=lang, config="--oem 1 --psm 3")
        log.info(f"OCR lang={lang} chars={len(text)}")
        return {"text": text.strip()}
    except Exception as e:
        log.error(f"OCR error: {e}", exc_info=True)
        raise HTTPException(500, str(e))

# ══ STT ═══════════════════════════════════════════════════════════════════════
@app.post("/api/stt")
async def stt(audio: UploadFile = File(...), lang: str = Form(default="")):
    if not WHISPER_OK:
        raise HTTPException(503, "Whisper غیرفعال است")
    content = await audio.read()
    if len(content) > MAX_AUDIO_MB:
        raise HTTPException(413, "فایل بیش از ۵۰ مگابایت است")
    suffix = Path(audio.filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content); tmp_path = tmp.name
    try:
        kw = {"beam_size":5, "vad_filter":True}
        if lang: kw["language"] = lang
        segments, info = whisper_model.transcribe(tmp_path, **kw)
        text = " ".join(s.text.strip() for s in segments)
        log.info(f"STT lang={info.language} dur={info.duration:.1f}s chars={len(text)}")
        return {"text":text.strip(), "language":info.language, "duration":round(info.duration,1)}
    except Exception as e:
        log.error(f"STT error: {e}", exc_info=True)
        raise HTTPException(500, str(e))
    finally:
        try: os.unlink(tmp_path)
        except OSError: pass

# ══ Health ═════════════════════════════════════════════════════════════════════
@app.get("/api/ai/health")
async def ai_health():
    return {"tts":"ok","ocr":"ok","whisper":"ok" if WHISPER_OK else "unavailable"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
