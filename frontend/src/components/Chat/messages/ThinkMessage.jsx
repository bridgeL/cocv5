import React from 'react';

export default function ThinkMessage({ content, isComplete, isPlaceholder, collapsed, onToggle }) {
  return (
    <div className={`message think ${collapsed ? 'collapsed' : ''} ${isPlaceholder ? 'placeholder' : ''}`}>
      <div className="message-header" onClick={onToggle}>
        {isPlaceholder ? (
          <span className="tool-call-thinking">思考中...</span>
        ) : (
          <>
            思考
            {!isComplete && <span className="tool-call-thinking">思考中...</span>}
            {!collapsed ? ' ▼' : ' ▶'}
          </>
        )}
      </div>
      {!collapsed && !isPlaceholder && <div className="message-content">{content}</div>}
    </div>
  );
}
