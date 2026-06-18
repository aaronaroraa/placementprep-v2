// InterviewRoom.jsx — proctored, chat-based mock interview.
// Flow: setup → camera-gate → rules → live (30 min) → debrief
// Privacy: the camera feed is shown live only. Nothing is recorded or uploaded.
import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'
import {
  FiVideo, FiVideoOff, FiClock, FiSend, FiAlertTriangle,
  FiShield, FiArrowRight, FiLock
} from 'react-icons/fi'
import { mockAPI } from '../api'
import { useStore } from '../stores'
import { Spinner, TypingDots } from '../components'

const DURATION_SECONDS = 30 * 60

export default function InterviewRoom() {
  const user = useStore(s => s.user)
  const navigate = useNavigate()

  const [phase, setPhase] = useState('setup') // setup|camera|rules|live|debrief

  // camera
  const videoRef = useRef(null)
  const streamRef = useRef(null)
  const [camReady, setCamReady] = useState(false)
  const [camError, setCamError] = useState(null)

  // interview state
  const [mockId, setMockId] = useState(null)
  const [exchangeCount, setExchangeCount] = useState(0)
  const [messages, setMessages] = useState([])
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  // proctoring + timer
  const [remaining, setRemaining] = useState(DURATION_SECONDS)
  const [tabSwitches, setTabSwitches] = useState(0)
  const timerRef = useRef(null)
  const endRef = useRef(null)
  const tabSwitchesRef = useRef(0)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading])

  // ── Camera lifecycle ──────────────────────────────────────────────────────
  const startCamera = useCallback(async () => {
    setCamError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play().catch(() => {})
      }
      setCamReady(true)
    } catch (e) {
      setCamReady(false)
      setCamError(
        e?.name === 'NotAllowedError'
          ? 'Camera access was denied. A live camera is required for a proctored interview.'
          : 'No camera was found. Connect a camera to continue.'
      )
    }
  }, [])

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach(t => t.stop())
    streamRef.current = null
    setCamReady(false)
  }, [])

  // Re-attach the live stream to the <video> whenever we enter a phase that shows it.
  useEffect(() => {
    if ((phase === 'camera' || phase === 'live') && streamRef.current && videoRef.current) {
      videoRef.current.srcObject = streamRef.current
      videoRef.current.play().catch(() => {})
    }
  }, [phase])

  // Detect the camera being cut mid-interview.
  useEffect(() => {
    if (phase !== 'live') return
    const track = streamRef.current?.getVideoTracks?.()[0]
    if (!track) return
    const onEnded = () => { setCamReady(false); toast.error('Camera turned off. Please keep it on.') }
    track.addEventListener('ended', onEnded)
    return () => track.removeEventListener('ended', onEnded)
  }, [phase])

  // Clean up on unmount.
  useEffect(() => () => { clearInterval(timerRef.current); stopCamera() }, [stopCamera])

  // ── Anti-cheat: tab/window switch detection during the live interview ──────
  useEffect(() => {
    if (phase !== 'live') return
    const onHidden = () => {
      if (document.hidden) {
        tabSwitchesRef.current += 1
        setTabSwitches(tabSwitchesRef.current)
        toast.error('You left the interview window. This has been noted.', { icon: '⚠️' })
      }
    }
    document.addEventListener('visibilitychange', onHidden)
    return () => document.removeEventListener('visibilitychange', onHidden)
  }, [phase])

  // ── Anti-cheat: block copy/cut/contextmenu globally while live ────────────
  useEffect(() => {
    if (phase !== 'live') return
    const block = (e) => { e.preventDefault(); return false }
    document.addEventListener('copy', block)
    document.addEventListener('cut', block)
    document.addEventListener('contextmenu', block)
    return () => {
      document.removeEventListener('copy', block)
      document.removeEventListener('cut', block)
      document.removeEventListener('contextmenu', block)
    }
  }, [phase])

  // ── Timer ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (phase !== 'live') return
    timerRef.current = setInterval(() => {
      setRemaining(r => {
        if (r <= 1) { clearInterval(timerRef.current); finishOnTimeout(); return 0 }
        if (r === 300) toast('5 minutes left.', { icon: '⏳' })
        return r - 1
      })
    }, 1000)
    return () => clearInterval(timerRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase])

  // ── Flow actions ──────────────────────────────────────────────────────────
  const goToCamera = () => {
    // Demo bypass: skip camera gate when running in mock/preview mode
    if (import.meta.env.DEV) { setPhase('rules'); return }
    setPhase('camera'); startCamera()
  }

  const beginInterview = async () => {
    setLoading(true)
    try {
      const r = await mockAPI.start({ round_type: 'full' })
      setMockId(r.data.mock_id)
      setExchangeCount(0)
      setMessages([{ role: 'interviewer', text: r.data.opening }])
      setRemaining(DURATION_SECONDS)
      setPhase('live')
    } catch (e) {
      if (e?.response?.status === 403) toast.error('Mock interviews require an active subscription.')
      else toast.error('Could not start the interview. Try again.')
    } finally { setLoading(false) }
  }

  const submitAnswer = async (endRequested = false) => {
    const text = answer.trim()
    if ((!text && !endRequested) || !mockId || loading) return
    const mine = endRequested ? (text || '(ending interview)') : text
    setAnswer('')
    if (!endRequested) setMessages(m => [...m, { role: 'candidate', text: mine }])
    setLoading(true)
    try {
      const r = await mockAPI.chat({
        mock_id: mockId,
        message: mine,
        end_requested: endRequested,
        tab_switches: tabSwitchesRef.current,
        camera_active: !!streamRef.current?.active,
      })
      setExchangeCount(r.data.exchange_count || 0)
      setMessages(m => [...m, { role: 'interviewer', text: r.data.reply }])
      if (r.data.is_complete) finish(r.data)
    } catch { toast.error('Failed to submit your answer.') }
    finally { setLoading(false) }
  }

  const finish = (data) => {
    clearInterval(timerRef.current)
    stopCamera()
    setResult({
      score: data.overall_score,
      verdict: data.verdict,
      feedback: data.feedback_summary || data.reply,
    })
    setPhase('debrief')
  }

  const finishOnTimeout = async () => {
    toast('Time is up. Wrapping up your interview.', { icon: '⏰' })
    if (mockId) {
      try {
        const r = await mockAPI.chat({
          mock_id: mockId,
          message: answer.trim() || '(time expired)',
          end_requested: true,
          tab_switches: tabSwitchesRef.current,
          camera_active: !!streamRef.current?.active,
        })
        if (r.data.is_complete) return finish(r.data)
      } catch {}
    }
    stopCamera()
    setResult({ score: null, verdict: null, feedback: 'The interview ended when the timer ran out. Start a new round when you are ready.' })
    setPhase('debrief')
  }

  const mm = String(Math.floor(remaining / 60)).padStart(2, '0')
  const ss = String(remaining % 60).padStart(2, '0')
  const urgent = remaining <= 300

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', position: 'relative' }}>
      <AnimatePresence mode="wait">

        {/* ─── SETUP ─────────────────────────────────────────────────── */}
        {phase === 'setup' && (
          <motion.div key="setup" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ maxWidth: 720, margin: '0 auto', padding: '64px 28px' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, padding: '5px 12px', borderRadius: 20, background: 'var(--indigo-dim)', color: 'var(--brand)', fontSize: 11, fontWeight: 700, letterSpacing: 0.5, marginBottom: 20 }}>
              <FiShield size={12} /> PROCTORED SESSION
            </div>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 34, fontWeight: 700, letterSpacing: '-1.2px', marginBottom: 10 }}>
              Sit a real interview.
            </h1>
            <p style={{ fontSize: 15, color: 'var(--text-2)', lineHeight: 1.6, marginBottom: 36, maxWidth: 540 }}>
              Thirty minutes. Questions drawn from your resume and your {user?.target_company || 'target company'}.
              Camera on, no copy-paste — exactly like the real thing. You'll get a full debrief at the end.
            </p>

            <button onClick={goToCamera} className="btn btn-primary" style={{ padding: '13px 28px', fontSize: 14 }}>
              Continue <FiArrowRight size={15} />
            </button>
            <button onClick={() => navigate('/interviews')} className="btn btn-ghost" style={{ marginLeft: 12 }}>Cancel</button>
          </motion.div>
        )}

        {/* ─── CAMERA GATE ───────────────────────────────────────────── */}
        {phase === 'camera' && (
          <motion.div key="camera" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ maxWidth: 560, margin: '0 auto', padding: '56px 28px', textAlign: 'center' }}>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, letterSpacing: '-0.6px', marginBottom: 8 }}>
              Camera check
            </h2>
            <p style={{ fontSize: 14, color: 'var(--text-2)', marginBottom: 28, lineHeight: 1.6 }}>
              Your camera stays on for the whole session — it's never recorded or uploaded.
              It's live on your screen only, to keep the pressure real.
            </p>

            <div style={{
              position: 'relative', width: '100%', aspectRatio: '4 / 3', borderRadius: 16, overflow: 'hidden',
              background: '#000', border: `1px solid ${camReady ? 'var(--brand)' : 'var(--border)'}`,
              marginBottom: 24, display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <video ref={videoRef} muted playsInline
                style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)', display: camReady ? 'block' : 'none' }} />
              {!camReady && (
                <div style={{ color: 'var(--text-3)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, padding: 24 }}>
                  {camError ? <FiVideoOff size={32} /> : <Spinner size={28} />}
                  <span style={{ fontSize: 13, maxWidth: 320, lineHeight: 1.5 }}>{camError || 'Requesting camera…'}</span>
                </div>
              )}
              {camReady && (
                <div style={{ position: 'absolute', top: 12, left: 12, display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px', borderRadius: 6, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(8px)', fontSize: 11, fontWeight: 600, color: 'var(--green)' }}>
                  <span style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--green)' }} /> Live
                </div>
              )}
            </div>

            {camError ? (
              <button onClick={startCamera} className="btn btn-primary">Retry camera access</button>
            ) : (
              <button onClick={() => setPhase('rules')} disabled={!camReady} className="btn btn-primary" style={{ padding: '13px 28px', fontSize: 14 }}>
                My camera looks good <FiArrowRight size={15} />
              </button>
            )}
            <div>
              <button onClick={() => { stopCamera(); setPhase('setup') }} className="btn btn-ghost" style={{ marginTop: 14 }}>Back</button>
            </div>
          </motion.div>
        )}

        {/* ─── RULES ─────────────────────────────────────────────────── */}
        {phase === 'rules' && (
          <motion.div key="rules" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ maxWidth: 560, margin: '0 auto', padding: '56px 28px' }}>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, letterSpacing: '-0.6px', marginBottom: 24, textAlign: 'center' }}>
              Before you begin
            </h2>
            <div style={{ display: 'grid', gap: 14, marginBottom: 32 }}>
              {[
                [FiClock, '30 minutes', 'The timer starts the moment you begin and does not pause.'],
                [FiLock, 'No copy or paste', 'You can\'t copy the questions or paste prepared answers. Think on your feet.'],
                [FiVideo, 'Camera stays on', 'If you turn it off, we\'ll know. Nothing is recorded.'],
                [FiAlertTriangle, 'Stay in this window', 'Switching tabs is flagged, just like a real remote interview.'],
              ].map(([Icon, title, desc]) => (
                <div key={title} style={{ display: 'flex', gap: 14, padding: '16px 18px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12 }}>
                  <div style={{ flexShrink: 0, width: 36, height: 36, borderRadius: 9, background: 'var(--indigo-dim)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Icon size={16} color="var(--brand)" />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>{title}</div>
                    <div style={{ fontSize: 13, color: 'var(--text-3)', lineHeight: 1.5 }}>{desc}</div>
                  </div>
                </div>
              ))}
            </div>
            <button onClick={beginInterview} disabled={loading} className="btn btn-primary" style={{ width: '100%', padding: '14px', fontSize: 15 }}>
              {loading ? <><Spinner size={16} color="white" /> Preparing your interviewer…</> : <>Start interview · 30:00</>}
            </button>
          </motion.div>
        )}

        {/* ─── LIVE ──────────────────────────────────────────────────── */}
        {phase === 'live' && (
          <motion.div key="live" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            style={{ maxWidth: 1100, margin: '0 auto', padding: '20px 24px', height: '100vh', display: 'flex', flexDirection: 'column' }}>
            {/* top bar */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 15 }}>{user?.target_company || 'Mock'} Interview</span>
                {exchangeCount > 0 && <span style={{ fontSize: 12, color: 'var(--text-3)' }}>{exchangeCount} exchange{exchangeCount !== 1 ? 's' : ''}</span>}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                {tabSwitches > 0 && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: 'var(--amber)' }}>
                    <FiAlertTriangle size={12} /> {tabSwitches} flag{tabSwitches > 1 ? 's' : ''}
                  </span>
                )}
                <span className={urgent ? 'countdown-urgent' : ''}
                  style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 600, color: urgent ? 'var(--red)' : 'var(--text-1)' }}>
                  <FiClock size={14} /> {mm}:{ss}
                </span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 20, flex: 1, minHeight: 0 }}>
              {/* conversation */}
              <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 14, padding: '4px 8px 4px 0', userSelect: 'none' }}
                  onCopy={(e) => e.preventDefault()}>
                  {messages.map((m, i) => (
                    <motion.div key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                      className={m.role === 'candidate' ? 'bubble-user' : 'bubble-ai'}
                      style={m.role !== 'candidate' ? { userSelect: 'none' } : undefined}>
                      {m.role === 'interviewer'
                        ? <div className="md"><ReactMarkdown>{m.text}</ReactMarkdown></div>
                        : m.text}
                    </motion.div>
                  ))}
                  {loading && <div className="bubble-ai"><TypingDots /></div>}
                  <div ref={endRef} />
                </div>

                {/* answer box */}
                <div style={{ marginTop: 14 }}>
                  <textarea
                    value={answer}
                    onChange={e => setAnswer(e.target.value)}
                    onPaste={(e) => { e.preventDefault(); toast.error('Pasting is disabled during the interview.') }}
                    onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submitAnswer() }}
                    placeholder="Type your answer… (paste is disabled · ⌘/Ctrl + Enter to send)"
                    disabled={loading}
                    rows={3}
                    className="input"
                    style={{ resize: 'none', fontFamily: 'var(--font-body)', lineHeight: 1.6 }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', marginTop: 10 }}>
                    <button
                      onClick={() => submitAnswer(false)}
                      disabled={loading || !answer.trim()}
                      className="btn btn-primary"
                    >
                      Send <FiSend size={14} />
                    </button>
                  </div>
                </div>
              </div>

              {/* camera column */}
              <div>
                <div style={{ position: 'relative', width: '100%', aspectRatio: '3 / 4', borderRadius: 14, overflow: 'hidden', background: '#000', border: `1px solid ${camReady ? 'var(--border-bright)' : 'var(--red)'}` }}>
                  <video ref={videoRef} muted playsInline
                    style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)' }} />
                  <div style={{ position: 'absolute', top: 10, left: 10, display: 'flex', alignItems: 'center', gap: 6, padding: '4px 9px', borderRadius: 6, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(8px)', fontSize: 10, fontWeight: 700, letterSpacing: 0.5, color: camReady ? 'var(--green)' : 'var(--red)' }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: camReady ? 'var(--green)' : 'var(--red)' }} />
                    {camReady ? 'LIVE' : 'CAMERA OFF'}
                  </div>
                </div>
                <p style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 10, lineHeight: 1.5, textAlign: 'center' }}>
                  Not recorded. Live preview only.
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* ─── DEBRIEF ───────────────────────────────────────────────── */}
        {phase === 'debrief' && result && (
          <Debrief result={result} onRetake={() => {
            setPhase('setup'); setResult(null); setMessages([]); setAnswer('')
            setExchangeCount(0); setRemaining(DURATION_SECONDS); setTabSwitches(0); tabSwitchesRef.current = 0
          }} onExit={() => navigate('/interviews')} />
        )}
      </AnimatePresence>
    </div>
  )
}

