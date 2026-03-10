import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Chat from './components/Chat'
import LoginPage from './components/Login/LoginPage'
import UserPage from './components/User/UserPage'
import { hasUser } from './utils/user'
import './App.css'

/**
 * 用户路由守卫
 * - 如果已登录，允许访问
 * - 如果未登录，重定向到登录页
 */
function RequireAuth({ children }) {
  return hasUser() ? children : <Navigate to="/" replace />
}

/**
 * 登录页路由守卫
 * - 如果已登录，直接跳转到聊天页
 * - 如果未登录，显示登录页
 */
function LoginGuard({ children }) {
  return hasUser() ? <Navigate to="/chat" replace /> : children
}

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          <Route
            path="/"
            element={
              <LoginGuard>
                <LoginPage />
              </LoginGuard>
            }
          />
          <Route
            path="/chat"
            element={
              <RequireAuth>
                <Chat />
              </RequireAuth>
            }
          />
          <Route
            path="/user"
            element={
              <RequireAuth>
                <UserPage />
              </RequireAuth>
            }
          />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
