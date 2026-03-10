import { Users, Lock, Crown } from 'lucide-react';
import { formatTime } from '../../utils/room';

export default function RoomCard({ room, onClick }) {
  return (
    <div className="room-card" onClick={onClick}>
      <div className="room-card-header">
        <h3 className="room-name" title={room.name}>
          {room.name}
        </h3>
        {room.has_password && (
          <Lock size={16} className="password-icon" title="需要密码" />
        )}
      </div>

      <div className="room-card-info">
        <div className="room-info-item">
          <Users size={14} />
          <span>{room.member_count || 1} 人</span>
        </div>
        <div className="room-info-item time">
          {formatTime(room.created_at)}
        </div>
      </div>

      <div className="room-card-footer">
        <span className="room-id">{room.id}</span>
        {room.is_owner && (
          <span className="owner-badge" title="你是房主">
            <Crown size={12} />
            房主
          </span>
        )}
      </div>
    </div>
  );
}
