# app/backend/services/report.py
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def _draw_bullets(c: canvas.Canvas, items, y):
    c.setFont("Helvetica", 10)
    if not items:
        items = ["—"]
    for it in items:
        c.drawString(2.2*cm, y, f"• {str(it)}")
        y -= 0.5*cm
    return y

def build_pdf_like(data: dict) -> str:
    """
    Принимает dict вида:
      {
        "score": 87.5,              # проценты
        "flags": ["...","..."],     # список строк
        "evidences": [              # опционально: [{skill, quote, t}, ...]
            {"skill":"python","quote":"Говорил про Python","t":12.3}, ...
        ]
      }
    Возвращает путь относительный к корню API: 'reports/report.pdf'
    """
    score = data.get("score", 0)
    flags = data.get("flags", []) or []
    evidences = data.get("evidences", []) or []

    out_path = REPORTS_DIR / "report.pdf"

    c = canvas.Canvas(str(out_path), pagesize=A4)
    w, h = A4

    # Заголовок
    c.setFont("Helvetica-Bold", 16)
    y = h - 2*cm
    c.drawString(2*cm, y, "HR-Avatar: Отчёт по интервью"); y -= 1.0*cm

    # Общая инфа
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, y, f"Итоговый скор: {score}%"); y -= 0.8*cm

    # Секция флагов
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Красные флаги"); y -= 0.5*cm
    y = _draw_bullets(c, flags, y); y -= 0.3*cm

    # Секция цитат/доказательств
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Цитаты (evidence)");
    y -= 0.5 * cm
    c.setFont("Helvetica", 10)
    if evidences:
        for ev in evidences:
            text = ev.get("quote") or ev.get("text") or ""
            line = f"[{ev.get('t', '—')}s] {ev.get('skill', '?')}: {text}"
            c.drawString(2.2 * cm, y, line)
            y -= 0.5 * cm
            if y < 3 * cm:  # новая страница при переполнении
                c.showPage()
                y = h - 2 * cm
                c.setFont("Helvetica", 10)

    else:
        c.drawString(2.2 * cm, y, "—");
        y -= 0.5 * cm

    c.showPage()
    c.save()

    # Возвращаем относительный URL-путь
    return str(out_path).replace("\\", "/")
