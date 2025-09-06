def prescreen(resume_skills, vacancy_weights):
    rs = {s.lower() for s in resume_skills}
    table, missing = [], []
    for skill, w in vacancy_weights.items():
        hit = skill.lower() in rs
        if not hit: missing.append(skill)
        table.append({"skill": skill, "in_resume": hit, "weight": w})
    return table, missing
