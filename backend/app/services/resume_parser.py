"""resume_parser.py"""
import re, io
from datetime import datetime, timezone
from typing import Optional
import pdfplumber

SKILL_DICT = {
    "languages": ["python","java","c++","c","javascript","typescript","go","rust","kotlin","swift","ruby","php","scala","r","c#","bash"],
    "frontend": ["react","vue","angular","nextjs","svelte","html","css","sass","tailwind","bootstrap","redux","graphql","webpack","vite"],
    "backend": ["fastapi","django","flask","node","express","spring","rails","laravel","gin","nestjs","grpc","rest","microservices"],
    "databases": ["postgresql","mysql","mongodb","redis","sqlite","cassandra","elasticsearch","dynamodb","firebase","kafka","snowflake"],
    "cloud": ["aws","gcp","azure","docker","kubernetes","terraform","ansible","jenkins","github actions","linux","nginx"],
    "ml_ai": ["tensorflow","pytorch","scikit-learn","pandas","numpy","hugging face","langchain","openai","transformers","opencv","keras"],
    "tools": ["git","github","gitlab","jira","postman","figma","vs code","intellij","agile","scrum"],
}
ALL_SKILLS = {s.lower() for cat in SKILL_DICT.values() for s in cat}
ROLE_REQS = {
    "SDE-1": {"python","java","c++","javascript","git","linux","docker"},
    "SDE-2": {"python","java","c++","javascript","git","linux","docker","kubernetes","microservices"},
    "Data Engineer": {"python","sql","spark","kafka","aws","postgresql","pandas"},
    "ML Engineer": {"python","tensorflow","pytorch","scikit-learn","pandas","numpy","docker"},
    "DevOps": {"linux","docker","kubernetes","terraform","ansible","aws","jenkins"},
    "Frontend": {"javascript","typescript","react","vue","html","css","tailwind"},
    "Backend": {"python","java","go","node","postgresql","redis","docker","rest"},
    "Full Stack": {"javascript","typescript","react","node","python","postgresql","redis","docker"},
}
SEC = {k: re.compile(r"^\s*"+k, re.I|re.M) for k in ["education","experience","projects","skills"]}

def extract_text(b: bytes) -> str:
    with pdfplumber.open(io.BytesIO(b)) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)

def extract_skills(text: str) -> list:
    tl = text.lower()
    return sorted([s for s in ALL_SKILLS if re.search(r'\b'+re.escape(s)+r'\b', tl)])

def extract_projects(text: str) -> list:
    projects, lines = [], text.split("\n")
    in_sec, cur, desc = False, {}, []
    for line in lines:
        line = line.strip()
        if not line:
            if cur and desc: cur["description"]=" ".join(desc); projects.append(cur); cur={}; desc=[]
            continue
        if SEC["projects"].match(line): in_sec=True; continue
        if in_sec and any(SEC[k].match(line) for k in ["education","experience","skills"]): break
        if in_sec:
            if re.match(r'^[A-Z][^.]{5,60}$', line) and not line.startswith("-"):
                if cur and desc: cur["description"]=" ".join(desc); projects.append(cur)
                cur={"name":line}; desc=[]
            elif cur: desc.append(line.lstrip("•-– "))
    if cur and desc: cur["description"]=" ".join(desc); projects.append(cur)
    return projects[:6]

def extract_experience(text: str) -> list:
    exps, lines, in_sec = [], text.split("\n"), False
    dp = re.compile(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*\d{4}', re.I)
    cur, desc = {}, []
    for line in lines:
        line = line.strip()
        if not line: continue
        if SEC["experience"].match(line): in_sec=True; continue
        if in_sec and any(SEC[k].match(line) for k in ["education","projects","skills"]): break
        if in_sec:
            if dp.search(line):
                if cur: cur["responsibilities"]=desc[:5]; exps.append(cur)
                cur={"period":line}; desc=[]
            elif cur and not cur.get("company"): cur["company"]=line
            elif cur and not cur.get("role"): cur["role"]=line
            else: desc.append(line.lstrip("•-– "))
    if cur: cur["responsibilities"]=desc[:5]; exps.append(cur)
    return exps[:5]

def extract_education(text: str) -> dict:
    lines, in_sec, edu_lines = text.split("\n"), False, []
    for line in lines:
        line=line.strip()
        if not line: continue
        if SEC["education"].match(line): in_sec=True; continue
        if in_sec and any(SEC[k].match(line) for k in ["experience","projects","skills"]): break
        if in_sec: edu_lines.append(line)
    edu = {"raw":" ".join(edu_lines[:8])}
    for line in edu_lines:
        if re.search(r'b\.?tech|be|bsc|bachelor|master|phd', line, re.I): edu["degree"]=line
        m = re.search(r'(cgpa|gpa)[\s:]*([0-9.]+)', line, re.I)
        if m: edu["cgpa"]=m.group(2)
    return edu

async def parse_resume(b: bytes, fname: str, role: Optional[str]=None) -> dict:
    raw = extract_text(b)
    skills = extract_skills(raw)
    projects = extract_projects(raw)
    experience = extract_experience(raw)
    education = extract_education(raw)
    gaps = sorted((ROLE_REQS.get(role, set()) - {s.lower() for s in skills})) if role and role in ROLE_REQS else []
    strengths = [f"{k.replace('_',' ').title()}" for k, v in SKILL_DICT.items() if len({s.lower() for s in v} & {s.lower() for s in skills}) >= 3]
    return {"raw_text": raw, "skills_extracted": skills, "projects_extracted": projects,
            "experience_extracted": experience, "education_extracted": education, "skill_gaps": gaps,
            "strengths": strengths, "interview_questions": [],
            "parsed_data": {"word_count": len(raw.split()), "skill_count": len(skills), "project_count": len(projects)},
            "analyzed_at": datetime.now(timezone.utc).isoformat()}
