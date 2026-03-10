import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Plus, Lock, MessageSquare, LogIn } from 'lucide-react';
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
  const [activeTab, setActiveTab] = useState('my');
  const [rooms, setRooms] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [myRoomsLoaded, setMyRoomsLoaded] = useState({ created: false, joined: false });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [error, setError] = useState('');

  // 加入房间表单状态
  const [joinRoomId, setJoinRoomId] = useState('');
  const [joinPassword, setJoinPassword] = useState('');

  const user = getUser();

  // 注册WebSocket消息监听
  useEffect(() => {
    const unsubscribes = [];

    // 监听房间列表
    unsubscribes.push(onMessage('rooms_list', (payload) => {
      const tab = payload.tab;
      if (activeTab === 'my' && tab) {
        // 合并 created 和 joined 的结果
        setRooms(prev => {
          const existingIds = new Set(prev.map(r => r.id));
          const newRooms = (payload.rooms || []).filter(r => !existingIds.has(r.id));
          return [...prev, ...newRooms];
        });
        setMyRoomsLoaded(prev => ({ ...prev, [tab]: true }));
        // 两个都加载完成才结束 loading
        if (tab === 'joined' || myRoomsLoaded.created) {
          setIsLoading(false);
        }
      } else {
        setRooms(payload.rooms || []);
        setIsLoading(false);
      }
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
    // 加入房间标签不需要加载列表
    if (activeTab === 'join') {
      setIsLoading(false);
      setRooms([]);
      return;
    }
    setIsLoading(true);
    if (activeTab === 'my') {
      setRooms([]);
      setMyRoomsLoaded({ created: false, joined: false });
      send('list_rooms', { tab: 'created' });
      send('list_rooms', { tab: 'joined' });
    } else {
      send('list_rooms', { tab: activeTab });
    }
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
    // 我的房间：已加入，直接进入（后端会自动识别已加入的用户）
    if (activeTab === 'my') {
      navigate(`/rooms/${room.id}`);
      return;
    }
    // 房间大厅：未加入，有密码的需要输入
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

  // 通过ID加入房间
  const handleJoinById = (e) => {
    e.preventDefault();
    if (!joinRoomId.trim()) return;
    send('join_room', {
      room_id: joinRoomId.trim(),
      password: joinPassword || undefined
    });
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
        {activeTab === 'join' ? (
          // 加入房间表单
          <div className="join-room-form-container">
            <div className="join-room-form">
              <LogIn size={48} className="join-room-icon" />
              <h3>加入房间</h3>
              <p>输入房间ID即可加入房间</p>
              <form onSubmit={handleJoinById}>
                <div className="form-group">
                  <label htmlFor="join-room-id">房间ID</label>
                  <input
                    id="join-room-id"
                    type="text"
                    value={joinRoomId}
                    onChange={(e) => setJoinRoomId(e.target.value)}
                    placeholder="例如: rm_abc123xyz"
                    disabled={connectionStatus !== 'connected'}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="join-room-password">房间密码（可选）</label>
                  <input
                    id="join-room-password"
                    type="password"
                    value={joinPassword}
                    onChange={(e) => setJoinPassword(e.target.value)}
                    placeholder="如果房间有密码请填写"
                    disabled={connectionStatus !== 'connected'}
                  />
                </div>
                <button
                  type="submit"
                  className="btn-primary join-btn"
                  disabled={!joinRoomId.trim() || connectionStatus !== 'connected'}
                >
                  加入房间
                </button>
              </form>
            </div>
          </div>
        ) : isLoading ? (
          <div className="loading-state">
            <div className="loading-spinner" />
            <p>加载中...</p>
          </div>
        ) : rooms.length === 0 ? (
          <div className="empty-state">
            <MessageSquare size={48} className="empty-icon" />
            <h3>暂无房间</h3>
            <p>
              {activeTab === 'my'
                ? '你还没有创建或加入任何房间，去房间大厅看看吧！'
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
