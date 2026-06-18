"""code_executor.py"""
import re, asyncio, httpx, base64
from typing import Optional
from app.config import settings

LANGUAGE_IDS = {"python":71,"cpp":54,"java":62,"javascript":63}
STARTER_CODE = {
    "python": "def solution():\n    # Write your solution here\n    pass\n\n# Test\nprint(solution())\n",
    "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    // Write your solution here\n    return 0;\n}\n",
    "java": "public class Solution {\n    public static void main(String[] args) {\n        // Write your solution here\n    }\n}\n",
    "javascript": "function solution() {\n    // Write your solution here\n}\n\nconsole.log(solution());\n",
}

def estimate_complexity(code: str, language: str) -> str:
    max_depth = 0; current_depth = 0
    if language == "python":
        for line in code.split("\n"):
            s = line.lstrip()
            if s.startswith("for ") or s.startswith("while "): current_depth += 1; max_depth = max(max_depth, current_depth)
            if len(line) - len(line.lstrip()) == 0 and current_depth > 0: current_depth = 0
    else:
        d = 0
        for line in code.split("\n"):
            s = line.strip()
            if any(s.startswith(k) for k in ["for","while"]): d = d + 1; max_depth = max(max_depth, d)
            d += s.count("{") - s.count("}")
    if re.search(r'\.sort\(|Arrays\.sort|sort\(|std::sort', code): return "O(n log n)"
    # Recursion heuristic: a function that calls itself by name (captured + backreferenced).
    if re.search(r'def (\w+)\s*\([^)]*\):[\s\S]*?\b\1\s*\(', code) or \
       re.search(r'function (\w+)\s*\([^)]*\)[\s\S]*?\b\1\s*\(', code):
        return "O(2^n) or O(n)"
    return {0:"O(1)",1:"O(n)",2:"O(n²)",3:"O(n³)"}.get(min(max_depth,3),"O(n)")

def score_submission(passed, total, code, language, complexity, optimal) -> tuple:
    score = 0.0; fb = []
    if total > 0: score += (passed/total)*60
    if re.search(r'#|//|/\*', code): score += 5; fb.append("Code is commented — good practice.")
    lines = [l for l in code.split("\n") if l.strip()]
    if 5 <= len(lines) <= 80: score += 5
    if re.search(r'def |function |void |int \w+\(', code): score += 5; fb.append("Uses functions — modular code.")
    if re.search(r'== \[\]|len\(\w+\) == 0|\.empty\(\)|isEmpty\(\)', code): score += 5; fb.append("Handles empty input.")
    if re.search(r'none|null|nullptr', code.lower()): score += 5; fb.append("Handles null/None.")
    if optimal and complexity:
        if complexity.lower() == optimal.lower(): score += 5; fb.append(f"Optimal complexity: {complexity}.")
        elif "n²" in complexity or "n^2" in complexity: score -= 5; fb.append(f"⚠️ {complexity} detected. Optimal is {optimal}.")
    score = max(0, min(100, score))
    prefix = "✅ All tests passed!" if passed == total and total > 0 else f"❌ {passed}/{total} tests passed."
    return round(score,1), [prefix] + fb, []

async def submit_to_judge0(code, language, stdin="") -> dict:
    lid = LANGUAGE_IDS.get(language, 71)
    headers = {"X-RapidAPI-Key": settings.JUDGE0_API_KEY, "X-RapidAPI-Host": settings.JUDGE0_HOST, "Content-Type": "application/json"}
    payload = {"source_code": base64.b64encode(code.encode()).decode(), "language_id": lid,
               "stdin": base64.b64encode(stdin.encode()).decode() if stdin else "", "base64_encoded": True}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"https://{settings.JUDGE0_HOST}/submissions?base64_encoded=true", json=payload, headers=headers)
        r.raise_for_status()
        token = r.json().get("token")
        for _ in range(10):
            await asyncio.sleep(2)
            sr = await client.get(f"https://{settings.JUDGE0_HOST}/submissions/{token}?base64_encoded=true", headers=headers)
            d = sr.json()
            if d.get("status",{}).get("id",0) > 2:
                stdout = base64.b64decode(d.get("stdout") or "").decode() if d.get("stdout") else ""
                return {"stdout": stdout.strip(), "status": d.get("status",{}).get("description",""), "time": d.get("time"), "memory": d.get("memory")}
    return {"stdout":"","status":"Time Limit Exceeded","time":None,"memory":None}

