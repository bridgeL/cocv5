import { getUser } from '../../utils/user';

export default function MemberList({ members: dynamicMembers }) {
  const user = getUser();

  // 如果有动态成员数据，使用动态数据（房间模式）
  // 否则使用静态数据（个人AI助手模式）
  const members = dynamicMembers || [
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
          <div key={member.id || member.user_id} className={`member-item ${member.isAI ? 'ai' : ''} ${member.is_owner ? 'owner' : ''}`}>
            <div className="member-avatar">{member.avatar || '👤'}</div>
            <div className="member-info">
              <div className="member-name">{member.name || member.nickname}</div>
              <div className="member-status">
                <span className={`status-dot ${member.status || 'online'}`}></span>
                {(member.status || 'online') === 'online' ? '在线' : '离线'}
              </div>
            </div>
            {member.isAI && <span className="member-badge">AI</span>}
            {member.user_id === user?.id && !member.isAI && <span className="member-badge me">我</span>}
            {member.is_owner && !member.isAI && <span className="member-badge owner">房主</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