// ── Debrief view ──────────────────────────────────────────────────────────────
function Debrief({ result, onRetake, onExit }) {
  const score = result.score
  const hasScore = typeof score === 'number'
  const verdict = result.verdict
  const tone = verdict === 'pass' ? 'var(--green)' : verdict === 'borderline' ? 'var(--amber)' : verdict === 'fail' ? 'var(--red)' : 'var(--text-2)'
  const headline = verdict === 'pass'
    ? "You're ready."
    : verdict === 'borderline'
      ? "Close. A bit more and you're there."
      : verdict === 'fail'
        ? "Not yet — but now you know exactly what to fix."
        : "Interview ended."
  const sub = verdict === 'pass'
    ? "You'd move to the next round. Don't over-prepare now — trust it."
    : verdict === 'borderline'
      ? "You showed real signal. Tighten the gaps below and come back."
      : verdict === 'fail'
        ? "Everyone starts here. The debrief below is your roadmap — work through it and retake."
        : "Start a fresh round whenever you're ready."

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
      style={{ maxWidth: 720, margin: '0 auto', padding: '56px 28px 80px' }}>
      <div style={{ textAlign: 'center', marginBottom: 36 }}>
        {hasScore && (
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 72, fontWeight: 700, letterSpacing: -3, lineHeight: 1, color: tone }}>
            {Math.round(score)}<span style={{ fontSize: 24, color: 'var(--text-3)' }}>/100</span>
          </div>
        )}
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, letterSpacing: '-0.6px', marginTop: hasScore ? 14 : 0, marginBottom: 8, color: tone }}>
          {headline}
        </h1>
        <p style={{ fontSize: 14, color: 'var(--text-2)', maxWidth: 460, margin: '0 auto', lineHeight: 1.6 }}>{sub}</p>
      </div>

      <div style={{ padding: '24px 26px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 16, marginBottom: 28 }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.5, color: 'var(--text-3)', marginBottom: 16 }}>YOUR DEBRIEF</div>
        <div className="md" style={{ fontSize: 14, color: 'var(--text-2)', lineHeight: 1.75 }}>
          <ReactMarkdown>{result.feedback || 'Interview completed.'}</ReactMarkdown>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12 }}>
        <button onClick={onRetake} className="btn btn-primary" style={{ padding: '12px 24px' }}>
          Retake when ready <FiArrowRight size={14} />
        </button>
        <button onClick={onExit} className="btn btn-ghost">View all interviews</button>
      </div>
    </motion.div>
  )
}
