import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Editor from '@monaco-editor/react'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'
import { FiPlay, FiRefreshCw, FiChevronDown, FiCheck, FiX, FiSend, FiAlertCircle } from 'react-icons/fi'
import { codingAPI, chatAPI } from '../api'
import { Navbar, Spinner, TypingDots, Label } from '../components'

const LANGS = ['python', 'cpp', 'java', 'javascript']
const DIFF_COLOR = { easy: 'var(--green)', medium: 'var(--amber)', hard: 'var(--red)' }

// Interviewer interrupts based on code activity
function useInterrupter(code, problem, onInterrupt, enabled) {
  const lastLen = useRef(0)
  const timer = useRef(null)

  useEffect(() => {
    if (!enabled || !problem || !code) return
    const diff = Math.abs(code.length - lastLen.current)
    if (diff > 50) {
      lastLen.current = code.length
      clearTimeout(timer.current)
      timer.current = setTimeout(() => {
        const intros = [
          `Walk me through what you're doing here.`,
          `You're ${code.split('\n').length} lines in — talk me through your approach.`,
          `I see you're using ${code.includes('dict') || code.includes('map') || code.includes('Map') ? 'a hash map' : 'this structure'} — why?`,
          `Quick check: what's your current time complexity?`,
        ]
        onInterrupt(intros[Math.floor(Math.random() * intros.length)])
      }, 18000) // interrupt after 18s of silence
    }
    return () => clearTimeout(timer.current)
  }, [code, enabled])
}

