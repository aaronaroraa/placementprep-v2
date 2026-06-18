"""
Unified AI service.
Modes: interviewer (coding), coach (onboarding), flashcard, mock_interview, resume_drill
"""
from typing import Optional
from app.config import settings

# ── Company question banks ─────────────────────────────────────────────────────
# Real historical question patterns for major companies. Used to ground mock
# interviews in what each company actually asks — not generic LeetCode patterns.
COMPANY_QUESTION_BANK: dict[str, dict] = {
    "google": {
        "technical": [
            "Design a distributed key-value store that can handle 1 million requests per second.",
            "Given an infinite stream of integers, find the median at any point in O(log n).",
            "Design Google Search's autocomplete feature. How would you handle 100k QPS?",
            "Implement LRU cache with O(1) get and put. Now make it thread-safe.",
            "How would you design Google Maps' shortest path algorithm for real-time traffic?",
            "Given a 2D matrix of 0s and 1s, find the largest rectangle of 1s.",
            "Design a system to detect plagiarism across billions of documents.",
            "How does Google rank search results? Describe PageRank in detail.",
            "Design YouTube's video recommendation system at scale.",
            "Implement a trie. Now design autocomplete using it at Google's scale.",
        ],
        "behavioral": [
            "Tell me about a time you disagreed with your manager and how you handled it.",
            "Describe the most technically complex project you've worked on.",
            "Tell me about a time you had to learn a new technology quickly under pressure.",
            "How do you handle ambiguity when requirements are unclear?",
            "Describe a time you improved a process or system significantly.",
        ],
        "values": "Google values: code elegance, optimal complexity (O(n log n) over O(n²)), scalability from day one, structured problem-solving, intellectual curiosity.",
    },
    "amazon": {
        "technical": [
            "Design Amazon's product recommendation engine.",
            "How would you design Amazon's order fulfillment system?",
            "Design a distributed rate limiter used across Amazon's microservices.",
            "Implement a system that processes 1 million orders per minute.",
            "Design Amazon's review spam detection system.",
            "How would you build Amazon Prime's video streaming service?",
            "Design the data pipeline for Amazon's real-time inventory management.",
            "How would you detect fraudulent transactions at Amazon's scale?",
            "Design a notification system that delivers 10 billion push notifications/day.",
            "Serialize and deserialize a binary tree. Why does Amazon use this in interviews?",
        ],
        "behavioral": [
            "Tell me about a time you delivered results despite obstacles (Deliver Results).",
            "Describe a situation where you had to make a decision with incomplete data (Bias for Action).",
            "Tell me about a time you disagreed with a team decision but committed anyway (Disagree and Commit).",
            "Give an example of when you went above and beyond for a customer (Customer Obsession).",
            "Describe a time you took ownership of a problem outside your scope (Ownership).",
            "Tell me about a time you raised the bar for quality on your team (Insist on the Highest Standards).",
            "When have you had to simplify something complex? (Think Big + Simplify)",
            "Describe a calculated risk you took. What was the outcome? (Bias for Action)",
        ],
        "values": "Amazon Leadership Principles are non-negotiable. Every behavioral answer must map to an LP. Amazon prioritizes: Customer Obsession, Ownership, Bias for Action, Deliver Results. STAR format required.",
    },
    "microsoft": {
        "technical": [
            "Design Microsoft Teams' real-time collaboration feature.",
            "How would you build Azure's auto-scaling infrastructure?",
            "Design a version control system like Git from scratch.",
            "How would you implement Ctrl+Z (undo) in a text editor?",
            "Design an API rate limiter for Azure's REST APIs.",
            "How would you build a distributed file system like OneDrive?",
            "Design Office 365's real-time co-authoring feature.",
            "Implement a graph data structure and find all connected components.",
        ],
        "behavioral": [
            "Tell me about a time you had to collaborate across teams to ship a feature.",
            "How do you handle a situation where two senior engineers disagree?",
            "Describe a time you made a technical decision that impacted the entire team.",
            "Tell me about a project where you had to balance technical debt vs. new features.",
        ],
        "values": "Microsoft values: growth mindset, collaboration, clarity of communication, OOP fundamentals, empathy for users. Show you can explain complex things simply.",
    },
    "meta": {
        "technical": [
            "Design Facebook's News Feed ranking algorithm.",
            "How would you design Instagram Stories at 500M daily active users?",
            "Design a system to detect hate speech at Facebook's scale.",
            "How would you build WhatsApp's end-to-end encryption?",
            "Design Facebook's friend recommendation system.",
            "How would you handle 1 billion photos uploaded daily to Instagram?",
            "Design a real-time analytics system for Facebook Ads.",
            "Implement a social graph and find shortest connection between two users.",
        ],
        "behavioral": [
            "Tell me about a time you moved fast and shipped something imperfect — then fixed it.",
            "How do you balance technical quality with shipping speed?",
            "Describe a time you had to convince a team to adopt your technical approach.",
            "Tell me about a project that had significant impact at scale.",
        ],
        "values": "Meta values: Move fast, bold bets, long-term impact, scale thinking. They want engineers who ship and iterate, not perfectionist planners.",
    },
    "flipkart": {
        "technical": [
            "Design Flipkart's flash sale system that handles 100k orders in 1 minute.",
            "How would you design Flipkart's search and filter system?",
            "Design a real-time inventory management system for 10M products.",
            "How would you build Flipkart's delivery tracking system?",
            "Design the payment gateway integration for Flipkart.",
            "How would you detect and prevent fraudulent sellers on Flipkart?",
        ],
        "behavioral": [
            "Tell me about a time you worked under tight deadlines.",
            "Describe a situation where you had to prioritize between multiple features.",
            "How do you approach a problem you've never solved before?",
        ],
        "values": "Flipkart values: frugality, customer-first, data-driven decisions, ability to operate under ambiguity and scale quickly.",
    },
    "default": {
        "technical": [
            "Design a URL shortener like bit.ly.",
            "How would you design a real-time chat application?",
            "Design a content delivery network (CDN).",
            "How would you build a notification service at scale?",
            "Implement an LRU cache.",
        ],
        "behavioral": [
            "Tell me about your most challenging technical project.",
            "Describe a time you had to learn something new quickly.",
            "How do you handle disagreements in a team?",
        ],
        "values": "Show structured thinking, clean code, and the ability to scale systems.",
    },
}

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


