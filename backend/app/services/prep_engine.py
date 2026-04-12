"""prep_engine.py — generates personalized study plans based on days, company, role, daily hours"""
from datetime import date, timedelta
from typing import Optional

COMPANY_FOCUS = {
    "google": ["graphs", "dynamic-programming", "system-design", "algorithms"],
    "amazon": ["behavioral", "trees", "system-design", "leadership-principles"],
    "microsoft": ["trees", "dynamic-programming", "oop", "system-design"],
    "flipkart": ["backend", "system-design", "databases", "java"],
    "razorpay": ["backend", "api-design", "databases", "payments"],
    "zepto": ["backend", "redis", "system-design", "databases"],
    "meta": ["graphs", "dynamic-programming", "system-design"],
    "uber": ["system-design", "geospatial", "backend"],
}

def determine_plan_type(days: int) -> str:
    if days <= 1: return "crash_24h"
    if days <= 7: return "fast_track_1w"
    if days <= 21: return "structured_3w"
    return "roadmap_1m_plus"

def tasks_per_day(daily_hours: float) -> int:
    if daily_hours <= 1: return 2
    if daily_hours <= 2: return 3
    if daily_hours <= 3: return 4
    return 5

def _t(day, type_, title, desc, priority=2, mins=30, meta=None):
    return {"day_number": day, "task_type": type_, "title": title, "description": desc,
            "priority": priority, "estimated_minutes": mins, "metadata": meta or {}}

def build_crash(company=None):
    return [
        _t(1,"dsa_problem","Two Sum","O(n) hash map solution. Must know cold.",1,20),
        _t(1,"dsa_problem","Valid Parentheses","Stack pattern — appears in every interview.",1,20),
        _t(1,"dsa_problem","Reverse Linked List","Pointer manipulation fundamentals.",1,20),
        _t(1,"dsa_problem","Binary Search","Master the template — lo, hi, mid invariant.",1,20),
        _t(1,"dsa_problem","Maximum Subarray","Kadane's — simplest DP pattern.",1,20),
        _t(1,"dsa_problem","Climbing Stairs","Fibonacci DP — explains memoization.",1,15),
        _t(1,"dsa_problem","Number of Islands","Grid BFS/DFS — mark visited.",1,25),
        _t(1,"dsa_problem","LRU Cache","HashMap + DoublyLinkedList. Design classic.",1,30),
        _t(1,"theory","OS: Process vs Thread, Deadlock","Core CS concepts asked everywhere.",1,20),
        _t(1,"theory","DBMS: ACID, Indexing, Joins","SQL and transaction questions.",1,20),
        _t(1,"behavioral","Tell me about yourself (2-min pitch)","Crisp, confident, tailored to role.",1,15),
        _t(1,"behavioral","Your biggest technical challenge","STAR format — specific impact.",1,15),
        _t(1,"project_review","Resume walkthrough — practice aloud","Say it out loud 3 times.",1,20),
        _t(1,"mock_test","Timed mock: 2 mediums in 45 min","Real interview simulation.",1,45),
    ]

def build_fast_track(days, company=None):
    schedule = [
        ("Arrays & Strings", ["Two Sum","Best Time to Buy/Sell Stock","Longest Substring Without Repeating","Product of Array Except Self"], "Sliding window and hash map patterns."),
        ("Linked Lists & Stacks", ["Reverse Linked List","Merge Two Sorted Lists","Valid Parentheses","Min Stack"], "Pointer manipulation and monotonic stacks."),
        ("Trees & Recursion", ["Max Depth of Binary Tree","Invert Binary Tree","LCA of BST","Path Sum"], "Recursive tree thinking — base case + return value."),
        ("Graphs & BFS/DFS", ["Number of Islands","Clone Graph","Course Schedule","Pacific Atlantic"], "Graph representations — adjacency list, visited set."),
        ("Dynamic Programming", ["Climbing Stairs","Coin Change","Longest Common Subseq","House Robber"], "Recurrence relations — top-down vs bottom-up."),
        ("System Design", ["Design URL Shortener","Design LRU Cache","Rate Limiter"], "Requirements → components → scale. Think aloud."),
        ("Full Mock Test", [], "90-min mock: 2 coding + 1 system design. Treat it real."),
    ]
    tasks = []
    for i, (theme, problems, note) in enumerate(schedule[:min(days, 7)]):
        d = i + 1
        if d == 7:
            tasks.append(_t(7,"mock_test","Final Mock Interview",schedule[6][2],1,90))
        else:
            tasks.append(_t(d,"dsa_problem",f"{theme} — Problem Set",f"Solve: {', '.join(problems)}. {note}",1,60,{"problems":problems,"theme":theme}))
            tasks.append(_t(d,"theory",f"Theory: Core CS concepts for Day {d}","OS/DBMS/CN rotation.",2,20))
            tasks.append(_t(d,"behavioral",f"Behavioral prep — Day {d}","One STAR story, polished.",2,15))
    return tasks