export default function Coding() {
  const [problems, setProblems] = useState([])
  const [problem, setProblem] = useState(null)
  const [lang, setLang] = useState('python')
  const [code, setCode] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [tab, setTab] = useState('problem')
  const [showList, setShowList] = useState(false)
  const [filter, setFilter] = useState('')
  const [messages, setMessages] = useState([{ role: 'assistant', text: "I'm your interviewer for this session. Before you start coding — walk me through your initial approach." }])
  const [input, setInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const endRef = useRef(null)

  useEffect(() => { loadProblems() }, [])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, chatLoading])

  const loadProblems = async () => {
    try {
      const r = await codingAPI.list({})
      setProblems(r.data)
      if (r.data.length > 0) selectProblem(r.data[0])
    } catch { toast.error('Failed to load problems') }
  }

  const selectProblem = async (p) => {
    try {
      const r = await codingAPI.get(p.id)
      setProblem(r.data)
      setCode(r.data.starter_code?.[lang] || '')
      setResult(null)
      setTab('problem')
      setShowList(false)
      setMessages([{ role: 'assistant', text: `Alright. "${r.data.title}" — ${r.data.difficulty} difficulty. Before you touch the keyboard, tell me your initial approach.` }])
    } catch { toast.error('Failed to load problem') }
  }

  const changeLang = l => { setLang(l); if (problem) setCode(problem.starter_code?.[l] || '') }

  const submit = async () => {
    if (!problem || !code.trim()) { toast.error('Write some code first'); return }
    setSubmitting(true); setTab('results')
    try {
      const r = await codingAPI.submit({ problem_id: problem.id, code, language: lang })
      setResult(r.data)
      // Interviewer reacts to submission
      const msg = r.data.status === 'accepted'
        ? `${r.data.tests_passed}/${r.data.tests_total} tests passed. ${r.data.complexity_estimate} time complexity — ${r.data.complexity_estimate === problem?.optimal_complexity ? 'that\'s optimal. Good.' : `optimal is ${problem?.optimal_complexity}. How would you get there?`}`
        : `${r.data.tests_passed}/${r.data.tests_total} tests passed. ${r.data.feedback?.split('.')[0]}. Walk me through why you think the remaining tests are failing.`
      setMessages(m => [...m, { role: 'assistant', text: msg }])
    } catch { toast.error('Submission failed') }
    finally { setSubmitting(false) }
  }

  const sendChat = async (msg) => {
    const text = (msg || input).trim()
    if (!text) return
    setInput('')
    setMessages(m => [...m, { role: 'user', text }])
    setChatLoading(true)
    try {
      const r = await chatAPI.send({ message: text, problem_id: problem?.id, current_code: code, context_type: 'coding' })
      setMessages(m => [...m, { role: 'assistant', text: r.data.reply }])
    } catch {
      setMessages(m => [...m, { role: 'assistant', text: 'What\'s your current approach? Think out loud.' }])
    } finally { setChatLoading(false) }
  }

  useInterrupter(code, problem, (msg) => {
    setMessages(m => [...m, { role: 'assistant', text: msg }])
  }, !!problem)

  const filtered = problems.filter(p => !filter || p.title.toLowerCase().includes(filter.toLowerCase()) || p.difficulty === filter)

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--void)', overflow: 'hidden' }}>
      <Navbar />
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* LEFT — Problem panel */}
        <div style={{ width: 380, flexShrink: 0, borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Problem selector */}
          <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
            <button onClick={() => setShowList(s => !s)} style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: 'var(--raised)', border: '1px solid var(--border)', borderRadius: 8, cursor: 'pointer', color: 'var(--text-1)' }}>
              <span style={{ fontSize: 12, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, textAlign: 'left' }}>{problem?.title || 'Select a problem'}</span>
              <FiChevronDown size={13} style={{ transform: showList ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s', flexShrink: 0, marginLeft: 8 }} />
            </button>
            <AnimatePresence>
              {showList && (
                <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}
                  style={{ marginTop: 6, background: 'var(--raised)', border: '1px solid var(--border)', borderRadius: 10, overflow: 'hidden', maxHeight: 320, overflowY: 'auto', zIndex: 20, position: 'relative' }}>
                  <div style={{ padding: '6px 8px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 5 }}>
                    <input value={filter} onChange={e => setFilter(e.target.value)} placeholder="Search…" className="input" style={{ padding: '5px 10px', fontSize: 11 }} />
                    {['easy','medium','hard'].map(d => (
                      <button key={d} onClick={() => setFilter(f => f === d ? '' : d)}
                        style={{ fontSize: 10, fontWeight: 700, padding: '4px 9px', borderRadius: 6, border: 'none', cursor: 'pointer', background: filter === d ? `${DIFF_COLOR[d]}22` : 'var(--raised)', color: DIFF_COLOR[d] }}>
                        {d}
                      </button>
                    ))}
                  </div>
                  {filtered.map(p => (
                    <button key={p.id} onClick={() => selectProblem(p)} style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: problem?.id === p.id ? 'var(--indigo-dim)' : 'transparent', border: 'none', cursor: 'pointer', textAlign: 'left', borderBottom: '1px solid var(--border)' }}>
                      <span style={{ width: 7, height: 7, borderRadius: '50%', background: DIFF_COLOR[p.difficulty], flexShrink: 0 }} />
                      <span style={{ fontSize: 12, color: 'var(--text-1)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title}</span>
                      <span style={{ fontSize: 9, color: 'var(--text-3)' }}>{p.times_asked}×</span>
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
            {['problem', 'results'].map(t => (
              <button key={t} onClick={() => setTab(t)} style={{ flex: 1, padding: '9px', fontSize: 11, fontWeight: 600, border: 'none', cursor: 'pointer', background: 'transparent', color: tab === t ? 'var(--indigo)' : 'var(--text-3)', borderBottom: tab === t ? '2px solid var(--indigo)' : '2px solid transparent', textTransform: 'uppercase', letterSpacing: 0.8 }}>
                {t}
              </button>
            ))}
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
            {tab === 'problem' && problem && (
              <>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
                  <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, color: 'var(--text-1)', flex: 1 }}>{problem.title}</h2>
                  <span className={`badge badge-${problem.difficulty}`}>{problem.difficulty}</span>
                </div>
                {problem.company_tags?.length > 0 && (
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 12 }}>
                    {problem.company_tags.slice(0, 5).map(c => <span key={c} className="badge badge-subtle">{c}</span>)}
                  </div>
                )}
                <div style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.75, whiteSpace: 'pre-wrap', marginBottom: 16 }}>{problem.description}</div>
                {problem.constraints && (
                  <div style={{ padding: '10px 12px', borderRadius: 8, background: 'var(--raised)', border: '1px solid var(--border)', marginBottom: 14 }}>
                    <Label>CONSTRAINTS</Label>
                    <pre style={{ fontSize: 11, color: 'var(--text-3)', fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap', margin: 0 }}>{problem.constraints}</pre>
                  </div>
                )}
                {problem.hints?.length > 0 && (
                  <details style={{ marginBottom: 12 }}>
                    <summary style={{ fontSize: 12, fontWeight: 600, color: 'var(--indigo)', cursor: 'pointer', marginBottom: 8 }}>Hints ({problem.hints.length})</summary>
                    {problem.hints.map((h, i) => (
                      <div key={i} style={{ fontSize: 12, color: 'var(--text-2)', padding: '8px 10px', borderRadius: 7, background: 'var(--indigo-dim)', marginBottom: 5, lineHeight: 1.55 }}>
                        <strong style={{ color: 'var(--indigo)' }}>#{i+1}</strong> {h}
                      </div>
                    ))}
                  </details>
                )}
                {problem.optimal_complexity && (
                  <div style={{ fontSize: 11, color: 'var(--text-3)', display: 'flex', alignItems: 'center', gap: 5 }}>
                    Optimal: <code style={{ color: 'var(--green)', fontFamily: 'var(--font-mono)' }}>{problem.optimal_complexity}</code>
                  </div>
                )}
              </>
            )}

            {tab === 'results' && (
              submitting ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 200, gap: 12 }}>
                  <Spinner size={28} />
                  <p style={{ fontSize: 12, color: 'var(--text-3)' }}>Running test cases…</p>
                </div>
              ) : result ? (
                <>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                    {result.status === 'accepted' ? <FiCheck size={22} color="var(--green)" /> : <FiX size={22} color="var(--red)" />}
                    <div>
                      <div style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, color: result.status === 'accepted' ? 'var(--green)' : 'var(--red)' }}>
                        {result.status === 'accepted' ? 'Accepted' : result.status.replace('_',' ').toUpperCase()}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{result.tests_passed}/{result.tests_total} tests</div>
                    </div>
                    <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                      <div style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, color: 'var(--indigo)' }}>{result.score}</div>
                      <div style={{ fontSize: 10, color: 'var(--text-3)' }}>/ 100</div>
                    </div>
                  </div>
                  <div className="progress-track" style={{ marginBottom: 16 }}>
                    <motion.div className="progress-fill" initial={{ width: 0 }} animate={{ width: `${result.score}%` }} transition={{ duration: 0.8 }} />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 14 }}>
                    {[['Your', result.complexity_estimate, 'var(--text-2)'], ['Optimal', result.optimal_complexity || '—', 'var(--green)']].map(([lbl, val, c]) => (
                      <div key={lbl} style={{ padding: '10px', borderRadius: 8, background: 'var(--raised)', border: '1px solid var(--border)', textAlign: 'center' }}>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, color: c }}>{val}</div>
                        <div style={{ fontSize: 10, color: 'var(--text-3)' }}>{lbl} complexity</div>
                      </div>
                    ))}
                  </div>
                  {result.feedback && <div style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.65, padding: '10px 12px', borderRadius: 8, background: 'var(--raised)', border: '1px solid var(--border)' }}>{result.feedback}</div>}
                </>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 160, fontSize: 12, color: 'var(--text-3)' }}>Submit to see results</div>
              )
            )}
          </div>
        </div>

        {/* CENTER — Monaco editor */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--border)', overflow: 'hidden' }}>
          {/* Toolbar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 14px', borderBottom: '1px solid var(--border)', flexShrink: 0, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', gap: 4 }}>
              {LANGS.map(l => (
                <button key={l} onClick={() => changeLang(l)} style={{ fontSize: 10, fontWeight: 700, padding: '4px 11px', borderRadius: 6, border: 'none', cursor: 'pointer', background: lang === l ? 'var(--indigo-dim)' : 'var(--raised)', color: lang === l ? 'var(--indigo)' : 'var(--text-3)', textTransform: 'capitalize' }}>
                  {l}
                </button>
              ))}
            </div>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
              <button onClick={() => problem && setCode(problem.starter_code?.[lang] || '')} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 500, padding: '5px 11px', borderRadius: 7, background: 'var(--raised)', border: '1px solid var(--border)', color: 'var(--text-3)', cursor: 'pointer' }}>
                <FiRefreshCw size={11} /> Reset
              </button>
              <motion.button whileTap={{ scale: 0.96 }} onClick={submit} disabled={submitting}
                style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, padding: '6px 18px', borderRadius: 8, background: 'var(--green)', border: 'none', color: '#06060d', cursor: 'pointer', opacity: submitting ? 0.7 : 1 }}>
                {submitting ? <Spinner size={13} color="#06060d" /> : <FiPlay size={12} />}
                {submitting ? 'Running…' : 'Submit'}
              </motion.button>
            </div>
          </div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <Editor
              height="100%"
              language={lang === 'cpp' ? 'cpp' : lang}
              value={code}
              onChange={v => setCode(v || '')}
              theme="light"
              options={{
                fontSize: 13, fontFamily: '"JetBrains Mono", monospace', fontLigatures: true,
                lineNumbers: 'on', wordWrap: 'on', minimap: { enabled: false },
                scrollBeyondLastLine: false, padding: { top: 14 },
                cursorBlinking: 'smooth', renderLineHighlight: 'gutter',
              }}
            />
          </div>
        </div>

        {/* RIGHT — AI Interviewer */}
        <div style={{ width: 340, flexShrink: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '12px 14px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--green)' }} />
              <span style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 13, color: 'var(--text-1)' }}>
                {problem?.company_tags?.[0] ? `${problem.company_tags[0].charAt(0).toUpperCase() + problem.company_tags[0].slice(1)} Interviewer` : 'Interviewer'}
              </span>
              <span style={{ fontSize: 10, color: 'var(--text-3)', marginLeft: 'auto' }}>Live session</span>
            </div>
            <div style={{ display: 'flex', gap: 5, marginTop: 10, flexWrap: 'wrap' }}>
              {["What's your approach?","Time complexity?","Edge cases?","Why this structure?"].map(q => (
                <button key={q} onClick={() => sendChat(q)} style={{ fontSize: 10, padding: '4px 9px', borderRadius: 6, background: 'var(--raised)', border: '1px solid var(--border)', color: 'var(--text-3)', cursor: 'pointer' }}>{q}</button>
              ))}
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
            {messages.map((msg, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                className={msg.role === 'user' ? 'bubble-user' : 'bubble-ai'}>
                {msg.role === 'assistant' ? (
                  <div className="md"><ReactMarkdown>{msg.text}</ReactMarkdown></div>
                ) : msg.text}
              </motion.div>
            ))}
            {chatLoading && <div className="bubble-ai"><TypingDots /></div>}
            <div ref={endRef} />
          </div>

          <div style={{ padding: '10px 12px', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
            <div style={{ display: 'flex', gap: 7 }}>
              <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendChat()}
                placeholder="Respond to the interviewer…" className="input" style={{ flex: 1, padding: '8px 12px', fontSize: 12 }} />
              <motion.button whileTap={{ scale: 0.92 }} onClick={() => sendChat()} disabled={chatLoading || !input.trim()}
                style={{ width: 34, height: 34, borderRadius: 8, border: 'none', background: input.trim() ? 'var(--indigo)' : 'var(--raised)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <FiSend size={13} color={input.trim() ? 'white' : 'var(--text-3)'} />
              </motion.button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
