// Interviews.jsx — the on-demand mock interview hub.
// Lists past attempts, shows the trend, and launches a new proctored room.
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FiVideo, FiArrowRight, FiTrendingUp, FiShield, FiClock, FiAlertTriangle } from 'react-icons/fi'
import { mockAPI } from '../api'
import { useStore } from '../stores'
import { Navbar, Orbs, Spinner } from '../components'

const VERDICT_META = {
  pass: { label: 'Strong', color: 'var(--green)', bg: 'var(--green-dim)' },
  borderline: { label: 'Needs Work', color: 'var(--amber)', bg: 'var(--amber-dim)' },
  fail: { label: 'Not Ready', color: 'var(--red)', bg: 'var(--red-dim)' },
}

function verdictFor(m) {
  if (m.verdict && VERDICT_META[m.verdict]) return VERDICT_META[m.verdict]
  if (typeof m.overall_score === 'number')
    return m.overall_score >= 70 ? VERDICT_META.pass : m.overall_score >= 50 ? VERDICT_META.borderline : VERDICT_META.fail
  return { label: 'Incomplete', color: 'var(--text-3)', bg: 'var(--raised)' }
}

export default function Interviews() {
  const user = useStore(s => s.user)
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const r = await mockAPI.history()
        const list = Array.isArray(r.data) ? r.data : (r.data?.sessions || [])
        setHistory(list)
      } catch { setHistory([]) }
      finally { setLoading(false) }
    })()
  }, [])

  const completed = history.filter(m => m.completed && typeof m.overall_score === 'number')
  const best = completed.length ? Math.max(...completed.map(m => m.overall_score)) : null
  const last = completed[0]?.overall_score ?? null
  const avg = completed.length ? Math.round(completed.reduce((a, m) => a + m.overall_score, 0) / completed.length) : null

  return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', position: 'relative' }}>
      <Orbs />
      <Navbar />
      <div style={{ position: 'relative', zIndex: 1, maxWidth: 900, margin: '0 auto', padding: '36px 28px 70px' }} className="page-enter">

        {/* Hero / launch card */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
          style={{ position: 'relative', overflow: 'hidden', padding: '32px 32px', borderRadius: 18, marginBottom: 32,
                   background: 'linear-gradient(135deg, rgba(20,184,166,0.14), rgba(52,211,153,0.06))',
                   border: '1px solid var(--border-bright)' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, padding: '5px 12px', borderRadius: 20, background: 'rgba(0,0,0,0.25)', color: 'var(--brand)', fontSize: 11, fontWeight: 700, letterSpacing: 0.5, marginBottom: 16 }}>
            <FiShield size={12} /> PROCTORED · 30 MIN · CAMERA ON
          </div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 30, fontWeight: 700, letterSpacing: '-1px', marginBottom: 8 }}>
            Mock Interview
          </h1>
          <p style={{ fontSize: 14, color: 'var(--text-2)', lineHeight: 1.6, maxWidth: 520, marginBottom: 24 }}>
            Take it whenever you feel ready. Questions come from your resume and your {user?.target_company || 'target company'}.
            You'll get a score and an honest debrief — and you can retake it as many times as you need.
          </p>
          <button onClick={() => navigate('/interview')} className="btn btn-primary" style={{ padding: '13px 26px', fontSize: 14 }}>
            <FiVideo size={15} /> Start a mock interview
          </button>
        </motion.div>

        {/* Stats */}
        {completed.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 32 }}>
            {[['Best score', best], ['Last score', last], ['Average', avg]].map(([label, val]) => (
              <div key={label} style={{ padding: '18px 20px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14 }}>
                <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: 'var(--text-3)', marginBottom: 8 }}>{label.toUpperCase()}</div>
                <div className="stat-number">{val ?? '—'}</div>
              </div>
            ))}
          </div>
        )}

        {/* History */}
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.5, color: 'var(--text-3)', marginBottom: 14 }}>YOUR ATTEMPTS</div>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}><Spinner /></div>
        ) : history.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 24px', background: 'var(--surface)', border: '1px dashed var(--border-bright)', borderRadius: 16 }}>
            <FiVideo size={28} color="var(--text-3)" style={{ marginBottom: 12 }} />
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 16, marginBottom: 6 }}>You haven't been grilled yet.</div>
            <div style={{ fontSize: 13, color: 'var(--text-3)' }}>That's about to change. Take your first mock when you're ready.</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {history.map((m, i) => {
              const v = verdictFor(m)
              const d = m.started_at ? new Date(m.started_at) : null
              return (
                <motion.div key={m.id || i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}
                  style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '16px 18px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12 }}>
                  <div style={{ width: 48, height: 48, borderRadius: 10, background: v.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 18, color: v.color }}>
                      {typeof m.overall_score === 'number' ? Math.round(m.overall_score) : '—'}
                    </span>
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                      <span style={{ fontWeight: 600, fontSize: 14 }}>{m.target_company || 'Mock'} · {(m.interview_type || 'full')[0].toUpperCase() + (m.interview_type || 'full').slice(1)}</span>
                      <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: 0.5, padding: '2px 8px', borderRadius: 5, background: v.bg, color: v.color }}>{v.label}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 12, color: 'var(--text-3)' }}>
                      {d && <span>{d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>}
                      {typeof m.duration_minutes === 'number' && <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><FiClock size={11} /> {m.duration_minutes} min</span>}
                      {m.tab_switches > 0 && <span style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--amber)' }}><FiAlertTriangle size={11} /> {m.tab_switches}</span>}
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}

        {completed.length >= 2 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 24, padding: '14px 18px', background: 'var(--green-dim)', borderRadius: 12, fontSize: 13, color: 'var(--green)' }}>
            <FiTrendingUp size={15} />
            {last >= best ? "That's your best score yet. Keep that momentum." : `Your best is ${best}. You can beat it — take another round.`}
          </div>
        )}
      </div>
    </div>
  )
}