def extract_score_from_evaluation(text: str) -> float:
    """
    Parses a numeric score from the AI's evaluation text.
    The AI is instructed to end evaluations with 'SCORE: <number>'.
    Falls back to 50 if no score is found.
    """
    import re
    match = re.search(r'SCORE:\s*(\d{1,3})', text, re.IGNORECASE)
    if match:
        return min(100.0, max(0.0, float(match.group(1))))
    return 50.0


def extract_verdict_from_score(score: float) -> str:
    if score >= 70:
        return "pass"
    if score >= 50:
        return "borderline"
    return "fail"


def _build_resume_section(resume_data: dict) -> str:
    """Formats full resume data into a rich context block for the interviewer prompt."""
    sections = []

    projects = resume_data.get("projects", [])
    if projects:
        lines = ["PROJECTS (ask deep questions about each one):"]
        for p in projects:
            name = p.get("name", "Unnamed Project")
            desc = p.get("description", "")[:200]
            tech = ", ".join(p.get("tech_stack", p.get("technologies", [])))
            lines.append(f"  • {name}: {desc}" + (f" | Stack: {tech}" if tech else ""))
        sections.append("\n".join(lines))

    experience = resume_data.get("experience", [])
    if experience:
        lines = ["WORK EXPERIENCE (probe for depth — what did they actually build?):"]
        for e in experience:
            role = e.get("role", e.get("title", ""))
            company = e.get("company", "")
            duration = e.get("duration", e.get("period", ""))
            resp = e.get("responsibilities", e.get("highlights", []))
            resp_str = "; ".join(str(r) for r in resp[:3]) if resp else ""
            lines.append(f"  • {role} at {company} ({duration}): {resp_str}")
        sections.append("\n".join(lines))

    skills = resume_data.get("skills", [])
    if skills:
        skill_str = ", ".join(str(s) for s in skills[:20])
        sections.append(f"SKILLS LISTED: {skill_str}\n(Hold them accountable — if it's on the resume, they should know it cold)")

    education = resume_data.get("education", [])
    if education:
        e = education[0] if isinstance(education, list) else education
        if isinstance(e, dict):
            sections.append(f"EDUCATION: {e.get('degree','')} from {e.get('institution', e.get('college',''))} ({e.get('year', e.get('graduation_year',''))})")

    return "\n\n".join(sections) if sections else "Resume not provided."


