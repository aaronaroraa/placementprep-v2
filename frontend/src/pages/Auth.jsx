import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { FiMail, FiLock, FiUser, FiEye, FiEyeOff, FiZap } from 'react-icons/fi'
import { authAPI, userAPI } from '../api'
import { useStore } from '../stores'
import { Orbs, Spinner } from '../components'

// Google icon SVG
function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 48 48">
      <path fill="#FFC107" d="M43.6 20.1H42V20H24v8h11.3C33.7 32.1 29.3 35 24 35c-6.1 0-11-4.9-11-11s4.9-11 11-11c2.8 0 5.3 1 7.2 2.7l5.7-5.7C33.6 7.2 29 5 24 5 12.4 5 3 14.4 3 26s9.4 21 21 21c11 0 20-8 20-21 0-1.3-.1-2.6-.4-3.9z"/>
      <path fill="#FF3D00" d="M6.3 15.7l6.6 4.8C14.6 17 19 14 24 14c2.8 0 5.3 1 7.2 2.7l5.7-5.7C33.6 7.2 29 5 24 5 16.3 5 9.7 9.4 6.3 15.7z"/>
      <path fill="#4CAF50" d="M24 47c5.2 0 9.9-1.9 13.5-5l-6.2-5.3C29.3 38.2 26.8 39 24 39c-5.3 0-9.7-2.9-11.3-7H6.4C9.7 39.6 16.3 47 24 47z"/>
      <path fill="#1976D2" d="M43.6 20.1H42V20H24v8h11.3c-.8 2.2-2.3 4.1-4.2 5.4l6.2 5.3C43.1 37.3 47 32 47 26c0-1.3-.1-2.6-.4-3.9z"/>
    </svg>
  )
}

// ── Callback page for Google OAuth redirect ───────────────────────────────────
export function AuthCallback() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const setUser = useStore(s => s.setUser)

  useEffect(() => {
    const at = params.get('access_token')
    const rt = params.get('refresh_token')
    const isNew = params.get('is_new') === 'True'
    if (!at) { navigate('/'); return }
    localStorage.setItem('access_token', at)
    localStorage.setItem('refresh_token', rt || '')
    userAPI.me().then(r => {
      setUser(r.data)
      navigate(isNew || !r.data.onboarding_completed ? '/onboarding' : '/dashboard')
    }).catch(() => navigate('/'))
  }, [])

  return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Spinner size={32} />
    </div>
  )
}

