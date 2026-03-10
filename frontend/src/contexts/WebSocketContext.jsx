import { createContext, useContext, useRef, useState, useEffect, useCallback } from 'react';
import { getUser } from '../utils/user';

const WebSocketContext = createContext(null);

const WS_URL = 'ws://127.0.0.1:8080/ws';

export function WebSocketProvider({ children }) {
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const listenersRef = useRef(new Map()); // type -> Set(callback)
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // 注册消息监听器
  const onMessage = useCallback((type, callback) => {
    if (!listenersRef.current.has(type)) {
      listenersRef.current.set(type, new Set());
    }
    listenersRef.current.get(type).add(callback);

    // 返回取消订阅函数
    return () => {
      listenersRef.current.get(type)?.delete(callback);
    };
  }, []);

  // 发送消息
  const send = useCallback((type, data = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, ...data }));
      return true;
    }
    console.warn('[WebSocket] 连接未就绪，无法发送:', type);
    return false;
  }, []);

  // 分发消息给监听器
  const dispatchMessage = useCallback((data) => {
    const { type, ...payload } = data;
    const listeners = listenersRef.current.get(type);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(payload);
        } catch (e) {
          console.error('[WebSocket] 监听器执行失败:', e);
        }
      });
    }
  }, []);

  // 建立连接
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionStatus('connecting');
    console.log('[WebSocket] 连接中...');

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      // 检查是否仍是当前 WebSocket 实例（避免 StrictMode 旧实例干扰）
      if (wsRef.current !== ws) return;
      console.log('[WebSocket] 已连接');
      setConnectionStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('[WebSocket] 收到:', data.type, data);

        // 处理认证相关消息
        if (data.type === 'session_init') {
          const user = getUser();
          if (user) {
            send('user_auth', { user_id: user.id, nickname: user.nickname });
          }
        } else if (data.type === 'user_auth_success') {
          setIsAuthenticated(true);
        } else if (data.type === 'user_auth_failed') {
          setIsAuthenticated(false);
        }

        // 分发给所有监听器
        dispatchMessage(data);
      } catch (e) {
        console.error('[WebSocket] 消息解析失败:', e);
      }
    };

    ws.onclose = () => {
      // 检查是否仍是当前 WebSocket 实例（避免 StrictMode 旧实例干扰）
      if (wsRef.current !== ws) return;
      console.log('[WebSocket] 已断开');
      setConnectionStatus('disconnected');
      setIsAuthenticated(false);
      wsRef.current = null;

      // 自动重连
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 20000);
    };

    ws.onerror = (error) => {
      // 检查是否仍是当前 WebSocket 实例（避免 StrictMode 旧实例干扰）
      if (wsRef.current !== ws) return;
      console.error('[WebSocket] 错误:', error);
      setConnectionStatus('disconnected');
    };
  }, [send, dispatchMessage]);

  // 断开连接
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  // 初始化连接
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  const value = {
    connectionStatus,
    isAuthenticated,
    send,
    onMessage,
    connect,
    disconnect
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

// 自定义Hook
export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
}
