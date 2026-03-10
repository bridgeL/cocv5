import { useState } from 'react';
import { X, Lock, Users } from 'lucide-react';

export default function JoinRoomModal({ room, onClose, onJoin }) {
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onJoin(password);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3><Lock size={20} /> 加入房间</h3>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="room-info">
          <h4 className="room-name">{room.name}</h4>
          <div className="room-meta">
            <span className="room-id">{room.id}</span>
            <span className="member-count">
              <Users size={14} />
              {room.member_count || 1} 人在线
            </span>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="join-password">
              房间密码 {room.has_password ? '*' : '(可选)'}
            </label>
            <input
              id="join-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={room.has_password ? "请输入房间密码" : "无密码可直接加入"}
              autoFocus
            />
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              取消
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={room.has_password && !password.trim()}
            >
              加入
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
