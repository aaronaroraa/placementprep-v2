import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { FiCheckCircle, FiCircle, FiLock, FiCode, FiBook, FiMic, FiFileText, FiClipboard } from 'react-icons/fi'
import { userAPI } from '../api'
import { Navbar, Spinner, Orbs } from '../components'
import toast from 'react-hot-toast'

const TASK_META = {
  dsa_problem:    { icon: FiCode,      color: 'var(--indigo)' },
  theory:         { icon: FiBook,      color: 'var(--green)' },
  behavioral:     { icon: FiMic,       color: 'var(--amber)' },
  project_review: { icon: FiFileText,  color: '#a78bfa' },
  mock_test:      { icon: FiClipboard, color: 'var(--red)' },
}

export default function Plan() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)

  useEffect(() => {
    userAPI.curriculum().then(r => {
      setData(r.data)
      setLoading(false)
    }).catch(e => {
      toast.error('Failed to load plan roadmap')
      setLoading(false)
    })
  }, [])

  if (loading) return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Spinner size={32} />
    </div>
  )

  const { current_day, completed_task_ids, days } = data

  return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', position: 'relative' }}>
      <Orbs />
      <Navbar />
      
      <div style={{ position: 'relative', zIndex: 1, maxWidth: 800, margin: '0 auto', padding: '40px 28px 80px' }} className="page-enter">
        <div style={{ marginBottom: 40, textAlign: 'center' }}>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 32, fontWeight: 700, color: 'var(--text-1)', letterSpacing: '-1px', marginBottom: 8 }}>Curriculum Roadmap</h1>
          <p style={{ fontSize: 13, color: 'var(--text-3)' }}>Your structured preparation journey, broken down day by day.</p>
        </div>

        <div style={{ position: 'relative' }}>
          {/* Timeline line */}
          <div style={{ position: 'absolute', top: 20, bottom: 20, left: 24, width: 2, background: 'var(--border)' }} />
          
          {days?.map((day, idx) => {
            const isCompleted = day.day < current_day
            const isActive = day.day === current_day
            const isLocked = day.day > current_day
            
            return (
              <motion.div key={day.day} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.1 }}
                style={{ position: 'relative', display: 'flex', gap: 24, marginBottom: 32, opacity: isLocked ? 0.6 : 1 }}>
                
                {/* Node */}
                <div style={{ 
                  width: 50, height: 50, borderRadius: '50%', background: isCompleted ? 'var(--green-dim)' : isActive ? 'var(--indigo-dim)' : 'var(--surface)',
                  border: `2px solid ${isCompleted ? 'var(--green)' : isActive ? 'var(--indigo)' : 'var(--border)'}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, zIndex: 2
                }}>
                  {isCompleted ? <FiCheckCircle size={20} color="var(--green)" /> : isLocked ? <FiLock size={18} color="var(--text-3)" /> : <span style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: 'var(--indigo)' }}>{day.day}</span>}
                </div>

                {/* Content */}
                <div style={{ flex: 1, background: isActive ? 'rgba(99,102,241,0.03)' : 'var(--surface)', border: `1px solid ${isActive ? 'var(--indigo)' : 'var(--border)'}`, borderRadius: 16, padding: 24 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                    <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 600, color: 'var(--text-1)' }}>Day {day.day}: {day.title}</h3>
                    {isActive && <div style={{ fontSize: 10, fontWeight: 700, padding: '4px 10px', background: 'var(--indigo)', color: 'white', borderRadius: 6, letterSpacing: 1 }}>IN PROGRESS</div>}
                    {isCompleted && <div style={{ fontSize:  10, fontWeight: 700, color: 'var(--green)', letterSpacing: 1 }}>COMPLETED</div>}
                    {isLocked && <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-3)', letterSpacing: 1 }}>LOCKED</div>}
                  </div>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {day.tasks.map(task => {
                      const Icon = TASK_META[task.task_type]?.icon || FiCode
                      const color = TASK_META[task.task_type]?.color || 'white'
                      const isTaskDone = completed_task_ids?.includes(task.id) || isCompleted
                      
                      return (
                        <div key={task.id} style={{ display: 'flex', alignItems: 'flex-start', gap: 12, padding: 12, background: 'rgba(255,255,255,0.02)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.03)' }}>
                          <div style={{ marginTop: 2 }}>{isTaskDone ? <FiCheckCircle size={14} color="var(--green)" /> : <FiCircle size={14} color="var(--border-bright)" />}</div>
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                              <Icon size={12} color={color} />
                              <span style={{ fontSize: 13, fontWeight: 500, color: isTaskDone ? 'var(--text-3)' : 'var(--text-1)', textDecoration: isTaskDone ? 'line-through' : 'none' }}>{task.title}</span>
                            </div>
                            <p style={{ fontSize: 11, color: 'var(--text-3)', margin: 0, lineHeight: 1.4 }}>{task.description} · {task.estimated_minutes}m</p>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
