"""
Unified AI service.
Modes: interviewer (coding), coach (onboarding), flashcard, mock_interview, resume_drill
"""
from typing import Optional
from app.config import settings

# ── Canned fallbacks by keyword ───────────────────────────────────────────────
FALLBACKS = {
    "approach": "Before coding, walk me through your approach. What data structure are you thinking of and why?",
    "complexity": "What's the time complexity of your current solution? Can you do better?",
    "edge": "You've handled the happy path. What about edge cases — empty input, single element, duplicates, negative numbers?",
    "stuck": "Let's break this down. What's the simplest version of this problem you could solve? Start there.",
    "hint": "Think about what you need to know at each step. What information can you precompute to avoid repeated work?",
    "review": "I see your code. Walk me through it line by line — explain every decision you made.",
    "behavioral": "Use the STAR framework: Situation, Task, Action, Result. Be specific — what were the actual numbers or outcomes?",
    "system": "Start with requirements: scale, latency, consistency. Then components. Don't jump to implementation.",
    "default": "Interesting. Tell me more about your reasoning. Why did you choose that approach over alternatives?",
}


def fallback(message: str) -> str:
    msg = message.lower()
    for kw, resp in FALLBACKS.items():
        if kw in msg:
            return resp
    return FALLBACKS["default"]


def _interviewer_system(user_name: str, company: str, role: str, problem_title: str, code: str, resume_projects: list) -> str:
    proj_str = ", ".join(p.get("name", "") for p in resume_projects[:2]) if resume_projects else "N/A"
    code_snippet = code[:800] + "..." if len(code) > 800 else code
    return f"""You are a senior {company} interviewer conducting a real {role} technical interview with {user_name}.

Problem: {problem_title}
Candidate's current code:
```
{code_snippet}
```
Candidate's notable projects: {proj_str}

YOUR BEHAVIOR (non-negotiable):
- You are evaluating them for a real offer. Be professional, precise, slightly intimidating but fair.
- NEVER give away the answer. Ask questions that make them think.
- When they explain an approach, probe deeper: "What's the time complexity?" "What if the input is empty?" "Can you do better?"
- When they write code, interrupt with: "Walk me through what you're doing here." "Why a hash map instead of a sorted array?"
- After submission, give honest {company}-caliber feedback: what would cost them the offer, what was strong.
- Reference {company}-specific values: Amazon = LP alignment, Google = code elegance + optimal complexity, Microsoft = clarity + OOP.
- Keep responses under 3 sentences. Real interviewers are concise.
- Occasionally add pressure: "You have 10 minutes left." "In a real interview, this would be a red flag."
"""


def _coach_system(user_name: str, target_role: str, target_company: str) -> str:
    return f"""You are a warm but no-nonsense placement prep coach helping {user_name} prepare for {target_role} at {target_company}.

Your style: friendly, direct, like a senior friend who got the offer and is helping you. Casual but sharp.
- Ask one question at a time during onboarding.
- When explaining a plan, be specific: company names, problem names, exact topics.
- Be encouraging but honest. If their self-assessment is weak, acknowledge it and reassure them you'll fix it.
- Keep responses concise — 2-3 sentences max unless explaining a plan.
"""


def _flashcard_system(topic: str, user_name: str) -> str:
    return f"""You are conducting a rapid-fire viva on {topic} with {user_name}.

Rules:
- Ask one crisp question at a time.
- When they answer, immediately evaluate: what they got right, what they missed, the key insight.
- Never give a lecture. One correction sentence, then the next question.
- Mix easy and hard questions. Start easy to build confidence, then push.
- If they get 3 wrong in a row, slow down and explain before asking again.
- Keep each exchange under 4 sentences total.
"""


def _mock_interview_system(user_name: str, company: str, role: str, resume_projects: list, round_type: str) -> str:
    proj_details = ""
    for p in resume_projects[:3]:
        name = p.get("name", "")
        desc = p.get("description", "")[:100]
        proj_details += f"\n- {name}: {desc}"

    return f"""You are a {company} interviewer conducting a {round_type} round for {user_name} applying for {role}.

Candidate's resume projects:{proj_details if proj_details else " Not provided."}

INTERVIEW PROTOCOL:
1. Start with "Tell me about yourself" — evaluate their pitch.
2. Ask 2-3 questions directly about their projects: implementation decisions, challenges, scaling.
3. Ask 1-2 {company}-specific behavioral questions tied to {company}'s values.
4. Ask 1 system design question appropriate for {role}.
5. End with "Any questions for me?" — evaluate their curiosity.

EVALUATION after each answer:
- Score 1-5 internally (don't reveal until end)
- Ask meaningful follow-ups, not just "okay, next question"
- Push back on vague answers: "Can you be more specific?" "What was the actual impact?"

After all questions, give a detailed debrief:
- Overall score /100
- Strongest moment
- Biggest red flag
- Would you hire? Why/why not?
- Top 3 things to improve

Be tough but fair. This is their career.
"""


