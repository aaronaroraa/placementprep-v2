// src/App.jsx
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AnimatePresence } from 'framer-motion'
import { ProtectedRoute } from './components'
import Landing from './pages/Landing'
import Auth, { AuthCallback } from './pages/Auth'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Coding from './pages/Coding'
import { MockInterview, Theory } from './pages/MockInterview'
import Analytics from './pages/Analytics'
import Plan from './pages/Plan'

function Routes_() {
  const loc = useLocation()
  return (
    <AnimatePresence mode="wait">
      <Routes location={loc} key={loc.pathname}>
        <Route path="/" element={<Landing />} />
        <Route path="/auth" element={<Auth />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/plan" element={<ProtectedRoute><Plan /></ProtectedRoute>} />
        <Route path="/coding" element={<ProtectedRoute><Coding /></ProtectedRoute>} />
        <Route path="/mock" element={<ProtectedRoute><MockInterview /></ProtectedRoute>} />
        <Route path="/theory" element={<ProtectedRoute><Theory /></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" toastOptions={{
        style: { background: 'var(--raised)', color: '#fff', border: '1px solid var(--border)', borderRadius: '10px', fontSize: '13px', fontFamily: 'var(--font-body)' },
        success: { iconTheme: { primary: 'var(--green)', secondary: '#06060d' } },
        error: { iconTheme: { primary: 'var(--red)', secondary: '#fff' } },
      }} />
      <Routes_ />
    </BrowserRouter>
  )
}
