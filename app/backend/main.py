from fastapi import FastAPI, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .schemas import VacancyIn, ResumeOut, PrescreenOut, ReportIn, ReportOut
from .services.parser import parse_resume
from .services.prescreen import prescreen
from .services.report import build_pdf_like

from .services.asr import SileroStreamer, transcribe_segment
import json, asyncio

import asyncio, json


app = FastAPI(title="HR-Avatar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# Простые in-memory "кеши" для happy-path
vacancy_cache: dict = {}
resume_cache: dict = {}

@app.post("/vacancy")
async def post_vacancy(v: VacancyIn):
    vacancy_cache.clear()
    vacancy_cache.update(v.model_dump())
    return {"ok": True}

@app.post("/resume", response_model=ResumeOut)
async def post_resume(file: UploadFile):
    b = await file.read()
    parsed = parse_resume(b, file.filename)
    resume_cache.clear()
    resume_cache.update(parsed)
    return parsed

@app.get("/prescreen", response_model=PrescreenOut)
async def get_prescreen():
    table, missing = prescreen(
        resume_cache.get("skills", []),
        vacancy_cache.get("weights", {})
    )
    return {"table": table, "top_missing": missing[:5]}



@app.websocket("/audio")
async def ws_audio(ws: WebSocket):
    await ws.accept()
    streamer = None
    lang = None
    last_text = ""

    try:
        while True:
            msg = await ws.receive()

            if "text" in msg and msg["text"] is not None:
                try:
                    data = json.loads(msg["text"])
                except Exception:
                    continue

                if data.get("event") == "start":
                    sr = int(data.get("sample_rate", 16000))
                    streamer = SileroStreamer(sample_rate=16000, min_chunk_sec=0.8, lookback_sec=5.0)
                    lang = data.get("lang")  # "ru" | "en" | None
                    await ws.send_text(json.dumps({"event":"ready"}))

                elif data.get("event") == "stop":
                    break

                elif data.get("event") == "lang":
                    lang = data.get("value")

            elif "bytes" in msg and msg["bytes"] is not None:
                if streamer is None:
                    continue
                segments = streamer.push(msg["bytes"])
                for pcm, t_end in segments:
                    text = await asyncio.to_thread(transcribe_segment, pcm, lang)
                    clean = (text or "").strip()
                    if clean and clean != last_text:
                        await ws.send_text(json.dumps({
                            "event": "final",
                            "text": clean,
                            "t": round((t_end or 0.0), 2)
                        }))
                        last_text = clean

    except WebSocketDisconnect:
        pass
    finally:
        await ws.close()


@app.post("/report", response_model=ReportOut)
async def post_report(payload: ReportIn):
    weights = payload.vacancy.weights
    have = {s.lower() for s in payload.resume.skills}
    score = sum(w for s, w in weights.items() if s.lower() in have) * 100
    flags = []
    if score < 50:
        flags.append("Недостаточное покрытие ключевых навыков")
    pdf_path = build_pdf_like({
        "score": round(score, 1),
        "flags": flags,
        "evidences": [e.model_dump() for e in payload.evidences]
    })
    return {"score": round(score,1), "flags": flags, "url_pdf": pdf_path}
