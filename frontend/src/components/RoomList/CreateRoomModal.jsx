import { useState } from 'react';
import { X, Lock, Hash } from 'lucide-react';

export default function CreateRoomModal({ onClose, onCreate }) {
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [hasPassword, setHasPassword] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    onCreate(name.trim(), hasPassword ? password : null);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3><Hash size={20} /> 创建房间</h3>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="room-name">房间名称 *</label>
            <input
              id="room-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="给你的房间起个名字"
              maxLength={50}
              autoFocus
            />
            <span className="char-count">{name.length}/50</span>
          </div>

          <div className="form-group checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={hasPassword}
                onChange={(e) => {
                  setHasPassword(e.target.checked);
                  if (!e.target.checked) setPassword('');
                }}
              />
              <Lock size={16} />
              设置房间密码
            </label>
          </div>

          {hasPassword && (
            <div className="form-group">
              <label htmlFor="room-password">房间密码</label>
              <input
                id="room-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="设置加入密码（可选）"
                maxLength={20}
              />
            </div>
          )}

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              取消
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={!name.trim()}
            >
              创建
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
