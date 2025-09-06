from pathlib import Path
from jinja2 import Template

TEMPLATE = """
<!doctype html><html><body style="font-family:Arial">
<h1>HR-Avatar Report</h1>
<p><b>Score:</b> {{ score }}%</p>
<h3>Flags</h3>
<ul>{% for f in flags %}<li>{{ f }}</li>{% endfor %}</ul>
<h3>Evidence</h3>
<ul>{% for e in evidences %}<li>[{{ "%.1f"|format(e.t) }}s] {{ e.skill }} — "{{ e.quote }}"</li>{% endfor %}</ul>
</body></html>
"""

def build_pdf_like(data, out_dir="reports") -> str:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    html = Template(TEMPLATE).render(**data)
    # День 1: создаём HTML-файл и даём ему .pdf-имя (для демо фронту всё равно)
    path = Path(out_dir) / "report_mock.pdf"
    path.write_text(html, encoding="utf-8")
    return str(path)