def _mock_interview_system(user_name: str, company: str, role: str, resume_data: dict, round_type: str = "full") -> str:
    company_key = company.lower().strip()
    bank = COMPANY_QUESTION_BANK.get(company_key, COMPANY_QUESTION_BANK["default"])
    company_values = bank.get("values", "")

    tech_qs = bank.get("technical", [])[:4]
    beh_qs = bank.get("behavioral", [])[:3]
    tech_str = "\n".join(f"  - {q}" for q in tech_qs)
    beh_str = "\n".join(f"  - {q}" for q in beh_qs)

    resume_section = _build_resume_section(resume_data)

    return f"""You are a senior {company} engineer conducting a REAL hiring interview for {user_name} applying for {role}.

This is a live, proctored, chat-based interview session. The candidate is on camera. Every message they
send is their own real-time response — no copy-paste allowed. Treat this exactly as you would treat a
candidate sitting across from you in an actual interview room.

━━━ CANDIDATE'S RESUME (you've read it in full — reference it specifically) ━━━
{resume_section}

━━━ {company.upper()} INTERVIEW PATTERNS (questions this company actually asks) ━━━
TECHNICAL:
{tech_str}

BEHAVIORAL:
{beh_str}

COMPANY VALUES: {company_values}

━━━ INTERVIEW COVERAGE ━━━
This is a single unified round covering everything in one natural conversation — resume deep-dives,
technical reasoning, system design thinking, and behavioral moments. Do NOT treat these as separate
sections. Flow between them organically based on what the candidate says.

Across the 30 minutes, work toward covering:
• At least one project deep-dive (their work, their decisions, their specific impact)
• Technical reasoning (why they built it a certain way, what tradeoffs they made)
• System thinking (how would it scale, what breaks first, how would you redesign it)
• One or two behavioral moments (a conflict, a failure, a time they led or pushed back)

━━━ HOW TO CONDUCT THIS INTERVIEW ━━━
This is a 30-minute live interview. Keep going continuously — do NOT stop to give a debrief or score
mid-interview. The session ends when the timer runs out. You will be told explicitly. Until then, just interview.

CONVERSATIONAL FLOW — your next question always responds to what they just said:

KEYWORD LISTENING: When they name a technology, metric, decision, or challenge — follow up on it immediately:
• Technology named ("Redis", "Docker", "GraphQL"): "How exactly did you use it? Walk me through the flow." → "Why that over [alternative]?"
• Metric mentioned ("10k users", "2ms latency"): "How did you hit that number? What was the bottleneck?" → "What breaks first at 10x?"
• Design decision made: "What alternatives did you consider and why did you reject them?"
• Vague claim ("improved performance", "handled scale"): "Be specific — what was the before and after, with numbers?"
• Challenge or failure: "What exactly broke? How long to find it? How long to fix?"

DEPTH AND PIVOTING:
1. Ask 2-3 follow-up questions per topic to go deep before moving on.
2. If the candidate answers confidently and completely, pivot to a new topic.
3. If the candidate is clearly stuck — after ONE gentle push ("take your time, even a rough direction is fine"),
   accept the gap and MOVE ON. Say "Okay, let's shift gears." Do not interrogate the same gap more than twice.
4. Keep each response to 1-2 sentences. Ask one question per turn. Real interviewers are concise.
5. Stay neutral — do not say "great answer" or "that's correct". You may say "okay" or "got it" briefly.
6. Do NOT break character. You are the interviewer, not a coach.

OPENING: Start with — "Let's begin. Walk me through your background in 90 seconds — focus on what's most relevant to {role} at {company}."

IMPORTANT: Do NOT give a score, debrief, or any kind of summary during the interview. Just keep asking.
You will receive an explicit signal when the interview ends, at which point you will give the full debrief.
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


def _with_progress(system: str, progress: str) -> str:
    """Appends the candidate's live progress so the AI can personalise its coaching."""
    if not progress:
        return system
    return system + f"\n\nCANDIDATE'S CURRENT PROGRESS (reference this naturally — don't recite it):\n{progress}"


