import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FiZap, FiGrid, FiCode, FiBarChart2, FiMic, FiLogOut, FiCalendar, FiMap } from 'react-icons/fi'
import { clearAuth } from '../api'
import { useStore } from '../stores'
import { Navigate } from 'react-router-dom'

// ── ProtectedRoute ────────────────────────────────────────────────────────────
export function ProtectedRoute({ children }) {
  const token = localStorage.getItem('access_token')
  if (!token) return <Navigate to="/" replace />
  return children
}

// ── Spinner ───────────────────────────────────────────────────────────────────
export function Spinner({ size = 20, color = 'var(--indigo)' }) {
  return (
    <div style={{ width: size, height: size, border: `2px solid rgba(255,255,255,0.1)`, borderTopColor: color, borderRadius: '50%' }} className="spin" />
  )
}

// ── Background Orbs ───────────────────────────────────────────────────────────
export function Orbs() {
  return (
    <>
      <div className="orb" style={{ width: 500, height: 500, top: '-15%', left: '-10%', background: 'radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)' }} />
      <div className="orb" style={{ width: 400, height: 400, top: '40%', right: '-10%', background: 'radial-gradient(circle, rgba(34,211,165,0.06) 0%, transparent 70%)' }} />
      <div className="orb" style={{ width: 350, height: 350, bottom: '5%', left: '25%', background: 'radial-gradient(circle, rgba(99,102,241,0.05) 0%, transparent 70%)' }} />
    </>
  )
}

// ── Navbar ────────────────────────────────────────────────────────────────────
export function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const user = useStore(s => s.user)

  const logout = () => { clearAuth(); useStore.getState().clearUser(); navigate('/') }

  const links = [
    { to: '/dashboard', label: 'Mission', icon: FiGrid },
    { to: '/plan', label: 'Plan', icon: FiMap },
    { to: '/coding', label: 'Code', icon: FiCode },
    { to: '/mock', label: 'Interview', icon: FiMic },
    { to: '/analytics', label: 'Analytics', icon: FiBarChart2 },
  ]

  return (
    <nav style={{
      position: 'sticky', top: 0, zIndex: 100,
      background: 'rgba(6,6,13,0.85)', backdropFilter: 'blur(20px)',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 28px', height: 52,
    }}>
      <Link to="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: 8, textDecoration: 'none' }}>
        <div style={{ width: 28, height: 28, background: 'var(--indigo)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <FiZap size={13} color="white" />
        </div>
        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 14, color: 'var(--text-1)', letterSpacing: '-0.3px' }}>PlacementPrep</span>
      </Link>

      <div style={{ display: 'flex', gap: 2 }}>
        {links.map(({ to, label, icon: Icon }) => {
          const active = location.pathname.startsWith(to)
          return (
            <Link key={to} to={to} style={{ textDecoration: 'none' }}>
              <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.96 }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 5, padding: '5px 12px', borderRadius: 7,
                  background: active ? 'var(--indigo-dim)' : 'transparent',
                  color: active ? 'var(--indigo)' : 'var(--text-3)',
                  fontSize: 12, fontWeight: 500,
                  border: active ? '1px solid rgba(99,102,241,0.25)' : '1px solid transparent',
                  transition: 'all 0.15s',
                }}>
                <Icon size={12} />
                {label}
              </motion.div>
            </Link>
          )
        })}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {user?.calendar_connected && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: 'var(--green)', padding: '4px 10px', background: 'var(--green-dim)', borderRadius: 6 }}>
            <FiCalendar size={11} /> Synced
          </div>
        )}
        {user?.avatar_url && (
          <img src={user.avatar_url} alt="" style={{ width: 26, height: 26, borderRadius: '50%', border: '1px solid var(--border-bright)' }} />
        )}
        <motion.button whileTap={{ scale: 0.96 }} onClick={logout}
          style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '5px 11px', borderRadius: 7, background: 'var(--red-dim)', border: '1px solid rgba(244,63,94,0.2)', color: 'var(--red)', fontSize: 11, fontWeight: 600, cursor: 'pointer' }}>
          <FiLogOut size={11} /> Out
        </motion.button>
      </div>
    </nav>
  )
}

// ── Typing Dots ───────────────────────────────────────────────────────────────
export function TypingDots() {
  return (
    <div style={{ display: 'flex', gap: 4, alignItems: 'center', padding: '10px 14px' }}>
      {[0, 1, 2].map(i => (
        <motion.div key={i} className="typing-dot"
          animate={{ y: [0, -5, 0] }}
          transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.16 }}
        />
      ))}
    </div>
  )
}

// ── Section label ─────────────────────────────────────────────────────────────
export function Label({ children }) {
  return (
    <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.5, color: 'var(--text-3)', textTransform: 'uppercase', marginBottom: 12 }}>
      {children}
    </p>
  )
}
