import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Plus, Lock, MessageSquare, ChevronLeft } from 'lucide-react';
import { getUser } from '../../utils/user';
import { useWebSocket } from '../../contexts/WebSocketContext';
import { formatTime, ROOM_TABS } from '../../utils/room';
import RoomCard from './RoomCard';
import CreateRoomModal from './CreateRoomModal';
import JoinRoomModal from './JoinRoomModal';
import './RoomList.css';

export default function RoomList() {
  const navigate = useNavigate();
  const { connectionStatus, send, onMessage } = useWebSocket();

  // 状态
  const [activeTab, setActiveTab] = useState('created');
  const [rooms, setRooms] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [error, setError] = useState('');

  const user = getUser();

  // 注册WebSocket消息监听
  useEffect(() => {
    const unsubscribes = [];

    // 监听房间列表
    unsubscribes.push(onMessage('rooms_list', (payload) => {
      setRooms(payload.rooms || []);
      setIsLoading(false);
    }));

    // 监听创建房间成功
    unsubscribes.push(onMessage('room_created', (payload) => {
      navigate(`/rooms/${payload.room.id}`);
    }));

    // 监听加入房间成功
    unsubscribes.push(onMessage('room_joined', (payload) => {
      navigate(`/rooms/${payload.room.id}`);
    }));

    // 监听错误
    unsubscribes.push(onMessage('room_error', (payload) => {
      setError(payload.error);
      setTimeout(() => setError(''), 5000);
    }));

    return () => {
      unsubscribes.forEach(unsubscribe => unsubscribe());
    };
  }, [onMessage, navigate]);

  // 加载房间列表
  const loadRooms = useCallback(() => {
    setIsLoading(true);
    send('list_rooms', { tab: activeTab });
  }, [send, activeTab]);

  // Tab切换时重新加载
  useEffect(() => {
    if (connectionStatus === 'connected') {
      loadRooms();
    }
  }, [activeTab, connectionStatus, loadRooms]);

  // 创建房间
  const handleCreateRoom = (name, password) => {
    send('create_room', {
      name,
      password: password || undefined
    });
    setShowCreateModal(false);
  };

  // 点击房间卡片
  const handleRoomClick = (room) => {
    if (room.has_password) {
      setSelectedRoom(room);
      setShowJoinModal(true);
    } else {
      joinRoom(room.id);
    }
  };

  // 加入房间
  const joinRoom = (roomId, password) => {
    send('join_room', {
      room_id: roomId,
      password: password || undefined
    });
    setShowJoinModal(false);
    setSelectedRoom(null);
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
