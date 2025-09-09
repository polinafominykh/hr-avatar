from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import asyncio, json
from .schemas import VacancyIn, ResumeOut, PrescreenOut, ReportIn, ReportOut
from .services.parser import parse_resume
from .services.prescreen import prescreen
from .services.report import build_pdf_like
from .services.asr import transcribe_segment
import numpy as np
import traceback
import difflib, re
import contextlib
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState
from .services.evidence import extract_evidences_from_text

# Абсолютный путь к reports/
ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="HR-Avatar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# Монтируем статику ПОСЛЕ создания app
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

from fastapi.responses import FileResponse  # <-- добавь импорт рядом с остальными

# --- статика для клиента и роут на сам тестер ---
PUBLIC_DIR = ROOT / "public"
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

# раздаём /public/* (на всякий)
app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")

# удобный URL: /ws_tester отдает public/ws_tester.html
@app.get("/ws_tester", include_in_schema=False)
def ws_tester():
    return FileResponse(str(PUBLIC_DIR / "ws_tester.html"))

@app.get("/public_ls", include_in_schema=False)
def public_ls():
    return {"public_dir": str(PUBLIC_DIR), "files": [p.name for p in PUBLIC_DIR.glob("*")]}


# Простые in-memory "кеши" для happy-path
vacancy_cache: dict = {}
resume_cache: dict = {}
evidence_cache: list[dict] = []

@app.get("/")
def root():
    return {"ok": True, "try": ["/docs", "/reports/test.txt"]}

@app.post("/vacancy")
async def post_vacancy(v: VacancyIn):
    vacancy_cache.clear()
    vacancy_cache.update(v.model_dump())
    evidence_cache.clear()
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

def _normalize_text(t: str) -> str:
    # нижний регистр, убираем повторяющиеся пробелы/пунктуацию
    t = t.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^\w\sа-яё]", "", t)  # оставим буквы/цифры/пробел
    return t

def _too_similar(a: str, b: str, thresh: float = 0.9) -> bool:
    if not a or not b:
        return False
    return difflib.SequenceMatcher(None, a, b).ratio() >= thresh

TECH_BIAS = [
    "Python", "Пайтон", "пайтон",
    "FastAPI", "ФастАПИ", "фаст апи", "фастапи",
    "SQL", "эс кью эл", "скьюэл", "сквл",
    "Postgres", "PostgreSQL", "Постгрес",
    "Docker", "Докер",
    "Kubernetes", "Кубернетес", "Кубер", "k8s",
    "Git", "Гит",
]

def normalize_tech_terms(s: str) -> str:
    t = s
    repl = [
        (r"\bскв?е?л\b", "SQL"),
        (r"\bэс\s*кью\s*эл\b", "SQL"),
        (r"\bsql\b", "SQL"),
        (r"\bфаст\s*апи\b", "FastAPI"),
        (r"\bфаста?\s*пи\b", "FastAPI"),
        (r"\bfast\s*api\b", "FastAPI"),
        (r"\bпайтон\b", "Python"),
        (r"\bpython\b", "Python"),
        (r"\bпостгрес\b", "Postgres"),
        (r"\bpostgres(?:ql)?\b", "Postgres"),
    ]
    import re
    for pat, to in repl:
        t = re.sub(pat, to, t, flags=re.IGNORECASE)
    return t

