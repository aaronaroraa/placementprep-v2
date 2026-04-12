import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import { FiSend, FiUploadCloud, FiCheck, FiCalendar, FiZap } from 'react-icons/fi'
import { userAPI, resumeAPI, authAPI } from '../api'
import { useStore } from '../stores'
import { Spinner, TypingDots } from '../components'

const ROLES = ['SDE-1','SDE-2','Data Engineer','ML Engineer','DevOps','Frontend','Backend','Full Stack','Product']
const COMPANIES = ['Google','Amazon','Microsoft','Meta','Apple','Flipkart','Paytm','Razorpay','Zepto','Swiggy','Zomato','Meesho','PhonePe','Groww','CRED','Atlassian','Adobe','Salesforce','Goldman Sachs','Uber','LinkedIn','Other']
const SKILL_LEVELS = ['Rusty — I need a lot of work','Decent — know the basics','Strong — comfortable with most topics']

// Coach "script" — each step defines what the coach says and what input to collect
const STEPS = [
  { id: 'name',       coach: (u) => `Hey! I'm your PlacementPrep coach 👋\nI'll build you a personalized interview plan in about 2 minutes.\n\nFirst — what's your name?`,                           inputType: 'text',    placeholder: 'Rahul Sharma' },
  { id: 'role',       coach: (u) => `Nice to meet you, ${u.name}! Which role are you targeting?`,                                                                                                   inputType: 'choice',  choices: ROLES },
  { id: 'company',    coach: (u) => `Great choice. Dream company, or open to any good offer?`,                                                                                                      inputType: 'choice',  choices: [...COMPANIES] },
  { id: 'date',       coach: (u) => `Got it — ${u.company}! When's the interview?\nA specific date or approximate works.`,                                                                          inputType: 'date',    placeholder: 'YYYY-MM-DD' },
  { id: 'dsa',        coach: (u) => `Okay, ${Math.max(0, Math.ceil((new Date(u.date) - new Date()) / 86400000))} days — we can work with that.\n\nHonest check (no judgment): how's your DSA right now?`, inputType: 'choice', choices: SKILL_LEVELS },
  { id: 'cs',         coach: (u) => `Got it. And CS fundamentals — OS, DBMS, Computer Networks?`,                                                                                                   inputType: 'choice',  choices: SKILL_LEVELS },
  { id: 'hours',      coach: (u) => `Good. How many hours can you give per day? Be realistic.`,                                                                                                     inputType: 'choice',  choices: ['1 hour','2 hours','3 hours','4+ hours'] },
  { id: 'resume',     coach: (u) => `Almost set up. Drop your resume if you have one — I'll find your skill gaps and build interview questions from YOUR projects. (Skip if you don't have one yet.)`, inputType: 'resume' },
  { id: 'calendar',   coach: (u) => `Last thing — want me to block prep time on your Google Calendar?\nI'll create daily sessions and sync when you complete tasks.`,                               inputType: 'calendar' },
]

function parseSkillLevel(choice) {
  if (!choice) return 2
  if (choice.startsWith('Rusty')) return 1
  if (choice.startsWith('Decent')) return 3
  return 4
}

function parseHours(choice) {
  if (!choice) return 2
  const n = parseFloat(choice)
  return isNaN(n) ? 2 : n
}

