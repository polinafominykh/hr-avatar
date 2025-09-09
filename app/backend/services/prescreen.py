from typing import List, Dict, Tuple

def prescreen(resume_skills: List[str], weights: Dict[str, float]) -> Tuple[list[dict], list[str]]:
    resume_set = {s.lower() for s in (resume_skills or [])}
    rows: list[dict] = []

    for skill, w in (weights or {}).items():
        have = skill.lower() in resume_set
        weight = float(w or 0.0)
        rows.append({
            "skill": skill,
            "weight": weight,
            "have": have,          # для фронта
            "in_resume": have,     # <-- это поле требует схема PrescreenOut
            "score": weight if have else 0.0,
            "note": None,
        })

    rows.sort(key=lambda r: (-int(r["have"]), -r["weight"], r["skill"].lower()))
    top_missing = [r["skill"] for r in rows if not r["have"]]
    return rows, top_missing
