import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, BarChart, Bar } from 'recharts'
import { FiTrendingUp, FiTrendingDown, FiMinus, FiAlertTriangle, FiAward } from 'react-icons/fi'
import { analyticsAPI } from '../api'
import { Navbar, Spinner, Label, Orbs } from '../components'

const TT = ({ active, payload, label }) => active && payload?.length ? (
  <div style={{ background: 'var(--raised)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 12px' }}>
    <p style={{ fontSize: 10, color: 'var(--text-3)', marginBottom: 4 }}>{label}</p>
    {payload.map(p => <p key={p.name} style={{ fontSize: 12, color: p.color, fontWeight: 600 }}>{p.name}: {typeof p.value === 'number' ? Math.round(p.value) : p.value}</p>)}
  </div>
) : null

function ReadinessGauge({ score }) {
  const pct = Math.min(100, Math.max(0, score || 0))
  const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? 'var(--amber)' : 'var(--indigo)'
  const r = 60, C = 2 * Math.PI * r
  const offset = C - (pct / 100) * C
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '32px 20px' }}>
      <svg width={160} height={160} viewBox="0 0 160 160">
        <circle cx={80} cy={80} r={r} fill="none" stroke="rgba(17,24,39,0.10)" strokeWidth={10} />
        <motion.circle cx={80} cy={80} r={r} fill="none" stroke={color} strokeWidth={10}
          strokeLinecap="round" strokeDasharray={C}
          initial={{ strokeDashoffset: C }} animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
          transform="rotate(-90 80 80)" />
        <text x={80} y={74} textAnchor="middle" fill="#111827" fontSize={30} fontWeight={700} fontFamily="'Montserrat', sans-serif">{Math.round(pct)}</text>
        <text x={80} y={92} textAnchor="middle" fill="rgba(17,24,39,0.42)" fontSize={11} fontFamily="'Poppins', sans-serif">/ 100</text>
      </svg>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 600, color: 'var(--text-2)', marginTop: 4 }}>Readiness</div>
      <div style={{ fontSize: 11, color, marginTop: 3 }}>
        {pct >= 80 ? '🚀 Interview-ready' : pct >= 60 ? '💪 On track' : pct >= 40 ? '📈 Building momentum' : '🌱 Just getting started'}
      </div>
    </div>
  )
}