def cleanup_text(t: str) -> str:
    t = re.sub(r"[«»]+", "", t)
    t = re.sub(r"[—–]{2,}", "—", t)
    t = re.sub(r"\b(\w{1,20})(?:\s+\1){2,}\b", r"\1", t, flags=re.IGNORECASE)
    t = re.sub(r"\b((?:\w+\s+){1,4}\w+)(?:\s+\1){1,}\b", r"\1", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(\w{2,})\b(\s+\1\b){3,}", r"\1 \1 \1", t, flags=re.IGNORECASE)
    t = re.sub(r"\s{2,}", " ", t).strip(" ,.;:—-")
    return t




@app.websocket("/audio")
async def ws_audio(ws: WebSocket):
    await ws.accept()
    lang = "ru"
    closed = False

    # --- параметры endpointing ---
    END_SILENCE = 0.6          # сек тишины, чтобы считать, что фраза закончилась
    UTT_MAX_SEC = 6.0          # максимум длины одной реплики (сек)
    MIN_UTT_SEC = 0.35         # слишком короткое не шлём
    SAMPLE_RATE = 16000

    # --- состояние ---
    last_voice_ts = 0.0
    last_send_ts = 0.0
    last_text_norm = ""
    utt_buf = bytearray()      # буфер текущей реплики
    accum = bytearray()        # для аварийного фолбэка

    try:
        while True:
            msg = await ws.receive()

            # ---------------- текстовые сообщения ----------------
            if "text" in msg and msg["text"] is not None:
                data = json.loads(msg["text"])
                evt = data.get("event")
                if evt == "start":
                    SAMPLE_RATE = int(data.get("sample_rate", 16000))
                    lang = data.get("lang") or "ru"
                    await ws.send_text(json.dumps({"event": "ready"}))
                    # начинаем чистую сессию интервью
                    evidence_cache.clear()
                    # сброс состояния
                    last_voice_ts = 0.0
                    last_send_ts = 0.0
                    last_text_norm = ""
                    utt_buf.clear()
                    accum.clear()

                elif evt == "stop":

                    # если есть незавершённая реплика — добьём
                    if len(utt_buf) >= int(SAMPLE_RATE * 2 * MIN_UTT_SEC):
                        pcm = bytes(utt_buf[-int(SAMPLE_RATE * 2 * UTT_MAX_SEC):])
                        text = await asyncio.to_thread(transcribe_segment, pcm, lang, None)  # без bias
                        clean = cleanup_text(normalize_tech_terms((text or "").strip()))
                        if len(clean) >= 2:
                            norm_new = _normalize_text(clean)
                            if norm_new != last_text_norm:
                                await ws.send_text(json.dumps({"event": "final", "text": clean, "t": None}))
                                last_text_norm = norm_new
                                # evidence и для финалки при stop
                                t_now = asyncio.get_event_loop().time()
                                evs = extract_evidences_from_text(clean, t_now, vacancy_cache.get("weights", {}))
                                if evs:
                                    evidence_cache.extend([e.asdict() for e in evs])
                                    print("[WS][evidence]", [e.skill for e in evs], "←", clean)

                    closed = True
                    with contextlib.suppress(Exception):
                        await ws.close(code=1000)
                    return

                elif evt == "lang":
                    lang = data.get("value") or lang

            # ---------------- бинарные аудио чанки ----------------
            elif "bytes" in msg and msg["bytes"] is not None:
                b = msg["bytes"]
                accum.extend(b)
                utt_buf.extend(b)

                # ограничиваем длину текущей реплики (кольцевой буфер)
                max_bytes = int(SAMPLE_RATE * 2 * UTT_MAX_SEC)
                if len(utt_buf) > max_bytes:
                    del utt_buf[:len(utt_buf) - max_bytes]

                # грубый RMS для endpointing (быстро и стабильно)
                sig = np.frombuffer(b, dtype=np.int16).astype(np.float32) / 32768.0
                rms = float(np.sqrt((sig**2).mean() + 1e-12))

                now = asyncio.get_event_loop().time()

                # если RMS выше порога — считаем, что есть голос
                if rms > 0.01:
                    last_voice_ts = now

                # если тишина длится достаточно и есть накопленная реплика — отправляем ОДИН final
                if last_voice_ts > 0 and (now - last_voice_ts) >= END_SILENCE:
                    if len(utt_buf) >= int(SAMPLE_RATE * 2 * MIN_UTT_SEC):
                        pcm = bytes(utt_buf[-max_bytes:])

                        # адаптивное мягкое усиление (AGC) — на случай тихого микрофона
                        sig_all = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
                        rms_all = float(np.sqrt((sig_all**2).mean() + 1e-12))
                        if rms_all < 0.01:
                            gain = min(3.0, 0.02 / max(rms_all, 1e-6))
                            sig_all = np.clip(sig_all * gain, -1.0, 1.0)
                            pcm = (sig_all * 32767.0).astype(np.int16).tobytes()

                        # ДЕТЕРМИНИРОВАННАЯ расшифровка, без bias
                        text = await asyncio.to_thread(transcribe_segment, pcm, lang, None)
                        clean = cleanup_text(normalize_tech_terms((text or "").strip()))

                        # фильтры: очень короткое/мусор не шлём
                        if len(clean) >= 2:
                            norm_new = _normalize_text(clean)
                            # блок «почти такой же текст подряд»
                            if norm_new != last_text_norm and (now - last_send_ts) > 0.4:
                                await ws.send_text(json.dumps({"event": "final", "text": clean, "t": None}))
                                last_text_norm = norm_new
                                last_send_ts = now
                                from .services.evidence import extract_evidences_from_text
                                evs = extract_evidences_from_text(clean, now, vacancy_cache.get("weights", {}))
                                if evs:
                                    evidence_cache.extend([e.asdict() for e in evs])
                                    print("[WS][evidence]", [e.skill for e in evs], "←", clean)
                    # считаем реплику завершённой — чистим её буфер
                    utt_buf.clear()

    except WebSocketDisconnect:
        closed = True
    finally:
        if not closed:
            with contextlib.suppress(Exception):
                await ws.close()



@app.post("/report", response_model=ReportOut)
async def post_report(payload: ReportIn):
    # --- скоринг по резюме ---
    weights = payload.vacancy.weights or {}
    have = {s.lower() for s in (payload.resume.skills or [])}
    score_raw = sum(w for s, w in weights.items() if s.lower() in have)
    score = round(score_raw * 100, 1)

    # --- флаги ---
    flags: list[str] = []
    if score < 50:
        flags.append("Недостаточное покрытие ключевых навыков")

    # --- объединяем evidences: из запроса + из кеша интервью (с дедупликацией) ---
    merged_evidences = []
    seen = set()

    def _push(lst):
        for e in lst or []:
            # e может быть pydantic-моделью или dict
            d = e.model_dump() if hasattr(e, "model_dump") else dict(e)
            key = (d.get("skill"), (d.get("quote") or d.get("text") or "").strip())
            if key in seen:
                continue
            seen.add(key)
            # нормализуем поле текста
            d["text"] = d.get("quote") or d.get("text") or ""
            d.pop("quote", None)
            merged_evidences.append(d)

    _push(payload.evidences)
    _push(evidence_cache)

    pdf_path = build_pdf_like({
        "score": score,
        "flags": flags,
        "evidences": merged_evidences
    })
    url_pdf = pdf_path if str(pdf_path).startswith("/") else "/" + str(pdf_path).replace("\\", "/")
    return {"score": score, "flags": flags, "url_pdf": url_pdf}
