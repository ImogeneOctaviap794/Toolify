import { useEffect } from 'react'
import { useAuthStore } from './lib/store'
import LoginPage from './pages/LoginPage'
import ConfigPage from './pages/ConfigPage'

function App() {
  const { isAuthenticated, checkAuth } = useAuthStore()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return <ConfigPage />
}

export default App

