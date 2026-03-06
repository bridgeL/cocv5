import { useState, useRef, useEffect, useCallback } from 'react';
import ToolCall from './ToolCall';
import './Chat.css';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [currentToolCall, setCurrentToolCall] = useState(null);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const currentAssistantMsgRef = useRef(null);

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // WebSocket 连接
  useEffect(() => {
    let isConnecting = false;
    let reconnectTimer = null;

    const connect = () => {
      if (isConnecting || wsRef.current?.readyState === WebSocket.OPEN) return;
      isConnecting = true;

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        isConnecting = false;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleMessage(data);
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        isConnecting = false;
        reconnectTimer = setTimeout(connect, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('连接出错');
        isConnecting = false;
      };
    };

    const handleMessage = (data) => {
      switch (data.type) {
        case 'session_init':
          setSessionId(data.session_id);
          setIsConnected(true);
          setError(null);
          break;

        case 'received':
          setIsProcessing(true);
          break;

        case 'chunk':
          // 流式输出
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.type === 'assistant' && !lastMsg.isComplete) {
              return [
                ...prev.slice(0, -1),
                { ...lastMsg, content: lastMsg.content + data.content }
              ];
            }
            return [...prev, { type: 'assistant', content: data.content, isComplete: false }];
          });
          break;

        case 'tool_before':
          // 工具调用前
          if (data.tool_calls) {
            data.tool_calls.forEach(tc => {
              setCurrentToolCall({
                id: `tool-${tc.name}-${Date.now()}`,
                name: tc.name,
                args: tc.arguments,
                status: 'executing'
              });
              setMessages(prev => [
                ...prev,
                {
                  type: 'tool',
                  name: tc.name,
                  args: tc.arguments,
                  status: 'executing'
                }
              ]);
            });
          }
          break;

        case 'tool_after':
          // 工具调用后
          if (data.results) {
            data.results.forEach(result => {
              setCurrentToolCall(null);
              setMessages(prev => {
                const lastMsg = prev[prev.length - 1];
                if (lastMsg && lastMsg.type === 'tool' && lastMsg.name === result.name && lastMsg.status === 'executing') {
                  return [
                    ...prev.slice(0, -1),
                    {
                      ...lastMsg,
                      result: result.result,
                      status: 'success'
                    }
                  ];
                }
                return prev;
              });
            });
          }
          break;

        case 'complete':
          setIsProcessing(false);
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.type === 'assistant') {
              return [...prev.slice(0, -1), { ...lastMsg, isComplete: true }];
            }
            return prev;
          });
          setCurrentToolCall(null);
          break;

        case 'error':
          setIsProcessing(false);
          setError(data.error || '未知错误');
          setCurrentToolCall(null);
          break;
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, []);

  // 发送消息
  const sendMessage = useCallback(() => {
    const text = input.trim();
    if (!text || isProcessing || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    setMessages(prev => [...prev, { type: 'user', content: text }]);
    setInput('');

    wsRef.current.send(JSON.stringify({
      type: 'agent_chat',
      message: text
    }));
  }, [input, isProcessing]);

  // 处理键盘事件
  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }, [sendMessage]);

  return (
    <div className="chat-container">
      {/* 顶部状态栏 */}
      <header className="chat-header">
        <div className="header-left">
          <h1>AI 助手</h1>
          <div className="status">
            <span className={`status-dot ${isConnected ? 'connected' : ''}`}></span>
            <span>{isConnected ? '已连接' : '连接中...'}</span>
          </div>
        </div>
        {sessionId && <div className="session-id">Session: {sessionId}</div>}
      </header>

      {/* 消息区域 */}
      <div className="messages">
        {messages.map((msg, index) => {
          if (msg.type === 'user') {
            return (
              <div key={index} className="message user">
                <div className="message-header">你</div>
                <div className="message-content">{msg.content}</div>
              </div>
            );
          }

          if (msg.type === 'assistant') {
            return (
              <div key={index} className="message assistant">
                <div className="message-header">AI</div>
                <div className="message-content">{msg.content}</div>
              </div>
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
              />
            );
          }

          return null;
        })}

        {isProcessing && (
          <div className="thinking">
            <div className="thinking-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span>AI 正在思考...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="input-area">
        <div className="input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入消息..."
            disabled={!isConnected || isProcessing}
            autoComplete="off"
          />
          <button onClick={sendMessage} disabled={!isConnected || isProcessing}>
            发送
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className={`error-toast ${error ? 'show' : ''}`} onAnimationEnd={() => setError(null)}>
          {error}
        </div>
      )}
    </div>
  );
}
