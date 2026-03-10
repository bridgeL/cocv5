import { useNavigate, useLocation } from 'react-router-dom';
import { MessageSquare, Users, User } from 'lucide-react';
import './MainLayout.css';

/**
 * 主布局组件
 * 提供左侧标签栏，切换右侧内容区域
 */
export default function MainLayout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();

  // 根据当前路径确定激活的标签
  const getActiveTab = () => {
    const path = location.pathname;
    if (path === '/chat') return 'chat';
    if (path === '/rooms' || path.startsWith('/rooms/')) return 'rooms';
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
          data-title="房间"
        >
          <Users size={22} />
        </button>

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
