# app/backend/services/evidence.py
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Iterable, Optional


@dataclass
class Evidence:
    """Подтверждение навыка, извлечённое из фразы кандидата."""
    skill: str          # каноническое имя навыка (как в weights вакансии)
    quote: str          # цитата / распознанный фрагмент речи
    t: float            # время конца фрагмента (сек) или None/0.0, если неизвестно
    confidence: float = 1.0  # на будущее — пока ставим 1.0

    def asdict(self) -> dict:
        return asdict(self)


# Канонический навык -> список регексов-алиасов (границы слов, регистронезависимо)
# Можно расширять по мере необходимости
# Канонический навык -> список регексов-алиасов (границы слов, регистронезависимо)
ALIASES: Dict[str, List[re.Pattern]] = {
    # --- Бизнес-аналитик ---
    "Анализ требований": [
        re.compile(r"анализ\w*\s+требован", re.I),
        re.compile(r"требован\w+\s*(?:бизн|функц)", re.I),
        re.compile(r"requirements?", re.I),
        re.compile(r"user\s*story", re.I),
        re.compile(r"use\s*case", re.I),
    ],
    "Антифрод-системы": [
        re.compile(r"антифрод", re.I),
        re.compile(r"anti[-\s]?fraud", re.I),
        re.compile(r"\baml\b", re.I),
        re.compile(r"под/?фт", re.I),
        re.compile(r"мошеннич", re.I),
        re.compile(r"\bfraud\b", re.I),
    ],
    "SQL/СУБД": [
        re.compile(r"\bsql\b", re.I),
        re.compile(r"postgres(?:ql)?", re.I),
        re.compile(r"\bmysql\b", re.I),
        re.compile(r"\boracle\b", re.I),
        re.compile(r"субд", re.I),
    ],
    "Документация (ТЗ, ФТ)": [
        re.compile(r"\bтз\b", re.I),
        re.compile(r"\bф[тд]\b", re.I),
        re.compile(r"тех\w*\s+задан", re.I),
        re.compile(r"функциональн\w*\s+требован", re.I),
        re.compile(r"документац", re.I),
    ],
    "Финансовые операции/карт-бизнес": [
        re.compile(r"карт", re.I),
        re.compile(r"плате?ж", re.I),
        re.compile(r"эквайр", re.I),
        re.compile(r"транзакц", re.I),
        re.compile(r"\bдбо\b", re.I),
    ],
    "MS Office": [
        re.compile(r"ms\s*office", re.I),
        re.compile(r"\bexcel\b", re.I),
        re.compile(r"\bword\b", re.I),
        re.compile(r"powerpoint", re.I),
        re.compile(r"\bvisio\b", re.I),
    ],

    # --- Ведущий специалист (ИТ, ЦОД) ---
    "Серверное оборудование x86": [
        re.compile(r"серверн\w+\s+оборудован", re.I),
        re.compile(r"\bx86\b", re.I),
        re.compile(r"\bbios\b", re.I),
        re.compile(r"\bbmc\b", re.I),
        re.compile(r"\braid\b", re.I),
    ],
    "Сети LAN/SAN": [
        re.compile(r"\blan\b", re.I),
        re.compile(r"\bsan\b", re.I),
        re.compile(r"ethernet", re.I),
        re.compile(r"\bfc\b", re.I),
        re.compile(r"storage", re.I),
        re.compile(r"сет[иях]", re.I),
    ],
    "Кабельные системы": [
        re.compile(r"\bскс\b", re.I),
        re.compile(r"кабельн\w+\s+систем", re.I),
        re.compile(r"оптич", re.I),
        re.compile(r"витая\s*пара", re.I),
    ],
    "Диагностика оборудования": [
        re.compile(r"диагностик", re.I),
        re.compile(r"troubleshoot", re.I),
        re.compile(r"инцидент", re.I),
        re.compile(r"авар", re.I),
    ],
    "Документооборот (CMDB, DCIM)": [
        re.compile(r"\bcmdb\b", re.I),
        re.compile(r"\bdcim\b", re.I),
        re.compile(r"систем\w+\s+уч[её]та", re.I),
        re.compile(r"документооборот", re.I),
    ],
    "MS Office (Excel, Word, Visio)": [
        re.compile(r"\bexcel\b", re.I),
        re.compile(r"\bword\b", re.I),
        re.compile(r"\bvisio\b", re.I),
        re.compile(r"ms\s*office", re.I),
    ],
    "Ответственность/внимательность": [
        re.compile(r"ответствен", re.I),
        re.compile(r"вниматель", re.I),
        re.compile(r"аккуратн", re.I),
        re.compile(r"исполнител", re.I),
    ],

    # (можешь оставить dev-навыки — не мешают)
    "Python": [re.compile(r"\bpython\b", re.I), re.compile(r"\bпитон\b", re.I), re.compile(r"\bпайтон\b", re.I)],
    "FastAPI": [re.compile(r"\bfast\s*api\b", re.I), re.compile(r"\bфаст\s*апи\b", re.I), re.compile(r"\bфаста?\s*пи\b", re.I)],
    "Docker": [re.compile(r"\bdocker\b", re.I), re.compile(r"\bдокер\b", re.I)],
    "Kubernetes": [re.compile(r"\bkubernetes\b", re.I), re.compile(r"\bk8s\b", re.I), re.compile(r"кубер(?:нетес)?", re.I)],
    "Git": [re.compile(r"\bgit\b", re.I), re.compile(r"\bгит\b", re.I)],
    "Jira": [re.compile(r"\bjira\b", re.I), re.compile(r"\bжира\b", re.I)],
    "Confluence": [re.compile(r"\bconfluence\b", re.I), re.compile(r"\bконфлюенс\b", re.I)],
    "Swagger": [re.compile(r"\bswagger\b", re.I), re.compile(r"\bopenapi\b", re.I)],
    "Excel": [re.compile(r"\bexcel\b", re.I), re.compile(r"\bms\s*excel\b", re.I), re.compile(r"\bэкс[еэ]ль?\b", re.I)],
    "ML": [re.compile(r"\bmachine\s*learning\b", re.I), re.compile(r"\bml\b", re.I), re.compile(r"машин\w*\s+обуч\w*", re.I)],
}



