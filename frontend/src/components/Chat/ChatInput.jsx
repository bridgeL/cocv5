import React from 'react';

export default function ChatInput({
  input,
  onInputChange,
  onSend,
  onKeyPress,
  disabled,
  placeholder = "输入消息..."
}) {
  return (
    <div className="input-area">
      <div className="input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyPress={onKeyPress}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete="off"
        />
        <button onClick={onSend} disabled={disabled}>
          发送
        </button>
      </div>
    </div>
  );
}