async def _call_gemini(system_prompt: str, history: list, message: str) -> str:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=system_prompt)
        hist = []
        for m in history[-12:]:
            hist.append({"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]})
        chat = model.start_chat(history=hist)
        return chat.send_message(message).text
    except Exception as e:
        return fallback(message)


async def _call_openai(system_prompt: str, history: list, message: str) -> str:
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        messages = [{"role": "system", "content": system_prompt}]
        for m in history[-12:]:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": message})
        resp = await client.chat.completions.create(model="gpt-4o-mini", messages=messages, max_tokens=400, temperature=0.8)
        return resp.choices[0].message.content or fallback(message)
    except Exception:
        return fallback(message)


async def _ai(system: str, history: list, message: str) -> str:
    p = settings.LLM_PROVIDER
    if p == "gemini" and settings.GEMINI_API_KEY:
        return await _call_gemini(system, history, message)
    if p == "openai" and settings.OPENAI_API_KEY:
        return await _call_openai(system, history, message)
    return fallback(message)


async def interviewer_response(
    message: str, history: list, user_name: str, company: str, role: str,
    problem_title: str, code: str, resume_projects: list,
) -> str:
    system = _interviewer_system(user_name, company, role, problem_title, code, resume_projects)
    return await _ai(system, history, message)


async def coach_response(message: str, history: list, user_name: str, target_role: str, target_company: str) -> str:
    system = _coach_system(user_name, target_role, target_company)
    return await _ai(system, history, message)


async def flashcard_response(message: str, history: list, topic: str, user_name: str) -> str:
    system = _flashcard_system(topic, user_name)
    return await _ai(system, history, message)


async def mock_interview_response(
    message: str, history: list, user_name: str, company: str,
    role: str, resume_projects: list, round_type: str = "technical",
) -> str:
    system = _mock_interview_system(user_name, company, role, resume_projects, round_type)
    return await _ai(system, history, message)


async def generate_resume_interview_questions(
    projects: list, experience: list, target_role: str, target_company: str
) -> list:
    """Generate deep, project-specific interview questions from actual resume content."""
    proj_text = ""
    for p in projects[:3]:
        proj_text += f"\nProject: {p.get('name','')}\nDescription: {p.get('description','')[:200]}\n"

    exp_text = ""
    for e in experience[:2]:
        exp_text += f"\nRole: {e.get('role','')} at {e.get('company','')}\nResponsibilities: {', '.join(e.get('responsibilities',[])[:3])}\n"

    prompt = f"""Given this candidate's resume for a {target_role} role at {target_company}:

PROJECTS:{proj_text}
EXPERIENCE:{exp_text}

Generate exactly 8 interview questions. Requirements:
1. Questions 1-3: Deep technical questions about their SPECIFIC projects (implementation, scaling, decisions)
2. Questions 4-5: Questions about technologies they used and WHY they chose them
3. Questions 6-7: Behavioral questions tied to {target_company}'s values about situations from their experience
4. Question 8: "If you had to rebuild [their main project] at {target_company} scale, what would you change?"

Format: Return ONLY a JSON array of strings. No preamble. Example:
["Question 1?", "Question 2?", ...]"""

    p = settings.LLM_PROVIDER
    try:
        if p == "gemini" and settings.GEMINI_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(prompt)
            import json, re
            text = resp.text
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        elif p == "openai" and settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
            )
            import json, re
            text = resp.choices[0].message.content or ""
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
    except Exception:
        pass

    # Fallback: generic but targeted questions
    questions = []
    for p in projects[:2]:
        name = p.get("name", "your project")
        questions += [
            f"Walk me through the architecture of {name}. What were your key design decisions?",
            f"What was the hardest technical problem you faced in {name} and how did you solve it?",
            f"If {name} had to handle 100x the current load, what would break first and how would you fix it?",
        ]
    questions += [
        f"Why did you choose your tech stack for your projects over alternatives?",
        f"Tell me about a time you had to learn something completely new under pressure.",
        f"Describe a situation where you disagreed with a technical decision. What did you do?",
        f"If you were rebuilding your main project at {target_company} scale, what would you change?",
    ]
    return questions[:8]
