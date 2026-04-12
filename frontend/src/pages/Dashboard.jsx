import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { FiCheckCircle, FiCircle, FiCode, FiBook, FiMic, FiFileText, FiClipboard, FiArrowRight, FiZap, FiStar, FiCalendar, FiTrendingUp } from 'react-icons/fi'
import { userAPI } from '../api'
import { useStore } from '../stores'
import { Navbar, Spinner, Label, Orbs } from '../components'

const TASK_META = {
  dsa_problem:    { icon: FiCode,      label: 'Code',       color: 'var(--indigo)' },
  theory:         { icon: FiBook,      label: 'Theory',     color: 'var(--green)' },
  behavioral:     { icon: FiMic,       label: 'Behavioral', color: 'var(--amber)' },
  project_review: { icon: FiFileText,  label: 'Resume',     color: '#a78bfa' },
  mock_test:      { icon: FiClipboard, label: 'Mock',       color: 'var(--red)' },
}

function DaysCountdown({ days }) {
  const isUrgent = days <= 2
  const color = days === 0 ? 'var(--red)' : days <= 2 ? 'var(--amber)' : days <= 7 ? 'var(--indigo)' : 'var(--text-1)'
  const msg = days === 0 ? "TODAY'S THE DAY" : days === 1 ? 'TOMORROW' : days <= 7 ? 'THIS WEEK' : 'DAYS LEFT'
  return (
    <div style={{ textAlign: 'center', padding: '28px 0 20px' }}>
      <motion.div
        className={isUrgent ? 'countdown-urgent' : ''}
        style={{ fontFamily: 'var(--font-display)', fontSize: 96, fontWeight: 700, letterSpacing: -6, color, lineHeight: 1 }}
        initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ duration: 0.5, ease: 'backOut' }}
      >
        {days}
      </motion.div>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 2.5, color: 'var(--text-3)', marginTop: 6 }}>{msg}</div>
    </div>
  )
}

function ReadinessMeter({ score }) {
  const pct = Math.min(100, Math.max(0, score || 0))
  const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? 'var(--amber)' : 'var(--indigo)'
  return (
    <div style={{ padding: '16px 20px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, textAlign: 'center' }}>
      <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.5, color: 'var(--text-3)', marginBottom: 10 }}>READINESS</div>
      <div style={{ position: 'relative', height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2, marginBottom: 10, overflow: 'hidden' }}>
        <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 1, ease: 'easeOut' }}
          style={{ position: 'absolute', inset: '0 auto 0 0', background: color, borderRadius: 2 }} />
      </div>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 30, fontWeight: 700, color, letterSpacing: -1 }}>{Math.round(pct)}%</div>
    </div>
  )
}