def build_chat_system(context_type: str, *, user_name: str, company: str, role: str,
                      problem_title: str = "", code: str = "", projects: list = None,
                      topic: str = "", progress: str = "") -> str:
    """Builds the right system prompt for a chat context (used by streaming + non-streaming)."""
    projects = projects or []
    if context_type == "coding":
        s = _interviewer_system(user_name, company, role, problem_title, code, projects)
    elif context_type == "flashcard":
        s = _flashcard_system(topic or "computer science", user_name)
    else:
        s = _coach_system(user_name, role, company)
    return _with_progress(s, progress)


async def stream_ai(system: str, history: list, message: str):
    """
    Async generator yielding response text in chunks for Server-Sent Events.
    Falls back to a single canned chunk if no provider/key or on error.
    """
    p = settings.LLM_PROVIDER
    try:
        if p == "gemini" and settings.GEMINI_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system)
            hist = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in history[-12:]]
            chat = model.start_chat(history=hist)
            for chunk in chat.send_message(message, stream=True):
                if getattr(chunk, "text", ""):
                    yield chunk.text
            return
        if p == "openai" and settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            messages = [{"role": "system", "content": system}]
            for m in history[-12:]:
                messages.append({"role": m["role"], "content": m["content"]})
            messages.append({"role": "user", "content": message})
            stream = await client.chat.completions.create(
                model="gpt-4o-mini", messages=messages, max_tokens=500, temperature=0.8, stream=True)
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            return
    except Exception:
        pass
    yield fallback(message)


async def interviewer_response(
    message: str, history: list, user_name: str, company: str, role: str,
    problem_title: str, code: str, resume_projects: list, progress: str = "",
) -> str:
    system = _interviewer_system(user_name, company, role, problem_title, code, resume_projects)
    return await _ai(_with_progress(system, progress), history, message)


async def coach_response(message: str, history: list, user_name: str, target_role: str, target_company: str, progress: str = "") -> str:
    system = _coach_system(user_name, target_role, target_company)
    return await _ai(_with_progress(system, progress), history, message)


async def flashcard_response(message: str, history: list, topic: str, user_name: str, progress: str = "") -> str:
    system = _flashcard_system(topic, user_name)
    return await _ai(_with_progress(system, progress), history, message)


async def mock_interview_response(
    message: str, history: list, user_name: str, company: str,
    role: str, resume_data: dict, round_type: str = "technical",
) -> str:
    system = _mock_interview_system(user_name, company, role, resume_data, round_type)
    return await _ai(system, history, message)


