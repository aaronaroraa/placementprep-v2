import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api', timeout: 40000 })

api.interceptors.request.use((config) => {
  const t = localStorage.getItem('access_token')
  if (t) config.headers['Authorization'] = `Bearer ${t}`
  return config
})

let refreshing = false, queue = []
const flush = (err, token) => { queue.forEach(p => err ? p.reject(err) : p.resolve(token)); queue = [] }

api.interceptors.response.use(r => r, async (error) => {
  const orig = error.config
  if (error.response?.status !== 401 || orig._retry) return Promise.reject(error)
  if (refreshing) return new Promise((res, rej) => queue.push({ resolve: res, reject: rej }))
    .then(t => { orig.headers['Authorization'] = `Bearer ${t}`; return api(orig) })
  orig._retry = true; refreshing = true
  const rt = localStorage.getItem('refresh_token')
  if (!rt) { clearAuth(); window.location.href = '/'; return Promise.reject(error) }
  try {
    const { data } = await axios.post('/api/auth/refresh', { refresh_token: rt })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    flush(null, data.access_token)
    orig.headers['Authorization'] = `Bearer ${data.access_token}`
    return api(orig)
  } catch (e) { flush(e, null); clearAuth(); window.location.href = '/'; return Promise.reject(e) }
  finally { refreshing = false }
})

