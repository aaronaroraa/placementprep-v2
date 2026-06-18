// MockInterview.jsx — full 45-min simulation with resume-based questions
import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'
import { FiMic, FiMicOff, FiSend, FiAward, FiClock, FiChevronRight, FiVolume2, FiVolumeX } from 'react-icons/fi'
import { mockAPI } from '../api'
import { useStore } from '../stores'
import { Navbar, Spinner, TypingDots, Orbs } from '../components'

export function MockInterview() {
  const user = useStore(s => s.user)
  const [state, setState] = useState('idle') // idle|active|complete
  const [mockId, setMockId] = useState(null)
  const [qIndex, setQIndex] = useState(0)
  const [totalQ, setTotalQ] = useState(0)
  const [currentQ, setCurrentQ] = useState('')
  const [answer, setAnswer] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  
  // Audio State
  const [isListening, setIsListening] = useState(false)
  const [ttsEnabled, setTtsEnabled] = useState(true)
  const recognitionRef = useRef(null)

  const timerRef = useRef(null)
  const endRef = useRef(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  useEffect(() => { 
    if (state === 'active') { 
      timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000) 
    } 
    return () => clearInterval(timerRef.current) 
  }, [state])

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      window.speechSynthesis?.cancel()
      if (recognitionRef.current) recognitionRef.current.stop()
    }
  }, [])

  // Setup STT
  useEffect(() => {
    const Sr = window.SpeechRecognition || window.webkitSpeechRecognition
    if (Sr && !recognitionRef.current) {
      const recognition = new Sr()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-US'

      recognition.onresult = (e) => {
        let finalTrans = ''
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const t = e.results[i][0].transcript
          if (e.results[i].isFinal) finalTrans += t + ' '
        }
        if (finalTrans) {
          setAnswer(prev => prev + finalTrans)
        }
      }
      
      recognition.onend = () => {
        setIsListening(false)
      }
      
      recognitionRef.current = recognition
    }
  }, [])

  const toggleListen = () => {
    if (!recognitionRef.current) return toast.error('Speech recognition not supported in your browser')
    if (isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    } else {
      window.speechSynthesis.cancel() // Stop AI if speaking
      recognitionRef.current.start()
      setIsListening(true)
    }
  }

  const speak = (text) => {
    if (!window.speechSynthesis || !ttsEnabled) return
    window.speechSynthesis.cancel()
    const plainText = text.replace(/[*_#`\n]/g, ' ')
    const msg = new SpeechSynthesisUtterance(plainText)
    msg.rate = 1.05
    window.speechSynthesis.speak(msg)
  }

  const start = async () => {
    setLoading(true)
    try {
      const r = await mockAPI.start({ interview_type: 'full' })
      setMockId(r.data.mock_id)
      setTotalQ(r.data.total_questions)
      setCurrentQ(r.data.first_question)
      setQIndex(0)
      
      const firstText = `Welcome. I'm going to conduct your ${user?.target_company || 'technical'} ${user?.target_role || 'SDE'} interview today.\n\nThere are ${r.data.total_questions} questions. Take your time, think out loud, and be specific.\n\n**${r.data.first_question}**`
      setMessages([{ role: 'interviewer', text: firstText }])
      setState('active')
      speak(firstText)
    } catch { toast.error('Failed to start interview') }
    finally { setLoading(false) }
  }

  const submitAnswer = async () => {
    if (!answer.trim() || !mockId) return
    
    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
    }

    const myAnswer = answer.trim()
    setAnswer('')
    setMessages(m => [...m, { role: 'candidate', text: myAnswer }])
    setLoading(true)
    try {
      const r = await mockAPI.answer({ mock_id: mockId, question_index: qIndex, answer: myAnswer })
      if (r.data.is_complete) {
        setMessages(m => [...m, { role: 'interviewer', text: r.data.interviewer_response }])
        speak(r.data.interviewer_response)
        setResult({ score: r.data.overall_score, feedback: r.data.feedback_summary })
        setState('complete')
        clearInterval(timerRef.current)
      } else {
        const nextText = `${r.data.interviewer_response}\n\n**Next: ${r.data.next_question}**`
        setMessages(m => [...m, { role: 'interviewer', text: nextText }])
        speak(nextText)
        setQIndex(r.data.next_question_index || qIndex + 1)
        setCurrentQ(r.data.next_question)
      }
    } catch { toast.error('Failed to submit answer') }
    finally { setLoading(false) }
  }

  const mins = Math.floor(elapsed / 60), secs = elapsed % 60
  const pct = totalQ ? Math.round((qIndex / totalQ) * 100) : 0

  return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', position: 'relative' }}>
      <Orbs />
      <Navbar />
      <div style={{ position: 'relative', zIndex: 1, maxWidth: 800, margin: '0 auto', padding: '32px 28px 60px' }} className="page-enter">

        {state === 'idle' && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div style={{ marginBottom: 32 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 700, color: 'var(--text-1)', letterSpacing: '-1px' }}>Mock Interview</h1>
                
                <button onClick={() => setTtsEnabled(!ttsEnabled)} className="btn btn-ghost" style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
                  {ttsEnabled ? <FiVolume2 size={16} /> : <FiVolumeX size={16} />}
                  {ttsEnabled ? 'Voice Enabled' : 'Voice Muted'}
                </button>
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-3)' }}>Full simulation · Questions from your resume · Score + debrief at end</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginBottom: 32 }}>
              {[
                ['🎯 Targeted', `Questions built from YOUR ${user?.target_company || 'target company'} profile`],
                ['🎙️ Interactive Voice', 'Talk back using your microphone just like a real interview'],
                ['📊 Scored', 'Score out of 100 + detailed debrief on what to improve'],
                ['⏱ Real Timing', '45 minutes — same as a real interview round'],
              ].map(([title, desc]) => (
                <div key={title} style={{ padding: '18px 20px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12 }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 600, color: 'var(--text-1)', marginBottom: 6 }}>{title}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-3)', lineHeight: 1.55 }}>{desc}</div>
                </div>
              ))}
            </div>

            <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} onClick={start} disabled={loading} className="btn btn-primary" style={{ padding: '13px 36px', fontSize: 14 }}>
              {loading ? <><Spinner size={16} color="white" /> Starting interview…</> : <><FiMic size={15} /> Begin Interview</>}
            </motion.button>
          </motion.div>
        )}

        {state === 'active' && (
          <div>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
              <div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: 'var(--text-1)' }}>{user?.target_company || 'Technical'} Interview</div>
                <div style={{ fontSize: 11, color: 'var(--text-3)' }}>Q {qIndex + 1} of {totalQ}</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <button onClick={() => { setTtsEnabled(!ttsEnabled); if (ttsEnabled) window.speechSynthesis?.cancel() }} style={{ background: 'none', border: 'none', color: 'var(--text-3)', cursor: 'pointer' }}>
                  {ttsEnabled ? <FiVolume2 size={16} /> : <FiVolumeX size={16} />}
                </button>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 13, fontWeight: 600, color: elapsed > 2400 ? 'var(--red)' : 'var(--text-2)', fontFamily: 'var(--font-mono)' }}>
                  <FiClock size={13} /> {String(mins).padStart(2,'0')}:{String(secs).padStart(2,'0')}
                </div>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--indigo)' }}>{pct}%</div>
              </div>
            </div>
            <div className="progress-track" style={{ marginBottom: 24 }}>
              <div className="progress-fill" style={{ width: `${pct}%`, transition: 'width 0.4s' }} />
            </div>

            {/* Chat */}
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, overflow: 'hidden', marginBottom: 16 }}>
              <div style={{ maxHeight: 420, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: 14 }}>
                {messages.map((msg, i) => (
                  <motion.div key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                    className={msg.role === 'candidate' ? 'bubble-user' : 'bubble-ai'}>
                    {msg.role === 'interviewer' ? <div className="md"><ReactMarkdown>{msg.text}</ReactMarkdown></div> : msg.text}
                  </motion.div>
                ))}
                {loading && <div className="bubble-ai"><TypingDots /></div>}
                <div ref={endRef} />
              </div>
            </div>

            {/* Answer input */}
            {!loading && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, padding: '20px 0' }}>
                <div style={{ fontSize: 15, color: answer ? 'var(--text-1)' : 'var(--text-3)', textAlign: 'center', minHeight: 40, width: '100%', padding: '0 20px', fontStyle: isListening ? 'italic' : 'normal', lineHeight: 1.5 }}>
                  {isListening ? (answer ? `"${answer}"` : 'Listening carefully...') : (answer ? `"${answer}"` : '🎙️ Tap the microphone and speak your answer')}
                </div>
                
                <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                  <motion.button 
                    whileTap={{ scale: 0.92 }} 
                    onClick={toggleListen}
                    className="btn btn-icon"
                    style={{ 
                      padding: '24px', 
                      borderRadius: '50%',
                      background: isListening ? 'var(--red)' : 'var(--raised)', 
                      color: isListening ? 'white' : 'var(--text-1)',
                      border: isListening ? 'none' : '1px solid var(--border)',
                      boxShadow: isListening ? '0 0 30px rgba(239, 68, 68, 0.4)' : 'none'
                    }}>
                    {isListening ? <FiMicOff size={28} /> : <FiMic size={28} />}
                  </motion.button>
                  
                  {answer.trim() && !isListening && (
                    <motion.button initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} 
                      onClick={submitAnswer} className="btn btn-primary" style={{ padding: '16px 32px', borderRadius: 30, fontSize: 15 }}>
                      Submit Answer <FiSend size={18} />
                    </motion.button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {state === 'complete' && result && (
          <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}>
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
              <FiAward size={40} color="var(--amber)" style={{ marginBottom: 12 }} />
              <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, color: 'var(--text-1)', letterSpacing: '-0.5px', marginBottom: 8 }}>Interview Complete</h1>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 64, fontWeight: 700, color: result.score >= 70 ? 'var(--green)' : result.score >= 50 ? 'var(--amber)' : 'var(--red)', letterSpacing: -3, lineHeight: 1 }}>{Math.round(result.score || 0)}</div>
              <div style={{ fontSize: 13, color: 'var(--text-3)', marginTop: 6 }}>/ 100 · {mins} min interview</div>
            </div>
            <div style={{ padding: '24px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, marginBottom: 24 }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.5, color: 'var(--text-3)', marginBottom: 14 }}>INTERVIEWER DEBRIEF</div>
              <div className="md" style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.7 }}>
                <ReactMarkdown>{result.feedback || 'Interview completed.'}</ReactMarkdown>
              </div>
            </div>
            <motion.button whileTap={{ scale: 0.97 }} onClick={() => { setState('idle'); setElapsed(0); setMessages([]); setResult(null) }} className="btn btn-primary">
              Take Another Round <FiChevronRight size={14} />
            </motion.button>
          </motion.div>
        )}
      </div>
    </div>
  )
}