def _debrief_prompt(user_name: str, company: str, role: str) -> str:
    """
    Injected as the final user message when the timer runs out.
    Forces the AI to review the full conversation history and produce a thorough, calibrated debrief.
    """
    return f"""[SESSION ENDED — the 30-minute timer has run out.]

Review EVERYTHING {user_name} said across the entire conversation — every answer, every follow-up,
every moment they were strong or struggled. Do not just summarize the last few messages.
This debrief is your only chance to give them an accurate picture of where they stand.

Give a comprehensive debrief in this exact format:

──────────────────────────────
INTERVIEW DEBRIEF
──────────────────────────────

OVERALL SCORE: [integer 0-100]
VERDICT: [Strong Hire / Hire / Borderline / No Hire]

STRONGEST MOMENT:
[One specific sentence — the single best thing they said or demonstrated. Reference what they actually said.]

BIGGEST GAP:
[One specific sentence — the one thing most likely to cost them the {company} offer. Be direct, not harsh.]

TOPIC-BY-TOPIC BREAKDOWN:
[For each major topic covered in this interview:]
→ What they demonstrated well (be specific — quote or reference their actual words)
→ Where they fell short or were vague (be direct and precise)
→ Whether this is a concern for {role} at {company}

RECRUITER SUMMARY:
[3-4 sentences. Write as if a recruiter will use this to make a hiring decision today. Honest about both
strengths and gaps. Do not inflate. Do not soften real weaknesses. Do not be cruel about honest effort.]

TOP 2 THINGS TO WORK ON:
1. [Tied specifically to something that came up in this conversation — not generic advice]
2. [Tied specifically to something that came up in this conversation — not generic advice]

──────────────────────────────

EVALUATION STANDARD:
Hold {user_name} to a high bar — the competition for {role} at {company} is real, and an inflated score
helps no one. A score of 75+ means genuinely interview-ready. 60-74 means real gaps that would give a
hiring committee pause. Below 60 means significant preparation is needed.

Be thorough and fair. Acknowledge what was genuinely strong. Acknowledge partial understanding and effort.
But do not reward vague answers, bluffing, or surface-level responses with a passing score.
The goal is an accurate read — not a motivational speech, and not a takedown."""


async def mock_interview_chat(
    message: str, history: list, user_name: str, company: str,
    role: str, resume_data: dict, round_type: str = "full",
    end_requested: bool = False,
) -> str:
    """
    Conversational mock interview turn. The AI reads the full conversation history
    and follows up on keywords from the candidate's last answer, or pivots after 2-3
    follow-ups. When end_requested=True, switches to the full debrief prompt.
    """
    system = _mock_interview_system(user_name, company, role, resume_data, round_type)
    if end_requested:
        # Replace the user message with the debrief instruction so the AI reviews everything
        message = _debrief_prompt(user_name, company, role)
    return await _ai(system, history, message)


