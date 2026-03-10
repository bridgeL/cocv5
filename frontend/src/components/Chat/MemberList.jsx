import { getUser } from '../../utils/user';

export default function MemberList() {
  const user = getUser();

  const members = [
    { id: 'ai', name: 'AI 助手', avatar: '🤖', status: 'online', isAI: true },
    { id: user?.id || 'user', name: user?.name || '我', avatar: '👤', status: 'online', isAI: false },
  ];

  return (
    <div className="member-list">
      <div className="member-list-header">
        <h3>房间成员</h3>
        <span className="member-count">{members.length}</span>
      </div>
      <div className="member-list-content">
        {members.map(member => (
          <div key={member.id} className={`member-item ${member.isAI ? 'ai' : ''}`}>
            <div className="member-avatar">{member.avatar}</div>
            <div className="member-info">
              <div className="member-name">{member.name}</div>
              <div className="member-status">
                <span className={`status-dot ${member.status}`}></span>
                {member.status === 'online' ? '在线' : '离线'}
              </div>
            </div>
            {member.isAI && <span className="member-badge">AI</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
