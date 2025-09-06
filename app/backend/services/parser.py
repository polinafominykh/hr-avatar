def parse_resume(file_bytes: bytes, filename: str) -> dict:
    # День 1: возвращаем мок-«распарсенный» текст/скиллы
    text = f"Mock parsed from {filename}. Python, FastAPI, NLP."
    skills = ["python", "fastapi", "nlp"]
    return {"text": text, "skills": skills}
