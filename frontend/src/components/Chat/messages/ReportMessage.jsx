import React from 'react';

export default function ReportMessage({ content, isComplete, collapsed, onToggle }) {
  return (
    <div className={`message report ${collapsed ? 'collapsed' : ''}`}>
      <div className="message-header" onClick={onToggle}>
        回答
        {!isComplete && <span className="tool-call-thinking">回答中...</span>}
        {!collapsed ? ' ▼' : ' ▶'}
      </div>
      {!collapsed && <div className="message-content">{content}</div>}
    </div>
  );
}
