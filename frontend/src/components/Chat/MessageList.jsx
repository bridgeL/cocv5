import React from 'react';
import ToolCall from '../ToolCall';
import UserMessage from './messages/UserMessage';
import ThinkMessage from './messages/ThinkMessage';
import ReportMessage from './messages/ReportMessage';
import PlaceholderThink from './messages/PlaceholderThink';

export default function MessageList({
  messages,
  collapseMode,
  showPlaceholderThink,
  isCollapsed,
  messagesContainerRef,
  messagesEndRef,
  isRoomMode
}) {
  return (
    <div className="messages" ref={messagesContainerRef}>
      {messages.map((msg, index) => {
        // 简略模式下：不显示思考和工具气泡，保留占位思考气泡
        if (collapseMode === 'all-collapsed') {
          if (msg.type === 'think' && !msg.isPlaceholder) return null;
          if (msg.type === 'tool') return null;
        }

        if (msg.type === 'user') {
          return <UserMessage key={index} content={msg.content} nickname={msg.nickname} isRoomMode={isRoomMode} />;
        }

        if (msg.type === 'think') {
          return (
            <ThinkMessage
              key={index}
              content={msg.content}
              isComplete={msg.isComplete}
              isPlaceholder={msg.isPlaceholder}
              collapsed={isCollapsed(index, 'think')}
            />
          );
        }

        if (msg.type === 'report') {
          return (
            <ReportMessage
              key={index}
              content={msg.content}
              isComplete={msg.isComplete}
              collapsed={isCollapsed(index, 'report')}
            />
          );
        }

        if (msg.type === 'tool') {
          return (
            <ToolCall
              key={index}
              name={msg.name}
              args={msg.args}
              result={msg.result}
              status={msg.status}
              collapsed={isCollapsed(index, 'tool')}
            />
          );
        }

        return null;
      })}

      {/* 简略模式下，检查是否有正在进行的思考或工具调用被隐藏，需要显示占位提示 */}
      {showPlaceholderThink && <PlaceholderThink />}
      <div ref={messagesEndRef} />
    </div>
  );
}
