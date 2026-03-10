import ChatHeader from './ChatHeader';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import { useChat } from './hooks/useChat';
import './Chat.css';

export default function Chat() {
  const {
    connectionStatus,
    messages,
    input,
    setInput,
    error,
    sessionId,
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
  } = useChat();

  return (
    <div className="chat-container">
      <ChatHeader
        connectionStatus={connectionStatus}
        sessionId={sessionId}
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
      />

      <ChatInput
        input={input}
        onInputChange={setInput}
        onSend={sendMessage}
        onKeyPress={handleKeyPress}
        disabled={connectionStatus !== 'connected'}
      />

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
