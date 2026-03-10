import React from 'react';

export default function UserMessage({ content, nickname, isRoomMode }) {
  return (
    <div className="message user">
      <div className="message-header">{isRoomMode ? nickname : '你'}</div>
      <div className="message-content">{content}</div>
    </div>
  );
}
