from io import BytesIO
from pathlib import Path
import re

# --- DOCX ---
def _extract_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text)

# --- PDF ---
def _extract_pdf(file_bytes: bytes) -> str:
    # быстрый high-level парсер
    from pdfminer.high_level import extract_text
    bio = BytesIO(file_bytes)
    text = extract_text(bio)
    return text or ""

# --- RTF ---
def _extract_rtf(file_bytes: bytes) -> str:
    """
    Надёжный разбор RTF без внешних зависимостей (pandoc не нужен).
    striprtf корректно убирает управляющие последовательности и декодирует текст.
    """
    try:
        from striprtf.striprtf import rtf_to_text
        # RTF — это по сути ASCII с управлялками, но внутри часто cp1251/utf-8.
        # Сначала пробуем в utf-8, если пусто — cp1251.
        raw = file_bytes.decode("utf-8", errors="ignore")
        text = rtf_to_text(raw).strip()
        if not text:
            raw = file_bytes.decode("cp1251", errors="ignore")
            text = rtf_to_text(raw).strip()
        return text
    except Exception:
        # Жёсткий фолбэк (на случай совсем кривого RTF)
        import re
        raw = file_bytes.decode("latin-1", errors="ignore")
        no_controls = re.sub(r"\\[a-zA-Z]+\d* ?", " ", raw)
        no_groups = re.sub(r"[{}]", " ", no_controls)
        no_hex = re.sub(r"\\'[0-9a-fA-F]{2}", " ", no_groups)
        return re.sub(r"\s+", " ", no_hex).strip()


# --- Плейн-текст (на всякий) ---
def _extract_plain(file_bytes: bytes) -> str:
    for enc in ("utf-8", "cp1251", "latin-1"):
        try:
            return file_bytes.decode(enc)
        except Exception:
            continue
    return ""

# --- Извлечение скиллов (очень простой детектор по ключевым словам) ---
_CANON_SKILLS = {
    "python": [r"\bpython\b"],
    "fastapi": [r"\bfastapi\b"],
    "ml": [r"\bmachine learning\b", r"\bml\b"],
    "nlp": [r"\bnlp\b", r"\bnatural language processing\b"],
    "pytorch": [r"\bpytorch\b"],
    "tensorflow": [r"\btensorflow\b"],
    "docker": [r"\bdocker\b"],
    "kubernetes": [r"\bk8s\b", r"\bkubernetes\b"],
    "sql": [r"\bsql\b", r"\bpostgres\b", r"\bmysql\b"],
    "git": [r"\bgit\b"],
    "react": [r"\breact\b"],
    "vite": [r"\bvite\b"],
    "tailwind": [r"\btailwind\b"],
    "websocket": [r"\bweb\s*socket(s)?\b", r"\bwebsocket(s)?\b"],
    "whisper": [r"\bwhisper\b"],
    "vad": [r"\bvad\b", r"\bvoice activity detection\b"],
    "jinja": [r"\bjinja\b"],
    "weasyprint": [r"\bweasyprint\b"],
    "reportlab": [r"\breportlab\b"],
    "pydantic": [r"\bpydantic\b"],
}

def _extract_skills(text: str) -> list[str]:
    found = []
    low = text.lower()
    for canon, patterns in _CANON_SKILLS.items():
        if any(re.search(p, low) for p in patterns):
            found.append(canon)
    # уникализируем и сохраняем порядок
    seen = set()
    uniq = []
    for s in found:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq

# --- Публичная функция, которую вызывает FastAPI роут ---
def parse_resume(file_bytes: bytes, filename: str) -> dict:
    ext = Path(filename).suffix.lower()
    if ext == ".docx":
        text = _extract_docx(file_bytes)
    elif ext == ".pdf":
        text = _extract_pdf(file_bytes)
    elif ext == ".rtf":
        text = _extract_rtf(file_bytes)
    else:
        text = _extract_plain(file_bytes)

    # подрезаем сверхдлинный текст, чтобы фронту не слать километры
    clean_text = re.sub(r"\s+", " ", text).strip()
    if len(clean_text) > 20000:
        clean_text = clean_text[:20000] + " ..."

    skills = _extract_skills(clean_text)
    return {"text": clean_text, "skills": skills}