async def generate_resume_interview_questions(
    projects: list, experience: list, target_role: str, target_company: str,
    skills: list = None, education: list = None,
) -> list:
    """Generate deep, resume-specific interview questions + company historical patterns."""
    bank = COMPANY_QUESTION_BANK.get(target_company.lower().strip(), COMPANY_QUESTION_BANK["default"])
    company_tech_qs = bank.get("technical", [])[:3]
    company_beh_qs = bank.get("behavioral", [])[:2]

    proj_text = ""
    for p in projects[:3]:
        name = p.get("name", "")
        desc = p.get("description", "")[:200]
        tech = ", ".join(p.get("tech_stack", p.get("technologies", [])) or [])
        proj_text += f"\nProject: {name}\nDescription: {desc}\nTech: {tech}\n"

    exp_text = ""
    for e in experience[:2]:
        role = e.get("role", e.get("title", ""))
        company = e.get("company", "")
        resp = e.get("responsibilities", e.get("highlights", []))
        resp_str = ", ".join(str(r) for r in resp[:4])
        exp_text += f"\nRole: {role} at {company}\nWork: {resp_str}\n"

    skill_str = ", ".join(str(s) for s in (skills or [])[:15])
    company_qs_str = "\n".join(f"- {q}" for q in company_tech_qs + company_beh_qs)

    prompt = f"""You are a {target_company} interviewer preparing questions for a {target_role} candidate.

CANDIDATE'S RESUME:
PROJECTS:{proj_text}
EXPERIENCE:{exp_text}
SKILLS: {skill_str}

{target_company.upper()} ACTUAL INTERVIEW QUESTIONS (from past 15 years of interview reports):
{company_qs_str}

Generate exactly 12 interview questions. Rules:
1. Questions 1-4: Deep technical questions about their SPECIFIC projects — reference exact project names, tech choices, and ask about implementation decisions, scale, and tradeoffs.
2. Questions 5-6: Hold them accountable for skills on their resume. "You listed [skill] — explain [specific concept] to me."
3. Questions 7-9: Adapt 2-3 questions from {target_company}'s actual question list above to fit this candidate's background.
4. Questions 10-11: Role-specific questions for {target_role} — what a day-1 engineer in this role needs to know cold.
5. Question 12: "Imagine you rebuilt [their main project] as an engineer at {target_company}. What changes immediately?"

Return ONLY a JSON array of 12 strings. No preamble.
["Question 1?", "Question 2?", ...]"""

    prov = settings.LLM_PROVIDER
    try:
        if prov == "gemini" and settings.GEMINI_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(prompt)
            import json, re
            text = resp.text
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        elif prov == "openai" and settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
            )
            import json, re
            text = resp.choices[0].message.content or ""
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
    except Exception:
        pass

    # Fallback: mix resume-specific + company bank questions
    questions = []
    for p in projects[:2]:
        name = p.get("name", "your project")
        questions += [
            f"Walk me through the architecture of {name}. What were your key design decisions?",
            f"What was the hardest technical problem you faced in {name}?",
            f"If {name} had to handle 100x load, what breaks first and how do you fix it?",
        ]
    questions += company_tech_qs[:3]
    questions += company_beh_qs[:2]
    questions += [
        f"You listed {(skills or ['Python'])[0]} as a skill — explain its memory management to me.",
        f"What would you change about your main project if you were rebuilding it at {target_company} scale?",
    ]
    return questions[:12]


# ── AI study-plan generation (RAG: retrieve real problems → augment → generate) ──
async def _ai_json(prompt: str, max_tokens: int = 2500):
    """
    Sends a prompt to the configured LLM and returns parsed JSON (list or dict),
    or None on any failure. Used for structured generation, not chat.
    """
    import json, re
    p = settings.LLM_PROVIDER
    text = ""
    try:
        if p == "gemini" and settings.GEMINI_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(prompt)
            text = resp.text or ""
        elif p == "openai" and settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens, temperature=0.6,
                response_format={"type": "json_object"},
            )
            text = resp.choices[0].message.content or ""
        else:
            return None
        # Extract the first JSON array or object from the response.
        match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        return json.loads(match.group()) if match else None
    except Exception:
        return None


