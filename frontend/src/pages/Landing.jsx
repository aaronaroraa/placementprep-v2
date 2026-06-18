import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FiZap, FiArrowRight, FiCode, FiMic, FiCalendar, FiTrendingUp, FiTarget, FiCpu } from 'react-icons/fi'
import { Orbs } from '../components'

const FEATURES = [
  { icon: FiTarget, label: 'Conversational Onboarding', desc: 'A coach asks smart questions and builds your plan — not a boring form.', color: 'var(--indigo)' },
  { icon: FiCode, label: 'Real Interviewer AI', desc: 'AI interrupts while you code. Asks complexity. Probes edge cases. Acts like your actual interviewer.', color: 'var(--green)' },
  { icon: FiMic, label: 'Mock Interview', desc: 'Full 45-min simulation. Questions from YOUR resume. Score + debrief at end.', color: 'var(--amber)' },
  { icon: FiCalendar, label: 'Google Calendar Sync', desc: 'Daily prep blocks auto-created. Task completion syncs back. Never miss a session.', color: '#a78bfa' },
  { icon: FiCpu, label: 'Flashcard Drills', desc: 'Rapid-fire viva on OS, DBMS, CN. AI pushes back on incomplete answers.', color: 'var(--red)' },
  { icon: FiTrendingUp, label: 'Readiness Tracking', desc: 'Streak, topic scores, mock interview history. One number: are you ready?', color: 'var(--green)' },
]

export default function Landing() {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', position: 'relative', overflow: 'hidden' }}>
      <Orbs />

      {/* Nav */}
      <nav style={{ position: 'relative', zIndex: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 48px', height: 60, borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 30, height: 30, background: 'var(--indigo)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FiZap size={14} color="white" />
          </div>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 15, color: 'var(--text-1)' }}>PlacementPrep AI</span>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <Link to="/auth?mode=login">
            <button className="btn btn-ghost btn-sm">Sign In</button>
          </Link>
          <Link to="/auth">
            <button className="btn btn-primary btn-sm">Get Started Free</button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ position: 'relative', zIndex: 1, padding: '110px 48px 80px', maxWidth: 1000, margin: '0 auto' }}>
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          {/* Pill */}
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, padding: '5px 14px', borderRadius: 20, background: 'var(--indigo-dim)', border: '1px solid rgba(13,148,136,0.3)', marginBottom: 32 }}>
            <div style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--green)' }} />
            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--indigo)', letterSpacing: 0.3 }}>AI Coach · Real Interviewer · Google Calendar</span>
          </div>

          {/* Headline */}
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(44px, 7vw, 82px)', fontWeight: 700, lineHeight: 1.04, letterSpacing: '-3px', color: 'var(--text-1)', marginBottom: 28 }}>
            From zero to{' '}
            <span style={{ color: 'var(--indigo)' }}>offer</span>
            <br />in days, not months.
          </h1>

          <p style={{ fontSize: 17, color: 'var(--text-2)', maxWidth: 520, lineHeight: 1.75, marginBottom: 44 }}>
            The only placement prep platform that acts like a real coach —
            builds your plan, drills you like an interviewer, and blocks time on your calendar.
          </p>

          <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'center' }}>
            <Link to="/auth">
              <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} className="btn btn-primary" style={{ padding: '13px 30px', fontSize: 14 }}>
                Start Preparing Free <FiArrowRight size={14} />
              </motion.button>
            </Link>
            <Link to="/auth?mode=login">
              <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} className="btn btn-ghost" style={{ padding: '13px 30px', fontSize: 14 }}>
                Sign In
              </motion.button>
            </Link>
          </div>
        </motion.div>

        {/* Stats row */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35 }}
          style={{ display: 'flex', gap: 0, marginTop: 80, borderTop: '1px solid var(--border)', paddingTop: 40 }}>
          {[['1 app', 'for everything'], ['50+', 'DSA problems'], ['23+', 'company profiles'], ['4', 'plan types']].map(([val, label], i) => (
            <div key={i} style={{ flex: 1, paddingRight: 32, borderRight: i < 3 ? '1px solid var(--border)' : 'none', paddingLeft: i > 0 ? 32 : 0 }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 700, color: 'var(--text-1)', letterSpacing: '-1px' }}>{val}</div>
              <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 3 }}>{label}</div>
            </div>
          ))}
        </motion.div>
      </section>

      {/* Features */}
      <section style={{ position: 'relative', zIndex: 1, padding: '0 48px 100px', maxWidth: 1000, margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 1, border: '1px solid var(--border)', borderRadius: 16, overflow: 'hidden' }}>
          {FEATURES.map((f, i) => (
            <motion.div key={f.label}
              initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }}
              transition={{ delay: i * 0.06 }}
              style={{ padding: '28px 28px', background: 'var(--surface)', borderRight: (i % 3 !== 2) ? '1px solid var(--border)' : 'none', borderBottom: i < 3 ? '1px solid var(--border)' : 'none' }}>
              <div style={{ width: 36, height: 36, borderRadius: 9, background: `${f.color}18`, border: `1px solid ${f.color}28`, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
                <f.icon size={16} color={f.color} />
              </div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 15, color: 'var(--text-1)', marginBottom: 7 }}>{f.label}</div>
              <div style={{ fontSize: 12, color: 'var(--text-3)', lineHeight: 1.65 }}>{f.desc}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer style={{ position: 'relative', zIndex: 1, borderTop: '1px solid var(--border)', padding: '24px 48px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <span style={{ fontSize: 12, color: 'var(--text-3)' }}>© 2024 PlacementPrep AI — Built for India's engineering talent</span>
        <div style={{ display: 'flex', gap: 6 }}>
          {['FastAPI', 'React 18', 'Gemini AI', 'Judge0', 'Google Calendar'].map(b => (
            <span key={b} style={{ fontSize: 10, fontWeight: 600, padding: '3px 9px', borderRadius: 5, background: 'var(--raised)', color: 'var(--text-3)', border: '1px solid var(--border)' }}>{b}</span>
          ))}
        </div>
      </footer>
    </div>
  )
}
