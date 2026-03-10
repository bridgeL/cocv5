import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ChevronLeft, Users, Crown, Send } from 'lucide-react';
import { getUser } from '../../utils/user';
import { useWebSocket } from '../../contexts/WebSocketContext';
import './RoomChat.css';

export default function RoomChat() {
  const navigate = useNavigate();
  const { roomId } = useParams();
  const { connectionStatus, send, onMessage } = useWebSocket();
  const messagesEndRef = useRef(null);

  // 状态
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [roomInfo, setRoomInfo] = useState(null);
  const [members, setMembers] = useState([]);
  const [error, setError] = useState('');
  const [isJoined, setIsJoined] = useState(false);

  const user = getUser();

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // 加入房间
  const joinRoom = useCallback(() => {
    if (roomId) {
      send('join_room', { room_id: roomId });
    }
  }, [send, roomId]);

  // 加载房间历史
  const loadRoomHistory = useCallback(() => {
    if (roomId) {
      send('load_room_history', { room_id: roomId, limit: 20 });
    }
  }, [send, roomId]);

  // 注册WebSocket消息监听
  useEffect(() => {
    const unsubscribes = [];

    // 监听加入房间成功
    unsubscribes.push(onMessage('room_joined', (payload) => {
      setRoomInfo(payload.room);
      setMembers(payload.members || []);
      setIsJoined(true);
      loadRoomHistory();
    }));

    // 监听房间消息
    unsubscribes.push(onMessage('room_message', (payload) => {
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
    }));

    // 监听KP思考/回答开始
    unsubscribes.push(onMessage('think_start', () => {
      setMessages(prev => [...prev, {
        id: `kp-${Date.now()}`,
        type: 'think',
        nickname: 'KP',
        content: '',
        isKP: true,
        isStreaming: true
      }]);
    }));

    unsubscribes.push(onMessage('report_start', () => {
      setMessages(prev => [...prev, {
        id: `kp-${Date.now()}`,
        type: 'report',
        nickname: 'KP',
        content: '',
        isKP: true,
        isStreaming: true
      }]);
    }));

    // 监听KP流式输出
    unsubscribes.push(onMessage('think_chunk', (payload) => {
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.isKP && lastMsg.isStreaming && lastMsg.type === 'think') {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1] = {
            ...lastMsg,
            content: lastMsg.content + (payload.content || '')
          };
          return newMessages;
        }
        return prev;
      });
    }));

    unsubscribes.push(onMessage('report_chunk', (payload) => {
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.isKP && lastMsg.isStreaming && lastMsg.type === 'report') {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1] = {
            ...lastMsg,
            content: lastMsg.content + (payload.content || '')
          };
          return newMessages;
        }
        return prev;
      });
    }));

    // 监听KP结束
    unsubscribes.push(onMessage('think_end', () => {
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.isKP && lastMsg.isStreaming) {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1] = { ...lastMsg, isStreaming: false };
          return newMessages;
        }
        return prev;
      });
    }));

    unsubscribes.push(onMessage('report_end', () => {
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.isKP && lastMsg.isStreaming) {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1] = { ...lastMsg, isStreaming: false };
          return newMessages;
        }
        return prev;
      });
    }));

    // 监听成员加入
    unsubscribes.push(onMessage('member_joined', (payload) => {
      if (payload.user_id !== user?.id) {
        setMembers(prev => [...prev, {
          user_id: payload.user_id,
          nickname: payload.nickname,
          is_owner: false
        }]);
      }
    }));

    // 监听成员离开
    unsubscribes.push(onMessage('member_left', (payload) => {
      setMembers(prev => prev.filter(m => m.user_id !== payload.user_id));
    }));

    // 监听房间关闭
    unsubscribes.push(onMessage('room_closed', () => {
      setError('房间已关闭');
      setTimeout(() => navigate('/rooms'), 2000);
    }));

    // 监听历史消息
    unsubscribes.push(onMessage('room_history', (payload) => {
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
    }));

    // 监听错误
    unsubscribes.push(onMessage('room_error', (payload) => {
      setError(payload.error);
      setTimeout(() => setError(''), 5000);
      if (payload.error?.includes('不在该房间')) {
        setTimeout(() => navigate('/rooms'), 2000);
      }
    }));

    return () => {
      unsubscribes.forEach(unsubscribe => unsubscribe());
    };
  }, [onMessage, user?.id, members, navigate, scrollToBottom, loadRoomHistory]);

  // 连接成功后加入房间
  useEffect(() => {
    if (connectionStatus === 'connected' && roomId) {
      joinRoom();
    }
  }, [connectionStatus, roomId, joinRoom]);

  // 消息更新时滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 离开房间
  const leaveRoom = () => {
    send('leave_room', { room_id: roomId });
    navigate('/rooms');
  };

  // 发送消息
  const sendMessage = () => {
    const text = input.trim();
    if (!text) return;

    send('room_chat', {
      room_id: roomId,
      content: text
    });

    setInput('');
  };

  // 处理键盘事件
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

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
            成员 ({members.length + 1})
          </h3>
          <ul className="members-list">
            {/* KP 固定显示 */}
            <li className="member-item is-kp">
              <span className="member-name">
                <Crown size={12} className="kp-icon" />
                KP
              </span>
              <span className="kp-badge">AI</span>
            </li>
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
