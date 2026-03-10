import React from 'react';

export default function ChatHeader({
  connectionStatus,
  sessionId,
  roomName,
  collapseMode,
  onCollapseModeChange
}) {
  return (
    <header className="chat-header">
      <div className="header-left">
        <h1>{roomName || 'AI 助手'}</h1>
        <div className="status">
          <span className={`status-dot ${connectionStatus === 'connected' ? 'connected' : ''}`}></span>
          <span>{connectionStatus === 'connected' ? '已连接' : '连接中...'}</span>
        </div>
      </div>
      <div className="header-right">
        {!roomName && (
          <div className="collapse-toggle">
            <button
              className={collapseMode === 'all-collapsed' ? 'active' : ''}
              onClick={() => onCollapseModeChange('all-collapsed')}
            >
              简略
            </button>
            <button
              className={collapseMode === 'all-expanded' ? 'active' : ''}
              onClick={() => onCollapseModeChange('all-expanded')}
            >
              详细
            </button>
          </div>
        )}
        {sessionId && <div className="session-id">Session: {sessionId}</div>}
      </div>
    </header>
  );
}