export const clearAuth = () => { localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token') }
export const isAuthed = () => !!localStorage.getItem('access_token')

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true' || (import.meta.env.DEV && !import.meta.env.VITE_API_URL);
const delay = ms => new Promise(r => setTimeout(r, ms))

export const authAPI = USE_MOCK ? {
  register: async d => { await delay(600); const tk = 'mock_at_' + (d.email || 'user'); return { data: { access_token: tk, refresh_token: 'mock_rt' } } },
  login: async d => { await delay(600); const tk = 'mock_at_' + (d.email || 'user'); return { data: { access_token: tk, refresh_token: 'mock_rt' } } },
  refresh: async rt => { await delay(300); return { data: { access_token: localStorage.getItem('access_token') || 'mock_at', refresh_token: 'mock_rt' } } },
  googleUrl: async () => { await delay(300); return { data: { url: '/auth/callback?access_token=mock_at_google&refresh_token=mock_rt&is_new=True' } } },
} : {
  register: d => api.post('/auth/register', d),
  login: d => api.post('/auth/login', d),
  refresh: rt => api.post('/auth/refresh', { refresh_token: rt }),
  googleUrl: () => api.get('/auth/google'),
}

// --- CURRICULUM MOCK STATE ---
const CURRICULUM = [
  { day: 1, title: 'Advanced Graphs & DP', tasks: [
    { id: 101, title: 'Alien Dictionary', description: 'Topological sort on directed graph', task_type: 'dsa_problem', priority: 1, estimated_minutes: 45 },
    { id: 102, title: 'Burst Balloons', description: 'Hard interval DP problem', task_type: 'dsa_problem', estimated_minutes: 45 },
    { id: 103, title: 'Behavioral: Conflict', description: 'Tell me about a time you disagreed with a PM', task_type: 'behavioral', estimated_minutes: 15 }
  ]},
  { day: 2, title: 'System Design: Scale', tasks: [
    { id: 201, title: 'Design Global Chat', description: 'WebSocket scale, Cassandra, Message Queues', task_type: 'mock_test', priority: 1, estimated_minutes: 60 },
    { id: 202, title: 'Theory: Consistency Models', description: 'CAP, PACELC, Eventual vs Strong Consistency', task_type: 'theory', estimated_minutes: 20 },
    { id: 203, title: 'LFU Cache', description: 'O(1) Data structure design', task_type: 'dsa_problem', estimated_minutes: 40 }
  ]},
  { day: 3, title: 'Hard Trees & Backtracking', tasks: [
    { id: 301, title: 'Serialize & Deserialize N-ary Tree', description: 'State machine tree parsing', task_type: 'dsa_problem', priority: 1, estimated_minutes: 40 },
    { id: 302, title: 'N-Queens II', description: 'Optimized backtracking with bitmasks', task_type: 'dsa_problem', estimated_minutes: 35 },
    { id: 303, title: 'Concurrency: Dining Philosophers', description: 'Deadlock avoidance in multi-threading', task_type: 'dsa_problem', estimated_minutes: 30 }
  ]},
  { day: 4, title: 'Engineering Deep Dive', tasks: [
    { id: 401, title: 'Design Distributed Ticket System', description: 'Ticketmaster scale, concurrency issues', task_type: 'mock_test', priority: 1, estimated_minutes: 60 },
    { id: 402, title: 'Regular Expression Matching', description: '2D Dynamic Programming', task_type: 'dsa_problem', estimated_minutes: 45 }
  ]}
]

const getTotalTasksCount = () => CURRICULUM.reduce((acc, d) => acc + d.tasks.length, 0)

const getTokenId = () => {
  const token = localStorage.getItem('access_token') || 'default'
  return token.replace('mock_at_', '')
}

const getProgressState = () => {
  const json = localStorage.getItem(`mock_curriculum_state_${getTokenId()}`)
  if (json) return JSON.parse(json)
  return { currentDay: 1, completedTaskIds: [] }
}

const saveProgressState = (state) => {
  localStorage.setItem(`mock_curriculum_state_${getTokenId()}`, JSON.stringify(state))
}

const getOnboardingState = () => localStorage.getItem(`mock_onboarded_${getTokenId()}`) === '1'
const setOnboardingState = () => localStorage.setItem(`mock_onboarded_${getTokenId()}`, '1')

export const userAPI = USE_MOCK ? {
  me: async () => { await delay(300); return { data: { id: 1, full_name: 'Demo User', email: `${getTokenId()}@example.com`, target_company: 'Google', target_role: 'Frontend Engineer', onboarding_completed: getOnboardingState() } } },
  update: async d => { await delay(400); return { data: { ...d, id: 1 } } },
  onboarding: async d => { await delay(600); setOnboardingState(); return { data: { success: true } } },
  dashboard: async () => { 
    await delay(500); 
    const state = getProgressState()
    const currentDayData = CURRICULUM.find(c => c.day === state.currentDay) || CURRICULUM[CURRICULUM.length - 1]
    const total = getTotalTasksCount()
    const compPct = Math.min(100, (state.completedTaskIds.length / total) * 100)
    
    const today_tasks = currentDayData.tasks.map(t => ({ ...t, completed: state.completedTaskIds.includes(t.id) }))
    
    return { data: { 
      user: { full_name: 'Demo User', target_company: 'Google', target_role: 'Frontend Engineer', calendar_connected: true },
      days_left: 14 - state.currentDay + 1, current_day: state.currentDay, total_days: CURRICULUM.length, 
      streak_days: state.currentDay, problems_solved: state.completedTaskIds.length, 
      completion_pct: compPct, readiness_score: 40 + (compPct * 0.5), plan_id: 1,
      today_tasks
    } } 
  },
  completeTask: async taskId => { 
    await delay(300); 
    const state = getProgressState()
    if (!state.completedTaskIds.includes(taskId)) {
      state.completedTaskIds.push(taskId)
      saveProgressState(state)
    }
    const compPct = Math.min(100, (state.completedTaskIds.length / getTotalTasksCount()) * 100)
    return { data: { completion_pct: compPct } } 
  },
  advanceDay: async () => {
    await delay(400);
    const state = getProgressState()
    if (state.currentDay < CURRICULUM.length) {
      state.currentDay += 1;
      saveProgressState(state)
    }
    return { data: { success: true, new_day: state.currentDay } }
  },
  curriculum: async () => {
    await delay(400);
    const state = getProgressState();
    return { data: { current_day: state.currentDay, completed_task_ids: state.completedTaskIds, days: CURRICULUM } }
  },
  connectCalendar: async tokenData => { await delay(400); return { data: { success: true } } },
} : {
  me: () => api.get('/users/me'),
  update: d => api.put('/users/me', d),
  onboarding: d => api.post('/users/onboarding', d),
  dashboard: () => api.get('/users/dashboard'),
  curriculum: () => api.get('/users/curriculum'),
  completeTask: taskId => api.post('/users/tasks/complete', { task_id: taskId }),
  advanceDay: () => api.post('/users/tasks/advance-day'),
  connectCalendar: tokenData => api.post('/users/calendar/connect', { token_data: tokenData }),
}

export const resumeAPI = USE_MOCK ? {
  upload: async file => { await delay(1000); return { data: { id: 101, filename: file.name, skills_extracted: ['React', 'JavaScript', 'Node.js'], skill_gaps: ['System Design', 'Redis'] } } },
  latest: async () => { await delay(300); return { data: { id: 101, parsed_skills: ['React', 'JavaScript'] } } },
  generateQuestions: async () => { await delay(1500); return { data: { questions: ['Tell me about a time you used React hooks.', 'How do you structure a Node.js app?'] } } },
} : {
  upload: file => { const fd = new FormData(); fd.append('file', file); return api.post('/resume/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 60000 }) },
  latest: () => api.get('/resume/latest'),
  generateQuestions: () => api.post('/resume/generate-questions'),
}

export const codingAPI = USE_MOCK ? {
  list: async p => { await delay(400); return { data: [{ id: 101, title: 'Two Sum', difficulty: 'easy', times_asked: 42, tags: ['Array', 'Hash Table'] }, { id: 201, title: 'Valid Palindrome', difficulty: 'easy', times_asked: 28, tags: ['Two Pointers'] }] } },
  get: async id => { await delay(300); return { data: { id, title: 'Problem Tracker', description: 'Given inputs...', difficulty: 'easy', optimal_complexity: 'O(N)', constraints: '1 <= nums.length <= 10^4', hints: ['Try hash map'], starter_code: { python: 'def solve():\n    pass\n', javascript: 'function solve() {\n\n}' } } } },
  submit: async d => { await delay(1200); return { data: { status: 'accepted', runtime: '52ms', memory: '42.1MB', tests_passed: 12, tests_total: 12, score: 100, complexity_estimate: 'O(N)', optimal_complexity: 'O(N)', feedback: 'Optimal solution.' } } },
  submissions: async (limit=20) => { await delay(300); return { data: [{ id: 1, problem_id: 101, status: 'accepted', created_at: new Date().toISOString() }] } },
} : {
  list: p => api.get('/coding/problems', { params: p }),
  get: id => api.get(`/coding/problems/${id}`),
  submit: d => api.post('/coding/submit', d),
  submissions: (limit=20) => api.get('/coding/submissions', { params: { limit } }),
}

export const chatAPI = USE_MOCK ? {
  send: async d => { await delay(800); return { data: { reply: "That's a good approach. How would you optimize the space complexity?" } } },
  end: async sessionId => { await delay(300); return { data: { feedback: "Strong problem solving skills, but need to communicate tradeoffs earlier." } } },
} : {
  send: d => api.post('/chat/message', d),
  end: sessionId => api.post('/chat/end-session', { session_id: sessionId }),
}

export const mockAPI = USE_MOCK ? {
  start: async d => { 
    await delay(600); 
    const isGoogle = Math.random() > 0.5;
    const company = isGoogle ? "Google" : "Meta";
    const qOptions = [
      `Since you're targeting ${company}, let's start with a question asked 14 times last month in their loops: Tell me about a time you had a fundamental disagreement with a Product Manager. How did you resolve the conflict?`,
      `Welcome. For a Frontend Engineering role at ${company}, you need to understand core architecture. This was asked last week: Walk me through exactly how you would architect a client-side routing library from scratch without React Router.`,
      `Let's begin your ${company} mock interview. A very common recent question is: Tell me about a heavily-invested project that ultimately failed. What did you learn and how did you pivot?`
    ];
    return { data: { mock_id: '123', total_questions: 3, first_question: qOptions[Math.floor(Math.random() * qOptions.length)] } } 
  },
  answer: async d => { 
    await delay(1000); 
    if (d.question_index === 2) { 
      return { data: { is_complete: true, interviewer_response: "That's a solid, comprehensive answer. I have all I need.", overall_score: 88, feedback_summary: "Great structural approach and communication depth. You framed the tradeoffs exactly how they expect in tier-1 interviews." } } 
    } else { 
      return { data: { is_complete: false, interviewer_response: "That makes sense. Let's pivot slightly.", next_question_index: d.question_index + 1, next_question: "Following up on that, an overarching theme in tech interviews right now is resilience. How would you scale that exact approach if network latency unexpectedly spiked by 500ms between your regional microservices?" } } 
    } 
  },
  history: async () => { await delay(400); return { data: { sessions: [] } } },
} : {
  start: d => api.post('/mock/start', d),
  answer: d => api.post('/mock/answer', d),
  history: () => api.get('/mock/history'),
}

export const analyticsAPI = USE_MOCK ? {
  dashboard: async (days=14) => { 
    await delay(500)
    const state = getProgressState()
    const history = []
    
    // Simulate progression incrementally based on `currentDay` and array mapping
    const progressPerDay = state.completedTaskIds.length / Math.max(1, state.currentDay)
    
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date()
      d.setDate(d.getDate() - i)
      
      const simulatedDayIndex = Math.max(1, state.currentDay - Math.min(state.currentDay - 1, i))
      let rs = 40 + (simulatedDayIndex * 6)
      let acc = Math.min(100, 50 + (simulatedDayIndex * 8))
      let solvedCount = Math.floor(simulatedDayIndex * progressPerDay)
      
      history.push({ date: d.toISOString(), readiness_score: rs, accuracy_rate: acc, problems_solved: solvedCount })
    }
    
    const finalScore = 40 + (state.currentDay * 6) + (progressPerDay * 2)
    return { data: {
      current: { 
        readiness_score: finalScore, 
        total_problems_solved: state.completedTaskIds.length, 
        accuracy_rate: Math.min(100, 50 + (state.currentDay * 8)), 
        improvement_trend: 'improving', streak_days: state.currentDay, 
        weak_areas: ['Dynamic Programming', 'Graph Traversal'], 
        strong_areas: ['Arrays', 'Two Pointers'], 
        topic_scores: { "array": 80 + state.currentDay * 2, "dp": 45, "graphs": 50, "sys_design": 60 + state.currentDay } 
      },
      history
    } }
  },
} : {
  dashboard: (days=14) => api.get('/analytics/dashboard', { params: { days } }),
}

export default api