async def generate_ai_study_plan(
    *, company: str, role: str, days_left: int, daily_hours: float,
    candidate_problems: list,
    # skill_assessment and skill_gaps retained as params for API compatibility but not used to filter topics
    skill_assessment: dict = None, skill_gaps: list = None,
) -> list | None:
    """
    Generates a complete, from-scratch day-by-day study plan covering EVERY important
    topic the candidate needs to succeed — not filtered by what they claim to know.

    Uses real problems from the DB for DSA tasks and fills the rest with theory,
    system design, and behavioral sessions matched to the target company's patterns.

    Returns a list of task dicts, or None if generation fails (caller falls back to static).
    """
    if not candidate_problems:
        return None

    catalogue = "\n".join(
        f"- {p['title']} [{p['difficulty']}, {p['category']}, asked {p.get('times_asked', 1)}x at {company}]"
        for p in candidate_problems[:60]
    )
    tasks_per_day = 2 if daily_hours <= 1 else 3 if daily_hours <= 2 else 4 if daily_hours <= 3 else 5

    bank = COMPANY_QUESTION_BANK.get(company.lower().strip(), COMPANY_QUESTION_BANK["default"])
    company_values = bank.get("values", "")

    # DSA topic coverage order — universal ground-up curriculum
    dsa_curriculum = """
COMPLETE DSA CURRICULUM (cover all of these, ordered from foundations to advanced):
Phase 1 – Foundations (Days 1-20% of plan): Arrays, Strings, Hashing, Two Pointers, Sliding Window, Binary Search
Phase 2 – Core Structures (next 25%): Stacks, Queues, Linked Lists, Trees (BFS/DFS), Recursion & Backtracking
Phase 3 – Intermediate (next 25%): Heaps/Priority Queues, Graphs (BFS/DFS/Topological), Dynamic Programming (1D→2D)
Phase 4 – Advanced (final 30%): Advanced DP (knapsack, intervals, state machines), Tries, Union-Find, Segment Trees, Greedy, Bit Manipulation
Behavioral + System Design: Spread throughout. 1 system design session every 3 days. Behavioral STAR practice every 2 days.
Mock tests: every 7 days and on the final day."""

    prompt = f"""You are an expert {company} interview coach building a COMPLETE {days_left}-day preparation plan for a {role} candidate.

GOAL: Build a comprehensive, ground-up curriculum that covers EVERYTHING the candidate needs to pass a {company} interview.
DO NOT skip topics because the candidate might already know them. Cover every important area properly.

CANDIDATE LOGISTICS:
- Daily study time: {daily_hours} hours (~{tasks_per_day} tasks/day)
- Target: {company} — {role} position

{dsa_curriculum}

{company.upper()} SPECIFIC FOCUS: {company_values}

AVAILABLE DSA PROBLEMS (you MUST only pick from this list for dsa_problem tasks):
{catalogue}

BUILD RULES:
1. Start from absolute foundations on Day 1 (arrays, basic string problems) and build up progressively.
2. Cover every DSA topic phase — do NOT skip any phase or topic cluster, even "easy" ones.
3. Prioritize problems with higher "asked Nx" counts — they reflect {company}'s real hiring patterns.
4. Every 3rd day: add 1 system design theory/exercise relevant to {company}'s product domain.
5. Every 2nd day: add 1 behavioral practice session with a {company}-specific scenario.
6. Final 20% of days: hard problems, full mock tests, company-specific pattern revision.
7. For dsa_problem tasks: "title" MUST exactly match a problem from the list above.
8. Mock test on final day (mandatory).

Return ONLY a JSON object: {{"tasks": [ ... ]}} where each task is:
{{"day_number": int, "task_type": "dsa_problem"|"theory"|"behavioral"|"project_review"|"mock_test",
  "title": string, "description": string (1 sentence explaining what this builds toward for {company}),
  "priority": 1|2|3, "estimated_minutes": int}}

Generate tasks for ALL {days_left} days (~{tasks_per_day} tasks/day). Cover the complete curriculum — leave nothing out."""

    data = await _ai_json(prompt)
    if not data:
        return None
    tasks = data.get("tasks") if isinstance(data, dict) else (data if isinstance(data, list) else None)
    if not tasks or not isinstance(tasks, list):
        return None

    valid_types = {"dsa_problem", "theory", "behavioral", "project_review", "mock_test"}
    clean = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        tt = t.get("task_type")
        if tt not in valid_types:
            continue
        try:
            day = int(t.get("day_number", 1))
        except (TypeError, ValueError):
            continue
        if day < 1 or day > max(days_left, 1):
            continue
        clean.append({
            "day_number": day,
            "task_type": tt,
            "title": str(t.get("title", "Study task"))[:300],
            "description": str(t.get("description", ""))[:500],
            "priority": t.get("priority", 2) if t.get("priority") in (1, 2, 3) else 2,
            "estimated_minutes": int(t["estimated_minutes"]) if str(t.get("estimated_minutes", "")).isdigit() else 30,
            "metadata": {},
        })
    return clean or None
