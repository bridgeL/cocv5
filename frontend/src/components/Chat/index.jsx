import { useParams } from 'react-router-dom';
import ChatHeader from './ChatHeader';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import MemberList from './MemberList';
import { useChat } from './hooks/useChat';
import { useRoomChat } from './hooks/useRoomChat';
import './Chat.css';

export default function Chat() {
  const { roomId } = useParams();

  // 根据是否有 roomId 决定使用哪个 hook
  const roomChat = roomId ? useRoomChat(roomId) : null;
  const normalChat = !roomId ? useChat() : null;

  const {
    connectionStatus,
    messages,
    input,
    setInput,
    error,
    sessionId,
    roomInfo,
    members,
    isJoined,
    collapseMode,
    showPlaceholderThink,
    messagesEndRef,
    messagesContainerRef,
    isCollapsed,
    toggleItemCollapse,
    sendMessage,
    handleKeyPress,
    setCollapseMode,
    clearError
  } = roomChat || normalChat || {};

  return (
    <div className="chat-container">
      <div className="chat-main">
        <div className="chat-area">
          <ChatHeader
            connectionStatus={connectionStatus}
            sessionId={sessionId}
            roomName={roomInfo?.name}
            collapseMode={collapseMode}
            onCollapseModeChange={setCollapseMode}
          />

          <MessageList
            messages={messages}
            collapseMode={collapseMode}
            showPlaceholderThink={showPlaceholderThink}
            isCollapsed={isCollapsed}
            onToggleCollapse={toggleItemCollapse}
            messagesContainerRef={messagesContainerRef}
            messagesEndRef={messagesEndRef}
            isRoomMode={!!roomId}
          />

          <ChatInput
            input={input}
            onInputChange={setInput}
            onSend={sendMessage}
            onKeyPress={handleKeyPress}
            disabled={connectionStatus !== 'connected' || (roomId && !isJoined)}
            placeholder={roomId && !isJoined ? "加入房间后才能发言..." : "输入消息..."}
          />
        </div>

        <MemberList members={members} />
      </div>

      {error && (
        <div
          className={`error-toast ${error ? 'show' : ''}`}
          onAnimationEnd={clearError}
        >
          {error}
        </div>
      )}
    </div>
  );
}