function TaskRow({ task, onComplete, completing, onNavigate }) {
  const meta = TASK_META[task.task_type] || TASK_META.dsa_problem
  const Icon = meta.icon
  return (
    <motion.div
      layout
      className={`task-row ${task.completed ? 'done' : ''}`}
      whileHover={task.completed ? {} : { x: 3 }}
      style={{ borderLeft: `3px solid ${task.completed ? 'var(--border)' : meta.color}` }}
    >
      <div 
        onClick={(e) => { e.stopPropagation(); !task.completed && !completing && onComplete(task.id); }} 
        style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', paddingRight: 8 }}
      >
        {completing ? (
          <Spinner size={18} color={meta.color} />
        ) : task.completed ? (
          <FiCheckCircle size={18} color="var(--green)" style={{ flexShrink: 0 }} />
        ) : (
          <FiCircle size={18} color="var(--text-3)" style={{ flexShrink: 0 }} />
        )}
      </div>
      <div style={{ flex: 1, minWidth: 0, cursor: 'pointer' }} onClick={() => onNavigate(task.task_type)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 2 }}>
          <span style={{ fontSize: 13, fontWeight: 500, color: task.completed ? 'var(--text-3)' : 'var(--text-1)', textDecoration: task.completed ? 'line-through' : 'none', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {task.title}
          </span>
          {task.priority === 1 && !task.completed && <FiStar size={10} color="var(--amber)" />}
        </div>
        {task.description && (
          <p style={{ fontSize: 11, color: 'var(--text-3)', lineHeight: 1.45, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{task.description}</p>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
        <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 5, background: `${meta.color}18`, color: meta.color }}>{meta.label}</span>
        {task.estimated_minutes && <span style={{ fontSize: 10, color: 'var(--text-3)' }}>{task.estimated_minutes}m</span>}
      </div>
    </motion.div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { setDashboard, updateTask } = useStore()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [completing, setCompleting] = useState(null)

  useEffect(() => { load() }, [])

  const load = async () => {
    try {
      const r = await userAPI.dashboard()
      setData(r.data)
      setDashboard(r.data)
    } catch { toast.error('Failed to load dashboard') }
    finally { setLoading(false) }
  }

  const completeTask = async (taskId) => {
    setCompleting(taskId)
    try {
      const r = await userAPI.completeTask(taskId)
      setData(d => d ? { ...d, today_tasks: d.today_tasks.map(t => t.id === taskId ? { ...t, completed: true } : t), completion_pct: r.data.completion_pct } : d)
      updateTask(taskId, { completed: true })
      toast.success('Task done! 🔥')
    } catch { toast.error('Failed to mark task') }
    finally { setCompleting(null) }
  }

  if (loading) return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Spinner size={28} />
    </div>
  )

  const u = data?.user
  const today = data?.today_tasks || []
  const done = today.filter(t => t.completed).length
  const firstName = u?.full_name?.split(' ')[0] || 'there'
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Morning' : hour < 17 ? 'Afternoon' : 'Evening'
  const crashMode = data?.days_left != null && data.days_left <= 2

  return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', position: 'relative' }}>
      <Orbs />
      <Navbar />

      <div style={{ position: 'relative', zIndex: 1, maxWidth: 1000, margin: '0 auto', padding: '32px 28px 60px' }} className="page-enter">

        {/* Crash mode banner */}
        <AnimatePresence>
          {crashMode && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
              style={{ padding: '12px 20px', borderRadius: 10, background: 'var(--red-dim)', border: '1px solid rgba(244,63,94,0.3)', marginBottom: 28, display: 'flex', alignItems: 'center', gap: 10 }}>
              <FiZap size={16} color="var(--red)" />
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--red)' }}>
                {data.days_left === 0 ? '⚡ INTERVIEW DAY — You\'ve prepared for this. Trust it.' : '⚡ CRASH MODE — Interview tomorrow. Focus on must-do tasks only.'}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 24, alignItems: 'start' }}>
          {/* LEFT — Countdown + stats */}
          <div style={{ position: 'sticky', top: 72 }}>
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 16, overflow: 'hidden', marginBottom: 16 }}>
              {data?.days_left != null ? (
                <DaysCountdown days={data.days_left} />
              ) : (
                <div style={{ padding: '28px 20px', textAlign: 'center' }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 14, color: 'var(--text-3)' }}>No interview date set</div>
                </div>
              )}
              <div style={{ padding: '0 20px 20px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                  <span style={{ color: 'var(--text-3)' }}>Target</span>
                  <span style={{ fontWeight: 600, color: 'var(--text-1)' }}>{u?.target_company || '—'} · {u?.target_role || '—'}</span>
                </div>
                {data?.streak_days > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                    <span style={{ color: 'var(--text-3)' }}>Streak</span>
                    <span style={{ fontWeight: 600, color: 'var(--amber)' }}>🔥 {data.streak_days} {data.streak_days === 1 ? 'day' : 'days'}</span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                  <span style={{ color: 'var(--text-3)' }}>Problems</span>
                  <span style={{ fontWeight: 600, color: 'var(--text-1)' }}>{data?.problems_solved || 0} solved</span>
                </div>
                {data?.completion_pct > 0 && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 5 }}>
                      <span style={{ color: 'var(--text-3)' }}>Plan progress</span>
                      <span style={{ color: 'var(--indigo)', fontWeight: 600 }}>{Math.round(data.completion_pct)}%</span>
                    </div>
                    <div className="progress-track">
                      <motion.div className="progress-fill" initial={{ width: 0 }} animate={{ width: `${data.completion_pct}%` }} transition={{ duration: 0.8 }} />
                    </div>
                  </div>
                )}
              </div>
            </div>
            <ReadinessMeter score={data?.readiness_score} />

            {/* Quick actions */}
            <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { icon: FiCode, label: 'Practice Coding', to: '/coding', color: 'var(--indigo)' },
                { icon: FiMic, label: 'Mock Interview', to: '/mock', color: 'var(--amber)' },
                { icon: FiTrendingUp, label: 'Analytics', to: '/analytics', color: 'var(--green)' },
              ].map(({ icon: Icon, label, to, color }) => (
                <motion.button key={to} whileHover={{ x: 3 }} whileTap={{ scale: 0.97 }} onClick={() => navigate(to)}
                  style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, cursor: 'pointer', textAlign: 'left', width: '100%' }}>
                  <Icon size={13} color={color} />
                  <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-2)' }}>{label}</span>
                  <FiArrowRight size={11} color="var(--text-3)" style={{ marginLeft: 'auto' }} />
                </motion.button>
              ))}
            </div>
          </div>

          {/* RIGHT — Today's mission */}
          <div>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 20 }}>
              <div>
                <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 700, color: 'var(--text-1)', letterSpacing: '-0.5px' }}>
                  {greeting}, {firstName}.
                </h1>
                <p style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 3 }}>
                  {today.length > 0
                    ? `${done}/${today.length} tasks done today · Day ${data?.current_day || 1} of ${data?.total_days || '—'}`
                    : data?.plan_id ? 'All done for today! Come back tomorrow.' : 'No plan yet — go to onboarding to generate one.'}
                </p>
              </div>
              {u?.calendar_connected && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, fontWeight: 600, color: 'var(--green)', padding: '4px 10px', background: 'var(--green-dim)', borderRadius: 6 }}>
                  <FiCalendar size={10} /> Calendar synced
                </div>
              )}
            </div>

            {today.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <Label>TODAY'S MISSION — {today.length} TASKS</Label>
                <AnimatePresence>
                  {today.map(task => (
                    <motion.div key={task.id} layout initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}>
                      <TaskRow task={task} onComplete={completeTask} completing={completing === task.id} onNavigate={(type) => {
                         if (type === 'dsa_problem') navigate('/coding')
                         else if (type === 'mock_test' || type === 'behavioral') navigate('/mock')
                         else if (type === 'theory') navigate('/theory')
                      }} />
                    </motion.div>
                  ))}
                </AnimatePresence>
                {done === today.length && today.length > 0 && (
                  <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                    style={{ padding: '20px', borderRadius: 12, background: 'var(--green-dim)', border: '1px solid rgba(34,211,165,0.25)', textAlign: 'center', marginTop: 8 }}>
                    <div style={{ fontSize: 22, marginBottom: 6 }}>🎉</div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: 'var(--green)' }}>Day {data?.current_day} Fully Completed!</div>
                    <p style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 4, marginBottom: 16 }}>Great job. You can rest, or unlock the next day's curriculum early.</p>
                    {data?.current_day < (data?.total_days || 1) ? (
                      <button onClick={async () => {
                        try {
                          await userAPI.advanceDay()
                          toast.success('Curriculum Advanced! 🚀')
                          load() // reload dashboard data
                        } catch {
                          toast.error('Failed to advance')
                        }
                      }} className="btn btn-primary btn-sm">Advance to Day {(data?.current_day || 1) + 1} →</button>
                    ) : (
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--green)' }}>You've finished the entire plan!</div>
                    )}
                  </motion.div>
                )}
              </div>
            ) : (
              !data?.plan_id && (
                <div style={{ padding: '40px', borderRadius: 14, background: 'var(--surface)', border: '1px solid var(--border)', textAlign: 'center' }}>
                  <FiZap size={28} color="var(--indigo)" style={{ marginBottom: 12 }} />
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: 'var(--text-1)', marginBottom: 8 }}>No active plan</div>
                  <p style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 20 }}>Complete onboarding to generate your personalized prep plan.</p>
                  <button onClick={() => navigate('/onboarding')} className="btn btn-primary btn-sm">Set Up My Plan →</button>
                </div>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
