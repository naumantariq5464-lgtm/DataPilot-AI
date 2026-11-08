import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { onAuthStateChanged } from 'firebase/auth'
import { auth } from './services/firebase'
import { useAuthStore } from './store/authStore'

// Layout
import Layout from './components/layout/Layout'

// Auth pages
import Login    from './pages/auth/Login'
import Register from './pages/auth/Register'

// App pages
import Overview         from './pages/Overview'
import NewAnalysis      from './pages/NewAnalysis'
import MyDatasets       from './pages/MyDatasets'
import AnalysisHistory  from './pages/AnalysisHistory'
import Settings         from './pages/Settings'

// Loading screen while Firebase resolves auth state
import LoadingSpinner from './components/common/LoadingSpinner'


// ── Auth guard — redirects to /login if not authenticated ────────────────────
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuthStore()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <LoadingSpinner size="lg" text="Loading..." />
      </div>
    )
  }

  return user ? <>{children}</> : <Navigate to="/login" replace />
}

// ── Redirect authenticated users away from auth pages ────────────────────────
function RedirectIfAuthed({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuthStore()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return user ? <Navigate to="/" replace /> : <>{children}</>
}


// ── Root App component ────────────────────────────────────────────────────────
export default function App() {
  const { setUser, setLoading } = useAuthStore()

  // Listen to Firebase auth state once at the top level
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      if (firebaseUser) {
        setUser({
          uid:   firebaseUser.uid,
          email: firebaseUser.email,
          name:  firebaseUser.displayName,
        })
      } else {
        setUser(null)
      }
      setLoading(false)
    })
    return unsubscribe
  }, [setUser, setLoading])

  return (
    <BrowserRouter>
      <Routes>

        {/* ── Public auth routes ── */}
        <Route path="/login" element={
          <RedirectIfAuthed><Login /></RedirectIfAuthed>
        } />
        <Route path="/register" element={
          <RedirectIfAuthed><Register /></RedirectIfAuthed>
        } />

        {/* ── Protected app routes (sidebar layout) ── */}
        <Route path="/" element={
          <RequireAuth><Layout /></RequireAuth>
        }>
          <Route index          element={<Overview />} />
          <Route path="analysis/new" element={<NewAnalysis />} />
          <Route path="datasets"     element={<MyDatasets />} />
          <Route path="history"      element={<AnalysisHistory />} />
          <Route path="settings"     element={<Settings />} />
        </Route>

        {/* ── Catch-all ── */}
        <Route path="*" element={<Navigate to="/" replace />} />

      </Routes>
    </BrowserRouter>
  )
}