export default function Analytics() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(14)

  useEffect(() => { load() }, [days])

  const load = async () => {
    setLoading(true)
    try {
      const r = await analyticsAPI.dashboard(days)
      setData(r.data)
    } catch { toast.error('Failed to load analytics') }
    finally { setLoading(false) }
  }

  if (loading) return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Spinner size={28} />
    </div>
  )

  const c = data?.current || {}
  const history = data?.history || []
  const TREND = { improving: { icon: FiTrendingUp, color: 'var(--green)', label: 'Improving' }, stable: { icon: FiMinus, color: 'var(--amber)', label: 'Stable' }, declining: { icon: FiTrendingDown, color: 'var(--red)', label: 'Declining' } }
  const trendCfg = TREND[c.improvement_trend] || TREND.stable
  const TIcon = trendCfg.icon

  const radarData = Object.entries(c.topic_scores || {}).map(([k, v]) => ({ topic: k.replace('_',' ').toUpperCase(), score: Math.round(v), fullMark: 100 }))
  const lineData = history.map(h => ({ date: new Date(h.date).toLocaleDateString('en-IN',{month:'short',day:'numeric'}), Readiness: Math.round(h.readiness_score), Accuracy: Math.round(h.accuracy_rate) }))
  const barData = history.map(h => ({ date: new Date(h.date).toLocaleDateString('en-IN',{month:'short',day:'numeric'}), Solved: h.problems_solved }))

  return (
    <div style={{ minHeight: '100vh', background: 'var(--void)', position: 'relative' }}>
      <Orbs />
      <Navbar />
      <div style={{ position: 'relative', zIndex: 1, maxWidth: 1000, margin: '0 auto', padding: '32px 28px 60px' }} className="page-enter">

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, color: 'var(--text-1)', letterSpacing: '-0.5px', marginBottom: 4 }}>Analytics</h1>
            <p style={{ fontSize: 12, color: 'var(--text-3)' }}>Readiness, accuracy, and topic mastery over time</p>
          </div>
          <div style={{ display: 'flex', gap: 5 }}>
            {[7, 14, 30].map(d => (
              <button key={d} onClick={() => setDays(d)} style={{ fontSize: 11, fontWeight: 600, padding: '5px 12px', borderRadius: 6, border: 'none', cursor: 'pointer', background: days === d ? 'var(--indigo-dim)' : 'var(--raised)', color: days === d ? 'var(--indigo)' : 'var(--text-3)' }}>{d}d</button>
            ))}
          </div>
        </div>

        {/* Top row */}
        <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 16, marginBottom: 20 }}>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14 }}>
            <ReadinessGauge score={c.readiness_score} />
          </motion.div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12 }}>
            {[
              { label: 'Total Solved', value: c.total_problems_solved || 0, icon: FiAward, color: 'var(--green)' },
              { label: 'Accuracy', value: `${Math.round(c.accuracy_rate || 0)}%`, icon: TIcon, color: 'var(--indigo)' },
              { label: 'Trend', value: trendCfg.label, icon: TIcon, color: trendCfg.color },
              { label: 'Streak', value: `${c.streak_days || 0}d 🔥`, icon: TIcon, color: 'var(--amber)' },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} style={{ padding: '18px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12 }}>
                <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.2, color: 'var(--text-3)', marginBottom: 10 }}>{label.toUpperCase()}</div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, color, letterSpacing: -0.5 }}>{value}</div>
              </div>
            ))}

            {/* Weak / strong */}
            <div style={{ padding: '16px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, gridColumn: 'span 2' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.2, color: 'var(--red)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}><FiAlertTriangle size={10} /> NEEDS WORK</div>
                  {(c.weak_areas?.length ? c.weak_areas : ['—']).map(a => <div key={a} style={{ fontSize: 12, color: 'var(--text-2)', padding: '3px 0', borderBottom: '1px solid var(--border)' }}>{a}</div>)}
                </div>
                <div>
                  <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1.2, color: 'var(--green)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}><FiAward size={10} /> STRONG</div>
                  {(c.strong_areas?.length ? c.strong_areas : ['—']).map(a => <div key={a} style={{ fontSize: 12, color: 'var(--text-2)', padding: '3px 0', borderBottom: '1px solid var(--border)' }}>{a}</div>)}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Charts row */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: '24px' }}>
            <Label>TOPIC RADAR</Label>
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(17,24,39,0.10)" />
                <PolarAngleAxis dataKey="topic" tick={{ fill: 'rgba(17,24,39,0.55)', fontSize: 10 }} />
                <Radar name="Score" dataKey="score" stroke="var(--indigo)" fill="var(--indigo)" fillOpacity={0.15} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: '24px' }}>
            <Label>PROBLEMS SOLVED / DAY</Label>
            {barData.some(d => d.Solved > 0) ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={barData} barSize={10}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(17,24,39,0.08)" />
                  <XAxis dataKey="date" tick={{ fill: 'rgba(17,24,39,0.45)', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: 'rgba(17,24,39,0.45)', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<TT />} />
                  <Bar dataKey="Solved" fill="var(--indigo)" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, color: 'var(--text-3)' }}>Start solving to see data</div>
            )}
          </div>
        </div>

        {/* Line chart */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, padding: '24px' }}>
          <Label>READINESS & ACCURACY TREND</Label>
          {lineData.length > 1 ? (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={lineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(17,24,39,0.08)" />
                <XAxis dataKey="date" tick={{ fill: 'rgba(17,24,39,0.45)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0,100]} tick={{ fill: 'rgba(17,24,39,0.45)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip content={<TT />} />
                <Line type="monotone" dataKey="Readiness" stroke="var(--indigo)" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Accuracy" stroke="var(--green)" strokeWidth={2} dot={false} strokeDasharray="5 3" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, color: 'var(--text-3)' }}>More data as you practice</div>
          )}
        </div>
      </div>
    </div>
  )
}
