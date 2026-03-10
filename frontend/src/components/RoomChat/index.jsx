import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ChevronLeft, Users, Crown, Send, LogOut } from 'lucide-react';
import { getUser } from '../../utils/user';
import './RoomChat.css';

const WS_URL = 'ws://127.0.0.1:8080/ws';

export default function RoomChat() {
  const navigate = useNavigate();
  const { roomId } = useParams();
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const messagesEndRef = useRef(null);

  // 状态
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [roomInfo, setRoomInfo] = useState(null);
  const [members, setMembers] = useState([]);
  const [error, setError] = useState('');
  const [isJoined, setIsJoined] = useState(false);

  const user = getUser();

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // 建立WebSocket连接
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionStatus('connecting');
    console.log('[RoomChat] 连接WebSocket...');

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[RoomChat] WebSocket已连接');
      setConnectionStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (e) {
        console.error('[RoomChat] 解析消息失败:', e);
      }
    };

    ws.onclose = () => {
      console.log('[RoomChat] WebSocket已断开');
      setConnectionStatus('disconnected');
      wsRef.current = null;
      setIsJoined(false);

      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('[RoomChat] WebSocket错误:', error);
      setConnectionStatus('disconnected');
    };
  }, []);

  // 处理WebSocket消息
  const handleWebSocketMessage = (data) => {
    const { type, ...payload } = data;

    switch (type) {
      case 'session_init':
        if (user && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'user_auth',
            user_id: user.id,
            nickname: user.nickname
          }));
        }
        break;

      case 'user_auth_success':
        // 认证成功后加入房间
        joinRoom();
        break;

      case 'room_joined':
        setRoomInfo(payload.room);
        setMembers(payload.members || []);
        setIsJoined(true);
        // 加载历史消息
        loadRoomHistory();
        break;

      case 'room_message':
        // 房间消息
        setMessages(prev => [...prev, {
          id: Date.now(),
          type: 'user',
          userId: payload.user_id,
          nickname: payload.nickname,
          content: payload.content,
          isKP: payload.is_kp,
          timestamp: payload.timestamp
        }]);
        setTimeout(scrollToBottom, 100);
        break;

      case 'think_start':
      case 'report_start':
        // KP开始思考/回答
        setMessages(prev => [...prev, {
          id: `kp-${Date.now()}`,
          type: type === 'think_start' ? 'think' : 'report',
          nickname: 'KP',
          content: '',
          isKP: true,
          isStreaming: true
        }]);
        break;

      case 'think_chunk':
      case 'report_chunk':
        // KP流式输出
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.isKP && lastMsg.isStreaming) {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = {
              ...lastMsg,
              content: lastMsg.content + (payload.content || '')
            };
            return newMessages;
          }
          return prev;
        });
        break;

      case 'think_end':
      case 'report_end':
        // KP结束思考/回答
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.isKP && lastMsg.isStreaming) {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = {
              ...lastMsg,
              isStreaming: false
            };
            return newMessages;
          }
          return prev;
        });
        break;

      case 'member_joined':
        // 新成员加入
        if (payload.user_id !== user?.id) {
          setMembers(prev => [...prev, {
            user_id: payload.user_id,
            nickname: payload.nickname,
            is_owner: false
          }]);
        }
        break;

      case 'member_left':
        // 成员离开
        setMembers(prev => prev.filter(m => m.user_id !== payload.user_id));
        break;

      case 'room_closed':
        // 房间关闭
        setError('房间已关闭');
        setTimeout(() => navigate('/rooms'), 2000);
        break;

      case 'room_history':
        // 历史消息
        if (payload.messages) {
          const formatted = payload.messages.map(msg => ({
            id: msg.id,
            type: msg.role === 'assistant' ? 'report' : 'user',
            userId: msg.user_id,
            nickname: msg.role === 'assistant' ? 'KP' : members.find(m => m.user_id === msg.user_id)?.nickname || '未知',
            content: msg.content,
            isKP: msg.role === 'assistant',
            isStreaming: false
          }));
          setMessages(formatted);
        }
        break;

      case 'room_error':
        setError(payload.error);
        setTimeout(() => setError(''), 5000);
        if (payload.error?.includes('不在该房间')) {
          setTimeout(() => navigate('/rooms'), 2000);
        }
        break;

      default:
        break;
    }
  };

  // 加入房间
  const joinRoom = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN && roomId) {
      wsRef.current.send(JSON.stringify({
        type: 'join_room',
        room_id: roomId
      }));
    }
  };

  // 加载房间历史
  const loadRoomHistory = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN && roomId) {
      wsRef.current.send(JSON.stringify({
        type: 'load_room_history',
        room_id: roomId,
        limit: 20
      }));
    }
  };

  // 离开房间
  const leaveRoom = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN && roomId) {
      wsRef.current.send(JSON.stringify({
        type: 'leave_room',
        room_id: roomId
      }));
    }
    navigate('/rooms');
  };

  // 发送消息
  const sendMessage = () => {
    const text = input.trim();
    if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    wsRef.current.send(JSON.stringify({
      type: 'room_chat',
      room_id: roomId,
      content: text
    }));

    setInput('');
  };

  // 处理键盘事件
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // 初始化WebSocket
  useEffect(() => {
    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  // 消息更新时滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 状态指示器
  const getStatusIndicator = () => {
    switch (connectionStatus) {
      case 'connected':
        return <span className="status-indicator connected" title="已连接" />;
      case 'connecting':
        return <span className="status-indicator connecting" title="连接中..." />;
      default:
        return <span className="status-indicator disconnected" title="已断开" />;
    }
  };

  return (
    <div className="room-chat-page">
      {/* 头部 */}
      <header className="room-chat-header">
        <div className="header-left">
          <button className="back-btn" onClick={leaveRoom} title="离开房间">
            <ChevronLeft size={20} />
          </button>
          <div className="room-info">
            <h1>{roomInfo?.name || '房间'}</h1>
            {getStatusIndicator()}
          </div>
        </div>
        <div className="header-right">
          <div className="member-count">
            <Users size={16} />
            <span>{members.length}</span>
          </div>
        </div>
      </header>

      {/* 错误提示 */}
      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      {/* 主体内容 */}
      <div className="room-chat-body">
        {/* 消息列表 */}
        <div className="messages-container">
          {!isJoined ? (
            <div className="loading-state">
              <div className="loading-spinner" />
              <p>正在加入房间...</p>
            </div>
          ) : messages.length === 0 ? (
            <div className="empty-state">
              <p>还没有消息，发送第一条消息吧！</p>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`message ${msg.isKP ? 'kp-message' : 'user-message'} ${msg.isStreaming ? 'streaming' : ''}`}
                >
                  <div className="message-header">
                    <span className="nickname">
                      {msg.isKP && <Crown size={12} className="kp-icon" />}
                      {msg.nickname}
                    </span>
                    {msg.isStreaming && <span className="typing-indicator">...</span>}
                  </div>
                  <div className="message-content">{msg.content}</div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* 成员列表侧边栏 */}
        <aside className="members-sidebar">
          <h3>
            <Users size={16} />
            成员 ({members.length})
          </h3>
          <ul className="members-list">
            {members.map((member) => (
              <li
                key={member.user_id}
                className={`member-item ${member.user_id === user?.id ? 'is-me' : ''} ${member.is_owner ? 'is-owner' : ''}`}
              >
                <span className="member-name">
                  {member.is_owner && <Crown size={12} className="owner-icon" />}
                  {member.nickname}
                </span>
                {member.user_id === user?.id && <span className="me-badge">我</span>}
              </li>
            ))}
          </ul>
        </aside>
      </div>

      {/* 输入区域 */}
      <footer className="room-chat-footer">
        <div className="input-wrapper">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isJoined ? "输入消息..." : "加入房间后才能发言"}
            disabled={!isJoined || connectionStatus !== 'connected'}
            autoComplete="off"
          />
          <button
            onClick={sendMessage}
            disabled={!isJoined || !input.trim() || connectionStatus !== 'connected'}
          >
            <Send size={18} />
          </button>
        </div>
      </footer>
    </div>
  );
}