// ── Theory Flashcard Drill ────────────────────────────────────────────────────
export function Theory() {
  const user = useStore(s => s.user)
  const [topic, setTopic] = useState('OS')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [started, setStarted] = useState(false)
  
  // Theory Audio
  const [isListening, setIsListening] = useState(false)
  const [ttsEnabled, setTtsEnabled] = useState(true)
  const theoryRecRef = useRef(null)
  
  const endRef = useRef(null)
  const TOPICS = ['OS', 'DBMS', 'Computer Networks', 'OOP', 'System Design', 'DSA Theory']

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  useEffect(() => {
    return () => {
      window.speechSynthesis?.cancel()
      if (theoryRecRef.current) theoryRecRef.current.stop()
    }
  }, [])

  useEffect(() => {
    const Sr = window.SpeechRecognition || window.webkitSpeechRecognition
    if (Sr && !theoryRecRef.current) {
      const recognition = new Sr()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-US'

      recognition.onresult = (e) => {
        let finalTrans = ''
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const t = e.results[i][0].transcript
          if (e.results[i].isFinal) finalTrans += t + ' '
        }
        if (finalTrans) {
          setInput(prev => prev + finalTrans)
        }
      }
      
      recognition.onend = () => {
        setIsListening(false)
      }
      
      theoryRecRef.current = recognition
    }
  }, [])

  const toggleListen = () => {
    if (!theoryRecRef.current) return toast.error('Speech recognition not supported in your browser')
    if (isListening) {
      theoryRecRef.current.stop()
      setIsListening(false)
    } else {
      window.speechSynthesis.cancel() // Stop AI if speaking
      theoryRecRef.current.start()
      setIsListening(true)
    }
  }

  const speak = (text) => {
    if (!window.speechSynthesis || !ttsEnabled) return
    window.speechSynthesis.cancel()
    const plainText = text.replace(/[*_#`\n]/g, ' ')
    const msg = new SpeechSynthesisUtterance(plainText)
    msg.rate = 1.05
    window.speechSynthesis.speak(msg)
  }

  const startDrill = async () => {
    setStarted(true)
    setLoading(true)
    try {
      const { chatAPI } = await import('../api')
      const r = await chatAPI.send({ message: `Start a rapid-fire viva drill on ${topic}. Ask me your first question.`, context_type: 'flashcard', topic })
      setMessages([{ role: 'assistant', text: r.data.reply }])
      speak(r.data.reply)
    } catch {
      const m = `Let's drill ${topic}. First question: What is the difference between a process and a thread?`
      setMessages([{ role: 'assistant', text: m }])
      speak(m)
    } finally { setLoading(false) }
  }

  const send = async () => {
    const text = input.trim()
    if (!text) return
    
    if (isListening) {
      theoryRecRef.current?.stop()
      setIsListening(false)
    }

    setInput('')
    setMessages(m => [...m, { role: 'user', text }])
    setLoading(true)
    try {
      const { streamChat } = await import('../api')
      // Add an empty assistant bubble we'll fill as tokens arrive.
      setMessages(m => [...m, { role: 'assistant', text: '' }])
      let full = ''
      let firstChunk = true
      await streamChat(
        { message: text, context_type: 'flashcard', topic },
        {
          onDelta: (piece) => {
            full += piece
            if (firstChunk) { setLoading(false); firstChunk = false }
            setMessages(m => { const copy = [...m]; copy[copy.length - 1] = { role: 'assistant', text: full }; return copy })
          },
          onDone: () => { speak(full) },
          onError: () => {
            const fb = 'Good attempt. Think about the key distinguishing factor. Next question coming.'
            setMessages(m => { const copy = [...m]; copy[copy.length - 1] = { role: 'assistant', text: fb }; return copy })
            speak(fb)
          },
        }
      )
    } catch {
      const fb = 'Good attempt. Think about this more carefully — what\'s the key distinguishing factor?'
      setMessages(m => [...m, { role: 'assistant', text: fb }])
      speak(fb)
    } finally { setLoading(false) }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', position: 'relative' }}>
      <Orbs />
      <Navbar />
      <div style={{ position: 'relative', zIndex: 1, maxWidth: 700, margin: '0 auto', padding: '32px 28px 60px' }} className="page-enter">
        <div style={{ marginBottom: 28, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, color: 'var(--text-1)', letterSpacing: '-0.5px', marginBottom: 6 }}>Theory Drill</h1>
            <p style={{ fontSize: 13, color: 'var(--text-3)' }}>Rapid-fire viva. One question at a time. AI pushes back on incomplete answers.</p>
          </div>
          <button onClick={() => { setTtsEnabled(!ttsEnabled); if (ttsEnabled) window.speechSynthesis?.cancel() }} className="btn btn-ghost" style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
            {ttsEnabled ? <FiVolume2 size={16} /> : <FiVolumeX size={16} />}
          </button>
        </div>

        {!started ? (
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1.5, color: 'var(--text-3)', marginBottom: 12 }}>CHOOSE TOPIC</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 28 }}>
              {TOPICS.map(t => (
                <motion.button key={t} whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.96 }} onClick={() => setTopic(t)}
                  style={{ padding: '9px 18px', borderRadius: 9, border: `1px solid ${topic === t ? 'var(--indigo)' : 'var(--border)'}`, background: topic === t ? 'var(--indigo-dim)' : 'var(--surface)', color: topic === t ? 'var(--indigo)' : 'var(--text-2)', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
                  {t}
                </motion.button>
              ))}
            </div>
            <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} onClick={startDrill} className="btn btn-primary" style={{ padding: '12px 28px', fontSize: 13 }}>
              Start {topic} Drill →
            </motion.button>
          </div>
        ) : (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
              <span className="badge badge-indigo">{topic}</span>
              <button onClick={() => { setStarted(false); setMessages([]); window.speechSynthesis?.cancel(); }} style={{ fontSize: 11, color: 'var(--text-3)', background: 'none', border: 'none', cursor: 'pointer', marginLeft: 'auto' }}>← Change topic</button>
            </div>

            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, overflow: 'hidden', marginBottom: 14 }}>
              <div style={{ maxHeight: 440, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
                {messages.map((msg, i) => (
                  <motion.div key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                    className={msg.role === 'user' ? 'bubble-user' : 'bubble-ai'}>
                    {msg.role === 'assistant' ? <div className="md"><ReactMarkdown>{msg.text}</ReactMarkdown></div> : msg.text}
                  </motion.div>
                ))}
                {loading && <div className="bubble-ai"><TypingDots /></div>}
                <div ref={endRef} />
              </div>
            </div>

            {!loading && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, padding: '20px 0' }}>
                <div style={{ fontSize: 14, color: input ? 'var(--text-1)' : 'var(--text-3)', textAlign: 'center', minHeight: 40, width: '100%', padding: '0 20px', fontStyle: isListening ? 'italic' : 'normal', lineHeight: 1.5 }}>
                  {isListening ? (input ? `"${input}"` : 'Listening carefully...') : (input ? `"${input}"` : '🎙️ Tap the microphone to speak your answer')}
                </div>
                
                <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                  <motion.button 
                    whileTap={{ scale: 0.92 }} 
                    onClick={toggleListen}
                    className="btn btn-icon"
                    style={{ 
                      padding: '20px', 
                      borderRadius: '50%',
                      background: isListening ? 'var(--red)' : 'var(--raised)', 
                      color: isListening ? 'white' : 'var(--text-1)',
                      border: isListening ? 'none' : '1px solid var(--border)',
                      boxShadow: isListening ? '0 0 20px rgba(239, 68, 68, 0.4)' : 'none'
                    }}>
                    {isListening ? <FiMicOff size={22} /> : <FiMic size={22} />}
                  </motion.button>
                  
                  {input.trim() && !isListening && (
                    <motion.button initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} 
                      onClick={send} className="btn btn-primary btn-icon" style={{ padding: '16px', borderRadius: '50%' }}>
                      <FiSend size={18} />
                    </motion.button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