async def run_python_locally(code, stdin="", timeout=5) -> dict:
    """
    Dev-only: actually executes Python in an isolated subprocess with a hard timeout.
    Real execution — stdout is compared against expected output by the caller.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "-I", "-c", code,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except Exception:
        return {"stdout": "", "status": "Runtime Error", "time": None, "memory": None, "executed": True}
    try:
        out, err = await asyncio.wait_for(proc.communicate(stdin.encode()), timeout=timeout)
    except asyncio.TimeoutError:
        try: proc.kill()
        except Exception: pass
        return {"stdout": "", "status": "Time Limit Exceeded", "time": timeout * 1000, "memory": None, "executed": True}
    status = "Accepted" if proc.returncode == 0 else "Runtime Error"
    return {"stdout": out.decode(errors="replace"), "status": status, "time": None, "memory": None, "executed": True}


def _execution_mode(language: str) -> str:
    """Decides how (or whether) we can really run this submission. No faking."""
    if settings.JUDGE0_API_KEY:
        return "judge0"
    if settings.ALLOW_LOCAL_EXECUTION and language == "python":
        return "local"
    return "none"


async def run_tests(code, language, test_cases) -> tuple:
    """Runs each test case for real. Returns (passed, total, results, avg_t, avg_m, executed)."""
    passed = 0; results = []; total_t = 0.0; total_m = 0.0
    mode = _execution_mode(language)
    if mode == "none":
        # Honest: we cannot verify this submission. Report it plainly, fake nothing.
        return 0, len(test_cases), [], 0.0, 0.0, False

    for i, tc in enumerate(test_cases[:10]):
        tin = str(tc.get("input", ""))
        expected = str(tc.get("expected_output", "")).strip()
        try:
            if mode == "judge0":
                result = await submit_to_judge0(code, language, tin)
            else:
                result = await run_python_locally(code, tin)
        except Exception:
            result = {"stdout": "", "status": "Runtime Error", "time": None, "memory": None}
        actual = (result.get("stdout") or "").strip()
        test_passed = actual == expected and result.get("status") not in ("Time Limit Exceeded", "Runtime Error")
        if test_passed: passed += 1
        if result.get("time"):
            # Judge0 reports seconds; local reports milliseconds. Normalise to ms.
            total_t += float(result["time"]) * (1000 if mode == "judge0" else 1)
        if result.get("memory"): total_m += float(result["memory"])
        results.append({"test_case": i + 1, "input": tin[:200], "expected": expected[:200],
                        "actual": actual[:200], "passed": test_passed, "status": result.get("status", "")})
    n = len(test_cases) or 1
    return passed, len(test_cases), results, total_t / n, total_m / n, True


async def execute_code(code, language, problem) -> dict:
    test_cases = problem.get("test_cases", [])
    optimal = problem.get("optimal_complexity")
    passed, total, test_results, avg_t, avg_m, executed = await run_tests(code, language, test_cases)
    complexity = estimate_complexity(code, language)

    if not executed:
        # Code was saved but never verified. Be transparent; do not award a passing score.
        return {
            "status": "wrong_answer", "tests_passed": 0, "tests_total": total, "test_results": [],
            "score": 0.0, "executed": False,
            "feedback": "⚠️ Code execution isn't configured, so your solution was saved but NOT verified against the test cases. Enable Judge0 (or local execution in dev) to get real results.",
            "complexity_estimate": complexity, "edge_cases_handled": [],
            "execution_time_ms": 0.0, "memory_used_kb": 0.0,
        }

    score, fb, edge = score_submission(passed, total, code, language, complexity, optimal)
    status = "accepted" if passed == total and total > 0 else ("tle" if avg_t > 2000 else "wrong_answer")
    return {"status": status, "tests_passed": passed, "tests_total": total, "test_results": test_results,
            "score": score, "executed": True, "feedback": " ".join(fb), "complexity_estimate": complexity,
            "edge_cases_handled": edge, "execution_time_ms": round(avg_t, 2), "memory_used_kb": round(avg_m, 2)}
