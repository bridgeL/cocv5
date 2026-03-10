import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Chat from './components/Chat'
import LoginPage from './components/Login/LoginPage'
import UserPage from './components/User/UserPage'
import RoomList from './components/RoomList'
import RoomChat from './components/RoomChat'
import MainLayout from './components/Layout/MainLayout'
import { hasUser } from './utils/user'
import { WebSocketProvider } from './contexts/WebSocketContext'
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
    <WebSocketProvider>
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
                <MainLayout>
                  <Chat />
                </MainLayout>
              </RequireAuth>
            }
          />
          <Route
            path="/user"
            element={
              <RequireAuth>
                <MainLayout>
                  <UserPage />
                </MainLayout>
              </RequireAuth>
            }
          />
          <Route
            path="/rooms"
            element={
              <RequireAuth>
                <MainLayout>
                  <RoomList />
                </MainLayout>
              </RequireAuth>
            }
          />
          <Route
            path="/rooms/:roomId"
            element={
              <RequireAuth>
                <MainLayout>
                  <RoomChat />
                </MainLayout>
              </RequireAuth>
            }
          />
        </Routes>
      </div>
      </BrowserRouter>
    </WebSocketProvider>
  )
}

export default App