// ── Main Auth page ────────────────────────────────────────────────────────────
export default function Auth() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [mode, setMode] = useState(searchParams.get('mode') === 'login' ? 'login' : 'register')
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm: '' })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [showPw, setShowPw] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const setUser = useStore(s => s.setUser)

  const set = f => e => { setForm(p => ({ ...p, [f]: e.target.value })); setErrors(p => ({ ...p, [f]: '' })) }

  const handleGoogle = async () => {
    setGoogleLoading(true)
    try {
      const r = await authAPI.googleUrl()
      window.location.href = r.data.url
    } catch {
      toast.error('Google auth unavailable — check GOOGLE_CLIENT_ID in .env')
      setGoogleLoading(false)
    }
  }

  const validate = () => {
    const e = {}
    if (mode === 'register' && !form.full_name.trim()) e.full_name = 'Required'
    if (!form.email) e.email = 'Required'
    else if (!/\S+@\S+\.\S+/.test(form.email)) e.email = 'Invalid email'
    if (!form.password) e.password = 'Required'
    else if (form.password.length < 8) e.password = 'Min 8 characters'
    if (mode === 'register' && form.password !== form.confirm) e.confirm = 'Passwords do not match'
    return e
  }

  const handleSubmit = async e => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setLoading(true)
    try {
      const res = mode === 'register'
        ? await authAPI.register({ full_name: form.full_name, email: form.email, password: form.password })
        : await authAPI.login({ email: form.email, password: form.password })
      localStorage.setItem('access_token', res.data.access_token)
      localStorage.setItem('refresh_token', res.data.refresh_token)
      const me = await userAPI.me()
      setUser(me.data)
      toast.success(mode === 'register' ? 'Account created!' : 'Welcome back!')
      navigate(mode === 'register' || !me.data.onboarding_completed ? '/onboarding' : '/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, position: 'relative', overflow: 'hidden' }}>
      <Orbs />
      <motion.div initial={{ opacity: 0, y: 20, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.35 }}
        style={{ width: '100%', maxWidth: 400, position: 'relative', zIndex: 1, background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 18, padding: 36 }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ width: 44, height: 44, background: 'var(--indigo)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 14px' }}>
            <FiZap size={20} color="white" />
          </div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text-1)', marginBottom: 4 }}>
            {mode === 'login' ? 'Welcome back' : 'Create your account'}
          </h1>
          <p style={{ fontSize: 12, color: 'var(--text-3)' }}>
            {mode === 'login' ? 'Continue your prep journey' : 'Free forever. Start preparing today.'}
          </p>
        </div>

        {/* Google button */}
        <motion.button whileTap={{ scale: 0.97 }} onClick={handleGoogle} disabled={googleLoading}
          style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, padding: '11px', borderRadius: 9, background: 'var(--raised)', border: '1px solid var(--border-bright)', color: 'var(--text-1)', fontSize: 13, fontWeight: 600, cursor: 'pointer', marginBottom: 20 }}>
          {googleLoading ? <Spinner size={16} /> : <GoogleIcon />}
          Continue with Google
        </motion.button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
          <span style={{ fontSize: 11, color: 'var(--text-3)' }}>or</span>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
        </div>

        <form onSubmit={handleSubmit}>
          <AnimatePresence mode="wait">
            {mode === 'register' && (
              <motion.div key="name" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} style={{ marginBottom: 12, overflow: 'hidden' }}>
                <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-3)', display: 'block', marginBottom: 5 }}>Full Name</label>
                <div style={{ position: 'relative' }}>
                  <FiUser size={13} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-3)' }} />
                  <input type="text" value={form.full_name} onChange={set('full_name')} placeholder="Rahul Sharma" className="input" style={{ paddingLeft: 34, borderColor: errors.full_name ? 'var(--red)' : undefined }} />
                </div>
                {errors.full_name && <p style={{ fontSize: 11, color: 'var(--red)', marginTop: 3 }}>{errors.full_name}</p>}
              </motion.div>
            )}
          </AnimatePresence>

          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-3)', display: 'block', marginBottom: 5 }}>Email</label>
            <div style={{ position: 'relative' }}>
              <FiMail size={13} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-3)' }} />
              <input type="email" value={form.email} onChange={set('email')} placeholder="you@college.edu" className="input" style={{ paddingLeft: 34, borderColor: errors.email ? 'var(--red)' : undefined }} />
            </div>
            {errors.email && <p style={{ fontSize: 11, color: 'var(--red)', marginTop: 3 }}>{errors.email}</p>}
          </div>

          <div style={{ marginBottom: mode === 'register' ? 12 : 22 }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-3)', display: 'block', marginBottom: 5 }}>Password</label>
            <div style={{ position: 'relative' }}>
              <FiLock size={13} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-3)' }} />
              <input type={showPw ? 'text' : 'password'} value={form.password} onChange={set('password')} placeholder="Min 8 characters" className="input" style={{ paddingLeft: 34, paddingRight: 40, borderColor: errors.password ? 'var(--red)' : undefined }} />
              <button type="button" onClick={() => setShowPw(p => !p)} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-3)', padding: 0 }}>
                {showPw ? <FiEyeOff size={13} /> : <FiEye size={13} />}
              </button>
            </div>
            {errors.password && <p style={{ fontSize: 11, color: 'var(--red)', marginTop: 3 }}>{errors.password}</p>}
          </div>

          <AnimatePresence mode="wait">
            {mode === 'register' && (
              <motion.div key="confirm" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} style={{ marginBottom: 22, overflow: 'hidden' }}>
                <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-3)', display: 'block', marginBottom: 5 }}>Confirm Password</label>
                <div style={{ position: 'relative' }}>
                  <FiLock size={13} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-3)' }} />
                  <input type="password" value={form.confirm} onChange={set('confirm')} placeholder="Repeat password" className="input" style={{ paddingLeft: 34, borderColor: errors.confirm ? 'var(--red)' : undefined }} />
                </div>
                {errors.confirm && <p style={{ fontSize: 11, color: 'var(--red)', marginTop: 3 }}>{errors.confirm}</p>}
              </motion.div>
            )}
          </AnimatePresence>

          <motion.button type="submit" disabled={loading} whileTap={{ scale: 0.97 }} className="btn btn-primary" style={{ width: '100%', padding: '12px', fontSize: 13 }}>
            {loading ? <Spinner size={16} color="white" /> : mode === 'login' ? 'Sign In →' : 'Create Account →'}
          </motion.button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 12, color: 'var(--text-3)' }}>
          {mode === 'login' ? "Don't have an account? " : "Already have one? "}
          <button onClick={() => setMode(m => m === 'login' ? 'register' : 'login')} style={{ color: 'var(--indigo)', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer', fontSize: 12 }}>
            {mode === 'login' ? 'Register free' : 'Sign in'}
          </button>
        </p>
      </motion.div>
    </div>
  )
}
