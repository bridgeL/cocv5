import { useNavigate } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import Chat from '../Chat';
import './RoomChat.css';

export default function RoomChat() {
  const navigate = useNavigate();

  return (
    <div className="room-chat-wrapper">
      <div className="room-chat-nav">
        <button className="back-btn" onClick={() => navigate('/rooms')}>
          <ChevronLeft size={20} />
          返回房间列表
        </button>
      </div>
      <Chat />
    </div>
  );
}
