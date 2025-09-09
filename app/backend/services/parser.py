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


# --- Извлечение скиллов (детектор по ключевым словам) ---
_CANON_SKILLS = {
    # ===== Вакансия: Бизнес-аналитик =====
    "Анализ требований": [
        r"\bанализ\w*\s+требован", r"\bтребован\w+\s*(?:бизн|функц)",
        r"\brequirements?\b", r"\buser\s*story\b", r"\buse\s*case\b"
    ],
    "Антифрод-системы": [
        r"\bантифрод\b", r"\banti[-\s]?fraud\b",
        r"\bпод/?фт\b", r"\baml\b", r"\bfraud\b", r"\bмошеннич\w+"
    ],
    "SQL/СУБД": [
        r"\bsql\b", r"\bpostgres(?:ql)?\b", r"\bmysql\b", r"\boracle\b", r"\bсубд\b"
    ],
    "Документация (ТЗ, ФТ)": [
        r"\bтз\b", r"\bф[тд]\b", r"\bтех\w*\s+задани", r"\bфункциональн\w*\s+требован"
    ],
    "Финансовые операции/карт-бизнес": [
        r"\bкарт\w+\b", r"\bплатеж\w+\b", r"\bэквайр\w+\b", r"\bплатёжн\w+\s+систем",
        r"\bдбо\b", r"\bкорпоративн\w*\s+карт", r"\bтранзакц\w+"
    ],
    "MS Office": [
        r"\bms\s*office\b", r"\bexcel\b", r"\bword\b", r"\bpowerpoint\b", r"\bvisio\b"
    ],

    # ===== Вакансия: Ведущий специалист (ИТ, ЦОД) =====
    "Серверное оборудование x86": [
        r"\bсерверн\w+\s+оборудован\w+\b", r"\bx86\b", r"\bbios\b", r"\bbmc\b", r"\braid\b"
    ],
    "Сети LAN/SAN": [
        r"\blan\b", r"\bsan\b", r"\bethernet\b", r"\bсет(и|ях)\b", r"\bfc\b", r"\bstorage\b"
    ],
    "Кабельные системы": [
        r"\bскс\b", r"\bкабельн\w+\s+систем", r"\bоптич\w+\b", r"\bвитая\s*пара\b"
    ],
    "Диагностика оборудования": [
        r"\bдиагностик\w+\b", r"\btroubleshoot\w*\b", r"\bинцидент\w+\b", r"\bavar[iй]\b"
    ],
    "Документооборот (CMDB, DCIM)": [
        r"\bcmdb\b", r"\bdcim\b", r"\bсистем\w+\s+уч[её]та\b", r"\bдокументооборот\b"
    ],
    "MS Office (Excel, Word, Visio)": [
        r"\bexcel\b", r"\bword\b", r"\bvisio\b", r"\bms\s*office\b"
    ],
    "Ответственность/внимательность": [
        r"\bответственн\w+\b", r"\bвнимательн\w+\b", r"\bаккуратн\w+\b", r"\bисполнительн\w+\b"
    ],
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
