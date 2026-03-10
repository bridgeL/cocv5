import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUser, updateNickname, generateRandomNickname, clearUser } from '../../utils/user';
import { User, ArrowLeft, LogOut, RefreshCw } from 'lucide-react';
import './UserPage.css';

/**
 * 用户页组件
 * 显示用户信息，支持修改昵称、注销账号等操作
 */
export default function UserPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [nickname, setNickname] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');

  // 加载用户信息
  useEffect(() => {
    const currentUser = getUser();
    if (!currentUser) {
      navigate('/');
      return;
    }
    setUser(currentUser);
    setNickname(currentUser.nickname);
  }, [navigate]);

  // 处理昵称修改
  const handleSaveNickname = () => {
    const trimmed = nickname.trim();
    if (!trimmed || trimmed === user?.nickname) {
      setIsEditing(false);
      setNickname(user?.nickname || '');
      return;
    }

    const updated = updateNickname(trimmed);
    if (updated) {
      setUser(updated);
      setIsEditing(false);
      setSaveStatus('保存成功');
      setTimeout(() => setSaveStatus(''), 2000);
    }
  };

  // 生成随机昵称
  const handleRegenerateNickname = () => {
    const newNickname = generateRandomNickname();
    setNickname(newNickname);
  };

  // 注销账号
  const handleLogout = () => {
    if (window.confirm('⚠️ 警告：注销账号将永久丢失此账号及其所有历史记录！\n\n此操作不可恢复，确定要继续吗？')) {
      clearUser();
      navigate('/');
    }
  };

  // 返回聊天页
  const handleBack = () => {
    navigate('/chat');
  };

  if (!user) {
    return (
      <div className="user-page">
        <div className="user-card loading">
          <div className="loading-text">加载中...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="user-page">
      <div className="user-card">
        {/* 头部 */}
        <div className="user-header">
          <button className="back-button" onClick={handleBack} title="返回聊天">
            <ArrowLeft size={20} />
          </button>
          <h1>个人中心</h1>
          <div className="header-placeholder"></div>
        </div>

        {/* 用户信息卡片 */}
        <div className="user-profile">
          <div className="user-avatar-large">
            <User size={48} />
          </div>
          <div className="user-info">
            <div className="user-id">ID: {user.id}</div>
            <div className="user-created">
              创建于: {new Date(user.createdAt).toLocaleDateString()}
            </div>
          </div>
        </div>

        {/* 昵称编辑区域 */}
        <div className="user-section">
          <label className="section-label">昵称</label>
          {isEditing ? (
            <div className="edit-nickname">
              <input
                type="text"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                maxLength={20}
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveNickname();
                  if (e.key === 'Escape') {
                    setIsEditing(false);
                    setNickname(user.nickname);
                  }
                }}
              />
              <button
                className="icon-button"
                onClick={handleRegenerateNickname}
                title="随机生成"
              >
                <RefreshCw size={18} />
              </button>
              <button className="save-button" onClick={handleSaveNickname}>
                保存
              </button>
            </div>
          ) : (
            <div className="nickname-display">
              <span className="nickname-text">{user.nickname}</span>
              <button className="edit-button" onClick={() => setIsEditing(true)}>
                修改
              </button>
            </div>
          )}
          {saveStatus && <span className="save-status">{saveStatus}</span>}
        </div>

        {/* 操作区域 */}
        <div className="user-actions">
          <button className="action-button logout" onClick={handleLogout}>
            <LogOut size={18} />
            <span>注销账号</span>
          </button>
        </div>

        {/* 底部信息 */}
        <div className="user-footer">
          <p>您的身份信息仅保存在本地浏览器中</p>
          <p>清除浏览器数据将导致身份丢失</p>
        </div>
      </div>
    </div>
  );
}
