import React from 'react';

export default function UserMessage({ content }) {
  return (
    <div className="message user">
      <div className="message-header">你</div>
      <div className="message-content">{content}</div>
    </div>
  );
}