def build_3w(days, company=None):
    tasks = []
    w1 = [
        (1,"Arrays & Hashing",["Two Sum","Valid Anagram","Group Anagrams","Top K Frequent"]),
        (2,"Two Pointers & Sliding Window",["3Sum","Container With Most Water","Longest Substring"]),
        (3,"Stacks & Queues",["Valid Parentheses","Min Stack","Daily Temperatures","Evaluate RPN"]),
        (4,"Binary Search",["Binary Search","Search Rotated Array","Find Min in Rotated Array"]),
        (5,"Linked Lists",["Reverse Linked List","Merge Sorted Lists","Detect Cycle","LRU Cache"]),
        (6,"Trees Foundations",["Max Depth","Invert Tree","Same Tree","BST Validation"]),
    ]
    for day, theme, problems in w1:
        tasks.append(_t(day,"dsa_problem",f"W1D{day}: {theme}",f"Solve: {', '.join(problems)}",1,60,{"problems":problems}))
        tasks.append(_t(day,"theory","OS Fundamentals","Process scheduling, memory management.",2,20))
    tasks.append(_t(7,"mock_test","Week 1 Mock — 30 min","1 easy + 1 medium, timed.",1,30))
    w2 = [
        (8,"Trees Advanced + BST",["BST Kth Smallest","Build Tree from Traversal","Max Path Sum"]),
        (9,"Heaps",["Kth Largest","Merge K Sorted Lists","Find Median from Stream"]),
        (10,"Graphs BFS/DFS",["Number of Islands","Clone Graph","Pacific Atlantic"]),
        (11,"Topological Sort",["Course Schedule","Alien Dictionary"]),
        (12,"DP Foundations",["Climbing Stairs","House Robber","Coin Change"]),
        (13,"DP Advanced",["Longest Common Subseq","Edit Distance","Word Break"]),
    ]
    for day, theme, problems in w2:
        if day <= days:
            tasks.append(_t(day,"dsa_problem",f"W2D{day-7}: {theme}",f"Solve: {', '.join(problems)}",1,60,{"problems":problems}))
            tasks.append(_t(day,"theory","DBMS & CN Deep Dive","ACID, indexes, TCP/IP, HTTP/2.",2,20))
    if 14 <= days:
        tasks.append(_t(14,"mock_test","Week 2 Mock — 60 min","2 mediums timed.",1,60))
        tasks.append(_t(14,"behavioral","STAR Stories Complete","All 5 stories polished.",1,30))
    w3 = [
        (15,"Advanced Graphs",["Redundant Connection","Number of Connected Components"]),
        (16,"Tries",["Implement Trie","Word Search II"]),
        (17,"Backtracking",["Subsets","Permutations","N-Queens"]),
        (18,"Greedy",["Jump Game","Gas Station","Task Scheduler"]),
        (19,"System Design I","Design Twitter/Instagram feed — sharding, CDN, eventual consistency."),
        (20,"System Design II","Design distributed cache + rate limiter."),
    ]
    for item in w3:
        day = item[0]
        if day <= days:
            if len(item) == 3 and isinstance(item[2], list):
                _, theme, problems = item
                tasks.append(_t(day,"dsa_problem",f"W3D{day-14}: {theme}",f"Solve: {', '.join(problems)}",1,60,{"problems":problems}))
            else:
                _, theme, desc = item
                tasks.append(_t(day,"theory",theme,desc,1,45))
    if 21 <= days:
        tasks.append(_t(21,"mock_test","Final Full Mock","90 min: 2 coding + system design + behavioral. Go.",1,90))
    return tasks

def build_extended(days, company=None):
    base = build_3w(min(days, 21), company)
    extras = ["Advanced System Design Patterns","Concurrency & Multithreading","SQL Window Functions & CTEs",
              "OOP Design: Parking Lot, Elevator","REST API Design & Versioning","Cloud Architecture Basics",
              "Microservices & Event-Driven Architecture","Mock Marathon: 3 Full Interview Rounds"]
    for i, topic in enumerate(extras):
        day = 22 + i
        if day <= days:
            base.append(_t(day,"theory",topic,f"Deep dive: {topic}",2,45))
    return base

def generate_plan(days_left, target_company=None, target_role=None, interview_date=None, daily_hours=2.0):
    plan_type = determine_plan_type(days_left)
    today = date.today()
    end = interview_date or (today + timedelta(days=max(days_left,1)))
    if plan_type == "crash_24h": tasks = build_crash(target_company)
    elif plan_type == "fast_track_1w": tasks = build_fast_track(days_left, target_company)
    elif plan_type == "structured_3w": tasks = build_3w(days_left, target_company)
    else: tasks = build_extended(days_left, target_company)
    return {
        "plan_type": plan_type, "start_date": today, "end_date": end,
        "total_days": days_left, "target_company": target_company, "target_role": target_role,
        "plan_structure": {"plan_type": plan_type, "total_tasks": len(tasks),
                           "company_overlay": COMPANY_FOCUS.get((target_company or "").lower(), [])},
        "tasks": tasks,
    }
