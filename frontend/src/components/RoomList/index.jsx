import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Plus, Lock, MessageSquare, ChevronLeft } from 'lucide-react';
import { getUser } from '../../utils/user';
import { formatTime, ROOM_TABS } from '../../utils/room';
import RoomCard from './RoomCard';
import CreateRoomModal from './CreateRoomModal';
import JoinRoomModal from './JoinRoomModal';
import './RoomList.css';

const WS_URL = 'ws://127.0.0.1:8080/ws';

export default function RoomList() {
  const navigate = useNavigate();
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // 状态
  const [activeTab, setActiveTab] = useState('created');
  const [rooms, setRooms] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState('connecting'); // connecting, connected, disconnected
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [error, setError] = useState('');

  const user = getUser();

  // 建立WebSocket连接
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');
    console.log('[RoomList] 连接WebSocket...');

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[RoomList] WebSocket已连接');
      setConnectionStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (e) {
        console.error('[RoomList] 解析消息失败:', e);
      }
    };

    ws.onclose = () => {
      console.log('[RoomList] WebSocket已断开');
      setConnectionStatus('disconnected');
      wsRef.current = null;

      // 自动重连
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('[RoomList] WebSocket错误:', error);
      setConnectionStatus('disconnected');
    };
  }, []);

  // 处理WebSocket消息
  const handleWebSocketMessage = (data) => {
    const { type, ...payload } = data;

    switch (type) {
      case 'session_init':
        // 发送用户认证
        if (user && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'user_auth',
            user_id: user.id,
            nickname: user.nickname
          }));
        }
        break;

      case 'user_auth_success':
        // 认证成功，加载房间列表
        loadRooms();
        break;

      case 'rooms_list':
        setRooms(payload.rooms || []);
        setIsLoading(false);
        break;

      case 'room_created':
        // 创建成功，跳转到房间
        navigate(`/rooms/${payload.room.id}`);
        break;

      case 'room_joined':
        // 加入成功，跳转到房间
        navigate(`/rooms/${payload.room.id}`);
        break;

      case 'room_error':
        setError(payload.error);
        setTimeout(() => setError(''), 5000);
        break;

      default:
        break;
    }
  };

  // 加载房间列表
  const loadRooms = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      setIsLoading(true);
      wsRef.current.send(JSON.stringify({
        type: 'list_rooms',
        tab: activeTab
      }));
    }
  };

  // 初始化WebSocket连接
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

  // Tab切换时重新加载
  useEffect(() => {
    if (connectionStatus === 'connected') {
      loadRooms();
    }
  }, [activeTab, connectionStatus]);

  // 创建房间
  const handleCreateRoom = (name, password) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'create_room',
        name,
        password: password || undefined
      }));
      setShowCreateModal(false);
    }
  };

  // 点击房间卡片
  const handleRoomClick = (room) => {
    if (room.has_password) {
      // 有密码，显示密码输入弹窗
      setSelectedRoom(room);
      setShowJoinModal(true);
    } else {
      // 无密码，直接加入
      joinRoom(room.id);
    }
  };

  // 加入房间
  const joinRoom = (roomId, password) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'join_room',
        room_id: roomId,
        password: password || undefined
      }));
      setShowJoinModal(false);
      setSelectedRoom(null);
    }
  };

  // 返回私聊
  const goToChat = () => {
    navigate('/chat');
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
    <div className="room-list-page">
      {/* 头部 */}
      <header className="room-list-header">
        <div className="header-left">
          <button className="back-btn" onClick={goToChat} title="返回私聊">
            <ChevronLeft size={20} />
            <span>私聊</span>
          </button>
          <h1>房间列表</h1>
          {getStatusIndicator()}
        </div>
        <div className="header-right">
          <span className="user-nickname">{user?.nickname}</span>
          <button
            className="create-room-btn"
            onClick={() => setShowCreateModal(true)}
            disabled={connectionStatus !== 'connected'}
          >
            <Plus size={18} />
            <span>创建房间</span>
          </button>
        </div>
      </header>

      {/* 错误提示 */}
      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      {/* Tab导航 */}
      <div className="tab-nav">
        {Object.values(ROOM_TABS).map(tab => (
          <button
            key={tab.key}
            className={`tab-btn ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
            title={tab.description}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 房间列表 */}
      <div className="room-list-content">
        {isLoading ? (
          <div className="loading-state">
            <div className="loading-spinner" />
            <p>加载中...</p>
          </div>
        ) : rooms.length === 0 ? (
          <div className="empty-state">
            <MessageSquare size={48} className="empty-icon" />
            <h3>暂无房间</h3>
            <p>
              {activeTab === 'created'
                ? '你还没有创建过房间，点击右上角创建吧！'
                : activeTab === 'joined'
                ? '你还没有加入任何房间，去房间大厅看看吧！'
                : '房间大厅空空如也，快来创建第一个房间吧！'}
            </p>
          </div>
        ) : (
          <div className="room-grid">
            {rooms.map(room => (
              <RoomCard
                key={room.id}
                room={room}
                onClick={() => handleRoomClick(room)}
              />
            ))}
          </div>
        )}
      </div>

      {/* 创建房间弹窗 */}
      {showCreateModal && (
        <CreateRoomModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateRoom}
        />
      )}

      {/* 加入房间弹窗 */}
      {showJoinModal && selectedRoom && (
        <JoinRoomModal
          room={selectedRoom}
          onClose={() => {
            setShowJoinModal(false);
            setSelectedRoom(null);
          }}
          onJoin={(password) => joinRoom(selectedRoom.id, password)}
        />
      )}
    </div>
  );
}
