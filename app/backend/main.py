from fastapi import FastAPI, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .schemas import VacancyIn, ResumeOut, PrescreenOut, ReportIn, ReportOut
from .services.parser import parse_resume
from .services.prescreen import prescreen
from .services.report import build_pdf_like
import asyncio, json, time

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
    # День 1: мок-«ASR» — сервер сам шлёт фразы раз в ~700мс
    phrases = [
        "Здравствуйте, меня зовут Полина.",
        "Опыт 3 года с Python и FastAPI.",
        "Делала NLP и сервисы на Kubernetes."
    ]
    try:
        t0 = time.time()
        for p in phrases:
            await asyncio.sleep(0.7)
            await ws.send_text(json.dumps({"text": p, "t": time.time()-t0}))
        await ws.close()
    except WebSocketDisconnect:
        pass

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
