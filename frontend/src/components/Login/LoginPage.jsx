import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createUser, getUser, generateRandomNickname } from '../../utils/user';
import './LoginPage.css';

/**
 * 登录页组件
 * 提供免登录入口：自动生成用户ID，用户只需设置昵称即可开始
 */
export default function LoginPage() {
  const navigate = useNavigate();
  const [nickname, setNickname] = useState('');
  const [isReturning, setIsReturning] = useState(false);
  const [existingUser, setExistingUser] = useState(null);

  // 检查是否已有用户
  useEffect(() => {
    const user = getUser();
    if (user) {
      setIsReturning(true);
      setExistingUser(user);
    } else {
      // 新用户：预填充随机昵称
      setNickname(generateRandomNickname());
    }
  }, []);

  // 处理表单提交
  const handleSubmit = (e) => {
    e.preventDefault();

    const trimmedNickname = nickname.trim();
    if (!trimmedNickname) return;

    if (isReturning && existingUser) {
      // 老用户：更新昵称（如果改变了）
      existingUser.nickname = trimmedNickname;
      localStorage.setItem('coc_user', JSON.stringify(existingUser));
    } else {
      // 新用户：创建用户
      createUser(trimmedNickname);
    }

    // 跳转到聊天页
    navigate('/chat');
  };

  // 生成新昵称
  const handleRegenerateNickname = () => {
    setNickname(generateRandomNickname());
  };

  // 继续作为现有用户
  const handleContinue = () => {
    navigate('/chat');
  };

  // 切换账号（清除当前用户，创建新账号）
  const handleSwitchAccount = () => {
    localStorage.removeItem('coc_user');
    setIsReturning(false);
    setExistingUser(null);
    setNickname(generateRandomNickname());
  };

  // 如果是老用户，显示欢迎回来界面
  if (isReturning && existingUser) {
    return (
      <div className="login-page">
        <div className="login-card welcome-back">
          <div className="login-header">
            <div className="user-avatar">
              {existingUser.nickname.charAt(0)}
            </div>
            <h1>欢迎回来，<span className="user-name">{existingUser.nickname}</span></h1>
            <p className="login-subtitle">准备好继续探索了吗？</p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="input-group">
              <label htmlFor="nickname">修改昵称（可选）</label>
              <input
                id="nickname"
                type="text"
                value={nickname || existingUser.nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="输入新昵称"
                maxLength={20}
                autoComplete="off"
              />
            </div>

            <button type="submit" className="login-button">
              开始对话
            </button>
          </form>

          <div className="login-footer">
            <button className="secondary-button" onClick={handleSwitchAccount}>
              使用新身份
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 新用户登录界面
  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <h1>欢迎来到 CoC V5</h1>
          <p className="login-subtitle">无需注册，输入昵称即可开始对话</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="nickname">昵称</label>
            <input
              id="nickname"
              type="text"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              placeholder="输入你的昵称"
              maxLength={20}
              autoFocus
              autoComplete="off"
            />
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={handleRegenerateNickname}
            title="生成随机昵称"
          >
            🎲 随机生成昵称
          </button>

          <button
            type="submit"
            className="login-button"
            disabled={!nickname.trim()}
          >
            开始对话
          </button>
        </form>

        <div className="login-footer">
          <p>您的身份将自动保存在本地浏览器中<br />清除浏览器数据将导致身份丢失</p>
        </div>
      </div>
    </div>
  );
}
