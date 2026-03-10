import { useNavigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { MessageSquare, Users, User, Hash } from 'lucide-react';
import { useWebSocket } from '../../contexts/WebSocketContext';
import './MainLayout.css';

/**
 * 主布局组件
 * 提供左侧标签栏，切换右侧内容区域
 */
export default function MainLayout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { send, onMessage, connectionStatus } = useWebSocket();
  const [userRooms, setUserRooms] = useState([]);

  // 获取用户房间列表
  useEffect(() => {
    if (connectionStatus === 'connected') {
      send('list_user_rooms');
    }
  }, [connectionStatus, send]);

  // 监听房间列表更新
  useEffect(() => {
    const unsubscribe = onMessage('user_rooms_list', (payload) => {
      setUserRooms(payload.rooms || []);
    });
    return () => unsubscribe();
  }, [onMessage]);

  // 根据当前路径确定激活的标签
  const getActiveTab = () => {
    const path = location.pathname;
    if (path === '/chat') return 'chat';
    if (path === '/rooms') return 'rooms';
    if (path.startsWith('/rooms/')) return `room-${path.split('/')[2]}`;
    if (path === '/user') return 'user';
    return 'chat';
  };

  const activeTab = getActiveTab();

  // 切换标签
  const handleTabClick = (tab) => {
    switch (tab) {
      case 'chat':
        navigate('/chat');
        break;
      case 'rooms':
        navigate('/rooms');
        break;
      case 'user':
        navigate('/user');
        break;
      default:
        break;
    }
  };

  // 点击房间
  const handleRoomClick = (roomId) => {
    navigate(`/rooms/${roomId}`);
  };

  return (
    <div className="main-layout">
      {/* 左侧标签栏 */}
      <aside className="sidebar">
        <button
          className={`sidebar-tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => handleTabClick('chat')}
          data-title="私聊"
        >
          <MessageSquare size={22} />
        </button>

        <button
          className={`sidebar-tab ${activeTab === 'rooms' ? 'active' : ''}`}
          onClick={() => handleTabClick('rooms')}
          data-title="房间列表"
        >
          <Users size={22} />
        </button>

        {/* 用户房间列表 */}
        {userRooms.length > 0 && (
          <>
            <div className="sidebar-divider" />
            <div className="user-rooms-section">
              {userRooms.map((room) => (
                <button
                  key={room.id}
                  className={`sidebar-tab room-tab ${activeTab === `room-${room.id}` ? 'active' : ''}`}
                  onClick={() => handleRoomClick(room.id)}
                  data-title={room.name}
                >
                  <Hash size={20} />
                </button>
              ))}
            </div>
          </>
        )}

        <div className="sidebar-divider" />

        <div className="sidebar-footer">
          <button
            className={`sidebar-tab ${activeTab === 'user' ? 'active' : ''}`}
            onClick={() => handleTabClick('user')}
            data-title="我的"
          >
            <User size={22} />
          </button>
        </div>
      </aside>

      {/* 主内容区域 */}
      <main className="main-content">
        <div className="page-container">
          {children}
        </div>
      </main>
    </div>
  );
}