def _skills_subset(vacancy_weights: Optional[Dict[str, float]]) -> Iterable[str]:
    """
    Если переданы weights вакансии — ограничиваемся только этими навыками.
    Иначе используем все, что есть в ALIASES.
    """
    if vacancy_weights:
        # нормализуем ключи как есть (каноническое имя = ключ в weights)
        return vacancy_weights.keys()
    return ALIASES.keys()


def extract_hits(text: str, vacancy_weights: Optional[Dict[str, float]] = None) -> List[str]:
    """
    Вернуть список канонических навыков, найденных в тексте по алиасам.
    Учитывает ограничение по вакансии (если передано).
    """
    if not text:
        return []

    hits: List[str] = []
    for canon in _skills_subset(vacancy_weights):
        # если в ALIASES нет такого ключа — проверяем точное слово как fallback
        patterns = ALIASES.get(canon, [re.compile(rf"\b{re.escape(canon)}\b", re.I)])
        if any(rx.search(text) for rx in patterns):
            hits.append(canon)

    # уникализируем, сохраняя порядок
    seen = set()
    uniq = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            uniq.append(h)
    return uniq


def extract_evidences_from_text(
    text: str,
    t_end: float,
    vacancy_weights: Optional[Dict[str, float]] = None,
) -> List[Evidence]:
    """
    MVP-логика: если фраза содержит один или несколько навыков — создаём Evidence на каждый.
    Цитатой берём всю фразу.
    """
    skills = extract_hits(text, vacancy_weights)
    if not skills:
        return []

    quote = (text or "").strip()
    if not quote:
        return []

    evs = [Evidence(skill=s, quote=quote, t=round(float(t_end or 0.0), 2), confidence=1.0) for s in skills]
    return evs


def merge_evidences(*lists: Iterable[Evidence]) -> List[Evidence]:
    """
    Аккуратно объединяет списки Evidence, удаляя дубликаты по (skill, quote).
    """
    result: List[Evidence] = []
    seen = set()
    for lst in lists:
        for e in lst or []:
            key = (e.skill, e.quote.strip())
            if key in seen:
                continue
            seen.add(key)
            result.append(e)
    return result