export default function Onboarding() {
  const navigate = useNavigate()
  const setUser = useStore(s => s.setUser)
  const [stepIndex, setStepIndex] = useState(0)
  const [answers, setAnswers] = useState({})
  const [messages, setMessages] = useState([])
  const [inputVal, setInputVal] = useState('')
  const [typing, setTyping] = useState(false)
  const [done, setDone] = useState(false)
  const [resumeData, setResumeData] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [finishing, setFinishing] = useState(false)
  const [calendarLoading, setCalendarLoading] = useState(false)
  const endRef = useRef(null)

  // Kick off first coach message on mount
  useEffect(() => { coachSay(STEPS[0].coach({})) }, [])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, typing])

  function coachSay(text) {
    setTyping(true)
    setTimeout(() => {
      setTyping(false)
      setMessages(m => [...m, { role: 'coach', text }])
    }, 700 + Math.random() * 400)
  }

  function userSay(text) {
    setMessages(m => [...m, { role: 'user', text }])
  }

  function advance(newAnswers, displayText) {
    userSay(displayText)
    const nextIndex = stepIndex + 1
    if (nextIndex < STEPS.length) {
      setStepIndex(nextIndex)
      setTimeout(() => coachSay(STEPS[nextIndex].coach(newAnswers)), 300)
    } else {
      finish(newAnswers)
    }
  }

  function handleTextSubmit() {
    const val = inputVal.trim()
    if (!val) return
    const step = STEPS[stepIndex]
    const newAnswers = { ...answers, [step.id]: val }
    setAnswers(newAnswers)
    setInputVal('')
    advance(newAnswers, val)
  }

  function handleChoice(choice) {
    const step = STEPS[stepIndex]
    const newAnswers = { ...answers, [step.id]: choice }
    setAnswers(newAnswers)
    advance(newAnswers, choice)
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'application/pdf': ['.pdf'] }, maxFiles: 1,
    onDrop: async ([file]) => {
      if (!file) return
      setUploading(true)
      userSay('Uploading resume…')
      try {
        const r = await resumeAPI.upload(file)
        setResumeData(r.data)
        const skills = r.data.skills_extracted?.slice(0, 5).join(', ')
        const gaps = r.data.skill_gaps?.slice(0, 3).join(', ')
        setMessages(m => [...m, { role: 'coach', text: `Resume analyzed! Found ${r.data.skills_extracted?.length || 0} skills.\n\nStrong: ${skills || 'detected'}\nGaps for ${answers.role}: ${gaps || 'none found'}` }])
        const newAnswers = { ...answers, resume: true }
        setAnswers(newAnswers)
        const nextIndex = stepIndex + 1
        setStepIndex(nextIndex)
        setTimeout(() => coachSay(STEPS[nextIndex].coach(newAnswers)), 600)
      } catch { toast.error('Upload failed') }
      finally { setUploading(false) }
    }
  })

  async function handleCalendar(connect) {
    if (connect) {
      setCalendarLoading(true)
      try {
        const r = await authAPI.googleUrl()
        // Store flag so callback knows to sync calendar
        sessionStorage.setItem('calendar_after_onboarding', JSON.stringify(answers))
        window.location.href = r.data.url
      } catch { toast.error('Google auth unavailable') }
      finally { setCalendarLoading(false) }
    } else {
      const newAnswers = { ...answers, calendar: false }
      setAnswers(newAnswers)
      userSay("I'll skip for now")
      setDone(true)
      setStepIndex(STEPS.length)
      finish(newAnswers)
    }
  }

  async function finish(ans) {
    setFinishing(true)
    const days = Math.max(0, Math.ceil((new Date(ans.date) - new Date()) / 86400000))
    const skill_assessment = {
      dsa: parseSkillLevel(ans.dsa),
      os: parseSkillLevel(ans.cs),
      dbms: parseSkillLevel(ans.cs),
      cn: parseSkillLevel(ans.cs),
      oop: 2,
      system_design: parseSkillLevel(ans.cs),
      behavioral: 2,
    }
    const planType = days <= 1 ? 'Crash Course (24h)' : days <= 7 ? '1-Week Fast Track' : days <= 21 ? '3-Week Structured Plan' : '1-Month Roadmap'

    coachSay(`Perfect, ${ans.name}. Here's your plan:\n\n📅 ${days} days until ${ans.company} ${ans.role}\n📋 Plan: ${planType}\n\nI'll give you targeted tasks every day based on your level. Let's get to work.`)

    try {
      const r = await userAPI.onboarding({
        college: 'Not specified', branch: 'Not specified',
        graduation_year: new Date().getFullYear() + 1,
        target_role: ans.role || 'SDE-1',
        target_company: ans.company || 'Top Tech Company',
        interview_date: ans.date,
        daily_hours: parseHours(ans.hours),
        skill_assessment,
      })
      const me = await userAPI.me()
      setUser(me.data)
      setTimeout(() => {
        toast.success('Plan generated! Calendar ' + (r.data.calendar_synced ? 'synced ✓' : 'not connected'))
        navigate('/dashboard')
      }, 2200)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Setup failed')
    } finally { setFinishing(false) }
  }

  const step = STEPS[stepIndex] || {}

  return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      {/* Header bar */}
      <div style={{ width: '100%', borderBottom: '1px solid var(--border)', padding: '0 32px', height: 52, display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{ width: 26, height: 26, background: 'var(--indigo)', borderRadius: 7, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <FiZap size={12} color="white" />
        </div>
        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 13, color: 'var(--text-1)' }}>PlacementPrep AI</span>
        {stepIndex > 0 && (
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 120, height: 3, background: 'var(--border)', borderRadius: 2, overflow: 'hidden' }}>
              <motion.div style={{ height: '100%', background: 'var(--indigo)', borderRadius: 2 }} animate={{ width: `${Math.min(100, (stepIndex / STEPS.length) * 100)}%` }} transition={{ duration: 0.4 }} />
            </div>
            <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{stepIndex}/{STEPS.length}</span>
          </div>
        )}
      </div>

      {/* Chat window */}
      <div style={{ flex: 1, width: '100%', maxWidth: 620, display: 'flex', flexDirection: 'column', padding: '24px 24px 0' }}>
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 12, paddingBottom: 16 }}>
          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}
                style={{ display: 'flex', flexDirection: 'column' }}>
                {msg.role === 'coach' ? (
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                    <div style={{ width: 28, height: 28, background: 'var(--indigo)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2 }}>
                      <FiZap size={12} color="white" />
                    </div>
                    <div className="bubble-ai" style={{ whiteSpace: 'pre-line', maxWidth: '85%' }}>{msg.text}</div>
                  </div>
                ) : (
                  <div className="bubble-user">{msg.text}</div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {typing && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
              <div style={{ width: 28, height: 28, background: 'var(--indigo)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <FiZap size={12} color="white" />
              </div>
              <div className="bubble-ai"><TypingDots /></div>
            </motion.div>
          )}
          <div ref={endRef} />
        </div>

        {/* Input area */}
        {!typing && stepIndex < STEPS.length && !finishing && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            style={{ borderTop: '1px solid var(--border)', paddingTop: 16, paddingBottom: 24 }}>

            {/* Text input */}
            {step.inputType === 'text' && (
              <div style={{ display: 'flex', gap: 8 }}>
                <input autoFocus value={inputVal} onChange={e => setInputVal(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleTextSubmit()}
                  placeholder={step.placeholder} className="input" style={{ flex: 1 }} />
                <motion.button whileTap={{ scale: 0.94 }} onClick={handleTextSubmit} disabled={!inputVal.trim()}
                  className="btn btn-primary btn-icon">
                  <FiSend size={14} />
                </motion.button>
              </div>
            )}

            {/* Date input */}
            {step.inputType === 'date' && (
              <div style={{ display: 'flex', gap: 8 }}>
                <input type="date" value={inputVal} onChange={e => setInputVal(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  className="input" style={{ flex: 1 }} />
                <motion.button whileTap={{ scale: 0.94 }} onClick={handleTextSubmit} disabled={!inputVal}
                  className="btn btn-primary btn-icon">
                  <FiSend size={14} />
                </motion.button>
              </div>
            )}

            {/* Choice buttons */}
            {step.inputType === 'choice' && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {step.choices.map(c => (
                  <motion.button key={c} whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.96 }} onClick={() => handleChoice(c)}
                    style={{ padding: '8px 16px', borderRadius: 9, background: 'var(--raised)', border: '1px solid var(--border-bright)', color: 'var(--text-1)', fontSize: 12, fontWeight: 500, cursor: 'pointer' }}>
                    {c}
                  </motion.button>
                ))}
              </div>
            )}

            {/* Resume dropzone */}
            {step.inputType === 'resume' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div {...getRootProps()} style={{
                  border: `2px dashed ${isDragActive ? 'var(--indigo)' : 'var(--border)'}`,
                  borderRadius: 12, padding: '28px 20px', textAlign: 'center', cursor: 'pointer',
                  background: isDragActive ? 'var(--indigo-dim)' : 'var(--raised)', transition: 'all 0.15s',
                }}>
                  <input {...getInputProps()} />
                  {uploading ? <Spinner /> : resumeData ? (
                    <div style={{ color: 'var(--green)', fontSize: 13, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                      <FiCheck size={16} /> Resume analyzed!
                    </div>
                  ) : (
                    <>
                      <FiUploadCloud size={22} color="var(--text-3)" style={{ marginBottom: 8 }} />
                      <p style={{ fontSize: 12, color: 'var(--text-2)' }}>Drop your PDF here, or click to browse</p>
                      <p style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 4 }}>PDF · Max 5MB</p>
                    </>
                  )}
                </div>
                <motion.button whileTap={{ scale: 0.96 }} onClick={() => { userSay("I'll skip for now"); const ni = stepIndex + 1; setStepIndex(ni); setTimeout(() => coachSay(STEPS[ni].coach(answers)), 300) }}
                  className="btn btn-ghost btn-sm" style={{ alignSelf: 'flex-start' }}>
                  Skip for now
                </motion.button>
              </div>
            )}

            {/* Calendar */}
            {step.inputType === 'calendar' && (
              <div style={{ display: 'flex', gap: 10 }}>
                <motion.button whileTap={{ scale: 0.96 }} onClick={() => handleCalendar(true)} disabled={calendarLoading}
                  className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                  {calendarLoading ? <Spinner size={14} color="white" /> : <FiCalendar size={14} />}
                  Connect Google Calendar
                </motion.button>
                <motion.button whileTap={{ scale: 0.96 }} onClick={() => handleCalendar(false)} className="btn btn-ghost">
                  Skip
                </motion.button>
              </div>
            )}
          </motion.div>
        )}

        {finishing && (
          <div style={{ padding: '20px 0 24px', display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-3)', fontSize: 13 }}>
            <Spinner size={18} /> Building your plan…
          </div>
        )}
      </div>
    </div>
  )
}
